"""Offline SDK/worker containment checks. Scripted model fixtures are NEVER product runs."""
import asyncio
import copy
import json
import os
import sys
import time
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from grantthread.worker import _build_agent, _claim, _GuardedRepository, RunStopped, run_job
from strands.models.model import Model


class MemoryRepository:
    def __init__(self):
        self.data = {"factVersion": 1, "version": 1, "jobs": {"job": {
            "id": "job", "status": "queued", "inputVersion": 1, "organisationId": "org",
            "actorId": "subject", "actor": {"id": "subject", "organisationId": "org", "role": "grantee"},
            "toolEvents": []}}}

    def read(self, _):
        return copy.deepcopy(self.data)

    def mutate(self, _, callback):
        data = copy.deepcopy(self.data)
        result = callback(data)
        data["version"] += 1
        self.data = data
        return copy.deepcopy(result)


class ScriptedModel(Model):
    """Protocol fixture for exercising real Strands dispatch; no network or model claims."""
    calls = []

    def __init__(self, **_):
        self.turn = 0

    def update_config(self, **_):
        pass

    def get_config(self):
        return {"model_id": "OFFLINE-TEST-FIXTURE"}

    async def structured_output(self, *args, **kwargs):
        raise AssertionError("No additional structured-output tool is allowed")
        yield

    async def stream(self, *args, **kwargs):
        yield {"messageStart": {"role": "assistant"}}
        if self.turn == 0:
            for index, (name, inputs) in enumerate(self.calls):
                yield {"contentBlockStart": {"start": {"toolUse": {"toolUseId": f"call-{index}", "name": name}}}}
                yield {"contentBlockDelta": {"delta": {"toolUse": {"input": json.dumps(inputs)}}}}
                yield {"contentBlockStop": {}}
            yield {"messageStop": {"stopReason": "tool_use"}}
        else:
            yield {"contentBlockDelta": {"delta": {"text": "Offline fixture finished."}}}
            yield {"contentBlockStop": {}}
            yield {"messageStop": {"stopReason": "end_turn"}}
        self.turn += 1
        yield {"metadata": {"usage": {"inputTokens": 1, "outputTokens": 1, "totalTokens": 2},
                            "metrics": {"latencyMs": 1}}}


class ScopedService:
    def __init__(self):
        self.executed = 0

    def list_requirements(self, _):
        self.executed += 1
        return [{"id": "configured", "grantId": "grant"}]

    def save_review_proposal(self, _):
        raise AssertionError("Malformed proposals must fail before service persistence")


class WorkerChecks(unittest.TestCase):
    def setUp(self):
        self.repository = MemoryRepository()
        self.job, self.token = _claim(self.repository, "org", "job")
        self.guarded = _GuardedRepository(self.repository, "org", "job", self.token, 1)

    def test_duplicate_delivery_and_expired_lease_fence(self):
        self.assertEqual(_claim(self.repository, "org", "job"), "busy")
        self.repository.data["jobs"]["job"]["leaseExpiresAt"] = time.time() - 1
        second_job, second_token = _claim(self.repository, "org", "job")
        self.assertNotEqual(second_token, self.token)
        self.assertEqual(second_job["attempts"], 2)
        with self.assertRaises(RunStopped):
            self.guarded.mutate("org", lambda data: data.update(corrupted=True))
        self.assertNotIn("corrupted", self.repository.data)

    def test_scope_and_stale_inputs_reject_writes(self):
        with self.assertRaises(RunStopped):
            self.guarded.read("another-organisation")
        self.repository.data["factVersion"] = 2
        with self.assertRaises(RunStopped):
            self.guarded.mutate("org", lambda data: data.update(corrupted=True))
        self.assertNotIn("corrupted", self.repository.data)

    def invoke_fixture(self, calls):
        service = ScopedService()
        with patch.dict(os.environ, {"BEDROCK_MODEL_ID": "OFFLINE-TEST-FIXTURE", "AWS_REGION": "eu-west-1"}), \
                patch("strands.models.BedrockModel", ScriptedModel):
            ScriptedModel.calls = calls
            agent, state = _build_agent(service, self.job, self.guarded, self.repository, "org", "job", self.token)
            self.assertEqual(len(agent.tool_registry.registry), 7)
            asyncio.run(agent.invoke_async("Offline protocol fixture only."))
        return service, state

    def test_sdk_enforces_eight_tool_limit_and_records_real_dispatch(self):
        service, state = self.invoke_fixture([("list_requirements", {})] * 9)
        self.assertEqual(service.executed, 8)
        self.assertEqual(state["tools"], 8)
        self.assertEqual(len(self.repository.data["jobs"]["job"]["toolEvents"]), 8)
        self.assertIsNotNone(state["stopped"])

    def test_sdk_cannot_save_financial_operation(self):
        _, state = self.invoke_fixture([("save_review_proposal", {"proposal": {
            "kind": "allocation", "expenseId": "venue", "amountMinor": 100000}})])
        self.assertEqual(state["successes"], 0)
        self.assertEqual(self.repository.data["jobs"]["job"]["toolEvents"][0]["status"], "error")


