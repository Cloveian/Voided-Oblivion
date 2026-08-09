# Communications

## Identify

I need to figure out what communications need to happen between tiles, and what hardware is going to carry them.

### Relevant constraints/nice to haves:

**Must haves:**
- Sub-1ms latency (key press to USB HID report)
- 1000Hz polling rate
- N-key rollover (including full analog values for rapid-trigger)
- USB Type-C wired connectivity (on whichever tile is master)

**From the architecture:**
- Up to 4 neighbors per tile (one per side)
- RP2350B PIO handles the inter-tile bus physical layer (decided in [controller](controller.md))
- One tile is master - the one with the active USB host connection
- Comms has to span the whole board regardless of how HV is partitioned (noted in [power](power.md))
- Tiles can be hotplugged into a running system
- Tiles need to know which of their sides have a neighbor

### What actually needs to be communicated

**Time-critical (has to fit in the 1ms scan window):**
- Key scan data: every tile's ~30 keys, full 12-bit ADC values for rapid-trigger, at 1000Hz

**Upstream (tile → master, not time-critical):**
- Topology: which tiles exist and which of their sides are connected
- Dynamic join: new tile announces itself, gets a position assigned, gets HV enabled
- PD results: cabled tiles tell master how much power they negotiated
- Submodule events: tile tells master when a submodule connects/disconnects so HID descriptors can be updated

**Downstream (master → tile, not time-critical):**
- HV enable/disable: master controls each tile's 4 per-side HV switches (noted in [power](power.md))
- RGB frame data: master sends LED state to each tile (~30 LEDs × 3–4 bytes)
- Power cap: master tells tiles how bright their RGB can be based on the negotiated power budget

## Brainstorm

### The latency problem

Key scan is the demanding one. Rapid-trigger needs full 12-bit ADC values per key, not just pressed/not pressed, so every scan has to send actual analog data. Worst case is a linear chain of tiles where each hop adds delay:

- 30 keys × 2 bytes (12-bit packed) = 60 bytes per tile per scan
- 5-tile chain: tile 5 → tile 4 → ... → master, so the farthest tile's data goes through 4 hops
- 60 bytes × 8 bits = 480 bits, at 4 Mbaud that's 0.12ms/hop × 4 hops = 0.48ms just in wire time
- plus framing, forwarding time, and USB report time
- leaves ~0.3–0.4ms for everything else in the 1ms window - tight but doable

So the target is **≥4 Mbaud**. PIO can do this easily, and it gives ~40% headroom over the bare minimum for framing and overhead.

Also: almost all keys are not being pressed at any given moment, so delta encoding (only send what changed) drops the average bandwidth way down. The 4 Mbaud sizing is worst case, normal use will be much lighter.

### PIO state machine budget

The RP2350B has 12 PIO state machines. The naive count of what i need:

| Use | SMs |
| --- | :---: |
| Inter-tile Tx (1 per side × 4 sides) | 4 |
| Inter-tile Rx (1 per side × 4 sides) | 4 |
| Submodule Tx (1 per corner × 4 corners) | 4 |
| Submodule Rx (1 per corner × 4 corners) | 4 |
| RGB | 1 |
| **Naive total** | **17** |

17 > 12, so i need to claw some back.

**Inter-tile stays at 8:** the relay path is time-critical and all 4 sides can be active at the same time (receiving from two neighbors while forwarding to two others). Can't mux these.

**RP2350B has 2 hardware UARTs** that don't use PIO SMs. Those can cover 2 of the 4 inter-tile sides, saving 4 SMs.

**Submodule can be muxed:** submodule traffic is async and slow. Two submodules firing at literally the same millisecond is pretty unlikely, and even if it happens the RP2350B can queue them. 1 Tx SM + 1 Rx SM GPIO-muxed across all 4 corner pins saves 6 SMs.

**SK9822 RGB runs off hardware SPI** (clock + data), so it doesn't need a PIO SM at all. SK6812 (single-wire, timing-critical) would need 1 SM - this is a nudge toward SK9822 from the PIO budget side, feeding back into the [RGB decision](rgb.md) that's still open.

