# Voided Oblivion — agent brief

Orientation document for AI agents working in this repo. It summarises the design as
currently decided, tells you **which document is authoritative** for each topic, and lists
the known contradictions so you don't "fix" something that is already fixed elsewhere.

**This file is a map, not a source of truth.** Every claim here is a compressed pointer to a
doc that has the derivation. When this file and a linked doc disagree, the linked doc wins —
and this file should be corrected.

---

## 1. What the project is

A **modular ortholinear analog keyboard**. The unit of the design is a **tile**: a
5un × 6un (95.25 × 114.3 mm) PCB with 30 hall-effect keys, 30 RGB LEDs, its own RP2350B MCU,
its own USB-PD front end, and edge connectors on all four sides. Tiles snap together
(2 tiles = 60%, 3 = 80%, 4 = 100%, more = macro pads) in any arrangement; whichever tile has
an enumerated USB host connection becomes **master**.

Hard constraints: USB-C wired, **sub-1 ms latency at 1000 Hz polling**, N-key rollover,
number row, ortholinear, portable, hot-swappable switches. Budget guideline ~$250.
Personal project, open source, assembled by **JLCPCB** (not by hand — this changed mid-project
and invalidates several older arguments; see §7).

Full goals: `docs/index.md` · project context and the author's tooling: `docs/overview.md`

---

## 2. Repo layout

| Path | What |
|---|---|
| `docs/` | All design documentation. The real content of this repo. |
| `docs/index.md` | **Start here.** Master index, goals, ordered list of every decision. |
| `docs/design-choices/` | *Why* each thing was chosen. Identify → Brainstorm → Select (weighted matrix). |
| `docs/schematic-design/` | *Why these values.* Datasheet math, as-built component derivations. |
| `docs/research/` | **Auto-generated, not decisions.** Per-chip datasheet reads by agents who were deliberately not shown the schematic, so they can be diffed against it. Proposals only. See `docs/research/README.md`. |
| `docs/chips.md` | Chip-level BOM (ICs and active parts, no passives). |
| `docs/schematic-checklist.md` | *What to wire*, per block, with pin assignment. Partly stale — see §8. |
| `docs/layout-checklist.md` | What's left to place and route, in order. |
| `Voided-Oblivion/` | The KiCad project (`.kicad_sch`, `.kicad_pcb`, `.kicad_dru`, footprints, symbols, 3D models). |
| `Refrences/datasheets/` | ~50 datasheet PDFs. Ground truth for any electrical claim. |
| `Refrences/recommended-layouts/` | Datasheet layout pages for every chip, stitched into one PDF, titled by refdes. |
| `Refrences/RP-006442-.../` | RP2350B minimal-board reference KiCad archive. |
| `analysis/` | Generated analyzer output (schematic/PCB/EMC/SPICE/deep-review JSON). |
| `old/`, `.schematic-backups/`, `*-backups/` | History. Do not treat as current. |

**Note the spelling: `Refrences/`, not `References/`.** It is intentional-by-accident; don't rename it.

---

## 3. Document hierarchy — which doc wins

Ordered most authoritative to least, for *as-built* questions:

1. **The KiCad files** (`Voided-Oblivion/*.kicad_sch`) — reality. The schematic has repeatedly
   turned out to be right where docs drifted.
2. **`docs/schematic-design/*.md`** — as-built values plus derivation. States explicitly where
   the board and the research disagree and resolves it.
3. **`docs/design-choices/*.md`** — the decision and its reasoning. Later "Revisit"/"Correction"
   sections *supersede* earlier ones in the same file; the earlier text is deliberately left in
   place as a record, so **always read a page to the end before quoting it.**
4. **`docs/chips.md`**, **`docs/schematic-checklist.md`** — summaries, most prone to drift.
5. **`docs/research/*.md`** — proposals from single-chip reads. Frequently correct in isolation
   and wrong in context (a per-chip agent cannot see a constraint living two parts away).

