# Main Topology

## Identify
The overall system needs a way to run.

### What Need to Be Done?

#### Roles
- Master 
	who?
- Edge cases
- Split roles? (data/power)

#### Execution
- What runs on what core
- Which tasks share an executor, what interrupts

#### Faults
- Watchdog
- PD gates

#### Inter-tile
- Discovery + join: HELLO, BFS from master, rotation per tile, hotplug mid-frame
- Frame format, slot assignment
- Downstream message types
- Errors: bad CRC, unplug garbage, neighbour goes quiet

#### Flash
- What chip for what?

#### Keys
- Actuation point, rapid trigger thresholds, per key or global
- Keymap/layers on the master, mapping onto arbitrary arrays

#### USB
- Default settings: N-key roll over, mouse, raw HID (config, analog, RGB), CDC (debug)
- Boot/BIOS fall back?
- FIDO2 interface (usage page `0xF1D0`) (but probably later)

#### Power
- PD control
- What to do on `SM+ FLT` and `BS+ SRC`
- Power usage prediction/management

#### Submodules
- ID levels → module classes
- UART protocol, hotplug, when the corner rail gets powered

## Brainstorm

## Select

---
Back to [firmware index](index.md)
