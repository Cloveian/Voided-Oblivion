# Implementation log - reality vs the plan

ok so this is where actually drawing the thing in KiCad smacks into the plan. the [checklist](../schematic-checklist.md) and the [calc pages](index.md) are what i *meant* to build. this is what actually happened when i sat down and drew it - what i placed, what broke, and anything that made me re-open a decision i thought was already done.

same shape as the design-choices pages when something forces a rethink: **Implement → Snags → (re)Brainstorm → (re)Select.** i'm leaving the original plans alone in their own pages on purpose - this isn't me quietly editing history, it's the "here's where reality pushed back" layer.

newest stuff on top. dated notes live in the [build log](log.md).

---

# Capacitor footprints

*(the one that would actually have stopped the board)*

## Snag
Ran a proper audit of every cap ≥1µF against the footprint it's been assigned. **Five parts have values that don't exist in the package they're drawn in, and two more are on a 20V rail in a package that only exists at 6.3V.**

| Ref | Value | Footprint | Net | Problem |
| --- | --- | --- | --- | --- |
| C28, C29 | 22µF | 0402 | +5VA | 22µF **does not exist** in 0402 |
| C34, C35 | 22µF | 0402 | +5VP | same |
| C41 | 100µF | 0402 | BS+ | 100µF **does not exist** in 0402 |
| C26, C31 | 10µF | 0402 | **PD+, up to 20V** | 10µF 0402 exists only at ≤6.3V rating |
| C24 | 10µF | 0402 | BS+ (~5.7V) | marginal at 6.3V |
| C40 | 10µF | 0402 | +3V3 | fine (6.3V part OK here) |

C26 and C31 are the serious pair - a 6.3V-rated part sitting directly on a rail that reaches 20V isn't a derating question, it's a part that fails.

## Why the old note didn't catch it
There's been a "cap voltage-derating pass" open in the [build log](log.md) since session 4. **That framing was wrong and that's why it stayed open harmlessly for so long.** Derating assumes the part exists and just loses capacitance under DC bias - you order it, measure it, and add more. Here the parts can't be ordered at all. It's a footprint/BOM error wearing a derating error's clothes.

Worth naming the actual mistake: I picked values from TI's reference design (44µF output is straight out of Table 7-2, and it's the *right* number) and never went back to check that the value and the assigned footprint could coexist. The electrical design was fine. The BOM wasn't buildable.

**Generalised lesson, same shape as the cold-start ones: a value being correct doesn't mean the part exists.** Reference designs give you values, not orderable parts. Worth a standing check before any fab order - sweep every passive for value-vs-package sanity.

