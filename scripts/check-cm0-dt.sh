#!/usr/bin/env bash
# Structural DT merge only. Firmware parameters/runtime hardware remain untested.
set -euo pipefail
if [[ $# -ne 3 ]]; then
    echo 'Usage: check-cm0-dt.sh BASE_CM0_DTB OVERLAY_DIRECTORY NEW_OUTPUT_DIRECTORY' >&2
    exit 64
fi
base=$1
ov=$2
out=$3
if [[ -e "$out" || -L "$out" ]]; then
    echo 'Output must not exist' >&2
    exit 2
fi
mkdir -p -- "$out"
fdtoverlay -i "$base" -o "$out/cm0-v5.dtb" \
    "$ov/cardputerzero-v5-overlay.dtbo" \
    "$ov/bq27220_v5.dtbo" \
    "$ov/bmi270_bmm150_overlay.dtbo"
i2c=$(fdtget -t s "$out/cm0-v5.dtb" /__symbols__ i2c1)
[[ $(fdtget -t s "$out/cm0-v5.dtb" "$i2c/gpio@4f" compatible) == 'm5stack,m5ioe1' ]]
[[ $(fdtget -t s "$out/cm0-v5.dtb" "$i2c/tca8418@34" compatible) == 'm5stack,tca8418c' ]]
[[ $(fdtget -t x "$out/cm0-v5.dtb" "$i2c/rx8130@32" reg) == '32' ]]
[[ $(fdtget -t x "$out/cm0-v5.dtb" "$i2c/bq27220@55" reg) == '55' ]]
[[ $(fdtget -t x "$out/cm0-v5.dtb" "$i2c/imu@68" reg) == '68' ]]
fdtget -t s "$out/cm0-v5.dtb" / model > "$out/model.txt"
printf '%s\n' 'Structural merge passed. Not runtime or dt-schema validation. NOT FOR FLASHING.' > "$out/RESULT.txt"
sha256sum "$base" "$out/cm0-v5.dtb" > "$out/SHA256SUMS"
