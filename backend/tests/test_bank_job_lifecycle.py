"""Bank queue lifecycle integration tests using fictional PDFs and no model calls."""
import base64
import copy
import io
import os
import sys
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from grantthread.api import dispatch
from grantthread.errors import DomainError
from grantthread.finance_service import FinancialService
from grantthread.repository import SQLiteRepository
from grantthread.seed import IDENTITIES, seed_all
from grantthread.service import Service, now
from grantthread.storage import LocalStorage
from grantthread.worker import RunStopped, _claim, _GuardedRepository


class BankJobLifecycle(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        environment = patch.dict(os.environ, {'GRANTTHREAD_MODE': 'local', 'GRANTTHREAD_DATA_DIR': self.directory.name,
                                              'BEDROCK_MODEL_ID': '', 'AWS_REGION': ''})
        environment.start()
        self.addCleanup(environment.stop)
        # Exercise queue creation without a configured provider or any model request.
        self.configured = patch('grantthread.worker.agent_configured', return_value=True)
        self.configured.start()
        self.addCleanup(self.configured.stop)
        self.repository, self.storage = SQLiteRepository(), LocalStorage()
        seed_all(self.repository, self.storage)
        self.identity = copy.deepcopy(IDENTITIES['brightpath'])
        self.other_identity = {**self.identity, 'id': 'fictional-second-grantee'}
        self.service = FinancialService(self.identity, self.repository, self.storage)
        self.other = FinancialService(self.other_identity, self.repository, self.storage)

    def body(self, label='bank'):
        from reportlab.pdfgen import canvas
        output = io.BytesIO()
        page = canvas.Canvas(output, invariant=True)
        page.drawString(40, 760, f'FICTIONAL BANK STATEMENT TEST: {label}')
        page.drawString(40, 730, '01.09.2026 Fictional supplies INV-01 Debit 10.00 RON')
        page.save()
        return {'name': f'{label}.pdf', 'kind': 'bank', 'grantId': 'digital-belonging',
                'contentBase64': base64.b64encode(output.getvalue()).decode()}

    def upload(self, label='bank'):
        result = self.service.upload_import(self.body(label))
        self.assertEqual(result['status'], 'needs_ai')
        return result

    def data(self):
        return self.repository.read('brightpath')

    def assert_error(self, action, code, status):
        with self.assertRaises(DomainError) as caught:
            action()
        self.assertEqual((caught.exception.code, caught.exception.status), (code, status))

    def seed_completed_runs(self, identity, count=30):
        def seed(data):
            for index in range(count):
                key = f'fictional-{identity["id"]}-{index}'
                data['jobs'][key] = {'id': key, 'actorId': identity['id'], 'actor': copy.deepcopy(identity),
                                     'organisationId': 'brightpath', 'inputVersion': data['factVersion'],
                                     'status': 'completed', 'createdAt': now(), 'finishedAt': now()}
        self.repository.mutate('brightpath', seed)

    def test_same_import_returns_existing_queued_or_running_job_without_reassigning_actor(self):
        item = self.upload()
        original = self.service.create_bank_job(item['id'])
        self.assertEqual(self.other.create_bank_job(item['id']), original)
        claimed, token = _claim(self.repository, 'brightpath', original['id'])
        self.assertEqual(self.other.create_bank_job(item['id']), claimed)
        after = self.data()
        self.assertEqual(len(after['jobs']), 1)
        self.assertEqual(after['jobs'][original['id']]['actor'], self.identity)
        self.assertEqual(after['jobs'][original['id']]['claimToken'], token)

    def test_stale_inputs_import_versions_and_expired_leases_allow_fenced_retry(self):
        for reason in ('facts', 'import_version', 'lease', 'missing_lease', 'parsed'):
            with self.subTest(reason=reason):
                item = self.upload(reason)
                original = self.service.create_bank_job(item['id'])
                claimed, token = _claim(self.repository, 'brightpath', original['id'])
                guard = _GuardedRepository(self.repository, 'brightpath', original['id'], token, claimed['inputVersion'])
                def invalidate(data):
                    if reason == 'facts': data['factVersion'] += 1
                    if reason == 'import_version': data['financeImports'][item['id']]['version'] += 1
                    if reason == 'lease': data['jobs'][original['id']]['leaseExpiresAt'] = time.time() - 1
                    if reason == 'missing_lease': data['jobs'][original['id']].pop('leaseExpiresAt')
                    if reason == 'parsed': data['financeImports'][item['id']]['status'] = 'parsed'
                self.repository.mutate('brightpath', invalidate)
                fresh = self.service.create_bank_job(item['id'])
                after = self.data()
                old = after['jobs'][original['id']]
                self.assertNotEqual(fresh['id'], original['id'])
                self.assertEqual(old['status'], 'failed')
                self.assertIn('finishedAt', old)
                self.assertNotIn('claimToken', old)
                self.assertNotIn('leaseExpiresAt', old)
                self.assertEqual(fresh['inputVersion'], after['factVersion'])
                self.assertEqual(fresh['importVersion'], after['financeImports'][item['id']]['version'])
                self.assertEqual(after['financeImports'][item['id']]['jobId'], fresh['id'])
                with self.assertRaises(RunStopped):
                    guard.mutate('brightpath', lambda data: data.update(corrupted=True))
                self.assertNotIn('corrupted', self.data())
                self.assertIsNone(_claim(self.repository, 'brightpath', original['id']))

    def test_valid_reconciliation_blocks_bank_run_without_changing_its_kind_or_scope(self):
        item = self.upload()
        reconciliation = Service(self.identity, self.repository, self.storage).create_job('digital-belonging')
        before = self.data()
        self.assert_error(lambda: self.service.create_bank_job(item['id']), 'job_in_progress', 409)
        self.assertEqual(self.data(), before)
        self.assertNotIn('kind', self.data()['jobs'][reconciliation['id']])
        self.assertNotIn('importId', self.data()['jobs'][reconciliation['id']])

    def test_valid_other_bank_run_blocks_same_actor_but_other_actor_can_queue(self):
        first, second = self.upload('first'), self.upload('second')
        original = self.service.create_bank_job(first['id'])
        before = self.data()
        self.assert_error(lambda: self.service.create_bank_job(second['id']), 'job_in_progress', 409)
        self.assertEqual(self.data(), before)
        separate = self.other.create_bank_job(second['id'])
        self.assertEqual(separate['actor'], self.other_identity)
        self.assertEqual(self.data()['jobs'][original['id']], original)

    def test_expired_reconciliation_allows_separate_bank_job_without_repurposing_it(self):
        item = self.upload()
        original = Service(self.identity, self.repository, self.storage).create_job('digital-belonging')
        _claim(self.repository, 'brightpath', original['id'])
        self.repository.mutate('brightpath', lambda data: data['jobs'][original['id']].update(leaseExpiresAt=time.time() - 1))
        bank = self.service.create_bank_job(item['id'])
        old = self.data()['jobs'][original['id']]
        self.assertNotEqual(bank['id'], original['id'])
        self.assertEqual(old['status'], 'failed')
        self.assertNotIn('kind', old)
        self.assertNotIn('importId', old)
        self.assertEqual(old['actor'], original['actor'])

    def test_new_upload_replaces_stale_queued_run_with_current_import_scope(self):
        first = self.upload('earlier-source')
        original = self.service.create_bank_job(first['id'])
        with patch('grantthread.api.dispatch_job', side_effect=lambda service, job: job) as dispatch_mock:
            result = dispatch('POST', '/api/financials/imports', self.body('new-source'), self.identity, self.repository, self.storage)
            dispatch_mock.assert_called_once()
        after = self.data()
        self.assertEqual(after['jobs'][original['id']]['status'], 'failed')
        self.assertEqual(after['jobs'][original['id']]['importId'], first['id'])
        self.assertEqual(result['job']['importId'], result['id'])
        self.assertEqual(result['job']['inputVersion'], after['factVersion'])
        self.assertEqual(result['job']['status'], 'queued')
        self.assertNotEqual(result['job']['id'], original['id'])

    def test_daily_limit_is_per_actor_and_same_import_reuse_does_not_spend_a_run(self):
        item = self.upload()
        self.seed_completed_runs(self.other_identity)
        bank = self.service.create_bank_job(item['id'])
        self.seed_completed_runs(self.identity, count=29)
        self.assertEqual(self.service.create_bank_job(item['id']), bank)
        self.repository.mutate('brightpath', lambda data: data['jobs'][bank['id']].update(status='completed'))
        before = self.data()
        self.assert_error(lambda: self.service.create_bank_job(item['id']), 'job_limit', 429)
        self.assertEqual(self.data(), before)

    def test_successful_upload_returns_warning_when_daily_limit_prevents_scheduling(self):
        self.seed_completed_runs(self.identity)
        body = self.body('saved-despite-quota')
        with patch('grantthread.api.dispatch_job') as dispatch_mock:
            result = dispatch('POST', '/api/financials/imports', body, self.identity, self.repository, self.storage)
            dispatch_mock.assert_not_called()
        self.assertEqual(result['status'], 'needs_ai')
        self.assertIn('Daily agent run limit', result['jobWarning'])
        self.assertNotIn('job', result)
        stored = self.data()['financeImports'][result['id']]
        self.assertEqual(self.storage.get(stored['objectKey']), base64.b64decode(body['contentBase64']))
        self.assertIn(b'FICTIONAL BANK STATEMENT', self.storage.get(stored['parsedKey']))
        self.assertEqual(stored['rows'], [])
        with patch('grantthread.api.dispatch_job') as dispatch_mock:
            duplicate = dispatch('POST', '/api/financials/imports', body, self.identity, self.repository, self.storage)
            dispatch_mock.assert_not_called()
        self.assertTrue(duplicate['alreadyImported'])
        self.assertEqual(duplicate['id'], result['id'])
        self.assertEqual(len(self.data()['financeImports']), 1)

    def test_concurrent_same_import_requests_create_one_immutable_job(self):
        item = self.upload()
        barrier = Barrier(2)
        def enqueue(service):
            barrier.wait(timeout=5)
            return service.create_bank_job(item['id'])
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(enqueue, service) for service in (self.service, self.other)]
            jobs = [future.result(timeout=10) for future in futures]
        self.assertEqual(jobs[0], jobs[1])
        self.assertEqual(len(self.data()['jobs']), 1)

    def test_concurrent_different_imports_for_one_actor_allow_only_one_job(self):
        first, second = self.upload('first'), self.upload('second')
        barrier = Barrier(2)
        def enqueue(key):
            barrier.wait(timeout=5)
            try:
                return self.service.create_bank_job(key)
            except DomainError as exc:
                return exc.code
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(enqueue, item['id']) for item in (first, second)]
            results = [future.result(timeout=10) for future in futures]
        self.assertEqual(sum(isinstance(result, dict) for result in results), 1)
        self.assertIn('job_in_progress', results)
        self.assertEqual(len(self.data()['jobs']), 1)

    def test_unavailable_run_is_terminal_and_import_remains_reviewable(self):
        item = self.upload()
        with patch('grantthread.worker.agent_configured', return_value=False):
            result = self.service.create_bank_job(item['id'])
        self.assertEqual(result['status'], 'unavailable')
        self.assertIn('finishedAt', result)
        self.assertEqual(self.data()['financeImports'][item['id']]['status'], 'needs_ai')
        self.assertIsNone(_claim(self.repository, 'brightpath', result['id']))

    def test_foreign_workspace_and_funder_cannot_queue_bank_import(self):
        item = self.upload()
        foreign = FinancialService(IDENTITIES['harbour'], self.repository, self.storage)
        funder = FinancialService(IDENTITIES['northstar'], self.repository, self.storage)
        self.assert_error(lambda: foreign.create_bank_job(item['id']), 'not_found', 404)
        self.assert_error(lambda: funder.create_bank_job(item['id']), 'forbidden', 403)
        self.assertEqual(self.data()['jobs'], {})


if __name__ == '__main__':
    unittest.main()
