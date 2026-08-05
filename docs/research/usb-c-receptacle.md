# USB Type-C receptacle (sink, 2 per tile) - spec research
> Independent spec read. Not written against the existing schematic.

**Sources used:**
- `Refrences/datasheets/USB-TypeC-spec.pdf` - USB Type-C Cable and Connector Specification, Release 2.0, August 2019 ("the spec"). All section/table/page numbers below refer to this document unless stated otherwise.
- `Refrences/datasheets/FUSB302BMPX-pd-phy.pdf` - Fairchild/ON FUSB302B, Rev. 1.4 ("FUSB302 datasheet"). Used only to sanity-check what a real PD PHY does with the spec's CC requirements, and because it happens to demonstrate the exact chicken-and-egg failure mode this project has already hit.
- `Refrences/datasheets/TPD2E2U06-esd.pdf` - TI TPD2E2U06 dual-channel ESD array, used for the D+/D- ESD discussion.
- `Refrences/datasheets/app-notes/TI-usb-type-c-pd-design-guide.pdf` and `Refrences/datasheets/app-notes/TI-esd-protection-usb.pdf` were opened but, despite their filenames, are **not** about Type-C connector design or USB ESD (the first is TI SLVA842 "USB PD Power Negotiations" for the TPS6598x family; the second is TI SLLA387A "Understanding Peak Source and Sink Current Parameters" for gate drivers). They contain nothing usable for this topic and are not cited below. Flagging this in case the files need re-fetching under correct names.

---

## What a sink must present passively at zero board voltage

This is the headline question, so the answer up front:

**The only things that must exist at the connector with zero board voltage are two resistors: Rd on CC1 and Rd on CC2, each 5.1 kΩ to GND.** Nothing else - not VBUS, not D+/D-, not SBU - needs to do anything for a source to apply VBUS.

Why this is the complete answer:

- The spec's sink functional model is explicit: "The Sink terminates both CC1 and CC2 to GND using pull-down resistors" (Section 4.5.1.3.2, p.156, point 1 of the Sink's functional characteristics).
- A source's entire attach-detection mechanism is watching its own CC pins for a voltage drop caused by an external Rd (Section 4.5.1.2.1, "Detecting a Valid Source-to-Sink Connection", p.152-153; Table 4-10 "Source Perspective", p.153). The source supplies its own Rp (or current source) and does the sensing - the sink does not need to sense or drive anything to be seen. It only needs to *be resistive*.
- Table 4-25 "Sink CC Termination (Rd) Requirements" (p.236) gives the resistor option a `Max voltage on pin` of 2.18 V (±20% variant) or 2.04 V (±10% variant) - i.e. the resistor never needs more than a few volts across it and never needs to source current. A plain resistor to a ground plane satisfies this with zero energy from the board.
- Section 4.8.5 "Charging a System with a Dead Battery" (p.228) makes the passivity requirement explicit for exactly this project's failure mode: *"A system that supports being charged by USB whose battery is dead shall apply Rd to both CC1 and CC2 and follow all Sink rules."* It further gives the one spec-sanctioned way to put an active element in series with Rd without breaking this: *"a 20% resistor of value Rd in series with a FET with V_GTH(max) < V_CLAMP(max) with the gate weakly pulled to CC would guarantee detection and be removable upon power up."* Note the shape of that circuit - the FET's gate is weakly pulled to a state that turns it **on** (i.e. Rd present) with no external bias. Power removes the Rd path if desired; power is never required to assert it. Any active gating of Rd that instead defaults **open** with no power is spec-noncompliant and is precisely the deadlock this project already hit.
- Everything else on the connector is either an input the sink only *senses* (VBUS - "the Sink determines that a Source is attached by the presence of power on VBUS", Section 4.5.1.3.2 point 2) or a pin with no required pre-attach state (D+/D-, SBU, TX/RX - see pin-by-pin section below). None of it gates whether a source is willing to turn VBUS on.
- The receptacle's VBUS-to-GND capacitance is bounded (≤10 µF, Table 4-3, discussed under Hotplug/inrush below) but this is a *ceiling* on what may passively exist, not something that needs to be built - an unpopulated board already satisfies it.

**Practical implication for this project:** every downstream component that depends on the two Rd resistors being "alive" - the PD PHY's own CC pins, any protection diodes, any mux - must never be able to pull CC away from that resistor state before board power exists. The two resistors (or a PD PHY with a genuine, datasheet-documented dead-battery Rd path - see Gotchas) are the entire cold-start requirement. If the design instead routes CC through, e.g., an analog switch that itself needs 3V3 to pass a signal, Rd effectively disappears until 3V3 exists, and 3V3 cannot exist until a source is convinced to apply VBUS - the exact deadlock already experienced.

---

## Pin-by-pin treatment (every contact on the receptacle)

The 24-pin USB Type-C receptacle pinout is defined in Table 3-4 "USB Type-C Receptacle Interface Pin Assignments" (p.68-69). Table 3-5 (p.69-70) gives the USB 2.0-only subset, which is what applies here since this design carries no SuperSpeed/USB4/Alt Mode.

