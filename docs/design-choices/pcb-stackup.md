# PCB stackup and net rules

How many layers, what order, and how wide every net gets to be. This is the page the DRC gets configured from - if a number here and a number in KiCad disagree, this page is wrong and should be fixed, not worked around.

## Identify

One tile is **5un × 6un = 95.25 × 114.3mm**. What has to coexist on it:

| | |
| --- | --- |
| **30 hall sensors** | high-impedance analog, read at **12 bits**, into 2× 74HC4067 → 2 ADC pins |
| **4 submodule ID lines** | more 12-bit analog, **32 discrete levels** off a divider - see [submodules](submodules.md) |
| **30 SK9822 LEDs** | ~500mA of switching current, daisy-chained across the whole board |
| **2 switching bucks** | 400kHz, one of them (L3) carrying **0.938A p-p** of ripple |
| **PD+ at up to 20V** | **5A at 20V, 4A at 15V or below** - physically bounded, see [below](#the-5a-bound-is-the-number-that-matters) |
| **8 UART links** | 4 sides + 4 corners, **≥4 Mbaud** |
| **USB 2.0 full-speed** | ×2 ports, differential, wants controlled impedance |
| **RP2350B** | QFN-80, 0.4mm pitch |

The thing that shapes everything: **the whole product is a 12-bit ADC reading 30 analog sensors, and the docs already flag that path as "not characterised end-to-end" and "the first suspect" if keys read noisy.** Layer choices that protect that path win arguments.

Also relevant: board **area is the binding constraint** everywhere else in this design, so anything that trades area for layers is worth looking at.

## Layer count

### Brainstorm

- **2-layer** - cheapest by a wide margin. No plane; GND becomes a pour with cuts wherever a trace crosses.
- **4-layer** - signal / GND / power / signal. The standard for an MCU board with analog.
- **6-layer** - adds a second plane pair, enough for a dedicated analog reference and more routing room.

### Select

Real JLC pricing, 5 boards:

| | 2-layer | 4-layer | 6-layer |
| --- | :---: | :---: | :---: |
| **green** | $9.20 | **$31.70** | **$40.00** |
| **black** | $9.20 | **$39.70** | $72.90 |

| Criteria | Weight | 2-layer | 4-layer | 6-layer |
| --- | :---: | :---: | :---: | :---: |
| Ground integrity / return paths | 9 | 2 | 9 | 10 |
| ADC noise floor (the key mechanism) | 9 | 2 | 9 | 9 |
| USB differential impedance control | 7 | 3 | 9 | 10 |
| Routing feasibility at this density | 7 | 3 | 8 | 9 |
| Cost (green) | 8 | 10 | 7 | 6 |
| EMC | 6 | 2 | 8 | 9 |
| Layout effort | 4 | 2 | 8 | 9 |
| **Weighted total (green)** | | 178 | 417 | **442** |
| **Weighted total (black)** | | 178 | 409 | **418** |

**2-layer is out and it isn't close.** There is no version of this board where 30 high-impedance analog lines, 30 switching LEDs and a 400kHz buck share two layers and the ADC still reads cleanly.

**The matrix picks 6-layer, in either colour.** And the technical case is better than "routing headroom" - re-reading the stackup below, six layers **deletes a constraint** rather than adding capacity:

> L3 is six rails' worth of pours, so **every pour boundary is a split** … on L4, don't cross power-pour boundaries with anything fast.

The standard 6-layer arrangement is `SIG / GND / SIG / SIG / GND / SIG` - power moves to the **buried** layers, sandwiched between two solid GND planes, and every signal layer gets an adjacent unbroken reference. No split-crossing rule to remember, no stitching vias at every boundary.

### Going 4-layer anyway - and why that overrides the table

**This is an open-source design. Other people will fab it, and they pay the layer count too.**

That is not a criterion you weight against ground integrity - it's a **constraint on what gets published**, the same way "must work without PD" was a gate rather than a row over in [submodules](submodules.md#identify---and-the-mistake). The matrix favours 6; something outside the matrix overrides it. Recording that plainly rather than retro-fitting the weights until 4 wins.

**And the $40 six-layer number doesn't generalise.** It's an artifact of *green being cheap*, not of six layers being cheap. A builder who wants any other colour is comparing **black 4L $39.70 against black 6L $72.90 - 84% more.** Publishing a 6-layer board exports a colour constraint along with the gerbers.

**Is 4 layers reasonable here? Yes.** ~60 nets on 95×114mm across two signal layers is not dense, a solid L2 GND already gives the analog/switching separation the ADC needs, and the split problem has a cheap mitigation (below). The honest summary is that 6 is **~8% better, spread thinly across five rows with no decisive axis** - not that 4 is inadequate.

**For v1.0.0 specifically**, green 6-layer at the same price as black 4-layer is genuinely tempting and there'd be nothing wrong with ordering one for a personal prototype. But the *design* targets 4, because that's what everyone else inherits.

**Escape hatch:** if layout genuinely can't be done cleanly on 4 - not "it was fiddly", but "the ADC lines cannot be kept off the split-crossing paths" - 6 is there. Fix the [conducted noise path](../schematic-design/power.md#clean-buck---tps54302-u5) first though, because more layers won't help if the noise is arriving through the LDO.

## The stackup

```
L1   signal   1oz    ── components, analog, USB, anything referenced to the plane below
L2   GND      0.5oz  ── SOLID. No cuts, no routing. This is the whole point.
L3   power    0.5oz  ── PD+ / per-side HV / +5VP pours
L4   signal   1oz    ── switching digital, LED chain, bulk routing
```

**Copper is 1oz outer / 0.5oz inner** - JLC's standard 4-layer, and what the quoted price is for. That asymmetry drives more than it looks like it should; see below.

> **Upgrading to 1oz inner costs $16 per 5 boards, and it's rejected.** That's **+50%** on the green 4-layer price ($31.70 → $47.70) - a *bigger* burden on downstream builders than the six-layer option already rejected at +26%, and $7.70 more in absolute terms than simply buying six layers. It also fixes nothing that's blocking: the 0.5oz constraint is fully handled by "power as pours on L3, high-current traces on L1/L4, watch the necks."
>
> **And this retro-justifies the layer choice.** The 6-layer arrangement `SIG/GND/SIG/SIG/GND/SIG` puts power on the **buried** layers - the 0.5oz ones - which would have made the thin-copper problem *worse* for power by removing the 1oz outer layers as a routing option. Four layers keeps thick copper available for exactly the nets that need it.

**L2 is not negotiable and not a routing resource.** Every trace on L1 gets a tight return directly beneath it, and it's the reference for USB impedance. The moment a signal is routed through it, whatever crosses that cut loses its return path.

### The rule that does the real work

> **Analog on L1. Switching on L4. Never the same layer, never overlapping through a split.**

Sensor outputs, the 4 submodule ID lines, and ADC_AVDD live on **L1**. The SK9822 chain, the buck switch nodes and the mux select lines live on **L4**. L2 sits between them.

### L3 is a patchwork, and that matters

Six rails share one power layer, so L3 is a set of pours, not a plane - **every boundary between two pours is a split.** A trace on L4 crossing a split has its return current forced around the gap. This is the one real cost of choosing 4 over 6.

- **L1 traces are unaffected** (they reference L2, which is solid) - another reason analog goes on top.
- **On L4, don't cross power-pour boundaries with anything fast.** If a 4 Mbaud UART or the LED clock has to cross, either route it on L1 instead or put a GND stitching via pair at the crossing.

### Mitigation: don't put all six rails on L3

**Only the rails that actually need copper area need to be pours.** Three of the six don't:

| Rail | Current | Needs a pour? |
| --- | :---: | --- |
| `PD+` | **5A** | **yes** - and it's the big one |
| `PD+ TOP/RIGHT/BOTTOM/LEFT` | 4A ceiling each | **yes** |
| `+5VP` | 1.7A | **yes** - and it feeds 30 LEDs spread board-wide |
| `BS+` | 1.5A | borderline - route as a wide trace |
| `SM+` | 1A | **no** - 0.5mm trace, and it only goes to 4 corners |
| `+5VA` | 0.3A | **no** - 0.4mm trace, and it's a short hop buck → U9 |
| `+3V3` | 0.4A | **no** - 0.5mm trace, but it goes *everywhere*, so a pour is convenient if there's room |

Dropping `SM+` and `+5VA` to traces on L1/L4 removes two pour boundaries outright. **Fewer pours, fewer splits, fewer places to get it wrong** - which is most of what the sixth layer would have bought.

`+3V3` is the judgement call: it's low-current enough to be a trace, but it fans out to the MCU, all 30 sensors, both muxes and the ID dividers, so a pour saves a lot of routing. If it stays a pour, keep its boundary away from where the LED chain crosses on L4.

## Net classes

Widths from IPC-2221 at **ΔT = 10°C, 1oz outer copper**, then rounded up - copper is free, and margin here costs nothing:

```
I = 0.048 · ΔT^0.44 · A^0.725        (A in mil², external layers)
```

**This table is the as-built KiCad netclass table**, not an aspirational one. An earlier version of this page listed eleven classes (`HV_MAIN`, `HV_SIDE`, `BOOTSTRAP`, `SW_5V`, `SUBMODULE`, `CLEAN_5V`, `LOGIC_3V3`, `FAST_SIG`…) which were never created. Seven exist, because several of those eleven differed by 0.1mm and a name:

| Class | Pattern | Nets it catches | Track | Clearance | Via |
| --- | --- | --- | :---: | :---: | :---: |
| **Power Delivery** | `PD+*` | `PD+`, `PD+ TOP/RIGHT/BOTTOM/LEFT` | **1.2mm** | 0.3mm | 0.8 / 0.4 |
| **Power** | `BS+`, `+5VP` | bootstrap, gated buck out | **0.8mm** | 0.2mm | 0.8 / 0.4 |
| **Power Low** | `SM+`, `SM BUS`, `+5VA`, `+3V3` | submodule, clean 5V, logic | **0.5mm** | 0.2mm | 0.6 / 0.3 |
| **GND** | `GND` | plane on L2 | 0.5mm | 0.2mm | 0.6 / 0.3 |
| **Analog** | `AM?:*`, `AM0`, `AM1`, `* ID` | 30 sensor channels + 2 mux outs + submodule IDs | **0.25mm** | 0.25mm | 0.6 / 0.3 |
| **Switching** | `Net-(LED*`, `LED*`, `SW CLEAN`, `SW NOISY` | SK9822 chain + both buck switch nodes | 0.25mm | 0.2mm | *(default)* |
| **USB** | `USB1 D*`, `USB2 D*` | both pairs | **0.30mm** | 0.2mm | none |
| **Default** | everything else | UARTs, GPIO | 0.2mm | 0.2mm | 0.6 / 0.3 |

**USB carries `DP Width 0.30 / DP Gap 0.20`** in the two right-hand columns of the dialog. Those are the ones the differential router reads — `Track Width` isn't. Leaving them blank routes the pair at Default geometry no matter what the USB row says, which is a silent wrong-impedance failure rather than a DRC error.

**`Switching` exists for the DRC rules, not for its width.** 0.25mm is right for the LED chain; the two buck switch nodes want to be short and fat and get drawn by hand as part of keeping the hot loop tight, so the class default never applies to them. What the class buys is the ability to *name* the aggressors - see [custom rules](#custom-drc-rules).

> **Naming caveat:** `SW CLEAN` / `SW NOISY` describe the **rails they produce** (`+5VA` and `+5VP`), not the switch nodes' own noise. Spectrally it's the other way round - `SW CLEAN` belongs to U5, which runs in [DCM pulse-skipping essentially all the time](../research/tps54302-buck.md), so its frequency wanders with load and the node rings freely during the dead time. `SW NOISY` (U6) runs clean fixed-frequency CCM and is the *magnitude* aggressor at 0.938A p-p. Both are in the class; the names just don't rank them.

**`PD+*` catching all five PD nets is the right shape** - one pattern instead of five hand-written rows, and the match preview confirms it. Worth copying that habit for anything else that grows per-side variants.

#### What the pattern column is actually doing

**Verify every pattern in the preview pane; it costs one click.** Two of these looked wrong and weren't, and one looked fine and was missing:

- **`AM?:*` catches all 30 sensor channels** - `AM0:0`…`AM0:14` and `AM1:0`…`AM1:14`. The separate `AM0` / `AM1` rows are the two mux *outputs*, which are different nets. I twice flagged this as probably broken on the theory that the explicit rows implied the wildcard wasn't working. It was fine.
- **`Net-(LED*` sweeps the whole SK9822 chain** in one row, and survives re-annotation because the names shift between LED refs but keep the prefix. Expect ~58 nets - 29 links × clock and data.
- **`LED*` is the row that catches `LED SCK` / `LED TX`** - the first segment, MCU→LED1. Those are explicitly labelled so they have no `Net-(` prefix, and `Net-(LED*` misses them. That segment is the longest run in the chain and the one most likely to pass the sensor field, so leaving it in `Default` would have been the worst single omission.

**Auto-generated names are a fragile thing to match on.** `Net-(LED*` is acceptable because the whole chain is deliberately unnamed and the prefix is stable. The switch nodes got real labels instead, which is why the `SW CLEAN` / `SW NOISY` patterns are exact strings rather than wildcards - and why they don't collide with the 30 `SW1`…`SW30` switch designators.

### The 5A bound is the number that matters

**Nothing can draw more than 5A at 20V, or 4A at 15V and below, in or through one tile.** That is a hard physical ceiling, not a design target, which makes it the right number to size copper against.

| through-current | rise on the 1.2mm class width | copper at 40°C ambient |
| :---: | :---: | :---: |
| **4A** (≤15V) | 24°C | 64°C - fine |
| **5A** (20V) | **40°C** | **80°C** - legal, but it becomes the FET's ambient |

Nothing breaks at 80°C - FR4 Tg is 130-150°C and IPC's curves run to a 100°C rise. But the AO4407A thermals in [power.md](../schematic-design/power.md) assume **40°C ambient**, and a trace running at 80°C past those FETs invalidates that assumption. So:

| | at ΔT=10 | at ΔT=20 | at ΔT=30 |
| :---: | :---: | :---: | :---: |
| 4A | 2.05mm | **1.35mm** | 1.05mm |
| 5A | 2.79mm | **1.83mm** | 1.43mm |

**Keep the class at 1.2mm - it's the correct floor for the branches.** The four PD pins per side are already four parallel 1A paths that don't merge until after the per-side FET, so each branch is capped at 4A by the connector itself, and 1.2mm covers 4A at a 24°C rise.

**Widen the merged node to ≥1.8mm, or pour it.** The only segment that ever carries the full 5A is short: PD input → the four per-side FETs. Four pads at 2.5mm pitch fanning into one node wants to be a zone anyway.

**And the vias are tighter than the copper.** A 0.4mm via with 25µm plating has ~0.031mm² of barrel - about **1.5A** at a 20°C rise. Five amps needs **four in parallel**, six if you want the rise down at 10°C. No netclass can express "four at this transition"; it's a placement rule, enforced by eye and by [the trunk rule area](#rule-areas).

> **The cheap way out is firmware.** The 5A case only exists at 20V, the default is 9V, and firmware does the negotiating - with the same tile map it already uses to prevent slow faults. If a given build's copper only supports 4A, firmware declines the 100W PDO and takes 60W. **Recording that as a firmware requirement rather than leaving it implicit**, because otherwise the 1.8mm pour is load-bearing and undocumented.

### Internal layers need **5.2×** the width, not 2×

Two effects stack: IPC's constant drops (k 0.048 → 0.024 for internal), **and** the inner copper is half as thick.

| Current | outer, 1oz | **inner, 0.5oz** |
| :---: | :---: | :---: |
| 1.0A | 0.30mm | **1.57mm** |
| 1.7A | 0.63mm | **3.27mm** |
| 2.0A | 0.79mm | **4.09mm** |
| 4.0A | 2.04mm | **10.64mm** |

**So: high current goes on L1/L4 as traces, or on L3 as a *pour* - never as a narrow trace on L3.** A 2A per-side rail routed as a 1.2mm trace on an inner layer would be at **3.4× its rated width**, and DRC would not catch it because the net class width is the same number on every layer.

The pours are fine - a pour is far wider than 10mm in most places - but **watch the necks.** Where a pour squeezes past a via field or between two other pours, that neck needs the 0.5oz number, not the 1oz one.

**Clearance is not driven by voltage here.** IPC-2221 B4 (external, uncoated) wants only **0.13mm** at 15-30V, so 0.2mm already clears 20V. The 0.3mm on the HV classes is manufacturing insurance, not electrical necessity - don't let it eat area if a corner gets tight.

### USB differential pair

> **Corrected.** This section used to say `W ≈ 0.19mm / S ≈ 0.13mm`, quoted without a derivation. **That geometry computes to 101Ω**, not 90. The real numbers are below, along with the working, so the next person doesn't have to take it on faith either.

Three inputs, and all three come from **the fab's stackup**, not from the board file:

| | JLC 4-layer 1.6mm | |
| --- | :---: | --- |
| **H** | 0.2104mm | the 7628 prepreg between L1 and L2 - the only dielectric that matters |
| **T** | 0.035mm | 1oz outer copper |
| **εr** | ~4.3 | 7628 at the knee frequency (sources say 4.05-4.6) |

**Step 1 - single-ended microstrip** (Hammerstad-Jensen, with the thickness correction):

```
εeff = (εr+1)/2 + (εr-1)/2 · (1 + 12H/W)^-0.5
Z0   = 120π / [ √εeff · (u + 1.393 + 0.667·ln(u + 1.444)) ]     u = W/H
```

**Step 2 - couple the pair** (IPC-2141):

```
Zdiff = 2·Z0 · (1 − 0.48·e^(−0.96·S/H))
```

S is the **edge-to-edge gap**, normalised to H. Coupling is set by the gap *relative to the dielectric height*, which is why a thin prepreg lets you couple tightly.

**Sanity-check the model before trusting it.** JLC publishes **0.36mm = 50Ω single-ended** for this stackup; the formulas give **51.0Ω**. 2% off, so the method is calibrated and the rest of the numbers can be believed.

#### 90Ω is a contour, not a point

This is the bit that makes it confusing, and it's why a bare `W / S` pair quoted with no context is so easy to get wrong. **Every W has an S that hits 90Ω:**

| W | Z₀ | S for 90Ω | pitch | |
| :---: | :---: | :---: | :---: | --- |
| 0.20 | 67.4 | 0.081 | 0.281 | ✗ under JLC's 0.127 minimum |
| 0.25 | 61.2 | 0.131 | 0.381 | ✗ *at* the floor |
| 0.28 | 58.0 | 0.167 | 0.447 | ok |
| **0.30** | **56.1** | **0.195** | **0.495** | ✓ **use this** |
| 0.36 | 51.0 | 0.308 | 0.668 | ok, wide |

**W = 0.30mm / S = 0.20mm.** Both sit clear of JLC's 5 mil floor, so etch tolerance is a percentage of something comfortable rather than a percentage of the minimum feature.

#### What actually moves it

| | Zdiff | |
| --- | :---: | :---: |
| nominal | 90.5 | |
| εr 4.05 / 4.60 | 93.0 / 87.8 | ±3% |
| prepreg thickness ±10% | 93.3 / 87.4 | ±3% |
| **etch ±0.02mm** | **95.6 / 85.6** | **±6% - dominant** |

**Etch dominates because it moves W and S in opposite directions** - over-etching narrows the traces *and* widens the gap, and both push impedance up. Stack every worst case and it's still inside USB's **±15%**. Solder mask isn't modelled; it raises εeff and pulls Z₀ down another 2-4%, eating into the low side without changing the conclusion.

#### Don't pay for controlled impedance

RP2350 USB is **full-speed, 12 Mbps**. With t_r ≈ 4ns and v = c/√εeff ≈ 169mm/ns, the critical length is `v·t_r/6 ≈ 110mm`. Every USB run on this tile is a fraction of that, so **the trace isn't a transmission line** - reflections resolve inside the rising edge. Route 0.30/0.20 because it costs nothing to draw, and skip JLC's impedance-test option, which costs money and needs a test coupon.

#### Reference-plane continuity beats all of it

A gap in the L2 plane under the pair does far more damage than a 10% width error, and it is the one thing DRC genuinely cannot check. Route on **L1 only**, referenced to L2, **no vias in the pair**.

The specific hazard on this board: the submodule sockets' 1.6mm holes punch a **12.7 × 2.6mm void through L2/L3 at every corner**. Keep the pair away from those - enforced as far as it can be by [the corner-void rule](#custom-drc-rules).

## Via rules

Two sizes in the as-built table: **0.6 / 0.3mm** for signal and the low rails, **0.8 / 0.4mm** on `Power` and `Power Delivery`.

Current per via, from the plated barrel area (`π · d · 25µm`) at a 20°C rise:

| via | barrel | per via | |
| :---: | :---: | :---: | --- |
| 0.6 / 0.3 | 0.024mm² | **1.2A** | |
| 0.8 / 0.4 | 0.031mm² | **1.5A** | |

| Net | Vias per transition | why |
| --- | :---: | --- |
| `PD+` merged node | **≥4** | 5A ÷ 1.5A, and 6 gets the rise to 10°C |
| `PD+ <side>` | **≥3** | 4A ÷ 1.5A |
| `BS+`, `+5VP` | **≥2** | 1.5-1.7A |
| `SM+`, `+3V3` | ≥1, prefer 2 | |
| signal | 1 | |

**Analog nets should not use vias at all** where it can be avoided. A via on a sensor output or an ID line punches through L2 and moves the reference - route those on L1 from sensor to mux, and from connector to MCU, without changing layers. If one absolutely must transition, put a GND stitching via immediately adjacent.

**GND stitching:** vias around the board perimeter and either side of every L4 trace that crosses an L3 pour boundary. Also a stitching ring around the RP2350B and under both bucks.

## Placement rules that belong with the stackup

- **Both bucks get their loops kept tight on L1** - input cap, IC and inductor in one small area, with the switch node as short as physically possible. L3's 0.938A p-p is the loudest thing on the board.
- **Spread heat on L1/L4, not L3.** The TPS54302s have **no exposed pad** ([power.md](../schematic-design/power.md#big-buck---tps54302-u6)), so heat leaves through the leads into whatever copper they sit on - and **L3 is half-thickness**, which makes it a much weaker spreader than the earlier version of this page assumed. Give both bucks and the four AO4407A generous **outer-layer** copper first; thermal vias down to L3 help, just less than they would at 1oz.
- **Keep the sensor field's L4 clear of the LED chain where sensors sit above it.** They're on opposite sides of L2 so coupling is small, but overlapping a switching LED trace directly under a high-impedance sensor line is free to avoid at placement time.
- **The magnets in the case walls** are a hall-sensor concern, not a stackup one - tracked in [module-connectors](module-connectors.md).

## KiCad Board Setup

The numbers above are useless unless the DRC enforces them. This section is the **Board Setup → Constraints** page, reviewed against both this design and JLC's process.

### Constraints - what to change from the current settings

| Setting | Currently | **Should be** | Why |
| --- | :---: | :---: | --- |
| Minimum clearance | **0** | **0.2mm** | A floor of 0 means **DRC will not catch a clearance violation at all** on any net that slips through unclassified. The net-class values still govern normally; this is the backstop |
| Minimum track width | 0.2mm | 0.2mm ✓ | matches the `SIG` class |
| Minimum connection width | **0** | **0.2mm** | zero disables the starved-thermal-connection check |
| Minimum annular width | **0.1mm** | **0.15mm** | 0.1 is at or under JLC's process minimum. Comes free with the via change below |
| Minimum via diameter | **0.5mm** | **0.6mm** | 0.6/0.3 is JLC's standard via and gives **0.15mm annular**. 0.5/0.3 gives only 0.1 |
| Copper to hole | 0.25mm | 0.25mm ✓ | |
| Copper to edge | 0.5mm | 0.5mm ✓ | generous but the board isn't edge-limited |
| Minimum drill | 0.3mm | 0.3mm ✓ | JLC's cheap-tier PTH minimum |
| Hole to hole | **0.25mm** | **verify** | JLC typically wants ~0.5mm hole-edge to hole-edge between *different nets*. Check their current capability page before trusting 0.25 |
| **uVia diameter / hole** | 0.2 / 0.1mm | **do not use uVias** | microvias are **HDI** - not available on the standard 4-layer service at the price this design is targeting. One placed uVia makes the board unquotable at that tier |
| Silk min text height | **0.8mm** | **1.0mm** | below JLC's reliable-rendering minimum |
| Silk min text thickness | **0.08mm** | **0.15mm** | same - and this board's silkscreen labels 30 switch positions and 16 connectors, so legibility isn't cosmetic |
| Arc max deviation | 0.005mm | ✓ | |
| Min thermal relief spokes | 2 | ✓ *(but see below)* | |

**Thermal relief is wrong for the power pads.** Two spokes is fine for signal pins, but the AO4407A drains, the buck pads and every HV via should use a **solid zone connection**, not thermal relief - L3 copper is the only heat path for parts with no exposed pad. Set those per-footprint or per-net rather than relying on the global default.

### Teardrops

The defaults shown (L 50%, W 100%, max 1mm × 2mm, span-two-segments and prefer-zone-connection on) are sensible and worth keeping. Teardrops cost nothing at fab and reduce stress at the pad/track junction, which matters on a board that will be **hand-assembled and reworked**.

The 2mm maximum width comfortably covers the widest copper on the board (the 1.8mm PD+ trunk), so no HV trace gets a teardrop narrower than the trace itself.

### Length tuning

**This board doesn't need it.** Worth stating so nobody burns time on serpentines:

- **USB is full-speed (12 Mbps)** - a bit is ~83ns, and the matching requirement is *millimetres of slack, not picoseconds*. Route the pair together and it's matched. No tuning pattern required.
- **The 8 UART links are single-ended at 4 Mbaud** - nothing to match against.
- There is no parallel bus, no DDR, no source-synchronous clock on this design.

The defaults shown are harmless. One clarification, because it's easy to misread: the **1mm "spacing" in the differential-pair tuning block is the serpentine spacing**, not the pair gap - the gap that sets 90Ω comes from [the impedance calculation](#usb-differential-pair) and is **0.20mm**.

**"Include stackup height in track length calculations" ✓ on** is correct - it counts via barrel length, which is the only place length would meaningfully change here.

## Custom DRC rules

Everything above is only real if DRC enforces it, and **three of the constraints on this page cannot be written in the Netclasses dialog at all.** Those three are the reason `Voided-Oblivion.kicad_dru` exists; the rest of the file is there because it was nearly free once the file existed.

Full file in the repo root next to the project. What each rule is for:

| rule | what it catches | expressible in the netclass table? |
| --- | --- | :---: |
| `sensor lines away from the power rails` | Analog within 0.5mm of a switching rail | **no** - the table gives one clearance per class, applied to *everything* |
| `USB pair away from switching nets` | a buck node or the LED chain crowding the pair | **no** - see below |
| `PD+ zone connections` | a 5A pour necked to 0.4mm at a pad | **no** - `connection_width` is the only constraint that looks at this |
| `PD+ off inner layers` | PD+ routed on 0.5oz copper | no |
| `PD+ trunk carries the full 5A` | the merged node under 1.8mm | no |
| `USB pair geometry` | wrong W/S, uncoupled runs | partly |
| `USB must not cross the corner plane voids` | the pair over a socket void | no |
| `THT pads: thermal relief for hand soldering` | a hand-soldered pad connected solid to a plane | partly |
| `board-wide` | microvias, single-spoke reliefs | partly |

**The USB clearance rule is the one worth understanding**, for two reasons.

First, it does something the dialog can't. Netclass `Clearance` is a single number applied to *every* other net **including the pair partner** - so it can never be larger than the 0.20mm pair gap, which pins USB at 0.2mm from everything on the board. Only a rule can split those cases.

Second, **the first version of it was the wrong shape, and the way it failed is the lesson.** It read:

```
(condition "A.inDiffPair('*') && !AB.isCoupledDiffPair()")     # 0.5mm to every foreign net
```

Correct in principle, and it immediately needed three exemptions:

| it fired on | why that's not fixable |
| --- | --- |
| the receptacle's own pads | 0.5mm pitch puts D+ ~0.2mm from VBUS/CC/SBU |
| the RP2350B's fanout | QFN-80 at 0.4mm pitch |
| the TPD2E2U06DRL's NC pins | no net, so no signal, so not an aggressor |

All three are geometry fixed by the part, and **none of them were what the rule was for.** It exists to keep the buck switch nodes and the LED chain off the pair. Once `Switching` existed to name those, four rules collapsed to one:

```
(condition "A.inDiffPair('*') && B.hasNetclass('Switching')")
```

and all three exemptions deleted themselves.

> **Three exemptions in a row is a rule telling you it's the wrong shape.** The blunt version was defensible while there was no class to point at - but the moment you find yourself carving out cases the rule was never meant to catch, the fix is to name the aggressor, not to keep patching. Same failure as [scoring a requirement as a weighted row](submodules.md#identify---and-the-mistake): the rule was answering a question adjacent to the one that mattered.

**A side effect worth keeping:** because the SK9822 chain is in `Switching`, the analog rule now also enforces 0.5mm between the sensor field and the LED chain - which until now existed only as prose in [placement rules](#placement-rules-that-belong-with-the-stackup). Naming the class turned a comment into a check.

**What was deliberately left out**, because a rule that fires on something already decided to be irrelevant just teaches you to click past DRC results:

- **`via_count`** for PD+. It counts vias *per net*, not per transition, so it cannot express "four in parallel here" - and it would fire on any PD+ net that legitimately has none. Wrong tool.
- **USB skew and length tuning.** Settled above: 12 Mbps on a sub-110mm run.
- **A hole-size assertion on the submodule sockets.** The footprint already fixes 1.6mm, and matching on footprint name is fragile.

> **Ordering matters and is easy to get wrong.** Within a constraint type the **last** matching rule wins, so general rules go high and specific overrides go low. `PD+ zone connections` sets `solid` and must stay *below* the THT thermal-relief rule to win on any pad that is both.
>
> KiCad also emits an informational notice when two rules share a condition. It is not an error - it just means they can be merged into one rule with several constraints, which is worth doing so a genuine shadowing warning isn't buried in noise.

### Rule areas

Two rules match on **named Rule Areas** that have to be drawn on the board. Place → Rule Area, then in properties:

- **Name** - this is the whole point; it's what the rule matches
- **Layers** - tick **all four copper layers**. The area test is evaluated per-layer, so an area on one layer silently fails to match a track on another, and a through via touches all four
- **Keepout checkboxes** - leave **all unticked**. KiCad may grumble that no keepout properties are set; that's expected

| name | where | why |
| --- | --- | --- |
| `PD_TRUNK*` | the common PD+ node, from the PD input out to the four per-side FETs | the only place 5A flows. Deliberately **not** over the per-side branches - the connector's 4×1A caps those at 4A, which 1.2mm already covers |
| `CORNER_VOID_NE/NW/SE/SW` | each submodule socket pad row, ~17 × 7mm | the plane void. Margin matters: return current has to detour *around* the void, so the disturbed region is bigger than the hole |

Compass points for the corners on purpose - `TOP/RIGHT/BOTTOM/LEFT` already means *sides* in this design.

**An area that doesn't exist produces no error at all.** Both rules are inert until drawn, which is the worst kind of failure. Draw one deliberate violation of each, confirm DRC complains, delete it.

`CORNER_VOID` should never fire in normal layout - USB runs USB-C → MCU and the corners are about as far from that path as this board allows. It's a tripwire, not a constraint.

## Routing order

**Route in descending order of how much the net's behaviour depends on its geometry.** Nets at the top have one correct path and everything else must move out of their way; nets at the bottom are allowed to wander the entire board, and one of them is *supposed* to.

The reason to fix an order at all: the constrained nets are a small minority, and if the unconstrained ones are routed first they will have eaten exactly the space the constrained ones needed.

### Tier A - geometry *is* the specification

Route first, shortest sensible path, no compromises. If one of these can't be routed cleanly, **move the components**, don't bend the trace.

1. **Both buck hot loops** - input cap → IC → inductor, switch node as short as physically possible. This is placement more than routing, and it's first because L3's 0.938A p-p is the loudest thing on the board and everything else is downstream of how well it's contained.
2. **QSPI to both flash chips** - the fastest bus on the board by a wide margin. Short, together, over solid L2.
3. **`AM0` / `AM1`, mux → MCU** - the two most sensitive nets in the design. Everything this product does arrives through them at 12 bits. L1 only, no vias, away from anything in Tier B.
4. **`MCU D+/D-`** - 0.30/0.20 on L1, no vias, clear of the corner voids.

### Tier B - needs *area*, and area is claimed by whoever asks first

5. **PD+ trunk and the L3 pours.** A 1.8mm pour cannot be retrofitted into a board that's already routed. Claim the copper, then route signals around it.
6. **L2 integrity.** Not a net - a rule. Nothing is routed on L2, ever. It's cheaper to state it here as a step than to discover a via field has perforated it.

### Tier C - constrained, but individually forgiving

7. **30 hall sensor outputs, sensor → mux.** High impedance, so keep them off the switching nets, but each one is short and there are 30 of them - they'll dominate the L1 area budget. Route as a field, not one at a time.
8. **The 4 submodule ID lines.** Analog, but read once at plug-in rather than continuously, so they tolerate far more than the sensor field does.
9. **8 UART links** - 4 sides, 4 corners. Long and exposed at the edges, but single-ended at 4 Mbaud with nothing to match against. Route on L1 where they'd otherwise cross an L3 pour boundary.
10. **I²C, mux select lines, reset and boot straps.**

### Tier D - meander freely

11. **The SK9822 chain.** It has to visit all 30 LEDs, so snaking across the whole board is not a compromise, it's the job. Keep it on L4, under L2, and off the sensor field's shadow.
12. **Spare GPIO and anything else left.**
13. **GND stitching vias**, then zone fills, then re-run DRC.

> **The one rule that outranks the order:** nothing crosses a plane split without a stitching via beside it. A Tier D net that breaks a Tier A net's return path has caused a Tier A problem.

## Mounting holes

### Identify

Four jobs, and the first one is specific to this being a hall-effect board:

1. **Hold the PCB-to-plate gap constant under typing load.** On a mechanical keyboard flex is a *feel* preference. Here the sensor is on the PCB and the magnet is in the switch stem, so if the plate holds the switch and the PCB deflects away from it, **the gap changes and that is a measurement error** - the key reads as partially pressed.
2. Keep the edges coplanar with neighbouring tiles so the pogo contacts stay inside their compression window.
3. React the insertion and removal force of the USB-C port and the four submodule sockets without levering the board.
4. Physically fit. **The key field fills the board exactly** (5un × 6un, no margin), so a hole can only go where a switch isn't.

**One thing that turns out not to be a job:** reacting the pogo spring force. The edge connectors are right-angle *surface-mount*, so their ~4N per connector pushes **in-plane**, not normal to the board. In-plane force over a 95mm span in FR4 is nothing. That removes what looked like the strongest argument for extra edge support.

### Where a hole can physically go

On the 19.05mm grid, switch centres are at `9.525 + 19.05k`, so the four-way junctions are at multiples of 19.05:

```
x junctions:  19.05   38.1   57.15   76.2
y junctions:  19.05   38.1   57.15   76.2   95.25
clear square at a junction:  19.05 − 14.0 = 5.05mm
```

**5.05mm is the hard constraint and it picks the screw.** An M2 hex standoff is 4.6mm across corners - fits. M2.5 is 5.77mm across corners - **does not fit**, at any junction, anywhere on this board. So: **M2**, 2.2mm clearance hole.

**And the board has no centre.** With 5 columns, `x = 47.625` is a *switch centre*, not a junction, so there is no hole position on the x midline. Symmetric column pairs are `{19.05, 76.2}` and `{38.1, 57.15}`. Worth knowing before drawing a layout that assumes a centre screw.

### Select

Deflection of a 1.6mm FR4 panel under a 2N bottom-out, by support grid:

| holes | arrangement | worst cell | deflection |
| :---: | --- | :---: | :---: |
| 4 | corners only | 95.2 × 114.3 | **32.7 µm** |
| **6** | `x{19.05, 76.2} × y{19.05, 57.15, 95.25}` | 57.1 × 38.1 | **5.9 µm** |
| 8 | + inner pair at y=57.15 | 38.1 × 38.1 | 4.5 µm |
| 12 | 4×3 grid | 19.1 × 38.1 | 1.6 µm |

**The budget comes from rapid trigger.** Thresholds are commonly set at 0.1mm and enthusiast firmware goes finer. A 33µm systematic error is a third of a 0.1mm threshold - enough to false-trigger neighbouring keys during fast typing. Under ~10µm it disappears into ADC noise and magnet tolerance.

**Six holes.** Corners-only is not close to adequate, and the step from 4 to 6 buys a **5.5× reduction** because deflection scales with span², so halving a span quarters it. The step from 6 to 8 buys 1.3× for two more screws per tile on a board other people have to assemble.

> **Treat the absolute numbers as order-of-magnitude.** The plate formula assumes continuously simply-supported edges; screws are point supports, which is meaningfully worse - call it 2-3×. Add a plate and it's better again. The *ordering* is robust even where the absolute figures aren't, and 4-corner still fails by a wide margin under any of those corrections.

### Result

- **6 × M2**, 2.2mm clearance hole, at `x ∈ {19.05, 76.2}` and `y ∈ {19.05, 57.15, 95.25}`
- **4.5mm copper keepout** around each, for the standoff or screw head
- **Five NPTH, one PTH tied to GND.** A metal plate left floating is an antenna; tying it at *one* point gives it a defined potential without creating a loop through the plate - which on a board whose whole job is a 12-bit ADC is worth the thirty seconds it takes to decide
- **Every tile uses the same pattern.** It's a modular design, so the plate and case are shared parts - this pattern gets frozen once and inherited by every future tile variant

## Open

- **Confirm JLC's actual 4-layer stackup** at order time and re-run the USB impedance numbers against it - the 0.2104mm figure is their standard, not a guarantee. The formulas above make this a two-minute re-derive rather than a re-guess.
- **Confirm KiCad actually sees `USB1 D+`/`USB1 D-` as a differential pair.** Every USB rule keys off `A.inDiffPair('*')`, not off the netclass - so if the pair isn't detected, the DP columns still drive the router but **all three custom rules silently match nothing.** Quickest check: start a trace with the differential-pair router and see whether it will begin.
- **Draw the rule areas** (`PD_TRUNK*`, `CORNER_VOID_*`) and confirm both rules actually fire. An area that doesn't exist produces no error.
- **ADC_AVDD filtering** is still unresolved ([review F6](../schematic-review-2026-08-08.md)) and it interacts with this page: whatever filter lands, it goes on L1 next to pin 59 with its own local GND via.
- **Copper weight** - 1oz assumed throughout. 2oz would halve every width above, but costs more and is rarely offered on 4-layer at the cheap tier. Revisit only if the HV routing genuinely can't fit.
- **Firmware must cap the PDO request** to what the build's copper supports, per the 5A note above. Currently an undocumented dependency on the trunk pour being wide enough.

back to [index](../index.md)
