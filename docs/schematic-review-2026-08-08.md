# Voided Oblivion — Schematic Design Review

**Date:** 2026-08-08 · **Scope:** `Voided-Oblivion/Voided-Oblivion.kicad_sch` (+ `keys.kicad_sch`, `power.kicad_sch`), KiCad 10 · **Analysis run:** `analysis/2026-08-08_2107/`

## Verdict

**The schematic is in very good shape.** No board-killing electrical error was found. Every IC subsystem was traced pin-by-pin and, where datasheets exist, verified against the manufacturer PDF. The design closely follows the RP2350 hardware design guide where it applies, and the project's own docs (`docs/schematic-design/*`) already contain unusually rigorous derivations that the schematic matches. What remains before fab: **the sourcing gap (1% MPN coverage), a PCB that is one design generation behind the schematic, and a short list of latent/provision bugs and cheap-insurance items below.**

## Analyses run

| Analysis | Status | Result |
|---|---|---|
| `analyze_schematic.py` | ✅ | 374 components, 280 nets, 120 findings (4 error, 17 warning — triaged below) |
| `analyze_pcb.py --full` | ✅ | Used for sync check only — layout is mid-progress |
| `cross_analysis.py` | ✅ | 10 findings (all schematic↔PCB sync) |
| EMC (`analyze_emc.py`) | ✅ | 35.5/100 — **provisional**: findings are dominated by the unfinished layout (no ground zones/fills yet). Re-run after layout. |
| SPICE (ngspice) | ✅ | **35/36 subcircuits pass**, 1 warn (C37 — deliberately DNP, see below) |
| Thermal | ✅ | 0 findings (limited value until PCB is current) |
| KiCad ERC (`kicad-cli sch erc`) | ✅ | **1 error** — the intentional SM+ power-OR node (see F3) |
| Deep review + gate | ✅ | 14 findings verified, 0 quarantined (`analysis/deep_review.json`) |
| Gerber analysis | — | Not applicable — no fabrication outputs exist yet |
| Lifecycle audit | — | Not run — MPN coverage is 1%, nothing to query. Re-run after BOM backfill. |
| Prior review delta | — | First review; no prior review file found |

**Verification basis:** Datasheets in `Refrences/datasheets/` were used as ground truth (RP2350 datasheet + hardware design guide, TPS54302, LM66100, TLV431, LM2903, AO3401A, AO4407A, FUSB302, ABM8-272, W25Q128JV, 74HC4067, GH39F/SS49E, SK9822, SN74LVC2T45, TPD2E2U06, SS54, BZX84, BZV55, APH0630). The **TLV767 datasheet was missing and was fetched during this review** (TI SLVSE84D — recommend saving it to `Refrences/datasheets/`). The **AP2171W datasheet is missing** — U12/U16 are verified only against the KiCad library symbol and convention (see F3).

---

## Findings

### Warnings (fix or decide before layout freeze)

**F1 — CC1/CC2 are crossed on both USB-C ports.**
`USB1.A5 (CC1) → R49 → PD1.CC2` and `USB1.B5 (CC2) → R48 → PD1.CC1`; USB2/PD2 are crossed identically via R50/R51. For a UFP sink using only USB 2.0 data this survives — the FUSB302 measures both CC pins and just reports mirrored cable orientation — but anything orientation-dependent (VCONN targeting, future SS mux control) acts on the wrong pin. Either straighten it or add a schematic note making the cross deliberate so firmware knows to flip orientation.

**F2 — The second-flash CS provision can never work as drawn.**
The provision net named `GPIO0` contains only R9.1 and R11.1 — it is an island, not connected to U1 pin 77 (whose net is `PD EN TOP`). Populating U4/R11/R13 would leave U4's CS undriven (R13's pull-up would at least hold it deselected). Deeper problem: XIP_SS_N_1 exists **only on GPIO0, GPIO8, GPIO19, GPIO47** (verified in the RP2350 datasheet GPIO CTRL register map), and GPIO0/GPIO8 are spent (PD EN TOP, AS0). **Fix:** move the provision wire to GPIO19 or GPIO47 — both are currently unused stubs. Latent (everything involved is DNP), but it silently defeats the documented second-flash option.

