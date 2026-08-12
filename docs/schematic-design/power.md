# Power - schematic-design calcs

Datasheet math and component derivations for the power block. Parts come from [chips](../chips.md); wiring/behavior from [power design-choice](../design-choices/power.md); the front-end story (implement → snags → re-select) is in [implementation](implementation.md).

Rails: **PD+** (HV, 5.7–20V), **BS+** (bootstrap 5V, always-on), **+5VA** (clean buck out), **+5VP** (gated buck out, RGB/submodules), **+3V3** (clean), **GND**.

**How to read this page.** Values here are **as-built from the schematic**, with the derivation that justifies them. Where the independent [datasheet research](../research/) proposed something different, both are shown and the disagreement is resolved explicitly - sometimes the research is right and it's a to-do, sometimes the board is right because the research only saw one chip and not the whole system. Those are the interesting rows.

Per-section skeleton: **Goal → Datasheet refs → Math → Result → Notes/gotchas.**

## Contents
- [Clean buck - TPS54302 (U5)](#clean-buck---tps54302-u5)
- [Big buck - TPS54302 (U6)](#big-buck---tps54302-u6)
- [Picking the inductors (L2/L3)](#picking-the-inductors-l2l3)
- [3V3 LDO - XC6220B331MR (U7)](#3v3-ldo---xc6220b331mr-u7)
- [Ideal diode - LM66100 (U9)](#ideal-diode---lm66100-u9)
  - [Accepted risk: 5.95V on a 6.0V part](#accepted-risk-595v-on-a-60v-part)
- [Reference - TLV431 (U10)](#reference---tlv431-u10)
- [Threshold detector - LM2903 (U11)](#threshold-detector---lm2903-u11)
- [Q1 - VBUS→BS+ switch (AO3401)](#q1---vbusbs-switch-ao3401)
- [Q2/Q3/D4 - VBUS→PD+ switch (AO4407A + BC857 + BZX84C10)](#q2q3d4---vbuspd-switch-ao4407a--bc857--bzx84c10)
- [HV per-side switches - picking the FET](#hv-per-side-switches---picking-the-fet)
  - [The body diode - an open switch only blocks *outbound*](#the-body-diode---an-open-switch-only-blocks-outbound)
- [Backfeed diodes - LM74700-Q1 (D1/D2)](#backfeed-diodes---lm74700-q1-d1d2)
  - [Re-select: SS54 → LM74700-Q1](#re-select-ss54--lm74700-q1)
- [Bulk caps and the footprint defect](#bulk-caps-and-the-footprint-defect)

---

## Clean buck - TPS54302 (U5)

### Goal
5.0V from PD+, ~150–300mA. Feeds the 3V3 LDO (via BS+) and OR's onto BS+ through the ideal diode.

### Datasheet refs
TI SLVSDG6C. Vref **0.596V** (±2.5%, 0.581–0.611), §5.5. fSW 400kHz typ (290–510). VIN UVLO 4.1V typ rising. EN thresholds 1.23V rising / 1.16V falling. Internal fixed 5ms soft-start, no SS pin, no PG pin. RθJA 118.9°C/W bare / 57.2°C/W on TI's EVM - **no exposed pad**, so copper is the only heat path.

### Math - feedback divider
As-built the top leg is **R18 49.9Ω + R19 100kΩ** in series, bottom **R20 13.3kΩ**:

```
Rtop = 49.9 + 100k = 100.05kΩ
Vout = Vref x (1 + Rtop/Rbot) = 0.596 x (1 + 100050/13300)
     = 0.596 x 8.5226 = 5.080 V      (+1.6% vs 5.00V nominal)
```
Vref tolerance alone spreads that **4.952V – 5.207V** worst case, before resistor tolerance.

R18 contributes 0.05% to the ratio - it is not doing divider work, it's isolating the FB sense tap from the output node. Keep it, but note the divider equation is effectively R19/R20.

The research proposed **110k/15k → 4.967V (−0.67%)**, which is tighter. Not worth changing: +1.6% on a 5V rail that feeds an LDO with 1.7V of dropout headroom and LEDs that don't care is a non-issue, and re-spinning two resistors buys nothing.

### Math - inductor (L2 = 10µH)
```
dI = Vout(Vin - Vout) / (Vin x L x fsw)
   = 5(20-5) / (20 x 10u x 400k) = 0.938 A p-p   at Vin = 20V
DCM boundary: Iload < dI/2 = 0.469 A
```
Load is 150–300mA, so **this buck runs in DCM / pulse-skip across its entire operating range**, not fixed-frequency CCM. Peak inductor current stays under ~0.77A, so nothing is stressed.

The research derived **100µH** to get 30% ripple in CCM at 300mA, and it's right that 10µH is nowhere near that. But DCM on a 300mA rail behind 44µF and an LDO is fine, and 100µH in a package that fits is a much worse part. **Keeping 10µH** - but see the gotcha below, because it does have a consequence.

### Result / parts (as-built)
| Ref | Value | Role |
| --- | --- | --- |
| R19 / R20 | 100kΩ / 13.3kΩ | FB divider → 5.08V |
| R18 | 49.9Ω | FB sense isolation |
| C30 | 75pF | feedforward across R19 (TI ref-design value) |
| L2 | 10µH | DCM at this load |
| C28, C29 | 22µF ×2 = **44µF** | Cout - matches TI Table 7-2 exactly |
| C26 / C25 | 10µF / 0.1µF | Cin bulk / HF |
| C27 | 0.1µF | CBOOT |
| R34 | 100kΩ | pull-up to +3V3 for the U11B open-collector EN |

### Notes / gotchas
- **EN comes from U11B, not a divider.** `+5VA EN` is U11B's open-collector output pulled to +3V3 by R34. High (enabled) above the trip. EN sees 3.3V - inside the 5.5V recommended max and well under the 7V abs max. This is the [enable-from-trigger trick](implementation.md#the-enable-from-trigger-thing-the-good-bit) and it's better than the research's suggested VIN divider, because it enables off the *same comparison* that connects PD+ rather than off the rail being started.
- **The buck is enabled at ~5.95V but can't actually regulate 5V until ~7–9V in.** Between those it sits in dropout, output ≈ VIN − (RDS(on) x I) ≈ 5.8V. That's harmless (BS+ just sits a bit low, the LDO still has >2V of headroom) and it only lasts as long as the PD ramp, which is milliseconds. Worth knowing it's a real operating state, not an error.
- **The rail called "clean" is the one running DCM.** Variable-frequency pulse-skip ripple → MAX40203 → BS+ → LDO → 3V3 → hall sensors and the ADC. The LDO's PSRR is a single 50dB @ 1kHz point and **it has no output-noise spec at all** (see LDO section). So the ADC noise path is not actually characterised end-to-end anywhere. Not a blocker, but if key readings turn out noisy, this chain is the first suspect, and the fix is more Cout / a bigger L, not a different sensor.
- No PG pin - "did the big buck come up" has to be inferred some other way if that ever matters.

## Big buck - TPS54302 (U6)

### Goal
5.0V gated, RGB + submodule ports, ~2A worst case.

### Math
Identical divider (**R25 100kΩ / R26 13.3kΩ**, R24 49.9Ω) → same **5.080V**. Same L = 10µH:
```
dI = 0.938 A p-p at Vin=20V
Iload 2A >> dI/2 = 0.469A  ->  CCM across the whole range
IL(pk)  = 2 + 0.469 = 2.47 A
IL(rms) = sqrt(2^2 + 0.938^2/12) = 2.02 A
```
**Inductor needs Isat >= 3A and Irms >= 2.5A.** The research derived 15µH/2.39A peak; 10µH gives 2.47A peak, so the same class of part. 10µH is fine here.

Conduction loss (25°C RDS(on), the only tabulated figures) at VIN=9V, D=0.556:
```
P_HS = 2.02^2 x 0.085 x 0.556 = 0.193 W
P_LS = 2.02^2 x 0.040 x 0.444 = 0.072 W  ->  ~0.27 W conduction floor
```
Switching loss is **not published** in this datasheet, so double it as a rough allowance: ~0.5W. At RθJA 118.9°C/W that's ΔTJ ≈ 60°C - fine at 25°C ambient, tight in a closed tile at 45°C+. **Copper pour is the whole thermal story on this package.**

### Notes / gotchas
- **EN is GPIO14 push-pull with R38 100kΩ pulling down** - default off, correct. The research warned against push-pull EN, but that warning applies when a VIN-referenced UVLO divider is present and would be fought. There isn't one here, and a GPIO trivially overrides the 0.7µA internal pull-up. **Push-pull is fine as drawn.**
- **!firmware-note!** **Consequence: the big buck has no input UVLO at all.** If firmware asserts GPIO14 while PD+ is still ~5.7V, the buck runs in dropout into the LED chain. Nothing breaks, but it's a firmware sequencing responsibility - don't enable +5VP until PD reports ≥9V.
- **Overcurrent is hiccup, not a trip.** Cycle-by-cycle limiting first, then after tHIC_WAIT = 512 cycles (1.28ms at 400kHz) it shuts down and retries after 16384 cycles (41ms). A shorted submodule port therefore draws elevated current for ~1.3ms every ~41ms indefinitely. Relevant to whatever the firmware power budget thinks is happening.
- Inductor Isat 3A is chosen against the 2.47A *operating* peak, not the IC's 6A max current limit - so a hard output short saturates the inductor before the IC's limit trips. Normal trade-off, noted for the record. (See [picking the inductors](#picking-the-inductors-l2l3) - the part actually chosen is 4.57A worst case / 5.5A typ, which narrows this a lot without closing it.)

## Picking the inductors (L2/L3)

L2 and L3 have been **10µH with no footprint and no part number** since I drew them, which makes them the only thing on the board that hard-blocks a fab order. Everything else is at worst a respin risk; this is a "can't generate a BOM" problem. So: pick them properly.

### Identify
Both are 10µH. That number is [already settled above](#big-buck---tps54302-u6) and I'm not reopening it here - the research wanted 100µH on the clean buck and 15µH on the big one, and the answer was that DCM on a 300mA rail behind 44µF and an LDO is fine, and 100µH in a package that fits is a worse part. **This is a part-selection decision, not a value decision.**

What the maths already fixed:

| | L2 (clean buck U5) | L3 (big buck U6) |
| --- | --- | --- |
| Load | 150–300mA | up to 2A |
| Mode | DCM across the whole range | CCM |
| Peak current | ~0.77A | **2.47A** |
| Irms | ~0.3A | **2.02A** |
| Minimum spec | Isat ≥ 1A | **Isat ≥ 3A, Irms ≥ 2.5A** |

L3 is the one with a real spec. L2 could be almost anything.

#### the axis that actually matters
DCR, and specifically **DCR times 2.02² at worst case**, because the TPS54302 has **no exposed pad** - [RθJA is 118.9°C/W and copper pour is the entire thermal story](#big-buck---tps54302-u6). The inductor sits on that same pour. So its I²R isn't just an efficiency number, it's a second heat source next to a part that's already running ΔTJ ≈ 60°C at full load.

Worth being honest that **2A is a worst case, not the operating point.** The RGB chain at the datasheet-recommended brightness ceiling is ~500mA and the rest is submodule ports. At 500mA the difference between a 30mΩ part and a 105mΩ part is 19mW and nobody cares. The DCR row only earns its weight in the corner case - a fully-loaded tile in a closed case at 45°C ambient - which is exactly the condition this board is least characterised for.

#### the gates
Anything that fails these is out before scoring:
- **10µH ±20%**
- **Isat ≥ 3A, Irms ≥ 2.5A** (L3)
- **in stock at LCSC in real quantity** - this is going to JLC assembled now, so "orderable" means "orderable there"
- **shielded** - it's sat next to 30 analog hall sensors feeding a 12-bit ADC

34 parts in the JLC catalogue clear those gates at 10µH. Most are eliminated on size alone (the low-DCR end of the market is 13×12mm parts meant for 10A rails).

### Brainstorm (survivors)
All Isat/Irms figures below are **from the manufacturer datasheets, not LCSC's description field** - that field lists two bare current numbers with no labels and inconsistent ordering, which is a great way to design in a part with half the saturation current you thought.

| | part | LCSC | land | H | DCR max | Irms | Isat | stock | $ @vol |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **A** | APH0630T100M (APV) | C5349698 | 7.0×6.6 | **2.8** | 68mΩ | 3.91A | 4.57A | **59.2k** | $0.052 |
| **B** | PSPMAA0603-100M-ANF | C436542 | 7.1×6.6 | **3.0** | 105mΩ | 3.0A * | 7.0A * | 38.8k | $0.071 |
| **C** | PSPMAA0805-100M-ANP | C2962885 | 8.5×8.0 | 5.0 | 35mΩ | 6.0A * | 10.0A * | 7.6k | $0.199 |
| **D** | APH1040T100M (APV) | C5349715 | 11×10 | 3.8 | 30mΩ | 7.8A | 8.5A | 9.5k | $0.135 |
| **E** | XGL6060-103MEC (Coilcraft) | C3911721 | 6.7×6.5 | 6.1 | 20.4mΩ | 7.3A | 10.0A | 716 | $2.88 |

**\* typical only.** APV publishes worst-case *and* typical for both currents; PROD Tech publishes only typical. A and D are quoted at worst case above, so B and C are being flattered by roughly the same margin APV's own spread shows (~20%). Small thing, but it means B's headline 7.0A Isat isn't the same kind of number as A's 4.57A, and i'd rather compare honestly than let the part with the vaguer datasheet win a row.

What each costs you at Irms = 2.02A, and the resulting temperature rise (both makers define Irms as the current giving a **40°C rise**, so this scales as I²):

| | I²R @ 2.02A | temp rise | Isat vs the 2.47A peak | Isat vs the IC's 6A limit |
| --- | --- | --- | --- | --- |
| A | **0.28W** | 11°C | 1.85× | **4.57A - saturates first** |
| B | **0.43W** | 18°C | 2.8× * | 7.0A * - IC trips first |
| C | 0.14W | 4.5°C | 4.0× * | 10A * ✓ |
| D | 0.12W | 2.7°C | 3.4× | 8.5A ✓ |
| E | 0.08W | 3.1°C | 4.0× | 10A ✓ |

Two things fall out of building that table that i didn't expect:

1. **Below 8.5×8mm there is essentially no low-DCR part.** The whole 7×6.6 class sits at 60–105mΩ. The one exception is the Coilcraft (20.4mΩ in 6.7×6.5) and it costs **30× more** than everything else and there are 716 of them.
2. **Height is a real axis and i nearly missed it.** The PROD Tech series datasheet has one land pattern in six different heights - 6.6×7.1mm exists at 1.8/2.0/2.4/3.0/4.0/5.0mm. Low profile is only a *nice to have* in [form factor](../design-choices/form-factor.md), but taking 5mm instead of 3mm for a part i'm putting on a keyboard is a choice i should make on purpose rather than by not looking.

### Select

| Criteria | Weight | A | B | C | D | E |
| --- | :---: | :---: | :---: | :---: | :---: | :---: |
| Worst-case loss / heat on a shared pour | 9 | 6 | 3 | 9 | 9 | 10 |
| Sourcing (stock at LCSC) | 7 | 10 | 9 | 7 | 7 | 3 |
| Board area | 6 | 9 | 9 | 6 | 3 | 10 |
| Height | 6 | 9 | 9 | 4 | 6 | 2 |
| Isat headroom | 5 | 5 | 8 | 10 | 9 | 10 |
| Cost | 5 | 10 | 9 | 6 | 7 | 1 |
| Footprint already in KiCad | 3 | 10 | 3 | 3 | 10 | 10 |
| **Weighted Total** | | **337** | 292 | 279 | 294 | 268 |

**Winner: A - APH0630T100M (C5349698), 337/410 = 82%.**

It's not close, and the reason is that it isn't a compromise on anything except saturation current: against B - the part i'd have grabbed for being the best-stocked cheap one - it has **lower DCR (68 vs 105mΩ), higher Irms (4.5 vs 3.0A), more stock (59k vs 39k), a stock KiCad footprint, and it's cheaper.** That combination is unusual enough that i went back and re-read both datasheets to check i hadn't crossed a column. i hadn't.

**Where i was wrong going in:** i started this assuming the answer was "pay a bit more for a low-DCR part", and had picked out the 8.5×8×5.0mm 35mΩ one (C) before doing the table. C loses, and it loses on **height** - 5mm of z on a low-profile board to save 0.14W in a condition that happens rarely. The DCR row is genuinely weighted 9 and C genuinely wins it; it just isn't enough. The right part was the one that was better on six rows out of seven, and i'd have missed it by shopping on one axis.

#### the one thing A is worse at, said plainly
**Isat is 4.57A worst case (5.5A typ), below the TPS54302's 6A current limit**, so on a hard output short the inductor saturates before the IC's protection trips. B's 7.0A doesn't - though see the asterisk above about what kind of number that is.

I'm taking it anyway, and here's why it isn't the regression it looks like: the gotcha above was written assuming a **3A** Isat part, so this is a large improvement on what was already documented and accepted, not a new hole. Against the thing that actually happens - the 2.47A operating peak - there's 1.85× of margin. The short-circuit case is a soft failure: the IC hiccups (1.3ms on, 41ms off, indefinitely), and inductance falling 30% past the saturation point just makes current ramp faster inside that 1.3ms window. Nothing is destroyed.

And here's the useful property: **the schematic decision is the land pattern, not the part.** APV's datasheet shows APH0615 / 0618 / 0620 / 0624 / **0630** / 0640 / 0650 all sharing the *same* 2.35 × 3.50mm pad geometry - seven heights from 1.3mm to 4.8mm on one footprint. LCSC stocks three of them at 10µH:

| part | LCSC | H | DCR max | Irms | Isat | stock |
| --- | --- | --- | --- | --- | --- | --- |
| APH0624T100M | C19634013 | 2.2mm | 101mΩ | 2.51A | 3.32A | 1.5k |
| **APH0630T100M** | **C5349698** | **2.8mm** | **68mΩ** | **3.91A** | **4.57A** | **59.2k** |
| APH0650T100M | C5349687 | 4.8mm | 60mΩ | ~4.5A | ~5.3A | 0.8k |

So if the saturation trade ever looks wrong, or a batch goes out of stock, it's a **stuffing change, not a respin** - as long as the layout leaves 4.8mm of z-clearance over that footprint, which costs nothing to do now and can't be added later.

### the L2 question - one part or two?
L2 needs Isat ≥ 1A against a 0.77A peak, so almost anything works. Two ways to go:

| | separate part | reuse the L3 part |
| --- | --- | --- |
| L2 part | SWPA4030S100MT (C38117), 4×4×3.0mm | APH0630T100M (C5349698) |
| DCR | 130mΩ → 12mW at 300mA | 68mΩ → 6mW |
| Isat margin | 2.4A = 3.1× | 4.57A = 5.9× |
| Area | 16mm² | 47mm² (**+31mm²**) |
| Height | 3.0mm | **2.8mm - shorter** |
| Unit price | $0.063 | **$0.052** |
| BOM lines | 2 (two setup fees) | **1** |
| KiCad footprint | `L_Sunlord_SWPA4030S` ✓ | `L_APV_APH0630` ✓ |

**Reuse the L3 part.** The big inductor is *cheaper per unit than the small one*, has lower DCR, and is the same height - so the entire cost of sharing is **31mm² of board area**, about 0.3% of a tile, in exchange for one fewer BOM line and one fewer JLC setup fee. That's not a close call.

The escape hatch if placement gets tight: drop L2 to the SWPA4030S. It's a different footprint so it's a layout change, not a stuffing change - decide it before routing, not after.

### Revisit: flat beats wide, and that only changes one number

**Nothing about the analysis above is wrong. One weight was.** Height was scored at 6 because [form factor](../design-choices/form-factor.md) calls low profile a *nice to have*. It isn't - on a keyboard, z is the dimension the case has to swallow, and there is no version of this where 2.8mm and 1.8mm are the same to me. **Height goes to 9. Board area drops 6 → 3**, because area turned out to be the thing i had backwards:

> **i argued the inductor was too wide to fit, and that was nonsense.** The claim was that nothing over ~5.07mm fits outside a switch body, which is true and irrelevant - **U1 is a 10×10 QFN that overlaps switch bodies by 39.1mm², 32% of its own courtyard.** Everything on this board sits partly under a switch; that's the design. Area is a budget here, not a wall, and i'd promoted it to a wall.

So: same five candidates, same scores, two weights moved.

| Criteria | Weight | A `0630` | B | C | D | E |
| --- | :---: | :---: | :---: | :---: | :---: | :---: |
| Worst-case loss / heat on a shared pour | 9 | 6 | 3 | 9 | 9 | 10 |
| **Height** | **9** | 9 | 9 | 4 | 6 | 2 |
| Sourcing (stock at LCSC) | 7 | 10 | 9 | 7 | 7 | 3 |
| Isat headroom | 5 | 5 | 8 | 10 | 9 | 10 |
| Cost | 5 | 10 | 9 | 6 | 7 | 1 |
| **Board area** | **3** | 9 | 9 | 6 | 3 | 10 |
| Footprint already in KiCad | 3 | 10 | 3 | 3 | 10 | 10 |
| **Weighted Total** | | **337** | 292 | 273 | 303 | 244 |

**A still wins - 337/410 = 82%, the identical total it scored before.** That's a coincidence of the arithmetic, not a deep truth, but the useful result is real: re-weighting the axis i said i'd underrated **did not flip the answer**, because A was already joint-best on height.

Two things did move. **The runner-up changes from B to D** (303, up from 294) - D is the 8.5×8mm low-DCR part, and it gains because punishing height properly hurts it less than it hurts C. And **the margin narrows from 43 points to 34.** C, the low-DCR part i'd originally been drawn to, falls further to 273.

#### so the decision moves inside the family, not between candidates

The [land-pattern property](#the-one-thing-a-is-worse-at-said-plainly) is what actually pays off here. Seven heights, one 2.35 × 3.50mm footprint. Applying the **existing gates** (Isat ≥ 3A, Irms ≥ 2.5A) to the whole family:

| part | H | DCR | Isat | Irms | passes gates? |
| --- | :---: | ---: | ---: | ---: | :---: |
| APH0615 | 1.3mm | 175mΩ | 2.70A | 1.80A | ✗ both |
| APH0618 | 1.6mm | 155mΩ | 3.32A | 2.00A | ✗ Irms |
| APH0620 | 1.8mm | 145mΩ | 3.34A | **2.31A** | ✗ Irms |
| **APH0624** | **2.2mm** | **101mΩ** | **3.32A** | **2.51A** | **✓** |
| APH0630 *(as-built)* | 2.8mm | 68mΩ | 4.57A | 3.91A | ✓ |

**The gates do the work. APH0624 is the only part flatter than as-built that survives them** - 0.6mm off, one stuffing change, zero layout change.

**And i'm not relaxing the Irms gate to reach APH0620 at 1.8mm.** The true RMS load is ~1.7A, so 2.31A would be 1.36× and "fine" - but the gate came out of the research derivation, and [the last time i scored a requirement instead of gating on it](../design-choices/submodules.md#identify---and-the-mistake) i picked an option that didn't satisfy it. If 1.8mm turns out to be worth reopening, that's a deliberate re-derivation of the gate, not a nudge.

#### what 0.6mm costs

| | APH0630 | APH0624 | |
| --- | ---: | ---: | --- |
| height | 2.8mm | **2.2mm** | −21% |
| DCR | 68mΩ | 101mΩ | |
| loss at the 2.02A worst case | 0.277W | **0.412W** | **+0.135W onto the buck's pour** |
| Isat margin vs the 2.47A peak | 1.85× | **1.34×** | |
| Irms margin vs ~1.7A actual | 2.3× | 1.48× | |
| LCSC stock | 59,200 | **1,500** | **the real cost** |

**Stock is what makes this a genuine trade and not a free win.** 1,500 pieces at 2 per tile is 750 tiles - fine for me, thin for something other people are meant to build, and it's the same single-source shape already flagged on [the pogo connectors](../chips.md). The 0.135W is the honest engineering cost; the 1.5k is the one that would actually stop a build.

**Isat still isn't a regression against what's written down.** The [gotcha above](#big-buck---tps54302-u6) was authored assuming a **3A** part; 3.32A is still better than that. It just gives back most of the improvement A had over it.

#### result

**Both L2 and L3 → APH0624T100M, LCSC C19634013.** Same land pattern, so [the one-part-for-both reasoning](#the-l2-question---one-part-or-two) is untouched - still one BOM line, one setup fee, and L2 is still absurdly over-specced at 3.32A Isat against a 0.77A peak. Nothing about the layout changes.

Keep the **4.8mm z-clearance** anyway. It costs nothing and it's what makes APH0630 a stuffing-level fallback if the 1.5k stock evaporates - which, given the numbers above, is the escape hatch i actually expect to need.

**Still open:** the original brainstorm filtered 34 candidates with height weighted 6. With it at 9 the *catalogue* search deserves redoing - there may be a flat-and-wide part outside the APV family that beats this, since flat-and-high-current means bigger core area, and area is now cheap. That's a sourcing pass, not a blocker.

### To do
- [ ] **L2 = L3 = APH0624T100M**, LCSC **C19634013** - stuffing change from C5349698, same footprint `Inductor_SMD:L_APV_APH0630`
- [x] ~~L2 = L3 = APH0630T100M, LCSC C5349698~~ - superseded by the height re-weight above; footprint unchanged
- [ ] Re-run the catalogue search with height weighted 9, looking for flat-and-wide outside APV
- [ ] Second-source APH0624 or accept APH0630 as the stuffing fallback (1.5k stock)
- [x] LCSC / MPN / Manufacturer fields set to match the rest of the BOM - **the parts-without-sourcing count is now 41**, and what's left is the deliberate exclusions plus R30/R31
- [x] APH0630 datasheet pulled into `Refrences/datasheets/APH0630-10uH-inductor.pdf`
- [ ] Confirm at layout that both land patterns clear the buck's copper pour rather than eating it - the pour *is* the heatsink on this package
- [ ] Leave **4.8mm of z-clearance** over the footprint so the taller APH0650 stays a stuffing option
- [ ] **Place L2 and L3 apart, and rotate one 90° to the other** - see below

#### does using one part for both share noise?
No, not electrically - two separate inductors on two separate nets, the shared BOM line is a purchasing fact and nothing else. But it's the right question, because there *is* a coupling story here and it's worth writing down while i'm thinking about it:

- **The real shared paths are PD+ and the ground return**, and they exist whatever parts i pick. Both bucks chop current out of the same input node; whatever impedance is common to both is the coupling.
- **The two ICs beat against each other.** Each TPS54302 free-runs at 400kHz typ but 290–510kHz spread, unsynchronised, so the difference frequency can land anywhere from near-DC to 220kHz. That's a consequence of using two of the same IC, which was already the design.
- **Where sharing the part genuinely matters is magnetic coupling, and it's a placement effect.** Identical parts have identical cores and geometry, and the natural habit is to place identical parts in the same orientation - which is the orientation that *maximises* mutual inductance. Two mismatched parts would couple less, but only by accident. Rotating one 90° costs nothing and removes it deliberately.

The direction is what makes this worth caring about: L3 carries **0.938A p-p** of ripple for the LED rail, and L2 is the head of `+5VA → MAX40203 → BS+ → LDO → +3V3 → 30 hall sensors → ADC` - [the chain that isn't characterised end-to-end anywhere](#clean-buck---tps54302-u5). L3→L2 is the one coupling direction to actively design against.

The datasheet's answer is *"closed magnetic circuit design reduces leakage flux"* - metal-alloy molded core, which is genuinely the good construction for this. But **there's no leakage-flux number published**, only the adjective. So that's a reason to place carefully, not a reason to stop worrying, and it goes on the same list as the LDO's missing noise spec: things where the part is probably fine and the datasheet won't tell me so.

### Carry-forward
- **[chips](../chips.md)** needs a BOM line for the inductors; like the level shifter, they've never had one
- The [big buck gotcha](#big-buck---tps54302-u6) about Isat vs the IC current limit is updated above but the numbers in that bullet (3A) are now stale in a good way
- **The 43-parts-without-sourcing count drops to 41.** The rest are the deliberate exclusions (VoidSwitch, DNP, mechanical)

## 3V3 LDO - XC6220B331MR (U7)

### Goal
3.3V for MCU + hall sensors + mux, from **BS+** so it exists pre-PD.

### Datasheet refs
Torex XC6220. Output **factory-fixed** by the `331` code - no FB pin, nothing to tune. VIN abs max **6.5V**; VCE abs max 6.5V, VCEH 1.2–6.0V. Dropout 110mV max @ 1A. Current limit 1005mA min. PSRR 50dB @ 1kHz. **θJA = 166.67°C/W** (derived from the p.26 Pd-vs-Ta curve, self-consistent at both endpoints). Datasheet design ceiling TJ = 125°C, thermal shutdown 150°C typ.

### Math - dropout (not the constraint)
5.0 − 3.3 = **1.7V available** vs 110mV worst-case dropout at 1A → ~15× margin. Dropout is a non-issue.

### Math - thermal (this *is* the constraint)
```
Pd = (Vin - Vout) x Iout = 1.7 x Iout
TJ = Ta + Pd x 166.67
```
| Iout | Pd | TJ @ 25°C | TJ @ 45°C |
| --- | --- | --- | --- |
| 200mA | 0.34W | 82°C | 102°C |
| **250mA** | 0.425W | **96°C** | 116°C |
| 300mA | 0.51W | 110°C | 130°C ✗ |
| 400mA | 0.68W | **138°C** ✗ | 158°C ✗✗ |

**Safe steady-state ceiling is ~250mA at room ambient, and less inside a closed case.** The 400mA figure from the load budget puts it past its own 125°C design point and into thermal-shutdown territory.

### Result / parts (as-built)
VIN = BS+; **CE tied to VIN via R12 0Ω** (VCEH 1.2–6.0V, and CE must never float on the B-series - "open = undefined state"). ~~**C24 10µF in / C23 4.7µF out** - exactly the pairing Torex characterises for the 3.00–3.50V row. Plus **C41 100µF** bulk on BS+.~~ **As-built the board says C24 = 1µF, C23 = 4.7µF, and C41 is now 1µF on `+5VA` (U9's C_IN), not 100µF on BS+.** So the "exactly the pairing Torex characterises" claim is **not true as drawn** - confirm 1µF input is acceptable for the XC6220, or change one of the two. The C41 change is deliberate and good: see [attach inrush](comms.md#attach-inrush---the-10µf-problem).

### Notes / gotchas
- **This is why the comparator trip has a ceiling.** BS+ is pulled up toward the trip voltage by Q1 during the handoff, and BS+ is this part's VIN. VIN abs max is 6.5V, so the trip *must* stay below it. See the detector section - this single number is what makes the board's 5.73V right and the research's proposed 7.36V destructive.
- **Bank-gating the hall sensors is load-bearing, not an optimisation.** 30 sensors at 9mA worst case is 270mA on its own, before the MCU. That alone lands in the red row above. Cross-check against [keys](keys.md#sensor-bank-power-gating), where the other half of the problem is that the sensor's power-on settling time isn't specified.
- **No output noise specification exists in this datasheet.** Not a missing number I failed to find - there is no such row and no noise-density graph. The original [LDO selection](../design-choices/power.md#33v-ldo) scored "output noise" at weight 10, the heaviest row in that table. That row was scored against something unpublished. Doesn't change the pick, but the low-noise claim is currently unevidenced and the ADC chain is downstream of it.
- ~~C41 at 100µF is fine electrically but see [the footprint defect](#bulk-caps-and-the-footprint-defect).~~ **C41 is now 1µF on `+5VA` (U9's C_IN)** - it left BS+ entirely, which fixed the attach inrush *and* removed it from the footprint defect list.

## Ideal diode - LM66100 (U9)

### Goal
OR the clean buck's 5V onto shared BS+ with near-zero drop, blocking reverse current from BS+ back into the buck.

### What is it actually blocking?

Worth stating properly, because "OR-ing" undersells it and the answer is a rail-sequencing one.

Pre-PD, Q1 is on so BS+ ≈ VBUS ≈ 5V, Q2 is open so **PD+ is dead**, and U5's EN (from U11B) is low so the clean buck is off and `+5VA` is 0V. Without U9, BS+ has a route straight through the dead buck:

```
BS+ (5V) ──► +5VA ──► L2 ──► U5 SW node
                                  │
                     high-side FET body diode (anode SW, cathode VIN)
                                  ▼
                             U5 pin 3 = PD+
```

The TPS54302's high-side FET is N-channel with drain on VIN and source on SW, so its body diode conducts **SW → VIN**, and the low-side body diode (GND→SW) doesn't shunt it away. **Result: PD+ would sit at ~4.3V before PD has negotiated anything**, charging U6's input, the four per-side FET sources and all of PD+'s bulk from the USB port at attach.

So U9 blocks **the bootstrap rail backfeeding into the high-voltage rail, through the converter that is meant to be off.** The mirror case is covered by Q1 - post-PD its body diode (anode BS+, cathode VBUS) is reverse-biased at BS+ 5.05V vs VBUS 20V, so BS+ can't push back that way either.

**Honest note:** a plain Schottky would block this too. The *ideal* part buys ~0.4V of BS+ headroom and ~0.11W at 300mA, and **neither is load-bearing** - the LDO downstream has ~1.6V of headroom either way, and in the no-PD case BS+ comes from Q1 without passing through U9 at all. The reason the part exists is the blocking, not the drop. It stays an ideal diode because SC-70-6 is smaller and cheaper than an SMA Schottky, not because the drop matters.

### Re-select: MAX40203 → LM66100

The MAX40203 was replaced. Four reasons, and **none of them is current** - see below for why current was never the sizing driver.

| | MAX40203 (was) | **LM66100DCKT** (now) |
| --- | --- | --- |
| LCSC | C5668579 | **C2832141** |
| Price | $0.77 | **$0.17** |
| Stock | **879**, single listing | 1123 |
| Package | WLP-4, **0.35mm chip-scale** | **SC-70-6, leaded** |
| RON | ~260-375mΩ (52mV typ / 75mV max @ **200mA**) | **110mΩ max** @ 5V |
| IQ | 300nA | **150nA** |
| Current | 1A | 1.5A |
| Abs max | 6.0V | 6.0V (VIN, VOUT **and** CE) |

- **Stock was the trigger.** 879 units from one listing isn't a supply you build on.
- **The package is worth more than the money.** The note this section used to carry said the chip-scale part still needed a fab question answered - *"confirm the assembly tier places 0.35mm WLCSP, and what trace/space (and possibly via-in-pad) it forces on the stack-up. That may cost more than the part does."* **SC-70-6 deletes that question.**
- **It was never a low-drop part.** 52mV typ at 200mA is ~260mΩ - worse than the LM66100 it was replaced by, and nowhere near the "near-zero drop" the old goal line claimed.
- **The quiescent-current argument survives, inverted.** MAX40203 was picked over MAX40200 specifically on **300nA vs 7µA**, "the right call when many tiles idle on a shared always-on bus." LM66100 is **150nA** - it doesn't just meet that criterion, it beats the incumbent by 2×.

**Current was never the sizing driver**, which is worth writing down because it nearly sent this the wrong way. U9 only carries current *post*-PD, when it feeds the LDO (~300mA). Pre-PD, BS+ comes from **Q1** (AO3401A, ~4A) and U9 is reverse-blocking, carrying nothing. So the submodule load never passes through it and 1A was never a constraint.

### Result / parts (as-built)

| pin | net | note |
| --- | --- | --- |
| 1 VIN | `+5VA` | **C41 1µF** local (datasheet §10 C_IN) |
| 2 GND | GND | |
| 3 CE | **BS+** via **R15 0Ω** | §8.3.2 Always-ON RCB: *"By connecting the CE pin to VOUT, this allows the comparator to detect reverse current flow."* |
| 4 N/C | GND | *"can be tied to GND or left floating"* |
| 5 ST | **R83 100kΩ → +3V3**, and `BS+ SRC` to a GPIO | open-drain status |
| 6 VOUT | BS+ | |

**CE→VOUT is the trap, and getting it wrong fails silently.** Active-low CE tied to **GND** does not disable the part - it enables it as a plain load switch with **no reverse current blocking at all**, so BS+ backfeeds through the dead buck into PD+ exactly as described above, while everything *appears* to work because BS+ is still live and the LDO still runs. That's the worst shape of failure this design can have. CE goes to VOUT.

**Don't copy TI's pull-up rail.** Figure 14 pulls R_ST to VOUT because their logic sits at VOUT level; here VOUT is BS+ at ~5V and RP2350 GPIO abs max is IOVDD+0.3 = **3.6V**. ST is open-drain so the pull-up rail sets the logic level for free - **+3V3, not VOUT**.

### `BS+ SRC` - what the status pin buys

ST is low when the device is disabled, Hi-Z when enabled. In RCB mode that means:

- **ST low** → reverse-blocking → `+5VA` is *not* feeding BS+ → running off VBUS through Q1 (pre-PD)
- **ST high** → conducting → the clean buck is feeding BS+ (post-PD)

That's a **hardware readout of which side of the handoff BS+ is on**, on a board where four sessions went into cold-start bring-up bugs. It also turned out to be the safety interlock for the submodule power question - see [submodules](../design-choices/submodules.md).

Name it `BS+ SRC`, not "BS+ Sense" - it reports *source selection*, not a voltage, and "sense" invites someone to read it as an analog rail measurement.

### Accepted risk: 5.95V on a 6.0V part

**This is deliberate, not an open item.** BS+ tracks VBUS until Q1 opens, so BS+max = the comparator's UTP = **5.95V**, against LM66100's **6.0V** abs max and 5.5V *operating* max. 50mV of margin, on three pins (VIN, VOUT, CE).

It can't be designed out, and the arithmetic is what makes that certain:

```
LTP ≥ 5.68V      (must clear vSafe5V's 5.5V ceiling + the ±157mV error budget)
UTP > LTP        (that's what hysteresis means)
∴ UTP > 5.68V > 5.5V
```

**UTP can never be below 5.5V while LTP is above it.** No divider or hysteresis tuning fixes that - the two constraints point in opposite directions. And nothing external helps either:

- **Series element:** in the 5.95V state no current flows through U9, so a series element drops nothing. In the state where current *does* flow it drops voltage in the direction you care about.
- **Shunt clamp:** the window between "highest legitimate BS+" (5.95V) and abs max (6.0V) is **50mV**. No zener or TVS discriminates at 50mV; tolerance alone is ±5%.

**Why it's acceptable:** 5.95V is *inside* the 6.0V abs max, the exposure is a few ms during the PD ramp, and C45's gate soft-start on Q1 limits di/dt so inductive overshoot is damped. The residual risk is ringing pushing past 6.0V - real, but small.

**The alternative, if this ever needs closing:** only a >6V part fixes it. `TPS2120` (C1850326, 2.8-22V, 3A, 62mΩ, DSBGA-20 1.5×2mm, $1.23) or `LM74800Q` (C3215600, 3-65V, controller + external FET). TPS2120's footprint is actually *smaller* than SC-70-6, but it puts you back in chip-scale - which is the thing the swap was partly done to escape.

### Notes / gotchas
- **Reverse blocking turns off at ~26mV of reverse bias** with sub-µA leakage at 125°C - the behaviour the whole hotplug-safe OR-ing scheme depends on, and well characterised.
- **The handoff dip is real and bounded.** `VON = -80mV` worst case means U9 only conducts once VOUT falls 80mV below VIN. At the trip BS+ is ~5.93V and +5VA is 5.08V, so U9 stays off until Q1 opens and BS+ droops to ~5.00V. With C24's **1µF** (as-built, not the 10µF this page used to claim) and ~300mA of LDO load that takes **~3.1µs**, and the LDO has ~1.6V of headroom - nothing notices. This is the number behind [checklist §3](../schematic-checklist.md)'s "hold-up caps on bootstrap to cover the µs comparator→buck handoff."
- **No chatter.** Steady-state drop once conducting is `I × RON` = **33mV at 300mA**, and VOFF's window is 0-80mV *positive*, so the operating point sits inside the hysteresis band.
- The old symbol was `Analog_Switch:MAX40200ANS` with a `MAX40203` Value. **The BOM pulls Value**, so symbol, footprint, Value and LCSC all have to move together.

## Reference - TLV431 (U10)

### Goal
Stable 1.24V for the detector to compare against, alive the instant VBUS exists.

### Math - bias resistor (R21 = 20kΩ from VBUS)
```
IK(5V)  = (5 - 1.24)/20k  = 188 uA
IK(20V) = (20 - 1.24)/20k = 938 uA
P(20V)  = 938u^2 x 20k    = 17.6 mW   (28% of a 0402's ~62.5mW)
```
The floor that matters is **IK(min) = 80µA MAX** for C/I grade (the front-page "80µA typical" is misleading - Table 5.5 is 55 typ / 80 max). 188µA is **2.35×** that max at the worst-case low supply. ✓

The research proposed 24kΩ (157µA, 1.96×). 20kΩ is the better of the two - more regulation margin for 3mW more dissipation.

### Notes / gotchas
- **VKA absolute max is 7V against a rail that reaches 20V.** R21 is the only thing standing between this part and destruction. Any rework or BOM change that shorts or removes it kills the reference. Worth a note on the schematic.
- **Biased from VBUS, not +3V3** - this was [snag 2](implementation.md#snags-round-2---cold-start-bring-up-a-second-review-pass-caught-these) and it's the whole reason the detector doesn't latch off at cold start.
- **C37 = 1nF on the cathode is the one thing here I'd question.** The datasheet default is *no* cathode capacitor ("internally compensated to be stable without an output capacitor"), and Figure 5-18 maps an unstable band at VKA=VREF spanning roughly **6nF to 400nF**. 1nF sits below that band, so it should be stable - **but those boundaries are read visually off a log-log plot and are only good to about a factor of 2.** 1nF is within ~6× of an estimated edge. Cheapest resolution: make C37 a DNP footprint and leave it unpopulated, which is what the datasheet actually recommends. If it stays, it's worth a scope check for oscillation on +1V24ref at both 5V and 20V.
- R27 (0Ω) straps REF→cathode for the plain 1.24V two-terminal config; R28 is a DNP footprint for a future divider. In this config REF can't float, so the "REF needs ≥0.5µA" requirement is satisfied automatically.

## Threshold detector - LM2903 (U11)

### Goal
Decide "VBUS is still vSafe5V" vs "VBUS has been negotiated up", entirely in hardware, and drive three things: Q2's gate, Q3's base, and a clean 3.3V buck enable.

### Datasheet refs
TI SLCS005AH. Supply 2–30V (non-B) - covers 5–20V from VBUS directly. **Output is open-drain NPN**, and its abs max (36V) is **independent of VCC** - which is what legally lets one channel's output ride VBUS while the other rides 3V3. VIO 15mV max full-range (non-B). IIB 500nA max. Response 0.3–1.3µs (irrelevant here, ~1000× faster than anything this does).

### Math - divider and trip

**R30 35.7kΩ / R31 10kΩ** off VBUS (both ±0.1%), hysteresis from **R22 5.1kΩ** and **R46 1MΩ**:

```
k = R31/(R30+R31) = 10 / 45.7 = 0.21882          divider ratio
f = R22/(R22+R46) = 5.1k / 1.0051M = 0.005074     feedback fraction
```

Hysteresis is on the **reference** side, not the divider side - R22 from the +1V24 ref to U11A's + input, R46 from U11A's output back to that node:

```
out LOW   ->  V+ = 1.24(1-f) + 0.1·f      = 1.23422 V
out HIGH  ->  V+ = 1.23371 + f·VBUS

falling (out LOW):   k·V = 1.23422            ->  LTP = 5.640 V
rising  (out HIGH):  k·V = 1.23371 + f·V      ->  UTP = 1.23371/(k-f) = 5.772 V
band = 132 mV
```

### Result
**LTP ≈ 5.640V, UTP ≈ 5.772V, band ≈ 132mV.**

### The margin question (read this one)

Two ceilings bracket this trip, and **they are not symmetric** - which is the thing the original design got backwards:

| Bound | Value | What happens if exceeded |
| --- | --- | --- |
| vSafe5V max (USB-C) | **5.5V** | trips early: Q1 opens, Q2 closes, PD+ = 5.5V, clean buck enables into dropout, LDO still has 2V of headroom. **Degrades gracefully** |
| **LM66100 abs max (any pin to GND)** | **6.0V** | BS+ peaks at UTP because Q1 holds it there until the trip. **Damaged part** |

**So margin belongs on the 6.0V side.** The old 44.2k/12.2k put 181mV on the graceful side and **52mV on the destructive one** - the protection was piled on the failure that doesn't matter.

| | LTP | UTP | vs 5.5V | vs 6.0V | band |
| --- | :---: | :---: | :---: | :---: | :---: |
| ~~44.2k / 12.2k, R22 10k~~ | 5.681 | 5.948 | 181mV | **52mV** | 267mV |
| 35.7k / 10k, R22 10k | 5.615 | 5.877 | 115mV | 123mV | 261mV |
| **35.7k / 10k, R22 5.1k** | **5.640** | **5.772** | **140mV** | **228mV** | **132mV** |

Two changes got there, and **the second one is the bigger lever**:

1. **Re-centre the divider.** `12.2kΩ does not exist` - it isn't an E-series value (E96 has 12.1k and 12.4k), so the old BOM line was unbuyable in any package or tolerance. 35.7k/10k is the nearest pair that both exists in ±0.1% *and* moves the band toward the middle of the window.
2. **Narrow the hysteresis.** The 267mV band was eating over half the 500mV window between the two limits. This page previously only considered *widening* it (and correctly concluded there was no room) - **narrowing buys margin on both sides at once**, and it's one resistor. Reducing R22 rather than raising R46 also halves the reference-side source impedance, which cuts the IIB term.

### Error budget

With TLV431B (±0.5%) fitted and ±0.1% divider resistors:

| Source | On the trip point |
| --- | --- |
| **LM2903 VIO 15mV ÷ k** | **±68.6mV** |
| TLV431B VREF ±0.5% ÷ k | ±28.3mV |
| IIB 500nA × (35.7k‖10k = 7.81k) ÷ k | ±17.9mV |
| IIB 500nA × (R22‖R46 = 5.07k) ÷ k | ±11.6mV |
| R30/R31 at ±0.1% | ±5.6mV |
| **RSS** | **±77mV** |
| **linear worst case** | **±132mV** |

```
LTP worst (linear)  5.640 - 0.132 = 5.508 V   ✓ above 5.5
UTP worst (linear)  5.772 + 0.132 = 5.904 V   ✓ below 6.0
```

**Both limits hold even at linear worst case**, where the old values blew through both - the UTP one being an abs-max violation, i.e. a damaged part rather than a mis-sequence. That was the real defect here, and it's closed.

**VIO is now the dominant term** - ±68.6mV of the ±77mV RSS. Tightening resistors further buys nothing (±0.1% contributes ±5.6mV), so **don't spend money on ±0.05% parts.** If this ever needs more margin it wants a lower-offset comparator, not better passives.

### Parts

| Ref | Value | LCSC | Stock | Note |
| --- | --- | --- | --- | --- |
| R30 | 35.7kΩ ±0.1% ±25ppm | `ARG02BTC3572` **C2681604** | 8,000 | |
| R31 | 10kΩ ±0.1% ±25ppm | `ARG02BTC1002` **C2902636** | 20,585 | same family |
| R22 | **5.1kΩ ±1%** | `0402WGF5101TCE` **C25905** | **11.0M**, **Basic** | was 10kΩ. E24 not E96 deliberately - R22 only sets the hysteresis fraction, so a ±1% part moves UTP by **1.4mV**. The E96 4.99k equivalent is Extended and would add a $3 setup fee for nothing |
| R46 | 1MΩ | *(unchanged)* | | |

Divider current at 20V is 438µA (was 355µA) and R30 dissipates 6.8mW against a 62.5mW 0402 rating - both non-issues.

**U11B's trip moves too**, from 5.732V to `1.24/k = 5.667V`. It has no hysteresis and only enables the clean buck, which can't regulate below ~7-9V in anyway, so it sits in dropout either side of that number. No consequence.

### Notes / gotchas
- **VCC = VBUS (pin 8).** Powered from a node its own outputs cannot switch off. This is the fix for [the comparator-eats-its-own-tail snag](implementation.md#snags-what-bit-me) and it's the single most important topological property on this sheet.
- **U11B has no hysteresis** - it taps the raw +1V24ref (pin 6) while U11A taps the R22/R46 node. So the buck enable trips at a hard 5.732V in both directions and can in principle chatter right at the threshold. In practice VBUS ramps monotonically through it during negotiation and the buck's own 5ms soft-start swamps any dither, so this is deliberate and fine - but if `+5VA EN` is ever seen oscillating, this is why.
- **Where the research was wrong, and why.** It derived a 7.36V trip with 47k/10k + 200k hysteresis, and on comparator grounds alone that's a better design - 1.08V of margin to vSafe5V instead of 180mV. But it only ever saw the LM2903 and TLV431. It couldn't know that **BS+ is dragged to the trip voltage by Q1 during the handoff, and BS+ feeds an LDO with a 6.5V absolute maximum.** A 7.36V trip would put 7.36V on a 6.5V part. The board's 5.73V is correct and the research isn't - a good reminder that a per-chip read can't see a system constraint that lives two parts away.

## Q1 - VBUS→BS+ switch (AO3401)

### Goal
Feed BS+ from raw VBUS below the trip. **Default ON with no drive present** (this is what lets a cold tile get its first 5V), fully OFF above the trip.

### Math - the off-state divider (the session-3 fix)
Gate is pulled to GND by **R35 1MΩ** and pulled to VBUS by Q3 through **R36 10kΩ**:
```
Vgate(off) = VBUS x 1M/(1M + 10k) = 0.990 x VBUS
Vgs(off)   = -0.0099 x VBUS = -0.20 V at VBUS = 20V
```
Vgs(th) min is −0.5V, so −0.20V is a clean off with 2.5× margin. **This is why R35 went 100k→1M** - at 100k the divider gave 0.909×VBUS → Vgs ≈ −1.8V, past the −1.5V worst-case threshold, and Q1 leaked VBUS into BS+.

### Math - on-state
At VBUS = 5V, gate at GND via R35: **Vgs = −5V**, against Vgs(th) max −1.5V (worst of the two conflicting AO3401A datasheets) → 3.5V of overdrive ✓. RDS(on) at that overdrive ≈ 75mΩ max (clone sheet). At 1.5A: P = 169mW.

### Notes / gotchas
- **Vgs abs max is ±12V and Q1 only ever conducts below ~6V**, so in normal operation Vgs never exceeds −5.95V. No clamp needed. ✓
- **The single-fault case is worth a cheap zener though.** If Q3 loses base drive (open R33, failed Q3) while VBUS is at 20V, R35 pulls the gate to GND and Vgs = −20V, well past ±12V. A BZX84C10 gate-source clamp costs about a cent and closes that off. Q2 already has one (D4); Q1 doesn't. **Recommend adding it.**
- C45 (1nF, gate→BS+) is Miller soft-start on the drain.
- The two AO3401A datasheets in the folder **disagree** (Vgs(th) max −1.3V vs −1.5V, RDS(on) 50 vs 65mΩ, IDM −27A vs −19A). LCSC doesn't guarantee which die you get, so everything above uses the worse number of the pair.

## Q2/Q3/D4 - VBUS→PD+ switch (AO4407A + BC857 + BZX84C10)

### Goal
Connect VBUS to the HV rail above the trip. Default OFF. Carries full port current, up to ~4A at 20V under the 80% rule.

### Math - gate drive
U11A's open-drain output sinks node X (shared by R29/R32/R33/R46). **R32 100kΩ** pulls node X to VBUS; **R29 10kΩ** sits between node X and Q2's gate.

Off (U11A released): node X → VBUS, Vgs ≈ 0 ✓
On (U11A sinking): node X → ~0.1V, so Vgs → −VBUS, clamped by D4.

**D4 BZX84C10** (anode at gate, cathode at VBUS) clamps Vgs at **−9.4 to −10.6V**. Against AO4407A's ±25V abs max that's enormous margin - the clamp isn't strictly needed on this FET (unlike the AO3401A positions) but it costs nothing and bounds the gate drive.

Sink current with the zener conducting at VBUS = 20V:
```
through R29: (20 - 10.6 - 0.1)/10k = 0.93 mA
through R32: (20 - 0.1)/100k       = 0.20 mA
total ~1.13 mA   vs LM2903 IOL 6mA min  ->  fine
```

RDS(on) at Vgs = −10V is 13mΩ max. At 4A: **P = 208mW** in SOIC-8. Comfortable.

### Math - soft-start
**C44 = 100nF gate→drain** (Miller), with R29 10kΩ:
```
tau = 10k x 100n = 1 ms   ->  PD+ ramps over roughly 1-3 ms
```
That's a genuine soft-start into the downstream bulk, and it matters because USB caps a sink at 10µF at the connector before attach - everything bigger has to come up behind a controlled ramp.

> **Doc correction:** [implementation](implementation.md) says "C44 + C45, 1nF each". As-built **C44 is 100nF** (C45 is 1nF). The 100nF is the better value - 1nF would give a 10µs ramp, which is nearly a hard switch into the PD+ bulk. Board wins; the older note is stale.

### Q3 (BC857 PNP)
Emitter at VBUS, base pulled to VBUS by **R47 100kΩ**, driven from node X through **R33 10kΩ**. When U11A sinks node X:
```
Ib = (20 - 0.7 - 0.1)/10k = 1.92 mA,  hFE min 125  ->  Ic capability 240 mA
```
Vastly more than the ~20µA needed to hold Q1's gate up through R36. R47 is the leakage/deterministic-off path added in session 4.

## HV per-side switches - picking the FET

Four per-edge switches plus NPN level-shifters, per [checklist §3](../schematic-checklist.md). **Nothing is drawn yet**, so this is a design decision, not an as-built. The gate-drive topology and passive values already exist in [the FET research](../research/fet-switching-and-gate-drive.md) (§ "Switches 3–6") - what was missing was the FET itself, because the FET couldn't be sized until the per-edge current budget existed. It does now.

### Identify

The research left this hanging with an explicit question: *"does any single edge realistically carry the full 4-5A ceiling continuously, or is that ceiling a shared/rare/transient case?"* - and called it **"the single biggest lever"** on whether SOT-23 works here. That 4-5A number was inherited from the old "80% of a 5A USB port" framing and was never a per-edge number at all.

[The connector decision](../design-choices/module-connectors.md#revisit-i-picked-a-real-connector-and-it-killed-the-custom-cutout-idea) settles it. Each edge is **4× 1A PD+ contacts and 4× 1A GND contacts**, so:

| | value | where from |
| --- | --- | --- |
| Hard ceiling per side | **4A** | 4 HV contacts × 1A, the connector's own rating |
| Design target, continuous | **≥2A** | 50% derate on the contacts - and what i actually want to guarantee |
| What 2A buys at 9V (the default) | 18W ≈ **3.6 tiles downstream** | ~5W/tile |
| What 2A buys at 20V | 40W ≈ **8 tiles downstream** | same |
| Realistic single-tile draw | 0.25A @20V → **0.56A @9V** | ~5W/tile |

So the switch has to do **2A continuous without complaint**, and ideally shouldn't be the thing that dies first if someone somehow pushes the connector to its full 4A. That second half matters more than it looks: if the FET fails below the connector rating then the FET is the weak link, and firmware OCP stops being *protection* and starts being *the only thing preventing a fire*.

### The axis i nearly got wrong

I'd been carrying "AO3401A is fine at 1–2A" from the research, which is true as far as it goes - but it's true **at the datasheet's RθJA**, and that figure is measured on a **1 in², 2oz copper reference board** (`AO3401A-pfet.pdf` p.1, Note A/D). There are four of these sitting at the board edges, in the same region the connectors and the key field are already fighting over. Nobody is giving each of them a square inch.

Redoing it honestly, using the worse of the two conflicting AO3401A sheets (65mΩ at Vgs=−10V) and iterating for RDS(on) tempco (~+0.5%/°C, so the number you start with isn't the number you end at):

| RθJA | what that assumes | Tj @ Ta 25°C | Tj @ Ta 40°C |
| --- | --- | :---: | :---: |
| 125°C/W | the datasheet's 1 in² reference board | 63°C | 78°C |
| **200°C/W** | **realistic edge copper, 4 parts sharing it** | **95°C** | **110°C** |

110°C against a 150°C limit is 73% of the way there, with RDS(on) already ~35% above its cold value, in a keyboard that has 30 RGB LEDs in it. That's not a failure, but it's not headroom either.

And at the connector's full 4A it doesn't converge at all - 1.04W cold in a SOT-23 drives Tj up, which drives RDS(on) up, which drives Tj up. **AO3401A cannot survive what the connector can deliver.**

### Brainstorm

First: is there just a better SOT-23? I went through every 30V P-FET in SOT-23 in the JLC catalogue. They land between 47mΩ and 350mΩ, and **AO3401A (C15127, 47mΩ@10V) is at the good end of that and is the only Basic part in the class**. There is no drop-in upgrade - the package is the limit, not the part.

| | option | package | RDS(on) | LCSC | $/tile (×4) |
| --- | --- | --- | --- | --- | --- |
| A | AO3401A ×4 - status quo | SOT-23 | 47mΩ@10V (65mΩ worst sheet) | C15127, **Basic** | $0.14 |
| B | **AO4407A ×4 - reuse Q2's part** | SOP-8 | 9.5mΩ@10V (13mΩ conservative) | C2841482 | $0.40 |
| C | 2× AO3401A paralleled per edge | SOT-23 ×8 | ~32mΩ effective | C15127, Basic | $0.28 |
| D | TPS1663 eFuse ×4 | SOIC-8 | integrated | TI | ~$6 |

Option D is the one that lost the [original discrete-vs-eFuse call](../design-choices/power.md#hv-per-side-switches-4-per-tile) on cost. It's in the table because the thing that made it lose (cost) hasn't changed, but the thing it was better at (OCP, soft-start, SOA) is exactly what's under review - so it deserves to be re-scored rather than assumed dead. Scored structurally from the earlier entry, not from a fresh datasheet read.

### Select

| Criteria | Weight | A: AO3401A | B: AO4407A | C: 2× parallel | D: TPS1663 |
| --- | :---: | :---: | :---: | :---: | :---: |
| Thermal headroom at 2A continuous | 9 | 4 | 10 | 7 | 9 |
| Survives the connector's full 4A | 8 | 1 | 10 | 7 | 6 |
| Vgs margin - not zener-dependent to survive | 8 | 2 | 9 | 2 | 10 |
| Board area at the edge | 6 | 9 | 5 | 6 | 5 |
| Cost + BOM lines | 5 | 10 | 8 | 7 | 2 |
| SOA margin during the soft-start ramp | 6 | 3 | 8 | 5 | 10 |
| Stock / sourcing | 4 | 10 | 8 | 10 | 5 |
| **Weighted total** | | 222 | **392** | 276 | 329 |

**Winner: AO4407A ×4 (392 / 460, 85.2%)** - the part already sitting at Q2.

### Result

**Q4–Q7 = AO4407A (C2841482), SOP-8**, same LCSC part as Q2.

Thermals, at the conservative 13mΩ and SOP-8's ~62°C/W:

| current | P | Tj @ Ta 25°C |
| --- | --- | :---: |
| 2A (design target) | 0.052W | **28°C** |
| 4A (connector ceiling) | 0.21W | **38°C** |
| 8A (double the connector) | 0.83W | 77°C |

It doesn't just clear 2A, it clears the connector's entire rating without ever becoming the limiting element. **The connector is now the limit, which is the correct way round.** Drop across the switch at 2A falls from ~176mV to **26mV** as a bonus - irrelevant even on the 9V rail, but it's free.

Three things fall out of this that are worth more than the thermal margin:

- **It costs $0.26/tile and zero BOM lines.** 4× $0.099 vs 4× $0.035, and Q2 is already this exact LCSC part, so there's no new reel and no new extended-part setup fee.
- **The ±12V gate problem disappears.** The research called AO3401A's ±12V Vgs abs max against a 20V source **"the single sharpest edge in this whole design"** - every AO3401A position is safe *only* because of its zener, and "remove or misconnect it and the very first PD negotiation above ~12V destroys the gate oxide." AO4407A is ±25V and has 5V of margin unclamped. **The 4× BZX84C10 go from mandatory to margin.** I'm keeping them anyway (they're a cent and the clamp resistor is already there for the pull-up), but they stop being load-bearing, and that's the difference between a design that survives a misplaced part and one that doesn't.
- **The unresolved SOA question gets much more room.** The soft-start ramp puts a computed **38.7W** instantaneous peak through the FET, which the research flagged as unverifiable from text extraction and said had to be checked against the SOA graph before R_soft/C_soft could be called final. That's a very different conversation in SOP-8 than in SOT-23.

### Gate drive - the research's values are backwards

The [FET research](../research/fet-switching-and-gate-drive.md) specifies `R_pu(Gate–Source) = 39kΩ` with `R_soft = 470kΩ` between the NPN collector and the gate. **Drawn as written, the switch never turns on.**

With the NPN saturated, R_pu and R_soft form a divider on the gate node:

```
V_gate = PD+ x R_soft/(R_pu + R_soft) = PD+ x 470/509 = 0.923 x PD+
Vgs    = V_gate - PD+ = -0.077 x PD+
```

| PD+ | Vgs | vs AO4407A Vgs(th) ~-1.8V |
| --- | --- | --- |
| 9V (the default) | **-0.69V** | **nowhere near - hard off** |
| 20V | -1.53V | marginal at best |

The ratio is inverted: **R_pu must be much larger than R_soft**, not smaller. The research computed the zener current as `(20 - 10.6)/39k`, which assumes the gate actually reaches the clamp - it can't, with 470k in the path to ground. The two halves of that note were never reconciled.

#### Corrected values

Want Vgs ≥ 95% of PD+, and a ~1ms output ramp.

```
Vgs/PD+ = R_pu/(R_pu + R_soft)          ->  R_pu ~ 20x R_soft
tau_on  = (R_pu || R_soft) x C_soft ~ R_soft x C_soft
t_ramp  ~ 2.2 x tau_on
```

| | value | why |
| --- | --- | --- |
| **R_pu** (gate→source) | **100kΩ** | ratio 100/104.7 = **0.955** |
| **R_soft** (NPN collector→gate) | **4.7kΩ** | τ_on = 4.49k × 100n = 0.45ms → **t_ramp ≈ 1ms** |
| **C_soft** (gate→source) | **100nF** | 48× the AO4407A's ~2.1nF Ciss, so the ramp is component-set, not process-set |
| **Rb** (GPIO→base) | **10kΩ** | Ib ≈ 253µA; BC847B hFE min 110 → 28mA capability vs 4.3mA peak needed |
| **Rbe** (base→GND) | **100kΩ** | deterministic off. BC847 ICBO ≤0.1µA × 100k = 10mV, far below Vbe. Matches R47's role on Q3 |

Resulting Vgs = **−0.955 × PD+**: **−8.6V at 9V** (AO4407A specs 9.5mΩ at −10V, so ~10.3mΩ here - no penalty) and **−19.1V at 20V**, which is **76% of the ±25V** abs max.

Sanity on the ramp target: the downstream tile presents roughly 54µF of PD+ bulk, so `I = C·dV/dt = 54µ × 9/1ms ≈ **0.5A** inrush`. That's the number the soft-start exists to produce.

Quiescent draw while a switch is on is `PD+/(R_pu + R_soft)` = **86µA at 9V**, 191µA at 20V. ×4 edges that's 0.34–0.76mA, nothing against 270mA of sensors.

#### Dropping the BZX84C10 clamps

**Cutting all four.** Two reasons, and the second is the one that decides it:

- AO4407A is **±25V**, so the clamp was already downgraded from mandatory to margin when the FET changed. Unclamped worst case is −19.1V, 76% of rating.
- **At the 9V default, Vgs is −8.6V — 35% of rating.** The clamp only does anything in the 20V case, which is already behind an explicit firmware flag and a "don't hot-unplug" warning. Spending **~32mm²** to protect a mode the user has to deliberately opt into, on a board where footprints are the binding constraint, is a bad trade.

#### Open: turn-off is structurally ~20× slower than turn-on

Turn-off discharges C_soft through R_pu alone: `τ_off = 100k × 100n = 10ms`, and since the on-ratio *requires* R_pu ≈ 20 × R_soft, **that asymmetry can't be tuned out** — it's inherent to the topology. A parallel diode across R_pu would fix it and also short out R_pu in the on-state, so that's not available either.

Estimated consequence: the FET spends ~11ms traversing its linear region, peaking near `I × V/4 ≈ 4.5W` at 2A/9V. Against SOP-8's ~5–15°C/W *transient* thermal impedance at 10ms that's a 20–70°C rise - survivable, and there's no fast-trip requirement left now that [OCP is gone](../design-choices/power.md#re-decision-does-this-need-per-edge-ocp-at-all). **Recorded as accepted, not verified** - confirming it properly needs the SOA curve, which is graphical.

### The body diode - an open switch only blocks *outbound*

This isn't specific to the AO4407A, it's true of every MOSFET, and it changes what "boundary switches stay open" actually buys. Writing it down because [power design-choice](../design-choices/power.md#per-side-control) reads as though an open switch isolates in both directions, and it doesn't.

Every MOSFET carries an intrinsic **body diode**: the die sits on a substrate (the body), the body–drain junction is a PN diode, and in a discrete part the body is internally shorted to the source so it can't float. That leaves a permanent diode across source–drain that **the gate has no control over**. For a P-channel (N body, P+ source/drain) the junction is N-to-P, so it sits **anode at drain, cathode at source**:

```
         ┌──────────┐
PD+ ─────┤ S      D ├───── HV_edge
         │    ◄─────┼─── body diode: anode D, cathode S
         └────┬─────┘
              G
```

Turning the gate off stops the *channel*. The diode keeps blocking PD+ → HV_edge (correct - the supply can't reach the load) and keeps conducting HV_edge → PD+ whenever the edge sits ~0.7V above the local rail.

Both tiles at a joint have identical parts wired identically, so both anodes land on the shared edge net:

| A's switch | B's switch | what happens |
| --- | --- | --- |
| off | off | **nothing flows.** Both anodes are on HV_edge, nothing drives it, the diodes oppose - the net floats ✓ |
| on | off | **A powers B through B's body diode**, bypassing B's open switch. B drops ~0.7V and dissipates ~0.39W in its own diode at 0.56A |
| on | on | normal - the 13mΩ channel shunts the diode entirely |

**So the partitioning works, but cooperatively.** It needs *both* sides of a boundary open. A tile cannot unilaterally refuse power from a neighbour that has decided to send it. Two sources at different voltages still can't fight, because that case has both boundary switches open - but the mechanism is "both agreed", not "either one can veto".

**Not fixing it.** True bidirectional blocking needs two FETs back-to-back (common-source, diodes opposing) - that's what battery protection and reverse-blocking load switches do. Here it'd cost 4 more AO4407A (~$0.40/tile) plus a gate drive referenced to a floating shared source, to defend against a case that only arises if firmware enables a switch toward a differently-powered region. That's a topology bug, not a hardware hazard. **Documented rather than designed around.**

Two things it *does* oblige:

- **!firmware-note!** **Firmware must turn an edge switch OFF when the neighbour disappears.** If an edge is left enabled after a tile is yanked, plugging a new tile in there is a **hard hot-insert**: the new tile's PD+ bulk charges through its own body diode with no soft-start anywhere in the path, because the sender's ramp finished long ago. The intended sequence (switches default OFF → detect neighbour on the Rx line → *then* enable with soft-start) is exactly right; this is the teardown half of it, and it's what makes the [4.7k Rx pull-down](mcu.md#rp2350-e9-and-the-neighbour-detect-pull-downs) load-bearing rather than a nicety.
- **The current sense has to be bidirectional.** Current through R_sense flows outbound when this tile is sourcing and **inbound through the body diode** when it's receiving. A unidirectional sense amp reads zero for half of normal operation. This is now a hard requirement on the still-unpicked amp, not a preference.

### Notes / gotchas

- **The real cost is area.** SOP-8 is ~5×8mm with pads, ×4 = **160mm²**, at the board edges where the connectors already live. On a ~10,800mm² tile that's 1.5%, but it's four chunky parts in the busiest region. This is the one thing that could push back at layout time.
- **R_sense stays 25mΩ.** I briefly thought it needed re-deriving for the lower current; it doesn't. Across 0–4A it drops 0–100mV, which into a gain-20 sense amp is 0–2.0V on a 3.3V ADC, reading 1.0V at the 2A target. Keep the ≥0.5W rating (2512, or a 0.5W 1206) - it still sees 0.4W at the 4A ceiling.
- **Q1 is now the last AO3401A on the board.** Moving it too would give one P-FET line at 6× and leave zero ±12V gates anywhere in the design. Against that, AO3401A is **Basic** so keeping the line costs nothing in assembly. Leaving Q1 alone unless there's another reason to touch it.
- **The `4A per-edge` figure is dead everywhere it appears.** It was never a per-edge number. [chips](../chips.md) and [checklist §3](../schematic-checklist.md) both still carry it plus the AO3401A ×4 assignment - both need the same edit.
- **Still open: the current-sense amplifier.** The research specifies R_sense feeding *"an external high-side current-sense amplifier (**not specified here**)"* - and nothing has ever been picked, or even scored. It's 4× of a part class that isn't in the BOM at all. This can't just be dropped either: the [discrete-over-eFuse decision](../design-choices/power.md#hv-per-side-switches-4-per-tile) was made explicitly accepting *"no automatic hardware OCP; firmware OCP via ADC instead"* - kill the sense path and that decision loses the argument it won on. **This is the last unpicked part in the whole per-side switch block.**
- **D scored second, and that's worth sitting with.** TPS1663 beat the status quo by 107 points. The eFuse was right about the things it was right about - it just costs 15× more than a part that gets most of the way there for 26 cents.

## Backfeed diodes - LM74700-Q1 (D1/D2)

### Goal
One per port, OR'ing each port's raw VBUS onto the shared internal `VBUS` node, so two ports at different negotiated voltages can't backfeed each other.

**The old goal line said "on the VBUS→PD+ path" and that was vague enough to mislead me.** As-built they sit *upstream* of that path: `VBUS1 →D1→ VBUS ←D2← VBUS2`, and Q2 then takes the merged `VBUS` node to PD+. Checked against the netlist, not the schematic sheet. It matters because `VBUS` is also **U11's VCC, R21's TLV431 bias and Q1's source** - so these parts are in circuit from the instant a cable is plugged in at vSafe5V, not just post-negotiation. Anything replacing them has to work at 5V, and that turned out to be the constraint that eliminated the obvious candidate.

### Math - thermal, as a function of tile count
VF max at 5A is **0.70V**. Dissipation scales with how much of the array one cable is feeding:

| Tiles fed | Load @20V | Diode current | VF (approx) | P | Verdict |
| --- | --- | --- | --- | --- | --- |
| 1 | 7W | 0.35A | ~0.45V | 0.16W | fine |
| 4 | 28W | 1.4A | ~0.55V | 0.77W | fine in SMC |
| 8 | 56W | 2.8A | ~0.62V | 1.7W | getting warm |
| max (80% of 5A) | 80W | 4.0A | ~0.65V | **2.6W** | too much |
| **hardware bound** | 100W | **5.0A** | ~0.64V | **3.2W** | **Tj ≈ 190°C - dead** |

**Footprint as-built is `D_SMC`, not SMA.** [chips](../chips.md) says SMA - the board is better than the doc, and this is one to fix in the doc rather than the board. SMC has meaningfully lower θJA, which is what makes the 4-to-8-tile range workable at all.

### Re-select: SS54 → LM74700-Q1

**The design policy is what re-opened this, not a new measurement.** Firmware limits the estimated budget to 80W; **hardware is designed to withstand 5A**, matching [the 5A bound](../design-choices/pcb-stackup.md#the-5a-bound-is-the-number-that-matters) that already sizes the copper. That's the right split - firmware owns the budget, hardware owns the ceiling - but it converts the bottom row of that table from a caveat into a hard fail. 3.2W in an SMC at 45°C/W in a 45°C tile lands past 190°C. **Destroyed, not derated.**

#### Hard gates

Applied before scoring, so most of the market doesn't get a row:

- **5A continuous, not 5A survivable.** The policy says withstand, and a dead short downstream is bounded by the source at 5A for as long as the fault persists.
- **Operates at 4.5-20V.** From the topology note above - these conduct at vSafe5V.
- **Rated ≥24V.** [The HV-path rule](../design-choices/power.md#hv-per-side-switches-4-per-tile): 20V + ~20%. A hot-unpluggable rail with an inductive cable on it.

#### Brainstorm

| | option | 5A? | ≥24V? | $/tile | notes |
| --- | --- | :---: | :---: | --- | --- |
| A | 2× SS54 paralleled per port | marginal | ✓ (40V) | ~$0.20 | same total heat, 2× area, 2× leakage |
| B | TPS2120 power MUX | ✓ (2 in parallel) | **✗ 22V** | $2.46-4.92 | gate-eliminated |
| C | **LM74700-Q1 + N-FET, ×2** | ✓ | ✓ (65V) | ~$3.26 | |
| D | keep SS54, firmware cap only | ✗ | ✓ | $0.10 | gate-eliminated by the policy |

**B is the one worth writing down, because i had it half-right.** TPS2120 is genuinely the right *class* of part and it has two inputs, so one chip replaces both D1 and D2 as a mux rather than needing one per port. Paralleling it is also fine in a way paralleling Schottkys isn't - Rds(on) has a positive tempco, so parallel FET paths self-balance. It dies on **22V against the ≥24V rule**, which is my own rule, and on putting DSBGA-20 chip-scale back into a BOM that [deliberately escaped it](#re-select-max40203--lm66100).

#### The paralleling folklore is right here, but not for the usual reason

Worth recording because the received wisdom ("never parallel Schottkys, they hog") is only half true and i nearly rejected A for the wrong reason. Hogging runs away when:

```
r_d  <  |dVf/dT| · θ · Vf
```

For SS54 at ~2.5A each: `r_d ≈ 55mΩ`, `dVf/dT ≈ -1.3mV/°C`, `Vf ≈ 0.6V`.

| θ per package | threshold | vs r_d = 55mΩ |
| --- | --- | --- |
| 45°C/W (generous pour) | 35mΩ | stable, 1.6× |
| 55°C/W (realistic) | 43mΩ | stable, 1.3× |
| 70°C/W (edge copper, crowded) | 55mΩ | **at the boundary** |

**So it converges - it just converges with 1.3× of margin, in exactly the crowded-copper condition you'd be adding the second diode for.** And the thing that actually saves it is thermal coupling: both on one shared pour so a hot one heats its neighbour, which drops the differential loop gain well below the numbers above. That's a placement requirement, not a nicety.

A loses anyway on the three things that don't depend on that math: **it doesn't remove the heat, it splits it** (3.2W is still 3.2W in a closed tile next to 30 ratiometric sensors), it doubles the area on a board where [area is the binding constraint](../design-choices/power.md#the-constraint-that-actually-decides-it), and it **doubles the reverse leakage** - which is the specific thing flagged in the gotcha below.

#### Result

**D1/D2 = LM74700QDDFRQ1 (SOT-23-THIN-6) + one N-channel FET each.**

| | SS54 (was) | **LM74700-Q1 + N-FET** |
| --- | --- | --- |
| Range | 40V PIV | **3.2-65V** |
| Drop at 5A | 0.64V | **~65mV** (13mΩ) |
| Dissipation at 5A | **3.2W** | **0.33W** |
| Reverse leakage | up to 50mA @100°C | **FET Idss, µA** |
| Package | SMC | **SOT-23-THIN-6, leaded** |
| $/tile (×2 ports) | ~$0.10 | **~$3.26** |

65V on a 20V rail is 3.25× - it doesn't just clear the ≥24V rule, it makes transient headroom a non-question. `DDF` is leaded, so this doesn't reopen the chip-scale problem the [LM66100 swap](#re-select-max40203--lm66100) was partly done to close. Same reasoning, one part over.

**It also closes the leakage gotcha below**, which has been open since the diode was picked. An off N-FET leaks microamps, so "pin the SS54 part number for its reverse leakage" stops being a live item.

**This is LM74700, not the `LM74800Q` this page listed at the [LM66100 alternatives](#accepted-risk-595v-on-a-60v-part).** LM74800 adds OV/UV protection that duplicates what U11 already does. The job here is pure reverse blocking.

#### What i'm giving up

- **~$3.26/tile, up from $0.10.** Between the discrete switches (~$1) and the [TPS1663 eFuse i rejected at $6](../design-choices/power.md#hv-per-side-switches-4-per-tile). On a 6-tile board that's ~$20 of a $250 budget, spent to remove a documented thermal failure.
- **Two new BOM lines** - controller plus an N-channel FET. There is no N-FET on this board today; AO3401A and AO4407A are both P-channel, and LM74700 drives N-channel off an internal charge pump. **No new footprint though:** a 30V N-FET in SOP-8 reuses the land pattern already placed 5× at Q2/Q4-Q7.
- **~+18mm² of land** across both ports vs the two SMCs, but 0.33W instead of 3.2W means it needs essentially no thermal pour and the SS54s need a lot. Net area is a win in practice.

#### Single source, and the fallback is a different topology

**1,530 in stock at $1.53 @10+. At 2 per tile that's 765 tiles** - the same shape as [the APH0624 flag](#what-06mm-costs) and [the pogo connectors](../chips.md). Third one, and the thread they share is that this isn't only being built by me.

Taking it anyway, because **it is the best-stocked ideal diode that clears the gates.** That's the useful part of the finding: if 1.5k is the ceiling for the whole class, the second source can't be another ideal-diode controller - it has to be a different topology, i.e. back to a Schottky with the current capped.

> **!firmware-note!** Which means **the 80W firmware cap is also the supply-risk escape hatch.** If LM74700 evaporates, the fallback build is SS54 + a firmware cap low enough that the SS54 thermals hold (~2A, the 4-tile row above). Recording that so the cap is understood as load-bearing in two directions, not just one.

**Cheapest mitigation to check first:** `LM74700QDBVRQ1` is the same die in standard SOT-23-6 rather than SOT-23-THIN. Both are 2.9 × 1.6mm on 0.95mm pitch and differ mainly in body height, so the land patterns should be interchangeable - which would make it a **stuffing-level second source**, exactly like APH0630/APH0624. Confirm against both package drawings before relying on it.

### To do
- [ ] **D1/D2 = LM74700QDDFRQ1** - replaces SS54, symbol + footprint + Value + LCSC all move together (the BOM pulls Value - same trap as the MAX40203 rename in the LM66100 section)
- [ ] **Pick the N-FET** - ≥30V, ~10mΩ @ Vgs=10V, SOP-8, LCSC-stocked. ~0.25W at 5A
- [ ] **Pull the LM74700 datasheet** and derive the support passives - VCAP cap, EN/UVLO treatment, any gate slew components. Not guessing these
- [ ] Confirm `LM74700QDBVRQ1` land pattern matches DDF, and check its stock - free second source if it holds
- [ ] **`VBUS*` needs a netclass.** It is currently on `Default` and therefore invisible to *every* custom rule in `Voided-Oblivion.kicad_dru`, including `sensor lines away from the power rails` - see the gotcha below
- [ ] [chips](../chips.md) - SS54 line out, two lines in. The stale `SMA` note goes with it
- [ ] [power design-choice](../design-choices/power.md#still-open-parts--details) - "backfeed/OR'ing protection on each PD input" can be closed

### Notes / gotchas
- ~~**Confirm which SS54 actually ships.** [chips](../chips.md) specifies C7420369 for 50µA reverse leakage over C22452 at 1mA. The datasheet the research fetched (MDD, C22452) specs reverse leakage up to **50mA at 100°C**.~~ **Closed by the re-select** - an off N-FET leaks µA, so the part-number pinning no longer has anything riding on it.
- **`VBUS` is electrically continuous with PD+ through Q2's 13mΩ**, so it carries both bucks' input ripple return current - ~0.87A RMS at 400kHz from U6 alone at 2A/20V. It is **not** a quiet DC input and should be treated as PD+ for keepout purposes. How noisy it actually gets is set by the PD+ input caps, which are [the same parts the footprint defect is about](#bulk-caps-and-the-footprint-defect) - fix those and VBUS gets quieter.
- **VBUS is also the *measured* quantity for the whole handoff** (R30/R31 divider, R21's TLV431 bias, U11's VCC) against a [±77mV error budget](#error-budget) and a 132mV hysteresis band. The reassuring part is structural: at the 5.7V trip, U6 is firmware-gated off and U5 has barely started, so the noisy phase and the sensitive phase don't overlap. **The one thing to scope:** U11B enables U5 at 5.667V, *inside* U11A's 5.640/5.772V band - U5's soft-start and inrush into 44µF land right in the window where U11A is deciding.
- **Both ports plugged in at once is a safety case, not a throughput case.** Each FUSB302 negotiates independently, the higher-voltage port wins the OR, the other is reverse-blocked. Only one controller ever conducts - but both still need full 5A rating, because either could be the one that's plugged in. Sub-case worth knowing: both plugged in and *neither* negotiated puts both ports at vSafe5V and both diodes conduct, paralleling the two ports at 5V. Benign, and identical to what the Schottkys did.
- The file `Refrences/datasheets/SS54-schottky.pdf` **is not an SS54 datasheet** - it's a 1N5817-1N5819 (1A axial). A correct one was fetched as `ss54-schottky-actual-mdd.pdf`. Both are now historical.

## Bulk caps and the footprint defect

**This is the thing to fix before ordering anything.** Five capacitors on the board are assigned values that do not exist in the footprint they've been given, and several more are unbuyable at the voltage their net actually sees.

| Ref | Value | Footprint | Net | Problem |
| --- | --- | --- | --- | --- |
| C28, C29 | 22µF | 0402 | +5VA | **22µF does not exist in 0402** |
| C34, C35 | 22µF | 0402 | +5VP | **22µF does not exist in 0402** |
| ~~C41~~ | ~~100µF~~ **1µF** | 0402 | ~~BS+~~ **+5VA** | **resolved** - repurposed as U9's input cap |
| C26, C31 | 10µF | 0402 | **PD+ (to 20V)** | 10µF 0402 exists only at ≤6.3V rating |
| C24 | ~~10µF~~ **1µF** | 0402 | BS+ (~5.7V) | **fine** - 1µF 0402 at 16V+ is easy. The 10µF concern was a doc error |
| C40 | 10µF | 0402 | +3V3 | 6.3V part is OK here |

The 20V ones are the serious pair: **C26 and C31 sit directly on PD+**, and a 6.3V-rated part on a 20V rail is a failure, not a derating question.

This is bigger than the "cap voltage-derating pass" that's been sitting open in the [build log](log.md) since session 4. Derating assumed the parts existed and would just lose capacitance under bias. They don't exist.

**What it needs:**
- **PD+ rail (C25, C26, C31, C32):** 25V minimum, 50V preferred - at 20V bias a 25V X7R is at 80% of rated and deep into the steep part of its derating curve, while a 50V part at 40% is barely bending. **0805 or 1206.** The 0.1µF HF parts can stay 0402 if correctly rated.
- **Buck outputs (C28/C29, C34/C35):** 44µF total each is the right number (TI's own Table 7-2 value). Realise it as 2×22µF in **0805/1206 at 16–25V**, and check the actual part's DC-bias curve - you can easily lose half the nominal at 5V bias in a small case.
- ~~**C41 100µF on BS+:** needs 1206 minimum, or a polymer/tantalum.~~ **Resolved - C41 is 1µF on +5VA.** The defect list is now **4 parts, all 22µF** (C28/C29/C34/C35).
- ~~**C24 10µF on BS+:** 0603/0805 at 16V.~~ **Moot - C24 is 1µF as-built.**

Everything at 100nF and below is fine in 0402 as long as the parts on PD+ are rated ≥25V.

---
Back to [schematic-design index](index.md) · [checklist](../schematic-checklist.md) · [research](../research/)
CLEAR_PAUSE 