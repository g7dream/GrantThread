"""Offline deployment guard checks using synthetic assets and no cloud access."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
from configure_frontend import render_env
from package_cpanel import MANIFEST, load_dist, package, validate_build
from release_config import ReleaseError, config_from_outputs, read_json, validate_cloud_config

SITE = "https://timeillusion.com/grantthread/"
BASE = "/grantthread/"
CONFIG = {
    "apiUrl": "https://abc123.execute-api.eu-north-1.amazonaws.com/api",
    "cognitoDomain": "https://grantthread-test.auth.eu-north-1.amazoncognito.com",
    "cognitoClientId": "1abc23def456ghi78",
    "cognitoRedirectUri": SITE,
}


def build_files(config=None, base=BASE):
    files = {
        "index.html": f'<script type="module" src="{base}assets/index-abcd.js"></script><link rel="stylesheet" href="{base}assets/index-abcd.css">'.encode(),
        "assets/index-abcd.js": b'console.log("fictional application fixture")',
        "assets/index-abcd.css": b"body{color:#123456}",
        "INTER-LICENSE.txt": b"Fictional licence fixture for tests only",
    }
    manifest = {"schemaVersion": 1, "mode": "production", "basePath": base,
                "publicConfig": dict(CONFIG if config is None else config),
                "assets": {name: hashlib.sha256(value).hexdigest() for name, value in files.items() if name != "INTER-LICENSE.txt"}}
    files[MANIFEST] = json.dumps(manifest).encode()
    return files


class ReleaseConfigTests(unittest.TestCase):
    def test_accepts_complete_cloud_config_and_exact_hosted_subfolder(self):
        self.assertEqual(validate_cloud_config(CONFIG, BASE, SITE), CONFIG)

    def test_rejects_relative_api_blank_login_and_mismatched_callback(self):
        for key, value in [("apiUrl", "/api"), ("cognitoDomain", ""), ("cognitoClientId", ""),
                           ("cognitoRedirectUri", "https://timeillusion.com/")]:
            with self.subTest(key=key), self.assertRaises(ReleaseError):
                validate_cloud_config({**CONFIG, key: value}, BASE, SITE)

    def test_rejects_insecure_local_placeholder_and_credential_urls(self):
        values = ["http://cloud.acme.com/api", "https://localhost/api", "https://127.0.0.1/api",
                  "https://192.168.1.4/api", "https://cloud.example/api", "https://example.com/api",
                  "https://user:secret@cloud.acme.com/api", "https://cloud.acme.com:8443/api",
                  "https://cloud.acme.com/api?token=secret", "https://cloud.acme.com/api#fragment",
                  "https://cloud.acme.com/${SECRET}/api", "https://cloud.acme.com/foo/../api",
                  "https://cloud.acme.com/%2e%2e/api", "https://cloud.acme.com/api\nINJECT=1"]
        for value in values:
            with self.subTest(value=value), self.assertRaises(ReleaseError):
                validate_cloud_config({**CONFIG, "apiUrl": value}, BASE, SITE)

    def test_root_base_supported_and_mixed_case_base_rejected(self):
        config = {**CONFIG, "cognitoRedirectUri": "https://timeillusion.com/"}
        self.assertEqual(validate_cloud_config(config, "/", config["cognitoRedirectUri"]), config)
        with self.assertRaises(ReleaseError):
            validate_cloud_config(CONFIG, "/GrantThread/", SITE)

    def test_outputs_select_only_public_settings_from_one_stack(self):
        outputs = {"ApiUrl": CONFIG["apiUrl"], "CognitoDomain": CONFIG["cognitoDomain"],
                   "CognitoClientId": CONFIG["cognitoClientId"], "CallbackUrl": SITE,
                   "FrontendOrigin": "https://timeillusion.com", "CognitoScope": "grantthread/access profile email openid",
                   "TableName": "PRIVATE-NOT-FOR-FRONTEND", "UnexpectedSecret": "MUST-NOT-BE-COPIED"}
        rows = [{"OutputKey": k, "OutputValue": v} for k, v in outputs.items()]
        for document in [outputs, rows, {"Outputs": rows}, {"Stacks": [{"Outputs": rows}]}]:
            with self.subTest(shape=type(document).__name__):
                config = config_from_outputs(document, SITE, BASE)
                self.assertEqual(config, CONFIG)
                env = render_env(config, BASE)
                self.assertEqual(len([line for line in env.splitlines() if line.startswith("VITE_")]), 5)
                self.assertNotIn("PRIVATE", env)
                self.assertNotIn("MUST-NOT", env)

    def test_outputs_reject_multiple_stacks_duplicate_keys_and_scope_mismatch(self):
        invalid = [{"Stacks": [{"Outputs": []}, {"Outputs": []}]},
                   [{"OutputKey": "ApiUrl", "OutputValue": "one"}, {"OutputKey": "ApiUrl", "OutputValue": "two"}],
                   {"ApiUrl": CONFIG["apiUrl"], "CognitoDomain": CONFIG["cognitoDomain"],
                    "CognitoClientId": CONFIG["cognitoClientId"], "CognitoScope": "openid"}]
        for document in invalid:
            with self.subTest(document=document), self.assertRaises(ReleaseError):
                config_from_outputs(document, SITE, BASE)
        with self.assertRaises(ReleaseError):
            read_json('{"ApiUrl":"first","ApiUrl":"second"}')

    def test_outputs_reject_wrong_registered_callback_or_cors_origin(self):
        outputs = {"ApiUrl": CONFIG["apiUrl"], "CognitoDomain": CONFIG["cognitoDomain"], "CognitoClientId": CONFIG["cognitoClientId"]}
        for key, value in [("CallbackUrl", "https://timeillusion.com/"), ("FrontendOrigin", "https://otherdomain.com")]:
            with self.subTest(key=key), self.assertRaises(ReleaseError):
                config_from_outputs({**outputs, key: value}, SITE, BASE)


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.dist = self.root / "frontend" / "dist"
        self.dist.mkdir(parents=True)
        self.write_build(build_files())
        (self.root / "LICENSE").write_text("Project licence fixture", encoding="utf-8")
        for name in ("react", "react-dom", "lucide-react"):
            target = self.root / "frontend" / "node_modules" / name
            target.mkdir(parents=True)
            (target / "LICENSE").write_text(f"{name} licence fixture", encoding="utf-8")

    def write_build(self, files):
        for name, content in files.items():
            target = self.dist / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)

    def test_cloud_package_is_reproducible_despite_file_time_changes(self):
        first = package(self.root, BASE, SITE)
        payload = Path(first["zip"]).read_bytes()
        for file in self.dist.rglob("*"):
            if file.is_file():
                os.utime(file, (1700000000, 1700000000))
        second = package(self.root, BASE, SITE)
        self.assertEqual(first["sha256"], second["sha256"])
        self.assertEqual(payload, Path(second["zip"]).read_bytes())
        self.assertFalse(second["liveVerified"])
        with zipfile.ZipFile(second["zip"]) as archive:
            self.assertEqual(archive.testzip(), None)
            self.assertIn(".htaccess", archive.namelist())
            self.assertIn("THIRD_PARTY_NOTICES.txt", archive.namelist())
            self.assertIn(b"CLOUD CONFIGURATION VALIDATED OFFLINE", archive.read("DEPLOYMENT.txt"))
            self.assertTrue(all((1980, 1, 1, 0, 0, 0) <= info.date_time < (2020, 1, 1, 0, 0, 0)
                                and info.date_time[5] % 2 == 0 for info in archive.infolist()))

    def test_equal_length_entry_updates_change_zip_times_without_changing_unchanged_assets(self):
        files = build_files()
        files["index.html"] = files["index.html"].replace(b'<script ', b'<script data-build="A" ')
        def write_current():
            metadata = json.loads(files[MANIFEST])
            metadata["assets"]["index.html"] = hashlib.sha256(files["index.html"]).hexdigest()
            files[MANIFEST] = json.dumps(metadata).encode()
            self.write_build(files)
        write_current()
        first = package(self.root, BASE, SITE)
        with zipfile.ZipFile(first["zip"]) as archive:
            before = {info.filename: (info.date_time, info.file_size) for info in archive.infolist()}
        files["index.html"] = files["index.html"].replace(b'data-build="A"', b'data-build="B"')
        write_current()
        second = package(self.root, BASE, SITE)
        with zipfile.ZipFile(second["zip"]) as archive:
            after = {info.filename: (info.date_time, info.file_size) for info in archive.infolist()}
        for name in ("index.html", MANIFEST):
            self.assertEqual(before[name][1], after[name][1])
            self.assertNotEqual(before[name][0], after[name][0])
        for name in before.keys() - {"index.html", MANIFEST}:
            self.assertEqual(before[name], after[name])
        self.assertEqual(package(self.root, BASE, SITE)["sha256"], second["sha256"])

    def test_entry_files_ignore_old_cache_validators_without_changing_asset_caching(self):
        result = package(self.root, BASE, SITE)
        with zipfile.ZipFile(result["zip"]) as archive:
            access = archive.read(".htaccess").decode()
        match = re.search(r'<FilesMatch "([^"]+)">\n(.*?)</FilesMatch>', access, re.S)
        self.assertIsNotNone(match)
        pattern, block = match.groups()
        for name in ("index.html", "grantthread-build.json"):
            self.assertIsNotNone(re.fullmatch(pattern, name))
        for name in ("index-abcd.js", "index-abcd.css", "inter.woff2", "other.html", "other.json"):
            self.assertIsNone(re.fullmatch(pattern, name))
        directives = set(block.splitlines())
        self.assertTrue({
            "FileETag None", "RequestHeader unset If-Modified-Since", "RequestHeader unset If-None-Match",
            "Header unset Last-Modified", "Header always unset Last-Modified",
            "Header unset ETag", "Header always unset ETag", 'Header always set Cache-Control "no-store"',
        }.issubset(directives))
        # Validator removal must remain within the entry-only FilesMatch block.
        outside = access[:match.start()] + access[match.end():]
        for token in ("FileETag", "RequestHeader", "Last-Modified", "ETag", "Cache-Control"):
            self.assertNotIn(token, outside)

    def test_cloud_packaging_requires_site_and_preview_has_separate_name(self):
        with self.assertRaisesRegex(ReleaseError, "requires --site-url"):
            package(self.root, BASE, None)
        self.write_build(build_files({"apiUrl": "/api", "cognitoDomain": "", "cognitoClientId": "", "cognitoRedirectUri": ""}))
        with self.assertRaises(ReleaseError):
            package(self.root, BASE, SITE)
        result = package(self.root, BASE, SITE, preview=True)
        self.assertEqual(Path(result["zip"]).name, "GrantThread-preview.zip")
        self.assertFalse(result["cloudConfigured"])
        self.assertFalse((self.root / "artifacts" / "GrantThread-cpanel.zip").exists())
        with zipfile.ZipFile(result["zip"]) as archive:
            self.assertIn(b"INTERFACE PREVIEW ONLY", archive.read("DEPLOYMENT.txt"))

    def test_failed_license_check_keeps_prior_artifact_untouched(self):
        prior = package(self.root, BASE, SITE)
        payload = Path(prior["zip"]).read_bytes()
        (self.root / "frontend" / "node_modules" / "react" / "LICENSE").unlink()
        with self.assertRaisesRegex(ReleaseError, "third-party licence"):
            package(self.root, BASE, SITE)
        self.assertEqual(Path(prior["zip"]).read_bytes(), payload)

    def test_failed_replacement_keeps_prior_artifact_and_cleans_temporary(self):
        prior = package(self.root, BASE, SITE)
        payload = Path(prior["zip"]).read_bytes()
        with patch("package_cpanel.os.replace", side_effect=OSError("fixture permission failure")):
            with self.assertRaises(OSError):
                package(self.root, BASE, SITE)
        self.assertEqual(Path(prior["zip"]).read_bytes(), payload)
        self.assertEqual(list((self.root / "artifacts").glob(".grantthread-package-*")), [])

    def test_private_files_and_sourcemaps_are_rejected(self):
        for name in [".env", "assets/index.js.map", "records.json", "bank.pdf", "assets/ledger.xlsx", "assets/.private/file.js"]:
            with self.subTest(name=name):
                target = self.dist / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("private fixture", encoding="utf-8")
                with self.assertRaises(ReleaseError):
                    load_dist(self.dist)
                target.unlink()
                if name.startswith("assets/.private/"):
                    target.parent.rmdir()

    def test_possible_aws_credentials_are_rejected(self):
        (self.dist / "assets" / "index-abcd.js").write_bytes(b"AKIA" + b"A" * 16)
        with self.assertRaisesRegex(ReleaseError, "credential material"):
            load_dist(self.dist)

    def test_modified_missing_unlisted_assets_and_bad_base_are_rejected(self):
        for mutation in ["changed", "missing", "extra", "base", "metadata"]:
            with self.subTest(mutation=mutation):
                files = build_files()
                if mutation == "changed":
                    files["assets/index-abcd.js"] += b"changed"
                elif mutation == "missing":
                    del files["assets/index-abcd.js"]
                elif mutation == "extra":
                    files["assets/unlisted.js"] = b"unexpected"
                elif mutation == "base":
                    files = build_files(base="/wrong/")
                else:
                    del files[MANIFEST]
                with self.assertRaises(ReleaseError):
                    validate_build(files, BASE, SITE, preview=True)

    def test_html_asset_references_cannot_escape_base_even_when_hash_matches(self):
        files = build_files()
        files["index.html"] = b'<script src="/outside/evil.js"></script>'
        manifest = json.loads(files[MANIFEST])
        manifest["assets"]["index.html"] = hashlib.sha256(files["index.html"]).hexdigest()
        files[MANIFEST] = json.dumps(manifest).encode()
        with self.assertRaisesRegex(ReleaseError, "HTML asset paths"):
            validate_build(files, BASE, SITE, preview=False)

    def test_config_helper_refuses_to_overwrite_existing_output(self):
        source = self.root / "outputs.json"
        source.write_text(json.dumps({"ApiUrl": CONFIG["apiUrl"], "CognitoDomain": CONFIG["cognitoDomain"], "CognitoClientId": CONFIG["cognitoClientId"]}), encoding="utf-8")
        output = self.root / "public.env"
        command = [sys.executable, str(SCRIPTS / "configure_frontend.py"), "--outputs", str(source), "--site-url", SITE, "--output", str(output)]
        first = subprocess.run(command, capture_output=True, text=True, timeout=10)
        self.assertEqual(first.returncode, 0, first.stderr)
        output.write_text("preserve me", encoding="utf-8")
        second = subprocess.run(command, capture_output=True, text=True, timeout=10)
        self.assertEqual(second.returncode, 2)
        self.assertEqual(output.read_text(encoding="utf-8"), "preserve me")


if __name__ == "__main__":
    unittest.main()
