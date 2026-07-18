# MCU & flash - schematic-design calcs

RP2350B support-circuit math. Parts from [chips](../chips.md); decision from [controller](../design-choices/controller.md).

Per-section skeleton: **Goal → Datasheet refs → Math → Result → Notes/gotchas.**

## Contents
- [RP2350B power / decoupling](#rp2350b-power--decoupling)
- [Crystal + load caps](#crystal--load-caps)
- [QSPI flash - W25Q128JVS](#qspi-flash--w25q128jvs)
- [USB DP/DM](#usb-dpdm)
- [Boot / reset / SWD](#boot--reset--swd)

---

## RP2350B power / decoupling
### Goal
Stable 3V3 (+ core) with proper decoupling per datasheet.
### Datasheet refs
- Per-pin decoupling, core regulator caps §_
### Math
### Result / parts
### Notes / gotchas
- Confirm core rail scheme (internal reg + caps)

## Crystal + load caps
### Goal
Accurate USB clock (12MHz).
### Math
_(CL = 2·(Cload − Cstray) → cap value)_
### Notes / gotchas
- Crystal, not internal osc - USB needs the accuracy

## QSPI flash - W25Q128JVS
### Goal
16MB steno dict.
### Notes / gotchas
- **OPEN: 2nd chip (CS1n GPIO19, 37/48) vs boot-flash-only (36/48)** - resolve before placing

## USB DP/DM
### Notes / gotchas
- To TMUX1574; 27Ω series + ESD if not handled by mux

## Boot / reset / SWD
### Notes / gotchas
- BOOTSEL, RUN/reset, SWD header (SWCLK/SWDIO/GND/3V3) - don't skip

---
Back to [schematic-design index](index.md) · [checklist](../schematic-checklist.md)
