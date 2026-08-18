# Electrical design review — 2026-08-18

**Project:** Voided-Oblivion (KiCad 10, 3 hierarchical sheets, 4-layer PCB) · **Scope:** full electrical review of the board declared "electrically done" at `a09633e`, third review in the series after [2026-08-08](schematic-review-2026-08-08.md) (F1–F14) and [2026-08-16](pcb-review-2026-08-16.md) (B1–B5). Read-only — no design file was modified. Fresh analyzer output in `analysis/2026-08-16_1510/` (regenerated 2026-08-18 over the same run id), fresh `kicad-cli pcb drc --severity-all` / `sch erc` in the session scratchpad, per-IC datasheet verification fanned out over every active part.

**Evidence labels used throughout:** *[DS p.X]* = datasheet-verified with page/table cite · *[RAW]* = verified in the raw `.kicad_sch`/`.kicad_pcb`/netlist or analyzer extract of them · *[DRC]/[ERC]* = fresh native run · *[INFER]* = computed/inferred, not directly verified. Nothing analyzer-only is called "verified".

---

## Verdict

**Not fab-ready electrically. Two hard blockers, one of them new.**

1. **The USB data mux selects the wrong port in every single-cable case** — with one cable plugged into either port, D± is routed to the *empty* connector and the keyboard can never enumerate. This is the board's core function (master election *is* USB enumeration). Netlist-level confirmed against the TS3USB30E truth table; one-net fix.
2. **B2 from the last review is still open and is worse than documented**: R30's MPN is still the 44.2 kΩ part against its 35.7 kΩ value, and as-assembled-from-BOM the divider becomes 44.2k/**10k** (not the old 44.2/12.2) — trip moves to **LTP ≈ 6.69 V / UTP ≈ 6.88 V**, which parks BS+ ~0.9 V past the LM66100's 6.0 V abs max and destroys U9 on the first PD negotiation. The other 13 respin parts still have empty MPN fields.

Beyond those: the project's own RP2350-E9 rule ([AGENTS.md §7], bitten twice before) is violated on **five** load-bearing enable nets — all four `PD EN *` edge-switch drives and `+5VP EN` — so every MCU reset with PD+ live momentarily turns on all four edge HV switches and can enable the LED buck uncommanded. Cheap resistor-value fixes, but they defeat the design's only overcurrent story during exactly the windows firmware isn't running, so they gate fab too.

The good news is equally real: **every IC pin map on the board is now datasheet-verified — including the full 80-pin RP2350B custom symbol, both custom-symbol LM74700s, the GH39F and SK9822-EC20 custom symbols against their PCB pads — and none is wrong.** The LED chain is fully routed (0 unconnected items, down from 189), B1's via shorts and B3's 0.05 mm VBUS clearance are gone, F2 (second-flash CS) is properly fixed on GPIO19, the CC pull-up/I²C/INT networks are clean, and the AP2171W open question is answered (auto-retry, not latching). One long-standing doc contract is inverted from reality: **CC1/CC2 are wired straight, not crossed** — firmware written to the documented contract would be wrong.

---

## Analyses run

