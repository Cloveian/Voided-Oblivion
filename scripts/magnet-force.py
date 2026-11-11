# /// script
# requires-python = ">=3.11"
# dependencies = ["magpylib>=6", "matplotlib", "numpy"]
# ///
# usage: uv run scripts/magnet-force.py --dia D --height H [--grade N52] [--pitch P] [--gap LO:HI:STEP] [--offset X,Y] [--preload G] [--plot out.png] ARRAY...
#   pull between two tiles' magnets vs gap. ARRAY is ROWSxCOLS@X,Y, X,Y the array's center in mm, ! on the end starts it on S. poles go NS/SN checkerboard in each array
#   e.g. uv run scripts/magnet-force.py --dia 3 --height 1 --preload 600 2x2@0,0 2x2@20,0 1x2@40,0
#   ideal magnets and no steel, so its an upper bound

import argparse
import re

import magpylib as magpy
import numpy as np

GRADES = {"N35": 1.19, "N38": 1.23, "N40": 1.27, "N42": 1.30, "N45": 1.35, "N48": 1.39, "N50": 1.42, "N52": 1.45}  # typical Br, T
MM = 1e-3
G = 9.80665  # N per kgf
ARRAY = re.compile(r"^(\d+)x(\d+)@(-?[\d.]+),(-?[\d.]+)(!?)$")


def array(spec):
    m = ARRAY.match(spec)
    if not m:
        raise argparse.ArgumentTypeError(f"cant read {spec!r}, want like 2x2@0,0")
    rows, cols, x, y, flip = m.groups()
    return int(rows), int(cols), float(x), float(y), bool(flip)


def span(spec):
    lo, hi, step = (float(v) for v in spec.split(":"))
    return np.arange(lo, hi + step / 2, step)  # hi included


def sites(arrays, pitch):
    # (x, y, sign) of every magnet in mm, sign +1 is N up on tile A
    out = []
    for rows, cols, cx, cy, flip in arrays:
        for r in range(rows):
            for c in range(cols):
                sign = (-1) ** (r + c) * (-1 if flip else 1)
                out.append((cx + (c - (cols - 1) / 2) * pitch, cy - (r - (rows - 1) / 2) * pitch, sign))
    return out


def tiles(spots, dia, height, br):
    # A's top faces at z=0, B's bottom faces at z=0 till it gets moved out to the gap
    # same polarization on both sides of a pair, A's N face up meets B's S face down so they pull
    a, b = magpy.Collection(), magpy.Collection()
    for x, y, sign in spots:
        for side, z in ((a, -height / 2), (b, height / 2)):
            side.add(magpy.magnet.Cylinder(polarization=(0, 0, sign * br), dimension=(dia * MM, height * MM), position=(x * MM, y * MM, z * MM)))
    return a, b


def force(spots, gaps, offset, dia, height, br, mesh):
    # force on B in N at each gap, (len(gaps), 3). B rides a path so it's one getFT call
    a, b = tiles(spots, dia, height, br)
    b.position = [(offset[0] * MM, offset[1] * MM, g * MM) for g in gaps]
    f, _ = magpy.getFT(a, b, meshing=mesh, eps=1e-5 * dia * MM, squeeze=False)
    return f.reshape(len(gaps), 3)


def plot(path, gaps, pull, single, n, preload, title):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(gaps, pull, label=f"array ({n} magnets)")
    ax.plot(gaps, single * n, "--", label=f"{n}x lone pair")
    if preload:
        ax.axhline(preload, color="red", lw=1, label=f"preload {preload:.0f} g")
    ax.set(xlabel="gap (mm)", ylabel="pull (g)", title=title)
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("arrays", nargs="+", type=array, help="ROWSxCOLS@X,Y, ! on the end starts on S")
    ap.add_argument("--dia", type=float, required=True, help="magnet diameter, mm")
    ap.add_argument("--height", type=float, required=True, help="magnet height, mm")
    ap.add_argument("--grade", default="N52", choices=GRADES)
    ap.add_argument("--br", type=float, help="Br in T, beats --grade")
    ap.add_argument("--pitch", type=float, help="center to center in an array, mm. default touching")
    ap.add_argument("--gap", type=span, default="0:3:0.25", help="LO:HI:STEP mm")
    ap.add_argument("--offset", default="0,0", help="how far off B sits sideways, X,Y mm")
    ap.add_argument("--preload", type=float, default=0, help="g pushing the tiles apart (pogo pins)")
    ap.add_argument("--mesh", type=int, default=500, help="cells per target magnet, 200 reads ~7%% low touching")
    ap.add_argument("--plot", help="png out")
    args = ap.parse_args()

    br = args.br or GRADES[args.grade]
    pitch = args.pitch or args.dia
    if pitch < args.dia:
        ap.error(f"pitch {pitch} is under the diameter, they'd overlap")
    offset = tuple(float(v) for v in args.offset.split(","))
    spots = sites(args.arrays, pitch)
    n = len(spots)

    f = force(spots, args.gap, offset, args.dia, args.height, br, args.mesh)
    pull = -f[:, 2] / G * 1000  # g, pulling together is +
    shear = np.hypot(f[:, 0], f[:, 1]) / G * 1000
    single = -force([(0, 0, 1)], args.gap, (0, 0), args.dia, args.height, br, args.mesh)[:, 2] / G * 1000

    print(f"{n} magnets {args.dia}x{args.height} mm, Br {br} T, pitch {pitch} mm, offset {offset} mm")
    print(f"{'gap mm':>7} {'pull g':>8} {'net g':>8} {f'{n}x lone g':>11} {'shear g':>8}")
    for g, pl, sg, sh in zip(args.gap, pull, single, shear):
        print(f"{g:7.2f} {pl:8.0f} {pl - args.preload:8.0f} {sg * n:11.0f} {sh:8.0f}")

    if args.plot:
        title = " + ".join(f"{r}x{c}" for r, c, *_ in args.arrays) + f", {args.dia}x{args.height} mm, pitch {pitch} mm"
        plot(args.plot, args.gap, pull, single, n, args.preload, title)
        print(f"wrote {args.plot}")


if __name__ == "__main__":
    main()
