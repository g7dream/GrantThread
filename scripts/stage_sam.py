"""Stage allowlisted runtime source for SAM without local records, tests or credentials.

The ordinary backend directory contains private local data and must NEVER be a
SAM CodeUri. This offline command prepares an immutable content-addressed tree.
Capture its JSON result and build the returned template path with SAM's Linux
container builder. No dependency installation or AWS request is performed here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import uuid

from release_config import ReleaseError

ROOT = Path(__file__).resolve().parents[1]
SOURCE_MARKER = "../artifacts/sam-source/UNSTAGED"
MODULES = {
    "__init__.py", "api.py", "auth.py", "bank_agent.py", "demo.py", "domain.py", "errors.py",
    "finance_io.py", "finance_math.py", "finance_service.py", "lambda_handler.py",
    "local_server.py", "reports.py", "repository.py", "response_estimates.py",
    "seed.py", "service.py", "storage.py", "worker.py",
}


def plain_path(path: Path, root: Path):
    if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()) or not path.resolve().is_relative_to(root.resolve()):
        raise ReleaseError("SAM source paths must not be symlinks, junctions or escape the repository")


def gather_source(root: Path) -> dict[str, bytes]:
    package = root / "backend" / "grantthread"
    plain_path(root / "backend", root)
    plain_path(package, root)
    if not package.is_dir():
        raise ReleaseError("Runtime source package is missing")
    actual = set()
    for path in package.iterdir():
        plain_path(path, root)
        if path.name == "__pycache__" and path.is_dir():
            continue
        if not path.is_file() or path.name not in MODULES:
            raise ReleaseError(f"Unexpected runtime package file or directory: {path.name}; review the explicit SAM source allowlist")
        actual.add(path.name)
    if actual != MODULES:
        raise ReleaseError("Runtime source is missing required modules: " + ", ".join(sorted(MODULES - actual)))
    files = {}
    for name in sorted(MODULES):
        content = (package / name).read_bytes()
        # Syntax validation has no module imports or runtime side effects.
        compile(content, name, "exec")
        files["backend/grantthread/" + name] = content
    requirements = root / "backend" / "requirements.txt"
    template = root / "infra" / "template.yaml"
    for path in (requirements, template):
        plain_path(path, root)
        if not path.is_file():
            raise ReleaseError("Runtime requirements or SAM source template is missing")
    files["backend/requirements.txt"] = requirements.read_bytes()
    text = template.read_text(encoding="utf-8")
    pattern = r"(?m)^(\s*CodeUri:) " + re.escape(SOURCE_MARKER) + r"\s*$"
    rewritten, count = re.subn(pattern, r"\1 ./backend", text)
    if count != 2 or len(re.findall(r"(?m)^\s*CodeUri:", text)) != 2:
        raise ReleaseError("Expected exactly two guarded CodeUri markers; review the SAM staging contract")
    files["template.yaml"] = rewritten.encode("utf-8")
    return files


def stage(root: Path) -> dict:
    files = gather_source(root)
    hashes = {name: hashlib.sha256(content).hexdigest() for name, content in sorted(files.items())}
    manifest = (json.dumps({"schemaVersion": 1, "files": hashes}, sort_keys=True, indent=2) + "\n").encode()
    digest = hashlib.sha256(manifest).hexdigest()
    files["stage-manifest.json"] = manifest
    parent = root / "artifacts" / "sam-source"
    for path in (root / "artifacts", parent):
        plain_path(path, root)
    target = parent / digest[:20]
    plain_path(target, root)
    if target.exists():
        if not target.is_dir():
            raise ReleaseError("Existing SAM staging target is not a directory")
        actual = set()
        directories = {"backend", "backend/grantthread"}
        for path in target.rglob("*"):
            plain_path(path, target)
            if path.is_dir() and path.relative_to(target).as_posix() not in directories:
                raise ReleaseError("Existing SAM stage contains an unexpected directory; inspect it before building")
            if path.is_file():
                name = path.relative_to(target).as_posix()
                actual.add(name)
                if name not in files or path.read_bytes() != files[name]:
                    raise ReleaseError("Existing SAM stage differs from its source manifest; inspect it before building")
        if actual != set(files):
            raise ReleaseError("Existing SAM stage is incomplete; inspect it before building")
    else:
        parent.mkdir(parents=True, exist_ok=True)
        staging_parent = parent.resolve()
        working_name = ".stage-" + uuid.uuid4().hex
        working = staging_parent / working_name
        # Normal mkdir inherits the parent's Windows ACL. TemporaryDirectory's
        # private ACL survives a rename and can lock the user out of SAM inputs.
        working.mkdir()
        def verify_working():
            plain_path(working, staging_parent)
            if working.resolve() != staging_parent / working_name or parent.resolve() != staging_parent:
                raise ReleaseError("SAM staging location changed; refusing to move or remove it")
        try:
            for name, content in sorted(files.items()):
                destination = working / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                with destination.open("xb") as stream:
                    stream.write(content)
            verify_working()
            if target.exists():
                raise ReleaseError("SAM destination was created during staging; inspect it before retrying")
            os.rename(working, target)
        finally:
            if working.exists() or working.is_symlink() or (hasattr(working, "is_junction") and working.is_junction()):
                # Remove only this call's exclusively created sibling, after
                # checking its frozen absolute parent and complete target path.
                verify_working()
                shutil.rmtree(working)
    return {"template": str(target / "template.yaml"), "sourceDirectory": str(target / "backend"),
            "sha256": digest, "files": len(files), "runtimeModules": len(MODULES),
            "verification": "offline source staging only; build with SAM's Linux container before deploying"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    try:
        result = stage(ROOT)
    except (OSError, ReleaseError, UnicodeError, SyntaxError) as exc:
        parser.exit(2, f"SAM source not staged: {exc}\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
