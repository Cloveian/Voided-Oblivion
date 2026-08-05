# TS3USB30E (USB mux) and TPD2E2U06 (ESD array) — implementation reference

Independent read of the datasheets only. No schematic/PCB file was opened while writing this. Figures are cited to the section/table of the datasheet as printed; anything not stated in the datasheet is marked **not specified**.

Sources used:
- `TS3USB30E-usb-mux.pdf` — TI SCDS255G, Dec 2008, revised Oct 2024 (current/primary source below).
- `TS3USB30E-mux-lcsc.pdf` — TI SCDS255F, Aug 2015 (older revision, checked for deltas, noted where they matter).
- `TPD2E2U06-esd.pdf` — TI SLLSEG9C, Jun 2013, revised Dec 2019.
- `app-notes/TI-esd-protection-usb.pdf` — **this file is mislabeled in the repo.** Its actual content is TI SLLA387A "Understanding Peak IOH and IOL Currents" (a gate-driver app note), not an ESD document. It was not used for anything below. The document the filename promises — TI SLVAF82B "ESD and Surge Protection for USB Interfaces" — was fetched from ti.com/lit/pdf/slvaf82 and saved to `Refrences/datasheets/app-notes/ti-esd-surge-protection-usb-interfaces-slvaf82.pdf` for this analysis. Recommend the maintainer re-fetch/rename the original file.
- `USB-TypeC-spec.pdf` — USB Type-C Cable and Connector Specification, Release 2.0, Aug 2019 — used only for VBUS timing parameters (Table 4-29) to characterize how long/deep a PD-rail power dip can be.

---

## TS3USB30E — 1:2 USB 2.0 mux/demux (ordered as TS3USB30ERSWR, UQFN-10, 1.8 mm × 1.4 mm)

### Part identity

- TI TS3USB30E, "ESD-Protected, High-Speed USB 2.0 (480 Mbps) 1:2 Multiplexer/Demultiplexer Switch With Single Enable." (Description, p.1)
- This project uses it purely as a **full-speed (12 Mbit/s)** switch — the "high-speed" (480 Mbps) branding is the part's rated ceiling, not a requirement being exercised here.
- Two package options exist: DGS (VSSOP-10, 3.00 mm × 4.9 mm nominal per rev G table, 3.00×3.00 mm per rev F table — the two datasheet revisions disagree on VSSOP body size printed in the info table; not consequential since the project specifies RSW) and RSW (UQFN-10, 1.8 mm × 1.4 mm). Project's chosen orderable part `TS3USB30ERSWR` is the RSW/UQFN-10 variant. (§Package Information / Device Information table, p.1)
- Pins (RSW/UQFN-10, Figure 4-1): 1=D1+, 2=D2+, 3=D+, 4=GND, 5=D-, 6=D2−, 7=D1−, 8=OE, 9=VCC, 10=S. (Table 4-1)
- Function: `D` (common, pin 3/5) is a bidirectional pass-through to either `D1` (port 1, pins 1/7) or `D2` (port 2, pins 2/6), selected by `S`, gated by `OE`. Truth table (Table 7-1): S=X, OE=H → disconnect (both channels high-Z); S=L, OE=L → D=D1; S=H, OE=L → D=D2.

### Absolute maximum ratings that constrain this design

All from §5.1 Table 5-1 (Absolute Maximum Ratings), TA range unless noted:

| Parameter | Min | Max | Unit | Note |
|---|---|---|---|---|
| VCC | −0.5 | **7** | V | This is the hard ceiling — see "gotchas" below, this rules out several rails in this project. |
| VIN (control inputs S, OE) | −0.5 | **7** | V | Fixed absolute rating, *not* VCC-relative. |
| VI/O (D+, D−) when VCC > 0V | −0.5 | **VCC + 0.3** | V | I/O clamp tracks VCC when the part is powered. |
| VI/O (D+, D−) when VCC = 0V | −0.5 | **5.25** | V | Powered-down tolerance — matters for cold-attach/hotplug. |
| IIK (control input clamp current, VIN < 0V) | — | −50 | mA | |
| II/OK (I/O clamp current, VI/O < 0V) | — | −50 | mA | |
| II/O (ON-state switch current) | — | ±64 | mA | |
| Continuous current through VCC or GND | — | ±100 | mA | |
| Tstg | −65 | 150 | °C | |

