# Schematic build log

Dated, newest-on-top. A few lines per session: what got wired/decided, what tripped me up, what's open, what's next. This is the "pick back up after being busy" page - read the top entry and you're back in it.

Calc details live in the [schematic-design pages](index.md); wiring progress in the [checklist](../schematic-checklist.md).

---

## 2026-07-05 (session 4) - front-end done, all snags + cleanup closed
Worked through every open item from the reviews. The whole power + USB/PD front-end is now done (bar a cap-derating pass). Full as-built writeup in [implementation](implementation.md#resolved---the-front-end-as-built).
- **all 4 cold-start snags fixed:** LDO→BS+, ref R21→VBUS (20k), CC direct + 2× FUSB302BMPX on separate buses + TS3USB30E data mux, Q1 R35→1M.
- **cleanup done:** hysteresis (R22 10k + R46 1M on U11A), trip retarget to ~5.73V (R30→44.2k), gate soft-start (C44/C45), Q3 base-emitter R47 100k, mux VCC→3V3.
- **PD decision locked:** B (2× FUSB302), and running **2 I²C buses** so both are the plain BMPX (cheaper, 1 BOM line) - pins GPIO30/31 for I2C1, budget now 40/48.
- **docs updated:** [chips](../chips.md) (dropped TLV1805/AO3415/TMUX1574, added LM2903/TLV431/AO4407A/AO3401/BC857/BZX84C10/TS3USB30E/2× FUSB302), [comms](../design-choices/comms.md), [pin-budget](../design-choices/pin-budget.md).
- **only open item:** cap voltage-derating pass on VBUS/PD+ ceramics (≥25-35V).
- **Next:** the cap-derating pass, then on to the next sheet (MCU / keys / RGB).

## 2026-07-05 (session 3) - built the front-end out, second review caught cold-start latches
Drew the full switching circuit (LM2903 dual comparator + TLV431 + Q1/Q2/Q3), including the **enable-from-trigger** trick: U11A runs both switches, U11B (swapped inputs + 3V3 pull-up) drives the clean-buck EN off the *same* comparison, so the buck enable doesn't depend on PD+ (the rail it's starting). Full write-up in [implementation](implementation.md#build-out--the-actual-switching-circuit).

Then a second review pass - aimed at **cold-start bring-up order**, not steady-state - found three latches the first pass (mine) missed:
- **LDO on +5VA → boot deadlock** → LDO VIN moved to **BS+**.
- **TLV431 ref on +3V3 → cold-start latch** (comparator boots wrong state, holds itself off) → bias **R21/TLV431 from VBUS**.
- **CC through the unpowered mux → Rd never reaches the connector passively → source never gives VBUS.** confirmed receptacle. root cause: 1 FUSB302 = 2 CC pins, 2 orientation-independent ports need 4. **reopens the [comms](../design-choices/comms.md) CC-mux decision** - fix is either (A) 5V-only secondary port or (B) 2× FUSB302. UNDECIDED.
- also: Q1 wasn't fully turning off (R35 100k→**1M**).
- still-to-do: U11A hysteresis + drop trip to ~5.75V, gate soft-start (inrush), Q3 base-emitter R, cap voltage derating.
- **lesson:** every latch was a rail depending on something downstream of itself. walk the bring-up order explicitly.
- **Next:** decide the CC architecture (A vs B) - that's the blocking one.

## 2026-07-05 (session 2) - started drawing the front-end, hit a comparator snag
Went to actually implement the VBUS front-end and reality pushed back. Documented as **implement → snags → re-brainstorm → re-select** in [implementation](implementation.md#vbus-front-end-the-6v-handoff) (didn't touch the original plan in [power](power.md) - kept it as the record).
- **XC6220:** output is factory-fixed (331=3.3V), no external divider. Caps got swapped on the board → should be **Cin 10µF / Cout 4.7µF**.
- **Bucks:** TPS54302 is a buck → **can't make 5V below ~9V in**; PD steps (5/9/12/15/20) mean lowest usable input is **9V**. Doesn't break bootstrap (pre-PD BS+ is raw VBUS via the P-FET, not the buck). Ref-design starting values recorded (L=10µH, R2=100k, R3=13.3k, C6=75pF, 2×22µF out).
- **Comparator snag:** almost powered the TLV1805 from the node it switches (bootstrap loop). Fix = power the detector from **VBUS upstream**, not the switched node.
- **Re-select leaning B:** wide-Vin **voltage supervisor** (TPS3760-class) + discrete Q1/Q2, over keeping the discrete comparator (A) or a mux+eFuse (C, reintroduces the 60V TPS1663 cost on the 20V PD+ path).
- **STILL OPEN:** verify TPS3760 specs; Q2 device + gate drive; consider a B/C hybrid (power-mux just for BS+).
- **Naming to reconcile:** the KiCad session called the shared 5V `+5V_BUS`; the vault calls it `BS+`. Pick one so nets match docs.
- **Next:** confirm the supervisor part, then finalize Q1/Q2 + the buck UVLO/EN divider.

## 2026-07-05 - front-end topology settled (on paper)
- Worked out the **VBUS front-end** wiring: 2× SS54 combine ports → VIN; TLV1805 comparator watches VIN and drives Q1 (VBUS→BS+, default on) + Q2 (VBUS→PD+, default off) at ~6V.
- **Decided:** 3V3 LDO taps **BS+**, not the clean-buck output - otherwise chicken-and-egg (buck needs PD+ needs MCU needs 3V3). BS+ is live the instant any cable's 5V arrives.
- **Decided:** backfeed protection = **SS54 Schottky per port** on the VBUS→PD+ path (Schottky fine on HV rail).
- **Fixed BOM error:** LDO was listed `XC6220B332MR / 300mA / SOT-23-3` - real part is **XC6220B331MR, 1A, SOT-25 (5-pin, CE)**. CE ties to VIN (always-on).
- **Conventions locked:** net names PD+/BS+/gated-5V/3V3/GND; 0402 default for R/C/jumpers (exceptions: inductors, HV-rail bulk caps, SMA diodes); 0Ω/jumper on all digital enable/select pins (default populated).
- **STILL OPEN:** Q2 device type + gate drive (P-FET vs N-FET+charge pump); comparator reference source + hysteresis values; steno flash 2nd-chip vs boot-only.
- **Next:** clean-buck TPS54302 feedback divider + inductor math → [power](power.md#clean-buck--tps54302).

---
Back to [schematic-design index](index.md)