With SK9822 + hardware UARTs on 2 inter-tile sides, two options:

**Option A: SW-muxed submodule (one active at a time)**

| Use | SMs |
| --- | :---: |
| Inter-tile Tx via PIO (2 sides) | 2 |
| Inter-tile Rx via PIO (2 sides) | 2 |
| Inter-tile via hardware UART0 + UART1 (2 sides) | 0 |
| Submodule Tx (SW-muxed across all 4 corners) | 1 |
| Submodule Rx (SW-muxed across all 4 corners) | 1 |
| RGB via hardware SPI | 0 |
| **Total** | **6** |

6 spare SMs. Two submodules trying to talk at the same time get queued in firmware, adds microseconds of latency, probably unnoticeable.

**Option B: Independent submodule SMs (all 4 corners truly parallel)**

| Use | SMs |
| --- | :---: |
| Inter-tile Tx via PIO (2 sides) | 2 |
| Inter-tile Rx via PIO (2 sides) | 2 |
| Inter-tile via hardware UART0 + UART1 (2 sides) | 0 |
| Submodule Tx (1 per corner × 4) | 4 |
| Submodule Rx (1 per corner × 4) | 4 |
| RGB via hardware SPI | 0 |
| **Total** | **12** |

0 spare SMs. All 4 corners can talk simultaneously with no queuing, but there's zero headroom left for anything i haven't thought of.

Both options require SK9822. SK6812 pushes Option B to 13 (over budget) and leaves Option A with only 5 spare.

Decision between A and B deferred to [Select](#select).

### Which sides get the hardware UARTs?

The hardware UARTs cover 2 of the 4 sides. The question is which 2, because the primary relay direction (where most traffic flows toward master) changes depending on how the tiles are arranged.

**Option 1: Left/right (side-to-side)**
Best for landscape configs where tiles are arranged horizontally in a row, which is probably the most common setup.

**Option 2: Top/bottom (up/down)**
Best for portrait/stacked configs, like a numpad tile sitting above or below the main tile.

**Option 3: Firmware-assigned at runtime**
The RP2350B's IO mux can route UART0 and UART1 to different GPIO pins. Checked against the datasheet pin mux table: UART TX/RX functions are available on virtually every GPIO pin (either F1 or F11), covering 12 pins each across the full GPIO range. With only 8 GPIO needed for inter-tile connectors (4 sides × Tx + Rx), there's no problem picking all 8 from UART-capable pins. **Firmware-assigned is confirmed feasible** - PCB routing just needs to keep it in mind, not work around it.
### Physical layer options

**A: Full-duplex UART per side**
Standard UART, PIO implementation is well-documented and trivial. Full-duplex means a tile can receive from one neighbor while transmitting to another at the same time, which is important for relay. 2 wires per side (Tx + Rx).

**B: Half-duplex single-wire per side**
1 SM per side instead of 2, cuts the wire count in half. But a tile can't receive and transmit on the same side simultaneously, so collision avoidance gets fiddly, especially at 4 Mbaud. Saves wires but complicates everything else.

**C: Differential pair (RS-485) per side**
Better noise immunity against the switching supplies and RGB. But needs a transceiver IC per side (×4 per tile), adds cost and parts. The traces are short (PCB to PCB across a connector), so single-ended is probably fine.

**D: Shared bus (I²C or similar)**
2 wires total, multi-master capable. I²C maxes out at 1MHz in fast mode+, way below the 4 Mbaud target. Also doesn't handle dynamic topology well.

### Dual USB-C ports

The keyboard needs to work with the cable coming from different directions depending on how it's oriented. Two USB-C ports: one on a horizontal edge and one on a vertical edge - that way a 90° rotation always puts a usable port in reach. Two ports on opposite ends would only handle 180° flips, which isn't the point.

**What i need:**
- Either port works as the USB data connection
- Both ports can supply PD power independently
- Both plugged in at once: safe, and i don't even care if it keeps working (it's fine if it does)

