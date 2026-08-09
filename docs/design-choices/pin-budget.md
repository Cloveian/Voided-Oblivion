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
| ~~HV per-side current sense (firmware OCP)~~ **cut** | ~~4~~ **0** | see the correction below |
| **Submodule corner ID / analog** (4 corners) | **4** | **ADC** (GPIO42–47) |
| **Submodule BS+ branch enable** (`SM BS EN`, U12) | **1** | anywhere |
| **Submodule group switch enable** (`SM EN`, U16) | **1** | anywhere |
| **Submodule rail fault** (`SM FLT`, U16 /FLG) | **1** | anywhere |
| **`BS+ SRC`** — LM66100 ST status (which source is feeding BS+) | **1** | anywhere |
| FUSB302 I²C — **2 separate buses** (SDA+SCL each) | **4** | I²C-capable |
| FUSB302 INT (2 PHYs, 1 line each) | 2 | anywhere |
| Inter-tile comms (4 sides × Tx/Rx) | 8 | 2 sides UART-capable |
| Submodule comms (4 corners × Tx/Rx) | 8 | anywhere (PIO) |
| RGB (SK9822 HW SPI: SCK + TX) | 2 | same SPI instance |
| Big buck enable | 1 | anywhere |
| Steno flash CS1n (if 2nd chip) | 1 | QMI CS1n: GPIO0/8/19/47 |
| **Total** | ~~38~~ **44** | |

**ADC used:** 2 (key mux) + 4 (submodule ID) = **6 of 8**
**GPIO used:** **44 of 48 → 4 spare**

> **Correction - this table has understated by 2 since session 4.** The I²C row said **2**, *"shared by both PHYs"*, but session 4 moved to **two separate I²C buses** so both PHYs could stay the plain BMPX. That added SDA/SCL *and* a second INT; the table picked up the INT (hence *"the +1 over the original 37"*) but never the extra bus. The [log](../schematic-design/log.md) recorded **"budget now 40/48"** at the time, which only works with I²C = 4 — so the log and this table have disagreed by 2 for three sessions. The schematic was always right; it has all four I²C pins drawn.
>
> Corrected chain: **40** (session 4) **− 4** (current sense cut) **+ 4** (submodule ID) **+ 3** (submodule: `SM BS EN`, `SM EN`, `SM FLT`) **+ 1** (`BS+ SRC`) = **44**. (and 2 of those spares, 46/47, are still ADC-capable, so i even have analog headroom). the +1 over the original 37 is the **2nd FUSB302's INT** - the dual-PHY PD call from the [comms revisit](comms.md#revisit-pdcc-architecture-the-cc-mux-doesnt-survive-cold-start).

it fits!! and not even barely, like there's real room left over. one RP2350B per tile does everything, no second MCU, no painful cuts. very relieved ngl >w<

