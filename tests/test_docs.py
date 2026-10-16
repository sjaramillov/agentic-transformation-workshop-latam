from html.parser import HTMLParser
from pathlib import Path
import re
import subprocess
import unittest
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.ids, self.images = [], set(), []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        for attr in ("href", "src"):
            if attr in attrs:
                self.links.append(attrs[attr])
        if tag == "img":
            self.images.append(attrs)


class DocumentationTests(unittest.TestCase):
    @staticmethod
    def docs():
        paths=list(ROOT.glob('*.md'))+[ROOT/'evidence/mit/README.md']
        for folder in ('diagramas','assets','booking_lab','workshop','historico'):
            paths.extend((ROOT/folder).rglob('*.md'))
        return paths

    def test_bash_snippets_parse(self):
        for path in self.docs():
            for index, snippet in enumerate(re.findall(r"```bash\n(.*?)```", path.read_text(), re.S)):
                result = subprocess.run(["bash", "-n"], input=snippet, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, f"{path.name} bloque {index}: {result.stderr}")

    def test_markdown_local_links(self):
        for path in self.docs():
            for link in re.findall(r"\]\(([^)]+)\)", path.read_text()):
                parts = urlsplit(link.strip("<>"))
                if not parts.scheme and parts.path:
                    self.assertTrue((path.parent / unquote(parts.path)).exists(), f"{path.name}: {link}")

    def test_gallery_links_anchors_and_alternatives(self):
        path = ROOT / "diagramas/index.html"
        parsed = Links()
        parsed.feed(path.read_text())
        self.assertEqual(len(parsed.images), 5)
        for img in parsed.images:
            self.assertTrue(img.get("alt"))
        for link in parsed.links:
            parts = urlsplit(link)
            if not parts.scheme:
                if parts.path:
                    self.assertTrue((path.parent / parts.path).is_file(), link)
                elif parts.fragment:
                    self.assertIn(parts.fragment, parsed.ids)

    def test_svg_accessible_and_self_contained(self):
        paths = list((ROOT / "diagramas").glob("*.svg"))
        self.assertEqual(len(paths), 5)
        for path in paths:
            root = ET.fromstring(path.read_text())
            self.assertEqual(root.attrib["role"], "img")
            ids = {e.get("id") for e in root.iter() if e.get("id")}
            for name in root.attrib["aria-labelledby"].split():
                self.assertIn(name, ids)
            for element in root.iter():
                self.assertNotEqual(element.tag.rsplit("}", 1)[-1], "script")
                for value in element.attrib.values():
                    for ident in re.findall(r"url\(#([^)]*)\)", value):
                        self.assertIn(ident, ids)


if __name__ == "__main__":
    unittest.main()
