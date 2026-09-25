# Intertile Communication

## Identify
The modules need to communicate with each other, but how?

### Info That Needs to Be Sent out from Master
- Keypress actuation point
- RGB instructions
- Firmware updates
- PD gates
- Tile coordinate/slot assignment
- Frame sync
- RGB
- "release your keys" / reset

### Data That Needs to Be Sent to Master
- Key presses
- Where/how many tiles there are
- PD negotiation from non master tiles
- Submodules what and where
- Errors/Faults
- PD Edge switch states
- 'I'm alive ദ്ദി(˵ •̀ ᴗ - ˵ ) ✧'

### Bidirectional Data
- Submodule data
- Power Delivery partitioning

### Relevant constraints
- Sub-1 ms latency
- 1000Hz polling rate (can have others, but must support 1000Hz)
- N-key rollover
- Per-key RGB

### What has to be managed/controlled
- USB-HID stack
- Inter-tile UART (PIO)
- Submodule UART (hardware+PIO)
- Power delivery PHY I2C
- Mux select+ ADC input

### Hardware locked stuff
- 4 full-duplex links per tile
- garbage frames on hot unplug
- 1000 Hz is max rp2350 usb speed



---

## Brainstorm

### latency

Originally (in [comms](../design-choices/comms.md#the-latency-problem)) i estimated latency with per-hop wire time times number of hops: *"0.12ms/hop × 4 hops = 0.48ms"* now that the hardware is finalized it is no longer accurate.

The thing is that it all depends on the tile layout. by design, a tile (specifically master) can receive data from all 4 (only 3 if master because of the usb) at the same time, so for larger arrays this can be taken advantage of via the master creating a 'data-flow map' on enumeration. it should avoid merges unless absolutely necessary as that has costs. 

But, most of that doesn't matter because like 99% of the time, layouts will be 1 row so there is no fancy path to make, and no merges

### data flow path thingy

so like idk im just a girll™

i can think harder about that later

### how should communication happen (╭ರ_•́) (scheduling)

|                | how it works                                                      | why not                                   |
| -------------- | ----------------------------------------------------------------- | ----------------------------------------- |
| **Polled**     | master asks, tile answers                                         | simple, but slow and ineffesent           |
| **Autonomous** | just say stuff whenever                                           | not consistant, needs 'store and forward' |
| **Scheduled**  | master assigns each tile a window where it gets a 'talking stick' | needs 'global' clock of some sort         |


### how is data sent to master? (upstream)

Ive been thinking in the back of my head from the start that if we do some sort of 'frame' or 'window' type thing then that would avoid the problem of colliding data and that makes stuff a lot faster if we don't need to worry about it.

options: 
- relay each received bit from down stream as it arrives (when not in its own 'window')
- relay each byte as it is received (can count bytes for timer)
- 'store and forward' aka relay a 'frame' at a time


### how is data sent to non-master(s) (down stream)
This data is probably not very time sensitive, it can afford 'store and forward', i see a few ways of doing it:
- Master puts address at front, and any data received from master is read by each tile on the way and if 'this message isn't for me' then it will continue down the path, if 'this message is for me' then it doesn't continue.
- Same as above but sent to every tile every time
- Same frame/window method as 'send to master' data, but this time it's the other way and would have to be sent to every tile
- Frame method, but only relay frames that need to be relayed further

### What data is sent upstream every frame?

| Data                 | priority | notes                                                                                             |
| -------------------- | -------- | ------------------------------------------------------------------------------------------------- |
| Key presses          | 10       | normalized, digital                                                                               |
| per key analog value | 7        | normalized                                                                                        |
| tile address         | 6        | assigned during enumeration                                                                       |
| general status       | 8        | 'I'm alive ദ്ദി(˵ •̀ ᴗ - ˵ ) ✧' any (power) sense info, firmware version, pd gate(s) status, etc. |
| submodule info       | 9        | like input devices and stuff (ex. rotery encoder)                                                 |
| envelope             |          |                                                                                                   |

### What baud speed?
depends on what data needs to be sent:
the raw size of data being sent upstream

| data           |  bytes |                                 |
| -------------- | -----: | ------------------------------- |
| key presses    |      4 | 30 bits                         |
| per key analog |     45 | 30 × 12-bit, packed             |
| tile address   |      0 | slot position is the address    |
| general status |      3 | one rotating register per frame |
| submodule info |     13 | length byte + payload           |
| envelope       |      5 | sync, flags, counter, CRC16     |
| **total**      | **70** | against ~140 B/tile available   |

rapid trigger is run locally per tile so it can scan way faster than 1kHz and run debounce stuff or whatever.

so 70 B/tile, 72 with a bit of buffer.

**4 × 72 = 288 B per period.**

PIO divides the 150MHz system clock by whole cycles per bit, and it has to be whole (a fractional divider jitters the bit period by a full system clock), so my options are discrete:

| cycles/bit |    baud | 288 B takes |
| ---------: | ------: | ----------: |
|          8 | 18.75 M |      154 µs |
|         16 | 9.375 M |      307 µs |
|         32 | 4.688 M |      614 µs |
I want to pick the fastest stable option (for scalability)

uart trace lengths(2D mm)

|        |     Tx |     Rx |
| ------ | -----: | -----: |
| top    |  38.48 |  40.93 |
| right  | 129.43 | 158.73 |
| bottom |  92.92 | 107.27 |
| left   |  52.13 |  60.13 |
The longest path is also the 99% use case path. *Yippee.*


## Select

### upstream data

i do some ~~meth~~ maths for these:

|          |     per hop | window, 5 tiles |
| -------- | ----------: | --------------: |
| bit      |       ~7 ns |          307 µs |
| **byte** | **1.07 µs** |      **311 µs** |
| frame    |       77 µs |          614 µs |
byte gains clean regenerated data every hop, byte counting (free clock/sync) and only loses ~4µs vs bit relaying and gains that back with (probably) more reliable data stream.
frame was never really a option cuz it sucks and is slow and yeah.
### scheduling

- Polled
	round trip per tile, scales horribly
- Autonomous
	better, but would requires storing frames for collisions
- Scheduled
	needs global clock, but best latency and efficient

Autonomous gone cuz it needs storing (already shot down), polled.... just *bleh*. 
The only real option **Scheduled**

### downstream

- address, consume data
	don't send more unnecessary data downstream
- address, relay every time
	one path for every frame, less to get wrong
- window method, reversed
	every tile all the data, specific frames for specific tiles, (probably have a all frame)
- only relay frames that need it
	doent really gain much

unlike what i originally thought relaying further doesn't really cost anything (all pio), so its between address, and frames. since we are already going to have to make a scheduler might as well make both the same.
**Scheduled frames**

### baud rate

i want the highest one that is consistent/stable, which is a different question.

|             |        bit | sample at |           early margin |
| ----------- | ---------: | --------: | ---------------------: |
| 18.75 M     |      53 ns |     27 ns |     17 ns = 2.5 cycles |
| **9.375 M** | **107 ns** | **53 ns** | **43 ns = 6.5 cycles** |
| 4.688 M     |     213 ns |    107 ns |    97 ns = 14.5 cycles |

18.75 saves 153 µs of window out of 1000 vs 9.375, which is basically irrelevant, and USB caps at 1kHz so there's not much to gain. 

I can probably test 18.75 later, 9.375 is the safe pick.

**9.375 Mbaud, 16 cycles/bit.**

