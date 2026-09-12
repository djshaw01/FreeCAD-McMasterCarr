"""Embedded McMaster-Carr browser using an addon-owned WebEngine profile."""

from pathlib import Path
from urllib.parse import quote, urlparse
import shutil

import FreeCAD as App
from PySide6 import QtCore, QtWidgets, QtWebEngineCore, QtWebEngineWidgets

from .downloads import DownloadController

HOME_URL = "https://www.mcmaster.com/"


def _is_mcmaster_url(value):
    parsed = urlparse(value)
    return parsed.scheme == "https" and (
        parsed.hostname == "mcmaster.com"
        or (parsed.hostname or "").endswith(".mcmaster.com")
    )


class BrowserPage(QtWebEngineCore.QWebEnginePage):
    def __init__(self, profile, owner):
        super().__init__(profile, owner)
        self.owner = owner

    def createWindow(self, window_type):
        return self.owner.add_tab().page()

    def certificateError(self, error):
        self.owner._status.setText(f"TLS certificate error: {error.errorDescription()}")
        return False

    def renderProcessTerminated(self, termination_status, exit_code):
        self.owner._status.setText(f"Renderer terminated (exit code {exit_code})")


class BrowserView(QtWebEngineWidgets.QWebEngineView):
    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner

    def createWindow(self, window_type):
        return self.owner.add_tab()


class McMasterBrowserWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None, profile=None):
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.setWindowTitle("McMaster-Carr")
        self.resize(1200, 800)
        self._storage_dir = Path(App.getUserAppDataDir()) / "McMasterCarr" / "WebEngine"
        self._profile = profile or self._new_profile()
        self._download_controller = DownloadController(self)
        self._profile.downloadRequested.connect(self._download_controller.handle_download)
        self._tabs = QtWidgets.QTabWidget()
        self._tabs.setTabsClosable(True)
        self._tabs.tabCloseRequested.connect(self.close_tab)
        self._tabs.currentChanged.connect(self._sync_url)
        self.setCentralWidget(self._tabs)
        self._build_toolbar()
        self._build_menu()
        self.add_tab("Catalog", HOME_URL)

    def _new_profile(self):
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        profile = QtWebEngineCore.QWebEngineProfile("McMasterCarr", self)
        profile.setPersistentStoragePath(str(self._storage_dir / "Storage"))
        profile.setCachePath(str(self._storage_dir / "Cache"))
        profile.setPersistentCookiesPolicy(
            QtWebEngineCore.QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies
        )
        return profile

    def _build_toolbar(self):
        toolbar = self.addToolBar("Navigation")
        for label, slot in (("Back", lambda: self.current_view().back()),
                            ("Forward", lambda: self.current_view().forward()),
                            ("Reload", lambda: self.current_view().reload()),
                            ("Home", lambda: self.navigate(HOME_URL))):
            action = QtGui.QAction(label, self)
            action.triggered.connect(slot)
            toolbar.addAction(action)
        self._address = QtWidgets.QLineEdit()
        self._address.returnPressed.connect(lambda: self.navigate(self._address.text()))
        toolbar.addWidget(self._address)
        self._status = QtWidgets.QLabel()
        toolbar.addWidget(self._status)

    def _build_menu(self):
        menu = self.menuBar().addMenu("McMaster-Carr")
        clear = menu.addAction("Clear McMaster Session")
        clear.triggered.connect(self.clear_session)

    def add_tab(self, title="New tab", url=HOME_URL):
        view = BrowserView(self)
        page = BrowserPage(self._profile, self)
        view.setPage(page)
        page.urlChanged.connect(lambda value, v=view: self._url_changed(v, value))
        page.loadStarted.connect(lambda: self._status.setText("Loading…"))
        page.loadProgress.connect(lambda value: self._status.setText(f"Loading {value}%"))
        page.loadFinished.connect(lambda ok: self._status.setText("Ready" if ok else "Page failed to load"))
        page.loadingChanged.connect(self._loading_changed)
        index = self._tabs.addTab(view, title)
        self._tabs.setCurrentIndex(index)
        view.setUrl(QtCore.QUrl(url))
        return view

    def _loading_changed(self, event):
        if event.status() == QtWebEngineCore.QWebEngineLoadingInfo.LoadStatus.LoadFailedStatus:
            self._status.setText(event.errorString())

    def _url_changed(self, view, url):
        if view is self.current_view():
            self._address.setText(url.toString())

    def _sync_url(self, index):
        if index >= 0:
            self._address.setText(self.current_view().url().toString())

    def current_view(self):
        return self._tabs.currentWidget()

    def current_page(self):
        return self.current_view().page()

    def navigate(self, value):
        value = value.strip()
        target = value if _is_mcmaster_url(value) else HOME_URL + quote(value, safe="") + "/"
        self.current_view().setUrl(QtCore.QUrl(target))

    def close_tab(self, index):
        if self._tabs.count() == 1:
            return
        widget = self._tabs.widget(index)
        self._tabs.removeTab(index)
        widget.deleteLater()

    def clear_session(self):
        if QtWidgets.QMessageBox.question(self, "Clear McMaster Session", "Clear saved McMaster session?") != QtWidgets.QMessageBox.StandardButton.Yes:
            return
        old = self._profile
        for index in range(self._tabs.count() - 1, -1, -1):
            if index:
                self.close_tab(index)
        old.cookieStore().deleteAllCookies()
        old.clearHttpCache()
        old.clearAllVisitedLinks()
        for index in range(self._tabs.count()):
            self._tabs.widget(index).page().deleteLater()
        old.deleteLater()
        QtWidgets.QApplication.processEvents()
        shutil.rmtree(self._storage_dir, ignore_errors=True)
        self._profile = self._new_profile()
        self._download_controller.set_profile(self._profile)
        self._profile.downloadRequested.connect(self._download_controller.handle_download)
        view = self.current_view()
        page = BrowserPage(self._profile, self)
        view.setPage(page)
        page.urlChanged.connect(lambda value, v=view: self._url_changed(v, value))
        view.setUrl(QtCore.QUrl(HOME_URL))

from PySide6 import QtGui
