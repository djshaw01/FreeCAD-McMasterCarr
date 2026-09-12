import pathlib
import sys
import types
import unittest
from unittest import mock


class Signal:
    def __init__(self, *args): self.callback = None
    def connect(self, callback): self.callback = callback
    def emit(self, *args):
        if self.callback: self.callback(*args)


class FakeRequest:
    def __init__(self, url="https://www.mcmaster.com/part.step", filename="part.step"):
        self._url, self._filename = url, filename
        self.receivedBytesChanged = Signal()
        self.totalBytesChanged = Signal()
        self.stateChanged = Signal()
        self.cancelled = self.accepted = False
        self.directory = self.name = None
    def url(self): return self._url
    def suggestedFileName(self): return self._filename
    def cancel(self): self.cancelled = True
    def setDownloadDirectory(self, value): self.directory = value
    def setDownloadFileName(self, value): self.name = value
    def accept(self): self.accepted = True
    def receivedBytes(self): return 1
    def totalBytes(self): return 2
    def interruptReasonString(self): return "network error"


class FakeWindow:
    def __init__(self): self.messages = []
    def statusBar(self): return self
    def showMessage(self, text): self.messages.append(text)


class DownloadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        qtcore = types.SimpleNamespace(QObject=type("QObject", (), {"__init__": lambda self, parent=None: None}), Signal=Signal)
        qtwidgets = types.SimpleNamespace(QFileDialog=types.SimpleNamespace(getSaveFileName=lambda *args: ("", "")))
        states = types.SimpleNamespace(DownloadInterrupted=1, DownloadCancelled=2, DownloadCompleted=3)
        webcore = types.SimpleNamespace(QWebEngineDownloadRequest=types.SimpleNamespace(DownloadState=states))
        freecad = types.SimpleNamespace(ActiveDocument=types.SimpleNamespace(Name="Doc"))
        freecadgui = types.SimpleNamespace()
        importgui = types.SimpleNamespace()
        with mock.patch.dict(sys.modules, {"PySide6": types.SimpleNamespace(QtCore=qtcore, QtWidgets=qtwidgets, QtWebEngineCore=webcore), "PySide6.QtCore": qtcore, "PySide6.QtWidgets": qtwidgets, "PySide6.QtWebEngineCore": webcore, "FreeCAD": freecad, "FreeCADGui": freecadgui, "ImportGui": importgui}):
            sys.modules.pop("McMasterCarr.downloads", None)
            import McMasterCarr.downloads as downloads
            cls.downloads = downloads

    def test_rejects_non_mcmaster_and_non_step(self):
        for request in (FakeRequest("https://example.com/a.step"), FakeRequest(filename="part.pdf")):
            self.assertFalse(self.downloads.is_allowed_download(request))

    def test_no_document_cancels_with_exact_message(self):
        self.downloads.App.ActiveDocument = None
        request, window = FakeRequest(), FakeWindow()
        controller = self.downloads.DownloadController(window)
        controller.handle_download(request)
        self.assertTrue(request.cancelled)
        self.assertEqual(window.messages[-1], self.downloads.NO_DOCUMENT)
        self.downloads.App.ActiveDocument = types.SimpleNamespace(Name="Doc")

    def test_save_cancel_does_not_accept(self):
        request, window = FakeRequest(), FakeWindow()
        with mock.patch.object(self.downloads.QtWidgets.QFileDialog, "getSaveFileName", return_value=("", "")):
            self.downloads.DownloadController(window).handle_download(request)
        self.assertTrue(request.cancelled)
        self.assertFalse(request.accepted)

    def test_accepts_selected_path_and_imports_only_on_completion(self):
        request, window = FakeRequest(), FakeWindow()
        target = pathlib.Path("/tmp/mcmaster-test.step")
        with mock.patch.object(self.downloads.QtWidgets.QFileDialog, "getSaveFileName", return_value=(str(target), "STEP files (*.step *.stp)")), mock.patch.object(self.downloads.importer, "import_step") as imported:
            controller = self.downloads.DownloadController(window)
            controller.handle_download(request)
            self.assertEqual(request.directory, "/tmp")
            self.assertEqual(request.name, target.name)
            self.assertTrue(request.accepted)
            request.stateChanged.emit(2)
            imported.assert_not_called()

    def test_completed_invalid_file_is_preserved_and_not_imported(self):
        request, window = FakeRequest(), FakeWindow()
        target = pathlib.Path("/tmp/mcmaster-invalid.step")
        target.write_text("not step")
        try:
            with mock.patch.object(self.downloads.QtWidgets.QFileDialog, "getSaveFileName", return_value=(str(target), "")), mock.patch.object(self.downloads.importer, "import_step") as imported:
                controller = self.downloads.DownloadController(window)
                controller.handle_download(request)
                request.stateChanged.emit(3)
                imported.assert_not_called()
                self.assertTrue(target.exists())
                self.assertIn("not a STEP exchange file", window.messages[-1])
        finally:
            target.unlink(missing_ok=True)


if __name__ == "__main__": unittest.main()