The **PCB is one design generation behind the schematic** (review finding F4). Treat any
PCB-derived analysis as provisional until an "Update PCB from Schematic" pass has run.

`docs/schematic-design/log.md` is the **build log** — dated, newest-on-top, one entry per
session. Read the top entry to know where things stand.

---

## 4. Architecture in brief

### Power (the most complex subsystem — `docs/design-choices/power.md`, `docs/schematic-design/power.md`)

Five rails per tile:

| Rail | What | Source |
|---|---|---|
| `PD+` | HV distribution, negotiated PD voltage, 5.7–20 V, per-side switched | VBUS via Q2 above the trip |
| `BS+` | Bootstrap 5 V, **always on, shared across all tiles** | raw VBUS via Q1 pre-PD; clean buck via ideal diode post-PD |
| `+5VA` | Clean buck output (U5 TPS54302) | PD+ |
| `+5VP` | Gated buck output (U6 TPS54302), RGB + submodules | PD+, EN = GPIO14 |
| `+3V3` | LDO, MCU + 30 sensors + muxes. **VIN = BS+**, so 3V3 exists pre-PD | BS+ |

**The rule that makes the whole scheme work:** HV **partitions** (different PD sources negotiate
different voltages, so regions must stay separate), bootstrap **combines** (every tile's buck
makes the same 5 V, so OR-ing just makes it stronger), GND is **common everywhere**.

