"""Recovery tests use disposable fictional data and never open the user's workspace."""
import hashlib
import json
import os
import sqlite3
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))
sys.path.insert(0, str(ROOT / 'scripts'))
from local_workspace import backup, restore
from grantthread.auth import local_login
from grantthread.finance_service import FinancialService
from grantthread.repository import SQLiteRepository
from grantthread.seed import IDENTITIES, seed_all
from grantthread.service import Service
from grantthread.storage import LocalStorage


class LocalWorkspaceRecovery(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data_dir = self.root / 'original'
        self.env = patch.dict(os.environ, {'GRANTTHREAD_MODE': 'local', 'GRANTTHREAD_DATA_DIR': str(self.data_dir), 'BEDROCK_MODEL_ID': ''})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.repo = SQLiteRepository()
        self.storage = LocalStorage()
        seed_all(self.repo, self.storage)
        self.service = Service(IDENTITIES['brightpath'], self.repo, self.storage)
        self.archive = self.root / 'backup.zip'

    def rewrite(self, edit):
        with zipfile.ZipFile(self.archive) as z:
            files = {name: z.read(name) for name in z.namelist()}
        edit(files)
        with zipfile.ZipFile(self.archive, 'w') as z:
            for name, raw in files.items():
                z.writestr(name, raw)

    def change_records_with_valid_checksums(self, edit):
        def alter(files):
            records = json.loads(files['records.json'])
            edit(records, files)
            files['records.json'] = json.dumps(records).encode()
            manifest = json.loads(files['manifest.json'])
            manifest['files'] = {name: {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
                                 for name, raw in files.items() if name != 'manifest.json'}
            files['manifest.json'] = json.dumps(manifest).encode()
        self.rewrite(alter)

    def test_restores_exact_financial_data_and_source_bytes_without_sessions(self):
        finance = FinancialService(IDENTITIES['brightpath'], self.repo, self.storage)
        grant = finance.create_grant({'name': 'Fictional recovery grant', 'funderName': 'Demo funder', 'currency': 'CAD', 'award': '1000'})
        finance.add_receipt({'grantId': grant['id'], 'receivedDate': '2026-04-01', 'sourceCurrency': 'RON', 'sourceAmount': '100', 'rate': '0.254321987654321'})
        token = local_login(self.repo, 'brightpath')['token']
        orphan = self.storage.root / 'unreferenced-secret.txt'
        orphan.write_text('not part of a workspace record')
        expected = self.repo.read('brightpath')
        result = backup(self.data_dir, self.archive)
        self.assertEqual(result['organisations'], 2)
        with zipfile.ZipFile(self.archive) as z:
            self.assertFalse(any('sqlite' in name or 'sessions' in name or 'unreferenced-secret' in name for name in z.namelist()))
            self.assertNotIn(token.encode(), z.read('records.json'))
            self.assertNotIn(hashlib.sha256(token.encode()).hexdigest().encode(), z.read('records.json'))
        target = self.root / 'restored'
        restore(self.archive, target)
        restored_repo = SQLiteRepository(target / 'grantthread.sqlite3')
        self.assertEqual(restored_repo.read('brightpath'), expected)
        with restored_repo.connect() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM sessions').fetchone()[0], 0)
        restored = Service(IDENTITIES['brightpath'], restored_repo, LocalStorage(target))
        self.assertEqual(restored.evidence_bytes('invoice-venue'), self.service.evidence_bytes('invoice-venue'))
        self.assertEqual(restored.read_evidence('invoice-venue'), self.service.read_evidence('invoice-venue'))

    def test_checksum_failure_never_creates_restore_target(self):
        backup(self.data_dir, self.archive)
        self.rewrite(lambda files: files.__setitem__('records.json', b'[]'))
        target = self.root / 'invalid'
        with self.assertRaisesRegex(ValueError, 'checksum'):
            restore(self.archive, target)
        self.assertFalse(target.exists())

    def test_unlisted_and_traversal_entries_are_rejected(self):
        backup(self.data_dir, self.archive)
        self.rewrite(lambda files: files.__setitem__('../outside.txt', b'bad'))
        target = self.root / 'invalid'
        with self.assertRaisesRegex(ValueError, 'manifest'):
            restore(self.archive, target)
        self.assertFalse(target.exists())
        self.assertFalse((self.root / 'outside.txt').exists())

    def test_manifest_cannot_authorize_a_cross_organisation_source_path(self):
        backup(self.data_dir, self.archive)
        def alter(files):
            records = json.loads(files['records.json'])
            records[0]['data']['evidence']['invoice-venue']['objectKey'] = '../escape.txt'
            files['records.json'] = json.dumps(records).encode()
            manifest = json.loads(files['manifest.json'])
            manifest['files']['records.json'] = {'size': len(files['records.json']), 'sha256': hashlib.sha256(files['records.json']).hexdigest()}
            files['manifest.json'] = json.dumps(manifest).encode()
        self.rewrite(alter)
        with self.assertRaisesRegex(ValueError, 'outside its organisation'):
            restore(self.archive, self.root / 'invalid')

    def test_existing_backup_and_restore_destinations_are_preserved(self):
        backup(self.data_dir, self.archive)
        original_bytes = self.archive.read_bytes()
        with self.assertRaisesRegex(ValueError, 'already exists'):
            backup(self.data_dir, self.archive)
        self.assertEqual(self.archive.read_bytes(), original_bytes)
        before = self.repo.read('brightpath')
        with self.assertRaisesRegex(ValueError, 'new directory'):
            restore(self.archive, self.data_dir)
        self.assertEqual(self.repo.read('brightpath'), before)

    def test_missing_or_changed_referenced_object_stops_backup(self):
        path = self.storage.path(self.repo.read('brightpath')['evidence']['invoice-venue']['objectKey'])
        path.write_bytes(b'different')
        with self.assertRaisesRegex(ValueError, 'checksum'):
            backup(self.data_dir, self.archive)
        self.assertFalse(self.archive.exists())
        path.unlink()
        with self.assertRaisesRegex(ValueError, 'missing'):
            backup(self.data_dir, self.archive)
        self.assertFalse(self.archive.exists())

    def test_active_jobs_block_backup_and_pending_uploads_expire_on_restore(self):
        self.repo.mutate('brightpath', lambda data: data['jobs'].update({'test': {'status': 'running'}}))
        with self.assertRaisesRegex(ValueError, 'jobs'):
            backup(self.data_dir, self.archive)
        self.repo.mutate('brightpath', lambda data: data['jobs'].clear())
        upload = self.service.upload_intent({'name': 'pending.txt', 'size': 4, 'grantIds': ['digital-belonging'], 'kind': 'invoice'})
        self.service.receive_upload(upload['id'], b'demo')
        backup(self.data_dir, self.archive)
        with zipfile.ZipFile(self.archive) as z:
            self.assertFalse(any('/incoming/' in name for name in z.namelist()))
        target = self.root / 'restored'
        restore(self.archive, target)
        result = SQLiteRepository(target / 'grantthread.sqlite3').read('brightpath')
        self.assertEqual(result['uploads'][upload['id']]['status'], 'expired')
        self.assertEqual(self.repo.read('brightpath')['uploads'][upload['id']]['status'], 'pending')

    def test_backup_does_not_create_database_when_directory_is_wrong(self):
        missing = self.root / 'missing'
        with self.assertRaisesRegex(ValueError, 'not found'):
            backup(missing, self.archive)
        self.assertFalse(missing.exists())

    def test_failed_restore_removes_only_its_own_stage_and_preserves_nearby_data(self):
        backup(self.data_dir, self.archive)
        before = self.repo.read('brightpath')
        unrelated = self.root / 'grantthread-restore-existing'
        unrelated.mkdir()
        sentinel = unrelated / 'keep.txt'
        sentinel.write_text('Fictional unrelated content')
        target = self.root / 'failed-restore'
        with patch('local_workspace.SQLiteRepository.put_initial', side_effect=OSError('Fictional disk write failure')):
            with self.assertRaisesRegex(OSError, 'disk write failure'):
                restore(self.archive, target)
        self.assertFalse(target.exists())
        self.assertEqual(list(self.root.glob('grantthread-restore-*')), [unrelated])
        self.assertEqual(sentinel.read_text(), 'Fictional unrelated content')
        self.assertEqual(self.repo.read('brightpath'), before)
        # A clean retry must still succeed after partial staging was removed.
        restore(self.archive, target)
        self.assertEqual(SQLiteRepository(target / 'grantthread.sqlite3').read('brightpath'), before)

    def test_case_aliases_cannot_silently_replace_a_restored_source_on_windows(self):
        backup(self.data_dir, self.archive)
        def add_alias(records, files):
            data = records[0]['data']
            copied = dict(data['evidence']['invoice-venue'])
            key = copied['objectKey']
            alias = key[:-1] + key[-1].upper()
            self.assertNotEqual(key, alias)
            raw = b'another source'
            copied.update(objectKey=alias, sha256=hashlib.sha256(raw).hexdigest())
            data['evidence']['alias'] = copied
            files['objects/' + alias] = raw
        self.change_records_with_valid_checksums(add_alias)
        target = self.root / 'invalid'
        with self.assertRaisesRegex(ValueError, 'collision'):
            restore(self.archive, target)
        self.assertFalse(target.exists())

    def test_windows_reserved_names_are_rejected_before_writing(self):
        backup(self.data_dir, self.archive)
        original = self.archive.read_bytes()
        for part in ('CON', 'nul.txt', 'name.', 'name ', 'a\x00b', 'COM1'):
            with self.subTest(part=part):
                self.archive.write_bytes(original)
                def bad_path(records, files):
                    item = records[0]['data']['evidence']['invoice-venue']
                    item['objectKey'] = 'brightpath/evidence/' + part
                self.change_records_with_valid_checksums(bad_path)
                with self.assertRaisesRegex(ValueError, 'Windows-unsafe'):
                    restore(self.archive, self.root / 'invalid')
                self.assertFalse((self.root / 'invalid').exists())

    def test_missing_or_malformed_collections_fail_before_restore(self):
        backup(self.data_dir, self.archive)
        original = self.archive.read_bytes()
        for field, invalid in (('organisation', []), ('grants', None), ('jobs', []), ('evidence', {'bad': None}), ('audit', {})):
            with self.subTest(field=field):
                self.archive.write_bytes(original)
                self.change_records_with_valid_checksums(lambda records, files: records[0]['data'].__setitem__(field, invalid))
                with self.assertRaises(ValueError):
                    restore(self.archive, self.root / 'invalid')
                self.assertFalse((self.root / 'invalid').exists())

    def test_unsupported_compression_fails_before_restore(self):
        backup(self.data_dir, self.archive)
        with zipfile.ZipFile(self.archive) as source:
            files = {name: source.read(name) for name in source.namelist()}
        with zipfile.ZipFile(self.archive, 'w', zipfile.ZIP_BZIP2) as target:
            for name, raw in files.items():
                target.writestr(name, raw)
        with self.assertRaisesRegex(ValueError, 'compression'):
            restore(self.archive, self.root / 'invalid')
        self.assertFalse((self.root / 'invalid').exists())


if __name__ == '__main__':
    unittest.main()
