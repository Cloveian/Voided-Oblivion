# Sourcing Pass — 2026-08-09

**Scope:** LCSC part-number backfill onto `Voided-Oblivion.kicad_sch`, `power.kicad_sch`, `keys.kicad_sch`.
**Result:** **311 of 373** placed components now carry `LCSC` + `MPN` + `Manufacturer` symbol properties (48 unique LCSC lines: 14 Basic, 4 Preferred, 30 plain-Extended → ~$90 in one-time setup fees). All 48 verified against the JLCPCB catalogue snapshot dated 2026-08-07. Every assigned part has ≥3× the stock needed for a 4-board run — no stock risk remains anywhere in the BOM.

This page records only what is **wrong, blocked, or contradictory**. Everything not listed here checked out.

---

## 1. The previous sourcing pass's results are not in the schematic files

`research/bom-sourcing.md` §*Properties written* and `schematic-design/power.md` §*To do* both record the LCSC/MPN/Manufacturer fields as written. **They are not present in the working files, and never were in any committed revision** (`git show HEAD:…` → 5 `LCSC` properties in `power.kicad_sch`, 0 in the other two).

The work was real and is recoverable as evidence: `Voided-Oblivion-backups/Voided-Oblivion-2026-08-07_210405.zip` contains a `power.kicad_sch` with **83** `LCSC` properties and the `APH0630` inductor assignment. But the schematics inside that zip are the **2026-08-05/08-07 design generation** (root sheet 218 KB vs 382 KB today) — they predate the pogo edge connectors, the submodule ID dividers, U15/U12/U16, and Q4–Q11. Restoring from it would roll the design back, so this pass re-derived the assignments instead and used the backup only as a cross-check on prior intent.

**Consequence:** the review's finding F5 ("MPN coverage 1%") described the files accurately; the two docs above overstate the state of the schematic. Trust the files, not the checkboxes.

---

## 2. `C83711` is 0.75 pF, not 75 pF — a 100× error carried in the docs

`research/bom-sourcing.md` §1 assigns **C83711 / `0402CGR75C500NT`** to **C30 and C36**, described as "75pF, C0G/NP0 50V".

The LCSC listing for C83711 reads **`0.75pF 50V C0G 0402`**. The MPN encodes it: `R75` is the decimal-point form for 0.75 pF; 75 pF would be `750`. The correct Fenghua part is **`0402CG750J500NT` = C37809** (75 pF, 50 V, C0G, ±5%, Extended, 21,458 stock, $0.0012).

This matters: the netlist puts C30 across `U5.FB` and C36 across `U6.FB` — they are the **TPS54302 feedforward capacitors**, i.e. loop compensation. A 0.75 pF part there is a 100× compensation error, not a tolerance nit.

**Action taken:** C30/C36 assigned **C37809**. The wrong number is still printed in `research/bom-sourcing.md` §1 and §8 and should be corrected there.

---

## 3. Footprint/value contradictions — four capacitor groups, nothing assigned

In every case the *previous* design generation had a footprint that worked and the current schematic has a 0402 that cannot. These read as footprint regressions, not new decisions. **No part was forced onto any of them.**

| Refs | Value | Current footprint | Net (from netlist) | Why nothing was assigned | Prior generation |
|---|---|---|---|---|---|
| **C26, C31** | 10 µF | `C_0402_1005Metric` | `PD+` (reaches 20 V) | A catalogue-wide query returns **zero** 10 µF 0402 parts rated above **10 V**. Not a sourcing gap — the part does not exist. | 1206, **C89632** (`CL31B106KBHNNNE`, 10 µF **50 V** X7R) |
| **C28, C29** | 22 µF | `C_0402_1005Metric` | `+5VA` | see below | 1206, **C12891** (`CL31A226KAHNNNE`, 22 µF 25 V X5R, Basic) |
| **C34, C35** | 22 µF | `C_0402_1005Metric` | `+5VP` | see below | 1206, **C12891** |

