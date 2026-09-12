"""Native FreeCAD STEP import boundary."""

from pathlib import Path
import FreeCAD as App
import FreeCADGui as Gui
import ImportGui


def import_step(path: Path, document_name: str, report=None) -> None:
    report = report or (lambda text: None)
    document = App.getDocument(document_name)
    if document is None or App.ActiveDocument is not document:
        report("Active document changed before import; STEP file was saved but not imported.")
        return
    document.openTransaction("Import McMaster-Carr STEP")
    try:
        ImportGui.insert(str(path), document_name)
        document.recompute()
        document.commitTransaction()
    except Exception as exc:
        document.abortTransaction()
        report(f"STEP import failed: {exc}")
        return
    Gui.activeDocument().activeView().fitAll()
    report(f"STEP file saved and imported: {path}")
