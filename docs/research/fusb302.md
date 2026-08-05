# FUSB302BMPX - datasheet research
> Independent datasheet read. Not written against the existing schematic.

Source: `Refrences/datasheets/FUSB302BMPX-pd-phy.pdf` (Fairchild/onsemi, FUSB302B "Programmable USB Type-C Controller w/PD", Rev. 1.4, Aug 2016). Page numbers below are the datasheet's own footer pagination as extracted with `pdftotext -layout`. Cross-references to `Refrences/datasheets/USB-TypeC-spec.pdf` (Release 2.0, Aug 2019) and `Refrences/datasheets/app-notes/TI-usb-type-c-pd-design-guide.pdf` are marked explicitly.

## Part identity

- Manufacturer: onsemi (originally Fairchild Semiconductor; datasheet still carries Fairchild branding/copyright with an onsemi transition notice on the cover).
- Ordering part **FUSB302BMPX**: top mark "UA", operating temperature **-40 to +125 °C**, package **14-lead MLP, 2.5 mm x 2.5 mm, 0.5 mm pitch**, tape-and-reel packing (Ordering Information table, p.1-2).
- Sibling packages/variants in the same family: `FUSB302BUCX` (9-ball WLCSP, 1.215 x 1.260 mm, -40 to 85 °C), `FUSB302B01MPX`, `FUSB302B10MPX`, `FUSB302B11MPX` (same MLP-14 package, -40 to 125 °C, differing only in fixed I2C address - see below).
- Function: USB Type-C CC-pin detection/control PHY + BMC (Biphase Mark Coding) USB-PD physical layer. All PD protocol/policy logic runs in the host MCU over I2C - the part itself only does CC switching, comparators/DAC, and BMC framing/CRC (Block Diagram, Fig. 3, p.2).
- I2C 7-bit slave address for **FUSB302BMPX** (and FUSB302BUCX): bits[7:1] = `0100010` = **0x22** (write byte 0x44, read byte 0x45) - Table 4, p.19.
- Two PHYs per tile, each wired to its own I2C bus and its own INT_N line (per project design) - see "Address collision" note below.

## Absolute maximum ratings that constrain this design

Table, p.13 ("Absolute Maximum Ratings"):

| Symbol | Parameter | Min | Max | Unit |
|---|---|---|---|---|
| V_VDD | Supply Voltage from VDD | -0.5 | 6.0 | V |
| V_CC_HDDRP | CC pins when configured as Host, Device or Dual Role Port | -0.5 | 6.0 | V |
| V_VBUS | VBUS Supply Voltage | -0.5 | 28.0 | V |
| T_STORAGE | Storage Temperature Range | -65 | +150 | °C |
| T_J | Maximum Junction Temperature | - | +150 | °C |
| T_L | Lead Temperature (Soldering, 10 s) | - | +260 | °C |
| ESD (HBM, ANSI/ESDA/JEDEC JS-001-2012) | All pins | - | 4 | kV |
| ESD (CDM, JEDEC JESD22-C101) | All pins | - | 1 | kV |

Relevance to this design:
- **VBUS pin, 28 V abs max / 21 V recommended max (see below)** vs. the tile's PD+ / HV rail (9-20 V per project spec): 8 V margin to abs max at 20 V, but only ~1 V margin to the *recommended* max (see Key electrical characteristics). VBUS pin must see the raw connector VBUS through external OVP (datasheet explicitly calls this out - see Recommended implementation).
- **CC pins, 6.0 V abs max**: the project brief specifically flags that an unmated/mismatched CC pin can see VCONN from some cables. VCONN's own recommended operating max is 5.5 V (p.13), so the CC abs-max rating has only **0.5 V** of margin over a worst-case VCONN-on-CC fault. External clamping (TVS) is prudent even though the datasheet's own reference passive list (Table 31) does not include one on CC.
- **VDD, 6.0 V abs max** vs. the 3V3 rail (nominal 3.3 V): comfortable margin (~2.7 V).

