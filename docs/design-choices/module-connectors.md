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

**Winner: case-wall magnets (329 / 440, 74.8%)** - which is the plan i walked in with, but now it's earned. it holds well, keeps the magnets clear of the sensors, and leaves the connector dumb. mechanical latch (295) scores well on holding + zero magnet risk but loses on bulk + snap feel + reconfig friction. in-connector magnets self-align best but park magnets right next to the hall sensors, the one thing i'm trying to avoid.

## decision
> **superseded in part** - the contact *mechanism* below still stands, but the physical realization changed completely. see [revisit](#revisit-i-picked-a-real-connector-and-it-killed-the-custom-cutout-idea) at the bottom: it's an off-the-shelf 6P connector pair now, not loose pogo pins, and the pinout grew from 8 contacts to 12.

- **contacts:** leaning pogo + flat pad (genderless via the center gender split), but it's a true tie with spring-finger, decided only by pogo's Z-compliance. spring-finger is a live co-winner if low-profile gets tight. **prototype both before committing.**
- **retention:** magnets baked into the case walls, separate from the contacts
- **pinout:** the palindrome (GND HV BOOT Tx Rx BOOT HV GND), power doubled, split pogo/pad down the middle
- **two variants:** short (5un) and long (6un) edges, like only ever mates like

### still open (carry forward)
- actually measure a case magnet's field at the nearest hall sensor, confirm it doesn't saturate
- ~~pick a real pogo part + magnet size once i'm doing the case + board outline~~ - **pogo part picked**, see revisit. magnet size still open.

## Revisit: i picked a real connector, and it killed the custom-cutout idea

### what i was about to build

i'd gone a long way down a rabbit hole. the plan was **individual discrete pogo pins** (Top-Link 10101012662) mounted into a **negative cutout routed into the board edge**, so the pin body lives *inside* the 1.6mm board thickness and adds zero Z-height. the contact side would be a **plated scallop** - a half-hole castellation routed at depanelization - giving the plunger a concave cradle of matched radius instead of a flat pad, so Hertzian contact spreads over a patch instead of a point.

it was a genuinely nice idea and the physics checked out. i worked through most of it:
- **0mm gap between tiles** makes working height = cutout depth, which drops the pin's own ±0.15mm length tolerance out of the stack entirely
- **advance = cavity depth `t`, not radius `R`**, so conformity (R) and protrusion (t) are independent knobs - `protrusion = 0.80 + t`, `pocket depth = 3.50 − t`
- landed on a ⌀1.5mm hole (R=0.75), t=0.40mm, 3.15mm pocket, 1.20mm protrusion

### why it died

none of the physics was wrong. what killed it was everything *around* the physics:

- **it's an unproven custom footprint, hand-soldered, ×40.** four edges × ~10 pins × however many tiles, every one of them a hand-placed pin in a routed slot. if the footprint is off by the 0.13/−0.08mm JLC gives me on holes plus ±0.1mm on routing, i find out forty joints in.
- **the tolerance stack was load-bearing and i'd already been wrong once.** i misread the pin drawing and told myself the body was ⌀1.54 when only the mid-lip is; i under-reported plunger protrusion as 0.85mm when the ⌀1.5 half-hole and its shallower pocket actually make it 1.55mm. two errors on the same part in one sitting is the design telling me something.
- **the scallop is a depanelization artifact.** it only exists because the plated hole gets routed through when the board leaves the panel, which means its finish quality is a process side-effect, not a spec i can order. and a routed vertical edge can't take hard gold (that's a top/bottom-face service) - so it's **ENIG's 0.05–0.1µm** on a surface designed to be *rubbed*, versus 0.75–1.27µm on a real wear finish.
- **i was designing a connector.** that's a solved problem someone else has already tooled.

### the part

**PG-6P-2.5-5.5H-SM-RA**, Shenzhen Yiwei Technology. 6 positions, 2.5mm pitch, 5.5mm height, surface-mount, right-angle. **Two per side: one 6P male + one 6P female.**

**and the gender split falls out for free.** the whole "split the gender down the middle" trick above - the thing that made every edge self-mating - is now just *place two bodies per edge, male one side of the midline and female the other.* i don't have to engineer it, it's two parts. the cleverest bit of the original design became the least clever bit of the implementation, which is exactly what you want.

### the gender rule: clockwise, male first

the one thing that is **not** obvious, and that i'd get wrong if i wrote it down lazily as "male on the left half": *left* stops meaning anything once the edge rotates. the actual invariant is rotational.

**going clockwise around the tile perimeter, every edge is male-then-female.**

