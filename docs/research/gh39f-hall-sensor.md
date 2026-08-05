# GH39F Hall-effect sensor - datasheet research
> Independent datasheet read. Not written against the existing schematic.

**Sources used**
- `Refrences/datasheets/GH39FKSW-hall-sensor.pdf` - GH39F series datasheet, GOCHIP Electronics Technology (Shanghai) Co., Ltd (鑫雁电子科技(上海)有限公司), Rev 1.0, dated 2016-02-29. 6 pages total, entire document read via `pdftotext -layout`. **Original document is in Chinese; all figures below are translated by me and the Chinese table/section names are given alongside so they can be checked against the source.**
- `Refrences/datasheets/SS49E-hall-honeywell.pdf` - Honeywell SS39ET/SS49E/SS59ET series datasheet, used only for sanity-checking and for parameters GH39F leaves out. Every SS49E-sourced number below is labeled as such and must not be read as a GH39F spec.
- `Refrences/datasheets/74HC4067-analog-mux.pdf` - Nexperia 74HC4067/74HCT4067, used for mux Ron/Ci/Csw figures for the driving analysis.
- `Refrences/datasheets/RP2350-datasheet.pdf` - used for RP2350B ADC timing/impedance figures (§12.4, "ADC and Temperature Sensor").
- `Refrences/datasheets/TPD2E2U06-esd.pdf` - used only for one clamp-voltage figure in the gotchas section.
- `Refrences/datasheets/app-notes/TI-adc-input-driving.pdf` - opened and read in full. **This document is actually "Selecting amplifiers for shunt-based current sensing in 3-phase motor drives" (TI Analog Design Journal) - it covers current-shunt amplifier selection for motor phase-current sensing, not generic ADC-input RC-driving theory.** It contains no source-impedance/settling-time material applicable to a mux+SAR-ADC front end, so it is not cited for any number below. This is flagged explicitly per the "say so if a datasheet is thin/wrong" instruction rather than silently ignored.
- Standard RC-settling math (`t = n·τ`, `n = ln(1/ε)`) and a generic N52 remanence figure (Br ≈ 1.43 T, a magnet-grade constant, not from any datasheet in this repo) are used in the derivation sections and are explicitly marked as external/generic, not GH39F datasheet values.

---

## Part identity

- **GH39F** is the series name. The datasheet cover reads "GH39F 系列线性霍尔电路" (GH39F series linear Hall-effect IC), manufactured by GOCHIP Electronics Technology (Shanghai) Co., Ltd (website golden-chip.com). [p.1/6, cover]
- The datasheet defines **two package codes** in its pinout section [p.2/6, "管脚定义"]:
  - **UA** = SIP-3L (TO-92S), through-hole.
  - **SW** = SOT23-3L, surface mount.
- **"GH39FKSW"** is not spelled out anywhere in the datasheet body - it never appears as a string in the PDF (checked by full-text search of the extracted text). What I can determine:
  - The trailing **"SW"** matches the datasheet's own SOT23-3L package designator, so GH39FKSW is, with reasonable confidence, the SOT23-3L-packaged part in this series.
  - Confirmed independently via LCSC's listing (C266230, GoChip Elec Tech (Shanghai), "GH39FKSW", package SOT-23-3L) — https://lcsc.com/product-detail/Linear-Hall-Sensors_GoChip-Elec-Tech-Shanghai-GH39FKSW_C266230.html. LCSC's scraped summary lists "sensitivity 1.8mV/Gs" and "magnetic field range ±100mT (±1000G)", matching the datasheet's typical values, and "SOT-23-3L" package, consistent with "SW".
  - **What the leading "K" denotes is not determinable** from either the datasheet or the LCSC listing — it is not explained in either source. Treat it as a GOCHIP-internal bin/grade/taping code unless GOCHIP is contacted directly.
- Internal structure per the datasheet's own description: "由霍尔电压发生器，线性放大器和射极跟随器组成" = "consists of a Hall voltage generator, a linear amplifier, and an emitter follower." [p.2/6, intro] Confirmed by the block diagram [p.4/6, "电路内部框图"]: HALL SENSOR → Amplifier → an output stage biased by a **65 µA (typ.)** current source to GND. This exact block-diagram topology and exact 65 µA figure also appear in the Honeywell SS49E datasheet's "Current Sourcing Output Block Diagram" [SS49E, Figure 1, p.3] — strong circumstantial evidence GH39F is architecturally a clone/equivalent of the SS49E-class device (see also the near-identical linearity, null voltage, and supply-current numbers below). This is an observation, not a datasheet-stated fact, and should not be relied on for any number GH39F doesn't itself specify — it does justify treating SS49E as a reasonable sanity-check part, which is what it's used for throughout.

