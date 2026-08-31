#!/usr/bin/env python3
"""Derive the narrower arrangements from 100-percent.json.

The 100% is the source of truth. The 80% is the same board with the fourth
tile removed, so it's the first 15 columns of every row - deriving it means
a legend fix made once shows up everywhere instead of drifting.

The 60% is NOT derived: two tiles landscape is 12x5, a different key count
with its own keymap. It stays hand-maintained.

    ./scripts/derive-layouts.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
LAYOUTS = ROOT / "layouts"

# KLE properties that persist across subsequent keys rather than applying
# only to the next one. Everything else is per-key and safe to drop.
STICKY = {"c", "t", "g", "a", "f", "f2", "p"}


def take_columns(row: list, n: int) -> list:
    """First n keycaps of a KLE row, carrying the property objects with them."""
    out, pending, count = [], {}, 0
    for item in row:
        if isinstance(item, dict):
            pending.update(item)
            continue
        if count >= n:
            break
        if pending:
            out.append(pending)
            pending = {}
        out.append(item)
        count += 1
    return out


def derive(src: Path, dst: Path, cols: int) -> None:
    data = json.loads(src.read_text())
    rows = [r for r in data if isinstance(r, list)]
    out = [take_columns(r, cols) for r in rows]

    # Match the hand-written style: one row per line, so diffs stay readable.
    body = ",\n\n".join("  " + json.dumps(r, ensure_ascii=False) for r in out)
    dst.write_text("[\n" + body + "\n]\n")

    total = sum(len([k for k in r if isinstance(k, str)]) for r in out)
    print(f"  {dst.relative_to(ROOT)}: {len(out)} rows x {cols} = {total} keys")


def main() -> None:
    derive(LAYOUTS / "100-percent.json", LAYOUTS / "80-percent.json", 15)


if __name__ == "__main__":
    main()