| edge | traversed clockwise | first body | second body |
| --- | --- | --- | --- |
| top | left → right | J1 **male** | J2 female |
| right | top → bottom | J3 **male** | J4 female |
| bottom | right → left | J7 **male** | J8 female |
| left | bottom → top | J5 **male** | J6 female |

and *that's* why it self-mates. when tile A's right edge butts against tile B's left edge, they're the same physical line, but A and B traverse it in **opposite** rotational senses - A's clockwise runs top→bottom along it, B's clockwise runs bottom→top. so A's male half is at the top and B's male half is at the bottom, which means A-male lands on B-female and A-female lands on B-male, everywhere, automatically. the 180° flip case falls out the same way.

it's the same trick as the palindrome, just applied to gender instead of nets, and it only reads correctly if you state it as a rotation.

### the pinout, now 12 contacts

```
contact:  1    2    3    4    5    6   |   7    8    9    10   11   12
net:      GND  GND  HV   HV   BS   Tx  |   Rx   BS   HV   HV   GND  GND
body:     <-------- 6P male -------->  |  <------- 6P female ------->
pin:      1    2    3    4    5    6   |   1    2    3    4    5    6
```

so per body, and this is what's actually drawn: **male = GND GND HV HV BS Tx** on pins 1–6, **female = Rx BS HV HV GND GND** on pins 1–6.

mirror check, contact `i` meets the neighbor's contact `13−i`:

| pair | nets | gender |
| --- | --- | --- |
| 1 ↔ 12 | GND ↔ GND ✓ | male ↔ female ✓ |
| 2 ↔ 11 | GND ↔ GND ✓ | male ↔ female ✓ |
| 3 ↔ 10 | HV ↔ HV ✓ | male ↔ female ✓ |
| 4 ↔ 9 | HV ↔ HV ✓ | male ↔ female ✓ |
| 5 ↔ 8 | BS ↔ BS ✓ | male ↔ female ✓ |
| 6 ↔ 7 | **Tx ↔ Rx** ✓ | male ↔ female ✓ |

**4× GND, 4× HV, 2× BS, Tx, Rx.** power doubled from the original 8-contact sketch (which had 2 HV / 2 GND), because two 6P bodies hand you twelve contacts whether you want them or not and spending the extras on copper is the obvious move.

**GND stays outboard**, exactly like the original `GND HV BOOT Tx Rx BOOT HV GND` sketch had it - i just doubled each pair rather than reordering. that ordering is worth keeping deliberately: the outermost contacts are the ones most exposed to debris, misalignment and a partially-inserted tile, and those should be **ground, not a 20V rail**. HV sits inboard behind them, and the comms pair sits dead centre where it's most protected.

> ⚠ **superseded.** putting GND at the extremes necessarily puts Tx/Rx furthest from any ground return - measured, **10.0mm** - which caps the link well below the PIO's ~18.75 Mbaud. reordered to `GND HV HV BS Tx GND` in [the revisit below](#revisit-gnd-outboard-was-the-wrong-principle---it-should-be-gnd-flanking). same counts, same palindrome, GND still on 1 and 12.

> **footprint rule, and it's the one that breaks everything if you get it wrong:** both bodies must be placed **symmetric about the edge midline**. the contacts don't need uniform 2.5mm spacing *across* the male/female boundary - the two bodies will have their own end margins, so that gap will be wider than 2.5mm - they only need to mirror. identical bodies butted symmetrically about center gives that automatically. an asymmetric placement silently maps HV onto Tx.

### what this does to the rest of the design

- **the per-side current budget finally exists.** 4× HV contacts at 1A each = **4A hard ceiling per side**, and i'm designing the switch for **≥2A continuous** (50% contact derate). that closed the question that had been blocking the HV per-side FET choice since the research flagged it as *"the single biggest lever"* - working through in [power schematic-design](../schematic-design/power.md#hv-per-side-switches---picking-the-fet). the FET went **AO3401A → AO4407A** as a direct result.
- **2A supports the array sizes i care about:** ~18W at 9V (≈3.6 tiles downstream), ~40W at 20V (≈8 tiles). at 9V the connector's 4A ceiling is the real limit rather than the voltage - 36W ≈ 7 tiles.
- **the "~6–8 contacts per edge" estimate in Identify was low**, and the "each power net has 2 mating contacts... HV ~4A = ~2A per contact" note is stale - it's 4 contacts at 1A now. leaving both as the record.
- **no inset sequencing.** with loose pins i could have recessed the signal contacts so they broke first on unplug. two molded bodies can't do that - each body carries HV, GND *and* signal, so there's no way to split them by depth. **all twelve contacts make and break together.** that means hot-unplug safety rests entirely on the PD voltage, not on ordering.

