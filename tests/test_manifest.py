import pathlib
import unittest
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).parents[1]


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.root = ET.parse(ROOT / "package.xml").getroot()
        self.ns = {"fc": "https://wiki.freecad.org/Package_Metadata"}

    def test_manifest_declares_publication_metadata(self):
        root, ns = self.root, self.ns
        self.assertEqual(root.findtext("fc:name", namespaces=ns), "McMaster-Carr Importer")
        self.assertEqual(root.findtext("fc:version", namespaces=ns), "0.1.0")
        self.assertEqual(root.findtext("fc:maintainer", namespaces=ns), "Daniel Shaw")
        self.assertEqual(root.find("fc:maintainer", ns).get("email"), "dan@danieljshaw.com")
        repository = root.find("fc:url[@type='repository']", ns)
        self.assertEqual(repository.get("branch"), "release")
        self.assertEqual(repository.text, "https://github.com/djshaw01/FreeCAD-McMasterCarr")
        self.assertEqual(root.findtext("fc:url[@type='readme']", namespaces=ns), "https://github.com/djshaw01/FreeCAD-McMasterCarr/raw/main/README.md")
        self.assertEqual(root.findtext("fc:license", namespaces=ns), "LGPL-2.1-or-later")
        self.assertEqual(root.findtext("fc:icon", namespaces=ns), "Resources/icons/McMasterCarr.svg")
        self.assertEqual({tag.text for tag in root.findall("fc:tag", ns)}, {"McMaster-Carr", "STEP", "import", "parts"})
        self.assertEqual(root.findtext("fc:content/fc:workbench/fc:freecadmin", namespaces=ns), "1.1.0")
        self.assertEqual(root.findtext("fc:content/fc:workbench/fc:classname", namespaces=ns), "McMasterCarrWorkbench")
        self.assertEqual(root.findtext("fc:content/fc:workbench/fc:subdirectory", namespaces=ns), "./")
        deps = {(d.get("type"), d.text) for d in root.findall("fc:depend", ns)}
        self.assertEqual(deps, { ("internal", "import") })
        for path in ("Init.py", "InitGui.py", "LICENSE", "README.md", "Resources/icons/McMasterCarr.svg"):
            self.assertTrue((ROOT / path).is_file(), path)


if __name__ == "__main__":
    unittest.main()
