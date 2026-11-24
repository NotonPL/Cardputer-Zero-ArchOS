#!/usr/bin/env bash
# Collect a kernel test bundle, NOT an OS image or pacman package.
set -euo pipefail
if [[ $# -ne 4 ]]; then
    echo 'Usage: stage-kernel-test.sh KERNEL_BUILD VENDOR_BUILD DT_RESULTS NEW_OUTPUT' >&2
    exit 64
fi
kernel=$(realpath -- "$1")
vendor=$(realpath -- "$2")
dt=$(realpath -- "$3")
out=$4
if [[ -e "$out" || -L "$out" ]]; then
    echo 'Output must not exist' >&2
    exit 2
fi
# Require the successful FULL module build, not objects or an incomplete run.
python3 - "$vendor/report.json" <<'PY'
import json, sys
report = json.load(open(sys.argv[1]))
if report.get('mode') != 'modules' or report.get('success') is not True:
    raise SystemExit('Successful modules-mode report required')
PY
release=$(make -s -C "$kernel" ARCH=arm64 CROSS_COMPILE="${CROSS_COMPILE:-aarch64-linux-gnu-}" kernelrelease)
[[ "$release" =~ ^[A-Za-z0-9._+-]+$ ]]
mkdir -p -- "$out"
out=$(realpath -- "$out")
mkdir -p "$out/root/usr/lib" "$out/kernel" "$out/licenses"
ln -s usr/lib "$out/root/lib"
# This is a fresh staging root; never install into the runner/host root.
make -C "$kernel" ARCH=arm64 CROSS_COMPILE="${CROSS_COMPILE:-aarch64-linux-gnu-}" \
    INSTALL_MOD_PATH="$out/root" modules_install > "$out/modules-install.log" 2>&1
module_root="$out/root/usr/lib/modules/$release"
mkdir -p "$module_root/extra/cardputer"
for module in "$vendor"/drivers/*.ko; do
    cp -- "$module" "$module_root/extra/cardputer/"
done
for name in build source; do
    if [[ -L "$module_root/$name" ]]; then
        unlink "$module_root/$name"
    fi
done
cat "$kernel/Module.symvers" "$vendor/drivers/Module.symvers" > "$out/combined.symvers"
depmod -b "$out/root" -e -E "$out/combined.symvers" "$release" 2> "$out/depmod.log"
if [[ -s "$out/depmod.log" ]]; then
    cat "$out/depmod.log" >&2
    exit 1
fi
test -s "$module_root/modules.dep"
cp "$kernel/arch/arm64/boot/Image" "$kernel/.config" "$out/kernel/"
cp -r -- "$dt" "$out/dt-results"
cp "$kernel/COPYING" "$out/licenses/kernel-COPYING"
cp "$kernel/LICENSES/preferred/GPL-2.0" "$out/licenses/GPL-2.0.txt"
project=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cp "$project/kernel/build-lock.json" "$out/source-lock.json"
cp "$vendor/report.json" "$out/vendor-build-report.json"
printf '%s\n' "$release" > "$out/kernelrelease.txt"
printf '%s\n' 'EXPERIMENTAL KERNEL TEST BUNDLE — NOT A BOOTABLE OS.' \
    'No rootfs, Pi boot firmware, peripheral firmware, initramfs or pacman package.' \
    'DT merge is structural only. Battery configuration writes and powerfail require review.' \
    'Do not flash or install on the factory card. No hardware validation.' > "$out/README.txt"
(cd "$out" && find kernel root -type f -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS)
