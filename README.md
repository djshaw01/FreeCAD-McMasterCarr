# McMaster-Carr Importer

FreeCAD workbench for browsing McMaster-Carr in system browser and automatically importing newly downloaded STEP files.

## Requirements

- FreeCAD 1.1 or later.
- Internet access to `https://www.mcmaster.com/`.
- McMaster-Carr account when download requires sign-in.

FreeCAD supplies required `PySide` Qt modules.

## Installation

1. Install repository contents in FreeCAD user `Mod/McMasterCarr`.
2. Keep `Init.py`, `InitGui.py`, and `package.xml` directly in that directory.
3. Restart FreeCAD and activate **McMaster-Carr**.

## Workflow

1. Create or open target FreeCAD document.
2. Activate **McMaster-Carr** workbench.
3. Click **Browse McMaster-Carr** in menu or toolbar.
4. On first use, choose addon destination folder. Later change it under **Edit → Preferences → McMaster-Carr**.
5. Browse, sign in, and download product **3-D STEP** in default browser.
6. Addon watches both configured destination and `~/Downloads`, moves valid files found in `~/Downloads` into configured folder, then imports them automatically.

Watcher scans direct children only. It ignores pre-existing unchanged files, browser temporary files, partial files, empty files, malformed files, and wrong suffixes. Stable files need two identical observations. Files arriving in `~/Downloads` move into configured folder with collision-safe names; failed moves preserve source file. Click **Cancel** to stop waiting. Concurrent STEP downloads can win deterministically by modification time, then path.

## Import safeguards

- Active FreeCAD document required before browsing.
- Captured document identity is enforced when import completes.
- Native FreeCAD STEP importer runs in transaction, recomputes, and fits active view.
- Changed active document, validation failures, and native import failures do not mutate wrong document.

## Privacy

Addon receives no browser cookies or credentials and does not scrape or automate McMaster-Carr. Browser authentication and downloading stay outside FreeCAD.

## Development

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q Init.py InitGui.py McMasterCarr tests
```

## License

LGPL-2.1-or-later. McMaster-Carr trademarks, website content, CAD files, and applicable usage rights remain subject to their owners' terms and licenses.