| Pin(s) | Signal | Count | Treatment for this design |
|---|---|---|---|
| A1, A12, B1, B12 | GND | 4 | All bussed together to the common ground plane. Required: "All Ground return pins shall be connected together... at the USB Type-C receptacle connector when the receptacle is in its mounted condition (e.g., all ground return pins bussed together on the PCB)" (Table 3-4, Note 3, p.69). |
| A4, A9, B4, B9 | VBUS | 4 | All bussed together to the sink's VBUS input node. Required identically: "All VBUS pins shall be connected together... at the USB Type-C receptacle connector" (Table 3-4, Note 2, p.69). See VBUS/GND current section - this is not optional at 5A. |
| A5 | CC1 | 1 | Rd = 5.1 kΩ to GND, always present (see above), plus PD PHY CC1 input. |
| B5 | CC2 | 1 | Rd = 5.1 kΩ to GND, always present, plus PD PHY CC2 input. Note B5 doubles as the VCONN contact position when the cable orientation puts VCONN there - see VCONN section. |
| A6, B6 | Dp1, Dp2 (D+) | 2 | Orientation-independent handling required - see D+/D- section below. |
| A7, B7 | Dn1, Dn2 (D-) | 2 | Same. |
| A8, B8 | SBU1, SBU2 | 2 | No alt mode in this design: leave open circuit, or add a weak pull-down no stronger than z_SBUTermination (see SBU section). |
| A2, A3, A10, A11, B2, B3, B10, B11 | TX1/RX1/TX2/RX2 (SuperSpeed pairs) | 8 | Not connected. Table 3-5 governs a USB 2.0-only receptacle explicitly: *"Unused contact locations shall be electrically isolated from power, ground or signaling (i.e., not connected)"* (Table 3-5, Note 1, p.70). Do not ground them - see TX/RX section for why. |
| Shell / mid-plate | Shield | - | Bond to PCB ground at multiple points, keep apertures small - see Shield section. |

Two structural notes worth carrying into layout:

