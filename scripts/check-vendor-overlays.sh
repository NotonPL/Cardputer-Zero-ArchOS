#!/usr/bin/env bash
# Syntax/fixup check only. Does not apply overlays to a base DTB or live system.
set -euo pipefail
if [[ $# -ne 2 ]]; then
    echo 'Usage: check-vendor-overlays.sh VENDOR_SOURCE NEW_OUTPUT_DIRECTORY' >&2
    exit 64
fi
command -v cpp >/dev/null
command -v dtc >/dev/null
command -v fdtget >/dev/null
source_root=$(realpath -- "$1")
output=$2
if [[ -e "$output" || -L "$output" ]]; then
    echo 'Output must not exist' >&2
    exit 2
fi
mkdir -p -- "$output"
printf '%s\n' 'Compile/fixup check only. Not approved for flashing or installation.' > "$output/NOT-FOR-INSTALLATION.txt"
for relative in CardputerZero/cardputerzero-v5-overlay bq27220-1.0/bq27220_v5 imu-1.0/bmi270_bmm150_overlay; do
    name=${relative##*/}
    source="$source_root/modules/$relative.dts"
    cpp -nostdinc -undef -x assembler-with-cpp -P -DCONFIG_CARDPUTERO_V0_5=1 \
        "$source" > "$output/$name.preprocessed.dts"
    dtc -@ -I dts -O dtb -o "$output/$name.dtbo" \
        "$output/$name.preprocessed.dts" 2> "$output/$name.warnings.log"
    fdtget -p "$output/$name.dtbo" /__fixups__ > "$output/$name.fixups.txt"
    sha256sum "$source" "$output/$name.dtbo" >> "$output/SHA256SUMS"
done