Footnote (1) on the Features-page Latch-up bullet ("Latch-up performance exceeds 100 mA per JESD 78, Class II") reads **"Except OE and S inputs."** The control pins are explicitly excluded from that latch-up guarantee. This is a real constraint on how SEL should be driven (see Gotchas).

### Key electrical characteristics

§5.2 ESD Ratings (Table, JEDEC component-level test methodology):
- HBM (JS-001), all pins: **8000 V**
- HBM, I/O port to GND only (high-voltage HBM, in addition to standard A114-B Class II testing): **15000 V**
- CDM (JS-002): **1000 V**

**No IEC 61000-4-2 (system-level, real-world ESD gun) rating is given anywhere in this datasheet.** This is the crux of the "is external ESD still needed" question below — flagged now.

§5.3 Recommended Operating Conditions:
- VCC: **3 V to 4.3 V**. (Features bullet on p.1 says "VCC operation at 2.7V to 4.3V" — this is a discrepancy between the marketing Features list and the binding Table 5-3; the older rev F datasheet's Recommended Operating Conditions already said 3 V min, so I'm treating **3 V as the real minimum**, not 2.7 V.)
- VIH: 1.3 V–VCC (VCC = 3–3.6 V) or 1.7 V–VCC (VCC = 4.3 V)
- VIL: 0–0.5 V (VCC = 3–3.6 V) or 0–0.7 V (VCC = 4.3 V)
- VI/O: 0 to VCC
- TA: −40 to 85 °C

§5.5 Electrical Characteristics (VCC = 3.3 V typ unless noted):
- RON: 6 Ω typ / **10 Ω max** (VCC = 3 V, VI = 0.4 V, IO = −8 mA)
- ΔRON (channel-to-channel match): 0.35 Ω typ
- ron(flat) (flatness across VI/O): 2 Ω typ
- Cio(ON): 7.5 pF typ; Cio(OFF): 2 pF typ (VCC = 3.3 V)
- Cin (control inputs): 1 pF (VCC = 0 V, VIN = VCC or GND)
- ICC: 1 µA max (switch on or off, II/O = 0 mA) — Features bullet claims "70 nA maximum," a tighter number than the 1 µA in the electrical table; use **1 µA** as the binding spec.
- ΔICC per input at TTL level: 10 µA max
- IIN (control input leakage): ±1 µA
- IOZ (D+/D− off-state leakage, switch off): ±1 µA
- IOFF (VCC = 0 V leakage, "partial power-down mode"): ±2 µA max
- VIK (control input clamp voltage, VCC=3V, II=−18mA): −1.2 V typ

§5.6 Dynamic Electrical Characteristics (VCC = 3.3 V ±10%):
- Crosstalk (XTALK): **−32 dB typ** @ 240 MHz (rev G value; rev F stated −54 dB — the newer revision is a *weaker* published spec, use −32 dB)
- OFF isolation (OISO): **−32 dB typ** @ 240 MHz (rev G; rev F stated −40 dB, same caveat)
- Bandwidth (−3 dB): 1400 MHz typ (rev G; rev F stated 900 MHz)

§5.7 Switching Characteristics (VCC = 3.3 V ±10%):
- tpd: 0.25 ns typ @ 480 Mbps
- tON (SEL→D or OE→D): 30 ns max
- tOFF (SEL→D or OE→D): 25 ns max
- tSK(O) (output skew, center port to any other port): 50 ps typ
- tSK(P) (pulse skew, tPHL−tPLH): 20 ps typ
- tJ (total jitter @ 480 Mbps PRBS): 20 ps typ

### Design equations

RC bandwidth sanity check using the datasheet's own RON/Cio numbers:
`f_-3dB ≈ 1 / (2·π·RON·Cio(ON)) = 1 / (2·π·10Ω·7.5pF) ≈ 2.1 GHz`
This is the same order of magnitude as the datasheet's characterized 1400 MHz figure (§5.6) — the difference is fixture/board parasitics not captured by a single-pole estimate. Either number is ~100× the bandwidth full-speed USB (12 Mbit/s, fundamental well under 100 MHz even accounting for edge rates) needs — **the switch is not a bandwidth constraint at FS.**

