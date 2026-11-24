#!/usr/bin/env python3
"""Compile a curated driver set using Kbuild. Never install or load modules."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys

# Do not execute vendor Makefiles: their install/config_setup targets alter a live OS.
GROUPS = {
    'm5ioe1-1.0': ['m5ioe1'],
    'tca8418-1.0': ['tca8418_keypad_m5stack'],
    'st7789v-1.0': ['panel-mipi-dbi-m', 'pwm_bl_m5stack'],
    'bq27220-1.0': ['bq27xxx_battery', 'bq27xxx_battery_i2c'],
    'es8389-1.0': ['es8389_m5stack', 'simple-amplifier'],
    'CardputerZero': ['cardputerzero-audio', 'gpio-forwarder', 'powerfail_suo'],
    'imu-1.0/bmi270': ['bmi270_core', 'bmi270_i2c'],
    'imu-1.0/magnetometer': ['bmc150_magn', 'bmc150_magn_bmi270'],
}
TARGETS = [target for targets in GROUPS.values() for target in targets]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def preflight(kernel, mode):
    # Prepared kernel build directory (in-tree or O=), not a headers version guess.
    config = (kernel/'.config').read_text()
    for option in ('CONFIG_ARM64=y', 'CONFIG_MODULES=y'):
        if option not in config.splitlines():
            raise ValueError(f'missing {option}')
    for relative in ('include/generated/autoconf.h', 'include/config/auto.conf'):
        if not (kernel/relative).is_file():
            raise ValueError(f'kernel is not prepared: {relative}')
    if mode == 'modules':
        symvers = kernel/'Module.symvers'
        if not symvers.is_file() or not symvers.stat().st_size:
            raise ValueError('full module build requires nonempty Module.symvers from matching kernel build')
        if ('CONFIG_MODVERSIONS=y' in config.splitlines()
                and 'CONFIG_BASIC_MODVERSIONS=y' not in config.splitlines()):
            raise ValueError('BASIC_MODVERSIONS=y required for the current module CRC validation tools')
    return config


def stage_sources(vendor, destination):
    destination.mkdir(parents=True, exist_ok=False)
    hashes = {}
    for group, targets in GROUPS.items():
        directory = vendor/'modules'/group
        for target in targets:
            if not (directory/(target+'.c')).is_file():
                raise ValueError(f'missing driver {group}/{target}.c')
        for source in sorted(directory.iterdir()):
            if source.suffix not in ('.c', '.h'):
                continue
            if source.is_symlink() or not source.is_file():
                raise ValueError('source symlinks unsupported')
            destination_path = destination/source.name
            if destination_path.exists():
                raise ValueError(f'duplicate source basename {source.name}')
            shutil.copyfile(source, destination_path)
            hashes[f'modules/{group}/{source.name}'] = sha(destination_path)
    (destination/'Kbuild').write_text(
        '# Project-owned build rules; no vendor install hooks\n'
        'ccflags-y += -DCONFIG_CARDPUTERO_V0_5=1\n'
        + ''.join('obj-m += '+target+'.o\n' for target in TARGETS))
    return hashes


def arm64_elf(path):
    header = path.read_bytes()[:20]
    return (len(header) == 20 and header[:6] == b'\x7fELF\x02\x01'
            and struct.unpack_from('<H', header, 18)[0] == 183)


def command(kernel, stage, prefix, jobs, mode):
    return ['make', '-C', str(kernel), f'M={stage}', 'ARCH=arm64',
            f'CROSS_COMPILE={prefix}', f'-j{jobs}'] + (
                ['modules'] if mode == 'modules' else [t+'.o' for t in TARGETS])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--kernel-build', required=True, type=Path)
    ap.add_argument('--vendor-source', required=True, type=Path)
    ap.add_argument('--output', required=True, type=Path, help='new output directory')
    ap.add_argument('--cross-compile', default='aarch64-linux-gnu-')
    ap.add_argument('--jobs', type=int, default=2)
    ap.add_argument('--mode', choices=['objects', 'modules'], default='objects')
    args = ap.parse_args()
    if not 1 <= args.jobs <= 64:
        ap.error('jobs must be 1..64')
    kernel, vendor, output = (p.resolve() for p in
                              (args.kernel_build, args.vendor_source, args.output))
    if output.exists() or args.output.is_symlink():
        ap.error('output must not exist; no previous output will be overwritten')
    try:
        preflight(kernel, args.mode)
    except (ValueError, OSError) as exc:
        ap.error(str(exc))
    output.mkdir(parents=True)
    report = dict(mode=args.mode, success=False, hardware_validated=False,
                  config_sha256=sha(kernel/'.config'),
                  note='Object mode checks C API only; modules mode is not a boot or load test.')
    try:
        report['sources'] = stage_sources(vendor, output/'drivers')
        if (kernel/'Module.symvers').is_file():
            report['symvers_sha256'] = sha(kernel/'Module.symvers')
        cmd = command(kernel, output/'drivers', args.cross_compile, args.jobs, args.mode)
        report['command'] = cmd
        with (output/'build.log').open('w') as log:
            result = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT)
        report['returncode'] = result.returncode
        if result.returncode:
            raise ValueError('Kbuild failed; see build.log')
        suffix = '.ko' if args.mode == 'modules' else '.o'
        for target in TARGETS:
            artifact = output/'drivers'/(target+suffix)
            if not arm64_elf(artifact):
                raise ValueError(f'not an AArch64 ELF: {artifact.name}')
        report['success'] = True
    except (ValueError, OSError) as exc:
        report['error'] = str(exc)
        print(exc, file=sys.stderr)
    finally:
        (output/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    return 0 if report['success'] else 1


if __name__ == '__main__':
    sys.exit(main())
