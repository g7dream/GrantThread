"""Validate and package a cloud frontend, or explicitly package an interface preview.

Only Vite's compiled public assets are accepted. Configured is not the same as
verified live: authentication, API permissions and Bedrock still need live tests.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import tempfile
import zipfile
from datetime import datetime, timedelta
from html.parser import HTMLParser
from pathlib import Path

from release_config import PUBLIC_KEYS, ReleaseError, read_json, validate_base, validate_cloud_config, validate_site

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = "grantthread-build.json"
STATIC_ROOT_FILES = {"index.html", "INTER-LICENSE.txt", MANIFEST}
ASSET_EXTENSIONS = {".js", ".css", ".woff", ".woff2", ".svg", ".png", ".jpg", ".jpeg", ".webp", ".avif", ".ico"}
SECRET_PATTERN = re.compile(rb"(?:AKIA|ASIA)[A-Z0-9]{16}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")


def content_timestamp(content: bytes) -> tuple[int, ...]:
    # LiteSpeed can reuse compressed bytes when mtime and size are unchanged.
    # Derive DOS-resolution timestamps from content, not build time, so changed
    # equal-sized entry files refresh that cache and identical ZIPs stay repeatable.
    # Use a fixed past range within ZIP's 1980-2107 limits, avoiding future HTTP dates.
    start = datetime(1980, 1, 1)
    slots = (datetime(2020, 1, 1) - start).days * 24 * 60 * 30
    slot = int.from_bytes(hashlib.sha256(content).digest()[:8], "big") % slots
    return (start + timedelta(seconds=slot * 2)).timetuple()[:6]


class AssetReferences(HTMLParser):
    def __init__(self):
        super().__init__()
        self.references = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "script" and values.get("src"):
            self.references.append(values["src"])
        if tag == "link" and values.get("rel") in {"stylesheet", "modulepreload"} and values.get("href"):
            self.references.append(values["href"])


def load_dist(dist: Path) -> dict[str, bytes]:
    if not dist.is_dir() or not (dist / "index.html").is_file():
        raise ReleaseError("Build the frontend first")
    if dist.is_symlink() or (hasattr(dist, "is_junction") and dist.is_junction()):
        raise ReleaseError("Build directory must not be a symlink or junction")
    resolved_dist = dist.resolve()
    files = {}
    total = 0
    for current, directories, filenames in os.walk(dist, followlinks=False):
        for name in directories + filenames:
            path = Path(current) / name
            if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()) or not path.resolve().is_relative_to(resolved_dist):
                raise ReleaseError("Build contains a symlink, junction or file outside dist")
            relative = path.relative_to(dist)
            if any(part.startswith(".") for part in relative.parts):
                raise ReleaseError(f"Unexpected hidden build path: {relative.as_posix()}")
        for name in filenames:
            path = Path(current) / name
            relative = path.relative_to(dist).as_posix()
            if relative not in STATIC_ROOT_FILES and not (relative.startswith("assets/") and path.suffix in ASSET_EXTENSIONS):
                raise ReleaseError(f"Unexpected public build file: {relative}; keep source, records and source maps out of dist")
            size = path.stat().st_size
            total += size
            if size > 25_000_000 or total > 100_000_000:
                raise ReleaseError("Build exceeds the public frontend package size limit")
            content = path.read_bytes()
            if SECRET_PATTERN.search(content):
                raise ReleaseError(f"Possible credential material found in {relative}; remove it before packaging")
            files[relative] = content
    return files


def validate_build(files: dict[str, bytes], base: str, site_url: str | None, preview: bool) -> dict:
    validate_base(base)
    if site_url:
        validate_site(site_url, base)
    if MANIFEST not in files:
        raise ReleaseError("Build metadata is missing; rebuild with the current Vite configuration before packaging")
    manifest = read_json(files[MANIFEST].decode("utf-8"))
    if not isinstance(manifest, dict) or set(manifest) != {"schemaVersion", "mode", "basePath", "publicConfig", "assets"}:
        raise ReleaseError("Build metadata has an unsupported shape; rebuild the frontend")
    if type(manifest["schemaVersion"]) is not int or manifest["schemaVersion"] != 1 or manifest["mode"] != "production":
        raise ReleaseError("Packaging requires current production build metadata")
    if manifest["basePath"] != base:
        raise ReleaseError("Build with VITE_BASE_PATH matching --base before packaging")
    config = manifest["publicConfig"]
    if not isinstance(config, dict) or set(config) != set(PUBLIC_KEYS) or not all(isinstance(v, str) for v in config.values()):
        raise ReleaseError("Build metadata must contain only the four supported public settings")
    digests = manifest["assets"]
    if not isinstance(digests, dict) or not digests:
        raise ReleaseError("Build metadata contains no asset hashes; rebuild the frontend")
    # Public fonts/images may be copied rather than generated by Rollup. Every
    # executable asset and the HTML entry point must still be bound to this build.
    required = {name for name in files if name == "index.html" or Path(name).suffix in {".js", ".css"}}
    if not required.issubset(digests) or MANIFEST in digests:
        raise ReleaseError("Build metadata is missing HTML, JavaScript or CSS asset hashes")
    for name, digest in digests.items():
        if name not in files or not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ReleaseError("Build metadata references an absent asset or invalid SHA-256")
        if hashlib.sha256(files[name]).hexdigest() != digest:
            raise ReleaseError(f"Build asset does not match its metadata: {name}; rebuild before packaging")
    references = AssetReferences()
    references.feed(files["index.html"].decode("utf-8"))
    if not references.references:
        raise ReleaseError("Build index has no script or stylesheet assets")
    for reference in references.references:
        if not reference.startswith(base + "assets/") or reference[len(base):] not in files:
            raise ReleaseError("HTML asset paths do not match --base or an asset is missing")
    if not preview:
        if not site_url:
            raise ReleaseError("Cloud packaging requires --site-url with the exact hosted callback URL; use --preview only for an interface preview")
        validate_cloud_config(config, base, site_url)
    return manifest


def deployment_files(base: str, site_url: str | None, preview: bool) -> dict[str, bytes]:
    rewrite = f"""Options -Indexes