---

## Absolute maximum ratings that constrain this design

From "极限参数" (Extreme/limit parameters) table [GH39F datasheet, p.2/6]:

| Parameter | Symbol | Value | Unit |
|---|---|---|---|
| Supply voltage | VCC | 15 | V |
| Output current | IOUT | 10 | mA |
| Operating ambient temperature | TA | -40 to +85 | °C |
| Storage temperature | TS | -65 to +150 | °C |

**Notable gaps** (checked the full extracted text for these terms — none present):
- **No reverse-supply / reverse-voltage rating is given anywhere in the GH39F datasheet.** For comparison, SS49E's abs-max table explicitly gives Vs = **-5.0 V to 8.0 V** [SS49E, Table 2] — i.e. Honeywell explicitly rates reverse-voltage tolerance to -5V; GOCHIP states nothing for GH39F, positive or negative. Do not assume reverse-supply protection exists on the GH39F part.
- **No ESD rating (HBM/CDM/IEC) is given anywhere.** SS49E's datasheet only carries a generic "Class 3" ESD-sensitivity caution icon [SS49E, p.3] with no kV figure either, so this is a shared gap across both parts, not a GH39F-specific gap — treat the SOT23-3L pins as unprotected against ESD and outside-supply-rail conditions in design terms.

---

## Key electrical characteristics

From "电磁特性 (TA=25℃, VCC=5V)" — "Electromagnetic characteristics, TA = 25°C, VCC = 5V" [GH39F datasheet, p.3/6]. **The whole table is characterized at VCC = 5V** even though the VCC row itself lists an operating range of 3.0-6.5V — there is no separate 3.3V row or ratiometric-scaling note.

| Parameter (translated) | 中文原文 | Symbol | Condition | Min | Typ | Max | Unit |
|---|---|---|---|---|---|---|---|
| Supply voltage | 电源电压 | VCC | — | 3.0 | — | 6.5 | V |
| Quiescent output voltage | 静态输出电压 | Vout | B = 0 | 2.25 | 2.50 | 2.75 | V |
| Supply current | 电源电流 | ICC | — | — | 6.0 | 9.0 | mA |
| Sensitivity | 灵敏度 | — | B = 0 to ±1000 Gs | 1.45 | 1.8 | 2.0 | mV/Gs |
| Output lower-swing limit | 输出端下限电压 | VH | — | 0.80 | — | 1.05 | V |
| Output upper-swing limit | 输出端上限电压 | VL | — | 3.95 | — | 4.20 | V |
| Magnetic range | 磁场范围 | B | — | ±650 | ±1000 | — | Gs |
| Linearity | 线性度 | — | — | — | 0.70 | — | % |

Footnote translated: "Output voltage should be measured with a voltmeter of input impedance greater than 10 kΩ; magnetic flux density should be measured at the device's most sensitive region (see outline drawing)." [p.3/6] — this is a **measurement-setup note**, not an output-impedance specification of the device; see the "Does it work at 3.3V" and "Driving a mux + ADC" sections below for why that distinction matters.

**Not specified anywhere in the GH39F datasheet** (checked explicitly, all absent from the extracted text):
- Power-on / start-up settling time
- Response time / bandwidth to a field step while powered
- Output source/sink current rating (no "output current" row exists in the electrical table — only the abs-max IOUT = 10 mA, which is a maximum-before-damage rating, not a guaranteed drive spec)
- Output impedance (Ω)
- Noise (voltage or current spectral density)
- Temperature drift coefficients (%/°C) for offset or sensitivity — only qualitative graphs exist (see below)
- Ratiometricity (no % or ppm/V figure, no explicit statement)

**Graphs present but not usable as numeric specs** [p.3/6, "特性曲线" / characteristic curves]: three plots — output vs. magnetic field (VCC=5V, no load), quiescent output vs. VCC (2-8V sweep), and quiescent output vs. temperature (-50 to 100°C). These are vector/image plots; `pdftotext` extracts only the axis labels (VOUT(V) 0-5, B(GS) -1000 to 1000, VCC(V) 2-8, TA(℃) -50 to 100), not the trace values, so no numeric offset/sensitivity-drift coefficient can be read off them. The VCC-sweep graph is the only evidence in the GH39F document that output tracks supply — see "Does it work at 3.3V?" below.

