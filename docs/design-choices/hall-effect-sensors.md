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

if reading by stream of consciousness go back to [index](../index.md)
