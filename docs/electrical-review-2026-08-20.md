# Electrical design review — 2026-08-20

**Project:** Voided-Oblivion (KiCad 10, 3 hierarchical sheets, 4-layer PCB) · **Scope:** fourth review in the series, after [2026-08-08](schematic-review-2026-08-08.md) (F1–F14), [2026-08-16](pcb-review-2026-08-16.md) (B1–B5) and [2026-08-18](electrical-review-2026-08-18.md) (E1–E5 + addendum). Target: commit `75ff5e5` ("i think everything but silk is acctualy done this time for reals"). Read-only — no design file was modified. Fresh analyzer run `analysis/2026-08-20_0147/`, fresh `kicad-cli pcb drc --severity-all` / `sch erc` (10.0.5) in the session scratchpad, deep-review evidence gated in `analysis/deep_review.json` (4 verified / 0 quarantined; helper scripts in `analysis/helpers/`).

**Evidence labels:** *[DS p.X]* datasheet-verified with cite · *[RAW]* raw `.kicad_sch`/`.kicad_pcb`/git-diff/analyzer-extract verified · *[DRC]/[ERC]* fresh native run · *[CALC]* computed (script cited) · *[INFER]* inference. Nothing analyzer-only is called "verified".

---

## Verdict

**Not fab-ready. The E9 fix itself introduced a new electrical blocker, the fix's own resistors are unsourced, and B4/B5 were "resolved" by deleting DRC rules rather than fixing the board.**

