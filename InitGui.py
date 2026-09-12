"""FreeCAD GUI entry point for McMaster-Carr Importer."""

import FreeCADGui as Gui


class McMasterCarrWorkbench(Gui.Workbench):
    MenuText = "McMaster-Carr"
    ToolTip = "Browse McMaster-Carr and import STEP models"
    Icon = "Resources/icons/McMasterCarr.svg"

    def GetClassName(self):
        return "Gui::PythonWorkbench"

    def Initialize(self):
        from McMasterCarr.command import OpenCatalogCommand

        Gui.addCommand("McMasterCarr_OpenCatalog", OpenCatalogCommand())
        self.appendMenu(self.MenuText, ["McMasterCarr_OpenCatalog"])
        self.appendToolbar(self.MenuText, ["McMasterCarr_OpenCatalog"])

    def IsActive(self):
        return True


Gui.addWorkbench(McMasterCarrWorkbench())
