# Pin Budget

## Identify
I need to figure out what my pin budget is for each module (like for the rp2350b)

### Constraints
not as relevant, just hooking made decisions up to each other.

### Things that need hooked up:
ok so basically i'm just going through every other page and grabbing whatever it said it needed pins for, and dumping it all here so i can see if it actually fits.

- **Key sensing** ([hall-effect-sensors](hall-effect-sensors.md)): 2× 74HC4067, so that's 2 ADC inputs + 4 select lines (the select lines are shared between both muxes, nice)
- **HV per-side switches** ([power](power.md)): 4× HV-enable, and since i went discrete instead of the fancy eFuse, firmware OCP needs to actually *see* the current per side too, so that's another 4 (ADC, or muxed, i'll figure it out lower down)
- **USB-PD** ([power](power.md)): FUSB302 talks over I²C, so SDA + SCL + an INT line
- **Inter-tile comms** ([comms](comms.md)): 4 sides × (Tx + Rx) = 8. yeah 2 sides ride the hardware UARTs and 2 ride PIO but they ALL still need a physical pin, the UART thing doesn't save me any copper
- **Submodules** ([submodules](submodules.md) / [comms](comms.md)): 4 corners × (Tx + Rx) = 8. and important gotcha i almost messed up: PIO-muxing the submodules saves *state machines*, not *pins*. still 8 pins. no getting around it :<
- **RGB** ([rgb](rgb.md)): SK9822 is on hardware SPI so just SCK + TX, 2 pins
- **Big buck enable** ([power](power.md)): 1 pin. the clean buck is always-on so it doesn't need a pin, only the big gated one does
- **Steno flash** ([controller](controller.md)): the 16MB QSPI flash. if it's a *second* chip hanging off the QSPI bus it wants QMI CS1n (1 pin), but if the steno dict just lives on the boot flash then it's free

**stuff that looks like it should cost pins but doesn't :3**
- USB D+/D− are their own dedicated pins, not part of the GPIO bank → 0
- the dual USB-C mux SEL is driven by VBUS in hardware ([comms](comms.md)) → 0
- FIDO2 secure element is baked into the RP2350B (TrustZone) so no external chip → 0
- the whole VBUS→bootstrap/HV comparator handoff is hardware ([power](power.md)) → 0

### The chip

**RP2350B (QFN-80):** 48 GPIO (0–47). the stuff that's actually picky about *where* it goes:
- **ADC:** only 8 channels and they're ONLY on GPIO40–47 (input 8 is the temp sensor). so anything analog HAS to land in that little corner. this is the real bottleneck, not the raw pin count.
- **Hardware UART:** 2 of them (UART0, UART1). TX/RX shows up on basically every pin (F1/F2/F11) so these go pretty much wherever
- **Hardware SPI:** 2 (SPI0, SPI1) via F0
- **I²C:** 2 via F3
- **PIO:** 12 state machines across 3 blocks, and PIO can map to *any* bank-0 GPIO, so the PIO stuff is the easy stuff to place

## Brainstorm

ok dumping it all in a table to see the damage:

| Function | Pins | where it has to go |
| --- | :---: | --- |
| Key mux ADC outputs (2× 74HC4067) | 2 | **ADC** (GPIO40–47) |
| Key mux select lines (shared) | 4 | anywhere |
| HV per-side enable | 4 | anywhere |
| HV per-side current sense (firmware OCP) | 4 | **ADC** (or mux, see below) |
| FUSB302 I²C (SDA + SCL, shared by both PHYs) | 2 | I²C-capable |
| FUSB302 INT (2 PHYs, 1 line each) | 2 | anywhere |
| Inter-tile comms (4 sides × Tx/Rx) | 8 | 2 sides UART-capable |
| Submodule comms (4 corners × Tx/Rx) | 8 | anywhere (PIO) |
| RGB (SK9822 HW SPI: SCK + TX) | 2 | same SPI instance |
| Big buck enable | 1 | anywhere |
| Steno flash CS1n (if 2nd chip) | 1 | QMI CS1n: GPIO0/8/19/47 |
| **Total** | **38** | |

