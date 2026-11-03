# MCU & flash - schematic-design calcs

RP2350B support-circuit math. Parts from [chips](../chips.md); decision from [controller](../design-choices/controller.md).

> **Note on scope.** There is deliberately no agent-written research page for the RP2350B - that one's the centrepiece and I'm doing the reasoning myself rather than reading an AI's summary of a 1300-page datasheet. So this page is **as-built documentation plus the maths I've actually checked**. The flash and crystal sections are complete; the RP2350 rail/decoupling section is descriptive rather than derived, on purpose.

## Contents
- [RP2350B rails and decoupling](#rp2350b-rails-and-decoupling)
- [Core regulator](#core-regulator)
- [Crystal + load caps](#crystal--load-caps)
- [QSPI flash - W25Q128JVS](#qspi-flash---w25q128jvs)
- [One flash chip or two?](#one-flash-chip-or-two)
- [USB DP/DM](#usb-dpdm)
- [Boot / reset / SWD](#boot--reset--swd)
- [RP2350-E9 and the neighbour-detect pull-downs](#rp2350-e9-and-the-neighbour-detect-pull-downs)

---

## RP2350B rails and decoupling

### Result / as-built
| Rail | Pins | Fed from | Decoupling |
| --- | --- | --- | --- |
| IOVDD ×8 | 5, 15, 24, 29, 41, 50, 60, 76 | +3V3 | C12–C18, C20, C21, C112, C113 (10 × 100nF) + C19 10µF + C6 4.7µF |
| DVDD ×3 | 10, 32, 51 | +1V1 | C8, C11, C110, C111 (4 × 100nF) + C7, C10 4.7µF |
| ADC_AVDD | 59 | +3V3 | shares the 3V3 bank |
| USB_OTP_VDD | 68 | +3V3 | shares |
| QSPI_IOVDD | 69 | +3V3 | shares |
| VREG_AVDD | 61 | +3V3 **through R3 33Ω** | C9 4.7µF |
| GND / EP | 81 | GND | - |

### Notes / gotchas
- ADC_AVDD is tied straight to +3V3 with no dedicated filter. On a board whose entire premise is 12-bit analog key sensing, that's the one rail I'd expect to see an RC or ferrite on, separated from the digital 3V3. The [3V3 rail's own noise story is unevidenced](power.md#3v3-ldo---tlv76733drvr-u7) and the [ratiometric assumption](keys.md#the-ratiometric-assumption) may or may not be cancelling supply noise for us.
- VREG_AVDD is the analog supply for the internal core regulator.

## Core regulator

### Result / as-built
Internal switching regulator:

| Pin | Net |
| --- | --- |
| VREG_VIN (64) | +3V3 |
| VREG_LX (63) | L1 3.3µH → +1V1 |
| VREG_FB (65) | senses +1V1 |
| VREG_PGND (62) | GND |

L1 is `L_pol_2016` - a 2016 polarised-marking inductor footprint carried over from the RP2350 reference design.

### Notes / gotchas
- Nothing here is tunable - the feedback is internal to the chip.

## Crystal + load caps

### Goal
12MHz reference accurate enough for USB full-speed.

### Datasheet refs
Abracon **ABM8-272-T3**: 12.000MHz, **load capacitance CL = 10pF**, drive level 10–200µW.

### Math
Standard load-cap sizing:
```
C1 = C2 = 2 x (CL - Cstray)
```
As-built C3 = C4 = **15pF**, which back-solves to:
```
Cstray = CL - C/2 = 10 - 7.5 = 2.5 pF
```
2.5pF of stray is optimistic - pin plus trace is more realistically 4–5pF. Taking Cstray = 5pF, the effective load the crystal actually sees is:
```
CL_actual = 15/2 + 5 = 12.5 pF   (vs 10 pF specified)
```
Frequency pulling from over-loading, using a generic motional capacitance C1m ≈ 5fF and C0 ≈ 3pF (these are typical values; the ABM8 datasheet doesn't publish them):
```
df/f = (C1m/2) x [ 1/(C0+CL_actual) - 1/(C0+CL_spec) ]
     = 2.5e-15 x [ 1/15.5p - 1/13p ]
     = -31 ppm
```

### Result
| | Value |
| --- | --- |
| C3, C4 as built | 15pF |
| R2 in series with XOUT | 1kΩ |
| Cstray | 5pF |
| CL_actual | 12.5pF (vs 10pF specified) |
| Frequency pulling | −30 to −60 ppm |
| USB full-speed requires | ±2500 ppm |

Not a problem, leave it.

### Notes / gotchas
- If you ever want it nominally right, 10–12pF caps would land closer to CL = 10pF.
- Over-loading does make the oscillator work slightly harder to start. Drive level hasn't been checked and can't be without knowing the RP2350's oscillator drive. If the crystal is slow to start or doesn't start cold, this is the first thing to look at.
- R2 in series with XOUT is the standard RP2350 crystal drive-limiting resistor. ✓

## QSPI flash - W25Q128JVS

### Goal
Boot flash for XIP, and optionally a second device for bulk storage.

### Datasheet refs
Winbond W25Q128JV. **W25Q128JVSIQ** (SOIC-8).

| Fact | Value | Why it matters |
| --- | --- | --- |
| QE bit | **permanently 1** on this ordering variant (§7.1.4, §11.1 note 5) | /WP and /HOLD are *always* IO2/IO3. They can never act as hardware pins, and need no external pull-ups. |
| Hardware /RESET | **none in SOIC-8** (only SOIC-16/TFBGA have it) | reset is software-only (66h+99h, ~30µs) or a power cycle |
| Max clock | 133MHz fast/dual/quad; **50MHz for plain Read Data (03h)** | dummy cycles are fixed |
| While BUSY | die "ignores further instructions except Read Status Register and Erase/Program Suspend" (§7.1.1) | **plain reads, including XIP fetches, are dropped - not queued** |

### Result / as-built
| | U3 (primary) | U4 (secondary) |
| --- | --- | --- |
| Populated | **yes** | **DNP** |
| /CS net | `FLASH_SS` | `FLASH2_SS` |
| /CS source | QSPI_SS via **R10 0Ω** (populated) | GPIO0 via **R11 DNP** |
| Alt /CS source | GPIO0 via **R9 DNP** | - |
| /CS pull-up | - | **R13 DNP** (+3V3) |
| Decoupling | C2 100nF | C22 DNP |
| IO0–3, CLK | shared QSPI bus | shared QSPI bus |

The schematic already carries the note: *"Optional Secondary flash or PSRAM (U4), using the second chip select (XIP_SS_N[1]) on GPIO0. N.B. Pull-up R13 will be required as GPIOs default to pull-downs at power-up."*

Without R13 the second device would be selected during boot while the primary is also being addressed.

### Notes / gotchas
- **No hardware reset on this package.** Combined with the RP2350 hardware design guide's own warning about flash getting stuck in continuous-read mode across a non-power-cycled MCU reset, a wedged flash needs a power cycle. On a bus-powered board that means unplugging.

## One flash chip or two?

While the die is BUSY with any program or erase, it drops plain reads - including XIP instruction fetches. So on a single chip, writing the steno dictionary stalls code execution, because the code is executing from the same die being written.

Erase/Program Suspend (75h) is the escape hatch, but:
- it doesn't cover Chip Erase,
- it needs firmware to orchestrate suspend/resume around every dictionary write,
- and the datasheet explicitly warns of data corruption if power is interrupted mid-suspend - on a **hotplug, no-battery board**.

### Does the dictionary ever get written at runtime?

| If... | Then |
| --- | --- |
| The dictionary is baked in with firmware and only ever **read** at runtime | **One chip is fine.** Drop U4 and its jumpers permanently, and GPIO19/GPIO0 frees up. 16MB is plenty for both. |
| The user can **edit/add** dictionary entries on the device | **Two chips.** Populate U4 + R11 + R13. The second die can erase in the background while XIP continues from the first, because erase is self-timed and continues after /CS deselects. |

The bus is still shared and time-multiplexed.

My read: on-device steno dictionary editing is a "nice to have" from the original goals list. So the default should be **one chip**, with U4 staying exactly as it is.

## USB DP/DM

### Result / as-built
| | Value |
| --- | --- |
| R7, R8 | 27Ω series on USB_DP / USB_DM |
| Then to | TS3USB30E mux |

Schematic note: *"Make sure R7 and R8 are close to RP2350"* ✓ - series termination belongs at the driver.

### Notes / gotchas
- ESD on D± is handled downstream - or rather, [isn't yet](comms.md#esd). The mux has component-level protection only and the TPD2E2U06 isn't placed.

## Boot / reset / SWD

### Result / as-built
| Function | Circuit |
| --- | --- |
| BOOTSEL | SW1 to GND, **R6 1kΩ** from QSPI_SS to the switch node (`USB_BOOT`) - pressing pulls QSPI_SS low through 1k |
| Reset | SW2 to `RUN`, **R4 1kΩ** to GND |
| SWD | **J4 SM03B-SRSS-TB** (JST SH 3-pin): SWCLK / GND / SWD, mounting pin to GND |

The BOOTSEL circuit is the standard RP2350 arrangement - hold QSPI_SS low at boot to force USB mass-storage mode. ✓

### Notes / gotchas
- **No 3V3 on the debug connector**, so a debug probe can't detect target power or power the target. Fine for a bus-powered board that's always self-powered when you'd want to debug it.
- RUN has an internal ~50kΩ pull-up on-chip, so R4 is only the switch's series limiter.

## RP2350-E9 and the neighbour-detect pull-downs

The RP2350 datasheet carries an inline warning in its GPIO/pads chapter: **"Under certain conditions, pull-down does not function as expected. For more information, see RP2350-E9."** The later-stepping changelog describes the fix as *"increased leakage current on Bank 0 GPIO when pad input is enabled - the pad circuit is modified to eliminate the erroneous leakage path through the input buffer."*

The [inter-tile neighbour detection](comms.md#inter-tile-uart-lines-not-drawn-yet) scheme depends on an Rx line reading **low** when no neighbour is present.

If that relies on an *internal* pull-down, the failure mode is a phantom neighbour on an empty edge - which corrupts topology discovery.

### The actual numbers - read the full erratum

Note the one in `Refrences/datasheets/` was a **truncated download** - `pdftotext` dies at EOF.

> "the leakage current exceeds the standard specified IIN leakage level. During this condition the pad **can source current** (the exact amount is dependent on the chip itself and the exact pad voltage, but **typically around 120μA**). This leakage will **hold the pad at around 2.2V** as that is the effective source voltage of the leakage, and can only be overcome with a suitably low impedance driver / pull."
>
> "**Driving / pulling the pad input low with a low impedance source of 8.2 kΩ or less** will overcome the erroneous leakage."

Sizing it, with **VIL max = 0.35 × IOVDD = 1.155V** (Table, "Input Voltage VIL"):

| R_pd | V at 120µA | margin to VIL |
| --- | --- | --- |
| 8.2kΩ (the datasheet's stated threshold) | 0.984V | **171mV** |
| **4.7kΩ** | **0.564V** | **591mV** |
| 10kΩ | 1.20V | **fails** |

Fit 4.7kΩ external pull-downs on all four inter-tile Rx lines - 4 resistors, immune to which silicon stepping arrives from LCSC. This is nothing against the sensor load:

| | Current |
| --- | --- |
| Pull-down per side, neighbour's Tx high | 0.70mA |
| Pull-downs per tile | 2.8mA |
| Sensor load | 270mA |

Worth confirming which stepping the purchased parts actually are.

- E9 affects stepping A2 and is fixed in A3.
- *"This doesn't affect the pull-down behaviour of the pads immediately following a PoR or RUN reset because the input enable field is initially clear."* Detection is broken exactly when firmware starts *using* the input, so the reset-time behaviour doesn't help.
- QSPI pads, the USB PHY and (effectively) SWD are unaffected. Only Bank 0 GPIO 0–47.

---
Back to [schematic-design index](index.md) · [checklist](../schematic-checklist.md) · [research](../research/README.md)
