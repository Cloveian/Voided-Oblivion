# Layout checklist - finishing placement and routing

`Complete`{.status .settled}

Where the board actually is, and the order to finish it in. Companion to [routing order](design-choices/pcb-stackup.md#routing-order), which has the *why*; this has the *what's left*.

!!! asbuilt "Done as of 2026-08-30 - the board is going to fab"
    everything below is finished: placement, routing, zones and silk. the phases are
    kept because the *order* turned out to be the useful part, not the state. if you're
    reading this to find out what's left, the answer is nothing.

<div class="superseded" markdown>

Counts from when this page was written, kept so the phase ordering below still makes sense.

**State as of writing:** 261 of 425 footprints placed, 530 segments, 86 vias, 32 zones. 242 multi-part nets excluding GND - **73 have tracks, 169 don't.**

</div>

---

## Phase 0 - route only what cannot meander

> **Corrected.** This phase first said "route the 71 nets whose parts are all placed - it's free progress." That's the wrong filter. **71 of those are routable; only 3 are *constrained*.** 58 of them are the SK9822 chain, which is the most meander-tolerant net on the board - routing it now would claim the exact channels the 90 unplaced power parts still need. Sort by *how much the net's behaviour depends on its geometry*, not by what happens to be placed.

**Route these three now. Nothing else.**

Everything else that's geometry-critical - the USB pair, QSPI, both buck hot loops - is already routed.

### 0.1 The two that matter - `AM0` and `AM1`
Both muxes and U1 are placed and these are still unrouted. They are **the most sensitive nets on the board** - every keystroke arrives through them at 12 bits.

- **L1 only, no vias.** A via punches L2 and moves the reference. If one is genuinely unavoidable, GND stitching via immediately adjacent.
- Keep them off `SW CLEAN` / `SW NOISY` and the LED chain - the `sensor lines away from the power rails` DRC rule enforces 0.5mm, but the rule is a floor, not a target.
- These are the shortest path from mux to ADC pin. Don't let anything else claim that channel first.

### 0.2 `/VREG_LX` - L1 to U1
The RP2350's **internal core-regulator switch node**. Same class of net as the buck SW nodes: short, small loop area, minimal copper. It's a 2-part net and both are placed - just make it tiny.

### Explicitly NOT now

| | why it waits |
| --- | --- |
| **SK9822 chain** (58 nets) | it's *supposed* to snake the whole board - that's the job, not a compromise. It will happily take whatever channels are left over, and it will take the good ones if you let it |
| **8 corner UARTs** | 4 Mbaud, single-ended, nothing to match against. Long by definition - they go to the corners |
| `PD+ BOTTOM`, `Net-(R4-Pad1)` | trivial, and PD+ wants its width decided after the FETs land |

---

## Phase 0.5 - place everything, then route the newly-constrained

Once the 164 parts are down (Phases 1-2 below), a second batch of nets becomes geometry-critical that isn't yet, because their parts don't exist on the board:

- **`Q2`'s VBUS→PD+ path** - full port current, 5A. Width and via count, not routing convenience.
- **U11's comparator inputs** - the guard-trace rule in 1.4. This is the one that fails as oscillation rather than as an obvious open.
- **Each AO4407A's gate-drive loop** - BC847B to FET gate. Short loop; the GPIO run into the base is the part that can wander.
- **`BS+` and the ideal-diode junction** - U9/U15 carry real current on a rail that exists pre-PD.

Route those immediately after placing, before the bulk. Then the meander-tolerant remainder: LED chain, corner UARTs, I²C, enables, spare GPIO.

---

## Phase 1 - place the power section (90 parts)

This is the biggest remaining block and it's one coherent circuit. Place it in **signal-flow order**, because each stage's position constrains the next.

### 1.1 PD front ends - `PD1`, `PD2` + their passives
`R39`-`R51`, `C39`, `C40`, `C42`, `C43`. One per USB-C port, **each hard against its own connector**. CC lines go direct to the port, so PD1 belongs at USB1 and PD2 at USB2 - they do not meet.

### 1.2 Backfeed diodes - `D1`, `D2`
SS54, SMA, one per port on the VBUS→HV path. Near their connector, before anything else taps VBUS.

### 1.3 VBUS→PD+ handoff - `Q1`, `Q2`, `Q3`, `D4`, `D5`, `C44`, `C45`, `R35`, `R36`, `R47`
The injection path. `Q2` carries **the full port current (5A)** - give it copper, and remember the AO4407A's datasheet thermals assume **1 in² of 2oz**, which this board cannot provide. Size the pour by what's achievable, not by the datasheet.

### 1.4 Comparator chain - `U11`, `U10` + `R21`, `R27`-`R33`, `R46`, `C37`, `C38`
Powered from VBUS so it's alive pre-PD. Two placement rules, both from the datasheet extract:

- ⚠ **Do not run U11's output parallel to its inverting input without a GND or VCC guard trace between them.** Your VBUS divider into U11A is exactly that topology and the failure mode is oscillation around the 5.640/5.772V trip - which would look like random PD handoff glitching.
- Input series resistors hard against the pins.
- `R30`/`R31` set the trip; keep them together and away from anything switching.

### 1.5 Ideal diodes - `U9`, `U15` + `R15`, `R16`, `C41`, `C76`
`U9` on the BS+/+5VA junction, `U15` on the +5VP branch. **CE→VOUT** on both - if that ends up strapped to GND instead, the part becomes a plain switch with no reverse blocking and nothing tells you.

### 1.6 Submodule switches - `U12`, `U16` + `C77`, `C120`, `C121`, `R92`, `R95`, `R96`
In series at 1A. `U16`'s `/FLG` is read, `U12`'s isn't.
⚠ **Both enables need 4.7kΩ pull-downs, not 100k** - RP2350-E9 parks a floating pad at 2.2V, above the EN threshold.

### 1.7 Per-side gate drive - `Q4`, `Q5`, `Q7` + `Q8`-`Q11`, `R67`-`R82`, `C116`-`C119`
`Q6` is already placed; put the other three at their own edges. Each BC847B sits next to its AO4407A - the gate drive loop is what wants to be short, not the GPIO run.

---

## Phase 2 - place the rest

### 2.1 `/keys/` - 18 parts
`U8` (level shifter) near the LED chain head; `R52`-`R66` are the mux select lines and belong next to AM0/AM1; `C108`/`C109` are the mux decoupling - **tight to the pins**, they're the one path by which mux switching couples into the analog rail.

### 2.2 Submodule ID dividers - `R93`, `R94`, `R97`-`R100`, `C122`-`C125`
One divider per corner, each next to its own corner connector. The cap is what makes 32 discrete levels work - keep it at the ADC end, not the connector end.

### 2.3 UART series resistors - `R84`-`R91`
`R84`-`R87` are in series to the edge connectors; `R88`-`R91` are the Rx pull-downs. Put the series ones near their connector so the probe point downstream of them is meaningful.

### 2.4 Test points - `TP1`-`TP37`
**Last, and on the bottom.** The top is ~85% covered; B.Cu is empty and 100% probeable with the board assembled.

The pogo-adjacent ones matter most: once two tiles are mated, those contacts are buried inside the joint, which is exactly when inter-tile comms bugs happen. Tap the **connector side** of the series resistors (`Net-(J1-Pin_6)` etc, currently auto-named) rather than `Tx TOP` - the MCU side can't tell you whether the resistor or the connector is the problem.

---

## Phase 3 - zones

- **Delete the transplanted `+3V3` zone on F.Cu.** It's 51 × 70mm covering a third of the board on the layer reserved for analog.
- **Add `+3V3` as a pour on In2.Cu (L3).** 128 pads need it, 96 of them away from the MCU including all 30 sensors. A trace tree won't do it.
- **Keep a small `+3V3` island on L1 around U1** so the 12 IOVDD decaps keep a low-inductance connection.
- ⚠ **14 cluster pads are currently fed by that F.Cu zone alone.** Add the L3 pour and the island *before* deleting it, then check the ratsnest.
- ⚠ `ADC_AVDD` (pad 59) and `VREG_VIN` (pad 64) must **not** share a feed path off the pour. VREG_VIN is a switching load; ADC_AVDD is the ADC's supply. Tap separately, with the [F6](schematic-review-2026-08-08.md) filter between +3V3 and ADC_AVDD.
- Re-check what's under the B.Cu USB excursions **after** the L3 pour lands - right now L3 is solid GND there, which is why it's currently safe.

---

## Phase 4 - close out

- [ ] **Decide the 0.15mm / 0.25mm question.** 195 `track_width` + 55 `drill_out_of_range` violations are the Pi reference fanout, which needs 0.15mm track and 0.25mm drill at 0.4mm QFN pitch. Either relax `min_track_width`/`min_through_hole_diameter`, or accept the fanout can't be coarser. Do not "fix" it by widening - that breaks the escape.
- [ ] `AM0:15` and `AM1:15` are floating - **tie both to GND**. Two resistors, and it's the only outright defect on the keys sheet.
- [ ] `R38` routing is not a copy of `R34` - R34 is a +3V3 pull-*up*, R38 is a GND pull-*down*. The 5 copied `+5VP EN` segments assume the wrong topology.
- [ ] GND stitching: perimeter, around the RP2350B, under both bucks, and either side of every L4 trace crossing an L3 pour boundary.
- [ ] Refill zones (`B`), run DRC, and confirm the `PD_TRUNK*` / `CORNER_VOID_*` rule areas exist - **the rules that depend on them are inert until they do, with no error shown.**

---

## Appendix - every net, ranked

242 multi-part nets excluding GND. **`READY`** = every part already on the board. **`blocked`** = waiting on placement.

| tier | nets | routed | ready now | blocked |
| --- | :---: | :---: | :---: | :---: |
| **A** geometry *is* the spec | 29 | 26 | **3** | 0 |
| **B** needs area / loop discipline | 31 | 6 | 1 | **24** |
| **C** constrained but forgiving | 62 | 30 | 8 | 24 |
| **D** meander freely | 120 | 11 | 59 | 50 |
| | **242** | **73** | **71** | **98** |

**Tier A is 90% done and its last three are all ready.** That's the whole argument for the phase order: route those, then place, because Tier B's 24 blocked nets are the power section and placing it unlocks nearly all the remaining constrained work.

### Tier A - route these before anything else
| net | status | why |
| --- | --- | --- |
| `AM0`, `AM1` | **READY** | mux→ADC. every keystroke arrives here at 12 bits |
| `/VREG_LX` | **READY** | core-regulator switch node - minimise copper area |
| `USB1/2 D±`, `/MCU D±`, `USB D±` | routed | 90Ω pair |
| `/QSPI_*`, `/FLASH*_SS`, `FLASH CS1n` | routed | up to 133MHz, the fastest bus here |
| `/XIN`, `/XOUT`, `Net-(C4-Pad1)` | routed | crystal - loading pulls the oscillator |
| `SW CLEAN`, `SW NOISY` | routed | switch nodes, high dV/dt |
| `Net-(U5/U6-BOOT)` | routed | bootstrap flying node |
| `Net-(U5/U6-FB)`, `Net-(C30/C36-Pad1)` | routed | buck feedback - high-Z, keep off SW |

### Tier B - unlocked by placing the power section
24 of 31 are blocked. In rough order of how much geometry matters:

1. `PD+` (21 parts) and `VBUS` (14) - **5A**. Pour, not trace; ≥4 vias per transition.
2. `PD+ TOP/RIGHT/BOTTOM/LEFT` - 4A each, 1.2mm floor. `PD+ BOTTOM` is already **READY**.
3. `Net-(U11A-+)`, `Net-(U10-REF)`, `+1V24ref`, `VDIV` - the comparator/reference node. **This is where the guard-trace rule applies.**
4. `Net-(Q4/Q5/Q7-G)`, `Net-(Q8..Q11-B/C)`, `Net-(Q3-B/C)` - gate-drive loops, keep each FET/BJT pair tight.
5. `BS+ SRC`, `SM+`, `/power/SM BUS` - rails, claim area before signals fill in.

### Tier C - after the above
30 already routed (the `AM0:x`/`AM1:x` sensor channels). Remaining: the 8 corner UARTs (**READY**), 8 side UARTs, 4 `* ID` dividers, `AS0`-`AS3`, both I²C buses, `LED SCK`/`LED TX`.

### Tier D - last, 120 nets
59 are **READY** and 58 of those are the SK9822 chain. Everything here takes whatever is left over by design. Also: all the `EN` nets, `USB SEL`, `SM+ FLT`, `PD EN *`, and the auto-named stubs.

> **One classifier miss worth knowing:** `USB D+` / `USB D-` - the segment between U2's common pins and the R7/R8 series resistors - sorted into Tier D because the name doesn't match the `USB1/USB2/MCU` pattern. They're **Tier A**; they're part of the same 90Ω chain. Already routed, so no harm, but don't let the tier label mislead you if you rework that area.

back to [index](index.md)
