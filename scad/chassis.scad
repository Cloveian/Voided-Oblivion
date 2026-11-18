use <outline.scad>
include <parts.scad>
// generated, rerun bake-pockets.py after changing parts.scad, the sheaths or pogo pins
use <pockets.scad>
use <../../Void_Switch/scad/sheath_negative.scad>

RENDER = "top"; // [top, bottom]

// BODY_HEIGHT echoed by Void_Switch/scad/void_switch.scad (8.4 at TOTAL_TRAVEL = 2)
TOP_HEIGHT = 8.4; // [4:0.01:15]
// DIN 965 M2 head is 1.2 tall
BOTTOM_HEIGHT = 1.2; // [0.4:0.01:5]
POGO_HEIGHT = 2.5; // [0:0.01:5]
// 45 on the top outside rim, size along each face
TOP_CHAMFER = 1; // [0:0.01:3]
// radius on both creases of the chamfer, capped at 1.71 * TOP_CHAMFER
TOP_CHAMFER_FILLET = 0.5; // [0:0.01:5]
// per side, on top of the courtyard
POGO_TOLERANCE = 0.2; // [0:0.01:1]

// tile to tile magnets, N52, rows alternate NS/SN
// rows, cols on the first and last 19.05 slot of each edge, 0 for none
EDGE_MAGNET_OUTER = [2, 3];
// rows, cols in the middle of each edge. on the left and right it lands on the screws at y 57.15
EDGE_MAGNET_MIDDLE = [0, 0];
EDGE_MAGNET_DIAMETER = 3; // [1:0.01:6]
// along its axis, into the edge
EDGE_MAGNET_HEIGHT = 2; // [0.5:0.01:5]
// on the diameter
EDGE_MAGNET_TOLERANCE = 0.2; // [0:0.01:1]
// epoxy over the magnet, 0.05 a side is the 0.1 gap
EDGE_MAGNET_CAP = 0.05; // [0:0.01:0.5]
// top row below the top face
EDGE_MAGNET_TOP = 0.5; // [0:0.01:4]
// plastic between neighbouring holes, 0 = magnets touching
EDGE_MAGNET_SPACING = 0; // [0:0.01:4]
// one pocket per group, epoxy fills between the magnets
EDGE_MAGNET_OPEN = true;
// radius on the notches between holes of an open pocket, 0 = sharp
EDGE_MAGNET_SMOOTH = 1; // [0:0.01:3]
// roof slope of the hole from horizontal as printed, degrees. 0 = round
EDGE_MAGNET_TEARDROP = 45; // [0:1:80]

SCREW_BOSS_D = 4.3; // [2:0.01:8]
SCREW_PILOT_D = 1.7; // [1:0.01:3]
// From the PCB side; M2x8 countersunk leaves 5.2 in the top after the bottom and PCB
SCREW_HOLE_DEPTH = 6; // [1:0.01:10]
SCREW_CLEARANCE_D = 2.2; // [1.5:0.01:3]
SCREW_HEAD_D = 3.8; // [2:0.01:6]

// Copy from void_switch.scad (must match the switches being printed)
MAGNET_DIAMETER = 4; // [3:1:5]
MAGNET_WALL_THICKNESS = 0.5; // [0.1:0.01:2]
STEM_DIAMETER = 5.35; // [3:0.01:8]
SHEATH_LENGTH = 0.2; // [0:0.01:2]
SHEATH_TOLERANCE = 0.15; // [0:0.01:0.5]
STEM_TOLERANCE = 0.11; // [0.01:0.01:0.3]
SHEATH_CLIP_WIDTH = 1.5; // [0.5:0.01:3]

KEY_UNIT = 19.05;
COLUMNS = 5;
ROWS = 6;

$fn = 32;

module through(height) {
    translate([0, 0, -0.01]) linear_extrude(height + 0.02) children();
}

module pogo_cutouts() {
    offset(delta = POGO_TOLERANCE) pogo_pins();
}

