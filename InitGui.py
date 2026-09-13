"""FreeCAD GUI entry point for McMaster-Carr Importer."""

import FreeCADGui as Gui


class McMasterCarrWorkbench(Workbench):
    MenuText = "McMaster-Carr"
    ToolTip = "Browse McMaster-Carr and import STEP models"
    Icon = "Resources/icons/McMasterCarr.svg"

    def GetClassName(self):
        return "Gui::PythonWorkbench"

    def Initialize(self):
        from McMasterCarr.command import BrowseCatalogCommand
        from McMasterCarr.preferences import PreferencesPage

        name = "McMasterCarr_BrowseCatalog"
        Gui.addCommand(name, BrowseCatalogCommand())
        self.appendMenu(self.MenuText, [name])
        self.appendToolbar(self.MenuText, [name])
        Gui.addPreferencePage(PreferencesPage, self.MenuText)

    def IsActive(self):
        return True


Gui.addWorkbench(McMasterCarrWorkbench())