**F3 — SM+ power-OR node: intentional, but carries the review's one ERC error and one unverified part.**
ERC flags `U12.OUT ∥ U15.VOUT` (power-output × power-output). The topology is right: U15 (LM66100, CE→VOUT via R16 = always-on reverse-blocking mode, same strap as U9/R15 and correct per LM66100 §8.3.2) ORs +5VP onto the node; U12 (AP2171W) switches BS+ onto it pre-PD; U16 gates the result to SM+. Two follow-ups: (a) add an ERC exclusion with a comment; (b) **the AP2171W datasheet isn't in the project** — confirm active-high EN, off-state reverse blocking, and current limit vs. SM+ worst-case load. Note that while U12 is enabled it conducts both directions, so if +5VP comes up with U12 still on, +5VP back-feeds BS+ — probably harmless at ~5V, but it's a firmware sequencing rule worth writing down.

**F4 — PCB is one generation behind the schematic.**
66 schematic components missing from the board; stale parts on it: U9 still MAX40203 (now LM66100), D3 still BZV55B**5V1** (now B**3V3**), C41 still 100µF on BS+ (now 1µF on +5VA), R48/R50 0Ω (now 100Ω), C76/C77/C114/R23 values stale. All match documented re-selects, confirming the schematic is truth. Run **Update PCB from Schematic** before any further layout; treat current EMC/PCB analyzer output as provisional.

**F5 — Sourcing blocker stands (SS-001).**
MPN fields readable by tooling: 1/77 unique parts (1.3%). The docs contain many settled picks (APH0630T100M C5349698, LM66100 C2832141, …) that aren't in symbol fields. Backfill LCSC/MPN/Manufacturer fields (the `bom` workflow can drive this) — it's the one thing that hard-blocks a JLC order.

### Recommendations (cheap insurance / open items from your own docs)

**F6 — ADC_AVDD is tied straight to +3V3.** The reference design does this too, but this board's entire key mechanism is 12-bit sampling of 30 hall sensors, and your docs call the supply chain feeding it "not characterised end-to-end" and "the first suspect." VREG_AVDD got an RC filter (R3 33Ω + C9 4.7µF); ADC_AVDD got nothing. Add a DNP-able filter provision (0Ω default, ferrite/33Ω + 1–4.7µF option) between +3V3 and pin 59. Costs nothing now, impossible after layout.

