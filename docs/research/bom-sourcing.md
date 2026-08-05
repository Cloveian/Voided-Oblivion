# BOM Sourcing Report — Voided-Oblivion (JLCPCB Assembly)

Generated 2026-08-05 (revised same day — see revision note at bottom). Covers all three schematic sheets:
`Voided-Oblivion.kicad_sch` (root/MCU), `power.kicad_sch` (power+USB), `keys.kicad_sch` (sensors/mux/RGB).

**297 placed, sourceable-or-not parts** across **89 unique (value, footprint) groups** were inventoried directly from the `.kicad_sch` S-expressions (not just the summary tool output) to guarantee every reference designator was accounted for exactly once. `LCSC`, `MPN`, and `Manufacturer` symbol properties have been written back to all schematics for every group that could be sourced. Everything below reflects what's now actually in the files.

Quantities in the tables are **per board**; multiply by 4 for the full run. Prices are LCSC unit prices at the quantities in their listing (small-qty tier) — treat them as directional, not a quote.

---

## 1. Capacitors

| Group (refs/board) | Value(s) as drawn | Footprint | LCSC | MPN | Mfr | Voltage/Dielectric | Basic/Pref/Ext | Stock | Unit $ |
|---|---|---|---|---|---|---|---|---|---|
| General 100nF-class, 0402 (89 pcs: 67×`100nF` + 16×`100n` + 6×`0.1µF`) | `100nF`/`100n`/`0.1µF` | C_0402_1005Metric | **C307331** | CL05B104KB54PNC | Samsung Electro-Mechanics | X7R **50V** | **Basic** | 15.9M | $0.0033 |
| 10µF, 1206, PD+ 20V (C26, C31) | `10µF` | C_1206_3216Metric | **C89632** | CL31B106KBHNNNE | Samsung Electro-Mechanics | X7R **50V** | Extended | 1.0M | $0.0513 |
| 22µF, 1206 (C28, C29, C34, C35) | `22µF` | C_1206_3216Metric | **C12891** | CL31A226KAHNNNE | Samsung Electro-Mechanics | X5R 25V | **Basic** | 3.2M | $0.0366 |
| 4.7µF, 0402 (5 pcs: C6, C7, C9, C10, C23) | `4.7u`/`4.7µF` | C_0402_1005Metric (2 differently-named footprint variants, see note) | **C23733** | CL05A475MP5NRNC | Samsung Electro-Mechanics | X5R 10V | **Basic** | 4.8M | $0.0045 |
| 10µF, 0402 (C40) | `10µF` | C_0402_1005Metric | **C315248** | CL05A106MP5NUNC | Samsung Electro-Mechanics | X5R **10V** | Extended | 3.2M | $0.0078 |
| 10µF, 0805 (C19) | `10u` | C_0805_2012Metric | **C95841** | CL21B106KOQNNNE | Samsung Electro-Mechanics | X7R 16V | Extended | 717K | $0.0223 |
| 1µF, 0805, BS+ ~6V (C24) | `1µF` | C_0805_2012Metric | **C24123** | CL21B105KOFNNNE | Samsung Electro-Mechanics | X7R 16V | Extended | 156K | $0.0092 |
| 75pF, 0402 (C30, C36) | `75pF` | C_0402_1005Metric | **C83711** | 0402CGR75C500NT | FH (Fenghua) | C0G/NP0 50V | Extended | 23.4K | $0.0011 |
| 15pF, 0402, crystal load (C3, C4) | `15p` | C_0402_1005Metric | **C1548** | 0402CG150J500NT | FH (Fenghua) | C0G/NP0 50V | **Basic** | 882K | $0.0009 |
| 1nF, 0402 (C37, C45) | `1nF` | C_0402_1005Metric | **C53547** | 0402CG102J500NT | FH (Fenghua) | C0G/NP0 50V | Extended | 280K | $0.0031 |

**Why one part covers the whole 100nF-class group:** C307331 is 50V-rated and JLC-**basic**, which comfortably exceeds every sub-requirement in that bucket — general ≥16V bypass (83 of the 89), the 0.1µF **boot caps** C27/C33 (≥16V), and the 0.1µF caps that sit directly on **PD+ at 20V** (C25, C32 — need ≥25V, prefer 50V). Using one basic part for all 89 instead of splitting into a 16V bucket + a 25V/50V bucket removes an entire BOM line and its setup-fee risk for a ~$0.002/unit premium (≈$0.7 total across 4 boards). This is the single biggest consolidation in the BOM.

