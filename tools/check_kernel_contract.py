#!/usr/bin/env python3
"""Check the generated Kconfig, not just requested options, before compilation."""
import argparse
import hashlib
import json
from pathlib import Path
from inspect_stock_config import parse_kernel

ROOT = Path(__file__).resolve().parents[1]


def check(actual, rules):
    failures = []
    for group, allowed in [('builtin', {'y'}), ('enabled', {'y', 'm'}), ('disabled', {'n'})]:
        for symbol in rules[group]:
            key = 'CONFIG_'+symbol
            # Known forbidden symbols absent from this configuration are disabled.
            value = actual.get(key, 'n')
            if value not in allowed:
                failures.append(dict(symbol=key, actual=value, requirement=group))
    return failures


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--config', type=Path, required=True)
    ap.add_argument('--requested', type=Path, default=ROOT/'kernel/cardputer-v5.config')
    ap.add_argument('--rules', type=Path, default=ROOT/'kernel/contract.json')
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    config = args.config.read_bytes()
    actual = parse_kernel(config.decode())
    requested = parse_kernel(args.requested.read_text())
    failures = check(actual, json.loads(args.rules.read_text()))
    result = dict(success=not failures, hardware_validated=False,
                  config_sha256=hashlib.sha256(config).hexdigest(), failures=failures,
                  drift={k: dict(requested=v, actual=actual.get(k, 'n'))
                         for k, v in requested.items() if actual.get(k, 'n') != v})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    if failures:
        print(json.dumps(failures, indent=2))
    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
