# Keys & sensing - schematic-design calcs

Hall sensor + mux + ADC math. Parts from [chips](../chips.md); decisions from [hall-effect-sensors](../design-choices/hall-effect-sensors.md).

Per-section skeleton: **Goal → Datasheet refs → Math → Result → Notes/gotchas.**

## Contents
- [Hall sensor - GH39F](#hall-sensor--gh39f)
- [Analog mux - 74HC4067 ×2](#analog-mux--74hc4067-2)
- [ADC scaling / scan timing](#adc-scaling--scan-timing)
- [Sensor bank-power gating](#sensor-bank-power-gating)

---

## Hall sensor - GH39F
### Goal
Per-key analog readout on 3V3 clean rail. 3-pin SOT-23 (Vcc/OUT/GND), substitutable footprint.
### Datasheet refs
- Supply current 2–9mA (budget 9mA worst); output swing vs field
### Math
_(output range into ADC; per-key min/max calibration absorbs offset)_
### Result / parts
### Notes / gotchas

## Analog mux - 74HC4067 ×2
### Goal
32 ch on 2 ADC pins + 4 shared selects. 30 keys → 2 spare ch.
### Datasheet refs
- Ron, switching time vs scan budget
### Math
_(settling time per channel vs 1ms/1000Hz scan; ~10× headroom claim)_
### Result / parts
### Notes / gotchas
- Outputs → ADC GPIO40/41; selects → GPIO8–11

## ADC scaling / scan timing
### Goal
Full 12-bit per key, sub-1ms whole-tile scan.
### Math
_(mux settle + ADC conv × 30 keys ≤ scan window)_
### Notes / gotchas

## Sensor bank-power gating
### Goal
Energize only the scanned group → cut ~270mA continuous.
### Math
_(FET pick; settle time after power-on vs scan)_
### Notes / gotchas
- Confirming this enables the XC6206/XC6220 LDO downgrade path

---
Back to [schematic-design index](index.md) · [checklist](../schematic-checklist.md)
