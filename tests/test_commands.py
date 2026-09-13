import sys
import tempfile
import types
import unittest
from unittest import mock


class Signal:
    def __init__(self, *args): self.slots = []
    def connect(self, slot): self.slots.append(slot)
    def emit(self, *args):
        for slot in list(self.slots): slot(*args)


class QObject:
    def __init__(self, parent=None): pass


class ProgressDialog:
    def __init__(self, *args): self.canceled = Signal(); self.closed = Signal(); self.finished = Signal()
    def setAutoClose(self, value): pass
    def setWindowTitle(self, value): pass
    def show(self): pass
    def close(self): self.closed.emit()


class CommandTests(unittest.TestCase):
    def setUp(self):
        self.document = types.SimpleNamespace(Name="CapturedDoc")
        self.params = {}
        self.app = types.SimpleNamespace(ActiveDocument=self.document, ParamGet=lambda _: types.SimpleNamespace(GetString=lambda k, d="": self.params.get(k, d), SetString=lambda k, v: self.params.__setitem__(k, v)))
        self.messages = []
        box = types.SimpleNamespace(critical=lambda *a: self.messages.append(("critical", a[-1])), information=lambda *a: self.messages.append(("information", a[-1])))
        self.url = mock.Mock(return_value=True)
        self.qtcore = types.SimpleNamespace(QObject=QObject, Signal=Signal, QUrl=lambda x: x)
        self.qtgui = types.SimpleNamespace(QDesktopServices=types.SimpleNamespace(openUrl=self.url))
        self.picker = mock.Mock(return_value="")
        widgets = types.SimpleNamespace(QMessageBox=box, QFileDialog=types.SimpleNamespace(getExistingDirectory=self.picker), QProgressDialog=ProgressDialog)
        self.modules = {"FreeCAD": self.app, "FreeCADGui": types.SimpleNamespace(getMainWindow=lambda: "main"), "ImportGui": types.SimpleNamespace(), "PySide": types.SimpleNamespace(QtCore=self.qtcore, QtGui=self.qtgui, QtWidgets=widgets)}
        with mock.patch.dict(sys.modules, self.modules):
            for name in ("McMasterCarr.command", "McMasterCarr.watcher", "McMasterCarr.importer"): sys.modules.pop(name, None)
            self.command = __import__("McMasterCarr.command", fromlist=["BrowseCatalogCommand"])

    def test_no_document_is_noop(self):
        self.app.ActiveDocument = None
        self.command.BrowseCatalogCommand().Activated()
        self.assertEqual(self.messages[-1][1], self.command.NO_DOCUMENT)

    def test_empty_preference_prompts_and_cancel_is_noop(self):
        with mock.patch.object(self.command, "DownloadWatchSession") as session: self.command.BrowseCatalogCommand().Activated()
        self.picker.assert_called_once(); session.assert_not_called(); self.url.assert_not_called()

    def test_session_starts_before_browser(self):
        with tempfile.TemporaryDirectory() as folder, mock.patch.object(self.command, "DownloadWatchSession") as cls:
            self.params["DownloadDirectory"] = folder; instance = cls.return_value; instance._done = False; self.command.BrowseCatalogCommand().Activated()
        instance.start.assert_called_once_with(); self.url.assert_called_once_with("https://www.mcmaster.com/")

    def test_selected_folder_is_persisted(self):
        self.picker.return_value = tempfile.gettempdir()
        with mock.patch.object(self.command, "DownloadWatchSession") as cls:
            cls.return_value._done = True; self.command.BrowseCatalogCommand().Activated()
        self.assertEqual(self.params["DownloadDirectory"], tempfile.gettempdir())

    def test_browser_failure_cancels_session(self):
        self.url.return_value = False
        with tempfile.TemporaryDirectory() as folder, mock.patch.object(self.command, "DownloadWatchSession") as cls:
            self.params["DownloadDirectory"] = folder; cls.return_value._done = False; self.command.BrowseCatalogCommand().Activated()
        cls.return_value.cancel.assert_called_once_with()

    def test_already_waiting_message(self):
        self.command._active_session = object(); self.command.BrowseCatalogCommand().Activated()
        self.assertEqual(self.messages[-1][1], self.command.ALREADY_WAITING)

    def test_finished_clears_ownership(self):
        with tempfile.TemporaryDirectory() as folder, mock.patch.object(self.command, "DownloadWatchSession") as cls:
            self.params["DownloadDirectory"] = folder; cls.return_value._done = False; cls.return_value.finished = Signal(); self.command.BrowseCatalogCommand().Activated(); self.assertIsNotNone(self.command._active_session); cls.return_value.finished.emit()
        self.assertIsNone(self.command._active_session)

    def test_window_close_cancels_session(self):
        with tempfile.TemporaryDirectory() as folder, mock.patch.object(self.command, "DownloadWatchSession") as cls:
            self.params["DownloadDirectory"] = folder; cls.return_value._done = False; self.command.BrowseCatalogCommand().Activated(); self.command._active_dialog.close()
        cls.return_value.cancel.assert_called_once_with()


if __name__ == "__main__": unittest.main()
