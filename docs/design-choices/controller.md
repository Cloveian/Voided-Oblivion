# Main controller/MCU

## Identify
I need to choose an MCU for the main board to use

### Relevant constraints/nice to haves:
#### Must haves
- USB type C wired connectivity
- Sub-1 ms latency
- 1000Hz polling rate (can have others, but must support 1000Hz)

#### Nice to haves
- Per-key RGB (under-glow)
- Low profile
- Number pad
- FIDO 2
- Ability to do on-device steno

#### New MCU requirements (some redundant, I'm too lazy to collapse them)
- Native USB device (composite HID) (on the root tile)
- Flexible timed I/O (PIO-like) to drive BOTH the inter-tile bus (≤4 sides) and the per-key RGB
- ADC + enough GPIO to analog-mux ~30 Hall keys/tile, fast enough for sub-1 ms
- Enough compute for per-tile analog scan + rapid-trigger at 1000 Hz
- Built in secure element, or I$^{2}$C for an external secure element (FIDO2)

## Brainstorm
There are a few chips i can think of, grouped by whether they have PIO (the thing my bus + RGB needs at the same time):

**Has PIO (Raspberry Pi silicon, the only ones with true PIO)**
- rp2040: dual M0+, 8 PIO state machines, 30 GPIO, USB FS, external flash, no secure boot
- rp2350a: dual M33/RISC-V, 12 PIO SMs, 30 GPIO, USB FS, TrustZone + secure boot, external flash
- rp2350b: same as A but 48 GPIO (QFN-80)
- rp2354a: rp2350a + 2MB built-in flash, 30 GPIO
- rp2354b: rp2350b + 2MB built-in flash, 48 GPIO

**Has a PIO-like peripheral (FlexIO)**
- Teensy 4.x (chip is NXP i.MX RT1062): M7 @600MHz, USB HS, FlexIO is the closest thing to PIO. Downsides: it's a board not a bare chip, and ~$20-30 each, rough when i need one per tile.

**Other USB-capable MCUs (no PIO; bus would have to run on UART/SPI + DMA)**
- STM32G4 (e.g. STM32G431/G474): M4F, the fastest/best STM32 ADCs, good for analog Hall scanning
- STM32F411 / F401: cheap M4, USB FS, very common
- STM32F405/407 or STM32H7 (H723/H750): more power / HS USB, overkill
- Microchip SAMD51 (ATSAMD51): M4F, USB, already used in some QMK boards
- WCH CH32V307: RISC-V, USB High-Speed, very cheap
- GD32F303 / GD32F4: STM32-ish clones

**Has a radio i'd pay for and not use (bluetooth was cut)**
- nRF52840: M4 + USB, my Corne chip, but the radio is now dead weight
- ESP32-S3 / ESP32-S2: native USB (classic ESP32 has none), WiFi/BT wasted

## Select

Gated first: needs PIO-like flexible I/O + native USB, which knocks out the radio chips and the no-PIO STM32/SAMD/CH32/GD32 options (kept only as fallback if PIO is ever abandoned). RP2350A/RP2354A are dominated by their B-variants (same chip, fewer GPIO), so only the B's are scored. That leaves four:

| Criteria                          | Weight | RP2040 | RP2350B | RP2354B | Teensy (i.MX RT1062) |
| --------------------------------- | :----: | :----: | :-----: | :-----: | :------------------: |
| PIO / flexible-IO (bus+RGB)       |   9    |   3    |    9    |    9    |          6           |
| GPIO count                        |   8    |   5    |    9    |    9    |          8           |
| Cost per unit (xN tiles)          |   7    |   9    |    7    |    7    |          1           |
| Integrated flash / fewer parts    |   6    |   4    |    4    |    9    |          8           |
| On-device steno (16-32 MB flash)  |   5    |   8    |    9    |    2    |          6           |
| Compute (scan, rapid-trigger)     |   5    |   5    |    7    |    7    |         10           |
| Availability / sourcing           |   5    |   9    |    8    |    5    |          7           |
| Security (FIDO2)                  |   3    |   2    |    7    |    7    |          7           |
| **Weighted Total**                |        |  270   | **367** |   347   |         309          |

**Winner: RP2350B (367 / 76.5%)**, paired with a big external QSPI flash (16-32 MB) for the steno dictionary.
