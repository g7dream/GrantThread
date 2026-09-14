"""Application operations; authority is supplied by the server, never by tool arguments."""
import copy
import csv
import hashlib
import io
import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import PurePath

from .domain import calculate, parse_csv, readiness, validate_allocations, validate_source
from .errors import DomainError, require
from .repository import get_repository
from .response_estimates import SIMULATED_HISTORY, estimate_response_time
from .storage import get_storage


def now():
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix):
    return prefix + "-" + uuid.uuid4().hex[:16]


def public_evidence(evidence):
    return {k: copy.deepcopy(v) for k, v in evidence.items() if k not in {"objectKey", "parsedKey"}}


def clean_text(value, label, limit=2000):
    require(isinstance(value, str) and 0 < len(value.strip()) <= limit, f"{label} is required (up to {limit} characters)")
    return value.strip()


class Service:
    def __init__(self, identity, repository=None, storage=None):
        require(isinstance(identity, dict) and identity.get("role") in {"grantee", "funder"}, "Sign in is required", "unauthorised", 401)
        self.identity = copy.deepcopy(identity)
        self.org_id = identity["organisationId"]
        self.repository = repository or get_repository()
        self.storage = storage or get_storage()

    def grantee(self):
        require(self.identity["role"] == "grantee", "This action requires the grantee workspace", "forbidden", 403)

    def data(self):
        self.grantee()
        return self.repository.read(self.org_id)

    def audit(self, data, action, target):
        data["audit"].append({"actorId": self.identity["id"], "actorName": self.identity.get("name", ""),
                              "action": action, "targetId": target, "at": now()})

    def activity(self, limit=200):
        """Expose recorded workspace changes, without claiming a complete access log."""
        rows = self.data().get('audit', [])
        start = max(0, len(rows) - limit)
        events = [{'sequence': index + 1, **{key: value for key, value in row.items()
                   if key in {'action', 'targetId', 'actorId', 'actorName', 'at'}}}
                  for index, row in enumerate(rows[start:], start)]
        return {'events': list(reversed(events)), 'total': len(rows), 'truncated': start > 0, 'limit': limit}

    def activity_csv(self):
        rows = self.data().get('audit', [])
        output = io.StringIO(newline='')
        writer = csv.writer(output)
        writer.writerow(['Sequence', 'Date (UTC)', 'Action', 'Record ID', 'Actor ID', 'Recorded actor name'])
        def text(value):
            value = str(value or '')
            # CSV readers must treat user-supplied names/identifiers as text, never spreadsheet formulas.
            return "'" + value if value.lstrip().startswith(('=', '+', '-', '@')) or value.startswith(('\t', '\r', '\n')) else value
        for index, row in enumerate(rows, 1):
            writer.writerow([index, *(text(row.get(key)) for key in ('at', 'action', 'targetId', 'actorId', 'actorName'))])
        return output.getvalue().encode('utf-8-sig')

    def grant(self, data, grant_id):
        require(grant_id in data["grants"], "Grant not found", "not_found", 404)
        grant = copy.deepcopy(data["grants"][grant_id])
        grant["allocatedMinor"] = calculate(data, grant_id)["allocatedMinor"]
        grant["readiness"] = readiness(data, grant_id)
        return grant

    def portfolio(self):
        data = self.data()
        totals = calculate(data)
        return {"organisation": data["organisation"], "grants": [self.grant(data, key) for key in data["grants"]],
                "decisions": [p for p in data["proposals"].values() if p["status"] == "pending"],
                "totals": {"currency": totals["currency"], "byCurrency": totals['byCurrency'], "awardMinor": sum(g["awardMinor"] for g in data["grants"].values()) if totals['currency'] else 0,
                           "allocatedMinor": totals["allocatedMinor"], "expenseMinor": totals["expenseMinor"],
                           "uniqueActivities": len({a["id"] for a in data["activities"] if a.get("confirmed")})},
                "requirements": self.list_requirements(), "jobs": list(data["jobs"].values())[-10:]}

    def grants(self):
        data = self.data()
        return [self.grant(data, key) for key in data["grants"]]

    def response_estimate(self, body):
        data = self.data()
        require(isinstance(body, dict), "An estimate request is required")
        grant_id = body.get("grantId")
        require(isinstance(grant_id, str), "Choose a grant")
        grant = self.grant(data, grant_id)
        estimate = estimate_response_time(SIMULATED_HISTORY.get(grant["funderOrgId"], ()), body.get("submittedDate"))
        return {**estimate, "grantId": grant_id, "grantName": grant["name"], "funderName": grant["funderName"]}

    def grant_detail(self, grant_id):
        data = self.data()
        return {"grant": self.grant(data, grant_id), "requirements": self.list_requirements(grant_id),
                "expenses": [e for e in data["expenses"].values() if any(a["grantId"] == grant_id for a in e["allocations"])],
                "activities": [a for a in data["activities"] if grant_id in a["grantIds"]],
                "evidence": [public_evidence(e) for e in data["evidence"].values() if grant_id in e["grantIds"]],
                "reports": [r for r in data["reports"].values() if r["grantId"] == grant_id]}

    def list_requirements(self, grant_id=None):
        data = self.data()
        if grant_id:
            self.grant(data, grant_id)
        return [r for key in data["grants"] if not grant_id or key == grant_id
                for r in readiness(data, key)["requirements"]]

    def calculate_allocations(self, grant_id=None):
        return calculate(self.data(), grant_id)

    def check_report_readiness(self, grant_id):
        data = self.data()
        self.grant(data, grant_id)
        return readiness(data, grant_id)

    def expenses(self):
        return list(self.data()["expenses"].values())

    def import_expenses(self, body):
        csv_text = body.get("csv")
        preview = parse_csv(csv_text, self.data())
        result = {k: v for k, v in preview.items() if k != "groups"}
        result.update(imported=0, proposalIds=[])
        if not body.get("commit", False):
            return result
        require(body.get("commit") is True, "Commit must be a boolean")
        require(not preview["errors"], "Resolve all CSV errors before importing", "csv_errors", 422)
        digest = hashlib.sha256(csv_text.encode()).hexdigest()

        def commit(data):
            prior = next((a for a in data["audit"] if a["action"] == "csv_import" and a["targetId"] == digest), None)
            if prior:
                return {**result, "alreadyImported": True}
            parsed = parse_csv(csv_text, data)
            require(not parsed["errors"], "Expense facts changed after preview; preview again", "stale", 409)
            proposal_ids, changed = [], False
            for expense_id, candidate in parsed["groups"].items():
                existing = data["expenses"].get(expense_id)
                if not existing:
                    existing = {**candidate, "allocations": [], "paidStatus": "not_provided"}
                    data["expenses"][expense_id] = existing
                    changed = True
                if candidate["allocations"] == existing["allocations"]:
                    continue
                pending = next((p for p in data["proposals"].values() if p["kind"] == "allocation"
                                and p["status"] == "pending" and p["expenseId"] == expense_id), None)
                if pending and pending["after"]["allocations"] == candidate["allocations"]:
                    proposal_ids.append(pending["id"])
                    continue
                # A changed CSV proposal supersedes the old pending proposal, not the confirmed ledger.
                if pending:
                    pending["status"] = "superseded"
                    pending["version"] += 1
                proposal_id = new_id("proposal")
                refs = [{"evidenceId": e["id"], "version": e["version"], "page": 1, "excerpt": e["excerpt"]}
                        for e in data["evidence"].values() if e.get("expenseId") == expense_id and e["kind"] == "invoice"][:1]
                excess = max(0, sum(a["amountMinor"] for a in candidate["allocations"]) - existing["amountMinor"])
                data["proposals"][proposal_id] = {"id": proposal_id, "kind": "allocation", "expenseId": expense_id,
                    "title": "Review " + existing["description"] + " allocation", "reason": "Imported split requires an authorised review before it changes the ledger.",
                    "status": "pending", "version": 1, "inputVersion": data["factVersion"], "sourceRefs": refs,
                    "before": {"allocations": copy.deepcopy(existing["allocations"])}, "after": {"allocations": candidate["allocations"]},
                    "excessMinor": excess, "createdAt": now(), "origin": "csv-import", "sourceHash": digest}
                proposal_ids.append(proposal_id)
            if changed:
                data["factVersion"] += 1
            for key in proposal_ids:
                data["proposals"][key]["inputVersion"] = data["factVersion"]
            self.audit(data, "csv_import", digest)
            return {**result, "imported": len(parsed["groups"]), "proposalIds": proposal_ids}
        return self.repository.mutate(self.org_id, commit)

    def list_evidence(self):
        return [public_evidence(e) for e in self.data()["evidence"].values()]

    def read_evidence(self, evidence_id):
        evidence = self.data()["evidence"].get(evidence_id)
        require(evidence is not None, "Evidence not found", "not_found", 404)
        parsed = json.loads(self.storage.get(evidence["parsedKey"]))
        return {**public_evidence(evidence), "pages": parsed["pages"], "text": "\n\n".join(parsed["pages"])}

    def evidence_bytes(self, evidence_id):
        evidence = self.data()["evidence"].get(evidence_id)
        require(evidence is not None, "Evidence not found", "not_found", 404)
        link = self.storage.presign_get(evidence["objectKey"], evidence["contentType"], evidence["name"])
        return link or self.storage.get(evidence["objectKey"]), evidence["contentType"], evidence["name"]

    def validate_upload_metadata(self, data, body):
        name = clean_text(body.get("name"), "File name", 180)
        require("/" not in name and "\\" not in name and not any(ord(c) < 32 for c in name), "Use a plain file name")
        suffix = PurePath(name).suffix.lower()
        require(suffix in {".txt", ".pdf"}, "Upload a TXT or text-based PDF. Image OCR is not supported.", "unsupported_type", 415)
        content_type = "text/plain" if suffix == ".txt" else "application/pdf"
        require(body.get("contentType", content_type) == content_type, "File extension and content type must match")
        size = body.get("size")
        require(type(size) is int and 0 < size <= 5 * 1024 * 1024, "Upload must contain 1 byte to 5 MB", "too_large", 413)
        grants = body.get("grantIds")
        require(isinstance(grants, list) and 0 < len(grants) <= 20 and all(isinstance(g, str) and g in data["grants"] for g in grants),
                "Select grants from your workspace", "forbidden", 403)
        require(len(set(grants)) == len(grants), "Do not repeat a grant")
        kind = body.get("kind")
        require(kind in {"invoice", "payment_proof", "activity", "agreement"}, "Select a supported evidence type")
        expense_id = body.get("expenseId") or None
        if expense_id:
            require(expense_id in data["expenses"], "Expense not found", "not_found", 404)
        if kind == "payment_proof":
            require(expense_id is not None, "Select the expense supported by this payment proof")
        replaces = body.get("replacesId") or None
        if replaces:
            require(replaces in data["evidence"], "Previous evidence version not found", "not_found", 404)
            previous = data["evidence"][replaces]
            require(previous["status"] == "confirmed", "Replace the current confirmed version of this document", "stale_source", 409)
            require(previous["kind"] == kind and previous.get("expenseId") == expense_id,
                    "A replacement must retain the document's evidence type and expense")
        return {"name": name, "contentType": content_type, "size": size, "grantIds": grants,
                "kind": kind, "expenseId": expense_id, "replacesId": replaces}

    def upload_intent(self, body):
        data = self.data()
        metadata = self.validate_upload_metadata(data, body)
        upload_id = new_id("upload")
        key = f"{self.org_id}/incoming/{upload_id}"
        upload = {**metadata, "id": upload_id, "objectKey": key, "actorId": self.identity["id"], "createdAt": now(), "status": "pending"}
        def save(current):
            for existing in current["uploads"].values():
                if existing["status"] == "pending" and (datetime.now(timezone.utc) - datetime.fromisoformat(existing["createdAt"])).total_seconds() > 600:
                    existing["status"] = "expired"
            require(sum(u["status"] == "pending" for u in current["uploads"].values()) < 10,
                    "Finish existing uploads before adding more", "upload_limit", 429)
            current["uploads"][upload_id] = upload
        self.repository.mutate(self.org_id, save)
        url = self.storage.presign_put(key, metadata["contentType"])
        return {"id": upload_id, "uploadUrl": url or f"/api/uploads/{upload_id}", "method": "PUT",
                "headers": {"Content-Type": metadata["contentType"]}}

    def receive_upload(self, upload_id, raw):
        require(os.getenv("GRANTTHREAD_MODE") != "aws", "Use the authorised upload URL", "forbidden", 403)
        upload = self.data()["uploads"].get(upload_id)
        require(upload and upload["actorId"] == self.identity["id"], "Upload not found", "not_found", 404)
        require(upload["status"] == "pending", "Upload is already complete", "conflict", 409)
        require(len(raw) == upload["size"] and len(raw) <= 5 * 1024 * 1024, "Uploaded size does not match the declared size", "size_mismatch")
        self.storage.put(upload["objectKey"], raw, upload["contentType"])
        return {"uploaded": True}

    def complete_upload(self, upload_id):
        data = self.data()
        upload = data["uploads"].get(upload_id)
        require(upload and upload["actorId"] == self.identity["id"], "Upload not found", "not_found", 404)
        if upload["status"] == "complete":
            return {"evidence": public_evidence(data["evidence"][upload["evidenceId"]]), "alreadyCompleted": True}
        require(upload["status"] == "pending", "This upload expired or failed. Start a new upload.", "upload_expired", 409)
        try:
            raw = self.storage.get(upload["objectKey"])
            require(len(raw) == upload["size"] and len(raw) <= 5 * 1024 * 1024, "Uploaded size does not match the declared size", "size_mismatch")
            pages = self.parse_document(raw, upload["contentType"])
        except DomainError:
            def failed(current):
                if current["uploads"][upload_id]["status"] == "pending":
                    current["uploads"][upload_id]["status"] = "failed"
            self.repository.mutate(self.org_id, failed)
            raise
        evidence_id = new_id("evidence")
        key = f"{self.org_id}/evidence/{evidence_id}"
        # Copy to a new immutable final key so the still-valid presigned PUT cannot replace approved bytes.
        self.storage.put(key + "/original", raw, upload["contentType"])
        self.storage.put(key + "/parsed.json", json.dumps({"pages": pages}).encode(), "application/json")
        version = data["evidence"][upload["replacesId"]]["version"] + 1 if upload.get("replacesId") else 1
        evidence = {k: copy.deepcopy(v) for k, v in upload.items() if k in {"name", "kind", "grantIds", "expenseId", "contentType", "size", "replacesId"}}
        evidence.update(id=evidence_id, version=version, status="pending", sha256=hashlib.sha256(raw).hexdigest(),
                        pageCount=len(pages), excerpt=pages[0][:260], objectKey=key + "/original", parsedKey=key + "/parsed.json", createdAt=now())
        def save(current):
            active = current["uploads"][upload_id]
            if active["status"] == "complete":
                return {"evidence": public_evidence(current["evidence"][active["evidenceId"]]), "alreadyCompleted": True}
            current["evidence"][evidence_id] = evidence
            current["factVersion"] += 1
            active.update(status="complete", evidenceId=evidence_id)
            proposal_id = new_id("proposal")
            current["proposals"][proposal_id] = {"id": proposal_id, "kind": "evidence_link", "title": "Review " + evidence["name"],
                "reason": "Confirm that this document supports the selected requirement. A source reference does not prove its interpretation.",
                "evidenceId": evidence_id, "grantIds": evidence["grantIds"], "status": "pending", "version": 1, "inputVersion": current["factVersion"],
                "sourceRefs": [{"evidenceId": evidence_id, "version": version, "page": 1, "excerpt": evidence["excerpt"]}],
                "before": {"status": "pending"}, "after": {"status": "confirmed", "grantIds": evidence["grantIds"]},
                "createdAt": now(), "origin": "user-upload"}
            self.audit(current, "evidence_uploaded", evidence_id)
            return {"evidence": public_evidence(evidence), "proposalId": proposal_id}
        return self.repository.mutate(self.org_id, save)

    @staticmethod
    def parse_document(raw, content_type):
        if content_type == "text/plain":
            try:
                text = raw.decode("utf-8-sig")
            except UnicodeDecodeError as exc:
                raise DomainError("TXT files must use UTF-8 encoding", "unsupported_encoding", 415) from exc
            require("\x00" not in text and text.strip(), "File contains no usable text", "unsupported_document", 415)
            pages = [text]
        else:
            require(raw.startswith(b"%PDF-"), "This file is not a valid PDF", "invalid_document", 415)
            try:
                from pypdf import PdfReader
                reader = PdfReader(io.BytesIO(raw))
                require(not reader.is_encrypted, "Encrypted PDFs are not supported", "unsupported_document", 415)
                require(0 < len(reader.pages) <= 20, "PDF must contain 1 to 20 pages", "page_limit", 413)
                pages = [page.extract_text() or "" for page in reader.pages]
            except DomainError:
                raise
            except Exception as exc:
                raise DomainError("The PDF could not be read", "invalid_document", 415) from exc
            require(all(p.strip() for p in pages), "Every PDF page needs extractable text. Scanned or image-only pages require OCR, which is not supported.", "ocr_unsupported", 415)
        require(sum(len(p) for p in pages) <= 120_000, "Extracted text exceeds the 120,000-character limit", "text_limit", 413)
        return pages

    def proposals(self):
        data = self.data()
        return [{**proposal, "status": "stale" if proposal["status"] == "pending" and proposal["inputVersion"] != data["factVersion"] else proposal["status"]}
                for proposal in data["proposals"].values()]

    def confirm_evidence_link(self, data, proposal):
        for ref in proposal["sourceRefs"]:
            validate_source(data, ref)
        evidence = data["evidence"][proposal["evidenceId"]]
        require(evidence["status"] == "pending", "Only pending evidence can be confirmed. Superseded sources stay immutable.", "stale_source", 409)
        reviewed_grants = proposal["after"].get("grantIds")
        require(isinstance(reviewed_grants, list) and bool(reviewed_grants) and set(reviewed_grants).issubset(evidence["grantIds"]),
                "The reviewed link scope is invalid", "forbidden", 403)
        if evidence.get("replacesId"):
            require(data["evidence"][evidence["replacesId"]]["status"] == "confirmed",
                    "Another replacement has been confirmed. Upload against the latest document version.", "stale_source", 409)
            data["evidence"][evidence["replacesId"]]["status"] = "superseded"
        evidence["grantIds"] = copy.deepcopy(reviewed_grants)
        evidence["status"] = "confirmed"

    def apply_evidence_batch(self, body):
        self.grantee()
        requested = body.get("proposals")
        require(isinstance(requested, list) and 1 <= len(requested) <= 20 and all(isinstance(item, dict) for item in requested),
                "Select one to twenty evidence proposals")
        ids = [item.get("id") for item in requested]
        require(all(isinstance(key, str) for key in ids) and len(set(ids)) == len(ids), "Proposal IDs must be unique")
        def mutate(data):
            proposals = []
            for item in requested:
                proposal = data["proposals"].get(item["id"])
                require(proposal and proposal["kind"] == "evidence_link", "Only evidence connections may be batch approved", "invalid_batch")
                require(type(item.get("expectedVersion")) is int and proposal["version"] == item["expectedVersion"]
                        and proposal["inputVersion"] == data["factVersion"] and proposal["status"] == "pending",
                        "One or more selected proposals changed. Refresh and review them before applying the batch.", "stale", 409)
                proposals.append(proposal)
            for proposal in proposals:
                self.confirm_evidence_link(data, proposal)
                proposal.update(status="applied", version=proposal["version"] + 1, handledAt=now())
                self.audit(data, "proposal_apply", proposal["id"])
            data["factVersion"] += 1
            return {"applied": len(proposals), "proposals": proposals}
        return self.repository.mutate(self.org_id, mutate)

    def proposal_action(self, proposal_id, body, action):
        self.grantee()
        def mutate(data):
            proposal = data["proposals"].get(proposal_id)
            require(proposal is not None, "Proposal not found", "not_found", 404)
            require(type(body.get("expectedVersion")) is int, "Expected proposal version is required")
            require(proposal["version"] == body["expectedVersion"], "Proposal changed; refresh before applying", "stale", 409)
            require(proposal["status"] == "pending", "Proposal has already been handled", "already_handled", 409)
            if action == "apply":
                require(proposal["inputVersion"] == data["factVersion"], "Evidence or facts changed. Recompute this proposal before applying.", "stale", 409)
                if proposal["kind"] == "allocation":
                    expense = data["expenses"][proposal["expenseId"]]
                    require(not expense.get('financeEntryId'), 'Use Financials to create a linked adjustment for this confirmed expense')
                    allocations = body.get("allocations", proposal["after"]["allocations"])
                    validate_allocations(data, expense, allocations)
                    expense["allocations"] = copy.deepcopy(allocations)
                    expense["version"] += 1
                    proposal["applied"] = {"allocations": copy.deepcopy(allocations)}
                elif proposal["kind"] == "evidence_link":
                    self.confirm_evidence_link(data, proposal)
                else:
                    raise DomainError("Unsupported proposal kind")
                data["factVersion"] += 1
                proposal["status"] = "applied"
            else:
                proposal["status"] = "rejected"
                # Rejection changes readiness even though it does not change money.
                data["factVersion"] += 1
            proposal["version"] += 1
            proposal["handledAt"] = now()
            self.audit(data, "proposal_" + action, proposal_id)
            return proposal
        return self.repository.mutate(self.org_id, mutate)

    def recompute_proposal(self, proposal_id):
        self.grantee()
        def mutate(data):
            proposal = data["proposals"].get(proposal_id)
            require(proposal is not None, "Proposal not found", "not_found", 404)
            require(proposal["status"] == "pending", "Only pending proposals can be recomputed", "already_handled", 409)
            for ref in proposal["sourceRefs"]:
                validate_source(data, ref)
            if proposal["kind"] == "allocation":
                proposal["before"] = {"allocations": copy.deepcopy(data["expenses"][proposal["expenseId"]]["allocations"])}
            proposal["inputVersion"] = data["factVersion"]
            proposal["version"] += 1
            self.audit(data, "proposal_recomputed", proposal_id)
            return proposal
        return self.repository.mutate(self.org_id, mutate)

    def save_review_proposal(self, proposal):
        self.grantee()
        require(isinstance(proposal, dict) and proposal.get("kind", "evidence_link") == "evidence_link",
                "Agent tools may only suggest scoped evidence links", "unsupported_proposal", 422)
        allowed = {"kind", "evidenceId", "grantIds", "sourceRefs", "title", "reason"}
        require(set(proposal).issubset(allowed), "Unsupported fields cannot enter a proposal", "unsupported_proposal", 422)
        evidence = self.read_evidence(proposal.get("evidenceId"))
        require(evidence["status"] == "pending", "Only pending evidence needs a link proposal", "stale_source", 409)
        grant_ids = proposal.get("grantIds")
        require(isinstance(grant_ids, list) and bool(grant_ids) and all(g in evidence["grantIds"] for g in grant_ids),
                "Suggested grants must be in the evidence's authorised scope", "forbidden", 403)
        refs = proposal.get("sourceRefs")
        require(isinstance(refs, list) and 0 < len(refs) <= 4, "Provide one to four authorised citations")
        def mutate(data):
            for ref in refs:
                validate_source(data, ref)
                require(ref["evidenceId"] == evidence["id"], "Citation must reference the suggested evidence", "invalid_source", 422)
                excerpt = ref.get("excerpt", "")
                require(isinstance(excerpt, str) and excerpt.strip() and excerpt in evidence["pages"][ref["page"] - 1],
                        "Citation excerpt must occur on the cited page", "invalid_source", 422)
            existing = next((p for p in data["proposals"].values() if p["kind"] == "evidence_link" and p["status"] == "pending"
                             and p["evidenceId"] == evidence["id"]), None)
            if existing:
                return existing
            proposal_id = new_id("proposal")
            result = {"id": proposal_id, "kind": "evidence_link", "evidenceId": evidence["id"], "grantIds": grant_ids,
                      "title": "Review " + evidence["name"], "reason": "Agent-proposed evidence link. Verify the source before confirming.",
                      "status": "pending", "version": 1, "inputVersion": data["factVersion"], "sourceRefs": refs,
                      "before": {"status": evidence["status"]}, "after": {"status": "confirmed", "grantIds": grant_ids}, "createdAt": now(), "origin": "strands-bedrock"}
            data["proposals"][proposal_id] = result
            return result
        return self.repository.mutate(self.org_id, mutate)

    def create_job(self, grant_id=None, evidence_id=None):
        self.grantee()
        def mutate(data):
            if grant_id:
                self.grant(data, grant_id)
            if evidence_id:
                require(evidence_id in data["evidence"], "Evidence not found", "not_found", 404)
            active = next((j for j in data["jobs"].values() if j["actorId"] == self.identity["id"] and j["status"] in {"queued", "running"}), None)
            if active:
                expired = active.get("leaseExpiresAt", 0) and active["leaseExpiresAt"] < datetime.now(timezone.utc).timestamp()
                if active["inputVersion"] != data["factVersion"] or expired:
                    active.update(status="failed", finishedAt=now(), message="Inputs changed or the worker lease expired. A fresh reconciliation has been queued.")
                    active.pop("claimToken", None)
                    active.pop("leaseExpiresAt", None)
                else:
                    return active
            require(sum(j["createdAt"][:10] == now()[:10] and j["actorId"] == self.identity["id"] for j in data["jobs"].values()) < 30,
                    "Daily synthetic agent run limit reached", "job_limit", 429)
            job_id = new_id("job")
            from .worker import agent_configured
            configured = agent_configured()
            waiting = next((j for j in reversed(list(data["jobs"].values())) if j["status"] == "waiting_input"
                            and j["actorId"] == self.identity["id"] and (not grant_id or j.get("grantId") == grant_id)), None)
            job = {"id": job_id, "actorId": self.identity["id"], "actor": self.identity, "organisationId": self.org_id,
                   "inputVersion": data["factVersion"], "status": "queued" if configured else "unavailable", "engine": "strands-bedrock",
                   "createdAt": now(), "message": "Queued for scoped reconciliation" if configured else "AWS Bedrock is not configured. No agent run has been performed. Your confirmed records remain available.",
                   "toolEvents": [], "grantId": grant_id, "evidenceId": evidence_id, "resumesJobId": waiting["id"] if waiting else None}
            if not configured:
                job["finishedAt"] = now()
            data["jobs"][job_id] = job
            return job
        return self.repository.mutate(self.org_id, mutate)

    def jobs(self):
        return list(self.data()["jobs"].values())

    def get_job(self, job_id):
        job = self.data()["jobs"].get(job_id)
        require(job is not None, "Job not found", "not_found", 404)
        return job

    def update_job(self, job_id, **fields):
        self.grantee()
        def mutate(data):
            job = data["jobs"].get(job_id)
            require(job is not None, "Job not found", "not_found", 404)
            require(not set(fields) & {"actor", "actorId", "organisationId", "inputVersion", "id"}, "Job scope is immutable")
            job.update(fields)
            return job
        return self.repository.mutate(self.org_id, mutate)

    def assemble_report_draft(self, grant_id):
        self.grantee()
        def mutate(data):
            grant = self.grant(data, grant_id)
            existing = next((r for r in reversed(list(data["reports"].values())) if r["grantId"] == grant_id and r["inputVersion"] == data["factVersion"] and not r.get("sharedSnapshotId")), None)
            if existing:
                return existing
            version = 1 + max((r["version"] for r in data["reports"].values() if r["grantId"] == grant_id), default=0)
            report_id = new_id("report")
            expenses = [{"id": e["id"], "description": e["description"], "amountMinor": a.get('reportAmountMinor', a["amountMinor"]), "date": e["date"], "paidStatus": e.get("paidStatus", "not_provided")}
                        for e in data["expenses"].values() for a in e["allocations"] if a["grantId"] == grant_id]
            expenses += [{'id': e['id'], 'description': 'Adjustment: ' + e['description'], 'amountMinor': e['reportAmountMinor'], 'date': e['date'], 'paidStatus': 'adjustment'}
                         for e in data.get('financeEntries', {}).values() if e['grantId'] == grant_id and e['status'] == 'confirmed' and e['kind'] == 'adjustment']
            activities = [{k: a[k] for k in ("id", "title", "date", "participants")}
                          for a in data["activities"] if grant_id in a["grantIds"] and a.get("confirmed")]
            evidence = [e for e in data["evidence"].values() if grant_id in e["grantIds"] and e["status"] == "confirmed"]
            refs = [{"evidenceId": e["id"], "version": e["version"], "page": 1, "excerpt": e["excerpt"]} for e in evidence]
            allocated = grant["allocatedMinor"]
            from .reports import money as format_money
            money = format_money(allocated, grant['currency'])
            if grant["template"] == "northstar-outcomes":
                activity_word = "activity" if len(activities) == 1 else "activities"
                narrative = f"{grant['name']} records {len(activities)} confirmed linked {activity_word} and {money} in allocated expenses. Participant counts are activity-level records; repeat participation is not deduplicated across activities."
            else:
                narrative = f"{grant['name']} has {len(expenses)} expense allocation lines totalling {money}. All amounts come from the confirmed allocation ledger. Payment status is separate from invoice allocation."
            report = {"id": report_id, "grantId": grant_id, "grantName": grant["name"], "funderName": grant["funderName"],
                      "granteeName": data["organisation"]["name"], "template": grant["template"], "templateVersion": 1,
                      "version": version, "inputVersion": data["factVersion"], "createdAt": now(), "status": "ready" if grant["readiness"]["ready"] else "incomplete",
                      "readiness": grant["readiness"], "currency": grant["currency"], "awardMinor": grant["awardMinor"],
                      "allocatedMinor": allocated, "expenses": expenses, "activities": activities, "narrative": narrative,
                      "sourceRefs": refs, "availableAttachments": [{k: e[k] for k in ("id", "name", "version", "kind")} for e in evidence],
                      "synthetic": not any(e['grantId'] == grant_id for e in data.get('financeEntries', {}).values()) and grant.get('synthetic', True),
                      "factsOrigin": "confirmed records and deterministic calculations", "confirmedReceiptsMinor": None}
            data["reports"][report_id] = report
            self.audit(data, "report_prepared", report_id)
            return report
        return self.repository.mutate(self.org_id, mutate)

    def reports(self):
        data = self.data()
        return [{**report, "status": "stale" if report["inputVersion"] != data["factVersion"] else report["status"]} for report in data["reports"].values()]

    def report(self, report_id):
        data = self.data()
        report = data["reports"].get(report_id)
        require(report is not None, "Report not found", "not_found", 404)
        return {**report, "status": "stale" if report["inputVersion"] != data["factVersion"] else report["status"]}

    def share_report(self, report_id, body):
        self.grantee()
        def mutate(data):
            report = data["reports"].get(report_id)
            require(report is not None, "Report not found", "not_found", 404)
            require(type(body.get("expectedVersion")) is int and report["version"] == body["expectedVersion"], "Report version changed", "stale", 409)
            require(report["inputVersion"] == data["factVersion"], "Confirmed facts or evidence changed. Prepare a new report before sharing.", "stale", 409)
            require(readiness(data, report["grantId"])["ready"], "Resolve missing requirements and allocation decisions before sharing", "not_ready", 422)
            attachments = body.get("attachmentIds")
            require(isinstance(attachments, list) and all(isinstance(x, str) for x in attachments), "Select attachments explicitly")
            require(len(set(attachments)) == len(attachments), "Attachment IDs must be unique")
            allowed = {e["id"] for e in report["availableAttachments"]}
            require(set(attachments).issubset(allowed), "Attachment is outside this report", "forbidden", 403)
            require(not attachments or body.get("confirmOriginals") is True, "Confirm the explicit disclosure of selected original documents", "original_confirmation", 422)
            if report.get("sharedSnapshotId"):
                existing = data["snapshots"][report["sharedSnapshotId"]]
                require([a["id"] for a in existing["attachments"]] == attachments, "Published snapshots are immutable. Prepare a new version to change disclosure.", "immutable_snapshot", 409)
                return existing
            grant = data["grants"][report["grantId"]]
            snapshot_id = new_id("snapshot")
            projection = {k: copy.deepcopy(v) for k, v in report.items()
                          if k not in {"readiness", "availableAttachments", "sourceRefs", "inputVersion", "sharedSnapshotId"}}
            projection["sourceRefs"] = [r for r in report["sourceRefs"] if r["evidenceId"] in attachments]
            selected = [{k: data["evidence"][key][k] for k in ("id", "name", "version", "kind", "sha256", "pageCount")} for key in attachments]
            snapshot = {"id": snapshot_id, "reportId": report_id, "grantId": grant["id"], "grantName": grant["name"],
                        "recipientOrgId": grant["funderOrgId"], "recipientName": grant["funderName"],
                        "granteeName": data["organisation"]["name"], "granteeOrgId": self.org_id,
                        "version": report["version"], "publishedAt": now(), "report": projection, "attachments": selected, "clarifications": []}
            data["snapshots"][snapshot_id] = snapshot
            report["sharedSnapshotId"] = snapshot_id
            self.audit(data, "report_shared", snapshot_id)
            return snapshot
        return self.repository.mutate(self.org_id, mutate)

    def snapshot_scopes(self):
        if self.identity["role"] == "grantee":
            return [self.org_id]
        scopes = self.identity.get("granteeOrgIds", [])
        require(isinstance(scopes, list) and len(scopes) <= 20, "Funder membership needs configuration", "forbidden", 403)
        return scopes

    def shared_reports(self):
        snapshots = []
        for org_id in self.snapshot_scopes():
            data = self.repository.read(org_id)
            for snapshot in data["snapshots"].values():
                if self.identity["role"] == "funder" and snapshot["recipientOrgId"] != self.org_id:
                    continue
                snapshots.append({**snapshot, "clarifications": [c for c in data["clarifications"].values() if c["snapshotId"] == snapshot["id"]]})
        return snapshots

    def shared_report(self, snapshot_id):
        snapshot = next((s for s in self.shared_reports() if s["id"] == snapshot_id), None)
        require(snapshot is not None, "Shared report not found", "not_found", 404)
        return snapshot

    def shared_attachment(self, snapshot_id, evidence_id):
        snapshot = self.shared_report(snapshot_id)
        attachment = next((a for a in snapshot["attachments"] if a["id"] == evidence_id), None)
        require(attachment is not None, "Attachment is not in this shared manifest", "not_found", 404)
        data = self.repository.read(snapshot["granteeOrgId"])
        evidence = data["evidence"].get(evidence_id)
        require(evidence and evidence["version"] == attachment["version"] and evidence["sha256"] == attachment["sha256"],
                "Shared source version is unavailable", "source_unavailable", 409)
        link = self.storage.presign_get(evidence["objectKey"], evidence["contentType"], evidence["name"])
        return link or self.storage.get(evidence["objectKey"]), evidence["contentType"], evidence["name"]

    def clarifications(self):
        return [c for snapshot in self.shared_reports() for c in snapshot["clarifications"]]

    def create_clarification(self, body):
        require(self.identity["role"] == "funder", "Only the recipient funder can open a clarification", "forbidden", 403)
        snapshot = self.shared_report(body.get("snapshotId"))
        question = clean_text(body.get("question"), "Question")
        source_ref = body.get("sourceRef")
        if source_ref:
            attachment = next((a for a in snapshot["attachments"] if a["id"] == source_ref.get("evidenceId") and a["version"] == source_ref.get("version")), None)
            require(attachment and type(source_ref.get("page")) is int and 1 <= source_ref["page"] <= attachment["pageCount"], "Question source must belong to the shared manifest", "invalid_source", 422)
        clarification_id = new_id("clarification")
        clarification = {"id": clarification_id, "snapshotId": snapshot["id"], "grantName": snapshot["grantName"],
                         "question": question, "status": "open", "createdAt": now(), "sourceRef": source_ref,
                         "messages": [{"actorName": self.identity["name"], "role": "funder", "message": question, "at": now()}]}
        def mutate(data):
            require(len(data["clarifications"]) < 100, "Synthetic clarification limit reached", "workspace_limit", 429)
            data["clarifications"][clarification_id] = clarification
            self.audit(data, "clarification_opened", clarification_id)
            return clarification
        return self.repository.mutate(snapshot["granteeOrgId"], mutate)

    def clarification_action(self, clarification_id, body, action):
        clarification = next((c for c in self.clarifications() if c["id"] == clarification_id), None)
        require(clarification is not None, "Clarification not found", "not_found", 404)
        snapshot = self.shared_report(clarification["snapshotId"])
        if action == "respond":
            self.grantee()
            message = clean_text(body.get("message"), "Response")
        else:
            require(self.identity["role"] == "funder", "Only the recipient funder can acknowledge resolution", "forbidden", 403)
            message = "Acknowledged and resolved."
        def mutate(data):
            current = data["clarifications"][clarification_id]
            require(current["status"] != "resolved", "This clarification is already resolved", "already_handled", 409)
            if action == "resolve":
                require(current["status"] == "answered", "A grantee response is needed before resolution", "response_required", 422)
            current["messages"].append({"actorName": self.identity["name"], "role": self.identity["role"], "message": message, "at": now()})
            current["status"] = "answered" if action == "respond" else "resolved"
            self.audit(data, "clarification_" + action, clarification_id)
            return current
        return self.repository.mutate(snapshot["granteeOrgId"], mutate)
