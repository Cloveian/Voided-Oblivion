# CD74HC4067 16:1 analog mux - datasheet research
> Independent datasheet read. Not written against the existing schematic.

**Sources used:**
- **TI** = Texas Instruments `CD74HC4067, CD74HCT4067` datasheet, doc SCHS209D, Nov 1998 – revised Dec 2024. File: `Refrences/datasheets/CD74HC4067-analog-mux-ti.pdf`. This is the datasheet for the actual target part (CD74HC4067SM / SSOP-24). All figures marked **TI** come from here, with section/table/page cited.
- **Nexperia** = Nexperia `74HC4067; 74HCT4067` datasheet, Rev. 10, 25 July 2024. File: `Refrences/datasheets/74HC4067-analog-mux.pdf`. **This is a different manufacturer's silicon, not the TI part** — same logic function and pinout, but not guaranteed to match TI's electrical numbers. It is cited only to fill gaps TI leaves open (e.g., RON vs. VCC shape, per-channel/common-pin capacitance split, off-isolation, THD). Every Nexperia number is labeled as such and flagged as non-TI.
- **RP2350** = Raspberry Pi `RP2350 Datasheet`, Section 12.4.3 "SAR ADC", pp. 1069–1074. File: `Refrences/datasheets/RP2350-datasheet.pdf`.
- The two app notes `TI-adc-input-driving.pdf` and `TI-mux-analog-selection.pdf` supplied for this task turned out, on inspection, to be misfiled/misnamed: their actual content is TI *Analog Design Journal* issues on shunt-based motor phase-current sensing, RF ADC noise figure, instrumentation amplifiers, and battery-charger power paths. **Neither contains any content about multiplexers, mux settling time, or driving an ADC through a mux.** They contributed nothing to this analysis and are not cited further below.
- Hall sensor datasheets (`GH39FKSW-hall-sensor.pdf`, `SS49E-hall-honeywell.pdf`) were checked for source-impedance data needed for the RC calculation; neither specifies an output impedance (see Open Questions).

---

## Part identity

- Target part per project title: **CD74HC4067SM** (TI, SSOP-24, "SM" suffix = SSOP package option).
- TI orderable part matching this: `CD74HC4067SM96` / `CD74HC4067SM96.A`, package **SSOP (DB) | 24**, body 8.20 mm × 7.40 mm nominal. (TI, Package Information table, p.1; Packaging Information addendum, p.15).
- TI datasheet covers two logic families on the same die family: **HC** (2 V–6 V, CMOS input levels) and **HCT** (4.5 V–5.5 V, TTL-compatible input levels). The project's 3.3 V rail only makes sense with the **HC** variant — HCT's recommended VCC floor (4.5 V) excludes 3.3 V operation entirely (TI, Section 7, Recommended Operating Conditions, p.6). All figures below are for **CD74HC4067**, not CD74HCT4067.
- Function: single-pole 16-throw bidirectional analog switch, digitally addressed by 4 select lines (S0–S3) plus an active-low enable (E). TI truth table: E=1 → no channel selected (all off); E=0 → S3:S0 binary selects channel 0–15 (TI, Table 4-1, Section 4.1, p.5). Nexperia's pin table explicitly calls E "active LOW" (Nexperia, Table 2, p.5/26).
- Nexperia's equivalent part (74HC4067) is **not** electrically identical to TI's CD74HC4067 despite the shared JEDEC-style part number and pinout — see RON comparison below. Do not substitute one for the other assuming matched RON/timing without re-checking.

---

## Absolute maximum ratings that constrain this design

**TI (Section 5, Absolute Maximum Ratings, p.5):**

| Parameter | Min | Max | Unit |
|---|---|---|---|
| VCC (DC supply, HC) | −0.5 | **7** | V |
| IIK, DC input diode current (VI < −0.5 V or > VCC+0.5 V) | −20 | 20 | mA |
| IOK, DC output diode current | −20 | 20 | mA |
| ICC, DC VCC or GND current | −50 | 50 | mA |
| IO, DC output source/sink current per pin | −25 | 25 | mA |
| TJ max | — | 150 | °C |
| Tstg | −65 | 150 | °C |

