#!/usr/bin/env python3
"""Fix the observed workshop callback ordering on an isolated source copy."""
import argparse
import hashlib
import json
from pathlib import Path

OLD = '$conn->close();\n?>'
NEW = ('// Keep the connection alive until shutdown response persistence completes.\n'
       '// PHP releases it when request shutdown finishes.\n?>')


def fix(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError('Expected a regular PHP file')
    source = path.read_text()
    if NEW in source:
        return {'changed': False, 'reason': 'already corrected'}
    if (source.count(OLD) != 1 or 'register_shutdown_function(' not in source
            or 'UPDATE idempotency_keys' not in source):
        raise ValueError('Source differs from the observed pattern; review manually')
    updated = source.replace(OLD, NEW)
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    path.write_text(updated)
    return {'changed': True, 'before_sha256': before,
            'after_sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(fix(args.source), indent=2))
    except (ValueError, OSError) as error:
        parser.exit(1, str(error) + '\n')


if __name__ == '__main__':
    main()