**Minimal implementation - just a USB mux:**
A USB 2.0 2:1 mux IC (e.g. TS3USB30 or FSUSB42, ~$0.40) between both ports' D+/D− and the RP2350B's USB data pins. VBUS from port A drives the select pin through a simple resistor/transistor: A has VBUS → route A, otherwise route B. Both plugged in → A wins, keyboard just works on A. No complex detection logic needed.

The D+/D− lines are low-voltage differential, the mux handles both inputs safely. VBUS from both ports simultaneously is already covered by the backfeed protection in [power](power.md).

**Second FUSB302:** if the secondary port needs full PD negotiation (not just 5V), it needs its own FUSB302. If 5V-only (~4.5W max) is acceptable on the secondary port, i can skip it - then it's literally just a connector + mux.

**CC mux option (middle ground):** the D+/D− mux can be paired with a 2-channel analog switch on CC1 and CC2 as well. Same select signal drives both. The single FUSB302 then sees the CC lines of whichever port is selected → full PD negotiation on the active port, no second FUSB302 needed. The non-selected port's CC lines float (or weakly pulled down through the switch), so it can't negotiate PD and stays at 5V. This also handles the "both plugged in" safety concern at the hardware level - only one port can ever negotiate at a time, the other is physically disconnected from the negotiation IC.

**"Both plugged in" risk:** if neither port's VBUS is isolated from the other at the backfeed protection level (covered in [power](power.md)), and one port negotiates to 20V while the other is at 5V, that's a problem. With CC mux this can't happen - the non-selected port is stuck at 5V because it can't negotiate. With two FUSB302s, firmware has to coordinate so they don't both try to negotiate simultaneously, which is a software correctness assumption i'd rather not rely on.

**Cost:**
- D+/D− mux only (5V-only on secondary): ~$0.40/tile extra
- D+/D− mux + CC mux (full PD on selected port, single FUSB302): ~$0.65/tile extra
- D+/D− mux + second FUSB302 (fully independent PD on both): ~$1.00/tile extra

### Master election

The master is whichever tile has an active USB host connection - not just PD power, but an actual data connection where the host has enumerated it. The RP2350B knows if it's been enumerated as a USB device.

Simple rule: **enumerated USB device = master.**

Edge cases:
- No USB cable: can't function as a keyboard anyway. Tiles can still boot and talk to each other, useful for testing/debugging.
- Multiple cables across different tiles: only one tile enumerates as a USB device. PD-only cables on other tiles don't enumerate, no conflict.
- Both ports on the same tile plugged in: mux routes port A → tile enumerates on A, works fine.
- USB cable moved to a different tile: easiest thing is to reboot the new master tile, it re-enumerates, the other tiles detect the old master is gone and re-discover.

### Topology discovery

At boot (or after hotplug), a tile doesn't know which of its sides have a live neighbor.

**Neighbor detection:** pull-down on the Rx line. If a neighbor is there, its Tx drives Rx high. If not, Rx sits low. Passive and costs nothing.

**Discovery sequence:**
1. tile boots on bootstrap
2. checks which sides have a live Rx signal (neighbor present)
3. sends HELLO on all live sides
4. neighbor responds with its own HELLO + which side it sees you on
5. repeats until master has the full adjacency graph
6. master assigns (row, col) coordinates by BFS from (0,0)
7. master broadcasts the layout so everyone knows where they are

Dynamic join (hotplug):
- new tile connects → gets bootstrap 5V + comms from neighbor → boots → sends HELLO
- neighbor forwards to master
- master runs the same discovery for the new tile, assigns it a position
- master enables HV to that side

### Protocol structure

Two classes of messages:

**Scan frame (time-critical, 1000Hz):**
Every tile sends one every 1ms. Contains key index + ADC value for every key that changed since the last scan. Master assembles the full keyboard state and generates the USB HID report.

