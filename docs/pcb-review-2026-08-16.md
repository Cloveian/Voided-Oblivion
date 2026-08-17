# PCB layout review — 2026-08-16

**Project:** Voided-Oblivion (KiCad 10, 3 hierarchical sheets, 4-layer PCB)
**Scope:** full-board layout review of the work-in-progress PCB, per request, while you're away. Read-only — **nothing in the design files was modified.** Fresh analyzer runs live in `analysis/2026-08-16_1508/` (schematic) and `analysis/2026-08-16_1510/` (PCB + cross + EMC + thermal + SPICE); fresh native DRC/ERC JSON in the session scratchpad (regenerate with `kicad-cli pcb drc --severity-all`).

**Analyzers run:** `analyze_schematic.py`, `analyze_pcb.py --full --proximity`, `cross_analysis.py`, `analyze_emc.py`, `analyze_thermal.py --ambient 40`, `simulate_subcircuits.py` (ngspice), `kicad-cli pcb drc` (honours `.kicad_dru`), `kicad-cli sch erc`, `diff_analysis.py` vs the 2026-08-08 run. Not run: gerber analysis (no fab outputs exist), lifecycle audit (see Review Limits).

---

## Verdict

**The board is dramatically further along than every doc in this repo says, and there is nothing architecturally wrong with it.** All **428 footprints are placed** (docs say 261/425), **212 of 268 nets have routing**, and the only completely-unrouted nets left are **32 segments of the SK9822 chain** — the one net class the layout checklist explicitly saved for last. Zones Phase 3 is substantially done: the F.Cu +3V3 transplant zone is gone, the full-board +3V3 pour is on In2.Cu, the MCU +3V3 island exists, and In1.Cu is a genuinely solid GND plane.

**Not fab-ready yet**, for five concrete reasons, all fixable in one sitting (see Blockers). The headline: **a copied LED-chain via pattern left ~6 stray vias carrying LED20/21/22 nets sitting on LED2/LED12's pads — 4 hard shorts**, plus one BOM landmine (R30's MPN is still the old 44.2 kΩ part while its value is the re-derived 35.7 kΩ).

Fresh DRC: **40 errors, 1017 warnings, 189 unconnected items** (unconnecteds are expected — LED chain + zone-fill-dependent pads).

---

## Blockers — fix before anything else

### B1. Stray vias from a copied LED routing pattern — 4 hard shorts ⚠⚠
*Raw-file + DRC verified.* The LED chain's per-LED via pattern (via pair at x≈51.1/52.6 next to each LED) was duplicated with the **source LEDs' nets still attached**. Vias carrying `Net-(LED20-CKO)`, `Net-(LED20-SDO)` are physically on top of LED2 pad 4 (52.61, 129.39) and LED12 pads 3/4 (51.09–52.61, 91.29) — exactly where LED2's and LED12's *own* chain vias belong (compare LED2's legit pair at y=127.79). Results:

- `shorting_items` ×4: LED11-CKO↔LED20-CKO, LED1-CKO↔LED20-CKO, LED11-SDO↔LED20-SDO, and **BS+↔LED20-CKO** (the stray via at y=129.39 also clips a BS+ track on B.Cu)
- `hole_clearance` 0.00 mm ×3 and front `solder_mask_bridge` ×3, same vias
- these same vias show up as "via-in-pad" on LED2/LED12/LED10/LED19 and as 8 of the 63 dangling vias

**Fix:** delete the stray vias at (51.09, 91.29), (52.61, 91.29), (52.61, 129.39) and audit every LED's via pair for net correctness (LED10/19/21 nets also show doubled vias). Then refill zones and re-run DRC.

### B2. R30 MPN contradicts its value — silently rebuilds the old comparator trip
*Raw-file verified.* R30 value = **35.7 kΩ** (the re-derived divider ✓) but its MPN field = **ARG02BTC4422 = 44.2 kΩ** — the superseded value. The BOM pulls the MPN, so JLC would assemble the *old* divider and move the VBUS handoff trip point the derivation in `schematic-design/power.md` exists to prevent. Same pass: **R31 (10 k 0.5 %), R22, U10 (TLV431B), C26/C28/C29/C31/C34/C35 (now 1206 — need ≥25 V parts for C26/C31 on PD+), U17/U18 (LM74700QDDFRQ1), Q13/Q14 (NCE4009S) all have empty MPN fields** — every part touched by the respin lost or never got sourcing. Full list of 33 missing-MPN refs is in `analysis/2026-08-16_1508/schematic.json → statistics.missing_mpn` (J1–J8/J9–J20/USB/SW are known off-catalogue or hand-soldered — fine).

### B3. VBUS trunk threads the LED via field at 0.05 mm
*DRC verified.* The 3.0 mm-wide VBUS runs on B.Cu at x=49.24 (lengths 22.7 mm and 29.25 mm) pass vias at **0.05 mm actual vs 0.2 mm class clearance** — a +5VP via at (49.24, 92.34), a GND via and `LED19-SDO` via at (49.24, 63.09). That's one fill-tolerance away from a 5 A short. Move the trunk or the via column; don't leave it to luck.

### B4. `/MCU D±` vs the "USB pair geometry" rule — the rule needs the same carve-out the clearance rule got
11 DRC errors: the QFN escape of `/MCU D+`/`/MCU D-` is 0.15 mm against the rule's 0.30 mm minimum. The copper is right (a 0.4 mm-pitch escape *can't* be 0.30 mm; the run is ~4 mm and the "MCU fanout neckdown" rule already accepts this for clearance) — the **rule is the wrong shape**, exactly the lesson recorded in the `.kicad_dru` comments. Add a `track_width` exemption for `A.inDiffPair('*') && A.intersectsArea('MCU')` (and check whether the `USB? pins` areas need the same), or these 11 errors will mask real ones forever.

