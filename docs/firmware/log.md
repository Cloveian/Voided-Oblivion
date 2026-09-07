# Firmware log

Dated, newest-on-top. Same job as the [schematic build log](../schematic-design/log.md): read the top entry and you're back in it.

---

## 2026-09-06 - section created, nothing written yet

Skeletoned the firmware section out before writing any code, on the theory that the board already dictates most of this and it's cheaper to collect it now than to find it one brownout at a time.

- **Pulled the pin assignment together** into a [pin map](pin-map.md), and the same pins grouped by function into a [truth table](truth-table.md) - what each state actually means at the other end. The hardware pages stay the source of truth; these are a summary and summaries drift.
- **The pin map needed reconstructing from three sources** and none of them is currently right on its own: [pin-budget](../design-choices/pin-budget.md#a-starting-assignment) and [checklist §9](../schematic-checklist.md) both predate the second I²C bus, the submodule control pins and the current-sense cut, and §9's "spare" list still names pins that are assigned. The reviews filled in GPIO33/36/37 from the raw files. **The netlist is the only authority** - the corner→physical-corner mapping and the `PD EN` side order still need reading off it.
- **Three things are contested and would produce silently wrong firmware:** CC crossed vs straight (docs say crossed, two reviews say straight with netlist evidence), the SK9822 colour order (the datasheet contradicts itself in one revision), and whether the [C1 fix](../schematic-design/power.md#revisit-2026-08-20---the-first-handoff-kills-bs-and-the-fix-is-moving-vin-to-vbus) landed before the boards were ordered. That last one gates every PD milestone - if it didn't land the board is 5 V-only and there's nothing to test against.
- **Drafted the [platform decision](platform.md).** QMK and ZMK both fail on gates rather than on scores - fixed build-time split topology and no PD concept - so the real field is Pico SDK + TinyUSB, Rust/embassy, or bare Zephyr. Table says Pico SDK at 88 %, and the sensitivity check says nothing *inside* the table flips it. What flips it is **gate 6, whether the co-writer works in C** - which is a gate, not a row, and isn't mine to answer.
- **Found one thing that needs deciding before any code:** the docs say the master "updates the HID descriptors" when a pointing submodule appears. That isn't possible after enumeration - it means a re-enumerate mid-use every time someone plugs in a knob. Fix is to declare a composite device up front and just not send reports for absent hardware. Cheap now, expensive later.
- **Also noted:** 1000 Hz is the *ceiling* here, not a target - RP2350 USB is full-speed and FS HID's minimum interval is 1 ms.

**Next:** settle gate 6, then confirm the C1 fix status against the ordered gerbers, then a single-tile bring-up firmware - no mesh, no PD - that can actually answer the bench list on the [truth table](truth-table.md).

---
Back to [firmware index](index.md)
