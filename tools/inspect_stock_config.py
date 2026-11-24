#!/usr/bin/env python3
"""Inspect reference files only. Does not evaluate Pi firmware filters or apply config."""
import argparse
import hashlib
import json
from pathlib import Path
import re

SYMBOLS = (
    'ARM64', '64BIT', 'MODULES', 'MODVERSIONS', 'MODULE_SIG', 'PREEMPT',
    'OF', 'DEVTMPFS', 'FW_LOADER', 'I2C', 'I2C_BCM2835', 'I2C_CHARDEV',
    'SPI', 'SPI_BCM2835', 'GPIOLIB', 'GPIO_CDEV', 'PINCTRL', 'PWM',
    'REGMAP_I2C', 'REGMAP_SPI', 'DRM', 'DRM_VC4', 'DRM_MIPI_DBI',
    'DRM_FBDEV_EMULATION', 'FRAMEBUFFER_CONSOLE', 'FRAMEBUFFER_CONSOLE_DETECT_PRIMARY',
    'FONT_8x8', 'FONT_8x16', 'KEYBOARD_TCA8418', 'BATTERY_BQ27XXX',
    'SND_SOC_ES8389', 'RTC_DRV_DS1307', 'ZRAM', 'ZRAM_DEF_COMP',
    'ZSWAP', 'ZSWAP_DEFAULT_ON', 'CMA', 'CMA_SIZE_MBYTES',
)


def parse_kernel(text):
    result = {}
    for line in text.splitlines():
        assignment = re.fullmatch(r'(CONFIG_[A-Za-z0-9_]+)=(.+)', line)
        disabled = re.fullmatch(r'# (CONFIG_[A-Za-z0-9_]+) is not set', line)
        if assignment or disabled:
            key, value = assignment.groups() if assignment else (disabled[1], 'n')
            if key in result:
                raise ValueError(f'duplicate kernel option: {key}')
            result[key] = value
    if not result:
        raise ValueError('no kernel configuration options found')
    return result


def parse_boot(text):
    records, section = [], 'unfiltered'
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.split('#', 1)[0].strip()
        if not line:
            continue
        if line.startswith('[') and line.endswith(']'):
            section = line[1:-1]
            continue
        # Preserve duplicates and filter context. This is not a firmware interpreter.
        key, separator, value = line.partition('=')
        records.append(dict(line=number, section=section, key=key.strip(),
                            value=value.strip() if separator else None))
    return records


def report(kernel, boot):
    config = parse_kernel(kernel.decode())
    return dict(schema=1, kind='static-reference-not-runtime-validation',
                kernel_sha256=hashlib.sha256(kernel).hexdigest(),
                boot_sha256=hashlib.sha256(boot).hexdigest(),
                symbols={'CONFIG_'+s: config.get('CONFIG_'+s) for s in SYMBOLS},
                boot_records=parse_boot(boot.decode()),
                warnings=[
                    'Missing symbols are unknown, not automatically disabled.',
                    'Firmware filters/includes are not evaluated; records are not effective settings.',
                    'Kernel support does not prove a feature is loaded or enabled at runtime.',
                    'No ABI compatibility or bootability is certified by this report.',
                ])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--kernel', required=True, type=Path)
    ap.add_argument('--boot', required=True, type=Path)
    ap.add_argument('--output', required=True, type=Path)
    args = ap.parse_args()
    try:
        result = report(args.kernel.read_bytes(), args.boot.read_bytes())
    except ValueError as exc:
        ap.error(str(exc))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+'\n')


if __name__ == '__main__':
    main()
