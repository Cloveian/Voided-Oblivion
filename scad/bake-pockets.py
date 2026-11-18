# /// script
# requires-python = ">=3.11"
# dependencies = ["shapely>=2"]
# ///
# usage: uv run scad/bake-pockets.py
#   slices the part pockets layer by layer, cleans up the plastic left between them and writes scad/pockets.scad
#   rerun after changing parts.scad, the sheath params or POGO_TOLERANCE in chassis.scad

import os
import re
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from shapely import MultiPolygon, Polygon, difference, intersection, make_valid, set_precision, union_all

HERE = Path(__file__).resolve().parent
SLICE = HERE / "bake-slice.scad"
OUT = HERE / "pockets.scad"

MIN_WALL = 0.8  # mm, two perimeters with a 0.4 nozzle
NECK = 2.5  # mm, plastic hanging on a narrower neck goes unless it reaches the board edge
EDGE = 4.33  # mm, how deep the pogo cutouts go (outline.scad)
OVERLAP = 0.01  # mm into the sheath cut, or a 0 mm skin is left
HAIR = 0.005  # mm
GRID = 1e-5  # mm


def openscad(out, **defs):
    # None when the slice is empty (above the tallest part)
    args = ["openscad", "-o", str(out), str(SLICE)]
    for k, v in defs.items():
        args += ["-D", f'{k}="{v}"' if isinstance(v, str) else f"{k}={v}"]
    r = subprocess.run(args, capture_output=True, text=True)
    if out.exists():
        return out
    # an empty union reads as "not a 2D object"
    if re.search(r"top level object is (empty|not a 2D object)", r.stderr):
        return None
    raise RuntimeError(f"openscad failed on {defs}:\n{r.stderr}")


def read_svg(path):
    shape = Polygon()
    if path is None:
        return shape
    for d in re.findall(r'd="([^"]+)"', path.read_text()):
        for loop in re.findall(r"M([^Mz]+)", d):
            # svg y is down
            pts = [(float(x), -float(y)) for x, y in re.findall(r"(-?[\d.]+),(-?[\d.]+)", loop)]
            shape = shape.symmetric_difference(Polygon(pts).buffer(0))  # even-odd, so holes come out
    return shape


def grow(g, d):
    # mitre like openscad offset(delta)
    return tidy(g).buffer(d, join_style="mitre")


def tidy(g):
    # overlays leave repeated points and 0 width spikes, buffer divides by zero on them
    return join(*pieces(make_valid(g)))


# snap rounded booleans. a buffered shape matches its source edges to float noise and the plain overlay chokes on that
def join(*gs):
    return polys(union_all(gs, grid_size=GRID))


def sub(a, *bs):
    for b in bs:
        a = polys(difference(a, b, grid_size=GRID))
    return a


def meet(a, b):
    return polys(intersection(a, b, grid_size=GRID))


def polys(g):
    # snapping collapses slivers to lines and the next overlay won't take a mix
    ps = pieces(g)
    return MultiPolygon(ps) if ps else Polygon()


def pieces(g):
    # differences can leave stray lines next to the polygons
    return [p for p in getattr(g, "geoms", [g]) if p.geom_type == "Polygon" and not p.is_empty]


def real(g):
    # the buffer round trips and the grid move edges by a hair, along a long edge that's area but no width
    return not grow(g, -HAIR).is_empty


def clean(cut, sheaths, board):
    # cut grows till nothing changes, taking thin walls, islands, necked pieces and fins with it
    outside = sub(grow(board, NECK), board)
    edge = sub(board, grow(board, -EDGE))

    def trim(p):
        # touching the outline only the part within EDGE of it stays
        return sub(p, edge) if p.distance(board.exterior) < 0.01 else p

    for _ in range(10):
        # walls under MIN_WALL next to a pocket. ones only between sheaths are the clips
        walled = join(cut, sheaths, outside)
        closed = grow(grow(walled, MIN_WALL / 2), -MIN_WALL / 2)
        grown = tidy(join(cut, meet(sub(closed, walled), grow(cut, MIN_WALL))))

        plastic = sub(board, grown, sheaths)
        parts = sorted(pieces(plastic), key=lambda p: -p.area)
        gone = [trim(p) for p in parts[1:]]

        core = grow(grow(plastic, -NECK / 2), NECK / 2)
        thin = sub(plastic, core)
        cores = sorted(pieces(core), key=lambda p: -p.area)
        for c in cores[1:]:
            # the core, its thin edges can run through a neck into something on the edge
            if c.distance(board.exterior) > 0.01:
                gone.append(join(c, meet(thin, grow(c, NECK))))

        # fins, thin bits with one end or none on the fat plastic. walls have two
        for t in pieces(thin):
            ends = pieces(meet(grow(t, 0.01), core))
            if real(t) and len(ends) <= 1:
                gone.append(trim(t))

        grown = tidy(join(grown, *gone))
        if not real(join(sub(grown, cut), sub(cut, grown))):
            # the pieces come from buffers, so their edges miss the cut and the sheaths by a hair and leave 0 mm walls.
            # taking the sheaths back off leaves slivers along their faces, the opening drops those
            closed = sub(grow(grow(join(grown, sheaths), HAIR), -HAIR), sheaths)
            return grow(grow(closed, -HAIR), HAIR)
        cut = grown
    raise RuntimeError("cleanup didn't settle in 10 rounds")


