"""Offline tests for excluding private working data from AWS source staging."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from release_config import ReleaseError
from stage_sam import MODULES, SOURCE_MARKER, gather_source, stage


class SamSourceStage(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.runtime = self.root / "backend" / "grantthread"
        self.runtime.mkdir(parents=True)
        for name in MODULES:
            (self.runtime / name).write_text('"""Fictional runtime source fixture."""\n', encoding="utf-8")
        (self.runtime / "__pycache__").mkdir()
        (self.runtime / "__pycache__" / "ignored.pyc").write_bytes(b"not source")
        (self.root / "backend" / "requirements.txt").write_text("# Empty fictional requirements fixture\n", encoding="utf-8")
        (self.root / "infra").mkdir()
        (self.root / "infra" / "template.yaml").write_text(
            f"Resources:\n  Api:\n    CodeUri: {SOURCE_MARKER}\n  Worker:\n    CodeUri: {SOURCE_MARKER}\n", encoding="utf-8")
        for name in [".data/objects/private-bank.pdf", ".data/grantthread.sqlite3", "tests/private_fixture.xlsx", ".env"]:
            path = self.root / "backend" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"PRIVATE-FIXTURE-MUST-NOT-BE-STAGED")

    def test_private_backend_records_tests_and_credentials_never_enter_stage(self):
        result = stage(self.root)
        target = Path(result["template"]).parent
        expected = {"backend/grantthread/" + name for name in MODULES} | {"backend/requirements.txt", "template.yaml", "stage-manifest.json"}
        actual = {path.relative_to(target).as_posix() for path in target.rglob("*") if path.is_file()}
        self.assertEqual(actual, expected)
        self.assertFalse(any(b"PRIVATE-FIXTURE" in path.read_bytes() for path in target.rglob("*") if path.is_file()))
        self.assertEqual((target / "template.yaml").read_text(encoding="utf-8").count("CodeUri: ./backend"), 2)
        self.assertNotIn(SOURCE_MARKER, (target / "template.yaml").read_text(encoding="utf-8"))
        self.assertTrue((self.root / "backend" / ".data" / "grantthread.sqlite3").exists())

    def test_identical_sources_reuse_verified_stage_and_changes_get_new_stage(self):
        first = stage(self.root)
        self.assertEqual(stage(self.root), first)
        (self.runtime / "worker.py").write_text('"""Changed synthetic runtime fixture."""\n', encoding="utf-8")
        second = stage(self.root)
        self.assertNotEqual(first["template"], second["template"])
        self.assertTrue(Path(first["template"]).is_file())

    def test_tampered_stage_refuses_reuse(self):
        first = stage(self.root)
        (Path(first["sourceDirectory"]) / "grantthread" / "worker.py").write_text("# changed outside staging", encoding="utf-8")
        with self.assertRaisesRegex(ReleaseError, "differs"):
            stage(self.root)

    def test_unexpected_runtime_file_or_package_is_rejected(self):
        for name in ["private.xlsx", "credentials.json", "unexpected.py", "subpackage"]:
            with self.subTest(name=name):
                path = self.runtime / name
                if name == "subpackage":
                    path.mkdir()
                else:
                    path.write_text("unexpected", encoding="utf-8")
                with self.assertRaisesRegex(ReleaseError, "Unexpected runtime"):
                    gather_source(self.root)
                path.rmdir() if path.is_dir() else path.unlink()

    def test_missing_runtime_or_unexpected_template_contract_is_rejected(self):
        path = self.runtime / "worker.py"
        original = path.read_bytes()
        path.unlink()
        with self.assertRaisesRegex(ReleaseError, "missing required"):
            gather_source(self.root)
        path.write_bytes(original)
        (self.root / "infra" / "template.yaml").write_text("Resources:\n  Api:\n    CodeUri: ../backend\n", encoding="utf-8")
        with self.assertRaisesRegex(ReleaseError, "guarded CodeUri"):
            gather_source(self.root)

    def test_python_syntax_error_does_not_publish_stage(self):
        (self.runtime / "worker.py").write_text("def broken(\n", encoding="utf-8")
        with self.assertRaises(SyntaxError):
            stage(self.root)
        self.assertFalse((self.root / "artifacts").exists())

    def test_unexpected_directory_in_old_stage_is_rejected(self):
        first = stage(self.root)
        (Path(first["sourceDirectory"]) / ".data").mkdir()
        with self.assertRaisesRegex(ReleaseError, "unexpected directory"):
            stage(self.root)

    def test_failed_publication_cleans_only_owned_staging_directory(self):
        parent = self.root / "artifacts" / "sam-source"
        neighbour = parent / ".stage-neighbour"
        neighbour.mkdir(parents=True)
        marker = neighbour / "keep.txt"
        marker.write_text("preserve nearby diagnostics", encoding="utf-8")
        with patch("stage_sam.os.rename", side_effect=OSError("simulated publication failure")):
            with self.assertRaises(OSError):
                stage(self.root)
        self.assertEqual(marker.read_text(encoding="utf-8"), "preserve nearby diagnostics")
        self.assertEqual(list(parent.iterdir()), [neighbour])

    def test_failed_source_write_cleans_only_owned_staging_directory(self):
        original_open = Path.open
        def failing_open(path, *args, **kwargs):
            if path.name == "worker.py" and ".stage-" in str(path) and args and args[0] == "xb":
                raise OSError("simulated stage write failure")
            return original_open(path, *args, **kwargs)
        with patch.object(Path, "open", failing_open):
            with self.assertRaises(OSError):
                stage(self.root)
        self.assertEqual(list((self.root / "artifacts" / "sam-source").iterdir()), [])
        self.assertTrue((self.runtime / "worker.py").is_file())

    def test_racing_destination_is_preserved_and_temporary_stage_removed(self):
        from stage_sam import hashlib
        source = gather_source(self.root)
        hashes = {name: hashlib.sha256(content).hexdigest() for name, content in sorted(source.items())}
        manifest = (json.dumps({"schemaVersion": 1, "files": hashes}, sort_keys=True, indent=2) + "\n").encode()
        digest = hashlib.sha256(manifest).hexdigest()
        target = self.root / "artifacts" / "sam-source" / digest[:20]
        original_open = Path.open
        def racing_open(path, *args, **kwargs):
            if path.name == "stage-manifest.json" and args and args[0] == "xb":
                target.mkdir()
                (target / "keep.txt").write_text("concurrent owner", encoding="utf-8")
            return original_open(path, *args, **kwargs)
        with patch.object(Path, "open", racing_open):
            with self.assertRaisesRegex(ReleaseError, "created during staging"):
                stage(self.root)
        self.assertEqual((target / "keep.txt").read_text(encoding="utf-8"), "concurrent owner")
        self.assertEqual(list(target.parent.iterdir()), [target])


if __name__ == "__main__":
    unittest.main()