DirectoryIndex index.html
<IfModule mod_rewrite.c>
RewriteEngine On
RewriteBase {base}
# Application uses hash routes; unknown non-file paths receive the SPA.
RewriteCond %{{REQUEST_FILENAME}} !-f
RewriteCond %{{REQUEST_FILENAME}} !-d
RewriteRule ^ index.html [L]
</IfModule>
<IfModule mod_headers.c>
Header always set X-Content-Type-Options nosniff
Header always set Referrer-Policy strict-origin-when-cross-origin
Header always set X-Frame-Options DENY
<FilesMatch "^(index\\.html|grantthread-build\\.json)$">
# ZIP timestamps are fixed: old browser validators must not yield stale 304s.
FileETag None
RequestHeader unset If-Modified-Since
RequestHeader unset If-None-Match
Header unset Last-Modified
Header always unset Last-Modified
Header unset ETag
Header always unset ETag
Header unset Cache-Control
Header always set Cache-Control "no-store"
</FilesMatch>
</IfModule>
"""
    segment = base.strip("/")
    parent_rule = ""
    if segment:
        parent_rule = f"RewriteEngine On\nRewriteCond %{{REQUEST_URI}} !^{re.escape(base)}\nRewriteRule ^{re.escape(segment)}(?:/(.*))?$ {base}$1 [R=302,L,NC]\n"
    status = ("INTERFACE PREVIEW ONLY: cloud sign-in, uploads and reporting are not ready for hosted testing.\n"
              "Configure the AWS API and Cognito public settings, rebuild and run cloud packaging before functional testing."
              if preview else
              "CLOUD CONFIGURATION VALIDATED OFFLINE: this is not evidence of working cloud services.\n"
              "Verify managed sign-in, scoped data, upload, reporting and model behavior on the hosted site.")
    readme = f"""GrantThread public frontend package

{status}

Destination: {site_url or ('the owned HTTPS domain at ' + base)}
Extract ZIP contents so index.html is directly inside the dedicated {base} directory.
Back up destination files before upload. Do not replace another website.
This package includes no AWS credentials or backend records. Uploaded user records are not demonstration data.

To support letter-case variants, merge this block into the PARENT document root
.htaccess before any catch-all rule. Preserve the existing file and unrelated rules:

{parent_rule}
Use temporary redirects for testing; switch 302 to 301 only after verifying your domain.
Configuration is embedded in the assets: editing the build metadata alone does not configure the app.
Restore the previous verified frontend package to roll back; do not reset backend data.
"""
    return {".htaccess": rewrite.encode("utf-8"), "DEPLOYMENT.txt": readme.encode("utf-8")}


def package(root: Path, base: str, site_url: str | None, preview: bool = False) -> dict:
    files = load_dist(root / "frontend" / "dist")
    manifest = validate_build(files, base, site_url, preview)
    files.update(deployment_files(base, site_url, preview))
    licence = root / "LICENSE"
    if not licence.is_file() or "INTER-LICENSE.txt" not in files:
        raise ReleaseError("Missing project or Inter font licence; restore the licensed public assets")
    files["LICENSE.txt"] = licence.read_bytes()
    notices = []
    for name in ("react", "react-dom", "lucide-react"):
        licence = root / "frontend" / "node_modules" / name / "LICENSE"
        if not licence.is_file():
            raise ReleaseError(f"Missing third-party licence for {name}; install locked frontend dependencies first")
        notices.append(name + "\n" + licence.read_text(encoding="utf-8"))
    notices.append("Inter font: see INTER-LICENSE.txt in this package.")
    files["THIRD_PARTY_NOTICES.txt"] = "\n\n".join(notices).encode("utf-8")
    # Validate all inputs before touching the prior artifact. Content-derived
    # timestamps, permissions and sorted names preserve identical ZIP builds.
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, content in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=content_timestamp(content))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, content, compresslevel=9)
    payload = buffer.getvalue()
    digest = hashlib.sha256(payload).hexdigest()
    output = root / "artifacts" / ("GrantThread-preview.zip" if preview else "GrantThread-cpanel.zip")
    output.parent.mkdir(exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(dir=output.parent, prefix=".grantthread-package-", suffix=".tmp", delete=False) as temporary:
            temp_path = Path(temporary.name)
            temporary.write(payload)
        os.replace(temp_path, output)
        output.with_suffix(".sha256").write_text(f"{digest}  {output.name}\n", encoding="ascii")
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
    return {"zip": str(output), "sha256": digest, "bytes": len(payload), "base": base,
            "mode": "interface-preview" if preview else "cloud-configured", "siteUrl": site_url,
            "cloudConfigured": not preview, "liveVerified": False, "assetCount": len(manifest["assets"])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="/grantthread/")
    parser.add_argument("--site-url", help="Exact hosted URL including the subfolder and trailing slash; required for cloud packaging")
    parser.add_argument("--preview", action="store_true", help="Explicitly create GrantThread-preview.zip without requiring cloud settings")
    args = parser.parse_args()
    try:
        result = package(ROOT, args.base, args.site_url, args.preview)
    except (ReleaseError, OSError, UnicodeError) as exc:
        parser.exit(2, f"Package not created: {exc}\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
