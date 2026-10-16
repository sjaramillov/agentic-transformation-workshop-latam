#!/usr/bin/env python3
"""Verify an exported ledger against a separately retained checkpoint and secret."""
import argparse
import json
from pathlib import Path
from audit import verify


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--snapshot',type=Path,required=True)
    p.add_argument('--checkpoint',type=Path,required=True)
    p.add_argument('--secrets',type=Path,required=True,help='Private audit.env from the lab; never commit this file')
    args=p.parse_args()
    values=dict(line.split('=',1) for line in args.secrets.read_text().splitlines() if '=' in line)
    snapshot=json.loads(args.snapshot.read_text())
    checkpoint=json.loads(args.checkpoint.read_text())
    verify(snapshot['records'],values['AUDIT_SIGNING_KEY'],checkpoint)
    print(json.dumps({'verified':True,'records':len(snapshot['records']),'checkpoint':checkpoint}))


if __name__=='__main__':
    main()
