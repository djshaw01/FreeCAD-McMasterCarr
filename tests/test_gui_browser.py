import tempfile
import unittest
from pathlib import Path
from unittest import mock


class BrowserGuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from PySide6 import QtCore, QtWidgets, QtWebEngineCore
            import FreeCAD
            import FreeCADGui
        except ImportError:
            raise unittest.SkipTest("FreeCAD Qt WebEngine unavailable")
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        cls.QtCore = QtCore
        cls.QtWebEngineCore = QtWebEngineCore
        cls.browser_module = __import__("McMasterCarr.browser", fromlist=["McMasterBrowserWindow"])

    def make_browser(self):
        directory = tempfile.TemporaryDirectory()
        page = Path(directory.name) / "page.html"
        page.write_text("<html><body>local test page</body></html>", encoding="utf-8")
        profile = self.QtWebEngineCore.QWebEngineProfile("test-profile")
        profile.setPersistentStoragePath(str(Path(directory.name) / "storage"))
        profile.setCachePath(str(Path(directory.name) / "cache"))
        browser = self.browser_module.McMasterBrowserWindow(
            profile=profile,
            initial_url=self.QtCore.QUrl.fromLocalFile(str(page)).toString(),
        )
        browser._storage_dir = Path(directory.name) / "owned"
        browser._test_directory = directory
        return browser, page

    def wait_loaded(self, browser):
        loop = self.QtCore.QEventLoop()
        browser.current_page().loadFinished.connect(loop.quit)
        self.QtCore.QTimer.singleShot(5000, loop.quit)
        loop.exec()
        self.app.processEvents()

    def test_local_navigation_and_profile(self):
        browser, page = self.make_browser()
        self.wait_loaded(browser)
        self.assertEqual(browser.current_view().url().toLocalFile(), str(page))
        browser.close()

    def test_popup_page_uses_same_profile(self):
        browser, _ = self.make_browser()
        self.wait_loaded(browser)
        popup = browser.current_page().createWindow(self.QtWebEngineCore.QWebEnginePage.WebBrowserWindow)
        self.assertIs(popup.profile(), browser._profile)
        browser.close()

    def test_session_clear_recreates_profile_without_network(self):
        browser, page = self.make_browser()
        self.wait_loaded(browser)
        old = browser._profile
        local_url = self.QtCore.QUrl.fromLocalFile(str(page)).toString()
        with mock.patch.object(self.browser_module, "HOME_URL", local_url), mock.patch.object(
            self.browser_module.QtWidgets.QMessageBox, "question",
            return_value=self.browser_module.QtWidgets.QMessageBox.StandardButton.Yes,
        ):
            browser.clear_session()
            self.wait_loaded(browser)
        self.assertIsNot(browser._profile, old)
        self.assertEqual(browser.current_view().url().toLocalFile(), str(page))
        browser.close()


if __name__ == "__main__":
    unittest.main()
