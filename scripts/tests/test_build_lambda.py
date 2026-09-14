"""Offline regression checks for cross-platform Lambda packaging."""
import hashlib
import json
from pathlib import Path
import stat
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from build_lambda import (MAX_UNPACKED, PLATFORMS, build, inspect_wheels, linux_requirements,
                          owned_directory, runtime_files, target_flags, write_zip)
from release_config import ReleaseError
from stage_sam import MODULES, SOURCE_MARKER


class LinuxLambdaBuild(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.wheelhouse = self.root / "wheels"
        self.wheelhouse.mkdir()

    def wheel(self, name="demo", version="1.0", tag="py3-none-any", dependencies=(), files=None, python=">=3.8"):
        path = self.wheelhouse / f"{name}-{version}-{tag}.whl"
        metadata = f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\nRequires-Python: {python}\n"
        metadata += "".join(f"Requires-Dist: {requirement}\n" for requirement in dependencies)
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr(f"{name}-{version}.dist-info/METADATA", metadata)
            archive.writestr(f"{name}/__init__.py", "# Synthetic package\n")
            for key, content in (files or {}).items():
                info = zipfile.ZipInfo(key)
                info.filename = key  # Preserve malicious backslashes on Windows.
                archive.writestr(info, content)
        return path

    def source(self):
        package = self.root / "backend" / "grantthread"
        package.mkdir(parents=True)
        for name in MODULES:
            (package / name).write_text("# Synthetic source\n", encoding="utf-8")
        (self.root / "backend" / "requirements.txt").write_text("demo==1.0\npywin32==312; sys_platform == 'win32'\n")
        (self.root / "backend" / ".data").mkdir()
        (self.root / "backend" / ".data" / "private.pdf").write_text("MUST-NOT-SHIP")
        (self.root / "infra").mkdir()
        (self.root / "infra" / "template.yaml").write_text(f"Resources:\n  A:\n    CodeUri: {SOURCE_MARKER}\n  B:\n    CodeUri: {SOURCE_MARKER}\n")
        return package

    def test_linux_markers_exclude_windows_even_when_built_on_windows(self):
        pins = linux_requirements("demo==1.0\npywin32==312; sys_platform == 'win32'\nlinux_dep==2.0; os_name == 'posix'\n")
        self.assertEqual(set(pins), {"demo", "linux-dep"})
        self.assertTrue(all(requirement.marker is None for requirement in pins.values()))
        self.assertIn("manylinux_2_34_x86_64", PLATFORMS)
        self.assertIn("manylinux2014_x86_64", PLATFORMS)
        self.assertNotIn("win_amd64", target_flags())

    def test_unpinned_urls_and_duplicate_requirements_fail_closed(self):
        for value in ["demo>=1", "demo==1.*", "demo @ https://example.com/package.whl", "demo==1\ndemo==1", "-r private.txt"]:
            with self.subTest(value=value), self.assertRaises(ReleaseError):
                linux_requirements(value)

    def test_target_metadata_enforces_linux_dependency_closure(self):
        self.wheel(dependencies=["linux-dep>=2; sys_platform == 'linux'", "pywin32; sys_platform == 'win32'"])
        pins = linux_requirements("demo==1.0")
        with self.assertRaisesRegex(ReleaseError, "closure is incomplete"):
            inspect_wheels(self.wheelhouse, pins)
        self.wheel("linux_dep", "2.0")
        pins = linux_requirements("demo==1.0\nlinux-dep==2.0")
        self.assertEqual(len(inspect_wheels(self.wheelhouse, pins)), 2)

    def test_activated_transitive_extras_are_checked(self):
        self.wheel(dependencies=["helper[crypto]>=1"])
        self.wheel("helper", dependencies=["native>=2; extra == 'crypto'"])
        pins = linux_requirements("demo==1.0\nhelper==1.0")
        with self.assertRaisesRegex(ReleaseError, "native"):
            inspect_wheels(self.wheelhouse, pins)

    def test_wrong_native_platform_or_python_is_rejected(self):
        for tag in ["cp312-cp312-win_amd64", "cp312-cp312-manylinux_2_35_x86_64", "cp311-cp311-manylinux2014_x86_64", "cp312-cp312-manylinux2014_aarch64"]:
            with self.subTest(tag=tag):
                path = self.wheel(tag=tag)
                with self.assertRaisesRegex(ReleaseError, "does not support"):
                    inspect_wheels(self.wheelhouse, linux_requirements("demo==1.0"))
                path.unlink()
        self.wheel(tag="cp39-abi3-manylinux_2_28_x86_64")
        self.assertEqual(len(inspect_wheels(self.wheelhouse, linux_requirements("demo==1.0"))), 1)

    def test_unpinned_local_extras_cannot_sneak_into_package(self):
        self.wheel()
        self.wheel("awscrt")
        with self.assertRaisesRegex(ReleaseError, "Unexpected"):
            inspect_wheels(self.wheelhouse, linux_requirements("demo==1.0"))

    def test_relocated_wheel_paths_cannot_overwrite_other_package(self):
        self.wheel(files={"shared.py": "first package code"})
        self.wheel("other", files={"other-1.0.data/purelib/shared.py": "overwriting code"})
        with self.assertRaisesRegex(ReleaseError, "overwrite one another"):
            inspect_wheels(self.wheelhouse, linux_requirements("demo==1.0\nother==1.0"))

    def test_unsafe_wheel_paths_rejected_before_pip_install(self):
        for name in ["../private.txt", "/absolute.txt", "C:/private.txt", "nested\\file.py", "nested/./alias.py"]:
            with self.subTest(name=name):
                path = self.wheel(files={name: "bad"})
                with self.assertRaisesRegex(ReleaseError, "unsafe archive path"):
                    inspect_wheels(self.wheelhouse, linux_requirements("demo==1.0"))
                path.unlink()

    def test_package_checks_native_architecture_and_size(self):
        source = self.source().parent
        package = self.root / "package"
        package.mkdir()
        native = package / "extension.so"
        native.write_bytes(b"MZ not a Linux library")
        with self.assertRaisesRegex(ReleaseError, "ELF x86_64"):
            runtime_files(package, source)
        native.write_bytes(b"\x7fELF\x02\x01" + b"\0" * 12 + b"\x3e\0")
        self.assertIn("extension.so", runtime_files(package, source))
        with patch("build_lambda.MAX_UNPACKED", 5), self.assertRaisesRegex(ReleaseError, "250 MiB"):
            runtime_files(package, source)

    def test_deterministic_zip_has_linux_file_permissions(self):
        first, second = self.root / "one.zip", self.root / "two.zip"
        write_zip(first, {"b.py": b"b", "a.py": b"a"})
        write_zip(second, {"a.py": b"a", "b.py": b"b"})
        self.assertEqual(first.read_bytes(), second.read_bytes())
        with zipfile.ZipFile(first) as archive:
            self.assertEqual(archive.namelist(), ["a.py", "b.py"])
            for info in archive.infolist():
                self.assertEqual(stat.S_IMODE(info.external_attr >> 16), 0o644)
                self.assertEqual(info.date_time, (1980, 1, 1, 0, 0, 0))

    def test_build_uses_only_staged_runtime_and_offline_pinned_install(self):
        self.source()
        self.wheel()
        commands = []
        def fake_pip(arguments):
            commands.append(arguments)
            package = Path(arguments[arguments.index("--target") + 1])
            (package / "demo").mkdir(parents=True)
            (package / "demo" / "__init__.py").write_text("# dependency\n")
            (package / "Scripts").mkdir()
            (package / "Scripts" / "generated.exe").write_bytes(b"MZ WINDOWS-LAUNCHER")
            (package / "demo-1.0.dist-info").mkdir()
            (package / "demo-1.0.dist-info" / "RECORD").write_text("host-specific-generated-script-hash")
        with patch("build_lambda.pip_run", side_effect=fake_pip):
            first = build(self.root, self.wheelhouse)
            second = build(self.root, self.wheelhouse)
        self.assertEqual(first, second)
        self.assertEqual(len(commands), 2)
        self.assertTrue(all("--no-index" in command and "--no-deps" in command for command in commands))
        manifest = json.loads(Path(first["manifest"]).read_bytes())
        self.assertFalse(manifest["linuxRuntimeVerified"])
        self.assertEqual(manifest["zipSha256"], hashlib.sha256(Path(first["zip"]).read_bytes()).hexdigest())
        with zipfile.ZipFile(first["zip"]) as archive:
            self.assertEqual(set(archive.namelist()), {"grantthread/" + name for name in MODULES} | {"demo/__init__.py"})
            self.assertFalse(any(b"MUST-NOT-SHIP" in archive.read(name) for name in archive.namelist()))

    def test_failed_build_cleans_only_owned_directory(self):
        self.source()
        self.wheel()
        parent = self.root / "artifacts" / "lambda-build"
        neighbour = parent / ".build-neighbour"
        neighbour.mkdir(parents=True)
        sentinel = neighbour / "keep.txt"
        sentinel.write_text("preserve")
        with patch("build_lambda.pip_run", side_effect=OSError("simulated install failure")):
            with self.assertRaises(OSError):
                build(self.root, self.wheelhouse)
        self.assertEqual(list(parent.iterdir()), [neighbour])
        self.assertEqual(sentinel.read_text(), "preserve")

    def test_source_changed_after_staging_cannot_be_packaged(self):
        self.source()
        self.wheel()
        def change_source(arguments):
            package = Path(arguments[arguments.index("--target") + 1])
            package.mkdir()
            staged_source = next((self.root / "artifacts" / "sam-source").glob("*/backend/grantthread/worker.py"))
            staged_source.write_text("# changed unexpectedly")
        with patch("build_lambda.pip_run", side_effect=change_source), self.assertRaisesRegex(ReleaseError, "source changed"):
            build(self.root, self.wheelhouse)
        self.assertEqual(list((self.root / "artifacts" / "lambda-build").iterdir()), [])


if __name__ == "__main__":
    unittest.main()