**ADC used:** 2 (key mux) + 4 (HV sense) = **6 of 8**
**GPIO used:** **38 of 48 → 10 spare** (and 2 of those spares, 46/47, are still ADC-capable, so i even have analog headroom). the +1 over the original 37 is the **2nd FUSB302's INT** - the dual-PHY PD call from the [comms revisit](comms.md#revisit-pdcc-architecture-the-cc-mux-doesnt-survive-cold-start).

it fits!! and not even barely, like there's real room left over. one RP2350B per tile does everything, no second MCU, no painful cuts. very relieved ngl >w<

## A starting assignment

this isn't final (KiCad gets the final say once i'm actually routing), but i wanted to actually slot real pins in to PROVE the picky ADC/UART/SPI stuff doesn't collide, instead of just trusting the count:

| Pins | Use | why these |
| --- | --- | --- |
| GPIO40, 41 | Key mux A/B ADC outputs | ADC |
| GPIO42–45 | HV per-side current sense | ADC |
| GPIO34 (SPI0 SCK), 35 (SPI0 TX) | RGB to SK9822 | hardware SPI0 |
| GPIO20 (I2C0 SDA), 21 (I2C0 SCL) | FUSB302 ×2 (shared bus, address variants) | hardware I²C0 |
| GPIO15 | FUSB302 #1 INT | anywhere |
| GPIO18 | FUSB302 #2 INT | anywhere |
| GPIO12/13 + 16/17 | Inter-tile **Top + Left** (UART0 pair) | both UART0 TX/RX capable, for the rotation thing |
| GPIO4/5 + 6/7 | Inter-tile **Bottom + Right** (UART1 pair) | both UART1 TX/RX capable |
| GPIO22–29 | Submodule corners (4× Tx/Rx) | PIO, anywhere |
| GPIO8–11 | Key mux select lines | anywhere |
| GPIO0–3 | HV per-side enable | anywhere |
| GPIO14 | Big buck enable | anywhere |
| GPIO19 | Steno flash CS1n | QMI CS1n |
| **Spare** | GPIO30–33, 36–39, 46, 47 | 10 free :3 |

the **rotation pairing** ([comms](comms.md)) is why Top+Left are both on UART0-capable pins and Bottom+Right are both on UART1-capable pins. that way when a tile gets turned 90° the same UART firmware path still works, firmware just hands the hardware UART to whichever side in the pair actually has a neighbor and lets the other side run on a PIO SM. past-me on the comms page was smart for once.

## Open / notes

couple things i'm leaving for later, none of them break anything:

- **HV current sense, mux or not:** a 5×6 tile is **30 keys** (locked since [form-factor](form-factor.md)), so the 2× 74HC4067 (32 channels) have exactly **2 spare channels**. the open question: do those 2 spares carry 2 of the 4 HV sense lines, or do all 4 sense lines get their own dedicated ADC?

  i want this all-or-nothing for cleanliness, either ALL 4 sense lines on the muxes or NONE, because a 2-on-mux / 2-on-dedicated split is the ugly middle (mixed routing, firmware reading sense two different ways). all-4-on-mux isn't possible with only 2 spare channels, so that leaves **none**: all 4 HV sense on dedicated ADC, **6/8**. i've got the ADC channels and GPIO to spare anyway, so no reason to get cute. spare mux channels stay spare :3
- **Steno flash:** if the dict just fits on the boot flash, i drop the CS1n pin and it's 36/48. the second-chip option is only if boot + dict don't wanna share nicely.
- **PIO SM sanity check** (cross-checking [comms](comms.md)): RGB on HW SPI (0 SMs) + 2 inter-tile sides on HW UART (0) + 2 inter-tile sides on PIO (4) + submodules NOT muxed, 1 Tx + 1 Rx per corner × 4 (8) = **12 of 12 SMs**. that's the whole budget with 0 spare, on purpose, see the [comms revisit](comms.md#revisit-actually-dont-mux-them) for why (simpler build, and muxing is an easy lever to claw back 6 SMs later if something else needs them). pins don't change either way, the 8 submodule lines are GPIO regardless. the two pages agree :3

so the verdict: **pins close (38/48), ADC closes (6/8), PIO SMs close (6/12).** everything fits on one chip with headroom in all three budgets. AND this clears the thing that was blocking [submodules](submodules.md), there's definitely room for the 4-corner connector, so i can go un-pause that page now >w<
