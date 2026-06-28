# Hall Effect Sensors

## Identify
I need to figure out what hall effect sensors i am going to use for the keys, as well as the analog MUX chip i am going to use
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
- **TI DRV5055** (bidirectional), **Allegro A1324/A1326**, **Honeywell SS495A** — alternates.

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