def stack(cuts, sheaths, board):
    # cleaned top down with the layer above added in, so nothing hangs off the plate (prints face down).
    # then ledges under MIN_WALL along the pocket above get cut from it too and the stack goes again
    cuts = list(cuts)
    done = [Polygon()] * len(cuts)
    for _ in range(10):
        above = Polygon()
        for i in reversed(range(len(cuts))):
            if not (cuts[i].is_empty and above.is_empty):
                done[i] = clean(tidy(join(cuts[i], above)), sheaths, board)
            above = done[i]

        moved = False
        for i in range(len(cuts) - 1):
            if done[i + 1].is_empty:
                break
            step = sub(done[i], done[i + 1])
            thin = sub(step, grow(grow(step, -MIN_WALL / 2), MIN_WALL / 2))
            # only along the pocket above, the top of a narrow pocket isn't a ledge
            ledges = [p for p in pieces(thin) if real(p) and p.distance(done[i + 1]) < 0.01]
            if ledges:
                cuts[i + 1] = tidy(join(cuts[i + 1], *ledges))
                # right away so the next layer up sees it this pass. only more cut, so nothing hangs
                done[i + 1] = clean(tidy(join(done[i + 1], cuts[i + 1])), sheaths, board)
                moved = True
        if not moved:
            return done
    raise RuntimeError("stack didn't settle in 10 rounds")


def polygons(g):
    out = []
    # snapped to the 0.001 that gets written, plain rounding can push a hole out of its polygon
    for p in pieces(set_precision(g.simplify(0.001), 0.001)):
        points, paths = [], []
        for ring in [p.exterior, *p.interiors]:
            coords = list(ring.coords)[:-1]
            paths.append(list(range(len(points), len(points) + len(coords))))
            points += coords
        pts = ", ".join(f"[{x:.3f},{y:.3f}]" for x, y in points)
        out.append(f"polygon([{pts}], {paths});")
    return out


def main():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        echo = openscad(tmp / "info.echo", MODE="info").read_text()
        top, layer = (float(v) for v in re.search(r"ECHO: ([\d.]+), ([\d.]+)", echo).groups())
        levels = [round(i * layer, 3) for i in range(1, round(top / layer) + 1)]

        with ThreadPoolExecutor(os.cpu_count()) as pool:
            board = pool.submit(openscad, tmp / "board.svg", MODE="board")
            sheaths = pool.submit(openscad, tmp / "sheaths.svg", MODE="sheaths")
            cuts = [pool.submit(openscad, tmp / f"cut{l}.svg", MODE="cut", LEVEL=l) for l in levels]
            board, sheaths = read_svg(board.result()), read_svg(sheaths.result())
            cuts = [read_svg(c.result()) for c in cuts]

    keep = grow(sheaths, -OVERLAP)
    bands = []  # [bottom, top, pocket]
    for level, cut, done in zip(levels, cuts, stack(cuts, sheaths, board)):
        if done.is_empty:
            continue
        # pushed into the sheaths it touches, edges that stop on a sheath leave a 0 mm skin. HAIR bridges what the opening left
        pocket = sub(join(done, meet(grow(done, 2 * OVERLAP), grow(sheaths, HAIR))), keep)
        touching = bands and bands[-1][1] == round(level - layer, 3)
        if touching and not real(join(sub(pocket, bands[-1][2]), sub(bands[-1][2], pocket))):
            bands[-1][1] = level
        else:
            bands.append([round(level - layer, 3), level, pocket])
        print(f"{level:4.1f} mm  {sub(pocket, cut).area:6.1f} mm2 more plastic cut than the parts need")

    lines = ["// generated by bake-pockets.py, don't edit", "module pockets() {"]
    for z0, z1, pocket in bands:
        lines.append(f"    translate([0, 0, {z0 - 0.01:.3f}]) linear_extrude({z1 - z0 + 0.02:.3f}) {{")
        lines += [f"        {p}" for p in polygons(pocket)]
        lines.append("    }")
    lines.append("}")
    OUT.write_text("\n".join(lines) + "\n")
    print(f"{len(bands)} bands, wrote {OUT}")


if __name__ == "__main__":
    main()
