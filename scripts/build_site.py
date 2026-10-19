#!/usr/bin/env python3
"""Build the public workshop site from an explicit list of teaching materials."""
import argparse
import json
from pathlib import Path
import re
import shutil
import tempfile

ROOT = Path(__file__).resolve().parents[1]
REPO = 'https://github.com/sjaramillov/agentic-transformation-workshop-latam/blob/main/'
MARKER = '.workshop-site'


def build(destination):
    destination = Path(destination).absolute()
    if destination.is_symlink():
        raise ValueError('El destino no puede ser un enlace simbólico.')
    if destination.exists() and (not destination.is_dir() or not (destination/MARKER).is_file()):
        raise ValueError('El destino ya existe y no es una salida generada por build_site.py.')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.workshop-build-', dir=destination.parent) as temp:
        stage=Path(temp)/'site'
        stage.mkdir()
        for folder, pattern in [('presentacion', '*'), ('assets/presentacion', '*.svg'), ('diagramas', '*.svg')]:
            for source in sorted((ROOT/folder).glob(pattern)):
                if not source.is_file() or source.suffix not in {'.html','.css','.js','.svg'}:
                    continue
                target=stage/source.relative_to(ROOT)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
        for relative in ['assets/presentacion/workshop.png', 'diagramas/index.html', 'diagramas/estilos.css', 'examples/discovery/tableros.html', 'LICENSE']:
            target=stage/relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT/relative, target)
        gallery=stage/'diagramas/index.html'
        gallery.write_text(re.sub(r'href="\.\./([^"#]+\.md)(#[^"]*)?"', lambda m: f'href="{REPO}{m[1]}{m[2] or ""}"', gallery.read_text()), encoding='utf-8')
        home=(stage/'presentacion/index.html').read_text()
        home=home.replace('href="../', 'href="').replace('src="../', 'src="')
        home=home.replace('href="style.css"', 'href="presentacion/style.css"').replace('src="deck.js"','src="presentacion/deck.js"')
        (stage/'index.html').write_text(home, encoding='utf-8')
        (stage/'.nojekyll').write_text('')
        (stage/MARKER).write_text('Generated public workshop site.\n')
        files=sorted(str(p.relative_to(stage)) for p in stage.rglob('*') if p.is_file())
        (stage/'manifest.json').write_text(json.dumps({'files':files}, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        if destination.exists():
            shutil.rmtree(destination)
        stage.rename(destination)
    return destination


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'.local/site')
    args=parser.parse_args()
    try:
        destination=build(args.output)
    except ValueError as error:
        parser.error(str(error))
    print(f'Sitio público preparado: {destination}')


if __name__ == '__main__': main()