> **Correction - HV current sense was cut entirely.** The line above says *"since i went discrete instead of the fancy eFuse, firmware OCP needs to actually **see** the current per side too"* - that premise is gone. Working through it properly ([re-decision](power.md#re-decision-does-this-need-per-edge-ocp-at-all)): the **fast** fault (dead short) is bounded by the PD source's own current limit, not by anything on my board, and at that limit the switch FET dissipates 0.33W. The **slow** fault (too many tiles on one joint) is preventable in firmware for free, because master already builds the tile map and can refuse to enable an over-budget path.
>
> Board **area** turned out to be the binding constraint, which also killed the "fit the footprints DNP" hedge - a DNP pad costs the same board as a populated one.
>
> **ADC goes 6/8 → 2/8, GPIO 38 → 34, and GPIO42–45 are free.** The "mux or dedicated?" question below is moot - there's nothing to route. Leaving it as the record.

## A starting assignment

this isn't final (KiCad gets the final say once i'm actually routing), but i wanted to actually slot real pins in to PROVE the picky ADC/UART/SPI stuff doesn't collide, instead of just trusting the count:

| Pins | Use | why these |
| --- | --- | --- |
| GPIO40, 41 | Key mux A/B ADC outputs | ADC |
| GPIO42–45 | **Submodule corner ID / analog** | ADC |
| GPIO34 (SPI0 SCK), 35 (SPI0 TX) | RGB to SK9822 | hardware SPI0 |
| GPIO20 (I2C0 SDA), 21 (I2C0 SCL) | FUSB302 ×2 (shared bus, address variants) | hardware I²C0 |
| GPIO15 | FUSB302 #1 INT | anywhere |
| GPIO18 | FUSB302 #2 INT | anywhere |
| GPIO12/13 + 16/17 | Inter-tile **Top + Left** | ~~UART0 pair~~ **all inter-tile is PIO now** |
| GPIO4/5 + 6/7 | Inter-tile **Bottom + Right** | ~~UART1 pair~~ **all inter-tile is PIO now** |
| GPIO22–29 | Submodule corners (4× Tx/Rx) | **24/25 = UART1, 28/29 = UART0 (both F2); 22/23 + 26/27 on PIO** |
| GPIO8–11 | Key mux select lines | anywhere |
| GPIO0–3 | HV per-side enable | anywhere |
| GPIO14 | Big buck enable | anywhere |
| GPIO19 | Steno flash CS1n | QMI CS1n |
| **Spare** | GPIO30–33, 36–39, 46, 47 | 10 free :3 |

the **rotation pairing** ([comms](comms.md)) is why Top+Left are both on UART0-capable pins and Bottom+Right are both on UART1-capable pins. that way when a tile gets turned 90° the same UART firmware path still works, firmware just hands the hardware UART to whichever side in the pair actually has a neighbor and lets the other side run on a PIO SM. past-me on the comms page was smart for once.

> **superseded** - all four inter-tile sides are on PIO now, so there's no hardware UART to hand around and the pairing constraint is gone. The pins stay where they are (no reason to churn them), but they no longer *need* to be UART-capable. Why: [the PL011 is the slower path](comms.md#revisit-the-piosm-allocation-was-built-on-a-wrong-assumption).

## Open / notes

couple things i'm leaving for later, none of them break anything:

- **HV current sense, mux or not:** a 5×6 tile is **30 keys** (locked since [form-factor](form-factor.md)), so the 2× 74HC4067 (32 channels) have exactly **2 spare channels**. the open question: do those 2 spares carry 2 of the 4 HV sense lines, or do all 4 sense lines get their own dedicated ADC?

  i want this all-or-nothing for cleanliness, either ALL 4 sense lines on the muxes or NONE, because a 2-on-mux / 2-on-dedicated split is the ugly middle (mixed routing, firmware reading sense two different ways). all-4-on-mux isn't possible with only 2 spare channels, so that leaves **none**: all 4 HV sense on dedicated ADC, **6/8**. i've got the ADC channels and GPIO to spare anyway, so no reason to get cute. spare mux channels stay spare :3
- **Steno flash:** if the dict just fits on the boot flash, i drop the CS1n pin and it's 36/48. the second-chip option is only if boot + dict don't wanna share nicely.
- **PIO SM sanity check** (cross-checking [comms](comms.md)): RGB on HW SPI (0 SMs) + **4 inter-tile sides on PIO (8)** + **2 submodule corners on HW UART (0) + 2 on PIO (4)** = **12 of 12 SMs**. that's the whole budget with 0 spare, on purpose, see the [comms revisit](comms.md#revisit-actually-dont-mux-them) for why (simpler build, and muxing the corners is an easy lever to claw back SMs later if something else needs them). pins don't change either way. the two pages agree :3
  - > **the allocation flipped**, same total. i'd put the hardware UARTs on the inter-tile sides assuming hardware was the faster path - it isn't. **PL011 caps at UARTCLK/16 = 7.8 Mbaud at 125MHz**; a PIO UART at 8 cycles/bit does ~18.75. So the low ceiling was sitting on the links that carry relayed traffic from every tile downstream, while a knob got the fast one. Swapped in [comms](comms.md#revisit-the-piosm-allocation-was-built-on-a-wrong-assumption). Side effects: **F11 disappears from the design**, and the 2+2 rotation pairing dissolves because all four sides are now identical.
  - **what binds next is DMA channels, not SMs** - 8 PIO inter-tile + 4 submodule directions + RGB SPI + ADC is ~16 against 16 if everything is DMA'd. The low-rate links can be interrupt-driven.

so the verdict: **pins close (44/48), ADC closes (6/8), PIO SMs close (6/12).** everything fits on one chip with headroom in all three budgets. AND this clears the thing that was blocking [submodules](submodules.md), there's definitely room for the 4-corner connector, so i can go un-pause that page now >w<
