# Submodules

## Identify
I need to decide on how to do the submodules

### Relevant constraints/nice to haves:

### Must haves
- Sub-1 ms latency
- Ortho-linear layout
- Portable
- Easily replaceable switches

### Nice to haves
- Low profile

## Brainstorm
The main idea i have is having a per corner connection for a submodule, where each corner has pin headers of some sort with 5V, GND, Rx and Tx, probably in an array like this:
```
______________________________________________________________________
|     5V GND Rx Tx                                 5V GND Rx Tx      |
| Tx                                                              5V |
| Rx                                                             GND |
| GND                                                             Rx |
| 5V                                                              Tx |
|                                                                    |
|                                                                    |
|                                                                    |
|                                                                    |
|                                                                    |
|                                                                    |
|                                                                    |
|                                                                    |
|                                                                    |
|                                                                    |
|                                                                    |
|                                                                    |
|                                                                    |
|                                                                    |
|                                                                    |
|                                                                    |
|                                                                    |
|                                                                    |
|                                                                    |
|                                                                    |
|                                                                    |
|                                                                    |
|                                                                    |
|                                                                    |
| Tx                                                              5V |
| Rx                                                             GND |
| GND                                                             Rx |
| 5V                                                              Tx |
|     Tx Rx GND 5V                                  Tx Rx GND 5V     |
|____________________________________________________________________|
```
And the submodule would look like this (if it were a rectangle)
```
________________________________
|                              |
| Rx                           |
| Tx                           |
| GND                          |
| 5v                           |
|______________________________|

(rotated)
___________________
|  5V  GND Tx Rx  |
|                 |
|                 |
|                 |
|                 |
|                 |
|                 |
|                 |
|                 |
|                 |
|                 |
|                 |
|                 |
|_________________|
```
And if it was more than 1un wide:
```
________________________________
|                5V GND Tx Rx  |
| Rx                           |
| Tx                           |
| GND                          |
| 5V                           |
|                              |
|                              |
|                              |
|                              |
|                              |
|                              |
|                              |
|                              |
|                              |
|                              |
|                              |
|                              |
|                              |
|                              |
|                              |
|                              |
|                              |
|______________________________|

(rotated)
_____________________________________________________________________
|                                                   5V GND Tx Rx    |
|                                                                   |
|                                                                   |
|                                                                   |
|                                                                   |
|                                                                   |
|                                                                   |
|                                                                   |
|                                                                   |
|                                                                   |
|                                                                5V |
|                                                               GND |
|                                                                Tx |
|                                                                Rx |
|___________________________________________________________________|
```
I think this would be good because it can be in every corner and is rotatable
## Power draw

Each submodule carries its own MCU (~tens of mA baseline) plus whatever its peripheral pulls. Rough per-module estimates at 5 V:

| Module | Typical draw | Notes |
| --- | --- | --- |
| Rotary encoder | ~10-30 mA | basically just the MCU |
| Analog joystick / slider | ~10-30 mA | |
| 7-segment display | ~20-60 mA | scales with lit segments |
| Small OLED | ~20-40 mA | |
| E-ink | ~uA idle, ~mA bursts | nearly free except during a refresh |
| NFC reader | ~30-60 mA | higher during a read |
| Trackpad / trackball | ~20-50 mA | |
| Fingerprint (smart sensor) | ~50-100 mA | during a scan; low idle |
| Touchscreen / backlit TFT | ~100-300 mA | the high end; the backlight dominates |

Takeaways:
- Most modules are tens of mA (MCU-dominated); the ceiling is a backlit display at a few hundred mA.
- For power budgeting, reserve a **per-port allowance** sized to the worst module class intended to be supported (~300 mA if displays/touch are in scope, much less for simple input-only modules).
- This is the ~50-300 mA/each figure carried into the [power](power.md) page, and it is **additive** on top of a tile's own key/RGB/MCU load.


I am gonna put a pin in this file for now as i need to figure our what the current state of what pins are available is, if reading by stream of consciousness go back to [index](../index.md)

## Continue — pins exist, un-pausing

ok i did the [pin-budget](pin-budget.md) page and the thing i was waiting on is answered: there's room. so let me actually lock the submodule connector down.

### the connector
sticking with the 4-pin per-corner idea from up top: **5V, GND, Rx, Tx**, one connector at each of the 4 corners. the mirrored/rotatable pad layout i sketched stays (so a module drops in the same regardless of which corner / rotation).

pin budget says each corner gets its own dedicated Tx + Rx straight off the RP2350B:
- 4 corners × (Tx + Rx) = **8 GPIO**, assigned GPIO22–29 in the budget
- and per the [comms revisit](comms.md#revisit-actually-dont-mux-them) these are **not muxed** — every corner is an independent PIO Tx/Rx pair, so all 4 corners can talk at once with zero queueing. (if i ever need those SMs back, muxing is the easy lever, but for now they're independent.)
- 5V comes off the tile's big buck (the gated noisy rail), GND is the common reference. no per-corner power switching, the per-port current is small enough not to bother.

so each corner connector is dead simple: power + ground + a full-duplex UART. a submodule is just "has an MCU, speaks UART, pulls ≤300mA."

### power
already worked out above — reserve a **per-port allowance** (~300mA if displays/touch are in scope, way less for simple input modules), additive on top of the tile's own load, carried into [power](power.md). firmware does live estimation: a module announces what class it is when it connects, master adds it to the budget, and if there isn't headroom it trims elsewhere (RGB first).

### protocol (the firmware side, just noting it)
- module connects → sends a hello on its corner UART saying what it is
- tile forwards that upstream to master (it's the "submodule connect" event from the [comms](comms.md) upstream list)
- master updates the USB HID descriptors if it's a pointing device / adds it to the power budget
- disconnect detection falls out of the same Rx-idle / pulldown trick comms already uses for neighbor detection

### what's actually still open
- **physical connector choice** — pin headers vs something keyed/magnetic vs pogo pins. this is a mechanical/enclosure call, not an electrical one, so it waits until i'm doing the case + board outline. the 4 signals don't change whatever i pick.
- everything electrical is settled. submodules are off the critical path now — i can design tiles without a single submodule existing, then add modules later against this fixed 4-pin contract.

so: **submodule connector = 4-pin (5V/GND/Rx/Tx) per corner, independent UART per corner, ~300mA/port budget.** un-paused and basically done, just the connector body to pick later. back to [index](../index.md)
