import pathlib
import unittest
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).parents[1]


class ManifestTests(unittest.TestCase):
    def test_manifest_declares_workbench_and_dependencies(self):
        root = ET.parse(ROOT / "package.xml").getroot()
        ns = {"fc": "https://wiki.freecad.org/Package_Metadata"}
        self.assertEqual(root.findtext("fc:name", namespaces=ns), "McMaster-Carr Importer")
        self.assertEqual(root.findtext("fc:version", namespaces=ns), "0.1.0")
        self.assertEqual(root.findtext("fc:content/fc:workbench/fc:freecadmin", namespaces=ns), "1.1.0")
        self.assertEqual(root.find("fc:content/fc:workbench/fc:classname", ns).text, "McMasterCarrWorkbench")
        self.assertEqual(root.find("fc:content/fc:workbench/fc:subdirectory", ns).text, "./")
        deps = {(d.get("type"), d.text) for d in root.findall("fc:depend", ns)}
        self.assertEqual(deps, { ("internal", "import") })
        for path in ("Init.py", "InitGui.py", "LICENSE", "README.md", "Resources/icons/McMasterCarr.svg"):
            self.assertTrue((ROOT / path).is_file(), path)


if __name__ == "__main__":
    unittest.main()
