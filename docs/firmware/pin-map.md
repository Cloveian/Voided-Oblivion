# Pin map

Every GPIO on the RP2350B, what it's wired to, and what firmware needs to know about it. The same pins grouped by what they *do*, with the state meanings, are in the [truth table](truth-table.md).

**44/48 GPIO, 6/8 ADC, 12/12 PIO state machines.**

| GPIO | Net            | Peripheral | What firmware needs to know                                                                                                                       |
| :--: | -------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
|  0   | `PD EN TOP`    | out        | Edge PD switch, must know that neighbor is there before enable. ~1 ms on-ramp, ~10 ms off, only blocks outbound. firmware controlled power budget |
|  1   | `PD EN RIGHT`  | out        |                                                                                                                                                   |
|  2   | `PD EN BOTTOM` | out        |                                                                                                                                                   |
|  3   | `PD EN LEFT`   | out        |                                                                                                                                                   |
|  4   | `Tx BOTTOM`    | PIO        |                                                                                                                                                   |
|  5   | `Rx BOTTOM`    | PIO        | Default pulled low, if high=neighbor there                                                                                                        |
|  6   | `Tx RIGHT`     | PIO        |                                                                                                                                                   |
|  7   | `Rx RIGHT`     | PIO        |                                                                                                                                                   |
|  8   | `AS0`          | out        | Mux select, shared by both muxes ~10–15 µs settling                                                                                               |
|  9   | `AS1`          | out        |                                                                                                                                                   |
|  10  | `AS2`          | out        |                                                                                                                                                   |
|  11  | `AS3`          | out        |                                                                                                                                                   |
|  12  | `Tx TOP`       | PIO        |                                                                                                                                                   |
|  13  | `Rx TOP`       | PIO        |                                                                                                                                                   |
|  14  | `+5VP EN`      | out        |                                                                                                                                                   |
|  15  | `PD1 INT`      | in         | PD chip #1, active low                                                                                                                            |
|  16  | `Tx LEFT`      | PIO        |                                                                                                                                                   |
|  17  | `Rx LEFT`      | PIO        |                                                                                                                                                   |
|  18  | `PD2 INT`      | in         | PD chip #2                                                                                                                                        |
|  19  | `FLASH CS1n`   | QMI        |                                                                                                                                                   |
|  20  | `PD1 SDA`      | I2C0       |                                                                                                                                                   |
|  21  | `PD1 SCL`      | I2C0       |                                                                                                                                                   |
|  22  | `SM Tx TL`     | PIO        |                                                                                                                                                   |
|  23  | `SM Rx TL`     | PIO        | No pull fitted - disable the input on an empty corner (E9)                                                                                        |
|  24  | `SM Tx TR`     | **UART1**  |                                                                                                                                                   |
|  25  | `SM Rx TR`     | **UART1**  |                                                                                                                                                   |
|  26  | `SM Tx BR`     | PIO        |                                                                                                                                                   |
|  27  | `SM Rx BR`     | PIO        |                                                                                                                                                   |
|  28  | `SM Tx BL`     | **UART0**  |                                                                                                                                                   |
|  29  | `SM Rx BL`     | **UART0**  |                                                                                                                                                   |
|  30  | `PD2 SDA`      | I2C1       |                                                                                                                                                   |
|  31  | `PD2 SCL`      | I2C1       |                                                                                                                                                   |
|  32  | `SM BS EN`     | out        |                                                                                                                                                   |
|  33  | `SM+ EN`       | out        |                                                                                                                                                   |
|  34  | `LED SCK`      | SPI0       | ≤15 MHz (EC20, not the plain SK9822's 30) Keep both driven, even if not powered                                                                   |
|  35  | `LED TX`       | SPI0       |                                                                                                                                                   |
|  36  | `BS+ SRC`      | in         | Open-drain. Low = running off VBUS via Q1 (pre-PD); high = clean buck feeding BS+                                                                 |
|  37  | `SM+ FLT`      | in         | Open-drain, 100k pull-up. Only signal that the submodule rail tripped                                                                             |
|  38  | *spare*        |            |                                                                                                                                                   |
|  39  | *spare*        |            |                                                                                                                                                   |
|  40  | `AM0`          | **ADC0**   | Mux A, 15 keys. `adc_gpio_init()` - E9                                                                                                            |
|  41  | `AM1`          | **ADC1**   | Mux B, 15 keys                                                                                                                                    |
|  42  | `SM ID TL`     | **ADC2**   | Divider off +3V3, so readable with the corner's own 5 V rail off                                                                                  |
|  43  | `SM ID TR`     | **ADC3**   |                                                                                                                                                   |
|  44  | `SM ID BR`     | **ADC4**   |                                                                                                                                                   |
|  45  | `SM ID BL`     | **ADC5**   |                                                                                                                                                   |
|  46  | *spare*        | (ADC6)     | Still ADC-capable                                                                                                                                 |
|  47  | *spare*        | (ADC7)     | Still ADC-capable                                                                                                                                 |

**TL / TR / BR / BL** are the four submodule corners, matching the [truth table](truth-table.md#uart). `SM` marks them as corner (submodule) signals - not to be confused with the edge signals `Tx TOP` / `Rx TOP`, which are inter-*tile*.

---
Back to [firmware index](index.md) · [truth table](truth-table.md)