## Fix
- **PD+ rail (C25, C26, C31, C32):** 25V minimum, **50V preferred** - at 20V bias a 25V X7R sits at 80% of rated and deep in the steep part of the derating curve; a 50V part at 40% is barely bending. **0805 or 1206.** The 0.1µF parts can stay 0402 if rated ≥25V.
- **Buck outputs (C28/C29, C34/C35):** keep 44µF total (TI's own number), realise as 2×22µF in **0805/1206 at 16–25V**, and check the chosen part's actual DC-bias curve - half the nominal can vanish at 5V bias in a small case.
- **C41 (100µF on BS+):** see below - the recommendation is to **delete it**, which fixes this and the inrush problem at once.
- **C24 (10µF on BS+):** 0603/0805 at 16V.

## And while auditing, a second thing fell out
C41 isn't just an impossible footprint - it's **actively harmful**. USB Type-C caps a sink at **10µF between VBUS and GND before attach** (Table 4-3). Q1 is default-ON by design, so everything on BS+ is presented to the connector as VBUS ramps:

```
C24  10 uF  +  C41 100 uF  =  110 uF   vs a 10 uF ceiling  ->  11x over
```

With Q1's existing 1nF Miller soft-start that's roughly 550mA of inrush, against the 500mA a source gives by default before negotiation. That's the "droop/renegotiate loop" risk that's been half-open since the round-2 review.

**C41 has no derivation behind it.** The LDO's datasheet asks for Cin = 10µF and C24 already provides it. **Deleting C41 takes attach capacitance to exactly 10µF and removes an unbuildable part.** One deletion, two problems gone. If bulk on BS+ turns out to be wanted later it belongs behind something that isn't presented at attach.

## To do
- [ ] Respec C25/C26/C31/C32 for the 20V rail (0805/1206, ≥25V, prefer 50V)
- [ ] Respec C28/C29/C34/C35 to 0805/1206, 16–25V, check DC-bias curves
- [ ] **Delete C41**
- [ ] Respec C24 to 0603/0805 16V
- [ ] Sweep every remaining passive for value-vs-footprint sanity before fab

---

# RGB level shifter

*(right part, wrong reasoning - and the wrong rail)*

## Implement (what i drew)
put a **74AHCT125 (U8)** on the keys sheet buffering `LED SCK` / `LED TX` up to 5V for the SK9822 chain, powered off **+5VP** (the gated buck). i put it in on the "better safe than sorry" instinct without actually opening the SK9822 datasheet first.

## Snags
1. **it wasn't a judgement call at all.** SK9822-EC20 §9 says **VIH min = 3.4V**. the 3V3 rail's absolute best case is 3.366V (XC6220 at +2%). so direct drive was never "marginal" - it's out of spec at every condition, always. the buffer was *mandatory* and i'd added it on a hunch. right answer, wrong reasoning, and i only found that out by going back and reading the table. full math in [rgb](rgb.md#spi-drive---sckdata-series--level-shift).
2. **the family i'd have reached for next doesn't work.** if i'd gone looking for something smaller than a quad, the obvious grab is the 74LVC1G125 (cheapest buffer on LCSC, 89k in stock). at VCC 4.5–5.5V its VIH is **0.7×VCC = 3.5V** - so it fails the exact same way direct drive does. **AHCT/HCT have a flat 2.0V VIH at 5V; LVC does not.** noting it loudly because "LVC is the modern cheap one" is a habit that would have quietly produced a broken board.
3. **the real one: the shifter is on a rail that switches, and the MCU isn't.** the SK9822s (and U8) sit on gated-5V, the MCU sits on always-on 3V3. so any time the big buck is off - pre-PD, or firmware capping RGB - the MCU can drive SPI0 into a buffer whose VCC is 0V. the 74AHCT125 has **no Ioff**, so its input clamp diodes conduct and the MCU starts back-feeding a rail that's meant to be dead, through its own SPI pins.

   this is the **same shape as all four cold-start latches**: something alive feeding something that's supposed to be off. i caught those by walking the bring-up order on the front end and then just... didn't do that pass on the RGB block. the lesson didn't transfer sheets.

   - **the obvious fix doesn't work:** "power U8 off BS+ instead, it's always on." then the shifter drives 5V into 30 *unpowered* SK9822s and i'm back-feeding through 30 sets of LED input clamps instead of one buffer's. strictly worse.
   - **the actual fix:** keep the shifter on the gated rail so the whole RGB domain dies together, and use a part that tolerates its output rail being dead - i.e. one specified for **partial-power-down (Ioff)**.

## Re-Select
full unbiased scoring (with the gates, LCSC stock, and the weighted table) lives in [rgb](rgb.md#picking-the-level-shifter). outcome: **SN74LVC2T45** (C15741, VSSOP-8) - dual-supply VCCA=3V3 / VCCB=gated-5V, DIR tied high, VIH 2.0V referenced to VCCA, Ioff. exactly 2 channels, no wasted gates. 323/370 vs 186 for the AHCT125 that's currently on the board.

**why i'm not just leaving the AHCT125 in:** the alternative to Ioff is a rule that says *firmware must never touch SPI0 while the big buck is off*. that's a software-correctness promise held forever across every future firmware change, and i already refused that trade in [comms](../design-choices/comms.md) for the both-ports-plugged case. $0.16 to make it a hardware property instead is an easy yes.

### done on the board
- [x] **U8 is now SN74LVC2T45DCUR** (VSSOP-8), VCCA→+3V3, VCCB→+5VP, DIR→+3V3 via R62 0Ω
- [x] **33Ω series on the B (5V) side**: R63 → LED1 SDI, R64 → LED1 CKI
- [ ] decoupling per supply pin - TI wants 0.1µF on *each* VCC (§8.3.1); check both are placed

as-built table in [rgb](rgb.md#as-built-done).

---

# VBUS front-end (the ~6V handoff)

the planned front-end (TLV1805 comparator + AO3415 + Q2) lives over in [power](power.md#threshold-detector---lm2903-u11). here's how drawing it actually went.

## Implement (what i drew / grabbed from datasheets)
- **XC6220 3V3 (U7):** placed it, CE→VIN through a 0Ω (R12). turns out the output is **factory-fixed** by the `331` code - the R1/R2 divider is *inside the chip*, so there's nothing to tune on the board. cap pairing for the 3.00–3.50V row is **Cin = 10µF, Cout(CL) = 4.7µF**, low-ESR ceramic, jammed as close to the pins as i can get it.
- **Bucks (TPS54302):** yoinked the 5V starting values straight off Table 7-2 / the ref design - **L = 10µH, Cout = 2×22µF (25V), R2(top) = 100k, R3(bot) = 13.3k, C6 = 75pF, fsw 400kHz**, Cin ≥10µF at ≥25V.
- **Comparator (TLV1805):** dropped it in to do the ~6V VBUS→BS+ / VBUS→PD+ handoff like the plan says.

### Snags (what bit me)
1. **the XC6220 caps came out swapped** on the board (Cin 4.7 / Cout 10). datasheet's 3.3V row wants them the other way round - Cin 10 / Cout 4.7. just a value swap, no BOM change. (if i left Cin at 4.7 i'd need a chunky 47µF output to stay in Torex's characterized set, no thanks.)
2. **the TPS54302 can't make 5V out of 5V.** it's a *buck* - the input has to sit a good bit above the output, realistically **≥~7–9V** to actually hold 5V under load (that's exactly why TI's own ref design starts VIN at 8V). and PD only hands out **5 / 9 / 12 / 15 / 20V**, nothing between 5 and 9 - so the **lowest input i can actually use is 9V**. both bucks really live at **9–20V**, not 5–20V like i wrote.
   - *does this kill pre-PD bootstrap?* **nope.** pre-PD, BS+ comes from raw VBUS 5V through the AO3415 P-FET, **not** the buck. the buck only takes over BS+ once PD ramps ≥9V. so that "clean buck must start ~5.5V" line back in the plan was never actually doing any work - the buck's real job doesn't kick in till 9V. (leaving the wrong note in [power](power.md#clean-buck---tps54302-u5) alone for the record, this here is the fix.)
3. **the comparator eats its own tail (this is the real one).** i was about to power the TLV1805 off the exact node it's switching → classic bootstrap loop: the second it flips away from a source it browns out its own supply and starts chattering. the one-liner i'll remember: **power the detector off a node its own output can't cut.**

## Re-Brainstorm - the ~6V handoff
the handoff is secretly doing **two** jobs off one ~6V trip point:
- **(a) VBUS→BS+:** on below 6V (raw 5V feeds bootstrap), *off* above 6V (keep BS+ from climbing past 5V).
- **(b) VBUS→PD+:** the opposite - *on* above 6V so VBUS joins the HV rail.

the thing that clicked from the snag: power the detector **off VBUS itself (upstream)** - VBUS is there whenever a cable is, and the detector only cuts stuff *downstream* of VBUS, so it never chops its own supply. no loop. that reframes the whole thing:

- **A - keep the discrete comparator (TLV1805), just fixed.** power it off VBUS instead of BS+/PD+, bolt on a reference + hysteresis network, drive Q1 (VBUS→BS+ P-FET) and Q2 (VBUS→PD+ switch). fixes the loop but i'm still hand-rolling a reference + hysteresis + a high-side Q2 gate drive.
- **B - wide-Vin voltage supervisor** (something like the TPS3760, 2.5–60V, adjustable trip, reference + hysteresis baked in, open-drain out). power it off VBUS, one divider sets the 6V trip, its output (+ the inverse) drives Q1/Q2. deletes the whole reference/hysteresis fiddling and keeps two cheap discrete switches that shrug off 20V.
- **C - go integrated / flip the framing.** treat **BS+ as "just auto-grab the highest 5V around"** with a power-mux (TPS2116, 1.6–5.5V) sitting between raw VBUS and the clean-buck 5V - that **straight up deletes the VBUS→BS+ comparator + P-FET.** then gate **VBUS→PD+** with an eFuse-with-UVLO. the catch: PD+ hits 20V so the eFuse has to be ≥24V - TPS2595x (18V) is out, which drags me back to the **TPS1663 (60V)**, aka the pricey part i already dodged on the HV switches. so it sneaks that cost right back in.

## Re-Select - front-end handoff (draft scores, gotta sanity-check before i commit)

| Criteria | Weight | A: comparator (fixed) | B: supervisor + discrete | C: mux + UVLO-eFuse |
| --- | :---: | :---: | :---: | :---: |
| No self-reference / bootstrap loop | 9 | 6 | 9 | 9 |
| Handles both jobs (BS+ cut + PD+ connect) | 8 | 8 | 9 | 8 |
| Vin headroom to 20V | 8 | 8 | 9 | 6 |
| Hardware-only (hotplug, no firmware) | 8 | 9 | 9 | 9 |
| Fewest hand-tuned analog nets | 6 | 3 | 8 | 9 |
| Part count / cost | 6 | 7 | 7 | 4 |
| Implementation risk | 6 | 5 | 8 | 6 |
| **Weighted draft total** | | **352** | **429** | **371** |

**leaning B: wide-Vin supervisor (built from an LM2903 + TLV431, see below) + discrete Q1/Q2.** it kills the reference/hysteresis/self-power mess (the actual snag), stays all-hardware so hotplug still works, and the discrete switches stay cheap and clear 20V without dragging a 60V eFuse into it. **C** is genuinely slick on the BS+ side (that power-mux really does delete a whole switch) but the 20V PD+ path forces the expensive TPS1663 i already said no to. **A** is salvageable but i'm hand-building a reference + hysteresis + Q2 gate drive for basically no win over just using a supervisor.

**still open before this is actually decided:**
- nail down the LM2903 + TLV431 divider + hysteresis resistor values for the 6V trip (rough cut ~47k / 12.2k, needs tuning) - those draft scores are still a first pass.
- Q2 (VBUS→PD+) still needs a device + gate drive picked (P-FET high-side vs N-FET + charge pump) - carries over from [power](power.md#q2q3d4---vbuspd-switch-ao4407a--bc857--bzx84c10).
- if i end up loving the power-mux for BS+ (the one genuinely nice bit of C), i could steal just that and still gate PD+ with the supervisor + discrete switch - a B/C mashup worth a look.

### actually picking the supervisor
went to actually pick the supervisor and... the TPS3760 just isn't on LCSC/JLCPCB. and TI's supervisor catalog in general is patchy there, especially the wide-Vin adjustable ones. so instead of chasing a fancy integrated part i'm building the "supervisor" out of jellybeans JLC always stocks:

- **LM2903** - the comparator. **3–36V supply**, so i power it straight off VBUS and it rides the whole 5→20V ramp no sweat. this is the sweet spot: cheap, everywhere, and rated way past 20V.
- **TLV431** - 1.24V shunt reference, like a cent, always in stock. this is the stable thing the comparator measures against.
- divider on VBUS into one comparator input, TLV431 into the other, plus one feedback resistor for hysteresis so it doesn't chatter at the trip point.
- **trip math:** divide VBUS so 6V lands on the 1.24V ref (ratio ≈ 4.84, e.g. **47k / 12.2k**), and the feedback resistor sets how wide the hysteresis is. numbers are a rough cut, gotta tune.

**the honest catch:** this is *exactly* the reference + hysteresis network i said option B skips. so building it out of an LM2903 + TLV431, B kinda slumps back toward A - i'm hand-rolling the reference either way. the real reason B still beats the original TLV1805 plan is dumber and more practical than "it's integrated": **LM2903 is actually stocked and 36V-rated**, and powering it off VBUS (not the node it switches) is the bit that genuinely kills the self-reference loop. same idea, boringly-available parts.

## Build-out - the actual switching circuit
ok, drew the whole front-end. what landed:
- **reference:** TLV431 (U10) as a plain shunt - R27 (0Ω) straps ref→cathode, R28 is a DNP footprint for a future divider if i ever want a different ref voltage. C37 1nF. out = **+1V24ref**.
- **the divider:** R30 47k / R31 12.2k off VBUS → **VDIV**, trips at 6.02V. bang on.
- **dual comparator (LM2903):**
  - **U11A** (+ = VREF, − = VDIV): goes LOW above 6V → drives **both Q2 gate AND Q3 base**. one comparator runs both switches since they want the same polarity.
  - **U11B** (+ = VDIV, − = VREF, *inputs swapped*): goes HIGH above 6V, pulled to 3V3 via R34 → drives the **clean buck EN**.
- **Q2 (AO4407A):** VBUS→PD+. default OFF (R32 100k gate→VBUS), D4 zener clamps Vgs, U11A sinks it on above 6V.
- **Q1 (AO3401):** VBUS→BS+. default ON (R35 pulldown), Q3 (BC857 PNP) yanks the gate up to turn it off above 6V.

### the enable-from-trigger thing (the good bit)
i wanted the clean buck EN driven by the *same comparison* that connects VBUS→PD+, NOT by a divider off PD+ - because PD+ is the thing being started, and i don't want the buck's enable to depend on the rail it's about to run from. the move: both switches want "active LOW above 6V" so they share **U11A**; the buck EN wants "HIGH above 6V" so it gets **U11B** with swapped inputs + a 3V3 pull-up. spent both halves of the dual comparator, no extra parts, EN is a clean 0/3.3V level. the buck's own VIN UVLO backstops it, so an early EN during startup does nothing (no PD+ = no output).
## Snags round 2 - cold-start bring-up (a second review pass caught these)
the topology was fine but nobody had walked the *power-on order* - who's alive before whom. that's where all the nasty ones hid. logging honestly: the first review (walking the steady-state circuit) passed it; a second pass aimed specifically at cold-start bring-up found these latches. **lesson up front: topology being right ≠ the board booting.**

1. **LDO fed from +5VA → boot deadlock.** the 3V3 LDO took its input from the clean-buck output (+5VA), but pre-PD the clean buck is off → +5VA = 0 → 3V3 = 0 → MCU can't boot → can't negotiate PD → buck never turns on → dead. **fix: LDO VIN → BS+** (alive pre-PD from VBUS via Q1). 3V3 exists the moment a cable gives 5V.

2. **reference fed from +3V3 → cold-start latch.** same class of bug, nastier. the TLV431 bias (R21) came off +3V3, which is 0 at cold start. so +1V24ref = 0 → U11A sees VDIV > 0 → outputs LOW → turns Q2 on and **Q1 off** → BS+ never charges → 3V3 stays 0 → ref stays 0 → **latched off forever.** the comparator boots into the wrong state and holds itself there. **fix: bias R21/TLV431 from VBUS, not +3V3** (~0.4–1.9mA across 5–20V, fine; nudged R21 toward 20k to keep the 20V current sane). then at 5V the ref is 1.24V, VDIV ≈ 1.03V, U11A goes high → Q1 on → bootstraps. *(this one's on me - i'd "validated" the +3V3 bias earlier by checking the bias current and never asking whether +3V3 even exists at power-on.)*

3. **CC through the unpowered mux → source never applies VBUS (the big one).** the Rd that tells a USB-C source "i'm a sink, give me power" lives in the FUSB302 - but it sits on the *mux side* of the TMUX1574, whose VDD is BS+. at cold attach BS+ = 0 → mux open → the connector's CC pin floats → source sees no Rd → never applies VBUS → no BS+ → mux never powers. chicken-and-egg, and you can't LDO your way out because there's no voltage anywhere until Rd reaches the connector passively.
   - **confirmed it's a receptacle** (not a plug), so Rd-on-both-CC-pins is normal - that part's fine, it's not a Debug-Accessory issue.
   - real root cause: **one FUSB302 has 2 CC pins, but two orientation-independent receptacle ports need 4.** the CC-mux (chosen back in [comms](../design-choices/comms.md)) was the attempt to share one PHY across both - and muxing CC is exactly what breaks the cold-start Rd.
   - **fix options (undecided, needs a real call):**
     - **(A) 5V-only secondary:** FUSB302 CC1/CC2 wired *straight* to port 1's two CC pins (full PD + passive Rd on port 1); port 2 gets passive **5.1k Rd** on its CC pins → 5V-only. no CC mux at all, kills the deadlock. downside: a tile cabled only on port 2 is stuck at 5V.
     - **(B) 2× FUSB302** (one per port, CC direct): both ports full PD + passive Rd. ~$0.60 + an I²C address more per tile. probably what the "any port can power the array" goal actually wants.
   - **this reopens the [comms](../design-choices/comms.md) dual-USB-C decision** - the CC-mux option won the table but doesn't survive the cold-start sequence. either way the D+/D− mux stays; only the CC handling changes. (full re-Select is on the [comms revisit](../design-choices/comms.md#revisit-pdcc-architecture-the-cc-mux-doesnt-survive-cold-start).)

4. **Q1 didn't fully turn off.** the Q3 pull-up (R36 10k) fought the Q1 gate pulldown (R35 100k) → gate only reached 0.9×VBUS → Vgs ≈ −1.8V, past the AO3401 threshold → Q1 leaky → VBUS bleeds into BS+. **fix: R35 → 1M** so the pull-up wins, gate → ~VBUS, Vgs ≈ −0.2V, clean off. (Q2 doesn't have this problem - its gate is pulled straight to VBUS by R32 with nothing fighting it.)

### still-to-do (real but not showstoppers)
- **hysteresis + margin:** add a few hundred mV of positive feedback around U11A, and drop the trip to ~5.75V (above vSafe5V's 5.5V) so BS+ doesn't get dragged to the TMUX1574 / XC6220 6V ceiling with zero margin.
- **inrush / soft-start:** Q1/Q2 hard-switch into discharged bulk caps, past USB's 10µF attach limit → can trip source OCP and cause a droop/renegotiate loop. RC on each gate (keep the zener).
- **Q3 base-emitter resistor:** ~100k B→E so leakage can't partially bias it when hot.
- **cap derating:** the 10µF ceramics on VBUS/PD+ lose most of their value at 20V bias - do an explicit voltage-rating pass (25–35V parts).

### the takeaway
every one of these latches came from a rail depending on something *downstream of itself* (LDO on the buck it's meant to bootstrap, ref on the 3V3 it's meant to create, Rd behind the mux the Rd is meant to power up). **walk the bring-up order explicitly** - steady-state review will not catch this class of bug.

## Resolved - the front-end as-built
all of it is fixed on the board now. final state, snag by snag:

- **snag 1 (LDO on +5VA → deadlock):** ✅ LDO VIN → **BS+**.
- **snag 2 (ref on +3V3 → latch):** ✅ TLV431 bias R21 → **VBUS**, bumped to **20k** (so the 20V draw is ~0.9mA, still >100µA at 5V).
- **snag 3 (CC through the mux):** ✅ full USB/PD rework — CC **direct** to each connector, **2× FUSB302BMPX on separate I²C buses** (PD1→I2C0 GPIO20/21, PD2→I2C1 GPIO30/31, INTs GPIO15/18), data-only mux is now the **TS3USB30ERSWR** (VCC on 3V3, built-in D± ESD), SEL still 5.1V-clamped. Rd now sits passively at each connector. decision in the [comms revisit](../design-choices/comms.md#revisit-pdcc-architecture-the-cc-mux-doesnt-survive-cold-start), pins in [pin-budget](../design-choices/pin-budget.md) (40/48 GPIO).
- **snag 4 (Q1 leak):** ✅ R35 → **1M** (gate reaches ~VBUS when off, Vgs ≈ −0.2V).

and the cleanup items, all done:
- **hysteresis:** R22 (10k series, +1V24ref→U11A+) + R46 (1M feedback, U11A out→U11A+); U11B taps the raw ref. ~200mV.
- **trip retarget:** VDIV 47k→**44.2k** / 12.2k → **~5.73V** (above vSafe5V 5.5V, below the ~6V LDO ceiling — BS+ gets dragged to the trip during the 5→9V handoff).
- **gate soft-start:** C44 (Q2) + C45 (Q1), 1nF each.
- **Q3 base-emitter:** R47 **100k** (base→VBUS).
- **mux VCC → 3V3** (off BS+, immune to the handoff spike).

### the one thing still open
- **cap voltage-derating pass:** the 10µF ceramics on VBUS/PD+ (up to 20V) lose most of their value at bias — respec **≥25–35V X5R/X7R** and size for the derated value. not a showstopper, just a values pass.

so: the whole power + USB/PD front-end is done bar the cap-derating pass. parts are in [chips](../chips.md).

---
Back to [schematic-design index](index.md) · [build log](log.md) · [checklist](../schematic-checklist.md)
