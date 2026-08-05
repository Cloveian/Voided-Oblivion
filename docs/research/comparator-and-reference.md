# LM2903 + TLV431 threshold detector - datasheet research
> Independent datasheet read. Not written against the existing schematic.

Sources read:
- `Refrences/datasheets/LM2903-dual-comparator.pdf` - TI SLCS005AH (Oct 1979, rev. April 2025), covers LM393B/LM2903B (new "B" versions) and the legacy LM193/LM293/LM393/LM2903/LM2903V/LM2903AV family in one document.
- `Refrences/datasheets/TLV431-shunt-reference.pdf` - TI SLVS139Z (Jul 1996, rev. June 2024), covers TLV431/TLV431A/TLV431B.
- `Refrences/datasheets/app-notes/TI-comparator-app-note.pdf` - TI SNOA997A, "Inverting Comparator With Hysteresis Circuit" (Analog Engineer's Circuit), used for the hysteresis derivation method.
- `Refrences/datasheets/TLV1805-comparator.pdf` was opened but not otherwise used - it is not one of the two chips assigned to this note, referenced only where it clarifies what a *push-pull* alternative would look like.

All part numbers, section numbers and page numbers below refer to the printed page numbers in these PDFs (as read via `pdftotext -layout`, cross-checked against rendered page images for tables that don't extract cleanly, notably the TLV431 stability graph).

---

## Part identity (both parts)

**LM2903 family** (LM2903-dual-comparator.pdf, Description & Device Information table, p.1):
- Two independent single-supply voltage comparators in one package.
- Legacy non-B parts (LM2903, LM2903V, LM2903AV, LM393, LM393A, LM193, LM293, LM293A) vs. new "B" versions (LM393B, LM2903B) which are drop-in replacements with tighter specs (§1 Features, p.1).
- Packages: SOIC-8 (4.90×3.91mm), VSSOP-8 (3.00×3.00mm), PDIP-8, SO-8 (6.20×5.30mm), TSSOP-8 (3.00×4.40mm); B-version only also in SOT-23-8 (2.90×1.60mm) and WSON-8 (2.00×2.00mm) (Device Information table, p.1).
- Pinout (8-pin SOIC/VSSOP/PDIP/SO/TSSOP, Fig 4-1, p.3): 1=1OUT, 2=1IN-, 3=1IN+, 4=GND, 5=2IN+, 6=2IN-, 7=2OUT, 8=VCC.

**TLV431 family** (TLV431-shunt-reference.pdf, Description & Package Information table, p.1):
- 3-terminal adjustable low-voltage shunt reference, VREF = 1.24V, adjustable 1.24V-6V with two external resistors.
- Grades: TLV431 (±1.5% @25°C), TLV431A (±1%), TLV431B (±0.5%) (§1 Features, p.1).
- Packages: SOT-23-3 (DBZ, 2.92×2.37mm), SOT-23-5 (DBV, 2.90×2.8mm, all grades), TO-92 (LP), SOT-89 (PK, A/B only), SOIC-8 (D, A/B only), SC-70-6 (DCK, B only, 2×1.5mm) (Package Information table, p.1).
- 3-terminal pin function (Table 4-1, p.3): CATHODE (I/O, shunt current/voltage input), REF (input, threshold relative to anode), ANODE (output, normally GND).

---

## Absolute maximum ratings that constrain this design

**LM2903** (§5.1, p.4):
| Parameter | Non-B | B version | Notes |
|---|---|---|---|
| VCC supply voltage | -0.3 to 36V | -0.3 to 38V | |
| VID differential input voltage | -36 to 36V | -38 to 38V | at IN+ w.r.t. IN- |
| VI input voltage (either input) | -0.3 to 36V | -0.3 to 38V | |
| IIK input current | -50mA | -50mA | via parasitic diode to GND if input driven negative |
| VO output voltage | -0.3 to 36V | -0.3 to 38V | **independent of VCC** - see gotchas |
| IO output current | 20mA | 25mA | |
| ISC output short to GND | Unlimited | Unlimited | |
| TJ | 150°C | 150°C | |

Critical implication: **VO's absolute maximum (36/38V) is a separate spec from VCC.** The open-drain output transistor's collector/drain can be pulled to a voltage far above the IC's own VCC, limited only by this 36/38V rating - not by VCC. This is explicitly load-bearing for driving a VBUS-referenced (5-20V) gate from a comparator whose own VCC could in principle be a lower rail. (In the architecture recommended below, VCC = VBUS directly, so this headroom isn't strictly needed for that reason, but it does mean the output pin can safely be pulled up all the way to the 20V VBUS maximum with large margin to the 36/38V ceiling.)

**TLV431** (§5.1, p.4):
| Parameter | Value | Notes |
|---|---|---|
| VKA cathode voltage | max **7V** | w.r.t. anode |
| IK continuous cathode current | -20 to 20mA | |
| Iref reference current | -0.05 to 3mA | |
| TJ | 150°C | |
| Tstg | -65 to 150°C | |

**This 7V absolute maximum on VKA is the single biggest constraint in this whole design.** VBUS ranges 5-20V. The TLV431 cathode can **never** be tied directly to VBUS or to any node that can reach 20V - it must always sit behind a current-limiting series resistor sized so that even fault conditions can't push VKA past 7V (in normal operation the device self-regulates VKA near VREF/1.24V once in regulation, so the resistor mainly sets current, but if the part were ever pulled out of regulation - e.g., cathode momentarily open before current is established - the resistor is what stands off the 20V rail; sizing it correctly is what keeps VKA away from 7V under all conditions, see the bias-resistor derivation below).

Recommended operating conditions for TLV431 (§5.3, p.4): VKA = VREF to 6V, IK = 0.1 to 15mA, TA per grade (0-70°C C-grade, -40-85°C I-grade, -40-125°C Q-grade).

**LM2903 recommended operating conditions** (§5.2, p.4): Supply voltage 2-30V (non-V), 2-32V (V-suffix), 2-36V ("B" version). Input voltage range 0 to (V+)-2.0V (non-B), -0.1 to (V+)-2.0V (B version). This comfortably spans VBUS's full 5-20V range if VCC = VBUS.

---

## Key electrical characteristics

### LM2903 (non-B, Electrical Characteristics for LM2903/LM2903V/LM2903AV, §5.10, p.10 - this is the classic/most commonly stocked part; B-version numbers in §5.6, p.7, given alongside)

| Parameter | LM2903/V (non-B) | LM2903B | Conditions |
|---|---|---|---|
| Input offset voltage VIO | 2mV typ / 7mV max @25°C; 15mV max full range | 0.37mV typ / 2.5mV max; 4mV max full range | VCC=5V |
| Input bias current IIB | 25nA typ / -250nA max @25°C; -500nA max full range | 3.5nA typ / -25nA max; -50nA max full range | |
| Input offset current IIO | 5nA typ / 50nA max; 200nA max full range | 0.5nA typ / 10nA max; 25nA max full range | |
| Common-mode input range VICR | 0 to VCC-1.5V @25°C; 0 to VCC-2.0V full range | -0.1 to VCC-1.5V @25°C; -0.1 to VCC-2.0V full range | footnote: input can't go >0.3V negative or output is undefined; only *one* input needs to be in-range, the other can go to VCC |
| Large-signal gain AVD | 25 typ / 100 min V/mV | 50 typ / 200 min V/mV | VCC=15V |
| VOL (low-level output voltage) | 150mV typ / 400mV max | 110mV typ / 400mV max (550mV full range) | IOL=4mA, VID=-1V |
| IOL (output sink capability) | 6mA min / 21mA typ | 6mA min / 21mA typ | VOL=1.5V, VS=5V |
| IOH leakage | 0.1nA typ / 50nA max | 0.1nA typ / 20nA max | VOH=5V, output off |
| Supply current IQ (whole package) | 0.8mA typ / 1mA max @5V; 2.5mA max @VCC-max | 0.4mA typ / 0.6mA max @5V | no load |
| Response time (100mV step, 5mV overdrive) | 1.3µs typ | 1.0µs typ | RL=5.1k to 5V, CL=15pF |
| Response time (TTL step) | 0.3µs typ | 0.3µs typ (300ns high-to-low, per §5.7 p.7) | |

**Output stage type (§6.1 Overview, §6.3 Feature Description, p.17):** explicitly **open-drain NPN** ("The output consists of an open drain NPN (pull-down or low side) transistor... The open-collector outputs allow the user to level shift to the desired logic level independent of VCC, while also enabling AND functionality when multiple outputs are connected together"). This means:
- A pull-up resistor is mandatory for any use of the output.
- The pull-up rail can be *anything* up to the output's 36/38V absolute max, regardless of what VCC is - this is what lets one comparator drive a VBUS-referenced gate and, on the other channel, a 3.3V logic rail, from the same VCC.
- Output HIGH state = high-impedance (pulled to whatever external rail the pull-up goes to); output LOW state = NPN saturated, sinking current, VOL as above.
- Two channels are functionally independent, sharing only VCC/GND (§6.1, "two independent voltage comparators... Quiescent current is independent of supply voltage"). No channel-to-channel crosstalk/isolation spec is given - **not specified**.

**Layout guidance (§7.2.5, p.19-20):** bypass cap recommended on VCC (no value given - **not specified**); do not run OUT and IN- traces in parallel (coupling can cause oscillation) - route VCC/GND trace between them if they must be close; place any input series resistors close to the device pins.

### TLV431 (Electrical Characteristics for TLV431, §5.5, p.5; A/B grade tables §5.6/5.7, p.6-7 are numerically tighter versions of the same rows)

| Parameter | TLV431 | TLV431A | TLV431B | Conditions |
|---|---|---|---|---|
| VREF @25°C | 1.222-1.24-1.258V | 1.228-1.24-1.252V | 1.234-1.24-1.246V | VKA=VREF, IK=10mA |
| VREF over full temp range | 1.194-1.286V (Q) | 1.209-1.271V (Q) | 1.221-1.265V (Q) | |
| Iref (reference terminal current) | 0.15 typ / 0.5 max µA | same | 0.1 typ / 0.5 max µA | IK=10mA, R1=10k, R2=open (Fig 6-2 config only) |
| **IK(min)** minimum cathode current for regulation | 55 typ / **80 max** µA (C/I grade); 100 max µA (Q grade) | same | same | VKA=VREF (Fig 6-1) - this is the number the bias resistor must guarantee |
| IK(off) off-state cathode current | 0.001 typ / 0.1 max µA | same | same | VREF=0, VKA=6V |
| Dynamic impedance \|zKA\| | 0.25 typ / 0.4 max Ω | same | same | f≤1kHz, IK=0.1-15mA |
| Temperature drift (typ, Features p.1) | 4mV (0-70°C), 6mV (-40-85°C), 11mV (-40-125°C) | same magnitudes, tighter % of a tighter VREF | same | |

**Minimum cathode current is the critical number for bias-resistor sizing.** Table 5.5 (p.5) lists it as TYP=55µA / MAX=80µA for the C and I grades, MAX=100µA for the Q (automotive, -40 to 125°C) grade. Design must guarantee IK stays above this MAX figure (not the typ) at the worst-case (lowest) supply condition, across tolerance and temperature, to guarantee the part stays in regulation.

**REF pin cannot float** (§7.3 Feature Description, p.18): "the reference pin can not be left floating, as it requires Iref ≥ 0.5µA... because the reference pin is driven into an NPN, which requires a base current to operate properly." Note this Iref spec (0.15µA typ/0.5µA max, Table 5.5) only applies to the *external-divider* configuration (Fig 6-2, VKA>VREF) where REF is fed from a separate R1/R2 tap. In the simple 2-terminal "diode" configuration (Fig 6-1, cathode shorted to REF, VKA=VREF=1.24V) the REF and CATHODE pins are the same physical node, so this is automatically satisfied by the cathode bias current - it is not a second, separate current budget to plan for.

**Stability / compensation region as a function of load capacitance** (§5.8 Typical Characteristics, Figure 5-18 "Stability Boundary Conditions," p.14 - read from the rendered page image since this is graphical, not tabulated data):

> "TLV431 is internally compensated to be stable without an output capacitor between the cathode and anode. However, if it is desired to use an output capacitor, Figure 5-19 [phase margin vs CL] can be used as a guide" (§7.3, p.18). "Though TLV431 is stable with no capacitive load, the device that receives the shunt regulator's output voltage could present a capacitive load that is within the TLV431 region of stability [i.e. instability], shown in Figure 5-18" (§8.2.2.2.3, p.23).

Figure 5-18 plots IK (cathode current, 0-15mA) vs. CL (load capacitance, 0.001-10µF log scale) for three fixed operating points: VKA=VREF (1.24V), VKA=2V, VKA=3V. The area *under* each curve is the unstable/oscillation region.
- For **VKA=VREF** (our configuration): the unstable "hump" spans roughly **CL ≈ 6nF to ≈ 400nF**, and is present across almost the entire 0-15mA cathode-current axis shown (the two boundary legs are close to vertical, only tapering to zero width right at the axis extremes). This is read visually off the graph, not a tabulated value - **treat the exact nF boundaries as approximate**, not datasheet-precision numbers.
- For VKA=2V and VKA=3V the unstable region is smaller and centered further up the current axis (peaks around 6-7mA and 1.5-2mA respectively), not relevant to a 1.24V "diode" reference use.

**Practical conclusion for this application:** do not add a deliberate capacitor across the TLV431 cathode-anode. PCB parasitic + component-pad capacitance at these node sizes is well under 5pF, an order of magnitude below the unstable region's lower boundary (~6nF), so no explicit action is needed - just don't add a bypass cap here, which is also literally what §7.3 (p.18) recommends by default ("stable without an output capacitor"). If a cathode capacitor is ever wanted for noise filtering, it needs to be either well under ~2-3nF or well over ~1µF to clear the mapped-out unstable band with margin - **the exact crossover points would need to be re-measured or re-read from a higher-resolution capture of Figure 5-18**, since pdftotext cannot extract curve data.

**Two-terminal vs. divider connection** (§8.2.1 "Comparator with Integrated Reference," p.21 = Fig 6-1 style; §8.2.2 "Shunt Regulator/Reference," p.23 = Fig 6-2 style):
- **Plain fixed 1.24V reference**: short CATHODE to REF (Fig 6-1, p.17). VO = VREF = 1.24V always, set by the internal bandgap only, no external resistors needed beyond the current-setting cathode bias resistor.
- **Higher fixed voltage via divider**: bridge R1 (cathode-to-REF) and R2 (REF-to-anode/GND) across the device (Fig 6-2, p.17); VO = (1 + R1/R2) × VREF - Iref × R1 (Eq. 1, §8.2.2.2.1, p.23). Valid range VREF (1.24V) to 6V (recommended VKA max, §5.3 p.4).

---

## Design equations (divider, hysteresis, bias resistor, gate drive)

### 1. TLV431 cathode bias resistor (5-20V supply → constant-ish IK)

R_bias sets IK = (V_supply - VKA)/R_bias, with VKA ≈ VREF = 1.24V in the 2-terminal configuration.

Constraint at the low end (V_supply = 5V, worst case for current): IK must clear IK(min) MAX spec (80µA for C/I grade, 100µA for Q grade, §5.5 p.5) with margin for resistor tolerance and TLV431 VREF tolerance.

Constraint at the high end (V_supply = 20V): keep IK within recommended operating range (0.1-15mA, §5.3 p.4, comfortably clear of the 20mA absolute max, §5.1 p.4) and keep resistor power dissipation sane for a 0402 package (rated roughly 62.5-100mW depending on vendor/series).

### 2. Threshold divider

Comparator reference input = TLV431's fixed VREF (1.24V, 2-terminal config). Comparator sense input = tap of a resistor divider (Rtop from VBUS, Rbottom to GND). At the (no-hysteresis) trip point:

V_trip = VREF × (Rtop + Rbottom) / Rbottom

### 3. Hysteresis (positive feedback on an open-drain comparator)

The available app note (TI SNOA997A, "Inverting Comparator With Hysteresis," p.1-3) derives a 4-resistor general case (separate Vref-bias network R1/R2 plus separate pull-up/feedback network R3/R4) for a comparator whose reference is itself resistor-derived. Our case is a simplified 2-resistor-divider version of the same idea because the reference is a fixed low-impedance node (TLV431's 1.24V) rather than a second divider - the same superposition method applies with one feedback element instead of the app note's R3/R4 pair.

Topology: Rtop (VBUS→node A), Rbottom (node A→GND), Rhys (comparator OUT→node A, comparator output pulled up to Vpu through a separate pull-up resistor Rpu ≪ Rhys). Comparator: IN- = node A, IN+ = VREF (so output sinks/LOW when node A rises above VREF, and releases/HIGH-Z when node A falls below VREF - matching the "output goes low when IN- > IN+" behavior described in §7.2.2.1, p.18).

By superposition at node A, treating the OUT pin as a voltage source of either ≈VOL (≈0V, saturated) or ≈Vpu (high-Z, pulled to Vpu through Rpu):

- **Upper trip point (UTP)**, VBUS rising, OUT currently LOW (VOL≈0V approx.):
  UTP = VREF × (1 + Rtop/Rbottom + Rtop/Rhys)

- **Lower trip point (LTP)**, VBUS falling, OUT currently HIGH-Z (≈Vpu):
  LTP = UTP - Vpu × (Rtop/Rhys)

- **Hysteresis band**: ΔV = Vpu × Rtop/Rhys

(VOL≈0V is an approximation; LM2903's actual VOL at the microamp-level Rhys current here is far below the 400mV worst case quoted at 4mA in §5.10 (p.10), since "VOL is resistive and scales with output current" per §6.3 (p.17) - the approximation error this introduces is negligible relative to the resistor-tolerance and VREF-tolerance budget below.)

### 4. Gate-drive pull-up resistor (open-drain output → P-FET gate referenced to VBUS)

Sizing driven by two constraints: (a) at VBUS_max, sink current through the resistor when the comparator is ON must stay well inside the characterized VOL region (test conditions in §5.10, p.10, characterize VOL up to IOL=4mA) and safely under the IOL/IO ratings (6mA min guaranteed, 20/25mA absolute max); (b) resistor power dissipation must stay reasonable for 0402.

I_sink(V_supply) = (V_supply - VOL) / R_pu

---

## Worked values for this application

Target: trip point above 5.5V (USB-C vSafe5V absolute max, per project brief) with margin, below 9V (lowest PD fixed voltage), no chatter through the transition. Design center chosen at ~7.1-7.4V.

### TLV431 bias resistor

Target: comfortable multiple of the 80µA MAX regulation floor (C/I grade) at VBUS=5V, without excessive dissipation at VBUS=20V.

- Ideal for ~150µA at 5V: R = (5 - 1.24)/150µA = **25.07kΩ**
- Nearest E24: **24kΩ**
- Actual IK at VBUS=5V: (5 - 1.24)/24k = **156.7µA** (1.96× the 80µA MAX regulation floor - comfortable margin against resistor tolerance, VREF headroom variation, and temperature)
- Actual IK at VBUS=20V: (20 - 1.24)/24k = **781.7µA** (well inside the 0.1-15mA recommended range, §5.3 p.4, and the 20mA absolute max, §5.1 p.4)
- Power dissipation at VBUS=20V: P = IK² × R = (781.7µA)² × 24kΩ ≈ **14.7mW** (24% of a typical 0402's 62.5mW rating - acceptable, but not enormous margin; a 12kΩ alternative that biases harder (313µA at 5V) pushes dissipation to ~29mW at 20V, close to half the 0402 rating, so **24kΩ is the better choice of the two** for thermal margin, at the cost of a slightly smaller current-margin cushion above IK(min)).
- Voltage across R at VBUS=20V: 18.76V - well inside typical 0402 resistor voltage ratings (commonly ≥50V), not a constraint here.

If TLV431Q (automotive, 100µA MAX floor) is used instead of C/I grade, 156.7µA still clears it with 1.57× margin - acceptable but tighter; would be worth re-checking the exact BOM grade before final sign-off.

### Threshold divider (no hysteresis, ideal reference point)

Choosing Rbottom = 10kΩ (E24) and targeting a nominal trip near 7.2V:

- Ideal Rtop = Rbottom × (Vtrip/VREF - 1) = 10k × (7.2/1.24 - 1) = **48.06kΩ**
- Nearest E24: **47kΩ**
- Actual trip (ideal divider, no hysteresis): V = VREF × (57k/10k) = 1.24 × 5.7 = **7.068V**
- Error vs. 7.2V target: **-1.8%**

### Hysteresis network

Using Rtop=47k, Rbottom=10k as above, and choosing the pull-up rail for this channel's output to be the 3.3V logic rail (Vpu=3.3V - see "Recommended implementation" for why):

- Ideal Rhys for ΔV≈0.8V: Rhys = Vpu × Rtop / ΔV = 3.3 × 47k / 0.8 = **193.9kΩ**
- Nearest E24: **200kΩ**
- Actual hysteresis band: ΔV = 3.3 × 47k/200k = **0.776V**
- **UTP** = 1.24 × (1 + 47/10 + 47/200) = 1.24 × 5.935 = **7.36V**
- **LTP** = UTP - 0.776 = **6.58V**

Margins: LTP to vSafe5V max (5.5V) = **1.08V**; 9V (lowest PD step) to UTP = **1.64V**. Both comfortably positive.

### Static trip-point error budget (worst case, linear sum, TLV431 blank grade / LM2903 non-B)

| Source | Contribution |
|---|---|
| TLV431 VREF tolerance (±1.5% of 1.24V) | ±18.6mV |
| Divider resistor tolerance (1%, two resistors) | ≈±99mV (worst-case linear, on a 7.07V trip) |
| LM2903 input offset voltage (full temp, non-B) | ±15mV |
| LM2903 input bias current × divider Thevenin impedance (Rtop‖Rbottom=8.25kΩ) × 250-500nA max | ±2.1 to ±4.1mV |
| **Total (worst case, linear)** | **≈ ±137mV** |

137mV worst-case static error is well under half of the 776mV hysteresis band (17.7%), so the hysteresis dominates and the design should not chatter from static accuracy alone, even at the tolerance corners. If a cheaper 5%-resistor divider is substituted, redo this sum - 5% resistors alone would contribute roughly ±350-500mV worst case and would eat most of the hysteresis margin.

### Gate pull-up resistor (P-FET gate referenced to VBUS)

- Choosing R_pu = **20kΩ** (E24):
- I_sink at VBUS=20V: (20 - 0.4)/20k = **0.98mA** (well under the 6mA guaranteed IOL, §5.10 p.10, and under the 4mA condition the VOL spec itself was characterized at, so the 400mV VOL max applies conservatively)
- Power at VBUS=20V: (0.98mA)² × 20k ≈ **19.2mW** (31% of 0402's 62.5mW rating - comfortable)
- I_sink at threshold (~7.36V, lowest voltage at which the gate would actually be pulled low): (7.36-0.4)/20k ≈ **0.35mA**, VOL even lower than the 400mV worst case.

---

## Recommended implementation (pin by pin, both comparator channels)

This is a synthesized circuit built from the documented part properties and the stated requirements - not itself a datasheet fact, flagged as design synthesis.

**Power for the detector (both LM2903 channels and TLV431):** VCC and the TLV431 bias resistor are both fed from **VBUS directly** (the sink-side USB-C VBUS pin, upstream of any FET this detector's own outputs control). VBUS is present (≥ vSafe5V, i.e. ≥ ~4.75V worst case per USB-C spec) whenever the detector needs to do anything at all, and is never switched off by this detector's own outputs (which switch downstream distribution FETs and a buck EN, not the sink-side VBUS pin itself) - satisfying requirement #1 (detector powered from a node its outputs can't switch off) and requirement #2 (bias resistors alive at cold start) in one move. LM2903's recommended VCC range (2-30/32/36V depending on suffix, §5.2 p.4) comfortably covers 5-20V.

**Shared analog nodes:**
- **REF-node**: TLV431 in 2-terminal "diode" configuration (CATHODE shorted to REF, Fig 6-1 p.17), biased through the 24kΩ resistor from VBUS. This node sits at a fixed 1.24V (±grade tolerance) whenever VBUS ≥ ~1.3V + a couple hundred mV of headroom for the bias resistor drop - i.e. essentially as soon as VBUS exists at all.
- **DIV-node**: midpoint of the 47k/10k divider off VBUS, with the 200k hysteresis resistor tied back to channel B's own output (below). Because DIV is a single shared physical node, **both** comparator channels reading it inherit the same hysteretic UTP/LTP - the hysteresis network only needs to exist once, not once per channel.

**Channel B (2IN-, 2IN+, 2OUT) - the authoritative threshold decision, doubles as the 3.3V logic enable:**
- 2IN+ = DIV-node, 2IN- = REF-node.
- 2OUT pulled up to **3V3** (the always-on LDO rail, itself fed from the always-on bootstrap 5V per the project's power architecture, so it is alive at cold start and not gated by this detector) through a pull-up resistor (a few kΩ - not critical, sized for 3.3V logic drive current, e.g. 10kΩ).
- 200kΩ hysteresis resistor from 2OUT back to DIV-node (this is the Rhys used in the worked-values section, with Vpu=3.3V).
- Output HIGH (pulled to 3.3V, high-Z) when DIV > REF, i.e. VBUS ≥ UTP (7.36V) rising, or VBUS > LTP (6.58V) once already high - a clean 0V/3.3V logic level directly off the open-drain output with nothing more than the pull-up resistor, satisfying the "clean 3.3V logic-level enable" requirement with zero extra parts. This can feed the buck EN pin directly.

**BJT stage (from Channel B's 3.3V output → second P-FET gate):**
- Channel B's 3.3V output drives a small NPN's base through a base resistor (sizing depends on the specific BJT's hFE and the second PFET's gate charge/Rgate_pu current - **out of scope for this LM2903/TLV431-focused note**; MMBT2222A-npn.pdf exists in the repo for that follow-up).
- NPN collector is the second P-FET's gate node, pulled up to VBUS through a ~20kΩ resistor (same sizing logic as the worked-value gate pull-up above).
- When Channel B is HIGH (VBUS ≥ threshold), the NPN turns on and pulls this second gate node toward GND, turning that P-FET on. This gives the BJT-driven P-FET the *same* sense/timing as the 3.3V enable (both active when VBUS ≥ threshold) - this is the natural pairing since the BJT is just inverting current, not logic level.

**Channel A (1IN-, 1IN+, 1OUT) - opposite polarity, direct VBUS-referenced gate drive:**
- Inputs swapped relative to Channel B: 1IN- = DIV-node, 1IN+ = REF-node (this is "the opposite polarity output from the second comparator channel" the task asks for - simply reversing which physical node goes to the inverting vs. non-inverting pin of the second, otherwise-identical channel).
- 1OUT pulled up to **VBUS** through the ~20kΩ resistor from the worked-values section, and drives the first P-FET's gate directly (no BJT needed - the datasheet's "output voltage independent of VCC, up to 36/38V abs max" property, §6.1/§5.1, is exactly what makes this legal even though VCC here already equals VBUS).
- Because 1IN-/1IN+ read the *same* DIV/REF nodes as Channel B, Channel A switches at the exact same VBUS crossings (7.36V rising / 6.58V falling) as Channel B - it inherits Channel B's hysteresis "for free" without needing its own feedback resistor, since the hysteresis lives in the shared analog node, not in either individual comparator.
- Channel A sinks (pulls its own gate node toward GND) when DIV > REF, i.e. it goes to the **opposite logic sense** from Channel B/BJT: Channel A's output is LOW exactly when Channel B's is HIGH. Whether that maps to "PFET1 ON when VBUS is HV" or "...OFF when VBUS is HV" is purely which way the gate is used downstream (P-FET turns on when Vgs is sufficiently negative, i.e., when this output pin is pulled LOW toward GND while its source sits at VBUS) - a system-level wiring choice, not a datasheet fact, and out of scope for a blind datasheet read.

**Cold-start / fail-safe property worth calling out explicitly:** every pull-up in this design (3.3V for Channel B, VBUS for Channel A and the BJT-driven gate) is either the very rail being measured (VBUS) or a rail that ramps up together with the bootstrap supply that also powers the detector (3.3V off BS+). Because the gate resistors always reference back to VBUS itself, a P-FET gate never gets an erroneous *low* relative to a *fully-present* VBUS during power-up transients - if VBUS hasn't ramped yet, the gate and its source both sit near the same low potential (Vgs≈0, FET off) regardless of what the comparator output is doing during the brief window before VCC/VREF are fully established. This is a structural defense against the "latch into the wrong state" failure mode called out in the brief, though it does not by itself prove the LM2903/TLV431 combination can't latch (see Gotchas below for the actual latch risk, which is about *where the bias resistors tap from*, not about this ramp-together property).

---

## Decoupling and passives

- **LM2903 VCC bypass**: §7.2.4 (p.19) recommends a bypass capacitor on the supply pin for noisy/AC inputs but gives **no specific value** - not specified. Common practice (100nF ceramic close to VCC/GND pins) is reasonable but is not a datasheet number; call it out as a design choice, not a citation.
- **TLV431 decoupling**: §8.4.1 (p.24) says only "place decoupling capacitors as close to the device as possible" - again **no value given**. Given the stability-region findings above, **do not add a deliberate cathode capacitor** - rely on parasitic capacitance only (well under the ~6nF lower boundary of the unstable region at VKA=VREF, Figure 5-18 p.14).
- All resistors (24k bias, 47k/10k divider, 200k hysteresis, ~10-20k gate pull-ups): default **0402**, verified above for power dissipation at both 5V and 20V extremes; none exceed roughly 30% of a typical 0402 power rating. Voltage drops (up to ~18.8V across the bias/divider top resistors at VBUS=20V) are within typical 0402 voltage ratings (commonly ≥50V) - **not a datasheet number for these specific TI parts**, this is a passive-component rating and should be checked against the actual resistor series chosen (e.g. LCSC/JLCPCB basic-parts 0402 thick-film resistors typically publish ≥50V working voltage).
- TLV431 package: SOT-23-3 (DBZ) is the smallest 3-pin option and adequate for the ≤800µA cathode current in this design - no thermal or current-density concern (§8.3, p.24, "for applications shunting high currents, pay attention to trace lengths" - our currents are two orders of magnitude below where that note is aimed).

---

## Layout notes

**LM2903** (§7.2.5.1-.2, p.19-20):
- Keep OUT and IN- traces from running parallel/adjacent without a VCC or GND trace between them - coupling from output to the inverting input can cause oscillation (this applies per-channel, output 1 to IN-1, output 2 to IN-2).
- Place any input series resistors physically close to the device pins.
- Bypass cap between VCC and GND close to the package; do **not** add a cap between the GND pin and system ground if there's no negative supply (single-supply here, so N/A - just note it doesn't apply).
- The datasheet's own layout example (Fig 7-4, p.20) shows input-resistor placement close to pins 2/3, with pin 1 (1OUT) and pin 8 (VCC) kept away from the input side of the package.

**TLV431** (§8.4.1-.2, p.24):
- Decoupling caps (if used) as close to the device as possible.
- Adequate trace width for cathode/anode current - not a concern at the ≤800µA level used here, but keep in mind if the bias resistor value is ever reduced.

**General for this application:** since Channel A's output drives a VBUS-referenced gate directly and Channel B's drives a 3.3V logic net, keep those two output traces well separated on the board (they carry very different voltage swings, 0-20V vs 0-3.3V) and away from the shared DIV/REF analog nodes, consistent with the general "don't run switching/output traces near sensitive input nodes" guidance above.

---

## Gotchas and failure modes

1. **TLV431 VKA absolute max is 7V (§5.1, p.4), not 20V.** The cathode bias resistor is not optional and not just for current-setting - it is the only thing standing between the TLV431 and destruction if it's ever connected on a path that could see the full 5-20V VBUS swing directly. Any BOM change, rework, or fault that shorts out or removes the bias resistor puts up to 20V directly on a part rated for 7V.

2. **Bias-resistor "node must be alive at cold start" trap applies to *where along the power tree* the tap is taken, not just *which named rail*.** If the TLV431 bias resistor or the divider top resistor is ever moved to tap VBUS *downstream* of a FET this same detector's outputs control (e.g., accidentally biasing off the switched/distributed side of the PD+ rail rather than the tile's own sink-side VBUS pin), the detector loses its own power exactly when it turns that FET off - classic self-latching/oscillating supply, the exact failure mode the brief calls out as having already bitten this project. The fix here is topological (tap upstream of any switch this circuit drives), not a component value, so it can't be caught by checking part numbers alone - it needs to be checked on the actual net each time this circuit is touched.

3. **REF pin floating.** §7.3 (p.18) is explicit that the REF pin needs ≥0.5µA and cannot float - in the diode-connected (Fig 6-1) configuration this is automatically satisfied because REF=CATHODE, but if a future revision moves to the divider configuration (Fig 6-2) for a higher reference voltage, the R1/R2 values need to guarantee this current independently.

4. **Comparator output pin voltage rating vs. VCC.** It's easy to assume an open-drain output can only swing up to VCC. It can't - it's rated separately (36/38V abs max, independent of VCC, §5.1/§6.1). This is a feature here (lets Channel A's output ride VBUS while Channel B's rides 3.3V, off a shared VCC=VBUS), but it also means a design that assumes "output can't exceed VCC" and therefore skips checking the pull-up rail against VO's absolute max could be wrong in the other direction on a different design - always check the VO abs max explicitly, not VCC.

5. **Stability-region graph is read visually, not from a table** (Figure 5-18, p.14). The numeric boundaries quoted above (~6nF, ~400nF) are estimates off a log-log plot. If a cathode capacitor is ever added for filtering, don't trust these numbers to better than roughly a factor of 2 - either avoid the region by a wide margin (as recommended: no capacitor at all) or get an actual bench measurement/SPICE model before committing to a value inside the marginal zone.

6. **Hysteresis margin depends on BOM grade.** The worked error budget (±137mV worst case) assumes TLV431 blank grade (±1.5%) and 1% divider resistors. Substituting a looser TLV431 grade is fine (grades only get tighter), but substituting 5% resistors is not checked here and would need the budget re-run - it could approach half the hysteresis band.

7. **CMR floor for legacy (non-B) parts is 0V, not below.** The REF-node and DIV-node both sit near 1.24V in this design, comfortably clear of 0V - no CMR issue expected - but if the reference were ever redesigned to a lower voltage, remember the non-B parts' input common-mode range only extends to 0V (down to -0.1V for B-version parts, §5.2 p.4), and going more than 0.3V negative on an input risks incorrect output per the footnote on every electrical characteristics table (e.g. footnote 1, §5.10 p.10).

8. **Response time is a non-issue for the 1kHz/sub-1ms scan requirement.** LM2903 response times (0.3-1.3µs typ, non-B; down to 300ns for B version, §5.7/§5.11 pp.7,10) are ~1000x faster than anything relevant to a power-sequencing/rail-sense signal - this detector's speed is not a design constraint, it's essentially instantaneous relative to the rest of the system.

---

## Open questions / not determinable from the datasheet

- **Exact TLV431 stability-region boundaries** (Figure 5-18, p.14) - graphical only, no tabulated CL breakpoints given at any specific IK. Estimated visually above; would need a higher-resolution read or a bench/SPICE check to pin down precisely.
- **LM2903 recommended bypass capacitor value** - the datasheet recommends one (§7.2.4, p.19) but gives no farad value.
- **TLV431 recommended decoupling capacitor value** - same, §8.4.1 (p.24) gives placement guidance only, no value.
- **Channel-to-channel isolation/crosstalk spec for LM2903** - not given anywhere in the document; the two comparators are described as "independent" but no isolation number (dB, mV, etc.) is specified.
- **Which LM2903/LM393 grade (B vs. non-B) and which TLV431 grade (blank/A/B) will actually be sourced** - this is a BOM/sourcing decision, not something the datasheet decides; the worked numbers above assume the more conservative, more commonly LCSC-stocked non-B LM2903 and blank-grade TLV431, and should be re-checked against whatever part numbers actually land in the BOM.
- **P-FET gate threshold voltage, gate charge, and BJT hFE/Vbe(sat)** needed to fully size the gate pull-ups and BJT base resistor precisely - these come from the AO3401A/AO4407A/MMBT2222A datasheets, not from LM2903 or TLV431, and are explicitly out of scope for this note (task was scoped to "your chips: LM2903 + TLV431" only). The 20kΩ gate pull-up and general BJT topology given above are reasonable starting points based on the comparator side of the interface only.
- **Exact system-level polarity mapping** (which physical P-FET each comparator channel's opposite-polarity output should drive, and what each P-FET actually gates in the power tree) is a schematic-level decision that a blind datasheet read cannot and should not invent - the note above shows how to *get* two opposite-polarity, VBUS/3.3V-referenced outputs from one dual comparator package sharing one hysteretic threshold, but not which specific FET each one belongs to.
