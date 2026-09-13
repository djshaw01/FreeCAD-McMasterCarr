import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock


class Signal:
    def __init__(self, *args): self.slots = []
    def connect(self, slot): self.slots.append(slot)
    def emit(self, *args):
        for slot in list(self.slots): slot(*args)


class QObject:
    def __init__(self, parent=None): pass


class Timer:
    def __init__(self, parent=None): self.timeout = Signal(); self.running = False
    def setInterval(self, value): self.interval = value
    def start(self): self.running = True
    def stop(self): self.running = False


class WatcherTests(unittest.TestCase):
    def setUp(self):
        app = types.SimpleNamespace()
        qtcore = types.SimpleNamespace(QObject=QObject, Signal=Signal, QTimer=Timer)
        modules = {"FreeCAD": app, "FreeCADGui": types.SimpleNamespace(), "ImportGui": types.SimpleNamespace(), "PySide": types.SimpleNamespace(QtCore=qtcore)}
        with mock.patch.dict(sys.modules, modules):
            for name in ("McMasterCarr.watcher", "McMasterCarr.importer"): sys.modules.pop(name, None)
            self.watcher = __import__("McMasterCarr.watcher", fromlist=["DownloadWatchSession"])

    def test_new_valid_file_requires_two_stable_scans(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); session = self.watcher.DownloadWatchSession(root, "Doc"); session.start(); path = root / "new.step"; path.write_bytes(b"  ISO-10303-21;")
            with mock.patch.object(self.watcher, "import_step") as imported:
                session._scan(); imported.assert_not_called(); session._scan(); imported.assert_called_once_with(path.resolve(), "Doc")

    def test_preexisting_file_ignored_and_malformed_reconsidered(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); old = root / "old.step"; old.write_bytes(b"ISO-10303-21;"); session = self.watcher.DownloadWatchSession(root, "Doc"); session.start()
            with mock.patch.object(self.watcher, "import_step") as imported:
                session._scan(); session._scan(); imported.assert_not_called(); old.write_bytes(b"bad"); session._scan(); session._scan(); imported.assert_not_called(); old.write_bytes(b"ISO-10303-21;"); session._scan(); session._scan(); imported.assert_called_once()

    def test_empty_wrong_suffix_and_temporary_files_ignored(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); session = self.watcher.DownloadWatchSession(root, "Doc"); session.start(); (root / "empty.step").write_bytes(b""); (root / "model.pdf").write_bytes(b"ISO-10303-21;"); (root / "model.step.part").write_bytes(b"ISO-10303-21;")
            with mock.patch.object(self.watcher, "import_step") as imported: session._scan(); session._scan(); imported.assert_not_called()

    def test_cancel_stops_future_scans(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); session = self.watcher.DownloadWatchSession(root, "Doc"); session.start(); session.cancel(); (root / "new.step").write_bytes(b"ISO-10303-21;")
            with mock.patch.object(self.watcher, "import_step") as imported: session._scan(); imported.assert_not_called()

    def test_import_runtime_error_is_emitted(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); session = self.watcher.DownloadWatchSession(root, "Doc"); session.start(); (root / "new.step").write_bytes(b"ISO-10303-21;"); errors = []; session.error.connect(errors.append)
            with mock.patch.object(self.watcher, "import_step", side_effect=RuntimeError("native failed")): session._scan(); session._scan()
            self.assertEqual(errors, ["native failed"])
    def test_overwritten_existing_file_requires_two_stable_scans(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); path = root / "existing.step"; path.write_bytes(b"ISO-10303-21;")
            session = self.watcher.DownloadWatchSession(root, "Doc"); session.start(); path.write_bytes(b"ISO-10303-21; changed")
            with mock.patch.object(self.watcher, "import_step") as imported:
                session._scan(); imported.assert_not_called(); session._scan(); imported.assert_called_once()

    def test_changing_partial_file_resets_stability(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); path = root / "partial.step"; session = self.watcher.DownloadWatchSession(root, "Doc"); session.start(); path.write_bytes(b"ISO-10303-21; one")
            with mock.patch.object(self.watcher, "import_step") as imported:
                session._scan(); path.write_bytes(b"ISO-10303-21; two with more bytes"); session._scan(); imported.assert_not_called(); session._scan(); imported.assert_called_once()

    def test_simultaneous_valid_files_choose_oldest_then_path(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); old = root / "z.step"; new = root / "a.step"
            old.write_bytes(b"ISO-10303-21;"); new.write_bytes(b"ISO-10303-21;")
            session = self.watcher.DownloadWatchSession(root, "Doc"); session._initial = {}
            signatures = {old.resolve(): (14, 10), new.resolve(): (14, 20)}
            with mock.patch.object(session, "_snapshot", side_effect=[signatures, signatures]), mock.patch.object(self.watcher, "import_step") as imported:
                session._scan(); session._scan(); imported.assert_called_once_with(old.resolve(), "Doc")

    def test_equal_mtime_uses_lexical_path(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); first = root / "b.step"; second = root / "a.step"
            first.write_bytes(b"ISO-10303-21;"); second.write_bytes(b"ISO-10303-21;")
            session = self.watcher.DownloadWatchSession(root, "Doc"); session._initial = {}
            signatures = {first.resolve(): (14, 20), second.resolve(): (14, 20)}
            with mock.patch.object(session, "_snapshot", side_effect=[signatures, signatures]), mock.patch.object(self.watcher, "import_step") as imported:
                session._scan(); session._scan(); imported.assert_called_once_with(second.resolve(), "Doc")
    def test_system_download_is_moved_before_import(self):
        with tempfile.TemporaryDirectory() as destination, tempfile.TemporaryDirectory() as system:
            target = Path(destination).resolve(); source_root = Path(system).resolve(); session = self.watcher.DownloadWatchSession(target, "Doc", system_directory=source_root); session.start(); source = source_root / "part.step"; source.write_bytes(b"ISO-10303-21;")
            with mock.patch.object(self.watcher, "import_step") as imported:
                session._scan(); session._scan()
                imported.assert_called_once_with(target / "part.step", "Doc"); self.assertFalse(source.exists()); self.assertTrue((target / "part.step").exists())

    def test_system_move_collision_uses_safe_name(self):
        with tempfile.TemporaryDirectory() as destination, tempfile.TemporaryDirectory() as system:
            target = Path(destination).resolve(); source_root = Path(system).resolve(); (target / "part.step").write_bytes(b"existing"); session = self.watcher.DownloadWatchSession(target, "Doc", system_directory=source_root); session.start(); source = source_root / "part.step"; source.write_bytes(b"ISO-10303-21;")
            with mock.patch.object(self.watcher, "import_step") as imported:
                session._scan(); session._scan(); imported.assert_called_once_with(target / "part-1.step", "Doc")

    def test_failed_system_move_preserves_source(self):
        with tempfile.TemporaryDirectory() as destination, tempfile.TemporaryDirectory() as system:
            target = Path(destination).resolve(); source_root = Path(system).resolve(); session = self.watcher.DownloadWatchSession(target, "Doc", system_directory=source_root); session.start(); source = source_root / "part.step"; source.write_bytes(b"ISO-10303-21;"); errors = []; session.error.connect(errors.append)
            with mock.patch.object(self.watcher, "_relocate_exclusive", side_effect=OSError("denied")), mock.patch.object(self.watcher, "import_step") as imported:
                session._scan(); session._scan()
            imported.assert_not_called(); self.assertTrue(source.exists()); self.assertIn("Could not move STEP file: denied", errors)

    def test_reservation_race_retries_without_overwrite(self):
        with tempfile.TemporaryDirectory() as destination, tempfile.TemporaryDirectory() as system:
            target = Path(destination).resolve(); source_root = Path(system).resolve(); session = self.watcher.DownloadWatchSession(target, "Doc", system_directory=source_root); session.start(); source = source_root / "part.step"; source.write_bytes(b"ISO-10303-21;")
            real_destination_for = self.watcher._destination_for
            raced = [False]
            def destination_for(path, directory, attempt):
                candidate = real_destination_for(path, directory, attempt)
                if not raced[0]:
                    candidate.write_bytes(b"concurrent")
                    raced[0] = True
                return candidate
            with mock.patch.object(self.watcher, "_destination_for", side_effect=destination_for), mock.patch.object(self.watcher, "import_step") as imported:
                session._scan(); session._scan()
            imported.assert_called_once_with(target / "part-1.step", "Doc"); self.assertEqual((target / "part.step").read_bytes(), b"concurrent"); self.assertFalse(source.exists())
    def test_source_unlink_failure_removes_partial_destination(self):
        with tempfile.TemporaryDirectory() as destination, tempfile.TemporaryDirectory() as system:
            target = Path(destination).resolve(); source_root = Path(system).resolve(); source = source_root / "part.step"; source.write_bytes(b"ISO-10303-21;")
            real_unlink = Path.unlink
            def fail_source(path, *args, **kwargs):
                if path == source:
                    raise OSError("cannot remove source")
                return real_unlink(path, *args, **kwargs)
            with mock.patch.object(self.watcher.Path, "unlink", autospec=True, side_effect=fail_source):
                with self.assertRaisesRegex(OSError, "cannot remove source"):
                    self.watcher._relocate_exclusive(source, target)
            self.assertTrue(source.exists()); self.assertFalse((target / "part.step").exists())


if __name__ == "__main__": unittest.main()
