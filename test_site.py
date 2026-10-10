"""Dependency-free checks for the published static site."""
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).parent


class Document(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.links = []
        self.assets = []
        self.h1_count = 0
        self.lang = None
        self.viewport = False

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "a":
            self.links.append(attrs.get("href", ""))
        if tag == "link" and attrs.get("rel") in ("stylesheet", "icon"):
            self.assets.append(attrs["href"])
        if tag == "h1":
            self.h1_count += 1
        if tag == "html":
            self.lang = attrs.get("lang")
        if tag == "meta" and attrs.get("name") == "viewport":
            self.viewport = True


class SiteTests(unittest.TestCase):
    def setUp(self):
        self.html = (ROOT / "index.html").read_text()
        self.document = Document()
        self.document.feed(self.html)

    def test_internal_links_and_assets(self):
        self.assertEqual(len(self.document.ids), len(set(self.document.ids)))
        for href in self.document.links:
            self.assertTrue(href)
            if href.startswith("#") and href != "#":
                self.assertIn(href[1:], self.document.ids)
            else:
                self.assertTrue(href == "#" or href.startswith("https://"), href)
        for asset in self.document.assets:
            self.assertTrue((ROOT / asset).is_file(), asset)

    def test_accessibility_and_mobile_basics(self):
        self.assertEqual(self.document.lang, "en")
        self.assertEqual(self.document.h1_count, 1)
        self.assertTrue(self.document.viewport)
        self.assertIn('class="skip-link"', self.html)
        css = (ROOT / "styles.css").read_text()
        self.assertIn(":focus-visible", css)
        self.assertIn("prefers-reduced-motion", css)
        self.assertIn("@media (max-width: 430px)", css)

    def test_current_repository_links(self):
        for repo in ("meridian", "meridian-okf-shop", "meridian-orders",
                     "meridian-payments", "meridian-storefront"):
            self.assertIn(f"https://github.com/meridian-kb-aidlc/{repo}", self.document.links)
        self.assertNotIn("dataopslabs", self.html)

    def test_qualified_claims(self):
        self.assertIn("need real A/B measurements", self.html)
        self.assertIn("not a blocking safety gate", self.html)
        self.assertIn("ILLUSTRATIVE", self.html)
        self.assertNotIn("open source", self.html.lower())


if __name__ == "__main__":
    unittest.main()
