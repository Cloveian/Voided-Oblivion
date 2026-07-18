# Power - schematic-design calcs

Datasheet math and component derivations for the power block. Parts come from [chips](../chips.md); wiring/behavior from [power design-choice](../design-choices/power.md); the front-end topology is in [schematic-checklist](../schematic-checklist.md).

Rails: **PD+** (HV, ~5–20V), **BS+** (bootstrap 5V, always-on), **gated-5V** (RGB/submodules), **3V3** (clean), **GND**.

Per-section skeleton: **Goal → Datasheet refs → Math → Result → Notes/gotchas.**

## Contents
- [Clean buck - TPS54302 (HV→5V, always-on)](#clean-buck--tps54302)
- [Big buck - TPS54302 (HV→gated-5V)](#big-buck--tps54302)
- [3V3 LDO - XC6220B331MR](#3v3-ldo--xc6220b331mr)
- [Ideal diode - MAX40203 (BS+ OR'ing)](#ideal-diode--max40203)
- [VBUS comparator - TLV1805 (~6V threshold)](#vbus-comparator--tlv1805)
- [VBUS→BS+ switch - AO3415](#vbusbs-switch--ao3415)
- [VBUS→PD+ switch - Q2 (TBD type)](#vbuspd-switch--q2)
- [HV per-side switches - AO3401A + NPN](#hv-per-side-switches--ao3401a--npn)
- [Backfeed diodes - SS54](#backfeed-diodes--ss54)
- [Bulk / hold-up caps](#bulk--hold-up-caps)

> The VBUS front-end (implement → snags → revisit) moved to its own page: [implementation](implementation.md#vbus-front-end-the-6v-handoff).

---

## Clean buck - TPS54302
### Goal
5.0V from PD+ (must start ~5.5V, run to 20V), ~150–300mA load. Feeds LDO + OR's onto BS+.
### Datasheet refs
- Vref = _TBD_ (§_), Vout = Vref·(1 + R_top/R_bot)
- Inductor eq _, Isat/Irms > _; input/output cap guidance §_
### Math
_(divider, inductor, caps - show E96 rounding + resulting Vout error)_
### Result / parts
_R_top, R_bot, L, Cin, Cout_
### Notes / gotchas
- 0402 OK on this 5V output rail; **Cin sees PD+ (20V) → needs ≥25–35V, 0805+**

## Big buck - TPS54302
### Goal
5.0V gated (EN=GPIO14), RGB + submodules, ~2A worst case, 5–20V in.
### Datasheet refs
### Math
### Result / parts
### Notes / gotchas
- Same part as clean buck (single BOM line); higher current → check inductor Irms + thermals

## 3V3 LDO - XC6220B331MR
### Goal
3.3V for MCU + hall sensors + mux, low-noise. Input = **BS+** (so 3V3 exists pre-PD).
### Datasheet refs
- 5-pin SOT-25, CE pin; dropout §_
### Math
### Result / parts
### Notes / gotchas
- **CE tied to VIN via jumper (always-on)**; confirm dropout at max sensor current

## Ideal diode - MAX40203
### Goal
OR clean-buck 5V onto shared BS+ with near-zero drop, ~1A.
### Datasheet refs
### Math
### Result / parts
### Notes / gotchas
- EN high= enableded

## VBUS comparator - TLV1805
### Goal
Trip at ~6V on VIN: below → VBUS feeds BS+; above → VBUS→PD+. Needs stable ref + hysteresis.
### Datasheet refs
- Supply range §_ (must survive VIN up to 20V); output type §_
### Math
_(sense divider on VIN; reference source; hysteresis resistor → V_trip_hi/V_trip_lo)_
### Result / parts
### Notes / gotchas
- **OPEN: reference source** (shunt ref vs 3V3 divider) - 3V3 is up pre-PD via BS+→LDO
- Pick hysteresis wide enough to not chatter as VIN ramps through 6V

## VBUS→BS+ switch - AO3415
### Goal
P-FET, VIN→BS+, default ON, comparator turns OFF above ~6V (protect BS+ from >5V).
### Datasheet refs
### Math
_(gate pull values; Rds/current at pre-PD load)_
### Result / parts
### Notes / gotchas
- 20V rating fine - only conducts while VIN ≤5V

## VBUS→PD+ switch - Q2
### Goal
Connect VIN→PD+ above ~6V, default OFF. Rated ≥24V, passes up to ~4A.
### Datasheet refs
### Math
### Result / parts
### Notes / gotchas
- **OPEN: device type + gate drive** - P-FET (simple high-side) vs N-FET (needs charge pump/bootstrap)

## HV per-side switches - AO3401A + NPN
### Goal
×4, switch PD+ per edge, RC soft-start, firmware OCP via ADC sense.
### Datasheet refs
- AO3401A 30V/4A; NPN (BC847/MMBT2222) gate level-shift
### Math
_(RC soft-start τ vs downstream Cin inrush; OCP sense-R value + ADC scaling; gate R)_
### Result / parts
### Notes / gotchas
- Sense lines → ADC GPIO42–45; enables → GPIO0–3 (jumpered)

## Backfeed diodes - SS54
### Goal
One per port on VBUS→PD+ path; block port-to-port backfeed; combine to VIN.
### Datasheet refs
- 40V/5A SMA; low reverse leakage (C7420369, 50µA)
### Math
_(worst-case current = 4A @ 80% of 5A@20V; forward drop / thermal)_
### Result / parts
### Notes / gotchas
- SMA package (not a chip passive); Schottky fine on HV rail (drop irrelevant)

## Bulk / hold-up caps
### Goal
BS+ hold-up over the comparator→clean-buck handoff (µs); PD+ and rail bulk.
### Datasheet refs
### Math
_(hold-up: C = I·Δt/ΔV for the handoff; DC-bias derating on 20V-rail 0402s)_
### Result / parts
### Notes / gotchas
- **HV-rail bulk caps → 0805/1206 at ≥25–35V** (0402 loses too much C to DC bias)

---
Back to [schematic-design index](index.md) · [checklist](../schematic-checklist.md)
