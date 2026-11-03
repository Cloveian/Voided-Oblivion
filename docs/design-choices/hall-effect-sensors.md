# Hall Effect Sensors

## Identify
I need to figure out what hall effect sensors i am going to use for the keys, plus the analog MUX chip
### Relevant constraints/nice to haves:

- Sub-1 ms / 1000 Hz scan
- Per-key analog readout
- Fits the low-profile void-based switch
- Easily-replaceable switches


## Brainstorm

### Hall effect sensors
- **GH39F** (chosen), cheap analog ratiometric hall sensor; the one used in the Void switch reference design.
- **49E / SS49E clones**, very common (~$0.05–0.10 @ LCSC). Higher current draw.
- **TI DRV5056**, radiometric, unidirectional (good: magnet approaches from one side), temperature-stable, and lower current (~1.5 mA vs ~6 mA).
- **TI DRV5055** (bidirectional), **Allegro A1324/A1326**, **Honeywell SS495A** - alternates.

### Analog MUXs

- **74HC4051** (8:1, 3 select lines)
- **74HC4067** (16:1, 4 select lines)
- **ADG706 / ADG726** (16:1, low on-resistance, faster), expensive

## Select

| Criteria                          | Weight |  GH39F  | DRV5056 | A1326 |
| --------------------------------- | :----: | :-: | :-----: | :---: |
| Operating current (power)         |   9    |  4  |    9    |   6   |
| Cost (×keys×tiles)                |   8    |  9  |    5    |   3   |
| Proven w/ hall switches           |   6    |   10    |    5    |   4   |
| Signal quality (ratiometric/temp) |   6    |    8    |    9    |   8   |
| Availability (LCSC etc.)          |   5    |    8    |    7    |   6   |
| Package / low-profile SMD         |   4    |    7    |    8    |   8   |
| **Weighted Total**                |        | **284** |   272   |  212  |

**Winner: GH39F (284 / 74.7%)**, over DRV5056 (272).

DRV5056 stays the fallback if the power budget turns out brutal.

**Design for sensor substitution:** any cheap analog hall works fine for a keyboard, since per-key min/max calibration absorbs sensitivity and offset differences (so signal quality barely matters).

the board uses a common 3-pin SOT-23 (Vcc/OUT/GND) footprint so any pin-compatible analog hall (GH39F, SMD 49E, A132x, DRV5056, ...) is a drop-in replacement.

Analog hall availability is known to fluctuate (the Void-Switch 'reference' sensor itself was selected during COVID-era supply issues), so GH39F is the default.

**Carry-forward to Power:** worst-case ~9 mA x ~30 keys x N tiles is up to ~270 mA/tile of continuous sensor current. ~~Strong argument for bank-powering the sensors (only energize the group being scanned).~~

> **Update: bank gating isnt really needed.** It would only ever exist to keep the 3V3 LDO inside its thermal limits, but now that the LDO moved to a package that can actually take 400mA, there is no point now, and at 1000Hz gateing is risky.

**MUX: 2x 74HC4067 (16:1):** 
32 channels on 2 ADC pins + 4 shared select lines (fewest parts), pleanty of headroom.

if reading by stream of consciousness go back to [index](../index.md)

## Revisit: hall effect sensor heat sensitivity

so i was on a call with riskable and he mentioned his experience that analog hall sensors are really sensitive to heat.

he's had it happen multiple times: he replaces a dead rgb LED and the heat cooks the hall sensor right next to it. the sensitivity shifts permanently.

i compared a bunch of datasheets. the A1326 from allegro has this dynamic offset cancellation thing that actively compensates for mechanical stress on the package (including from rework heat).

the DRV5056 has a higher operating temp range. the GH39F has none of that.

so yeah if you were hand soldering an LED at 350C right next to a SOT-23 with a 150C storage limit you could absolutely cook it.

but i have a combo of tools that make those points less relavent it:

1. i have a hotplate.
2. i can use low temp solder paste.
3. the firmware calibrates this out anyway.

## Correction: the DRV5056 current figure above is wrong

i wrote "**DRV5056** ... lower current (~1.5 mA vs ~6 mA)" in the brainstorm, and scored **Operating current = 9** for it against GH39F's 4 in the table - on a row weighted **9**.

not idea where i got that number, cuz looking the datasheets again:

| Part | ICC | at |
| --- | --- | --- |
| GH39F | - / 9mA max | (5V characterised) |
| **DRV5056** | **6mA typ / 10mA max** | flat across 3–5.5V |
| **DRV5055** | **2mA typ / 4mA max** | VCC = 3.3V |

DRV5056 is not the low-current part - it's slightly worse than GH39F. The low-current TI part in that family is the **DRV5055**, and only at 3.3V, which happens to be exactly what i run.

So that row should have been roughly GH39F 4 / DRV5056 4 / DRV5055 9. Does it change the winner? No, GH39F still wins on cost and proven-with-the-Void-switch, and DRV5056 loses its single biggest advantage.

So the fallback is the DRV5055. Two other reasons it's the better fallback:
- **It's Bipolar**, the DRV5056 is unipolar
- **it's rated ratiometric** (from datasheet). addresses [the ratiometric assumption](../schematic-design/keys.md#the-ratiometric-assumption) i currently can't verify for the GH39F.

**Sourcing:** **DRV5055A1QDBZR** (C962987, SOT-23, 6660 in stock, $0.594) vs GH39FKSW (C266230, 2968 in stock, $0.130). Pin-compatible - **verified**: both are 1=VCC, 2=OUT, 3=GND in SOT-23, which matches the symbol already on the board.

## Re-revisit: i'm not assembling this myself anymore

i've since assembled a board with an MCU on it by hand and it is *substantially* less fun than a passive board. so this is going to JLC assembled. which means two of the three legs i was standing on just walked off:

1. ~~**i have a hotplate**~~ JLC has the oven now. i don't control the profile.
2. ~~**low temp solder paste**~~ JLC's line runs standard paste. peak is going to be well north of the 160C i was planning for, whether that's their leaded process or lead-free.
3. **the firmware calibrates it out anyway** still true.

GH39F's *only* thermal numbers are **TA -40 to +85C operating** and **TS -65 to +150C storage** (p.94/96 of the datasheet) - there is **no reflow profile in it at all**.

under standard reflow i'm 80-100C past the only published ceiling with nothing in the datasheet saying that's fine.

does this change the part choice? no. does it change what i'm relying on? yes. i'm now relying entirely on leg 3, plus the empirical fact that every commercial hall-effect keyboard is reflow-assembled with sensors in this class and they work.

### what i should actually do about it

the DRV5056 fallback is still there and it explicitly has a wider operating range, so if a batch comes back with dead or drifting keys that's the escape hatch.

**side effect worth noting:** chip-scale / fine-pitch parts (WLP, DSBGA, 0.4mm-pitch QFN) were previously ruled out because low-temp bismuth paste won't reflow SAC balls and i can't inspect or rework a BGA at home.

none of that applies now - it's a fab capability question instead. so a part like the MAX40203 in WLP is fine to keep.

**new cost i've bought instead:** one tile is roughly 200 placements (30 switches + 30 LEDs + 30 sensors + the rest), times however many tiles, and every part on the BOM is a JLC *extended* part so far, each carrying a setup fee.

worth a real quote for one tile before i commit to a tile count.

if reading by stream of consciousness go back to [index](../index.md)

## Re-revisit: the sequal
I am acctualy gonna assemble it myself cuz it saves ~$250 (not including labor). mainly becaude of terrifs.
