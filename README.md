# Voided Oblivion

**An infinitely\* tileable analog hall-effect keyboard.** Identical 5×6 ortholinear tiles that
snap together edge to edge in any arrangement, two tiles for a 60%, three for an 80%, four for
full size. Each tile is a complete unit with its own RP2350B, dual USB-C PD ports, and power
system.

Designed by **Clover**

![Voided Oblivion, top](docs/images/rev-1-top.png)
![Voided Oblivion, bottom](docs/images/rev-1-bottom.png)

**Status: design complete, ordering boards.**

<sub>\* not actually infinite. one PD port runs about four tiles, after that you need more
ports - see [power](docs/design-choices/power.md).</sub>

---

## At a glance

|                 |                                                                                     |
| --------------- | ----------------------------------------------------------------------------------- |
| **Board**       | 4-layer, ~425 components, 242 nets                                                  |
| **MCU**         | RP2350B, 44/48 GPIO, 6/8 ADC, 12/12 PIO state machines                              |
| **Dual USB**    | 2 USB-C ports for ease of use when rotating the module(s) 90°                       |
| **Power**       | FUSB302 PD port(s), TPS54302 bucks, comparator-based VBUS→PD/BS handoff             |
| **Sensing**     | Analog hall effect, 74HC4067 muxes into the ADC, 30 keys/tile                       |
| **Performance** | 1000 Hz polling, sub-1 ms latency, rapid trigger (in theory)                        |
| **Effort**      | 100 hours across 40 days, June–August 2026                                          |

---

## The parts i find most interesting/difficult

**Stupid people ~~proofing~~ resistanting.** *so* many things would have been so much easier if
i were just designing this for myself, but i'm not. i had to think of random scenarios like
*'what if someone plugs both USBs in at the same time?'*, i had to add protection circuits for
that. 'what if someone wanted to put 64 of them together?' (ok that one i would do if i had that
many >w<) and minimizing the damage that a short between the outer pogo pins can do, and several
other random things that i would just think 'i wont do that'

**Power system.** this project uses USB power delivery for 2 main reasons. non PD is not enough
power for more than like 1 tile (with rgb) and with PD i can run a higher voltage across the
whole network without worrying about voltage drop. But PD comes with its problems, the switch
from 5v to higher voltages, i designed a comparator based system so all the power routing would
happen with hardware so a firmware mistake ~~wouldn't~~ couldn't fry anything.
→ [power](docs/schematic-design/power.md)

**Everything budgeted onto one MCU.** 44 of 48 GPIO, 6 of 8 ADC channels, 12 of 12 PIO state
machines. The interesting thing is that PIO uart is faster than hardware uart.
→ [pin budget](docs/design-choices/pin-budget.md)

---

## What's in here

| | |
| --- | --- |
| [`Voided-Oblivion/`](Voided-Oblivion/) | the KiCad 10 project - schematic, PCB, and the JLCPCB gerber/drill output |
| [`docs/`](docs/) | the design documentation, written while designing. an MkDocs site, but readable as plain markdown on GitHub |
| [`layouts/`](layouts/) | keymaps in [keyboard-layout-editor](http://www.keyboard-layout-editor.com/) JSON, from 60% up to the silly ones |
| [`scripts/`](scripts/) | tooling for the layouts and docs - deriving one arrangement from another, image-to-keymap, etc |
| [`graphics/`](graphics/) | silkscreen art |

Datasheets aren't in the repo - they're manufacturer PDFs i don't own, and it was 129MB of them.
[`docs/datasheets.md`](docs/datasheets.md) indexes every part and where to get its datasheet.
`old/` (the first attempt) is out of the working tree but still in git history.

## Reading the docs

Start at [`docs/index.md`](docs/index.md). These are working engineering documents written
during the design process, not a writeup made afterwards, so **incorrect reasoning is kept**
rather than deleted, with a link to whatever replaced it. That's deliberate - the point is
remembering *why* something changed.

- **what got designed** - [chip list](docs/chips.md) · [schematic calcs](docs/schematic-design/index.md) · [layout checklist](docs/layout-checklist.md)
- **why the chosen features** - [design decisions](docs/design-choices/index.md) · [goals and constraints](docs/goals.md)
- **how it was checked** - [design reviews](docs/schematic-review-2026-08-08.md) · [datasheet research](docs/research/README.md)

To read them as a site locally, with working cross-links and the superseded-block styling:

```sh
./preview.py
```

That builds a venv, checks every cross-link, and serves on the first free port from 8001.

## Licence

[CC BY-NC-SA 4.0](LICENSE.md), with the NonCommercial term relaxed so it only catches people
actually making money. Build it, modify it, fork it, publish your changes - just credit it and
share alike.

The carve-outs, in full in [LICENSE.md](LICENSE.md):

- **Under US$1,000/year in revenue, sell freely.** No permission needed, nothing owed. The
  NonCommercial term exists to stop a company mass-producing this, not to stop you selling a few
  boards.
- **Over that, open an issue** and we'll work out a percentage. Expect a conversation, not a no.
- **The inter-tile connector interface is public domain** - pinout, pitch, gender rule, protocol.
  Submodules and accessories that mate with a tile are entirely yours to sell, commercially,
  without asking.

## On LLM use

i used LLMs while working on this, and i'd rather say so than have someone guess.

**what they did:** the [datasheet research pages](docs/research/README.md) were written by agents
that were handed a datasheet and the role a chip had to play, and *deliberately not shown my
schematic*, so their conclusions could be diffed against what i'd actually drawn. same idea for
the [review passes](docs/electrical-review-2026-08-20.md) - a second set of eyes that doesn't get
tired. they also helped with editing the docs, and wrote some of the tooling in `scripts/`.

**what they didn't do:** every idea, every design decision, the whole modular architecture, the
trade studies, the schematic, and the layout are mine. every value in
[schematic-design](docs/schematic-design/index.md) is one i derived and can defend. when the
research disagreed with the board, i checked which one was wrong - sometimes it was me, and
sometimes the [research was backwards](docs/chips.md) and would have meant a switch that never
turns on. deciding which is which is the actual work, and it isn't something you can hand off.

worth saying plainly: the blind review pass was maybe 60% noise. it also caught a bug that made
the board 5V-only, which four sighted passes had missed. knowing which 40% to keep is the part
that took a year of learning this stuff.

also, and i say this as someone who has spent 100 hours in the same room as them: LLMs could not
have done this. they really, really suck at it. trust me, i would know.
