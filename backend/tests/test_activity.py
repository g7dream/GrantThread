import csv
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from grantthread.api import Binary, dispatch
from grantthread.errors import DomainError
from grantthread.finance_service import FinancialService
from grantthread.repository import SQLiteRepository
from grantthread.seed import IDENTITIES, seed_all
from grantthread.service import Service
from grantthread.storage import LocalStorage


class ActivityHistory(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.env = patch.dict(os.environ, {'GRANTTHREAD_MODE': 'local', 'GRANTTHREAD_DATA_DIR': self.temp.name})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.repo, self.storage = SQLiteRepository(), LocalStorage()
        seed_all(self.repo, self.storage)
        self.service = Service(IDENTITIES['brightpath'], self.repo, self.storage)

    def record(self, action, target):
        self.repo.mutate('brightpath', lambda data: self.service.audit(data, action, target))

    def test_history_is_newest_first_and_read_only(self):
        self.record('entry_created', 'entry-first')
        self.record('entry_confirmed', 'entry-first')
        before = self.repo.read('brightpath')
        result = dispatch('GET', '/activity', {}, IDENTITIES['brightpath'], self.repo, self.storage)
        self.assertEqual([e['sequence'] for e in result['events']], [2, 1])
        self.assertEqual(result['events'][0]['action'], 'entry_confirmed')
        self.assertEqual(result['events'][0]['actorName'], 'Alex Morgan')
        self.assertFalse(result['truncated'])
        self.assertEqual(self.repo.read('brightpath'), before)

    def test_recent_history_is_bounded_but_csv_includes_older_rows(self):
        self.repo.mutate('brightpath', lambda data: data['audit'].extend(
            {'action': 'entry_created', 'targetId': str(n), 'actorId': 'legacy', 'at': '2026-04-01T00:00:00Z'} for n in range(203)))
        result = self.service.activity()
        self.assertEqual(result['total'], 203)
        self.assertEqual(len(result['events']), 200)
        self.assertTrue(result['truncated'])
        self.assertEqual(result['events'][-1]['sequence'], 4)
        self.assertNotIn('actorName', result['events'][0])
        exported = dispatch('GET', '/activity/csv', {}, IDENTITIES['brightpath'], self.repo, self.storage)
        self.assertIsInstance(exported, Binary)
        rows = list(csv.reader(io.StringIO(exported.data.decode('utf-8-sig'))))
        self.assertEqual(len(rows), 204)
        self.assertEqual(rows[1][0], '1')
        self.assertEqual(rows[-1][0], '203')

    def test_funder_cannot_read_grantee_private_history_and_other_org_has_its_own(self):
        self.record('report_prepared', 'private-report')
        for endpoint in ('/activity', '/activity/csv'):
            with self.assertRaises(DomainError) as error:
                dispatch('GET', endpoint, {}, IDENTITIES['northstar'], self.repo, self.storage)
            self.assertEqual(error.exception.status, 403)
        result = dispatch('GET', '/activity', {}, IDENTITIES['harbour'], self.repo, self.storage)
        self.assertEqual(result['events'], [])

    def test_csv_escapes_formulas_and_keeps_names_with_commas_and_newlines(self):
        self.repo.mutate('brightpath', lambda data: data['audit'].extend([
            {'actorId': 'id', 'actorName': name, 'action': 'event', 'targetId': 'entry', 'at': '2026-04-01'}
            for name in ('=1+1', ' +SUM(A1)', '@formula', '\tformula', 'Example, Name\nSecond line')]))
        rows = list(csv.reader(io.StringIO(self.service.activity_csv().decode('utf-8-sig'))))
        self.assertTrue(all(row[-1].startswith("'") for row in rows[1:5]))
        self.assertEqual(rows[5][-1], 'Example, Name\nSecond line')

    def test_financial_review_records_real_lifecycle_and_actor(self):
        finance = FinancialService(IDENTITIES['brightpath'], self.repo, self.storage)
        draft = finance.create_entry({'grantId': 'digital-belonging', 'kind': 'expense',
            'date': '2026-09-14', 'description': 'Fictional audit supplies', 'reference': 'TEST-AUDIT',
            'currency': 'EUR', 'amount': '100', 'category': '1.4 Goods and Supplies', 'conversionMode': 'same_currency'})
        edited = finance.update_entry(draft['id'], {**draft, 'amount': '120', 'expectedVersion': draft['version']})
        finance.confirm_entries({'entries': [{'id': edited['id'], 'expectedVersion': edited['version']}]})
        events = self.service.activity()['events']
        self.assertEqual([event['action'] for event in events],
            ['financial_expense_confirmed', 'financial_draft_edited', 'financial_draft_created'])
        self.assertTrue(all(event['targetId'] == draft['id'] and event['actorName'] == 'Alex Morgan' for event in events))


if __name__ == '__main__':
    unittest.main()
