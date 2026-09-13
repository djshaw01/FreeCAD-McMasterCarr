import sys
import types
import unittest
from unittest import mock


class PreferencesTests(unittest.TestCase):
    def setUp(self):
        self.values = {}
        class LineEdit:
            def __init__(inner): inner.value = ""
            def setText(inner, value): inner.value = value
            def text(inner): return inner.value
        class Signal:
            def connect(inner, slot): inner.slot = slot
        class Button:
            def __init__(inner, text): inner.clicked = Signal()
        widgets = types.SimpleNamespace(QWidget=lambda: object(), QFormLayout=lambda _: types.SimpleNamespace(addRow=lambda *a: None), QLineEdit=LineEdit, QPushButton=Button, QHBoxLayout=lambda: types.SimpleNamespace(addWidget=lambda *a: None), QLabel=lambda x: x, QFileDialog=types.SimpleNamespace(getExistingDirectory=mock.Mock(return_value="")))
        app = types.SimpleNamespace(ParamGet=lambda _: types.SimpleNamespace(GetString=lambda k, d="": self.values.get(k, d), SetString=lambda k, v: self.values.__setitem__(k, v)))
        with mock.patch.dict(sys.modules, {"FreeCAD": app, "PySide": types.SimpleNamespace(QtWidgets=widgets)}):
            sys.modules.pop("McMasterCarr.preferences", None)
            self.preferences = __import__("McMasterCarr.preferences", fromlist=["PreferencesPage"])

    def test_load_and_save_exact_key(self):
        self.values["DownloadDirectory"] = " /tmp/downloads "
        page = self.preferences.PreferencesPage(); page.loadSettings(); self.assertEqual(page.directory.text(), " /tmp/downloads ")
        page.directory.setText(" /chosen "); page.saveSettings(); self.assertEqual(self.values["DownloadDirectory"], "/chosen")

    def test_picker_cancel_preserves_value(self):
        page = self.preferences.PreferencesPage(); page.directory.setText("/prior")
        page._browse(); self.assertEqual(page.directory.text(), "/prior")

    def test_picker_success_updates_field(self):
        self.preferences.QtWidgets.QFileDialog.getExistingDirectory.return_value = "/new"
        page = self.preferences.PreferencesPage(); page._browse(); self.assertEqual(page.directory.text(), "/new")


if __name__ == "__main__": unittest.main()
