# Module Connectors

## Identify
I need to figure out the actual *physical* connector that mates one tile to its neighbor. the [pin-budget](pin-budget.md) and [comms](comms.md) pages decided what signals exist and which GPIO they live on, but nothing yet about the metal that bridges two tiles across an edge.

### what each edge connector has to carry
per side, between two neighboring tiles (from [power](power.md) + [comms](comms.md)):

| Net | what | rough current |
| --- | --- | --- |
| HV | negotiated PD rail, ~9–20V, per-side switched | up to ~4A (80% of 5A @ 20V) |
| Bootstrap | always-on shared 5V, boot + handshake | up to ~1.5A pre-PD |
| GND | common reference + return for both rails | sum of the above |
| Tx | inter-tile UART out | signal |
| Rx | inter-tile UART in | signal |

so the *minimum* is 5 nets, but HV and GND want more than one contact each to actually carry the current (most small contacts are ~1–2A apiece), so realistically **~6–8 contacts per edge**.

### constraints / nice-to-haves (the ones that actually shape this)
- **hotplug-safe**: the whole [power](power.md) scheme is built around mating a tile onto a *live* neighbor (bootstrap + comms live, HV on that edge off until master enables it). the connector has to make/break under power without arcing or shorting adjacent contacts
- **orientation rules (scoped down):** the supported moves are **180° flip of an individual tile** and **90° rotation of the *whole* keyboard as a unit**, NOT 90° of a single tile relative to its neighbors. since a tile is 5×6, that means **only same-length edges ever meet** (a 5un edge mates a 5un edge, a 6un edge mates a 6un edge), never a 5un against a 6un. so:
    - there are really **two edge connectors**: a short one (5un edges) and a long one (6un edges). each only ever mates its own kind.
    - within a kind, every edge still needs the **identical, self-mating connector + pinout**, and the pinout still has to be **symmetric** so a mirrored edge maps power→power and swaps Tx↔Rx (more below). the 180° flip is exactly a mirror, so the symmetry work covers it.
    - whole-keyboard 90° doesn't un-mate or re-mate anything (the whole array turns together), it just changes which USB-C port faces you, already handled by the dual-port thing in [comms](comms.md). so 90° costs the connector nothing.
    - (the hardware-UART side assignment over in [comms](comms.md) isn't an orientation thing, it's just optimizing which sides carry the most traffic toward master, so none of this touches it.)
- **self-aligning + retention**: tiles snap together and stay together; ideally the connector helps hold them
- **low profile**: it's a must-have for the whole board, so the connector can't be a tall stack
- **cheap**: ×4 edges × N tiles, this multiplies fast
- **durable / many mate cycles**: people will reconfigure these a lot

## Brainstorm

### the symmetry thing (this constrains every option)
when tile A's right edge butts against tile B's left edge, A's contacts meet B's contacts *mirrored*. so whatever order i put the nets in has to be a palindrome for power and swap for comms. something like:

```
edge pinout (8 contacts):   GND  HV  BOOT  Tx    Rx  BOOT  HV  GND
neighbor sees it reversed:  GND  HV  BOOT  Rx    Tx  BOOT  HV  GND
                                            └swap┘
```

power/ground land on themselves (palindrome), and Tx lands on the neighbor's Rx / vice-versa, which is exactly what a UART link wants. doubling HV and GND kills two birds: it makes the layout symmetric for free, AND it's the only way to get the current across at all. this pinout requirement applies no matter which connector type i pick, so i'm locking it in up front.

**current note:** with the gender split, each power net has 2 mating contacts (one pogo + one pad in parallel), so each carries half. HV ~4A = ~2A per contact. that's a non-issue, high-current pogos and spring-fingers rated 3–5A+ are cheap and common, so i just spec a contact rated for it. no extra contacts needed.

### connector type options