// inset of the rim at depth h below the top face, s=0 on the side.
// fillet centres at (f, c + f(√2-1)) and (c + f(√2-1), f), each touches the chamfer f(1 - 1/√2) along from the crease
function rim_inset(h, c, f) =
    let(k = f * (sqrt(2) - 1), t = f * (1 - 1 / sqrt(2)))
    h >= c + k ? 0
    : h >= c - t ? f - sqrt(max(0, f * f - pow(h - (c + k), 2)))
    : h >= t ? c - h
    : c + k - sqrt(max(0, f * f - pow(h - f, 2)));

// the board is convex, so a hull of inset slices is the chamfered block
module top_body() {
    c = TOP_CHAMFER;
    f = min(TOP_CHAMFER_FILLET, c / (2 - sqrt(2)));
    k = f * (sqrt(2) - 1);
    // slices by angle round both 45 degree arcs, the hull draws the flat between them
    n = 8;
    hs = concat([for (i = [0:n]) f - f * cos(45 * i / n)], [for (i = [0:n]) c + k - f * sin(45 * (n - i) / n)]);
    if (c <= 0) linear_extrude(TOP_HEIGHT) board();
    else hull() {
        linear_extrude(TOP_HEIGHT - c - k) board();
        for (h = hs)
            translate([0, 0, TOP_HEIGHT - h - 0.001]) linear_extrude(0.001) offset(r = -rim_inset(h, c, f)) board();
    }
}

// teardrop, the point goes toward the PCB which is up when the top prints face down
module magnet_hole() {
    d = EDGE_MAGNET_DIAMETER + EDGE_MAGNET_TOLERANCE;
    // tip where the two roof lines meet
    hull() {
        circle(d = d);
        translate([0, -d / 2 / cos(EDGE_MAGNET_TEARDROP)]) square(0.01, center = true);
    }
}

// in an edge with +y pointing out, u along the edge from its middle
module magnet_group(rows, cols, u) {
    d = EDGE_MAGNET_DIAMETER + EDGE_MAGNET_TOLERANCE;
    pitch = d + EDGE_MAGNET_SPACING;
    top = TOP_HEIGHT - EDGE_MAGNET_TOP - d / 2;
    left = u - (cols - 1) / 2 * pitch;
    smooth = EDGE_MAGNET_OPEN ? EDGE_MAGNET_SMOOTH : 0;
    translate([0, 0.01, 0]) rotate([90, 0, 0]) linear_extrude(EDGE_MAGNET_HEIGHT + EDGE_MAGNET_CAP + 0.01)
        offset(r = -smooth) offset(r = smooth) {
            for (r = [0:rows - 1], c = [0:cols - 1])
                translate([left + c * pitch, top - r * pitch]) magnet_hole();
            if (EDGE_MAGNET_OPEN) group_middle(rows, cols, left, top, d, pitch);
        }
}

// everything between the hole centres. the bottom stays a V between teardrops,
// straight across would be a flat roof once it's printed face down
module group_middle(rows, cols, left, top, d, pitch) {
    right = left + (cols - 1) * pitch;
    bottom = top - (rows - 1) * pitch;
    tip = bottom - d / 2 / cos(EDGE_MAGNET_TEARDROP);
    // where neighbouring roof lines cross, kept under the centre line (only steeper)
    meet = min(tip + pitch / 2 * tan(EDGE_MAGNET_TEARDROP), bottom);
    vs = [for (c = [cols - 1:-1:0]) each concat([[left + c * pitch, tip]], c > 0 ? [[left + (c - 0.5) * pitch, meet]] : [])];
    polygon(concat([[left, top], [right, top], [right, bottom]], vs, [[left, bottom]]));
}

module edge_magnets() {
    w = COLUMNS * KEY_UNIT;
    h = ROWS * KEY_UNIT;
    // [rows, cols, t], t 0 = first slot, 0.5 = middle, 1 = last slot
    groups = [
        for (g = [[EDGE_MAGNET_OUTER, 0], [EDGE_MAGNET_MIDDLE, 0.5], [EDGE_MAGNET_OUTER, 1]])
            if (g[0][0] > 0 && g[0][1] > 0) [g[0][0], g[0][1], g[1]]
    ];
    // [middle, turn so +y points out, length]
    for (e = [[[w / 2, 0], 180, w], [[w / 2, h], 0, w], [[0, h / 2], 90, h], [[w, h / 2], -90, h]])
        translate(e[0]) rotate([0, 0, e[1]])
            for (g = groups) magnet_group(g[0], g[1], (g[2] - 0.5) * (e[2] - KEY_UNIT));
}

