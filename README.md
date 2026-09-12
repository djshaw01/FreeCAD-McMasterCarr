# McMaster-Carr Importer

Standalone FreeCAD workbench for browsing McMaster-Carr in an embedded Qt
WebEngine window, signing in through McMaster-Carr, saving user-selected STEP
files, and importing them into the active FreeCAD document.

## Requirements

- FreeCAD 1.1 or later.
- A FreeCAD build that provides both `PySide6.QtWebEngineCore` and
  `PySide6.QtWebEngineWidgets`.
- Internet access to `https://www.mcmaster.com/`.
- A McMaster-Carr account when a product or CAD download requires sign-in.
- Permission to download and use McMaster-Carr CAD files.

Qt WebEngine is a runtime requirement. If it is unavailable, the workbench
shows an error and does not fall back to an external browser.

## Installation

### FreeCAD user `Mod` directory

1. Download or clone this repository.
2. Copy the repository directory into FreeCAD's user `Mod` directory, using
   `McMasterCarr` as its directory name.
3. Restart FreeCAD.
4. Select **View → Workbench → McMaster-Carr**.

The resulting layout must contain these files:

```text
Mod/
└── McMasterCarr/
    ├── Init.py
    ├── InitGui.py
    ├── package.xml
    ├── McMasterCarr/
    └── Resources/icons/McMasterCarr.svg
```

Typical user `Mod` locations are:

- **Windows:** `%APPDATA%\\FreeCAD\\Mod`
- **macOS:** `~/Library/Application Support/FreeCAD/Mod`
- **Linux:** `~/.local/share/FreeCAD/Mod` (older installations may use
  `~/.FreeCAD/Mod`)

The exact location can differ by FreeCAD package and version. Confirm the
active user data directory in FreeCAD before installing. Do not place the
repository inside another workbench's directory.

### Addon Manager

If this repository is available in your FreeCAD Addon Manager catalog, install
**McMaster-Carr Importer** there and restart FreeCAD when prompted. If the
Addon Manager does not list it, use the manual installation above.

## First use

1. Open FreeCAD.
2. Choose the **McMaster-Carr** workbench.
3. Choose **McMaster-Carr → Open Catalog**, or use the matching toolbar button.
4. The modeless catalog window opens at `https://www.mcmaster.com/`.
5. Search using McMaster-Carr's own page. Enter a full HTTPS McMaster URL in
   the address field, or enter search text such as `96924A450`.
6. Sign in only through the embedded McMaster-Carr page when prompted.

The browser provides Back, Forward, Reload, Home, tabs, an address/search
field, loading status, and popup handling. McMaster login and download cookies
stay inside the addon-owned Qt WebEngine profile. The addon never reads,
exports, or stores credentials.

## Import a STEP model

1. Open or create the FreeCAD document that should receive the model.
2. Browse to a McMaster-Carr product.
3. Choose McMaster-Carr's **3-D STEP** option. Do not use an HTML download or
   another file format.
4. When prompted, choose the destination filename in the save dialog. The
   suggested filename and `STEP files (*.step *.stp)` filter are supplied by
   the workbench.
5. Wait for the download to complete. Progress appears in the browser window;
   **Cancel STEP download** cancels an active request.
6. The workbench validates that the saved file is a regular nonempty file and
   begins with the `ISO-10303-21;` STEP exchange header.
7. On successful validation, FreeCAD's native STEP importer inserts the model
   into the document that was active when the download began, recomputes it,
   and fits the active view.

The selected file remains at the path you chose after import. The addon does
not maintain a download cache or delete the saved file.

### Document and download safeguards

- With no active document, the request is cancelled and this message appears:
  `Open or create a FreeCAD document before importing a STEP file.`
- Non-McMaster URLs, non-HTTPS downloads, and non-STEP filenames are cancelled.
- Interrupted or cancelled downloads are not imported or deleted.
- Empty, malformed, HTML, login, or non-STEP responses remain on disk but are
  not imported.
- If the original document was closed or another document became active while
  downloading, the file remains saved and is not imported into the wrong
  document.
- Only one accepted STEP download runs at a time.

## Browser controls and session management

- **Back / Forward:** move through page history.
- **Reload:** reload the current page.
- **Home:** return to McMaster-Carr's home page.
- **Tabs:** popup and new-window flows open in additional tabs. The primary
  tab cannot be closed.
- **Clear McMaster Session:** available in the browser window's menu. After
  confirmation, it clears McMaster cookies, HTTP cache, and visited links,
  removes only this addon's WebEngine storage, recreates the profile, and
  returns to the home page.

Clearing the session does not affect Safari, Chrome, Firefox, or any other
browser profile. It also does not delete STEP files saved through the file
dialog.

## Privacy and security

The workbench is deliberately user-driven:

- It displays McMaster-Carr's public website in Qt WebEngine.
- It does not scrape the DOM or depend on CSS selectors.
- It does not call private McMaster search, token, or CAD endpoints.
- It does not automate authentication or bypass access controls.
- It does not read or export cookies, credentials, or page contents.
- It accepts only user-initiated HTTPS McMaster STEP downloads.
- It refuses certificate errors rather than bypassing TLS validation.

McMaster-Carr terms, account requirements, access controls, and CAD-file
licenses still apply. Review and accept those terms yourself.

## Troubleshooting

### Workbench does not appear

- Confirm the directory is exactly `Mod/McMasterCarr`.
- Confirm `Init.py` and `InitGui.py` are directly inside that directory.
- Restart FreeCAD after copying files.
- Check FreeCAD's Python console and log for import errors.

### WebEngine dependency error

Install a FreeCAD package that includes PySide6 Qt WebEngine modules. The
required modules are:

```text
PySide6.QtWebEngineCore
PySide6.QtWebEngineWidgets
```

Installing an unrelated system PySide package may not fix a FreeCAD build that
was packaged without WebEngine support.

### Download is cancelled

The workbench accepts only an HTTPS McMaster-Carr download whose suggested
filename ends in `.step` or `.stp`. Return to the product page and select
**3-D STEP**. Ensure a FreeCAD document is active before starting the download.

### File saves but does not import

Open the saved file manually only after checking it is a valid STEP exchange
file. The workbench intentionally preserves files when validation, document
identity, or native import fails. Check the browser status message and ensure
the original document remains active until download completion.

### Login does not persist

Do not use **Clear McMaster Session** if you want to retain the session. The
profile is stored under FreeCAD's user data directory in
`McMasterCarr/WebEngine`. File permissions, private browsing behavior on the
McMaster site, or an external cleanup utility can also remove session state.

## Development and tests

Run the pure tests from repository root:

```bash
python3 -m unittest discover -s tests -v
```

Tests requiring FreeCAD and Qt WebEngine skip when those modules are not
available. They use temporary local HTML pages and never contact McMaster-Carr.

For a FreeCAD installation with bundled Python, the equivalent command is:

```bash
freecadcmd -c "import unittest; r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.discover('tests')); raise SystemExit(not r.wasSuccessful())"
```

## License

McMaster-Carr Importer is licensed under
[LGPL-2.1-or-later](LICENSE). McMaster-Carr trademarks, website content, CAD
files, and applicable usage rights remain subject to their respective owners'
terms and licenses.
