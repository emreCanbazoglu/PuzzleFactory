#!/usr/bin/env python3
import json
import sys
from pathlib import Path


def fail(msg: str) -> None:
    print(f"ERROR: {msg}")
    raise SystemExit(1)


def main() -> int:
    if len(sys.argv) != 2:
        fail("usage: check_wave_isolation.py <run_config.json>")

    path = Path(sys.argv[1])
    data = json.loads(path.read_text(encoding="utf-8"))
    cells = data.get("cells", [])

    if not cells:
        fail("no cells found")

    seen = set()
    for cell in cells:
        cid = cell.get("cell_id")
        if cid in seen:
            fail(f"duplicate cell_id: {cid}")
        seen.add(cid)

        # Guardrail: no inter-cell dependency fields in generation config.
        if "depends_on_cells" in cell:
            fail(f"cell {cid} has forbidden field depends_on_cells")

    print("OK: cell isolation checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
