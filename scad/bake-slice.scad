// 2D slices for bake-pockets.py
include <chassis.scad>

RENDER = "none";
MODE = "cut"; // "cut", "sheaths", "board", "info"
LEVEL = 0.2;

if (MODE == "cut") {
    cut(LEVEL);
    part(LEVEL, POGO_HEIGHT) pogo_cutouts();
}
if (MODE == "sheaths") projection(cut = true) sheaths();
if (MODE == "board") board();
if (MODE == "info") echo(TOP_HEIGHT, LAYER_HEIGHT);