Worst-case switch power dissipation at the RON test condition:
`P = IO² · RON = (8 mA)² × 10 Ω = 0.64 mW` — trivial, no thermal derating needed for signal-path current.

### Worked values for this application

**VCC rail selection — this is the sequencing-sensitive decision.**

The project has four candidate rails: PD+/HV (9–20 V, switched per-edge), BS+ (5 V, always-on bootstrap), gated-5V (5 V, MCU-enabled buck), 3V3 (LDO, alive as soon as any cable supplies 5V).

- **PD+/HV is disqualified outright, not just "non-ideal": VCC absolute max is 7 V (§5.1).** PD negotiates 9 V, 15 V, 20 V rails as a matter of routine operation — connecting VCC to PD+ would exceed the absolute maximum rating under normal (not fault) conditions and destroy the part.
- **BS+ (5 V) is within absolute max (7 V) but exceeds the recommended operating max (4.3 V, §5.3).** RON, Cio, XTALK, OISO and all switching timing in this datasheet are only characterized up to VCC = 4.3 V. Running VCC at 5 V is out-of-spec: nothing is guaranteed, and D+/D− clamp would track up to VCC+0.3 = 5.3 V (§5.1), higher than needed.
- **gated-5V is disqualified for the same voltage reason as BS+, plus it is not always-on** — it is MCU-enabled and shares state with the RGB/submodule power path, i.e. exactly the kind of rail that can sequence/glitch independently of USB activity.
- **3V3 is the correct choice.** It sits centrally in the 3–4.3 V recommended range (§5.3), it is already the rail powering the RP2350B and Hall-effect analog front end (so if 3V3 isn't up, there's no MCU behind the mux to care about bus state anyway), and critically:

**Why VCC must not be on the PD/HV rail even if voltage were survivable — the sequencing argument.** Per USB Type-C spec Release 2.0 §4.11.2 Table 4-29 (`USB-TypeC-spec.pdf`), VBUS timing parameters include:
- `tVBUS_ON`: max **275 ms** from Attached.SRC entry to VBUS reaching vSafe5V
- `tVBUS_OFF`: max **650 ms** from detach until VBUS reaches vSafe0V

These are not fault conditions — they're the *normal* bounds on how long a VBUS transition (attach, detach, and by extension renegotiation transients riding through similar state machine paths) is allowed to take. A rail that can legitimately sag or disappear for up to 650 ms is not a supply a USB data-path switch should be powered from — every one of the mux's electrical specs (RON, leakage, switching time) is characterized against a *stable* VCC. Powering VCC from PD+/HV (were its voltage even in range) would mean the mux's own logic-high/low thresholds and RON drift or drop out in lockstep with every PD attach/detach/renegotiation event — precisely the "glitch or float the bus during power transition" failure mode called out in the task. 3V3 being derived independently (LDO, "alive as soon as any cable supplies 5V") does not ride PD's negotiation state machine at all.

**SEL (S pin) drive network.**

S's absolute max is a flat **7 V regardless of VCC** (§5.1, VIN is not written as "VCC + x" the way the D+/D− I/O max is — it's a fixed −0.5/7 V rating). The task states the select signal is "derived from whether one particular port has VBUS present," originating from a node that "can be at 5V and could in principle be exposed to a rail reaching 20V." Two separate concerns:

