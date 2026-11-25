#!/usr/bin/env python3
"""Inspect numeric keymaps in a single consolidated vendor DTS, not a DT compiler."""
import argparse
import hashlib
import json
from pathlib import Path
import re


def inspect(text):
    # Remove comments before extracting properties; do not evaluate macros or code.
    clean = re.sub(r'/\*.*?\*/|//[^\n]*', '', text, flags=re.S)
    if re.search(r'^\s*#\s*(?:if|ifdef|ifndef|else|elif|endif|include|define|undef|pragma|error)\b',
                 clean, flags=re.M):
        raise ValueError('preprocessor directives unsupported; use a consolidated DTS')

    def cells(name):
        matches = re.findall(r'(?<![\w,-])'+re.escape(name)+r'\s*=\s*<([^<>]*)>\s*;', clean)
        if len(matches) != 1:
            raise ValueError(f'expected exactly one {name}')
        tokens = matches[0].split()
        if not tokens or any(not re.fullmatch(r'0[xX][0-9a-fA-F]+|[0-9]+', t) for t in tokens):
            raise ValueError(f'non-numeric cells in {name}')
        return [int(t, 16) if t.lower().startswith('0x') else int(t, 10) for t in tokens]

    def scalar(name):
        values = cells(name)
        if len(values) != 1:
            raise ValueError(f'expected scalar {name}')
        return values[0]

    rows, columns = scalar('keypad,num-rows'), scalar('keypad,num-columns')
    if not (1 <= rows <= 8 and 1 <= columns <= 10):
        raise ValueError('dimensions outside TCA8418 matrix')
    maps = {}
    positions = None
    for name in ('linux,keymap', 'linux,keymap1', 'linux,keymap2'):
        entries, seen = [], set()
        for value in cells(name):
            if not 0 <= value <= 0xffffffff:
                raise ValueError('cell exceeds 32 bits')
            row, column, keycode = value >> 24, (value >> 16) & 0xff, value & 0xffff
            position = (row, column)
            if row >= rows or column >= columns or position in seen:
                raise ValueError(f'out-of-range or duplicate position in {name}')
            seen.add(position)
            entries.append(dict(row=row, column=column, keycode=keycode))
        if positions is not None and seen != positions:
            raise ValueError('layer positions do not match')
        positions = seen
        maps[name] = entries
    return dict(rows=rows, columns=columns, mapped_positions=len(positions), maps=maps,
                hardware_validated=False,
                warning='Vendor numeric layers only; not proof of physical keys or FN semantics')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('source', type=Path)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    data = args.source.read_bytes()
    try:
        report = inspect(data.decode())
    except ValueError as exc:
        ap.error(str(exc))
    report['source_sha256'] = hashlib.sha256(data).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
