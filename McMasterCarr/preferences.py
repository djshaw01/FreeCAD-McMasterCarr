"""McMaster-Carr workbench preferences."""

import FreeCAD as App
from PySide import QtWidgets

PARAMETER = "User parameter:BaseApp/Preferences/Mod/McMasterCarr"
KEY = "DownloadDirectory"


class PreferencesPage:
    def __init__(self):
        self.form = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(self.form)
        self.directory = QtWidgets.QLineEdit()
        button = QtWidgets.QPushButton("Browse…")
        button.clicked.connect(self._browse)
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.directory)
        row.addWidget(button)
        layout.addRow(QtWidgets.QLabel("Browser download folder (non-recursive):"), row)

    def saveSettings(self):
        App.ParamGet(PARAMETER).SetString(KEY, self.directory.text().strip())

    def loadSettings(self):
        self.directory.setText(App.ParamGet(PARAMETER).GetString(KEY, ""))

    def _browse(self):
        chosen = QtWidgets.QFileDialog.getExistingDirectory(
            self.form, "Choose browser download folder", self.directory.text().strip()
        )
        if chosen:
            self.directory.setText(chosen)
