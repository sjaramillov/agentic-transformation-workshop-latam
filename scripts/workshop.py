#!/usr/bin/env python3
"""Prepare original public A–C outputs and isolated Git sources for AWS Transform."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def run(*args):
    return subprocess.check_output(args, text=True).strip()


def prepare(output, revision='HEAD'):
    output = Path(output).resolve()
    if output.exists():
        raise ValueError('El destino ya existe; elige otro para conservar la evidencia')
    sha = run('git', '-C', str(ROOT), 'rev-parse', '--verify', revision+'^{commit}')
    scenario = json.loads((ROOT/'workshop/scenario.json').read_text())
    output.mkdir(parents=True)
    for name, content in {
        'A-eventstorming.json': {k:scenario[k] for k in ('actors','events','exceptions','invariants')},
        'B-opportunities.json': {k:scenario[k] for k in ('opportunities','selected')},
        'C-workflow.json': {k:scenario[k] for k in ('selected','workflow','roles')},
    }.items():
        (output/name).write_text(json.dumps(content, indent=2, ensure_ascii=False)+'\n')
    shutil.copytree(ROOT/'workshop/contexts', output/'contexts')
    source = output/'sources/ara/booking-mit'
    source.mkdir(parents=True)
    paths = run('git','-C',str(ROOT),'ls-tree','-r','--name-only',sha,'booking_lab','LICENSE').splitlines()
    if not paths or 'booking_lab/run.py' not in paths:
        raise ValueError('La revisión no contiene el laboratorio MIT')
    hashes = {}
    for name in paths:
        if '..' in Path(name).parts:
            raise ValueError('Ruta no permitida')
        raw = subprocess.check_output(['git','-C',str(ROOT),'show',sha+':'+name])
        target = source/name
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(raw)
        hashes[name] = hashlib.sha256(raw).hexdigest()
    (source/'.gitignore').write_text('.local/\n__pycache__/\n*.pyc\n.env*\n')
    for args in [('init','-q','-b','main'),('config','user.name','MIT Workshop'),
                 ('config','user.email','workshop@example.invalid'),('add','.'),
                 ('commit','-qm','Original MIT source from '+sha)]:
        run('git','-C',str(source),*args)
    moda = output/'sources/moda/booking-mit'
    moda.parent.mkdir(parents=True)
    run('git','clone','--quiet','--no-hardlinks',str(source),str(moda))
    run('git','-C',str(moda),'remote','remove','origin')
    manifest = {'public_commit':sha,'analysis_commit':run('git','-C',str(source),'rev-parse','HEAD'),
                'source_sha256':hashes,'context_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (output/'contexts').iterdir()},
                'cloud_analysis_executed':False, 'scenario':'workshop/scenario.json'}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['prepare'])
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--revision',default='HEAD')
    args=p.parse_args()
    print(json.dumps(prepare(args.output,args.revision),indent=2))


if __name__=='__main__':
    main()
