# High-side P-FET switching and gate drive - datasheet research
> Independent datasheet read. Not written against the existing schematic.

**Scope**: six high-side P-FET switch positions (VBUS→BS+, VBUS→HV, and four HV edge-distribution switches), their level-shift BJTs, Vgs zener clamps, and the SS54 backfeed-blocking Schottky. Every number below is cited to a specific datasheet, file, and page/table. Where a graphical curve (SOA, transient thermal impedance) can't be read as an exact number from `pdftotext -layout` output, this is stated as "not specified" rather than estimated.

**Two findings surfaced by this read that belong at the top, before the detail:**

1. **The file `Refrences/datasheets/SS54-schottky.pdf` is not an SS54 datasheet.** It is Diodes Inc.'s `1N5817-1N5819` datasheet (1 A, DO-41 axial, 20/30/40 V) — see Gotchas. All SS54 numbers in this document come from a freshly-fetched, correctly-matched datasheet, saved as `Refrences/datasheets/ss54-schottky-actual-mdd.pdf` (MDD Microdiode Semiconductor, SS52–SS5200 series, LCSC C22452, the JLCPCB basic-part listing for "SS54").
2. **The two AO3401A datasheets already in the folder disagree with each other** on Vgs(th) max, IDM, RDS(on), and body-diode Vf. Both are used below; the worse-case figure from either is what the design should be sized against, since JLCPCB/LCSC basic-part sourcing does not guarantee which fab supplies the die.

Datasheets fetched for this task (missing at start, now saved lowercase-hyphenated per instructions):
- `Refrences/datasheets/bc857-pnp.pdf` — BC856…BC860, Semtech Electronics Ltd., LCSC C148244
- `Refrences/datasheets/bc847-npn.pdf` — BC846…BC848, Zhuhai Hongjiacheng ("ichjc"), LCSC C20069135 (BC847B, preferred/basic)
- `Refrences/datasheets/bzx84c10-zener.pdf` — BZX84C2V4…BZX84C75, Zhuhai Hongjiacheng, LCSC C19077470 (BZX84C10, preferred)
- `Refrences/datasheets/bzv55b5v1-zener.pdf` — BZV55B series, LGE, LCSC C545327 (BZV55B5V1, only listing)
- `Refrences/datasheets/ss54-schottky-actual-mdd.pdf` — SS52…SS5200, MDD Microdiode Semiconductor, LCSC C22452 (basic part)

---

## Part identity (every FET, BJT, zener, diode)

| Ref | Part | Package | Manufacturer / datasheet used | Role |
|---|---|---|---|---|
| Q_SW1 | AO3401A | SOT-23 | Alpha & Omega Semi (`AO3401A-pfet.pdf`) **and** a second-source clone from "hs-semi.cn" (`AO3401A-pfet-lcsc.pdf`) — see Gotchas | Switch 1: VBUS→BS+ (5 V bootstrap), default ON |
| Q_SW2 | AO4407A | SOIC-8 | Alpha & Omega Semi (`AO4407A-pfet.pdf`) | Switch 2: VBUS→HV rail, default OFF, full port current |
| Q_SW3…6 | AO3401A ×4 | SOT-23 | Same dual-source situation as Q_SW1 | Switches 3–6: per-edge HV distribution, default OFF, soft-start + current sense |
| Q1 (PNP) | BC857 | SOT-23 | Semtech Electronics Ltd. (`bc857-pnp.pdf`) | Switch 1 only: active pull-up that forces Gate→Source (commanded OFF) |
| Q2 (NPN) | BC847 (preferred) or MMBT2222A | SOT-23 | Hongjiacheng (`bc847-npn.pdf`) / onsemi (`MMBT2222A-npn.pdf`) | Level-shift translator for all six gate-drive networks |
| D_z1 | BZX84C10 | SOT-23 | Hongjiacheng (`bzx84c10-zener.pdf`) | Gate-source clamp on every AO3401A position (mandatory on 1, 3–6; recommended on 2) |
| D_z2 | BZV55B5V1 | LL-34 (MiniMELF) | LGE (`bzv55b5v1-zener.pdf`) | Candidate for a tighter, lower-voltage clamp (BJT base-emitter reverse protection or a logic-level clamp point) — see Open Questions, no single-clear-use datasheet evidence emerged for this part vs BZX84C10 |
| D_bf1, D_bf2 | SS54 | SMA (DO-214AC) | MDD (`ss54-schottky-actual-mdd.pdf`) | Back-to-back backfeed blocking between two live USB-C ports on the HV rail |

Both AO3401A datasheets describe the same MPN in SOT-23, both list VDS = −30 V, VGS = ±12 V absolute max — the disagreement is in the guaranteed *guardband* numbers (see Absolute Maximums and Key Electrical Characteristics below), not the headline ratings.

---

## Absolute maximum ratings that constrain this design

All values TA = 25 °C unless noted. AOS = official Alpha & Omega sheet; CLONE = the "hs-semi.cn" second-source sheet, both filed under the same AO3401A part number.

