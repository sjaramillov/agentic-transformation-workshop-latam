#!/usr/bin/env python3
"""Operator client for the synthetic workshop; session file is a private issuer fixture."""
import argparse
import json
from pathlib import Path
import re
import uuid
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from auth import encode


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--session',type=Path,required=True)
    p.add_argument('--subject',choices=['agent-a','agent-b'],default='agent-a')
    subs=p.add_subparsers(dest='action',required=True)
    subs.add_parser('list')
    create=subs.add_parser('create')
    create.add_argument('--itinerary',default='BOG-MDE')
    create.add_argument('--amount',type=int,default=12500)
    create.add_argument('--key',required=True,help='Reuse this key for retries of the same request')
    cancel=subs.add_parser('cancel')
    cancel.add_argument('booking_id')
    args=p.parse_args()
    session=json.loads(args.session.read_text())
    if not re.fullmatch(r'db-lab-[a-f0-9]{10}',session['prefix']) or type(session['port']) is not int:
        p.error('Invalid workshop session')
    headers={'Authorization':'Bearer '+encode(session['key'],args.subject),'X-Correlation-ID':str(uuid.uuid4())}
    method,path,data='GET','/bookings',None
    if args.action=='create':
        method='POST'
        headers.update({'Content-Type':'application/json','Idempotency-Key':args.key})
        data=json.dumps({'itinerary':args.itinerary,'amount':args.amount}).encode()
    elif args.action=='cancel':
        if not re.fullmatch(r'[a-f0-9]{64}',args.booking_id):
            p.error('Invalid booking ID')
        method,path='DELETE','/bookings/'+args.booking_id
    req=Request(f'http://127.0.0.1:{session["port"]}'+path,data=data,headers=headers,method=method)
    try:
        with urlopen(req,timeout=15) as r:
            status,body=r.status,json.load(r)
    except HTTPError as e:
        status,body=e.code,json.load(e)
    print(json.dumps({'http_status':status,'body':body},indent=2))
    return 0 if status<400 else 1


if __name__=='__main__':
    raise SystemExit(main())