**Control messages (async, lower priority):**
- HELLO / topology
- PD status
- HV enable / disable
- RGB frame
- Power cap
- Submodule connect / disconnect

Scan frames get priority. Control messages ride in gaps or get a reserved slot at the end of each 1ms window.

## Select

### Physical layer

| Criteria | Weight | Full-duplex UART | Half-duplex | RS-485 | I²C |
| --- | :---: | :---: | :---: | :---: | :---: |
| Meets ≥4 Mbaud | 10 | 10 | 7 | 10 | 1 |
| Full-duplex relay (receive + transmit simultaneously) | 9 | 10 | 2 | 10 | 6 |
| PIO SM cost (higher = cheaper) | 7 | 6 | 8 | 4 | 9 |
| Wire count (higher = fewer wires) | 5 | 6 | 9 | 4 | 8 |
| Noise immunity | 4 | 5 | 5 | 10 | 5 |
| Implementation simplicity | 6 | 8 | 5 | 4 | 7 |
| **Weighted total** | | **330** | 239 | 302 | 229 |
I already kinda knew this

---

### Submodule State Machine allocation

| Criteria                     | Weight | SW-muxed, 6 spare | independent, 0 spare |
| ---------------------------- | :----: | :---------------: | :------------------: |
| Spare SM headroom            |   8    |        10         |          1           |
| Simultaneous submodule comms |   5    |         3         |          10          |
| Implementation simplicity    |   7    |         5         |          8           |
| Future flexibility           |   8    |         9         |          1           |
| **Weighted total**           |        |      **202**      |         122          |

---

### Which sides get the hardware UARTs

90% of the time there will only be one row with x modules in a full keyboard setup, personally i would have the modules in portrait (which as of now is the 'default' position) and have 3 or 4 of them so i would want it on the 'left/right' as those would be the only sides connected, but if i were to go 'portable' then i would probably use 2 modules in landscape for a smaller keyboard.

The three options from the brainstorm:

| Criteria | Weight | Left/Right fixed | Top/Bottom fixed | Firmware-assigned |
| --- | :---: | :---: | :---: | :---: |
| Handles portrait (most common config) | 9 | 10 | 3 | 10 |
| Handles landscape / 90° rotation | 8 | 3 | 10 | 10 |
| PCB routing complexity (simpler = higher) | 5 | 8 | 8 | 8 |
| Firmware complexity (simpler = higher) | 6 | 9 | 9 | 6 |
| Flexibility for unusual configs | 4 | 3 | 3 | 10 |
| **Weighted total** | | 220 | 213 | **286** |

PCB routing complexity is the same across all three because the pin mux analysis confirmed UART TX/RX is available on virtually every GPIO - making all 4 sides UART-capable costs nothing extra on the PCB.

**Rotation pairing constraint (PCB layout note):**
For 90° rotation to work, the UART assignment has to survive the tile being turned. The two diagonal pairs need to share hardware resources:
- **Top + Left** → UART0 + PIO SM set A
- **Bottom + Right** → UART1 + PIO SM set B

When a tile is rotated 90°, "left" becomes "top" (or vice versa) - but it's still on UART0, so the same firmware path handles it. PCB routing just needs to make sure top_Tx and left_Tx are both UART0-TX-capable GPIO, and bottom_Tx and right_Tx are both UART1-TX-capable GPIO (same for Rx). Given the pin mux coverage this is trivial to satisfy.

Firmware then assigns the UART to whichever side in the pair actually has a live neighbor after topology discovery, and uses a PIO SM for the other.

---

### Dual USB-C ports

| Criteria                             | Weight | No dual ports | Dual, 5V-only secondary | Dual, CC mux (single FUSB302) | Dual, 2× FUSB302 |
| ------------------------------------ | :----: | :-----------: | :---------------------: | :---------------------------: | :--------------: |
| 90° rotation convenience             |   9    |       1       |            6            |              10               |        10        |
| Cost per tile                        |   8    |      10       |            8            |               7               |         5        |
| Power availability on secondary port |   5    |       5       |            3            |               9               |        10        |
| PCB / BOM simplicity                 |   7    |      10       |            8            |               6               |         4        |
| Safe if both plugged in              |   7    |      10       |            8            |               9               |         4        |
| **Weighted total**                   |        |      254      |           245           |            **296**            |        236       |