1. **Absolute overvoltage.** If the VBUS-present detector's output stage (comparator, whatever) is ever allowed to swing toward the raw 9–20 V PD rail — e.g. a pull-up resistor tied to PD+ instead of a low-voltage rail, or a fault that shorts the detector node to VBUS — 7 V is violated immediately and destructively. The detector's output stage pull-up (or push-pull supply) must be referenced to a rail that itself cannot exceed ~7 V under any circumstance: BS+ (5 V, always-on) is safe by voltage; PD+/HV (9–20 V) must never appear directly on this node under any single fault, so a series limiting resistor plus a clamp (zener/TVS to VCC or GND) between any HV-adjacent divider and the S pin is warranted as a second line of defense if the detector topology puts S anywhere near a HV-derived node.
2. **Above-VCC drive while under the abs-max ceiling.** If the detector is referenced to BS+ (5 V) while mux VCC = 3.3 V, S can sit at 5 V — under the 7 V absolute max, but **above VCC**, which forward-biases the internal ESD/clamp structure from pin to VCC and sources current back into the VCC rail. This is exactly the class of stress the datasheet's own footnote flags: **S and OE are excluded from the 100 mA JESD 78 Class II latch-up guarantee** (§ Features, footnote 1). Driving S from a 5 V-referenced signal into a 3.3 V-VCC part is not covered by that guarantee. **Recommendation: whatever generates the VBUS-present decision should have its logic output stage referenced to the same 3V3 rail that powers the mux's VCC**, not to BS+ or a raw HV divider. If the natural output of the detection circuit is 5 V-referenced, level-shift it (or use an open-drain output pulled up to 3V3) before it reaches S.

No internal pull-up or pull-down value is specified for S or OE anywhere in the datasheet — only leakage (IIN = ±1 µA) and input capacitance (Cin = 1 pF) are given. §8.2.1 explicitly instructs: **"TI recommends that the digital control pins S and OE be pulled up to VCC or down to GND to avoid undesired switch positions that could result from the floating pin."** No resistor value is given — **not specified**, so the value below is my own choice against the leakage number, not a datasheet figure:

Worked pull resistor: with IIN = ±1 µA max and a 100 kΩ (E24) pull, worst-case offset = 1 µA × 100 kΩ = 100 mV — negligible against VIL max (0.5–0.7 V) or VIH min (1.3–1.7 V), and weak enough not to fight an active driver once the detector circuit powers up. This value is a design choice justified by the datasheet's leakage spec, not a datasheet-stated resistor value.

**OE handling.** Not addressed at all in the project brief provided to me. The truth table's default-safe state is OE = H (disconnect). If OE is intended to be permanently enabled, tie it directly to GND (not left floating) per §8.2.1's floating-pin warning — this needs an explicit design decision that I can't make blind.

**Unused-pin termination.** §8.2.2: "TI recommends to connect any unused pins to ground through a 50 Ω resistor to prevent signal reflections." In this application both D1± and D2± ports are used (two receptacles), so there should be no unused D-side pins to terminate. If a future variant removes one receptacle, terminate that port's D+/D− to GND through 50 Ω each. Ideal 50 Ω → nearest E96 1% value **49.9 Ω** (common USB-termination value) → error −0.2%. Standard E24 doesn't have 50 Ω either; 49.9 Ω (E96) is the conventional choice in TI's own USB reference designs. Size: 0402 is fine (no voltage/power concern).

### Recommended implementation (pin by pin)