| Parameter | AO3401A (AOS) | AO3401A (CLONE) | AO4407A | MMBT2222A(L) | BC857 | BC847 | BZX84C10 | BZV55B5V1 | SS54 (MDD) |
|---|---|---|---|---|---|---|---|---|---|
| VDS / VCEO / VRRM | −30 V | −30 V | −30 V | 40 V (A) | 45 V (VCEO) | 45 V (VCEO) | — | — | 40 V |
| **VGS abs max** | **±12 V** | **±12 V** | **±25 V** | — | — | — | — | — | — |
| VCBO | — | — | — | 75 V | 50 V | 50 V | — | — | — |
| VEBO | — | — | — | 6.0 V | 5 V | 6.0 V | — | — | — |
| ID continuous | −4 A (25 °C) / −3.2 A (70 °C) | −4.2 A (25 °C) / −3.5 A (70 °C) | −12 A (25 °C) / −10 A (70 °C) | 600 mA | 100 mA | 100 mA | — | — | 5.0 A (avg) |
| **IDM pulsed** | **−27 A** | **−19 A** | −60 A | 1100 mA (peak) | 200 mA (peak) | — | — | — | 120 A (8.3 ms surge) |
| PD | 1.4 W(25°C)/0.9 W(70°C) | 1.0 W(25°C)/0.9 W(70°C) | 3.1 W(25°C)/2.0 W(70°C) | 225 mW (FR-5) | 200 mW | 200 mW | 300 mW | 500 mW | not tabulated as PD (thermal via RJA) |
| TJ max | 150 °C | 150 °C | 150 °C | 150 °C | 150 °C | 150 °C | 150 °C | 200 °C | 125 °C (SS52–56 group) |

Sources: `AO3401A-pfet.pdf` p.1 Abs Max table; `AO3401A-pfet-lcsc.pdf` p.1; `AO4407A-pfet.pdf` p.1; `MMBT2222A-npn.pdf` p.1; `bc857-pnp.pdf` p.1; `bc847-npn.pdf` p.1; `bzx84c10-zener.pdf` p.1; `bzv55b5v1-zener.pdf` p.1; `ss54-schottky-actual-mdd.pdf` p.1.

**The line that matters most for this design**: AO3401A's Vgs abs max is ±12 V while the source of Q_SW1 and Q_SW3…6 sits on VBUS/HV, which the project spec puts at 5–20 V. An **ungated gate pulled to GND at VBUS = 20 V produces Vgs = −20 V, which exceeds ±12 V and is outside the manufacturer's rated envelope** on both AO3401A sheets. AO4407A is rated to ±25 V and has 5 V of headroom at the same 20 V condition without a clamp — a materially different risk profile from AO3401A for the same "gate referenced to a floating 5–20 V source" architecture. This is why a zener clamp is mandatory on every AO3401A position and only a margin-improving nicety on the AO4407A position.

---

## Key electrical characteristics

