"""Single-action McMaster-Carr browser and STEP download watcher."""
from pathlib import Path
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui, QtWidgets
from .watcher import DownloadWatchSession, system_download_directory

TITLE = "McMaster-Carr Importer"
NO_DOCUMENT = "Open or create a FreeCAD document before browsing for a STEP file."
ALREADY_WAITING = "Already waiting for a STEP download."
_active_session = None
_active_dialog = None


class _WaitingDialog(QtWidgets.QProgressDialog):
    closed = QtCore.Signal()

    def closeEvent(self, event):
        self.closed.emit()
        super().closeEvent(event)


def _clear_session():
    global _active_session, _active_dialog
    if _active_dialog is not None:
        _active_dialog.close()
    _active_dialog = None
    _active_session = None


class BrowseCatalogCommand:
    def GetResources(self):
        return {"Pixmap": "Resources/icons/McMasterCarr.svg", "MenuText": "Browse McMaster-Carr", "ToolTip": "Browse McMaster-Carr and import the next downloaded STEP file"}

    def IsActive(self):
        return True

    def Activated(self):
        global _active_session, _active_dialog
        if App.ActiveDocument is None:
            QtWidgets.QMessageBox.critical(Gui.getMainWindow(), TITLE, NO_DOCUMENT)
            return
        if _active_session is not None:
            QtWidgets.QMessageBox.information(Gui.getMainWindow(), TITLE, ALREADY_WAITING)
            return
        document_name = App.ActiveDocument.Name
        parameter = App.ParamGet("User parameter:BaseApp/Preferences/Mod/McMasterCarr")
        stored = parameter.GetString("DownloadDirectory", "").strip()
        directory = Path(stored).expanduser() if stored else None
        if directory is None or not directory.is_dir():
            initial_directory = system_download_directory() or Path.home().resolve()
            chosen = QtWidgets.QFileDialog.getExistingDirectory(Gui.getMainWindow(), "Choose browser download folder", str(initial_directory))
            if not chosen:
                return
            directory = Path(chosen)
            parameter.SetString("DownloadDirectory", str(directory))
        session = DownloadWatchSession(directory, document_name, Gui.getMainWindow())
        dialog = _WaitingDialog(f"Waiting for a STEP download in {directory}", "Cancel", 0, 0, Gui.getMainWindow())
        dialog.setAutoClose(False)
        dialog.setWindowTitle(TITLE)
        dialog.canceled.connect(session.cancel)
        dialog.closed.connect(session.cancel)
        session.error.connect(self._session_message)
        session.finished.connect(_clear_session)
        _active_session, _active_dialog = session, dialog
        session.start()
        if _active_session is None:
            return
        dialog.show()
        if not QtGui.QDesktopServices.openUrl(QtCore.QUrl("https://www.mcmaster.com/")):
            session.cancel()
            QtWidgets.QMessageBox.critical(Gui.getMainWindow(), TITLE, "Could not open McMaster-Carr in the system browser.")

    @staticmethod
    def _session_message(message):
        box = QtWidgets.QMessageBox.information if message.startswith("STEP file imported:") else QtWidgets.QMessageBox.critical
        box(Gui.getMainWindow(), TITLE, message)
