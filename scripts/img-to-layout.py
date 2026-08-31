#!/usr/bin/env python3
"""Turn an image into a KLE layout where one key is one pixel.

power.md says of the 8x8 case: "you could probably run doom on the RGB with
that". This is the still-frame version of that claim - each key's cap colour
is a pixel, so the array is a 48x40 display.

    ./scripts/img-to-layout.py layouts/frame_0309.png
    ./scripts/img-to-layout.py <img> --tiles 8x8 --orientation landscape

Writes <name>-<W>x<H>.json (KLE) and <name>-<W>x<H>.svg (preview, because
KLE gets very slow past a few hundred keys and this is 1920).
"""

import argparse
import json
from pathlib import Path

from PIL import Image

PORTRAIT = (5, 6)   # tile is 5 wide, 6 tall
LANDSCAPE = (6, 5)


def fit(img: Image.Image, w: int, h: int, pad: str, mode: str) -> Image.Image:
    """Resize to exactly w x h, preserving aspect.

    cover   - fill the frame and crop the overflow (no blank keys)
    contain - fit the whole image and pad the remainder
    """
    pick = max if mode == "cover" else min
    scale = pick(w / img.width, h / img.height)
    new = (max(1, round(img.width * scale)), max(1, round(img.height * scale)))
    img = img.resize(new, Image.LANCZOS)

    if mode == "cover":
        left, top = (new[0] - w) // 2, (new[1] - h) // 2
        return img.crop((left, top, left + w, top + h))

    canvas = Image.new("RGB", (w, h), pad)
    canvas.paste(img, ((w - new[0]) // 2, (h - new[1]) // 2))
    return canvas


def to_kle(px: Image.Image) -> list:
    """One key per pixel. Emit a colour object only when it changes."""
    rows, current = [], None
    for y in range(px.height):
        row = []
        for x in range(px.width):
            r, g, b = px.getpixel((x, y))
            c = f"#{r:02x}{g:02x}{b:02x}"
            if c != current:
                row.append({"c": c})
                current = c
            row.append("")
        rows.append(row)
    return rows


def tile_color(x: int, y: int, tw: int, th: int, tiles_x: int) -> str:
    """Pastel for the tile a given key falls in - makes the seams visible."""
    return PALETTE[((y // th) * tiles_x + (x // tw)) % len(PALETTE)]


def to_svg(px: Image.Image, tw: int, th: int, tiles_x: int,
           key: int = 16, gap: int = 2, stroke: float = 1.6) -> str:
    """Pixel colour fills the cap; the tile's pastel outlines it."""
    w, h = px.width * key, px.height * key
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
           f'viewBox="0 0 {w} {h}" role="img">',
           f'<rect width="{w}" height="{h}" fill="#1b1b1b"/>']
    inset = stroke / 2
    for y in range(px.height):
        for x in range(px.width):
            r, g, b = px.getpixel((x, y))
            out.append(
                f'<rect x="{x*key + inset:.1f}" y="{y*key + inset:.1f}" '
                f'width="{key - gap - stroke:.1f}" height="{key - gap - stroke:.1f}" '
                f'rx="2.5" fill="#{r:02x}{g:02x}{b:02x}" '
                f'stroke="{tile_color(x, y, tw, th, tiles_x)}" '
                f'stroke-width="{stroke}"/>'
            )
    out.append("</svg>")
    return "".join(out)


def to_preview(px: Image.Image, tw: int, th: int, tiles_x: int, key: int = 12) -> Image.Image:
    """Same treatment as the SVG, rasterised, so the result can be eyeballed."""
    from PIL import ImageDraw

    img = Image.new("RGB", (px.width * key, px.height * key), "#1b1b1b")
    draw = ImageDraw.Draw(img)
    for y in range(px.height):
        for x in range(px.width):
            x0, y0 = x * key, y * key
            draw.rectangle(
                [x0, y0, x0 + key - 2, y0 + key - 2],
                fill=px.getpixel((x, y)),
                outline=tile_color(x, y, tw, th, tiles_x),
                width=1,
            )
    return img


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("image", type=Path)
    ap.add_argument("--tiles", default="8x8", help="tile grid, e.g. 8x8")
    ap.add_argument("--orientation", default="landscape",
                    choices=["landscape", "portrait"])
    ap.add_argument("--fit", default="cover", choices=["cover", "contain"],
                    help="cover crops the overflow; contain pads")
    ap.add_argument("--pad", default="white", help="letterbox colour (contain only)")
    args = ap.parse_args()

    tx, ty = (int(v) for v in args.tiles.lower().split("x"))
    tw, th = LANDSCAPE if args.orientation == "landscape" else PORTRAIT
    w, h = tw * tx, th * ty

    img = Image.open(args.image).convert("RGB")
    px = fit(img, w, h, args.pad, args.fit)

    stem = f"{args.image.stem}-{w}x{h}"
    out_dir = args.image.parent

    kle = to_kle(px)
    body = ",\n".join(json.dumps(r) for r in kle)
    (out_dir / f"{stem}.json").write_text("[\n" + body + "\n]\n")
    (out_dir / f"{stem}.svg").write_text(to_svg(px))
    px.resize((w * 8, h * 8), Image.NEAREST).save(out_dir / f"{stem}-preview.png")

    keys = w * h
    print(f"  {args.image.name} {img.width}x{img.height} -> {w}x{h} ({args.fit})")
    print(f"  {tx}x{ty} tiles {args.orientation} = {tx*ty} tiles, {keys} keys")
    print(f"  wrote {stem}.json and {stem}.svg")


if __name__ == "__main__":
    main()