**Nexperia (Table 4, Limiting Values, p.7/26)** shows a wider absolute-max VCC (−0.5 V to **+11.0 V**), ISW ±25 mA, ICC ±50 mA, Ptot 500 mW, per-switch power 100 mW — these are the *Nexperia die's* limits, not TI's. **Design to the TI 7 V absolute maximum**, since the target part is CD74HC4067. The project's 3.3 V rail sits nowhere near this ceiling, but it matters for ESD/surge event sizing on the common pin if it's ever exposed to a fault above VCC — clamp diodes exist (TI notes "inputs include clamp diodes… enables use of current limiting resistors to interface inputs to voltages in excess of VCC," Nexperia general description, p.1) but IIK is capped at 20 mA, so any external overvoltage clamp path needs a series resistor sized to that limit.

**Recommended operating conditions (TI, Section 7, p.6):** VCC (HC) 2 V–6 V; analog switch I/O voltage VIS = GND to VCC; TA −55 °C to +125 °C. **3.3 V sits comfortably inside the recommended HC operating range** — this is a real, not marginal, operating point per the recommended-conditions table, even though (see below) it is not one of the *characterized test points*.

---

## Key electrical characteristics (state clearly what is guaranteed at 3.3 V)

**The central caveat for this whole section: TI's Electrical Characteristics tables for HC devices (Section 8, p.7–8) are only populated at VCC = 2 V, 4.5 V, and 6 V. There is no 3.3 V column anywhere in the TI datasheet.** Everything at 3.3 V below is either (a) directly guaranteed because it's specified as a fraction of VCC, or (b) interpolated/extrapolated and explicitly marked as such — never presented as a tested TI number.

### Logic input thresholds (S0–S3, E)
TI (Section 8, p.7), values at 25 °C:

| VCC | VIH min | VIL max |
|---|---|---|
| 2 V | 1.5 V | 0.5 V |
| 4.5 V | 3.15 V (=0.70×VCC) | 1.35 V (=0.30×VCC) |
| 6 V | 4.2 V (=0.70×VCC) | 1.8 V (=0.30×VCC) |

TI's Features list separately states "High noise immunity: NIL = 30%, NIH = 30% of VCC at VCC = 5V" (TI, Features, p.1) — a proportional-threshold claim, but explicitly scoped to VCC = 5 V and not one of the three tested columns. **At 3.3 V, TI gives no tested VIH/VIL.** Interpolating the 4.5 V/6 V pattern (which holds a clean 70%/30% split) gives an *estimated* VIH_min ≈ 2.31 V, VIL_max ≈ 0.99 V at 3.3 V — this is a derived estimate, not a datasheet guarantee. In practice this is not a real risk: the RP2350 drives these pins with a rail-to-rail 3.3 V CMOS GPIO (VOH near 3.3 V, VOL near 0 V), which clears either the tested-column pattern or the low-VCC 2 V column (1.5 V/0.5 V) with large margin either way.

### RON (analog switch on-resistance)
TI (Section 8, "'ON' Resistance IO = 1mA", p.7) gives two RON figures per VCC — a "VCC or GND → VCC or GND" condition (switch driven at either rail, call it RON(rail)) and a "VCC to GND → VCC to GND" condition (RON(peak), i.e. worst point across the analog swing):

| VCC | RON(rail) typ/max @25°C | RON(rail) max @ −55…125°C | RON(peak) typ/max @25°C | RON(peak) max @ −55…125°C |
|---|---|---|---|---|
| 4.5 V | 70 / 160 Ω | 240 Ω | 90 / 180 Ω | 270 Ω |
| 6 V | 60 / 140 Ω | 210 Ω | 80 / 160 Ω | 240 Ω |

**TI gives no RON figure at 2 V or at 3.3 V at all.** The lowest characterized VCC for RON is 4.5 V.

