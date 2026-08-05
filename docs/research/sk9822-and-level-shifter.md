# SK9822-EC20 + SN74LVC2T45 - datasheet research
> Independent datasheet read. Not written against the existing schematic.

Sources:
- `Refrences/datasheets/SK9822-EC20-rgb.pdf` - OPSCO Optoelectronics, doc no. SK9822-EC20-000, Rev A/0, dated 2024-03-20. Bilingual Chinese/English, 14 pages. **This is the actual part used** (reverse-mount, 2.0x2.0x0.65mm PCB-holder package). All Chinese text below was translated by me; translations are marked.
- `Refrences/datasheets/SK9822-rgb-led.pdf` - OPSCO Optoelectronics, doc "SPC/SK9822", Rev 01, dated 2016-03-18. Bilingual, 12 pages. **This is a different, older, physically larger part** (5.5x5.0x1.6mm top-view SMD 5050-style package) from the same manufacturer/family. Used here only for cross-reference where the EC20 sheet is silent - every figure pulled from it is explicitly labeled "plain SK9822" below and should not be assumed to transfer to the EC20 silently.
- `Refrences/datasheets/SN74LVC2T45-level-shifter.pdf` - was missing from the repo, fetched from `https://www.ti.com/lit/ds/symlink/sn74lvc2t45.pdf` and saved at that path. TI literature number **SCES516N**, "DECEMBER 2003 - REVISED JUNE 2024".

---

## Part identity

**SK9822-EC20** (p.1, p.3 General instructions for product naming): a single-die RGB LED with an integrated constant-current driver IC, two-wire (clock + data) serial cascade, "infinite cascading capability" (p.1 Overview). Package: 2.0mm x 2.0mm x 0.65mm PCB-holder SMD, bottom-view pinout, six pads (p.4 Mechanical dimensions). Not the same physical part as the plain SK9822 (5.5x5.0x1.6mm, top-view, different pin count arrangement and different absolute-max/electrical tables - see discrepancies noted throughout).

Pinout (p.4, Section 5, Pin Function Description), bottom view:
| Pin | Symbol | Function |
|---|---|---|
| 1 | SDO | Serial data output (cascade to next chip) |
| 2 | GND | Ground / power negative |
| 3 | SDI | Serial data input (cascade from previous chip / controller) |
| 4 | CKI | Serial clock input |
| 5 | VDD | Power positive |
| 6 | CKO | Serial clock output (cascade to next chip) |

**SN74LVC2T45** (p.1, Description): "Dual-Bit Dual-Supply Bus Transceiver With Configurable Voltage Translation." Two independent non-inverting I/O channels, each channel's A-side referenced to VCCA and B-side referenced to VCCB, single shared DIR pin (referenced to VCCA) controlling both channels together. Not a buffer/gate - it is a bidirectional transceiver with direction control, no output-enable pin.

Package options (p.1, Package Information table):
| Part suffix | Package | Body size |
|---|---|---|
| DCT | SM8 (SOT-23-like, 8-pin) | 2.95mm x 4mm |
| DCU | VSSOP, 8-pin | 2mm x 3.1mm |
| YZP | DSBGA, 8-pin | 1.5mm x 0.5mm |

Pinout, DCT/DCU (Section 4, Table 4-1, p.2-3): 1 VCCA, 2 A1, 3 A2, 4 GND, 5 DIR, 6 B2, 7 B1, 8 VCCB. **A1<->B1 is one channel, A2<->B2 is the other** - the numbering does not run straight across the package.

**Package recommendation for this project's hotplate-reflow constraint:** DCT or DCU are ordinary leaded/gull-wing-pad SMD packages that stencil and hotplate-reflow fine. **YZP (DSBGA) should be avoided here** - it's a 1.5x0.5mm ball-grid part with no exposed leads to inspect optically, and DSBGA parts are far more sensitive to paste-volume/coplanarity control than a home hotplate setup with low-temp paste can reliably guarantee (this is my engineering judgment, not a datasheet statement - TI's datasheet does not comment on hand/hotplate assembly suitability at all).

---

## Absolute maximum ratings that constrain this design

### SK9822-EC20 (Section 7, p.5, Ta=25C)

| Parameter | Symbol | Range | Unit |
|---|---|---|---|
| Working (logic) voltage | VDD | -0.3 ~ VDD+0.3 | V |
| Operating temperature | Topt | -40 ~ +85 | C |
| Storage temperature | Tstg | -40 ~ +85 | C |
| ESD (human body model) | VESD | 2000 | V |

**The VDD abs-max range as printed ("-0.3~VDD+0.3") is self-referential/nonsensical** - it defines VDD's limit in terms of VDD. This reads as a copy-paste artifact from a generic template (a level-shifter or logic datasheet where "VDD+0.3" is a *different* pin's rating relative to the supply) that wasn't fixed for this LED IC. I cannot recover an intended number from it. Use the Electrical Characteristics table instead (Section 9, p.6): VDD min not given, typical 5V, max 5.3V - treat 5.3V as the practical ceiling and flag the abs-max table entry as unusable as printed.

