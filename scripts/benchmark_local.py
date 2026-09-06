"""Time three isolated synthetic domain journeys; do not infer human time savings."""
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from grantthread.repository import SQLiteRepository
from grantthread.reports import manifest, pdf_bytes
from grantthread.seed import IDENTITIES, seed_all
from grantthread.service import Service
from grantthread.storage import LocalStorage


def main():
    results = []
    artifacts = ROOT / "artifacts"
    artifacts.mkdir(exist_ok=True)
    for iteration in range(3):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"GRANTTHREAD_MODE": "local", "GRANTTHREAD_DATA_DIR": directory, "BEDROCK_MODEL_ID": ""}):
            started = time.perf_counter()
            repository, storage = SQLiteRepository(Path(directory) / "benchmark.sqlite3"), LocalStorage(directory)
            seed_all(repository, storage)
            grantee = Service(IDENTITIES["brightpath"], repository, storage)
            funder = Service(IDENTITIES["northstar"], repository, storage)
            csv_text = (ROOT / "fixtures" / "ledger-proposed.csv").read_text(encoding="utf-8-sig")
            preview = grantee.import_expenses({"csv": csv_text})
            assert not preview["errors"] and preview["warnings"][0]["excessMinor"] == 20000
            grantee.import_expenses({"csv": csv_text, "commit": True})
            grantee.proposal_action("venue-split", {"expectedVersion": 1, "allocations": [
                {"grantId": "digital-belonging", "amountMinor": 50000}, {"grantId": "community-makers", "amountMinor": 50000}]}, "apply")
            incomplete = grantee.assemble_report_draft("digital-belonging")
            assert not incomplete["readiness"]["ready"]
            raw = (ROOT / "fixtures" / "payment-proof-printing.txt").read_bytes()
            intent = grantee.upload_intent({"name": "payment-proof-printing.txt", "size": len(raw), "contentType": "text/plain",
                                           "grantIds": ["digital-belonging"], "expenseId": "printing", "kind": "payment_proof"})
            grantee.receive_upload(intent["id"], raw)
            uploaded = grantee.complete_upload(intent["id"])
            grantee.proposal_action(uploaded["proposalId"], {"expectedVersion": 1}, "apply")
            reports = [grantee.assemble_report_draft(key) for key in ["digital-belonging", "community-makers"]]
            assert [report["allocatedMinor"] for report in reports] == [170000, 310000]
            for report in reports:
                pdf = pdf_bytes(report)
                assert pdf.startswith(b"%PDF-")
                if iteration == 0:
                    (artifacts / (report["grantId"] + "-sample.pdf")).write_bytes(pdf)
                    (artifacts / (report["grantId"] + "-manifest.json")).write_text(json.dumps(manifest(report), indent=2), encoding="utf-8")
            report = reports[0]
            snapshot = grantee.share_report(report["id"], {"expectedVersion": report["version"], "attachmentIds": ["invoice-venue", uploaded["evidence"]["id"]], "confirmOriginals": True})
            question = funder.create_clarification({"snapshotId": snapshot["id"], "question": "How many unique workshops does this package represent?"})
            grantee.clarification_action(question["id"], {"message": "One workshop with 24 recorded participants; it supports two grants and counts once for the organisation."}, "respond")
            funder.clarification_action(question["id"], {}, "resolve")
            job = grantee.create_job()
            assert job["status"] == "unavailable" and not job["toolEvents"]
            assert funder.shared_report(snapshot["id"])["clarifications"][0]["status"] == "resolved"
            totals = grantee.calculate_allocations()
            results.append({"iteration": iteration + 1, "seconds": round(time.perf_counter() - started, 4),
                            "uniqueExpenses": 5, "expenseMinor": totals["expenseMinor"], "allocatedMinor": totals["allocatedMinor"],
                            "byGrant": totals["byGrant"], "reportFormats": 2, "resolvedClarifications": 1,
                            "humanReviewTimeSeconds": None, "manualBaselineSeconds": None, "agentStatus": job["status"]})
    record = {"kind": "scripted synthetic local benchmark", "userValidation": "pending", "liveModel": "not configured; not measured",
              "scope": "Seed, CSV preview/import, correction, evidence review, two reports/PDFs, snapshot and clarification. Service-layer execution; excludes browser, network and human review.",
              "limitations": "Automated runtime is not a measure of administrator time savings. No manual baseline or participant timing is available.", "runs": results}
    path = ROOT / "docs" / "BENCHMARK_RESULTS.json"
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
