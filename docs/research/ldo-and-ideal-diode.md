# LDO and Ideal Diode — datasheet-derived implementation reference

Scope: the two small parts on the 5V/3V3 path — the XC6220B331MR 3.3V LDO (always-on bootstrap rail → MCU/analog domain) and the MAX40203 ideal diode (local 5V buck OR'd onto the shared bootstrap bus). Written cold, from datasheets only, without looking at the current schematic. Every number below is cited to a datasheet section/table/page; anything the datasheet doesn't state is marked "not specified."

Datasheets used:
- `Refrences/datasheets/XC6220B331MR-ldo.pdf` — Torex XC6220 Series, doc ETR0341-013 (31 pages, page numbers below refer to the printed "N/31" footer).
- `Refrences/datasheets/MAX40203-ideal-diode.pdf` — Analog Devices/Maxim MAX40203, 19-100354 Rev 3, 3/21 (page numbers below refer to the printed "Maxim Integrated | N" footer).
- For part-identity comparison only, the MAX40200 datasheet (19-8728 Rev 4, 2/23) was also fetched and read, but not saved into the project (not requested) — cited inline as "MAX40200 datasheet" where relevant.

---

## PART 1 — XC6220B331MR (Torex 3.3V LDO)

### Part identity

Ordering code decode, per the "Product Classification / Ordering Information" table (page 3/31):

`XC6220 ①②③④⑤⑥-⑦` = `XC6220 B 3 3 1 MR`

| Field | Value | Meaning (page 3/31) |
|---|---|---|
| ① Type of CE | `B` | Without CE pull-down resistor, **with** CL auto-discharge ("Standard") |
| ②③ Output voltage | `33` | 3.3 V (e.g. "3.0V → ②=3, ③=0") |
| ④ 2nd decimal digit | `1` | 2nd decimal place is "0" → 3.30V exactly (vs. `B` = "5" → x.x5V) |
| ⑤⑥-⑦ Package | `MR` | SOT-25, 3000/reel |

**Output voltage is factory-fixed by laser trimming, not externally set.** The general description states: "Output voltage is selectable in 0.05V increments within the range of 0.8V~5.0V, using laser trimming technologies" (page 1/31) — the "selectable" is a factory ordering-code choice (this is why the "331" suffix exists), not a user-adjustable feedback divider. There is no FB pin and no external resistor network in the pin assignment table (page 2/31). **There is no design equation for setting VOUT** — it is fixed at 3.30V for this exact part number.

Accuracy for VOUT ≥ 2.0V is ±1% in HS mode / ±2% in PS mode (Features, page 1/31; Electrical Characteristics, page 5/31). The Voltage Chart (page 7/31) gives the exact guaranteed band at VOUT(T)=3.30V: HS mode 3.2670V–3.3330V, PS mode 3.2340V–3.3660V.

Family: XC6220A/B/C/D differ only in CE pull-down resistor and CL auto-discharge presence (page 3/31 "FUNCTIONS" table); B = no pull-down, has auto-discharge.

### Absolute maximum ratings that constrain this design

(Page 4/31, Ta=25°C unless noted)

| Parameter | Symbol | Rating | Units |
|---|---|---|---|
| Input voltage | VIN | VSS−0.3 to +6.5 | V |
| Output current | IOUT | 1400 | mA |
| Output voltage | VOUT | VSS−0.3 to VIN+0.3 | V |
| CE input voltage | VCE | VSS−0.3 to 6.5 | V |
| Power dissipation, SOT-25 | Pd | 250 mW (standalone) / 600 mW (PCB-mounted, see note *2) | mW |
| Operating ambient temp | Topr | −40 to +85 | °C |
| Storage temp | Tstg | −55 to +125 | °C |

**Note:** the Absolute Maximum Ratings table has no separate "Junction Temperature" line item for the XC6220 (unlike the MAX40203 below). The IC's own thermal-shutdown trips at TJ=150°C typ (Electrical Characteristics, page 6/31, see below), and the packaging-info power-dissipation curve (page 26/31) is built around a design point of TJ=125°C. Treat 125°C as the rated design ceiling and 150°C as the hard (typ, not guaranteed min/max) shutdown point — **there is no datasheet-stated "absolute max TJ" number to cite for this part.**

5V (our VIN) is well inside VIN's 6.5V abs-max and within the 1.6–6.0V operating range (page 1/31 Features).

### Key electrical characteristics

(VDD/VCE=VIN unless noted; page 5–6/31)

| Parameter | Symbol | Condition | Min | Typ | Max | Units | Source |
|---|---|---|---|---|---|---|---|
| Output current, max | IOUTMAX | VIN=VOUT(T)+1.0V, 1.2V≤VOUT(T)≤5.0V | 1000 | 1200 | — | mA | p.5 |
| Load regulation | ΔVOUT | HS mode, 10mA≤IOUT≤300mA | — | 10 | 45 | mV | p.5 |
| Dropout voltage 1 (@300mA) | Vdif1 | IOUT=300mA, VOUT(T)=3.30V bracket (2.70–3.45V) | — | **65** | — | mV | p.7 Voltage Chart 2, breakpoint row |
| Dropout voltage 2 (@1000mA) | Vdif2 | IOUT=1000mA, same VOUT bracket | — | — | **110** | mV | p.7 Voltage Chart 2, breakpoint row |
| Supply current, HS mode | ISS1 | IOUT=10mA, A/B series | — | 50 | 108 | µA | p.5 |
| Supply current, PS mode | ISS2 | IOUT=0.1mA, A/B series | — | 8 | 18 | µA | p.5 |
| Standby current | ISTBY | VIN=6.0V, CE=VSS | −0.1 | 0.01 | 0.1 | µA | p.5 |
| Line regulation | ΔVOUT/ΔVIN | VOUT(T)+0.5V≤VIN≤6.0V, IOUT=100mA, 1.1≤VOUT(T)≤5.0V | — | 0.01 | 0.20 | %/V | p.6 |
| Output temp coefficient | ΔVOUT/(ΔTa·VOUT) | IOUT=30mA, −40≤Ta≤85°C | — | ±100 | — | ppm/°C | p.6 |
| PSRR | — | f=1kHz, IOUT=30mA, VIN=VOUT(T)+1.0V+0.5Vpp AC (0.85≤VOUT(T)≤4.7V bracket) | — | 50 | — | dB | p.6 |
| Limit current | ILIM | VIN=VOUT(T)+1.0V, 1.2≤VOUT(T)≤5.0V | 1005 | 1200 | — | mA | p.6 |
| Short current | ISHORT | VOUT shorted to VSS | — | 180 | — | mA | p.6 |
| Inrush current | IRUSH | CL=22µF, CE 0V→VOUT(T)+1.0V, <1ms | — | — | 700 | mA | p.6 |
| Thermal shutdown detect | TTSD | Junction temp | — | 150 | — | °C | p.6 |
| Thermal shutdown release | TTSR | Junction temp | — | 135 | — | °C | p.6 |
| CL discharge resistance | RDCHG | B/D series only, VIN=6.0V, VOUT=5.0V | — | 460 | — | Ω | p.6 |
| CE high level voltage | VCEH | — | 1.2 | — | 6.0 | V | p.6 |
| CE low level voltage | VCEL | — | — | — | 0.4 | V | p.6 |
| CE high current (A/B) | ICEH | VCE=VIN=6.0V | −0.1 | — | 0.1 | µA | p.6 |

**Output noise (µV RMS, spectral density):** not specified anywhere in this datasheet. No "Output Noise Voltage" row exists in the Electrical Characteristics tables, and no noise-density graph appears in the Typical Operating Characteristics section. Only the marketing line "low noise ... CMOS voltage regulator" (page 1/31, General Description) references noise qualitatively. **This is a real gap for an ADC-reference application and cannot be filled from this datasheet.**

**PSRR vs. frequency:** section (15) "Ripple Rejection Ratio" (pages ~20–21/31) is a plotted graph only — no tabulated dB-vs-Hz values are given in text, so beyond the single 50dB@1kHz table entry above, PSRR-vs-frequency is **not extractable as a number** from this PDF (image data only).

### Design equations

- **Junction temperature:** TJ = Ta + (Pd × θJA), where Pd = (VIN − VOUT) × IOUT (linear regulator dissipation, standard form; not stated as an explicit formula in this datasheet but directly implied by the Pd-vs-Ta curves on page 26/31).
- **θJA (SOT-25, PCB-mounted):** derived from the page 26/31 packaging data — Pd=600mW at Ta=25°C and Pd=240mW at Ta=85°C, both referenced to TJ,max=125°C design point:
  - θJA = (125−25)/0.600 = **166.67°C/W**
  - θJA = (125−85)/0.240 = **166.67°C/W** (self-consistent)
  - Measured per JEDEC on a 40×40mm, 1.6mm FR-4 board with 50% copper coverage on top and back, package pad tied to copper (page 26/31, "Measurement Condition").
- **No output-voltage-setting equation** — see Part Identity above; VOUT is fixed at 3.30V by the ordering code, no R1/R2 divider exists on this pin-out.
- **CL discharge (informational only, B/D series):** V(t) = VOUT(E)·e^(−t/τ), τ = RDCHG × CL (page 9/31). Only relevant if CE is pulled low with VIN still present — see Gotchas.

### Worked values for this application

Input: VIN = 5.0V (BS+, always-on bootstrap rail). Output: VOUT = 3.30V. Load per project brief: 200–400mA (RP2350B + up to 30 Hall sensors + 2 muxes, sensor share firmware-gateable).

**Dropout margin:** Available headroom = 5.0 − 3.3 = 1.7V. Worst-case dropout at 1000mA (Vdif2 max) = 110mV (p.7). Margin ratio ≈ 1700mV / 110mV ≈ **15.5×**. At 400mA the actual dropout will be well under the 110mV/1000mA figure (dropout scales roughly with Rds(on)×I, and 0.2Ω is the quoted driver on-resistance per General Description, p.1/31 — 400mA×0.2Ω≈80mV, consistent with interpolating between the 65mV@300mA and 110mV@1000mA table points). **Conclusion: 5V-in/3.3V-out has enormous dropout margin at all specified loads — dropout is not a constraint here.**

**Junction temperature — this is the actual constraint:**

Pd = (VIN − VOUT) × IOUT

| IOUT | Pd | TJ @ Ta=25°C (TJ=Ta+Pd·166.67°C/W) | TJ @ Ta=45°C | TJ @ Ta=70°C |
|---|---|---|---|---|
| 200mA | 340mW | 25+56.7 = **81.7°C** | 45+56.7 = **101.7°C** | 70+56.7 = **126.7°C** |
| 300mA | 510mW | 25+85.0 = **110.0°C** | 45+85.0 = **130.0°C** | 70+85.0 = **155.0°C** |
| 400mA | 680mW | 25+113.3 = **138.3°C** | 45+113.3 = **158.3°C** | 70+113.3 = **183.3°C** |

Compared against the datasheet's own design ceiling of TJ=125°C (page 26/31 Pd-Ta curve basis) and its typ thermal-shutdown trip at 150°C (page 6/31):

- At the worst-case 400mA load figure given in the project brief, **the part exceeds its own 125°C design-point rating at any ambient ≥ 25°C**, and will hit or exceed the 150°C thermal-shutdown trip point at ambients in the 25–45°C range that are entirely plausible inside an enclosed keyboard tile.
- At 300mA the part is marginal — over the 125°C design point above ~15°C ambient, though still under the 150°C shutdown trip until ~40°C ambient.
- At 200mA the part has real margin (about 23°C to the 125°C design ceiling at 45°C ambient).
- **This assumes Torex's own reference board thermals (166.67°C/W, 40×40mm board, 50% Cu both sides, page 26/31).** A smaller/thinner copper pour around the actual part will make θJA worse (higher), pulling every number in the table further over budget.

**This is the headline finding for this chip: a linear regulator dropping 5V→3.3V cannot sustain the full 200–400mA load range named in the project brief without exceeding its own rated thermal design point, unless firmware keeps steady-state load well under ~250mA or the layout dedicates significantly more copper than the reference condition.**

**Capacitor selection** (VOUT(T)=3.30V falls in the "3.00V–3.50V" bracket, page 9/31 table):

| CIN choice | Required CL (min) |
|---|---|
| 4.7µF | 47µF |
| **10µF** | **4.7µF** |
| 22µF | 4.7µF |

Using the datasheet's own characterization condition (CIN=10µF, CL=4.7µF, ceramic — explicitly used throughout the "XC6220x 301" typical-characteristics graphs, e.g. page 13/31 caption "CIN=10μF, CL=4.7μF (ceramic)"), both are already standard E6/E12 values — **ideal → E-series → actual → error is 10µF→10µF (0% error), 4.7µF→4.7µF (0% error).** No derivation needed; these are the manufacturer-characterized values, not derived ones.

### Recommended implementation (pin by pin)

SOT-25 pinout (page 2/31 "PIN ASSIGNMENT" table):

| Pin | Name | Connection |
|---|---|---|
| 1 | VIN | BS+ (5V always-on bootstrap rail), with CIN=10µF ceramic to VSS close to the pin |
| 2 | VSS | GND |
| 3 | CE | **Tie directly to VIN (pin 1).** VCEH spec is 1.2–6.0V (p.6) and abs-max VCE is VSS−0.3 to 6.5V (p.4) — 5V is safely inside both, so a direct tie is valid. This satisfies the project requirement that "this rail must never be gated off" and simultaneously satisfies the datasheet's own hard requirement that CE must never be left floating on A/B-series parts (page 2/31, "CE PIN LOGIC CONDITION": OPEN = "Undefined state (XC6220A/B Series)... Please avoid the state of OPEN, and connect CE pin to any arbitrary voltage"). |
| 4 | NC | No connect — leave unconnected or use for routing only, not internally connected (page 8/31 pin assignment). |
| 5 | VOUT | 3.3V rail out, with CL=4.7µF ceramic to VSS close to the pin |

### Decoupling and passives

- CIN = 10µF ceramic, as close to VIN/VSS as possible ("Notes on Use" #3, page 10/31: "Please wire the input capacitor (CIN) and the output capacitor (CL) as close to the IC as possible").
- CL = 4.7µF ceramic minimum (per the VOUT=3.0–3.5V/CIN=10µF bracket, page 9/31); this is a stability-relevant minimum, not just a filtering nicety — "If a loss of the capacitance happens, the stable phase compensation may not be obtained" (page 9/31).
- ESR: no explicit min/max ESR spec is given. The datasheet states the part has "a built-in phase compensation circuit which means that a stable output voltage is achieved even if the IC is used with low ESR capacitors" (page 9/31) — i.e. low-ESR ceramics are explicitly fine, but **no numeric ESR window (min or max) is stated anywhere in this document.**
- Dielectric type: the graphs' test conditions state "(ceramic)" throughout but do not specify X7R/X5R/COG — **not specified.**
- Case size: 4.7µF and 10µF at low voltage rating (6.3V is plenty for a 5V/3.3V rail) are commonly available in 0402, but with meaningful DC-bias capacitance derating at that case size — **this is general MLCC industry knowledge, not a datasheet fact for either part**, and is flagged here per your sizing rule ("call out anywhere 0402 is wrong"): verify actual effective capacitance at 5V bias for whatever 0402 10µF part is selected, since derated capacitance below the ~4.7–10µF stability minimum would be a real stability risk. 0603 may be the safer default for these two caps specifically.
- Inrush: IRUSH is rated up to 700mA for ~1ms at power-on with CL=22µF (page 6/31) — with our smaller 4.7µF CL, inrush will be lower, but input trace and any upstream OR-diode (see Part 2) must tolerate whatever inrush actually occurs at cold power-up.

### Layout notes

- Torex's own thermal characterization (166.67°C/W, page 26/31) assumes a 40×40mm board with 50% copper coverage top and bottom and the package pad tied into that copper. **A keyboard tile is unlikely to have 1600mm² of contiguous copper available near this part** — real θJA in the final layout should be assumed worse than 166.67°C/W unless deliberately matched. Given the thermal margin problem identified above, this makes the situation worse, not better, in a compact tile layout.
- CIN and CL both need to be placed immediately adjacent to their respective pins (VIN/VSS and VOUT/VSS) per "Notes on Use" #3 (page 10/31) and #2 ("Where wiring impedance is high, operations may become unstable due to noise and/or phase lag ... strengthen VIN and VSS wiring in particular").
- Since this is the ADC reference domain, keep the VOUT trace and its return path away from any switching-regulator (gated-5V buck) copper, though the datasheet itself gives no EMI/layout guidance beyond the wiring-impedance note above — this recommendation is general practice, not datasheet-sourced.

### Gotchas and failure modes

- **Thermal is the real constraint, not dropout.** See Worked Values — at the project's stated 400mA worst case, this part exceeds its own datasheet design point at any realistic ambient, and can reach its 150°C typ thermal-shutdown trip. This directly threatens "sub-1ms key scan at 1000Hz" if the LDO cycles in and out of thermal shutdown under sustained full-bank Hall-sensor operation.
- **CE must never float** on this A/B-family part (open CE = "Undefined state," page 2/31) — tying to VIN as recommended above avoids this, but if a design instead drives CE from GPIO or another rail, that source must be guaranteed present whenever VIN is present, and must never be left in a Hi-Z state.
- **Power-down / cold-start interaction with CL auto-discharge:** the "B" series (this part) includes a CL auto-discharge N-channel FET across R1/R2 that engages "while the power supply is applied to VIN" when CE goes low (page 9/31, "CL Discharge Function") — this actively pulls VOUT to GND on a controlled shutdown (CE low, VIN still up), preventing the output from floating charged after a power-down. **But in our implementation CE is tied directly to VIN**, so on a hot-unplug both nodes collapse together rather than CE going low while VIN is still present. Whether the discharge FET remains biased and active during that simultaneous-collapse case is **not stated in the datasheet** — it may or may not meaningfully discharge CL faster than the downstream load alone would. This is exactly the class of cold-start ambiguity worth bench-verifying.
- **Notes on Use item 4** (page 10/31) states that on the A/C series (no auto-discharge), "the output voltage may float with a leakage current... while stand-by" — this does **not** apply to the B series used here, but is worth knowing since it explains why B/D exist.
- Reflow: this device is rated to standard reflow peak temps implicitly (no explicit "reflow peak" line was found in the Absolute Maximum Ratings table itself in the pages read — see Open Questions).

### Open questions / not determinable from the datasheet

- Output noise voltage (µV RMS or spectral density, µV/√Hz) — not specified anywhere in the datasheet. This is a real gap given the stated ADC-reference role; get this from lab measurement or an app note, not this PDF.
- PSRR vs. frequency beyond the single 50dB@1kHz table point — only shown as an un-tabulated graph.
- No explicit ESR min/max window for CIN/CL — only a qualitative "works fine with low-ESR ceramic" statement.
- No explicit reflow-peak-temperature or MSL rating was located in the pages captured by this extraction; if needed for the low-temp Sn42/Bi57/Ag1 hotplate process, check the full package-outline/reliability pages (25–31/31) which were not fully read in this pass.
- No absolute-maximum Junction Temperature line item exists in the Abs Max Ratings table (only a thermal-shutdown detect/release pair in Electrical Characteristics) — the effective ceiling is inferred (125°C design point / 150°C typ shutdown), not directly stated as a hard rating.
- Actual real-board θJA for whatever copper area this tile design ends up with — the datasheet only characterizes one specific 40×40mm/50%-Cu reference board.

---

## PART 2 — MAX40203 (Analog Devices ideal diode)

### Part identity

**Confirmed part: MAX40203**, from Analog Devices (formerly Maxim Integrated), datasheet 19-100354 Rev 3, 3/21, downloaded from analog.com and saved as `Refrences/datasheets/MAX40203-ideal-diode.pdf`.

Title: "Ultra-Tiny **nanoPower**, 1A Ideal Diodes with Ultra-Low-Voltage Drop" (page 1).

**Ordering info** (page 18): two package options, both with an EN pin —

| Part | Temp range | Package | Top mark |
|---|---|---|---|
| MAX40203ANS+T | −40 to +125°C | 4-bump WLP | +H |
| MAX40203AUK+T | −40 to +125°C | 5-pin SOT23 | AMJO |

**Comparison against MAX40200** (separately fetched, 19-8728 Rev 4, 2/23, for identity-confirmation purposes only — not saved to the project since it wasn't requested): both parts, *as currently sold*, share the same 4-bump WLP / 5-pin SOT23 packages, the same pinout (VDD/OUT/EN/GND/NC), and both currently carry an EN pin — so pin count and EN presence do **not** distinguish them in the datasheets as they exist today. What differs:

| | MAX40200 (rev.4, 2/23) | MAX40203 (rev.3, 3/21) |
|---|---|---|
| Marketing tier | "Micropower" | "**nanoPower**" |
| Quiescent current IDD (EN=VDD, IFWD=0) | 7µA typ / 18µA max | **300nA typ / 500nA max** (~23–36× lower) |
| VDD operating range | 1.5–5.5V | **1.2–5.5V** (wider low end) |
| WLP abs-max continuous current | 1.2A | **1.5A** |
| SOT23 abs-max continuous current | 1.0A | 1.0A (same) |
| Forward voltage @1A, SOT23 | 197mV typ / 350mV max | 230mV typ / 500mV max (MAX40200 slightly better here) |
| Reverse turn-off threshold | 20mV typ | 26mV typ |
| Thermal protection threshold | 154°C typ | 163°C typ |

**Given the project's rails (always-on bootstrap bus, many tiles' diodes idle in parallel most of the time), the ~23–36× lower quiescent current of the MAX40203 is the decisive difference** — with potentially dozens of tiles' diodes sitting on the shared bus continuously, nanoAmp-class IQ vs. microAmp-class IQ is a real standby-power difference at scale. **MAX40203 is the correct choice for this application**, consistent with what's already specified in the project brief. Both families support an EN pin and both are rated to 1A in WLP; SOT23 continuous rating is identical (1.0A) between them — see Worked Values below for why that 1.0A SOT23 rating is not actually usable continuously for either part.

### Absolute maximum ratings that constrain this design

(Page 2)

| Parameter | Rating |
|---|---|
| Any pin to GND | −0.3V to +6V |
| Continuous current into EN | 10mA |
| Continuous current VDD→OUT (WLP) | 1.5A |
| **Continuous current VDD→OUT (SOT23)** | **1A** |
| Continuous power dissipation, WLP (Ta=70°C, derate 9.58mW/°C above) | 766mW |
| **Continuous power dissipation, SOT23 (Ta=70°C, derate 3.90mW/°C above)** | **312.60mW** |
| Operating temperature | −40 to +125°C |
| Junction temperature | +150°C |
| Storage temperature | −60 to +165°C |
| Reflow soldering peak | +260°C |

Package thermal resistance (page 2–3, four-layer board, JESD51-7):

| Package | θJA | θJC |
|---|---|---|
| 4 WLP | 104.41°C/W | N/A |
| **5 SOT23** | **255.90°C/W** | 81°C/W |

### Key electrical characteristics

(VDD=3.6V, VEN=VDD, CIN=0.1µF‖10µF, CL=10µF, Ta=−40 to +125°C unless noted; page 4–6)

**Forward-biased:**

| Parameter | Condition | Min | Typ | Max | Units |
|---|---|---|---|---|---|
| Supply voltage | Guaranteed by VFWD@100mA | 1.2 | — | 5.5 | V |
| Supply current (fwd, enabled) IAG | No load, Ta=25°C | — | 300 | 500 | nA |
| Supply current (fwd, enabled) IAG | No load, −40 to +125°C | — | — | 1200 | nA |
| Supply current (fwd, disabled) | EN=0V, VOUT=0V, −40 to +85°C | 130 | — | 600 | nA |
| Forward voltage (WLP), IFWD=1mA | | — | 14 | 35 | mV |
| Forward voltage (WLP), IFWD=100mA | | — | 16 | 35 | mV |
| Forward voltage (WLP), IFWD=500mA | | — | 43 | 90 | mV |
| **Forward voltage (WLP), IFWD=1A** (Note 3, pulsed) | | — | **90** | **200** | mV |
| Forward voltage (SOT23), IFWD=1mA | | — | 14 | 35 | mV |
| Forward voltage (SOT23), IFWD=100mA | | — | 28 | 70 | mV |
| Forward voltage (SOT23), IFWD=500mA | | — | 100 | 200 | mV |
| **Forward voltage (SOT23), IFWD=1A** (Note 3, pulsed) | | — | **230** | **500** | mV |
| Capacitive loading | Stable for all load currents | 0.3 | — | 100 | µF |
| Thermal protection threshold | | — | 163 | — | °C |
| Thermal protection hysteresis | | — | 14 | — | °C |

Note 3: "1A pulsed current in duty cycle used for this test to make sure the device's self heating is negligible" — **the 1A forward-voltage numbers are explicitly not a continuous-current characterization**; continuous 1A self-heating will push VFWD (and dissipation) higher than these table numbers, per the device's positive temperature coefficient (page 15, "Thermal Performance and Power Dissipation" section).

**Reverse-biased (the "job" of this part):**

| Parameter | Condition | Min | Typ | Max | Units |
|---|---|---|---|---|---|
| Turn-off reverse threshold (VOUT−VDD) | | — | 26 | — | mV |
| Leakage from VDD, ICA | VOUT=4V, Ta=25°C | −50 | 10 | 50 | nA |
| Leakage from VDD, ICA | VOUT=5V, Ta=25°C | — | 15 | 100 | nA |
| Leakage from VDD, ICA | VOUT=5V, −40 to 125°C | −0.5 | — | 0.5 | µA |
| Current into OUT, IC | VOUT=4V, Ta=25°C | — | 350 | 900 | nA |
| Current into OUT, IC | VOUT=5V, −40 to 125°C | — | 700 | 2200 | nA |
| Leakage into VDD, disabled | EN=0V, VOUT=5V, Ta=25°C | −100 | 10 | 100 | nA |
| Leakage into VDD, disabled | EN=0V, VOUT=5V, −40 to 125°C | −500 | — | 500 | nA |

**Enable:**

| Parameter | Condition | Min | Typ | Max | Units |
|---|---|---|---|---|---|
| VIL | | — | — | 0.4 | V |
| VIH | | 1.25 | — | — | V |
| Enable hysteresis | | 10 | — | 350 | mV |
| Low-level input current | VEN=0V, Ta=25°C | — | 15 | 50 | nA |
| High-level input current | VEN=3.6V, Ta=25°C | — | — | 80 | nA |
| High-level input current (VEN>VDD) | VEN=5V, Ta=25°C | — | 750 | — | nA |
| High-level input current (VEN>VDD) | VEN=5V, −40 to 125°C | — | — | 1300 | nA |

**Transients/timing:** Power-up delay 450µs typ; Enable time 320µs typ (VEN=VDD to 90% forward current); Disable time 80µs typ (100mA load, EN low to <1mA output). (page 6)

**Current limit (2A):** stated only in the General Description prose ("During a short-circuit or a fast power-up, the device limits its output current to 2A," page 1) — **not present as a min/typ/max table row anywhere in the Electrical Characteristics.** Treat 2A as an unguaranteed typical figure only.

### Design equations

- **Power dissipation:** P = VFWD × IFWD (quiescent current negligible; page 15).
- **Junction temperature:** TJ = Ta + (VFWD × IFWD × θJA) — this exact form is given explicitly in the datasheet (page 15, "Thermal Performance and Power Dissipation"): *"the die temperature rise is [VFWD x IFWD x θJA] + TA."*
- **Package power-dissipation ceiling above 70°C:** Pd(Ta) = 312.6mW − [(Ta−70°C) × 3.90mW/°C] for SOT23 (page 2 abs-max, applied explicitly in the datasheet's own worked example on page 16).
- **Reverse blocking:** the internal PMOSFET switch turns off automatically once VOUT − VDD exceeds the 26mV typ turn-off threshold (page 5) — this is the entire mechanism behind "OR-ing without a diode drop," and it is what protects a tile whose local buck hasn't started yet from being back-driven by the shared bus (see Worked Values / Gotchas).
- **Parallel current sharing:** no formula given — qualitative only ("relies on the strong positive temperature coefficient of MOSFETs... by keeping the paralleled units in close thermal contact, they will inherently share the current," page 17).

### Worked values for this application

Target: ~1A continuous OR-ing current onto the shared 5V bus, from a per-tile local buck.

**SOT23 package cannot sustain 1A continuous — this is stated explicitly by the datasheet's own worked example (page 16) and independently confirmed here:**

Datasheet's own example (SOT23, IFWD reduced to 500mA "because the SOT23 package has a higher thermal resistance than the WLP"):
- VFWD (max @500mA) = 175mV → Pd = 500mA × 175mV = 87.5mW
- Package-derated ceiling at Ta=85°C: 312.6mW − [(85−70)×3.9mW/°C] = 253.5mW — comfortably clears 87.5mW.
- TJ = 85°C + (87.5mW/3.9mW/°C) = 85 + 22.4 = **107.4°C** — comfortably under the 150°C abs-max.
- The datasheet then states directly: *"for IFWD = 1A, the worst-case forward voltage increases to 500mV, yielding a power dissipation of 500mW, which is greater than the maximum limit, and would be expected to trip the thermal shutdown."*

Independent check using θJA=255.90°C/W (page 3) and the two 1A VFWD data points (typ 230mV, max 500mV, page 4):

| Case | VFWD | Pd | ΔTJ (Pd×θJA) | TJ @ Ta=25°C | TJ @ Ta=45°C |
|---|---|---|---|---|---|
| Typ, 1A | 230mV | 230mW | 58.9°C | **83.9°C** | **103.9°C** |
| Max, 1A | 500mV | 500mW | 128.0°C | **153.0°C** (exceeds 150°C abs-max TJ) | 173.0°C |

At the typical corner this looks survivable at room temperature but is already eating deeply into margin below the 163°C thermal-protection trip; at the worst-case (max VFWD) corner it exceeds the part's own 150°C absolute-maximum junction temperature at 25°C ambient before any self-heating feedback is even accounted for (VFWD rises further as the die heats, since the part is resistive above its rated forward current — page 15). **SOT23 at continuous 1A is not usable per the datasheet's own numbers.**

**WLP package handles 1A fine:** θJA=104.41°C/W (page 2), VFWD@1A = 90mV typ/200mV max (page 4).
- Typ: Pd=90mW, ΔTJ=9.4°C → TJ@25°C = 34.4°C.
- Max: Pd=200mW, ΔTJ=20.9°C → TJ@25°C = 45.9°C.
- Both comfortably under 150°C abs-max even at elevated ambient.

**This creates a direct conflict with the project's home-hotplate-reflow constraint.** WLP is a 0.77mm×0.77mm, 4-bump, 0.35mm-pitch chip-scale package (page 1) — effectively a micro-BGA with no visible solder fillet for optical inspection, which is a poor fit for hand-placed, low-temperature-paste hotplate reflow without X-ray or a very high-confidence stencil/placement process. SOT23 is the hand-assembly-friendly package but, per the numbers above, cannot sustain the ~1A target continuously.

**Datasheet-sanctioned way out — parallel two SOT23 packages** (page 17, "Higher Currents Using Paralleled Ideal Diodes," explicit typical application circuit given): "placing two or more in parallel will safely increase the current handling capability," relying on the positive tempco for current sharing, with the practical guidance to keep units in close thermal contact and to use 2oz copper on the top layer. The datasheet states "up to six units is generally practical when using the WLP versions" — it does not give a specific practical unit-count ceiling for SOT23, only implying it's lower due to higher θJA per package. Two SOT23 parts each carrying ~500mA continuous sit well within the datasheet's own 500mA worked example (TJ=107.4°C at Ta=85°C) — this is the datasheet-supported path to 1A in a hand-solderable package.

### Recommended implementation (pin by pin)

SOT-23-5 pinout (page 11):

| Pin | Name | Function/connection |
|---|---|---|
| 1 | VDD | Input from local gated-5V buck output, "Diode Anode." CIN=0.1µF‖10µF near this pin (per characterization condition, page 4). |
| 2 | GND | Ground |
| 3 | EN | Active-high, weak internal pullup. Tie to a supply that only comes up **after** VDD (the local buck output) is established — datasheet: "EN should not be turned on before VDD" (page 13) and "EN must be turned on after VDD is ready" (page 11, pin description). Can be left open only for −40 to +85°C operation; **must be tied to VDD for the full −40 to +125°C range** (page 13) — given the automotive-temp part choice, tie it, don't float it. |
| 4 | N.C. | Not internally connected (page 11) — **do not treat this as GND**; the WLP pinout has no equivalent NC ball, so double-check whichever package is chosen against its own pin table. |
| 5 | OUT | Output to the shared bootstrap bus, "Diode Cathode." CL=10µF near this pin. |

### Decoupling and passives

- CIN = 0.1µF in parallel with 10µF — this exact combination is the manufacturer's own characterization condition (page 4, table header) and matches the "Typical OR Application" figure (Figure 3, page 14) which explicitly shows a small CS at the source plus a larger CIN at VDD.
- CL = 10µF at OUT (characterization condition, page 4 and page 7 "Typical Operating Characteristics" header).
- Both fall inside the datasheet's stated stable capacitive-load range of 0.3–100µF (page 4) — headroom is generous, so exact values aren't stability-critical the way they can be on some LDOs.
- No dielectric type (X7R/X5R/COG) is stated anywhere in the document — **not specified.**
- Case size: at 5V rail voltage, 0.1µF and 10µF ceramics are both commonly available in 0402, but as with the LDO, a 10µF part at 0402 will show meaningful DC-bias capacitance derating — general MLCC knowledge, not sourced from this datasheet; verify effective capacitance at the actual 5V bias before committing to 0402 for the 10µF part.
- Source impedance note (page 15, "Loading Limitations"): a current step causes a momentary drop across the input source's own inductance/resistance (LS/RS in Figure 3) as the ideal diode turns on; "Placing CS very close to the VDD pin reduces both LS and RS," and adding more output load capacitance improves load-step response. This matters more at low VDD (<2V, explicitly called out) — less relevant at our 5V rail but the placement guidance (CS/CIN tight to VDD) still applies.

### Layout notes

- If parallel SOT23 devices are used to reach 1A (see Worked Values), the datasheet recommends: keep units in **close thermal contact** so the positive-tempco current-sharing mechanism works, and use **2oz copper on the top metal layer** to aid thermal coupling between the parallel devices (page 17). No numeric spacing is given.
- No general PCB layout/EMI guidance is otherwise provided in this datasheet beyond the CS-placement note above.

### Gotchas and failure modes

- **SOT23 at continuous 1A will very likely trip thermal shutdown** — this is the headline risk for this part in this application. See Worked Values.
- **VFWD is not flat with temperature/current at high load** — above the specified current, the part becomes resistive (page 12, Figure 1 reference; page 15) so dissipation rises with I², compounding the thermal problem at exactly the currents this OR-ing application needs.
- **Cold-start / hotplug reverse-blocking behavior is exactly what this part is designed for and is well-characterized:** when a tile's local buck hasn't started (VDD absent or low) but the shared bus is already held up by other tiles (OUT > VDD), the internal PMOSFET turns off once VOUT exceeds VDD by the 26mV typ threshold (page 5, 15), and reverse leakage back into the dead tile's VDD is tiny — 10nA typ / 100nA max at Ta=25°C, rising to 0.5µA max at 125°C (VOUT=5V case, page 5). **This directly answers the "input absent, output held up by another source" scenario in the brief: leakage is negligible (sub-µA even at the worst temperature corner), and blocking is fast relative to the 1000Hz/1ms scan requirement** (enable/disable timing is in the hundreds of microseconds, page 6, though that's EN-controlled turn-on/off, not the passive reverse-block response time — see Open Questions).
- **Not suited to rectifying AC** — explicit datasheet warning (page 12): "these ideal diodes are designed to be used to switch between different DC sources, and not for rectifying AC. In applications where an input voltage that is negative with respect to ground may be applied to the diode, conventional diodes should be used." Not a concern for DC bus OR-ing, but worth knowing if the shared bus ever sees a genuinely negative transient (ESD/inductive kick) rather than just "absent."
- **Current limit (2A) is not a guaranteed spec** — see Key Electrical Characteristics. Don't rely on it as a hard fault-current ceiling in a fault-tree analysis without margin, since it only appears as prose, not as a min/typ/max table entry.
- **EN sequencing relative to VDD matters** — "EN should not be turned on before VDD" (page 13). If EN is tied to something that can be present before the local 5V buck output ramps (e.g., tied to the always-on bootstrap rail rather than to the buck's own output or a power-good signal), this ordering requirement would be violated at every cold start. Tie EN to a node that tracks the local buck output, not to the bootstrap rail.

### Open questions / not determinable from the datasheet

- Exact reverse-recovery / turn-off **speed** (as opposed to the 26mV threshold and the leakage-current numbers) is not given as a µs/ns figure anywhere in the document — only forward-direction Enable/Disable timing (320µs/80µs) is specified, and those are EN-driven, not passive-reverse-bias-driven. If fast fault isolation on the shared bus matters for the sub-1ms scan budget, this needs bench measurement.
- No practical unit-count ceiling is given for paralleling SOT23 packages specifically (only "up to six... for WLP versions," page 17) — how many SOT23s can practically share current with acceptable thermal margin is not stated.
- No dielectric type for CIN/CL.
- Current limit (2A) has no guaranteed min/typ/max — see above.
- No explicit current-sharing mismatch tolerance (e.g., how far VFWD can differ between two parallel units before one hogs current) is quantified — only the qualitative "strong positive temperature coefficient... inherently share the current" statement (page 17).

---

Back to [research index](README.md)