Cross-reference, plain SK9822 (Section 7, p.3, Ta=25C) - **different part, do not mix into EC20 design math**:
| Parameter | Symbol | Range | Unit |
|---|---|---|---|
| Power supply voltage | VDD | -0.5 ~ +5.5 | V |
| Logic input voltage | VIN | -0.3 ~ VDD+0.3 | V |
| Operating temperature | Topt | -20 ~ +80 | C |
| Storage temperature | Tstg | -50 ~ +120 | C |
| ESD | VESD | 4000 | V |

Note the plain part is rated to a wider Tstg and a higher ESD (4kV vs the EC20's 2kV) - **the EC20's ESD budget is the tighter of the two and the one that actually applies.** With only 2kV HBM on the LED chain and it sitting directly under user-touched keycaps (hot-pluggable tiles, exposed connectors), ESD protection at the tile edge connectors is doing real work here, not just belt-and-suspenders.

### SN74LVC2T45 (Section 5.1, Table, p.4)

| Parameter | Symbol | Min | Max | Unit |
|---|---|---|---|---|
| Supply voltage (VCCA, VCCB) | - | -0.5 | 6.5 | V |
| Input voltage | VI | -0.5 | 6.5 | V |
| Output voltage, Hi-Z/power-off state | VO | -0.5 | 6.5 | V |
| Output voltage, driven state, A port | VO | -0.5 | VCCA+0.5 | V |
| Output voltage, driven state, B port | VO | -0.5 | VCCB+0.5 | V |
| Input clamp current, VI<0 | IIK | -50 | - | mA |
| Output clamp current, VO<0 | IOK | -50 | - | mA |
| Continuous output current | IO | -50 | 50 | mA |
| Continuous current through VCC or GND | - | -100 | 100 | mA |
| Junction temperature | TJ | - | 150 | C |
| Storage temperature | Tstg | -65 | 150 | C |

ESD (Section 5.2, p.4): HBM +-4000V (JS-001), CDM +-1000V (JS-002).

3V3-always-on / gated-5V-switched sit at 3.3V and 5V respectively, both comfortably inside the -0.5 to 6.5V window with wide margin - abs-max is not a binding constraint here.

---

## Key electrical characteristics

### SK9822-EC20 (Section 9, p.6, TA=25C unless noted)

| Parameter | Symbol | Min | Typ | Max | Unit | Condition |
|---|---|---|---|---|---|---|
| Chip supply voltage | VDD | - | 5 | 5.3 | V | - |
| Signal input flip threshold, high | VIH | 3.4 | - | 5.3 | V | - |
| Signal input flip threshold, low | VIL | -0.3 | - | 1.6 | V | - |
| R/B/G output drive current | IDOUT | 16 | - | 21 | mA | VDS=1V |
| PWM frequency | FPWM | - | 1.2 | - | kHz | - |
| Static power consumption | IDD | - | 1 | - | mA | - |

**VIH min = 3.4V is the headline number for the 3.3V-driver question.** A 3.3V push-pull CMOS output (RP2350B GPIO, or a 3.3V SPI peripheral) driven directly at the LED's SDI/CKI pins tops out at roughly VDD_MCU (3.3V, maybe a little less under load) - **that is below the LED's own 3.4V VIH minimum**, i.e. a "high" from a bare 3.3V driver is not guaranteed to register as a logic high on the SK9822-EC20. This is a hard requirement for a level shifter between the MCU and the LED chain, not an optional nicety - the datasheet's own numbers rule out direct 3.3V drive.

Timing parameters (clock high/low width, data setup time) **are not given anywhere in the EC20 electrical characteristics table** - Section 9 lists only the five rows above. Cross-reference, plain SK9822 (Section 8, p.4, TA=-20~+70C, VDD=4.5~5.5V) - **different part, use only as an order-of-magnitude proxy, not an EC20 spec**:

| Parameter | Symbol | Min | Max | Unit |
|---|---|---|---|---|
| Clock high level width | TCLKH | - | >30 | ns |
| Clock low level width | TCLKL | - | >30 | ns |
| Data setup time | TSETUP | - | >10 | ns |
| R/G/B output pressure | VDS,MAX | - | 17 | V |
| Max LED output current | Imax | - | 20 | mA |

Maximum serial clock frequency: **EC20 states 15MHz** ("最大串行输入数据频率15MHZ" / "Maximum serial input data frequency 15MHz", p.1 Overview). The plain SK9822 states a different, higher figure - "The maximum frequency of 30MHZ serial data input" (p.1 Section 3 Features/Description) - **these are two different dies and the numbers should not be conflated; 15MHz is the number that governs this design.** An RP2350B hardware SPI clock driving this chain should be configured at or below 15MHz.

### SN74LVC2T45 (Section 5.5, p.5-6, TA=25C unless noted; Section 5.3 Recommended Operating Conditions, p.4-5)

Thresholds are tiered by VCCI (the supply on the *input* side of a given port) per Section 5.3:

| VCCI range | VIH min | VIL max |
|---|---|---|
| 1.65-1.95V | VCCI x 0.65 | VCCI x 0.35 |
| 2.3-2.7V | 1.7V | 0.7V |
| 3.0-3.6V | 2.0V | 0.8V |
| 4.5-5.5V | VCCI x 0.7 | VCCI x 0.3 |

At VCCA=3.3V (our MCU-side rail, "3V to 3.6V" row): VIH min = 2.0V, VIL max = 0.8V. RP2350B 3.3V CMOS GPIO output swings full rail-to-rail, so it drives this comfortably.

Output drive (Section 5.3, IOH/IOL rows): at 3.0-3.6V, +-24mA; at 4.5-5.5V, +-32mA. Matches the "+-24-mA output drive at 3.3V" feature bullet (p.1).

Electrical Characteristics table (Section 5.5, p.5-6):

| Parameter | Condition | Min | Typ | Max (-40 to 85C) | Unit |
|---|---|---|---|---|---|
| VOH | IOH=-100uA, VCC 1.65-4.5V | VCCO-0.1 | - | - | V |
| VOL | IOL=100uA, VCC 1.65-4.5V | - | - | 0.1 | V |
| II (DIR input leakage) | VI=VCCA or GND | - | - | +-2 | uA |
| **Ioff, A port** | VCCA=0V, VI/VO on B port 0-5.5V | - | - | **+-2** | **uA** |
| **Ioff, B port** | VCCB=0V, VI/VO on A port 0-5.5V | - | - | **+-2** | **uA** |
| IOZ (either port, Hi-Z) | VO=VCCO or GND | - | - | +-2 | uA |
| ICCA, ICCB (static, powered) | VI=VCCI or GND, IO=0 | - | - | 3-4 | uA |
| Cio (I/O pin capacitance) | VO=VCCA/B or GND, 3.3V | - | 6 | - | pF |
| CI (DIR pin capacitance) | 3.3V | - | 2.5 | - | pF |

**The Ioff row is the number that answers the headline question of this document - see below.**

Propagation delay at our actual operating point, VCCA=3.3V+-0.3V, VCCB=5V+-0.5V (Section 5.8, "Switching Characteristics: VCCA=3.3V+-0.3V", p.8):

| Path | tPLH (min/max) | tPHL (min/max) | Unit |
|---|---|---|---|
| A -> B | 0.7 / 4.4 | 0.7 / 4.0 | ns |
| B -> A | 0.6 / 5.4 | 0.7 / 4.5 | ns |

Both well under a nanosecond-to-single-digit-ns scale, negligible against a 15MHz (66.7ns period) SPI clock.

---

## Protocol / timing (SK9822 section only)

All of this is from the **EC20 datasheet, Section 10, Function Description, p.7-9** unless marked as plain-SK9822 cross-reference. The plain SK9822's equivalent Section 9 "(1) Series data structure" heading exists (p.4) but the frame-structure diagram under it did not extract as text (it's an embedded image with no OCR layer) - so the frame details below come solely from the EC20 sheet, which is fortunately the actual part in use.

