// PCB part heights and the pocket each one needs, baked into pockets.scad by bake-pockets.py
use <outline.scad>

POCKET_CLEARANCE = 0.3;
LAYER_HEIGHT = 0.2;

// Slice from level - LAYER_HEIGHT to level
module part(level, height) {
    if (height + POCKET_CLEARANCE > level - LAYER_HEIGHT) children();
}

// component heights
// Inside the sheath cutouts, so the teal boxes ignore them
module sheath_parts(level) {
    part(level, 1.0) leds();
    part(level, 1.2) hall_sensors();
}

module boxed_parts(level) {
    part(level, 0.5) passives_0402();
    part(level, 0.57) usb_mux();
    part(level, 1.6) passives_1206();
    part(level, 1.2) sot23_misc();
    part(level, 1.55) sot23_5();
    part(level, 1.55) sot23_6();
    part(level, 1.2) sot23_8();
    part(level, 1.1) sot363();
    part(level, 0.63) sot553();
    part(level, 1.6) mosfets();
    part(level, 2.1) mux();
    part(level, 2.16) flash();
    part(level, 0.8) pd_chips();
    part(level, 0.9) rp2350b();
    part(level, 0.85) level_shifter();
    part(level, 0.82) ldo_3v3();
    part(level, 1.25) l1();
    part(level, 2.8) coils();
    part(level, 1.4) diode();
    part(level, 0.64) crystal();
    part(level, 3.31) usb();
    part(level, 1.35) button_bodies();
    part(level, 1.2) button_fronts();
}

// Hulls against copies pushed far off along each axis give the x and y extents
module bounding_box() {
    intersection() {
        hull() {
            translate([0, -1000]) children();
            translate([0, 1000]) children();
        }
        hull() {
            translate([-1000, 0]) children();
            translate([1000, 0]) children();
        }
    }
}

// On each layer a box cuts the bounding box of its parts that reach that layer, stretched
// out to any edge drawn into a sheath cutout so no spike is left between them
module merged(level) {
    sides = [[-1, 0], [0, -1], [1, 0], [0, 1]];
    for (r = merged_rects())
        intersection() {
            box(r);
            hull() for (d = concat([[0, 0]], [for (i = [0:3]) if (r[4 + i] == 1) sides[i]]))
                translate(d * 1000) bounding_box() intersection() {
                    box(r);
                    boxed_parts(level);
                }
        }
}

module box(r) {
    translate([r[0], r[1]]) square([r[2] - r[0], r[3] - r[1]]);
}

module cut(level) {
    sheath_parts(level);
    boxed_parts(level);
    merged(level);
}