---

## Does it work at 3.3V?

**Yes, 3.3V is inside the stated operating supply range** — the electrical table's VCC row gives 3.0V min to 6.5V max [p.3/6], so 3.3V clears the minimum with only 0.3V of margin. This is a genuine question worth having asked: many Hall-effect ICs in this class (e.g., some Allegro/Melexis linear Hall parts) are 5V-only or 4.5V-min parts. GH39F is not one of them — 3.3V is explicitly inside spec.

**However, every characteristic number in the datasheet (null voltage, sensitivity, output swing limits) is measured at VCC = 5V, not 3.3V, and the datasheet gives no separate 3.3V table, no ratiometricity percentage, and no "sensitivity vs. VCC" table.** The only evidence that behavior scales with supply is the qualitative "静态输出电压随电源电压的变化" (quiescent output voltage vs. supply voltage) graph on p.3/6, which shows Vout rising roughly linearly with VCC from ~2.5V up through 8V — consistent with, but not a numeric proof of, ratiometric operation.

Cross-check against SS49E (Honeywell, comparable part, **not** GH39F): SS49E's own description states "The linear sourcing output voltage **is set by the supply voltage** and varies in proportion to the strength of the magnetic field" [SS49E, p.2, product description] — again, no page in the SS49E document uses the literal word "ratiometric" (checked by text search), but the "Sensitivity per Volt vs. Vsupply (mV/Gauss/V)" graph [SS49E, p.4] shows sensitivity/V roughly flat across the 2.7-6.5V range, with a min-max spread of about 0.15-0.40 mV/Gauss/V around a ~0.25-0.30 nominal — i.e. Honeywell characterizes it as **approximately** ratiometric, with real part-to-part spread, not as a tightly guaranteed ratio.

**Conclusion**: 3.3V operation is in spec for GH39F. Treat GH39F's null/sensitivity/swing numbers as **5V-characterized figures that must be assumed (not proven) to scale with VCC** for a 3.3V design. If ADC-accuracy budget matters, this assumption should be bench-verified against real parts at 3.3V — the datasheet gives no basis to certify it. Because this assumption is load-bearing for the whole analog chain, all 3.3V-scaled numbers below are explicitly marked "(ratiometric assumption, not GH39F-specified)".

