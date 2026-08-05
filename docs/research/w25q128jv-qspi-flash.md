# W25Q128JV QSPI flash — datasheet research
> Independent datasheet read. Not written against the existing schematic.

Sources:
- **[W25Q128JV]** = `Refrences/datasheets/W25Q128JV-winbond-qspi-flash.pdf`, Winbond, Rev. F, "Publication Release Date: March 27, 2018" (generic W25Q128JV datasheet, all packages, adds Industrial-Plus grade). Page numbers below are the datasheet's own printed page numbers (footer), not PDF page indices.
- **[SIQ]** = `Refrences/datasheets/W25Q128JVSIQ-flash.pdf`, Winbond, Rev. E, "November 23, 2017" — same part, older revision, SOIC-8-centric. Content is identical everywhere it was cross-checked; cited only where it adds or differs.
- **[RP2350-HWG]** = `Refrences/datasheets/RP2350-hardware-design-guide.pdf` — consulted **only** for QSPI flash interface requirements (Chapter 3, "Flash Memory"), per task scope. Notably, this guide's own reference design uses **this exact part** (`W25Q128JVS`) as its primary flash, and documents a second-flash-on-GPIO0-CS pattern that is directly relevant to the two-device question.

Where a figure is not stated in either datasheet, this document says so explicitly rather than estimating.

## Part identity

- Device: W25Q128JV, 128 M-bit (16 MB) Serial NOR Flash, Dual/Quad SPI, "3V" family. [W25Q128JV §1, p.4]
- Ordering breakdown of the exact P/N used on this board, **W25Q128JVSIQ**: `W25Q128JV` + `S` (8-pin SOIC 208-mil) + `I` (Industrial, −40 to +85 °C) + `Q` ("Green package... **with QE = 1 (fixed) in Status Register-2**. Backward compatible to FV family"). [W25Q128JV §11, p.74]
- **QE is factory-fixed to 1 on the IQ suffix and cannot be cleared.** Consequence: `/WP` and `/HOLD` are **permanently** IO2/IO3 on this part — it can never be strapped back into a mode where those pins behave as a hardware write-protect or hold input. [W25Q128JV §7.1.4, p.16; §11.1, p.74 note 5: "/HOLD function is disabled to support Standard, Dual and Quad I/O without user setting."]
- Manufacturer ID: EFh (Winbond, JEDEC-assigned). Device ID (90h opcode): 17h/4018h depending on read command. [W25Q128JV §8.1.1, p.21]
- Array organization: 65,536 pages × 256 bytes; 4,096 erasable 4 KB sectors; 256 erasable 64 KB blocks (all three views equal 16,777,216 bytes = 16 MB, self-consistent). [W25Q128JV §1, p.4]
- Package for this part: **8-pin SOIC, 208-mil body** (Package Code S). [W25Q128JV §3.1, p.5; §10.1, p.67]

## Absolute maximum ratings that constrain this design

[W25Q128JV §9.1, Table, p.60]

| Parameter | Symbol | Range | Unit |
|---|---|---|---|
| Supply voltage | VCC | −0.6 to 4.6 | V |
| Voltage on any pin | VIO | −0.6 to VCC+0.4, relative to GND | V |
| Transient voltage on any pin (<20 ns) | VIOT | −2.0 to VCC+2.0 | V |
| Storage temperature | TSTG | −65 to +150 | °C |
| ESD (Human Body Model) | VESD | −2000 to +2000 | V |

Note 2 under this table specifies JEDEC J-STD-20C compliance for **Sn-Pb or Pb-free (Green) assembly** — relevant given this project's low-temperature Sn42/Bi57/Ag1 paste; the datasheet does not itself give a reflow profile limit beyond that standards reference (not specified numerically).