The **VBUS handoff** is pure hardware, no firmware: an LM2903 comparator (U11, powered from
VBUS so it can't cut its own supply) watches VBUS against a TLV431B 1.24 V reference. Below the
trip, Q1 feeds VBUS→BS+. Above it, Q1 opens and Q2 connects VBUS→PD+ while U11B simultaneously
enables the clean buck. Trip: **LTP 5.640 V / UTP 5.772 V**, bracketed by vSafe5V's 5.5 V ceiling
below (graceful failure) and the LM66100's 6.0 V abs max above (destructive failure) — margin is
deliberately biased toward the 6.0 V side.

Four per-side HV switches (**Q4–Q7, AO4407A**, same LCSC part as Q2) gate PD+ to each edge.
**No per-edge current sensing exists** — it was cut entirely (not DNP; a DNP pad costs the same
board area). Firmware owns overcurrent by limiting topology before enabling a path.

### Comms (`docs/design-choices/comms.md`)

Full-duplex UART per side, **≥4 Mbaud** target, all four inter-tile sides on **PIO**
(a PIO UART does ~18.75 Mbaud; the hardware PL011 caps at 7.8 Mbaud, so the fast path belongs on
the relay links). The two hardware UARTs went to submodule corners instead.
Neighbour detection = external **4.7 kΩ** pull-down on each Rx line. Master election = whichever
tile enumerates as a USB device.

**PIO SM budget: 12/12.** RGB on hardware SPI (0), 4 inter-tile sides on PIO (8),
2 submodule corners on hardware UART (0) + 2 on PIO (4). The next budget to watch is
**DMA channels (~16 of 16)**, not state machines.

### Key sensing (`docs/schematic-design/keys.md`)

30 × **GH39F** analog hall sensors on +3V3 → 2 × **74HC4067** 16:1 muxes → 2 RP2350 ADC pins,
4 shared select lines. Scan budget ~**116 µs** worst case against 1000 µs — 8.6× margin.
**No bank power gating** — decided against; the 270 mA is a permanent load and the LDO was fixed
instead. Per-key min/max calibration in firmware absorbs sensitivity and offset spread, which is
what makes the sensor a swappable choice (generic 3-pin SOT-23 footprint; DRV5055 is the
verified pin-compatible fallback).

### RGB (`docs/schematic-design/rgb.md`)

30 × **SK9822-EC20** on `+5VP`, hardware SPI0, chain refresh 68 µs at the 15 MHz clock ceiling.
A **level shifter is mandatory, not optional** (VIH min 3.4 V vs a 3V3 rail topping out at
3.366 V) — **SN74LVC2T45**, chosen specifically for Ioff partial-power-down because the LEDs sit
on a gated rail while the MCU does not.

### Connectors

- **Inter-tile (J1–J8):** `PG-6P-2.5-5.5H-SM-RA` pogo, **2 bodies per edge** (one male, one female).
  Pinout `GND HV HV BS Tx GND | GND Rx BS HV HV GND` — a palindrome, so a mirrored edge maps
  power→power and swaps Tx↔Rx. Gender rule is **rotational: clockwise around the perimeter,
  every edge is male-then-female**, which is what makes every edge self-mating.
  4× GND, 4× HV (**4 A per-side ceiling**, ≥2 A continuous design target), 2× BS, Tx, Rx.
- **Submodule corners (×4):** 5-pin `ID GND 5V Rx Tx` clockwise. The ID pin is an ADC-read
  divider giving presence + identity + optional analog input, and it works **with the corner rail
  switched off** because it runs off +3V3. Modules may have no MCU at all.

### Budgets (all close, with headroom)

| | Used | Total |
|---|:---:|:---:|
| GPIO | **44** | 48 |
| ADC | **6** | 8 |
| PIO state machines | **12** | 12 |

Everything fits on **one RP2350B per tile**. Pin-by-pin assignment:
`docs/design-choices/pin-budget.md#a-starting-assignment` and
`docs/schematic-checklist.md#9-pin-assignment-cross-check-paste-into-schematic-notes`.

### PCB (`docs/design-choices/pcb-stackup.md`)

**4 layers**, `SIG / GND / power / SIG`, 1 oz outer / 0.5 oz inner. The weighted matrix picked
6 layers; 4 was chosen anyway because **this is open source and other people pay the layer count** —
an override from outside the matrix, recorded as such. L2 is solid GND and is not a routing
resource. The governing rule: **analog on L1, switching on L4, never the same layer.**
7 net classes, custom DRC rules in `Voided-Oblivion/Voided-Oblivion.kicad_dru`.
6 × M2 mounting holes (deflection under typing load is a *measurement error* on a hall board,
not a feel preference).

---

## 5. Locked decisions — one line each

| Topic | Decision | Full working |
|---|---|---|
| Form factor | Modular 5×6 ortho tiles | `design-choices/form-factor.md` |
| Switches | Custom low-profile Void Switch, analog hall, N52 4×1 mm magnets, ~2 mm travel | `design-choices/switches.md` |
| MCU | **RP2350B** QFN-80 + external 16 MB QSPI flash | `design-choices/controller.md` |
| Sensors | **GH39F**, 2 × **74HC4067** mux | `design-choices/hall-effect-sensors.md` |
| RGB | **SK9822-EC20** (clocked, hardware global brightness, 0 PIO SMs) | `design-choices/rgb.md` |
| PD | **2 × FUSB302BMPX**, one per port, CC wired **direct** (passive Rd at each connector) | `design-choices/comms.md#revisit-pdcc-architecture-the-cc-mux-doesnt-survive-cold-start` |
| USB data | **TS3USB30E** 2:1 D± mux, VCC on 3V3, port-2-priority hardware arbiter | `schematic-design/comms.md` |
| Bucks | **TPS54302 ×2** (one clean/always-on, one big/gated) | `schematic-design/power.md` |
| Ideal diode | **LM66100DCKT ×2** (U9 bootstrap OR, U15 submodule branch), **CE→VOUT** | `schematic-design/power.md#ideal-diode---lm66100-u9` |
| HV side switches | **AO4407A ×4** + BC847B level shift, gate 100k/4.7k/100nF | `schematic-design/power.md#hv-per-side-switches---picking-the-fet` |
| Submodule power | Dual-sourced `+5VP ∥ BS+` → U12/U15 → U16 → SM+, ≤300 mA/port, ≤1 A total | `design-choices/submodules.md#corner-power-dual-sourced-so-submodules-work-without-pd` |
| Edge connector | `PG-6P-2.5-5.5H-SM-RA`, off-catalogue, hand-soldered, buy spares | `design-choices/module-connectors.md` |
| Stackup | 4-layer, 1 oz/0.5 oz | `design-choices/pcb-stackup.md` |
| Bank gating | **Rejected** — no gating, fix the supply not the load | `schematic-design/keys.md#sensor-bank-power-gating` |
| Per-edge OCP | **Cut entirely** — firmware owns it via the tile map | `design-choices/power.md#re-decision-does-this-need-per-edge-ocp-at-all` |
| Bluetooth, 3.5 mm AUX | **Cut** | `design-choices/feature-decisions.md` |

---

## 6. Firmware requirements captured in hardware docs

Search the docs for the literal marker **`!firmware-note!`** — these are hardware decisions that
push a permanent obligation onto firmware. The load-bearing ones:

- **80 % rule:** never draw more than 80 % of negotiated PD capacity from any port.
- **Default to 9 V PD.** All 12 contacts break together (no inset sequencing possible with molded
  connector bodies), so hot-unplug safety rests entirely on voltage. Gold's minimum arcing
  voltage is ~15 V *and* ~0.4 A — 9 V misses on voltage regardless of load. 20 V sits behind an
  explicit flag and a don't-hot-unplug warning. (12 V is **not** a required PD step.)
- **Clamp SK9822 global brightness to ≤10 of 32** — a *package thermal* limit, independent of the
  power budget. Getting it wrong cooks LEDs rather than tripping a budget.
- **Turn an edge switch OFF when a neighbour disappears**, or the next hotplug there is a hard
  hot-insert with no soft-start in the path (the MOSFET body diode conducts inbound regardless
  of gate state).
- **Don't enable `+5VP` until PD reports ≥9 V** — the big buck has no input UVLO.
- **Owns overcurrent** by refusing to enable an over-budget path, using the tile map it already
  builds. There is no hardware per-edge OCP.
- **Cap the PDO request to what the build's copper supports** (the 5 A case only exists at 20 V).
- **Never enable the FUSB302 VCONN switch** (sink-only; VCONN pins are tied to +3V3).
- **CC1/CC2 are crossed** on both ports — the orientation bit firmware reads is inverted from
  physical reality; never use it for anything physical.
- **Keep the level shifter's A-port inputs driven at all times**, even when RGB is off.
- Verify SK9822 **colour order against a physical LED** — the datasheet contradicts itself
  (p.7 RBG vs p.8 GRB).

---

## 7. Conventions and recurring lessons

These are the project's own hard-won rules; they generalise and are worth applying to new work.

- **A requirement is a gate, not a scoring row.** A weighted matrix can only compare options that
  already satisfy the requirements. Once, a matrix produced a confident winner that failed the
  actual requirement, complete with a sensitivity analysis "proving" nothing could flip it.
  (`design-choices/submodules.md#identify---and-the-mistake`)
- **Walk the bring-up order explicitly.** Four separate cold-start latches were found, all the same
  shape: *a rail depending on something downstream of itself*. Steady-state review does not catch
  this class of bug.
- **A value being correct doesn't mean the part exists.** Reference designs give you values, not
  orderable parts (22 µF in an 0402; 12.2 kΩ is not an E-series value).
- **"Lots of people do it" is not a spec.**
- **Silent failure modes are the ones to design against.** LM66100 `CE→GND` doesn't disable the
  part — it turns it into a plain switch with no reverse blocking, while everything appears to work.
- **Three exemptions in a row means the rule is the wrong shape** — name the aggressor instead of
  patching (the DRC USB-clearance rule).
- **A per-chip datasheet read cannot see a constraint two parts away.** The research proposed a
  7.36 V comparator trip which would destroy an LDO one part downstream.
- **Old sections are kept and marked superseded**, not deleted. Read to the end of a page.
- Schematic conventions: net names `PD+ / BS+ / +5VA / +5VP / +3V3 / GND`; 0402 default for R/C;
  **0Ω jumper on every digital enable/select pin**, default populated.
- **RP2350-E9:** any pin whose default-low state is load-bearing needs an **external pull-down
  ≤8.2 kΩ; use 4.7 kΩ**. The erratum is an active ~120 µA *source* that parks a floating input at
  2.2 V, not a weak pull-down. Bitten twice (inter-tile Rx detect, AP2171W enables).
- **The project is no longer hand-assembled** — it goes to JLC. Any argument in `docs/research/`
  that rejects a package on *solderability* grounds is void; sourcing/cost/DRC arguments stand.

---

## 8. Current state, open items, and known doc traps

**Read this section before changing anything.** These are places where two documents disagree and
the disagreement is already understood.

### State

- Schematic: substantially complete (374 components, 280 nets, ERC = 1 intentional error).
  Power + USB/PD front end done.
- PCB: **261 of 425 footprints placed; 73 of 242 nets routed.** One generation behind the schematic.
- Sourcing: **311 of 373** components carry LCSC/MPN/Manufacturer (48 unique lines, ~$90 in setup fees).

### Known contradictions between docs

| Trap | Reality |
|---|---|
| **The 3V3 LDO** | `chips.md` and `schematic-design/power.md` document **XC6220B331MR**. As-built U7 is **TLV76733** (WSON-6) — verified against TI SLVSE84D in the review, and `keys.md` already reasons from it. The swap is good (it dissolved the thermal ceiling that made bank gating look mandatory); **the docs are stale, not the board.** |
| **Backfeed diodes D1/D2** | `chips.md`, `schematic-checklist.md` and `layout-checklist.md` say **SS54**. `schematic-design/power.md` re-selected to **LM74700-Q1 + NCE4009S N-FET** (SS54 dissipates 3.2 W at the 5 A hardware bound → dead part). Not yet applied to the board. |
| **Comparator divider** | Docs re-derived to **R30 35.7k / R31 10k / R22 5.1k**. The schematic still has **44.2k / 12.2k**, and **12.2 kΩ does not exist on LCSC at any package or tolerance.** Must be applied. |
| **Edge-connector pinout** | `chips.md` and `schematic-checklist.md` §7 quote the old `GND GND HV HV BS Tx \| Rx BS HV HV GND GND`. Current is **`GND HV HV BS Tx GND \| GND Rx BS HV HV GND`** (same counts, reordered so GND flanks the signals). |
| **`schematic-checklist.md` §3 and §6** | Still describe **TLV1805 + AO3415**, a **TMUX1574 CC mux**, external **Rd pull-downs**, and a **single FUSB302**. All four are superseded — the CC mux does not survive cold start, and Rd comes from the FUSB302's own dead-battery clamp (adding external Rd would *break* it). |
| **Inductors L2/L3** | Sourcing pass assigned **APH0630T100M (C5349698)**; `power.md` then re-weighted height and moved to **APH0624T100M (C19634013)** — same land pattern, so it is a stuffing change. Footprint field on both parts is **still empty**. |
| **Capacitor footprints** | **C28/C29/C34/C35 are 22 µF in an 0402**, which does not exist. **C26/C31 are 10 µF 0402 on a 20 V rail**, where only ≤6.3 V parts exist. This is the one defect that would actually stop a fab order. Fix is the footprint (1206), not the part number. |
| **`AM0:15` / `AM1:15`** | Floating. Tie both to GND — the only outright defect on the keys sheet. |
| **`U16` EN** | Tied to GND through a 0Ω, and AP2171W is active-high — **the submodule rail can never turn on as drawn.** Needs 4.7 kΩ + an `SM EN` GPIO. |
| **Pin-budget arithmetic** | The table in `pin-budget.md` understated by 2 for three sessions (the I²C row). Current correct figure is **44/48 GPIO**. |

### Genuinely unresolved / needs bench work

- **Does AP2171W's OCP latch or auto-retry?** Diodes bot-blocks the datasheet. If it latches,
  U16's EN is the only fault reset.
- **Is the GH39F actually ratiometric at 3.3 V?** The whole ADC noise argument rests on it and the
  datasheet characterises only 5 V. Plan: mixed population (26 GH39F + 4 DRV5055) on the first
  board — one variable, ~$2.40.
- **ADC_AVDD has no filter** (review F6). Add a DNP-able provision before layout freeze; impossible after.
- **The ADC supply chain is not characterised end-to-end** — DCM buck ripple → LDO with no
  published output-noise spec → 3V3 → sensors. First suspect if keys read noisy.
- Accepted risks, deliberately: **5.95 V on the LM66100's 6.0 V abs max** (structurally unfixable);
  **turn-off ~20× slower than turn-on** on the HV side switches (inherent to the gate topology);
  **no bidirectional blocking** on the per-side switches (body diode conducts inbound).
- No ESD on the 16 UART lines; no OVP on the FUSB302 VBUS sense pin; `USB SEL` zener is 5.1 V
  where it should be ~3.3 V.

---

## 9. Where to look — topic index

| Question | Go to |
|---|---|
| What is this and what are the goals? | `docs/index.md`, `docs/overview.md` |
| Where does the project stand *right now*? | `docs/schematic-design/log.md` (top entry) |
| Why was part X chosen? | `docs/chips.md` first, then the linked `design-choices/` page |
| Why is component value Y what it is? | `docs/schematic-design/` — power / comms / keys / rgb / mcu |
| What still has to be wired? | `docs/schematic-checklist.md` (check §8 traps above first) |
| What still has to be placed and routed? | `docs/layout-checklist.md` |
| Track widths, clearances, layers, DRC rules | `docs/design-choices/pcb-stackup.md` |
| Which GPIO does what? | `docs/design-choices/pin-budget.md` |
| Power flow, rails, startup sequence | `docs/design-choices/power.md` → `docs/schematic-design/power.md` |
| Why the CC mux was killed | `docs/design-choices/comms.md#revisit-pdcc-architecture-the-cc-mux-doesnt-survive-cold-start` |
| Cold-start bugs and how they were found | `docs/schematic-design/implementation.md` |
| Independent datasheet reads (proposals, not decisions) | `docs/research/` — read its `README.md` first |
| Last full design review | `docs/schematic-review-2026-08-08.md` (findings F1–F14) |
| BOM / LCSC state and what's unsourceable | `docs/sourcing-pass-2026-08-09.md` |
| Raw datasheets | `Refrences/datasheets/` |
| Manufacturer-recommended layouts, per refdes | `Refrences/recommended-layouts/recommended-layouts.pdf` |
| The actual design files | `Voided-Oblivion/Voided-Oblivion.kicad_{sch,pcb,pro,dru}` |

---

## 10. Working notes for agents

- **Prefer citing a doc anchor over restating a number.** Numbers in this repo have been revised
  repeatedly and the derivation is where the current value lives.
- **Check for a "Revisit" or "Correction" section** before acting on anything in a design-choices page.
- **Cross-check any electrical claim against `Refrences/datasheets/`.** The project has been bitten by
  LCSC description fields carrying *typical* values where the datasheet gives a *max*
  (AP3010's Vth, inductor Isat), and by a truncated PDF download hiding half of an erratum.
- **The KiCad MCP tools are available** for reading and editing the schematic/PCB directly.
  There is an active `.lck` file pattern — check whether KiCad is open before writing.
- When adding a decision, follow the house format: **Identify → Brainstorm → Select** with a
  weighted matrix, gates stated *above* the table, and the losing options left in place.
