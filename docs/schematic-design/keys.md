# Keys & sensing - schematic-design calcs

Hall sensor + mux + ADC math. Parts from [chips](../chips.md); decisions from [hall-effect-sensors](../design-choices/hall-effect-sensors.md).

Values are **as-built**, with the derivation. Where the independent [datasheet research](../research/) disagrees or found a gap, it's called out.

Per-section skeleton: **Goal → Datasheet refs → Math → Result → Notes/gotchas.**

## Contents
- [Hall sensor - GH39FKSW ×30](#hall-sensor---gh39fksw-30)
- [The ratiometric assumption](#the-ratiometric-assumption)
- [Analog mux - CD74HC4067SM ×2](#analog-mux---cd74hc4067sm-2)
- [Scan budget](#scan-budget)
- [Sensor bank-power gating](#sensor-bank-power-gating)
- [Loose ends on this sheet](#loose-ends-on-this-sheet)

---

## Hall sensor - GH39FKSW ×30

### Goal
Per-key analog readout on the clean 3V3 rail, into a 16:1 mux, into the RP2350B ADC. Firmware does per-key min/max calibration.

### Datasheet refs
GoChip GH39F series (LCSC **C266230**, SOT-23-3L). Everything below is from the "电磁特性" table, p.3/6 - **and the entire table is characterised at VCC = 5V.**

| Parameter | Min | Typ | Max | Unit |
| --- | :---: | :---: | :---: | :---: |
| Supply voltage VCC | 3.0 | — | 6.5 | V |
| Supply current | — | — | **9.0** | mA |
| Sensitivity | 1.45 | **1.8** | 2.0 | mV/Gs |
| Magnetic range | ±650 | ±1000 | — | Gs |

Output stage is an **emitter follower biased by a 65µA typical current source** to GND (block diagram, p.4/6) - the same topology and the same 65µA figure as the Honeywell SS49E, which strongly suggests this is an SS49E-class clone.

**What the datasheet does not contain, at all:**
- power-on / start-up settling time
- output impedance, source current, or sink current as specified rows
- any ESD rating (HBM/CDM/IEC)
- any reverse-supply rating
- numeric temperature-drift coefficients (graphs only, and they're images - no extractable values)

### Result / as-built
30 sensors, VDD → **+3V3**, OUT → its mux channel, pin 3 → GND, each with a **100nF (C78–C107)** local decoupling cap. Schematic note says "put 1 of these next to each sensor between pin 1 and 3" ✓ - that's the right instruction and the right count.

**3.3V operation is in spec** (3.0V min) but with only 0.3V of margin, and it is *not* the condition anything is characterised at.

### Notes / gotchas
- **The weak sink is the interesting one.** An emitter follower with a 65µA tail can source ~10mA but can only sink 65µA. Driving a mux common node with **CCOM = 50pF**, that puts a slew limit on falling transitions:
  ```
  dV/dt = 65uA / 50pF = 1.3 V/us
  ```
  A worst-case channel-to-channel step of ~2.3V therefore takes **~1.8µs to settle downward**, versus ~200ns for the RC-limited rising case. That's a 9× asymmetry the naive RC analysis misses entirely - see [scan budget](#scan-budget), where it turns out not to break anything but does change which term dominates.
- 9mA × 30 = **270mA** worst case, which is the number that makes [bank gating](#sensor-bank-power-gating) load-bearing.
- No ESD rating and no reverse rating on a part that sits under a keycap the user touches. Not much to do about it directly, but worth knowing these pins are unprotected.

## The ratiometric assumption

This deserves its own section because the whole analog chain leans on it and **it is not proven anywhere.**

The sensor's characteristics are given at 5V. The board runs it at 3.3V. The only evidence that the output scales with supply is a qualitative "quiescent output vs VCC" graph (p.3/6) showing Vout rising roughly linearly from ~2.5V to 8V. There is **no ratiometricity percentage, no sensitivity-vs-VCC table, and no 3.3V column.** Honeywell characterises the comparable SS49E as *approximately* ratiometric with real part-to-part spread (0.15–0.40 mV/Gauss/V around ~0.25–0.30 nominal) - approximately, not tightly guaranteed.

Why it matters more than it looks:

- **If ratiometric holds**, noise on 3V3 partially cancels in the ADC reading, because the sensor's transfer function and the ADC's own reference (ADC_AVDD, also 3.3V) move together. That's a big free win for a noisy rail.
- **If it doesn't hold**, 3V3 noise appears directly in every keypress measurement with no cancellation - which puts a much stiffer requirement on the LDO and its decoupling than currently exists, especially given the LDO has [no output-noise specification at all](power.md#3v3-ldo---tlv76733drvr-u7) and the clean buck feeding it [runs in DCM](power.md#clean-buck---tps54302-u5).

**This is a bench measurement, not a datasheet question.** Scaled sensitivity at 3.3V would be ~1.19 mV/Gs (1.8 × 3.3/5) if the assumption holds. Worth measuring on real parts before trusting the ADC budget - and it's cheap to measure: sweep VCC, watch quiescent output and a fixed-magnet reading.

Every 3.3V-scaled number on this page is **assumed, not specified.**

## Analog mux - CD74HC4067SM ×2

### Goal
32 channels into 2 ADC pins with 4 shared select lines. 30 keys → 2 spare channels.

### Datasheet refs
TI CD74HC4067 (SCHS209D). **HC family, VCC 2–6V** - and 3.3V, while inside the recommended range, is **not a characterised test point**: the electrical tables are populated only at 2V, 4.5V and 6V. There is no 3.3V column anywhere.

| Parameter | Value | Note |
| --- | --- | --- |
| VCC abs max | 7V | design to TI's, not Nexperia's 11V |
| RON(rail) @4.5V | 70Ω typ | **no figure at 3.3V or 2V** |
| ΔRON @4.5V | 10Ω | 25°C only |
| CCOM (common pin) | **50pF** | dominates the settling RC |
| VIH/VIL @3.3V | **not tested** | interpolating the 70%/30% pattern gives ~2.31V/0.99V |

The Nexperia part with the same number is **different silicon** (RON 90Ω typ vs TI's 70Ω at 4.5V) and carries an explicit footnote that RON becomes "extremely non-linear" as VCC approaches 2V, recommending digital-only use there. We're at 3.3V, not 2V, so that warning doesn't bite - but it's the reason to use a **design value of ~400Ω** for RON at 3.3V with margin rather than TI's 4.5V number, since TI gives nothing to interpolate from.

Select-line logic levels are a non-issue: the RP2350 drives rail-to-rail 3.3V CMOS, clearing any plausible threshold with large margin.

### Result / as-built
| Item | As-built |
| --- | --- |
| VCC | +3V3, C108/C109 100nF each |
| E (inhibit) | tied **low** via R61 / R52 (0Ω) → always enabled |
| S0–S3 | via R60/R59/R58/R57 and R56/R55/R54/R53 (0Ω) to **AS0–AS3**, shared by both muxes ✓ |
| COM | AM0 → GPIO40/ADC0, AM1 → GPIO41/ADC1 ✓ |
| Channels used | AM0:0–14 and AM1:0–14 = **30 sensors** |
| Channels spare | **AM0:15, AM1:15** |

The 0Ω jumpers on every select and enable line follow the project convention (default-populated jumper on all digital enable/select pins) - good, it makes the enable line reworkable if E ever needs firmware control for bank gating.

### Notes / gotchas
- ⚠ **AM0:15 and AM1:15 are floating.** Each has exactly one node on the net - the mux input pin - and nothing else. Unused CMOS analog switch inputs shouldn't be left open; they pick up charge and can inject it onto COM when addressed, and TI's own guidance for the family is to hold unused inputs at VCC or GND. **Tie both to GND**, ideally through a pad so they can be repurposed as test points later. This is a 2-resistor fix and it's the only outright defect on this sheet.
- Both muxes switch simultaneously on the shared select lines, so their supply-current transients coincide. With 100nF each and a shared 3V3 rail this is small, but it's the one mechanism by which mux switching couples into the analog rail - keep C108/C109 tight to the pins.

## Scan budget

### Goal
30 keys, full 12-bit, inside 1ms.

### Math
Per channel, three terms:

```
1. mux propagation (TI, worst case @4.5V)              ~90 ns
2. settle on COM to 1/2 LSB of 12 bits
     RC case:   tau = RON x CCOM = 400R x 50pF = 20 ns
                n = ln(2^13) = 9.0 time constants      ~180 ns
     slew case: 65uA into 50pF = 1.3 V/us
                worst 2.3V step, falling               ~1770 ns
3. RP2350 SAR conversion (96 clocks @ 48MHz)           ~2000 ns
```

The research computed the RC case and got ~2.3µs/channel → **~69µs for a full scan, 14.5× margin**. That's right as far as it goes, but it assumes a symmetric driver.

Taking the **slew-limited** falling case as the worst term instead:
```
90 ns + 1770 ns + 2000 ns = 3.86 us/channel
x 30 channels             = 116 us
```

### Result
**~116µs worst case against a 1000µs budget - roughly 8.6× margin.** Comfortable either way. Even the pessimistic slew-limited number leaves the scan taking about a tenth of the window.

**The ADC conversion, not the mux, is the floor.** At 2µs per conversion, 30 channels can't go faster than 60µs no matter what the analog front end does. If the scan rate ever needs to go up, the lever is the ADC clock, not RON or capacitance.

### What the RP2350 side contributes - and it is not what i assumed

The budget above treats the ADC as a 2µs black box. Pinning down what it does to the *analog* side turns out to matter more than the timing:

> **"The ADC input is capacitive. When sampling, the ADC places about 1pF across the input… the effective impedance, even when sampling at 500 kS/s, is over 100 kΩ. DC measurements have no need to buffer."** — RP2350 datasheet §12.4.3

Three things fall out.

**1. The ADC is not the load; the mux is.** 1pF against C_COM's 50pF is 2%. This is *not* the usual SAR that dumps a big sampling cap onto the pin - there is no charge-redistribution kick to settle. Every settling number above is set by C_COM alone, and adding a cap at the ADC pin (the trick that made the [32-level submodule ID divider](../design-choices/submodules.md#the-5th-pin-id) work) would **make settling worse here, not better** - it's more C for the sensor to charge through R_ON.

**2. There's a DC gain error nobody had counted.** >100kΩ effective impedance against a real source impedance is a divider:

| R_source (sensor Zout + R_ON) | gain error | at 12 bits |
| ---: | ---: | ---: |
| 260Ω | 0.26% | ~11 LSB |
| 500Ω | 0.50% | ~20 LSB |
| 1500Ω | 1.48% | ~61 LSB |

Common to all 30 channels and constant, so **per-key calibration removes it** - which this design does anyway for magnet tolerance. The part that *doesn't* calibrate out: TI's Figure 14-1 shows **R_ON varies with input signal voltage**, so this divider varies across the sensor's swing. That's a small INL term rather than an offset - a few LSB, below the noise floor i'd expect, but it's a real mechanism and it's the only one here that calibration can't flatten.

**3. Off-channel feedthrough is 0.44 LSB.** −75dB on a 2.3V swing is **356µV** against an 806µV LSB. Under half a count, from all 15 unselected channels combined. Not a concern, and worth writing down so nobody re-derives it.

#### the 64mm sensor traces don't enter this at all
Worth stating because it's counter-intuitive: the long analog runs are on the mux's **input** side, where each channel's trace is held statically at its sensor's voltage. Only the **COM node** has to slew when the address changes. Trace length on the sensor side is a **noise-pickup question, not a settling one** - which is why the [analog-on-L1 rule](../design-choices/pcb-stackup.md#the-rule-that-does-the-real-work) is the thing protecting it, not the scan budget.

> **This closes the settling half of the ADC path, not the noise half.** The "[not characterised end-to-end](power.md#clean-buck---tps54302-u5)" flag is about the *supply* chain - DCM ripple → LDO with no output-noise spec → 3V3 → sensors - and none of the above touches it. Same for [review F6](../schematic-review-2026-08-08.md) on ADC_AVDD. Impedance and timing are now known; supply noise still isn't.

### Notes / gotchas
- The RP2350 datasheet's line *"switching AINSEL requires no settling time"* refers to the **RP2350's internal ADC input selection**, not to an external mux. It does not apply to the CD74HC4067, which genuinely needs the settle above. Easy line to misread into a much rosier budget.
- **R_ON is not specified at 3.3V.** TI's table gives it at 4.5V (160Ω max, 225Ω over temperature) and 6V only - the mux runs on +3V3, where HC-family R_ON is roughly 2× the 4.5V figure. The 400Ω used in the math above is that extrapolation, not a datasheet number. It doesn't change the conclusion (the margin absorbs it), but it is an assumption, not a spec.
- **The GH39F never states an output impedance.** All its parameters are "No load", and the only related figure is a note to measure with a >10kΩ instrument - that's a *load* requirement, not a source impedance. The 65µA sink figure above comes from the sensor side and is the number the whole slew case rests on; it deserves a bench measurement on the first board.
- Scan order is free to choose, and choosing it to minimise large falling steps between consecutive channels would cut the slew term - but with 8.6× margin there's no reason to bother.
- Charge injection on channel switch is **not specified by either vendor at any voltage**. With 8.6× timing margin there's room to absorb it, but if per-key readings show a dependence on *which key was scanned previously*, this is the mechanism.

## Sensor bank-power gating

### Identify
30 hall sensors × 9mA worst case = **270mA continuous**, burning whether or not anyone is typing. But i only ever *read* one sensor at a time through the mux - at any instant 29 of them are producing a value nobody looks at.

**Bank gating** = split the sensors into groups, put a high-side switch on each group's VDD, and only energise the group i'm about to scan. Current scales as `270mA / number_of_banks`.

```
now:        +3V3 ─┬─ all 30 sensors, always on              270 mA

banked:     +3V3 ─┬─[FET]─ bank 0   <- only this one on      45 mA  (6 banks)
                  ├─[FET]─ bank 1      (off)
                  ├─[FET]─ bank 2      (off)
                  └─ ...
```

Cost is one P-FET + one GPIO per bank, plus firmware sequencing.

#### Relevant constraints
- **1000Hz polling** - the hard one. Everything below lives or dies on the scan fitting in 1ms.
- Sub-1ms latency
- Portable / bus-powered, so current isn't free

#### What changed since this was first proposed
When [hall-effect-sensors](../design-choices/hall-effect-sensors.md) first said "strong argument for bank-powering", the reason was the LDO: the XC6220 in SOT-25 can't dissipate 5V→3.3V at 400mA (TJ ≈ 138°C at room ambient, past its own 125°C design point). **Gating was survival, not optimisation.**

Then [swapping to a TLV767 in WSON-6](power.md#3v3-ldo---tlv76733drvr-u7) dropped θJA from 166.7 to 77.7°C/W - **TJ ≈ 78°C at the same 400mA**. The thermal argument evaporated. So this is now a genuine open choice rather than a forced move, which is why it deserves an actual decision instead of a to-do.

### The 1000Hz arithmetic (this is what decides it)

From the [scan budget](#scan-budget), a full 30-key scan costs **~116µs** of the 1000µs window. Banking adds a settling wait every time a bank is energised:

```
total = 116us  +  B x t_settle          (naive, serial)
```

**But you can pipeline it** - energise bank *k+1* while still reading bank *k*. Then settling only costs anything if it's *longer* than the time spent scanning one bank:

```
scan time per bank = 116us / B
settling is FREE if  t_settle <= 116/B
otherwise you stall by (t_settle - 116/B) per bank
```

| Banks | Current | Scan per bank | t_settle that stays free | Cost if t_settle = 100µs |
| :---: | :---: | :---: | :---: | --- |
| 1 (none) | 270mA | — | n/a | 0 |
| 2 | 135mA | 58µs | **≤58µs** | +84µs → 200µs total |
| 6 | 45mA | 19.3µs | **≤19µs** | +484µs → 600µs total |
| 30 | 9mA | 3.9µs | **≤3.9µs** | +2.9ms → **misses 1000Hz entirely** |

(Pipelining means two banks are lit during the overlap, so real current is `2/B × 270mA` - 90mA at 6 banks, not 45mA. Still a big win, just not the headline number.)

**And here is the problem: `t_settle` is not specified anywhere.** The GH39F datasheet has no power-on settling row. The SS49E's "3µs response time" is a *field-step* response in an already-powered part and cannot substitute. So every row in that table except the first is **a bet on a number nobody has published**, and the tighter the banking the bigger the bet.

> **Update - there is now a number, and it's bad for gating.** The TI **DRV5056** (same class of part: linear ratiometric hall, SOT-23, same application) *does* publish it: **tON = 150µs typ / 300µs max**, B=0mT, no load on OUT (SBAS644C §5.5). That's the closest thing to a datasheet answer available for what a sensor like this costs to wake up.
>
> Running the table again with t_settle = 300µs:
>
> | Banks | Pipelined cover | Serial total | Verdict |
> | :---: | :---: | :---: | --- |
> | 2 | 58µs (blown through) | 116 + 600 = **716µs** | fits 1000µs, but leaves ~280µs for USB, comms, RGB and everything else |
> | 6 | 19µs (blown through) | 116 + 1800 = **1916µs** | **misses 1000Hz outright** |
>
> If the GH39F behaves like its class - and it's architecturally an SS49E-clone with the same emitter-follower output stage - then **bank gating at 1000Hz isn't merely risky, it's close to infeasible.** That takes the decision below from a judgement call to something much more settled.

That is what the 1000Hz requirement does to this decision: it converts a missing datasheet spec into a **schedule risk on the hardest constraint in the project**. A design that only meets 1000Hz if an unmeasured number turns out small is not a design, it's a hope.

### Brainstorm

- **A - no gating.** 270mA continuous, TLV767 carries it at 78°C. Zero added parts, zero firmware, zero dependency on t_settle.
- **B - 2 banks.** 135mA (190mA pipelined). 58µs of cover for settling, which is generous for any plausible linear-hall startup. 2 FETs, 2 GPIO.
- **C - 6 banks.** 45mA (90mA pipelined). Only 19µs of cover. 6 FETs, 6 GPIO.
- **D - per-key, 30 banks.** 9mA. 3.9µs of cover, and it needs 30 GPIO i do not have ([pin-budget](../design-choices/pin-budget.md) is at 40/48 with 8 spare). Listed for completeness, not seriously on the table.
- **E - change the sensor to DRV5055.** 2mA typ / 4mA max at 3.3V → 30 × 4 = **120mA worst case with no gating at all**, less than half the GH39F's 270mA. Kills the problem at the source rather than working around it. ~$0.59/sensor vs GH39F's $0.13, and gives up the "proven on the Void switch reference design" argument that won [the original selection](../design-choices/hall-effect-sensors.md#select).
  - **Note this is DRV50*55*, not DRV50*56*.** The 5056 is 6mA typ / 10mA max - *worse* than the GH39F - and unipolar, so magnet polarity has to be right. The current figure in [hall-effect-sensors](../design-choices/hall-effect-sensors.md#correction-the-drv5056-current-figure-above-is-wrong) was wrong and is corrected there.

### Select

| Criteria | Weight | A: none | B: 2 banks | C: 6 banks | D: per-key | E: DRV5055 |
| --- | :---: | :---: | :---: | :---: | :---: | :---: |
| Meets 1000Hz with margin | 10 | 10 | 4 | 1 | 1 | 10 |
| No dependency on an unpublished spec | 8 | 10 | 4 | 2 | 1 | 9 |
| Current saved | 6 | 1 | 5 | 8 | 10 | 7 |
| Part count / GPIO cost | 5 | 10 | 8 | 6 | 1 | 10 |
| Firmware simplicity | 5 | 10 | 8 | 6 | 4 | 10 |
| Cost (×30 ×N tiles) | 6 | 10 | 9 | 8 | 4 | 2 |
| Keeps the proven Void-switch sensor | 6 | 10 | 10 | 10 | 10 | 1 |
| **Weighted total** | | **406** | 302 | 232 | 191 | 332 |

*(the 1000Hz and unpublished-spec rows for B/C/D were re-scored downward after the DRV5056 tON figure above - 300µs max makes every banked option either marginal or impossible, where before they merely lacked evidence.)*

**Winner: A - no gating (406/460, 88%).** Second is now **E (332)**, not B - once the 300µs power-on figure lands, changing the sensor beats gating it.

Which is a slightly funny result, because it means the answer is *"delete the feature i've been carrying as a to-do since the hall-effect page."* But it follows directly once the LDO stops being the bottleneck:

- **Gating never had an independent justification.** It existed to keep the LDO alive. Fix the LDO properly and the reason goes with it.
- **The 1000Hz row and the unpublished-spec row are the two heaviest**, and A is the only option that scores 10 on both. Every gating option pays on at least one, and C and D pay heavily on both.
- **B (362) is the honourable second** and stays the retrofit if the power budget ever demands it - 58µs of settling cover is enough that it'd probably just work.
- **E (338) is the technically cleanest answer and loses on money.** 6× lower sensor current, real TI specs including a startup time, no FETs, no GPIO, no firmware. It gives up ~$100 across four tiles' worth of sensors and the Void-switch pedigree. If the GH39F ever turns out to have a nasty unpublished behaviour, this is where i go, and it's a drop-in because the footprint is already the generic 3-pin SOT-23 chosen for exactly this reason.

**Decision: no bank gating. Keep all 30 sensors on +3V3 continuously, and fix the supply instead of the load.**

### Testing the alternative sensor on the first run

The footprint is a **verified** drop-in (GH39F, DRV5055 and DRV5056 are all 1=VCC, 2=OUT, 3=GND in SOT-23, matching the symbol on the board), so the first prototype run can settle the GH39F-vs-DRV5055 question empirically instead of on paper.

**Do it as a mixed population on one board, not as a split order.**

| | Split the order | Mixed population |
| --- | --- | --- |
| Assembly orders | 2 (two setup fees, two extended-part fees) | 1 |
| What differs between the samples | sensor **+ panel + reflow run + board** | **sensor only** |
| Working keyboards | 2, one of each | 1, fully working |
| Cost of the experiment | 2× setup | ~4 × $0.59 = **$2.40** |

Populate e.g. **26 GH39F + 4 DRV5055A1** (C962987) at chosen grid positions - one BOM, two part lines against different refdes, which is a completely normal thing to hand JLC. Same panel, same reflow profile, same rail, same firmware. **The only variable is the sensor**, which is the entire point.

Pick the 4 positions to be informative rather than adjacent: one near the LED chain (thermal), one near a mux, one mid-field, one at a board edge.

What that run answers:
- **Does the 300µs-class power-on time apply to the GH39F too?** Scope both types on the same rail.
- **Is the GH39F actually ratiometric?** DRV5055 is explicitly specified as ratiometric, so it's a reference against which the GH39F's behaviour at 3.3V can be compared directly - which is the [one measurement still load-bearing](#the-ratiometric-assumption) on this sheet.
- Sensitivity, null drift and noise, side by side, with identical magnets and identical mechanics.

The 4 test keys will need their own calibration constants, but per-key min/max calibration is already in the design, so that costs nothing - and it's exactly the mechanism being tested.

**Sourcing caution either way:** GH39FKSW stock is **2968** at LCSC. 30/tile means one order of 4 tiles eats 120, which is fine, but that's a thin single-source line for a part that has no second source. DRV5055A1 sits at 6660. Worth watching.

### Leave the door open - but only just

The obvious hedge is to draw the gating circuit now and leave it DNP, in the same style as the [second flash](mcu.md#qspi-flash---w25q128jvs) and R28 on the reference. Per bank that's:

```
+3V3 ──┬── R_link (0R, POPULATED) ──┬── +3V3_S0  → bank 0 sensors
       └── Q_bank (P-FET, DNP) ─────┘
                 │gate
                 ├── R_pu (DNP, gate→+3V3)     default-off once populated
                 └── R_g  (populated, GPIO→gate)
```
Default = jumper in, FET absent, sensors always on. Retrofit = pull 2× 0Ω, populate 2 FETs + 2 pull-ups. No level shifting needed: source and gate drive are both 3.3V, so a logic-level P-FET runs straight off a GPIO.

**Bank by mux, not by select address.** Bank 0 = AM0's 15 sensors, bank 1 = AM1's 15. Two reasons:
1. The RP2350 has **one** SAR ADC with an input mux, so all 30 readings are sequential regardless - banking by mux costs **zero** scan time. (An earlier version of this page claimed by-mux banking would halve throughput. That was wrong; there is no second ADC to idle.)
2. Physically, AM0's sensors sit roughly on one side of the tile and AM1's on the other, so each bank is a coherent pour. Banking by select address would give two **interleaved** rails scattered across all 30 positions, because the channel assignment was done for routing convenience, not grid order.

**Is the hedge worth it? Marginally, and less than it looked before the 300µs figure.** At 2 banks the serial cost is 716µs of the 1000µs window - it fits, but it spends 60% of the budget to save 135mA. Six banks doesn't fit at all. So the retrofit this hedge preserves is a *narrow* one.

Cost of carrying it: 2 SOT-23 + 4× 0402 footprints, 2 GPIO (8 spare), and the sensor supply becomes two nets instead of one pour. That last one is the real cost, and it's paid in layout time now for an option that may never be exercised.

**If only one hedge gets carried, carry the sensor test above instead** - it costs $2.40 and answers a question that actually matters, where this one preserves access to a scheme the numbers have already mostly ruled out.

### Carry-forward
- The ~270mA stays in the [power budget](../design-choices/power.md#load-budget) as a permanent per-tile load: 0.9W at 3.3V, plus ~0.46W wasted in the LDO making it. ~1.4W/tile out of ~7W - about 20%, constant.
- **Measuring GH39F power-on settling is no longer blocking anything.** Still worth doing on the first assembled board, purely so option B is a known quantity if it's ever needed.

## Loose ends on this sheet

- [ ] **Tie AM0:15 / AM1:15 to GND** - currently floating (the one clear defect here)
- [ ] **Split sensor VDD onto its own net with a 0Ω link to +3V3** - keeps the gating retrofit cheap, see [above](#leave-the-door-open---but-only-just)
- [ ] **Bench-verify ratiometric behaviour at 3.3V** - the whole ADC noise argument rests on it, and it's the one measurement here that's still load-bearing
- [ ] Bench-measure GH39F power-on settling on the first board - **no longer blocking**, just makes option B a known quantity if the power budget ever wants it
- [x] ~~Add bank-gating FETs~~ - **decided against**, see the [selection above](#select). Fixed the LDO instead.
- The E pins are hard-tied low through 0Ω jumpers. Leaving as-is: with no bank switching there's nothing to blank the muxes *for*, and the jumpers mean a GPIO can be wired in later if that changes.

---
Back to [schematic-design index](index.md) · [checklist](../schematic-checklist.md) · [research](../research/)
