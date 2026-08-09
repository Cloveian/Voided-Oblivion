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
- **TI DRV5055** (bidirectional), **Allegro A1324/A1326**, **Honeywell SS495A** - alternates.

### Analog MUXs

- **74HC4051** (8:1, 3 select lines)
- **74HC4067** (16:1, 4 select lines)
- **ADG706 / ADG726** (16:1, low on-resistance, faster), expensive

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

GH39F is the cheap analog ratiometric hall sensor used in the Void switch reference design, so it's the proven choice for this exact switch design, and it's cheap. It *loses* the power axis (supply current 2-9 mA, so budget the 9 mA worst case, vs DRV5056's ~1.5 mA) but wins on proven + cost, and it stays ahead even with power weighted to the top of the scale. 

DRV5056 stays the fallback if the power budget turns out brutal. A1326 (212) is dominated.

**Design for sensor substitution:** any cheap analog hall works fine for a keyboard, since per-key min/max calibration absorbs sensitivity and offset differences (so signal quality barely matters). Rather than single-source one generic part, the board uses a common 3-pin SOT-23 (Vcc/OUT/GND) footprint so any pin-compatible analog hall (GH39F, SMD 49E, A132x, DRV5056, ...) is a drop-in. Analog hall availability is known to fluctuate (the Void reference sensor itself was selected during COVID-era supply issues), so GH39F is the default, not a hard dependency.

**Carry-forward to Power:** worst-case ~9 mA x ~30 keys x N tiles is up to ~270 mA/tile of continuous sensor current. Strong argument for bank-powering the sensors (only energize the group being scanned).

> **Update - bank gating was scored and rejected.** It only ever existed to keep the 3V3 LDO inside its thermal limits; once the LDO moved to a package that can actually take 400mA, the reason went away, and at 1000Hz every gating scheme is a bet on a GH39F power-on settling time the datasheet never publishes. Full working in [keys](../schematic-design/keys.md#sensor-bank-power-gating). The 270mA stays as a permanent load.

**MUX: 2x 74HC4067 (16:1)** gives 32 channels on 2 ADC pins + 4 shared select lines (fewest parts). With ~10x timing headroom, the premium low-Ron muxes (ADG706) buy nothing.

if reading by stream of consciousness go back to [index](../index.md)

## Revisit: hall effect sensor heat sensitivity

so i was on a call with riskable and he mentioned his experience that analog hall sensors are really sensitive to heat.

he's had it happen multiple times: he replaces a dead rgb LED and the heat cooks the hall sensor right next to it. the sensitivity shifts permanently and the key never feels right again.

i compared a bunch of datasheets, the A1326 from allegro has this dynamic offset cancellation thing that actively compensates for mechanical stress on the package (including from rework heat), and the DRV5056 has a higher operating temp range so it survives better. the GH39F has none of that. so yeah if you were hand soldering an LED at 350C right next to a SOT-23 with a 150C storage limit you could absolutely cook it.

but i have three things that each individually solve this:

1. **i have a hotplate.** rework on a hotplate with preheat means the temperature delta between the LED pad and the sensor next to it is tiny. no thermal shock.

2. **i can use low temp solder paste.** Sn42/Bi57/Ag1 melts at 138C, peak reflow is like 160C. the GH39F's storage limit is 150C and its operating is 85C. 160C peak is barely over storage and way gentler than 250C lead-free reflow. and for a desk keyboard that sits at room temp its whole life, i don't care about the brittleness tradeoff.

3. **the firmware calibrates this out anyway.** the whole point of analog hall sensors with per-key min/max calibration is that sensitivity and offset differences get absorbed. even if rework shifts the null by 80mV or the gain drops 5%, the firmware just re-reads the endpoints and the key feels the same. this was already in the design doc from the start.

so basically if i was building this with a hand iron at 350C, riskable would be right to warn me. but hotplate + low temp paste + firmware calibration means the thermal differences between sensor options are basically irrelevant. GH39F stays the right call, and if i somehow kill one during rework they're 16 cents to replace.

## Correction: the DRV5056 current figure above is wrong

i wrote "**DRV5056** ... lower current (~1.5 mA vs ~6 mA)" in the brainstorm, and scored **Operating current = 9** for it against GH39F's 4 in the table - on a row weighted **9**, the heaviest one. Went back to the actual TI datasheet (SBAS644C) and that number isn't real:

| Part | ICC | at |
| --- | --- | --- |
| GH39F | — / 9mA max | (5V characterised) |
| **DRV5056** | **6mA typ / 10mA max** | flat across 3–5.5V |
| **DRV5055** | **2mA typ / 4mA max** | VCC = 3.3V |

**DRV5056 is not the low-current part - it's slightly worse than GH39F.** The low-current TI part in that family is the **DRV5055**, and only at 3.3V, which happens to be exactly what i run.

So that row should have been roughly GH39F 4 / DRV5056 4 / DRV5055 9. Does it change the winner? No - GH39F still wins on cost and proven-with-the-Void-switch, and DRV5056 loses its single biggest advantage, so it moves *further* behind. But the table was right for a wrong reason on its heaviest row, and that's worth knowing if i ever re-run it.

**The fallback part is therefore DRV5055, not DRV5056.** Two other reasons it's the better fallback:
- **Bipolar** (responds to either magnetic pole). DRV5056 is *unipolar* - "output drives 0.6V when no field is present and increases when a **south** pole is applied" - so if the switch magnet presents north to the sensor it reads nothing at all. For a drop-in substitution where i haven't verified magnet orientation, bipolar is the safe choice.
- **Explicitly ratiometric**, stated by TI rather than assumed. That directly addresses [the ratiometric assumption](../schematic-design/keys.md#the-ratiometric-assumption) i currently can't verify for the GH39F.

Sourcing: **DRV5055A1QDBZR** (C962987, SOT-23, 6660 in stock, $0.594) vs GH39FKSW (C266230, 2968 in stock, $0.130). Pin-compatible - **verified**: both are 1=VCC, 2=OUT, 3=GND in SOT-23, which matches the symbol already on the board. The generic-footprint decision earned its keep.

## Re-revisit: i'm not assembling this myself anymore

ok so the argument above has aged badly and i need to say so rather than quietly leave it standing.

i've since assembled a board with an MCU on it by hand and it is *substantially* less fun than a passive board. so this is going to JLC assembled. which means **two of the three legs i was standing on just walked off**:

1. ~~**i have a hotplate**~~ - JLC has the oven now. i don't control the profile.
2. ~~**low temp solder paste**~~ - JLC's line runs standard paste. peak is going to be well north of the 160C i was planning for, whether that's their leaded process or lead-free.
3. **the firmware calibrates it out anyway** - still true, and it was always the strongest one.

and the datasheet gives me nothing to fall back on. GH39F's *only* thermal numbers are **TA -40 to +85C operating** and **TS -65 to +150C storage** (p.94/96 of the datasheet) - there is **no reflow profile in it at all**. so under my old plan i was at 160C peak against a 150C storage number, which was "barely over" as i wrote above. under standard reflow i'm 80-100C past the only published ceiling with nothing in the datasheet saying that's fine.

**does this change the part choice? no. does it change what i'm relying on? yes.** i'm now relying entirely on leg 3, plus the empirical fact that every commercial hall-effect keyboard is reflow-assembled with sensors in this class and they work. that's a real argument, it's just not a *datasheet* argument, and i'd rather write that down than pretend the original three-legged version still holds.

what i should actually do about it:
- ask JLC for their **leaded** process if it's an option - lower peak, and i don't care about RoHS for a personal board
- ask the supplier whether GH39F has a reflow qualification that just isn't in the public datasheet
- per-key min/max calibration was always in the design, so a sensitivity shift gets absorbed. the failure mode i'd actually worry about is a sensor that shifts *over time* after being cooked, not one that reads differently on day one - calibration catches the second, not the first

the DRV5056 fallback is still there and it explicitly has a wider operating range, so if a batch comes back with dead or drifting keys that's the escape hatch, not a redesign.

**side effect worth noting:** dropping hand assembly also un-blocks a bunch of package decisions. chip-scale / fine-pitch parts (WLP, DSBGA, 0.4mm-pitch QFN) were previously ruled out because low-temp bismuth paste won't reflow SAC balls and i can't inspect or rework a BGA at home. none of that applies now - it's a fab capability question instead. so a part like the MAX40203 in WLP is fine to keep.

**new cost i've bought instead:** assembly is now a line item rather than free labour. one tile is roughly 200 placements (30 switches + 30 LEDs + 30 sensors + the rest), times however many tiles, and every part on the BOM is a JLC *extended* part so far, each carrying a setup fee. worth a real quote for one tile before i commit to a tile count - it may reprice the whole "how many tiles can i afford" question.

if reading by stream of consciousness go back to [index](../index.md)
