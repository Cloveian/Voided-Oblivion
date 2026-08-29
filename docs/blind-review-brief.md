# Voided Oblivion — blind-review brief

This file is the **only** project documentation a blind reviewer gets, alongside the KiCad
files (`Voided-Oblivion/`) and the datasheet library (`Refrences/datasheets/` — note the
spelling). It states what the design is required to do and the constraints it lives under.
It deliberately contains **no design reasoning, no component-value derivations, no known-issue
or accepted-risk lists** — re-derive everything from the board and the datasheets.

## What this is

A **modular ortholinear analog keyboard**. The unit is a **tile**: a 95.25 × 114.3 mm 4-layer
PCB with 30 hall-effect keys, 30 RGB LEDs, its own RP2350B MCU, its own USB-C/USB-PD front
end, and inter-tile edge connectors on all four sides. Tiles snap together in any arrangement
(2 = 60 %, 3 = 80 %, 4 = 100 % keyboard); whichever tile has an enumerated USB host connection
becomes master and relays for the rest. Each tile also has 4 corner sockets for small
"submodule" add-ons (knobs, displays, etc.).

## Hard requirements

- USB-C wired. Two USB-C ports per tile; **either** port may be the host and/or the power
  source, in any orientation, and both may be plugged at once.
- **Sub-1 ms end-to-end input latency at 1000 Hz USB polling**, N-key rollover.
- All 30 keys are **analog** (hall sensor per key, magnet in the switch), sampled every
  polling cycle. The analog signal chain *is* the keyswitch mechanism — its integrity is a
  first-class requirement, not a nicety.
- Hot-swappable switches; **hot-pluggable tiles and submodules** — any connector may be
  mated or broken at any time, including under power, without damage.
- A tile must **cold-boot from a bare 5 V USB attach** (vSafe5V, 4.45–5.5 V) on either port,
  run its MCU, and negotiate USB-PD from that state with no external help.
- A tile with **no USB cable at all** must run as a slave, powered only through its edge
  connectors from a neighbor.
- Submodules must work **without any PD contract present** (5 V-only source), and a corner's
  identity must be readable by the MCU **while that corner's power rail is off**. Submodules
  may contain no MCU at all.
- Assembled by **JLCPCB** (SMT). Exceptions, hand-soldered by the designer: the 16 edge
  pogo-connector bodies (J1–J8) and the 8 corner socket headers (J10–J12, J16–J20; J9 is the
  SWD debug header). USB receptacles
  and the two Alps switches are also off-catalogue.
- Open source; budget guideline ~$250 for a full keyboard.
- Temperature: **reasonable consumer-keyboard conditions**, but this is an open-source
  design meant for many users in many environments — a cold garage workshop, an unheated
  room in winter, a hot attic office are all in scope, not just a comfortable desk.
  Commercial-grade parts and indoor ambient, judged across that full spread; industrial
  extremes are out of scope.

## Electrical environment

- USB-PD sink only. The source may offer 5/9/15/20 V (12 V is optional in PD and may be
  absent). Negotiated voltage appears on VBUS; both ports have independent PD PHYs.
- Neighbor tiles feed power into edges: an edge's HV contacts may carry **any negotiated PD
  voltage (up to 20 V)** *inbound* from a neighbor, at any time, regardless of this tile's
  own state.
- **Per-edge current ceiling: 4 A** (the edge connector provides 4 × 1 A HV contacts +
  4 × GND). Design target ≥2 A continuous per edge. There is **no per-edge current sensing
  on the board — this is intentional**; overcurrent management is a system/firmware concern.

## Rails contract

| Rail | Contract |
|---|---|
| `PD+` | The negotiated PD voltage, distributed to the four edges through per-side switches. **Partition rule:** regions of a multi-tile array negotiated by *different* PD sources must be isolatable from each other — a tile must be able to keep its PD+ region separate from a neighbor's. |
| `BS+` | 5 V bootstrap rail. **Always on from the moment any valid source exists**, and **shared/combined across all tiles** in the array — every tile's BS+ is the same net through the edges. |
| `+5VA` | Clean always-on 5 V (post-PD). |
| `+5VP` | Gated 5 V for RGB + submodule power; may be off indefinitely while everything else runs. |
| `+3V3` | MCU, all 30 sensors, muxes. **Must be alive pre-PD** (from a bare 5 V attach) — the MCU has to boot before any PD negotiation can happen. |
| `GND` | Common everywhere, across all tiles, unconditionally. |

