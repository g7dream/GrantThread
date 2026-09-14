"""Public demo isolation, reset fencing and transport checks; no AWS calls."""
import copy
import base64
import hashlib
import json
import os
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from grantthread.api import dispatch
from grantthread.auth import gateway_identity
from grantthread.demo import identity_for_subject, request_repository, reset, session, start
from grantthread.errors import DomainError
from grantthread.finance_service import FinancialService
from grantthread.lambda_handler import handler
from grantthread.repository import SQLiteRepository
from grantthread.seed import IDENTITIES, seed_all
from grantthread.service import Service
from grantthread.storage import LocalStorage
from grantthread.worker import _GuardedRepository, RunStopped


class PublicDemo(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        env = patch.dict(os.environ, {"GRANTTHREAD_MODE": "local", "GRANTTHREAD_DATA_DIR": temporary.name,
                                     "GRANTTHREAD_PUBLIC_DEMO": "true", "BEDROCK_MODEL_ID": ""})
        env.start()
        self.addCleanup(env.stop)
        self.repo = SQLiteRepository(Path(temporary.name) / "demo.sqlite3")
        self.storage = LocalStorage(temporary.name)
        self.alice = identity_for_subject("fictional-subject-alice")
        self.bob = identity_for_subject("fictional-subject-bob")

    def denied(self, action, code):
        with self.assertRaises(DomainError) as caught:
            action()
        self.assertEqual(caught.exception.code, code)

    def create(self, identity=None):
        identity = identity or self.alice
        start(identity, self.repo, self.storage, {})
        return Service(identity, self.repo, self.storage)

    def restore(self, identity=None):
        identity = identity or self.alice
        version = self.repo.read(identity["demoWorkspaceId"])["version"]
        return reset(identity, self.repo, self.storage, {"version": version, "confirm": "RESTORE DEMO"})

    def event(self, subject="fictional-subject-alice", role=None, **claims):
        event = {"requestContext": {"authorizer": {"jwt": {"claims": {
            "token_use": "access", "sub": subject, "scope": "openid email grantthread/access", **claims}}}}}
        if role is not None:
            event["headers"] = {"X-GrantThread-Demo-Role": role}
        return event

    def test_subject_namespace_is_stable_and_arbitrary_roles_are_rejected(self):
        self.assertEqual(gateway_identity(self.event(), self.repo), self.alice)
        self.assertNotEqual(self.alice["organisationId"], self.bob["organisationId"])
        funder = gateway_identity(self.event(role="funder"), self.repo)
        self.assertEqual(funder["granteeOrgIds"], [self.alice["organisationId"]])
        self.assertNotEqual(funder["organisationId"], "northstar")
        for role in ("admin", "northstar", "brightpath", "", "funder,grantee"):
            self.denied(lambda: gateway_identity(self.event(role=role), self.repo), "invalid_demo_role")

    def test_missing_membership_remains_closed_when_flag_is_disabled(self):
        with patch.dict(os.environ, {"GRANTTHREAD_PUBLIC_DEMO": "false"}):
            self.denied(lambda: gateway_identity(self.event(), self.repo), "membership_required")

    def test_invalid_jwt_never_becomes_a_public_demo(self):
        for claims in ({"token_use": "id"}, {"scope": "openid email"}, {"sub": ""}):
            with patch.object(self.repo, "read_key") as read:
                self.denied(lambda: gateway_identity(self.event(**claims), self.repo), "unauthorised")
                read.assert_not_called()

    def test_operator_membership_is_preserved_and_cannot_switch_demo_roles(self):
        identity = {**IDENTITIES["brightpath"], "id": "fictional-subject-alice"}
        with self.repo.connect() as db:
            db.execute("INSERT INTO records VALUES (?,?,?)", ("MEMBER#fictional-subject-alice", json.dumps(identity), 1))
        self.assertEqual(gateway_identity(self.event(), self.repo), identity)
        self.denied(lambda: gateway_identity(self.event(role="funder"), self.repo), "forbidden")
        self.denied(lambda: start(identity, self.repo, self.storage, {}), "forbidden")

    def test_repository_errors_cannot_fall_back_to_public_demo(self):
        for error in (DomainError("outage", "not_found", 503), DomainError("denied", "forbidden", 404)):
            with patch.object(self.repo, "read_key", side_effect=error):
                with self.assertRaises(DomainError) as caught:
                    gateway_identity(self.event(), self.repo)
                self.assertIs(caught.exception, error)

    def test_session_is_read_only_and_start_publishes_only_generated_private_sources(self):
        with patch.object(self.repo, "put_initial", wraps=self.repo.put_initial) as put, \
             patch.object(self.storage, "put", wraps=self.storage.put) as source:
            result = dispatch("GET", "/api/session", {}, self.alice, self.repo, self.storage)
            self.assertEqual(result["demo"], {"available": True, "initialized": False, "version": None, "roles": ["grantee", "funder"]})
            put.assert_not_called()
            source.assert_not_called()
            result = dispatch("POST", "/api/demo/start", {}, self.alice, self.repo, self.storage)
        self.assertTrue(result["demo"]["initialized"])
        self.assertEqual(put.call_count, 1)
        self.assertEqual(source.call_count, 18)
        self.assertTrue(all(call.args[0].startswith(self.alice["organisationId"] + "/demo-seed/1/") for call in source.call_args_list))
        data = self.repo.read(self.alice["organisationId"])
        self.assertEqual(len(data["grants"]), 3)
        for evidence in data["evidence"].values():
            self.assertEqual(hashlib.sha256(self.storage.get(evidence["objectKey"])).hexdigest(), evidence["sha256"])
            self.assertTrue(set(evidence["grantIds"]).issubset(data["grants"]))
        self.assertEqual(Service(self.alice, self.repo, self.storage).calculate_allocations()["expenseMinor"], 520000)

    def test_start_is_idempotent_and_never_reads_or_overwrites_shared_demo_data(self):
        seed_all(self.repo, self.storage)
        self.repo.mutate("brightpath", lambda data: data["grants"]["digital-belonging"].update(name="PRIVATE operator record"))
        operator_before = self.repo.read("brightpath")
        service = self.create()
        self.assertNotIn("PRIVATE operator record", json.dumps(service.data()))
        self.repo.mutate(service.org_id, lambda data: data["organisation"].update(name="Visitor edit"))
        before = service.data()
        with patch.object(self.storage, "put") as put:
            start(self.alice, self.repo, self.storage, {})
        put.assert_not_called()
        self.assertEqual(service.data(), before)
        self.assertEqual(self.repo.read("brightpath"), operator_before)

    def test_start_failure_does_not_publish_a_partial_workspace(self):
        with patch.object(self.storage, "put", side_effect=OSError("fictional storage outage")):
            with self.assertRaises(OSError):
                start(self.alice, self.repo, self.storage, {})
        self.assertFalse(session(self.alice, self.repo)["demo"]["initialized"])

    def test_concurrent_start_keeps_one_complete_workspace(self):
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(lambda _: start(self.alice, self.repo, self.storage, {}), range(2)))
        self.assertTrue(all(result["demo"]["initialized"] for result in results))
        data = self.repo.read(self.alice["organisationId"])
        self.assertEqual(data["version"], 1)
        self.assertEqual(len(data["evidence"]), 9)

    def test_forged_workspace_or_body_scope_never_starts_existing_data(self):
        for forged in ({**self.alice, "organisationId": "brightpath"}, {**self.alice, "demoWorkspaceId": "brightpath"}):
            self.denied(lambda: start(forged, self.repo, self.storage, {}), "forbidden")
        self.denied(lambda: start(self.alice, self.repo, self.storage, {"organisationId": "brightpath"}), "invalid_request")

    def test_personal_funder_can_only_review_own_explicitly_shared_report(self):
        alice, bob = self.create(), self.create(self.bob)
        def publish(service):
            proposal = next(iter(service.data()["proposals"].values()))
            service.proposal_action(proposal["id"], {"expectedVersion": proposal["version"], "allocations": [
                {"grantId": "demo1-digital-belonging", "amountMinor": 50000},
                {"grantId": "demo1-community-makers", "amountMinor": 50000}]}, "apply")
            report = service.assemble_report_draft("demo1-youth-skills")
            return service.share_report(report["id"], {"expectedVersion": report["version"], "attachmentIds": []})
        own_snapshot, other_snapshot = publish(alice), publish(bob)
        funder = Service(identity_for_subject(self.alice["id"], "funder"), self.repo, self.storage)
        self.assertEqual([item["id"] for item in funder.shared_reports()], [own_snapshot["id"]])
        self.denied(lambda: funder.shared_report(other_snapshot["id"]), "not_found")
        self.denied(lambda: funder.expenses(), "forbidden")
        question = funder.create_clarification({"snapshotId": own_snapshot["id"], "question": "Fictional demo question"})
        alice.clarification_action(question["id"], {"message": "Fictional response"}, "respond")
        self.assertEqual(funder.clarification_action(question["id"], {}, "resolve")["status"], "resolved")

    def test_reset_requires_confirmation_revision_and_no_active_job(self):
        service = self.create()
        for body in ({}, {"version": True, "confirm": "RESTORE DEMO"}, {"version": 1, "confirm": "yes"}):
            self.denied(lambda: reset(self.alice, self.repo, self.storage, body), "demo_confirmation")
        self.denied(lambda: reset(self.alice, self.repo, self.storage, {"version": 4, "confirm": "RESTORE DEMO"}), "stale")
        for status in ("queued", "running"):
            self.repo.mutate(service.org_id, lambda data: data["jobs"].update({"job-active": {"status": status}}))
            with patch.object(self.storage, "put") as put:
                self.denied(lambda: self.restore(), "demo_busy")
                put.assert_not_called()

    def test_reset_does_not_affect_another_visitor_or_reuse_ids_source_keys_or_versions(self):
        alice, bob = self.create(), self.create(self.bob)
        before, other_before = alice.data(), bob.data()
        originals = {e["objectKey"]: self.storage.get(e["objectKey"]) for e in before["evidence"].values()}
        result = self.restore()
        after = alice.data()
        self.assertEqual(result["demo"]["version"], after["version"])
        self.assertGreater(after["factVersion"], before["factVersion"])
        for collection in ("grants", "expenses", "evidence", "proposals"):
            self.assertFalse(set(before[collection]) & set(after[collection]))
            self.assertTrue(all(record["version"] > before["version"] for record in after[collection].values()))
        self.assertTrue(all(self.storage.get(key) == raw for key, raw in originals.items()))
        self.assertFalse(set(originals) & {e["objectKey"] for e in after["evidence"].values()})
        self.assertEqual(bob.data(), other_before)

    def test_reset_fences_old_proposals_and_financial_targets(self):
        service = self.create()
        old_proposal = next(iter(service.data()["proposals"].values()))
        old_grant = next(iter(service.data()["grants"]))
        self.restore()
        for action in ("apply", "reject"):
            self.denied(lambda: service.proposal_action(old_proposal["id"], {"expectedVersion": old_proposal["version"]}, action), "not_found")
        finance = FinancialService(self.alice, self.repo, self.storage)
        self.denied(lambda: finance.create_entry({"grantId": old_grant, "kind": "expense", "amount": "10"}), "not_found")

    def test_reset_failure_and_concurrent_change_preserve_existing_data(self):
        service = self.create()
        before = service.data()
        with patch.object(self.storage, "put", side_effect=OSError("fictional storage outage")):
            with self.assertRaises(OSError): self.restore()
        self.assertEqual(service.data(), before)
        original_put = self.storage.put
        first = True
        def competing_write(*args):
            nonlocal first
            original_put(*args)
            if first:
                first = False
                self.repo.mutate(service.org_id, lambda data: data["organisation"].update(name="Concurrent edit"))
        with patch.object(self.storage, "put", side_effect=competing_write):
            self.denied(lambda: self.restore(), "stale")
        self.assertEqual(service.data()["organisation"]["name"], "Concurrent edit")
        self.assertEqual(set(service.data()["grants"]), set(before["grants"]))

    def test_reset_preserves_daily_agent_run_accounting_and_stale_worker_fence(self):
        service = self.create()
        jobs = [service.create_job() for _ in range(30)]
        guarded = _GuardedRepository(self.repo, service.org_id, jobs[0]["id"], "old-token", 1)
        self.restore()
        self.assertEqual(service.data()["jobs"], {job["id"]: job for job in jobs})
        self.denied(lambda: service.create_job(), "job_limit")
        with self.assertRaises(RunStopped):
            guarded.read(service.org_id)

    def test_request_repository_denies_cross_workspace_reads_and_writes(self):
        self.create()
        self.create(self.bob)
        bounded = request_repository(self.alice, self.repo)
        self.denied(lambda: bounded.read(self.bob["organisationId"]), "forbidden")
        self.denied(lambda: bounded.mutate(self.bob["organisationId"], lambda data: data.clear()), "forbidden")
        self.restore()
        self.denied(lambda: bounded.read(self.alice["organisationId"]), "stale")
        self.denied(lambda: bounded.mutate(self.alice["organisationId"], lambda data: data.clear()), "stale")

    def test_inflight_new_grant_cannot_commit_after_another_tab_restores_demo(self):
        self.create()
        from grantthread.finance_service import parse_amount
        def restoring_parse(value):
            self.restore()
            return parse_amount(value)
        with patch("grantthread.finance_service.parse_amount", side_effect=restoring_parse):
            self.denied(lambda: dispatch("POST", "/api/financials/grants", {
                "name": "Old tab's new grant", "funderName": "Fictional funder", "currency": "EUR", "award": "100"},
                self.alice, self.repo, self.storage), "stale")
        self.assertEqual(len(self.repo.read(self.alice["organisationId"])["grants"]), 3)

    def test_inflight_bank_import_cannot_enter_a_freshly_restored_demo(self):
        self.create()
        def restoring_parse(raw):
            self.restore()
            return {"recognized": True, "textPages": ["Fictional statement"], "rows": []}
        with patch("grantthread.finance_io.parse_bank_pdf", side_effect=restoring_parse):
            self.denied(lambda: dispatch("POST", "/api/financials/imports", {
                "grantId": "demo1-digital-belonging", "name": "fictional.pdf", "kind": "bank",
                "contentBase64": base64.b64encode(b"%PDF-fictional-parser-fixture").decode()},
                self.alice, self.repo, self.storage), "stale")
        self.assertFalse(self.repo.read(self.alice["organisationId"]).get("financeImports"))

    def test_namespaced_fixture_retains_explicit_simulated_response_history(self):
        service = self.create()
        result = service.response_estimate({"grantId": "demo1-digital-belonging", "submittedDate": "2026-09-01"})
        self.assertEqual(result["sampleCount"], 12)
        self.assertTrue(result["simulated"])

    def test_public_health_advertises_signup_without_repository_access(self):
        with patch.dict(os.environ, {"GRANTTHREAD_MODE": "aws"}), patch("grantthread.lambda_handler.get_repository") as repo:
            response = handler({"rawPath": "/api/health", "requestContext": {"http": {"method": "GET"}}}, None)
        self.assertEqual(response["statusCode"], 200)
        self.assertTrue(json.loads(response["body"])["publicDemoSignup"])
        repo.assert_not_called()


if __name__ == "__main__":
    unittest.main()