**F7 — Sensor-VDD split (keys.md's own to-do) is not implemented.** All 30 GH39F VDD pins tie directly to +3V3; the "0Ω link on its own net" that keeps the bank-gating retrofit possible does not exist yet.

**F8 — R30/R31 tolerance not encoded.** power.md's margin analysis wants 0.5% here (worst-case LTP 5.52V RSS vs the 5.5V vSafe5V ceiling — the thinnest margin on the board). U10 is already TLV431B (±0.5%) ✅; put the 0.5% tolerance in the R30/R31 fields so the BOM actually orders it.

**F9 — No ESD protection on submodule/inter-tile UART lines.** TPD2E2U06 covers both USB data pairs ✅. The 8 corner submodule UART lines (user-facing, hot-plug by design) and 8 tile-edge UARTs have none. Consider a 4-channel TVS per corner, or at least series resistors for hot-plug.

**F10 — No connector-side VBUS capacitance.** Connector VBUS nets carry only the FUSB302 sense pin and SS54 anodes; the only cap is C38 100nF behind the diodes. The deliberate 10µF-attach-limit strategy is sound, but ~1µF per port before D1/D2 would still be inside the limit and gives FUSB302 a cleaner measurement node.

**F11 — 100Ω CC series resistors (R48–R51).** Rd seen by the source becomes 5.2k (+2%, inside the 4.59–6.12k window) and BMC is unaffected — fine for a sink. VCONN *sourcing* through 100Ω is impossible, but a sink doesn't need it. Keep if intended as hot-plug/ESD damping; document why, since the PCB still has 0Ω.

**F12 — Five spare GPIOs (19, 38, 39, 46, 47) end in bare wire stubs.** Harmless, but label them or add test points; reserve GPIO19 or GPIO47 for F2.

**F13 — 22µF output caps (C28/C29/C34/C35) have no footprint/MPN yet.** When assigning, they must be ≥0805-class 6.3V+ X5R/X7R — a 0402 22µF loses ~half its capacitance at 5V bias, and the 44µF total is what the TI Table 7-2 stability design assumes.

**F14 — Doc drift:** power.md's LDO section still documents XC6220B331MR; as-built U7 is TLV76733. The swap is *good* (see below) — update the doc, and save the TLV767 PDF into `Refrences/datasheets/`.

### Analyzer false positives (triaged, no action)

- **PP-001 "U16.5 IN has no DC path to a power rail"** — the pin is fed by U15/U12 switch outputs on the OR node. Powered; false positive.
- **RS-001 "+5VA EN / +5VP EN have no declared source"** — they're enable nets that merely *look* like rails to the parser (`+5…` prefix). +5VA EN is U11B open-collector + R34 100k→3V3; +5VP EN is GPIO14 + R38 100k pull-down. Both correct. (Renaming, e.g. `5VA_EN`, would silence tooling.)
- **VM-001 "BS+ SRC 5V/3.3V domain crossing"** — BS+ SRC is the LM66100 open-drain status pin pulled to +3V3 by R83, exactly as your docs specify ("don't copy TI's pull-up rail"). Correct.
- **UC-003 "CC missing 5.1k pull-downs"** — Rd is integrated in the FUSB302. Correct as drawn.
- **UC-002 "no ESD on VBUS"** — partially true (see F10), but the D+/D- pairs *are* protected (U13/U14), and VBUS goes through Schottky ORing + soft-started FETs, not directly to loads.
- **SPICE warn on C37** — the TLV431 cathode cap the docs already recommend keeping DNP (unstable 6nF–400nF band). It *is* DNP. Consistent.
- **EMC errors (no ground plane, decoupling distance, IO filtering)** — artifacts of the half-built layout; re-run after F4.

---

## What was verified correct (the positive findings)

**RP2350B core (U1)** — all against the datasheet + hardware design guide:
- All 8 IOVDD pins → +3V3; 3× DVDD → +1V1; VREG loop verified: VREG_VIN=3V3, LX→L1 3.3µH→+1V1, FB sensed at +1V1, VREG_AVDD through R3 33Ω + C9 4.7µF (guide values), VREG_PGND→GND. USB_OTP_VDD→3V3 ✅
- Crystal: ABM8-272-T3 (the Pico 2 part, CL=10pF) + 15pF/15pF (CL_eff ≈ 10.5pF) + 1kΩ XOUT series — the guide's exact circuit ✅
- USB: DP/DM through 27Ω series (R7/R8) to the TS3USB30E mux ✅
- Flash: W25Q128JVS (the guide's own chip) on QSPI, CS strap network exactly per guide (R10 0Ω link, R1 DNF pull-up, R6 1k + BOOTSEL to GND); second-flash provision DNP (but see F2) ✅
- RUN: button-only, matching the Minimal/Pico 2 practice; SWD on dedicated J9 header ✅
- Pin budget matches `pin-budget.md`: 4 side UARTs, 4 corner submodule UARTs + 4 ADC ID lines, 4 PD-EN, I2C ×2 + INT ×2 for the PD PHYs, AS0–3 mux address, 2 ADC mux returns, LED SCK/TX, 5 power-control GPIOs, 5 spare ✅

**Power (all SPICE-checked, values match `power.md` derivations):**
- U5/U6 TPS54302: FB 100k/13.3k → 5.08V (Vref 0.596V per SLVSDG6C), 10µH APH0630T100M (Isat 4.57A vs 2.47A peak), 2×22µF out, bootstrap caps, feedforward 75pF ✅
- U7 TLV76733: **pinout verified against TI SLVSE84D Table 5-1** (OUT/SNS/GND/EN/GND/IN — the symbol is right), SNS→OUT, EN→IN via R12 0Ω (explicitly sanctioned; internal pull-up), CIN 1µF / COUT 4.7µF meet the 1µF minima — this answers power.md's open "is 1µF in OK" question with a datasheet **yes**. The WSON-6 pad also dissolves the XC6220 thermal ceiling that made bank gating load-bearing (≈+41°C at 400mA vs +113°C) ✅
- U9/U15 LM66100: CE→VOUT reverse-current-blocking strap on **both** (R15/R16) — the exact trap power.md warns about, avoided twice; ST pulled to +3V3 not VOUT ✅
- U10 TLV431**B** + R21 20k bias (188µA ≥ 2.35× IK(min)); R27 0Ω REF strap; C37 DNP per doc recommendation ✅
- U11 LM2903: VCC=VBUS (can't eat its own tail), A-side hysteresis on the reference node (R22/R46 → UTP 5.95V / LTP 5.68V), B-side clean 5.73V buck-enable — matches the doc's derivation; divider R30/R31 44.2k/12.2k confirmed ✅
- Q1 AO3401: off-divider R35 1M / R36 10k (Vgs −0.2V at 20V), **D5 gate zener present** — the single-fault clamp power.md recommended adding has been added ✅
- Q2/Q3/D4: gate network (R32/R29/R33/R47), D4 BZX84C10 clamp, C44 100nF Miller soft-start (~1–3ms PD+ ramp) ✅
- Per-side HV switches: 4× AO4407A (the doc's re-select away from SOT-23 thermal limits) + BC847 level shifters with 10k base/pull networks, drains to per-side PD nets on J1–J8 ✅
- SM+ chain: U12/U15/U16 with EN pull-downs (default off), FLG̅ pull-up 100k, BS+ SRC status to GPIO36 ✅

**USB/PD:** FUSB302 ×2 with VDD/VCONN on 3V3, I2C 4.7k pull-ups ×2 ports, INT pull-ups, VBUS sense direct to connector; TS3USB30E mux with OE̅ grounded, port-2-priority auto-select (USB2 VBUS → R37 10k → D3 3.3V clamp + C39 + R39 100k pull-down → S) — a clean hardware port arbiter; D1/D2 SS54 VBUS ORing ✅

**Keys & RGB:** 30× GH39F on +3V3 → AM0/AM1 (74HC4067, E̅ tied low via jumper, unused I15 grounded via R65/R66, 0Ω jumper convention on all select lines) → ADC0/ADC1; 30× SK9822 chain traced end-to-end (LED1→LED30, SDO/CKO chain intact, ends floating as expected), driven through SN74LVC2T45 (VCCA 3V3/VCCB +5VP, DIR strapped A→B, 33Ω series into the first LED; partial-power-down safe when +5VP is off) ✅

**ERC: 1 error total** (the intentional F3 node) — for a 374-component, 3-sheet hierarchical design that is remarkably clean.

## Review limits

- **AP2171W (U12/U16)** and **GH39FKSW** electrical limits verified only against library symbols/docs already in-repo; AP2171W PDF should be added (F3). GH39F's own PDF is present but thin (settling time unpublished — your keys.md already covers this).
- PCB, EMC, and thermal conclusions are deferred until the layout catches up with the schematic (F4).
- Lifecycle/pricing audit deferred until MPN backfill (F5).

*Full evidence-linked findings: `analysis/deep_review.json` (gate: 14 verified / 0 quarantined). Analyzer JSON: `analysis/2026-08-08_2107/`.*
