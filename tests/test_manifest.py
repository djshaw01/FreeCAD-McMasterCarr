import pathlib
import unittest
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).parents[1]


class ManifestTests(unittest.TestCase):
    def test_manifest_declares_workbench_and_dependencies(self):
        root = ET.parse(ROOT / "package.xml").getroot()
        self.assertEqual(root.findtext("name"), "McMaster-Carr Importer")
        self.assertEqual(root.findtext("version"), "0.1.0")
        self.assertEqual(root.findtext("freecadmin"), "1.1.0")
        self.assertEqual(root.find("workbench/classname").text, "McMasterCarrWorkbench")
        self.assertEqual(root.find("workbench/subdirectory").text, "./")
        deps = {(d.get("type"), d.text) for d in root.findall("depend")}
        self.assertIn(("internal", "import"), deps)
        self.assertIn(("python", "PySide6-Addons"), deps)
        for path in ("Init.py", "InitGui.py", "LICENSE", "README.md", "Resources/icons/McMasterCarr.svg"):
            self.assertTrue((ROOT / path).is_file(), path)


if __name__ == "__main__":
    unittest.main()
