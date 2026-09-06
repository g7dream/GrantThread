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
    return Redirect(source[0]) if isinstance(source[0], str) else Binary(*source)


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
        return {"user": identity, "mode": os.getenv("GRANTTHREAD_MODE", "local")}
    if method == "GET":
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