### the voltage consequence

pogo voltage ratings are **arc-erosion** specs, not dielectric ones (the magnetic connector i looked at earlier rates 36VDC but withstands 500VAC). what actually matters on a hot break is the **minimum arcing voltage** of the contact metal: gold is **~15V**. below that a sustained arc physically cannot form, regardless of current. that's a floor, not a derating.

and it's not just voltage - **an arc needs a minimum voltage AND a minimum current**, both. for gold that's **~15V and ~0.4A**. miss either one and it can't sustain.

> **correction: 12V was the wrong default.** i'd written this around 12V, but **12V isn't a required PD voltage** - the USB PD Power Rules make the steps above 5V **9V (27W) / 15V (45W) / 20V (60W)**. 12V is never required at any power level, it's an optional extra PDO. a source may simply not offer it. so the plan can't be built on it.

redoing it against the steps that actually exist:

| PD step | vs V_min (15V) | per-tile draw | verdict |
| --- | --- | --- | --- |
| **9V** | below | 0.56A | **unconditionally safe** - the voltage axis alone blocks it, current doesn't matter |
| **15V** | *at* the threshold | 0.33A/tile | safe **only when breaking ≤1 tile** (0.33A < 0.4A). 2 tiles = 0.67A → can arc |
| **20V** | above | - | not arc-safe |

**!firmware-note!** so the standing plan is **firmware defaults to 9V**, and that's a stronger result than the 12V version it replaces - 12V was safe with ~3V of room, 9V has 6V, and it doesn't depend on how much is downstream. 15V turns out to be conditionally safe in a way that's nearly useless: it only holds for a single-tile break, which is exactly the case i don't care about. 20V stays behind an explicit flag with a "don't hot-unplug" warning.

**what 9V costs:** 2A × 9V = 18W ≈ **3.6 tiles** per joint, down from 5 at 12V. the connector's 4A ceiling gives 36W ≈ 7 tiles. so at 9V the array is **current-limited rather than voltage-limited**, which is one more reason the [per-side FET](../schematic-design/power.md#hv-per-side-switches---picking-the-fet) needed to be the one with current headroom.

**and one to actually check on the bench:** [session 2](../schematic-design/log.md) records that the TPS54302 *"can't make 5V below ~9V in"*, so **9V is exactly the buck's stated minimum input**. the safest arc voltage is also the tightest buck condition. that's a measurement, not an assumption.

### risks i'm carrying knowingly

- **single-source niche part.** it isn't in the LCSC/JLC catalogue at all (i searched). that's *fine* because these are hand-soldered - a constraint the original decision quietly assumed but never wrote down - but it means no second source and no JLC assembly for this line. buy spares.
- **5.5mm height vs "low profile", which is a stated must-have.** this is taller than the 4.00mm magnetic connector i partly rejected on bulk, so i should be honest that i'm not applying the criterion evenly. the argument for why it's OK: it's a right-angle part at the board perimeter, below switch height, and the thing it actually has to clear is the case wall - not the key stack. **needs checking against the real case cross-section**, not hand-waved.
- **populate 2 tiles first.** 40 hand-soldered connectors on a footprint that has never been built is not where i want to discover a 0.2mm error. validate the joint on one mating pair before committing the rest.

### still open

- price + stock, once i've actually ordered
- confirm 5.5mm clears the case wall on the real cross-section
- magnet size for retention (unchanged from above)
- draw the two footprints (short 5un / long 6un edge) with the symmetric-about-midline rule baked in

## Revisit: GND outboard was the wrong principle - it should be GND *flanking*

### what prompted it

comms is spec'd at **≥4 Mbaud** and the PIO can theoretically do **~18.75 Mbaud** (8 cycles/bit at 150MHz). i wanted to know what stops me taking it. the answer isn't the PCB - it's this connector, and it's a consequence of the ordering i chose two sections up for a completely different reason.

measured off the as-drawn footprint:

```
J1 male:  GND  GND  HV   HV   BS   Tx        pitch 2.5mm
                                   ^
          Tx pad -> nearest GND pad:  10.00 mm
```

**Tx and Rx are the two contacts furthest from a ground return in the whole connector.** that fell straight out of "GND outboard" - putting ground at the extremes necessarily puts the comms pair at the other end from it.

### why 10mm matters at 18.75 Mbaud and not at 4

the return current for Tx has to travel 10mm laterally through the connector body before it finds a ground pin. that's a loop, and a loop is an inductor:

