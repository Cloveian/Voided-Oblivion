# Comms & USB - schematic-design calcs

Datasheet math for the USB front-end and the inter-tile / submodule links. Parts from [chips](../chips.md); behaviour from [comms design-choice](../design-choices/comms.md); the PD/CC re-decision is in [comms revisit](../design-choices/comms.md#revisit-pdcc-architecture-the-cc-mux-doesnt-survive-cold-start).

Values here are **as-built**, with the derivation. Where the independent [datasheet research](../research/) disagrees, both are shown and resolved.

Per-section skeleton: **Goal → Datasheet refs → Math → Result → Notes/gotchas.**

## Contents
- [USB-C receptacles (USB1/USB2)](#usb-c-receptacles-usb1usb2)
- [Cold start: where Rd actually comes from](#cold-start-where-rd-actually-comes-from)
- [Attach inrush - the 10µF problem](#attach-inrush---the-10µf-problem)
- [USB-PD PHY - FUSB302BMPX ×2 (PD1/PD2)](#usb-pd-phy---fusb302bmpx-2-pd1pd2)
- [USB data mux - TS3USB30ERSWR (U2)](#usb-data-mux---ts3usb30erswr-u2)
- [SEL detect - which port wins](#sel-detect---which-port-wins)
- [ESD](#esd)
- [Inter-tile UART lines (not drawn yet)](#inter-tile-uart-lines-not-drawn-yet)
- [Submodule corner UART lines (not drawn yet)](#submodule-corner-uart-lines-not-drawn-yet)

---

## USB-C receptacles (USB1/USB2)

### Goal
Two sink-only receptacles per tile, both orientation-independent, both able to negotiate full PD. USB 2.0 full-speed only - no SuperSpeed, no alt mode.

### Result / as-built pin treatment
| Contact | As-built | Verdict |
| --- | --- | --- |
| A4, A9, B4, B9 (VBUS ×4) | all bussed to one node per port | ✓ required by Table 3-4 Note 2, not optional at 5A |
| A1, A12, B1, B12 (GND ×4) | all to GND | ✓ |
| A5 / B5 (CC1 / CC2) | direct to the port's own FUSB302 | ✓ - see cold-start below |
| A6, B6 (Dp1, Dp2) | **shorted together**, then to the mux | ✓ spec-sanctioned |
| A7, B7 (Dn1, Dn2) | **shorted together**, then to the mux | ✓ |
| A8, B8 (SBU1/2) | open | ✓ correct with no alt mode |
| A2/A3/B2/B3, A10/A11/B10/B11 (TX/RX) | open | ✓ correct for USB 2.0 only |
| SH (shield) | direct to GND | acceptable; see note |

**Shorting Dp1↔Dp2 and Dn1↔Dn2 at the receptacle is the spec's own answer** to orientation independence for a USB 2.0 device (Table 3-4 Note 1), keeping the stub short. It means no active part is needed to make either plug orientation work on data - which matters given this project's history with active parts in the cold-start path.

### Notes / gotchas
- Shield straight to GND is the simple option and fine for a wired desk device. The alternative (resistor + cap bleed to GND) buys EMI/ground-loop flexibility that a single-ended, bus-powered board doesn't obviously need. Leaving as-is.

## Cold start: where Rd actually comes from

This is the thing that killed the CC-mux, so it's worth stating precisely what makes the current design work.

**There are no external 5.1kΩ Rd resistors on this board, and none are needed.** The FUSB302B provides Rd from on-die circuitry, and it does so *before VDD exists*:

- The datasheet specifies **`VUFPDB` ≤ 2.18V max** - "SNK Pull-down Voltage in Dead Battery under all Pull-up SRC Loads" (CC Switches table, p.15). That is a *clamped voltage* spec, deliberately separate from the precision resistance.
- Footnote 5 on the same table: **"RDEVICE minimum and maximum specifications are only guaranteed when power is applied."** The datasheet is explicit about separating "the precise 4.6–5.6kΩ you get once powered" from "what CC does with zero power".
- `Switches0` (0x02) **resets to 0x03 = PDWN1=PDWN2=1** (Table 6, p.21). Both pull-downs are on by hardware reset default, before firmware writes a single I²C byte - so there's no race where firmware has to be fast enough.
- USB Type-C §4.8.5 sanctions exactly this shape of circuit: a clamp rather than a precision resistor is sufficient for a source to recognise a sink and apply VBUS.

Two consequences worth writing down:

1. **2.18V clamped ≈ the ±20% Rd row in Table 4-25**, which the spec says is good for attach detection but *not* guaranteed for reading the source's current advertisement. Once VDD is up, `RDEVICE` is 4.6–5.6kΩ = 5.1k ±10%, which *is* guaranteed for advertisement detection. So: **unpowered → the source turns VBUS on; powered → full 1.5A/3.0A advertisement reading works.** Correct behaviour in both states.
2. **[checklist §6](../schematic-checklist.md) still says "Rd pull-downs on the RP2350B side".** That's left over from the CC-mux design and is wrong now - adding external Rd in parallel with the PHY's own would put ~2.5kΩ on CC and break the advertisement thresholds. **Don't add them.**

> **!firmware-note!** **CC1/CC2 are crossed between each PHY and its connector** - PD1 CC1 lands on USB1's CC2 and vice versa, consistently on both ports. For a USB-2.0-only sink this is harmless: both pins carry Rd, D± are position-shorted so data doesn't care, and there's no VCONN or alt-mode lane to steer. The only effect is that the orientation bit firmware reads is inverted from physical reality. **Firmware must not use that bit for anything physical**, and if VCONN is ever enabled it would land on the wrong pin. Worth a comment on the schematic so it reads as deliberate rather than as a mistake.

## Attach inrush - the 10µF problem

USB Type-C **Table 4-3 caps a sink at 10µF between VBUS and GND at the receptacle before attach.** The point is that a source applying default 5V/500mA into a big discharged bulk sees an inrush it may read as a fault.

**As-built, the tile presents far more than that.** Q1 (VBUS→BS+) is *default ON* - that's deliberate and necessary, it's what lets a cold tile get its first 5V. But it means everything on BS+ is presented to the connector as soon as Q1's Vgs passes threshold partway up the VBUS ramp:

```
C24  10 uF   (LDO Cin)
C41 100 uF   (bulk)
-----------
    110 uF   presented through Q1   vs a 10 uF spec ceiling  ->  11x over
```

PD+ bulk (C26, C31, 10µF each) is *not* part of this, because Q2 is default OFF - that part of the design is right.

Rough inrush with Q1's existing Miller soft-start (C45 1nF against R35 1MΩ, τ ≈ 1ms):
```
I = C dV/dt = 110uF x 5V / 1ms = 550 mA
```
That is over the 500mA a source supplies by default before any negotiation, on a rail that also has to boot the MCU. This is the "droop/renegotiate loop" risk that was flagged as a to-do in [implementation](implementation.md#still-to-do-real-but-not-showstoppers) and only partly closed by adding C45.

> **RESOLVED.** C41 was repurposed rather than deleted - it's now **1µF on `+5VA`** serving as U9's input cap. BS+ attach capacitance is now **C24 1µF + C76 1µF ≈ 2µF**, comfortably under the 10µF ceiling instead of 11× over it. One refdes, two problems fixed.

**The cheap fix is to delete C41.** It's 100µF of bulk on BS+ with no derivation behind it - the LDO's own datasheet asks for **Cin = 10µF**, which C24 already provides. Dropping C41 takes attach capacitance from 110µF to 10µF, landing exactly on the spec ceiling, and simultaneously removes the [100µF-in-an-0402 footprint error](power.md#bulk-caps-and-the-footprint-defect). One deletion fixes two problems.

If bulk on BS+ turns out to be genuinely wanted later (e.g. to ride out the handoff), it belongs **behind** something that isn't presented at attach, not directly across VBUS through a default-ON FET.

## USB-PD PHY - FUSB302BMPX ×2 (PD1/PD2)

### Goal
One PHY per receptacle so either port can negotiate independently in any rotation. Sink-only. MCU runs the PD state machine over I²C.

### Datasheet refs
onsemi FUSB302B. I²C address **0x22** (7-bit) fixed by part number. VDD abs max 6.0V. **CC abs max 6.0V.** VBUS pin abs max 28V, **recommended max 21V**. I²C Fast Mode Plus to 1MHz, Cb ≤ 550pF. Table 31 recommends RPU 4.7kΩ, RPU_INT 1.0kΩ min / 4.7kΩ typ.

### Result / as-built
| Item | As-built | Verdict |
| --- | --- | --- |
| VDD | +3V3, C42/C43 0.1µF | ✓ |
| I²C | separate buses: PD1→GPIO20/21, PD2→GPIO30/31 | ✓ no address collision, both plain BMPX |
| I²C pull-ups | R42/R43, R40/R41 = **4.7kΩ to +3V3** | ✓ matches RPU typ |
| INT_N pull-ups | R44/R45 = **100kΩ to +3V3** | ⚠ see below |
| VBUS sense | each PHY to its **own port's raw pre-Schottky VBUS** | ✓ correct, verified on the netlist |
| CC1/CC2 | direct to the port's connector | ✓ (crossed - see above) |
| VCONN | both pins tied to **+3V3** | ⚠ see below |

### Notes / gotchas
- **INT_N pull-up at 100kΩ is 21× the datasheet typical** (Table 31: 1.0kΩ min, 4.7kΩ typ). It'll work - INT_N is an interrupt, not a timed bus - but 100kΩ against pin and trace capacitance gives slow rising edges and more noise pickup on a line that sits next to switching converters. **Recommend 4.7kΩ–10kΩ.** Cheap change, no downside.
- **!firmware-note!** **VCONN tied to +3V3 contradicts [chips](../chips.md)**, which says "VCONN NC (sink)". As-built is harmless: VCONN's recommended range is 2.7–5.5V so 3.3V is legal as a supply input, and since this is sink-only, firmware never enables the internal VCONN switch. But **the doc and the board must agree** - and there's a standing firmware rule that falls out of it: *never enable the VCONN switch*, because it would drive 3.3V onto a CC pin (harmless against the 6V abs max, but not a valid VCONN and potentially confusing to an e-marked cable).
- **No OVP on the VBUS sense pin.** The datasheet describes this pin as "expected to be an OVP protected input". As-built it connects straight to the raw port VBUS, which reaches 20V against a **21V recommended max** - about 1V of margin, with abs max at 28V. A 20V contract with any overshoot during transition eats that. Worth either a small series resistor + clamp, or at minimum acknowledging it as an accepted risk.
- **CC has 6.0V abs max and a cable can put VCONN (5.5V max) on the unused CC pin** - 0.5V of margin, with nothing on the net. The old [checklist](../schematic-checklist.md) plan for "100Ω series on CC" would help here without disturbing Rd (100Ω against 5.1kΩ is a 2% perturbation, inside the ±10% window). **Worth adding**, given CC pins are the most exposed nets on the board.
- The datasheet contradicts itself on I²C pull-up rail: Table 31 says VPU 1.62–1.98V, but Note 6 (p.17) says "between 1.71V and VDD". Pulling to 3.3V = VDD is legal under Note 6. As-built is fine; noting it because a future reader will find the Table 31 range and worry.

## USB data mux - TS3USB30ERSWR (U2)

### Goal
Switch D+/D− between the two receptacles and the MCU's single USB port. CC does **not** go through here.

### Datasheet refs
TI TS3USB30E. **VCC abs max 7V, recommended 3.0–4.3V.** Control inputs (S, OE) abs max **7V, fixed, not VCC-relative**. RON 10Ω max, Cio(ON) 7.5pF, bandwidth 1400MHz. ESD: **JEDEC HBM/CDM only - no IEC 61000-4-2 rating anywhere.** Latch-up "exceeds 100mA per JESD 78 Class II" — **"Except OE and S inputs."**

### Result / as-built
VCC = **+3V3** (C40 10µF, C115 100nF), OE tied low through R17 0Ω (always enabled), S driven from `USB SEL` through R14 0Ω with R39 100kΩ pull-down.

**VCC on +3V3 is the only correct choice** and the board has it right. The recommended range is 3.0–4.3V: BS+ and +5VP at 5V are outside it, and PD+ at 9–20V would destroy the part outright (7V abs max). +3V3 is also the rail that doesn't move during PD transitions, which matters because Type-C allows VBUS transitions to take up to 650ms - a mux riding a rail that follows PD's state machine would glitch the data bus mid-negotiation.

Bandwidth is a non-issue: ~1.4GHz characterised against full-speed USB at 12Mbit/s, roughly 100× more than needed.

## SEL detect - which port wins

### Goal
Pick which receptacle's D± reaches the MCU, in hardware, with no firmware involvement.

### Result / as-built
```
USB1 raw VBUS --R37 10k--> USB SEL --R14 0R--> U2 pin 10 (S)
                              |
                        D3 BZV55B3V3 (3.3V zener) to GND
                        C39 100nF to GND
                        R39 100k pull-down
```
S low = port 2, S high = port 1. So **port 1 wins when both are plugged in**, and port 2 is the default with nothing attached.

> ⚠ **Corrected 2026-08-20.** This section used to say "USB2 raw VBUS → R37" and "port 2 wins" - and the board was wired that way, which was **backwards**. The mux's channels are physically D1± = USB2, D2± = USB1, and the truth table is S=L → D1, S=H → D2 - so sensing VBUS2 selected whichever port *didn't* have the cable in every single-cable case. The keyboard could never enumerate on one cable. The 08-08 review verified the S-network levels, called it "a clean hardware port arbiter", and never checked the channel map; the 08-18 review caught it. Fix was one net - R37's sense moved to **VBUS1** - and the cost is the priority flip: **port 1 wins when both are plugged.** If both-plugged behaviour ever surprises anyone, this is why. Firmware note: there is no readback on `USB SEL`, so master election infers the active port from FUSB302 status, not from the mux.

### Notes / gotchas
- ✅ **Fixed on the board** - D3 is a BZV55B**3V3** now (verified in the 08-18 review), exactly the cheap fix below. Old text kept for the record:
- ⚠ **The clamp voltage is wrong for the rail the mux runs on.** D3 clamps `USB SEL` at ~5.1V. That's safely under the 7V absolute max — but the mux's VCC is 3.3V, and the datasheet's recommended VIH range is **1.3V to VCC**. Driving S to 5.1V puts it ~1.8V above VCC, forward-biasing the input's clamp structure into the supply. And the latch-up guarantee **explicitly excludes S and OE**, so this is precisely the pin where exceeding VCC isn't covered by anything.
  - **Fix (cheap): change D3 to a ~3.0–3.3V zener** (e.g. BZX84C3V3), so the clamp lands inside the recommended input range instead of above it. R37's 10kΩ already limits the current, so nothing else changes.
  - The intent behind the 5.1V part is sound - the comment on the sheet says "don't fry the SEL pin on the usb mux", and it does prevent the 20V case. It just doesn't go far enough: the target isn't "under 7V", it's "at or below VCC".
- With R37 10kΩ into R39 100kΩ, an unclamped divider would sit at VBUS × 100/110 = 0.91 × VBUS, i.e. 4.5V at a 5V VBUS and 18V at 20V - so the zener is doing real work, not decoration. An alternative fix is re-proportioning R37/R39 to divide down to ~3V and keep the zener as backstop.

## ESD

**As-built there is no external ESD protection on the USB data lines**, and the TPD2E2U06 in [checklist §1](../schematic-checklist.md) isn't placed.

The mux's built-in protection is **component-level only** (JEDEC HBM/CDM) - the datasheet carries **no IEC 61000-4-2 rating at all**, which is the system-level test that describes a human touching a connector. TI's own USB ESD app note recommends ≥8kV contact / 15kV air for USB 2.0 D±.

**Verdict: the external array is not redundant - add it.** TPD2E2U06 gives 25kV/30kV at 1.5pF per channel, which is negligible against full-speed USB. **One per receptacle, placed between the connector and the mux**, as close to the connector as routing allows.

## Inter-tile UART lines (not drawn yet)

4 sides × Tx/Rx at ≥4 Mbaud. Top+Left on UART0-capable pins, Bottom+Right on UART1-capable, for the [rotation pairing](../design-choices/comms.md#which-sides-get-the-hardware-uarts).

- **Rx pull-down per side** for neighbour detection - a side with no neighbour reads low, a side with one is driven high by the neighbour's Tx.
- ~~**Check this against the RP2350 errata before committing.**~~ **checked - it bites, and hard.** RP2350-E9 isn't a weak pull-down, it's an active ~120µA *source* that parks a floating input at 2.2V, i.e. a **phantom neighbour on every empty edge**. Must be external, and **4.7kΩ**, not the datasheet's 8.2k boundary. Full working in [mcu](mcu.md#rp2350-e9-and-the-neighbour-detect-pull-downs).
- Series termination on the Tx side is worth pads at 4 Mbaud across a pogo/spring-finger contact of unknown impedance. **Fit the footprint, populate 0Ω**, per the project's jumper convention - swap to 22–33Ω if the prototype rings.

### ~~which function number~~ - superseded, inter-tile is all-PIO now

Checked the Bank 0 function table (Table 3) because on RP2040 the pattern is `base+0 = TX, +1 = RX, +2 = CTS, +3 = RTS`, which would have made GPIO6/7 a CTS/RTS pair and broken the pairing on Bottom+Right. **RP2350 adds an F11 column** that puts UART TX/RX back onto the CTS/RTS pins, so all four pairs were genuinely hardware-UART-capable - just with **Right on F11 where the other three are F2**, which was a real firmware gotcha.

> **All of that is now moot.** The [PIO/SM reallocation](../design-choices/comms.md#revisit-the-piosm-allocation-was-built-on-a-wrong-assumption) moved both hardware UARTs to submodule corners, so **all four inter-tile sides run on PIO** - and PIO functions (F6/F7/F8) are uniform across every GPIO. **Nothing in the design uses F11.** Keeping the table below because the finding is still true of the silicon and worth not re-deriving.

| side | pins | UART | function |
| --- | --- | --- | --- |
| Top | GPIO12 / 13 | UART0 TX/RX | F2 |
| Left | GPIO16 / 17 | UART0 TX/RX | F2 |
| Bottom | GPIO4 / 5 | UART1 TX/RX | F2 |
| Right | GPIO6 / 7 | UART1 TX/RX | **F11** |

### ~~why the pairing is 2+2, and *these* 2+2~~ - superseded

> **The pairing no longer exists.** With all four inter-tile sides on PIO they're identical - there's no hardware UART to assign, so no pairing to get right. Kept because the *reasoning* is the interesting part and it's the kind of thing that gets re-derived from scratch otherwise.

the *reason* is already settled over in [design-choices](../design-choices/comms.md#which-sides-get-the-hardware-uarts): the hardware UARTs cover 2 of 4 sides, the primary relay direction changes with how the tiles are arranged, so **firmware picks the most important sides at runtime based on the tile configuration**. that's what won the table (286 vs 220/213).

what's *not* recorded there is the pin-level half - which specific 2+2 actually delivers that, because not every 2+2 does. each hardware UART is a **2-way selector**, and the pairing deliberately puts **opposing sides on different UARTs**:

| | UART0 picks | UART1 picks |
| --- | --- | --- |
| | **Top** or **Left** | **Bottom** or **Right** |

so Left and Right sit on *different* UARTs, and Top and Bottom sit on *different* UARTs. that's what makes the [firmware-assigned decision](../design-choices/comms.md#which-sides-get-the-hardware-uarts) actually pay off in both configs:

- **portrait / horizontal row** - Left+Right are the connected sides. Left takes UART0, Right takes UART1. **both traffic-carrying sides are on hardware.**
- **landscape / stack** - Top+Bottom are connected. Top takes UART0, Bottom takes UART1. **both on hardware.**

either way the two sides that carry real traffic get the two hardware UARTs, and the two sides with no neighbour fall to PIO SMs where they cost nothing. **that's the "firmware picks the important sides" decision actually being buildable** - the runtime choice only has something to choose from because the pins were paired this way.

**a 1+3 split would break this**, which is why it isn't one. pin UART0 to Top and let UART1 choose among Bottom/Left/Right, and a horizontal row suddenly needs Left *and* Right out of the same UART - so one of the two active sides drops to PIO. the count is the same (2 hardware, 2 PIO) but it lands on the wrong sides. **2+2 across the opposing axes is the thing that makes it work, not the number 2.**

## Submodule corner UART lines (not drawn yet)

4 corners × Tx/Rx on GPIO22–29, independent PIO state machines, 5V + GND per corner from the gated buck, ~300mA/port budget.

- Corner power comes off **+5VP** via a **group load switch** (AP2171WG-7, 1A), so firmware can shed submodules without touching RGB — but not the reverse. The switch is *downstream* of +5VP, so it can only remove power. Submodules still die when the big buck is gated; **the lever for RGB is the SK9822's hardware global brightness, not the rail.**
- ~~Same disconnect detection as the inter-tile Rx idle/pull-down trick.~~ **Only works for modules that have an MCU.** The Rx-idle trick needs the far end to drive Tx; a dumb module never drives anything and reads as absent forever. **Detection is now the ID pin** — a divider between the tile's +3V3 pull-up and a resistor in the module, read on an ADC. It also identifies the module class, and works **with the corner rail switched off**, so firmware can read what's plugged in before deciding to power it. See [submodules](../design-choices/submodules.md#the-gap-isnt-pin-count-its-detection).
- **Connector is 5-pin now:** `ID GND 5V Rx Tx` clockwise. A module with no MCU just gets Tx/Rx reconfigured as plain GPIO.
- Nothing here constrains the electrical design further until the physical connector is picked - the 4-signal contract is fixed either way.

---
Back to [schematic-design index](index.md) · [checklist](../schematic-checklist.md) · [research](../research/)
