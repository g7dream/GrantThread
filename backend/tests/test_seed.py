"""Startup seeding preserves existing fictional records and their immutable source bytes."""
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from grantthread.errors import DomainError
from grantthread.repository import SQLiteRepository
from grantthread.seed import make_seed, seed_all
from grantthread.storage import LocalStorage


class SeedPreservation(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = SQLiteRepository(Path(self.temp.name) / 'grantthread.sqlite3')
        self.storage = LocalStorage(self.temp.name)

    def changed_source(self):
        data = self.repo.read('brightpath')
        key = data['evidence']['invoice-venue']['objectKey']
        raw = b'Fictional retained source from an earlier workspace version.'
        self.storage.put(key, raw, 'text/plain')
        def revise(current):
            current['grants']['digital-belonging']['name'] = 'Fictional retained grant'
            current['evidence']['invoice-venue'].update(sha256=hashlib.sha256(raw).hexdigest(), size=len(raw))
        self.repo.mutate('brightpath', revise)
        return key, raw, self.repo.read('brightpath')

    def test_repeated_startup_writes_neither_existing_records_nor_source_files(self):
        seed_all(self.repo, self.storage)
        key, raw, expected = self.changed_source()
        with patch.object(self.storage, 'put', wraps=self.storage.put) as put_source, \
             patch.object(self.repo, 'put_initial', wraps=self.repo.put_initial) as put_record:
            seed_all(self.repo, self.storage)
        put_source.assert_not_called()
        put_record.assert_not_called()
        self.assertEqual(self.repo.read('brightpath'), expected)
        self.assertEqual(self.storage.get(key), raw)
        with patch('grantthread.seed.get_storage') as storage_factory:
            seed_all(self.repo)
        storage_factory.assert_not_called()

    def test_partial_seed_creates_only_missing_organisation(self):
        seeds = make_seed(self.storage)
        self.repo.put_initial('brightpath', seeds['brightpath'])
        key, raw, expected = self.changed_source()
        with patch.object(self.storage, 'put', wraps=self.storage.put) as put_source, \
             patch.object(self.repo, 'put_initial', wraps=self.repo.put_initial) as put_record:
            seed_all(self.repo, self.storage)
        self.assertTrue(put_source.call_args_list)
        self.assertTrue(all(call.args[0].startswith('harbour/') for call in put_source.call_args_list))
        self.assertEqual([call.args[0] for call in put_record.call_args_list], ['harbour'])
        self.assertEqual(self.repo.read('brightpath'), expected)
        self.assertEqual(self.storage.get(key), raw)
        self.assertEqual(self.repo.read('harbour'), seeds['harbour'])

    def test_explicit_overwrite_still_resets_records_and_seed_source_files(self):
        seed_all(self.repo, self.storage)
        key, changed, _ = self.changed_source()
        with patch.object(self.storage, 'put', wraps=self.storage.put) as put_source:
            seed_all(self.repo, self.storage, overwrite=True)
        self.assertEqual(self.repo.read('brightpath'), make_seed()['brightpath'])
        restored = self.storage.get(key)
        self.assertNotEqual(restored, changed)
        self.assertEqual(hashlib.sha256(restored).hexdigest(), self.repo.read('brightpath')['evidence']['invoice-venue']['sha256'])
        self.assertEqual({call.args[0].split('/')[0] for call in put_source.call_args_list}, {'brightpath', 'harbour'})

    def test_read_failures_are_not_misread_as_missing_workspaces(self):
        for error in [DomainError('Fictional outage', 'not_found', 503),
                      DomainError('Fictional forbidden request', 'forbidden', 404), OSError('Fictional disk failure')]:
            with self.subTest(error=error), patch.object(self.repo, 'read', side_effect=error), \
                 patch.object(self.storage, 'put') as put_source, patch.object(self.repo, 'put_initial') as put_record:
                with self.assertRaises(type(error)) as caught:
                    seed_all(self.repo, self.storage)
                self.assertIs(caught.exception, error)
                put_source.assert_not_called()
                put_record.assert_not_called()

    def test_later_read_failure_stops_before_writing_an_earlier_missing_workspace(self):
        missing = DomainError('Fictional absent workspace', 'not_found', 404)
        unavailable = DomainError('Fictional repository outage', 'unavailable', 503)
        with patch.object(self.repo, 'read', side_effect=[missing, unavailable]), \
             patch.object(self.storage, 'put') as put_source, patch.object(self.repo, 'put_initial') as put_record:
            with self.assertRaises(DomainError) as caught:
                seed_all(self.repo, self.storage)
        self.assertIs(caught.exception, unavailable)
        put_source.assert_not_called()
        put_record.assert_not_called()


if __name__ == '__main__':
    unittest.main()