| Pin | Signal | Recommendation |
|---|---|---|
| 1 | D1+ | To USB-C receptacle 1 D+ (via TPD2E2U06 #1, IO1 or IO2), differential pair with pin 7 |
| 2 | D2+ | To USB-C receptacle 2 D+ (via TPD2E2U06 #2), differential pair with pin 6 |
| 3 | D+ | Common, to RP2350B USB D+ |
| 4 | GND | Solid ground, short via to plane |
| 5 | D− | Common, to RP2350B USB D− |
| 6 | D2− | To USB-C receptacle 2 D− (via TPD2E2U06 #2) |
| 7 | D1− | To USB-C receptacle 1 D− (via TPD2E2U06 #1) |
| 8 | OE | Tie to GND if permanently enabled (needs explicit decision, not specified by task); do not float |
| 9 | VCC | **3V3 rail**, not PD+/HV, not BS+/gated-5V. Local bypass cap (see Decoupling). |
| 10 | S | Driven by VBUS-present detector logic referenced to the **same 3V3 domain**. Add pull-down (or pull-up, depending on which port should be the power-up default) sized ≈100 kΩ per the leakage-margin analysis above (not a datasheet value). |

### Decoupling and passives

§8.3 Power Supply Recommendations: "TI recommends placing a bypass capacitor as close as possible to the supply pin VCC... Place supply bypass capacitors as close to VCC pin as possible and avoid placing the bypass caps near the D+ and D− traces" (§8.4.1). **No capacitance value is given anywhere in the datasheet** — not specified. Standard practice for a low-current (ICC ≤ 1 µA quiescent, transient switching current negligible per the RC/power numbers above) logic supply pin is a single 100 nF 0402 X7R ceramic directly at pin 9, referenced to the adjacent GND (pin 4). This is an engineering default, not a cited datasheet number — call it out as such if audited.

### Layout notes

All from §8.4.1/§8.4.2, TI's own text, condensed:
- D+/D− traces must be **equal length**, **≤ 4 inches**, or eye-diagram performance degrades (this ceiling is for the 480 Mbps HS case the datasheet is written around; at FS 12 Mbit/s this length limit has large margin, but equal-length/matched routing should still be kept for common-mode noise rejection).
- Route with a controlled differential impedance matching the intended cable/system impedance; minimize vias and corners; use two 45° turns or an arc instead of a single 90°.
- Route all high-speed traces over continuous (uncut) reference planes; avoid crossing plane splits.
- Keep USB traces away from crystals, oscillators, clock generators, switching regulators, and magnetic parts.
- Avoid stubs; if unavoidable, keep any stub < 200 mm.
- TI's own example layout (Figure 8-5) places the VCC bypass cap away from the D+/D− traces, with OE and S routed in from the side opposite the data pairs, and GND stitching vias around the part.
- Given the two-receptacle topology here, physically the natural layout is: receptacle 1 — TPD2E2U06 #1 — mux D1± (pins 1/7); receptacle 2 — TPD2E2U06 #2 — mux D2± (pins 2/6); mux common D± (pins 3/5) — short trace to RP2350B USB pins.

### Gotchas and failure modes

- **VCC on PD+/HV is not a design tradeoff, it's a destroyed part** — 7 V absolute max vs 9–20 V PD rail. If this project has a bug in this family, this is the first thing to check.
- **S/OE excluded from the JESD 78 latch-up guarantee** — driving them from a rail above the mux's own VCC (even within the 7 V absolute max) is a real, named risk, not theoretical.
- **The two published bandwidth/crosstalk numbers differ between datasheet revisions** (BW 900→1400 MHz, XTALK −54→−32 dB, OISO −40→−32 dB between rev F and rev G) — same silicon, different characterization/spec commitment. Design against the current (rev G, −32 dB / 1400 MHz) numbers; don't quote the more optimistic rev F figures from an older copy of the datasheet.
- **Features-bullet numbers don't always match the binding tables**: VCC min (2.7 V bullet vs 3 V table) and ICC max (70 nA bullet vs 1 µA table) both disagree between the marketing Features list and §5.3/§5.5. Always use the numbered table, not the bullet list.
- **Powered-off state is functionally safe but not a documented "hard open."** With VCC = 0 V, IOFF leakage is bounded (±2 µA max) and D+/D− tolerate up to 5.25 V (§5.1) — this is good for hotplug (a tile whose 3V3 hasn't come up yet won't corrupt a neighbor's bus), but the datasheet never states the switch is a literal open circuit at VCC=0, only that leakage is bounded. Treat it as "electrically inert, not verified as a hard break" if a design depends on true isolation during power-loss.
- **Switching S mid-transaction will corrupt in-flight USB traffic** — tON/tOFF are 25–30 ns, fast enough that a switch event looks like a bus glitch to anything mid-packet. S should only change while the bus is idle/unenumerated (e.g., during the initial VBUS-present decision at attach, before enumeration begins), never as a live failover during active use.

### Open questions / not determinable from the datasheet

- No bypass capacitor value is specified (assumed 100 nF, not a datasheet number).
- No pull-up/pull-down resistor value is specified for S/OE (100 kΩ proposed here, derived from leakage margin, not from the datasheet).
- No IEC 61000-4-2 system-level ESD number is given for this part at all — see the ESD verdict below.
- Whether the actual VBUS-present detector circuit in this project is push-pull or open-drain, and what rail its output stage is referenced to, is **not knowable from these two datasheets** — that's a schematic-level fact this document deliberately wasn't shown.
- RP2350B's own USB D+/D− pin absolute-max voltage was not verified against the mux's downstream output here (out of scope for this document — RP2350B's own page in `docs/schematic-design/mcu.md` is presumably the place for that). For context only: the RP2350 datasheet's general GPIO absolute max is IOVDD+0.5 V for standard pins or up to 5.5 V for "FT" 5V-tolerant pins with IOVDD present (Table 1433/1434, RP2350 datasheet) — whether the USB DP/DM pins specifically fall in the FT class wasn't checked here.

---

## TPD2E2U06 — dual-channel ESD protection diode array

### Part identity

- TI TPD2E2U06, "Dual-Channel High-Speed ESD Protection Device" — a passive TVS diode array, 2 channels, intended for USB 2.0/LVDS/I²C data lines. (§3 Description)
- Two packages: DRL (SOT-5X3, 5-pin, 1.60 mm × 1.20 mm body) with pinout IO1=3, IO2=5, GND=4, NC=1,2; and DCK (SC70, 3-pin, 2.0 mm × 1.25 mm body) with pinout IO1=1, IO2=2, GND=3. (§5 Pin Configuration and Functions, Device Information table p.1)
- Purely passive — "there is no need to power it" (§9 Power Supply Recommendations). No VCC pin, no enable pin.
- No package suffix was given in the task brief; see recommendation below.

### Absolute maximum ratings that constrain this design

§6.1 Table:

| Parameter | Max | Unit | Note |
|---|---|---|---|
| IPP (peak pulse current, tp=8/20µs) | 5.5 | A | measured at 25°C |
| PPP (peak pulse power, DRL) | 85 | W | measured at 25°C |
| PPP (peak pulse power, DCK) | 75 | W | measured at 25°C |
| Operating temperature | −40 to 125 | °C | |
| Storage temperature | −65 to 155 | °C | |

§6.3 Recommended Operating Conditions: VIO 0 to **5.5 V**; TA −40 to 125 °C.

### Key electrical characteristics

§6.2 ESD Ratings:
- HBM (JS-001): **±4000 V**
- CDM (JESD22-C101): **±1500 V**
- **IEC 61000-4-2 contact discharge: ±25000 V (±25 kV)**
- **IEC 61000-4-2 air-gap discharge: ±30000 V (±30 kV)**

This is the number the mux datasheet never gives — a real, system-level connector-facing ESD rating.

§6.5 Electrical Characteristics:
- VRWM (reverse stand-off voltage, IIO < 10 µA): **5.5 V max** — the device's rated continuous working voltage.
- VBR (breakdown voltage, IIO = 1 mA): 6.5 V min, 8.5 V typ.
- VCLAMP, IO→GND: 9.7 V typ @ IPP=1A (TLP); 12.4 V typ @ IPP=5A (TLP).
- VCLAMP, GND→IO (reverse polarity): 1.9 V typ @ IPP=1A; 4 V typ @ IPP=5A.
- RDYN, DRL package: IO→GND 0.5 Ω typ; GND→IO 0.25 Ω typ.
- RDYN, DCK package: IO→GND 0.6 Ω typ; GND→IO 0.4 Ω typ.
- CL (line capacitance, f=1MHz, VBIAS=2.5V): **1.5 pF typ / 1.9 pF max**.
- CCROSS (channel-to-channel capacitance): 0.02 pF typ / 0.03 pF max.
- ΔCIO-TO-GND (channel-to-channel capacitance mismatch): 0.03 pF typ / 0.1 pF max.
- ILEAK (VIO=2.5V): 1 nA typ / **10 nA max**.

§7.3.2: "These capacitances support data rates in excess of 1.5 Gbps" — far beyond the 12 Mbit/s FS requirement here, and also comfortably under HS (480 Mbps) if this project ever needed it.

### Design equations

None required beyond straightforward parameter comparison — this is a passive clamp with no derived sizing (no series resistor is specified or needed by the datasheet; it's a shunt device only).

Capacitance budget check: TPD2E2U06 (1.5 pF typ per channel) + TS3USB30E Cio(ON) (7.5 pF typ) ≈ 9 pF total load presented to each active USB data line, once summed with trace parasitics. FS USB's capacitive loading budget is defined in the USB 2.0 electrical specification, which is **not among the reference documents provided for this task** — I have not independently verified a numeric FS capacitance ceiling here, so I won't state one. Qualitatively: FS (12 Mbit/s) tolerates dramatically more load capacitance than HS (480 Mbps) by design (much longer bit period, slower required edge rates), and the TI ESD app note (SLVAF82B, fetched separately, see below) recommends ESD diodes with capacitance **< 4 pF** specifically for USB 2.0 D+/D− lines (§3.2) — TPD2E2U06's 1.5 pF typ is well inside that guidance.

### Worked values for this application

- **Working voltage vs signal swing.** D+/D− full-speed signaling swings roughly 0–3.3 V referenced to the transceiver supply. VRWM = 5.5 V max rating comfortably covers this with margin (TI's own USB app note, SLVAF82B §3.2, recommends VRWM ≥ 3.3 V for USB 2.0 D+/D− — TPD2E2U06 exceeds that).
- **IEC 61000-4-2 vs TI's own recommendation.** SLVAF82B §3.2 recommends a minimum IEC 61000-4-2 rating of **8 kV contact / 15 kV air-gap** for USB 2.0 D+/D− lines. TPD2E2U06's 25 kV/30 kV rating is 3–2× that minimum — appropriately overspecified for a connector that a user can physically touch (two exposed USB-C receptacles on this board, both need this).
- **Clamp voltage vs downstream part.** VCLAMP at IPP=5A (a real IEC-level strike) is 12.4 V typ. This number is naturally higher than any of the mux's or the RP2350B's normal operating voltage — that's expected and correct for a TVS: the clamp voltage during a transient energy-dump event is allowed to exceed steady-state absolute max, because the event is sub-microsecond and the downstream device's own ESD structures (plus the fact that the TVS has already diverted the bulk of the current) keep it survivable. Whether 12.4 V is safely below the RP2350B's D+/D− absolute max specifically was **not verified here** (out of scope — that's the RP2350B's own document).

### Recommended implementation (pin by pin)

Two TPD2E2U06 instances needed — one per USB-C receptacle, ahead of the mux (mux has two upstream ports, each needs independent connector-facing protection since either receptacle can be exposed to an ESD event regardless of which one is currently selected/enumerated):

| Instance | IO1 | IO2 | GND |
|---|---|---|---|
| TPD2E2U06 #1 | Receptacle 1 D+ (upstream of mux D1+) | Receptacle 1 D− (upstream of mux D1−) | GND plane, shortest possible via |
| TPD2E2U06 #2 | Receptacle 2 D+ (upstream of mux D2+) | Receptacle 2 D− (upstream of mux D2−) | GND plane, shortest possible via |

Channel assignment (IO1 vs IO2 to D+ vs D−) is arbitrary — §8.2.2.1: "The symmetry of the device provides flexibility when selecting which of the 2 I/O channels will protect which signal lines." No NC-pin requirement beyond leaving them per Table (§5 Pin Functions): "NC... left floating, grounded, or connected to VCC" (DRL package only, since there's no VCC net anywhere near this passive part, "connected to VCC" in that sentence is boilerplate from a shared pin-description template — tie NC to GND or leave floating, either is explicitly permitted).

**Package recommendation:** not specified by the task, so this is my own read of the datasheet's guidance. §7.3.7 specifically calls out DRL (SOT-5X3) as "small easy-to-route... offers flow-through routing" with GND as the center pin between the two IO channels on opposite sides of the package. For a receptacle→mux path this flow-through geometry (signal in one side, signal out the other, GND stitched in the middle) lines up naturally with the physical path from connector to mux and keeps the GND return path short between the two channels, which also helps the datasheet's own §10.1 EMI-coupling layout advice (below). DCK (SC70-3) is a viable smaller-pin-count alternative if board area is tighter, at the cost of losing the flow-through pinout (IO1/IO2/GND arranged as a normal 3-pin device instead).

### Decoupling and passives

None — this is a passive device with no supply pin (§9). No decoupling applicable.

### Layout notes

§10.1 Layout Guidelines, verbatim guidance condensed:
- **"The optimum placement is as close to the connector as possible."** EMI from an ESD event can couple from the struck trace to nearby unprotected traces — keep any unprotected trace away from the segment between the connector and the TVS.
- Route the protected traces (connector-to-TVS segment) as straight as possible.
- Eliminate sharp corners on the protected traces; use the largest practical rounding radius (electric fields build up on corners, increasing EMI coupling).
- §10.2 Layout Example (Figure 12, DRL package): IO1 and IO2 on opposite sides, GND via directly under/adjacent to the GND pin, in a flow-through arrangement matching the "small easy-to-route" claim.

Net effect for this board: TPD2E2U06 sits physically between the USB-C receptacle and the mux, oriented so the connector-side traces are as short and via-free as possible, with the mux-side traces continuing on to D1±/D2±.

### Gotchas and failure modes

- **This part protects D+/D− only.** It has no channel for VBUS or CC. VBUS surge protection (relevant given this project's 9–20 V PD rail and hot-plug/hot-unplug inductive ringing) and CC-line protection are out of scope for the TPD2E2U06 and need separate parts — not addressed in this document since they weren't part of the assignment, but flagging so it isn't assumed "USB protection is done" once these two channels are in.
- **Passive means no failure indication.** If a channel is ever driven into breakdown continuously (design fault elsewhere pushing DC voltage above VRWM), there's no way to observe it electrically without measuring VCLAMP/leakage directly — no enable/fault pin exists to poll.
- Package NC pins (DRL only) being "left floating, grounded, or connected to VCC" per the pin table is copy-pasted boilerplate from a family of parts that do have supply pins — don't read it as implying this part needs a VCC connection; it emphatically does not (§9).

### Open questions / not determinable from the datasheet

- Exact channel-to-D+-vs-D− assignment doesn't matter electrically (device is symmetric) but wasn't specified by the task, so it's a free choice at layout time.
- Whether DRL or DCK package is the intended orderable variant for this project isn't stated in the task — DRL recommended above on datasheet-stated layout merits, but this is a judgment call, not a hard requirement.
- Real-world downstream survivability of the 12.4 V (IPP=5A) clamp voltage against the RP2350B's D+/D− absolute max was not verified — out of scope here.

---

## Is the external ESD array needed?

**Yes — the TPD2E2U06 (or an equivalent) is needed, not redundant, and it belongs upstream of the mux, one per connector.**

Reasoning:

1. The TS3USB30E's own ESD spec is **JEDEC component-level only** — 8000 V HBM (all pins), 15000 V HBM (I/O-to-GND only, §5.2), 1000 V CDM. These are die-handling/manufacturing-process ESD ratings (per JEDEC JS-001/JS-002 methodology: charged capacitor discharged through a defined RC network directly into a pin under controlled lab conditions).
2. **The TS3USB30E datasheet states no IEC 61000-4-2 rating at all.** IEC 61000-4-2 is the system-level test standard (contact and air-gap discharge through a human/furniture-model gun) that characterizes survivability at an *exposed connector a user can physically touch* — a fundamentally different (and for connector-facing purposes, more relevant) stress than JEDEC HBM/CDM. TI's own separately-fetched app note (SLVAF82B, §3.2) explicitly recommends a minimum of 8 kV contact / 15 kV air-gap IEC 61000-4-2 rating for any USB 2.0 D+/D− line, and lists dedicated ESD diode part numbers (ESD321, ESD122, TPD4E05U06, etc.) as the way to meet it — never suggesting a USB mux/switch IC alone is sufficient for that role.
3. This project has **two physically exposed USB-C receptacles**, both user-accessible connectors regardless of which one currently has an enumerated host. Both need independent connector-level protection; the mux only sits behind them, so putting the TVS only after the mux would leave one receptacle covered depending on S state and never both simultaneously.
4. TPD2E2U06 is well matched to the FS/HS USB role by every number that matters: capacitance (1.5 pF typ, under the ESD app note's <4 pF USB2.0 guidance and TS3USB30E's own 7.5 pF Cio(ON) budget), working voltage (5.5 V max ≥ the 3.3 V USB2.0 signal swing per SLVAF82B's ≥3.3V guidance), and IEC 61000-4-2 rating (25 kV/30 kV, 3×/2× the app note's stated minimum).

**Placement: connector → TPD2E2U06 (one per receptacle, IO1/IO2 = D+/D−) → TS3USB30E D1±/D2± → TS3USB30E common D± → RP2350B.** Two TPD2E2U06 instances total.
