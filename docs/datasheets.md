# Datasheets

The PDFs used to live in `Refrences/datasheets/`. they're gone from the repo now - 129MB of
manufacturer documents i don't own and [can't licence](https://github.com/Cloveian/Voided-Oblivion/blob/main/LICENSE.md)
to anyone. this page is the index instead.

Everything the design actually concluded from these is written up in
[schematic-design](schematic-design/index.md) and [research](research/README.md), with the
relevant section and page cited inline. you shouldn't need the PDFs to read the docs - they're
here so you can check my work.

## Where to get them

| part | what it does here | source |
| --- | --- | --- |
| **RP2350** (datasheet, hardware design guide, product brief, errata) | the MCU. one per tile | [datasheets.raspberrypi.com](https://datasheets.raspberrypi.com/) |
| Pico SDK / getting-started / MicroPython guides | firmware reference | [datasheets.raspberrypi.com](https://datasheets.raspberrypi.com/) |
| **TPS54302** | 5V bucks (U5 clean, U6 big) | [ti.com/product/TPS54302](https://www.ti.com/product/TPS54302) |
| **TLV76733** | 3V3 LDO (U7) - the as-built part | [ti.com/product/TLV767](https://www.ti.com/product/TLV767) |
| **TLV431** | shunt reference (U10) | [ti.com/product/TLV431](https://www.ti.com/product/TLV431) |
| **LM2903** | dual comparator (U11), the VBUS→PD handoff | [ti.com/product/LM2903](https://www.ti.com/product/LM2903) |
| **TLV1805** | comparator considered and rejected | [ti.com/product/TLV1805](https://www.ti.com/product/TLV1805) |
| **LM66100** | ideal diode (U9) | [ti.com/product/LM66100](https://www.ti.com/product/LM66100) |
| **LM74700-Q1** | backfeed protection (D1/D2) | [ti.com/product/LM74700-Q1](https://www.ti.com/product/LM74700-Q1) |
| **CD74HC4067** | 16:1 analog mux, 2 per tile | [ti.com/product/CD74HC4067](https://www.ti.com/product/CD74HC4067) |
| **SN74LVC2T45** | 3V3→5V level shift for the LED chain | [ti.com/product/SN74LVC2T45](https://www.ti.com/product/SN74LVC2T45) |
| **TPD2E2U06** | ESD array on USB | [ti.com/product/TPD2E2U06](https://www.ti.com/product/TPD2E2U06) |
| **TS3USB30E** | USB mux | [ti.com/product/TS3USB30E](https://www.ti.com/product/TS3USB30E) |
| **MAX40203** | ideal diode considered and rejected | [analog.com](https://www.analog.com/en/products/max40203.html) |
| **FUSB302BMPX** | USB-PD PHY, 2 per tile | [onsemi.com](https://www.onsemi.com/products/interfaces/usb-type-c/fusb302b) |
| **W25Q128JV** | QSPI flash | [winbond.com](https://www.winbond.com/hq/product/code-storage-flash-memory/serial-nor-flash/) |
| **AO3401A / AO4406A / AO4407A / AO4606** | the P-FET switches (Q1-Q7) | [aosmd.com](https://www.aosmd.com/) |
| **NCE4009S / WSP4606 / WSP4882** | FETs evaluated during selection | LCSC part search |
| **BC847 / BC857 / MMBT2222A** | gate-drive BJTs | [nexperia.com](https://www.nexperia.com/) |
| **BZX84C10 / BZV55B5V1** | zener gate clamps | [nexperia.com](https://www.nexperia.com/) |
| **SS54** | schottky backfeed diode | [LCSC C7420369](https://www.lcsc.com/product-detail/C7420369.html) |
| **GH39FKSW** | the hall sensor, 30 per tile | [LCSC C5668579](https://www.lcsc.com/product-detail/C5668579.html) |
| **SS49E** | hall sensor considered and rejected | [honeywell.com](https://sps.honeywell.com/) |
| **SK9822 / SK9822-EC20** | per-key RGB | LCSC part search |
| **ABM8-272-T3** | 12MHz crystal | [abracon.com](https://abracon.com/) |
| **APH0630 10µH** | buck inductors (L2/L3) | LCSC part search |
| **AP3010 / AP2171** | submodule power switch | [diodes.com](https://www.diodes.com/) |
| **XC6220B331MR** | the LDO i *thought* i had - see [the revisit](schematic-design/power.md#revisit-the-part-is-a-tlv76733-not-an-xc6220---and-it-changes-three-conclusions) | [torexsemi.com](https://www.torexsemi.com/) |
| **PG-2.5-6P-5.5H-SM-RA** / PD- variant | the inter-tile pogo connector. single-source, not on LCSC | Shenzhen Yiwei, direct |
| **USB Type-C spec** | receptacle pinout, PD power rules | [usb.org/documents](https://www.usb.org/documents) |

## App notes worth keeping

these were load-bearing in the layout and power work rather than the part selection:

- TI **SLPA005** power-supply layout, and the buck layout guide - both feed [pcb-stackup](design-choices/pcb-stackup.md)
- TI ADC input-driving note - the settling-time analysis in [keys](schematic-design/keys.md)
- TI USB Type-C PD design guide, and two ESD/surge notes for USB interfaces
- Nexperia MOSFET app note - gate drive
- TI analog mux selection guide

## Getting them back locally

if you want the PDFs on disk again, the MPNs above are enough to re-download them. i keep mine
in `Refrences/datasheets/`, which is now in `.gitignore` - it stays on my machine and out of git.
