# Schematic-design calcs

The datasheet math and component-value derivations behind the tile schematic - feedback dividers, current limits, RC time constants, cap sizing, thresholds. One page per category (mirrors the design-choices folder). This is the *why these values* layer; [schematic-checklist](../schematic-checklist.md) is the *what to wire* layer, and [chips](../chips.md) is the final BOM. When drawing pushes back on the plan (a snag that reopens a decision), that goes in [implementation](implementation.md).

Every section uses the same skeleton: **Goal → Datasheet refs → Math → Result → Notes/gotchas.** Always cite the datasheet section/page, and show the E-series rounding (ideal → nearest real 0402 → actual value + error).

## Pages
- [Power](power.md) - bucks, LDO, ideal diode, comparator, HV switches, backfeed diodes, caps
- [Comms & USB](comms.md) - USB mux, FUSB302, CC/D± passives, inter-tile & submodule lines
- [Keys & sensing](keys.md) - GH39F, 74HC4067, ADC scaling, bank-power
- [RGB](rgb.md) - SK9822-EC20 chain, SPI drive, rail caps
- [MCU & flash](mcu.md) - RP2350B decoupling, crystal, QSPI, USB, boot/SWD
- [Implementation](implementation.md) - reality vs the plan: what snagged while drawing, and re-decisions (VBUS front-end)

## Open items surfaced here
- Q2 (VBUS→PD+ switch) device type + gate drive - [power](power.md#q2q3d4---vbuspd-switch-ao4407a--bc857--bzx84c10)
- VBUS comparator reference source + hysteresis - [power](power.md#threshold-detector---lm2903-u11)
- Steno flash: 2nd chip vs boot-flash-only - [mcu](mcu.md#qspi-flash---w25q128jvs)
- ~~SK9822 3.3V→5V level-shift needed?~~ **closed** - yes, mandatory (VIH 3.4V vs 3.366V best case). Part picked: **SN74LVC2T45** - [rgb](rgb.md#picking-the-level-shifter)
- ~~Board still has the option-A part (74AHCT125)~~ **done** - U8 is now the SN74LVC2T45DCUR, wired VCCA/VCCB across the rail split
- ~~HV per-side switch FET undecided (SOT-23 thermally marginal at the "4A per-edge" ceiling)~~ **closed** - connector gives a real 4A/side ceiling, design target ≥2A, part is **AO4407A ×4** (same LCSC part as Q2) - [power](power.md#hv-per-side-switches---picking-the-fet)
- ~~Current-sense amplifier for per-side OCP is not picked~~ **closed - cut entirely.** Not DNP: a DNP footprint costs the same board area as a populated one, and area is the binding constraint. Fast fault is bounded by the PD source, slow fault is preventable in firmware via the tile map. **ADC budget 6/8 → 2/8** - [re-decision](../design-choices/power.md#re-decision-does-this-need-per-edge-ocp-at-all)
- **The research's HV-switch gate values are backwards** (39k/470k forms a divider → Vgs = −0.69V at 9V, switch never turns on). Corrected to 100k/4.7k/100nF - [power](power.md#gate-drive---the-researchs-values-are-backwards)
- **Comparator divider re-derived, needs applying in KiCad:** R30 → **35.7k** (C2681604), R31 → **10k** (C2902636), R22 → **5.1k** (C25905). 12.2kΩ never existed, and the old split put the margin on the graceful limit instead of the destructive one. U10 is already TLV431B ✓ - [power](power.md#the-margin-question-read-this-one)
- **U9 swap not applied to the board yet** - schematic still has `MAX40203` / WLP-4. Symbol, footprint (SC-70-6), Value and LCSC (C2832141) must move together because the BOM pulls Value - [power](power.md#ideal-diode---lm66100-u9)
- ~~MAX40203 6.0V ceiling vs UTP 5.95V~~ **closed - accepted deliberately.** Structurally unfixable (UTP can never be below 5.5V while LTP clears vSafe5V), inside abs max, transient - [power](power.md#accepted-risk-595v-on-a-60v-part)
- **U16's EN is tied to GND through a 0Ω (R23)** - AP2171W is active-high, so the submodule rail can never turn on as drawn. Needs 4.7kΩ + a `SM EN` GPIO
- **Unverified: does AP2171W's OCP latch or auto-retry?** Diodes bot-blocks the datasheet. If it latches, U16's EN is the only way to clear a submodule fault - [submodules](../design-choices/submodules.md#why-u16-does-need-firmware-control)
- **Capacitor footprints are wrong on 4 parts** (~~5~~ - the 100µF **C41 is now 1µF**, which fixes one). Remaining: **4× 22µF in 0402** (C28/C29/C34/C35), which doesn't exist. Plus C26/C31 10µF 0402 on the 20V PD+ rail, unbuyable at that voltage - [implementation](implementation.md#capacitor-footprints)
- **Doc/board mismatch on the LDO input cap:** power.md claimed **C24 = 10µF** *"exactly the pairing Torex characterises"*; the board has **1µF**. Confirm 1µF is acceptable for the XC6220 or change one of them - [power](power.md#3v3-ldo---tlv76733drvr-u7)

---
Back to [main index](../index.md) · build log at [log](log.md)
