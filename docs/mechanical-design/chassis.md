# Chassis
the chassis/case of the keyboard

## Identify
I need a chassis/case for the keyboard

Ok ok, so a lot of this depends on the switches, but this is what i can think of for what it needs

- Way to snap to the other tiles
- hold switches
- uhh... thats basically it i guess ┐(°_°)ʃ

so the snap to other tiles is actually a little harder than i thought it would be, i am probably gonna have to drop 'submodules' on rev 1 of this pcb cuz that is the only location i have to put magnets...

ok so the pogo pins on each side require about ~300g $\cdot$ 2 of force to push into the working position 
(my phone died so no pic)
so 600g *plus* however much i want it to 'stay togeather' which is... "almost feel like one piece"
i dont want it easy to separate, therefore the answer to 'how much force do i need' is 'what ever i can squeeze in there'

so i need to research what force the magnets i have (and don't have) force is, like per magnet.

**Constraints:**
- Tile is 95.25 $\cdot$ 114.3 mm 
- Magnets go on the edge face, ~8mm of 3d printed room
- The magnets need a gap (cant be the first thing to touch) cuz they will break.

## Brainstorm/Research
Ok, from what i can find, there aren't any websites that calculate the force of 'magnet arrays' cuz i was thinking that i could probably have like 8 magnets per side in this orientation:
```
NS
SN
```
just by messing around with magnets you can get them to stay like that, cuz they 'like' it
problem is, i genuinely cant find a tool that calculates what force that would be, time to write a tool i guess *yippee* ¬_¬.

So looking for a bit, i found [Magpylib](https://magpylib.readthedocs.io/en/latest/index.html) it would let me 'simulate' what the force of the magnets in that orientation would be. I would just have to figure out how to do that... your mum

### Force tool
So i was lazy and had Claude help me write [`scripts/magnet-force.py`](../../scripts/magnet-force.py) it uses Magpylib to calculate the pull between two mating magnet layouts. Each array is written as `ROWSxCOLS@X,Y` and alternates NS/SN in a checkerboard:

```
uv run scripts/magnet-force.py --dia 3 --height 2 --preload 600 --gap 0:0.3:0.1 2x2@-30,-1.5 1x2@0,0 2x2@30,-1.5
```

Prints pull, pull minus preload, the same magnets as lone pairs, and sideways force with `--offset`. `--plot` for a graph.

this is just the 'ideal' calculation, so i took like 15% off the numbers:

Single 3 $\cdot$ 1 mm N52 pair: 286 g at contact.

### Gap
0.1 mm between the faces when mated.

0.1 → 0.2 mm costs ~15-20% of the pull.

### Load case
Test case: pick the board up by one tile, the other one hangs.

The joint 'hinges' on its bottom edge, so the lever is the magnets' height above it. The tile's weight acts at its center, 47.6 mm out side by side, 57.15 mm stacked.

Pull needed ~ $\frac {( \text {tile weight} \cdot \text {center distance}) + ( \text {600 g} \cdot \text {pogo height})} {\text {magnet lever}}$ 

Assumed: 300 g tile, pogo pins at mid-height. Neither is checked.

Top row 0.5 mm below the top edge: lever goes 6 → ~8.5 mm for 2 rows of 3 mm.

Bent the other way (held under the seam) it hinges on the top edge, lever ~3.5 mm.

### Magnet layouts
N52, 2 rows, magnets touching, top row 0.5 mm below the top edge unless noted. Pull at 0.1 mm. Max tile = heaviest tile the joint holds.

| layout                                                        | #   | pull    | max tile, side by side | max tile, stacked | max tile, bent other way |
| ------------------------------------------------------------- | --- | ------- | ---------------------- | ----------------- | ------------------------ |
| A1: 2 $\cdot$ 2 + 2 $\cdot$ 2 of 3 $\cdot$ 1 mm               | 8   | 2.18 kg | 158 g                  | 131 g             | 158 g                    |
| A2: 2 $\cdot$ 2 + 2 $\cdot$ 2 of 3 $\cdot$ 2 mm               | 8   | 3.29 kg | 277 g                  | 231 g             | 277 g                    |
| B1: 2 $\cdot$ 2 + 1 $\cdot$ 2 + 2 $\cdot$ 2 of 3 $\cdot$ 1 mm | 10  | 2.68 kg | 344 g                  | 287 g             | 78 g                     |
| B2: 2 $\cdot$ 2 + 1 $\cdot$ 2 + 2 $\cdot$ 2 of 3 $\cdot$ 2 mm | 10  | 4.07 kg | 563 g                  | 469 g             | 158 g                    |
| C1: 2 $\cdot$ 3 + 2 $\cdot$ 3 of 3 $\cdot$ 1 mm               | 12  | 3.35 kg | 433 g                  | 361 g             | 134 g                    |
| C2: 2 $\cdot$ 3 + 2 $\cdot$ 3 of 3 $\cdot$ 2 mm               | 12  | 5.00 kg | 684 g                  | 570 g             | 237 g                    |
| D1: 2 $\cdot$ 3 + 1 $\cdot$ 2 + 2 $\cdot$ 3 of 3 $\cdot$ 1 mm | 14  | 3.85 kg | 522 g                  | 435 g             | 152 g                    |
| D2: 2 $\cdot$ 3 + 1 $\cdot$ 2 + 2 $\cdot$ 3 of 3 $\cdot$ 2 mm | 14  | 5.79 kg | 823 g                  | 686 g             | 265 g                    |

A:
```
NS            NS
SN            SN
```

B:
```
NS     NS     NS
SN            SN
```

C:
```
NSN          NSN
SNS          SNS
```

D:
```
NSN    NS    NSN
SNS          SNS
```



| B2 gap | pull | minus 600 g | minus 600 g, 0.2 mm off sideways |
| --- | --- | --- | --- |
| 0 mm | 4.98 kg | 4.38 kg | 3.91 kg |
| 0.1 mm | 4.07 kg | 3.47 kg | 3.24 kg |
| 0.2 mm | 3.43 kg | 2.83 kg | 2.69 kg |
| 0.3 mm | 2.94 kg | 2.34 kg | 2.25 kg |

0.2 mm off sideways, it pulls back into line with ~700 g.

E: lip or tongue-and-groove along the bottom edge takes the bending, magnets just hold it closed.

### Magnet 'protection'
Magnets sunk in the pocket and capped with epoxy, cured face-down on release film (packing tape on glass) so it's flush.

Cured face-up it domes, and the domes set the gap.

Epoxy depth sets the gap: 0.05 mm per side = 0.1 mm.

The epoxy also holds the magnets in, each one pulls ~400 g at 0.1 mm.

Scuff the PETG pockets, CA bonds poorly to PETG.