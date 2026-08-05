# TPS54302 - datasheet research
> Independent datasheet read. Not written against the existing schematic.

Source: `Refrences/datasheets/TPS54302-buck.pdf`, TI literature number **SLVSDG6C**, "MAY 2016 - REVISED MARCH 2026" (current revision C at time of writing). A second copy, `TPS54302-buck-lcsc.pdf` (ZHCSF83A, May 2016, Chinese-language, LCSC-hosted mirror), is the **original Rev A** text - it predates two spec changes TI made in Rev C (ESD rating dropped from ±4000V to ±2500V HBM; EN threshold typicals shifted from 1.21V/1.19V to 1.23V/1.16V; high-side current-limit max raised from 5.9A to 6A). Everything below cites the current SLVSDG6C figures unless stated otherwise. Also referenced: `app-notes/TI-buck-layout-guide.pdf` (Analog Applications Journal 1Q2015, "Five steps to a great PCB layout for a step-down converter") and `app-notes/TI-power-supply-layout-slpa005.pdf` ("Reducing Ringing Through PCB Layout Techniques", SLPA005).

## Part identity

- TPS54302: 4.5V-28V input, 3A-capable synchronous **peak-current-mode** buck converter, two integrated NFETs, SOT-23-THIN (DDC), 6 pins (p.1, Features/Description).
- Package: DDC, SOT-23-THIN, 6-pin, 2.9mm x 2.8mm nominal body (p.1, Package Information table). **No exposed thermal pad is called out anywhere in the pin table** (Table 4-1) - GND is a normal leaded pin, not a pad. Primary heat path is the GND/VIN/SW copper, not a bottom-side thermal pad (see Layout notes).
- Pinout, 6 pins (Section 4, Figure 4-1, Table 4-1): 1 GND, 2 SW, 3 VIN, 4 FB, 5 EN, 6 BOOT. No SS/TR pin, no PG pin - soft-start is fixed internally and there is no power-good output.
- Fixed switching frequency, internally compensated, internal 5ms soft-start, integrated boot diode - "reduces external component count" (Section 3, Description).

## Absolute maximum ratings that constrain this design

All from Table 5.1 (Section 5.1, p.4) and Table 5.3 (Section 5.3, p.4):

| Pin/parameter | Abs max | Recommended operating | Notes |
|---|---|---|---|
| VIN | -0.3V to 30V | 4.5V to 28V | HV rail here maxes at 20V (highest USB-PD fixed voltage) - **10V of headroom below abs max, 8V below the top of recommended range**. Comfortable margin. |
| EN | -0.3V to 7V | -0.1V to 5.5V | 3.3V GPIO and a resistor-divider UVLO network both stay well inside this. |
| FB | -0.3V to 7V | -0.1V to 5.5V | Regulated node, always ~0.596V in normal operation. |
| BOOT-SW | -0.3V to 7V | -0.1V to 5.5V | Gate-drive rail, nominally ~5V above SW. |
| SW | -0.3V to 30V (continuous); -5V to 30V (20ns transient) | -0.1V to 28V | Negative transient allowance covers normal switch-node ringing below GND. |
| TJ (operating) | -40°C to 150°C (abs max) | -40°C to 125°C | |
| Tstg | -65°C to 150°C | - | |

**ESD (Table 5.2, p.4, Rev C only):** HBM ±2500V (per ANSI/ESDA/JEDEC JS-001), CDM ±1500V (per JESD22-C101). The older LCSC-mirrored datasheet lists ±4000V HBM - **use the ±2500V figure**, it is the current spec.

The VIN rail never gets close to its abs max in this design (20V vs 30V abs max / 28V recommended max), so VIN transient overshoot during PD renegotiation is not a concern by itself. What *is* a real constraint is the low end: internal VIN UVLO is only ~4.1V typical (see below), so the part will attempt to switch as soon as VIN clears that threshold - including at the 5V PD state, where a 5V-in/5V-out buck has no headroom to regulate.

## Key electrical characteristics

All from Section 5.5 (Electrical Characteristics, p.5) and Section 5.6 (Timing Requirements, p.5) unless noted. Test condition: TJ = -40°C to 125°C, VIN = 4.5V to 28V, unless otherwise noted.

