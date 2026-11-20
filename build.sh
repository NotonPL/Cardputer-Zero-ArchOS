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
  --image)
    printf '%s\n' 'BLOCKED: stage 1 hardware integration is not validated.' \
      'Missing M5IOE1 integration, verified DT/keymap, battery/power-off support and real boot test.' \
      'No image was generated. See docs/stages.md.' >&2
    exit 2
    ;;
  --help)
    printf '%s\n' 'Stage 1: --check (offline tests), --audit (GitHub sources), --image (blocked)'
    ;;
  *) printf 'Unknown option: %s\n' "$1" >&2; exit 64 ;;
esac
