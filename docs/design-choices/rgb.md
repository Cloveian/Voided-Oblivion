# RGB LED's
## Identify
I need to decide on how i am doing the per-key RGB

### Relevant constraints/nice to haves:

#### Must haves
- Portable (bus-powered, so RGB has to live inside the USB power budget)

#### Nice to haves
- Per-key RGB (the feature being designed here)
- Low profile

#### Carried in from other pages
- RGB is the dominant power load (see [power](power.md)), so efficiency + global dimming matter
- Modular tiles: each tile drives its own LEDs locally (the inter-tile bus carries the frame data), so the LED protocol is per-tile and single-wire vs clocked does not affect cross-tile relay

## Brainstorm
RGB LED chips split into two families: single-wire (timing-strict) and two-wire clocked.

**Single-wire** (one data pin, daisy-chained, ~800 kHz timing-critical, no global-brightness field):
- **WS2812B**: ~$0.05-0.09 ubiquitous and cheap, but 5050 (big). Smaller variants: WS2812B-2020, WS2812B-Mini.
- **SK6812 / SK6812MINI-E**: ~$0.09 5V@12mA the keyboard-standard single-wire LED; reverse/south-facing-mount versions exist so it lights up through the switch.

**Two-wire clocked** (clock + data, SPI-like, not timing-critical, fast refresh, has a 5-bit global-brightness field):
- **APA102 / APA102-2020**: the original.
- **SK9822**: ~$0.08 5V@17mA APA102 clone that fixed some timing quirks.
- **SK9822-EC20**: ~$0.09 5V@18mA smaller package, good for low-profile / dense per-key.

### What actually matters here
- **Clocked vs single-wire:** both "refresh" and "forwarding" matter less than expected here: each tile only drives ~30 local LEDs (single-wire is ~1 kHz/frame, already imperceptibly fast), and cross-tile relay is the bus's job, not the LED's. So neither really separates them at this scale.
- **Global brightness** (clocked only): hardware-dims everything at once, which directly helps the RGB power cap (the dominant load). Single-wire has to scale every value in software.
- **Package:** EC20 / 2020 / MINI-E small packages suit low-profile and dense per-key; need reverse-mount to light through the switch.
- **Pins:** single-wire = 1 pin, clocked = 2 (clock + data), fine given the PIO budget.

## Select

The SK6812MINI-E vs SK9822-EC20 call is close and partly depends on the PCB assembly-side decision (reverse-mount through a cutout, board thickness, etc.), so the final pick waits until that's settled. Current lean is SK6812MINI-E (lower current, proven keyboard-standard reverse-mount, 1 data pin); SK9822-EC20 is the fallback if hardware global dimming turns out worth the extra current.

What carries forward either way (RGB is the dominant power load, so [power](power.md) needs these regardless):

**Worst-case current, all LEDs full white, ~30 LEDs/tile:**

| LED          | per LED | per tile (~30) |  @ 5 V  |
| ------------ | :-----: | :------------: | :-----: |
| SK6812MINI-E |  12 mA  |    ~360 mA     | ~7.2 W  |
| SK9822-EC20  |  18 mA  |    ~540 mA     | ~10.8 W |

These are absolute worst case (every key full white); firmware brightness/current capping runs well below this in practice. Either way it confirms RGB dwarfs the ~270 mA/tile sensor load and is the number the power budget has to size around.

If reading by stream of consciousness go back to [index](../index.md)

## Continue
After talking with Riskable, he said that the SK6812MINI-E draw 12 mA ... Always even when at like 1% brightness so that basically entirely rules it out, leaving **SK9822-EC20** as the selected chip.