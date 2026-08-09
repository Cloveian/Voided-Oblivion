# Single-Tile Schematic Checklist

Everything that has to land in the KiCad schematic for **one tile**. Pulled from [chips](chips.md), [pin-budget](design-choices/pin-budget.md), [power](design-choices/power.md), [comms](design-choices/comms.md), [hall-effect-sensors](design-choices/hall-effect-sensors.md), and [module-connectors](design-choices/module-connectors.md). One tile does everything - no second MCU - so this is the whole board.

Pin numbers are the **starting assignment** from [pin-budget](design-choices/pin-budget.md#a-starting-assignment) (KiCad gets final say when routing). Budget targets: **44/48 GPIO, 6/8 ADC, 12/12 PIO SMs.**

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

- [x] **FUSB302BMPX** USB-PD PHY - I²C0 **SDA GPIO20 / SCL GPIO21**, **INT GPIO15**, CC1/CC2 from the active port (via CC mux, §6)
- [x] **TPS54302** ×2 (same part, 2 BOM instances):
  - [x] **Clean buck** (HV→5V, always-on) - input must work from ~5.5V (pre-PD) through 20V; feeds the LDO + OR's onto bootstrap
  - [x] **Big buck** (HV→5V, gated) - enable on **GPIO14**; feeds RGB + submodules
  - [x] Each: inductor, input/output caps, feedback divider for 5V per datasheet
- [x] **XC6220B331MR** 3.3V LDO off clean 5V - feeds MCU + hall sensors + mux (low-noise, this is the analog rail). **5-pin SOT-25 with a CE pin - tie CE to VIN** (always-on clean rail, must never gate off)
- [x] ~~**MAX40203**~~ → **LM66100DCKT** (C2832141) ideal diode - clean buck 5V → shared **bootstrap** net
  - [ ] **CE (3) → VOUT/BS+ via R15 0Ω** — always-on RCB. CE to GND silently disables reverse blocking
  - [ ] **C114 100nF → 1µF** on VIN, local to the part
  - [ ] **R83 100k: ST (5) → +3V3** (*not* VOUT — 5V would exceed RP2350's 3.6V pin max), ST → `BS+ SRC` GPIO
  - [ ] Pin 4 (N/C) → GND or no-connect flag
  - [ ] Symbol + footprint (SC-70-6) + Value + **LCSC** all move together — the BOM pulls Value

## 3. Power - VBUS handoff & HV switching (hardware, no firmware)

- [ ] **TLV1805** comparator watching VBUS vs ~6V resistor divider, drives two things at once:
  - [ ] **AO3415** P-FET: VBUS→bootstrap path, normally on, comparator turns OFF above ~6V
  - [ ] N-FET/switch: VBUS→local HV rail, normally off, comparator turns ON above ~6V
- [ ] **AO4407A** ×4 (Q4–Q7) - HV per-side switches (one per edge), SOP-8 P-FET, 30V/9.5mΩ, **≥2A continuous** design target against the connector's 4A ceiling. RC soft-start on gate (values below). ~~AO3401A ×4~~ - SOT-23 couldn't survive the connector's full current, [working](schematic-design/power.md#hv-per-side-switches---picking-the-fet)
  - [ ] **BC847B** (C20069135) ×4 - NPN level-shift, **Basic**. MCU GPIO0–3 → base → pulls the gate toward GND through R_soft
  - [x] ~~**BZX84C10** ×4 gate clamps~~ - **cut.** AO4407A is ±25V, and at the 9V default Vgs is only −8.6V (35% of rating). They'd protect the flagged 20V mode only, for ~32mm² of scarce board
  - [ ] Gate network per switch, [corrected values](schematic-design/power.md#gate-drive---the-researchs-values-are-backwards) - **the research's 39k/470k is backwards and won't turn on at 9V**:
    - [ ] **R_pu 100kΩ** gate→source · **R_soft 4.7kΩ** NPN collector→gate · **C_soft 100nF** gate→source
    - [ ] **Rb 10kΩ** GPIO→base · **Rbe 100kΩ** base→GND
    - [ ] → Vgs = −0.955 × PD+ (−8.6V @ 9V, −19.1V @ 20V), t_ramp ≈ 1ms, ~0.5A inrush
  - [ ] HV enable GPIO: **GPIO0–3** (one per side)
  - [x] ~~HV per-side current sense → ADC GPIO42–45~~ - **cut entirely, not even DNP footprints.** A DNP pad costs the same board area as a populated one, and area is the binding constraint. Re-decision + weighted table in [design-choices/power](design-choices/power.md#re-decision-does-this-need-per-edge-ocp-at-all)
    - **ADC budget drops 6/8 → 2/8. GPIO42–45 are free.**
    - **FIRMWARE now owns overcurrent** - limit topology *before* enabling a path, using the tile map it already builds. Prevention, not tripping
- [ ] **Wire the switch source to PD+ and the drain to the connector**, not the reverse - that orientation points every tile's body diode inward, so two neighbours with both switches open sit diode-to-diode and the edge net floats. Flipped, every tile permanently powers its neighbours. [why](schematic-design/power.md#the-body-diode---an-open-switch-only-blocks-outbound)
- [ ] **FIRMWARE: turn an edge switch OFF on neighbour loss.** An edge left enabled after a tile is yanked makes the next hotplug a hard hot-insert - the new tile's bulk charges through its own body diode with no soft-start in the path. This is what makes the Rx pull-down detection in §7 load-bearing
- [ ] **SS54** Schottky ×(per VBUS→HV path) - backfeed protection (40V/5A)
- [ ] Hold-up caps on bootstrap to cover the µs comparator→buck handoff

## 4. Key sensing

- [ ] **GH39F** hall sensor ×30 (5×6) - generic 3-pin SOT-23 footprint (Vcc/OUT/GND) so any analog hall drops in
- [ ] **74HC4067** 16:1 analog mux ×2
  - [ ] Mux outputs → ADC **GPIO40, 41**
  - [ ] Shared 4 select lines → **GPIO8–11**
  - [ ] 30 keys into 32 channels = 2 spare channels (leave unconnected/test pads)
- [x] ~~Consider sensor **bank-power gating**~~ - **decided against** ([working](schematic-design/keys.md#sensor-bank-power-gating)). Fixed the LDO instead. Do route sensor VDD as its own net with a 0Ω link to +3V3 so it can be retrofitted.
- [ ] Tie the 2 spare mux channels (AM0:15, AM1:15) to GND - currently floating
- [ ] Sensors on the **clean 3.3V** rail, kept off the noisy buck

## 5. RGB

- [ ] **SK9822-EC20** ×30 - daisy-chained
- [ ] Hardware **SPI0**: SCK **GPIO34**, TX(MOSI) **GPIO35**
- [ ] Powered from the **big (gated) buck** 5V, NOT the clean rail
- [ ] **SN74LVC2T45** level shifter 3.3V→5V on SCK/data - **required**, not conditional (SK9822-EC20 VIH min 3.4V > the 3.366V the 3V3 rail can manage). VCCA→3V3, VCCB→gated-5V, DIR high. 22–33Ω series on the 5V side. See [rgb calcs](schematic-design/rgb.md#picking-the-level-shifter)
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

Per side carries: **HV, Bootstrap, GND, Tx, Rx**. **Part picked: PG-6P-2.5-5.5H-SM-RA** (Shenzhen Yiwei), **2 per side** - one 6P male + one 6P female. Pinout is the palindrome with power ×4, gender split falling out of the two bodies - see [module-connectors](design-choices/module-connectors.md#revisit-i-picked-a-real-connector-and-it-killed-the-custom-cutout-idea):

```
GND  GND  HV   HV   BS   Tx   |   Rx   BS   HV   HV   GND  GND
<--------- 6P male --------->  |  <-------- 6P female ------->
pin:  1    2    3    4   5   6 |   1    2    3    4    5    6
```

**GND outboard** (deliberate - the most exposed contacts should be ground, not the 20V rail). Per body: male = `GND GND HV HV BS Tx`, female = `Rx BS HV HV GND GND`.

- [ ] Two footprints: **short (5un edge)** and **long (6un edge)** - like only mates like
- [x] **Gender rule: clockwise around the perimeter, every edge is male-then-female.** Top L→R, Right T→B, Bottom R→L, Left B→T. Two neighbouring tiles traverse the shared edge in *opposite* rotational senses, so male always lands on female. Drawn as J1/J3/J7/J5 male, J2/J4/J8/J6 female
- [ ] **Both bodies symmetric about the edge midline** - this is the one that silently maps HV onto Tx if you get it wrong
- [ ] HV/GND get **4 contacts each** (1A per contact → **4A per-side ceiling**, which is what sizes Q4–Q7 in §3)
- [ ] Rx line **pulldown, 4.7kΩ** per side to GND - **required by RP2350-E9**, which sources ~120µA and parks a floating input at 2.2V (phantom neighbour). 8.2k is the datasheet's boundary with only 171mV to VIL; 10k **fails**. [working](schematic-design/mcu.md#rp2350-e9-and-the-neighbour-detect-pull-downs)
- [ ] Tx series-termination footprint per side, **populate 0Ω** (pads for 22–33Ω if it rings at 4 Mbaud)
- [ ] **Inter-tile UART pins - all four sides on PIO** ([why](design-choices/comms.md#revisit-the-piosm-allocation-was-built-on-a-wrong-assumption)): the hardware UARTs moved to submodule corners, because the PL011 caps at **7.8 Mbaud** while a PIO UART does ~18.75 - the slow path was on the high-traffic links
  - [ ] **Top** GPIO12/13 · **Left** GPIO16/17 · **Bottom** GPIO4/5 · **Right** GPIO6/7 — all PIO (F6/F7/F8), uniform, **no F11 anywhere**
  - [ ] Pins no longer need to be UART-capable; left as-is to avoid churn
- [ ] ~~Footprint placeholder pending pogo-vs-spring-finger prototype~~ - **resolved**, it's an off-the-shelf pogo pair. Footprint still needs drawing from the part drawing
- [ ] **No inset sequencing is possible** with molded bodies - all 12 contacts break together, so hot-unplug safety rests on PD voltage. Default **9V** - unconditionally under gold's ~15V minimum arcing voltage. (**not 12V** - 12V isn't a required PD step, the Power Rules give 9/15/20. 15V is only arc-safe breaking ≤1 tile, since an arc needs 15V **and** 0.4A.) 20V behind an explicit firmware flag + warning

## 8. Submodule corner connectors (×4 corners)

**5-pin** (revised from 4 — [working](design-choices/submodules.md#revision-5-pins-not-4---adding-a-senseid-line)), clockwise-consistent at every corner:

```
ID   GND  5V   Rx   Tx
 1    2    3    4    5
```

- [ ] **`ID GND 5V Rx Tx`** — prepend ID, don't append. 5V must stay **interior** (a misaligned module can't land it on a signal pin); ID sits at an end next to GND, the quietest pin
- [ ] 5V from the **submodule group switch** (below); independent UART per corner, not muxed
- [ ] Corner Tx/Rx → **GPIO22–29** — **2 corners on hardware UART, 2 on PIO**:
  - [ ] **GPIO24/25 = UART1 TX/RX (F2)** and **GPIO28/29 = UART0 TX/RX (F2)** — the only two pairs in that range that are TX/RX at F2, and conveniently on *different* UARTs
  - [ ] **GPIO22/23 and GPIO26/27 on PIO** — both are UART1 CTS/RTS at F2, so they could never have paired with each other anyway
- [ ] **ID → 4× ADC-capable GPIO** (from GPIO42–47), **pull-up to +3V3** (not 5V), **series ~10kΩ** to the pin — the module is an untrusted 5V load
- [ ] **Corner power is dual-sourced** so submodules work on a 5V-only (non-PD) source - [working](design-choices/submodules.md#corner-power-dual-sourced-so-submodules-work-without-pd)
  - [ ] **U15 LM66100DCKT**: +5VP → SM_BUS, **CE→VOUT via 0Ω** (always-on reverse blocking). No GPIO — +5VP is genuinely 0V pre-PD, so there's nothing to arbitrate
  - [ ] **U12 AP2171WG-7**: BS+ → SM_BUS, EN = `SM BS EN`. **Firmware rule: enable only while `BS+ SRC` reads low** (clean buck not feeding BS+)
  - [ ] **U16 AP2171WG-7**: SM_BUS → SM+, EN = `SM EN`. This is the independent gate — U15 has no enable, so without it the only post-PD off-switch is the big buck, which kills RGB too
  - [ ] **Both AP2171W enables: 4.7kΩ pull-down to GND** — *not* 100k, *not* 0Ω. RP2350-E9 parks a floating pad at 2.2V, above the EN threshold, so a mis-configured pin can turn the rail **on**
  - [ ] **U16 /FLG → `SM FLT` GPIO** with 100k pull-up to +3V3. **U12 /FLG and U15 ST: no-connect flags, no pull-ups** — U12 is in series with U16 at the same 1A so it reports the identical fault, and U15's ST duplicates `BS+ SRC`
  - [ ] Caps: 1µF at each IN, 10µF on SM_BUS and SM+
  - [ ] **CHECK BEFORE FAB: does AP2171W's OCP latch or auto-retry?** If it latches, U16's EN is the only fault reset
- [ ] Mechanical keying (shrouded header / asymmetric mount) — pin order limits misinsertion damage, it doesn't prevent it
- [ ] **4-pin machined (Swiss) socket → now 5-pin**, socket on the tile

**Notes:** the ID divider runs off +3V3, so presence and identity work **with the corner rail switched off** — firmware can read what's plugged in before deciding to power it. A module needs **no MCU**: firmware just doesn't configure UART on Tx/Rx and uses them as GPIO.

**Not provided:** 5V-only (non-PD) operation, and submodules-alive-with-RGB-off. The switch is downstream of +5VP so it can only remove power. RGB dimming is the SK9822 global-brightness lever, not a rail gate.

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
| GPIO42–45 | **Submodule corner ID / analog** (4× ADC) |
| **Spare** | GPIO18, 30–33, 36–39, 46, 47 (11 free) |

**ADC:** 6/8 used · **GPIO:** 44/48 used · **PIO SMs:** 12/12 (RGB on HW SPI; **4 inter-tile sides on PIO = 8**; 2 submodule corners on HW UART, 2 on PIO = 4)

## 10. Before first PCB / sanity

- [ ] ERC clean
- [ ] Confirm every ADC-needed net actually lands on GPIO40–47 (hard constraint)
- [ ] Confirm both RGB SPI nets are the **same** SPI instance
- [ ] Test points: 3V3, 5V bootstrap, HV, GND, key-mux out, a couple UART lines
- [ ] Decoupling sweep - every IC has its caps
- [ ] **Blocked-on-hardware** (don't gate the schematic, just remember): case-magnet field vs hall saturation, pogo vs spring-finger, XC6206/MAX40203 downgrade triggers

---

Back to [index](index.md).
