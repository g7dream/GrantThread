"""Back up local records and referenced private files; restore only into a new directory.

This never calls AWS. Sessions, credentials, unreferenced files and incomplete uploads
are not portable workspace content. Archives are private, unencrypted working copies.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import sqlite3
import sys
import uuid
import zipfile
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from grantthread.repository import SQLiteRepository, encode
from grantthread.errors import DomainError

MAX_BYTES = 256 * 1024 * 1024
MAX_OBJECT_BYTES = 5 * 1024 * 1024
MAX_FILES = 2048


def check(condition, message):
    if not condition:
        raise ValueError(message)


def payload(records):
    return json.dumps(records, ensure_ascii=False, separators=(',', ':')).encode('utf-8')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def object_references(records):
    refs = {}
    folded_paths = {}
    check(isinstance(records, list) and 0 < len(records) <= 20, 'Archive needs 1–20 local organisations.')
    seen = set()
    for record in records:
        check(isinstance(record, dict) and set(record) == {'pk', 'data'}, 'Invalid record envelope.')
        pk, data = record['pk'], record['data']
        check(isinstance(pk, str) and re.fullmatch(r'ORG#[a-zA-Z0-9_-]{1,100}', pk), 'Invalid organisation key.')
        check(pk.casefold() not in seen, 'Duplicate organisation record or case-insensitive directory collision.')
        seen.add(pk.casefold())
        org_id = pk[4:]
        check(isinstance(data, dict) and isinstance(data.get('organisation'), dict)
              and data['organisation'].get('id') == org_id and isinstance(data['organisation'].get('name'), str),
              'Organisation scope or metadata is invalid.')
        check(all(type(data.get(field)) is int and data[field] >= 1 for field in ('version', 'factVersion')), 'Invalid record version.')
        for collection in ('grants', 'expenses', 'evidence', 'proposals', 'reports', 'jobs', 'snapshots', 'clarifications', 'uploads'):
            check(isinstance(data.get(collection), dict) and all(isinstance(item, dict) for item in data[collection].values()),
                  f'Invalid or missing workspace collection: {collection}')
        for collection in ('requirements', 'activities', 'audit'):
            check(isinstance(data.get(collection), list) and all(isinstance(item, dict) for item in data[collection]),
                  f'Invalid or missing workspace collection: {collection}')
        for collection in ('financeEntries', 'financeImports', 'fundingReceipts', 'financialReportSettings'):
            check(collection not in data or isinstance(data[collection], dict)
                  and all(isinstance(item, dict) for item in data[collection].values()), f'Invalid workspace collection: {collection}')
        encode(data)
        check(not any(j.get('status') in {'queued', 'running'} for j in data.get('jobs', {}).values()),
              'Wait for queued or running agent jobs to finish before backing up or restoring.')
        for collection in ('evidence', 'financeImports'):
            for item in data.get(collection, {}).values():
                check(isinstance(item.get('objectKey'), str), 'A recorded source needs its object key.')
                if collection == 'evidence':
                    check(isinstance(item.get('parsedKey'), str), 'Evidence needs its parsed text key.')
                for field in ('objectKey', 'parsedKey'):
                    key = item.get(field)
                    if key is None:
                        continue
                    check(isinstance(key, str) and '\\' not in key and ':' not in key, 'Invalid object path.')
                    parts = PurePosixPath(key).parts
                    check(len(parts) >= 3 and parts[0] == org_id and all(p not in {'.', '..', ''} for p in key.split('/')),
                          'Object path is outside its organisation.')
                    check(all(re.fullmatch(r'[A-Za-z0-9_.-]+', part) and not part.endswith('.')
                              and part.split('.')[0].upper() not in {'CON', 'PRN', 'AUX', 'NUL', *(f'COM{i}' for i in range(10)), *(f'LPT{i}' for i in range(10))}
                              for part in parts), 'Object path contains a Windows-unsafe component.')
                    folded = key.casefold()
                    check(folded not in folded_paths or folded_paths[folded] == key, 'Case-insensitive object path collision.')
                    folded_paths[folded] = key
                    checksum = item.get('sha256') if field == 'objectKey' else None
                    if checksum is not None:
                        check(isinstance(checksum, str) and re.fullmatch(r'[0-9a-f]{64}', checksum), 'Invalid source checksum.')
                    if key in refs:
                        check(refs[key] == checksum, 'Conflicting references to the same source.')
                    refs[key] = checksum
    return refs


def private_destination(path):
    resolved = Path(path).resolve()
    check(not any(resolved.is_relative_to((ROOT / folder).resolve()) for folder in ('frontend', 'fixtures')),
          'Keep private workspace archives outside frontend assets and public fixtures.')
    return resolved


def backup(data_dir, output):
    source = Path(data_dir).resolve()
    db_path = source / 'grantthread.sqlite3'
    check(db_path.is_file(), f'Local database not found: {db_path}')
    destination = private_destination(output)
    check(not destination.exists(), 'Backup destination already exists; choose a new filename.')
    # Read all organisation payloads from one SQLite snapshot, including live WAL data.
    with closing(sqlite3.connect(db_path.as_uri() + '?mode=ro', uri=True)) as db:
        rows = db.execute("SELECT pk,payload,version FROM records WHERE pk LIKE 'ORG#%' ORDER BY pk").fetchall()
    records = []
    for pk, value, version in rows:
        data = json.loads(value)
        check(data.get('version') == version, 'Stored record version is inconsistent.')
        records.append({'pk': pk, 'data': data})
    refs = object_references(records)
    check(len(refs) + 2 <= MAX_FILES, 'Workspace has too many source files for this backup format.')
    files = {'records.json': payload(records)}
    object_root = (source / 'objects').resolve()
    size = len(files['records.json'])
    for key, checksum in sorted(refs.items()):
        path = (object_root / key).resolve()
        check(path.is_relative_to(object_root) and path.is_file(), f'Referenced source is missing or outside storage: {key}')
        check(path.stat().st_size <= MAX_OBJECT_BYTES, f'Source exceeds backup file limit: {key}')
        raw = path.read_bytes()
        check(checksum is None or digest(raw) == checksum, f'Source checksum does not match the record: {key}')
        size += len(raw)
        check(size <= MAX_BYTES, 'Workspace exceeds the 256 MB backup limit.')
        files['objects/' + key] = raw
    manifest = {'format': 'grantthread-local-workspace', 'version': 1,
                'createdAt': datetime.now(timezone.utc).isoformat(),
                'files': {name: {'size': len(raw), 'sha256': digest(raw)} for name, raw in files.items()},
                'excludes': ['sessions', 'credentials', 'unreferenced objects', 'incomplete upload bytes']}
    check(size + len(payload(manifest)) <= MAX_BYTES, 'Workspace and manifest exceed the 256 MB backup limit.')
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Reserve with exclusive creation; never overwrite another backup.
    with destination.open('xb') as output_file:
        try:
            with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as archive:
                archive.writestr('manifest.json', payload(manifest))
                for name, raw in files.items():
                    archive.writestr(name, raw)
        except BaseException:
            output_file.close()
            destination.unlink(missing_ok=True)
            raise
    return {'archive': str(destination), 'organisations': len(records), 'objects': len(refs),
            'sha256': digest(destination.read_bytes()), 'private': True}


def inspect_archive(archive_path):
    with zipfile.ZipFile(archive_path) as archive:
        entries = archive.infolist()
        names = [entry.filename for entry in entries]
        check(len(entries) <= MAX_FILES and len(names) == len(set(names)), 'Duplicate or excessive archive entries.')
        check(sum(entry.file_size for entry in entries) <= MAX_BYTES, 'Archive exceeds the 256 MB expanded limit.')
        check(all(entry.file_size <= MAX_OBJECT_BYTES * 2 and not entry.is_dir() for entry in entries), 'Invalid archive entry size or type.')
        check(all(not entry.flag_bits & 1 and entry.compress_type in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}
                  for entry in entries), 'Encrypted archives and unsupported ZIP compression are not supported.')
        check('manifest.json' in names and 'records.json' in names, 'Workspace manifest or records are missing.')
        manifest = json.loads(archive.read('manifest.json'))
        check(isinstance(manifest, dict) and manifest.get('format') == 'grantthread-local-workspace' and manifest.get('version') == 1,
              'Unsupported workspace archive format.')
        expected = manifest.get('files')
        check(isinstance(expected, dict) and set(expected) | {'manifest.json'} == set(names), 'Archive contents do not match the manifest.')
        files = {}
        for name, metadata in expected.items():
            check(isinstance(metadata, dict), 'Invalid file manifest.')
            raw = archive.read(name)
            check(len(raw) == metadata.get('size') and digest(raw) == metadata.get('sha256'), f'Archive checksum failed: {name}')
            files[name] = raw
    records = json.loads(files['records.json'])
    refs = object_references(records)
    check(set(files) == {'records.json'} | {'objects/' + key for key in refs}, 'Unexpected or missing source files in archive.')
    for key, checksum in refs.items():
        raw = files['objects/' + key]
        check(len(raw) <= MAX_OBJECT_BYTES, 'Source exceeds the file limit.')
        check(checksum is None or digest(raw) == checksum, f'Source checksum does not match the record: {key}')
    return records, files


def restore(archive_path, target):
    destination = private_destination(target)
    check(not destination.exists(), 'Restore requires a new directory; existing workspaces are never replaced.')
    records, files = inspect_archive(archive_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    restore_parent = destination.parent.resolve()
    stage_name = 'grantthread-restore-' + uuid.uuid4().hex
    stage = restore_parent / stage_name
    # Use normal directory creation so Windows inherits the destination parent's ACL.
    # TemporaryDirectory's private ACL can otherwise lock out the user's local server after rename.
    stage.mkdir()
    def verify_stage():
        check(not stage.is_symlink() and not (hasattr(stage, 'is_junction') and stage.is_junction())
              and stage.resolve() == restore_parent / stage_name,
              'Restore staging location changed; refusing to move or remove it.')
    try:
        repository = SQLiteRepository(stage / 'grantthread.sqlite3')
        for record in records:
            for upload in record['data'].get('uploads', {}).values():
                if upload.get('status') == 'pending':
                    upload['status'] = 'expired'
            repository.put_initial(record['pk'][4:], record['data'])
        for name, raw in files.items():
            if name == 'records.json':
                continue
            path = stage / name
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('xb') as output_file:
                output_file.write(raw)
        check(not destination.exists(), 'Restore destination was created during validation; choose another directory.')
        verify_stage()
        check(destination.parent.resolve() == restore_parent, 'Restore destination parent changed during validation.')
        stage.rename(destination)
    finally:
        if stage.exists() or stage.is_symlink() or (hasattr(stage, 'is_junction') and stage.is_junction()):
            # Delete only this invocation's exclusively created sibling after verifying its absolute path.
            verify_stage()
            shutil.rmtree(stage)
    return {'dataDirectory': str(destination), 'organisations': len(records), 'sessionsRestored': 0,
            'note': 'Sign in again. Incomplete uploads must be uploaded again.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    save = commands.add_parser('backup', help='Create a private local archive without sessions or credentials')
    save.add_argument('--data-dir', type=Path, default=ROOT / 'backend' / '.data')
    save.add_argument('--output', type=Path, default=ROOT / 'artifacts' / 'private-backups' /
                      ('GrantThread-workspace-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '.zip'))
    load = commands.add_parser('restore', help='Verify and restore into a NEW local data directory')
    load.add_argument('archive', type=Path)
    load.add_argument('--target', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = backup(args.data_dir, args.output) if args.command == 'backup' else restore(args.archive, args.target)
    except (ValueError, OSError, sqlite3.Error, zipfile.BadZipFile, KeyError, TypeError, DomainError) as exc:
        parser.exit(1, f'Workspace operation stopped: {exc}\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
