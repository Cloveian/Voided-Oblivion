# Design choices

`Revisited`{.status .revisited}

<!-- STUB - this is a reading-path skeleton, not finished prose. The one-line
     descriptors below are lifted verbatim from the root index so nothing here
     is invented; rewrite them in your own voice when you do the content pass. -->

Read these roughly in order - each one constrains the next, and several get
reopened later once a downstream decision proved them wrong.

## The shape of the thing

1. [Form factor](form-factor.md) - **Modular 5×6 ortho tiles** (won't be a simple build)
2. [Switches](switches.md) - **Void Switch-based custom switch** (low-profile modified Void Switch, analog hall effect)
3. [Feature decisions](feature-decisions.md) - Submodules, per-key RGB, FIDO 2, no bluetooth, no AUX port

Those three together produce the MCU requirements, which is what the next
section is answering.

## Picking the parts

4. [Controller (MCU)](controller.md) - RP2350B with the option to populate a second 16MB flash chip
5. [Key sensors & MUX](hall-effect-sensors.md) - GH39F for sensor, 74HC4067 for mux · *revisited twice*
6. [RGB](rgb.md) - SK9822-EC20 · *revisited*
7. [Submodules](submodules.md) - 4-pin (5V/GND/Rx/Tx) per corner · *revisited*
8. [Power](power.md) - really complicated power flow · *re-decided*
9. [Communications](comms.md) - PIO UART inter-module, independent UART per corner · *revisited ×3*

## Does it fit

10. [Pin budget](pin-budget.md) - 44/48 GPIO, 6/8 ADC, 12/12 PIO SMs · *corrected*
11. [Module connectors](module-connectors.md) - *revisited ×2*
12. [PCB stackup & net rules](pcb-stackup.md) - **4-layer** (sig/GND/pwr/sig)

---

Pages marked *revisited* / *corrected* contain reasoning that was later found
wrong. It's kept rather than deleted - the dimmed blocks are the original
thinking, with a link to what replaced it.