/* replaced by bake-pockets.py
MIN_WALL = 0.8;
NECK = 2.5;
KEEP = 3;

// Closing fills every gap narrower than gap
module closing(gap) {
    offset(delta = -gap / 2) offset(delta = gap / 2) children();
}

module sheath_outlines() {
    projection(cut = true) sheaths();
}

// The intersection keeps the fill to gaps that touch a pocket so sheath clips elsewhere survive
module closed(level, gap) {
    intersection() {
        closing(gap) {
            cut(level);
            sheath_outlines();
            difference() {
                offset(delta = gap) board();
                board();
            }
        }
        offset(delta = gap) cut(level);
    }
}

// Plus everything it walls in. The rest of each layer reaches the board edge so it never gets filled
module walled(level, gap) {
    fill() {
        closed(level, gap);
        sheath_outlines();
    }
}

// The ones with no room for a KEEP square
module small() {
    difference() {
        children();
        offset(delta = KEEP / 2) offset(delta = -KEEP / 2) children();
    }
}

// Islands, and the small hanging pieces along with their neck
module printable(level) {
    difference() {
        union() {
            walled(level, MIN_WALL);
            intersection() {
                walled(level, NECK);
                // pieces on a neck under NECK
                offset(delta = NECK) small() difference() {
                    walled(level, NECK);
                    closed(level, NECK);
                    sheath_outlines();
                }
            }
        }
        // cut by sheaths() in 3D, keeps the slabs light. 0.01 overlap or a 0 mm skin is left
        offset(delta = -0.01) sheath_outlines();
    }
}

module pockets() {
    for (level = [LAYER_HEIGHT : LAYER_HEIGHT : TOP_HEIGHT])
        translate([0, 0, level - LAYER_HEIGHT - 0.01])
            linear_extrude(LAYER_HEIGHT + 0.02) printable(level);
}
*/

module sheaths() {
    for (c = [0:COLUMNS - 1], r = [0:ROWS - 1])
        translate([(c + 0.5) * KEY_UNIT, (r + 0.5) * KEY_UNIT, TOP_HEIGHT / 2])
            // The sheath module puts the magnet at (-,-); the hall sensors are at (+,-)
            rotate([0, 0, 90])
                void_sheath_negative(MAGNET_DIAMETER, MAGNET_WALL_THICKNESS, TOP_HEIGHT, STEM_DIAMETER,
                    SHEATH_LENGTH, SHEATH_TOLERANCE, STEM_TOLERANCE, SHEATH_CLIP_WIDTH);
}

module top() {
    difference() {
        union() {
            difference() {
                top_body();
                pockets();
                sheaths();
                through(POGO_HEIGHT + POCKET_CLEARANCE) pogo_cutouts();
            }
            // the ones by the edge would stand up out of the chamfer
            intersection() {
                for (p = screw_hole_centres())
                    translate(p) cylinder(d = SCREW_BOSS_D, h = TOP_HEIGHT);
                top_body();
            }
        }
        for (p = screw_hole_centres())
            translate(p) through(SCREW_HOLE_DEPTH) circle(d = SCREW_PILOT_D);
        // after the bosses, a boss by the edge would fill them back in
        edge_magnets();
    }
}

module bottom() {
    countersink_depth = (SCREW_HEAD_D - SCREW_CLEARANCE_D) / 2;
    difference() {
        linear_extrude(BOTTOM_HEIGHT) board();
        for (p = screw_hole_centres()) translate(p) {
            through(BOTTOM_HEIGHT) circle(d = SCREW_CLEARANCE_D);
            translate([0, 0, -0.01])
                cylinder(d1 = SCREW_HEAD_D, d2 = SCREW_CLEARANCE_D, h = countersink_depth + 0.01);
        }
    }
}

if (RENDER == "top") top();
else if (RENDER == "bottom") bottom();
