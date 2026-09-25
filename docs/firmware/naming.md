# Naming

Firmware nameing conventions

Actual key mapping lives in the [Key/LED/Mux table](truth-table.md#keyledmux-table)

## The namespaces

| Name               |        Range        | Fixed by                                           | Used for                               |
| ------------------ | :-----------------: | -------------------------------------------------- | -------------------------------------- |
| **Local key**      |        0–29         | this page (`row × 5 + col`)                        | storage, wire format, calibration      |
| **Row / Col**      |      0–5, 0–4       | physical position on the tile                      | keymaps, RGB effects, anything spatial |
| **Mux + Channel**  |      0–1, 0–14      | **copper** - routing convenience, *not* grid order | the scan loop only                     |
| **LED**            |        0–29         | **copper** - it's the SPI chain position           | the RGB frame only                     |
| **Tile Row / Col** | assigned at runtime | master, BFS from (0,0) after discovery             | where a tile sits in the array         |

Mux/channel and LED aren't choices - the first is which ADC pin plus which select address, the second is a shift-register position, so frame slot *N* is physically LED *N*.

## Rules

1. Top is the side with a USB that doesnt have the boot/reset buttons on it (rest can be infured)
2. **0-based everywhere in firmware.** ~~The exception is the LEDs cuz i was dumb and missed that the LEDs started at 1 not 0, and its too late to change the silkscreen~~ idk why but no references got put on the silkscreen so that no longer applies.
3. **Origin is top-left.** Row 0 is the row against the top, Col 0 is left

## Local key is grid order

`local_key = row × 5 + col`, so key 0 is top-left and key 29 is bottom-right.

## Effects

Calibration follows `local_key`, not array position

Per-key min/max belongs to a specific switch, magnet and sensor - so it's a property of local tile - key 17, not of "the key at position (2,3)". (this avoids problems when 'master layout array' comes into play)

### Row-Col or Col-Row

`R2C3` or `row 2, col 3` not `(2,3)` - cuz i keep swaping around row,col/col,row



---
Back to [firmware index](index.md) · [truth table](truth-table.md) · [pin map](pin-map.md)