**A: pogo pins (spring-loaded) + flat pads**
one edge has pogo pins, the mating edge has gold flat pads. springy contacts tolerate a little misalignment and z-height variation, great for hotplug (wiping contact), no insertion force to speak of.
- + hotplug-friendly, self-cleaning wipe, tolerant of slop, low profile-ish
- + cheap-ish per pin
- − they wear, and they need *something else* (magnets?) for retention since they only push apart
- + self-mating is handled by the half-pogo/half-pad gender split (see below), so the usual "pins-on-one-edge-pads-on-the-other" headache doesn't apply here

**B: magnetic pogo (pogo + magnets for alignment & retention)**
same pogo contacts but with magnets doing self-alignment + holding the tiles together (think laptop magnetic chargers / a lot of modular gadgets). magnet polarity can also enforce correct orientation.
- + everything pogo has, plus retention + snap-together feel + self-alignment for free
- + polarity keying can physically prevent mating something backwards
- + inherits the same self-mating gender split as plain pogo, so no gender headache
- − magnets cost money and add a little height/weight, ×4 edges
- − magnets near the hall sensors?? need to check they don't mess with key sensing (the keys are literally magnetic hall switches). probably fine if far enough / shielded but FLAG THIS, it's the scary one

**C: board-to-board mezzanine / hirose-style**
precision plug + socket.
- + tons of contacts, solid signal integrity, compact
- − needs exact alignment, fragile, real insertion force, not made for blind hotplug or repeated reconfig, and plug≠socket so same self-mating problem but worse. probably not it for a snap-together board

**D: card-edge (PCB edge into a slot connector)**
the tile's own PCB edge is the contact, mates into an edge-card slot on the neighbor.
- + dirt cheap (contacts are just PCB), durable-ish
- − a slot is bulky + has insertion force + is directional, doesn't snap/hotplug nicely, and orientation-agnostic is hard. eh

**E: spring-finger / leaf contacts (one edge sprung, other flat pads)**
like pogo but flat leaf springs instead of plunger pins.
- + low profile, cheap, wiping contact
- + a wide beam is solid metal end to end, so current per contact is actually as good as or better than a small pogo
- + the gender split works here too (sprung half / pad half), so self-mating is fine, same as pogo
- − less Z-travel than a pogo plunger, so fussier about tiles sitting coplanar

### the self-mating problem: split the gender down the middle
the "this edge is male, that edge is female" asymmetry is what fought "every edge identical." the fix falls right out of the palindrome: make **half the contacts pogo (male) and half flat pad (female), split exactly at the center**. so on the 8-contact edge:

```
contact:  1     2    3     4    5    6     7    8
net:      GND   HV   BOOT  Tx   Rx   BOOT  HV   GND
gender:   pogo  pogo pogo  pogo pad  pad   pad  pad
```

because contact `i` always meets the neighbor's contact `9−i` (mirror), the male half of one edge lands exactly on the female half of the other. every pair checks out, right net AND opposite gender:
- GND↔GND, HV↔HV, BOOT↔BOOT on the power contacts (palindrome handles the net)
- Tx(pogo)↔Rx(pad) and Rx(pad)↔Tx(pogo) on the comms pair (swap is what UART wants)

so **every edge of a given length is self-mating**: any 5un edge mates any 5un edge, any 6un edge mates any 6un edge, no bridge piece, no separate male/female tile variants. two footprints total (short + long), each repeated on its two edges. this is the whole thing clicking into place :3

### retention: separate job from the contacts
the pogo contacts only push apart, they don't hold anything, so keeping tiles stuck together is its own problem. my original plan was **bigger magnets baked into the case walls** along each edge, doing the holding (and some self-alignment) totally independent of the electrical contacts. i like this because:
- the holding magnets can sit out at the case wall, away from the key area, which keeps them away from the hall sensors (the scary interaction)
- the connector stays a dumb genderless pogo strip, no magnets in the contact itself
- big magnets = strong hold, instead of relying on tiny in-connector ones

on the hall-sensor worry: a case magnet is a *static* DC field, and per-key min/max calibration already absorbs DC offset (noted on the [hall-effect-sensors](hall-effect-sensors.md) page). so as long as the case magnet doesn't *saturate* the sensor, the offset just calibrates out. that downgrades it from "scary" to "keep the magnet far enough away and check it doesn't rail the sensor." still need to actually measure it, but it's not a dealbreaker.

