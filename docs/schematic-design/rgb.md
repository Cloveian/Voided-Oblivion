# RGB - schematic-design calcs

SK9822-EC20 chain math. Parts from [chips](../chips.md); decision from [rgb design-choice](../design-choices/rgb.md).

Per-section skeleton: **Goal → Datasheet refs → Math → Result → Notes/gotchas.**

## Contents
- [SK9822-EC20 chain](#sk9822-ec20-chain)
- [SPI drive - SCK/DATA series & level shift](#spi-drive---sckdata-series--level-shift)
- [Picking the level shifter](#picking-the-level-shifter)
- [Rail current budget & caps](#rail-current-budget--caps)

---

## SK9822-EC20 chain
### Goal
30 reverse-mount LEDs/tile on gated-5V, daisy-chained, driven from hardware SPI0 (SCK GPIO34, TX GPIO35).

### Datasheet refs
SK9822-EC20, OPSCO. **Max serial input clock 15MHz** (p.1). VDD 5–5.3V. VIH min 3.4V / VIL max 1.6V (§9). PWM 1.2kHz. IDD static 1mA.

> **Do not use the plain SK9822's 30MHz figure.** That's a different die. The EC20 is the part on this board and its number is **15MHz**. Cap SPI0 at or below that.

### Math - protocol
```
start frame :  32 bits of 0x00
per LED     :  32 bits = 111 + 5-bit global brightness + 24-bit colour
end frame   :  32 bits of 0xFF
```
Refresh rate, from the datasheet's own formula `1 / ((64 + 32N) x T_CKI)`:
```
N = 30, CKI = 15 MHz (66.7 ns)
(64 + 32x30) = 1024 clocks   ->  1024 x 66.7ns = 68.3 us  ->  ~14.6 kHz
```
So a full chain refresh costs **68µs at max clock** - about 7% of the 1ms scan window, and the LED refresh doesn't need to happen every scan anyway. **SPI time is not in competition with key scanning.**

Each chip deliberately delays CKO by **half a clock** relative to CKI, so no two chips latch on the same edge. That's why a fixed 32-bit end frame works: propagating through N chips costs on the order of N/2 clock edges, so 30 LEDs needs ~15 and 32 is comfortable. **If a future revision ever chains multiple tiles' LEDs onto one SPI bus, re-check this** - the fixed 32-bit end frame goes marginal somewhere around 64 LEDs.

### Math - current, and the thermal ceiling
This is the number that actually matters, and it isn't the one in the old note:

| Condition | Per LED | Chain of 30 |
| --- | --- | --- |
| Brightness level 10 (**datasheet's recommended max**) | 15.7mA | **~471mA** (+30mA static = ~501mA) |
| Brightness levels 11–32 | up to ~63mA | **~1.9A** |

The datasheet says outright: *"Based on the heat dissipation of the product, it is recommended to use a maximum current of 0–5mA for adjustment. The current adjustment level of 11–32 is not recommended."*

**That's a package thermal limit, not a power-source limit** - it applies even if the PD contract has amps to spare. So:

> **!firmware-note!** **Firmware must clamp the 5-bit global brightness field to ≤10, independent of the PD power budget.** This is separate from PWM duty-cycle capping and separate from the RGB brightness cap the master already sends. Getting this wrong doesn't trip a power budget, it cooks LEDs.

The old "540mA worst case" figure in [rgb design-choice](../design-choices/rgb.md) was based on 18mA/LED. The real ceiling under the datasheet's own guidance is **~500mA**, and the real *unrestricted* worst case is **~1.9A** - so the old number was neither the safe ceiling nor the true worst case. Rail sizing should use ~500mA as the design point and 1.9A as the fault case.

### Result / parts (as-built)
LED1–LED30, daisy-chained SDO→SDI / CKO→CKI, all on **+5VP**, each with a local 100nF (C46–C75). Chain head is fed from U8 through R63/R64 33Ω.

### Notes / gotchas
- **!firmware-note!** **Colour order is contradicted within the datasheet.** p.7 says RBG, p.8 says GRB, same revision. The frame table's concrete field order (red, blue, green) is the more trustworthy of the two, but **this needs verifying against a physical LED before firmware ships.** Cheap to check, annoying to debug later.
- The datasheet's own abs-max VDD row is a self-referential copy-paste artifact and can't be read as a real rating. Treat 5.3V as the ceiling from the operating table.
- Series resistors belong **once, between the controller and LED1** - the datasheet's application circuit doesn't repeat them at each inter-chip junction. As-built matches.

## SPI drive - SCK/DATA series & level shift
### Goal
3.3V MCU → 5V LED logic. SPI0 (SCK GPIO34, TX GPIO35) has to actually register as a logic high on LED1's CKI/DI pins.

### Datasheet refs
- SK9822-EC20 §9 *IC electrical parameters* (TA=25°C): **VIH min 3.4V**, VIL max 1.6V, VDD 5–5.3V, IDD 1mA
- SK9822-EC20 features: **max serial input data frequency 15MHz**
- XC6220B331MR: fixed 3.3V output, ±2% - so 3V3 lives in **3.234–3.366V**

### Math
i wrote "add a level shift **if marginal**" the first time round, which was me assuming this was a judgement call. it isn't. the numbers:

```
SK9822-EC20 VIH min      = 3.400 V
3V3 rail, best case      = 3.366 V   (XC6220 at +2%)
3V3 rail, nominal        = 3.300 V
RP2350B VOH              ≤ 3V3 rail  (never above it)
```

so the **best possible** high the MCU can put out is 3.366V against a 3.400V threshold. it doesn't clear it at nominal, it doesn't clear it at the top of the LDO's tolerance, and it doesn't clear it at 25°C which is the only condition the table is even specified at. margin is **−34mV in the best case and −100mV nominal**.

**so "better safe than sorry" turns out to have been the wrong framing entirely - there was nothing to be safe *about*, it's just out of spec.** driving these direct is a violation, full stop. worth writing down *why* i almost talked myself out of it: everyone on the internet runs APA102/SK9822 straight off a 3.3V micro and reports it working, so the vibe is "eh it's fine." and it probably does work on a bench at room temp with a fresh reel. but "works on the parts i happened to get, at the temperature i happened to test at" is not the same as "the datasheet guarantees it," and this is a keyboard i want to *daily drive* with 30 of these per tile and up to 8 tiles. one flaky LED in the chain corrupts every LED downstream of it, because the data is a daisy chain. that's a really bad failure mode to gamble on for the sake of one 16-cent part.

**lesson in the same shape as the [power](power.md) ones: "lots of people do it" is not a spec.** if the table says 3.4 and i have 3.3, i need a part, not a vibe.

### Result / parts
level shifter is **mandatory**, 2 channels (CKI + DI). part chosen in [picking the level shifter](#picking-the-level-shifter) below → **SN74LVC2T45DCUR**.

### Notes / gotchas
- the shifter only ever drives **LED1**. every SK9822 regenerates the signal on its CKO/DO pins, so drive strength / fan-out is a non-issue - it's a 1-load net, not a 30-load net
- 15MHz ceiling is miles above anything i need (30 LEDs × 32 bits ≈ 1k bits/frame; even 1MHz is 30 fps), so **speed is not the constraint here** - don't let it drive the part choice
- still want **22–33Ω series** on SCK/DI for ringing, placed at the *shifter output* (the 5V side), not between MCU and shifter
- do **not** try to fix this by lowering the LED VDD - VIH is a flat 3.4V in the table, not a ratio of VDD, so dropping VDD doesn't drop the threshold. dead end, noting it so i don't rediscover it later

## Picking the level shifter

### Identify
i need a part (or circuit) that takes 3.3V push-pull logic in and puts 5V push-pull logic out, on 2 lines, non-inverting.

**the constraint nobody flagged until i looked at the rails:** the SK9822s are on **gated-5V** (the big buck, EN=GPIO14) and the MCU is on **3V3** (off BS+, always-on). those two power up at *different times*, and the whole [implementation](implementation.md#the-takeaway) lesson was "walk the bring-up order." so:

> when the big buck is **off** (pre-PD, or firmware power-capping the RGB), the MCU is alive and can drive SPI0 into a level shifter whose 5V supply is at **0V**.

a plain single-supply buffer has input clamp diodes to VCC. input at 3.3V, VCC at 0 → the clamp conducts and the MCU starts back-powering the dead rail through its own SPI pins. that's the exact class of bug (something upstream feeding a rail that's supposed to be off) that bit me four times on the front end.

**the rescue that doesn't work:** "just power the shifter off BS+ instead, that's always on." no - then the shifter is happily driving 5V logic into 30 *unpowered* SK9822s, and now i'm back-feeding the LED string through 30 sets of input clamps instead of one buffer. strictly worse. **the shifter belongs on the same gated rail as the LEDs, so the whole RGB domain goes dark together** - which means the part has to tolerate its output rail being dead while its input side is live.

### the gates
1. **guaranteed VIH ≥ 3.4V drive at 5V, from a 3.3V input.** hard pass/fail against the datasheet table, no judgement.
2. **non-inverting.** it's a clocked protocol, an inverter breaks it.

gate 1 kills more than i expected:
- **direct drive, no shifter:** 3.366V max vs 3.4V min. **fail.**
- **74LVC1G125** (the cheapest, best-stocked buffer on LCSC by miles - 89k in stock at $0.045): at VCC 4.5–5.5V its VIH is **0.7 × VCC = 3.5V**. so a 3.3V input doesn't drive it either. **fail.** this one genuinely surprised me - i had "LVC = the cheap modern jellybean" in my head and would have grabbed it. LVC is TTL-ish at 3.3V VCC, but at 5V VCC it goes back to CMOS thresholds. **AHCT/HCT are the families with a flat 2.0V VIH at 5V, LVC is not.**

### Brainstorm (survivors)
- **A - 74AHCT125**, quad buffer, single 5V supply. the LED-community default. VIH 2.0V flat at 4.5–5.5V VCC ✓. SO-14/TSSOP-14, 2 of the 4 gates wasted (and the datasheet says unused inputs must be tied, so they cost me copper too). **no Ioff.**
- **B - 74AHCT1G125 ×2**, single-gate version of the same thing in SOT-23-5 / SC-70-5. same VIH ✓, much smaller, but 2 packages + 2 sets of decoupling. **no Ioff.**
- **C - SN74LVC2T45**, dual-bit *dual-supply* translator, VSSOP-8. VCCA=3V3, VCCB=gated-5V, DIR tied for A→B. VIH is referenced to VCCA (2.0V at 3–3.6V) ✓, and it's explicitly specified with **Ioff / partial-power-down**: when VCCB is 0 it disables the I/O instead of clamping. exactly 2 channels, no waste.
- **D - BSS138 ×2 discrete** (the classic FET shifter, 2 FETs + 4 resistors). cheap as dirt and stocked in the hundreds of thousands. but the rising edge is an RC through the pull-up, so edges are asymmetric and slow - on a *clocked* bus that's clock/data skew, which is the thing you least want.

dismissed without scoring: TXB0104-class auto-direction translators (weak output drivers, they fight series resistors and capacitive loads - wrong tool for driving a LED string), and NPN inverter pairs (inverting, needs two stages, more parts than C for worse everything).

### Select

| Criteria | Weight | A: 74AHCT125 | B: 74AHCT1G125 ×2 | C: SN74LVC2T45 | D: BSS138 ×2 |
| --- | :---: | :---: | :---: | :---: | :---: |
| Guaranteed VIH from 3.3V | gate | pass | pass | pass | pass |
| Non-inverting | gate | pass | pass | pass | pass |
| Survives gated-5V off w/ MCU driving | 9 | 2 | 2 | 10 | 8 |
| Speed / edge quality vs 15MHz | 6 | 9 | 9 | 10 | 3 |
| Part count & area for exactly 2 ch | 6 | 4 | 6 | 9 | 4 |
| Cost per tile | 5 | 5 | 7 | 7 | 9 |
| LCSC stock / JLC sourcing | 6 | 5 | 7 | 9 | 10 |
| Implementation simplicity | 5 | 7 | 8 | 6 | 5 |
| **Weighted Total** | | 186 | 225 | **323** | 244 |

**Winner: C - SN74LVC2T45 (323/370, 87.3%)**, and it's not close.

the gated-rail row is doing most of the work, which i think is correct - it's weighted 9 because it's a *hardware correctness* thing, and the alternative is "firmware must never touch SPI0 while the big buck is off," which is exactly the kind of software-correctness assumption i refused to rely on back in [comms](../design-choices/comms.md) for the both-ports-plugged case. i'd rather spend $0.16 than owe firmware a promise forever.

the rest of the ordering is honest but secondary: **D (244)** does surprisingly well because it's dirt cheap, enormously stocked, and the pull-up actually limits back-feed to a fraction of a mA - it only loses because slow asymmetric edges on a clocked bus is a real risk and i'd be hand-tuning pull-ups against edge rate for no reason. **B (225)** beats **A (186)** purely on package - two SOT-23-5s beat one SO-14 where i'd waste half the part and still have to tie off the spares. both AHCT options eat the same 2 on the gated-rail row.

**sourcing (LCSC, checked):**

| Part | LCSC | Package | Stock | Price | JLC |
| --- | --- | --- | --- | --- | --- |
| **SN74LVC2T45DCUR** | **C15741** | **VSSOP-8** | **17,079** | **$0.161** | extended |
| SN74LVC1T45DBVR (×2 fallback) | C7843 | SOT-23-6 | 38,783 | $0.057 ea | extended |
| SN74AHCT1G125DBVR | C7484 | SOT-23-5 | 1,635 | $0.091 | extended |
| SN74AHCT125PWR | C36365 | TSSOP-14 | 741 | $0.347 | extended |

nothing here is a JLC basic part, so they all cost the same setup fee - which means cost basically drops out as a tiebreaker and i should just take the one that's *right*.

**fallback if C ever goes out of stock:** **SN74LVC1T45 ×2** (C7843, 38k in stock, $0.057 each). same family, same Ioff behaviour, same dual-supply wiring, just one bit per package - so it's a drop-in decision with no re-analysis, only a footprint swap.

### package: DCUR (VSSOP-8), not YZP (DSBGA-8)
the part comes in a 2.0×3.1mm VSSOP (DCUR) and a 1.5mm-ish die-size BGA (YZP, 0.5mm max height vs 0.9mm).

i originally ruled YZP out because i was hand-assembling: its balls are **SNAGCU** (SAC, melts ~217C) and my paste was Sn42/Bi57/Ag1 at ~160C peak, so the balls would never collapse - plus no visual inspection and no realistic rework. **that argument is dead now that JLC assembles this** (see the [hall-effect re-revisit](../design-choices/hall-effect-sensors.md#re-revisit-im-not-assembling-this-myself-anymore)).

DCUR still wins, just on duller grounds:
- **$0.161 vs $0.374** and **17,079 vs 1,996 in stock**. both are JLC *extended* parts, so identical setup fee - the price gap is pure loss.
- YZP is 0.35mm-pitch die-size BGA, which drags finer trace/space (and probably via-in-pad) onto the whole board for one part that doesn't need it.
- the 0.4mm height saving buys **nothing** - board Z-height is set by the switches and the LED package, not an 8-pin logic part.

so: same answer, weaker reasons. worth knowing that if the price ever inverted the argument would too.

### wiring it
- **VCCA → 3V3**, **VCCB → gated-5V (+5VP)**, decoupling on both
- **DIR tied high to VCCA** (A→B, fixed direction - i never read back from the LEDs)
- A1/A2 ← SPI0 SCK (GPIO34) / TX (GPIO35); B1/B2 → LED1 CKI / DI through the 22–33Ω series
- both rails already exist right there, so "needs two supplies" costs me nothing but a via

### as-built (done)
swapped on the board, **U8 = SN74LVC2T45DCUR**, VSSOP-8:

| pin | net | note |
| --- | --- | --- |
| 1 VCCA | +3V3 | always-on side |
| 2 A1 | `LED SCK` | SPI0 SCK, GPIO34 |
| 3 A2 | `LED TX` | SPI0 TX, GPIO35 |
| 4 GND | GND | |
| 5 DIR | +3V3 via **R62 0Ω** | H = A→B, fixed direction |
| 6 B2 | → **R63 33Ω** → LED1 SDI | series on the 5V side |
| 7 B1 | → **R64 33Ω** → LED1 CKI | series on the 5V side |
| 8 VCCB | +5VP | gated side, dies with the LEDs |

the 74AHCT125 that was here is gone, and with it the back-feed exposure. TI's own numbers for the replacement: **total static current is <2µA** with VCCA=3V3/VCCB=5V, **<1µA** with VCCB at 0 (Table 8-4), and the datasheet states outright that if either VCC is at GND both ports go high-impedance (§1) with Ioff bounding leakage to **±2µA** (§5.5).

**!firmware-note!** one behavioural note that came out of the datasheet read and is a *firmware* requirement, not a hardware one: **the A-port inputs must never float**, even while VCCB is dead, or ICC goes up. so firmware should keep SCK and TX driven at all times rather than releasing them to inputs when RGB is off.

### carry-forward
- **[chips](../chips.md)** got the new BOM line - the level shifter was missing from it entirely

## Rail current budget & caps
### Goal
Bulk cap for LED inrush/ripple on gated-5V.
### Math
_(bulk C for chain; per-LED decoupling density)_
### Notes / gotchas
- Powered from **big (gated) buck**, NOT the clean rail

---
Back to [schematic-design index](index.md) · [checklist](../schematic-checklist.md)