**Frame structure** (Section 10(1), p.7):

```
Start frame  |  Data frame (LED 1)  |  Data frame (LED 2)  | ... |  Data frame (LED N)  |  End frame
  0x00000000 |  111 + 5-bit + 24-bit RBG data              |     |                       |  0xFFFFFFFF
   (32 bits) |          (32 bits per LED)                                                |  (32 bits, fixed)
```

- **Start frame:** 32 bits of `0000 0000` (4 bytes of 0x00).
- **Per-LED data frame**, 32 bits total, MSB-first on each field:
  - 3-bit fixed header `111`
  - 5-bit global brightness/current-gain field
  - 8-bit "red" data
  - 8-bit "blue" data
  - 8-bit "green" data
- **End frame:** 32 bits of `1111 1111` (4 bytes of 0xFF), fixed length regardless of chain length as printed in the table.

**Bit-order caveat / datasheet self-contradiction:** the per-LED frame table (p.7) labels the three 8-bit color fields, in bitstream order, as red / blue / green, and the same page (line under the frame table) says "产品输出结构：RBG顺序点亮" ("product output structure: RBG sequential lighting"). But the propagation-behavior section two pages later (Section 10(4), p.8) says "产品输出结构：GRB顺序点亮" ("product output structure: GRB sequential lighting"), describing what looks like the same thing. **These two statements contradict each other within the same datasheet revision.** I cannot resolve from the text which one is authoritative, or whether one of them is actually describing the physical R/G/B die stacking order inside the package (for color-mixing uniformity) rather than the SPI bitstream field order - the frame table's field order (red, blue, green) is the one concrete, structurally-placed fact and is what I'd trust for firmware bit-packing, but this should be verified against a physical LED before shipping firmware. Flagged in Open Questions.

**Global brightness field:** 5 bits, giving 32 current-gain levels, applied uniformly to all three (R/G/B) output currents simultaneously (Section 10(5), p.9 heading: "5-Bit(32-level) brightness adjustment (simultaneously controlling the current of the three ports OUTR/OUTB/OUTG)"). This is a *current-level* select, separate from the 8-bit-per-channel PWM duty cycle - the two controls are orthogonal (PWM sets average brightness within a fixed current level; the 5-bit field sets what that current level actually is in mA).