Nexperia's own device (different silicon, Table 6, p.8/26) shows RON(rail) typ = 150 Ω at VCC = 2.0 V vs. 90 Ω typ at VCC = 4.5 V — i.e., roughly a **1.7× increase in RON going from 4.5 V down to 2 V** on that part, with an explicit footnote: *"At supply voltages (VCC−GND) approaching 2 V, the analog switch ON resistance becomes extremely non-linear. Therefore it is recommended that these devices be used to transmit digital signals only, when using these supply voltages."* (Nexperia, Table 6 footnote [1], p.8/26). This is a real, cited warning about low-VCC analog behavior, but it is about the *Nexperia* part, and its 2 V/4.5 V ratio is not proof of what TI's die does — it is only used here as a qualitative shape reference (RON rises as VCC falls) since TI provides no data point to interpolate from directly.

**Conclusion on RON at 3.3 V: not specified by TI.** For the settling-time calculation below, a design value is derived from TI's 4.5 V worst-case-over-temperature figure with an explicit engineering margin applied for the unquantified low-VCC increase — clearly flagged as an estimate, not a TI spec (see "Worked values").

### Channel-to-channel matching (ΔRON)
TI (Section 8, p.7): ΔRON = 10 Ω at VCC = 4.5 V, 8.5 Ω at VCC = 6 V, 25 °C only. **Note:** the extracted table shows a single value per row rather than clearly separated MIN/TYP/MAX columns (the PDF layout collapses this ambiguously) — treat as either typ or max conservatively; Nexperia's equivalent parameter (Table 6, p.8/26) is unambiguously listed as "Typ 9 Ω @ 4.5V" with no max given, which is broadly consistent. No 3.3 V or 2 V figure from either vendor.

### RON flatness across the analog input range
TI shows this only as **Figure 14-1, "Typical ON Resistance vs Input Signal Voltage"** (Section 14, p.12), a curve at VCC = 4.5 V, Vis swept 0–6 V, TA = 25 °C. This is a graph, not a table — **no numeric flatness figure (e.g., ΔRON across Vis in Ω) is tabulated anywhere in either datasheet.** Not specified quantitatively.

### Leakage currents
TI (Section 8, p.7), tested only at **VCC = 6 V**:
- IZ, off-switch leakage (E = VCC, whole device disabled, measured at Z): ±0.8 µA typ/max @25°C, ±8 µA max over both extended temp ranges.
- IIL, input (control pin) leakage: ±0.1 µA @25°C, ±1 µA over extended temp.

