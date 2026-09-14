# Local testing and workspace recovery

Run these commands from the repository root in PowerShell after installing the dependencies in [SETUP.md](SETUP.md). These tools use local files only and never connect to AWS.

## Start a separate fictional workspace

```powershell
.\scripts\start-local.ps1 -CheckOnly
.\scripts\start-local.ps1 -DataDirectory .\artifacts\my-test-workspace -Offline -OpenBrowser
```

A new data directory is seeded with fictional organisations. Choosing another directory does not replace the usual `backend/.data` workspace. `-Offline` disables Bedrock calls for this run, even if a model was previously configured in the terminal. Close the launcher with Ctrl+C when finished. It stops only the API process it started; it refuses to start if port 8000 or 5173 is already occupied. The launcher forces local mode and restores the caller's environment on exit.

## Create a private backup

Wait for any queued/running agent jobs to finish. For a stable recovery point, close the app launcher before backing up.

```powershell
.\.venv\Scripts\python.exe scripts/local_workspace.py backup
```

The default source is `backend/.data`; the result prints the archive path and SHA-256 checksum. Archives go under `artifacts/private-backups/` and are **private, unencrypted copies**. Keep them on a protected local drive. Do not upload them to cPanel, public GitHub or public fixtures. The tool refuses destinations inside `frontend/` and `fixtures/` and refuses to replace an existing backup.

For a separate test workspace:

```powershell
.\.venv\Scripts\python.exe scripts/local_workspace.py backup --data-dir .\artifacts\my-test-workspace --output .\artifacts\private-backups\test-workspace.zip
```

Backups contain organisation records and only the private source files referenced by those records. They include financial entries, funding receipts, import previews, evidence and recorded history. Sessions, credentials, orphaned objects and incomplete upload bytes are excluded. The tool checks source hashes, organisation paths, active jobs and the 256 MiB expanded archive limit.

## Restore and verify

Always restore into a **new directory**. Existing workspaces are never overwritten.

```powershell
.\.venv\Scripts\python.exe scripts/local_workspace.py restore .\artifacts\private-backups\test-workspace.zip --target .\artifacts\restored-test
.\scripts\start-local.ps1 -DataDirectory .\artifacts\restored-test -Offline -OpenBrowser
```

Before creating the destination, restore checks the manifest, file hashes, required collections, tenant scope and Windows-safe file paths. It stages the complete result before moving it into place. Sign in again after restoring; previous sessions do not carry over. Incomplete uploads are expired and must be uploaded again.

Check the expected grant, confirmed financial totals, receipt rates and at least one original source download. Retain the previous workspace until you have checked the restored one. A valid archive proves file consistency, not the accounting correctness of its records.

Normal startup seeds only missing demonstration organisations. Existing organisation records and their referenced source files are preserved; explicit reset is a separate operation.

This is a local recovery format, not a cloud migration tool. It does not restore Cognito memberships, S3 permissions, running jobs or AWS configuration.