class WorkerServiceIntegration(unittest.TestCase):
    def setUp(self):
        from grantthread.repository import SQLiteRepository
        from grantthread.storage import LocalStorage
        from grantthread.seed import seed_all
        from grantthread.service import Service
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.environment = patch.dict(os.environ, {"GRANTTHREAD_MODE": "local", "GRANTTHREAD_DATA_DIR": self.directory.name,
                                                   "BEDROCK_MODEL_ID": "OFFLINE-TEST-FIXTURE", "AWS_REGION": "eu-west-1"})
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.repository = SQLiteRepository()
        self.storage = LocalStorage()
        seed_all(self.repository, self.storage)
        self.identity = {"id": "test-subject", "organisationId": "brightpath", "role": "grantee",
                         "name": "Offline test", "organisationName": "Bright Path Lab"}
        self.service = Service(self.identity, self.repository, self.storage)

    def test_unconfigured_run_is_unavailable_without_tool_events(self):
        job = self.service.create_job()
        with patch.dict(os.environ, {"BEDROCK_MODEL_ID": ""}):
            run_job("brightpath", job["id"])
        result = self.service.get_job(job["id"])
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["toolEvents"], [])

    def test_stale_queued_job_does_not_invoke_model(self):
        job = self.service.create_job()
        self.repository.mutate("brightpath", lambda data: data.update(factVersion=2))
        with patch("strands.models.BedrockModel", side_effect=AssertionError("must not invoke")):
            run_job("brightpath", job["id"])
        self.assertEqual(self.service.get_job(job["id"])["status"], "failed")

    def test_new_input_replaces_stale_active_job_and_fences_old_worker(self):
        prior = self.service.create_job("digital-belonging")
        _, claim_token = _claim(self.repository, "brightpath", prior["id"])
        old_worker = _GuardedRepository(self.repository, "brightpath", prior["id"], claim_token, prior["inputVersion"])
        self.repository.mutate("brightpath", lambda data: data.update(factVersion=data["factVersion"] + 1))
        fresh = self.service.create_job("digital-belonging")
        self.assertNotEqual(fresh["id"], prior["id"])
        self.assertEqual(fresh["inputVersion"], prior["inputVersion"] + 1)
        self.assertEqual(fresh["status"], "queued")
        previous = self.service.get_job(prior["id"])
        self.assertEqual(previous["status"], "failed")
        self.assertNotIn("claimToken", previous)
        self.assertNotIn("leaseExpiresAt", previous)
        with self.assertRaises(RunStopped):
            old_worker.mutate("brightpath", lambda data: data.update(corrupted=True))
        self.assertNotIn("corrupted", self.repository.read("brightpath"))

    def test_expired_active_lease_allows_fresh_job(self):
        prior = self.service.create_job("digital-belonging")
        _claim(self.repository, "brightpath", prior["id"])
        self.repository.mutate("brightpath", lambda data: data["jobs"][prior["id"]].update(leaseExpiresAt=time.time() - 1))
        fresh = self.service.create_job("digital-belonging")
        self.assertNotEqual(fresh["id"], prior["id"])
        self.assertEqual(fresh["inputVersion"], prior["inputVersion"])
        self.assertEqual(self.service.get_job(prior["id"])["status"], "failed")
        self.assertEqual(self.service.create_job("digital-belonging")["id"], fresh["id"])

    def test_resume_uses_same_actor_and_affected_grant(self):
        from grantthread.service import Service
        own = self.service.create_job("digital-belonging")
        self.service.update_job(own["id"], status="waiting_input")
        other_actor = Service({**self.identity, "id": "another-subject"}, self.repository, self.storage)
        other = other_actor.create_job("digital-belonging")
        other_actor.update_job(other["id"], status="waiting_input")
        fresh = self.service.create_job("digital-belonging")
        self.assertEqual(fresh["resumesJobId"], own["id"])
        self.service.update_job(fresh["id"], status="completed")
        unrelated = self.service.create_job("community-makers")
        self.assertIsNone(unrelated["resumesJobId"])

    def test_model_timeout_preserves_confirmed_ledger(self):
        before = self.repository.read("brightpath")["expenses"]
        job = self.service.create_job()
        class DelayedProvider:
            async def invoke_async(self, _):
                await asyncio.sleep(1)
        with patch("grantthread.worker.MAX_SECONDS", 0.05), \
                patch("grantthread.worker._build_agent", return_value=(DelayedProvider(), {})):
            run_job("brightpath", job["id"])
        saved = self.service.get_job(job["id"])
        self.assertEqual(saved["status"], "failed")
        self.assertIn("runtime limit", saved["message"])
        self.assertEqual(self.repository.read("brightpath")["expenses"], before)
        self.assertEqual(saved["toolEvents"], [])

    def test_sdk_service_draft_and_proposal_keep_confirmed_facts_unchanged(self):
        text = "SYNTHETIC OFFLINE TEST. Printing payment proof. EUR 600.00. Transfer received 2026-08-23."
        raw = text.encode("utf-8")
        upload = self.service.upload_intent({"name": "offline-payment.txt", "kind": "payment_proof", "expenseId": "printing",
                                             "contentType": "text/plain", "size": len(raw), "grantIds": ["digital-belonging"]})
        self.service.receive_upload(upload["id"], raw)
        evidence_id = self.service.complete_upload(upload["id"])["evidence"]["id"]
        before = self.repository.read("brightpath")
        self.assertEqual(before["evidence"][evidence_id]["status"], "pending")
        job = self.service.create_job("digital-belonging", evidence_id)
        ScriptedModel.calls = [
            ("read_evidence", {"evidence_id": evidence_id}),
            ("suggest_evidence_links", {"evidence_id": evidence_id, "grant_ids": ["digital-belonging"],
             "reason": "OFFLINE TEST source candidate", "source_refs": [{"evidenceId": evidence_id, "version": 1, "page": 1, "excerpt": text[:50]}]}),
            ("calculate_allocations", {"grant_id": "digital-belonging"}),
            ("assemble_report_draft", {"grant_id": "digital-belonging"}),
        ]
        with patch("strands.models.BedrockModel", ScriptedModel):
            run_job("brightpath", job["id"])
            run_job("brightpath", job["id"])
        after = self.repository.read("brightpath")
        saved = after["jobs"][job["id"]]
        self.assertEqual(saved["status"], "waiting_input", saved["message"])
        self.assertEqual(len(saved["toolEvents"]), 4)
        self.assertTrue(all(event["status"] == "success" for event in saved["toolEvents"]))
        self.assertEqual(len(saved["proposalIds"]), 1)
        self.assertEqual(len(saved["reportIds"]), 1)
        for key in ("expenses", "grants", "evidence", "factVersion", "snapshots"):
            self.assertEqual(before[key], after[key], key)


if __name__ == "__main__":
    unittest.main(verbosity=2)