**10µF 1206 note (C26/C31, PD+):** no *basic* 10µF/1206/≥25V part exists on LCSC. Both the 25V and 50V options are extended; the 50V part (CL31B106KBHNNNE) was chosen per the "strongly prefer 50V" guidance for ~$0.014/unit more (~$0.11 total across 4 boards) — trivial next to the fixed $3 extended-part fee already being paid either way.

**10µF 0402 note (C40):** the *basic* 10µF/0402 part (C15525, CL05A106MQ5NUNC) is only rated **6.3V** — confirmed via datasheet — which fails the "≥10V" requirement. Had to go extended (CL05A106MP5NUNC, 10V) instead.

---

## 2. Resistors (all 0402, all thick/thin-film chip)

| Group (refs/board) | Value(s) as drawn | LCSC | MPN | Mfr | Tolerance | Basic/Pref/Ext | Stock | Unit $ |
|---|---|---|---|---|---|---|---|---|
| 0-ohm jumper (19: R10 + 18×`0Ω`) | `0`/`0Ω` | **C17168** | 0402WGF0000TCE | UNI-ROYAL | n/a | **Basic** | 18.4M | $0.0005 |
| 100kΩ (7: R19,R25,R32,R34,R38,R39,R47) | `100kΩ` | **C25741** | 0402WGF1003TCE | UNI-ROYAL | 1% | **Basic** | 15.4M | $0.0005 |
| 4.7kΩ (6: R40–R45) | `4.7kΩ` | **C25900** | 0402WGF4701TCE | UNI-ROYAL | 1% | **Basic** | 9.4M | $0.0005 |
| 10kΩ (5: R22,R29,R33,R36,R37) | `10kΩ` | **C25744** | 0402WGF1002TCE | UNI-ROYAL | 1% | **Basic** | 20.7M | $0.0005 |
| 100Ω (4: R48–R51) | `100Ω` | **C25076** | 0402WGF1000TCE | UNI-ROYAL | 1% | **Basic** | 9.8M | $0.0005 |
| 1kΩ (3: R2, R4, R6) | `1k` | **C11702** | 0402WGF1001TCE | UNI-ROYAL | 1% | **Basic** | 12.6M | $0.0005 |
| 27Ω (2: R7, R8) | `27` | **C138021** | RC0402FR-0727RL | Yageo | 1% | Extended | 191K | $0.0006 |
| 13.3kΩ, buck feedback divider (2: R20, R26) | `13.3kΩ` | **C2974007** | FRC0402F1332TS | FOJAN | 1% | Extended | 182K | $0.0004 |
| 49.9Ω, buck feedback divider (2: R18, R24) | `49.9Ω` | **C49654456** | GR0402F49R9TAG00 | GiantOhm | 1% | Extended | 10.0K | $0.0004 |
| 1MΩ (2: R35, R46) | `1MΩ` | **C26083** | 0402WGF1004TCE | UNI-ROYAL | 1% | **Basic** | 4.2M | $0.0005 |
| 33Ω (3: R3 + R63, R64) | `33`/`33Ω` | **C138002** | RC0402FR-0733RL | Yageo | 1% | Extended | 1.2M | $0.0006 |
| 20kΩ, ref bias/hysteresis (R21) | `20kΩ` | **C25765** | 0402WGF2002TCE | UNI-ROYAL | 1% | **Basic** | 3.0M | $0.0005 |
| **44.2kΩ, 0.5%, comparator trip divider (R30)** | `44.2kΩ` | **SEE §6 — GAP** | — | — | 0.5% req'd | — | — | — |
| **12.2kΩ, 0.5%, comparator trip divider (R31)** | `12.2kΩ` | **SEE §6 — GAP** | — | — | 0.5% req'd | — | — | — |

Every resistor group above is 1%-or-better even where 1% was merely "fine" per the spec — 1% thick-film costs the same as 5% at this scale, so there was no reason to source anything looser. All of the basic-tier picks (0Ω, 100k, 4.7k, 10k, 100Ω, 1k, 1M, 20k) are the same "0402WGF" UNI-ROYAL family, which happens to cover most of the round E96 decade values as JLC-basic; the odd values (27, 33, 13.3k, 49.9) fall outside that family's basic line and had to go extended, chosen for the best stock depth available at each value (some earlier candidates for 33Ω and 100Ω had uncomfortably thin stock, e.g. 248 units — swapped for parts with six-figure-plus stock instead).

