# Datasheet research (auto-generated)

These pages are **not written in my voice** and are **not design decisions**. Each one was produced by an agent that was given:

- the project's power architecture and constraints,
- the role a given chip has to play,
- the datasheet,

and *deliberately not shown the current schematic*. So each is an independent "here's what the datasheet says the right way to do this is," written without knowing what I actually drew.

The point is to **diff them against the as-built design** and see where they disagree. Where they agree, that's a cross-check. Where they disagree, that's either a bug in my schematic or a thing the agent missed - and either way it's worth a look before fab.

Values here are *proposals*, not decisions. Anything I adopt gets written up properly in [schematic-design](../schematic-design/index.md) with my own reasoning, and the part lands in [chips](../chips.md).

**Caveat added after these were written:** the agents were briefed that i was hand-assembling on a hotplate with low-temp bismuth paste. **that's no longer true - this is going to JLC assembled.** so anywhere one of these pages rejects a package or a part on *solderability* grounds, that reasoning is void (the sourcing, cost and PCB-design-rule arguments still stand). The affected calls are the MAX40203 WLP package in [ldo-and-ideal-diode](ldo-and-ideal-diode.md) and the reflow-profile discussion in [sk9822-and-level-shifter](sk9822-and-level-shifter.md). Background in the [hall-effect re-revisit](../design-choices/hall-effect-sensors.md#re-revisit-im-not-assembling-this-myself-anymore).

**There is deliberately no RP2350B page here.** That one's the centrepiece of the whole design and the reasoning *is* the project, so i'm doing it myself rather than reading someone else's summary of it. Its working goes in [mcu](../schematic-design/mcu.md) like everything else i actually decide.

---
Back to [main index](../index.md)
