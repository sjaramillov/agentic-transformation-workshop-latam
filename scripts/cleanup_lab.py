#!/usr/bin/env python3
"""Release stopped containers of one lab, preserving volumes, source and logs."""
import argparse
import json
from pathlib import Path
import re
import subprocess

SUFFIXES=('db','audit','payments','api-a','api-b','worker')


def cleanup(review,remove=False):
    review=Path(review).resolve()
    manifest=json.loads(review.read_text())
    prefix=manifest['prefix']
    if not re.fullmatch(r'db-lab-[a-f0-9]{10}',prefix) or review.parent.name!=prefix:
        raise ValueError('Expected the review.json inside its own db-lab directory')
    names=[]
    for suffix in SUFFIXES:
        name=prefix+'-'+suffix
        state=subprocess.run(['docker','inspect','-f','{{.State.Running}}',name],capture_output=True,text=True)
        if state.returncode:
            continue
        if state.stdout.strip()!='false':
            raise ValueError('Lab has a running container; stop its runner first: '+name)
        names.append(name)
    if remove:
        for name in names:
            log=subprocess.run(['docker','logs',name],capture_output=True,text=True,check=True)
            path=review.parent/(name+'.log')
            path.write_text(log.stdout+log.stderr);path.chmod(0o600)
            # No force, no volume deletion. A concurrent start makes rm fail safely.
            subprocess.run(['docker','rm',name],check=True,capture_output=True,text=True)
    return {'prefix':prefix,'containers':names,'removed':remove,'volumes_preserved':True,'logs_directory':str(review.parent)}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--review',type=Path,required=True)
    p.add_argument('--remove-stopped',action='store_true')
    args=p.parse_args()
    print(json.dumps(cleanup(args.review,args.remove_stopped),indent=2))


if __name__=='__main__':
    main()
