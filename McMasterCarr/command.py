"""FreeCAD command entry point with lazy Qt WebEngine loading."""

import FreeCADGui as Gui


ERROR_MESSAGE = (
    "McMaster-Carr Importer requires PySide6 Qt WebEngine. "
    "Install a FreeCAD build that provides "
    "PySide6.QtWebEngineCore and PySide6.QtWebEngineWidgets."
)


class OpenCatalogCommand:
    def GetResources(self):
        return {
            "Pixmap": "Resources/icons/McMasterCarr.svg",
            "MenuText": "Open Catalog",
            "ToolTip": "Open McMaster-Carr catalog",
        }

    def IsActive(self):
        return True

    def Activated(self):
        try:
            from PySide6 import QtWebEngineCore, QtWebEngineWidgets  # noqa: F401
        except ImportError:
            Gui.showMainWindow()
            Gui.activeDocument()
            from PySide6 import QtWidgets
            QtWidgets.QMessageBox.critical(None, "McMaster-Carr Importer", ERROR_MESSAGE)
            return

        from .browser import McMasterBrowserWindow
        window = McMasterBrowserWindow(Gui.getMainWindow())
        window.show()
        window.raise_()
        window.activateWindow()
        self._window = window