**Consequence for supply noise rejection**: *if* ratiometric behavior holds, noise on the 3V3 rail partially cancels in the ADC reading, because both the sensor's transfer function and the ADC's own reference (RP2350's ADC_AVDD is nominally 3.3V — RP2350 datasheet §6.1.5, p.442) move together. *If it doesn't hold* (unverified for GH39F), 3V3 rail noise shows up directly in the reading with no cancellation, which is a much stiffer requirement on the LDO/decoupling for this "clean, low-noise" rail. This is exactly the case the project brief calls out as mattering "enormously," and the datasheet does not resolve it either way.

---

## Driving a mux + ADC: output impedance and settling

**GH39F gives no output impedance, no source-current spec, no sink-current spec.** The only current-related number anywhere near the output is the **65 µA (typ.)** bias current shown in the block diagram [p.4/6] — this is a figure annotation, not a row in the electrical characteristics table, so it is not a guaranteed spec.

Because the output stage is described as an emitter follower [p.2/6 text] biased by that same 65 µA current source to GND [block diagram], the drive capability is structurally asymmetric:
- **Sourcing** (output voltage rising, e.g. charging the mux/ADC input capacitance): the output transistor actively drives current, limited only by the abs-max IOUT = 10 mA rating [p.2/6]. This direction is comparatively fast.
- **Sinking** (output voltage falling, e.g. discharging that same capacitance): an NPN emitter-follower can only pull current away from a load via its own bias current source — here the 65 µA (typ.) tail current shown in the diagram. **If that figure is representative of real sink capability, it is a genuinely weak pull-down** — two orders of magnitude below the 10 mA source rating. This is architecturally the same as SS49E, whose datasheet explicitly calls its output type "linear, sourcing" [SS49E, Table 1] and shows the identical 65 µA tail-current block diagram [SS49E, Fig.1] — reinforcing that this asymmetry is a real characteristic of this device class, not a translation artifact, even though GH39F never states a guaranteed sink current itself.
- Rough order-of-magnitude small-signal output impedance, derived (not measured, not spec'd) from the 65 µA figure via the standard bipolar emitter-follower relation r_e ≈ V_T/I_E ≈ 26 mV / 65 µA ≈ **400 Ω**. This is presented explicitly as a physics estimate chained off a non-guaranteed figure-caption number, not a datasheet output-impedance spec — flagged here so it is never mistaken for one later.

**Mux + ADC side of the interface (this part *is* well characterized, from the mux and MCU datasheets):**
- 74HC4067 mux, Table 6 [Nexperia datasheet]: **Ron is characterized at VCC = 4.5V and 6.0V, not at 3.3V.** At 4.5V: RON(peak) typ 110-180Ω (max up to 270Ω across speed grades), RON(rail) typ 90-160Ω (max up to 240Ω). At VCC ≈ 2.0V the datasheet explicitly warns Ron "becomes extremely non-linear" and recommends the part for digital signals only at that voltage [Note 1, Table 6] — 3.3V sits between the characterized 2.0V warning and the 4.5V table, so **exact Ron at 3.3V is not given** and should be measured or requested, not assumed from interpolation.
- 74HC4067 capacitances [electrical characteristics tables]: per-channel input capacitance Ci = 3.5 pF typ; switch capacitance Csw = 5 pF typ at an individual Y pin, but **45 pF typ at the common Z pin** (the pin that feeds the ADC) — this is the dominant capacitance in the settling calculation, not the per-channel figure.
- 74HC4067 propagation delay Yn→Z at VCC=4.5V: 9 ns typ / 15 ns max (up to 22 ns at 125°C) — negligible next to the RC settling time below.
- RP2350B ADC [RP2350 datasheet §12.4, p.1069-1070]: 12-bit SAR, 500 kS/s max, 96 clk_adc cycles per conversion at 48 MHz = **2 µs/conversion**. Sampling places "about 1 pF" across the ADC input; "the effective impedance, even when sampling at 500 kS/s, is over 100 kΩ... DC measurements have no need to buffer" [same section]. ADC_AVDD is nominally 3.3V [§6.1.5, p.442].

**Worked settling number for the mux/ADC side alone** (Ron 150Ω, a mid-of-typical-range placeholder since 3.3V isn't characterized, × C_total = Csw,Z 45pF + C_adc 1pF = 46pF):
τ = 150Ω × 46pF = **6.9 ns**. Settling to 1 LSB of 12 bits requires n = ln(4096) = 8.32 time constants → **t ≈ 57 ns**.

This is the key structural finding of this section: **the mux/ADC side of the signal path settles in tens of nanoseconds — three to four orders of magnitude faster than the scan budget allows for (tens of microseconds per channel, see next section) — so it is not the bottleneck.** The only unresolved settling question is the sensor's own behavior, covered next.

---

## Bank power-gating viability (with numbers)

**The datasheet gives zero data on power-on settling time**, for either part. This is the single most important gap found in this research, because it's the one figure the project brief specifically asked to be verified before committing to gating.

- GH39F: no "start-up time," "power-on time," "turn-on time," or equivalent term appears anywhere in the 6-page document (checked the full extracted text).
- SS49E: Table 1 lists a **"Response time" = 3 µs typical** [SS49E, Table 1] — but this is response to a *field step while the device is already powered and settled*, not a power-on transient from Vcc = 0. Real linear Hall ICs' power-on transients are typically dominated by internal bandgap/bias-network start-up, which is a different (and often slower) mechanism than field-step response — so this 3 µs figure is not a safe stand-in for power-on settling time, and it is SS49E's number, not GH39F's, regardless.

**Scan timing budget, computed from figures that are documented (RP2350 + the 1 kHz/30-key constraint):**
- 30 ADC conversions × 2 µs (RP2350, §12.4.3) = 60 µs of the 1000 µs (1 kHz) budget used just for conversions → **940 µs of margin remains** in the naive case of a single always-on scan pass.
- If sensors are gated in **N banks**, scanned sequentially, budget per bank = 1000/N µs, of which (30/N)×2µs goes to ADC conversions, leaving the rest for bank power-up + settling:

| Banks (N) | Keys/bank | Slot | ADC time/bank | Settling budget/bank |
|---|---|---|---|---|
| 30 (per-key gating) | 1 | 33.3 µs | 2.0 µs | **31.3 µs** |
| 10 | 3 | 100.0 µs | 6.0 µs | 94.0 µs |
| 6 | 5 | 166.7 µs | 10.0 µs | 156.7 µs |
| 5 | 6 | 200.0 µs | 12.0 µs | 188.0 µs |
| 4 | 7.5 | 250.0 µs | 15.0 µs | 235.0 µs |
| 3 | 10 | 333.3 µs | 20.0 µs | 313.3 µs |
| 2 | 15 | 500.0 µs | 30.0 µs | 470.0 µs |

**Verdict**: this cannot be certified from the datasheet, because the one number that decides it — power-on settling time — is not given for either part. What the numbers above do establish:
- **Mux/ADC-side settling is a non-issue at any bank count** (57 ns computed above, vs. tens-to-hundreds of µs of available budget) — if bank gating fails, it will be because of the sensor, not the mux or ADC.
- **Coarse gating (2-6 banks) has 150-470 µs of settling headroom per bank.** Linear Hall ICs of this simple, non-chopper-stabilized class (3-stage: Hall plate → amplifier → emitter follower, per GH39F's own block diagram) typically settle from power-on in the single-to-low-double-digit microseconds, occasionally into the tens of µs if there's meaningful internal RC filtering — plausibly comfortable inside this margin, but this is a general-class expectation, not a GH39F-verified number.
- **Fine-grained per-key gating (30 banks) has only ~31 µs of settling budget per key.** This is tight enough that it is a real risk, not just a formality — if actual power-on settling turns out to be in the tens-of-µs-to-low-hundreds-of-µs range (also plausible for this device class, especially once external VDD decoupling-cap recharge is added — see below), per-key gating would blow the 1 kHz/30-key budget.
- The **external decoupling capacitor's own RC recharge time is separately bounded and is fast**: for a typical 100 nF bypass cap recharged through a low-Ron gating switch (say ≤10Ω, generic estimate — no specific switch part was in scope for this research), τ ≈ 10Ω × 100nF = 1 µs, settling (8.32τ) ≈ 8.3 µs. This is small next to even the tightest (31 µs) per-key budget, so **the decoupling cap itself is not expected to be the limiting factor — the sensor's internal bias/bandgap start-up is the unresolved unknown**, and that number is not published.

**Recommendation given the gap**: default to coarse bank gating (2-6 banks) rather than per-key gating, since it is robust to a wide range of plausible-but-unverified power-on times, and bench-measure actual GH39F power-on settling (scope the output on a freshly-gated part, field held constant) before committing to fine-grained gating. Do not treat "bank gating works" as proven by this datasheet — it's a scan-budget argument that coarse gating has generous headroom, not a confirmation of the missing spec.

---

## Design equations

1. **RC settling to n-bit resolution**: for a single-pole RC into a converter needing settlement to 1 LSB of an N-bit range, ε = 1/2^N, and the required number of time constants is n = ln(1/ε) = N·ln(2). For 12-bit: n = 12·ln(2) = 8.32. Settling time t = n·τ = n·R·C. (Standard RC theory — general engineering knowledge, not sourced from a device datasheet.)
2. **On-axis field of a short cylindrical magnet** (used only for the physics estimate in the next section, standard magnetostatics, not a datasheet formula):
   B(z) = (Br/2)·[ (z+D)/√((z+D)²+R²) − z/√(z²+R²) ]
   where z = air gap from magnet face to sensor, D = magnet thickness, R = magnet radius, Br = remanence.
3. **Ratiometric scaling** (assumption flagged throughout, not proven for GH39F): X(Vcc) ≈ X(5V) × (Vcc/5V) for null voltage, swing limits, and sensitivity.
4. **ADC LSB size**: LSB = V_FS / 2^N. For RP2350B, 3.3V/4096 = **0.8057 mV/LSB**.
5. **E-series component derivation used below**: ideal value → nearest E24 (resistors) or nearest available standard capacitance → actual value → resulting % error, per the project's stated convention.

---

## Worked values for this application

### 1. Magnetic field over 2mm of travel (physics estimate, NOT a datasheet value)

Using equation 2 above with Br = 1.43 T (typical N52 remanence — a generic magnet-grade constant, not sourced from any datasheet in this repo, since no magnet datasheet is in scope), D = 1 mm, R = 2 mm (4×1mm disc), on-axis, no keeper/back-iron:

| Gap z | B (computed) |
|---|---|
| 0.2 mm | 2967 G |
| 0.5 mm | 2556 G |
| 1.0 mm | 1858 G |
| 1.5 mm | 1293 G |
| 2.0 mm | 893 G |
| 2.5 mm | 625 G |
| 3.0 mm | 446 G |
| 3.5 mm | 326 G |
| 4.0 mm | 244 G |

**Important consequence**: GH39F's guaranteed linear magnetic range is only ±650 Gs (min) to ±1000 Gs typical [p.3/6 table]. Per this on-axis model, that corresponds to a gap of roughly **1.4-1.7 mm** at the near end of travel — meaning if the sensor sits within about 1.5 mm of the magnet at any point in the key's 2mm stroke, **the sensor is in saturation for that portion of travel**, producing a flat, non-informative output (bad for both rapid-trigger and calibration). This is a real geometry constraint the mechanical design needs to satisfy, not just an electrical one. Two caveats on this estimate, stated explicitly because it's physics-derived, not measured: (a) it assumes pure on-axis (face-on) approach — if the actual switch geometry is a side-swipe/off-axis approach (plausible given the brief's "approaching from one side" wording, which is also consistent with a lateral/shutter geometry, not just a face-on one), the field profile is materially different and this table doesn't directly apply; (b) it ignores any keeper, back-iron, or neighboring-key crosstalk, none of which are in scope here.

Illustrative example used below: assume the key travel places the sensor between a 1.5 mm gap (near end, B ≈ 1293 G — already just past typical saturation) and a 3.5 mm gap (far end, B ≈ 326 G) — chosen purely to have concrete numbers to carry through the next calculation; not a claim about the actual mechanical design, which was not read as part of this blind research.

### 2. Output voltage swing over that window

At VCC = 3.3V, ratiometric-scaled sensitivity (assumption, see "Does it work at 3.3V?"): typ 1.8 mV/Gs × 0.66 = **1.188 mV/Gs** (min 0.957, max 1.320 mV/Gs).

ΔB across the illustrative 1.5→3.5mm window = 1293 − 326 = 967 G.
ΔVout (typ) = 1.188 mV/Gs × 967 G ≈ **1.15 V** of swing out of the 3.3V rail.

Guaranteed usable output window at 3.3V (scaling the datasheet's VH/VL swing-limit rows by 3.3/5, same assumption): VH_max ≈ 0.693V, VL_min ≈ 2.607V, span ≈ **1.91V**, i.e. about **58% of the 3.3V ADC full-scale range** is usable in the guaranteed worst case — corresponding to roughly 2376 ADC codes, i.e. ~11.2 effective bits out of the nominal 12.

### 3. Effective resolution per micron of travel

LSB (RP2350B, 12-bit, 3.3V FS) = 0.8057 mV.
Using the 1.15V swing over 2mm (2000 µm) of travel: 1.15V / 2000 µm ≈ 0.575 mV/µm.
Resolution ≈ 0.8057 mV ÷ 0.575 mV/µm ≈ **1.4 µm per ADC code**, i.e. roughly one distinguishable step per 1.4 µm of key travel over the illustrative window — good resolution *if* travel stays in the sensor's linear region. Near either end of travel where the field approaches saturation (per the table above), the local mV/µm slope drops toward zero and effective resolution degrades sharply — this is the practical argument for choosing gap geometry that keeps the *entire* 2mm stroke within the ±650-1000 Gs linear window, not just the midpoint.

### 4. Supply current, 30 sensors

Using GH39F's own ICC max = 9.0 mA [p.3/6 table, characterized at VCC=5V — no separate 3.3V figure exists; cross-checking against SS49E's "Supply Current vs Temperature" graph [SS49E, Fig.3], which shows the Vcc=3.0V max curve running *below* the Vcc=6.5V max curve, i.e. lower supply tends toward lower or equal current for this device class — so 9.0mA is treated here as a conservative (not necessarily tight) worst case at 3.3V too]:

| Config | Current |
|---|---|
| All 30 always on | **270 mA** |
| Bank of 15 | 135 mA |
| Bank of 10 | 90 mA |
| Bank of 6 | 54 mA |
| Bank of 5 | 45 mA |
| Bank of 4 | 36 mA |
| Bank of 2 | 18 mA |
| Single sensor | 9 mA |

270 mA continuous on a "clean, low-noise" 3V3 rail that also feeds the RP2350B and the mux is a meaningful design constraint on the LDO's thermal budget and output noise, independent of the gating question.

### 5. Recommended series R + filter C for each sensor's mux input line

Not a datasheet-derived value — a recommendation, since GH39F specifies no output impedance and no ESD rating, and the mux input has no series protection of its own.

- Target: a gentle low-pass with corner well above any real key-travel signal content (key presses are tens-of-ms events, i.e. sub-kHz) but well below RF/EMI pickup, while settling comfortably inside even the tightest (31.3 µs, per-key gating) budget computed above.
- Ideal R chosen as a round protection/current-limit value: **R = 1.0 kΩ** (exact E24 value, no rounding error).
- Target fc = 100 kHz → ideal C = 1/(2π·1kΩ·100kHz) = 1591.5 pF.
- Nearest E24 value: **1.6 nF** (0402). |1591.5 − 1600| = 8.5 pF vs. |1591.5 − 1500| = 91.5 pF, so 1.6nF is the nearer E24 step.
- **Actual fc = 1/(2π × 1kΩ × 1.6nF) = 99.5 kHz, error = −0.53%** vs. the 100kHz target.
- τ = 1kΩ × 1.6nF = 1.6 µs; settling to 12-bit (8.32τ) ≈ **13.3 µs** — comfortably inside the 31.3 µs per-key-gating budget and trivially inside coarser-bank budgets.
- Plus a **100 nF, 0402** VDD decoupling capacitor per sensor (standard bypass practice, not a derived value).

This is offered as a starting point for the schematic, not a verified-against-the-actual-design recommendation, consistent with the blind-read scope of this document.

---

## Recommended implementation (pin by pin, plus per-sensor passives)

SOT23-3L package (GH39FKSW), pinout per datasheet's mapping table [p.2/6]:

| Pin | Name | Function | Recommended treatment |
|---|---|---|---|
| 1 | VDD | Supply | 3V3 rail (per-tile gating switch if bank-gated), local 100nF 0402 bypass cap right at the pin |
| 2 | VOUT | Analog output | Series 1.0kΩ 0402 into a 1.6nF 0402 low-pass to the mux Y-input (see derivation above); keep this trace short and away from switching nodes (gated-5V, BS+ regulators) given the part has no stated PSRR/noise spec |
| 3 | GND | Ground | Direct to local ground plane/pour, short return path |

Per-sensor passive count: 1× 100nF (bypass) + 1× 1.0kΩ (series/filter) + 1× 1.6nF (filter), all 0402, ×30 per tile if this filter recommendation is adopted.

If bank power-gating is implemented, the gating element (load switch or small PFET) belongs between the bank's shared 3V3 feed and each sensor's VDD pin; per the settling analysis above, favor 2-6 banks over 30 individually-gated sensors unless bench data justifies finer granularity.

---

## Layout notes

- Route VOUT away from the gated-5V and BS+/bootstrap rails and their switching nodes — the datasheet gives no PSRR or noise figure, so there is no basis to claim the part rejects rail-coupled or radiated switching noise; treat the analog output trace as fully exposed to whatever it's routed near.
- Keep the VOUT trace short between the sensor and the mux input — the recommended 1kΩ series resistor combined with any extra parasitic trace capacitance beyond the ~10pF assumed above will push the RC pole down further; at 1kΩ, even 10pF of added stray capacitance only costs ~63ns of τ, so this is forgiving, but very long runs (multi-cm, high-stray-C) should be re-checked against the per-key 31.3µs budget if fine-grained gating is ever used.
- Sensor placement relative to the magnet is the dominant lever on signal quality here, more than anything electrical — per the "worked values" section, keeping the full 2mm stroke inside the ±650-1000 Gs linear window is what determines whether the ADC sees a usable, monotonic signal across the whole key travel or saturates (flat, useless output) near one end.
- No thermal/power-dissipation footprint concern at the sensor itself: ICC × VCC ≈ 9mA × 3.3V ≈ 30mW per sensor, trivial for an SOT23-3L.

---

## Gotchas and failure modes

- **No reverse-voltage rating on GH39F.** Whatever gates VDD to this part (if bank-gating is implemented) must not be capable of driving VDD negative relative to GND, since there is nothing in the datasheet to say what happens if it does. (SS49E is explicitly rated to -5V here; GH39F says nothing, so don't assume the same tolerance.)
- **No ESD rating on either part.** The SOT23-3L VOUT pin, feeding out to the mux, is a genuine ESD exposure point with no stated protection on the sensor side and no series/clamp protection at the mux input either (74HC4067 has standard CMOS input diodes only, not a dedicated ESD spec in the excerpted table). If ESD hardening is wanted, `TPD2E2U06-esd.pdf` (already in this project's reference set) is electrically compatible: VRWM = 5.5V, DC breakdown min 6.5V, clamps to 9.7V @1A / 12.4V @5A [TPD2E2U06 datasheet, §7.3.3/7.3.5] — comfortably above the ≤3.3V signal swing here. This is offered as a candidate part, not a verified recommendation against the existing schematic.
- **Weak/undocumented output sink capability.** The emitter-follower topology (see "Driving a mux + ADC") means falling-edge response is plausibly much slower than rising-edge response, and the only current figure available (65 µA typical bias) is a block-diagram annotation, not a guaranteed spec. If bench testing shows asymmetric rise/fall behavior at the ADC, this architecture is the likely reason.
- **5V-characterized table applied to a 3.3V design.** Every number in the electrical characteristics table assumes VCC=5V; using them at 3.3V requires the ratiometric assumption flagged throughout this document. This assumption is unverified for GH39F specifically.
- **Saturation risk over the mechanical travel.** Per the physics estimate above, a 4×1mm N52 magnet gets a linear-region-compatible field only in roughly the 1.5-4mm gap range (on-axis); closer gaps saturate the sensor. This is a mechanical/geometry risk, not just an electrical one, and needs to be checked against the actual switch design (out of scope for this blind read).
- **GH39F's per-unit tolerance band is wide relative to null.** Null voltage min/max is 2.25-2.75V (±0.25V, ±10% of the 2.50V typ) and sensitivity min/max is 1.45-2.0 mV/Gs (roughly -19%/+11% of the 1.8 mV/Gs typ) [p.3/6 table] — this is exactly why the project's per-key min/max calibration approach is necessary rather than optional; a fixed global scale/offset would not work given this spread.
- **Datasheet is thin and the manufacturer is a small/regional supplier (GOCHIP, Shanghai).** No response time, no drift coefficients, no output current, no ESD rating, no power-on time. Where this document cross-checks against SS49E, treat every borrowed number as an estimate of device-class behavior, not a GH39F guarantee — SS49E is a Honeywell part with a materially more rigorous datasheet, and nothing here proves GH39F meets the same bar.

---

## Open questions / not determinable from the datasheet

1. **Power-on / start-up settling time** — not given for GH39F or SS49E (SS49E's "response time" is a powered-state field-step figure, not a power-on transient). This is the load-bearing unknown for the bank-gating decision; recommend direct bench measurement.
2. **What "K" denotes in "GH39FKSW"** — not explained in the datasheet or in the LCSC listing checked.
3. **Ratiometricity, quantified** — no % or ppm/V figure for GH39F; only a qualitative VCC-sweep graph. SS49E's own ratiometricity graph shows real part-to-part spread rather than a tight guarantee, and that's a different (though architecturally similar) part.
4. **Output source/sink current spec** — no table row in GH39F; abs-max IOUT=10mA is a damage limit, not a guaranteed drive current. SS49E does give one (1.0-1.5mA typ/min/max, Vs>3.0V) but that's Honeywell's part, not GOCHIP's.
5. **Output impedance** — no spec; the ~400Ω figure in this document is a derived estimate chained off a non-guaranteed 65µA block-diagram annotation, explicitly not a datasheet number.
6. **Noise (voltage/current spectral density)** — absent from both datasheets.
7. **Numeric temperature drift coefficients for GH39F** — only qualitative graphs exist; SS49E's explicit %/°C figures (null drift ±0.10%/°C; sensitivity drift -0.15 to +0.05%/°C above 25°C, -0.04 to +0.185%/°C below) are Honeywell-specific and not confirmed to apply to GH39F.
8. **74HC4067 Ron at 3.3V specifically** — datasheet only characterizes 4.5V, 6.0V, 9.0V, and separately warns 2.0V is unsuitable for analog use; 3.3V falls in an uncharacterized gap.
9. **Actual magnet approach geometry (on-axis vs. off-axis/side-swipe)** — not knowable from the sensor datasheet; the field-vs-gap table in "Worked values" assumes on-axis approach and should be revisited once the real mechanical geometry is confirmed.