## Key electrical characteristics

Recommended Operating Conditions, p.13:

| Symbol | Parameter | Min | Typ | Max | Unit |
|---|---|---|---|---|---|
| V_VBUS | VBUS Supply Voltage | 4.0 | 5.0 | 21.0 | V |
| V_VDD | VDD Supply Voltage | 2.7 | 3.3 | 5.5 | V |
| V_VCONN | VCONN Supply Voltage | 2.7 | - | 5.5 | V |
| I_VCONN | VCONN Supply Current | - | - | 560 | mA |
| T_A | Operating Temperature | -40 | - | +85 | °C |

Note 3 on that table: "This is for functional operation only and not the lowest limit for all subsequent electrical specifications below. All electrical parameters have a minimum of 3.0 V operation." Every DC/AC characteristics table in the datasheet (Baseband PD p.14, CC Switches p.15, Current Consumption p.16, IO Specifications p.17) is specified over **VDD = 3.0 to 5.5 V**. The project's 3V3 LDO rail (nominal 3.3 V) sits inside this guaranteed range with margin, not just the "functional-only" 2.7 V floor.

CC Switches table, p.15 (selected rows):
- `RDEVICE` - Device Pull-down Resistance: **4.6 - 5.6 kΩ** (typ implied ~5.1 kΩ from Table 2's context; explicit min/max only). **Footnote 5: "RDEVICE minimum and maximum specifications are only guaranteed when power is applied."**
- `VUFPDB` - "SNK Pull-down Voltage in Dead Battery under all Pull-up SRC Loads": **Max 2.18 V** (no min/typ given).
- `zOPEN` - CC Resistance for Disabled State: 126 kΩ typ.
- `vVBUSthr` - VBUS threshold at which I_VBUSOK interrupt triggers: 4.0 V typ ("Assumes measure block on, i.e. PWR[2]=1").
- `I80_CCX` / `I180_CCX` / `I330_CCX` - host Rp current sources (80/180/330 µA, ±20% typ tolerance bands) - not used in this sink-only design.
- `vBC_LVL` thresholds (BC=2'b00/01/10): 0.20 V / 0.66 V / 1.23 V typ, ±~5% bands; hysteresis 20 mV typ.

Current Consumption table, p.16:
- `Idisable` (nothing attached, no I2C): 0.37 µA typ, **5.00 µA max**.
- `Itog` (unattached standby, TOGGLE=1): 25 µA min, **40 µA max**. (Matches the Features-page claim "Low Power Operation: ICC = 25 µA (Typical)", p.1.)
- `Ipd_stby_meas` (attached, BMC PD active but idle): 40 µA typ.

IO Specifications table, p.17:
- `VOLINTN` (INT_N output low): max 0.4 V @ IOL = 4 mA.
- `VILI2C` / `VIHI2C`: max 0.51 V / min 1.32 V (VDD = 3.0-5.5 V).
- `VOLSDA` (SDA open-drain low): max 0.35 V @ IOL = 2 mA; `IOLSDA` guaranteed sink current: **min 20 mA** @ VOL = 0.4 V.
- `CI`: 5 pF typ per I/O pin.
- **Note 6 on this table: "I2C pull up voltage is required to be between 1.71 V and VDD."**

I2C Specifications (Fast Mode Plus), p.18: `fSCL` 0 - **1000 kHz**; `Cb` (bus capacitive load) max **550 pF**; `tr`/`tf` max 120 ns; other timing per I2C Fast Mode Plus. The datasheet states (p.12) the I2C slave "fully complies with the I2C specification version 6... designed for Fast Mode Plus traffic up to 1 MHz SCL", while also noting the low-power TOGGLE feature "may not be fully compliant to the 1 MHz operation."

Reference/recommended passives, Table 31, p.34:

| Symbol | Parameter | Min | Typ | Max | Unit |
|---|---|---|---|---|---|
| CRECV | CCx Receiver Capacitance | 200 | - | 600 | pF |
| CBULK | VCONN Source Bulk Capacitance | 10 | - | 220 | µF |
| CVCONN | VCONN Decoupling Capacitance | - | 0.1 | - | µF |
| CVDD1 | VDD Decoupling Capacitance | - | 0.1 | - | µF |
| CVDD2 | VDD Decoupling Capacitance | - | 1.0 | - | µF |
| RPU | I2C Pull-up Resistors | - | 4.7 | - | kΩ |
| RPU_INT | INT_N Pull-up Resistor | 1.0 | 4.7 | - | kΩ |
| VPU | I2C Pull-up Voltage | 1.62 | 1.80 | 1.98 | V |

**Flagged conflict**: Table 31 (p.34) recommends an I2C pull-up rail of 1.62-1.98 V (typ 1.8 V), while Note 6 in the IO Specifications table (p.17) states the pull-up voltage is required only to be "between 1.71 V and VDD" - a much wider, VDD-inclusive range. The datasheet does not reconcile these. See "Gotchas" below.

## Cold-start / Rd presentation analysis

**This is the single most important conclusion in this document, and it is unambiguous: yes, Rd (or a dead-battery-compliant clamp that a source recognizes as Rd) is present on CC1 and CC2 purely from internal FUSB302B circuitry, before VDD exists and with no external pull-down components required on CC.**

Evidence, cited precisely:

1. **Feature list, p.1**: "Dead Battery Support (SNK Mode Support when No Power Applied)" is listed as a headline feature of the part.
2. **CC Switches electrical table, p.15**: a dedicated parameter `VUFPDB` - "SNK Pull-down Voltage in Dead Battery under all Pull-up SRC Loads" - is specified with **Max = 2.18 V** (no min/typ given). This is a distinct, separately-guaranteed spec from the normal Rd resistance.
3. **Same table, Footnote 5**: "RDEVICE minimum and maximum specifications are only guaranteed when power is applied." This explicitly *excludes* the precision 4.6-5.6 kΩ Rd figure from the unpowered condition - the datasheet is careful to separate "the precise 5.1 kΩ Rd you get once VDD is up" from "what CC does with zero power."
4. **Configuration Channel Switch section, p.5**: lists "Device Port Pull-Down (RD)" as one of two integrated switch-matrix functions (the other being "Host Port Pull-Up (IP)"), consistent with Rd being generated on-die rather than by an external resistor network.
5. **Register default, Switches0 (Table 6, addr 0x02, p.21)**: reset value is `0x03` = `PDWN2=1, PDWN1=1` (all other bits 0). This means that **the instant VDD is applied and the chip's internal POR completes**, both CC pull-downs are enabled by hardware reset default - *before firmware issues a single I2C write*. There is no race condition where firmware must configure the part quickly enough to keep Rd present after power arrives.
6. **USB Type-C spec, Release 2.0, Section 4.8.5 "Charging a System with a Dead Battery" (spec p.227-228)**, quoted verbatim: *"A system that supports being charged by USB whose battery is dead shall apply Rd to both CC1 and CC2 and follow all Sink rules... Circuitry to present Rd in a dead battery case only needs to guarantee the voltage on CC is pulled within the same range as the voltage clamp implementation of Rd in order for a Source to recognize the Sink and provide VBUS. For example, a 20% resistor of value Rd in series with a FET with VGTH(max) < VCLAMP(max) with the gate weakly pulled to CC would guarantee detection and be removable upon power up."* This is exactly the class of circuit `VUFPDB` characterizes: a clamped voltage rather than a precision resistor, sufficient to trip a source's Rp/comparator logic and cause it to apply default VBUS, without needing any rail alive.

**Sequencing conclusion for this tile**: at cold attach with zero board voltage, the FUSB302B's internal dead-battery clamp (guaranteed only as `VUFPDB ≤ 2.18 V`, not as a resistance) pulls CC1 and CC2 low enough for a compliant source to recognize a sink and apply VBUS (5 V default). Once VBUS/VDD/3V3 come up and the FUSB302B completes its internal reset, register defaults (`PDWN1=PDWN2=1`) hand off seamlessly to the "real", tighter-toleranced 4.6-5.6 kΩ Rd - with no firmware action required and no gap where Rd could disappear. This directly resolves the chicken-and-egg deadlock described in the project brief: **Rd generation for this chip is a hardware/silicon property, not something firmware or an external passive must supply.**

What is **not** stated by the datasheet (see Open Questions): the internal topology of the dead-battery clamp (resistor+FET per the Type-C spec's illustrative example, or something else), whether both CC1 and CC2 are simultaneously covered pre-power (the Type-C spec *requires* both; the FUSB302B datasheet's `VUFPDB` parameter doesn't explicitly say "both CC1 and CC2" though the feature is generically named "Dead Battery Support"), and any minimum/floor voltage for `VUFPDB` (only a max is given).

## Design equations

**I2C pull-up sizing** (Fast Mode Plus spec, p.18: `tr` max 120 ns, `Cb` max 550 pF - these are the datasheet's own bus-loading ceiling, not this board's actual capacitance):

- Standard I2C rise-time relation: `Rp_max ≈ tr / (0.8473 × Cb)`. Using the datasheet's own worst-case `Cb` = 550 pF and `tr` = 120 ns bounds gives Rp_max ≈ 120 ns / (0.8473 × 550 pF) ≈ 257 Ω — but this is the ceiling for a fully-loaded 550 pF bus; each tile's actual per-PHY bus is a single slave with `CI` = 5 pF (p.17) plus a few pF of MCU pin + trace capacitance (real `Cb` likely well under 20-30 pF), so the actual achievable Rp_max is far higher than 257 Ω.
- Rp_min is set by drive strength: at VDD = 3.3 V and the recommended `RPU` = 4.7 kΩ, pull-up current = 3.3 V / 4.7 kΩ ≈ 702 µA, which is far below the guaranteed `IOLSDA` sink capability of 20 mA min (p.17) - no risk of exceeding sink current.
- Ideal target: **4.7 kΩ** (Table 31, p.34) → nearest E24 value: **4.7 kΩ** (already an E24 standard value) → actual 4.7 kΩ → **0% error**.

**INT_N pull-up**: recommended range 1.0-4.7 kΩ (Table 31, p.34). Ideal target 4.7 kΩ (matching the I2C pull-ups for BOM commonality) → nearest E24: **4.7 kΩ** → actual 4.7 kΩ → **0% error**. At VDD = 3.3 V this draws ≈702 µA, comfortably inside the 4 mA test condition used for `VOLINTN` (p.17).

**CC receiver capacitor (CRECV)**: recommended window 200-600 pF, no typ given (Table 31, p.34). Midpoint ideal ≈ 400 pF → nearest E24 value: **390 pF** → actual 390 pF → error = (390-400)/400 = **-2.5%**, well inside the 200-600 pF window regardless. (A common alternative, 470 pF, is also E24-exact and stays inside the window with room to spare.)

**VDD decoupling**: CVDD1 = 0.1 µF and CVDD2 = 1.0 µF are given directly as fixed typical values (Table 31, p.34), not derived from a formula - both are standard capacitor values requiring no E-series rounding.

## Worked values for this application

- **VDD**: 3V3 rail (nominal 3.3 V) falls inside the 3.0-5.5 V range over which *every* electrical spec in the datasheet is guaranteed (not just the 2.7 V "functional-only" floor per Note 3, p.13). No derating concern.
- **VBUS pin**: the tile's PD+/HV rail is 9-20 V. Against the *recommended* VBUS max of 21.0 V (p.13), a 20 V PD contract leaves only **1.0 V (5%) margin** - tight but compliant. Against the absolute max of 28 V, margin is 8 V (40%). Because VBUS is a per-connector detect/measure pin (not a power pin), it must be wired to the **raw, un-switched connector VBUS** of the specific receptacle this PHY serves - not to the shared/switched HV distribution bus - and the datasheet explicitly expects external OVP ahead of this pin ("Expected to be an OVP protected input", Pin Descriptions, p.4).
- **I2C address**: FUSB302BMPX = **0x22** (7-bit, Table 4 p.19). Since this design puts each of the two PHYs on its own dedicated I2C bus, address collision is a non-issue regardless of which fixed-address variant is used.
- **Address-selectable variants for a future shared-bus revision**: `FUSB302B01MPX` = 0x23, `FUSB302B10MPX` = 0x24, `FUSB302B11MPX` = 0x25 (Table 4, p.19). **There is no address-select pin** - address is fixed by silicon/ordering part number only, so sharing one bus would require deliberately ordering two *different* part numbers, not strapping an ADDR pin.
- **Dead-battery clamp**: guarantees CC ≤ 2.18 V under "all Pull-up SRC loads" (p.15) with zero board power - sufficient for a compliant Type-C source to see a sink and apply default 5 V VBUS, satisfying the bootstrap requirement described in the project brief.

## Recommended implementation (pin by pin)

MLP-14 pinout per Pin Map (Fig. 5, p.3):

| Pin(s) | Name | Recommendation |
|---|---|---|
| 3, 4 | VDD | Tie together; 3V3 rail. Place CVDD1 = 0.1 µF as close as physically possible to pins 3/4, CVDD2 = 1.0 µF slightly further out (Table 31, p.34). |
| 8, 9 | GND | Tie directly to ground plane/pour with short via(s); datasheet's pin-map annotation under these pins reads "Connect to GND for Thermal" (Fig. 5, p.3), i.e. these pins also serve the part's thermal path. |
| 2 | VBUS | Connect to the **raw connector VBUS** of the receptacle this PHY monitors, through external OVP (per pin description, p.4: "VBUS input pin for attach and detach detection... Expected to be an OVP protected input"). Do **not** tie to the switched/distributed HV bus. No external divider is specified or needed - the internal MDAC/comparator measures VBUS directly (step size 420 mV/code up to a max code corresponding to 26.88 V, Table 8 p.22). |
| 10, 11 | CC1 | Tie together (internally the same net, doubled for current capacity); wire directly to the connector's CC1 pin, no series resistor. Add CRECV (200-600 pF, recommend 390-470 pF E24) from CC1 to GND. |
| 1, 14 | CC2 | Same treatment as CC1, wired to the connector's CC2 pin. |
| 12, 13 | VCONN | **Unused** in this sink-only design (project states VCONN is not supplied). Leave floating/no-connect; do not populate CBULK or CVCONN (Table 31). Firmware must keep `VCONN_CC1`/`VCONN_CC2` (Switches0 register bits 5:4) at their power-on-reset default of 0 (Table 6, p.21) since there is no VCONN source to switch onto CC. This floating recommendation is an inference - see Open Questions. |
| 6 | SCL | Route to this PHY's dedicated I2C bus. Requires an external pull-up (open-drain-compatible input per I2C spec; SCL is listed as "Input" only in Pin Descriptions, p.4, i.e. this device never drives SCL low itself, but the bus still needs a pull-up per I2C convention and per Table 31). Recommend 4.7 kΩ. |
| 7 | SDA | Open-drain I/O (Pin Descriptions, p.4). External pull-up required, recommend 4.7 kΩ (Table 31, p.34), pulled to a rail between 1.71 V and VDD (Note 6, p.17). |
| 5 | INT_N | Open-drain, active-low interrupt output (Pin Descriptions, p.4; `VOLINTN` max 0.4 V @ IOL=4 mA, p.17). External pull-up required, recommend 4.7 kΩ (Table 31, p.34, range 1.0-4.7 kΩ). Route to an RP2350B GPIO configured as an edge-triggered interrupt input. |

## Decoupling and passives

Per PHY instance (x2 per tile):

| Ref | Function | Value | Package | Note |
|---|---|---|---|---|
| CVDD1 | VDD decoupling, close-in | 0.1 µF | 0402 | Table 31, p.34. |
| CVDD2 | VDD decoupling, bulk-ish | 1.0 µF | 0402 caution | Table 31, p.34. **0402 X7R ceramics at 1.0 µF suffer significant DC-bias capacitance derating; verify effective capacitance at 3.3 V bias meets the 1.0 µF nominal intent, or step up to 0603 if the derated value falls short.** |
| CRECV x2 | CC1/CC2 receiver cap | ~390-470 pF | 0402 | Table 31, p.34, window 200-600 pF; place near the FUSB302B CC pins. |
| RPU (SDA) | I2C pull-up | 4.7 kΩ | 0402 | Table 31, p.34; per-bus (one bus per PHY in this design). |
| RPU (SCL) | I2C pull-up | 4.7 kΩ | 0402 | Table 31, p.34. |
| RPU_INT | INT_N pull-up | 4.7 kΩ | 0402 | Table 31, p.34, 1.0-4.7 kΩ window. |

Not populated (sink-only, VCONN unused): CBULK (10-220 µF), CVCONN (0.1 µF).

Not specified by this datasheet as required externally, but worth flagging given the CC/VBUS pins are connector-facing: TVS/ESD protection on CC1, CC2, and (post-OVP) VBUS. The project's parts library already includes `TPD2E2U06-esd.pdf`; sizing/placement is out of scope for this document but should clamp below the CC abs-max of 6.0 V without adding meaningful series resistance (a series R would bias the Rd/Rp measurement - see Gotchas).

## Layout notes

- CVDD1 (0.1 µF) placed at the VDD pins (3/4) with the shortest possible loop to GND pins 8/9; CVDD2 (1.0 µF) next-closest.
- GND pins 8/9 stitched into the ground pour with multiple vias - the pin-map explicitly ties a thermal note to these pins (Fig. 5, p.3), so they are doing double duty as the part's heat path in the absence of a distinct exposed pad callout in the extracted text.
- CRECV capacitors placed close to the FUSB302B CC pins (they filter/bandwidth-limit the BMC receiver at the chip, not at the connector).
- CC1/CC2 traces routed directly from connector to CCx pins with no series component in the signal path (none appears in the datasheet's own recommended passive list, Table 31).
- Fast Mode Plus (1 MHz) I2C bus capacitance ceiling is 550 pF (p.18) - not a practical constraint at board scale for a single-slave, one-PHY-per-bus topology, but keep SDA/SCL/INT_N traces short and low-capacitance as general practice.
- Each PHY's SDA/SCL/INT_N should route as a clean, non-shared trio directly to its own MCU I2C peripheral/GPIO, consistent with the two-independent-buses architecture.

## Gotchas and failure modes

1. **VBUS pin routing is the single easiest thing to get wrong**: it must see the *actual connector* VBUS (through OVP), not a switched or shared rail, or attach/detach detection (`I_VBUSOK`, `vVBUSthr` = 4.0 V typ, p.15) and the cold-start sequence both break.
2. **I2C pull-up voltage ambiguity**: Table 31 (p.34) recommends 1.62-1.98 V (typ 1.8 V), while Note 6 on the IO Specifications table (p.17) permits anything from 1.71 V up to VDD. A straightforward 3.3 V (VDD-referenced) pull-up satisfies Note 6's stated spec but falls outside Table 31's example range - the datasheet does not explain why its own reference design uses a sub-VDD rail (possibly just matching a particular reference platform's 1.8 V host rail, not a hard electrical necessity). Treat Table 31's voltage column as an example datapoint, not a binding limit.
3. **RDEVICE (the precise 4.6-5.6 kΩ Rd) is explicitly not guaranteed pre-power** (Footnote 5, p.15). Only the dead-battery clamp (`VUFPDB` ≤ 2.18 V max, no min) is guaranteed with VDD absent. A source may not reliably distinguish current-capability levels (Ra vs. Rd-1.5A vs. Rd-3A) during the earliest dead-battery instant - firmware should assume default USB power until VDD/3V3 are up and it can read accurate `BC_LVL`/measure-block status.
4. **No power-up/reset timing spec is given** (no `tPOR` from VDD-valid to registers-ready). "Power Up, Initialization and Reset" (p.10) only states that registers reset to defaults when VDD is first applied, and that software can additionally force a reset via `SW_RES` (Reset register, 0x0C, Table 16, p.26). Firmware should confirm readiness by reading a known register (e.g. Device ID, 0x01, Table 5 p.21) rather than assuming a fixed delay.
5. **CC absolute max (6.0 V) has only 0.5 V margin** over the worst-case VCONN voltage (5.5 V max, p.13) that could appear on an unmated/mismatched cable's CC-turned-VCONN pin. External clamping is advisable even though it's absent from the datasheet's own passive list.
6. **0402 1.0 µF ceramic (CVDD2) DC-bias derating** - verify actual delivered capacitance at 3.3 V bias; may warrant 0603 if the vendor's derating curve shows a large shortfall.
7. **VCONN pins left floating**: the datasheet's typical application (Fig. 2, p.2) always shows VCONN populated and sourced; there is no explicit "leave VCONN unconnected in a sink-only design" statement. The recommendation to float is inferred from the pin's function (a switch input, not a bias-critical input) and from `VCONN_CC1`/`VCONN_CC2` defaulting off at reset - but it is an inference, not a quoted datasheet instruction.
8. **No address-select pin** exists on this part. If a future revision wants to put both PHYs on one shared bus, that requires ordering two different fixed-address part numbers (e.g., FUSB302BMPX + FUSB302B01MPX), not a strap.

## Open questions / not determinable from the datasheet

- **Internal topology of the dead-battery Rd clamp** (resistor+FET per the Type-C spec's illustrative example, or a different structure) - the FUSB302B datasheet gives only the electrical result (`VUFPDB` ≤ 2.18 V max, no min, no topology description).
- **No minimum bound on `VUFPDB`** - only a max is specified (2.18 V), so there's no stated floor for the dead-battery CC voltage.
- **No power-up/reset timing** (`tPOR`) from VDD becoming valid to registers being reliably readable/writable - not specified anywhere in the document.
- **No explicit guidance for unused VCONN pins in a sink-only design** - float vs. ground is not addressed; float is the reasonable inference but not a quoted datasheet instruction.
- **Table 31's I2C pull-up voltage window (1.62-1.98 V) vs. Note 6's wider (1.71 V-VDD) allowance** are not reconciled in the datasheet.
- **No formal max sink-current rating for INT_N** beyond the `VOLINTN` test condition (IOL = 4 mA) - unlike SDA, which has an explicit `IOLSDA` ≥ 20 mA guarantee (p.17).
- **MLP-14 exposed thermal pad**: whether there is a distinct center exposed pad beyond pins 8/9 (which the pin map calls out for "Connect to GND for Thermal") could not be confirmed from the OCR'd/extracted mechanical drawing text (package drawing on p.34-35 is largely vector graphics); verify directly against the mechanical drawing if a specific pad geometry is needed for the footprint.
- **Whether the dead-battery clamp is guaranteed simultaneously on both CC1 and CC2 pre-power** - the Type-C spec requires both; the FUSB302B's `VUFPDB` parameter is stated generically ("SNK Pull-down Voltage in Dead Battery under all Pull-up SRC Loads") without explicitly confirming both pins are covered concurrently.