```
L ~ (u0/pi) * l * ln(d/r)      l = 5.5mm connector height, r ~ 0.5mm pin
   d = 10.0mm  ->  6.6 nH
   d =  2.5mm  ->  3.5 nH        (logarithmic, so 4x closer is only ~2x better)

bounce = L * di/dt,  3.3V into ~50R in ~2ns  ->  di/dt ~ 3.3e7 A/s
   6.6 nH  ->  0.22 V
   3.5 nH  ->  0.12 V
```

**at 4 Mbaud this is invisible** - a 250ns bit sampled mid-bit doesn't care about 220mV of ringing that settles in nanoseconds. at 18.75 Mbaud the bit is **53ns**, and 0.22V is ~7% of the swing injected at the seam, on a signal that then has to survive the neighbouring tile's identical version of it.

### the new pinout

```
contact:  1    2    3    4    5    6   |   7    8    9    10   11   12
net:      GND  HV   HV   BS   Tx  GND  |   GND  Rx   BS   HV   HV   GND
body:     <-------- 6P male -------->  |  <------- 6P female ------->
```

mirror check, contact `i` meets contact `13−i`:

| pair | nets | |
| --- | --- | --- |
| 1 ↔ 12 | GND ↔ GND | ✓ |
| 2 ↔ 11 | HV ↔ HV | ✓ |
| 3 ↔ 10 | HV ↔ HV | ✓ |
| 4 ↔ 9 | BS ↔ BS | ✓ |
| 5 ↔ 8 | **Tx ↔ Rx** | ✓ |
| 6 ↔ 7 | GND ↔ GND | ✓ |

**still a palindrome, and the counts are identical: 4× GND, 4× HV, 2× BS, Tx, Rx.** nothing is traded away in current capacity - this is pure reordering.

### the version i nearly settled for, and why this one is better

the obvious move was `GND HV HV BS GND Tx` - just slide one ground next to Tx. that fixes the return path and passes the palindrome. but it leaves **Tx at 6 and Rx at 7, directly adjacent across the seam with nothing between them**, which is full-duplex near-end crosstalk between the two signals i care most about.

putting the ground *inboard* of the signal instead gets both:

| | Tx → nearest GND | Tx ↔ Rx |
| --- | --- | --- |
| as drawn (GND outboard) | 10.0mm | adjacent |
| `…BS GND Tx` | 2.5mm | **adjacent** |
| **`…BS Tx GND`** ✅ | **2.5mm** | **7.5mm, two grounds between** |

and it means the two bodies meet **GND-to-GND at the seam**, which is the widest gap in the whole run.

### what this costs, said plainly

**"GND outboard" is dead as a principle.** the [original reasoning](#the-pinout-now-12-contacts) was that the outermost contacts see debris, misalignment and partial insertion, so they should be ground rather than a 20V rail. that's still true, and **positions 1 and 12 are still GND** - the single most exposed contact on each end is unchanged.

what changes is that **HV moves from position 3 to position 2**, so the 20V rail is now 2.5mm from the exposed end instead of 5mm. that's a real reduction in the exposure margin and i'm taking it deliberately.

the replacement principle is stronger, not weaker: **GND outermost *and* flanking the signals.** it satisfies the original safety argument at the extremes and adds a return path where the original had none.

### this alone doesn't get me to 18.75 Mbaud

the pinout halves the bounce. the other half is **`R84`–`R87`, which are currently 0Ω placeholders** - populating them at **22–33Ω** makes them proper source-series termination, damping the reflection at the driver *and* slowing di/dt:

| | bounce | Tx↔Rx |
| --- | --- | --- |
| today | 0.22 V | adjacent |
| new pinout only | 0.12 V | 7.5mm, shielded |
| **new pinout + 33Ω series** | **~0.05 V** | **7.5mm, shielded** |

**neither alone is enough; both together are.** and the 33Ω is worth doing regardless of whether i ever chase 18.75 Mbaud - it's free, it's already a placeholder, and it helps the crosstalk-into-analog problem that every fast digital net on this board has.

### carry-forward

- **8 connector instances** (J1–J8) need the new pin assignment in the schematic - and the [gender rule](#the-gender-rule-clockwise-male-first) has to survive it unchanged, since it's rotational and independent of net order
- **[chips](../chips.md)** quotes the old `GND GND HV HV BS Tx | Rx BS HV HV GND GND` string
- **R84–R87 → 22–33Ω**, and they stop being placeholders
- if i take 18.75 Mbaud, the inter-tile UARTs move from Tier C to Tier A in [the layout checklist](../layout-checklist.md#appendix---every-net-ranked) and probably want adding to the `Switching` netclass so the 0.5mm analog-separation rule covers them

if reading by stream of consciousness go back to [index](../index.md)
