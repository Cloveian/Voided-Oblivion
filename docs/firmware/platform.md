# Platform
what language, SDK and stacks

## Identify

### Relevant constraints
- **Sub-1 ms latency**
- 1000Hz polling rate (can have others, but must support 1000Hz)
- N-key rollover
- Per-key RGB


### What has to be managed/controlled
- USB-HID stack
- Inter-tile UART (PIO)
- Submodule UART (hardware+PIO)
- Power delivery PHY I2C
- Mux select+ ADC input


### The gates

1. pure state-machine/PIO control
2. USB device stack doing **composite HID at 1000 Hz**
3. Full power management control
4. 1 ms loop

## Brainstorm

**Ruled out by the gates:**

- **QMK** rp2350 barely supported, and not very good raw control
- **ZMK** same
- **MicroPython / CircuitPython** Too slow - not enough controll

**Survivors:**

- Pico SDK (C/C++) + TinyUSB Full manufacturer support, full PIO/DMA/ADC/QMI exposed directly and documented. TinyUSB is the reference HID stack. The secure-boot path for FIDO 2 later is SDK + bootrom. Everything above the HAL is from scratch.
- **B - Rust (embassy-rp / rp235x-hal).** Good PIO support, `embassy-usb` does composite HID, and async/await maps genuinely well onto "8 links + a scan loop a PD state machine". The gap is PD - Rust FUSB302 work exists but with nothing like the mileage of the C options - and the secure-boot story is thinner.
- **C - Zephyr, bare (not ZMK).** Real driver model, threading, mature USB stack, scales to this much structural complexity. but not very good PIO

## Select (draft)

| Criteria                  | Weight | A: Pico SDK | B: Rust | C: Zephyr |
| ------------------------- | :----: | :---------: | :-----: | :-------: |
| Deterministic 1 ms loop   |   10   |      9      |    9    |     7     |
| Direct PIO + DMA control  |   9    |     10      |    8    |     4     |
| Composite HID at 1000 Hz  |   8    |      9      |    7    |     8     |
| Secure boot path (FIDO 2) |   5    |      9      |    5    |     5     |
| How much 'from scratch'   |   4    |      8      |    4    |     5     |
| **Weighted total**        |        |   **329**   |   259   |    215    |

Out of a possible 360 - **A wins at 91 %**, against B 72 % and C 60 %.

What 'from scratch' means: USB and PD. Those are the only two chunks big enough to move the number. A gets TinyUSB and a production-grade FUSB302 PD stack, both already in C. B has workable USB but writes PD from nothing, and PD is the single largest borrowable piece in the project. C has a mature USB stack and a USB-C subsystem, but is weakest exactly where this board leans hardest - PIO carries eight of its links.

---
Back to [firmware index](index.md) · [pin map](pin-map.md) · [truth table](truth-table.md) · [log](log.md)