1. **N1 — the 2.2 kΩ base shunts that fixed E3 break the ON-state drive of all four edge HV switches.** With R75–R78 still 10 k, a 3.3 V GPIO can only present 0.595 V to the BC847B bases — at/below Vbe. Typical parts work at room temperature; a high-Vbe part at 0 °C sinks ~15 µA, leaving the AO4407A at Vgs ≈ −1.5 V, below its own minimum threshold: **the edge switch never closes and inter-tile power distribution fails, temperature- and batch-dependent**. One resistor value fixes it (R75–R78 → 4.7 k).
2. **N2 — ten parts have no sourcing at all**: R79–R82 (the E9 fix — blanked when revalued) and the six respin caps C26/C31/C28/C29/C34/C35 (carried from E2's tail; C26/C31 are the 20 V-rail input caps that need ≥25 V + DC-bias derating). As-exported, JLC doesn't place the E9 protection or the buck input/output capacitors.
3. **N3 — four custom DRC rules were deleted instead of implemented, and B4 is still open.** `PD+ trunk carries the full 5A`, `PD+ off inner layers`, `PD+ zone connections`, and the THT hand-solder thermal-relief rule are gone from `.kicad_dru`; the `PD_TRUNK*`/`CORNER_VOID_*` areas were never drawn (so the surviving USB corner-void rule is *still* inert); the same 11 `/MCU D±` track_width errors persist. Nothing is electrically wrong in the copper *today* — but the review series' standing blockers were closed by removing the checks, not by passing them.

The genuinely good news, verified: **E1 is closed in copper** (R37 pad 1 on VBUS1, routed, mux now correct in every single-cable case, port-1 priority), **E4 is closed and sourced**, **E2's core is closed exactly per power.md's Parts table**, the schematic↔PCB sync gap from the 08-18 addendum is gone (U10 pad map, R36 1 k on the board), DRC is at 0 unconnected / 20 warnings (was 370), all dangling vias are cleaned, and the analog chain is untouched (AM0/AM1 still F.Cu-only, zero vias).

---

## Analyses run

| Analysis | Status | Result |
|---|---|---|
| `analyze_schematic.py` | ✅ fresh | 428 components, 269 nets; **diff vs 2026-08-18_1139: exactly 5 changes** — R79–R82 100k→2.2k (MPN blanked), R38 100k→4.7k (re-sourced). Nothing else moved at schematic level *[RAW diff_analysis]* |
| `analyze_pcb.py --full --proximity` | ✅ fresh | 427 footprints (H6 was a PCB-only orphan, removed by the sync — benign; 12 M2 holes remain), routing complete |
| `cross_analysis.py` | ✅ fresh | 13 findings — all the known RP-002/PS-002 plane-split false-positive family (scores the In2 power plane; In1 is the solid GND reference) |
| EMC (`analyze_emc.py`) | ✅ fresh | 212 findings; same triage as 08-18. Real keepers unchanged: DP-003 ×6 USB layer transitions without adjacent GND stitching — the stitching pass is still open |
| SPICE (ngspice) | ✅ fresh | **37 pass / 1 warn / 1 skip** — identical to 08-18 (C37-DNP artifact; Q2/Q13 mis-pattern-matched) |
| Thermal | ✅ fresh | 0 findings, low coverage — the docs' hand calcs (TLV767, AO4407A) remain the governing evidence |
| `kicad-cli pcb drc --severity-all` | ✅ fresh | **11 errors / 20 warnings / 0 unconnected** (was 11/370/0). All 11 errors are still B4. The warning collapse is real fixes plus the two new severity-ignore rules plus ~212 hidden silk refs *[RAW]* |
| `kicad-cli sch erc` | ✅ fresh | **1 error** — the intentional U12∥U15 `SM BUS` OR. Unchanged |
| Per-IC datasheet verification | ✅ delta | The 08-18 full per-IC pass stands (schematic unchanged except 5 resistor values). Re-verified for the delta: AO4407A Vgs(th)/RDS(on) [DS p.1], BC847B (fitted HJC PDF — publishes **no** VBE(on) limit), TPS54302 VEN [DS §5.5], TS3USB30E truth table vs the new copper. New LCSC numbers decoded: C189610 = NCE4009S SOP-8 ✓, C3236229 = LM74700QDDFRQ1 ✓ (jlcsearch) |
| Deep-review evidence gate | ✅ | 4 verified / 0 quarantined; computations in `analysis/helpers/` |
| Gerber analysis · lifecycle audit | — | Not applicable / not run — no fab outputs; N2's sourcing pass rewrites the same fields first |

---

## Blockers

### N1 — E3's fix breaks the ON state: the edge HV switches may never turn on · **NEW, introduced by 75ff5e5**
*[RAW] topology + [DS AO4407A p.1] + [CALC `analysis/helpers/edge_switch_on_drive.py`].* `PD EN *` (GPIO0–3, 3.3 V) → R75–R78 **10 k** → Q8–Q11 base, with the new R79–R82 **2.2 k** base-emitter shunts. Base drive available: Thevenin **0.595 V / 1.80 k**. The AO4407A gate hangs on 100 k to PD+ (R67–R70), so the BJT must sink **≥60 µA** to reach Vgs = −6 V (the lowest RDS(on) spec point, 17 mΩ) and ≥30 µA just to reach the worst-case threshold (Vgs(th) = −1.7/−2.3/−3.0 V min/typ/max [DS p.1]). What a BC847B can sink at 0.595 V:

| Corner | Sinkable Ic | Resulting Vgs (20 V rail) | Switch |
|---|---|---|---|
| typ Vbe, 25 °C | ~760 µA | −19 V (full) | on |
| max Vbe (660 mV @ 2 mA), 25 °C | ~160 µA | −16 V | on, no margin |
| typ Vbe, 0 °C | ~83 µA | −8.3 V | on, marginal |
| max Vbe, 0 °C | ~15 µA | **−1.5 V < \|Vgs(th)\|min** | **off** |

The fitted HJC BC847B datasheet (`Refrences/datasheets/bc847-npn.pdf`) publishes **no VBE(on) limit at any current** — nothing bounds the bad corner. The 08-18 review applied its own "a BJT base conducts at ~0.6 V" test to the E9 *off* state ("a pad-side 4.7 k leaves the node at 0.56 V — marginal against Vbe") but never re-ran it on the *on* state, where the very same 0.6 V is now all the drive there is. The previous 100 k shunts gave 3.0 V of drive; the fix traded all of it away. Cold keyboard + one high-Vbe transistor out of four per tile = an edge that silently refuses to power its neighbor — the exact silent failure shape §7 warns about.

**Fix: R75–R78 10 k → 4.7 k** (existing BOM line `0402WGF4701TCE`/C25900 — zero new lines). ON drive becomes 1.05 V Thevenin → Ib ≈ 0.27 mA → hard saturation at every corner; the E9 OFF state is untouched (120 µA × 2.2 k = 0.26 V at the base — the shunt, not the series R, sets it); GPIO load 0.48 mA. Keep R79–R82 at 2.2 k.

### N2 — the E9 fix and the respin caps are unsourced: the BOM assembles neither · **NEW + carried E2 tail**
*[RAW `statistics.missing_mpn` + `analysis/helpers/missing_sourcing.py`].* **R79–R82: LCSC and MPN both empty** — revaluing 100 k → 2.2 k blanked the sourcing, so the assembled board gets no base shunts at all (open base node = E3's original failure, now with no resistor rather than the wrong one, plus N1's drive problem is moot because nothing conducts — the switches simply follow whatever the floating pad does). **C26/C31/C28/C29/C34/C35 still have no sourcing** — carried from E2/B2 through three reviews now. C26/C31 sit on the 20 V PD+ rail: ≥25 V rating plus DC-bias derating (a 25 V X5R 1206 10 µF keeps ~40–50 % at 20 V, under TI's >10 µF input recommendation [DS TPS54302 §7.2.3.1]; prefer 35 V/X7R or parallel a second 10 µF). Fix: R79–R82 → `0402WGF2201TCE` (C25879); source the six caps with the derating constraint. Note for the same pass: Q13/Q14, U17/U18, R22, U10 carry **LCSC-only** fields (MPN empty) — fine for a JLC-driven BOM, and all four LCSC numbers verify correct (*[RAW + jlcsearch]*), but whichever field the export actually keys on should be the one that's populated consistently.

### N3 — B4/B5 were closed by deleting the rules, not fixing the board · **carried, shape changed**
*[RAW git diff + `analysis/helpers/dru_rule_inventory.py` + DRC].* `75ff5e5` deleted from `.kicad_dru`: **"PD+ trunk carries the full 5A"** (1.8 mm min inside `PD_TRUNK*`), **"PD+ off inner layers"**, **"PD+ zone connections"** (solid, ≥1.2 mm connection width), and **"THT pads: thermal relief for hand soldering"** (0.5 mm spokes for the hand-soldered J9–J20 sockets). The `PD_TRUNK*`/`CORNER_VOID_*` areas were never drawn, so the surviving "USB must not cross the corner plane voids" rule **remains silently inert** — B5's original complaint, unchanged since 2026-08-16. And **B4 is still open**: the same 11 `track_width` errors on `/MCU D±` vs "USB pair geometry" *[DRC]* — the MCU-area carve-out still isn't in the file; what was added instead is two severity-ignore rules.

What this doesn't break today, verified so the deletions aren't over-read: PD+ tracks exist only on F/B.Cu (the inner-layer rule wasn't masking anything) *[RAW]*; the 0.2 mm PD+ stubs are the R67–R70/C44 gate-pull-up taps carrying µA, not power *[RAW]*; the main GND zone still defaults to thermal reliefs so the J-socket pads keep their spokes *[RAW]*; the trunk copper (3.0/1.2 mm) is unchanged since the 08-18 assessment. But the checks that would catch a regression — a future refill going solid, a rerouted trunk necking down, PD+ straying onto 0.5 oz inner copper — are gone, in a repo whose own rule is that these guards "back a decision recorded in docs/design-choices/". Restore the four rules, draw the two area families, add the B4 carve-out, and deal with what the trunk rule then flags (the 1.2 mm trunk portions are legal-but-40 °C at the flagged-only 5 A case per the deleted rule's own comment). Also: the new **"connector mounting holes" ignore rule is broader than its justification** — `A.memberOfFootprint('J1') || B.memberOfFootprint('J1') || …` silences `hole_clearance` for *any* pair involving those footprints (e.g. an unrelated via drilled near a J-pad), not just the NPTH-peg-vs-own-pad case its comment argues. Narrow it to the peg pads.

---

## Should-fix

1. **Doc contracts are still inverted, and firmware is next** *(carried)*: [comms.md](schematic-design/comms.md) line 143 still says "S high = port 2… port 2 wins" — the board now senses VBUS1 and **port 1 wins** *[RAW]*; [AGENTS.md §6] still says "CC1/CC2 are crossed" — they are **straight** (re-verified on this revision *[RAW]*). Both are one-line doc fixes that prevent wrong firmware.
2. **The fetched LM66100/AP2171 datasheets were still not saved** into `Refrences/datasheets/` *(carried from 08-18 should-fix 8)* — the next review re-fights the Diodes bot-wall.
3. **Stitching pass still open** *(carried)*: EMC DP-003 ×6 on the USB pair's layer transitions; the ~5×4 mm antipad void under the Q2 handoff cluster.
4. **PD+ In2 isolated island at (67.4, 98.1)** *[DRC `isolated_copper`]* — now carried through three reviews. Delete it or connect it.
5. **3 dangling GND stubs on F.Cu** at (68.5, 98.3), (50.4, 42.7), (46.2, 54.2) *[DRC]* — down from 9+22 dangling items; finish the sweep.
6. **14 `diff_pair_gap` warnings** *[DRC]*: short uncoupled segments (0.03–1.7 mm) where USB pairs split around obstacles; the 15 mm uncoupled budget is not violated. Skim-and-accept tier — but they're the only warnings left, so they're now visible.
7. **Local decoupling gaps** *(carried from 08-18 should-fix 7, unchanged)*: AM0/AM1 have no dedicated VCC cap; PD2's nearest 100 nF ~6 mm; neither FUSB302 has the datasheet's local 1 µF. One-cap fixes, still open. Likewise U15's floating ST pin.
8. **Silk** — deliberately deferred by the commit message; ~212 footprint refs are hidden on silk *[RAW]*, which is also most of why the DRC warning count collapsed. Fine as a deferral; don't read the 20-warning DRC as "silk done".

---

## Accepted risks — re-verified, acceptance holds

The schematic is untouched since 08-18 except five resistor values, so the 08-18 re-verification of every acceptance stands unchanged: 5.95 V on the LM66100 (structurally unfixable, [power.md#accepted-risk-595v-on-a-60v-part]), slow HV-switch turn-off (~10 ms), body-diode inbound conduction (orientation re-confirmed 08-18), no UART ESD (F9), no FUSB302 VBUS OVP, gate clamps cut, AP2171 limit vs the published contract, TPS54302 hiccup OCP and no +5VP UVLO (`!firmware-note!` obligations stand). **One acceptance improved:** the Q1 turn-off slew race (08-18 should-fix 2) is closed — R36 = 1 kΩ on schematic *and* board *[RAW]*, bounding the BS+ excursion at spec-max PD slew. Note E3/N1 interact with the acceptances: until N1 is fixed, the "firmware owns overcurrent by refusing to enable a path" story has a hardware dual — a path firmware *wants* enabled may not actually close.

---

## Fixed since 08-18 — verified, so it doesn't get re-checked

- **E1 closed end-to-end** *[RAW + DS + DRC]*: R37 pad 1 on VBUS1 net and copper (0 unconnected items); TS3USB30E D1=USB2/D2=USB1 with S sensed from VBUS1 → every single-cable case routes correctly per the Table 7-1 truth table; both-plugged priority is now **port 1**.
- **E4 closed**: R38 = 4.7 k, sourced (C25900); TPS54302 VEN 1.28 V max unreachable from the E9 park level through the new pull-down; 3.3 V GPIO drive unaffected [DS §5.5].
- **E2 core closed**: R30/R31/R22/U10 fitted exactly per [power.md's Parts table](schematic-design/power.md) (±0.1 % carried in the ARG02 MPNs; R22 ±1 % deliberate, 1.4 mV of UTP). The MPN-decode sweep over every sourced R/C found **zero** value/MPN mismatches *[CALC]*.
- **Sync gap closed**: U10 pads carry the corrected REF/K map; R36 value synced; H6 (a PCB-only orphan footprint) removed.
- **Hygiene**: 22 dangling vias → 0; duplicated-via pairs stayed fixed; DRC warnings 370 → 20; ERC exactly 1 intentional error; zone fills current.
- **Unchanged-and-still-good spot checks after the 51k-line PCB diff**: AM0/AM1 F.Cu-only with 0 vias (46/29 mm); `/MCU D±` 4.0/3.7 mm; USB pair via counts unchanged; footprint edits (VoidSwitch, PG-6P male) touched no pads *[RAW]*.

---

## False-positive triage (re-confirmed on fresh runs, no action)

The standing list holds: PP-001 (U16.IN fed by the U12∥U15 OR), VM-001 (BS+ SRC open-drain to 3V3), UC-003 ×4 (FUSB302 dead-battery Rd — external Rd would break it), UC-004 (deliberate attach-inrush ceiling), RS-001 (+5VA EN/+5VP EN are enable nets, not rails), RP-002/PS-002/GP-001 plane-split flood (scores In2; In1 is the solid reference), SW-003 (wrong cap association), SPICE C37 warn + Q2/Q13 skip, NT-001 (spare GPIO stubs + LED30 chain ends), lib_footprint_mismatch ×2 (deliberate pad edits on U1/U18). New this run: **PU-001 "U17/U18 EN missing pull-up"** — EN→ANODE via 0 Ω is the sanctioned always-on strap, datasheet-verified 08-18; **DS-002** — datasheets live in `Refrences/datasheets/`, not `datasheets/`; pin-level claims here were made against the PDFs directly.

## Not performed / review limits

- **Gerber analysis** — no fab outputs exist; run after export, before ordering.
- **Lifecycle audit** — not run; N2's sourcing pass rewrites the same fields first.
- **Thermal analyzer** — 0 findings at low coverage; the docs' hand calcs remain the governing evidence.
- **Per-IC datasheet verification** was a delta pass over what `75ff5e5` touched, on top of the 08-18 full pass (which covered every active part including the 80-pin RP2350B symbol); the schematic diff proves nothing else changed. Pad-level parity spot-checked on every changed ref.
- **Bench items unchanged**: GH39F ratiometricity at 3.3 V (mixed-population plan), +5VP vs the SK9822 5.3 V max, LDO TJ at full load, AP2171 OCP thermal cycling under a real short. N1 adds one: verify edge-switch turn-on at the cold corner after the R75–R78 change (trivial once the value is right).
- No `.lck` files, no running KiCad; nothing was written to design files.

---

## Previous-review delta

| Status | Items |
|---|---|
| **Fixed since 08-18** | E1 (in copper) · E4 (value + sourcing) · E2 core (R30/R31/R22/U10 per Parts table) · Q1 slew race (R36 1 k, board) · U10 pad map synced · dangling vias 22→0 · dangling stubs 9→3 · DRC warnings 370→20 · H6 orphan removed |
| **Still open** | E2 tail → **N2** (six respin caps; now joined by R79–R82) · B4 (11 track_width errors) → **N3** · B5 (rule areas) → **N3, worse: rules deleted** · doc contracts (comms.md port priority, AGENTS.md §6 CC) · datasheet saves · stitching pass · PD+ In2 island · AM0/AM1/PD2 local caps · U15 ST · silk (deferred by author) |
| **New this review** | **N1** edge-switch ON-drive broken by the E3 fix · R79–R82 sourcing blanked (folded into N2) · four `.kicad_dru` rules deleted + overly-broad hole_clearance ignore (folded into N3) |
| **Closed as verified-benign** | footprint edits pad-free · 0.2 mm PD+ stubs are gate-network taps · H6 removal · silk-warning collapse explained (hidden refs + ignore rules, not lost checks) |

## Suggested order of work

1. **N1** — R75–R78 10 k → 4.7 k (schematic), keep R79–R82 2.2 k.
2. **N2** — source R79–R82 (C25879) + the six caps (C26/C31 ≥25 V, derating-aware) in the same pass; pick one sourcing field (LCSC) and make sure the export keys on it.
3. Sync → refill → DRC (one sync, after both edits).
4. **N3** — restore the four deleted rules, draw `PD_TRUNK*`/`CORNER_VOID_*`, add the B4 `track_width` carve-out, narrow the mounting-hole ignore to the peg pads → refill → DRC → resolve what the trunk rule flags.
5. Doc pass: comms.md port-1 priority, AGENTS.md §6 CC-straight, save the two datasheets.
6. Hygiene: PD+ island, 3 GND stubs, stitching pass, local caps, silk.
7. Export gerbers → gerber analysis → order.

---

# Re-review addendum — same day, after `d12a8aa "BOMB update … and some library linking"`

**Scope:** delta re-review of `d12a8aa` (BOM/sourcing pass + library relinking; PCB 17.8k-line diff, power/root/keys schematics, RP2350 footprint, sym-lib-table). Fresh analyzer run `analysis/2026-08-20_0312/`, fresh DRC/ERC, full-BOM MPN decode sweep (value + package size + voltage rating). Same evidence labels. Deep-review gate: 5 verified / 0 quarantined.

## Verdict: **electrically fab-ready.** N1 and N2 are closed and verified; every remaining open item is process, documentation, or cheap-insurance tier — none is an electrical defect in the design as it stands.

## What d12a8aa fixed (verified)

- **N1 → closed.** R75–R78 10 k → **4.7 k**, in the schematic *and* in copper *[RAW both]*. Re-running the drive calc (`analysis/helpers/edge_switch_on_drive.py`): Thevenin base drive is now **1.05 V / 1.5 k** → ~270 µA of available base current against the ~1 µA needed — Q8–Q11 saturate hard at every Vbe corner and temperature, including the unspecified-Vbe fitted part. The E9 off-state is untouched (0.26 V at the base). The edge-switch ON path now has real margin at both ends.
- **N2 → closed.** `missing_mpn` (non-connector) is **empty** *[RAW]*. R79–R82 = C25879 (verified 2.2 k 0402 *[jlcsearch]*). The respin caps: **C26/C31 = CL31B106KBHNNNE, 1206 X7R 50 V** (C89632) — comfortably past the ≥25 V + derating requirement on the 20 V rail; **C28/C29/C34/C35 = CL31A226KAHNNNE, 1206 X5R 25 V** (C12891, JLC **Basic**). Q13/Q14, U17/U18, U10, R22, SW1/SW2, and both USB receptacles (HC-TYPE-C-16P-01A) all gained MPNs matching their LCSC numbers.
- **Three latent bugs no review had caught, fixed as a side effect:** C19, C40, C77, C121 previously carried 0805/0402-coded MPNs on their 1206 footprints (assembly would have failed), and the old part was **6.3 V-rated** — C77 sits on `SM BUS` and C121 on `SM+`, whose documented worst case is ~5.95 V, i.e. 94 % of rating with near-total X5R bias derating. All four are now the 50 V 1206 part. (Reviewer's note: the earlier "MPN decode sweep" checked value↔MPN only; this pass added package-size and voltage-rating decode, which is what surfaced these as *already fixed*. The sweep gap is closed going forward.)
- **Hygiene, all verified on fresh runs:** the 3 dangling GND stubs — gone; the **PD+ In2 isolated island (carried since 08-16) — gone**; both `lib_footprint_mismatch` warnings — gone (the RP2350 footprint diff is a format-only re-save: **pad geometry is semantically identical**, 102 pads unchanged *[RAW parse]*); `49e` symbol library registered; ERC severities *raised* (`pin_not_connected` ignore → warning) with NC markers added on the four spare-GPIO stubs and LED30's chain outputs — ERC still exactly **1 intentional error**. DRC: **11 errors / 14 warnings / 0 unconnected** — the 11 are B4's known rule-shape errors, the 14 are the benign short diff-pair-gap segments.
- **Corner-void intent verified manually** *[CALC]*: with `CORNER_VOID_*` areas still undrawn (rule inert), a geometric sweep of every USB-pair segment against generous ±8 × 3.5 mm envelopes around all 12 corner-socket bodies finds **zero incursions** — the copper satisfies the rule the DRC can't currently check.

## Reclassification: the deleted DRC rules (from N3)

Per the designer: the four rules were deleted deliberately — the triggering locations were judged individually and were false positives for the rules' intent (e.g. 0.3 mm VBUS *sense* lines tripping power-width rules because sense nets share the `Power Delivery` netclass). Reclassified from process-blocker to **accepted-by-designer, recorded here**. Standing recommendation, not a gate: the misfires were a netclass-granularity problem — moving sense nets to their own netclass would let the power-copper guards return without the noise. The board as-is passes every deleted rule's intent on manual check (PD+ tracks F/B-only; trunk 3.0/1.2 mm; main GND zone thermal-relieved).

## Still open — none electrical, none fab-gating

| Item | Tier |
|---|---|
| **B4**: 11 `/MCU D±` track_width errors vs the "USB pair geometry" rule — the copper is right, the rule still needs the MCU-area carve-out or these mask future real errors | DRC hygiene |
| `CORNER_VOID_*` areas undrawn — rule inert (intent verified manually this pass; a redraw would keep it checked automatically) | DRC hygiene |
| Doc contracts: [comms.md](schematic-design/comms.md) still says port-2-priority (board is port-1); [AGENTS.md §6] still says CC crossed (they're straight) | docs — fix before firmware |
| LM66100 / AP2171 datasheets still not saved into `Refrences/datasheets/` | docs |
| Stitching pass: EMC DP-003 ×6 USB layer transitions; Q2-cluster antipad void | cheap insurance (FS USB) |
| Local decoupling one-cap items: AM0/AM1 VCC, PD2 100 nF distance, FUSB302 1 µF; U15 ST float | cheap insurance |
| Silk pass | deferred by author |
| Gerber analysis | run after export, **before ordering** |

## Bench list for first power-up (unchanged + one addition)

GH39F ratiometricity at 3.3 V (mixed population); +5VP vs SK9822 5.3 V max — scope at first power-up; LDO TJ at full load; AP2171 OCP cycling under a real short; SK9822 color order vs a physical LED; **edge-switch Vgs at 9 V and 20 V** (one-time confirmation of the reworked drive, trivial with a probe on any Q4–Q7 gate).