**On the 22 µF group specifically:** 22 µF 0402 parts *do* exist, but only at **6.3 V and 10 V** X5R (best-stocked: C105226 6.3 V, C3845593 10 V). Neither is usable here. The 6.3 V parts fail derating against a 5.08 V rail outright; the 10 V parts pass derating but lose roughly half their capacitance at 5 V DC bias, which is exactly the failure mode review finding **F13** already called out — the TPS54302 Table 7-2 stability design assumes **44 µF total** per output, and two bias-collapsed 0402s deliver nowhere near that.

So the constraint is not voltage rating, it is DC-bias derating plus loop stability. **The fix is the footprint, not the part number:** restore these four to a 1206 (or at minimum 0805) land and C12891 becomes valid again with no other change. Same for C26/C31 with C89632.

---

## 4. R31 — 12.2 kΩ does not exist on LCSC, at any package, at any tolerance

R30/R31 form the comparator trip divider off `VBUS` (netlist: `R30` VBUS→VDIV, `R31` VDIV→GND). `power.md` requires **0.5 %** here; review **F8** flags the tolerance as unencoded.

- **R30 (44.2 kΩ) — assigned `C2683024`** (`ARG02BTC4422`, Viking Tech, thin film, **±0.1 %**, ±25 ppm/°C, 10,005 stock, $0.022). Judgement call: the only true ±0.5 % 0402 at this value is `C705671` (`RT0402DRD0744K2L`, 113 stock). C2683024 is a *tighter* tolerance, better tempco and ~90× the stock for ~2× the (negligible) unit price, so it satisfies the 0.5 % requirement with margin rather than merely meeting it.
- **R31 (12.2 kΩ) — not assigned.** A direct query of the full catalogue for `12.2k` in the resistor category returns **0 rows**, any package, any tolerance. This confirms `bom-sourcing.md` §6.1: 12.2 k is not an E96 value (E96 has 12.1 k and 12.4 k) and LCSC does not stock the E192 grid at 0402.

**Not substituted, deliberately.** For whoever redoes this: the nearest stocked 0.5 % neighbour is **C4217510** (`RC0402DR-0712K4L`, 12.4 kΩ, ±0.5 %, 10,000 stock). Swapping it moves the trip point from `1.24 × (44.2+12.2)/12.2 = 5.73 V` to `1.24 × (44.2+12.4)/12.4 = 5.66 V` — a **−72 mV** shift against a margin budget the docs put at ~180 mV. That is a real fraction of the budget, so it needs the divider re-derived, not a drop-in.

Practical alternatives unchanged from `bom-sourcing.md`: hand-solder R30/R31 from DigiKey/Mouser (both carry E192 0402 at 0.5 %), or recompute the divider onto a stocked pair.

---

## 5. `C49654456` (49.9 Ω, R18/R24) is gone from the catalogue

The part assigned by `bom-sourcing.md` §2 (`GR0402F49R9TAG00`, GiantOhm, noted there at only 10.0 K stock) returns **not found** in the 2026-08-07 snapshot.

**Replaced with `C140147`** (`RC-02K49R9FT`, Fenghua, 49.9 Ω ±1 % 0402, **145,977 stock**, $0.00067) — same spec, three orders of magnitude more stock. Flagging rather than silently swapping because it changes a line in the published BOM.

---

## 6. L2 / L3 have the part but no footprint

`power.md` §*To do* marks **`[x] L2 = L3 = APH0630T100M`, LCSC `C5349698`, footprint `Inductor_SMD:L_APV_APH0630`** as done. The LCSC assignment has now been written (verified: C5349698, 10 µH, 4.5 A/5.5 A, 68 mΩ, 59,158 stock).

**The `Footprint` field on both L2 and L3 is still empty.** Only the footprint half of that checkbox was lost. Nothing else in this pass depends on it, but it blocks layout and will drop both parts from any position file.

---

## 7. Parts with no LCSC source (expected, listed for completeness)

