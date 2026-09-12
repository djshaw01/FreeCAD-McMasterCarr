import sys
import unittest
from unittest import mock


class BrowserGuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from PySide6 import QtCore, QtWidgets, QtWebEngineCore, QtWebEngineWidgets
            import FreeCAD
            import FreeCADGui
        except ImportError:
            raise unittest.SkipTest("FreeCAD Qt WebEngine unavailable")
        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        cls.app = app
        cls.QtCore = QtCore
        cls.window_type = __import__("McMasterCarr.browser", fromlist=["McMasterBrowserWindow"])

    def test_local_navigation_and_profile(self):
        browser = self.window_type.McMasterBrowserWindow(profile=self.window_type.QtWebEngineCore.QWebEngineProfile(self.window_type.QtWebEngineCore.QWebEngineProfile.NoPersistentCookies))
        browser.navigate("example local query")
        self.assertEqual(browser.current_view().url().toString(), "https://www.mcmaster.com/example%20local%20query/")
        browser.close()

    def test_popup_page_uses_same_profile(self):
        browser = self.window_type.McMasterBrowserWindow()
        popup = browser.current_page().createWindow(self.window_type.QtWebEngineCore.QWebEnginePage.WebBrowserWindow)
        self.assertIs(popup.profile(), browser._profile)
        browser.close()

    def test_session_clear_recreates_profile(self):
        browser = self.window_type.McMasterBrowserWindow()
        old = browser._profile
        with mock.patch.object(self.window_type.QtWidgets.QMessageBox, "question", return_value=self.window_type.QtWidgets.QMessageBox.StandardButton.Yes):
            browser.clear_session()
        self.assertIsNot(browser._profile, old)
        self.assertEqual(browser.current_view().url().toString(), self.window_type.HOME_URL)
        browser.close()


if __name__ == "__main__":
    unittest.main()
