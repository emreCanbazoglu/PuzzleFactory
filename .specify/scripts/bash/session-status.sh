#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT_DIR"

echo "== Current branch =="
git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "(no git branch)"

echo
echo "== Specs with open tasks =="
for file in specs/*/tasks.md; do
  [ -f "$file" ] || continue
  total=$(grep -c "^- \[" "$file" || true)
  open=$(grep -c "^- \[ \]" "$file" || true)
  done=$(grep -c "^- \[x\]" "$file" || true)
  if [ "$total" -gt 0 ]; then
    echo "$file -> open: $open, done: $done, total: $total"
  fi
done

echo
echo "== Wave 001 execution log (last 20 lines) =="
if [ -f runs/wave_001/execution_log.md ]; then
  tail -n 20 runs/wave_001/execution_log.md
else
  echo "runs/wave_001/execution_log.md not found"
fi
