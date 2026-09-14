"""Build a Linux CPython 3.12 x86_64 Lambda ZIP without Docker or SAM CLI.

Use --download to fetch only pinned binary wheels from PyPI, or --wheelhouse
for an entirely offline build. Runtime source comes ONLY from stage_sam's
allowlist. No AWS calls or runtime imports occur. A successful build verifies
metadata and archive contents; the native Linux runtime still needs a smoke test.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from email.parser import BytesParser
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import uuid
import zipfile

from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.tags import compatible_tags, cpython_tags
from packaging.utils import canonicalize_name, parse_wheel_filename

from release_config import ReleaseError
from stage_sam import MODULES, ROOT, plain_path, stage

PLATFORMS = [f"manylinux_2_{minor}_x86_64" for minor in range(34, 16, -1)] + ["manylinux2014_x86_64"]
TARGET_ENV = {
    "implementation_name": "cpython", "implementation_version": "3.12.0",
    "os_name": "posix", "platform_machine": "x86_64", "platform_release": "",
    "platform_system": "Linux", "platform_version": "", "platform_python_implementation": "CPython",
    "python_full_version": "3.12.0", "python_version": "3.12", "sys_platform": "linux", "extra": "",
}
TAGS = set(cpython_tags((3, 12), ["cp312"], PLATFORMS)) | set(compatible_tags((3, 12), "cp312", PLATFORMS))
MAX_UNPACKED = 250 * 1024 * 1024


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def active(requirement, extras=()):
    if requirement.marker is None:
        return True
    # Kernel versions aren't a stable Lambda dependency boundary. Never silently
    # use the Windows host's version when evaluating an unsupported marker.
    if re.search(r"\bplatform_(release|version)\b", str(requirement.marker)):
        raise ReleaseError("Kernel-specific dependency markers require a Linux build environment")
    return any(requirement.marker.evaluate({**TARGET_ENV, "extra": extra}) for extra in ["", *extras])


def linux_requirements(content):
    result = {}
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            requirement = Requirement(line)
        except ValueError as exc:
            raise ReleaseError("Runtime requirements must contain only exact package pins") from exc
        specs = list(requirement.specifier)
        if requirement.url or len(specs) != 1 or specs[0].operator != "==" or "*" in specs[0].version:
            raise ReleaseError(f"Runtime dependency is not exactly pinned: {requirement.name}")
        if not active(requirement):
            continue
        requirement.marker = None
        name = canonicalize_name(requirement.name)
        if name in result:
            raise ReleaseError(f"Duplicate runtime pin: {name}")
        result[name] = requirement
    return result


def target_flags():
    return ["--implementation", "cp", "--python-version", "3.12", "--abi", "cp312", "--only-binary=:all:",
            *[flag for platform in PLATFORMS for flag in ("--platform", platform)]]


def pip_run(arguments):
    # Ignore developer machine indexes/options and never execute a source build.
    env = {key: value for key, value in os.environ.items() if not key.upper().startswith("PIP_")}
    env["PIP_CONFIG_FILE"] = os.devnull
    subprocess.run([sys.executable, "-m", "pip", "--isolated", "--disable-pip-version-check", "--quiet", *arguments],
                   env=env, check=True, stdout=sys.stderr)


def safe_member(name):
    parts = name.rstrip("/").split("/")
    if (not parts or name.startswith("/") or "\\" in name or ":" in name or "\x00" in name
            or any(part in {"", ".", ".."} or part.endswith((".", " ")) for part in parts)):
        raise ReleaseError("Wheel contains an unsafe archive path")


def installed_member(name):
    """Account for wheel relocation before detecting cross-package overwrites."""
    parts = name.split("/")
    if parts[0].endswith(".data"):
        if len(parts) < 3 or parts[1] not in {"purelib", "platlib", "data", "scripts", "headers"}:
            raise ReleaseError("Wheel has an unsupported installation layout")
        if parts[1] in {"scripts", "headers"}:
            return name  # Separate installation scheme; never aliases runtime code.
        name = "/".join(parts[2:])
    return name


def inspect_wheels(wheelhouse, pins):
    wheels, metadata, members = [], {}, {}
    for path in sorted(wheelhouse.iterdir()):
        plain_path(path, wheelhouse)
        if not path.is_file() or path.suffix != ".whl":
            raise ReleaseError("Wheelhouse must contain only pinned .whl files")
        name, version, _, tags = parse_wheel_filename(path.name)
        if name not in pins or version not in pins[name].specifier or name in metadata:
            raise ReleaseError(f"Unexpected, duplicate or incorrectly versioned wheel: {path.name}")
        if not tags.intersection(TAGS):
            raise ReleaseError(f"Wheel does not support Linux CPython 3.12 x86_64: {path.name}")
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
            if sum(info.file_size for info in infos) > MAX_UNPACKED:
                raise ReleaseError("Wheel exceeds Lambda's unpacked size limit")
            seen = set()
            for info in infos:
                safe_member(info.orig_filename)
                safe_member(info.filename)
                if stat.S_ISLNK(info.external_attr >> 16):
                    raise ReleaseError("Wheel symlinks are not supported")
                key = info.filename.casefold().rstrip("/")
                if key in seen:
                    raise ReleaseError("Wheel contains duplicate archive paths")
                seen.add(key)
                if info.is_dir():
                    continue
                content = archive.read(info)
                installed_key = installed_member(info.filename).casefold()
                previous = members.get(installed_key)
                digest = hashlib.sha256(content).hexdigest()
                if previous and previous != digest:
                    raise ReleaseError(f"Wheels overwrite one another: {info.filename}")
                members[installed_key] = digest
            matches = [info for info in infos if info.filename.endswith(".dist-info/METADATA")]
            if len(matches) != 1:
                raise ReleaseError("Wheel must contain one package metadata file")
            message = BytesParser().parsebytes(archive.read(matches[0]))
        if canonicalize_name(message["Name"] or "") != name or message["Version"] != str(version):
            raise ReleaseError(f"Wheel filename and metadata disagree: {path.name}")
        if message["Requires-Python"] and TARGET_ENV["python_full_version"] not in SpecifierSet(message["Requires-Python"]):
            raise ReleaseError(f"Wheel requires a different Python version: {path.name}")
        metadata[name] = [Requirement(value) for value in message.get_all("Requires-Dist", [])]
        wheels.append({"file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                       "name": name, "version": str(version), "tags": sorted(map(str, tags))})
    if metadata.keys() != pins.keys():
        raise ReleaseError("Missing pinned Linux wheels: " + ", ".join(sorted(pins.keys() - metadata.keys())))
    # Resolve extras to a fixed point. pip's resolver runs on Windows; this is
    # the authoritative dependency-closure check for the actual Linux target.
    extras = {name: set(requirement.extras) for name, requirement in pins.items()}
    changed = True
    while changed:
        changed = False
        for owner, dependencies in metadata.items():
            for requirement in dependencies:
                if not active(requirement, extras[owner]):
                    continue
                name = canonicalize_name(requirement.name)
                version = next(iter(pins[name].specifier)).version if name in pins else None
                if requirement.url or version is None or version not in requirement.specifier:
                    raise ReleaseError(f"Linux dependency closure is incomplete: {owner} requires {requirement}")
                if not requirement.extras.issubset(extras[name]):
                    extras[name].update(requirement.extras)
                    changed = True
    return wheels


@contextmanager
def owned_directory(parent, prefix):
    parent.mkdir(parents=True, exist_ok=True)
    resolved_parent = parent.resolve()
    name = prefix + uuid.uuid4().hex
    working = resolved_parent / name
    working.mkdir()  # Inherit the destination parent's ACL on Windows.
    def verify():
        plain_path(working, resolved_parent)
        if parent.resolve() != resolved_parent or working.resolve() != resolved_parent / name:
            raise ReleaseError("Build staging path changed; refusing to remove it")
    try:
        yield working
    finally:
        if working.exists() or working.is_symlink() or (hasattr(working, "is_junction") and working.is_junction()):
            verify()
            for path in working.rglob("*"):
                plain_path(path, working)
            shutil.rmtree(working)


def runtime_files(package, source):
    files = {}
    for path in sorted(package.rglob("*")):
        plain_path(path, package)
        if not path.is_file():
            continue
        name = path.relative_to(package).as_posix()
        parts = PurePosixPath(name).parts
        if parts[0].lower() in {"bin", "scripts"} or "__pycache__" in parts or path.suffix == ".pyc":
            continue
        if path.parent.name.endswith(".dist-info") and path.name in {"RECORD", "INSTALLER", "REQUESTED", "direct_url.json"}:
            continue  # pip-generated paths/launchers vary with the Windows host.
        if parts[0].lower() == "grantthread" or path.suffix.lower() in {".dll", ".exe", ".pyd"}:
            raise ReleaseError(f"Unexpected host binary or runtime collision: {name}")
        content = path.read_bytes()
        if path.suffix == ".so" or ".so." in path.name:
            if len(content) < 20 or content[:6] != b"\x7fELF\x02\x01" or int.from_bytes(content[18:20], "little") != 62:
                raise ReleaseError(f"Native library is not ELF x86_64: {name}")
        files[name] = content
    for name in sorted(MODULES):
        files["grantthread/" + name] = (source / "grantthread" / name).read_bytes()
    if sum(map(len, files.values())) >= MAX_UNPACKED:
        raise ReleaseError("Lambda ZIP exceeds the 250 MiB unpacked size limit")
    return files


def write_zip(path, files):
    with zipfile.ZipFile(path, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, content in sorted(files.items()):
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, content, compresslevel=9)


def build(root, wheelhouse=None, download=False):
    if (wheelhouse is None) == (not download):
        raise ReleaseError("Choose either --download or --wheelhouse")
    source_result = stage(root)
    source = Path(source_result["sourceDirectory"])
    source_manifest = (source.parent / "stage-manifest.json").read_bytes()
    if hashlib.sha256(source_manifest).hexdigest() != source_result["sha256"]:
        raise ReleaseError("Staged source manifest changed before packaging")
    source_hashes = json.loads(source_manifest)["files"]
    original_requirements = (source / "requirements.txt").read_bytes()
    if hashlib.sha256(original_requirements).hexdigest() != source_hashes["backend/requirements.txt"]:
        raise ReleaseError("Staged runtime requirements changed before packaging")
    pins = linux_requirements(original_requirements.decode("utf-8"))
    requirements = "".join(str(pins[name]) + "\n" for name in sorted(pins)).encode()
    parent = root / "artifacts" / "lambda-build"
    for path in (root / "artifacts", parent):
        plain_path(path, root)
    with owned_directory(parent, ".build-") as working:
        requirements_path = working / "requirements-linux.txt"
        requirements_path.write_bytes(requirements)
        if download:
            wheelhouse = working / "wheels"
            wheelhouse.mkdir()
            pip_run(["download", "--no-deps", *target_flags(), "--index-url", "https://pypi.org/simple",
                     "--dest", str(wheelhouse), "-r", str(requirements_path)])
        else:
            wheelhouse = Path(wheelhouse).resolve()
        wheels = inspect_wheels(wheelhouse, pins)
        package = working / "package"
        pip_run(["install", "--no-deps", "--no-index", "--no-compile", *target_flags(), "--find-links", str(wheelhouse),
                 "--target", str(package), "-r", str(requirements_path)])
        if inspect_wheels(wheelhouse, pins) != wheels:
            raise ReleaseError("Wheelhouse changed during dependency installation")
        plain_path(package, working)
        files = runtime_files(package, source)
        for name in MODULES:
            if hashlib.sha256(files["grantthread/" + name]).hexdigest() != source_hashes["backend/grantthread/" + name]:
                raise ReleaseError("Staged runtime source changed during packaging")
        hashes = {name: hashlib.sha256(content).hexdigest() for name, content in sorted(files.items())}
        manifest = {"schemaVersion": 1, "target": TARGET_ENV, "platforms": PLATFORMS,
                    "sourceStageSha256": source_result["sha256"], "wheels": wheels, "files": hashes,
                    "unpackedBytes": sum(map(len, files.values())), "linuxRuntimeVerified": False}
        manifest["requirementsSha256"] = hashlib.sha256(requirements).hexdigest()
        content_hash = hashlib.sha256(json_bytes(manifest)).hexdigest()
        release = working / "release"
        release.mkdir()
        archive = release / "function.zip"
        write_zip(archive, files)
        archive_sha = hashlib.sha256(archive.read_bytes()).hexdigest()
        manifest.update(zipSha256=archive_sha, zipBytes=archive.stat().st_size, fileCount=len(files))
        (release / "build-manifest.json").write_bytes(json_bytes(manifest))
        (release / "requirements-linux.txt").write_bytes(requirements)
        target = parent / content_hash[:20]
        plain_path(target, parent)
        if parent.resolve() != working.parent:
            raise ReleaseError("Lambda build parent changed during packaging")
        if target.exists():
            if not target.is_dir() or {path.name for path in target.iterdir()} != {path.name for path in release.iterdir()}:
                raise ReleaseError("Existing Lambda build has unexpected files")
            for path in release.iterdir():
                existing = target / path.name
                plain_path(existing, target)
                if not existing.is_file() or existing.read_bytes() != path.read_bytes():
                    raise ReleaseError("Existing Lambda build differs; refusing to overwrite")
        else:
            os.rename(release, target)
        # Downloaded wheels are preserved separately for a network-free rebuild.
        if download:
            wheel_target = parent / ("wheels-" + hashlib.sha256(json_bytes(wheels)).hexdigest()[:20])
            plain_path(wheel_target, parent)
            if wheel_target.exists():
                if inspect_wheels(wheel_target, pins) != wheels:
                    raise ReleaseError("Existing wheelhouse differs; refusing to overwrite")
            else:
                os.rename(wheelhouse, wheel_target)
            wheelhouse = wheel_target
        return {"zip": str(target / "function.zip"), "manifest": str(target / "build-manifest.json"),
                "sha256": archive_sha, "zipBytes": manifest["zipBytes"], "unpackedBytes": manifest["unpackedBytes"],
                "files": len(files), "wheels": len(wheels), "wheelhouse": str(wheelhouse),
                "sourceTemplate": source_result["template"], "verification": "Offline archive checks passed; Linux Lambda runtime import is not yet verified"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--download", action="store_true", help="Download pinned Linux wheels from PyPI")
    choice.add_argument("--wheelhouse", type=Path, help="Build offline from an existing verified wheel directory")
    args = parser.parse_args()
    try:
        result = build(ROOT, args.wheelhouse, args.download)
    except (OSError, ReleaseError, ValueError, zipfile.BadZipFile, subprocess.CalledProcessError) as exc:
        parser.exit(2, f"Lambda package not built: {exc}\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
