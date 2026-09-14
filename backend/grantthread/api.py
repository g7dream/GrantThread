"""Transport-independent route dispatcher used by local HTTP and Lambda."""
import os
import threading

from .errors import DomainError, require
from .reports import manifest, pdf_bytes
from .service import Service


class Binary:
    def __init__(self, data, content_type, name):
        self.data, self.content_type, self.name = data, content_type, name


class Redirect:
    def __init__(self, location):
        self.location = location


def source_download(source):
    # Private S3 downloads avoid Lambda's response limit for permitted 5 MB files.
    # A separate credentialless browser fetch retains the configured CORS origin;
    # redirecting the authenticated cross-origin API request can produce Origin: null.
    if isinstance(source[0], str):
        return {"downloadUrl": source[0], "contentType": source[1], "filename": source[2]}
    return Binary(*source)


def dispatch_job(service, job):
    if job["status"] != "queued":
        return job
    if os.getenv("GRANTTHREAD_MODE") == "aws":
        import boto3
        import json
        try:
            boto3.client("sqs").send_message(QueueUrl=os.environ["GRANTTHREAD_QUEUE_URL"],
                MessageBody=json.dumps({"organisationId": service.org_id, "jobId": job["id"]}))
        except Exception:
            return service.update_job(job["id"], status="failed", message="Could not enqueue the agent run. Your confirmed records are unchanged.")
    else:
        from .worker import run_job
        threading.Thread(target=run_job, args=(service.org_id, job["id"]), daemon=True, name="grantthread-agent").start()
    return job


def trigger(service, result, grant_id=None, evidence_id=None):
    try:
        result["job"] = dispatch_job(service, service.create_job(grant_id, evidence_id))
    except DomainError as exc:
        # The user operation already persisted. Queue pressure must not misreport a successful import as failed.
        result["jobWarning"] = exc.message
    return result


