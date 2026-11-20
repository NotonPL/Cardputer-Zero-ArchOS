#!/usr/bin/env python3
"""Read-only inventory. No I2C scans, register writes, modules or root required."""
import argparse
import json
import platform
from pathlib import Path
import time


def read(path):
    try:
        return path.read_text(errors='replace').strip('\x00\n ')
    except (OSError, ValueError):
        return None


def fields(path):
    result = {}
    for line in (read(path) or '').splitlines():
        key, sep, value = line.partition(':')
        if sep:
            result[key] = value.strip()
    return result


def inventory(root):
    sys = root/'sys'
    model = read(sys/'firmware/devicetree/base/model')
    compatible = read(sys/'firmware/devicetree/base/compatible')
    devices = {}
    for bus in ('i2c', 'spi', 'usb'):
        rows = []
        for device in sorted((sys/f'bus/{bus}/devices').glob('*')):
            row = {'node': device.name}
            for key in ('name', 'modalias', 'idVendor', 'idProduct'):
                value = read(device/key)
                if value is not None:
                    row[key] = value
            driver = device/'driver'
            if driver.is_symlink():
                row['driver'] = driver.resolve().name
            rows.append(row)
        devices[bus] = rows
    return {
        'schema': 1,
        'kind': 'read-only-inventory-not-hardware-certification',
        'model': model,
        'compatible': compatible.split('\x00') if compatible else [],
        'meminfo': fields(root/'proc/meminfo'),
        'uptime': read(root/'proc/uptime'),
        'devices': devices,
        'drm': {p.parent.name: read(p) for p in sorted((sys/'class/drm').glob('*/status'))},
        'power': {p.name: {k: read(p/k) for k in ('type', 'status', 'capacity', 'voltage_now')}
                  for p in sorted((sys/'class/power_supply').glob('*'))},
        'thermal': {p.name: {'type': read(p/'type'), 'millidegrees_c': read(p/'temp')}
                    for p in sorted((sys/'class/thermal').glob('thermal_zone*'))},
        'input_devices': read(root/'proc/bus/input/devices'),
    }


def cpu_ticks(root):
    line = (read(root/'proc/stat') or '').splitlines()
    if not line or not line[0].startswith('cpu '):
        return None
    # guest and guest_nice are already included in user/nice.
    values = [int(x) for x in line[0].split()[1:9]]
    if len(values) < 5:
        return None
    return sum(values), values[3] + values[4]


def busy_percent(before, after):
    if before is None or after is None or after[0] <= before[0]:
        return None
    return round(100 * (1 - (after[1]-before[1])/(after[0]-before[0])), 3)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', type=Path, default=Path('/'), help='fixture root for tests')
    ap.add_argument('--output', required=True, type=Path)
    ap.add_argument('--label', default='inventory',
                    choices=['inventory', 'boot', 'login', 'launcher', 'hdmi', 'ssh'])
    ap.add_argument('--sample-seconds', type=float, default=1)
    args = ap.parse_args()
    if not 0.1 <= args.sample_seconds <= 60:
        ap.error('sample duration must be 0.1..60 seconds')
    result = inventory(args.root)
    before = cpu_ticks(args.root)
    start = time.monotonic()
    time.sleep(args.sample_seconds)
    after = cpu_ticks(args.root)
    result.update(label=args.label, sample_seconds=time.monotonic()-start,
                  cpu_busy_percent=busy_percent(before, after),
                  collector_machine=platform.machine(), collector_kernel=platform.release())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+'\n')


if __name__ == '__main__':
    main()
