# Voided Oblivion

**A infinitely\* tillable analog hall-effect keyboard.** Identical 5×6 ortholinear tiles that snap
together edge to edge in any arrangement, two tiles for a 60%, three for an 80%, four
for full size. Each tile is a complete unit with its own RP2350B, dual USB-C PD ports,
and power system.

Designed by **Clover**

![Voided Oblivion front render](images/rev-1-top.png)
![Voided Oblivion front render](images/rev-1-bottom.png)


`Design complete - ordering boards`{.status .settled}

---

## At a glance

|                 |                                                                                                        |
| --------------- | ------------------------------------------------------------------------------------------------------ |
| **Board**       | 4-layer, ~425 components, 242 nets                                                                     |
| **MCU**         | RP2350B, 44/48 GPIO, 6/8 ADC, 12/12 PIO state machines, (i dunno if i am utilizing the chip enough :P) |
| **Dual USB**    | 2 USB-C ports for ease of use when rotating the module(s) 90°                                         |
| **Power**       | FUSB302 PD port(s), TPS54302 bucks, comparator-based VBUS→PD/BS handoff                                |
| **Sensing**     | Analog hall effect, 74HC4067 muxes into the ADC, 30 keys/tile                                          |
| **Performance** | 1000 Hz polling, sub-1 ms latency, rapid trigger (in theory)                                           |
| **Effort**      | 100 hours across 40 days, June–August 2026                                                             |

---

## The parts I find most interesting/difficult

**Stupid people ~~proofing~~ resistanting.** *so* many things would have been so much easier if i were just designing this for myself, but i'm not. i had to think of random scenarios like *'what if someone plugs both USBs in at the same time?'*, i had to add protection circuits for that. 'what if someone wanted to put 64 of them together?' (ok that one i would do if i had that many >w<) and minimizing the damage that a short between the outer pogo pins can do, and several other random things that i would just think 'i wont do that' 

**Power system** this project uses USB power delivery for 2 main reasons. non PD is not enough power for more than like 1 tile (with rgb) and with PD i can run a higher voltage across the whole network without worrying about voltage drop. But PD comes with its problems, the switch from 5v to higher voltages, i designed a comparator based system so all the power routing would happen with hardware so a firmware mistake ~~wouldn't~~ couldn't fry anything
[→ Power](schematic-design/power.md)

**Everything budgeted onto one MCU.** 44 of 48 GPIO, 6 of 8 ADC channels, 12 of 12 PIO
state machines. The interesting thing is that PIO uart is faster than hardware uart.
[→ Pin budget](design-choices/pin-budget.md)

---

## How to read this documentation

These are working engineering documents, they were written during the design process (how it should be), and i **keep incorrect reasoning**/assumptions to remember *why* something changed

A example of this is, a review pass caught the bootstrap rail collapsing at PD handoff; the fix was leaving the buck
permanently enabled and tied to VBUS instead of the PD rail (not always powered, only when above 5v) The original wrong reasoning is still on the power page, as it helps me not make the same mistake again if i drop the project for a while

- **What got designed:** [chip list](chips.md) · [schematic calcs](schematic-design/index.md) · [layout checklist](layout-checklist.md)
- **Why the chosen features:**  [design decisions](design-choices/index.md) · [goals and constraints](goals.md)

---