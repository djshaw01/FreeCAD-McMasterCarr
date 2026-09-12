# McMaster-Carr Importer

Standalone FreeCAD 1.1+ workbench for browsing McMaster-Carr in Qt WebEngine,
authenticating through McMaster, saving user-selected STEP downloads, and
importing them into the active document.

## Requirements

- FreeCAD 1.1 or later
- FreeCAD build providing `PySide6.QtWebEngineCore` and
  `PySide6.QtWebEngineWidgets`
- User-driven McMaster-Carr login and download permission

The workbench does not scrape McMaster, automate login, access private APIs, or
read credentials. WebEngine profile state is stored in FreeCAD's user data
folder and can be cleared from the browser window menu.

## Install

Copy this directory to the FreeCAD `Mod/McMasterCarr` directory, restart
FreeCAD, activate **McMaster-Carr**, and choose **McMaster-Carr → Open Catalog**.
