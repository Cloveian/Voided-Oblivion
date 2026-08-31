#!/usr/bin/env python3
"""Generate the theoretical tile-arrangement figures as SVG.

The point of these figures is not the keymap - it's showing that the same
5x6 tile makes a 60%, an 80% or a 100% depending on how many you snap
together and which way round they sit. So tiles are colour-coded and their
orientation is labelled.

    ./scripts/gen-layouts.py

Writes docs/images/layout-*.svg. Edit ARRANGEMENTS below to change what gets
drawn - positions are in key units, measured from the top-left.
"""

from pathlib import Path

ROOT = Path(__file__).parent.parent
OUT = ROOT / "docs" / "images"

# --- geometry ---------------------------------------------------------------
TILE_COLS, TILE_ROWS = 5, 6      # a tile in portrait: 5 wide, 6 tall
KEY = 34                          # px per key unit
GAP = 3                           # px gap between keys
TILE_GAP = 6                      # extra px between tiles so the seam is visible
PAD = 18                          # px padding around the figure
TITLE_H = 34
LEGEND_H = 30

# Muted enough to read on both the light and dark site themes.
TILE_COLORS = ["#5b8dd9", "#d98b5b", "#5bb98d", "#a97bd9"]

# --- what to draw -----------------------------------------------------------
# Each tile is (x, y, orientation) in key units. "landscape" swaps cols/rows.
ARRANGEMENTS = {
    "60": {
        "title": "60% - two tiles, landscape",
        "note": "12 x 5 = 60 keys",
        "tiles": [(0, 0, "landscape"), (6, 0, "landscape")],
    },
    "80": {
        "title": "80% - three tiles, portrait",
        "note": "15 x 6 = 90 keys",
        "tiles": [(0, 0, "portrait"), (5, 0, "portrait"), (10, 0, "portrait")],
    },
    "100": {
        "title": "100% - four tiles, portrait",
        "note": "20 x 6 = 120 keys",
        "tiles": [
            (0, 0, "portrait"),
            (5, 0, "portrait"),
            (10, 0, "portrait"),
            (15, 0, "portrait"),
        ],
    },
}


def tile_size(orientation: str) -> tuple[int, int]:
    if orientation == "landscape":
        return TILE_ROWS, TILE_COLS
    return TILE_COLS, TILE_ROWS


def draw_tile(x0: int, y0: int, orientation: str, color: str, ox: float, oy: float,
              index: int) -> list[str]:
    """Emit the keys of one tile. x0/y0 are in key units."""
    cols, rows = tile_size(orientation)
    parts = []

    # tile backing plate, so the module boundary is obvious
    bx = ox + x0 * KEY + x0 // max(cols, 1) * 0
    parts.append(
        f'<rect x="{ox + x0 * KEY - TILE_GAP / 2:.1f}" '
        f'y="{oy + y0 * KEY - TILE_GAP / 2:.1f}" '
        f'width="{cols * KEY + TILE_GAP:.1f}" height="{rows * KEY + TILE_GAP:.1f}" '
        f'rx="6" fill="{color}" fill-opacity="0.13" '
        f'stroke="{color}" stroke-width="1.5"/>'
    )

    for r in range(rows):
        for c in range(cols):
            kx = ox + (x0 + c) * KEY + GAP / 2
            ky = oy + (y0 + r) * KEY + GAP / 2
            parts.append(
                f'<rect x="{kx:.1f}" y="{ky:.1f}" '
                f'width="{KEY - GAP:.1f}" height="{KEY - GAP:.1f}" '
                f'rx="3.5" fill="{color}" fill-opacity="0.30" '
                f'stroke="{color}" stroke-width="1"/>'
            )

    # orientation label, centred on the tile
    cx = ox + (x0 + cols / 2) * KEY
    cy = oy + (y0 + rows / 2) * KEY
    parts.append(
        f'<text x="{cx:.1f}" y="{cy:.1f}" text-anchor="middle" '
        f'dominant-baseline="central" font-family="system-ui, sans-serif" '
        f'font-size="12" font-weight="600" fill="{color}">'
        f'tile {index + 1} · {orientation[:4]}</text>'
    )
    return parts


def render(key: str, spec: dict) -> str:
    tiles = spec["tiles"]

    width_u = max(x + tile_size(o)[0] for x, _, o in tiles)
    height_u = max(y + tile_size(o)[1] for _, y, o in tiles)
    w = width_u * KEY + PAD * 2
    h = height_u * KEY + PAD * 2 + TITLE_H + LEGEND_H

    body = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" height="{h:.0f}" '
        f'viewBox="0 0 {w:.0f} {h:.0f}" role="img" '
        f'aria-label="{spec["title"]}">',
        f'<title>{spec["title"]}</title>',
        f'<text x="{PAD}" y="22" font-family="system-ui, sans-serif" font-size="15" '
        f'font-weight="700" fill="#888">{spec["title"]}</text>',
    ]

    for i, (x, y, orientation) in enumerate(tiles):
        body += draw_tile(x, y, orientation, TILE_COLORS[i % len(TILE_COLORS)],
                          PAD, PAD + TITLE_H, i)

    body.append(
        f'<text x="{PAD}" y="{h - PAD + 4:.0f}" font-family="system-ui, sans-serif" '
        f'font-size="12" fill="#888">{spec["note"]} · '
        f'every tile is the same 5x6 board</text>'
    )
    body.append("</svg>")
    return "\n".join(body)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for key, spec in ARRANGEMENTS.items():
        path = OUT / f"layout-{key}.svg"
        path.write_text(render(key, spec))
        print(f"  wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
