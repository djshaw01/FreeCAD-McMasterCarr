import pathlib
import sys
import types
import unittest
from unittest import mock


class Document:
    Name = "Doc"
    def __init__(self): self.events = []
    def openTransaction(self, name): self.events.append(("open", name))
    def recompute(self): self.events.append("recompute")
    def commitTransaction(self): self.events.append("commit")
    def abortTransaction(self): self.events.append("abort")


class ImporterTests(unittest.TestCase):
    def test_imports_active_document_and_commits(self):
        doc = Document()
        app = types.SimpleNamespace(ActiveDocument=doc, getDocument=lambda name: doc)
        gui = types.SimpleNamespace(activeDocument=lambda: types.SimpleNamespace(activeView=lambda: types.SimpleNamespace(fitAll=lambda: None)))
        imp = types.SimpleNamespace(insert=mock.Mock())
        with mock.patch.dict(sys.modules, {"FreeCAD": app, "FreeCADGui": gui, "ImportGui": imp}):
            sys.modules.pop("McMasterCarr.importer", None)
            from McMasterCarr.importer import import_step
            import_step(pathlib.Path("x.step"), "Doc")
        imp.insert.assert_called_once_with("x.step", "Doc")
        self.assertEqual(doc.events, [("open", "Import McMaster-Carr STEP"), "recompute", "commit"])

    def test_import_aborts_on_failure(self):
        doc = Document()
        app = types.SimpleNamespace(ActiveDocument=doc, getDocument=lambda name: doc)
        gui = types.SimpleNamespace(activeDocument=lambda: None)
        imp = types.SimpleNamespace(insert=mock.Mock(side_effect=RuntimeError("bad")))
        with mock.patch.dict(sys.modules, {"FreeCAD": app, "FreeCADGui": gui, "ImportGui": imp}):
            sys.modules.pop("McMasterCarr.importer", None)
            from McMasterCarr.importer import import_step
            messages = []
            import_step(pathlib.Path("x.step"), "Doc", messages.append)
        self.assertEqual(doc.events[-1], "abort")
        self.assertIn("bad", messages[0])


if __name__ == "__main__":
    unittest.main()