### B5. `PD_TRUNK*` and `CORNER_VOID_*` rule areas still don't exist
*Raw-file verified* — only `MCU`, `USB1 pins`, `USB2 pins` are drawn. So two custom rules are **silently inert**, as the layout checklist warned: the 1.8 mm 5 A-trunk width rule and the USB-corner-void keepout. The power section is now placed, so `PD_TRUNK*` can finally be drawn (Q2's drain node → the per-side FET commons). Draw them, refill, re-run DRC — expect new, *real* violations to surface.

---

## Should-fix (warning tier, in rough priority order)

1. **AM0 vs LED18 vias, 0.45 mm vs the 0.5 mm sensor rule** (2 DRC errors). The most-sensitive net on the board is 50 µm inside its own guard rule because of LED chain vias at (51.1–52.6, 72.19). Nudge the vias, not AM0 — AM0/AM1 themselves are exemplary (F.Cu only, zero vias, 46/29 mm direct runs).
2. **LED via field spacing is systematically ~25 µm tight.** The copied pattern's via-to-pad gaps land at 0.175–0.182 mm vs the 0.2 mm class (C65/C66/C67 pads, LED19–22 pads, `/QSPI_SS` at 0.08 mm). One pattern fix + re-stamp beats 12 individual nudges.
3. **Isolated copper:** the In2 PD+ pour has an unconnected island at (68.5, 98.1); a VBUS B.Cu pour island at (47.1, 128.3). Connect or delete.
4. **63 dangling vias** — some are the B1 strays, the +5VP (×11)/GND (×8)/PD+ (×5) ones look like stitching into areas whose fills have moved. Sweep after the zone refill.
5. **Starved thermals (60)** — includes **J9–J20 submodule socket THT pads**, which are the pads the hand-solder thermal-relief rule exists for (0.5 mm spokes, ≥2). Check spoke generation after refill; the rest are LED/passive pads worth a skim.
6. **USB B.Cu excursions now reference the In2 +3V3 pour** (x 31–65, y 48–78 — clear of the PD+ pour, but the +3V3 fill is 65 % and broken around the LED via field). The checklist's "re-check after the L3 pour lands" item is now due: add GND stitching vias adjacent to the USB pair's layer-transition vias (EMC flagged all 6 transitions) and check pour continuity under the run. FS USB is forgiving; this is cheap insurance, not a crisis.
7. **ERC hygiene:** `VBUS1`/`VBUS2` need PWR_FLAGs (2 of the 3 ERC errors; the third — U12/U15 power-out join on `SM BUS` — is the intentional dual-source OR). Also **`Voided-Oblivion-misc` is missing from `sym-lib-table`** — SW1/SW2/U17/U18 resolve only via the embedded cache. Add the lib entry.
8. **Via annular ring 0.1 mm** (DFM): 0.6/0.4 vias have 0.1 mm rings — below JLC standard (0.125) and IPC Class 2. This is the same decision as the open "0.15 mm/0.25 mm question" (9 `drill_out_of_range` warnings remain): either accept JLC's advanced process for the fine fanout, or bump those vias to 0.65–0.7 mm OD. Decide once, record it.
9. **PD1/PD2 exposed pads have 0 thermal vias** (grounded correctly, dissipation is tiny — add 2–4 if convenient, or accept).
10. **Silk:** 199 overlaps + 50 edge-clearance warnings — cosmetic pass before fab, standard.

---

## Verified good (worth knowing so you don't re-check)

- **Placement is 100 %**: 0 of 428 footprints outside the outline; board outline is valid (July's `invalid_outline` error is gone).
- **Comparator region (Phase 0.5's oscillation risk):** U11's output net stays ≥1.0 mm from `VDIV` and `Net-(U11A-+)` and only *crosses* them — no parallel run, so the guard-trace warning from the datasheet extract doesn't bite. R30/R31 sit together 3 mm from U11, away from switching. *Raw-file verified geometry.*
- **Buck hot loops:** C25+C26 are 3.7/5.4 mm from U5; C32+C31 are 3.7/5.4 mm from U6, inductors opposite side. (The EMC "large hot loop U6" error paired U6 with *U5's* cap — false positive.)
- **Power copper:** VBUS power path 3.0 mm + pours; PD+ trunk 3.0/1.2 mm; PD+ TOP/RIGHT/LEFT/BOTTOM at 1.2 mm with **25 vias each** (0.8/0.4); BS+ 402 mm of 1.2 mm. The thin VBUS2/VBUS 0.2 mm runs are sense lines, not power.
- **In1.Cu is solid GND** — the analyzer's "74 GND islands / plane split" flood scores the F.Cu/B.Cu fill fragments and the In2 *power* plane; the actual L2 reference under QSPI/USB/analog is continuous (rendered and inspected). One note: a ~5×4 mm merged antipad void sits under the Q2 handoff cluster (~56–62, 98–107) — worth a few stitching vias around it, per the Phase 4 stitching pass which remains open.
- **LM74700 + NCE4009S respin is correctly drawn** — *datasheet-verified*: DDF 8-pin map (1 EN, 2 GND, 4 VCAP, 5 ANODE, 6 GATE, 8 CATHODE — `Refrences/datasheets/lm74700-q1.pdf` (ZHCSHV4G), §5 Pin Configuration, DDF table) matches U17/U18 exactly; FET source→ANODE (VBUS1/2), drain→CATHODE (VBUS), EN→ANODE via 0Ω = always-on; VCAP caps present (C128/C129). NCE4009S SOP-8 1-3=S/4=G/5-8=D matches.
- **Old "known contradictions" now closed on the board:** R30/R31/R22 = 35.7k/10k/5.1k ✓ · U10 = TLV431B ✓ · 22 µF & PD+ 10 µF caps all 1206 ✓ · SS54 → LM74700+NCE4009S applied ✓ · L2/L3 footprints filled ✓ · mux channel 15 tied to GND (R65/R66 0Ω) ✓ · mux ~E grounded ✓ · U16 EN fixed: `SM+ EN` on GPIO33 with R95 4.7 k pull-down, `SM+ FLT` on GPIO37 ✓ · R38 is a proper GND pull-down ✓ · all 37 test points on B.Cu ✓ · U1/U7/PD1/PD2 EPs grounded ✓ · Q1/Q2 orientations match the handoff architecture ✓.
- **SPICE:** 37/39 subcircuits pass (ngspice). The single warn (C37 "decoupling" impedance) is the comparator input RC being scored as a decoupler — not applicable.
- **Thermal:** nothing above 45 °C at 40 °C ambient in the model (only U6 carried enough data to assess — low-coverage result, not a clean bill; the docs' own TLV767/AO4407A hand calcs remain the better evidence).

---

## Previous review delta (vs 2026-08-08 run + schematic-review F1–F14)

| Status | Items |
|---|---|
| **Fixed** | F14 LDO doc (docs now corrected, uncommitted) · comparator divider applied · cap footprint defect (all 6) · backfeed diode respin applied · U16 EN · mux ch15 · TLV431B · zones Phase 3 (transplant zone deleted, In2 pour + MCU island live) · placement 261→428 |
| **Still open** | F6 ADC_AVDD filter provision (**still no RC/ferrite between +3V3 and pad 59 — last chance is before routing freezes around U1**) · PD_TRUNK/CORNER_VOID areas (B5) · GND stitching pass · 0.15/0.25 drill decision · silk pass |
| **New** | B1 stray-via shorts · B2 R30 MPN/value split · B3 VBUS 0.05 mm · sym-lib-table gap · VBUS1/2 PWR_FLAGs |

Schematic diff since 2026-08-08: +67/−10/~310 changes — the bulk is the LM74700/NCE4009S respin, TLV431B, sourcing-field edits, and R57–R60 consolidation. The diff's "BREAKING" flags (no_driver on AS0–AS3/VBUS1/VBUS2, multi-driver SM BUS) are all triaged benign: GPIO-driven selects, connector-sourced rails, intentional OR.

## False positives / reviewer overrides (so they don't get re-chased)

- **KO-001 ×50 "via inside keepout MCU"** — the MCU rule area has every keepout unticked (verified raw); analyzer treats named rule areas as keepouts. Native DRC agrees: zero keepout violations.
- **PP-001 "U16.IN floats"** — SM BUS is fed by U12.OUT ∥ U15.VOUT; analyzer doesn't credit load-switch outputs.
- **VM-001 "BS+ SRC 5 V→3.3 V"** — open-drain ST pin pulled to +3V3 by design.
- **UC-003 CC pull-downs ×4** — Rd comes from the FUSB302 dead-battery clamp; adding external Rd would break it (documented).
- **UC-004 VBUS decoupling 0.2 µF** — deliberate (10 µF attach ceiling / inrush).
- **SW-003 U6 hot loop, RP-002/GP-001 plane-gap flood, PS-002 island counts** — see Verified-good; wrong cap association and wrong reference plane respectively.
- **CC-002 "narrow signal" ×20** — 0.15 mm on logic/UART/QSPI escapes; carries µA–mA.
- **PM-002 SW1/SW2 courtyard overhang 0.2 mm** — edge-actuated Alps switches; the overhang is the actuator.
- **FD-001 no fiducials** — JLC uses panel fiducials; add 3 if you ever change fab.
- **lib_footprint_mismatch ×40** — the 30 hall SOT-23s + edited power parts differ from library copies on purpose (custom pads). Worth one skim to confirm they're *your* edits, then ignore.

## Not performed / review limits

- **Gerber analysis** — no fabrication outputs exist yet. Run it after export, before ordering.
- **Lifecycle audit** — not run (network API sweep; the 2026-08-09 sourcing pass is 8 days old and B2's re-sourcing pass will touch the same fields anyway).
- **Datasheet extraction cache** — absent; pin-level checks above marked *datasheet-verified* were done directly against `Refrences/datasheets/` PDFs (LM74700, NCE4009S). The 2026-08-08 deep review (`analysis/deep_review.json`) still stands for the rest of the schematic; parts added since then were the ones re-verified here.
- **Thermal model coverage** — analyzer assessed only U6; the project's hand calcs are the real thermal evidence.
- **Zone-fill staleness** — copper-presence and connection-width results reflect the fills saved in the file; several findings (starved thermals, dangling vias, isolated islands) should be re-checked after a fresh **Fill All Zones**.

## Suggested order of work when you're back

1. Delete/repair the B1 stray vias → refill → DRC (should clear ~12 errors).
2. Fix R30's MPN; run the sourcing pass over the 14 respin parts (B2).
3. Re-route the VBUS trunk away from the via column at x=49.24 (B3).
4. Amend the USB rule with the MCU-area track_width carve-out (B4).
5. Draw `PD_TRUNK*` + `CORNER_VOID_*` areas → refill → DRC, and deal with what surfaces (B5).
6. Decide F6 (ADC_AVDD filter provision) **before** the area around U1 pad 59 closes up.
7. Nudge the LED via pattern (+25 µm) and the two AM0 offenders; finish the LED chain routing.
8. Stitching pass (perimeter, RP2350B, bucks, Q2 void, USB transitions) → silk pass → 0.15/0.25 decision → export gerbers → gerber analysis.

Also: AGENTS.md §8 and the layout checklist header are now badly stale (placement/routing counts, "not yet applied" items that are applied). Worth a docs pass so the next session doesn't re-fix fixed things.
