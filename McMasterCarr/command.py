"""FreeCAD command entry point with lazy Qt WebEngine loading."""

import FreeCADGui as Gui


ERROR_MESSAGE = (
    "McMaster-Carr Importer requires PySide6 Qt WebEngine. "
    "Install a FreeCAD build that provides "
    "PySide6.QtWebEngineCore and PySide6.QtWebEngineWidgets."
)

_catalog_window = None


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
        global _catalog_window
        try:
            from PySide6 import QtWidgets, QtWebEngineCore, QtWebEngineWidgets  # noqa: F401
            from .browser import McMasterBrowserWindow
            if _catalog_window is None:
                _catalog_window = McMasterBrowserWindow(Gui.getMainWindow())
            _catalog_window.show()
            _catalog_window.raise_()
            _catalog_window.activateWindow()
        except ImportError:
            from PySide6 import QtWidgets
            QtWidgets.QMessageBox.critical(None, "McMaster-Carr Importer", ERROR_MESSAGE)
        except Exception as exc:
            from PySide6 import QtWidgets
            QtWidgets.QMessageBox.critical(
                Gui.getMainWindow(),
                "McMaster-Carr Importer",
                f"Could not open McMaster-Carr catalog:\n{exc}",
            )