Events that must be survivable without damage or lockup: cable hot-unplug mid-operation;
PD renegotiation mid-operation; one port unplugged while the second stays attached; a
neighbor tile appearing or disappearing on any edge at any time; a submodule inserted into
an unpowered or powered corner.

## Connectors

**Inter-tile edges (J1–J8):** two 6-pin pogo bodies per edge (one male, one female).
Contact order along an edge:

```
GND  HV  HV  BS  Tx  GND | GND  Rx  BS  HV  HV  GND
```

The pinout is a palindrome: a mirrored (mating) edge lands power on power and swaps Tx↔Rx.
Gender rule is rotational — clockwise around the tile perimeter every edge is
male-then-female — so any edge mates with any edge of another tile. Each edge must be able
to **detect whether a neighbor is present**.

**Submodule corners (J9–J20, 4 corners):** 5-pin socket, clockwise: `ID GND 5V Rx Tx`.
`ID` is an analog identity/presence line readable with `5V` off. Per-corner power budget:
**≤300 mA per corner and ≤1 A total** across all four corners.

## Comms

- Full-duplex UART per edge, **≥4 Mbaud** target on inter-tile links (they carry relayed
  traffic for every tile downstream — the 1 ms budget includes multi-hop relay).
- Inter-tile UARTs are implemented on **PIO**; the two hardware UARTs go to submodule
  corners (GPIO24/25 = UART1, GPIO28/29 = UART0; the other two corners are PIO).
  RGB is on **hardware SPI0**. Two separate hardware **I²C buses**, one per PD PHY.
- Master election: whichever tile enumerates as a USB device is master. Exactly one USB
  data path may be active per tile; with both ports plugged, the selection must be
  deterministic.

## Keys & RGB

- 30 × analog hall sensors on +3V3 → two 16:1 analog muxes → 2 RP2350 ADC inputs, 4 shared
  select lines. All 30 keys sampled with margin inside each 1000 µs polling cycle at 12-bit
  quality.
- 30 × SK9822-EC20 (clocked, two-wire) on `+5VP`, driven from the 3V3 MCU domain.

## Fab facts

- 4 layers, 1 oz outer / 0.5 oz inner copper, JLCPCB standard process assumed.
- Stackup intent: L2 is a solid GND reference plane; L3 is power distribution.
- Custom DRC rules live in `Voided-Oblivion/Voided-Oblivion.kicad_dru`.

## Ground rules for the reviewer

1. **Datasheets are ground truth.** `Refrences/datasheets/` covers ~50 parts. Verify pin
   maps, ratings, and required externals against the PDFs, not against KiCad library symbols.
   Cite pages. If a needed datasheet is missing, say so rather than assuming.
2. **Firmware is an allowed mitigation — but name the price.** This architecture deliberately
   delegates some protection and sequencing to firmware. Wherever the hardware is only safe
   or only functional *if firmware does something specific*, you must state that obligation
   explicitly as a finding ("hardware forces firmware to X, or else Y"). Produce the complete
   list; it is a primary deliverable of this review.
3. **Assume at least one real bug exists.** The board has been reviewed before (you don't
   get those reviews); every prior pass found something the author was confident wasn't there.
4. Worst-case, not typical: check abs-max and recommended-operating on every pin against the
   worst voltage it can actually see (including what neighbors can push in through the edges),
   with tolerances, temperature, and the fitted parts' actual specs.
5. Walk the bring-up order explicitly (cold 5 V attach → PD negotiation → rails up → edges →
   submodules), and the teardown/hot-unplug order. Steady-state review is not sufficient.
6. Nothing in this brief explains *why* anything is the way it is. If a design choice looks
   wrong, argue it from physics and datasheets — do not assume it was considered.
