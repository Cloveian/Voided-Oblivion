# RGB - schematic-design calcs

SK9822-EC20 chain math. Parts from [chips](../chips.md); decision from [rgb design-choice](../design-choices/rgb.md).

Per-section skeleton: **Goal → Datasheet refs → Math → Result → Notes/gotchas.**

## Contents
- [SK9822-EC20 chain](#sk9822-ec20-chain)
- [SPI drive - SCK/DATA series & level shift](#spi-drive--sckdata-series--level-shift)
- [Rail current budget & caps](#rail-current-budget--caps)

---

## SK9822-EC20 chain
### Goal
~30 reverse-mount LEDs/tile on gated-5V, hardware SPI0 (SCK GPIO34, TX GPIO35).
### Datasheet refs
- 18mA/LED worst case; global brightness field
### Math
_(worst-case 30×18mA = 540mA; firmware cap in practice)_
### Result / parts
### Notes / gotchas

## SPI drive - SCK/DATA series & level shift
### Goal
3.3V MCU → 5V LED logic.
### Math
_(check SK9822 VIH vs 3.3V; add 74AHCT level shift if marginal; 22–33Ω series for ringing)_
### Notes / gotchas

## Rail current budget & caps
### Goal
Bulk cap for LED inrush/ripple on gated-5V.
### Math
_(bulk C for chain; per-LED decoupling density)_
### Notes / gotchas
- Powered from **big (gated) buck**, NOT the clean rail

---
Back to [schematic-design index](index.md) · [checklist](../schematic-checklist.md)
