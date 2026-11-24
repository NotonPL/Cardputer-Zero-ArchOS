#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
case "${1:---help}" in
  --check)
    python3 -m unittest discover -s tests -v
    ;;
  --audit)
    python3 tools/audit_sources.py --output out/source-evidence.json
    ;;
  --audit-vendor)
    python3 tools/audit_sources.py --manifest hardware/vendor-sources.toml \
      --output out/vendor-evidence.json --cache-dir .cache/vendor
    python3 tools/audit_sources.py --manifest hardware/rtc-sources.toml \
      --output out/rtc-evidence.json
    python3 tools/inspect_keymap.py \
      .cache/vendor/modules/CardputerZero/cardputerzero-v5-overlay.dts \
      --output out/keymap-v5.json
    ;;
  --drivers)
    shift
    python3 tools/build_vendor_modules.py "$@"
    ;;
  --image)
    printf '%s\n' 'BLOCKED: stage 1 hardware integration is not validated.' \
      'Vendor sources found; kernel build, reviewed DT/power-off integration and real boot test still required.' \
      'No image was generated. See docs/stages.md.' >&2
    exit 2
    ;;
  --help)
    printf '%s\n' 'Stage 1: --check, --audit, --audit-vendor, --drivers [builder arguments], --image (blocked)'
    ;;
  *) printf 'Unknown option: %s\n' "$1" >&2; exit 64 ;;
esac