3V3 rail (this project's supply for this chip) sits at roughly 71% of VCC abs-max (4.6 V) — comfortable margin; no clamping/TVS is mandated by the datasheet for this pin, but see ESD row above for pin robustness under HBM only (no CDM figure given — not specified).

## Key electrical characteristics

### Operating ranges [W25Q128JV §9.2, p.60]

| Parameter | Condition | Min | Max | Unit |
|---|---|---|---|---|
| VCC | FR = 133 MHz, fR = 50 MHz | 3.0 | 3.6 | V |
| VCC | FR = 104 MHz, fR = 50 MHz | 2.7 | 3.0 | V |
| TA (Industrial, "I" suffix — this part) | | −40 | +85 | °C |

Note 1: "VCC voltage during Read can operate across the min and max range but should not exceed ±10% of the programming (erase/write) voltage" — i.e. VCC must not move by more than 10% between the read and the preceding/following program-erase operation. [W25Q128JV §9.2 note 1, p.60]

**Is 3.3 V fully in spec?** Yes, and with margin to run at the full 133 MHz clock ceiling: the project's 3V3 rail (always-on LDO) sits inside the 3.0–3.6 V window with headroom on both sides, so as long as the LDO's regulation band stays ≥3.0 V under load (a normal LDO spec, e.g. ±2–3%), the part qualifies for the 133 MHz row, not just the 104 MHz row. **Datasheet does not state an LDO tolerance requirement itself** — this is a system-level constraint on the regulator choice, not the flash.

### DC electrical characteristics [W25Q128JV §9.4, Table, p.62]

| Parameter | Symbol | Condition | Typ | Max | Unit |
|---|---|---|---|---|---|
| Standby current | ICC1 | /CS = VCC | 10 | 60 | µA |
| Power-down current | ICC2 | /CS = VCC, after B9h | 1 | 20 | µA |
| Read current, Dual/Quad @ 50 MHz | ICC3 | checkerboard pattern, DO open | 8 | 15 | mA |
| Read current, Dual/Quad @ 80 MHz | ICC3 | " | 10 | 18 | mA |
| Read current, Dual/Quad @ 104 MHz | ICC3 | " | 12 | 20 | mA |
| Write Status Register current | ICC4 | /CS = VCC | 20 | 25 | mA |
| Page Program current | ICC5 | " | 20 | 25 | mA |
| Sector/Block Erase current | ICC6 | " | 20 | 25 | mA |
| Chip Erase current | ICC7 | " | 20 | 25 | mA |
| Input leakage | ILI | | | ±2 | µA |
| I/O leakage | ILO | | | ±2 | µA |
| VIL | | | −0.5 | VCC×0.3 | V |
| VIH | | VCC×0.7 | VCC+0.4 | V |
| VOL | IOL = 100 µA | | 0.2 | V |
| VOH | IOH = −100 µA | VCC−0.2 | | V |
| CIN / COUT | VIN/VOUT = 0V, characterized only | | 6 / 8 | pF |

There is no ICC3 figure at 133 MHz in this table (only 50/80/104 MHz rows are given) — **not specified numerically**; a 133 MHz read current must be assumed to be at or above the 20 mA (104 MHz max) figure for budgeting purposes, but the datasheet gives no number.

Both program/erase-family currents (ICC4–ICC7) share the same typ 20 mA / max 25 mA envelope regardless of which of Write-Status/Page-Program/Sector-Erase/Block-Erase/Chip-Erase is active — useful for a single worst-case current budget line during any write-family operation.

### Standby / power-down current comparison

Standby (deselected, no power-down command issued): 10 µA typ / 60 µA max.
Deep power-down (after B9h): 1 µA typ / 20 µA max.
The always-on-3V3, no-battery framing of this project means neither of these matters much for battery life, but the *decade* difference does matter if this rail also has to satisfy a tight power budget from the shared 3V3 LDO across many tiles — deep power-down is worth using for the second (bulk/dictionary) device if it's genuinely idle most of the time (see recommended implementation).

### Clock frequency [W25Q128JV §9.6, Table, p.64]

| Description | Symbol | Max | Condition |
|---|---|---|---|
| Clock freq, all instructions except Read Data (03h) | FR (fC1) | **133 MHz** | VCC 3.0–3.6 V |
| Clock freq, all instructions except Read Data (03h) | FR (fC2) | **104 MHz** | VCC 2.7–3.0 V |
| Clock freq, Read Data (03h) instruction only | fR | **50 MHz** | — |

This is the single most important number for the QSPI vs. standard-SPI distinction: **plain Read Data (03h) is capped at 50 MHz regardless of VCC**, while Fast Read (0Bh), Fast Read Dual/Quad Output (3Bh/6Bh), Fast Read Dual/Quad I/O (BBh/EBh), page program, and erase instructions can all run up to 133 MHz (at 3.0–3.6 V). There is no separate, higher ceiling specifically for Quad mode over Fast/Dual mode — **133 MHz is the ceiling for the SPI clock itself in every fast mode**; "quad" increases *bits per clock* (4 vs 1), giving an *equivalent* data rate of up to 532 MHz-worth of throughput at the same 133 MHz clock, not a higher clock. [W25Q128JV §1, p.4: "SPI clock frequencies... up to 133MHz... equivalent clock rates of 266MHz... for Dual I/O and 532MHz... for Quad I/O"]

**Dummy-cycle configurability:** this part has **no dummy-cycle configuration bits**. Status Register-3 exposes only WPS (protect scheme select) and DRV1:0 (output driver strength) as writable fields [W25Q128JV §7.1, Fig. 4c, p.16] — there is no equivalent of the configurable-dummy-cycle field some other Winbond/GD25 parts expose. Dummy-cycle counts are **fixed per instruction**: 8 dummy clocks for Fast Read (0Bh)/Fast Read Dual Output (3Bh)/Fast Read Quad Output (6Bh); 4 dummy clocks (after the M7-0 mode byte) for Fast Read Dual I/O (BBh) and Fast Read Quad I/O (EBh). [W25Q128JV §8.2.7–§8.2.11, pp.29–33] All of these dummy-clock counts are already what's needed to hit the 133 MHz ceiling — the datasheet frames the 8/4 dummy clocks as *the mechanism* that lets these instructions reach FR, not an optional tradeoff.

### AC timing highlights [W25Q128JV §9.6, pp.64–65]

| Parameter | Symbol | Min | Typ | Max | Unit |
|---|---|---|---|---|---|
| /CS High → Power-down mode | tDP | | | 3 | µs |
| /CS High → Standby (no ID read) | tRES1 | | | 3 | µs |
| /CS High → Standby (with ID read) | tRES2 | | | 1.8 | µs |
| /CS High → next instruction after Suspend | tSUS | | | 20 | µs |
| /CS High → next instruction after Reset | tRST | | | 30 | µs |
| /RESET pin low period to reset | tRESET | 1(note4) | | | µs |
| Write Status Register time | tW | | 10 | 15 | ms |
| Page Program time | tPP | | 0.4 | 3 | ms |
| Sector Erase (4 KB) | tSE | | 45 | 400 | ms |
| Block Erase (32 KB) | tBE1 | | 120 | 1,600 | ms |
| Block Erase (64 KB) | tBE2 | | 150 | 2,000 | ms |
| Chip Erase | tCE | | 40 | 200 | **s** |

Note 4: "It's possible to reset the device with shorter tRESET (as short as a few hundred ns), a 1 µs minimum is recommended to ensure reliable operation." [W25Q128JV §9.6 note 4, p.65]

### Endurance and retention [W25Q128JV §2 "Features", p.4]

- Minimum **100K program-erase cycles per sector**.
- **>20-year data retention** (temperature/condition not further specified in the Features list — the standard JEDEC retention test condition is implied but not restated numerically here — **not specified**).

## One chip or two? (XIP + bulk storage coexistence analysis)

This is the crux of the schematic decision, and the datasheet gives a fairly direct answer for the *hazard*, plus one documented mechanism to mitigate it.

**1. During any program/erase/write-status cycle, the device stops answering reads — full stop, with one narrow exception.**

> "BUSY is a read only bit... set to a 1 state when the device is executing a Page Program, Quad Page Program, Sector Erase, Block Erase, Chip Erase, Write Status Register or Erase/Program Security Register instruction. **During this time the device will ignore further instructions except for the Read Status Register and Erase/Program Suspend instruction.**" [W25Q128JV §7.1.1, p.13]

> "If a Read Data instruction is issued while an Erase, Program or Write cycle is in process (BUSY=1) the instruction is ignored and will not have any effects on the current cycle." [W25Q128JV §8.2.6, p.28]

That means: any XIP fetch that misses the RP2350's instruction cache while a dictionary write/erase is in flight on the *same die* gets ignored by the flash — not queued, not delayed, **ignored**. The CPU would stall waiting for data that never arrives until BUSY clears. This is the datasheet-grounded version of the "NOR flash typically cannot be read while it's being written" caveat the task called out, confirmed explicitly for this part.

**2. Erase/Program Suspend (75h) is the documented escape hatch, but it's a firmware-managed mechanism, not something a hardware XIP engine does automatically.**

> "The Erase/Program Suspend instruction '75h', allows the system to interrupt a Sector or Block Erase operation or a Page Program operation and then read from or program/erase data to, **any other sectors or blocks**." [W25Q128JV §8.2.19, p.42]

Constraints on this mechanism, all from the same section:
- Suspend is valid only for **Sector or Block Erase or Page Program** — "If written during the Chip Erase operation, the Erase Suspend instruction is ignored." So a full-chip erase (e.g. bench reprovisioning) cannot be interrupted at all.
- Suspending takes up to tSUS = 20 µs; resuming requires the same tSUS gap before another suspend can be issued — real, if small, overhead per suspend/resume pair.
- **"Unexpected power off during the Erase/Program suspend state will reset the device and release the suspend state... The data within the page, sector or block that was being suspended may become corrupted."** [W25Q128JV §8.2.19, p.42] This is a direct, named hazard for a board that explicitly has no battery and is expected to see supply dips from neighbor hot-plugs.
- Using suspend/resume to let XIP continue during a dictionary write requires the firmware/bootrom to *actively* issue 75h before the read burst and 7Ah after — RP2350's hardware XIP/QMI cache-fill path (triggered by an instruction-cache miss) has no documented awareness of this instruction; making it work would require either disabling XIP during any dictionary write (defeating the point) or a from-scratch software protocol wrapping every dictionary write in explicit suspend/resume pairs synchronized with anything that might touch code memory — non-trivial, and the datasheet gives no guarantee about what happens if a normal (non-suspend-aware) read instruction is issued while SUS=1 on the *same* sector that's suspended, only that it works for *other* sectors/blocks. **Not specified**: behavior of a plain Read Data/Fast Read aimed at the specific sector/block that is itself suspended.

**3. Program/erase timing versus the 1 ms scan-loop constraint.** Even ignoring Suspend, a single Page Program (up to 3 ms max), Sector Erase (up to 400 ms max), 64 KB Block Erase (up to 2 s max), or Chip Erase (up to 200 s max) [W25Q128JV §9.6, p.65] each vastly exceeds the board's sub-1 ms/1000 Hz key-scan budget. If firmware code or scan-loop data ever needs a cache-miss fetch from the same die during one of these operations, the scan loop misses its deadline for the entire duration of the write — not just once, but for as long as BUSY stays set. A large dictionary write (megabytes, at up to 400 ms per 4 KB sector erase or 2 s per 64 KB block erase) could stall the scan loop for a very long time if it shares a die with code the CPU needs to keep fetching.

**4. What a single device *can* do to reduce (not eliminate) the blast radius: Block Protect / Individual Block Locks.**

Both write-protect schemes give a way to partition the 16 MB array so that firmware sectors are protected from any dictionary-write mistake, but neither changes the coexistence hazard above — they're data-integrity guards, not a fix for the BUSY-blocks-reads problem, and the finer-grained one still defaults to "everything erasable" at boot unless deliberately provisioned:
- **CMP/SEC/TB/BP[2:0]** (WPS=0, factory default): protects a *fractional, contiguous* Top or Bottom region of the array — e.g. lower 1/16 (1 MB), lower 1/8 (2 MB), etc. — only fixed fractional splits are available, not arbitrary boundaries. [W25Q128JV §7.1.8/§7.1.9, pp.18–19]
- **Individual Block/Sector Locks** (WPS=1): per-64 KB-block granularity across the whole array (4 KB granularity only within the top/bottom blocks). **Default state on power-up is all-blocks-locked** — nothing is erasable until explicitly unlocked with `Individual Block Unlock (39h)`. [W25Q128JV §6.5.1, p.12] This is a genuinely useful fail-safe default (an unprovisioned or freshly-reset chip cannot have its firmware region erased by accident), and gives arbitrary-boundary partitioning at 64 KB (or 4 KB at the array edges) resolution for a firmware/dictionary split on one physical device.

**5. Conclusion for this design question (datasheet-grounded, not a recommendation of which schematic choice is "right", since that's for the diff):**
- A single device **can** technically hold both firmware and dictionary, and the write-protect mechanisms above can guard the firmware region from being erased by dictionary-write bugs.
- What a single device **cannot** do, per this datasheet, is let XIP code fetches or scan-loop-critical data reads continue *uninterrupted* while any dictionary program/erase is in flight on the same die — the exception (Suspend) is a firmware-orchestrated, per-erase-operation opt-in, not a free "read while write" capability, and it explicitly does **not** cover Chip Erase and explicitly risks data corruption if power is interrupted mid-suspend — a real risk on a hot-plug, no-battery, dip-prone bus.
- Two physically separate devices sidestep the BUSY-blocks-reads problem entirely, because each die's BUSY state is independent (see next section for exactly how sharing the bus interacts with this) — at the cost of a second footprint, a second /CS line + pull-up, and a second BOM line.
- The size of the risk is proportional to **how often the dictionary is actually written at runtime**. The task frames it as "a large read-mostly dataset" — if writes only happen during an explicit provisioning/update mode (not concurrently with normal keyboard use), the single-device BUSY hazard may be an acceptable, well-understood risk; if the dictionary can be updated live while the board is being typed on, the hazard is much harder to accept given the sub-1 ms scan deadline.

## Two devices on one QSPI bus

**Deselection is a real, documented high-Z state**, not merely implied: "When /CS is high the device is deselected and the Serial Data Output (DO, or IO0, IO1, IO2, IO3) pins are at high impedance." [W25Q128JV §4.1, p.9] This is stated for the DO/IOx pins specifically; CLK and DI are simplex inputs on the device side regardless of selection state, so bus sharing of CLK/DI (or IO0 as bidirectional in quad mode) is only a concern for driving contention on the shared output/IO lines, which the deselected-Hi-Z behavior above resolves as long as only one device is ever selected (one /CS low) at a time — the datasheet's own /HOLD description implicitly assumes exactly this topology: "The /HOLD function can be useful when **multiple devices are sharing the same SPI signals**." [W25Q128JV §4.4, p.9]

**The shared bus is still fully time-multiplexed — a second /CS does not give simultaneous access.** CLK, DI/IO0, DO/IO1 (and IO2/IO3 in quad mode) are shared wires; only one device can be selected and driving/receiving at any instant regardless of how many chip-selects exist. The actual benefit of a second physical device comes from **program/erase being self-timed and running in the background after /CS goes high**, explicitly stated for every erase instruction, e.g.: "The /CS pin must be driven high after the eighth bit of the last byte has been latched... After /CS is driven high, the **self-timed** Sector Erase instruction will commence for a time duration of tSE." [W25Q128JV §8.2.15, p.38; same wording for 32 KB/64 KB Block Erase §8.2.16/§8.2.17] Because the erase/program cycle continues internally on the die **after** the SPI bus is released, a controller can start a dictionary-chip erase, deselect it, and immediately go talk to the boot-flash chip over the same physical CLK/DI/DO/IOx wires while the dictionary chip's internal cycle finishes in the background — polling its BUSY bit later via a Read Status Register (05h) transaction. That is the mechanism by which two devices genuinely decouple XIP-availability from dictionary writes; it is not "parallel" electrical operation, it's asynchronous background completion plus bus time-sharing.

**Pull-ups/series resistors on shared CLK/data lines:** the datasheet gives **no** general multi-drop bus guidance (impedance, stub length, termination) beyond the deselected-Hi-Z statement and the /HOLD note above — **not specified**. Practical multi-drop SPI guidance (short stubs, one clock source, matched trace lengths) is standard SI practice but isn't sourced from this datasheet.

**Do the two /CS pull-ups interact?** Each device's /CS is a simple high-impedance input (input leakage ±2 µA max, [W25Q128JV §9.4, p.62]) with no internal pull resistor documented on the SOIC-8 package (contrast: the /RESET pin on SOIC-16/TFBGA packages explicitly does have "an internal pull-up resistor" [W25Q128JV §6.4 note 3, p.11] — /CS has no equivalent statement, so assume none). Two independent /CS nets, each with its own pull-up to the shared 3V3 rail and its own GPIO driver, do not interact electrically with each other — they're separate nodes. The only shared consideration is that **both devices' VCC and GND are the same rails**, so both need decoupling and both need to be included in supply-current budgeting; and per **[RP2350-HWG Ch.3.2, p.11]**, if the second chip-select line is a GPIO that "defaults to be pulled low at power-up" (true of RP2350's GPIO0/XIP_CS1n), an external pull-up on that CS **is** mandatory — a floating/default-low GPIO driving that flash's /CS low at power-up before firmware configures it would select the device prematurely during the VCC ramp, exactly the failure mode the primary-flash /CS pull-up guidance is trying to avoid.

## Design equations

### /CS pull-up resistor

The datasheet only says a pull-up "can be used" to make /CS track VCC at power-up/down, without giving a target value or bound. [W25Q128JV §4.1, p.9; §9.3, p.61] A loose upper bound can be derived from input leakage: to keep /CS from sagging below VIH_min = 0.7×VCC under the worst-case ±2 µA input leakage [W25Q128JV §9.4, p.62]:

R_max = (VCC − 0.7×VCC) / ILI_max = 0.3×VCC / ILI_max

At VCC = 3.0 V (low end of the 133 MHz operating range) and ILI_max = 2 µA: R_max = 0.3 × 3.0 V / 2 µA ≈ **450 kΩ** — an extremely loose bound; leakage alone does not meaningfully constrain the pull-up value. The lower bound is set by the driving GPIO's sink-current spec when it needs to pull /CS low through the pull-up — that figure is an RP2350 GPIO characteristic, outside this document's sourced datasheets (**not determinable from the two flash datasheets**).

- Ideal (per RP2350-HWG's own worked reference design for exactly this part and exactly this purpose): **10 kΩ**. [RP2350-HWG §3.1 R1, §3.2 R13, p.10–11]
- Nearest E24 value: **10 kΩ** (already a standard value).
- Actual: 10 kΩ.
- Error: 0%.

This value sits comfortably inside the ~450 kΩ leakage-derived ceiling, so 10 kΩ is not a marginal choice.

Notably, **[RP2350-HWG]** marks the *primary*-flash pull-up (R1) as DNF (do-not-fit) specifically for this part: "we have found that with this particular flash device, the external pull-up is unnecessary" because RP2350's own QSPI_SS pin defaults to an internal pull-up during boot — but keeps the resistor footprint present "just in case" a different flash is substituted. [RP2350-HWG §3.1, p.10] The *secondary*-flash pull-up (R13) is explicitly called "definitely needed" because the RP2350 GPIO used for the second CS defaults low at power-up. [RP2350-HWG §3.2, p.11] This distinction matters directly for a two-device schematic on this board.

### Decoupling capacitor

Neither W25Q128JV datasheet gives a recommended decoupling value — **not specified**. [RP2350-HWG]'s own reference schematic places a 100 nF capacitor (C2) directly at the primary flash's VCC pin [RP2350-HWG §3.1 Fig.8, p.10], and calls out that the optional secondary device needs the equivalent (C22) "for local power supply decoupling for U4" if populated [RP2350-HWG §3.2, p.11]. No formula is given for sizing this beyond the standard "place close to VCC pin" guidance; treat 100 nF X7R as the precedent value, default 0402 per this project's convention.

## Worked values for this application

| Quantity | Value | Basis |
|---|---|---|
| VCC | 3.3 V nominal, always-on LDO | Project spec; within [W25Q128JV §9.2, p.60] 3.0–3.6 V band for full 133 MHz operation |
| Max SPI clock (fast/dual/quad instructions) | 133 MHz | [W25Q128JV §9.6, p.64], at VCC ≥ 3.0 V |
| Max clock for plain Read Data (03h) | 50 MHz | [W25Q128JV §9.6, p.64] — this is what RP2350's bootROM flash-probe sequence uses, at ~1 MHz, per [RP2350-HWG §3.3, p.12], well within margin |
| Standby current per device (worst case) | 60 µA | [W25Q128JV §9.4, p.62] |
| Active read current per device (104 MHz, worst case) | 20 mA | [W25Q128JV §9.4, p.62] (133 MHz figure not given) |
| Program/erase current per device (worst case, any op) | 25 mA | [W25Q128JV §9.4, p.62] |
| Two devices both idle | 2 × 60 µA = 120 µA max | Additive, independent standby currents |
| Two devices, one erasing + one reading (worst case, simultaneous) | 25 mA + 20 mA = 45 mA | Sum of independent worst-case figures — realizable per the "self-timed background erase + bus-share for the other device" mechanism above |
| /CS pull-up (both nets, if two devices used) | 10 kΩ, E24, 0% error | See Design equations |
| Decoupling cap per device | 100 nF, 0402 | Precedent value, [RP2350-HWG §3.1, p.10] — not numerically specified by the flash datasheet |
| Sector erase time (4 KB), worst case | 400 ms | [W25Q128JV §9.6, p.65] |
| 64 KB block erase, worst case | 2 s | [W25Q128JV §9.6, p.65] |
| Chip erase, worst case | 200 s | [W25Q128JV §9.6, p.65] |
| Page program, worst case | 3 ms | [W25Q128JV §9.6, p.65] |

## Recommended implementation (pin by pin, for both the boot device and a possible second device)

Pinout is identical for both devices (SOIC-8 208-mil, package code S): [W25Q128JV §3.1, p.5]

| Pin | Name (Quad mode) | Boot device (chip 1) | Second device (chip 2, if used) |
|---|---|---|---|
| 1 | /CS | QSPI_SS / RP2350 dedicated flash CS, with 3.3V pull-up (RP2350-HWG marks this DNF for this exact part — RP2350's QSPI_SS defaults pulled up internally — but keep the footprint) | A GPIO configured as the second chip-select (e.g. RP2350 XIP_CS1n / GPIO0), **with a populated 10 kΩ pull-up** — this GPIO defaults low at power-up per [RP2350-HWG §3.2, p.11], so the pull-up here is not optional |
| 2 | DO/IO1 | QSPI_SD1, shared bus | Same shared bus net |
| 3 | /WP → IO2 | QSPI_SD2, shared bus. **QE is factory-fixed to 1 on this "Q"-suffix part, so this pin is always IO2 — never usable as a hardware write-protect input.** [W25Q128JV §7.1.4, p.16; §11.1 note 5, p.74] | Same |
| 4 | GND | Common ground | Common ground |
| 5 | DI/IO0 | QSPI_SD0, shared bus | Same shared bus net |
| 6 | CLK | QSPI_SCLK, shared bus, short direct trace | Same shared bus net |
| 7 | /HOLD → IO3 | QSPI_SD3, shared bus. Same QE-fixed caveat as pin 3 — /HOLD is never usable; this is always IO3. | Same |
| 8 | VCC | 3V3 rail, local 100 nF decoupling at the pin | 3V3 rail, local 100 nF decoupling at the pin |

Both devices share CLK, DI/IO0, DO/IO1, IO2, IO3 on one physical bus; only /CS differs per device, per the standard SPI multi-drop topology the datasheet's /HOLD note assumes. [W25Q128JV §4.4, p.9]

Note this package (SOIC-8 / S code) has **no dedicated hardware /RESET pin** — that only exists on the 16-pin SOIC-300mil and TFBGA packages. [W25Q128JV §3.1 vs §3.4, pp.5–6; §4.6, p.9: "A dedicated hardware /RESET pin is available on SOIC-16 and TFBGA packages"] Reset on this part is software-only: `Enable Reset (66h)` + `Reset (99h)`, ~30 µs (tRST), or a full VCC power cycle below VWI. [W25Q128JV §6.4, p.11] This is a real constraint given the RP2350-HWG's own caution about the flash getting stuck in a continuous-read XIP mode across an RP2350-side (non-power-cycled) reset [RP2350-HWG §3.3, p.12] — recovery on this package relies entirely on either the bootROM's documented best-effort CSn/IO toggle sequence or a full power cycle; there is no hardware-pin escape hatch as there would be with the 16-pin package.

## Decoupling and passives

- 100 nF (0402, X7R or better) directly at each device's VCC pin (pin 8), shortest possible loop to GND (pin 4) — precedent value per [RP2350-HWG §3.1/§3.2, p.10–11]; not a datasheet-mandated figure.
- No bulk/reservoir capacitor value is specified by either flash datasheet or the hardware design guide excerpt reviewed — **not specified**. Given the project's own stated risk (supply dips from neighbor hot-plug events) and that this rail is shared with the MCU/Hall sensors/mux, bulk capacitance sizing is a system-level 3V3-rail decision, not a per-flash-chip one, and is outside this chip's datasheet.
- /CS pull-up: 10 kΩ, 0402, per Design Equations above — required (populated) on any GPIO-sourced chip-select that defaults low or floating at power-up; may be DNF/unpopulated-footprint on a /CS driven by a controller pin that is documented to default high (e.g. RP2350's dedicated QSPI_SS), per [RP2350-HWG §3.1, p.10].
- No termination or series resistor value is specified by the flash datasheet for CLK/DI/DO — **not specified**; see Layout notes for the general practice this leaves unquantified.

## Layout notes

- CLK/DI/DO/IOx should be routed as short, direct connections between MCU and flash to preserve signal integrity and minimize crosstalk — this is [RP2350-HWG]'s own guidance for the primary flash link, not the flash datasheet's: "the QSPI pins of RP2350 should be wired directly to the flash, using short connections to maintain the signal integrity, and to also reduce crosstalk in surrounding circuits." [RP2350-HWG §3.1, p.10]
- /CS pull-up resistors "should be placed close to the flash chip" to avoid extra copper length affecting the strapping signal. [RP2350-HWG §3.1, p.10]
- With two devices sharing one bus, the shared CLK/DI/DO/IOx nets now fan out to two loads instead of one — keep both stub lengths short and roughly matched; the datasheet gives no multi-drop impedance/stub-length numbers, so this is general SI practice, not a sourced spec (**not specified** by either datasheet).
- Package footprint: SOIC-8, 208-mil body — body length/width ≈5.28 mm nominal, overall span with leads (H) ≈7.90 mm nominal, pitch 1.27 mm (50 mil), max package height 2.16 mm. [W25Q128JV §10.1, Table, p.67] This is a *wider* SOIC-8 than the common 150-mil/3.9 mm-body SOIC-8 footprint — footprint choice in the PCB library must match "208-mil," not generic "SOIC-8."
- Max package height 2.16 mm — relevant to the project's low-profile constraint but not itself a binding figure without knowing the stack-up clearance available (**not evaluated further here**, outside chip-level datasheet scope).

## Gotchas and failure modes

1. **QE is fixed to 1 on this exact part number — /WP and /HOLD are permanently unavailable as hardware pins.** Any schematic note or silkscreen implying a jumper-selectable write-protect or hold function on this chip is wrong for the "Q"-suffix variant; those pins are IO2/IO3, full stop, and must be wired into the quad bus (not left as spare GPIO-controllable protect/hold lines). [W25Q128JV §7.1.4, p.16; §11.1 note 5, p.74]
2. **No hardware /RESET pin on SOIC-8.** If the RP2350 resets without a full power cycle while the flash is mid-continuous-read-mode, recovery depends entirely on the bootROM's best-effort CSn/IO toggle sequence [RP2350-HWG §3.3, p.12] — there's no pin to force a clean flash-side reset the way the 16-pin/TFBGA packages allow. Worth an explicit test: reset the RP2350 (not the whole board) while a quad continuous-read is active and confirm the bootROM's documented sequence actually recovers it on this specific device.
3. **/CS floating during VCC ramp is explicitly flagged as unsafe by the datasheet.** "/CS must track VCC" during ramp up/down [W25Q128JV Fig.58b, p.61], and "Program, Erase and Write Instructions are ignored" only while VCC is still below VCC(min) — a /CS pin driven by an MCU GPIO that is itself not yet configured (or briefly tri-stated) during this project's cold-start or hot-plug power-up could leave /CS indeterminate exactly while VCC's ratiometric VIL/VIH thresholds (0.3×VCC / 0.7×VCC) [W25Q128JV §9.4, p.62] are also moving — a pull-up tied to the same VCC rail is the datasheet's own recommended fix for this. [W25Q128JV §9.3, p.61; §6.5.1, p.12]
4. **Supply dips during a self-timed program/erase are not covered by the datasheet at all.** The only power-interruption behavior documented is for the *Suspend* state specifically ("data... may become corrupted" [W25Q128JV §8.2.19, p.42]) — there is no equivalent statement for a plain (non-suspended) program/erase cycle interrupted by a VCC dip. Given this project explicitly expects supply dips from neighbor tile hot-plugs, this is a real, un-quantified risk for both the boot flash (bricking a tile) and the dictionary flash (silent corruption) any time a write happens to coincide with a hot-plug event elsewhere on the shared bus rails. **Not specified** what actually happens; treat as "assume corruption is possible" and avoid triggering writes during any window where a hot-plug is plausible, and/or add CRC/redundancy at the firmware level.
5. **Erase Suspend does not cover Chip Erase.** A full-chip reprovisioning erase (bench/factory step) cannot be paused for any reason; plan for that to be a dedicated, non-interruptible maintenance operation, not something done on a live/assembled system. [W25Q128JV §8.2.19, p.42]
6. **A second device's GPIO-sourced /CS needs its pull-up populated, not DNF.** RP2350's second XIP chip-select GPIO defaults **low** at power-up, unlike the dedicated QSPI_SS pin (defaults high/pulled-up) — omitting this pull-up (by analogy with the primary flash's DNF pull-up) would select the second flash prematurely during power-up. [RP2350-HWG §3.2, p.11]
7. **ICC3 (active read current) has no published figure at 133 MHz**, only at 50/80/104 MHz — budgeting the 3V3 rail at the full clock rate this design targets requires either headroom above the 104 MHz max (20 mA) figure or bench measurement; the datasheet doesn't give the number needed. [W25Q128JV §9.4, p.62]

## Open questions / not determinable from the datasheet

- **LDO tolerance requirement to guarantee ≥3.0 V (for the full 133 MHz spec) under worst-case load** — a system-level regulator spec, not in either flash datasheet.
- **RP2350 GPIO sink-current spec**, needed to compute a true lower bound on the /CS pull-up value — out of scope per this task's instruction to consult the hardware design guide only for QSPI interface requirements, and not covered by the flash datasheets themselves.
- **RP2350 QMI's actual maximum supported SPI/QSPI clock, and whether it can address two independent chip-selects with genuinely independent read/write scheduling (vs. the host-side driver simply time-slicing manually)** — this requires the RP2350 datasheet's QMI chapter, explicitly out of scope for this document per task instructions ("For more details on the QSPI, please see QSPI Memory Interface (QMI) in the RP2350 datasheet" — [RP2350-HWG §3.2, p.11] — not read here).
- **Behavior of a plain (non-suspend-aware) Read Data/Fast Read instruction targeting the specific sector/block that is itself in the Suspended state** — the datasheet documents reads/writes to *other* sectors during Suspend but is silent on the suspended sector/block itself.
- **What actually happens to an in-progress self-timed program/erase cycle if VCC dips below VCC(min) (or below VWI) mid-cycle without a full power-down** — not covered anywhere in either datasheet; only the Suspend-state power-interruption case is documented.
- **ICC3 read current at 133 MHz** — table stops at 104 MHz.
- **Data retention test condition/temperature behind the ">20-year" figure** — Features list states the headline number without the underlying test condition.
- **Recommended bulk/reservoir decoupling capacitance value** — neither the flash datasheet nor the hardware design guide excerpt gives a number; only a 100 nF per-device bypass cap is shown by example.
- **Whether JLCPCB/LCSC stock for this exact SOIC-8 208-mil part matches the schematic's footprint library entry** — a sourcing question, out of scope for a datasheet-only research pass.
