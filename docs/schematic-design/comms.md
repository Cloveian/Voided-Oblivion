# Comms & USB - schematic-design calcs

Datasheet math for the USB front-end and inter-tile/submodule links. Parts from [chips](../chips.md); behavior from [comms design-choice](../design-choices/comms.md).

Per-section skeleton: **Goal → Datasheet refs → Math → Result → Notes/gotchas.**

## Contents
- [USB-C mux - TMUX1574PWR](#usb-c-mux--tmux1574pwr)
- [USB-PD PHY - FUSB302BMPX](#usb-pd-phy--fusb302bmpx)
- [D+/D− series & ESD](#dd-series--esd)
- [CC line series R / Rd pulldowns](#cc-line-series-r--rd-pulldowns)
- [VBUS-A → SEL detect](#vbus-a--sel-detect)
- [Inter-tile UART lines](#inter-tile-uart-lines)
- [Submodule corner UART lines](#submodule-corner-uart-lines)

---

## USB-C mux - TMUX1574PWR
### Goal
Mux CC1/CC2/D+/D− between 2 ports, single SEL from VBUS-A detect.
### Datasheet refs
### Math
### Result / parts
### Notes / gotchas
SEL has a internal pull down resistor

## USB-PD PHY - FUSB302BMPX
### Goal
I²C PD negotiation, MCU-driven. SDA/SCL GPIO20/21, INT GPIO15.
### Datasheet refs
### Math
_(I²C pullup values; address)_
### Result / parts
### Notes / gotchas

## D+/D− series & ESD
### Goal
### Datasheet refs
### Math
_(series R ~22–33Ω if needed; ESD array)_
### Result / parts
### Notes / gotchas
- Short the two D+ pads / two D− pads (orientation-agnostic)

## CC line series R / Rd pulldowns
### Goal
### Math
- ~100Ω series (ESD), Rd on RP2350B side
### Notes / gotchas

## VBUS-A → SEL detect
### Goal
Drive mux SEL: A has VBUS → route A, else B.
### Math
_(divider/transistor thresholds)_
### Notes / gotchas

## Inter-tile UART lines
### Goal
4 sides × Tx/Rx, ≥4 Mbaud. Top+Left=UART0, Bottom+Right=UART1 (rotation pairing).
### Notes / gotchas
- Rx pulldown per side (neighbor detect)

## Submodule corner UART lines
### Goal
4 corners × Tx/Rx (GPIO22–29), independent PIO, ~300mA/port 5V.
### Notes / gotchas

---
Back to [schematic-design index](index.md) · [checklist](../schematic-checklist.md)
