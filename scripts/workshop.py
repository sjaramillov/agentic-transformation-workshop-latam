#!/usr/bin/env python3
"""Prepare value/AI-DLC handoffs and isolated sources from one public Git revision."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def run(*args):
    return subprocess.check_output(args, text=True).strip()


def snapshot(sha, *paths):
    """Read only files belonging to this commit, never uncommitted working copies."""
    names = run('git', '-C', str(ROOT), 'ls-tree', '-r', '--name-only', sha, '--', *paths).splitlines()
    files = {}
    for name in names:
        if Path(name).is_absolute() or '..' in Path(name).parts:
            raise ValueError('Ruta no permitida')
        files[name] = subprocess.check_output(['git', '-C', str(ROOT), 'show', sha+':'+name])
    return files


def json_bytes(value):
    return (json.dumps(value, indent=2, ensure_ascii=False)+'\n').encode('utf-8')


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def prepare(output, revision='HEAD'):
    output = Path(output).resolve()
    if output.exists():
        raise ValueError('El destino ya existe; elige otro para conservar la evidencia')
    sha = run('git', '-C', str(ROOT), 'rev-parse', '--verify', '--end-of-options', revision+'^{commit}')
    inputs = snapshot(sha, 'workshop/scenario.json', 'workshop/contexts', 'workshop/templates')
    sources = snapshot(sha, 'booking_lab', 'LICENSE')
    required = ('workshop/scenario.json', 'workshop/contexts/ara.txt', 'workshop/contexts/moda.txt')
    if any(name not in inputs for name in required) or 'booking_lab/run.py' not in sources or 'LICENSE' not in sources:
        raise ValueError('La revisión no contiene el laboratorio MIT y sus contextos completos')
    scenario = json.loads(inputs['workshop/scenario.json'])
    artifacts = {
        name: json_bytes(content) for name, content in {
            'A-eventstorming.json': {k:scenario[k] for k in ('actors','events','exceptions','invariants')},
            'B-opportunities.json': {k:scenario[k] for k in ('opportunities','selected')},
            'C-workflow.json': {k:scenario[k] for k in ('selected','workflow','roles')},
        }.items()
    }
    for name, raw in inputs.items():
        if name.startswith('workshop/contexts/') or name.startswith('workshop/templates/'):
            artifacts[name.removeprefix('workshop/')] = raw
    # Historical revisions keep their historical deliverables. New files are never
    # silently borrowed from HEAD when preparing an older source version.
    value_available = 'value_case' in scenario
    if value_available:
        value_template = 'workshop/templates/value.md'
        trace_template = 'workshop/templates/traceability.csv'
        if value_template not in inputs or trace_template not in inputs:
            raise ValueError('La revisión tiene ficha de valor pero faltan sus plantillas')
        artifacts['0-value.json'] = json_bytes(scenario['value_case'])
        artifacts['0-value-worksheet.md'] = inputs[value_template]
        columns = next(csv.reader(io.StringIO(inputs[trace_template].decode('utf-8'))))
        table = io.StringIO(newline='')
        writer = csv.DictWriter(table, fieldnames=columns, lineterminator='\n')
        writer.writeheader()
        writer.writerows(scenario['traceability'])
        artifacts['G-traceability.csv'] = table.getvalue().encode('utf-8')
        for phase in ('inception', 'construction', 'operations'):
            artifacts[f'ai-dlc/{phase}.json'] = json_bytes({
                'public_commit': sha,
                'scenario': scenario['name'],
                'value_case_id': scenario['value_case']['id'],
                'phase': phase,
                **scenario['ai_dlc'][phase],
            })
        artifacts['ai-dlc/decisions.md'] = (
            '# Registro de decisiones humanas\n\n'
            f'Commit de entrada: `{sha}`. La preparación no aprueba decisiones.\n\n'
            '| Fecha | Fase | Responsable | Decisión | Evidencia / artefactos | Riesgos y próxima revisión |\n'
            '| --- | --- | --- | --- | --- | --- |\n'
            '| Por completar | Inception | Producto / seguridad | Pendiente | | |\n'
            '| Por completar | Construction | Ingeniería / seguridad | Pendiente | | |\n'
            '| Por completar | Operations | Operaciones / producto | Pendiente | | |\n'
        ).encode('utf-8')
    output.mkdir(parents=True)
    for name, raw in artifacts.items():
        target = output/name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    source = output/'sources/ara/booking-mit'
    source.mkdir(parents=True)
    for name, raw in sources.items():
        target = source/name
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(raw)
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
                'source_sha256':{name:sha256(raw) for name,raw in sources.items()},
                'context_sha256':{name.removeprefix('contexts/'):sha256(raw) for name,raw in artifacts.items() if name.startswith('contexts/')},
                'input_sha256':{name:sha256(raw) for name,raw in inputs.items()},
                'artifact_sha256':{name:sha256(raw) for name,raw in artifacts.items()},
                'preparer_sha256':sha256(Path(__file__).read_bytes()),
                'value_and_ai_dlc_available':value_available,
                'human_decisions_approved':False,
                'cloud_analysis_executed':False, 'scenario':'workshop/scenario.json',
                'analysis_scope':['booking_lab/', 'LICENSE', 'generated .gitignore'],
                'analysis_scope_excludes':['tests/', '.github/', 'root guides', 'workshop/']}
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