| Parameter | Min | Typ | Max | Unit | Condition |
|---|---|---|---|---|---|
| IQ, non-switching quiescent current | - | 45 | - | µA | EN=5V, VFB=1V |
| IOFF, shutdown current | - | 2 | - | µA | EN=GND |
| VIN UVLO, rising | 3.8 | 4.1 | 4.4 | V | |
| VIN UVLO, falling | 3.3 | 3.6 | 3.9 | V | |
| VIN UVLO hysteresis | 400 | 480 | 560 | mV | |
| VENrising (EN threshold, rising) | - | 1.23 | 1.28 | V | |
| VENfalling (EN threshold, falling) | 1.1 | 1.16 | - | V | |
| I(EN_INPUT), EN pull-up current | - | 0.7 | - | µA | VEN=1V (this is "Ip" in the UVLO equations) |
| I(EN_HYS), EN hysteresis current | - | 1.55 | - | µA | VEN=1.5V (this is "Ih") |
| VFB, feedback reference voltage | 0.581 | 0.596 | 0.611 | V | VIN=12V - a ±2.5% spec (Section 6.3.7 states this explicitly) |
| I(SKIP), pulse-skip peak-inductor-current threshold | - | 500 | - | mA | VIN=12V, VOUT=5V, L=10µH; not production tested |
| R(HSD), high-side FET RDS(on) | - | 85 | - | mΩ | TA=25°C, VBST-SW=5V |
| R(LSD), low-side FET RDS(on) | - | 40 | - | mΩ | TA=25°C, VIN=12V |
| I(LIM_HS), high-side current limit (peak inductor current) | 4 | 5 | 6 | A | |
| I(LIM_LS), low-side source current limit (valley inductor current) | 3.1 | 4 | 5.5 | A | |
| fSW, center switching frequency | 290 | 400 | 510 | kHz | |
| Thermal shutdown, rising | - | 160 | - | °C | |
| Thermal shutdown hysteresis | - | 10 | - | °C | (i.e. restarts once TJ drops below ~150°C) |
| Thermal hiccup time | - | 32768 | - | cycles | |
| tHIC_WAIT (overcurrent hiccup wait) | - | 512 | - | cycles | Table 5.6 |
| tHIC_RESTART (hiccup time before restart) | - | 16384 | - | cycles | Table 5.6 |
| tSS, internal soft-start | - | 5 | - | ms | Table 5.6, fixed, not adjustable (no SS pin) |
| tMIN_ON, minimum on-time | - | 110 | - | ns | measured 90%-90%, 1A load; not production tested |

**RDS(on) temperature dependence is only shown graphically** (Figures 5-3 / 5-4, "High-Side/Low-Side FET Rds(on) vs Junction Temperature") - no tabulated hot value is given, only the 25°C typical in the table above. Any thermal calc using only the 25°C number will under-estimate loss at operating temperature; treat that as a **known gap, not a datasheet omission** you can paper over with a guess.

**Datasheet internal inconsistency worth flagging:** Figure 6-3 (Spread Spectrum diagram, Section 6.3.12) labels the center frequency "fc = 500 KHz", which contradicts the 400kHz typical center frequency in Table 5.5. This looks like reused generic artwork from another TI part in the same family rather than a real spec for this device. **Design to the Electrical Characteristics table value (400kHz typ, 290-510kHz min/max) plus the stated ±6% spread-spectrum jitter around whatever the actual center is** - do not design to the 500kHz figure in the diagram.

Thermal resistance (Section 5.4, Table 5.4, p.4), DDC-6 package:

