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

## Continue - pins exist, un-pausing

ok i did the [pin-budget](pin-budget.md) page and the thing i was waiting on is answered: there's room. so let me actually lock the submodule connector down.

### the connector
sticking with the 4-pin per-corner idea from up top: **5V, GND, Rx, Tx**, one connector at each of the 4 corners. the mirrored/rotatable pad layout i sketched stays (so a module drops in the same regardless of which corner / rotation).

pin budget says each corner gets its own dedicated Tx + Rx straight off the RP2350B:
- 4 corners × (Tx + Rx) = **8 GPIO**, assigned GPIO22–29 in the budget
- and per the [comms revisit](comms.md#revisit-actually-dont-mux-them) these are **not muxed** - every corner is an independent PIO Tx/Rx pair, so all 4 corners can talk at once with zero queueing. (if i ever need those SMs back, muxing is the easy lever, but for now they're independent.)
- 5V comes off the tile's big buck (the gated noisy rail), GND is the common reference. no per-corner power switching, the per-port current is small enough not to bother.

so each corner connector is dead simple: power + ground + a full-duplex UART. a submodule is just "has an MCU, speaks UART, pulls ≤300mA."

### power
already worked out above - reserve a **per-port allowance** (~300mA if displays/touch are in scope, way less for simple input modules), additive on top of the tile's own load, carried into [power](power.md). firmware does live estimation: a module announces what class it is when it connects, master adds it to the budget, and if there isn't headroom it trims elsewhere (RGB first).

### protocol (the firmware side, just noting it)
- module connects → sends a hello on its corner UART saying what it is
- tile forwards that upstream to master (it's the "submodule connect" event from the [comms](comms.md) upstream list)
- master updates the USB HID descriptors if it's a pointing device / adds it to the power budget
- disconnect detection falls out of the same Rx-idle / pulldown trick comms already uses for neighbor detection

### what's actually still open
- ~~**physical connector choice** - pin headers vs something keyed/magnetic vs pogo pins. this is a mechanical/enclosure call, not an electrical one, so it waits until i'm doing the case + board outline. the 4 signals don't change whatever i pick.~~ **closed**, see below
- everything electrical is settled. submodules are off the critical path now - i can design tiles without a single submodule existing, then add modules later against this fixed 4-pin contract.
  - > **superseded** - it's a **5-pin** contract now (`ID GND 5V Rx Tx`), revised while zero tiles and zero modules existed. See [revision](#revision-5-pins-not-4---adding-a-senseid-line).

so: **submodule connector = 4-pin (5V/GND/Rx/Tx) per corner, independent UART per corner, ~300mA/port budget.** un-paused and basically done, just the connector body to pick later. back to [index](../index.md)

## Picking the connector body - machined pin headers

### Identify
The 4 signals were never in question; this is purely mechanical. What the corner connector actually has to do:

| | requirement | why |
| --- | --- | --- |
| pins | 4 (5V, GND, Rx, Tx) | fixed by the contract above |
| orientation | **straight, above the board** | a submodule sits on top of the tile, not beside it - this is what rules out the edge-connector family entirely |
| mate cycles | **low** | *"it's not intended to constantly swap submodules"* - a module goes on and mostly stays |
| rotatable | mirrored pad layout | so a module drops into any corner the same way |
| current | ≤300mA/port | trivial for anything in this class |

That mate-cycle line is the one that decides it, and it's worth stating explicitly because it's the *opposite* of the [inter-tile edge connectors](module-connectors.md), where "people will reconfigure these a lot" is a stated constraint. Same project, opposite requirement, so they get different answers - that's not inconsistency.

### Brainstorm / what riskable said

Asked [riskable](https://github.com/riskable) since he's built a lot more of these than i have. Two things came back:

- **on pogo pins:** not favourable - but pogo was never a candidate here anyway. A submodule sits *on top of* the tile, so this connector is straight/vertical and the pogo family doesn't apply.
- **on headers: *"I just use my bog-standard dupont headers unless I know I'm going to be using some JST thing"*,** then on being shown machined pins: ***"Swiss/machine pin headers are awesome. Though, they wear out. Dupont headers never wear out."***

That last pair is the real tradeoff and it's a genuinely good observation:

| | stamped (Dupont) | machined (Swiss / turned pin) |
| --- | --- | --- |
| contact | flat stamped spring, 2 point contacts | full circumferential grip on a turned barrel |
| wear | **essentially never** | socket springs fatigue over many cycles |
| plating | usually tin | usually gold |
| profile | taller | lower |
| cost | pennies | a few × more |
| feel | loose-ish | positive, low insertion force |

### Select

**Machined pin headers.** riskable's objection is real and i'm not dismissing it - i'm saying it doesn't apply *here*, because the axis it attacks (wear over many cycles) is the axis this connector doesn't have. A submodule mounts and stays. Trading "never wears out" for better contact, gold plating and a lower stack is the right way round when the cycle count is in the tens, not the thousands.

If submodules turn out to be something people *do* swap constantly, this flips and stamped headers win. Recording that as the trigger to revisit rather than pretending it can't happen.

### The bit the conversation didn't cover: which side gets the socket

**Only the socket wears.** The machined pin is a solid turned barrel - it's the socket's internal spring fingers that fatigue. So which board carries which half is a real decision, not a coin flip:

| | wear lands on | downside |
| --- | --- | --- |
| socket on the **submodule**, pins on the tile | the cheap, replaceable part ✓ | four bare pins sticking up out of every unoccupied corner - pokey, bendable, and there are 4 corners × N tiles of them |
| **socket on the tile**, pins on the submodule | the expensive board (30 switches + an MCU) ✗ | none really, at this cycle count |

**Going with socket on the tile.** The wear argument only matters if the cycles are there to accumulate, and by the same logic that picked machined pins in the first place, they aren't. Meanwhile exposed pins on an empty corner of a keyboard you actually handle is a permanent, everyday annoyance. Optimising against a failure mode that needs thousands of cycles, at the cost of something that's wrong every single day, is the wrong trade.

### Result

- **Tile side: 4-pin machined (Swiss) socket strip**, 2.54mm pitch, straight/vertical, one per corner, mirrored pad layout so a module drops into any corner
- **Submodule side: matching 4-pin machined header**
- 5V / GND / Rx / Tx unchanged - the electrical contract from above is untouched
- **Revisit trigger:** if submodules become something that gets swapped constantly, stamped Dupont wins instead

Specific MPN + footprint still to pick at layout time, but the *class* is settled, which is what was blocking.

## Revision: 5 pins, not 4 - adding a sense/ID line

### Why reopen a "fixed" contract

The 4-pin contract above was sold as the thing that took submodules off the critical path: *"add modules later against this fixed 4-pin contract."* Changing it is only free **now**, while zero tiles and zero modules exist. So this is the moment.

What prompted it: **GPIO stopped being scarce.** Cutting the [per-side current sense](power.md#re-decision-does-this-need-per-edge-ocp-at-all) freed 4 ADC and 4 pins. With spare I/O, a dumb submodule - one with no MCU at all - becomes possible.

### The gap isn't pin count, it's detection

Worth being precise, because the obvious framing is wrong. **A dumb module already has two signal pins.** Tx and Rx are plain GPIO; if firmware knows there's no MCU on the other end it simply doesn't configure UART on them and uses them as digital I/O, PIO, PWM, whatever. Power, ground and two signals are already there.

What's missing is **detection**. The scheme above says disconnect detection *"falls out of the same Rx-idle / pulldown trick comms already uses"* - but that trick needs an MCU on the far end to drive Tx high. **A dumb module never drives anything, so it reads as absent forever.** That is the actual blocker, and one pin fixes it.

### The 5th pin: ID

One **ADC-capable** pin per corner (there are six free: GPIO42-47), doing three jobs:

| job | how |
| --- | --- |
| **presence** | tile pulls up; empty corner reads rail, occupied reads the module's divider |
| **identity** | one resistor in the module → firmware reads the class off the ADC. No MCU, no handshake, no protocol |
| **analog signal** | for a module that *is* a pot / slider / force sensor, this is the input |

A dumb module then gets 5V, GND, two digital and one analog/ID - enough for a rotary encoder plus an ID resistor, or a pot plus two buttons.

**One pin, not two.** Two per corner is 8 GPIO and leaves only 3 spare, and this project keeps discovering pins it wants.

**It works with the corner rail switched off.** The divider is pulled up from the tile's **+3V3** and returns through the module's resistor to GND - it never touches the corner 5V. So firmware can read what's plugged into a corner *before* deciding whether to power anything, and identification survives the rail being gated. That's strictly better than the Rx-idle trick, which needs the module powered and its MCU running before it can say anything. **Property, not accident** - worth designing around.

**Safety: the module is an untrusted external thing with 5V on it.** Pull up to **+3V3, not 5V**, so the tile side can't overdrive the pin, and put a **series ~10kΩ** between the connector and the GPIO so the RP2350's clamp diode survives a module that shorts ID to its own rail. Same reasoning as not putting submodules on BS+ - you can publish a contract, you can't enforce it.

### Pin order: `ID GND 5V Rx Tx` (clockwise)

Corner connectors **don't self-mate** - a corner meets a *submodule*, not another tile - so unlike the [edge connectors](module-connectors.md) there's no palindrome to satisfy. Only the rotational rule from the sketch above: every corner reads the same sequence traversed clockwise.

Four things actually constrain the order:

1. **5V must not be at either end.** This is a hand-inserted header; if a module goes in one position off, a 5V pin at an end lands on a module *signal* pin. Interior positions can only ever meet their neighbours.
2. **ID wants a quiet neighbour** - it's a high-impedance analog line into an ADC.
3. **5V and GND adjacent** keeps the module's decoupling loop short.
4. **GND near the UART pair** for a return reference.

| pos | pin | why |
| --- | --- | --- |
| 1 | **ID** | end - one open side, and its only neighbour is GND, the quietest pin on the connector |
| 2 | **GND** | adjacent to ID (analog reference) *and* to 5V |
| 3 | **5V** | interior, so a misaligned module can't land it on a signal pin |
| 4 | **Rx** | |
| 5 | **Tx** | end - a signal, not power |

**Prepend, don't append.** The intuitive `5V GND Rx Tx ID` is worse on two counts at once: it puts the analog pin next to Tx (the switching line) *and* moves 5V to an end position. Prepending keeps the existing four in exactly the order already sketched and fixes both.

> **Corrected mid-decision:** I first put ID next to 5V, reasoning that 5V is a quiet DC rail. **It isn't** - corner power is +5VP, the gated big buck, sharing L3's 0.938A p-p of ripple with 30 RGB LEDs. The conclusion "ID next to 5V beats ID next to Tx" still holds, because crosstalk is dV/dt-driven and a 3.3V digital edge is orders of magnitude worse than tens of mV at 400kHz - but GND is the better neighbour, so ID moved. Honestly both orderings are within noise of each other; this one is just more defensible.

**The real noise path is the GND pin, not the 5V pin** - up to 300mA of module return current through one 2.54mm contact shifts the module's ground relative to the tile's, and that appears directly in whatever the ADC reads. Pin order doesn't fix it. Negligible for a read-once ID, a small accuracy floor for a continuous pot.

**Don't rely on ordering to survive misinsertion - solve it mechanically.** Ordering only limits the damage; a keyed shroud, an asymmetric mounting hole, or a module outline that only fits one way makes it impossible. Machined headers come shrouded/keyed.

## Corner power: dual-sourced so submodules work without PD

> **The first version of this section got the decision wrong, and the wrong version is kept below** because the *way* it was wrong is the useful part.

### Identify - and the mistake

Should the corner 5V be switchable, and should it come from BS+ so submodules work on a **5V-only source**? That case is real: Type-C lets a source advertise **3A at 5V through Rp alone**, with no PD at all, which is common on motherboards.

**Submodules working without PD is a requirement, not a preference.** That's the thing I originally missed. I scored it as one weighted criterion among eight, concluded that "one switch on +5VP, no second source" won 399/510, and even ran a sensitivity analysis showing no weighting could flip it.

**A requirement is a gate, not a scoring row.** You filter candidates on it and score whatever survives. Options A and A2 both fail the gate outright, so they were never candidates - and a matrix that lets a failing option *win* is answering a question nobody asked.

It also inverted the "B is dominated by C" finding. C only beat B because it *also* delivered RGB-without-PD - and that's explicitly unwanted (asked riskable directly: *"No. What's the point if you can't blind someone with it?"*). Strip out a benefit you don't want and C's lead evaporates, while its costs don't: it touches the RGB rail, drags the level shifter's VCCB along with it, and re-couples RGB gating to the shared rail.

### Select - apply the gate

| | option | passes the gate? |
| --- | --- | --- |
| A | status quo, both straight off +5VP | ✗ |
| A2 | one switch on +5VP, no second source | ✗ |
| **B** | **`SM+` dual-sourced from +5VP ∥ BS+** | **✓** |
| C | shared rail dual-sourced, RGB included | ✓ - but buys an unwanted feature at extra cost |
| D | separate `SM+` and `+5VLED`, each dual-sourced | ✓ - 4 switches, and half of it unwanted |

**B.** Only three options clear the gate, and of those it's the only one that doesn't also deliver something explicitly rejected.

### Result - the topology

```
BS+  ──► U12  AP2171W  (EN = SM BS EN) ──┐
                                          ├──► SM_BUS ──► U16 AP2171W ──► SM+ ──► 4 corners
+5VP ──► U15  LM66100  (CE→VOUT, RCB) ───┘                (EN = SM EN)
```

| ref | part | role |
| --- | --- | --- |
| **U12** | AP2171WG-7 (C110466) | BS+ branch, firmware-gated. 1A limit, OCP/OTP |
| **U15** | LM66100DCKT (C2832141) | +5VP branch, always-on ideal diode with reverse blocking |
| **U16** | AP2171WG-7 (C110466) | group on/off + 1A limit + fault containment |

**No new BOM lines** - LM66100 is already U9, AP2171W is already the group switch.

### Why the +5VP branch is a diode, not a switch

**It has to block reverse current.** With a plain switch off and BS+ driving the bus, current flows back through it into the disabled big buck's output, down L3 to the SW node, and out through the high-side FET's body diode into PD+ - **the same path U9 exists to block, one buck over.**

An ideal diode does that with **no GPIO and no firmware**, and the usual objection doesn't apply: the auto-OR ambiguity between two ~5V rails only exists *post*-PD, where +5VP is meant to win anyway. **Pre-PD, +5VP is genuinely at 0V** because the big buck is off - not merely lower - so there is nothing to arbitrate. That's what makes automatic safe here when it wouldn't be in general.

### Why U16 does need firmware control

Because **U15 has no enable**. Trace how you'd turn submodules off without U16's EN:

| state | feeding the bus | how to kill submodules |
| --- | --- | --- |
| pre-PD | U12 | turn off U12 ✓ |
| post-PD | U15 | turn off the **big buck** - which kills RGB too ✗ |

That reintroduces exactly the coupling this whole exercise was meant to remove. U16's EN is the independent gate; tie it high and U16 becomes a pure protection device.

**Unverified, and worth checking before fab:** whether AP2171W's OCP auto-retries or latches. Diodes' site bot-blocks the datasheet. If it latches, EN is the *only* way to clear a fault, and this stops being a convenience.

### What gets read, and what doesn't

Three open-drain outputs. Two were dropped:

| | reports | verdict |
| --- | --- | --- |
| U12 /FLG | fault on the BS+ branch | **dropped** - U12 and U16 are in **series at the same 1A**, so U16 sees the identical fault. Same event, reported twice |
| U15 ST | is +5VP feeding the bus | **dropped** - the same pre/post-PD distinction [`BS+ SRC`](../schematic-design/power.md#bs-src---what-the-status-pin-buys) already gives, and firmware knows GPIO14's own state |
| **U16 /FLG** | the submodule rail tripped | **kept**, routed to a GPIO |

U16's is kept because **the obvious inference just broke.** The ID pin already separates *absent* from *present* (it runs off +3V3 and works with SM+ dead). What it can't tell you is why an *installed* module is silent - and you'd normally infer "silent UART = faulted", except **MCU-less modules are now supported and a silent UART is their normal state.** So /FLG is the only direct signal that the rail actually tripped. Without it, a shorted module presents as "the knob stopped working" with no way to separate a tripped switch from a dead module from a firmware bug.

**An open-drain output nobody reads doesn't need a pull-up** - the two dropped pins get no-connect flags, not resistors.

### The enable pull-down rule

Both AP2171W enables need **4.7kΩ** to GND, not 100k, and not 0Ω.

RP2350-E9 sources **~120µA** into a floating input-enabled pad and parks it at **2.2V** - above the switch's EN threshold. So a mis-configured pin doesn't merely fail to disable the rail, it can actively **enable** it.

| R_pd | V at 120µA | |
| --- | --- | --- |
| 100k | clamps ~2.2V | rail turns **on** |
| **4.7k** | **0.56V** | off ✓ |

**Stating this as a general rule, since it's now the second instance:** *anywhere a default-low state is load-bearing on an RP2350 pin, the pull-down must be ≤8.2kΩ; 4.7k is the safe pick.* (First instance: the inter-tile Rx neighbour-detect pull-downs.)

### Current budget

The group is **1A in both states** - U12 and U16 are both 1A parts, so the cap is the same whether BS+ or +5VP is sourcing. Contract stays **≤300mA per port and ≤1A total**.

On a 5V-only source the *supply* is not the limit: a 3A Type-C port leaves ~2.7A after the LDO's ~300mA. On a 1.5A port it's ~1.2A, and on a 500mA legacy port ~200mA - and **the FUSB302 reads the Rp advertisement**, so firmware knows which it has before enabling U12.

### What it still doesn't buy

- **No submodules-alive-with-RGB-off in the post-PD case.** U15's source is +5VP, so gating the big buck kills the bus regardless. The RGB lever remains the SK9822's hardware global brightness (~500mA at level 10 vs ~1.9A unrestricted), not a rail gate.
- **No per-corner isolation.** One shorted module trips the shared limit and kills all four - the accepted trade for one enable instead of four.

### ~~Superseded: the original A2 decision~~

Kept for the record, because the failure mode is instructive. The matrix below scored "works on a 5V-only source" as **one weighted criterion among eight**, at weight 8, and produced a confident winner that fails the actual requirement - complete with a sensitivity analysis "proving" nothing could flip it. Everything in it is arithmetically correct and the conclusion is wrong, because the premise was.

| Criteria | Weight | A | A2 | B | C | D |
| --- | :---: | :---: | :---: | :---: | :---: | :---: |
| Board area | 9 | 10 | 9 | 6 | 6 | 2 |
| Works on a 5V-only source | 8 | 2 | 2 | 6 | 10 | 10 |
| GPIO cost | 6 | 10 | 9 | 6 | 6 | 3 |
| Design risk / new failure modes | 8 | 10 | 9 | 6 | 5 | 4 |
| Fault containment | 7 | 2 | 9 | 9 | 9 | 9 |
| Cost | 4 | 10 | 9 | 8 | 8 | 6 |
| Firmware complexity | 5 | 10 | 9 | 6 | 6 | 4 |
| Independent RGB / submodule control | 4 | 3 | 8 | 7 | 3 | 10 |
| **Weighted total** | | 362 | **399** | 339 | 347 | 295 |

**Lesson worth keeping: a weighted matrix can only compare options that already satisfy the requirements.** Anything mandatory belongs in a gate above the table, not as a row inside it.

### Revised contract

**Submodule connector = 5-pin `ID GND 5V Rx Tx` (clockwise), one per corner, independent UART per corner, ≤300mA/port and ≤1A total, dual-sourced from +5VP (via ideal diode) and BS+ (firmware-gated), group-switched by U16.** Works on a 5V-only source. Modules may be MCU-less; the ID resistor identifies them and works whether the corner rail is powered or not.

back to [index](../index.md)