i still want to score the alternatives instead of just defaulting to my plan, so retention gets its own table below.

## Select

### contact mechanism
(retention is scored separately, so magnetic-pogo's magnets aren't counted here, just the contact itself. so "pogo" covers both plain and magnetic pogo.)

| Criteria                                        | Weight | Pogo + pad | Mezzanine | Card-edge | Spring-finger |
| ----------------------------------------------- | :----: | :--------: | :-------: | :-------: | :-----------: |
| Hotplug-safe make/break under power             |   9    |     9      |     3     |     4     |       8       |
| Current per contact                             |   7    |     7      |     8     |     6     |       8       |
| Self-mating / genderless (with the split trick) |   8    |     9      |     2     |     3     |       8       |
| Low profile                                     |   7    |     7      |     6     |     8     |       9       |
| Cost (×4 edges × N tiles)                       |   7    |     6      |     4     |     9     |       7       |
| Durability / mate cycles                        |   6    |     7      |     5     |     7     |       6       |
| Alignment tolerance                             |   5    |     8      |     3     |     5     |       7       |
| **Weighted total**                              |        |  **375**   |    214    |    288    |    **375**    |

**It's a tie: pogo + pad and spring-finger both land at 375 / 490 (76.5%).** 

the two really differ on just two axes:
- **pogo wins on Z-axis compliance:** the plunger has real travel (~0.5–2mm), so it forgives tiles not sitting perfectly coplanar (warp, slop, an uneven desk). a spring-finger deflects less, so it's fussier about the gap staying consistent.
- **spring-finger wins on profile + cost:** it's flatter and basically free to stamp.

mezzanine and card-edge stay out (neither likes blind hotplug or genderless mating).

**leaning pogo, but barely, and only for the Z-compliance.** modular tiles that get pulled apart and snapped back a lot are exactly where coplanarity drifts, and pogo travel eats that. but spring-finger is a real co-winner, not a fallback: if a prototype shows pogo height fighting the low-profile goal, switching costs nothing in the scoring. **this one wants a physical prototype of both to break the tie for real.**

### retention

| Criteria | Weight | Case-wall magnets | In-connector magnets | Mechanical latch | Friction / none |
| --- | :---: | :---: | :---: | :---: | :---: |
| Holding strength | 8 | 8 | 7 | 9 | 3 |
| Keeps magnets away from hall sensors | 8 | 8 | 3 | 10 | 10 |
| Self-aligning help | 6 | 6 | 9 | 4 | 3 |
| Low profile / not bulky | 6 | 7 | 6 | 4 | 9 |
| Cost | 5 | 6 | 5 | 6 | 9 |
| Snap-together feel / hotplug | 6 | 8 | 9 | 5 | 3 |
| Doesn't complicate the genderless connector | 5 | 9 | 6 | 7 | 8 |
| **Weighted total** | | **329** | 279 | 295 | 279 |

**Winner: case-wall magnets (329 / 440, 74.8%)** — which is the plan i walked in with, but now it's earned. it holds well, keeps the magnets clear of the sensors, and leaves the connector dumb. mechanical latch (295) scores well on holding + zero magnet risk but loses on bulk + snap feel + reconfig friction. in-connector magnets self-align best but park magnets right next to the hall sensors, the one thing i'm trying to avoid.

## decision
- **contacts:** leaning pogo + flat pad (genderless via the center gender split), but it's a true tie with spring-finger, decided only by pogo's Z-compliance. spring-finger is a live co-winner if low-profile gets tight. **prototype both before committing.**
- **retention:** magnets baked into the case walls, separate from the contacts
- **pinout:** the palindrome (GND HV BOOT Tx Rx BOOT HV GND), power doubled, split pogo/pad down the middle
- **two variants:** short (5un) and long (6un) edges, like only ever mates like

### still open (carry forward)
- actually measure a case magnet's field at the nearest hall sensor, confirm it doesn't saturate
- pick a real pogo part + magnet size once i'm doing the case + board outline

back to [index](../index.md)
