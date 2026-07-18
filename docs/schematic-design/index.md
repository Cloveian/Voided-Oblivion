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
- Q2 (VBUS→PD+ switch) device type + gate drive - [power](power.md#vbuspd-switch--q2)
- VBUS comparator reference source + hysteresis - [power](power.md#vbus-comparator--tlv1805)
- Steno flash: 2nd chip vs boot-flash-only - [mcu](mcu.md#qspi-flash--w25q128jvs)
- SK9822 3.3V→5V level-shift needed? - [rgb](rgb.md#spi-drive--sckdata-series--level-shift)

---
Back to [main index](../index.md) · build log at [log](log.md)
