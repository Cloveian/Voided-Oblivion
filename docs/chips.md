# Chip List

Tracking the "smartish" components - ICs and active parts only, no passives. Grouped by function. Where a part is still TBD, the current frontrunner or the shortlist is listed.

---

## MCU

| Part | Function | Notes |
| --- | --- | --- |
| **RP2350B** (QFN-80) | Main MCU, 1× per tile | 48 GPIO, 12 PIO SMs, 2× HW UART, 2× SPI, USB FS, TrustZone |
| **W25Q128JVS** | Steno dictionary storage | 16MB QSPI NOR flash, external, paired with RP2350B |

---

## Power

| Part                       | Function                                            | Notes                                                                                                                                                                                           |
| -------------------------- | --------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **FUSB302BMPX** | USB-PD PHY, **2× per tile** (one per USB-C port) | I²C, MCU-controlled negotiation. Two on **separate I²C buses** (PD1→I2C0 GPIO20/21, PD2→I2C1 GPIO30/31) so both stay the plain BMPX variant — no address-variant needed. CC wired **direct** to each port, so the cold-start Rd sits passively at the connector. VDD→3V3 + decoupling, VCONN NC (sink), VBUS pin senses its own port (pre-SS54) |
| **TPS54302**               | Buck converter (×2 per tile)                        | One clean buck (HV→5V, always-on), one big buck (HV→5V, gated for RGB/submodules). 4.5–28V in, 3A. Same part for both, single BOM line                                                          |
| **XC6220B331MR** | 3.3V LDO (clean rail), 1× per tile | 1A, low-noise, SOT-25 (5-pin, CE tied to VIN for always-on). **VIN = BS+** (not the clean-buck output) so 3V3 exists pre-PD — otherwise the MCU can't boot to negotiate PD (cold-start deadlock). Feeds MCU + hall sensors + MUX |
| **LM66100DCKT** (C2832141) | Ideal diode, **2× per tile** (U9 bootstrap OR-ing, U15 submodule +5VP branch) | SC-70-6, 1.5A, **110mΩ max**, **IQ 150nA**, $0.17. Blocks BS+ backfeeding through the *disabled* clean buck into PD+ (via L2 → SW → the TPS54302 high-side body diode) — that path would put ~4.3V on PD+ pre-negotiation. **CE → VOUT** for always-on reverse-current blocking (§8.3.2) — CE to **GND** silently turns it into a plain switch with no blocking. ST (open-drain) → 100k to **+3V3, not VOUT** (RP2350 abs max 3.6V) → `BS+ SRC`. Replaces **MAX40203** (C5668579): 879 stock single-listing, $0.77, WLP-4 0.35mm chip-scale, and ~260mΩ despite the "low drop" billing. **Accepted risk:** BS+ reaches the 5.95V UTP against a 6.0V abs max — structurally unfixable, see [power](schematic-design/power.md#accepted-risk-595v-on-a-60v-part) **U15** is the second instance: it blocks BS+ from backfeeding through the *disabled big buck* into PD+ (same path, one buck over), and needs no GPIO because +5VP is genuinely at 0V pre-PD rather than merely lower |
| **LM2903** (dual comparator) | VBUS→BS+/PD+ handoff + clean-buck enable, 1× per tile | Powered from **VBUS** (alive pre-PD). U11A: VBUS-divider vs 1.24V → drives Q2 (VBUS→PD+) + Q3 (turns Q1 off) above the trip. U11B (inputs swapped): enables the clean buck at the same trip. **LTP 5.640V / UTP 5.772V** (VDIV **35.7k/10k** ±0.1%), 132mV hysteresis (**R22 5.1k** series + R46 1M feedback on U11A). ~~44.2k/12.2k~~ — **12.2kΩ is not an E-series value and does not exist**; the re-derive also moved the margin onto the 6.0V side, where exceeding the limit damages the ideal diode rather than degrading gracefully. Replaces the earlier TLV1805 plan (36V-rated + on LCSC). No firmware |
| **TLV431** | 1.24V shunt reference for the comparator, 1× per tile | Biased from **VBUS** through 20k (NOT 3V3 — 3V3 is dead at cold start → latch). Ref strapped to cathode (R27 0Ω), 1nF on the output, DNP footprint for a future divider |
| **AO4407A** | Q2: VBUS→PD+ switch, 1× per tile | SO-8 P-FET, 30V / ~12A / ~10mΩ. On above the trip — this is the VBUS→PD+ injection path, carries the **full port current** (5A). RC gate soft-start (C44 1nF); **10V zener (BZX84C10) gate clamp mandatory** on the 20V rail |
| **AO3401** | Q1: VBUS→BS+ bootstrap switch, 1× per tile | SOT-23 P-FET, 30V. Default **ON** (feeds BS+ pre-PD), off above the trip. Gate: 1M pulldown (R35, so it fully turns off) + Q3 pull-up + 1nF soft-start (C45). ~1.5A. Same family as the AO3401A HV switches |
| **BC857** | Q3: PNP, Q1 gate driver, 1× per tile | Pulls Q1's gate up to VBUS to turn it off above the trip. 100k base-emitter resistor (R47) for a deterministic off + leakage path |
| **BZX84C10** | Gate clamps, **2× per tile** | 10V zener, gate→source. D4 on Q2 (1×) + Q1 single-fault (1×). ~~4× on the per-side switches~~ **cut** — AO4407A is ±25V and at the 9V PD default Vgs is only −8.6V (35% of rating), so they would guard the flagged 20V mode alone for ~32mm² of scarce board |
| **AO4407A** (C2841482) | **Q4–Q7: HV per-side switches, 4× per tile** | SOP-8 P-FET, 30V, 9.5mΩ@10V. **Same LCSC part as Q2, so no extra BOM line or setup fee.** Designed for **≥2A continuous** per side against the connector's 4A ceiling; Tj ≈ 28°C at 2A. Replaces the earlier AO3401A ×4 — SOT-23 could not survive what the connector can deliver. Gate: **R_pu 100k / R_soft 4.7k / C_soft 100nF** → Vgs = −0.955×PD+, ~1ms ramp, ~0.5A inrush. (The research's 39k/470k is **backwards** — it forms a divider giving Vgs = −0.69V at 9V, i.e. the switch never turns on.) ±25V Vgs, so unlike AO3401A it does **not** depend on a zener to survive the 20V rail — the 4 clamps are cut. No current sensing |
| **BC847B** (C20069135) | Gate drive level-shift for HV switches, 4× per tile | Generic NPN SOT-23, **Basic**. MCU GPIO0–3 → **Rb 10k** → base → pulls the AO4407A gate toward GND through R_soft. **Rbe 100k** base→GND for a deterministic off (ICBO ≤0.1µA × 100k = 10mV, far below Vbe). hFE min 110 → 28mA capability vs 4.3mA peak needed. (Was "BC847/MMBT2222 TBD" — pinned to BC847B) |
| ~~current-sense amp~~ | **CUT — 0× per tile** | Per-edge current sensing is gone entirely, not DNP: a DNP footprint costs the same area as a populated one and area is the binding constraint. **Frees GPIO42–45, ADC budget 6/8 → 2/8.** Firmware owns overcurrent by limiting topology before enabling a path. Note `INA180` is a **trap** — cheapest and best-stocked in the class, but SOT-23-5 has no REF pin, so it is unidirectional and cannot read the inbound body-diode current. Full re-decision in [design-choices/power](design-choices/power.md#re-decision-does-this-need-per-edge-ocp-at-all) |
| **AP2171WG-7** (C110466) | Submodule power switches, **2× per tile** (U12, U16) | SOT-25-5, 2.7–5.5V, **1A**, 95mΩ, $0.21, 35,414 stock, **OCP + OTP**. Symbol `Power_Management:AP2171W`, pinout `1=OUT 2=GND 3=/FLG 4=EN 5=IN`. **U12** gates the BS+ branch (`SM BS EN`, interlocked on `BS+ SRC`); **U16** is the group on/off + fault containment (`SM EN`), and its **/FLG is read** (`SM FLT`) — U12's isn't, since the two are in series at the same 1A and see the identical fault. **Both enables need 4.7kΩ pull-downs**, not 100k — RP2350-E9 parks a floating pad at 2.2V, above the EN threshold. **Unverified: whether OCP latches or auto-retries** (Diodes bot-blocks the datasheet) — if it latches, U16's EN is the only fault reset. Chosen over SY6288CAAC because the symbol exists and SY6288's pinout could not be verified. [working](design-choices/submodules.md#corner-power-dual-sourced-so-submodules-work-without-pd) |
| **SS54** (C7420369, R+O)   | Backfeed protection on each VBUS→HV path            | 40V/5A, SMA. Firmware caps draw at 80% of negotiated PD capacity, so worst case is 4A (80W @ 20V) - 80% of the 5A rating, correct derating. C7420369 chosen over C22452 for 50uA vs 1mA leakage |

---

## Key sensing

| Part         | Function                                  | Notes                                                                                                                                              |
| ------------ | ----------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| **GH39F**    | Hall effect sensor, 1× per key (~30/tile) | Analog ratiometric, SOT-23. Used in Void switch reference design. Footprint is generic 3-pin SOT-23 so any pin-compatible analog hall is a drop-in |
| **74HC4067** | 16:1 analog MUX, 2× per tile              | 32 channels on 2 ADC pins + 4 shared select lines                                                                                                  |

---

## RGB

| Part            | Function              | Notes                                                                  |
| --------------- | --------------------- | ---------------------------------------------------------------------- |
| **SK9822-EC20** | Per-key RGB, ~30/tile | SK9822 uses hardware SPI (0 PIO SMs) + has hardware global brightness. |
| **SN74LVC2T45DCUR** (C15741) | 3V3→5V level shift on SPI0 (SCK+DI), 1× per tile | VSSOP-8, ~$0.16. **Mandatory, not optional** - SK9822-EC20 VIH min is **3.4V** and the 3V3 rail tops out at 3.366V, so direct drive is out of spec at every condition. Dual-supply: **VCCA=3V3, VCCB=gated-5V**, DIR tied high (A→B). Chosen over 74AHCT125/1G125 for **Ioff partial-power-down** - the LEDs sit on the gated buck, so the 5V side is dead while the MCU is live, and Ioff stops the MCU back-feeding that rail through the buffer's clamp diodes. Note **74LVC1G125 does NOT work** (VIH = 0.7×VCC = 3.5V at 5V); AHCT/HCT are the flat-2.0V-VIH families. Fallback: 2× SN74LVC1T45 (C7843). Full working in [rgb calcs](schematic-design/rgb.md#picking-the-level-shifter) |

---

## Communications

| Part | Function | Notes |
| --- | --- | --- |
| **TS3USB30ERSWR** (C73880) | USB 2.0 D+/D− 2:1 data mux, 1× per tile | UQFN-10, ~$0.13. HS-capable (900MHz, overkill for FS) with **built-in D± ESD** (drops external ESD). **VCC on 3V3** (off BS+, immune to the handoff spike). SEL from VBUS-A detect, **clamped by a 5.1V zener (BZV55B5V1)** so the 7V S pin survives 20V. **CC is no longer muxed** — it goes direct to the 2 FUSB302s. Replaces the TMUX1574, which was dropped once CC came out of the mux (that muxing broke the cold-start Rd) |

---

## Connectors

| Part | Function | Notes |
| --- | --- | --- |
| **PG-6P-2.5-5.5H-SM-RA** (Shenzhen Yiwei) | Inter-tile edge connector, **8× per tile** (4 edges × 1 male + 1 female) | 6 positions, 2.5mm pitch, 5.5mm height, SMT right-angle pogo. **Not in the LCSC/JLC catalogue — hand-soldered, single-source, buy spares.** One male + one female per edge gives 12 contacts: `GND GND HV HV BS Tx \| Rx BS HV HV GND GND` — a palindrome about the edge midline, with **GND outboard** so the most exposed contacts are ground rather than the 20V rail. Gender rule is rotational: **clockwise around the perimeter, every edge is male-then-female** (J1/J3/J7/J5 male, J2/J4/J8/J6 female), which is what makes neighbouring edges land male-on-female. **4× HV at 1A = 4A per-side ceiling**, which is what sizes Q4–Q7. Both bodies must be placed **symmetric about the edge midline** or the mirror maps HV onto Tx. Full working in [module-connectors](design-choices/module-connectors.md#revisit-i-picked-a-real-connector-and-it-killed-the-custom-cutout-idea) |
