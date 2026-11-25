#!/usr/bin/env python3
"""Compile real hash-checked patched functions against fake I2C, never real hardware."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def function(text, name):
    start = text.index('static int '+name+'(')
    brace = text.index('{', start)
    depth = 1
    end = brace+1
    # These exact hash-checked functions contain no braces inside C strings/comments.
    while depth:
        depth += (text[end] == '{') - (text[end] == '}')
        end += 1
    return text[start:end]+'\n'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--drivers', required=True, type=Path)
    args = ap.parse_args()
    lock = json.loads((ROOT/'kernel/patches/series.json').read_text())
    sources = {}
    for name, checksums in lock['files'].items():
        data = (args.drivers/name).read_bytes()
        if hashlib.sha256(data).hexdigest() != checksums['after']:
            ap.error('test requires exact patched source hashes')
        sources[name] = data.decode()
    body = (ROOT/'tests/c/bq27220_transport_prefix.h').read_text()
    for suffix in ('read', 'write', 'bulk_read', 'bulk_write'):
        body += function(sources['bq27xxx_battery_i2c.c'], 'bq27xxx_battery_i2c_'+suffix)
    body += function(sources['bq27xxx_battery.c'], 'bq27220_battery_settings')
    body += (ROOT/'tests/c/bq27220_transport_main.c').read_text()
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root/'test.c').write_text(body)
        subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                        '-Wno-unused-parameter', '-Wno-sign-compare',
                        str(root/'test.c'), '-o', str(root/'test')], check=True)
        subprocess.run([str(root/'test')], check=True)


if __name__ == '__main__':
    main()
