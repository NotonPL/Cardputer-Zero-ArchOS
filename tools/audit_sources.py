#!/usr/bin/env python3
"""Read immutable GitHub files using gh. Never execute downloaded source."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]


def validate(config):
    if not re.fullmatch(r"[\w-]+/[\w.-]+", config['repository']):
        raise ValueError('invalid repository')
    if not re.fullmatch(r'[0-9a-f]{40}', config['revision']):
        raise ValueError('revision must be immutable SHA-1')
    ids = set()
    for probe in config['probe']:
        path = Path(probe['path'])
        if (path.is_absolute() or '..' in path.parts or not path.parts
                or not re.fullmatch(r'[A-Za-z0-9_.,+@/-]+', probe['path'])):
            raise ValueError('unsafe source path')
        if probe['id'] in ids:
            raise ValueError('duplicate probe')
        ids.add(probe['id'])


def inspect(probe, data):
    return dict(id=probe['id'], path=probe['path'],
                sha256=hashlib.sha256(data).hexdigest(),
                result=('found' if probe.get('needle', '').encode().lower() in data.lower()
                        else 'identifier-not-found'))


def cache_source(directory, relative_path, data):
    """Explicit opt-in source cache; no execution or installation."""
    root = directory.resolve()
    destination = root / relative_path
    if not destination.resolve().is_relative_to(root):
        raise ValueError('cache path escapes destination')
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--manifest', type=Path, default=ROOT/'hardware/sources.toml')
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--cache-dir', type=Path,
                    help='optionally save fetched sources; never executes them')
    args = ap.parse_args()
    config = tomllib.loads(args.manifest.read_text())
    validate(config)
    report = {'repository': config['repository'], 'revision': config['revision'],
              'warning': 'Source presence only; no hardware validation', 'probes': []}
    failed = False
    for probe in config['probe']:
        endpoint = f"repos/{config['repository']}/contents/{probe['path']}?ref={config['revision']}"
        proc = subprocess.run(['gh', 'api', endpoint], capture_output=True, text=True)
        if proc.returncode:
            # A network/auth error is not evidence of an absent driver.
            row = dict(id=probe['id'], path=probe['path'], result='fetch-error',
                       error=proc.stderr.strip())
            failed = True
        else:
            data = base64.b64decode(json.loads(proc.stdout)['content'])
            row = inspect(probe, data)
            if args.cache_dir:
                cache_source(args.cache_dir, probe['path'], data)
        row['url'] = f"https://github.com/{config['repository']}/blob/{config['revision']}/{probe['path']}"
        report['probes'].append(row)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