| Analysis | Status | Result |
|---|---|---|
| `analyze_schematic.py` | ✅ fresh | 428 components, 269 nets; **diff vs 2026-08-16_1508 run: zero changes** — everything since the last review is PCB-only |
| `analyze_pcb.py --full --proximity` | ✅ fresh | 428 footprints, routing complete |
| `cross_analysis.py` | ✅ fresh | 15 findings — all in the known plane-split false-positive family (see triage) |
| EMC (`analyze_emc.py`) | ✅ fresh | 178 findings; dominated by the same family; real keepers = 2 missing stitching vias, USB layer transitions |
| SPICE (ngspice) | ✅ fresh | **37 pass / 1 warn / 1 skip** — warn is the known C37-DNP artifact; skip is Q2/Q13 mis-pattern-matched as a "bridge" |
| Thermal | ✅ fresh | Only U6 assessable (44.5 °C @ 40 °C ambient) — low coverage; the docs' hand calcs remain the real evidence |
| `kicad-cli pcb drc --severity-all` | ✅ fresh | **11 errors / 587 warnings / 0 unconnected** (was 40 / 1017 / 189) — all 11 errors are the B4 rule-shape issue |
| `kicad-cli sch erc` | ✅ fresh | **1 error** (the intentional U12∥U15 `SM BUS` OR) + 4 `Voided-Oblivion-misc` lib warnings — the VBUS1/2 PWR_FLAG errors are fixed |
| Per-IC datasheet verification | ✅ | Every active part; pages cited inline below. LM66100 + AP2171W PDFs were **missing from `Refrences/datasheets/`** and were fetched (TI symlink; LCSC CDN — the Diodes site bot-blocks, as the log predicted) |
| Deep-review evidence gate | ✅ | `analysis/deep_review.json`: 9 verified / 1 quarantined (the CC doc-correction — no datasheet quote applies to a netlist-vs-docs finding) |
| Gerber analysis | — | Not applicable — no fabrication outputs exist yet |
| Lifecycle audit | — | Not run — 33 refs still have no MPN (B2's sourcing pass will rewrite the same fields first) |

---

## Blockers

### E1 — USB mux select polarity is inverted: single-cable USB routes data to the empty connector · **NEW**
*[RAW] wiring + [DS p.12] truth table.* U2's `D1±` = **USB2 D±**, `D2±` = **USB1 D±** (schematic pins and PCB pads 1/7 and 2/6 agree), and `S` is driven high by **VBUS2** presence (`VBUS2 → R37 10k → USB SEL → R14 0Ω → S`, R39 100k pull-down, D3 3.3 V clamp). TS3USB30E Table 7-1: **S=L → D=D1, S=H → D=D2**. So:

| Case | S | Mux selects | Result |
|---|---|---|---|
| Host on port 1 only | L | D1 = USB2 | **dead — no enumeration** |
| Host on port 2 only | H | D2 = USB1 | **dead — no enumeration** |
| Host port 1 + source port 2 | H | D2 = USB1 | works, but by accident |
| Both, host on port 2 | H | D2 = USB1 | data to the wrong host |

[comms.md#sel-detect---which-port-wins](schematic-design/comms.md) states the intent — "S low = port 1, S high = port 2, port 2 wins" — which requires `D2 = USB2`. The wiring has the channels backwards relative to that intent. The 2026-08-08 review's "clean hardware port arbiter ✅" checked the S-network, not the channel mapping — this survived two reviews.

**Fix (either):** (a) swap the D1±/D2± connector assignments (schematic + a local reroute at U2 — pads 1↔2, 7↔6); or (b) move R37's sense from VBUS2 to VBUS1 — one net, no D± reroute, but both-plugged priority flips to port 1 (update comms.md if chosen).

### E2 — R30's MPN still rebuilds a *destructive* comparator trip; the 14 respin parts are still unsourced · **carried from B2, consequence upgraded**
*[RAW] fields + [DS] abs max.* R30: value 35.7 kΩ, MPN `ARG02BTC4422` = **44.2 kΩ**. The BOM pulls the MPN, and against the *new* R31 = 10 k the assembled divider is 44.2k/10k: k = 0.1845 → **LTP ≈ 6.69 V, UTP ≈ 6.88 V** — not the old 5.95 V design the 08-16 review warned about, but ~0.9 V *past* the LM66100's 6.0 V abs max (VIN/VOUT/CE all rate 6 V — [DS SLVSEZ8A p.4], it is not VIN-only). Q1 holds BS+ at the trip during the PD ramp, so first 5→9 V negotiation takes U9 (and, with U12 enabled, U15/U16) above abs max. An MPN-decode sweep over **every** sourced R/C/L found no second instance of this bug — R30 is the only value/MPN mismatch on the board *[RAW]*.

Also still unsourced from the same respin: R31, R22, U10 (TLV431B), C26/C28/C29/C31/C34/C35, U17/U18, Q13/Q14 *[RAW `missing_mpn`]* — and **F8 is still open**: the ±0.1 % divider intent lives only in [power.md#parts](schematic-design/power.md); with generic ±1 % parts the linear worst case blows the 5.5 V vSafe5V floor ([power.md#error-budget](schematic-design/power.md) — the ±0.1 % R-term ±5.6 mV becomes ~±88 mV).

**Fix:** R30 MPN → `ARG02BTC3572` (C2681604), R31 → `ARG02BTC1002` (C2902636), R22 → C25905, per power.md's own Parts table; then the rest of the respin sourcing pass. C26/C31 need **≥25 V** parts and a DC-bias check — a 25 V X5R 1206 10 µF retains ~40–50 % at 20 V, under TI's ">10 µF" input-cap recommendation [DS TPS54302 §7.2.3.1 p.15]; prefer 35 V/X7R or parallel a second 10 µF.

### E3 — RP2350-E9 on all four `PD EN` nets: every edge HV switch turns ON while the MCU floats · **NEW**
*[RAW] topology + [DS RP2350 p.1366–1367] erratum.* `PD EN TOP/RIGHT/BOTTOM/LEFT` (GPIO0–3) reach the BC847B bases (Q8–Q11) through R75–R78 10 k, with only R79–R82 **100 k** base-emitter shunts. E9 makes an input-enabled floating pad an active ~120 µA source parked at ~2.2 V; through 10 k into a 0.65 V base that delivers ~110 µA of base current → Q8–Q11 saturate → Q4–Q7 enhance. **All four edges energize simultaneously whenever GPIO0–3 sit input-enabled and undriven with PD+ live** — the `gpio_init()`-before-`gpio_set_dir()` window on every boot, any firmware crash, any reflash. That defeats "firmware owns overcurrent by limiting topology" ([design-choices/power.md#re-decision-does-this-need-per-edge-ocp-at-all]) during exactly the windows firmware isn't running, and at a partition boundary it can drag a neighbor's 9 V region to ~19 V through the inward body diodes ([power.md#the-body-diode---an-open-switch-only-blocks-outbound]) — prolonged by the accepted ~10 ms turn-off. This is the project's own §7 rule ("anywhere a default-low state is load-bearing… ≤8.2 kΩ"), generalized in session 8 and applied to the Rx detects and both AP2171 ENs (all 4.7 k ✓ *[RAW]*) but never back-applied here.

**Fix:** the 8.2 k number was derived for CMOS VIL 1.155 V; a BJT base conducts at ~0.6 V, so don't blind-copy 4.7 k. **R79–R82 100 k → 2.2 k** holds the base node at ≤0.26 V at the full 120 µA (a pad-side 4.7 k leaves the node at 0.56 V — marginal against Vbe). Belt-and-braces: firmware never leaves GPIO0–3 as enabled inputs.

### E4 — RP2350-E9 on `+5VP EN`: R38 = 100 k lets the big buck enable uncommanded · **NEW**
*[RAW] + [DS TPS54302 §5.5 p.5].* TPS54302 VEN rising is 1.23 V typ / **1.28 V max** — the 2.2 V E9 park level is a guaranteed enable. With PD+ at 9–20 V, an MCU-float window turns on the LED/submodule rail; the same window leaves U8's A-port (LED SCK/TX) floating, so the level shifter can clock garbage into 30 SK9822s at unclamped brightness (the ≤10/32 thermal clamp is firmware — [AGENTS.md §6] — and firmware is exactly what's not running). [power.md#big-buck notes] says "R38 100 k … default off, correct" — that note predates the session-8 E9 generalization and only considered the buck's 0.7 µA internal pull-up; it is superseded by the project's own rule. **Fix: R38 100 k → 4.7 k** (0.56 V at full E9 current, below VEN falling 1.1 V).

### E5 — Pre-fab gating items carried from 2026-08-16 (unchanged)
- **B4:** the 11 remaining DRC errors are all `/MCU D±` at 0.15 mm vs the `USB pair geometry` 0.30 mm min-width inside the QFN escape *[DRC]*. The copper is right; the rule still needs the MCU-area `track_width` carve-out or these errors mask real ones forever.
- **B5:** `PD_TRUNK*` and `CORNER_VOID_*` rule areas still don't exist — only `MCU`, `USB1 pins`, `USB2 pins` are drawn *[RAW]* — so `.kicad_dru:103` ("PD+ trunk carries the full 5A") and `.kicad_dru:84` ("USB must not cross the corner plane voids") remain silently inert. Draw them, refill, re-run DRC, and deal with what surfaces.

---

## Doc-contract correction (firmware-facing — fix the docs before firmware exists)

**CC1/CC2 are wired STRAIGHT on both ports, not crossed.** *[RAW]*: `USB1.A5(CC1)–R49–PD1.CC1`, `USB1.B5(CC2)–R48–PD1.CC2`, `USB2.A5(CC1)–R51–PD2.CC1`, `USB2.B5(CC2)–R50–PD2.CC2`. [AGENTS.md §6] ("CC1/CC2 are crossed on both ports — the orientation bit firmware reads is inverted from physical reality") and F1 describe the opposite; either F1 was mis-read or the cross was straightened in the 08-08→08-16 edit window (~310 changes). **Firmware written to the documented contract would invert orientation wrongly.** Correct AGENTS.md §6 and anywhere F1's note propagated. (The 100 Ω series parts are fine for a dead-battery Rd sink: Rd through 100 Ω ≈ 5.2 k, inside the Type-C window [DS FUSB302 + INFER].)

---

## Should-fix

1. **TLV431 symbol has REF/CATHODE swapped vs the real part — masked only by R27 = 0 Ω.** *[DS TLV431 Table 4-1 p.3] vs [RAW]*: the `TL431DBZ` symbol puts K on pad 1 / REF on pad 2; TI's TLV431x DBZ is pin 1 = REF, pin 2 = CATHODE, pin 3 = ANODE. In zener mode (R27 0Ω shorting the two nets) the node still regulates at 1.24 V, so the board works as built — but the DNP R27/R28 divider option is booby-trapped (fitting it would not produce the intended Vka equation), and `+1V24ref` physically lands on REF, not the cathode. Fix the pin map at the next schematic touch, or annotate that R27 must stay 0 Ω forever.
2. **Q1 turn-off vs PD slew race erodes the 5.95 V acceptance at fast sources.** *[INFER, DS-anchored]*: after the UTP trips, Q1's gate charges through Q3/R36 10 k against Ciss + C45 ≈ 1.6–2 nF → ~20–25 µs still conducting. USB-PD allows vSrcSlewPos up to 30 mV/µs, so VBUS can climb ~0.6–0.75 V past UTP before Q1 opens: **BS+ transient ≈ 6.4–6.7 V** against the 6.0 V abs max. [power.md#accepted-risk-595v-on-a-60v-part] covers steady-state UTP plus "ringing", not this race; typical sources slew ~100× slower and stay inside the acceptance, so this is erosion, not a new steady-state violation. **Cheap fix: R36 10 k → 1 k** (turn-off 10× faster, excursion <100 mV even at spec-max slew; turn-on soft-start is the R35/C45 path and is untouched; Q3 pulse ≈ 6 mA — fine for BC857). Bonus: it also improves Q1's thin off-state margin (Vgs −0.20 V vs Vth min −0.5 V at 20 V → −0.02 V) flagged by the FET verification.
3. **Inductor stuffing change: don't apply APH0624 as written.** The fitted MPN is still APH0630T100M (Isat 4.57 A) — the board is right. [power.md#revisit-flat-beats-wide]'s gate (Isat ≥ 3 A) was derived from operating peaks; the TPS54302's cycle-by-cycle limit is **4/5/6 A min/typ/max** [DS §5.5 p.5], and APH0624's 3.32 A rated / 4.0 A typ Isat [DS APH p.7] sits at-or-below it, so a startup-into-short saturates the inductor before the limit trips. The gotcha section already accepts saturation-under-short for a 3 A-class part — but the Revisit's "Isat still isn't a regression" bullet compares against the old 3 A assumption, not against the current limit. Keep APH0630, or re-derive the gate deliberately before the stuffing change (the project's own "requirement is a gate" lesson).
4. **`sym-lib-table` still missing `Voided-Oblivion-misc`** — 4 ERC warnings; SW1/SW2/U17/U18 resolve only via the embedded cache *[ERC]*. Carried from 08-16.
5. **Sourcing/DFM sweep items** *[DRC][RAW]*: 4 pairs of duplicated same-net vias (`holes_co_located` at (75.94, 39.54) +3V3, (59.55, 54.19) PD EN BOTTOM, (91.29, 63.69) SW NOISY, (91.39, 44.79) SW CLEAN — delete the duplicates); 22 dangling vias + 11 dangling track stubs (incl. two `Net-(J16-Pin_1)` stubs); the PD+ In2 isolated island **still present** at (67.4, 98.1) (carried from 08-16); 15 starved thermals incl. J-socket THT pads — re-check spokes after the next refill.
6. **Stitching pass (still open from 08-16):** EMC flags layer-transition vias without adjacent GND stitching on `LED SCK` and `/USB_BOOT` plus the 6 USB pair transitions; the ~5×4 mm antipad void under the Q2 handoff cluster still wants a few vias.
7. **Local decoupling gaps** *[RAW placements]*: AM0/AM1 have no dedicated VCC cap (nearest 100 nF is 5.6–6.3 mm away — a borrowed hall-sensor cap); PD2's nearest VDD 100 nF is ~6.2 mm (PD1 has C42 at 2.6 mm), and neither FUSB302 has the datasheet's local 1 µF (CVDD2) [DS FUSB302 external components]. All low-risk; all one-cap fixes.
8. **Save the fetched datasheets into `Refrences/datasheets/`** — LM66100 (TI SLVSEZ8A) and AP2171 (Diodes DS31564, via LCSC CDN — the Diodes site bot-blocks). Without them in-repo, the next review re-fights the same bot wall. Also: U15's ST pin is floating; the datasheet says "connect to GND if not required" [DS p.3] — electrically harmless, one-strap tidy-up.
9. **Extend the accepted-risk log for the 5.95 V excursion's blast radius** *[DS]*: it propagates to U15 (VOUT/CE ~50 mV under 6.0 V abs max), U12/U16 (above AP2171's 5.5 V rec-op, under 6.5 V abs max), and SM+ delivers up to ~5.95 V to submodules pre-PD — the submodule spec should say so. Same acceptance, wider blast radius than the U9-only entry.
10. **Corner-socket Rx lines (GPIO23/25/27/29) have no pulls at all** *[RAW]*: with no submodule fitted, E9 parks them ~2.2 V. Presence detection is the ID divider (not Rx-idle), so nothing false-triggers — but they'll read as noise mid-rail. Pulls or firmware input-disable when unused; note-tier.

---

## Accepted risks — re-verified, acceptance holds

- **5.95 V on the LM66100's 6.0 V abs max**: structurally-unfixable argument re-checked and still valid ([power.md#accepted-risk-595v-on-a-60v-part] — LTP ≥ 5.68 V floor forces UTP > 5.5 V; no clamp discriminates at 50 mV). Two amendments, not re-litigations: the slew race (should-fix 2) and the blast radius (should-fix 9).
- **Slow HV-switch turn-off (τ_off ≈ 10 ms)**: inherent to the R_pu≫R_soft topology, unchanged ([power.md#open-turn-off]). Note E3 makes the slow turn-off *matter more* until the E9 fix lands.
- **Body-diode inbound conduction / cooperative partitioning**: orientation (source on PD+, drains outboard) re-confirmed on all five FETs *[RAW pads]*; the acceptance reasoning holds.
- **No ESD on the 16 UART lines** (F9): unchanged, accepted. USB D± pairs are protected (U13/U14 verified on the connector side of the mux *[RAW]*, working voltage 5.5 V [DS §6.3]).
- **No OVP on the FUSB302 VBUS pin**: re-verified — rec-op max 21.0 V, abs max 28 V [DS tables]; 20 V contract leaves ~1 V rec-op margin, transients covered by abs max. Acceptance stands ([schematic-design/comms.md] note).
- **Q4–Q7 gate clamps cut** ([log, session 7]): at 20 V mode Vgs ≈ −19 V = 76 % of ±25 V abs max *[DS AO4407A p.1]* — legal, as decided; the 9 V default sits at −8.5 V. Unchanged.
- **TPS54302 hiccup OCP** and **no +5VP input UVLO**: behavior re-confirmed [DS §5.5, §6.3.5]; the `!firmware-note!` obligations stand.
- **AP2171 current limit ≠ the 300 mA/1 A contract**: ILIMIT is 1.1/1.5/1.9 A min/typ/max [DS p.4] — the hardware backstop is looser than the published contract (the log's "1 A part enforces the budget" oversells it slightly); firmware still owns the per-port budget. Thermal shutdown backs it.

**Open questions from AGENTS.md §8, updated:** AP2171W OCP **auto-retries** (constant-current, then thermal cycling with ~25 °C hysteresis; "continues to cycle… until the load fault or input power is removed" [DS p.10]) — the U16-EN-as-fault-reset contingency is unnecessary; bench item closed. GH39F ratiometricity at 3.3 V remains a bench item (datasheet characterizes 5 V only; quiescent out ≈ mid-rail at 3.3 V per the Vout-vs-VCC curve [DS p.4], mixed-population plan still sensible).

---

## Per-IC verification (what was checked and is right)

Every pin map below was verified against the manufacturer PDF **and** the PCB pad→net parity — none disagrees:

- **U1 RP2350B (custom 80-pin symbol)** — all 80 pins + EP vs the QFN-80 pinout figure [DS p.16]: no off-by-one anywhere. Decoupling per the hardware design guide (10× 100 nF on the 3V3 ring ≤3.7 mm, VREG 33 Ω/4.7 µF filter, DVDD set exceeds guide) ✓; crystal circuit guide-exact (CL_eff ≈ 10.5 pF vs 10 pF spec, 1 k on XOUT) [DS ABM8 p.2, guide p.13] ✓; RUN/BOOTSEL straps guide-identical ✓; SWD order standard ✓. **F2 is properly fixed**: the second-flash CS provision is now a complete DNP set (R11/R13/C22/U4) on **GPIO19**, which carries XIP_SS_N_1 (FUNCSEL 0x09, GPIO19_CTRL) ✓. **F6 status:** ADC_AVDD (pin 59) is still tied directly to +3V3 on both schematic and board — no filter provision ever landed; the datasheet only mandates a nearby 100 nF [DS §6.1.5 p.442], so this is now a permanent, minor, accepted deviation rather than a fixable one (routing is closed around U1). Note: L1 is the unmarked-winding TDK part, not the guide's polarity-marked Abracon — orientation can't be controlled at assembly [guide p.7–8].
- **U3/U4 W25Q128JVS** — SOIC-8 pin map [DS p.5], VCC/decoupling, /WP and /HOLD as IO2/IO3 (JVSIQ = QE preset) ✓.
- **U5/U6 TPS54302** — pin map [DS Table 4-1], FB dividers = the datasheet's own 5 V design row (Vout 5.08 V), bootstrap, 75 pF feedforward, 2×22 µF out vs the Table 7-2 stability design, min on-time at 20 V in, UVLO ✓. EN drives verified both directions (U11B open-collector + R34 ↔ VEN 1.28 V max; cold-start float-enable is *correct* for the always-on rail [DS §6.3.5]).
- **U7 TLV76733** — DRV pin map incl. SNS [DS Fig 5-2 p.3], EN=IN sanctioned [DS Table 5-1], VIN abs max 18 V ≫ BS+ 5.95 V, cap minima met, dropout fine at 800 mA. Worst-case dissipation ≈1.07 W → TJ ≈ 108 °C at 25 °C ambient on the JEDEC θJA — inside limits, monitor at bring-up [DS §6.4–6.5].
- **U9/U15 LM66100** — DCK pin map [DS p.3], CE→VOUT strap = §8.3.2 Always-ON RCB (the doc's cite is correct), ST open-drain legality at 3V3 pull-up, reverse leakage µA-class, 6 V abs max on *all* pins confirmed [DS p.4–5, p.9].
- **U12/U16 AP2171W** — SOT-25 pin map [DS p.1–2], EN active-high VIH 2.0 V, both ENs 4.7 k-pulled (E9-safe), UVLO 1.6–2.5 V, /FLG deglitch 4/7/15 ms with R96 100 k pull-up ✓. SM chain walked end-to-end pre-PD and post-PD — both work; enabled-U12 backfeed remains the documented firmware sequencing rule.
- **U17/U18 LM74700 + Q13/Q14 NCE4009S** — re-verified after the respin: DDF/SOP-8 pin maps, VCAP 0.1 µF correctly **VCAP-to-ANODE** (C128/C129), ANODE/CATHODE caps present, EN→ANODE always-on sanctioned, gate drive ≤13 V vs ±20 V FET rating, 20 V cross-port blocking within ratings, unplugged-port float self-limits below vSafe5V (no bleed resistor — acceptable) [DS both].
- **PD1/PD2 FUSB302B** — MLP-14 pin map [DS Fig 5], VBUS pin ratings, VDD/VCONN legality, both I²C buses with 4.7 k pull-ups, **INT pull-ups now 4.7 k** (R44/R45 — the old 100 k flag is closed on the board) [DS RPU_INT 1.0–4.7 k] ✓.
- **U2 TS3USB30E** — pin map/package ✓, S-network levels at 5 V/20 V/0 V ✓ (D3 is now BZV55B**3V3** — the old "5.1 V should be 3.3 V" item is fixed on the board), Ioff partial-power-down ✓ — but see blocker E1 for the channel mapping.
- **U8 SN74LVC2T45** — DCU pin map, VCCA/VCCB/DIR orientation, **Ioff specified for exactly the VCCB=0-while-A-driven case** [DS Ioff rows + §7.3.5], B-side VOH ≈ 5.0 V vs SK9822 VIH 3.4 V ✓.
- **AM0/AM1 CD74HC4067** — 24-pin map incl. the S2/S3 cross-mapping (the design gets it right), E̅/ch-15 straps, address lines ✓. No Ron spec exists at 3.3 V (only 4.5/6 V + Nexperia's 2 V row); the settling math below absorbs a ≤500 Ω worst case.
- **GH39F ×30 (custom symbol)** — SOT-23 pin map (1=VDD, 2=OUT, 3=GND) vs the datasheet pin-definition table ✓, PCB pads spot-verified on 4 sensors, one 100 nF within ~2.6 mm of each ✓. (The `VoidSwitch` symbols are deliberate pad-less mechanical templates — the electrical parts are the `H0:x`/`H1:x` refs.)
- **SK9822-EC20 ×30 (custom symbol + footprint)** — 6-pad EC20 pin map and pad geometry vs the mechanical drawing ✓, chain CKO→CKI/SDO→SDI verified at 5 hops, 33 Ω series, per-LED 100 nF (exceeds the datasheet's app circuit), LED30 outputs floating as expected ✓. Note: +5VP 5.08 V nominal vs SK9822 operating max 5.3 V — ~0.2 V margin; scope the rail at first power-up.
- **Comparator/handoff network** — LM2903 works from 4.45 V (VS min 2 V) through 20 V with VCM respected at both corners; TLV431 bias ≥1.6× Ik(min) at cold attach; Q1/Q2 gate math re-derived at 9 V/20 V; D4 clamps at ~9.4 V (Iz ≈ Izk — benign); D3/D4/D5 polarities pad-verified ✓.

**ADC chain settling** *(the product-is-this-chain check)*: mux COM 50 pF + strays ≈ 60 pF, RP2350 ADC ~1 pF ("no need to buffer" for DC [DS §12.4.3 p.1070]); rising settle <1 µs; falling settle depends on the GH39F's unspecified sink path — assuming a ≤10 k effective pulldown, 9τ ≈ 5.7 µs against a ≥30 µs per-step window → ~5× margin. The conclusion only fails if the sensor's effective pulldown exceeds ~55 kΩ (implausible for a 6 mA-bias output stage, but it is the one unverifiable number — the ch-15 ground channel is already wired as an inter-key discharge step if it ever shows up). AM0/AM1 routing is still exemplary (F.Cu only, no vias).

**Copper/current** *[RAW]*: per-edge PD+ = 1.2 mm B.Cu + 25 vias + F/B pours each (≈20 °C rise at the 4 A ceiling, ~6 °C at the 2 A target — the connector remains the limit, as designed); trunk 3.0/1.2 mm; VBUS 3.0 mm; BS+ 1.2/0.8 mm; SM+ 0.5 mm for ≤1 A ✓.

---

## Previous-review delta

| Status | Items |
|---|---|
| **Fixed since 08-16** | B1 stray-via shorts (0 shorting/hole/clearance errors) · B3 VBUS 0.05 mm · LED chain fully routed (189→0 unconnected) · AM0-vs-LED18 0.45 mm errors gone · VBUS1/2 PWR_FLAGs · DRC 40→11 errors, 1017→587 warnings |
| **Fixed earlier, confirmed here** | F2 (second-flash CS → GPIO19, complete DNP set) · F13 (22 µF/10 µF now 1206) · D3 → BZV55B3V3 · FUSB302 INT pull-ups → 4.7 k · comparator divider values on the board · U16 EN + `SM EN`/`SM FLT` · mux ch15/E̅ straps |
| **Still open** | **B2/E2** (R30 MPN + 14 respin parts, F8 tolerance encoding) · **B4** (rule carve-out) · **B5** (rule areas) · sym-lib-table · PD+ isolated island · stitching pass · silk pass (587 warnings incl. 50 silk-edge) · 0.15/0.25 drill decision |
| **New this review** | **E1** USB mux select inversion · **E3/E4** E9 on `PD EN ×4` and `+5VP EN` · TLV431 symbol pin swap (masked) · Q1 turn-off slew race · CC-not-crossed doc contract · APH0624 gate-vs-current-limit · duplicated-via pairs ×4 |
| **Closed as answered** | AP2171W OCP behavior (auto-retry) · AP2171/LM66100 datasheet gap (fetched — save them) |
| **Moot** | F7 sensor-VDD split provision — never implemented, and bank gating is a locked rejection; the routed board closes the retrofit either way |

---

## False-positive triage (no action, so they don't get re-chased)

All of the 08-16 list re-confirmed on fresh runs: KO-001 (MCU rule area isn't a keepout — native DRC agrees, 0 keepout violations), PP-001 (U16.IN fed by the U12∥U15 OR), VM-001 (BS+ SRC open-drain to 3V3 by design), UC-003 (CC Rd is the FUSB302 dead-battery clamp — external Rd would break it), UC-004 (deliberate attach-inrush ceiling), SW-003 (wrong cap association), RP-002/GP-001/PS-002 plane-split flood (scores the In2 power plane; In1 is the solid GND reference), CC-002 narrow-signal family (logic escapes), lib_footprint_mismatch ×40 (deliberate pad edits). New this run: SPICE "skip" on Q2/Q13 (pattern-matched as a bridge circuit — it's the handoff FET + ideal-diode FET, not a bridge); the analyzer showing U13.5 floating (netlist proves it's on USB1 D− — extraction artifact); `PD+ BOTTOM` showing 0 track length (it distributes through its B.Cu/F.Cu pours + 25 vias — real copper, just no tracks); ERC pin_to_pin ×1 (the documented intentional OR).

## Not performed / review limits

- **Gerber analysis** — no fab outputs exist; run after export, before ordering.
- **Lifecycle audit** — not run; 33 refs have no MPN and E2's sourcing pass rewrites the same fields.
- **Thermal analyzer** — only U6 assessable; the docs' hand calcs (TLV767, AO4407A, LDO) remain the governing evidence, now cross-checked per-IC above.
- **PCB analyzer diff vs the 08-16 run** — impossible: the analysis cache reused run `2026-08-16_1510` and overwrote its `pcb.json` in place. Deltas above are against the 08-16 review text + fresh DRC instead (the schematic diff *was* run against the intact `2026-08-16_1508` output: zero changes).
- **Zone-fill staleness** — copper/DRC results reflect the fills saved in the file (0 unconnected suggests they're current).
- **GH39F at 3.3 V, AP2171 OCP thermal cycling under a real short, +5VP vs the 5.3 V LED max, LDO TJ at 400 mA** — bench items, not desk items.
- The two `~*.lck` files in `Voided-Oblivion/` are stale (no KiCad process); nothing was written to design files regardless.

## Suggested order of work

1. **E1** — decide priority direction, fix the mux select (one net or one swap), update comms.md.
2. **E2** — R30/R31/R22 MPNs per power.md's Parts table (+ tolerance fields, F8), then the 14-part respin sourcing pass with the C26/C31 ≥25 V/derating constraint.
3. **E3/E4** — R79–R82 → 2.2 k, R38 → 4.7 k. Consider R36 → 1 k (should-fix 2) in the same pass; all five are resistor-value edits, no layout change.
4. **B4/B5** — rule carve-out + draw the two rule-area families → refill → DRC clean.
5. Correct AGENTS.md §6 (CC not crossed) + the accepted-risk log extensions; save the two fetched datasheets.
6. Hygiene sweep: duplicated vias, dangling vias/stubs, PD+ island, stitching pass, mux/PD2 local caps, sym-lib-table, silk, drill decision.
7. Export gerbers → gerber analysis → order.

---

# Re-review addendum — same day, after `d71a73c "small changes"`

**Scope:** delta re-review of `d71a73c` (PCB 181k-line diff, power.kicad_sch, symbol lib, sym-lib-table). Fresh analyzer run `analysis/2026-08-18_1139/`, fresh DRC/ERC. Same evidence labels.

## Verdict: still not fab-ready — but for a *narrower* reason

Two of the four electrical blockers were fixed **at schematic level**, and the fixes are correct. The new gate: **the PCB was not updated from the schematic**, so the E1 fix isn't in copper yet — and E3/E4 weren't touched at all.

## What d71a73c fixed (verified)

- **E1 → schematic-fixed, copper-pending.** R37's sense moved from VBUS2 to **VBUS1** *[RAW: R37 pins now `VBUS1`/`USB SEL`]* — the one-net option. Truth-table check: VBUS1 present → S=H → D2=USB1 ✓; absent → D1=USB2 ✓ — every single-cable case now routes correctly. Both-plugged priority flips to **port 1 wins**; [comms.md#sel-detect---which-port-wins] still documents port-2-priority and needs updating. **But the board still has R37 pad 1 on the VBUS2 net/copper** *[RAW pcb pad_nets]* — see "the sync gap" below.
- **E2 → core fixed, sourcing tail remains.** R30 MPN → `ARG02BTC3572` ✓, R31 → `ARG02BTC1002` ✓ *[RAW]* — the destructive 6.9 V trip path is closed. U10's new LCSC `C398374` **verified = TLV431BQDBZR, ±0.5 %, SOT-23-3, 12k stock** (jlcsearch lookup). Still MPN/LCSC-empty: **R22, C26/C31 (the ≥25 V PD+ caps), C28/C29/C34/C35, U17/U18, Q13/Q14** *[RAW `missing_mpn`, 32 refs incl. the intentional off-catalogue connectors]*. F8 note: no Tolerance fields were added — the ±0.1 % intent now lives in the ARG02 MPNs themselves, which is acceptable.
- **TLV431 symbol pin-swap (should-fix 1) → fixed.** New `Voided-Oblivion-misc:TL431BQDBZ` symbol has the correct TI DBZ map (1=REF, 2=K, 3=A) *[RAW symbol + analyzer pins]*, and the R27/R28 topology is now the textbook adjustable form (REF–R27–cathode node, R28 DNP to GND) — the divider provision is no longer booby-trapped. PCB pads still carry the old mapping (benign while R27 = 0 Ω; the pad-1/2 traces at U10 swap on the next sync).
- **Q1 slew race (should-fix 2) → fixed.** R36 10 k → **1 kΩ** (`0402WGF1001TCE`) *[RAW]* — turn-off ~10× faster, bounding the BS+ excursion to <100 mV even at PD-spec-max slew, and Q1's off-state Vgs improves as a side effect. PCB value field still says 10 kΩ (see sync gap).
- **Hygiene:** `sym-lib-table` gained `Voided-Oblivion-misc` (ERC now exactly 1 error = the intentional `SM BUS` OR ✓); all 4 duplicated-via pairs (`holes_co_located`) gone; starved thermals gone; DRC warnings 587 → **370** (new no-silkscreen-text 0402 footprints account for much of the drop); dangling tracks 11 → 9. The PG-6P male footprint edit is cosmetic geometry only (courtyard/silk line nudges, no pad changes) *[RAW diff]*.

## Still open (unchanged from the main review)

- **E3 — R79–R82 still 100 k**: all four `PD EN` nets remain E9-exposed; every edge HV switch still turns on during an MCU-float window with PD+ live. Fix unchanged: **→ 2.2 k** (BJT base, not the CMOS 8.2 k number).
- **E4 — R38 still 100 k** on `+5VP EN`: uncommanded big-buck enable during MCU float. Fix unchanged: **→ 4.7 k**.
- **B4** — the same 11 `track_width` errors on `/MCU D±` *[DRC]*; the rule carve-out still isn't in `.kicad_dru`.
- **B5** — `PD_TRUNK*` / `CORNER_VOID_*` rule areas still don't exist *[RAW]*; two custom rules still inert.
- PD+ In2 isolated island (67.4, 98.1), 22 dangling vias, stitching pass, silk-edge 50, the doc corrections (AGENTS.md §6 **CC-not-crossed** — re-verified straight on this revision *[RAW]* — and the accepted-risk log extensions), and saving the fetched LM66100/AP2171 PDFs into `Refrences/datasheets/`.

## New since the main review: the schematic↔PCB sync gap

`d71a73c` edited the schematic but never ran **Update PCB from Schematic**, so the board now *disagrees* with the schematic exactly where the fixes are:

| Ref | Schematic (truth) | PCB (as-routed) | Consequence |
|---|---|---|---|
| R37 pad 1 | **VBUS1** | **VBUS2** net *and copper* | **E1 is not fixed on the board.** The mux still mis-selects until this pad is re-netted and rerouted to VBUS1 copper |
| U10 pads 1/2 | 1=REF node, 2=+1V24ref | 1=+1V24ref, 2=REF node | Electrically identical while R27 = 0 Ω; traces at pads 1/2 must swap on sync for the R28 provision to be real |
| R36 value | 1 kΩ | 10 kΩ | Cosmetic if the BOM exports from the schematic; fix on sync |

*[RAW: `analysis/2026-08-18_1139/pcb.json` pad_nets vs schematic nets]*. Cross-analysis' XV checks didn't flag these (they compare net-name presence, not per-pad assignment) — worth knowing that this gap class is invisible to both DRC and the analyzer's sync summary.

## Remaining order of work

1. Fix **E3/E4** in the schematic (R79–R82 → 2.2 k, R38 → 4.7 k) — do it *before* the sync so there's one sync, not two.
2. **Update PCB from Schematic** → reroute R37 pad 1 to VBUS1 copper, swap the two short traces at U10 → refill → DRC.
3. **B4** rule carve-out + **B5** rule areas → refill → DRC clean (expect real findings from the newly-live trunk rule).
4. Finish the sourcing tail: R22, C26/C31 (≥25 V, derating-aware), C28/C29/C34/C35, U17/U18, Q13/Q14.
5. Doc pass: comms.md SEL priority (now port 1), AGENTS.md §6 CC contract, accepted-risk extensions, save the two datasheets.
6. Hygiene sweep (island, dangling vias, stitching, silk) → gerbers → gerber analysis → order.
