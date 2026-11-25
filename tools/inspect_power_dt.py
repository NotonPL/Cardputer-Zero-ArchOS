#!/usr/bin/env python3
"""Read active powerfail DT and public driver bindings; never access raw I2C/GPIO."""
import argparse
import json
from pathlib import Path
import re
import struct

LIMIT = 4096


def blob(path):
    try:
        with path.open('rb') as stream:
            value = stream.read(LIMIT + 1)
        return value if len(value) <= LIMIT else None
    except OSError:
        return None


def text(path):
    value = blob(path)
    return value.rstrip(b'\0\n ').decode('utf-8', errors='replace') if value is not None else None


def cells(value):
    if value is None or len(value) % 4:
        return None
    return list(struct.unpack('>' + 'I' * (len(value) // 4), value))


def inspect(root):
    tree = root/'sys/firmware/devicetree/base'
    nodes = sorted({p.parent for p in tree.rglob('compatible')}) if tree.is_dir() else []
    providers = {}
    duplicates = set()
    provider_nodes = set(nodes)
    if tree.is_dir():
        for key in ('phandle', 'linux,phandle'):
            provider_nodes.update(p.parent for p in tree.rglob(key))
    for node in sorted(provider_nodes):
        for key in ('phandle', 'linux,phandle'):
            handle = cells(blob(node/key))
            if handle and len(handle) == 1:
                if handle[0] in providers and providers[handle[0]] != node:
                    duplicates.add(handle[0])
                providers[handle[0]] = node
    for handle in duplicates:
        del providers[handle]

    def gpio(node, name):
        raw = cells(blob(node/name))
        result = {'cells': raw, 'resolved': False}
        if not raw:
            return result
        provider = providers.get(raw[0])
        if provider is None:
            return result
        count = cells(blob(provider/'#gpio-cells'))
        result['provider_path'] = '/' + str(provider.relative_to(tree))
        result['provider_compatible'] = (text(provider/'compatible') or '').split('\0')
        # This collector decodes only the standard two-cell provider used here.
        if count == [2] and len(raw) == 3:
            result.update(resolved=True, offset=raw[1], flags=raw[2],
                          active_low=bool(raw[2] & 1))
        return result

    power = []
    for node in nodes:
        compatible = (text(node/'compatible') or '').split('\0')
        if 'cardputerzero,powerfail-suo' not in compatible:
            continue
        power.append({'path': '/' + str(node.relative_to(tree)),
                      'status': text(node/'status') or 'okay (DT default)',
                      'debounce_ms_cells': cells(blob(node/'debounce-ms')),
                      'irq_gpio': gpio(node, 'irq-gpios'),
                      'disabled_gpio': gpio(node, 'disabled-gpios')})
    bindings = []
    for device in sorted((root/'sys/bus/i2c/devices').glob('*-004f')):
        driver = device/'driver'
        bindings.append({'device': device.name,
                         'driver': driver.resolve().name if driver.is_symlink() else None})
    hw_id = text(root/'proc/cardputerzero_hw_id')
    if hw_id is not None and not re.fullmatch(r'0x[0-9a-fA-F]{2}', hw_id):
        hw_id = None  # Do not echo arbitrary unexpected file content.
    return {'schema': 1, 'kind': 'read-only-active-power-dt',
            'hardware_validated': False,
            'kernel_release': text(root/'proc/sys/kernel/osrelease'),
            'hw_id': hw_id, 'dt_available': tree.is_dir(),
            'powerfail_nodes': power, 'm5ioe1_bindings': bindings,
            'warnings': [
                'DT describes configuration, not electrical function or successful probe.',
                'GPIO offset is not a physical MCU pin number.',
                'No firmware-version register, raw bus, debugfs or GPIO was accessed.',
                'Missing data may mean unavailable interface or insufficient permissions.',
                'No conclusion about safe shutdown or storage integrity.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('/'), help='fixture root for offline tests')
    args = parser.parse_args()
    print(json.dumps(inspect(args.root), indent=2))


if __name__ == '__main__':
    main()
