"""Policy and lifecycle for user-selected McMaster STEP downloads."""

from pathlib import Path
from urllib.parse import urlparse

from PySide6 import QtCore, QtGui, QtWidgets, QtWebEngineCore
import FreeCAD as App

from . import importer

NO_DOCUMENT = "Open or create a FreeCAD document before importing a STEP file."


def is_allowed_download(request):
    url = request.url()
    parsed = urlparse(url.toString() if hasattr(url, "toString") else str(url))
    host = parsed.hostname or ""
    filename = request.suggestedFileName()
    return parsed.scheme == "https" and (host == "mcmaster.com" or host.endswith(".mcmaster.com")) and filename.lower().endswith((".step", ".stp"))


class DownloadController(QtCore.QObject):
    message = QtCore.Signal(str)

    def __init__(self, window, profile=None):
        super().__init__(window)
        self.window = window
        self.profile = profile
        self.active = None
        self.cancel_action = QtGui.QAction("Cancel STEP download", window)
        self.cancel_action.setEnabled(False)
        self.cancel_action.triggered.connect(self.cancel_active)
        window.menuBar().addAction(self.cancel_action)

    def cancel_active(self):
        if self.active is not None:
            self.active[0].cancel()
            self._report("Cancelling STEP download…")

    def set_profile(self, profile):
        self.profile = profile

    def _report(self, text):
        self.window.statusBar().showMessage(text)
        self.message.emit(text)

    def handle_download(self, request):
        if self.active is not None:
            request.cancel()
            self._report("A STEP download is already in progress.")
            return
        if not is_allowed_download(request):
            request.cancel()
            self._report("Select a 3-D STEP format on McMaster-Carr.")
            return
        document = App.ActiveDocument
        if document is None:
            request.cancel()
            self._report(NO_DOCUMENT)
            return
        filename = request.suggestedFileName()
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self.window, "Save STEP file", filename, "STEP files (*.step *.stp)")
        if not path:
            request.cancel()
            return
        target = Path(path)
        request.setDownloadDirectory(str(target.parent))
        request.setDownloadFileName(target.name)
        self.active = (request, target, document.Name)
        self.cancel_action.setEnabled(True)
        request.receivedBytesChanged.connect(self._progress)
        request.totalBytesChanged.connect(self._progress)
        request.stateChanged.connect(self._state_changed)
        request.accept()

    def _progress(self):
        if self.active:
            request = self.active[0]
            self._report(f"Downloading {request.receivedBytes()} / {request.totalBytes()} bytes")

    def _state_changed(self, state):
        if self.active is None:
            return
        request, path, document_name = self.active
        if state == QtWebEngineCore.QWebEngineDownloadRequest.DownloadState.DownloadInterrupted:
            self._report(request.interruptReasonString())
        elif state == QtWebEngineCore.QWebEngineDownloadRequest.DownloadState.DownloadCancelled:
            self._report("STEP download cancelled.")
        elif state == QtWebEngineCore.QWebEngineDownloadRequest.DownloadState.DownloadCompleted:
            if not path.is_file() or path.stat().st_size == 0:
                self._report("Downloaded file is not a STEP exchange file.")
            else:
                with path.open("rb") as stream:
                    header = stream.read(4096).lstrip()
                if not header.startswith(b"ISO-10303-21;"):
                    self._report("Downloaded file is not a STEP exchange file.")
                else:
                    try:
                        importer.import_step(path, document_name)
                    except RuntimeError as exc:
                        self._report(str(exc))
        if state in (QtWebEngineCore.QWebEngineDownloadRequest.DownloadState.DownloadInterrupted,
                     QtWebEngineCore.QWebEngineDownloadRequest.DownloadState.DownloadCancelled,
                     QtWebEngineCore.QWebEngineDownloadRequest.DownloadState.DownloadCompleted):
            self.cancel_action.setEnabled(False)
            self.active = None