**End-frame length for a 30-LED chain:** the datasheet states a fixed 32-bit (0xFFFFFFFF) end frame with no formula tying it to chain length N - it's presented as a constant, not derived. Separately, Section 10(4) (p.8) states the propagation design intent: "CKO比CKI减少半个Clock" / "design a unified CKO that reduces CKI by half a Clock" - i.e. **each chip deliberately delays its clock output by half a clock cycle relative to its clock input**, specifically so that no two chips in the chain latch/shift on the exact same edge (the datasheet explains this was needed because a fully-synchronous CKO would cause every chip to read and write simultaneously on the same edge, which it calls "an extremely unstable situation" that causes garbled transfer). **Combining that stated half-clock-per-chip delay with the well-known SK9822/APA102-family clocking model** (my inference, not a direct datasheet derivation): propagating a bit through N chips costs on the order of N/2 clock edges end-to-end, so an end frame needs at least ~N/2 extra clock edges after the last data frame to fully shift/latch the last chips' data. For N=30, that's roughly 15 bits minimum. The datasheet's fixed 32-bit end frame comfortably covers this (32 > 15, margin for ~64 LEDs before the fixed frame would become marginal) - **this is my derived reasoning connecting two facts in the datasheet, not a number the datasheet states outright as a formula.** For a design with more than one tile daisy-chained on a single SPI bus (30, 60, 90... LEDs), this margin should be re-checked; at 30 LEDs (one tile) the fixed 32-bit end frame is not a concern.

**Refresh rate** (Section 10(2), p.7): `frame rate = 1 / ((64 + 32*N) * CKI_period)`, where N = number of LED points. Worked for N=30, CKI=15MHz (66.7ns period): `(64 + 32*30) = 1024` clock cycles per full-chain refresh; `1024 * 66.7ns = 68.3us`; frame rate = 1/68.3us ~= **14.6kHz** max theoretical full-chain update rate at the datasheet's stated max clock. Far above the sub-1ms (1000Hz) key-scan requirement, so SPI-bus time for LED refresh is not going to compete meaningfully with scan timing at this clock.

**256-level grayscale / PWM** (Section 10(3), p.7-8, and Electrical Characteristics FPWM row, p.6): 8-bit (256-level) PWM per channel, duty = value/256. Internal PWM frequency FPWM = **1.2kHz typical** (Section 9, p.6) - this figure is identical between the EC20 and plain SK9822 sheets. 1.2kHz is far above human flicker-fusion threshold (~60-90Hz) so **no perceptible flicker to the naked eye**. It is, however, low by modern addressable-LED standards (many parts run 2-20+kHz internal PWM specifically to be camera-safe) - **1.2kHz is squarely in the range that can produce visible banding/rolling-shutter artifacts in recorded video or under a phone camera**, especially at partial duty cycles and fast shutter speeds. Worth calling out as a real limitation for anyone streaming/filming the keyboard, not a defect, just a spec to be aware of - not something firmware can fix since it's the LED IC's internal oscillator.

**SDI/CKI/SDO/CKO relationship** (Section 10(4), p.8, direct translation):
- "SDI jumps on the falling edge of CKI, and reads the current chip on the rising edge of CKI."
- "SDO can only be output after SDI is read in, and SDI is read in on the rising edge of CKI, so SDO is output on the rising edge of CKI."
- CKO is deliberately staggered from CKI by half a clock cycle (see end-frame discussion above), by design, to avoid every chip in the chain shifting on the same edge.

This is **CPOL=0/data-changes-on-falling-edge, sampled-on-rising-edge** behavior, i.e. standard SPI Mode 0 from the controller's point of view.

---

## Design equations

**Total LED current, N LEDs, all channels at full duty (worst-case instantaneous = worst-case average at 100% duty):**

`I_total = N x 3 x I_channel`

where `I_channel` is set by the 5-bit global brightness field (Section 10(5) table, p.9 - reproduced below for the values used).

**Bulk capacitance sizing** (general design equation, not a datasheet-given target - see "not specified" note below):

`C_bulk >= (I_step x t_response) / dV_allowed`