> ⚠️ **REOPENED at schematic time** - the winning **CC-mux** option does **not survive cold-start**: the FUSB302's Rd (which a source must see before it applies VBUS) sits behind the mux, whose VDD isn't up at attach, so the source never sees Rd and never applies VBUS. This table scored steady-state behavior and missed the bring-up sequence. Re-selected below in [Revisit: PD/CC architecture](#revisit-pdcc-architecture-the-cc-mux-doesnt-survive-cold-start).

---

### Relay strategy

| Criteria | Weight | Store-and-forward | Cut-through |
| --- | :---: | :---: | :---: |
| Per-hop latency | 9 | 6 | 10 |
| Implementation simplicity | 8 | 9 | 7 |
| Works for ≤6 tile configs | 7 | 9 | 9 |
| Scales to larger configs | 5 | 5 | 9 |
| **Weighted total** | | 214 | **254** |
But now that i think about it, this is 99% firmware so i don't need to worry about it at the moment

## Revisit: actually, don't mux them

coming back to this after doing the [pin-budget](pin-budget.md) page, because that's where i had the whole picture. back in [Select](#select) i leaned Option A (SW-mux the submodules) on the weighted table, but i'm flipping to **Option B, independent SM per corner**.

the PIO tally if i DON'T mux:
- RGB on hardware SPI → **0 SMs**
- 2 inter-tile sides on the hardware UARTs → **0 SMs**
- 2 inter-tile sides on PIO → **4 SMs**
- submodules, 1 Tx + 1 Rx per corner × 4 → **8 SMs**
- **total: 12 of 12**

yeah that's the whole budget, 0 spare. but here's why i'm fine with it: not muxing is just *cheaper to build*. no GPIO-mux juggling, no firmware queueing logic, each corner is a dead-simple dedicated Tx/Rx pair. and i HAVE the PIO right now, nothing else is asking for those SMs, so why pay in firmware complexity to hoard state machines i'm not using?

and the safety net is that muxing is an easy "i need this for something else" lever. if future-me adds something that needs a couple SMs, collapsing the 4 submodule corners back down to 1 Tx + 1 Rx muxed frees up **6 SMs** instantly, and submodule traffic is slow/async so the queueing cost is microseconds nobody feels. so i'm not locking myself out of anything, i'm just spending the spare now because it's the simpler build and reclaiming it later is trivial.

**going with Option B (not muxed), 12/12.** mux is the escape hatch if i ever need the SMs back.

## Revisit: the PIO/SM allocation was built on a wrong assumption

### the assumption

[Which sides get the hardware UARTs](#which-sides-get-the-hardware-uarts) above, and the [12/12 SM allocation](#revisit-actually-dont-mux-them), both rest on something i never checked: **that the hardware UART is the better/faster path**, so it should go to the inter-tile sides where the relay traffic is, and the submodules can live on PIO.

That's backwards. Straight from the RP2350 datasheet, UART chapter:

> "Supports a maximum baud rate of **UARTCLK / 16** in UART mode (**7.8 Mbaud at 125MHz**)"

~9.4 Mbaud at 150MHz. A PIO UART at the standard 8 cycles/bit does **18.75 Mbaud** at the same clock - **roughly 2× the ceiling of the hardware peripheral.**

So the PL011 is the *slow* option, and the allocation had it capping the one path where bandwidth actually accumulates. Inter-tile links carry relayed traffic from **every tile downstream**; a submodule carries one encoder or one display. Putting the lower ceiling on the relay path and the higher one on a knob is exactly the wrong way round.

### what the hardware UART is actually good for

Not speed - **zero SM cost and a 32-byte FIFO.** That's a real advantage, it's just a *CPU-load* advantage, not a throughput one. Which means it belongs on the links that are low-rate and numerous, not the ones that are high-rate and few.

### the swap

Move the two hardware UARTs from the inter-tile sides to two submodule corners:

| | before | after |
| --- | --- | --- |
| RGB (HW SPI) | 0 SMs | 0 SMs |
| Inter-tile | 2 HW + 2 PIO = **4 SMs** | **4× PIO = 8 SMs** |
| Submodules | 4× PIO = **8 SMs** | **2 HW + 2 PIO = 4 SMs** |
| **Total** | **12 / 12** | **12 / 12** |

**The SM budget doesn't move at all.** It's a pure reallocation - which is why this is a correction rather than a trade.

### the pin constraint that decides *which* corners

Of GPIO22-29, only two pairs are TX/RX at F2:

| pins | F2 | F11 |
| --- | --- | --- |
| 22/23 | UART1 **CTS/RTS** | UART1 TX/RX |
| **24/25** | **UART1 TX/RX** ✓ | - |
| 26/27 | UART1 **CTS/RTS** | UART1 TX/RX |
| **28/29** | **UART0 TX/RX** ✓ | - |

And they're on *different* UARTs - one UART0, one UART1 - which is what makes running both at once possible. `22/23` and `26/27` are both UART1, so they could never have been paired with each other anyway.

**So: hardware corners on GPIO24/25 (UART1) and GPIO28/29 (UART0); the other two corners on PIO.**

### two things that fall out for free

**F11 disappears from the entire design.** PIO functions (F6/F7/F8) are uniform across every GPIO, so all-PIO inter-tile has no per-pin special case, and the two hardware corners use F2. The "the Right side needs function 11 where the other three need function 2" firmware gotcha simply stops existing.

**The rotation pairing dissolves for inter-tile.** [Which sides get the hardware UARTs](#which-sides-get-the-hardware-uarts) picked firmware-assignment (286) and the pins were then paired 2+2 across opposing axes so either orientation had both active sides on hardware. With all four sides on PIO they're **identical** - no assignment to make, no pairing constraint, no runtime handover. The decision was right for its premise; the premise is gone, and what replaces it is simpler.

It also means the inter-tile pins no longer need to be UART-capable at all. Leaving them where they are (GPIO4/5, 6/7, 12/13, 16/17) since there's no reason to churn them, but that constraint is off the table for any future reshuffle.

### what binds next

Not SMs - **DMA channels.** Eight PIO inter-tile SMs, plus four submodule directions, plus RGB SPI and the ADC is ~16 against RP2350's 16 if every link is DMA'd. It doesn't have to be; the low-rate links are fine interrupt-driven. But that's the budget to watch now, not state machines.

## Revisit: PD/CC architecture (the CC-mux doesn't survive cold start)

came back to this hard at schematic time. a second review pass aimed at cold-start bring-up (see [implementation](../schematic-design/implementation.md#snags-round-2---cold-start-bring-up-a-second-review-pass-caught-these) snag 3) found the CC-mux is a non-starter. re-picking.

### why the mux is dead
**the tile has no power of its own** - it's a pure bus-powered sink, BS+ has nothing behind it, so at cold attach there is *literally no voltage anywhere* on it. the only way anything powers up is: a USB-C source sees **Rd** on the connector's CC pin and decides to apply VBUS. so that Rd has to be present **passively**, before a single rail comes alive.

the CC-mux put the FUSB302's Rd on the far side of the TMUX1574, whose VDD is BS+ (= 0 at attach). so the mux is open, the connector CC floats, the source never sees Rd, never applies VBUS → no BS+ → mux never powers. chicken-and-egg, permanent - and with nothing to pre-power the tile, there's no way to sidestep it. it just bricks.

### the new hard gate
the Rd must reach **each connector passively** at cold start, before anything on the tile has power. anything active (a mux, a switch) in the CC path fails the gate → the CC-mux is out.

### the core constraint
one FUSB302 has **2 CC pins**. two orientation-independent **receptacle** ports need **4** (both CC1/CC2 per port, for either plug orientation). so one PHY can't fully serve both ports - something gives.

### options
- **A - 5V-only secondary (1 FUSB302).** FUSB302 CC1/CC2 wired *straight* to port 1's two CC pins → full PD + orientation + passive Rd on port 1. port 2 gets a passive **5.1k Rd** on each CC pin → always-present Rd + **5V at up to 3A (15W)** by Type-C current advertising (no PD). the mux drops to 2 channels (D+/D- only). cheapest, simplest firmware (1 PD stack), smallest area, inherently safe if both plugged (port 2 can't negotiate). cost: rotate so port 2 faces you and you lose high-voltage PD in that orientation.
- **B - 2× FUSB302 (one per port).** each port its own PHY, CC direct → both ports full PD + orientation + passive Rd, symmetric in any rotation. two I²C **address variants** (FUSB302B / B01 / B10 / B11) share one bus, no I²C mux. matches the "any port can power the array" goal. cost: ~$0.60-1.20 more per tile *on every tile* (any tile can be the cabled one), 2 PD state machines in firmware, more board area. "both plugged" wants firmware coordination, though the backfeed diodes make it safe regardless (higher voltage wins the OR).
- **D - drop dual ports (1 port).** one USB-C, one FUSB302, direct. full PD + passive Rd, dead simple, no data mux. but it throws away the rotation cable-reach that was the whole reason for two ports - so it's really only on the table if i drop that goal.

### select

| Criteria                        | Weight | A: 5V-only 2nd | B: 2× FUSB302 | D: single port |
| ------------------------------- | :----: | :------------: | :-----------: | :------------: |
| Cold-start                      |  gate  |      pass      |     pass      |      pass      |
| Can use in both orientations    |   9    |       10       |      10       |       0        |
| Full PD where you plug          |   8    |       1        |      10       |       8        |
| Cost / tile (×N tiles)          |   4    |       8        |       5       |       10       |
| Firmware simplicity             |   2    |       5        |       2       |       5        |
| Board area                      |   6    |       8        |       4       |       10       |
| Safe if both plugged            |   7    |       8        |       8       |       10       |
| Matches "any port powers array" |   9    |       1        |      10       |       3        |
| **Weighted total**              |        |    **253**     |    **364**    |    **271**     |

**B 364 > D 271 > A 253** (out of 450, so 81% / 60% / 56%). B wins.

why: B is the only option that scores top marks on *both* of the heavily-weighted rows - usable in both orientations (9) AND any-port-powers-the-array (9).
- **D** eats a 0 on both-orientations (one port can't reach after a 90° turn), so all its cost/simplicity wins can't dig out of that hole.
- **A** does both orientations fine but face-plants on any-port-powers-array (a 5V-only secondary can't inject PD), so it lands last.

**Winner: B - 2× FUSB302, one per port, CC direct.** both ports get full PD + orientation + passive Rd, symmetric in any rotation, and any port on any tile can inject PD into the region. it costs ~$1/tile and a second PD stack in firmware, but the two things i weighted highest both demand it, and everything else (cost, board area, firmware) i'd already decided i care less about.

(D+/D- still gets a 2:1 mux either way - that didn't change. what changed is CC comes *out* of the mux entirely, and Rd sits passively right at each connector.)

**locked: B (2× FUSB302).** what changes downstream:
- [chips](../chips.md): add a **2nd FUSB302** (an address-variant so both share I²C), and the **TMUX1574 drops to a 2-channel data-only mux** (D+/D- - CC comes out of it entirely).
- each port: FUSB302 CC1/CC2 wired **direct** to that port's two CC pins, so passive Rd is right at the connector (fixes the cold-start snag).
- firmware: two PD state machines; the backfeed diodes keep "both plugged" safe regardless (higher voltage wins the OR), coordination is a nicety not a safety.

if reading by stream of consciousness go back to [index](../index.md)