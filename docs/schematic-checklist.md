# Single-Tile Schematic Checklist

Everything that has to land in the KiCad schematic for **one tile**. Pulled from [chips](chips.md), [pin-budget](design-choices/pin-budget.md), [power](design-choices/power.md), [comms](design-choices/comms.md), [hall-effect-sensors](design-choices/hall-effect-sensors.md), and [module-connectors](design-choices/module-connectors.md). One tile does everything - no second MCU - so this is the whole board.

Pin numbers are the **starting assignment** from [pin-budget](design-choices/pin-budget.md#a-starting-assignment) (KiCad gets final say when routing). Budget targets: **37/48 GPIO, 6/8 ADC, 12/12 PIO SMs.**

---

## 1. MCU + boot

- [ ] **RP2350B** (QFN-80), 1×
- [ ] Decoupling: 100nF per power pin + bulk caps per datasheet
- [ ] Crystal (12MHz) + load caps, or confirm using internal - Void needs accurate USB so **crystal**
- [ ] USB DP/DM to the USB mux (see §6), with 27Ω series + ESD if not handled by mux
- [ ] BOOTSEL button (or test pad) for UF2 flashing
- [ ] RUN/reset button or pad
- [ ] SWD header (SWCLK/SWDIO/GND/3V3) - do **not** skip, you'll want it
- [ ] **W25Q128JVS** 16MB QSPI flash on the QMI bus (steno dict)
  - [ ] Resolve first: boot flash only, or this as a 2nd chip on **CS1n (GPIO19)**? Checklist assumes 2nd chip (37/48). If boot-only, drop GPIO19 → 36/48.
- [ ] FIDO2 = TrustZone, internal, **no external secure element to wire**

## 2. Power - rails & regulators

See [power](design-choices/power.md) for the full flow. Three rails: **HV** (per-side switched), **bootstrap 5V** (always-on, shared), **clean 3.3V** (LDO). GND common everywhere.

- [ ] **FUSB302BMPX** USB-PD PHY - I²C0 **SDA GPIO20 / SCL GPIO21**, **INT GPIO15**, CC1/CC2 from the active port (via CC mux, §6)
- [ ] **TPS54302** ×2 (same part, 2 BOM instances):
  - [ ] **Clean buck** (HV→5V, always-on) - input must work from ~5.5V (pre-PD) through 20V; feeds the LDO + OR's onto bootstrap
  - [ ] **Big buck** (HV→5V, gated) - enable on **GPIO14**; feeds RGB + submodules
  - [ ] Each: inductor, input/output caps, feedback divider for 5V per datasheet
- [ ] **XC6220B331MR** 3.3V LDO off clean 5V - feeds MCU + hall sensors + mux (low-noise, this is the analog rail). **5-pin SOT-25 with a CE pin - tie CE to VIN** (always-on clean rail, must never gate off)
- [ ] **MAX40203** ideal diode - clean buck 5V → shared **bootstrap** net (near-zero drop OR'ing)

## 3. Power - VBUS handoff & HV switching (hardware, no firmware)

- [ ] **TLV1805** comparator watching VBUS vs ~6V resistor divider, drives two things at once:
  - [ ] **AO3415** P-FET: VBUS→bootstrap path, normally on, comparator turns OFF above ~6V
  - [ ] N-FET/switch: VBUS→local HV rail, normally off, comparator turns ON above ~6V
- [ ] **AO3401A** ×4 - HV per-side switches (one per edge), 30V/4A P-FET, RC soft-start on gate
  - [ ] **BC847/MMBT2222** ×4 - NPN level-shift, MCU GPIO → base → pulls AO3401A gate low
  - [ ] HV enable GPIO: **GPIO0–3** (one per side)
  - [ ] HV per-side current sense → ADC **GPIO42–45** (firmware OCP; all 4 dedicated ADC, not muxed)
- [ ] **SS54** Schottky ×(per VBUS→HV path) - backfeed protection (40V/5A)
- [ ] Hold-up caps on bootstrap to cover the µs comparator→buck handoff

## 4. Key sensing

- [ ] **GH39F** hall sensor ×30 (5×6) - generic 3-pin SOT-23 footprint (Vcc/OUT/GND) so any analog hall drops in
- [ ] **74HC4067** 16:1 analog mux ×2
  - [ ] Mux outputs → ADC **GPIO40, 41**
  - [ ] Shared 4 select lines → **GPIO8–11**
  - [ ] 30 keys into 32 channels = 2 spare channels (leave unconnected/test pads)
- [ ] Consider sensor **bank-power gating** (energize only the scanned group) - note the FET/transistor if doing it; affects LDO load
- [ ] Sensors on the **clean 3.3V** rail, kept off the noisy buck

## 5. RGB

- [ ] **SK9822-EC20** ×30 (reverse-mount, lights through switch) - daisy-chained
- [ ] Hardware **SPI0**: SCK **GPIO34**, TX(MOSI) **GPIO35**
- [ ] Powered from the **big (gated) buck** 5V, NOT the clean rail
- [ ] Level-shift 3.3V→5V on SCK/data if SK9822 needs it (check VIH; add 74AHCT if marginal)
- [ ] Bulk cap near the LED chain; per-LED decoupling per density

## 6. USB-C (dual port + mux)

- [ ] 2× USB-C receptacles (one horizontal edge, one vertical edge - for 90° reach)
- [ ] **TMUX1574PWR** - muxes CC1/CC2/DP/DM between both ports, single SEL driven by VBUS-A detect
  - [ ] 100Ω series on CC lines (ESD)
  - [ ] Rd pull-downs on the RP2350B side
  - [ ] VBUS-A → SEL detect circuit (resistor/transistor)
- [ ] Selected port's CC → single FUSB302 (§2); non-selected port can't negotiate (stays 5V)
- [ ] VBUS from both ports → backfeed protection (§3)

## 7. Inter-tile edge connectors (×4 sides)

Per side carries: **HV, Bootstrap, GND, Tx, Rx**. Pinout is the palindrome with doubled power, gender-split down the middle - see [module-connectors](design-choices/module-connectors.md):

```
GND  HV  BOOT  Tx   Rx   BOOT  HV  GND
pogo pogo pogo pogo pad  pad   pad pad
```

- [ ] Two footprints: **short (5un edge)** and **long (6un edge)** - like only mates like
- [ ] HV/GND get 2 contacts each (current sharing, ~2A/contact)
- [ ] Rx line **pulldown** per side (neighbor detection - Tx drives it high if present)
- [ ] UART pin pairs (rotation pairing from [comms](design-choices/comms.md)):
  - [ ] **Top + Left** = UART0-capable: **GPIO12/13 + 16/17**
  - [ ] **Bottom + Right** = UART1-capable: **GPIO4/5 + 6/7**
- [ ] Footprint placeholder pending pogo-vs-spring-finger prototype (electrical is fixed either way)

## 8. Submodule corner connectors (×4 corners)

- [ ] 4-pin per corner: **5V, GND, Rx, Tx** (mirrored/rotatable pad layout)
- [ ] 5V from the big buck; independent UART per corner (not muxed)
- [ ] Corner Tx/Rx → **GPIO22–29** (PIO, 8 pins)
- [ ] Physical connector body TBD (header/pogo/magnetic) - footprint placeholder, signals fixed

## 9. Pin assignment cross-check (paste into schematic notes)

| Pins | Use |
| --- | --- |
| GPIO0–3 | HV per-side enable |
| GPIO4/5 + 6/7 | Inter-tile Bottom + Right (UART1) |
| GPIO8–11 | Key mux select lines |
| GPIO12/13 + 16/17 | Inter-tile Top + Left (UART0) |
| GPIO14 | Big buck enable |
| GPIO15 | FUSB302 INT |
| GPIO19 | Steno flash CS1n (if 2nd chip) |
| GPIO20/21 | FUSB302 I²C0 SDA/SCL |
| GPIO22–29 | Submodule corners (4× Tx/Rx) |
| GPIO34/35 | RGB SPI0 SCK/TX |
| GPIO40, 41 | Key mux A/B ADC outputs |
| GPIO42–45 | HV per-side current sense (ADC) |
| **Spare** | GPIO18, 30–33, 36–39, 46, 47 (11 free) |

**ADC:** 6/8 used · **GPIO:** 37/48 used · **PIO SMs:** 12/12 (RGB+UARTs on HW peripherals, 2 inter-tile sides + 8 submodule on PIO)

## 10. Before first PCB / sanity

- [ ] ERC clean
- [ ] Confirm every ADC-needed net actually lands on GPIO40–47 (hard constraint)
- [ ] Confirm both RGB SPI nets are the **same** SPI instance
- [ ] Test points: 3V3, 5V bootstrap, HV, GND, key-mux out, a couple UART lines
- [ ] Decoupling sweep - every IC has its caps
- [ ] **Blocked-on-hardware** (don't gate the schematic, just remember): case-magnet field vs hall saturation, pogo vs spring-finger, XC6206/MAX40203 downgrade triggers

---

Back to [index](index.md).
