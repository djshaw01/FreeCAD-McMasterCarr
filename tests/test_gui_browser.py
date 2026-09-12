import unittest


class BrowserContractTests(unittest.TestCase):
    def test_browser_module_declares_home_url_without_importing_freecad(self):
        source = open("McMasterCarr/browser.py", encoding="utf-8").read()
        self.assertIn('HOME_URL = "https://www.mcmaster.com/"', source)
        self.assertIn("class McMasterBrowserWindow", source)
        self.assertIn("clear_session", source)


if __name__ == "__main__":
    unittest.main()