| Metric | Value | Unit |
|---|---|---|
| RθJA | 118.9 | °C/W |
| RθJC(top) | 58.3 | °C/W |
| RθJB | 35.0 | °C/W |
| ψJT | 14.0 | °C/W |
| ψJB | 34.8 | °C/W |
| RθJA_EVM (TI's own EVM board) | 57.2 | °C/W |

The gap between RθJA (118.9, minimal JEDEC test board) and RθJA_EVM (57.2, TI's actual layout with real copper) is **more than 2x** - board copper matters enormously for this package since there's no exposed pad to sink heat through a via farm; the only path is the leaded pins and whatever copper pour is around them.

## Design equations

All from Section 6.3 (Feature Description) and Section 7.2.3 (Detailed Design Procedure).

**Feedback divider** (Section 6.3.8, Eq. 3 / Section 7.2.3.3, Eq. 6-7). R2 = upper resistor (VOUT to FB), R3 = lower resistor (FB to GND), matching the reference schematic (Figure 7-1) labeling:

```
VOUT = Vref * (R2/R3 + 1)
R3 = R2 * Vref / (VOUT - Vref)
```
TI recommends starting with R2 ≈ 100kΩ, 1% tolerance or better, and notes larger values trade light-load efficiency for FB-node noise susceptibility (Section 6.3.8).

**External input UVLO via EN divider** (Section 6.3.5, Eq. 1-2, Figure 6-1). R4 from VIN to EN, R5 from EN to GND:

```
R4 = [VSTART*(VENfalling/VENrising) - VSTOP] / [Ip*(1 - VENfalling/VENrising) + Ih]
R5 = R4*VENfalling / [VSTOP - VENfalling + R4*(Ip + Ih)]
```
where Ip = 0.7µA, Ih = 1.55µA, VENfalling = 1.16V, VENrising = 1.23V (all typ, per the current Rev C table). TI recommends external UVLO hysteresis > 500mV (Section 6.3.5, text).

**Inductor** (Section 7.2.3.5.1, Eq. 8-10):
```
LMIN = VOUT*(VIN(MAX) - VOUT) / (VIN(MAX) * KIND * IOUT * fsw)
IL(RMS) = sqrt( IOUT(MAX)^2 + (1/12) * [ VOUT*(VIN(MAX)-VOUT) / (VIN(MAX)*LO*fSW*0.8) ]^2 )
IL(PK)  = IOUT(MAX) + VOUT*(VIN(MAX)-VOUT) / (1.6 * VIN(MAX) * LO * fSW)
```
KIND (ripple-current ratio) is designer's choice; TI's own worked example uses 0.35, and notes ceramic (low-ESR) output caps tolerate higher KIND while higher-ESR caps want KIND≈0.2 (Section 7.2.3.5.1, text).

**Output capacitor** (Section 7.2.3.5.2, Eq. 11-15):
```
CO(transient)  > 2*dIOUT / (fSW*dVOUT)                          -- transient/load-step sizing
CO(ripple)     > (1/(8*fSW)) * (Iripple/VOUTripple)              -- ripple-based sizing
RESR(max)      < VOUTripple / Iripple
fo (crossover, no feedforward cap) = 5.1 / (VOUT*CO)             -- keep < 40kHz per TI's guidance
ICOUT(RMS)     = (1/sqrt(12)) * VOUT*(VIN(MAX)-VOUT) / (VIN(MAX)*LO*fSW*NC)   -- NC = number of parallel output caps
```

**Feedforward capacitor** (Section 7.2.3.5.3, Eq. 16), across R2, only useful/needed when COUT is dominated by low-ESR ceramics:
```
C6 = (1/(2*pi*fo)) * (1/R2)
```

**Input capacitor** (Section 7.2.3.1, Eq. 4-5):
```
dVIN = IOUT(MAX)*0.25 / (CBULK*fsw) + IOUT(MAX)*ESRMAX
ICIN(RMS) = IOUT(MAX) / 2
```
Max voltage seen by the input cap = VINmax + dVIN/2 (Section 7.2.3.1, text).

## Worked values for this application

Both instances target **VOUT = 5.0V**, VIN(MAX) = **20V** (highest USB-PD fixed voltage, not the datasheet's own 28V example), fSW = 400kHz typ (Table 5.5). KIND = 0.3 chosen (mid-point of TI's stated 0.2-0.4 useful range, Section 7.2.3.5.1).

### Feedback divider (shared by both instances)

Ideal ratio needed: R2/R3 = VOUT/Vref - 1 = 5.0/0.596 - 1 = 7.38926.

Two E24 candidates evaluated (R2 = upper, R3 = lower):

| R2 (E24) | R3 (E24) | Ratio | VOUT (typ Vref) | Error |
|---|---|---|---|---|
| 100kΩ | 13kΩ | 7.6923 | 5.181V | **+3.61%** |
| 110kΩ | 15kΩ | 7.3333 | 4.967V | **-0.67%** (recommended - close to TI's suggested ~100k impedance, low divider current ~33µA) |
| 200kΩ | 27kΩ | 7.4074 | 5.011V | **+0.22%** (tighter, but ~4.4x lower divider current, more FB-node noise sensitivity per Section 6.3.8) |

Recommendation: **R2 = 110kΩ, R3 = 15kΩ** for both instances (identical divider - divider current is negligible next to either 300mA or 2A load, so there's no reason to differ it per instance). Stack the resistor tolerance (1%, E24 assumed) with the Vref spec spread (±2.5%, Table 5.5) and worst-case output swings roughly -3.2% to +1.8% around 5.0V (using Vref_min/max = 0.581/0.611V against the 7.333 ratio) - i.e. **4.84V to 5.09V** worst-case, before line/load regulation and layout-induced FB noise are even considered.

### Inductor - clean buck (A) vs big buck (B)

| | Clean buck (A), IOUT=0.3A | Big buck (B), IOUT=2A |
|---|---|---|
| LMIN (Eq. 8, KIND=0.3) | 104.2µH | 15.6µH |
| Chosen L | 100µH (E12, slightly below LMIN -> KIND_actual ≈ 0.31) | 15µH (E12, slightly below LMIN -> KIND_actual ≈ 0.31) |
| IL(PK) (Eq. 10, at VIN=20V) | 0.359A | 2.39A |
| IL(RMS) (Eq. 9, at VIN=20V) | 0.302A | 2.01A |
| Recommended Isat rating | ≥0.6-1A (generous margin trivial at this current) | ≥3A (≈25-30% margin over 2.39A operating peak) |
| Recommended Irms rating | ≥0.4A | ≥2.5A |

**The two instances need different inductors, both in value and current rating - confirmed by the math, not just "different loads."** The clean buck's 300mA max load pushes LMIN to over 100µH to hit even a modest 30% ripple ratio, while the big buck's 2A load wants ~15µH. Using one part for both would either massively over-spec the small one's ripple, or run the big one at very high di/dt with a huge saturation margin problem.

**Pulse-skip crossover:** I(SKIP) = 500mA typ (Table 5.5). Clean buck peak current (0.359A) stays below this across its whole 150-300mA operating range, meaning **the clean buck runs in Eco-mode/DCM pulse-skipping essentially all the time**, not fixed-frequency CCM - apparent switching frequency will sag at light load (Section 6.3.2, Section 6.4.2). Big buck peak current (2.39A) is well above 500mA, so it runs in fixed-frequency CCM across its whole operating range.

Saturation-current caveat: I(LIM_HS) max = 6A (Table 5.5). Choosing the big buck's inductor for only ~3A Isat (comfortable margin over the 2.39A *operating* peak) means the inductor could saturate before the IC's own hard current limit trips under an output short. This is a normal, common trade-off (full 6A-rated inductors for a 2A rail are oversized/expensive) but is worth an explicit note for anyone doing FMEA on submodule-port shorts.

### Input/output capacitors, including DC-bias derating

Using Eq. 11-15 with the transient/ripple spec left **not specified by the project** (no explicit dV/dI transient budget was given for either rail): defaulting to TI's own validated reference-design target for a 5V output, Table 7-2, "Recommended Component Values" - **COUT = 44µF** (their reference design, Figure 7-1, uses two 22µF/25V X7R ceramics in parallel to hit this, C4+C5). This should be revisited once actual LED brightness-step and submodule hot-plug inrush transients are characterized - the project brief explicitly states gated-5V (instance B) ripple is "irrelevant," but instance A's output feeds a 3V3 LDO for the ADC domain, where ripple/noise is not irrelevant, so instance A's COUT sizing deserves more scrutiny than instance B's once real numbers exist.

Input cap: TI's own 8-28V/5V/3A reference design (Section 7.2.3.1, Figure 7-1) uses C1 = 10µF ceramic + optional C2 = 0.1µF, both effectively rated 35V, noting "maximum voltage across the input capacitors is VINmax + dVIN/2" and that the selected part's 35V rating and >2A ripple-current capacity "provide ample margin" against their 28V max input.

**This project's HV rail maxes at 20V, not 28V - but the DC-bias derating problem is worse here, not better, because case size will likely be smaller.** This is general MLCC/ceramic-capacitor knowledge, **not stated in the TPS54302 datasheet** (the IC datasheet only says "capacitor voltage rating must be greater than the maximum input voltage" and gestures at "additional capacitance deratings for aging, temperature, and DC bias must be considered," Section 6.3.8/7.2.3.5.2, without giving numbers):

- X7R ceramic capacitors lose a large fraction of their nominal capacitance as applied DC bias approaches their rated voltage - commonly 40-60%+ loss for a small-case-size part biased near its rated voltage, much less loss the further below rated voltage you stay.
- A **25V-rated** part biased at 20V is at 80% of its rated voltage - deep into the steep part of the derating curve for typical 0402/0603 X7R parts. A **50V-rated** part biased at 20V is at only 40% of rated voltage, sitting in a much gentler part of the curve.
- **Recommendation for this design: rate CIN/COUT for 25V minimum (matching TI's margin ratio scaled to a 20V rail), but prefer 50V-rated parts in 0805 or larger where board area allows**, and always check the actual chosen part's DC-bias curve from its own (non-TI) datasheet before finalizing nominal capacitance - "not specified" here is a real gap, not a rounding error, since it can mean losing more than half the intended output capacitance right when the rail is at its most stressful voltage (20V, post-PD-negotiation).
- **0402 is explicitly wrong for the bulk input/output caps** on this rail: a 10-22µF/25-50V X7R part does not exist in 0402 (capacitance-per-case-size limits), so these must be 0805 or 1206 (project default explicitly excludes "bulk caps on rails above 5V" from 0402, and this is exactly that case).
- The small 0.1µF high-frequency VIN bypass cap (C2 in the reference design) *can* stay 0402 if a correctly 25-50V-rated 0402 part is selected (these exist commercially) - the DC-bias loss on a small-value HF bypass cap is a much smaller practical problem than on the bulk cap, since even a 50%-derated 0.05µF still does its job as HF bypass.
- The 0.1µF BOOT capacitor sits on the ~5V BOOT-SW rail (abs max 7V), not the 20V rail - a 10-16V-rated 0402 X7R/X5R part is fine there with negligible derating concern (Section 6.3.10 explicitly recommends X7R or X5R for BOOT).

**Bus-distributed HV is a distance concern, not just a voltage-rating one.** Section 7.3 (Power Supply Recommendations) explicitly warns: "If the input supply is located more than a few inches from the device...additional bulk capacitance may be required...An electrolytic capacitor with a value of 47µF is a typical choice." The HV rail here is explicitly "distributed between tiles, switched per-edge" - i.e. exactly the long-source-impedance scenario this warning is about, for *every* tile downstream of the source tile. Recommend local bulk capacitance per tile beyond the immediate CIN, sized in whatever low-profile SMD form factor (polymer/tantalum/multiple parallel ceramics) fits the reflow/low-profile constraints - true through-hole/SMD electrolytics are a poor fit for a hotplate-reflow, low-profile board, so this likely wants to be extra parallel ceramic rather than TI's literal "electrolytic" suggestion.

### EN pin / UVLO worked example

Section 6.3.5 explicitly states: "If an application requires control of the EN pin, use open-drain or open-collector output logic to interface with the pin," and "Float the EN pin to enable" (Table 4-1) because of the internal pull-up current source. This has direct implications for both instances:

**Clean buck (A)** - "always-on once HV exists," but should not actually regulate while VIN sits at the unusable 5V PD state (see Gotchas below). Recommend the R4/R5 external-UVLO divider, not a bare float, so the part stays disabled until VIN is comfortably above the 5V dropout danger zone. Worked example targeting **VSTART (turn-on) ≈ 7.5V, VSTOP (turn-off) ≈ 6.6V** - comfortably above the 5V PD state, comfortably below the 9V PD state:

```
R4 ideal = 342.7kΩ -> nearest E24 = 330kΩ
R5 ideal = 60.1kΩ  -> nearest E24 = 62kΩ
```
Back-solving the actual thresholds with R4=330kΩ, R5=62kΩ (using Ip=0.7µA before crossing threshold, Ip+Ih=2.25µA after, per the equations' structure):
```
VSTART ≈ 7.55V
VSTOP  ≈ 6.59V
Hysteresis ≈ 0.95V   (> TI's recommended 500mV minimum, Section 6.3.5)
```
At VIN = 20V (top of range), this divider puts EN at ≈3.28V - comfortably inside the -0.1V to 5.5V recommended range (Table 5.3) and far under the 7V abs max (Table 5.1).

**Big buck (B)** - must additionally be MCU-gated. Per Section 6.3.5's explicit guidance, do **not** drive EN push-pull from the 3.3V GPIO (it would fight both the internal pull-up and the R4/R5 UVLO network). Use an open-drain stage (small NMOS, gate from the 3.3V GPIO, drain to EN, source to GND) in parallel with the same R4/R5 divider: GPIO low -> transistor off -> UVLO divider governs, buck enables once VIN clears ~7.5V; GPIO high -> transistor pulls EN to GND -> forced off regardless of VIN. This gives the MCU authoritative override in both directions (can force off even with valid HV present; cannot force on below the UVLO floor without also defeating the divider, which is correct - the MCU choosing "on" while VIN is still at 5V should not create a false regulation attempt).

### Thermal, big buck at 2A

No switching-loss coefficients (Qg, Eon/Eoff, driver loss) are published anywhere in this datasheet - only RDS(on) at 25°C (Table 5.5) and thermal resistances (Table 5.4). The following is therefore a **conduction-loss-only floor**, not a full thermal budget:

```
P_HS = IL(RMS)^2 * R(HSD) * D
P_LS = IL(RMS)^2 * R(LSD) * (1-D)
```
At VIN=9V (D=VOUT/VIN=0.556, worst case for combined conduction given roughly balanced D), L=15µH:
```
IL(RMS) = 2.004A (Eq. 9)
P_HS = 2.004^2 * 0.085 * 0.556 = 0.190W
P_LS = 2.004^2 * 0.040 * 0.444 = 0.071W
Total conduction ≈ 0.26W
```
At VIN=20V (D=0.25), IL(RMS)=2.013A, total conduction ≈ 0.21W. Both figures use only the 25°C RDS(on) typicals - real dissipation will be somewhat higher once switching loss and hot-RDS(on) are included, but neither is quantified in this datasheet.

Temperature rise, worst-case RθJA (118.9°C/W, minimal JEDEC test board, Table 5.4): even doubling the conduction-only estimate to ~0.5W for a rough switching-loss allowance gives ΔTJ ≈ 60°C. At a plausible enclosed/stacked-tile ambient of 40-50°C, that's TJ ≈ 100-110°C - inside the 125°C operating max (Table 5.3) but with less margin than the raw numbers suggest, and there is real risk of tripping thermal shutdown (160°C typ, Section 6.3.14) at higher ambient plus underestimated switching loss. Using the EVM figure instead (RθJA_EVM = 57.2°C/W, Table 5.4) roughly halves that rise - **this is the practical argument for generous copper pour under and around this part**, since it has no exposed pad to do that work for you.

## Recommended implementation (pin by pin)

1. **VIN (pin 3)** - direct to the HV rail. Abs max 30V, recommended max 28V; our 20V max leaves large margin (Table 5.1/5.3). Needs local bulk + HF bypass caps per the capacitor section above.
2. **GND (pin 1)** - source of the low-side FET and controller ground reference; "Connect sensitive VFB to this GND at a single point" (Table 4-1). No exposed pad - see Layout notes.
3. **SW (pin 2)** - switch node to the inductor. Abs max -0.3V/30V continuous, -5V/30V for 20ns transients (Table 5.1) - covers normal ringing. Keep this node's copper area minimal (Section 7.4.1) both instances.
4. **FB (pin 4)** - feedback divider midpoint. Recommended R2=110kΩ/R3=15kΩ per above. Kelvin-connect to GND at a single point (Table 4-1); keep the trace short (Section 7.4.1).
5. **EN (pin 5)** - external UVLO divider (R4=330kΩ from VIN, R5=62kΩ to GND) for both instances; big buck additionally gets an open-drain NMOS override to GND from the MCU GPIO. Do not float on instance A even though the datasheet allows it - floating gives no protection against the 5V dropout state.
6. **BOOT (pin 6)** - 0.1µF ceramic (X7R/X5R recommended, Section 6.3.10) to SW. Mandatory for high-side gate drive; BOOT-SW UVLO is ~2.1V typ, below which the high-side FET is disabled (Section 6.3.10, Figure 5-9).

## Decoupling and passives

| Component | Instance A (clean buck) | Instance B (big buck) | Notes |
|---|---|---|---|
| CIN bulk | ≥10µF nominal, 25-50V rated, 0805/1206 | ≥10µF nominal, 25-50V rated, 0805/1206 (may want more given 2A load - Eq. 4/5 not fully solvable without a chosen ESRmax/part) | DC-bias derating applies to both - see above |
| CIN HF bypass | 0.1µF, 25-50V rated (0402 OK if correctly rated) | same | Section 7.2.3.1 calls this "optional"; recommended given the 20V rail and shared/distributed bus |
| CBOOT | 0.1µF, X7R/X5R, ~10-16V rating | same | Section 6.3.10, mandatory |
| COUT | ≥44µF nominal (2x22µF/25V typical starting point per Table 7-2), derate for DC bias | same starting point, but ripple explicitly "irrelevant" per project brief so this can likely be reduced once real transient specs exist | Not specified by project - defaulted to TI's own reference value |
| L | 100µH, ≥0.6-1A Isat | 15µH, ≥3A Isat, ≥2.5A Irms | See inductor section - different parts required |
| R2 (FB upper) | 110kΩ, E24, 0402 (low voltage/current, fine at 0402) | same | |
| R3 (FB lower) | 15kΩ, E24, 0402 | same | |
| R4 (EN/UVLO upper) | 330kΩ, E24, 0402 (standard 0402 chip resistors are commonly rated ≥50V working voltage - general resistor knowledge, not in this datasheet - 20V across R4 is not a concern) | same | |
| R5 (EN/UVLO lower) | 62kΩ, E24, 0402 | same | |
| Feedforward cap (C6/C8 in datasheet, inconsistent naming) | Optional; only needed if COUT is low-ESR ceramic dominated and phase margin needs boosting (Section 7.2.3.5.3) | same | Eq. 16, not solved here - needs a chosen crossover frequency first |
| MCU-gate NMOS (EN override) | n/a | small-signal NMOS, VGS(th) compatible with 3.3V drive, drain to EN, source to GND | Open-drain override per Section 6.3.5 guidance |

## Layout notes

From Section 7.4 (Layout, p.21-22) plus the two app notes:

- VIN and GND traces as wide as possible - both for trace impedance and heat dissipation (Section 7.4.1). Given there's no exposed pad on this package, **copper area is the primary thermal path** - directly relevant to closing the RθJA vs RθJA_EVM gap noted above.
- Input and output capacitors placed as close to the device as possible, minimize trace impedance, with sufficient vias (Section 7.4.1). The buck-layout app note frames this as "Step #1" - place and route the input cap *immediately after the IC, before anything else*, because parasitic inductance between CIN and VIN/GND creates switching voltage spikes that "can lead to IC failure" (buck-layout guide, p.11).
- SW trace physically short and wide, minimize its copper area to reduce radiated EMI and parasitic-capacitance noise coupling (Section 7.4.1; buck-layout guide "Step #2"). No switching current should flow under the device (Section 7.4.1).
- FB trace: separate VOUT sense path to the upper feedback resistor, Kelvin connection to GND, kept away from the high-voltage switching trace, preferably with a ground shield, and made "as small as possible" (Section 7.4.1). This is the single most emphasized small-signal routing point in both the datasheet and the app note ("most critical small-signal connection," buck-layout guide p.12).
- GND trace between output capacitor and the GND pin as wide as possible (Section 7.4.1).
- Single-point/star ground: join the noisy power ground and quiet small-signal ground at one point (buck-layout app note, "Step #5") - here that's effectively the GND pin itself, since there's no thermal pad to use as the star point.
- Both app notes stress minimizing loop area between input cap, high-side FET, low-side FET/SW node, and back to input cap ground - this is the loop that generates SW-node ringing (SLPA005, "Optimized Placement of Power Stage Components").
- Placement order recommended by the app note (buck-layout guide, "five steps"): (1) input cap, (2) inductor + optional SW-node RC snubber, (3) output cap + FB/VOS routing, (4) small-signal components (divider resistors, boot cap), (5) single-point ground + vias to the rest of the system, ~1 via per amp of current as a rule of thumb.

## Gotchas and failure modes

- **The 5V PD state is not usable as an input to either buck if you need a clean regulated 5V out.** VIN UVLO turns the part on around 4.1V typical (Table 5.5) - well below 5V - so a naive design (EN floated per the datasheet's literal default) would have the IC *attempt* to regulate 5V-in/5V-out with essentially zero headroom. At near-100% duty cycle: (a) output sags below setpoint by whatever the FET RDS(on) x current drop is (trivial for instance A at 300mA, ~170mV at instance B's 2A from R(HSD)=85mΩ alone, before adding inductor DCR or connector/switch resistance elsewhere on the distributed HV bus - and output can never exceed input regardless), and (b) line/load regulation and ripple rejection degrade because there's no control authority left. This is exactly why the project routes BS+ (bootstrap 5V) from raw VBUS pre-negotiation rather than from either TPS54302 instance - **that architectural choice is validated by this datasheet's numbers**, and the R4/R5 UVLO divider worked out above (~7.5V turn-on) is the mechanism that keeps both instances off during the 5V PD state rather than limping in dropout.
- **EN floating is the datasheet's literal default ("float to enable"), but is a bad idea here.** A hotplug tile with a floating EN pin during the 0V-to-4.1V VIN ramp is racing against noise/ESD on an unterminated high-impedance node right next to a switching regulator. Use the R4/R5 divider (also gets you the UVLO benefit above) rather than a literal float.
- **Prebias/OR-bus interaction:** Section 6.3.6 (Safe Start-Up into Prebiased Outputs) states the part won't let the low-side FET discharge a prebiased output during monotonic startup - both FETs stay off until internal soft-start voltage exceeds FB voltage. This is a real hotplug-relevant feature, **but it protects the TPS54302's own FB/output node, not necessarily what happens on the far side of the ideal-diode OR device on BS+.** If that ideal-diode device (not covered by this datasheet) properly blocks reverse current, instance A's own output node won't actually see the shared bus's pre-existing 5V while its own buck is unpowered, and Section 6.3.6 is a secondary safety margin rather than the primary hotplug protection. Verify the ideal-diode device's reverse-blocking behavior separately - don't rely on this datasheet's prebias handling as the mechanism keeping a newly-attached tile's unpowered buck output safe.
- **Hiccup mode on overcurrent is not instantaneous shutdown** - cycle-by-cycle current limiting engages first (Section 6.3.11), and only after the overload persists for tHIC_WAIT = 512 cycles (1.28ms at 400kHz) does the part shut down and wait tHIC_RESTART = 16384 cycles (41ms at 400kHz) before retrying (Section 6.3.11, Table 5.6). For instance B (LEDs + submodule ports, both plausible short-circuit sources on a hotplug system), this means a downstream short causes a ~1.3ms window of elevated current before hiccup engages, repeating roughly every 41ms while the fault persists - relevant to any upstream fusing/current-budget logic the MCU is doing.
- **No dedicated SS/TR or PG pin.** Soft-start is fixed at 5ms internally (Table 5.6) - cannot be slowed down for a heavier inrush load (e.g. all 30 LEDs plus 4 submodule ports drawing max current the instant instance B's EN is asserted), and there's no power-good signal for the MCU to poll - "did the big buck actually come up" has to be inferred some other way (e.g. an ADC-monitored resistor divider on gated-5V, external to this IC).
- **Min on-time (110ns, Table 5.6) is "not production tested"** - i.e. it's a design guideline, not a guaranteed/tested spec. Not a binding constraint at VIN≤20V/VOUT=5V (25% min duty at 20V, versus a ~4.4%-duty min-on-time floor at 400kHz), but worth knowing it isn't a hard guaranteed number if the design ever changes to accept higher VIN or lower VOUT.
- **Spread-spectrum diagram (Figure 6-3) states a center frequency inconsistent with the Electrical Characteristics table** (500kHz vs 400kHz typ) - see note in Key electrical characteristics. Do not size ripple/EMI filtering off the 500kHz figure.
- **Two different datasheet revisions exist for this exact part** (Rev A via LCSC vs Rev C direct from TI) with different ESD ratings and EN thresholds - if BOM/sourcing pulls the LCSC-hosted PDF as the reference, the numbers used for EN/UVLO divider math could silently be stale. Confirm which revision the actual purchased die matches (should be Rev C given "SLVSDG6C...REVISED MARCH 2026" and current TI orderable-part status).

## Open questions / not determinable from the datasheet

- **RDS(on) at operating temperature** - only shown graphically (Figures 5-3/5-4), no tabulated hot value. Any thermal margin calc beyond the 25°C-typical conduction-loss floor above is an estimate, not a datasheet number.
- **Switching loss (Qg, Eon/Eoff, driver loss)** - not published anywhere in this datasheet. The thermal worked example above is conduction-loss-only.
- **Minimum off-time / minimum boot-recharge time** - the datasheet asserts 100% duty cycle capability as long as BOOT-SW > 2.1V typical (Section 6.3.10) and shows an internal "Boot Charge" block in the functional diagram (Figure, Section 6.2), but never quantifies how that boot-recharge mechanism actually behaves near 100% duty (e.g. does it force a minimum LS on-time each cycle, or use a separate internal charge pump/LDO independent of switching). Not specified.
- **DC-bias derating curves for any specific capacitor** - this is inherently outside an IC datasheet's scope, but it's a real, sizeable gap for this design (rail sits at 20V much of the time) and needs the actual chosen MLCC part's own datasheet before finalizing nominal CIN/COUT values.
- **Inductor package/footprint dimensions** - explicitly out of scope for this IC datasheet; both instances' inductor is a vendor part choice constrained by the Isat/Irms/inductance values derived above, not by anything in the TPS54302 datasheet.
- **Exact CIN/COUT minimum values via Eq. 4/5/11-15** - several of these equations need a project-specified ESRmax, transient dI/dV budget, or output-ripple target that the project brief doesn't provide for either rail (explicitly "ripple irrelevant" for instance B, no number given for instance A). Values used in the worked section default to TI's own validated reference-design numbers rather than a value derived from a project spec that doesn't exist yet.
