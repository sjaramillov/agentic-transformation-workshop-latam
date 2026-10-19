from html.parser import HTMLParser
from pathlib import Path
import sys
import tempfile
import unittest
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import build_site
import render_presentation


class Document(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.ids=set()
        self.links=[]
        self.images=[]
        self.slides=[]
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs=dict(attrs)
        if 'id' in attrs: self.ids.add(attrs['id'])
        for key in ['href','src']:
            if key in attrs: self.links.append(attrs[key])
        if tag=='img': self.images.append(attrs)
        if 'slide' in attrs.get('class','').split(): self.slides.append(attrs)


class SiteTests(unittest.TestCase):
    def test_presentation_is_current_accessible_and_portable(self):
        for name, content in render_presentation.render().items():
            with self.subTest(name=name):
                self.assertEqual((ROOT/'assets/presentacion'/name).read_text(),content)
                svg=ET.fromstring(content)
                self.assertEqual(svg.attrib['viewBox'],'0 0 1200 650')
                self.assertEqual(svg.attrib['role'],'img')
                ids={e.get('id') for e in svg.iter()}
                self.assertTrue(set(svg.attrib['aria-labelledby'].split())<=ids)
                self.assertNotIn('<script',content)
                self.assertNotIn('href=',content)

    def test_published_site_links_and_image_alternatives(self):
        with tempfile.TemporaryDirectory() as temporary:
            output=build_site.build(Path(temporary)/'site').resolve()
            pages={p:Document(p.read_text()) for p in output.rglob('*.html')}
            for path, document in pages.items():
                for image in document.images: self.assertTrue(image.get('alt'),str(path))
                for link in document.links:
                    parts=urlsplit(link)
                    if parts.scheme or parts.netloc: continue
                    target=path.parent/unquote(parts.path) if parts.path else path
                    if target.is_dir(): target/='index.html'
                    target=target.resolve()
                    self.assertTrue(target.is_relative_to(output),link)
                    self.assertTrue(target.is_file(),f'{path.name}: {link}')
                    if parts.fragment and target.suffix=='.html':
                        self.assertIn(unquote(parts.fragment),pages[target].ids,link)
            home=pages[output/'index.html']
            self.assertEqual(len(home.slides),8)
            self.assertEqual(len(home.images),7)
            self.assertTrue({'previous','next','slide-select','print'}<=home.ids)

    def test_build_excludes_private_and_runtime_material(self):
        with tempfile.TemporaryDirectory() as temporary:
            output=build_site.build(Path(temporary)/'site')
            files={p.relative_to(output).as_posix() for p in output.rglob('*') if p.is_file()}
            for name in files:
                self.assertNotRegex(name,r'(^|/)(\.git|\.local|\.env|social|resources|booking_lab|evidence)(/|$)')
            self.assertIn('assets/presentacion/workshop.png',files)
            self.assertIn('examples/discovery/tableros.html',files)
            self.assertEqual(sum(p.startswith('diagramas/') and p.endswith('.svg') for p in files),6)
            before={p.relative_to(output):p.read_bytes() for p in output.rglob('*') if p.is_file()}
            build_site.build(output)
            self.assertEqual(before,{p.relative_to(output):p.read_bytes() for p in output.rglob('*') if p.is_file()})

    def test_build_preserves_unrelated_folder_and_rejects_symlink(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination=Path(temporary)/'mine'
            destination.mkdir()
            keep=destination/'notes.txt'
            keep.write_text('keep')
            with self.assertRaises(ValueError): build_site.build(destination)
            self.assertEqual(keep.read_text(),'keep')
            link=Path(temporary)/'link'
            link.symlink_to(destination, target_is_directory=True)
            with self.assertRaises(ValueError): build_site.build(link)
            self.assertEqual(keep.read_text(),'keep')


if __name__=='__main__': unittest.main()
