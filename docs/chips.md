# Chip List

Tracking the "smartish" components — ICs and active parts only, no passives. Grouped by function. Where a part is still TBD, the current frontrunner or the shortlist is listed.

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
| **FUSB302BMPX**            | USB-PD PHY, 1× per tile                             | I²C, MCU-controlled negotiation, open-source RP2040 stack exists                                                                                                                                |
| **TPS54302**               | Buck converter (×2 per tile)                        | One clean buck (HV→5V, always-on), one big buck (HV→5V, gated for RGB/submodules). 4.5–28V in, 3A. Same part for both, single BOM line                                                          |
| **XC6220B332MR**           | 3.3V LDO (clean rail), 1× per tile                  | 300mA, low-noise, SOT-23-3. Feeds MCU + hall sensors + MUX                                                                                                                                      |
| **MAX40203**               | Ideal diode (bootstrap OR'ing), 1× per tile         | 1A integrated, SOT-23-3. OR's clean buck output onto shared 5V bootstrap net                                                                                                                    |
| **TLV1805**                | VBUS comparator, 1× per tile                        | Watches VBUS against ~6V resistor-divider threshold. Fires two things simultaneously: opens VBUS→bootstrap switch, connects VBUS to local HV rail. No firmware involved                         |
| **AO3415** (or equivalent) | P-FET, VBUS→bootstrap switch, 1× per tile           | Normally on (VBUS feeds bootstrap), comparator turns it off above ~6V. 20V rated — fine since it only conducts at ≤5V                                                                           |
| **AO3401A**                | HV per-side switches, 4× per tile                   | 30V/4A P-FET, SOT-23. Soft-start via RC gate, firmware OCP via ADC. Needs 1× NPN (e.g. BC847/MMBT2222) per switch to level-shift gate drive from 3.3V MCU GPIO                                  |
| **BC847 / MMBT2222** (TBD) | Gate drive level-shift for HV switches, 4× per tile | Any generic NPN SOT-23. MCU GPIO → NPN base → pulls AO3401A gate to GND to turn on                                                                                                              |
| **SS54** (C7420369, R+O)   | Backfeed protection on each VBUS→HV path            | 40V/5A, SMA. Firmware caps draw at 80% of negotiated PD capacity, so worst case is 4A (80W @ 20V) — 80% of the 5A rating, correct derating. C7420369 chosen over C22452 for 50uA vs 1mA leakage |

---

## Key sensing

| Part | Function | Notes |
| --- | --- | --- |
| **GH39F** | Hall effect sensor, 1× per key (~30/tile) | Analog ratiometric, SOT-23. Used in Void switch reference design. Footprint is generic 3-pin SOT-23 so any pin-compatible analog hall is a drop-in |
| **74HC4067** | 16:1 analog MUX, 2× per tile | 32 channels on 2 ADC pins + 4 shared select lines |

---

## RGB

| Part | Function | Notes |
| --- | --- | --- |
| **SK6812MINI-E** *or* **SK9822-EC20** | Per-key RGB, ~30/tile | **Still open** — see [rgb.md](design-choices/rgb.md). SK6812 leans lower power + 1 PIO SM; SK9822 uses hardware SPI (0 PIO SMs) + has hardware global brightness. PIO budget nudges toward SK9822 |

---

## Communications

| Part | Function | Notes |
| --- | --- | --- |
| **TMUX1574PWR** (C2673443) | USB 2.0 + CC 2-port mux, 1× per tile | 4-channel 2:1 SPDT, TSSOP-16, ~$0.30. One chip handles CC1, CC2, D+, D− switching between both ports. Single SEL pin driven by VBUS-A detection. 2Ω Ron, 2GHz BW (overkill for USB FS but fine). 100Ω series resistors on CC lines recommended for ESD. Rd pull-downs stay on RP2350B side so only the active port sees a device |