TI does not break leakage down per-channel or give a separate "on-state leakage" figure. Nexperia (Table 7, p.9–10/26), tested at VCC = 6 V and 10 V, gives finer granularity:
- IS(OFF) **per channel**: ±0.1 µA @25°C / ±1 µA (−40…125°C) at VCC = 6 V.
- IS(OFF) **all channels** (sum): ±0.8 µA @25°C / ±8 µA at VCC = 6 V.
- IS(ON): ±0.8 µA @25°C / ±8 µA at VCC = 6 V (this labeling matches TI's single IZ figure).

**No leakage data at 3.3 V or 2 V from either vendor.** Leakage in CMOS switches generally falls as VCC falls (less reverse-bias headroom on the substrate/well junctions), so using the 6 V figures as a conservative upper bound at 3.3 V is a reasonable but unverified assumption — flagged in Open Questions.

**Error this injects into a high-impedance source:** with 15 unselected channels per mux each leaking up to ±1 µA (extended-temp, Nexperia per-channel figure) into the shared Z node, and that current forced through whatever series resistance sits between the Hall sensor and the mux common pin, ΔV = I_leak × R_source. Because the Hall sensor's own output impedance is not specified (see Open Questions), this error cannot be bounded from datasheets alone — see the worked numbers below for why it matters at 12-bit resolution.

### Off-channel signal feedthrough / crosstalk
TI (Section 13, Analog Channel Specifications, p.11): **"Switch OFF signal feedthrough" = −75 dB @ 1 kHz, VCC = 4.5 V.** This is the one clean tabulated crosstalk number in either datasheet.

Nexperia (Table 13, Additional Dynamic Characteristics, p.18–19/26): "isolation (OFF-state)" αiso = **−50 dB typ** at both VCC = 4.5 V and 9.0 V, RL = 600 Ω, presented as a curve vs. frequency in Fig. 14 (not a single-frequency spot value like TI's). The two numbers (−75 dB TI vs. −50 dB Nexperia) are not directly comparable (different test conditions/manufacturer) but both indicate strong (>50 dB) isolation between an off channel and the selected channel, at their respective test frequencies.

### Capacitances
TI (Section 13, p.11):
- CI (switch/channel input capacitance, per Yn pin): 5 pF.
- CCOM (common pin, Z): 50 pF.

Nexperia (Table 13, p.18–19/26), same physical quantities under different names:
- Csw independent pins (Y): 5 pF typ.
- Csw common pin (Z): 45 pF typ.

The two vendors agree closely (5 pF/50 pF vs. 5 pF/45 pF) — used as cross-check. **CCOM ≈ 45–50 pF at the common pin is the single largest capacitance in the analog signal path**, larger than the RP2350's own ADC sampling capacitance by roughly 50×.

### Switching times
TI (Section 11, Switching Characteristics HC, p.9), CL = 50 pF unless noted:

| Parameter | VCC=4.5V typ | VCC=4.5V max (25°C) | VCC=4.5V max (−55…125°C) |
|---|---|---|---|
| Switch Turn On, Sn→Out (tPZH/tPZL) | 60 ns | 75 ns | 90 ns |
| Switch Turn Off, Sn→Out (tPHZ/tPLZ) | 58 ns | 73 ns | 87 ns |
| Propagation delay, Yn→Z (tPHL/tPLH) | 9 ns | 15 ns | 22 ns |

No 3.3 V column exists here either. As with RON, use the 4.5 V worst-case-over-temperature figures as the nearest characterized floor.

### Break-before-make
TI states in Features (p.1): **"Break-before-make switching — 6 ns (typ) at 4.5 V."** Nexperia's feature list similarly states "Typical 'break before make' built-in" (Nexperia, Features, p.1). **This is a typical characteristic claim, not a tested min/max spec in either device's characteristics tables** — there is no guaranteed break-before-make time bounded by a MIN/MAX row anywhere in either document. Implication: the architecture (single decoder driving mutually-exclusive switches, per the functional block diagrams in both datasheets) inherently prevents two channels from being driven onto Z simultaneously by design, and both vendors advertise it, but neither commits to a worst-case number you can put in a timing budget.

### Charge injection
**Not specified in either datasheet.** Neither the TI nor the Nexperia document contains a "charge injection" parameter, table row, or test circuit. This cannot be bounded from the documents on hand — flagged as an open question.

### Supply current
TI (Section 8, p.8): ICC (quiescent) = 8 µA max @25°C, up to 160 µA max at −55…125 °C, tested at VCC = 6 V. This is static/quiescent current only.

TI CPD (power dissipation capacitance, Section 11, p.9) = 93 pF at VCC = 5 V — used per the standard HC-family formula to estimate *dynamic* supply current from switching activity (see Decoupling section). TI does not state whether this 93 pF is per-switch or whole-device. Nexperia's equivalent parameter (CPD = 29 pF, Section 11 footnote [5], p.14/26) is explicitly labeled **"per switch."** This inconsistency between vendors is noted as an open question below.

### Enable/inhibit (E) pin
Active LOW (TI Table 4-1, p.5; Nexperia Table 2, p.5/26: "enable input (active LOW)"). E = HIGH forces all 16 channels off regardless of S0–S3. It is a standard CMOS input — like S0–S3, it must never be left floating.

### Analog signal range vs. supply
TI (Section 7, Recommended Operating Conditions, p.6): VIS (analog switch I/O voltage) = GND to VCC. Nexperia (Table 5, p.7/26): VSW = GND to VCC. **Full rail-to-rail switch — no headroom loss at either end**, which matches a ratiometric 3.3 V Hall sensor whose output already swings within 0–VCC.

---

## Design equations

**RC settling (single-pole approximation):** for a step applied through a resistance R into a capacitance C, the output after n time constants is within a fraction ε of final value where ε = e^(−n), i.e. n = −ln(ε) = ln(1/ε).

**Settling target for 12-bit resolution, ½ LSB:** ε = 1 / (2 × 2^12) = 1/8192 = 1.221×10⁻⁴.
n = ln(8192) ≈ **9.01 time constants.**

**Per-channel dwell floor:**
t_channel = t_prop (mux address→output propagation) + n·τ (RC settling) + t_ADC (RP2350 SAR acquire+convert)

**Total scan time:** t_scan = N_channels × t_channel (N = 30 keys; 2 spare mux channels unused per tile)

**Max scan rate:** f_max = 1 / t_scan

**Dynamic switching current (order-of-magnitude, standard HC power formula, both datasheets cite the same form):**
I_dynamic ≈ CPD × VCC × f_switch (from PD = CPD·VCC²·f, TI Section 11 note; Nexperia Section 11 note [5], same formula)

---

## Settling time and scan budget (the headline calculation)

### Every term in the RC path

| Element | Value | Source |
|---|---|---|
| Hall sensor output impedance (R_source) | **Not specified** | GH39FKSW and SS49E datasheets checked — neither states an output impedance. GH39F's only related note: "output voltage should be measured with a voltmeter of input impedance >10 kΩ" (GH39FKSW datasheet, Electromagnetic characteristics table footnote) — implies a non-trivial but unstated Zout. Treated as an unknown/open risk, not zero. |
| Mux RON (design value used) | **~400 Ω** (derived, not a datasheet spec) | TI's worst-case-over-temperature RON(peak) at the nearest characterized voltage is 270 Ω at VCC = 4.5 V (Section 8, p.7). Since RON rises as VCC falls (direction confirmed qualitatively by Nexperia's own 4.5 V→2 V curve, Table 6/Fig. 7, p.8/26 — a different die, used only for shape), a ~1.5× engineering margin is applied to TI's 270 Ω figure to stand in for the uncharacterized 3.3 V case: 270 Ω × 1.5 ≈ 400 Ω. **This is an estimate, explicitly not a TI number.** |
| Mux common-pin capacitance (CCOM) | 50 pF | TI, Section 13, p.11 (cross-checked against Nexperia's 45 pF, Table 13, p.18–19/26) |
| PCB trace R, C | Negligible (assume <5 Ω, <3 pF for a short 0402-scale trace) | Not a datasheet value — board-layout dependent, not characterized here |
| RP2350 ADC sampling capacitance | ~1 pF | RP2350 Datasheet, Section 12.4.3, p.1069: "The ADC input is capacitive. When sampling, the ADC places about 1pF across the input." |
| RP2350 effective ADC input impedance | >100 kΩ even at 500 kS/s | RP2350 Datasheet, Section 12.4.3, p.1069: "The effective impedance, even when sampling at 500 kS/s, is over 100 kΩ. DC measurements have no need to buffer." |

**R_total ≈ R_mux (400 Ω design value) + R_source (unknown) + R_trace (negligible) → dominated by the mux's own RON given no other large term is known.**
**C_total ≈ 50 pF (CCOM) + 1 pF (ADC) + a few pF trace ≈ 55 pF.**

τ = R_total × C_total ≈ 400 Ω × 55 pF ≈ **22 ns**

n·τ = 9.01 × 22 ns ≈ **198 ns** (round to 200 ns) — time to settle to ½ LSB of 12 bits.

### Per-channel dwell time

- t_prop (address-change → switch conducting): TI worst-case over full military temperature range, VCC = 4.5 V (nearest characterized point, CL = 50 pF): **90 ns** ("Switch Turn On Sn to Out," TI Section 11, p.9).
- n·τ (RC settling, derived above): **~200 ns**
- t_ADC (RP2350 SAR, fixed hardware cost): **2 µs** — "Capturing a sample takes 96 clock cycles (96 × 1/48 MHz) = 2 μs per sample (500 kS/s)" (RP2350 Datasheet, Section 12.4.3, p.1069). This single number already covers both the RP2350's internal sample-and-hold acquisition and the SAR conversion; the datasheet gives no further split.

**t_channel ≈ 90 ns + 200 ns + 2000 ns ≈ 2.29 µs, round to ~2.3 µs per channel.**

### Total scan and verdict

t_scan(30 channels) = 30 × 2.3 µs ≈ **69 µs**

f_max = 1 / 69 µs ≈ **14.5 kHz** theoretical max scan rate (ignoring firmware GPIO-toggle overhead, which is out of scope of this datasheet-only analysis but is typically tens of ns on a 150 MHz core and would not change this conclusion).

**Against the 1000 Hz requirement (1 ms budget for a full 30-key scan): 69 µs used of 1000 µs available = 6.9% of the budget. Margin factor ≈ 14.5×.**

**Verdict: comfortable, not tight.** Even under a doubly-pessimistic scenario — RON at 3.3 V twice the derived 400 Ω estimate, a nontrivial Hall sensor R_source (e.g. a few hundred ohms to ~1 kΩ), and generous firmware overhead per channel — the total per-channel time would still be dominated by the RP2350's own fixed 2 µs ADC conversion window (about 85–90% of the per-channel budget in every scenario examined), and 30 × ~3–4 µs is still only 90–120 µs, leaving a >8× margin against the 1 ms requirement. **The mux's RON/settling behavior is not the scan-rate bottleneck; the RP2350's own 500 kS/s SAR ADC throughput is**, and even that leaves over an order of magnitude of headroom at 1000 Hz.

---

## Worked values for this application

### RON at 3.3 V: ideal → derived design value
- TI's nearest characterized worst-case RON(peak), full temp range, VCC = 4.5 V: 270 Ω (TI, Section 8, p.7).
- No TI 3.3 V data point exists to interpolate from directly (2 V column is absent for RON).
- Design value used: 270 Ω × 1.5 (engineering margin for unquantified low-VCC increase) ≈ **400 Ω**. This is explicitly an estimate — not a spec, not from either datasheet's tables.

### Optional protective series resistor at the common (Z) pin — E24 worked example
If a small series resistor is added at the mux's Z output for ESD/glitch robustness before the RP2350 ADC pin, its effect on settling time can be bounded even though its value is a design choice, not a datasheet number:
- Target: keep the *added* settling-time contribution ≤ 50 ns (an arbitrary, generous margin given the 14.5× headroom above).
- Ideal R: 50 ns ÷ (9.01 × 22 pF total added shunt cap, using a 22 pF optional filter cap example below) ≈ 252 Ω.
- Nearest E24 value: **240 Ω**.
- Actual added settling contribution: 9.01 × 240 Ω × 22 pF ≈ 47.6 ns.
- Error vs. 50 ns target: −4.8%.
- Net effect on total scan budget: negligible (adds <1.5 µs across 30 channels, still <2% of the 1 ms budget).

### Optional filter capacitor at Z — helps EMI, costs settling time, still cheap given margin
Adding a 22 pF C0G/NP0 0402 cap at the ADC input (on top of the mux's own 50 pF CCOM) raises C_total to ~77 pF. New τ (with the 400 Ω design RON) = 30.8 ns; n·τ ≈ 277 ns; t_channel ≈ 90 ns + 277 ns + 2000 ns ≈ 2.37 µs; 30-channel scan ≈ 71 µs — still under 7.2% of the 1 ms budget. **Given how much margin exists, a modest deliberate filter cap is affordable if EMI testing calls for one; a large one (>200 pF) would still only cost ~2.7% of the budget.** This is a genuine trade space, not a forced choice — the datasheets support either decision.

### Dynamic switching-current estimate (shared select lines, both muxes switching together)
Using TI's CPD = 93 pF (Section 11, p.9 — ambiguous whether per-switch or per-device, treated here as a whole-device figure, the more conservative reading) at VCC = 3.3 V and an effective switching frequency of ~1/2.3 µs ≈ 434 kHz (worst case, every channel change is a full transition):
- I_dynamic per mux ≈ CPD × VCC × f = 93 pF × 3.3 V × 434 kHz ≈ 133 µA average.
- With **two muxes switching simultaneously** (shared S0–S3), the combined transient draw on the local 3V3 rail roughly doubles to **~266 µA average**, with instantaneous peaks higher than the average for the few-nanosecond switching edges.
- This is small compared to typical LDO/regulator drive capability but is a genuine simultaneous, correlated event (see Gotchas) — addressed with local decoupling, not by redesigning the mux interface.

---

## Recommended implementation (pin by pin)

Based on datasheet function only (TI, Section 4, Pin Configuration and Functions, p.4; Table 4-1, p.5):

- **VCC (pin 24):** 3V3 ADC-domain rail. Recommended operating range confirms 3.3 V is valid (TI Section 7, p.6). Decouple locally (see below).
- **GND (pin 12):** tie to the common ground plane, shortest possible return path to VCC decoupling cap.
- **Z / common I/O (pin 1):** the analog output feeding the RP2350 ADC pin. Route short and direct; keep clear of digital switching traces (select lines, buck regulator switch nodes) per the project's stated ADC-domain noise sensitivity. Optional series R (E24, e.g. 240 Ω, worked above) and/or optional small filter cap (e.g. 22 pF C0G) are both affordable given the timing margin.
- **Y0–Y15 (pins 2–9, 16–23):** connect to the 16 Hall sensor analog outputs (2 spare channels per mux, since only 15 keys map per mux for 30 total across two muxes — confirm actual channel allocation against the key matrix). Neither datasheet gives explicit guidance for unused/spare channels; given the measured off-channel isolation (−75 dB TI / −50 dB Nexperia), leaving spares floating vs. tying to GND makes negligible difference to the selected channel's accuracy — tying to GND via the same footprint discipline as populated channels is the tidier choice.
- **S0–S3 (pins 10, 11, 14, 13):** drive from shared RP2350 GPIOs, routed to **both** muxes with matched trace length/topology, since "shared select lines" means both decoders must see the same transitions at effectively the same time (see Gotchas for the supply-transient implication). Standard CMOS push-pull drive from the RP2350 clears the (interpolated) 3.3 V thresholds with large margin.
- **E (pin 15), active LOW:** never leave floating (CMOS input). Either tie directly to GND for "always enabled" simplicity, or drive from an MCU GPIO if a hardware "all channels off" state is wanted during power-up/hotplug sequencing — the datasheet supports either, this is a system-level choice outside the mux datasheet's scope.

---

## Decoupling and passives

- **Local bypass:** place a 100 nF (0402, X7R) capacitor directly at each mux's VCC pin (24) to GND (12), shortest loop area, one per mux (two total per tile, since select lines are shared but VCC/GND are still per-device pins).
- Given the switching-time figures (tens of ns) and the −3 dB bandwidth (89 MHz HC / 89 MHz HCT at VCC = 4.5 V, TI Section 13, p.11), a smaller high-frequency companion cap (e.g., 10 nF or 1 nF, 0402) alongside the 100 nF is reasonable practice for a chip with ns-scale internal switching edges, though the datasheets do not specify a required decoupling value — this is general HC-family practice, not a cited spec.
- The **dynamic current from simultaneous mux switching (~266 µA average combined, worked above) is small** relative to typical local decoupling capability; a 100 nF cap supplies far more instantaneous charge than needed for a single switching edge at these currents. No unusual decoupling burden is created by the shared-select architecture — it is a real, correlated event, but not a large one in absolute terms.
- **Series resistance/capacitance at the common pin:** see "Worked values" — both are affordable in the timing budget given the 14.5× margin; a small series R helps ESD/glitch robustness at negligible timing cost, and a small filter cap helps EMI at negligible timing cost. Neither is required by the datasheets; both are optional given the margin.

---

## Layout notes

- Route the Z-pin-to-ADC trace short, direct, and away from the select-line traces and any switching-regulator nodes (gated-5V buck, HV rail) — this is a project-level noise concern (ADC domain sensitivity, per project context), not a datasheet requirement, but the datasheet's 89 MHz bandwidth figure (TI Section 13, p.11) confirms the mux itself will faithfully pass high-frequency noise coupled onto that trace, so keeping it short/shielded matters.
- Route S0–S3 as a matched group to both muxes (equal length, same layer if possible) since they are shared and simultaneously decoded.
- Solid ground plane under and around both muxes; no split plane beneath the analog signal path.
- Place the 100 nF decoupling cap for each mux as close to its VCC/GND pins as the SSOP-24 footprint allows.
- Two spare channels per mux (30 keys into 32 channels) — if left unpopulated, keep their PCB pads/traces short so they don't become unintentional antennas coupling into the −50/−75 dB-isolated bus.

---

## Gotchas and failure modes

1. **TI's electrical characteristics tables do not include a 3.3 V column.** RON, VIH/VIL, and leakage are all characterized at 2 V/4.5 V/6 V only (TI Section 8). Reading the 70 Ω typ @ 4.5 V RON number and assuming that's what you get at 3.3 V is wrong — RON is known to increase as VCC decreases (confirmed only qualitatively, via a different manufacturer's part).
2. **Do not confuse the RP2350's own ADC-input-mux settling behavior with this external mux's.** The RP2350 datasheet states "Switching AINSEL requires no settling time" (Section 12.4.3.1, p.1070) — but that statement is about the RP2350's *internal* selection among its own bonded ADC-capable GPIOs, not about an external CD74HC4067 analog switch feeding one of those pins. The external mux **does** require settling time, as derived above (~200 ns for ½ LSB at 12 bits) — this is a genuinely easy documentation-reading mistake to make.
3. **E is active LOW.** Tying it high (assuming "enable" is active-high) disables all 16 channels permanently.
4. CMOS control inputs (S0–S3, E) must never float — undriven inputs on this family risk excess supply current and unpredictable switch state, standard CMOS practice, not something either datasheet calls out explicitly for this part but implied by "CMOS input" classification.
5. **Break-before-make (6 ns typ @ 4.5 V, TI Features p.1) is a typical characteristic, not a guaranteed spec** — no MIN/MAX row exists for it in either datasheet's characteristics tables. Don't budget a hard number against it.
6. **TI and Nexperia parts are not interchangeable for RON/timing purposes** despite matching part numbers and pinout — TI's RON(rail) typ at 4.5 V is 70 Ω vs. Nexperia's 90 Ω at the same conditions (TI Section 8 vs. Nexperia Table 6). If the BOM or a substitute-parts flow ever swaps in the Nexperia die expecting identical electrical behavior to the TI part this analysis was built around, that assumption is wrong.
7. **Charge injection is entirely unspecified** by both datasheets — cannot be bounded or ruled out from the documents on hand.
8. **Leakage-into-high-impedance-source error is real but not fully quantifiable** here because the Hall sensor's output impedance is not published (see Open Questions) — the mux side of the equation (≤1 µA per channel at extended temp, Nexperia) is known, but the resulting voltage error at the ADC depends on an unspecified sensor parameter.

---

## Open questions / not determinable from the datasheet

- **RON at 3.3 V (TI)** — not tested; only 2 V/4.5 V/6 V columns exist. The 400 Ω design value used above is an engineering estimate with an applied margin, not a datasheet number.
- **VIH/VIL guaranteed at 3.3 V (TI)** — not tested; interpolated from the 4.5 V/6 V pattern only.
- **Leakage currents at 3.3 V (TI, Nexperia)** — both vendors test only at 6 V/10 V; no low-voltage leakage data exists.
- **Charge injection** — not specified by either datasheet at any voltage.
- **Numeric RON flatness across the analog input range** — TI Figure 14-1 is a graph only; no tabulated values were extractable.
- **Hall sensor output impedance** (GH39FKSW, SS49E) — neither Hall sensor datasheet states an output impedance; this is the largest unresolved unknown feeding into the RC settling and leakage-error calculations above. GH39FKSW's only related hint is a recommendation to measure its output with a voltmeter of input impedance >10 kΩ, implying a non-negligible but unstated Zout.
- **Whether TI's CPD = 93 pF (Section 11, p.9) is per-switch or per-device** — ambiguous in TI's table; Nexperia's equivalent parameter is explicitly labeled "per switch" (29 pF), but that's a different part.
- **Whether TI's ΔRON figures (10 Ω @ 4.5 V / 8.5 Ω @ 6 V, Section 8, p.7) are typ or max** — the extracted table layout does not clearly separate the columns for this row.
- **RP2350's internal split of its 96-cycle (2 µs) ADC sample into acquire-time vs. convert-time cycles** — the RP2350 datasheet states the combined figure only (Section 12.4.3, p.1069) and does not break it down further in the sections reviewed, so this analysis treats the mux settling as strictly serial before the full 2 µs window rather than assuming any overlap opportunity.
- The two supplied app notes (`TI-adc-input-driving.pdf`, `TI-mux-analog-selection.pdf`) do not contain mux-relevant content at all (see Sources note above) — if TI application guidance on driving a SAR ADC through an external mux is needed, it was not found in the files provided for this task.
