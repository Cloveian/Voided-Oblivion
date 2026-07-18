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
| **MAX40203**               | Ideal diode (bootstrap OR'ing), 1× per tile         | 1A integrated, SOT-23-3. OR's clean buck output onto shared 5V bootstrap net                                                                                                                    |
| **LM2903** (dual comparator) | VBUS→BS+/PD+ handoff + clean-buck enable, 1× per tile | Powered from **VBUS** (alive pre-PD). U11A: VBUS-divider vs 1.24V → drives Q2 (VBUS→PD+) + Q3 (turns Q1 off) above the trip. U11B (inputs swapped): enables the clean buck at the same trip. **Trip ~5.75V** (VDIV 44.2k/12.2k), ~200mV hysteresis (10k series + 1M feedback on U11A). Replaces the earlier TLV1805 plan (36V-rated + on LCSC). No firmware |
| **TLV431** | 1.24V shunt reference for the comparator, 1× per tile | Biased from **VBUS** through 20k (NOT 3V3 — 3V3 is dead at cold start → latch). Ref strapped to cathode (R27 0Ω), 1nF on the output, DNP footprint for a future divider |
| **AO4407A** | Q2: VBUS→PD+ switch, 1× per tile | SO-8 P-FET, 30V / ~12A / ~10mΩ. On above the trip — this is the VBUS→PD+ injection path, carries the **full port current** (5A). RC gate soft-start (C44 1nF); **10V zener (BZX84C10) gate clamp mandatory** on the 20V rail |
| **AO3401** | Q1: VBUS→BS+ bootstrap switch, 1× per tile | SOT-23 P-FET, 30V. Default **ON** (feeds BS+ pre-PD), off above the trip. Gate: 1M pulldown (R35, so it fully turns off) + Q3 pull-up + 1nF soft-start (C45). ~1.5A. Same family as the AO3401A HV switches |
| **BC857** | Q3: PNP, Q1 gate driver, 1× per tile | Pulls Q1's gate up to VBUS to turn it off above the trip. 100k base-emitter resistor (R47) for a deterministic off + leakage path |
| **BZX84C10** | Q2 gate clamp, 1× per tile | 10V zener, gate→source. Holds Vgs within ±12V when Q2 switches the 20V PD+ rail |
| **AO3401A**                | HV per-side switches, 4× per tile                   | 30V/4A P-FET, SOT-23. Soft-start via RC gate, firmware OCP via ADC. Needs 1× NPN (e.g. BC847/MMBT2222) per switch to level-shift gate drive from 3.3V MCU GPIO                                  |
| **BC847 / MMBT2222** (TBD) | Gate drive level-shift for HV switches, 4× per tile | Any generic NPN SOT-23. MCU GPIO → NPN base → pulls AO3401A gate to GND to turn on                                                                                                              |
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

---

## Communications

| Part | Function | Notes |
| --- | --- | --- |
| **TS3USB30ERSWR** (C73880) | USB 2.0 D+/D− 2:1 data mux, 1× per tile | UQFN-10, ~$0.13. HS-capable (900MHz, overkill for FS) with **built-in D± ESD** (drops external ESD). **VCC on 3V3** (off BS+, immune to the handoff spike). SEL from VBUS-A detect, **clamped by a 5.1V zener (BZV55B5V1)** so the 7V S pin survives 20V. **CC is no longer muxed** — it goes direct to the 2 FUSB302s. Replaces the TMUX1574, which was dropped once CC came out of the mux (that muxing broke the cold-start Rd) |