### AO3401A — AOS official (`AO3401A-pfet.pdf`, p.2, Electrical Characteristics)
- Vgs(th): −0.5 V min / −0.9 V typ / **−1.3 V max**, tested at VDS=VGS, ID=−250 µA
- RDS(on): 41 typ / **50 max** mΩ @ VGS=−10 V, ID=−4 A (TJ=25°C); 62/75 mΩ at TJ=125°C; 47/**60** mΩ @ VGS=−4.5 V, ID=−3.5 A; 60/**85** mΩ @ VGS=−2.5 V, ID=−2.5 A
- Body diode: VSD −0.7 typ/**−1.0 max** V @ IS=−1A; IS max continuous −2 A
- Qg: 14 nC typ (10 V drive) / 7 nC typ (4.5 V drive); Qgs 1.5 nC, Qgd 2.5 nC
- trr 11 ns, Qrr 3.5 nC @ IF=−4A
- RθJA: 100 typ/**125 max** °C/W steady-state; 70/**90** °C/W (t≤10s pulse); RθJL 63/80 °C/W

### AO3401A — "hs-semi.cn" clone (`AO3401A-pfet-lcsc.pdf`, p.2)
- Vgs(th): −0.5 min / −0.9 typ / **−1.5 max** V — worse (higher-magnitude) max than the AOS sheet
- RDS(on): 54 typ/**65 max** mΩ @ VGS=−10V, ID=−3A; 64/**75** mΩ @ VGS=−4.5V, ID=−3A; 84/**100** mΩ @ VGS=−2.5V, ID=−2A — worse across the board, and tested at a lower ID
- Body diode: IS max continuous **−4.1 A** (higher than AOS); VSD max **−1.2 V** (worse than AOS's −1.0V)
- Qg (4.5 V drive) 10.9 nC typ; Qgs 1.7 nC, Qgd 2.8 nC
- RθJA: 125 max °C/W steady state (same as AOS); 85 max °C/W (t≤10s) — slightly better than AOS's 90

**Design rule applied throughout this document**: use whichever of the two sheets is worse for each parameter. Concretely: Vgs(th) max = **−1.5 V**, IDM = **−19 A**, RDS(on)@VGS=−10V = **65 mΩ max**, VSD = **−1.2 V max**.

### AO4407A (`AO4407A-pfet.pdf`, p.2)
- Vgs(th): −1.7 min / −2.3 typ / −3.0 max V
- RDS(on): 8.5 typ/**11 max** mΩ @ VGS=−20V, ID=−12A (25°C), 11.5/**15** mΩ at 125°C; 10/**13** mΩ @ VGS=−10V, ID=−12A; 12.7/**17** mΩ @ VGS=−6V, ID=−10A
- Qg total 30 typ/**39 max** nC; Qgs 4.6 nC, Qgd 10 nC; Rg 2.4 typ/3.6 max Ω
- Body diode: VSD −0.7 typ/−1.0 max V @ IS=−1A; IS max continuous −3 A
- trr 30 typ/40 max ns @ IF=−12A; Qrr 22 nC
- RθJA: 60 typ/**75 max** °C/W steady state; 32/**40** °C/W (t≤10s); RθJL 17/24 °C/W

### MMBT2222A (`MMBT2222A-npn.pdf`, p.1–2, "A" grade)
- hFE min: 35 @ IC=0.1mA; 50 @ 1mA; **75 @ 10mA**; 100 @ 150mA — no data below 0.1 mA
- VCE(sat) max: 0.3 V @ IC=150mA,IB=15mA; 1.0 V @ IC=500mA,IB=50mA
- VCBO 75V, VCEO(A) 40V, VEBO 6.0V; ICBO ≤0.01mA @ VCB=60V; RθJA 556°C/W (FR-5 board) / 417°C/W (alumina)

### BC847 (`bc847-npn.pdf`, p.1–2, BC847 rows)
- VCBO 50V, VCEO 45V, VEBO 6.0V; IC 100mA, PC 200mW; RθJ-A **625 °C/W** typ
- hFE bins @ IC=2mA, VCE=5V: A 110–220, B 200–450, C 420–800 (best low-current gain data of the candidate NPNs, but only one test current is given)
- VCE(sat) ≤0.5V, VBE(sat) ≤1.1V @ IC=100mA, IB=5mA
- fT ≥100MHz @ IC=10mA

### BC857 (`bc857-pnp.pdf`, p.1–2)
- VCBO(857) 50V, VCEO(857) 45V, VEBO 5V; IC 100mA, Ptot 200mW
- hFE bins @ −VCE=5V, −IC=2mA: A 125–250, B 220–475, C 420–800
- −VCE(sat): 0.3V max @ −IC=10mA,−IB=0.5mA; 0.65V max @ −IC=100mA,−IB=5mA
- −VBE(on): 0.6–0.75V @ −IC=2mA; 0.82V max @ −IC=10mA
- fT 100MHz min

### BZX84C10 (`bzx84c10-zener.pdf`, p.2, row "BZX84C10")
- VZ: 9.4 min / 10 nom / **10.6 max** V @ IZT=5mA
- ZZT 20Ω @ IZT; ZZK 150Ω @ IZK=1.0mA
- IR: 0.2 µA max @ VR=7.0V
- Temp coefficient: +4.5 to +8.0 mV/°C @ IZT
- PD 300 mW, RθJ-A 417 °C/W (SOT-23)

### BZV55B5V1 (`bzv55b5v1-zener.pdf`, p.3, row "BZV55B5V1")
- VZ: 5.00 min / **5.2 max** V @ IZT=5mA
- ZZT 35Ω max @ IZT; ZZK 550Ω max @ IZK=1.0mA
- IR: 0.1 µA max @ VR=1.0V
- Ptot 500 mW; RthJA = 300 K/W (Fig.10 label, p.2); TJ/TSTG −65 to +200 °C

### SS54 (`ss54-schottky-actual-mdd.pdf`, p.1)
- VRRM/VRWM/VDC = **40 V**
- I(AV) 5.0 A; IFSM 120 A (8.3 ms single half-sine)
- VF max @ IF=5.0A: **0.70 V** (SS54 shares this column with SS55/SS56)
- IR max: **1.0 mA @ 25°C / 50 mA @ 100°C** at rated VDC blocking voltage
- CJ typ 500 pF (1MHz, VR=4V); RJA typ **60.0 °C/W** (2"×2" copper pad, note 2)
- TJ −55 to +125°C (SS52–56 group); TSTG −55 to +150°C
- **trr: not specified.** No reverse-recovery row exists in this datasheet — consistent with Schottky majority-carrier behavior, but not a number I can cite.

---

## Design equations (gate networks, soft-start, base drive, clamping, sensing)

### Topology used throughout
Two circuit families cover all six switch positions:

**Family A — default-ON (Switch 1 only).** Gate pulled to GND by R_pd by default (no drive present → deeply negative Vgs → ON). A PNP (Q1, emitter at Source) driven through an NPN translator (Q2, emitter at GND) actively pulls Gate up to Source when firmware commands OFF. A zener (Gate anode, Source cathode) clamps Vgs during the transition and during any fault where VBUS is high but the OFF command is lost.

**Family B — default-OFF (Switches 2–6).** Gate pulled up to Source by R_pu by default (Vgs=0 → OFF, trivially safe, no current flows). A single NPN (Q2) pulls Gate toward GND when firmware commands ON. Same Gate-Source zener clamp is mandatory on the AO3401A positions (3–6) and optional-but-recommended on the AO4407A position (2). Switches 3–6 add a series soft-start resistor R_soft between the NPN collector and the Gate, with a discrete Gate-Source capacitor C_soft dominating the RC time constant over the FET's intrinsic Ciss.

### Off-state Vgs arithmetic (the resistor-divider check)
In Family B's OFF state, Gate is pulled to Source only by R_pu; no other element loads it except the NPN's cut-off leakage. Using the worst leakage figure available (BC847 ICBO ≤ 0.1 µA, `bc847-npn.pdf` p.2) through R_pu = 39 kΩ (derived below): ΔV = 0.1 µA × 39 kΩ = 3.9 µV. Vgs(off) ≈ 0 V, four orders of magnitude below Vgs(th) min (0.5 V, both AO3401A sheets) or AO4407A's 1.7 V min. **This state has essentially no margin problem** — it's the ON transition and the fault case that need the arithmetic.

**What happens when a pull-up "fights" a too-strong pull-down (the failure this project has already hit):** in Family A, when Q1 (PNP) is commanded to hold OFF, it must source current through R_pd against R_pd's own pull toward GND. If R_pd is sized too small (too "strong"), the continuous current the PNP must supply to hold Gate near Source scales as (VBUS − VCE,sat(PNP)) / R_pd, and if that current exceeds what the PNP's base drive can sustain in saturation, the PNP falls out of saturation into its active region. The Gate node then settles wherever the PNP's now-finite output impedance and R_pd divide the rail — not at Vgs≈0, but at some partially-negative Vgs, e.g. Vgs = −(VBUS)·R_pd/(R_pd+R_PNP,active). With R_pd picked too small relative to available base drive, this lands well past Vgs(th) (−1.5V worst case) and the FET stays partially ON — exactly the "leaks the rising VBUS into a 5V bus" failure named in the brief. This is why R_pd must be sized generously relative to the PNP's guaranteed base drive (worked below), not picked as a generic "100k default" without checking the current budget.

### RC soft-start vs. inrush current
For a downstream bulk capacitance C_down charged through a linearly-enhancing FET, the average charging current over a controlled voltage ramp of duration t_ramp is:

**I_inrush ≈ C_down · ΔV / t_ramp**

t_ramp is set by the gate RC: using the standard 10–90% exponential-charge relation (t_ramp ≈ 2.2·τ, generic RC theory, not a datasheet figure), τ = R_soft · C_gate, where C_gate is dominated by a discrete added C_soft (Gate-Source) rather than the FET's much smaller intrinsic Ciss (645–670 pF per the two AO3401A sheets), so the ramp time is predictable and component-tolerance-dominated rather than process-dominated.

Combining: **R_soft = ΔV · C_down / (2.2 · C_soft · I_inrush,target)**

### Base resistor sizing (NPN translator)
Rb = (V_GPIO − V_BE(on)) / I_B, where I_B is chosen for comfortable overdrive above I_C(needed)/hFE(min). V_BE(on) is not tabulated at the low currents (~100–500 µA) relevant here on any of the three candidate NPN sheets — MMBT2222A's lowest characterized point is 0.1 mA (hFE min 35, no VBE given at all at that current) and BC847's is 2 mA. **This document uses 0.7 V as a standard silicon-BJT approximation, not a datasheet figure** — flagged explicitly since no sheet gives VBE at this current.

A base-emitter bleed resistor R_be (base to emitter) holds the NPN off against any GPIO leakage/high-Z condition (e.g. before firmware configures the pin) by drawing a controlled sneak current — a standard practice not derived from any datasheet leakage spec, since RP2350B GPIO leakage isn't part of the datasheets read for this task.

### Zener clamp selection
Pick Vz comfortably under |Vgs max| with margin for the zener's own tolerance band (BZX84C10 spans 9.4–10.6 V, `bzx84c10-zener.pdf` p.2) — clamping at up to 10.6 V leaves only 1.4 V of margin to AO3401A's ±12 V absolute max, which is tight but workable since the zener's max is a hard ceiling, not a typical. Series resistance (R_pd or R_pu, already present for the default-bias function) doubles as the zener current-limiter: I_z = (V_source,max − V_z,max) / R.

### Current sense
No current-sense amplifier IC was among the candidate parts for this task, so only the resistor-and-scaling half of this can be specified from the datasheets read here (see Open Questions). General scaling: V_ADC = I_load · R_sense · Gain, with Gain supplied by an external current-sense amplifier (high-side, since the sense point sits on the switched HV rail at up to 20 V and the tiles share a common GND — a low-side per-edge shunt isn't architecturally available without splitting GND per edge, which the project's stated common-GND rail rules out).

---

## Worked values, per switch position (1, 2, and 3–6)

### Switch 1 (AO3401A, VBUS→BS+, default ON, ~1.5 A)

**R_pd (Gate-to-GND, default-bias + zener current limiter).** Design target: idle current through the PNP+R_pd path ≤ 200 µA at VBUS,max = 20 V (an efficiency/idle-power design choice, not a datasheet spec).
- Ideal: R = 20 V / 200 µA = **100 kΩ**
- Nearest E24: **100 kΩ** (exact E24 value)
- Actual current @ 20V: 20 V / 100 kΩ = 200 µA exactly — 0% error
- Resulting zener current in the fault-clamped state (VBUS=20V, OFF command lost, Q1/Q2 fail passive): I_z = (20 − 10.6) / 100 kΩ = **94 µA** — below IZK (1.0 mA, the datasheet's regulation-guarantee current, `bzx84c10-zener.pdf` p.2), meaning the clamp voltage in this fault scenario is not tightly guaranteed by the tabulated ZZT/ZZK figures. It still functions as a breakdown-limited clamp, just without datasheet-guaranteed precision. **Trade-off, not resolved by the datasheet**: a smaller R_pd (e.g. 3.3 kΩ) would push I_z to ~2.85 mA (above IZK, tightly regulated) at the cost of ~6 mA continuous idle current whenever Switch 1 is held OFF (which is most of normal operation). This document recommends the 100 kΩ / low-idle-power choice given the project has no local energy storage and every mA matters, but flags the soft-clamp trade-off explicitly for the schematic decision.
- Cold-start check (VBUS=5V, zener not conducting since 5V<Vz): Vgs = −5V, comfortably past Vgs(th) max of −1.5V (worst-case sheet) with 3.5V of overdrive.

**Q1 base resistor network (R3, PNP base pull-up to Source).** Target: PNP (BC857) Ic ≥ 200 µA (matches R_pd's off-state current) with ≥20× base-current overdrive above the hFE-min requirement, sized at the lowest VBUS at which OFF might be commanded (~9V, a plausible first PD voltage step — not a datasheet number, a system assumption).
- Ib(PNP) target with hFE min = 125 (BC857 bin A, `bc857-pnp.pdf` p.2): Ib_min = 200µA/125 = 1.6 µA; design Ib ≈ 32 µA (20× margin)
- R3 ideal = (9V − 0.7V(Vbe) − 0.2V(Q2 Vce,sat)) / 32µA ≈ 253 kΩ
- Chosen (favoring margin over exact E24 rounding, since this is a "make sure it's always enough" resistor): **100 kΩ**. Resulting Ib(PNP) @ 9V = 81 µA (2.5× the 32µA target); @ 20V = 191 µA (6× target) — margin grows with VBUS, which is the safe direction.

**Q2 (NPN) base resistor Rb, base-emitter resistor Rbe.** Target Ib(Q2) = 150 µA design overdrive (arbitrary but generous choice, not datasheet-derived).
- Ideal: Rb = (3.3V − 0.7V) / 150µA = 17.33 kΩ
- Nearest E24: **18 kΩ**; actual Ib = 2.6V/18kΩ = 144.4 µA — error vs 150µA target = **−3.7%**
- Rbe = **10 kΩ** (standard bleed-resistor choice, not datasheet-derived); current stolen from Rb's output: 0.7V/10kΩ = 70 µA
- Net Ib(Q2) reaching the base = 144.4 − 70 = 74.4 µA
- Ic(Q2) available at hFE min: using BC847's 2mA-referenced bin-A min (110, closest characterized point to this current, `bc847-npn.pdf` p.2) = 74.4µA × 110 = **8.2 mA**, vs. the ≤200 µA actually needed — 40× margin, comfortably saturates Q2 regardless of which candidate NPN is populated.

**Thermal check @ ID=1.5A**, using worst-case (clone) RDS(on) at VGS≈−4.5V test point (closest to the ~−5V cold-start overdrive): 75 mΩ max (`AO3401A-pfet-lcsc.pdf` p.2).
- P = I²R = 1.5² × 0.075 = 0.169 W
- Tj = Ta + P·RθJA(steady, worst of both sheets, 125°C/W) = 25 + 0.169×125 = **46.1°C** @ Ta=25°C; ≈81°C @ Ta=60°C — comfortable margin either way, PD (1.0-1.4W) not a binding constraint at this current.

### Switch 2 (AO4407A, VBUS→HV, default OFF, up to 4–5 A)

**R_pu (Gate-to-Source, default OFF).** Target ON-state static bleed ≤ 500 µA at VBUS=20V.
- Ideal: 20V/500µA = 40 kΩ
- Nearest E24: **39 kΩ**; actual = 20/39k = 513 µA — error = **+2.6%**
- Power in R_pu: 513µA² × 39kΩ = **10.3 mW** — fits 0402 (typ. 1/16W = 62.5mW rating) with large margin

**Clamp decision (optional here, unlike 3–6).** AO4407A's ±25V Vgs abs max gives 5V of margin at VBUS=20V unclamped (Vgs=−20V, 80% of abs max — a real but workable derating, ~20% below the rated ceiling with zero fault tolerance beyond that). Clamping to the same BZX84C10 (10.6V max) costs some RDS(on) headroom: at Vgs=−10V,ID=−12A, RDS(on)=10/13mΩ vs 8.5/11mΩ at Vgs=−20V (`AO4407A-pfet.pdf` p.2) — a small (~15%) RDS(on) penalty for a large safety-margin gain. **Recommendation (mine, not datasheet-derived): clamp it anyway**, given this project's stated history of sequencing bugs and the fact that AO3401A positions 1 and 3–6 already require the identical clamp component — reusing it on position 2 is free in BOM terms and removes the only unclamped high-side gate in the design.

**Thermal check @ ID=4A**, RDS(on) at VGS=−10V (if clamped, conservative choice): 13mΩ max.
- P = 4² × 0.013 = 0.208 W
- Tj = 25 + 0.208×75(RθJA steady max) = **40.6°C** @ Ta=25°C; ≈75.6°C @ Ta=60°C — large margin against 150°C Tj max. AO4407A in SOIC-8 is comfortably sized for the 4A ceiling.

### Switches 3–6 (AO3401A ×4, per-edge HV distribution, default OFF, soft-start + sense)

**R_pu**: same derivation and value as Switch 2 — **39 kΩ**, 513 µA @ 20V, 10.3 mW.

**Zener clamp is mandatory here** (not optional, unlike Switch 2) — AO3401A's ±12V abs max is exceeded by an unclamped Vgs=−20V. Same BZX84C10, same R_pu doubles as the current-limiter: I_z = (20−10.6)/39kΩ = **241 µA** — also below IZK=1.0mA, same soft-clamp caveat as Switch 1. Given this position needs firm, precise Vgs control for RDS(on) reasons during soft-start (see below), consider a dedicated lower-value resistor in the clamp path here rather than reusing R_pu directly if tighter regulation is wanted — **not resolved by the datasheet, a schematic-level choice**.

**Soft-start RC.** Design targets (stated explicitly as assumptions, not datasheet or spec values): downstream tile bulk capacitance C_down ≈ **100 µF** (a plausible order-of-magnitude placeholder pending the real BOM figure), worst-case rail step ΔV = 20V, target I_inrush = 2 A.
- t_ramp,ideal = C·ΔV/I = 100µF×20V/2A = **1.0 ms**
- τ_ideal = t_ramp/2.2 = **454.5 µs**
- Choose C_soft = 1 nF (standard value, C0G/NP0). R_soft,ideal = 454.5µs/1nF = **454.5 kΩ**
- Nearest E24: **470 kΩ**; actual τ = 470µs, actual t_ramp(2.2τ) = 1034µs
- Actual I_inrush = 100µF×20V/1034µs = **1.93 A** — error vs 2A target = **−3.3%**

**SOA check — not fully resolvable from text extraction.** Peak instantaneous power at the very start of the ramp (before C_down has charged at all): P ≈ I·ΔV = 1.93A × 20V = **38.7 W**, vastly above the steady PD rating (1.0–1.4W) but potentially within the 1 ms single-pulse SOA — AO3401A's SOA and normalized transient thermal impedance are given only as graphs (Fig. 9–11 in both sheets), and pdftotext cannot extract numeric values from a curve. **This is explicitly "not specified" and must be checked graphically against the actual (V, I, t) trajectory before this RC choice is finalized** — I am not going to assert a pass/fail here without the real curve data.

**Base drive for the switching NPN**: identical Rb=18kΩ/Rbe=10kΩ derivation as Switch 1's Q2, since the required Ic (513µA) and available margin are the same order of magnitude.

**Current sense.** Target sense voltage 100 mV at I_max=4A (upper end of the common 20–100mV current-sense design range — a design rule of thumb, not a datasheet spec, since no sense-resistor or sense-amplifier part was among the candidates).
- R_sense,ideal = 100mV/4A = 25 mΩ. Purpose-built current-sense resistors are commonly sold in round decade values (10/20/25/50/100 mΩ) rather than strict E24 — chosen: **R_sense = 25 mΩ** (0% error by construction against the round target)
- V_sense @ 4A = 100 mV exactly
- **Power: P = I²R = 4² × 0.025 = 0.4 W.** This is nowhere close to a 0402-viable dissipation (0402 typ. 1/16W=62.5mW; even 0805 at 1/8W=125mW and 1206 at 1/4W=250mW fall short). **Requires a purpose-built current-sense part in 1206 or 2512 rated ≥0.5W (ideally 1W for margin)** — flagged explicitly per the instruction to call out where 0402 (or even larger standard sizes) is wrong.
- ADC scaling: with a 3.3V ADC and 3.0V target full-scale (0.3V margin), Gain = 3.0V/100mV = **30×**, required from an external high-side current-sense amplifier not covered by any datasheet read for this task (see Open Questions).

---

## Recommended implementation (per switch position)

**Switch 1**: AO3401A + R_pd(Gate–GND)=100kΩ 0402 + BZX84C10 (Gate–Source, cathode to Source) + Q1=BC857 (E–Source, C–Gate) + R3(PNP base pull-up to Source)=100kΩ + Q2=BC847 (E–GND, C–Q1 base) + Rb=18kΩ + Rbe=10kΩ from GPIO.

**Switch 2**: AO4407A + R_pu(Gate–Source)=39kΩ 0402 + BZX84C10 clamp (recommended, not strictly required) + Q2=BC847/MMBT2222A (E–GND, C–Gate) + Rb=18kΩ + Rbe=10kΩ. No soft-start requirement stated for this position.

**Switches 3–6** (×4 identical): AO3401A + R_pu(Gate–Source)=39kΩ 0402 + BZX84C10 clamp (mandatory) + Q2=BC847/MMBT2222A (E–GND, C→R_soft→Gate) + R_soft=470kΩ + C_soft=1nF Gate–Source + Rb=18kΩ + Rbe=10kΩ + R_sense=25mΩ (1206/2512, ≥0.5W) on the switched HV output feeding an external high-side current-sense amplifier (not specified here) into the RP2350B ADC.

**Backfeed blocking**: two SS54 (MDD, LCSC C22452 basic part or equivalent) back-to-back on the HV rail between ports — see Thermal Analysis below for why this position needs a specific check against the 4-5A ceiling, and Gotchas for the manufacturer-dependent leakage concern.

---

## Thermal analysis

### Switches 3–6 at the full 4A design ceiling — the headline finding of this section

Using worst-case (clone) RDS(on) at VGS≈−10V (post-clamp, per the mandatory zener above), ID=−4A: **65 mΩ max** (`AO3401A-pfet-lcsc.pdf` p.2, extrapolated from the −3A test point — the datasheet doesn't test at 4A directly, so this is a same-order-of-magnitude estimate off the nearest tabulated point, not a cited number at exactly 4A).
- P = 4² × 0.065 = **1.04 W**
- Tj = 25°C + 1.04W × 125°C/W(RθJA steady max, worst of both sheets) = **155°C — exceeds the 150°C Tj max at just 25°C ambient, with zero margin for any real operating ambient.**

Even using the better AOS-sheet RDS(on) max at the closer-matching VGS=−10V,ID=−4A test point (50 mΩ, an exact match to our operating current, `AO3401A-pfet.pdf` p.2):
- P = 4² × 0.050 = 0.8 W
- Tj = 25 + 0.8×125 = **125°C** — no margin left for any ambient above ~4°C over the datasheet's 25°C reference condition before hitting 150°C, and the datasheet's RθJA is itself only valid on its specific "1in² FR-4, 2oz copper" reference board (`AO3401A-pfet.pdf` p.1, Note A/D) — real copper area is a layout decision, not something this document can verify.

**This is a load-bearing finding, not a rounding error**: a SOT-23 AO3401A, by either candidate datasheet, is thermally marginal-to-inadequate for continuously carrying the full 4A per-edge budget ceiling stated in the project constraints. Whether this matters depends on a system fact not in scope for a datasheet-only read: **does any single edge realistically carry the full 4-5A ceiling continuously, or is that ceiling a shared/rare/transient case?** If continuous full-current single-edge distribution is a real operating mode, AO3401A in SOT-23 should be reconsidered (larger package, e.g. an SO-8 part like AO4407A, or paralleled devices) for positions 3–6. Flagged for the schematic diff.

### Switch 1 and Switch 2
Both check out with comfortable margin — see the per-position thermal checks above (46°C and 41°C Tj respectively at Ta=25°C, both well under 150°C).

### SS54 backfeed diodes
Using the datasheet's own thermal resistance (RJA = 60°C/W, 2"×2" copper pad reference, `ss54-schottky-actual-mdd.pdf` p.1) and its max VF at rated current (0.70V @ 5A):
- At the rated 5.0A: P = 5×0.70 = 3.5W → ΔTj = 3.5×60 = 210°C over ambient — physically impossible; the part cannot run at its own rated 5A continuously without far more copper than a 2"×2" pad, consistent with the datasheet's own derating curve (Fig.1, `ss54-schottky-actual-mdd.pdf` p.2) showing average current falling toward 0A as case temperature rises toward 150°C.
- At the project's 4A ceiling, using the same 0.70V figure as a conservative upper bound (the true VF at 4A is somewhat lower but not tabulated — Fig.3's exact curve values aren't text-extractable): P ≈ 2.8W → ΔTj ≈ 168°C over ambient, still exceeding the 125°C Tj max (SS52-56 group) even starting from 0°C ambient.
- **Solving for the maximum continuous current the datasheet's own thermal numbers actually support**, using TJ,max−Ta=25°C = 100°C headroom at the reference ambient: P_max = 100/60 = 1.67W → I_max ≈ 1.67/0.7 ≈ **2.4A continuous** — roughly half the project's 4A ceiling, using a single SMA SS54 on modest copper.

**This is the second load-bearing thermal finding**: if the backfeed-blocking position sees anywhere near the full 4-5A ceiling continuously (plausible, since the brief notes a Schottky drop is only acceptable on the HV rail, implying this sits in the HV current path, not the low-current 5V bootstrap path), a single SMA SS54 per leg is under-provisioned by the datasheet's own numbers. Mitigations worth checking against the schematic: parallel diodes, a larger package (SMB/SMC — both listed as available LCSC alternatives for "SS54"), generous copper pour beyond the 2"×2" reference, or confirmation that this position's actual duty cycle/current is much lower than the full ceiling.

---

## Layout notes

- **Zener polarity**: BZX84C10 cathode must land on the Source net (the floating 5–20V rail), anode on the Gate net, so the diode's reverse-breakdown direction is the one that limits how far below Source the Gate can be pulled. Reversed polarity would clamp the wrong direction and provide no protection during turn-on.
- **R_sense (25mΩ, ~0.4W) is not a 0402/0603/0805 part** — needs a footprint sized for continuous sub-watt dissipation (1206/2512 current-sense-rated part), called out explicitly per the "call out anywhere 0402 is wrong" instruction.
- **SS54 in SMA needs real copper**, not just its footprint pad — the RJA=60°C/W figure is only valid at the datasheet's reference 2"×2" copper pad condition (`ss54-schottky-actual-mdd.pdf` p.1, Note 2); anything smaller makes the thermal finding above worse.
- Keep the Gate–Source zener and the gate resistor(s) physically close to the FET gate pin — this is standard high-dV/dt gate-node practice, not a number from any specific datasheet read here.
- The base-emitter bleed resistors (Rbe) and base resistors (Rb) are small-signal, low-power — 0402 is fine.

---

## Gotchas and failure modes

1. **`SS54-schottky.pdf` in the repo is the wrong datasheet** (it's `1N5817-1N5819`, a 1A axial-leaded DO-41 part with a completely different VF/IR/thermal profile than the SMA SS54 this design calls for). Every SS54 number in this document instead comes from a newly-fetched, verified-correct sheet saved as `ss54-schottky-actual-mdd.pdf`. Worth checking whether this mislabeling also misled any earlier design decision in the schematic.
2. **Two different "AO3401A" datasheets in the folder disagree** on Vgs(th) max (−1.3V vs −1.5V), IDM (−27A vs −19A), RDS(on) (up to ~30% higher on the clone sheet), and body-diode Vf (−1.0V vs −1.2V). Since LCSC/JLCPCB basic-part sourcing doesn't guarantee a specific fab, every margin calculation in this document uses the worse of the two — the schematic should do the same, or explicitly pin the AOS-only part number if that guarantee matters.
3. **AO3401A's ±12V Vgs abs max vs a 20V source is the single sharpest edge in this whole design.** Every AO3401A position (1, 3–6) is only safe because of the zener clamp; remove or misconnect it and the very first PD negotiation above ~12V destroys the gate oxide. AO4407A (Switch 2) does not have this specific failure mode (±25V abs max) but is still recommended to carry the same clamp for consistency and margin.
4. **Soft-clamp regime at low I_z.** Every clamp current computed above (94–241 µA, depending on the chosen R value) sits below the datasheet's IZK=1.0mA regulation-guarantee current for both zener parts. The clamp still functions (breakdown doesn't have a hard "off" below IZK, it's just less tightly specified), but this document cannot cite a guaranteed clamp voltage in that regime — only the datasheet's ZZT/ZZK figures at their tested currents.
5. **Switches 3–6 are thermally marginal at the stated 4A ceiling in SOT-23** (Tj = 125–155°C at Ta=25°C depending on which AO3401A sheet is used, using the datasheet's own reference-board RθJA) — see Thermal Analysis. This is the kind of finding this whole exercise exists to surface; it needs a real answer about actual per-edge duty current, not just a datasheet re-read.
6. **SS54 in SMA is thermally under-provisioned for continuous 4-5A duty** by the datasheet's own numbers (≈2.4A continuous ceiling on reference copper vs. a stated 4-5A design ceiling) — see Thermal Analysis.
7. **SS54 reverse leakage is manufacturer-dependent and non-trivial here**: MDD's sheet specifies up to 1.0 mA at 25°C and **50 mA at 100°C** at rated blocking voltage. With two SS54s back-to-back between two live ports, this leakage forms a real (if partial) coupling path between two independently-negotiated USB-C supplies — 50mA at elevated temperature is not "essentially zero," and different manufacturers' SS54 die (which is exactly what LCSC basic-part sourcing may substitute) can spec meaningfully lower or higher leakage than this. Worth an explicit manufacturer pin if this leakage budget matters to the negotiation logic.
8. **VBE(sat) at the actual operating currents (~100–500 µA) isn't characterized on any of the three candidate NPN sheets** — all base-resistor sizing above uses the standard 0.7V silicon approximation, not a cited datasheet number, because none of MMBT2222A/BC847/BC857 test that low.

---

## Open questions / not determinable from the datasheet

- **No current-sense amplifier IC was among the candidate parts for this task.** The sense-resistor value, its power dissipation, and the required gain (30×) are derived above, but the actual amplifier (or comparator-based OCP scheme) that turns 100mV into a 0-3.3V ADC-compatible, GND-referenced signal on a 20V high-side rail is not something any of the read datasheets specify — this is a real gap in the parts list for this subsystem, not just an oversight in this document.
- **AO3401A SOA and normalized transient thermal impedance curves (Fig. 9–11, both sheets) are graphical only.** The soft-start worked example above computes a 38.7W peak instantaneous power during the inrush ramp but cannot verify it against the actual SOA boundary from text extraction — this needs to be read directly off the graph (or the underlying digitized data, if AOS provides it) before the R_soft/C_soft values above are treated as final.
- **BZV55B5V1's actual role in this design was not resolvable from the datasheets alone.** It's listed as a candidate alongside BZX84C10 but nothing in the electrical characteristics of either part points to an obvious division of labor beyond "BZX84C10 clamps the 5-20V gate networks, BZV55B5V1 could clamp something at a lower voltage" — possibly BJT base-emitter reverse-voltage protection (Q1/Q2's VEBO is 5-6V, in the same range as BZV55B5V1's 5.1V), but this is speculation, not a cited conclusion.
- **Real downstream bulk capacitance (C_down) for the soft-start calculation is an assumed 100µF placeholder**, not a project-supplied or datasheet-derived figure — the R_soft/C_soft worked values should be re-derived once the actual number is known.
- **Real ambient temperature inside an assembled, enclosed tile is unknown** — all Tj calculations above use the datasheets' 25°C reference condition plus a spot-check at an assumed 60°C; the actual number depends on enclosure and neighboring-tile heat, outside this task's scope.
- **Whether any single edge (Switches 3-6) is expected to carry the full stated 4-5A ceiling continuously, or only transiently/rarely**, is a system architecture question this document flags but cannot answer from datasheets alone — it's the single biggest lever on whether the SOT-23 AO3401A thermal finding above is a real problem or a non-issue.