where `I_step` is the worst-case current step the rail must absorb (e.g. all 30 LEDs snapping from off to full brightness in one frame), `t_response` is the regulator's loop response time, and `dV_allowed` is the tolerable droop on gated-5V before the SK9822's VIH margin (relative to the level shifter's VOH) is put at risk. Neither datasheet gives `I_step`, `t_response`, or a target `dV_allowed`, so this is presented as a formula only - see Open Questions.

**Series-resistor value** (from EC20 datasheet's own stated range, Section 11, p.10): the datasheet gives a *range* (20 to 2000 ohm) and a *typical* (~500 ohm) directly, not a formula - see Worked Values below for the E-series rounding of that number.

---

## Worked values for this application

### LED chain current, 30 LEDs

Per-channel current at the datasheet's stated regulation levels (Section 10(5) table, p.9, reproduced in relevant part):

| Level | 5-bit code | Fraction | Current (mA) |
|---|---|---|---|
| 1 | 00000 | 0/31 | 0 |
| 10 | 01001 | 9/31 | 5.229 |
| 32 (full scale) | 11111 | 31/31 | 18.000 |

The same section's notes (p.9, right-hand margin annotations, translated) state explicitly:
- Around level 5-6: "Suggested use of current: 1-10 current regulation level."
- Around level 18-19: **"Based on the heat dissipation of the product, it is recommended to use a maximum current of 0-5mA for adjustment. The current adjustment level of 11-32 is not recommended."**

This is a real, quoted thermal derating recommendation specific to this small (2x2x0.65mm) package - **it is not just a suggestion, it's the datasheet's own ceiling for sustained operation.**

Worked totals for 30 LEDs, full white (R=G=B=255, 100% duty, all three channels on simultaneously):

| Scenario | Per-channel current | Per-LED (x3 ch) | 30 LEDs (x3 ch x 30) |
|---|---|---|---|
| Datasheet-recommended ceiling (level 10, per note above) | 5.229mA (table value, level 10) | 15.687mA | **470.6mA** |
| Electrical-characteristics absolute max (IDOUT max, Section 9) | 21mA | 63mA | **1890mA (1.89A)** |

Add static logic current: IDD typ 1mA/chip x 30 = 30mA (Section 9, p.6). So:
- Recommended operating ceiling, whole chain: ~470.6 + 30 = **~501mA**
- Electrical abs-max ceiling (not recommended per the IC's own thermal note, but electrically the pins can source it): ~1890 + 30 = **~1.92A**

**Implication for rail sizing:** firmware that limits the 5-bit global brightness field to <=10 (per the datasheet's own thermal guidance) keeps the whole 30-LED chain under ~500mA on gated-5V. If firmware (or a bug) ever pushes the brightness field into the "not recommended" 11-32 range, worst-case draw on gated-5V nearly quadruples to ~1.9A - this is a firmware-enforceable ceiling, and given the project's existing PD-budget-driven brightness capping, the 5-bit brightness field itself (not just PWM duty) should be clamped in code to <=10, independent of whatever the PD power budget otherwise allows, because this is a package thermal limit, not a power-source limit.

### Series resistor (R1/R2 on SDI/CKI, per EC20 Section 11, p.10)

Datasheet text (translated): "The signal input and output terminals of the product must be connected in series with protective resistors R1/R2 ... generally recommended to take a value between 20-2000 ohm, and it is usually recommended to take a value of around 500 ohm." No formula tying the value to chain length N=30 is given beyond "the more cascaded, the smaller R1/R2" (qualitative only).

Derived component value, using the 500 ohm figure the datasheet states directly:

| Ideal | Nearest E24 | Actual | Error |
|---|---|---|---|
| 500 ohm | 510 ohm | 510 ohm | +2.0% |

(470 ohm, the other E24 neighbor, is -6.0% off - 510 ohm is the closer standard value.)

### Level-shifter decoupling (TI's own numbers, Section 8.3.1, p.19)

"Each VCC pin must have a good bypass capacitor... If there are multiple VCC pins, 0.01uF or 0.022uF is recommended for each power pin... 0.1uF and 1uF capacitors are commonly used in parallel."

This part has two VCC pins (VCCA, VCCB) so the "multiple VCC pins" guidance applies - 0.01-0.022uF close bypass per pin, per TI directly.

| Ideal | Nearest E12 | Actual | Error |
|---|---|---|---|
| 0.022uF | 22nF (standard E12 value) | 22nF | 0% |
| 0.1uF (parallel bulk, if used) | 100nF (standard value) | 100nF | 0% |

Package for both: 0402 is appropriate (small bypass caps, short lead length matters more than case size here).

---

## Recommended implementation (pin by pin)

### SN74LVC2T45 (DCU/VSSOP-8 recommended over YZP/DSBGA for hotplate assembly - see Part Identity)

| Pin | Signal | Connection |
|---|---|---|
| 1 VCCA | 3.3V, always-on | 3V3 rail. Bypass 0.01-0.022uF close to pin (TI Section 8.3.1). |
| 2 A1 | MCU SPI clock in (3.3V) | RP2350B hardware SPI SCK, driven push-pull, never left floating (see Gotchas). |
| 3 A2 | MCU SPI data in (3.3V) | RP2350B hardware SPI MOSI, same driven-not-floating requirement. |
| 4 GND | Ground | Common GND. Per TI Section 8.3, "Always apply a ground reference to the GND pins first" during power-up sequencing planning. |
| 5 DIR | Direction control, referenced to VCCA | **Tie hard to VCCA (3V3).** DIR=H means "A data to B bus" (Table 7-1, p.15) - since this design is unidirectional MCU->LED, a permanent DIR=H is correct, and because DIR is referenced to the always-on VCCA rail, this tie is glitch-free and stable across gated-5V power cycling (Section 7.3.5, "Glitch-Free Power Supply Sequencing", p.14). |
| 6 B2 | LED-side data out (5V) | Through series R (see below) to first SK9822-EC20 SDI. Pairs with A2 (same "bit 2" channel). |
| 7 B1 | LED-side clock out (5V) | Through series R to first SK9822-EC20 CKI. Pairs with A1 (same "bit 1" channel). |
| 8 VCCB | gated-5V, switched | gated-5V rail (same rail the LEDs run from). Bypass 0.01-0.022uF close to pin. |

No output-enable pin exists on this part (Section 8.2.2, p.17-18, states this explicitly: "Because the SN74LVC2T45 does not have an output-enable (OE) pin..."). In this design that's fine - the desired "outputs off" state is achieved for free whenever gated-5V is at 0V, via the VCC-isolation behavior (see next section), with no need for an explicit OE signal from firmware.

### SK9822-EC20 chain

- VDD -> gated-5V (matches the level shifter's VCCB, so translated VOH tracks the LED's own supply and VIH margin stays consistent chip-to-chip down the chain).
- GND -> common GND.
- SDI/CKI on the first chip -> through the series resistors (510 ohm, from the B-port of the level shifter).
- SDO/CKO -> daisy-chain to next chip's SDI/CKI, chip to chip, no additional resistor per the datasheet's application circuit (Section 11, p.10) - the series R is shown once, between controller and the first chip, not repeated at every inter-chip junction in the printed diagram.

---

## Decoupling and passives

**SK9822-EC20:** the datasheet is explicit that per-LED decoupling should not be omitted ("It is generally not recommended to omit the decoupling capacitance at both ends of the product", Section 11, p.10) but **gives no capacitance value** - "the value" is not specified anywhere in either EC20 or plain SK9822 sheet. Common industry practice for SK9822/APA102-family chains is a 100nF ceramic per LED plus a larger bulk cap every several LEDs, but **that number is my general engineering knowledge, not a datasheet figure - flagging per the rules of this document, do not treat 100nF as sourced from these datasheets.**

**Bulk capacitance for the chain:** no value given in either LED datasheet (see Design Equations above for the sizing formula with no populated targets). Not specified.

**Level shifter bypass:** 0.01-0.022uF per VCC pin, TI Section 8.3.1 (quoted above), optionally paralleled with 0.1uF/1uF bulk per TI's own text. 0402 is appropriate for these.

**Series resistors (CLK, DATA):** 510 ohm (E24, from the datasheet's stated ~500 ohm typical), one pair between the level shifter's B-port and the first LED in the chain. 0402 is appropriate size-wise for a 510 ohm 0.1W-class resistor at these current levels (only signal current, not LED supply current, flows through them).

**Where 0402 is wrong:** any bulk/reservoir capacitance for the LED chain's 5V supply (not sized here, but bulk electrolytic/polymer/large-MLCC values needed to buffer ~0.5-1.9A step loads will not be 0402 - expect 0805/1206 MLCC at minimum, or a leaded/SMD electrolytic, depending on the final capacitance value chosen). This is a placeholder flag since the actual uF value is not determinable from these two datasheets.

---

## Layout notes

**SK9822-EC20 chain, snaking across a 5x6 grid (from EC20 Section 11 app circuit, p.10, plus general clocked-serial-bus practice):**
- Route CKI/CKO and SDI/SDO as a matched pair - similar length, similar via count, physically adjacent - all the way down the snake. The datasheet's own explanation of *why* CKO is deliberately delayed half a clock from CKI (Section 10(4), p.8) is about chip-to-chip shift-register stability, not board-level skew, but it implies the design has essentially zero slack for additional skew being added by the PCB: at 15MHz (66.7ns period) with the plain-SK9822 cross-referenced setup time of >10ns (not confirmed for EC20, but the only number available), skew between CLK and DATA arrival at a given chip should stay a small fraction of the clock period. If clock and data get routed apart (different layers, one taking a via detour the other doesn't, one snaking around a Hall sensor mux trace the other doesn't), the accumulated skew down a 30-chip chain risks eating into that already-tight margin. Keep them together as a pair; treat any layer change as something that happens to both signals together, not independently.
- The level shifter's B-port drives with **strong output current (+-32mA at 5V, Section 5.3)** into fast edges (sub-5ns typ at this operating point, Section 5.8) - TI's own text (Section 7.3.4, "Balanced High-Drive CMOS Push-Pull Outputs", p.14) warns "impedance matching and load conditions should be considered to prevent ringing" for exactly this combination of high drive + light load. **The SK9822's own recommended series resistor (500 ohm typical, Section 11) is doing double duty here** - it's specified by OPSCO as ESD/hot-plug protection, but it also functions as a de facto slew-rate/edge-rate limiter for the level shifter's fast, strong output driving a short, lightly-loaded trace. This is my synthesis connecting the two datasheets, not a stated fact in either one, but it means there's no separate termination network needed beyond that resistor - don't double up on damping.
- Bypass caps for the level shifter go right at pins 1 (VCCA) and 8 (VCCB) per TI's layout example (Figure 8-3, Section 8.4.2, p.20), which explicitly shows one bypass cap per VCC pin with vias to the respective power plane, placed as close to the pin as possible.

---

## Gotchas and failure modes

### The headline issue: MCU alive (3V3 always-on) while gated-5V is off

This is exactly the scenario in the project brief: the RP2350B and the level shifter's A-side (VCCA=3V3) stay powered continuously, while gated-5V (the level shifter's VCCB and the entire LED chain's VDD) is deliberately dropped to 0V whenever firmware decides there's no power budget for LEDs, or before PD negotiation completes.

**What the datasheet says happens, quoted directly:**

- Section 1, Features, p.1: **"VCC isolation feature - if either VCC input is at GND, both ports are in the high-impedance state."**
- Section 7.3.6, "Vcc Isolation", p.15: "The I/Os of both ports will enter a high-impedance state when either of the supplies are at GND, while the other supply is still connected to the device. The maximum leakage into or out of any input or output pin on the device is specified by Ioff in the Electrical Characteristics."
- Section 7.3.3, "Ioff Supports Partial-Power-Down Mode Operation", p.14: "Ioff will prevent backflow current by disabling I/O output circuits when the device is in Partial-Power-Down mode. The inputs and outputs for this device enter a high-impedance state when the device is powered down, inhibiting current backflow into the device."
- Section 5.5, Electrical Characteristics, p.5-6: Ioff, A port (VCCA=0V, VI/VO on B port swept 0-5.5V) and Ioff, B port (VCCB=0V, VI/VO on A port swept 0-5.5V) are both spec'd at **max +-2uA** across -40 to 85C.

**Answer to "what should it be powered from, and can current flow backwards into the dead rail":** VCCA should be the always-on 3V3 rail (matches the MCU's own logic level, and DIR - which must stay valid at all times per Section 8.1's "should not have any floating I/Os when changing translation direction" - is referenced to VCCA so it stays well-defined across every gated-5V power cycle). VCCB should be gated-5V, matching the LED VDD exactly. When gated-5V drops to 0V: both ports of the shifter go high-impedance (quoted above), and any leakage current into or out of the dead B-port pins - the mechanism by which "something alive could feed something that's supposed to be off" - is bounded by the datasheet to **+-2uA max**. That is not enough current to do anything meaningful to a rail whose LEDs draw hundreds of mA when actually on; it will not phantom-power the LED chain, and it will not stress the shifter. **The SN74LVC2T45 is specifically designed for this exact partial-power-down topology - this is the textbook case the Ioff spec exists for**, and choosing this part (over a plain buffer/gate with no Ioff spec) is the right call for a switched-rail-fed-from-always-on-logic architecture.

**A caveat the datasheet does flag, worth carrying into firmware:** Section 5.3 footnote (p.4-5) and the general input-circuit description (p.1, Description) both state that "the input circuitry on both A and B ports are always active and must have a logic HIGH or LOW level applied to prevent excess ICC and ICCZ" - i.e. **the A-port (MCU-side) inputs must never be left floating**, even while gated-5V is off and the B-port is in its isolated Hi-Z state. If firmware ever tri-states the SPI SCK/MOSI GPIOs (e.g. during a peripheral reconfiguration, sleep mode, or before SPI is initialized at boot) while VCCA is powered, the A-port inputs can sit in an undefined intermediate voltage and drive excess quiescent current through the CMOS input stage. This has nothing to do with the gated-5V state - it's purely an A-side (always-on rail) concern, and worth explicitly keeping SCK/MOSI driven (or pulled to a rail) at all times the MCU is powered, not just when the LEDs are meant to be lit.

**A related but distinct failure mode not covered by this datasheet at all:** the level shifter itself is proven not to back-feed the dead rail (Ioff, <=2uA), but the *SK9822 chips themselves* have their own input ESD/clamp structure on SDI/CKI, and neither SK9822 datasheet describes that clamp's behavior with VDD unpowered. If the level shifter's B-port output pins toggle at all while gated-5V is at 0V (they shouldn't, per Vcc isolation, but this is worth stating as a boundary condition rather than assumed away) any current into the LED's own SDI/CKI clamp diodes would flow through the LED IC's internal structure, not through the shifter, and is outside what either datasheet documents. Given the shifter's own leakage is bounded to a few uA, this is very unlikely to be practically significant, but it is a genuinely open question rather than something the datasheets answer - flagged below.

### Other gotchas

- **15MHz clock ceiling is EC20-specific and lower than you'd guess from the plain SK9822's 30MHz figure or the level shifter's 420Mbps capability.** The binding constraint on SPI clock configuration is the LED IC, not the level shifter or the RP2350B.
- **The 5-bit brightness field has its own thermal ceiling (levels 11-32 "not recommended," per the EC20 datasheet's own annotation) that is separate from, and tighter than, whatever the PD power budget otherwise allows.** A firmware brightness-limiting scheme built only around the negotiated PD wattage could still command a brightness level the package itself isn't rated to sustain. Both limits need to be enforced.
- **VIH min (3.4V) makes direct 3.3V drive of the LED chain a real (not theoretical) violation** - any point in the design where a 3.3V GPIO might bypass the level shifter (test points, a debug header, a bring-up shortcut) would be out of spec against the EC20's own stated input threshold.
- **1.2kHz internal PWM is fine for the eye, not necessarily fine for a camera.** Not a bug, but worth documenting so nobody spends time debugging "flicker" that shows up only on video.
- **DSBGA (YZP) package is a poor fit for a home hotplate/low-temp-paste assembly process** - flagged in Part Identity, repeated here as a concrete gotcha since it's an easy part-number trap (DCT/DCU/YZP share the same base part number on distributor listings).

---

## Open questions / not determinable from the datasheet

- **RBG vs GRB channel order** - the EC20 datasheet contains two contradictory statements about output/color-mixing order ("RBG" on p.7, "GRB" on p.8) within the same document. Not resolvable from the text; needs physical verification against a lit LED before finalizing firmware bit-packing (though the bitstream field order in the per-LED frame table - red, blue, green - is the more structurally concrete of the two claims).
- **Bulk capacitance value for the LED chain's gated-5V feed** - no target given in either LED datasheet; only the design equation (current step / response time / allowed droop) is available, with no populated inputs.
- **Per-LED decoupling capacitance value** - datasheet says not to omit it, never gives a number.
- **SK9822-EC20 input pin capacitance** - not stated; relevant to any trace-loading/ringing calculation on the CLK/DATA lines, only the level shifter's own Cio (6pF typ) is documented, and that's the shifter's pin, not the LED's.
- **SK9822-EC20 timing parameters (clock high/low width, data setup time)** - genuinely absent from the EC20 sheet; the plain-SK9822 cross-reference numbers (TCLKH/TCLKL >30ns, TSETUP >10ns) are the only available proxy and may not hold for the EC20's different die.
- **A validated reflow profile for the actual EC20 part** - see below, this is significant enough to break out on its own.
- **Level-shifter channel-to-channel (bit-to-bit) skew** - no dedicated matched-pair skew spec is published; only the per-channel min/max propagation-delay window (Section 5.8) is available, and that window reflects process/voltage/temperature corner spread across different units/conditions, not a same-device same-conditions skew figure.
- **Whether SK9822's internal ESD/input clamp structure could source any current into an unpowered VDD net if its data/clock inputs are toggled while dead** - not documented in either SK9822 sheet; the level shifter's own Ioff bound (<=2uA) makes this unlikely to matter in practice, but it isn't a claim either datasheet actually makes.

### Reflow profile and low-temperature bismuth paste compatibility

**The EC20 datasheet (the actual part) does not contain a reflow oven profile at all.** Its only thermal-stress figure is a reliability test (Section 14, Table row 1, p.13): **"Resistance to Soldering Heat: Tsld = 260C, 10 sec, 2 times"**, referenced to JEITA ED-4701 300 301 - this is a solder-heat-resistance survival test (a fixed high-temperature dwell), not a ramp/soak/peak oven profile with preheat rates.

**The plain SK9822 (cross-reference, different part) does contain a full profile** (Section 3.4, "Reflow Soldering Characteristics", p.10/12), stated as JEDEC J-STD-020C compliant:

| Profile feature | Lead-based | Lead-free |
|---|---|---|
| Average ramp-up rate (Ts max to Tp) | 3C/s max | 3C/s max |
| Preheat temp min (Ts min) | 100C | 150C |
| Preheat temp max (Ts max) | 150C | 200C |
| Preheat time (ts min to ts max) | 60-120s | 60-180s |
| Time maintained above TL | 183C | 217C |
| Time above TL (tL) | 60-150s | 60-150s |
| **Peak/classification temperature (Tp)** | **215C** | **240C** |
| Time within 5C of peak (tp) | <10s | <10s |
| Ramp-down rate | 6C/s max | 6C/s max |
| Time 25C to peak | <6 min max | <6 min max |

**Is ~160C peak with Sn42/Bi57/Ag1 (~138C melt) compatible?** On the numbers actually published: yes with large margin, but with an important caveat about what that margin is actually measuring.

- Against the EC20's own rated solder-heat-resistance test (260C, 10s): 160C is 100C below that survival threshold.
- Against the plain SK9822's cross-referenced peak classification temperatures (215C leaded / 240C lead-free): 160C is 55-80C below.

So on pure peak-temperature headroom, ~160C should not stress either part anywhere near its documented thermal-damage limits - there's no indication in either datasheet that a lower peak temperature than what they were characterized against would be a problem (lower peak is, if anything, gentler than what they're rated to survive).

**The caveat:** the plain SK9822's published profile is built around the liquidus temperatures of standard alloys (183C for eutectic Sn63Pb37, 217C for SAC-family lead-free) - the "time maintained above TL" and "peak temperature" figures are calibrated to *those* alloys' melting behavior, not to a Bi/Sn/Ag low-temperature alloy with a ~138C melt point. A Sn42/Bi57/Ag1 profile properly needs its own TL/soak/peak targets built around its own ~138C liquidus, and **neither LED datasheet publishes or validates a profile for that alloy family.** So the honest conclusion is: **the peak-temperature margin is comfortable and nothing in either datasheet suggests 160C would cause thermal damage, but no datasheet here explicitly blesses a low-temperature bismuth-alloy profile** - this is inferred from margin against unrelated-alloy profiles, not datasheet-validated for the paste actually being used. Flagging as open rather than asserting compatibility as a confirmed datasheet fact.
