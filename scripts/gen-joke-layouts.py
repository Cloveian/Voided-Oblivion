#!/usr/bin/env python3
"""Build the absurd arrangements: a grid of tiles with the 80% in the corner.

form-factor.md sells the modular idea with "you can have like infinite macro
keys >w<". These are that sentence, rendered. The 100% sits bottom-left with
its real legends - function row included - and every other tile is Macro.

    ./scripts/gen-joke-layouts.py

Tiles are landscape (6 wide x 5 tall), so a tiles_x by tiles_y grid is
(6*tiles_x) x (5*tiles_y) keys. The 100% is a portrait arrangement 20 columns wide, so on the 18-wide 3x2 its
last 2 columns run off the right edge and are dropped.
"""

import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
LAYOUTS = ROOT / "layouts"

TILE_W, TILE_H = 6, 5

# Light enough for black legends; distinct enough that the seams read.
PALETTE = [
    "#cfe0f7", "#f7e0cf", "#cff7e0", "#e5d5f7",
    "#f7cfd9", "#f7f3cf", "#cff3f7", "#dcf7cf",
    "#f7cfcf", "#d9cff7", "#cfd9f7", "#f0cff7",
]

# KLE properties that persist across subsequent keys.
STICKY = {"c", "t", "g", "a", "f", "f2", "p"}


def flatten(path: Path) -> list[list[tuple[str, dict]]]:
    """Rows of (legend, active-sticky-props) - properties resolved per key."""
    data = json.loads(path.read_text())
    state: dict = {}
    out = []
    for row in (r for r in data if isinstance(r, list)):
        keys = []
        for item in row:
            if isinstance(item, dict):
                state.update({k: v for k, v in item.items() if k in STICKY})
                continue
            keys.append((item, dict(state)))
        out.append(keys)
    return out


def build(tiles_x: int, tiles_y: int, base: list[list[tuple[str, dict]]]) -> list:
    cols, rows = TILE_W * tiles_x, TILE_H * tiles_y
    base_h = len(base)

    grid: list[list[tuple[str, dict]]] = []
    for r in range(rows):
        line = []
        # the 100% occupies the bottom-left, clipped to the grid width
        in_base_rows = r >= rows - base_h
        for c in range(cols):
            tile_i = (r // TILE_H) * tiles_x + (c // TILE_W)
            color = PALETTE[tile_i % len(PALETTE)]
            if in_base_rows and c < len(base[0]):
                legend, props = base[r - (rows - base_h)][c]
                props = {**props, "c": color}
            else:
                legend, props = "Macro", {"c": color, "a": 7, "f": 3}
            line.append((legend, props))
        grid.append(line)

    # emit, writing property objects only where the active state changes
    emitted: list = []
    state: dict = {}
    for line in grid:
        row_out = []
        for legend, props in line:
            diff = {k: v for k, v in props.items() if state.get(k) != v}
            if diff:
                row_out.append(diff)
                state.update(diff)
            row_out.append(legend)
        emitted.append(row_out)
    return emitted


def write(name: str, rows: list) -> None:
    body = ",\n".join("  " + json.dumps(r, ensure_ascii=False) for r in rows)
    path = LAYOUTS / name
    path.write_text("[\n" + body + "\n]\n")
    n = sum(len([k for k in r if isinstance(k, str)]) for r in rows)
    print(f"  {path.relative_to(ROOT)}: {len(rows)} rows, {n} keys")


def main() -> None:
    base = flatten(LAYOUTS / "100-percent.json")
    write("joke-3x2.json", build(3, 2, base))
    write("joke-4x3.json", build(4, 3, base))


if __name__ == "__main__":
    main()