def dispatch(method, path, body, identity, repository=None, storage=None, raw=None):
    service = Service(identity, repository, storage)
    parts = [part for part in path.strip("/").split("/") if part]
    if parts and parts[0] == "api":
        parts = parts[1:]
    if parts == ["session"] and method == "GET":
        from .demo import session
        return session(identity, service.repository)
    if len(parts) == 2 and parts[0] == "demo" and method == "POST":
        from .demo import start, reset
        if parts[1] == "start": return start(identity, service.repository, service.storage, body)
        if parts[1] == "reset": return reset(identity, service.repository, service.storage, body)
    if identity.get("publicDemo") is True:
        from .demo import request_repository
        repository = request_repository(identity, service.repository)
        service.repository = repository
    if parts and parts[0] == 'financials':
        from .finance_service import FinancialService
        finance = FinancialService(identity, repository, storage)
        route = parts[1:]
        if method == 'GET':
            if not route: return finance.overview()
            if len(route) == 3 and route[0] == 'imports' and route[2] == 'source': return source_download(finance.source_bytes(route[1]))
            if len(route) == 2 and route[0] == 'report': return finance.financial_report(route[1])
            if len(route) == 3 and route[0] == 'report' and route[2] in {'xlsx', 'template-xlsx'}:
                return Binary(finance.export_report(route[1], template=route[2] == 'template-xlsx'),
                              'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', f'{route[1]}-financial-report.xlsx')
            if len(route) == 4 and route[0] == 'report' and route[2] == 'template-xlsx':
                return Binary(finance.export_report(route[1], template=True, template_id=route[3]),
                              'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', f'{route[1]}-funder-template.xlsx')
        if method == 'POST':
            if route == ['grants']: return finance.create_grant(body)
            if route == ['receipts']: return finance.add_receipt(body)
            if route == ['entries']: return finance.create_entry(body)
            if route == ['entries', 'batch-confirm']: return finance.confirm_entries(body)
            if route == ['imports']:
                result = finance.upload_import(body)
                if result['status'] == 'needs_ai' and not result.get('alreadyImported'):
                    try:
                        result['job'] = dispatch_job(finance, finance.create_bank_job(result['id']))
                        result['message'] = result['job']['message']
                    except DomainError as exc:
                        result['jobWarning'] = exc.message
                return result
            if len(route) == 2 and route[0] == 'report': return finance.save_report_settings(route[1], body)
            if len(route) == 3 and route[0] == 'entries':
                if route[2] == 'update': return finance.update_entry(route[1], body)
                if route[2] == 'reject': return finance.reject_entry(route[1], body)
                if route[2] == 'adjust': return finance.adjust_entry(route[1], body)
                if route[2] == 'confirm':
                    require('id' not in body or body['id'] == route[1], 'Entry ID must match the requested entry')
                    return finance.confirm_entries({'entries': [{**body, 'id': route[1]}]})['entries'][0]
            if len(route) == 3 and route[0] == 'imports':
                if route[2] == 'preview': return finance.preview_import(route[1], body)
                if route[2] == 'commit': return finance.commit_import(route[1], body)
                if route[2] == 'map-template': return finance.map_template(route[1], body)
                if route[2] == 'review': return finance.review_import(route[1], body)
                if route[2] == 'analyse': return dispatch_job(finance, finance.create_bank_job(route[1]))
        raise DomainError('Financial endpoint not found', 'not_found', 404)
    if method == "GET":
        if parts == ["activity"]: return service.activity()
        if parts == ["activity", "csv"]: return Binary(service.activity_csv(), "text/csv; charset=utf-8", "grantthread-activity.csv")
        if parts == ["portfolio"]: return service.portfolio()
        if parts == ["grants"]: return service.grants()
        if len(parts) == 2 and parts[0] == "grants": return service.grant_detail(parts[1])
        if parts == ["expenses"]: return service.expenses()
        if parts == ["evidence"]: return service.list_evidence()
        if len(parts) == 2 and parts[0] == "evidence": return service.read_evidence(parts[1])
        if len(parts) == 3 and parts[0] == "evidence" and parts[2] == "download": return source_download(service.evidence_bytes(parts[1]))
        if parts == ["proposals"]: return service.proposals()
        if parts == ["jobs"]: return service.jobs()
        if len(parts) == 2 and parts[0] == "jobs": return service.get_job(parts[1])
        if parts == ["reports"]: return service.reports()
        if len(parts) in {2, 3} and parts[0] == "reports":
            report = service.report(parts[1])
            if len(parts) == 2: return report
            if parts[2] == "pdf": return Binary(pdf_bytes(report), "application/pdf", f"{report['grantId']}-v{report['version']}.pdf")
            if parts[2] == "manifest": return manifest(report)
        if parts == ["shared-reports"]: return service.shared_reports()
        if len(parts) >= 2 and parts[0] == "shared-reports":
            snapshot = service.shared_report(parts[1])
            if len(parts) == 2: return snapshot
            if len(parts) == 3 and parts[2] == "pdf": return Binary(pdf_bytes(snapshot["report"]), "application/pdf", f"{snapshot['grantId']}-shared-v{snapshot['version']}.pdf")
            if len(parts) == 3 and parts[2] == "manifest":
                return {**manifest(snapshot["report"], snapshot["attachments"]), "snapshotId": snapshot["id"], "recipientName": snapshot["recipientName"], "publishedAt": snapshot["publishedAt"]}
            if len(parts) == 4 and parts[2] == "attachments": return source_download(service.shared_attachment(parts[1], parts[3]))
        if parts == ["clarifications"]: return service.clarifications()
    if method == "PUT" and len(parts) == 2 and parts[0] == "uploads":
        return service.receive_upload(parts[1], raw or b"")
    if method == "POST":
        if parts == ["response-estimates"]: return service.response_estimate(body)
        if parts == ["proposals", "batch-apply"]: return trigger(service, service.apply_evidence_batch(body))
        if parts == ["expenses", "import"]:
            result = service.import_expenses(body)
            return trigger(service, result) if body.get("commit") else result
        if parts == ["evidence", "upload-intent"]: return service.upload_intent(body)
        if parts == ["evidence", "complete"]:
            result = service.complete_upload(body.get("id"))
            return trigger(service, result, evidence_id=result["evidence"]["id"]) if not result.get("alreadyCompleted") else result
        if parts == ["evidence"]:
            require(os.getenv("GRANTTHREAD_MODE") != "aws", "Use signed upload endpoints in the cloud", "forbidden", 403)
            raw_text = body.get("content")
            require(isinstance(raw_text, str), "TXT content is required")
            raw_text = raw_text.encode("utf-8")
            intent = service.upload_intent({**body, "size": len(raw_text), "contentType": "text/plain"})
            service.receive_upload(intent["id"], raw_text)
            result = service.complete_upload(intent["id"])
            return trigger(service, result, evidence_id=result["evidence"]["id"])
        if len(parts) == 3 and parts[0] == "proposals":
            if parts[2] in {"apply", "reject"}:
                result = service.proposal_action(parts[1], body, parts[2])
                return trigger(service, result) if parts[2] == "apply" else result
            if parts[2] == "recompute": return service.recompute_proposal(parts[1])
        if parts == ["jobs"]: return dispatch_job(service, service.create_job(body.get("grantId")))
        if parts == ["reports"]: return service.assemble_report_draft(body.get("grantId"))
        if len(parts) == 3 and parts[0] == "reports" and parts[2] == "share": return service.share_report(parts[1], body)
        if parts == ["clarifications"]: return service.create_clarification(body)
        if len(parts) == 3 and parts[0] == "clarifications" and parts[2] in {"respond", "resolve"}: return service.clarification_action(parts[1], body, parts[2])
    raise DomainError("Endpoint not found", "not_found", 404)