---

## 3. Inductors

| Ref | Value | Footprint | LCSC | MPN | Mfr | Rating | Basic/Ext | Stock | Unit $ |
|---|---|---|---|---|---|---|---|---|---|
| L1 (RP2350 core reg.) | `3.3u` | RP2350_80QFN_minimal:L_pol_2016 | **C3221749** | VLS201610CX-3R3M-1 | TDK | Isat 1.41A, Irms ~1.1A (2016/0806 case) | Extended | 4.0K | $0.0889 |
| **L2 (clean buck, 0.3A, need Isat≥1A)** | `10µH` | **none assigned** | **NOT SOURCED — see §6** | | | | | | |
| **L3 (big buck, 2A, need Isat≥3A, Irms≥2.5A)** | `10µH` | **none assigned** | **NOT SOURCED — see §6** | | | | | | |

---

## 4. ICs, diodes, transistors, crystal (mostly pre-specified MPNs, LCSC number found/confirmed)

| Ref(s) | Value/MPN | LCSC | MPN | Mfr | Package | Basic/Ext | Stock | Unit $ | Note |
|---|---|---|---|---|---|---|---|---|---|
| U7 | TLV76733DRVR | **C2848334** | TLV76733DRVR | Texas Instruments | WSON-6 | Extended | 8.7K | $0.242 | given |
| U13, U14 | TPD2E2U06DRLR | **C1972959** | TPD2E2U06DRLR | Texas Instruments | SOT-553 | Extended | 4.5K | $0.224 | given |
| U8 | SN74LVC2T45DCUR | **C15741** | SN74LVC2T45DCUR | Texas Instruments | VSSOP-8 | Extended | 17.1K | $0.161 | given |
| H0:\*, H1:\* (30) | GH39FKSW | **C266230** | GH39FKSW | GoChip Elec Tech (Shanghai) | SOT-23 | Extended | 3.0K | $0.130 | given |
| U2 | TS3USB30ERSWR | **C73880** | TS3USB30ERSWR | Texas Instruments | UQFN-10 | Extended | 5.2K | $0.230 | only listing on LCSC |
| PD1, PD2 | FUSB302BMPX | **C132291** | FUSB302BMPX | onsemi | WQFN-14 | Extended | **627** | $0.687 | only listing; stock covers 4 boards (need 8) with modest margin — monitor before ordering |
| U5, U6 | TPS54302 | **C311983** | TPS54302DDCR | Texas Instruments | TSOT-23-6 | Extended | 183K | $0.163 | |
| U9 | MAX40203 | **C5668579** | MAX40203ANS+T | Analog Devices (Maxim) | **WLP-4** | Extended | **1** | $0.727 | **STOCK=1 — see §6, critical** |
| U10 | TLV431B | **C398374** | TLV431BQDBZR | Texas Instruments | SOT-23-3 | Extended | 18.8K | $0.206 | B-grade = ±0.5% confirmed |
| U11 | LM2903 | **C7549** | LM2903DR | Texas Instruments | SOIC-8 | Extended | 94.6K | $0.063 | |
| U3 | W25Q128JVS | **C97521** | W25Q128JVSIQ | Winbond | SOIC-8-208mil | **Basic** | 110K | $1.22 | U4 is DNP, not sourced |
| U1 | RP2350B | **C42415655** | RP2350B | Raspberry Pi | QFN-80 | Extended | 6.1K | $1.127 | only listing |
| LED1–30 | SK9822-EC20 | **C2909059** | SK9822-EC20 | OPSCO Optoelectronics | SMD 2x2mm | Extended | 53.6K | $0.110 | |
| D1, D2 | SS54 | **C18199188** | SS54C | R+O | **SMC** | Preferred | 10.0K | $0.065 | **Ir=150µA@40V, confirmed via datasheet** — see note below |
| D4, D5 | BZX84C10 | **C19077470** | BZX84C10 | R+O (Asian Brands) | SOT-23 | Preferred | 3.7K | $0.016 | |
| D3 | BZV55B3V3 | **C545375** | BZV55B3V3 | LGE | LL-34 (MiniMELF) | Extended | 1.0K | $0.016 | |
| Q1 | AO3401A | **C15127** | AO3401A | Alpha & Omega Semiconductor | SOT-23 | **Basic** | 1.19M | $0.053 | value field says `AO3401` — see §7 |
| Q2 | AO4407A | **C2841482** | AO4407A | Alpha & Omega Semiconductor | SOP-8 | Extended | 34.7K | $0.111 | |
| Q3 | BC857 | **C20069137** | BC857C | R+O (Asian Brands) | SOT-23 | Preferred | 94.5K | $0.012 | "C" gain grade — functionally fine |
| AM0, AM1 | CD74HC4067SM | **C98457** | CD74HC4067SM96 | Texas Instruments | SSOP-24 | Extended | 2.0K | $0.509 | only listing |
| Y1 | ABM8-272-T3 | **C20625731** | ABM8-272-T3 | Abracon | SMD3225-4P | Extended | 15.7K | $0.327 | 12MHz, matches C3/C4 |

