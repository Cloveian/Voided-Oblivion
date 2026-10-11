# Naming

Firmware naming conventions

## Vocab
- Central
	What i have been calling the 'master' tile before now
- Peripheral
	The non-Central tiles
- Submodule
	Extra add on boards that come later (ex. rotary encoder, screen, etc.)
- Discovery
	new central tile (first 'boot')
- Rediscovery
	same central tile, plugging tiles (active 'boot')


## Names

There are 3 types of 'names' 
- Local
	never changes, defined by hardware designs
- Regional
	things that only the local tile uses but has to be told 
- Global
	mapped on top of local based on location and orientation of the tiles.

### Local
local mappings in [Key-LED-Mux mapping](truth-table.md#Key-LED-Mux%20table)

| Name              |       Range       | Fixed by                                                | Used for                 |
| ----------------- | :---------------: | ------------------------------------------------------- | ------------------------ |
| **Local key**     |       0–29        | me. L to R, T to B starting at 0                        | anything looking at keys |
| **Mux + Channel** |     0–1, 0–14     | Hardware design (prioritized analog trace lengths)      | scan loop                |
| **LED**           |       0–29        | same number as key it is next to                        | RGB                      |
| **LED chain**     |       0–29        | Hardware design (SPI chain position)                    | static mapping to 'LED'  |
| **Edge**          |   N / E / S / W   | net names -> local mapping                              | links, PD switches       |
| **Corner**        | NW / NE / SE / SW | net names -> local mapping                              | submodules               |
| (USB) **Port**    |        0-1        | Hardware: Port0 = USB1/PD1 (N) and Port1 = USB2/PD2 (W) | PD, Orientation          |

I was a little un-smart when naming the edge/corner nets and didn't think much about orientation, but in firmware i am going to use N/E/S/W for anything that rotates

### Regional

| Name             |            Range            | Set by                                                        | Used for                        |
| ---------------- | :-------------------------: | ------------------------------------------------------------- | ------------------------------- |
| **Flipped**      |   0-1 (normal or flipped)   | neighbour's (with central upstream) Flipped + edge pair       | mapping global arrays and stuff |
| **Side**         | Top / Right / Bottom / Left | Edge + (Orientation + Flipped)                                | PD sectors, links               |
| **Submodule ID** |             0-3             | Corner + (Orientation + Flipped) (tack onto end of Tile Slot) | submodule position              |


### Global

| Name                |                          Range                           | Set by                                                       | Used for                       | Change on rediscovery                  |
| ------------------- | :------------------------------------------------------: | ------------------------------------------------------------ | ------------------------------ | -------------------------------------- |
| **Orientation**     |               0-1 (portrait or landscape)                | Central's host port (and more inferring later)               | mapping like everything        | No (maybe with future inference logic) |
| **Tile Position**   |         \[-128,127\],\[-128,127\] (16bit total)          | Central=0,0. Peripheral=Relative to Central                  | where a tile sits in the array | No                                     |
| (key) **Row / Col** |                 R\[0,1535\],C\[0,1535\]                  | (Minimum)Tile Position + (Orientation + Flipped) + local key | keymaps, RGB effects           | Yes                                    |
| (Tile) **Slot**     | 0-65535(16bits, massively degraded with that many tiles) | Central created data-flow tree                               | frame schedule, wire format    | Yes                                    |






---
Back to [firmware index](index.md) · [truth table](truth-table.md) · [pin map](pin-map.md)