1. Even in a USB 2.0-only design, **all 24 mating contacts must physically exist in the receptacle** - "All contacts are required to be present in the mating interface of the USB Type-C receptacle connector" (p.56, discussing Table 3-5's simplification, which only relaxes the *plug* side). Table 3-5 only tells you which receptacle pads may be left unconnected on the PCB; it does not let you buy a receptacle missing pins. This has no cost impact (all commodity 24-pin receptacles include the SS pins) but it means the footprint must route out (or deliberately not route) all 24 lands.
2. Contacts B6 and B7 (Dp2, Dn2 in the full pin table's A/B numbering) are the ones the plug typically omits in a USB-2.0 cable, and Table 3-4 Note 1 (p.69) is the source of the D+/D- shorting technique discussed below.

---

## CC electrical requirements

### Rd value and tolerance

Table 4-25 "Sink CC Termination (Rd) Requirements" (Section 4.11.1, p.236):

| Rd implementation | Nominal value | Can detect source power capability? | Max voltage on pin |
|---|---|---|---|
| Voltage clamp | 1.1 V | No | 1.32 V |
| Resistor to GND, ±20% | 5.1 kΩ | No | 2.18 V |
| Resistor to GND, ±10% | 5.1 kΩ | Yes | 2.04 V |

For a design that wants to read the source's 1.5 A / 3.0 A current advertisement (this one does, given a PD PHY per receptacle and a 20 V/5 A rail to negotiate), **the ±10%-tolerance resistor variant is the one that qualifies** - the ±20% part is legal for basic attach detection but the spec does not guarantee current-advertisement detection with it. A 5.1 kΩ 1% (E96) resistor comfortably clears the ±10% requirement.

This must be present identically on **both** CC1 and CC2, independently - Section 4.5.1.3.2 (p.156) point 1, quoted above. A plug only needs Rd on the one CC wire that happens to be routed through the cable to its host, because a plug's orientation is fixed at manufacture; a receptacle must work in either orientation, so it needs Rd on both physical CC pins, and the source figures out at connect time which one is "the" CC by which one it sees pulled down.

### How the source detects attach and orientation

Both CC pins on the sink are Rd-terminated at all times; only one of them ends up electrically continuous to the source across the cable (the other cable-side contact carries VCONN instead - Section 4.4.3, p.144: *"VCONN is provided over the CC pin that is determined not to be connected to the CC wire of the cable"*). The source watches both its own CC pins for a voltage below its unterminated (Rp) level (Section 4.5.1.2.1, p.152). Whichever CC pin sags is the one connected through, and that identifies both "something with Rd is attached" and the plug orientation (Table 4-10 "Source Perspective", p.153; and p.154: *"the inserted plug orientation is detected at the Source's receptacle by noting on which of the two CC pins in the receptacle an Rd termination is sensed"*). tCCDebounce (100-200 ms, Table 4-31, p.239) is the source's minimum settle time before it acts on this.

### The three current advertisements and what the sink sees

Source side (what the source puts on its CC pin, Table 4-24, p.235 - context for what a source we plug into might do):

| Advertisement | Current source | R pull-up to 4.75-5.5 V | R pull-up to 3.3 V ±5% |
|---|---|---|---|
| Default USB Power | 80 µA ±20% | 56 kΩ ±20% (±5% for captive/legacy-adapter Rp, Note 1) | 36 kΩ ±20% |
| 1.5 A @ 5 V | 180 µA ±8% | 22 kΩ ±5% | 12 kΩ ±5% |
| 3.0 A @ 5 V | 330 µA ±8% | 10 kΩ ±5% | 4.7 kΩ ±5% |

Sink side - what our design's PD PHY must actually measure across its own Rd. This project needs **Table 4-36** (multi-advertisement sink), not Table 4-35 (default-only sink), since a 20 V/5 A rail is meaningless without reading the higher advertisements:

Table 4-36 "Voltage on Sink CC pins (Multiple Source Current Advertisements)" (p.241):

| Detection | Min voltage | Max voltage | Threshold |
|---|---|---|---|
| vRa | -0.25 V | 0.15 V | 0.2 V |
| vRd-Connect | 0.25 V | 2.04 V | - |
| vRd-USB (default) | 0.25 V | 0.61 V | 0.66 V |
| vRd-1.5 | 0.70 V | 1.16 V | 1.23 V |
| vRd-3.0 | 1.31 V | 2.04 V | - |

(Table 4-35, the default-only-sink table, is simpler - vRd-Connect spans 0.25-2.18 V with no sub-bands - and applies only if the sink chooses not to implement current-advertisement detection at all.)

### When PD messaging supersedes this

Once a USB PD contract exists, CC voltage-based current advertisement is no longer authoritative: *"While a USB PD contract is in place, a Sink is not required to monitor USB Type-C current advertisements and shall not respond to USB Type-C current advertisements"* (Section 4.6.2, p.219). Practically: the sink's PD PHY should use vRp/Rd sensing to get *some* current budget immediately at attach (this is what lets a tile draw more than default current even before any PD messages have been exchanged), but as soon as a PD Explicit Contract is established, the negotiated PDO/RDO governs, not CC voltage. tSinkAdj (≤60 ms, Table 4-29, p.238) bounds how fast the sink must react to a *change* in Type-C current advertisement while no PD contract is active.

### Debug Accessory Mode / Audio Adapter Accessory Mode - and why a receptacle sink can't be confused for one

Table 4-10 (p.153) defines the two accessory signatures as seen by a source:
- **Rd on both CC1 and CC2 simultaneously** → Debug Accessory Mode (Appendix B).
- **Ra on both CC1 and CC2 simultaneously** → Audio Adapter Accessory Mode (Appendix A).

Audio Adapter Accessory Mode is not a real risk here: Appendix A (p.309) defines it as *"resistance to GND of ≤ Ra on both A5 (CC) and B5 (VCONN)"* at the *plug* - it requires shorting CC to what is normally the VCONN contact, along with re-purposing D+/D-/SBU as analog audio signals. Nothing in a standard sink wiring does this.

Debug Accessory Mode is the one worth being precise about, because at first glance "Rd on both CC pins" is *exactly* what a sink receptacle always presents. The resolution is in how a standard passive cable is built: only **one** of the two CC contact positions at each end is electrically continuous through the cable; the other position carries VCONN instead (Section 4.4.3, p.144, quoted above). So across a normal detachable USB-C cable, a source's two CC pins can never both simultaneously see an external Rd from the same device - one of them will only ever see (at most) VCONN or nothing. Debug Accessory Mode's Rd/Rd signature is only produced by a **captive-cable, direct-plug DTS (Debug and Test System) device** that exposes both CC1 and CC2 undivided (Appendix B.2.1, p.314: *"Both CC1 and CC2 are used for current advertisement and optional orientation detection"* on the DTS plug). As long as this design is a normal receptacle mated through a normal passive/e-marked Type-C cable - not a captive-cable debug probe - the cable construction itself prevents the ambiguity. Nothing extra needs to be added to the sink circuit to avoid it. (This would stop being true only if a captive cable or a direct-plug adapter that shorts both CC contacts together were used - don't do that.)

---

## VBUS / GND current handling

- **4 VBUS contacts, 4 GND contacts** per receptacle (A4/A9/B4/B9 and A1/A12/B1/B12 - Table 3-4, p.68).
- **Contact current rating test** (Section 3.7.8.4, p.123-124): *"A current of 5 A shall be applied collectively to VBUS pins (i.e., pins A4, A9, B4, and B9)... terminated through the corresponding GND pins (i.e., pins A1, A12, B1, and B12)"*, with temperature rise capped at 30 °C above ambient measured at the shell over the VBUS/GND contacts. This is a *collective* 5 A across all four VBUS pins together - not 5 A per pin - and it is a manufacturer qualification test on the bare connector, not a statement that current divides evenly across the four pins in an application.
- **Contact resistance**: LLCR ≤ 40 mΩ initial, ≤ 50 mΩ after environmental stress, for VBUS, GND and all other contacts (Section 3.7.8.1, p.122).
- **All four VBUS pins must be bussed together on the PCB; all four GND pins must be bussed together on the PCB** - this is explicitly normative, not just good practice: Table 3-4 Notes 2 and 3 (p.69), *"shall be connected together at the USB Type-C receptacle connector when the receptacle is in its mounted condition (e.g., all VBUS pins bussed together on the PCB)"*.

**Implication at 5 A:** since the spec only qualifies the connector collectively and does not guarantee equal current sharing between the four parallel contacts (four independent low-resistance paths in parallel will split current in inverse proportion to their individual, uncontrolled contact + trace resistance), the PCB-side bussing must not rely on any single pin/via carrying a full-share fraction reliably. Practical consequence for layout: tie all four VBUS lands with a wide copper pour (not four thin traces converging on one point) with enough via count that no single via is anywhere near its own current limit even if it ends up carrying a disproportionate share, and do the same for the four GND lands. This is a layout requirement, not a spec-quoted number - the spec is silent on how to apportion PCB copper.

---

## Design equations

**Rd resistor selection** (5.1 kΩ ±10% target, Table 4-25):
- Ideal: 5.1 kΩ.
- Nearest E24 value: 5.1 kΩ (5.1 is itself a standard E24/E96 value - no rounding needed).
- Actual (1% E96 part, LCSC-stocked): 5.10 kΩ ±1%.
- Resulting error vs. ±10% spec requirement: 0% nominal offset; worst-case ±1% << spec's ±10% budget, so no compliance risk from component tolerance. (A ±20% 5.1 kΩ part would also pass the *basic* Rd requirement but would forfeit power-capability detection per Table 4-25 - not recommended given this design needs to read 1.5 A/3.0 A advertisements.)

**Power dissipated in each Rd resistor** at the worst-case CC voltage (2.04 V max per the ±10% row of Table 4-25):
P = V² / R = (2.04)² / 5100 = 8.16 × 10⁻⁴ W ≈ 0.82 mW.
An 0402 resistor is typically rated 1/16 W (62.5 mW); 0.82 mW is ~1.3% of rating - 0402 is correct here, no de-rating concern.

**Voltage rating check for anything tied to CC1/CC2:** the spec's own ceiling on what a CC pin may ever see in normal operation is 5.5 V - both from vVCONN Valid max (Table 4-5, p.144: 3.0-5.5 V) and from the Rp pull-up voltage ceiling ("Other pull-up voltages shall be allowed if they remain less than 5.5 V", Table 4-24 preamble, p.235). Any component with a pin tied directly to CC1 or CC2 - Rd resistor, PD PHY, ESD diode - therefore needs a working/breakdown/abs-max voltage rating comfortably above 5.5 V. A standard-package 0402 resistor (typically ≥25-50 V working voltage from any major manufacturer) clears this trivially; it's the PD PHY and ESD diode that need the rating checked deliberately (see Decoupling/ESD section).

---

## Worked values for this application

- **Rd**: 5.1 kΩ ±1% (E96), 0402, direct to the local GND plane, on *both* CC1 and CC2 of *each* of the 2 receptacles - 4 discrete resistors total per tile if Rd is implemented discretely. Present with zero board voltage; do not gate.
- **Alternative - PD PHY internal Rd**: the FUSB302 (`Refrences/datasheets/FUSB302BMPX-pd-phy.pdf`) is a concrete, useful example of the tradeoff here, because its datasheet documents exactly the failure mode this project already hit and how one real part avoids it:
  - Its `Switches0` register (address 0x02) controls the internal Rd pull-downs via bits PDWN1/PDWN2, and its **power-on-reset default value is 0x03** (both PDWN1=1 and PDWN2=1) - meaning Rd is asserted on both CC pins by hardware default, before the MCU has written a single I²C byte (FUSB302 datasheet, Register Definitions table, and Table 6 "Switches0").
  - It further advertises a distinct feature, "Dead Battery Support (SNK Mode Support when No Power Applied)" (FUSB302 datasheet, Features list), backed by an electrical parameter `V_UFPDB` = "SNK Pull-down Voltage in Dead Battery under all Pull-up SRC Loads", max 2.18 V, and `R_DEVICE` = "Device Pull-down Resistance", 4.6/5.1/5.6 kΩ (min/typ/max) - numbers that map directly onto the Type-C spec's Table 4-25 resistor rows (2.18 V matches the ±20% row's max-voltage-on-pin exactly; the ~±10% resistance band matches the power-capability-detecting row). This says the FUSB302B's dead-battery Rd path is designed to work with **no VDD at all**, not merely "before firmware configures it."
  - **But** this only holds if (a) the exact part used genuinely documents a no-VDD dead-battery path (verify per datasheet - do not assume every PD PHY has this; many do not), and (b) CC1/CC2 are wired straight from the receptacle to that chip's CC pins with nothing else - no series switch, no mux stage - between them. If anything sits between the receptacle and the PHY that itself needs power to pass a signal through, the dead-battery guarantee is void regardless of what the PHY chip can do on its own.
  - Given this project has already been burned by exactly this dependency, **discrete Rd resistors wired straight to the receptacle, independent of any chip, are the lower-risk choice** and cost essentially nothing (4× 0402 5.1 kΩ resistors). If the PD PHY's internal Rd is used instead to save parts, its no-VDD behavior needs to be bench-verified with the PHY's VDD pin *disconnected*, not just assumed from a feature bullet.
- **CC PD PHY input protection**: since CC1/CC2 can see up to 5.5 V (worked above) plus ESD transients, and the FUSB302's own CC-pin absolute maximum is -0.5 V to 6.0 V (FUSB302 datasheet, Absolute Maximum Ratings) - any board-level ESD device placed on CC needs a working voltage rated above 5.5 V and a clamp voltage that stays under the PHY's 6.0 V abs-max at the PHY's expected fault current. This is a part-selection constraint to carry into ESD diode selection (see next section); the Type-C spec does not specify an ESD diode part, only the environment it must survive.
- **VBUS/GND bussing**: 4 VBUS lands tied in parallel to one net, 4 GND lands tied in parallel to the ground plane, per Table 3-4 Notes 2/3 - not optional, and worth generous copper/via count given the 20 V/5 A negotiated ceiling (see VBUS/GND section above).

---

## Decoupling, ESD and protection

**ESD - the Type-C spec itself is silent.** A full-text search of `USB-TypeC-spec.pdf` for "ESD" / "electrostatic" returns zero matches - connector-level ESD immunity (e.g. IEC 61000-4-2) is out of scope for the USB-IF Type-C connector spec and is left to system-level design and other standards. This is worth stating explicitly rather than inventing a number: **ESD requirement at the connector: not specified by USB-TypeC-spec.pdf.** The practical requirement comes from general electronics design practice and from whatever regulatory/compliance target the project sets for itself (not derived here).

For a concrete part, `Refrences/datasheets/TPD2E2U06-esd.pdf` (TI TPD2E2U06, already in this project's datasheet folder) is a reasonable fit for the D+/D- pair specifically: dual-channel TVS array, 1.5 pF (typ) / 1.9 pF (max) line capacitance (low enough not to matter for USB 2.0 Full-Speed signaling), DC breakdown voltage ≥6.5 V min, clamp voltage ~9.7 V at 1 A TLP (IO-to-GND), rated to IEC 61000-4-2 Level 4 (±25 kV contact / ±30 kV air-gap). Its two channels map naturally onto one D+/D- pair. CC1/CC2 need a *separate* ESD device selection pass (not this same part) sized against the 5.5 V CC ceiling worked out above, and VBUS needs a device rated for the full 20 V negotiated rail, not the USB default 5 V - neither of these is covered by TPD2E2U06's typical low-voltage USB-2.0-signal use case. Exact part selection for CC/VBUS TVS diodes is a BOM decision, not something the Type-C spec dictates a number for.

**Bulk decoupling near the connector**: keep it small and see the Hotplug/inrush section below - anything beyond a few nF-to-low-µF of local decoupling at the connector itself should sit behind whatever gates VBUS onward into the tile (load switch / eFuse / buck input), not permanently wired to the VBUS pins.

---

## Footprint / mechanical notes

The spec has real, cited mechanical requirements worth designing to even though they're not electrical:

- **Durability**: 10,000 mating cycles minimum for the connector family, tested at 500±50 cycles/hour with no physical damage (Section 3.8.1.3, p.126). For a device meant to be plugged/unplugged constantly, this is the connector's entire mechanical life budget - it's a reason to buy from a reputable connector line with independently verified cycle testing rather than the cheapest LCSC basic-part receptacle, since 10k cycles is a spec *floor*, not a guarantee every listed part meets it under real (non-test-fixture) conditions.
- **Insertion force**: 5-20 N at up to 12.5 mm/min (Section 3.8.1.1, p.126). **Extraction force**: 8-20 N, measured after 5 preconditioning cycles and again after 30 total cycles (Section 3.8.1.2, p.126). A receptacle with SMT-only leads (no through-hole shell anchor) relies entirely on the solder joints of small SMT tabs to react these repeated forces over 10k cycles - this is exactly the failure mode "through-hole-anchored SMD" receptacles solve.
- **What to look for**: receptacles marketed as "mid-mount" or with **through-hole side/bottom mounting legs** in addition to SMT signal pins. The through-hole legs (usually 2-4 per connector, sometimes combined with the shell itself) take the mechanical insertion/extraction/lateral load; the SMT pins only carry signal/power current and don't have to survive the cyclic mechanical stress. This is standard practice for any connector expected to survive repeated hand-plugging rather than being mated once in a factory and left alone (e.g. inside a sealed product).
- **Reflow compatibility**: since this project reflows on a hotplate with low-temperature Sn42/Bi57/Ag1 paste (~139 °C eutectic, reflow peak likely in the 150-170 °C range), check the connector's rated reflow profile - USB-C receptacles are usually qualified for standard SAC305 profiles (245-260 °C peak). A low-temp Bi-Sn paste reflowing at a much lower peak is very unlikely to thermally stress the connector, so this cuts the *other* direction from the usual concern (no risk of exceeding the connector's rating) - but it's worth confirming wetting/solderability of the connector's terminal finish (usually gold-flash or tin) is adequate at a lower peak temperature and longer/gentler ramp than a hotplate profile typically gives, since this is more a paste/joint-quality risk than a connector-rating risk.
- **Board thickness / mid-plate**: the spec's reference designs assume a mid-plate directly bonded to PCB ground with at least two ground points (Section 3.2.2.1, p.61) and receptacle shell solder tails with multiple connection points and small apertures (≤1.5 mm recommended, Section 3.10.1, p.135-136) - both are about EMC/shielding, covered further below, but they also double as *mechanical* anchor points and should be treated as structural, not just as ground connections, when laying out keepout/stress relief around the connector.
- **Keepout for repeated stress**: given the tile is "constantly plugged and unplugged" per the project brief, keep the receptacle mounted flush to the board edge with the shell tabs landing on generous copper (not just vias to plane) and avoid placing any other component or via directly under the connector body where lateral flex from plug insertion could crack a joint.

---

## Layout notes

- **VBUS/GND**: all 4 VBUS lands to one wide pour/net, all 4 GND lands to the ground plane, per Table 3-4 Notes 2/3 (not optional). Use multiple vias per pad group rather than a single choke point, given the current isn't guaranteed to split evenly across the 4 physical contacts (see VBUS/GND section).
- **CC1/CC2**: route directly from receptacle pin to Rd resistor pad to PD PHY pin with the shortest practical stub - no switches, muxes, or anything requiring board power in series, per the cold-start requirement above. Keep away from VBUS/high-di/dt switching nodes; the spec itself cares about VBUS-to-CC coupling at the cable level (Section 3.7.2.5.2, p.106: max mutual inductance between VBUS and CC of 350 nH is a *cable* wire-to-wire spec, not a board layout spec, but the same physical concern - keep CC away from power switching - applies on the PCB by extension).
- **D+/D-**: keep the shorted Dp1/Dp2 and Dn1/Dn2 stub length ≤3.5 mm per Table 3-4 Note 1 (p.69) if using the passive-shorting approach (see D+/D- section below) - this is an explicit spec number, not a guideline.
- **SBU**: if left open, no layout concern; if adding the optional pull-down, keep it away from CC/D+/D- given the spec's own SBU-to-CC and SBU-to-D+/D- crosstalk limits exist at the cable level (Sections 3.7.2.5.3-3.7.2.5.5, p.106-107) - again a cable spec, but motivates the same "don't route SBU parallel and close to CC or D+/D-" board practice.
- **Shield/mid-plate**: multiple direct ground-plane tie points, small apertures (≤1.5 mm), per Section 3.10.1 (p.135-136) - see Shield section for the tradeoff on whether this is a direct tie or an RC-bled tie for this project.

---

## Gotchas and failure modes

- **The one this project already hit**: any active component (switch, mux, load-controlled FET with the wrong default polarity) placed between the receptacle's CC pins and their Rd terminations, if it needs board power to pass a signal or to default into the "Rd present" state, creates a state from which no source will ever apply VBUS - because the source's entire attach algorithm is "watch for Rd" and there is no other way in the spec for a sink to signal presence pre-VBUS. Section 4.8.5's dead-battery guidance (p.228) shows the one correct way to add an active element in series with Rd (gate weakly pulled to default the FET **on**); anything that defaults the other way is the deadlock.
- **Confusing Table 4-25's two "resistor to GND" rows**: the ±20% and ±10% rows have the *same nominal value* (5.1 kΩ) and differ only in tolerance and in whether power-capability detection is guaranteed. It's easy to read "5.1 kΩ ±20%" as the spec value and stop there; for a design that needs to read 1.5 A/3.0 A advertisements (this one does), the ±10% row is the one that actually applies.
- **Grounding the unused SuperSpeed pins "to be safe"**: Table 3-5 Note 1 (p.70) says unused contacts "shall be electrically isolated... (i.e., not connected)" - not grounded. Tying TX/RX pins to ground when the spec says not-connected is a spec deviation, and depending on the receptacle's internal shield/pin proximity could create an unintended coupling path; there's no requirement or benefit to grounding them.
- **Bulk capacitance left permanently on VBUS**: Table 4-3's 10 µF pre-attach ceiling (see Hotplug/inrush) applies to the receptacle's VBUS-to-GND capacitance "when not in Attached.SNK" - if the tile's downstream buck regulator input caps (which could easily be tens of µF) are wired directly and permanently to the connector's VBUS net with no switch/eFuse in between, the design violates this ceiling continuously, not just at the moment of attach, and risks a source's inrush protection rejecting the attach or the source folding back voltage.
- **Assuming a PD PHY's advertised "dead battery support" means zero-VDD operation without checking**: as shown above with the FUSB302, some real PD PHYs do have a genuine no-VDD dead-battery Rd path documented with real numbers - but "Dead Battery Support" as a marketing bullet should be verified against the actual electrical table (V_UFPDB, R_DEVICE or equivalent) before relying on it, and re-verified that nothing else in the signal path (a mux, a level shifter) also needs power.
- **Two receptacles, two independent PD PHYs, one shared VBUS/GND**: since either receptacle can become master and the rail is shared between tiles, both receptacles' Rd/PD-PHY circuits need to be fully independent per the "sink-only, independently capable of negotiating a full PD contract" requirement - a single shared Rd or shared PHY between the two ports would violate "independently capable" and also break orientation/attach detection on whichever port isn't the active one.

---

## Open questions / not determinable from the spec

- **ESD immunity level/target** (kV, IEC 61000-4-2 level, which pins) - not specified anywhere in `USB-TypeC-spec.pdf` (confirmed via full-text search - zero hits for "ESD"). This is a system-level design decision for this project to set, not something derivable from the connector spec.
- **Exact TVS/ESD diode part numbers for CC and VBUS** - the spec defines the electrical environment (CC ≤5.5 V nominal, VBUS up to 20 V negotiated) but does not recommend components; TPD2E2U06 was evaluated for D+/D- only, and CC/VBUS need their own part selection against the voltage ceilings derived above.
- **Whether to use discrete Rd resistors or a PD PHY's internal dead-battery Rd** - this is a project risk decision informed by the FUSB302 case study above, not a spec requirement (the spec is indifferent to implementation as long as the electrical behavior in Table 4-25 is met).
- **Shield bleed resistor/capacitor values** (if a resistor+capacitor bleed to chassis is chosen over a direct tie) - the spec describes *that* the shell should be well-bonded to PCB ground (Section 3.10.1) but gives no RC bleed values; this is a general EMC-practice technique (used when there's a separate floating chassis/enclosure ground that needs a high-impedance-at-DC, low-impedance-at-RF path to board ground) not sourced from this spec, and its applicability depends on whether this tile's enclosure design has a true separate chassis ground plane at all - which is outside this document's scope (mechanical/enclosure design, not connector spec).
- **VBUS/GND per-pin current de-rating margin for continuous 5 A operation** - the spec's contact current test (Section 3.7.8.4) is a connector-qualification test at 5 A collective/30 °C rise, not a continuous-duty safety margin recommendation for board design; how much margin to design in above the connector's bare rating (e.g., derating for ambient temperature, duty cycle, or connector aging over 10k cycles) is not specified and would need to come from the specific receptacle manufacturer's datasheet, which is out of scope for this document (blind spec read, no specific receptacle chosen).
- **Whether to use the passive Dp1/Dp2-Dn1/Dn2 shorting technique or an active USB 2.0 mux for orientation switching** - both are spec-legal (Table 3-4 Note 1 permits the passive short with a ≤3.5 mm stub; nothing prohibits an active mux instead), and the choice has direct cold-start implications (a mux needs power; a passive short does not) that this document flags under D+/D- below but does not resolve, since it depends on whether the project's downstream USB PHY (RP2350B) can tolerate the D+/D- stub length/capacitance of a passive short versus wanting a clean single-ended mux output - a decision for the schematic, not the connector spec.

---

## SBU1/SBU2 - detail

Section 4.3 (p.140): *"The SBU pins on a port shall either be open circuit or have a weak pull-down to ground no stronger than z_SBUTermination."* Table 4-28 (p.237) gives z_SBUTermination ≥ 950 kΩ, noted as "functional equivalent to an open circuit." For a design with no alt-mode support (this one, USB 2.0 full-speed only, no video/alt-mode use of SBU), the correct treatment is: **leave A8/B8 unconnected**, or if a defined pull-down is wanted for ESD/noise reasons, use ≥950 kΩ to GND - never a low-impedance pull-down or pull-up, and never tie them to a signal.

## The unused SuperSpeed pairs (TX/RX) - detail

**Spec-correct answer**: not connected, isolated from power/ground/signal (Table 3-5 Note 1, p.70). **Practical answer**: same as the spec-correct answer here - there's no competing "safer" practical alternative worth deviating for. Grounding them buys nothing (they're already isolated inside the connector's shield structure) and isn't what the spec describes for a USB 2.0-only receptacle wiring. Leave A2, A3, A10, A11, B2, B3, B10, B11 unrouted/not-connected.

## D+/D- - detail

The receptacle has two D+ contacts (A6, B6) and two D- contacts (A7, B7) because the cable can be inserted in either orientation, and only one of the two pairs is the one actually wired through in any given plug orientation. Table 3-4 Note 1 (p.69) gives the spec-sanctioned simplification for a device (not a full USB 3.2 host) that only needs to expose one USB 2.0 PHY: *"Dp1 and Dp2 may be shorted on the host/device as close to the receptacle as possible to minimize stub length; Dn1 and Dn2 may also be shorted. The maximum shorting trace length should not exceed 3.5 mm."* This is why an orientation-independent USB-2.0-only device does not need an active D+/D- mux at all - shorting Dp1-Dp2 and Dn1-Dn2 right at the receptacle, feeding a single USB 2.0 PHY, is spec-legal and requires zero active/powered components, which also keeps it out of the cold-start dependency chain. An active mux (as in the project's own TS3USB30E datasheet on file, suggesting this may have been considered) is also legal but adds a component that needs power and adds signal path length/capacitance - worth weighing against the free passive-short option given this design has already suffered from unnecessary power-dependent gating.

## VCONN - detail

This design is a sink that never sources VCONN (no accessory support implied by the brief - two independent PD PHYs each doing sink-only negotiation). A sink that never sources VCONN simply has no VCONN switch/boost circuitry - there's no "shall not" action required, sourcing VCONN is fundamentally a Source-role behavior (Section 4.4.3, p.144) and a pure sink doesn't do it unless it explicitly implements the optional VCONN_Swap PD message to take over the role.

What matters instead is what the **other end** may put on the CC pin not used for communication. A powered cable or a source may apply VCONN to that pin, bounded by Table 4-5 "VCONN Source Characteristics" (p.144): vVCONN Valid range 3.0-5.5 V. Combined with the Rp pull-up ceiling of <5.5 V (Table 4-24 preamble), **5.5 V is the maximum voltage either CC pin can see under normal (non-fault) spec-compliant operation** - this is the number that sets the absolute-maximum requirement on anything wired to CC1/CC2 (Rd resistor voltage rating, PD PHY CC-pin abs-max, any ESD device's breakdown voltage), as used in the Design equations and Worked values sections above.

## Shield and chassis ground - detail

The spec's own guidance (informative, Section 3.10.1, p.135-136, and Section 3.2.2.1, p.61) is about bonding the receptacle shell/mid-plate to the **PCB ground plane** directly, with multiple solder-tail connection points and apertures kept small (≤1.5 mm recommended) for EMC. It does not itself prescribe an RC bleed network - that's a separate, common practice used specifically when a product has a **physically separate chassis/enclosure ground** (e.g. a metal case or panel) that must be kept galvanically isolated from board GND at DC (to avoid ground loops, ESD/lightning coupling paths, or safety isolation requirements) while still being bonded to it at RF for shielding effectiveness. The bleed network is then typically a resistor (or resistor+capacitor in parallel, e.g. ~1 MΩ with a small-value, high-voltage-rated ceramic cap) between chassis and board ground, sized case-by-case (not a Type-C-spec number). For this project - modular tiles with no metal chassis described in the brief, snap-together plastic/PCB-edge construction - there is likely no separate chassis ground plane to bleed *to* at all, in which case the spec's default recommendation (direct shell-to-PCB-GND bond at the receptacle, multiple points, small apertures) is the right call rather than adding an RC bleed for a chassis ground that may not exist. If a later enclosure revision does add a metal panel/frame, that's when the bleed-resistor question becomes live - it is not resolvable from the connector spec itself either way.

## ESD and dead-battery/no-power behaviour - detail

**ESD**: not specified in the Type-C connector spec (see Decoupling/ESD/Protection section above - zero hits searching the spec text). Handle via board-level TVS/ESD diode selection against whatever compliance target the project sets, sized against the CC (5.5 V) and VBUS (20 V) voltage ceilings derived elsewhere in this document.

**Dead-battery/no-power behaviour**: Section 4.8.5 (p.228, quoted in full above) - the sink must present Rd on both CC pins and behave as a sink even with a fully dead battery/no local power, receiving default VBUS as a result. This is the same requirement as the cold-start requirement at the top of this document; Section 4.8.5 is simply the spec's name for it in the context of a battery-powered device. This project's tile has no battery at all, so it is *always* in the "dead battery" case from the spec's point of view until BS+ or a negotiated rail exists - meaning the dead-battery Rd requirement isn't an edge case for this design, it's the design's *normal* startup state on every single hotplug event.

## Hotplug / inrush - detail

The spec's bulk-capacitance ceiling for a sink is in **Table 4-3 "VBUS Sink Characteristics"** (p.142), last row: *"VBUS Capacitance... 10 µF max... Capacitance between VBUS and GND pins on receptacle when not in Attached.SNK."* This is the sink-side inrush/hotplug limit: whatever capacitance sits directly across VBUS/GND at the receptacle, before the sink has reached the Attached.SNK state, must not exceed 10 µF. (The source side has its own, separate ceiling in Table 4-2, p.141: 3000 µF for source-only ports, 10 µF for DRP ports - not directly binding on this sink design, but shows the same order-of-magnitude philosophy on both sides of the connection.)

Given the negotiated rail on this project can reach 20 V, a naive design with the tile's full downstream bulk capacitance (buck regulator input caps, bootstrap supply caps, etc.) wired straight to the connector's VBUS net would both violate this 10 µF ceiling and create a real inrush event when a source that has just negotiated 20 V switches its output on into a large discharged capacitance. The clean answer implied by the ceiling: keep only small, local decoupling (well under 10 µF) directly on the VBUS/GND nets at the connector, and put the bulk capacitance behind a controlled turn-on element (load switch, eFuse, or the buck regulator's own soft-start) that only connects the larger capacitance after Attached.SNK/negotiation has completed and the sink is ready to actually draw power. The Type-C spec does not specify *how* to implement that gating (that's downstream power-path design, covered by whatever chip/topology is chosen there) - it only sets the 10 µF number this document is citing.