| Refs | What | Why unsourced |
|---|---|---|
| J1–J8 (8) | `PG-6P-2.5-5.5H-SM-RA` pogo edge connectors | Deliberately off-catalogue, hand-soldered, single-source (Shenzhen Yiwei). Per `chips.md`. Buy spares. |
| J10–J12, J16–J20 (8) | Submodule corner connectors | **Connector body was never chosen.** `design-choices/submodules.md` §*Revision* settles the pinout (5-pin `ID GND 5V Rx Tx`) but closes with "just the connector body to pick later". All 8 symbols have an **empty Footprint field**. No part can be committed until the body is picked. |
| SW1, SW2 | Boot/reset tactile | Footprint is locked to Würth `434133025816`; no match on LCSC. Substituting a generic SMD tactile risks a pad/actuator mismatch. Hand-place, or change the footprint to a JLC-stocked switch. |
| AM0:0–AM1:14 (30) | VoidSwitch key switches | Mechanical, not an LCSC part. Left untouched, as in the prior pass. |
| C22, C37, R1, R11, R13, R28, U4 (7) | DNP placeholders | No intended part. |

---

## 8. Smaller notes

- **Two stock blockers from `bom-sourcing.md` §6 have resolved.** FUSB302BMPX (C132291) is at **6,187** units, not the 627 that prompted the "monitor before ordering" warning. The MAX40203 WLP-4 stock=1 blocker is moot — U9 is now LM66100DCKT (C2832141, 1,123 stock) and U15 is a second instance of the same part.
- **C2841482 is manufactured by UMW, not Alpha & Omega.** `chips.md` and `bom-sourcing.md` both attribute AO4407A/C2841482 to Alpha & Omega; the LCSC listing for that specific number is **UMW (Youtai Semiconductor)**, 105,495 stock. Same MPN and spec (30 V, 9.5 mΩ@10 V, SOP-8) — worth knowing only because it is a second-source house brand. The `Manufacturer` field was written as UMW to match the listing. Note this one number now covers **five** FETs (Q2 + Q4–Q7), not one.
- **Field-name inconsistency fixed.** The 30 hall sensors carried their LCSC number under a field named **`LCSC Part`**, while `power.kicad_sch` used **`LCSC`**. A BOM tool reading `LCSC` would have silently missed all 30. Renamed to `LCSC` on all 30 instances plus the cached library symbol; `MPN` was already correct and `Manufacturer` was added.
- **1 µF moved from 0805 to 0402** (C24, plus new C41/C76/C114/C120). Assigned **C52923** (`CL05A105KA5NQNC`, 1 µF **25 V** X5R, **Basic**, 12.5 M stock) — Basic tier and 25 V, so it clears BS+ at its 5.95 V worst case with wide margin. This replaces the prior 0805 pick C24123 and drops a BOM line.
- **C77 and C121** (10 µF 0402 on the ~5 V `U12.OUT` / `SM+` nodes) were assigned **C315248** (10 V) for consistency with C40 rather than the 6.3 V Basic part. At 5 V bias a 10 V 0402 still derates substantially; these are bulk decoupling on a switch output rather than loop-critical, so it is acceptable — but if either node ever needs a *known* capacitance, size the footprint up rather than the voltage rating.
- **Value-string inconsistencies from `bom-sourcing.md` §7 are unchanged** (`100n`/`100nF`/`0.1µF`, `4.7u`/`4.7µF`, `0`/`0Ω`, Q1's value reading `AO3401` against an `AO3401A` symbol). Sourcing is unaffected — each spelling group resolves to one part — but a literal-text BOM grouper will still split them.

---

## Verification performed

- Paren balance checked on all three files after writing (depth 0, string-aware).
- `kicad-cli sch export netlist` re-parses cleanly; netlist grew 563 KB → 666 KB as the new fields propagate.
- `kicad-cli sch erc` → **1 violation**, unchanged: the intentional `U12.OUT ∥ U15.VOUT` power-OR node (review F3). No regression.
- `kicad-cli sch export bom --group-by LCSC` → 49 grouped rows. **U11 (LM2903, 3 units) groups as a single line**, confirming the multi-unit symbol is counted once.
