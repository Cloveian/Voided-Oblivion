# Voided Oblivion

The working design doc. Project context, tools, and background live in the [overview](overview.md).

## Goals & constraints
There are a few things I wanted when I originally had the idea for this keyboard, listed roughly from hardest constraints down to less necessary stuff:

### Must haves
- Work as a keyboard
- Be able to finish in under ~2 months

### Must haves in order to be useful as my daily driver (basically full on constraints)
- USB type C wired connectivity
- Sub-1 ms latency
- 1000Hz polling rate (can have others, but must support 1000Hz)
- Have number row
- Ortho-linear layout
- Portable
- N-key rollover
- Easily replaceable switches

### Nice to haves
- Function keys row
- Per-key RGB (under-glow)
- Low profile
- Number pad
- ~~Bluetooth+USB dongle~~
- FIDO 2
- Ability to do on-device steno

### Nice to have, but slightly far-fetched (harder to achieve)
- Have submodules
	- Fingerprint sensor
	- Screen
	- Rotary encoders
	- ~~3.5 mm AUX port for sound output~~

## Design Choices

- [Form factor](design-choices/form-factor.md) - **Modular 5×6 ortho tiles** (won't be a simple build)
- [Switches](design-choices/switches.md) - **Void Switch-based custom switch** (low-profile modified Void Switch, analog hall effect)
- [Random-ah features](design-choices/feature-decisions.md) - For sure decisions: Submodules, per-key RGB, FIDO 2, no bluetooth, no AUX port

With these design choices these are the **MCU requirements**:
- Native USB device (composite HID) (on the root tile)
- Flexible timed I/O (PIO-like) to drive BOTH the inter-tile bus (≤4 sides) and the per-key RGB
- ADC + enough GPIO to analog-mux ~30 Hall keys/tile, fast enough for sub-1 ms
- Enough compute for per-tile analog scan + rapid-trigger at 1000 Hz
- Built in secure element, or I$^{2}$C for an external secure element (FIDO2)

Continuing:
- [Controller (MCU)](design-choices/controller.md) - RP2350B with the option to populate a second 16MB flash chip
- [Key sensors & MUX](design-choices/hall-effect-sensors.md) - GH39F for sensor, 74HC4067 for mux
- [RGB](design-choices/rgb.md) - need to make more decisions before this
- [Submodules](design-choices/submodules.md) - basic idea sketched out
- [Power](design-choices/power.md) - really complicated power flow mostly figured out
- [Communications](design-choices/comms.md) - PIO uart for inter-module communication, independent uart per sub module corner
- [RGB (revisit)](design-choices/rgb.md#continue)- SK9822-EC20 was chosen
- [Pin budget](design-choices/pin-budget.md) - it all fits on one RP2350B: 44/48 GPIO, 6/8 ADC, 12/12 PIO SMs
- [Submodules (revisit)](design-choices/submodules.md#continue---pins-exist-un-pausing) - 4-pin (5V/GND/Rx/Tx) per corner, independent UART, un-paused
- [module-connectors](design-choices/module-connectors.md)
- [Key sensors (revisit)](design-choices/hall-effect-sensors.md#revisit-hall-effect-sensor-heat-sensitivity) - rework heat is not a concern with hotplate + low temp paste + firmware calibration
- [PCB stackup & net rules](design-choices/pcb-stackup.md) - **4-layer** (sig/GND/pwr/sig). The matrix picked 6, but this is open source and other people pay the layer count - track/via/clearance rules for every net class

## Building the schematic
Design choices are settled; now wiring up one tile.
- [Schematic checklist](schematic-checklist.md) - what to wire, per block, with the pin assignment
- [Schematic-design calcs](schematic-design/index.md) - datasheet math behind the component values
- [Build log](schematic-design/log.md) - dated, pick-up-where-I-left-off notes

## Laying out the board
- [Layout checklist](layout-checklist.md) - what's left to place and route, in order. **164 of 425 parts still off-board, 169 of 242 nets unrouted**
- [Recommended layouts](../Refrences/recommended-layouts/recommended-layouts.pdf) - datasheet layout pages for every chip, stitched, titled with the ref designator and what it does here