**D1/D2 low-leakage confirmation:** "SS54" on LCSC is a generic multi-manufacturer bucket where leakage varies a lot by brand — I pulled the actual LCSC datasheet fields for the two best-stocked SMC-package candidates directly: R+O's `SS54C` (C18199188, the part assigned) is rated **Ir = 150µA @ 40V**; JUXING's `SS54LC` (C3033290, a tempting pick on name alone since "LC" reads like "low current") is actually rated **Ir = 200µA @ 40V** — worse, plus non-basic/non-preferred and ~40% pricier. ("LC" in JUXING's naming appears to track their low-*Vf* line, not low-leakage — a naming trap worth flagging.) R+O's plain `SS54C` also carries **Preferred** tier (fee-exempt) vs `SS54LC`'s plain Extended tier. Package is SMC either way, matching the schematic footprint (the plain-SMA basic SS54, C22452, does **not** match the footprint and was correctly rejected regardless of leakage).

---

## 5. Connectors / mechanical

| Ref(s) | Part | LCSC | MPN | Mfr | Basic/Ext | Stock | Unit $ |
|---|---|---|---|---|---|---|---|
| USB1, USB2 | USB-C receptacle, Molex 105450-0101 (footprint-locked) | **C134092** | 1054500101 | Molex | Extended | 34.1K | $0.651 |
| J4 | JST SM03B-SRSS-TB | **C160403** | SM03B-SRSS-TB(LF)(SN) | JST | Extended | 4.5K | $0.154 |
| SW1, SW2 (boot/reset) | Würth 434133025816 tactile, vertical SMD | **NOT FOUND — see §6** | | | | | |

---

## 6. Could not source / constraint gaps — explicit, nothing substituted

1. **R30 (44.2kΩ, 0.5%) and R31 (12.2kΩ, 0.5%), comparator trip divider.** These set a trip point with only ~180mV of margin, so 1% was explicitly ruled out. **No LCSC number was written to R30 or R31** — this is deliberate, not an oversight, after two independent search passes (fuzzy-text jlcsearch queries across many phrasings/manufacturer-code guesses, plus manufacturer-family-specific probing for Yageo/Vishay/KOA/Susumu/Panasonic 0.5%-tolerance "D"-code variants) both came up empty:
   - **44.2kΩ** *is* a standard E96 value and trivial to find at **1%** (e.g. C25895 `0402WGF4422TCE`, C354260 `RC0402FR-0744K2L`) — but every 0402 **0.5%**-tolerance variant I tried (`0402WGD4422TCE`, Vishay `CRCW040244K2D...`, Panasonic ERA, Susumu RT/AC-series equivalents) returned nothing on LCSC.
   - **12.2kΩ is not a standard E96 value at all** (E96 has 12.1k and 12.4k, not 12.2k) — it only exists on the finer E192 grid. No 0402 12.2kΩ part turned up on LCSC at *any* tolerance grade, under any manufacturer-code guess tried.
   - **Do not substitute** a 1% part or a nearby E96 value (12.1k/12.4k) without redoing the trip-point math — a swap changes the actual threshold. Practical paths: (a) hand-solder these two from DigiKey/Mouser, which both stock full E192 0402 0.5% resistor lines, while JLC assembles everything else; or (b) recompute the divider for a pair of values that *do* exist as stocked 0.5% parts.

2. **U9 (MAX40203, WLP-4).** The design requires WLP-4 specifically — the SOT-23-5 variant (MAX40203AUK+T) cannot carry the required 1A and was correctly excluded. The only WLP-4 listing on LCSC, C5668579 (MAX40203ANS+T), currently shows **stock = 1 unit**. Need 4 total (1/board × 4 boards). **This is a hard blocker as of the date of this report** — either wait for restock, source this one part from Digikey/Mouser/Maxim direct and hand-supply it to JLC ("customer-supplied parts" workflow), or reconsider the ideal-diode topology if WLP-4 stock doesn't recover before the order date.

3. **L2 (10µH, clean buck, need Isat≥1A) and L3 (10µH, big buck 2A, need Isat≥3A, Irms≥2.5A).** Per instructions, **no footprint was invented.** Both currently have `Device:L` with no footprint at all, so no case size is constrained and no LCSC number can be committed responsibly — a part chosen now could turn out to have the wrong pad layout once a footprint is picked. For reference only (not written to the schematic): common shielded power-inductor families in the 4×4mm–5×5mm class (e.g. "SNR4012", "SNR5020"-style 10µH parts) can plausibly hit L3's 3A/2.5A numbers, and smaller 3×3mm–2.5×2mm 10µH parts (e.g. "FNR3015"/"2520"-case parts) are in the right ballpark for L2's 1A — but spot-checks during this pass found some very-similar-looking 3015-case 10µH parts rated as low as **0.7–0.9A Isat**, i.e. parts that *look* interchangeable but would silently fail L2's requirement. **This needs a real footprint decision and a datasheet-verified pick, not a text-search guess — flagging rather than forcing it.**

4. **SW1, SW2 (boot/reset tactile switches).** Footprint is locked to a specific Würth Elektronik part, 434133025816. No exact match for that MPN exists on LCSC via the search API. Generic vertical SMD tactile switches exist on LCSC but substituting one risks a pad/actuator mismatch against the Würth footprint already in the design, so nothing was substituted. These are cheap and available directly from Würth/Digikey/Mouser — likely the pragmatic path is to hand-place these two parts rather than route them through JLC assembly, or swap to a JLC-stocked tactile switch footprint (a footprint change, which this pass was not authorized to make).

---

## 7. Data hygiene — confirmed, not touched

- **`100n` (16 parts, root sheet) and `100nF` (67 parts, power+keys sheets) are the same 100nF/0.1µF value spelled two ways.** They will not group together in a naive BOM export. (Sourcing-wise this didn't matter — both landed on the same LCSC part, see §1 — but the schematic-level value strings are still inconsistent and will confuse any tool that groups by literal value text.)
- All **30 SK9822-EC20 LEDs (LED1–LED30) have an empty `Value` field.**
- **L2, L3 have no footprint assigned** — see §6.
- Value strings are inconsistently unit-suffixed throughout: `0` (R10) vs `0Ω` (18 others); `33` (R3) vs `33Ω` (R63/R64); `1k` vs values elsewhere written with `Ω`/`k`/`Ω` suffixes inconsistently across sheets in general.
- **New, not previously flagged:** `4.7u` (C6, C7, C9, C10 — two different footprints) vs `4.7µF` (C23) is the same additional-suffix inconsistency as the 100n/100nF issue, just for the 4.7µF group. All five landed on the same LCSC part (§1), but the value text won't group in a literal-text BOM tool.
- **Q1's value says `AO3401`, but the placed symbol/footprint is `AO3401A`** (`Transistor_FET:AO3401A`, SOT-23). The LCSC part sourced (C15127) is genuinely AO3401A, matching the symbol — but the value field itself is wrong/abbreviated and should be corrected by the designer to avoid confusion later. Not changed here per instructions.

---

## 8. Consolidation opportunities

- **100nF-class merge (already applied):** `100nF` (67) + `100n` (16) + `0.1µF` (6) → one basic 50V part, C307331. This is the headline win — 89 of 297 parts (30%) collapse to a single BOM/assembly line instead of what could have been 2–3 lines split by voltage grade.
- **4.7µF merge (already applied):** `4.7u` (4, two footprint-name variants) + `4.7µF` (1) → one basic part, C23733.
- **33Ω merge (already applied):** `33` (R3) + `33Ω` (R63, R64) → one part, C138002.
- **0Ω merge (already applied):** `0` (R10) + `0Ω` (18) → one basic part, C17168.
- **Not pursued — L1 vs L2/L3:** all three are inductors in the same rough inductance neighborhood (3.3µH / 10µH / 10µH), but they serve three different current classes (≈1A core rail, ≈0.3A clean buck, ≈2A big buck) and L1 already has a fixed 2016-size footprint the other two don't share, so forcing one part across all three would either overspec L1's cost or underspec L3's current handling. Left as three separate decisions (two of which are still open, see §6).

---

## 9. Cost summary

All 46 priced groups below are **basic, preferred, or plain-extended by the labels in §1–§5**. JLCPCB Economic assembly fee model: basic parts carry no per-part setup fee; **Preferred**-tier extended parts (BC857C, BZX84C10, SS54C — 3 groups) are *also* fee-exempt under Economic assembly; every other **plain-extended** part costs a flat **$3 one-time fee per order** (not per board) — so ordering all 4 boards in a single JLCPCB order (not 4 separate orders) is what makes this affordable.

| | Amount |
|---|---|
| Parts cost, 1 board (sum of qty × unit price, all 46 sourced groups) | **≈ $17.19** |
| Parts cost, 4 boards | **≈ $68.77** |
| Basic-tier groups | 14 |
| Preferred-tier groups (fee-exempt) | 3 |
| Plain-**extended** groups (fee-liable) | **29** |
| One-time extended-part setup fees (29 × $3, charged once regardless of board count) | **≈ $87.00** |
| **Total, 4 boards, single combined JLCPCB order** | **≈ $155.77** |
| **Total, 1 board only (if ordered alone)** | **≈ $104.19** |

Not included above (still open per §6): R30, R31, L2, L3 stock/price, and SW1/SW2 (assume hand-sourced separately, low cost, non-JLC). U9's stock=1 blocker (§6) could also force a price/logistics change if it has to be hand-supplied instead of JLC-stocked.

**Budget read:** at ≈$156 for 4 boards' worth of BOM (parts + one-time setup fees) against a ~$250 total-build target, there's roughly $94 of headroom left for bare-PCB fabrication (×4), stencil, shipping, and the still-open items above. The extended-part fee ($87) is by far the largest single line item — it's a fixed cost of this BOM's part diversity, not something that scales with board count, so it doesn't get worse by building more tiles later, only better on a per-unit basis. Verify JLCPCB's current fee schedule at checkout — it changes periodically and this estimate assumes Economic assembly with the Preferred-tier exemption.

---

*Properties written: every ref listed with an LCSC number in §1–§5 now carries `LCSC`, `MPN`, and `Manufacturer` symbol properties in its source `.kicad_sch` file. DNP refs (C22, R1, R9, R11, R13, R28, U4) received a `DNP` property instead, with no LCSC/MPN/Manufacturer set. The 30 VoidSwitch instances (AM0:0–AM0:14, AM1:0–AM1:14) were left completely untouched, as instructed — they are not an LCSC part.*

---

**Revision note:** this report was regenerated in a second pass over the same schematic. Two changes
from an earlier draft of this document are worth calling out because they reversed an initial pick:

- **0-ohm jumpers (19 pcs)** moved from an extended part to **C17168** (`0402WGF0000TCE`,
  UNI-ROYAL) — same family as the other UNI-ROYAL basic picks, **Basic tier**, 18.4M stock. The
  earlier draft had landed on an extended part for this group; the basic option exists and is now
  what's written to the schematic.
- **D1/D2 (SS54 Schottky)** were re-verified against actual LCSC datasheet fields rather than name
  pattern-matching: R+O's `SS54C` (**C18199188**, the part now assigned) is **150µA @ 40V**
  reverse leakage and Preferred-tier; JUXING's `SS54LC` (**C3033290**) — despite the tempting "LC"
  suffix — is actually **200µA**, worse, and plain-Extended. "LC" in JUXING's scheme tracks their
  low-*Vf* line, not leakage. Confirmed directly via each part's LCSC page rather than inferred from
  the part number.

All prices, stock figures, and cost totals in this document reflect the parts actually written to
the schematic as of this revision.
