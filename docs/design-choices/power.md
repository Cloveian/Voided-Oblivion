# Power management and Inter Module connections
# Identify
I need to decide on how i am going to do power distribution

### Relevant constraints/nice to haves:

#### Must haves
- Portable

#### Nice to haves
- Per-key RGB (under-glow)

#### Nice to have, but harder to achieve
- Have submodules

### Design rules

**80% rule - firmware enforced:** firmware never draws more than 80% of the negotiated PD capacity from any port. This applies to the total allocated power budget across all tiles in a region. Consequences that flow from this:
- A 100W port (20V @ 5A) is treated as 80W (20V @ 4A) available to spend
- Components on the HV path (backfeed diodes, switches) are sized to the 80% current ceiling, not the port's rated max
- RGB brightness caps, submodule power limits, and multi-port load balancing all operate against the 80% budget, not the raw negotiated wattage

### Load budget

| Load               | Worst case (5 V)                                            | Notes                                                                   |
| ------------------ | ----------------------------------------------------------- | ----------------------------------------------------------------------- |
| RGB                | ~360 mA (SK6812) / ~540 mA (SK9822)                         | dominant; full-white, firmware-capped in practice                       |
| Hall sensors       | ~270 mA                                                     | GH39F 9 mA × 30; less if bank-powered                                   |
| RP2350B + misc     | ~50–100 mA                                                  |                                                                         |
| Submodules         | ~500 mA but probably per assembled keyboard, not per module | (will probably implement submodule power useage estimation in firmware) |
| **Per tile total** | ~1.41A (or 0.91 x # of modules +0.5)                        | worst case                                                              |

## Brainstorm

### PD, or not
I am going to need USB-PD to work at full capacity, there is no question. With a power budget of 1.41A per module, i need it to be able to produce 5V@1.75A (per 80% rule) from the 'high voltage' coming from the PD.

**Idea #1 (going with this cuz its one of those 'all the other ideas are kinda stupid and immediately dismiss-able so they aren't even worth writing down'):** design against the worst possible event, a 8x8 module setup (you could probably run doom on the RGB with that). im not planning on designing it to *support* 64 modules, but it would like it to *work*, just be highly discoraged.

64 modules is ~300W max draw, no way to power that off 1 USB-PD port, so it needs to support multiple ports and share. The flow:
PD capability of plugged in port (what voltages and current) → PD Chip → RP2350B → Master RP2350B
Then the master consolidates whatever voltage gives the most power, tells the system to pick that voltage, remembers how many watts it can 'spend', and if there isn't enough power it limits things like RGB. The PD voltage gets its own dedicated line between modules that each module bucks down itself.

What it requires:
- USB-PD chip the MCU can control
- buck converter for 5V from the high voltage line
- a high voltage line running across the whole keyboard

![power-flow](power-flow.canvas)

**Idea #2:** uhhh, no PD, just deal with the lack of power and limit the LEDs.

Going with **Idea #1** because it's a lot more fun to implement and actually lets the keyboard be fully utilized. (Idea #2 isn't really a separate design anyway, it's just what #1 does when a port can't supply enough.)

### The 3 power systems (rails)
Keeping the noisy stuff off the sensitive stuff:
- **Clean rail** (3.3V) for the MCU + hall sensors + MUX, LDO'd off bootstrap so the buck and RGB noise doesn't mess with the analog sensor readings
- **Bootstrap** (5V, always on) so every tile can boot and handshake before high voltage is allowed on
- **Noisy rail** (LED + submodule) off each tile's local buck from the high voltage line, where ripple doesn't matter

### Independent vs linked control
**Linked** (one always on, the other always off):

|              | State 0 | State 1 |
| ------------ | ------- | ------- |
| High voltage | off     | on      |
| Bootstrap    | on      | off     |

**Independent:**

|              | State 0 | State 1 | State 2 | State 3 |
| ------------ | ------- | ------- | ------- | ------- |
| High voltage | off     | on      | off     | on      |
| Bootstrap    | on      | off     | off     | on      |


Going **independent, bootstrap always on**. i was worried about state 3 (both on), but that's only a problem if both 5V sources feed the same net, and they don't: the MCU/clean stuff is on bootstrap and the heavy stuff is on the local buck. So both being on is just the normal running state, not something to avoid.

Reasons i'm not doing the linked/complementary thing (bootstrap off when HV on):
- it breaks hotplug. a new tile needs bootstrap to boot and handshake, but if the system already turned bootstrap off it can't onboard anything new without dropping back to the boot state
- handing the MCU's power from bootstrap over to the local buck mid-run risks a brownout glitch
- the only upside (bootstrap not carrying MCU current once HV is up) only matters at like 64 tiles. at a normal ~6 tiles it's like 0.5A, who cares

### Per-side control
High voltage gets a switch per side (4x). that's what lets me do the partition thing instead of paralleling PD sources (each source owns its own region at its own voltage, boundary switches stay open), plus it gives me per-side fault isolation and the ability to power one neighbor on/off at a time. Each switch is an e-fuse / soft-start, so it also handles inrush into the buck input caps and gives per-tile overcurrent protection for free.

Bootstrap does NOT get per-side switches: it's always on and spans every side because it has to reach everything for the handshake/hotplug. GND also spans everywhere (never partitioned, everything needs a shared reference), and comms spans the whole board too so one master can still run the show even when power is split into regions.

(this adds 4 HV-enable GPIO per tile, noting it for the pin budget)

### Buck setup
The buck has to source from the HV rail, not just the local PD chip, so a tile with no USB port can still make its own 5V off the incoming high voltage. Leaning toward 2 bucks: a small always-on one for bootstrap/clean, and a big gated one for the HV->5V heavy loads.

### Bootstrap: where it comes from + OR'ing
Bootstrap isn't pushed from one place. every powered tile feeds it locally:
- **pre-HV:** the cabled tile's raw VBUS 5V (USB gives 5V by default before any PD negotiation, which is what powers the MCU + PD chip + comms so they can even handshake)
- **post-HV:** every tile makes its own 5V off the HV rail (its clean buck) and ideal-diode OR's that onto the shared bootstrap net (ideal-diode, NOT a plain schottky, the drop is too much on 5V)

So in steady state bootstrap is sourced locally at every tile, not shoved from one buck across the whole array (kills the IR-drop / one-buck-carries-everyone worry).

Hotplug falls right out of this: plug a tile onto a running neighbor and it gets bootstrap 5V straight from that neighbor's local buck (across the bootstrap pin), boots, asks the master for power over comms, master enables HV to it, then it starts making its own 5V and feeding bootstrap too. The edge it mates to has live bootstrap + comms but dead HV (that side's switch is still off), so plugging in is safe.
(this needs comms to handle dynamic join + adjacency detection, not just one-time startup discovery. noting it for the comms page)

### Startup + inrush
The dangerous window is before PD negotiates: i only have ~1.5A at 5V, so if a bunch of tiles all wake at the same instant the inrush can sag/collapse the rail and deadlock before i ever reach negotiation. Fix: per-tile soft-start on the bootstrap input, and keep the pre-PD load to just MCU + comms (no RGB/submodules).

Why per-tile/ripple HV enable does NOT work for startup: the big inrush is the global 5V->20V ramp (one source raising the whole connected rail), which sequencing can't stage, and enabling tiles one-by-one onto an already-live rail just dips it each time. So the move is: pre-connect the tree at 5V (low energy) then ramp once. Per-side enable earns its keep on topology/fault/hotplug, not startup inrush.

Order:
1. plug in, VBUS = 5V (USB default, no negotiation yet)
2. raw 5V gets OR'd onto the bootstrap rail and spans the network, every MCU + comms boots
3. master discovers topology over comms (HV still off)
4. master closes the HV tree switches while everything is still at 5V (low-energy connect)
5. as VBUS ramps past ~6V, the hardware comparator fires: VBUS→bootstrap switch opens AND VBUS connects to the local HV rail simultaneously. the tile's clean buck spins up from HV and feeds bootstrap back almost immediately - hold-up caps only need to cover the microseconds in between. no firmware involvement.
6. negotiate PD up to ~20V. VBUS + the whole HV rail ramp 5V->20V together, PD slew limits the inrush
7. each tile's bucks now make their own 5V from HV (clean buck -> MCU/sensors + bootstrap, big buck -> RGB/submodules)
8. master turns loads on within the negotiated power budget

Multi-port version: step 4 is "enable HV per region from each source", a tree per source instead of one global enable.

### Why HV partitions but bootstrap combines
The thing that makes the whole scheme click:
- **HV = partitioned.** different PD sources negotiate different voltages (20V vs 15V vs whatever). tie those together and the higher one dumps into the lower one, so HV regions have to stay separate (boundary switches open).
- **Bootstrap = combined.** every tile's buck puts out the *same* 5V no matter what its HV input is, so OR'ing them just makes a stronger 5V, there's no voltage mismatch to fight. the bucks normalize everything to 5V, which is exactly what lets bootstrap be one shared net even when HV is chopped into regions.
- **GND = common everywhere.** always. everything needs a shared reference.

The ideal diodes do the rest: highest source conducts, the others stand by, they droop-share if the load grows, and a short on one tile just opens its own diode/e-fuse without dragging down the net. So combining bootstrap isn't a problem, it's a feature: redundancy + local sourcing + per-tile fault isolation.

### Still open (parts + details)
- exact PD chip: needs MCU control, so a FUSB302-class PD PHY, not a fixed-request HUSB238
- buck + ideal-diode controller + e-fuse part numbers
- backfeed/OR'ing protection on each PD input for the multi-port case
- whether to bother rippling the pre-PD bring-up or just lean on per-tile soft-start

### How the power flows (revised)

#### The rails
- **Bootstrap (5V, always on, shared):** powers every MCU + comms, so tiles can boot and handshake before HV exists.
- **HV (negotiated PD voltage, ~20V, per-side switched):** the distributed high-voltage line. partitionable into per-source regions.
- **Clean 3.3V (LDO off the local 5V):** MCU + hall sensors + MUX, kept away from the noisy stuff.
- **GND:** common everywhere.

#### Per tile
- USB-C + PD chip (only actually used on a tile with a cable plugged in)
- hardware comparator watching VBUS: below ~6V → VBUS feeds bootstrap; above ~6V → VBUS disconnects from bootstrap and connects to local HV rail instead, clean buck immediately takes over bootstrap
- small "clean" buck (HV -> 5V) for the clean rail, ideal-diode OR'd onto bootstrap
- big buck (HV -> 5V) for RGB + submodules
- 3.3V LDO off the clean 5V for the MCU + sensors
- 4x per-side HV switches (e-fuse / soft-start)

#### Startup
1. plug in -> VBUS is 5V (USB default, no negotiation yet)
2. raw 5V -> bootstrap net -> every MCU + comms boots
3. master discovers the layout over comms (HV still off)
4. master closes the HV tree switches while everything is still at 5V (low-energy connect)
5. as VBUS ramps past ~6V, the hardware comparator opens the VBUS→bootstrap switch automatically (bootstrap holds on its caps)
6. negotiate PD up to ~20V; the whole HV rail ramps 5V -> 20V, PD slew limits the inrush
7. each tile's bucks now make their own 5V from HV: clean buck -> MCU/sensors (and feeds bootstrap), big buck -> RGB/submodules
8. master turns loads on within the negotiated power budget

#### Steady state
- every tile self-powers off HV through its own bucks
- bootstrap is one shared 5V net fed by every tile's clean buck (ideal-diode OR'd): redundant and locally sourced
- HV is partitioned per PD source, GND is common

#### Hotplug
plug a tile onto a running neighbor -> it gets bootstrap 5V + comms from that neighbor (HV on that edge is still off, so it's safe to mate) -> boots -> asks the master for power -> master enables HV to that side -> the tile self-powers and joins in.

#### The rule that makes it work
HV **partitions** (sources are different voltages, can't mix), bootstrap **combines** (the bucks make them all the same 5V, so OR'ing is fine), GND is **common**.

### What chips are actually needed

#### USB-PD PHY
Needs to: take orders from the RP2350B, negotiate any PD profile (not just a fixed list), and report back what the port can actually supply. The MCU has to be in the loop because the multi-port power budget logic lives in firmware.

**Options:**
- **FUSB302BMPX**: I²C, handles both source and sink roles, RP2350B runs the full PD state machine in firmware. Open-source stacks exist for RP2040 that should port to RP2350 cleanly. QFN-24, ~$0.60 at LCSC.
- **STUSB4500**: has its own NVM and can negotiate without MCU involvement, but that fights with the multi-port budget logic where the MCU *needs* to be in the loop. Also slightly more expensive.
- **CH224K / HUSB238**: fixed-request, no MCU control, already ruled out.


#### Small clean buck (HV → 5V, always on)
Needs to: take HV (5–20V input - has to work from the moment VBUS arrives at 5V, before PD negotiates up) and output a stable 5V for the LDO. Load is just MCU + sensors (~150–300mA). Doesn't need to be ultra-quiet itself since the LDO is downstream. Must run always-on (MCU and comms need it).

**Options:**
- **MP2161GJ-Z** (MPS, 2A, SOT-23-5, ~$0.20 LCSC): cheap, very common, 2A gives headroom on a ≤300mA load, ~1.5 MHz.
- **RT8272AGSP** (Richtek, 2A, SOT-23-5, ~$0.15 LCSC): same class, slightly cheaper. Good sourcing fallback if MP2161 goes out of stock.
- **TPS62130** (TI, 3A, VQFN): more capable but bigger and pricier. Overkill here.


#### Big buck (HV → 5V, gated)
Needs to: handle RGB + submodule load (~2A worst case per tile), with 5–20V input range. Can be off until HV is up and loads are enabled. Noise on this rail doesn't matter.

**Options:**
- **MP2315GJ-Z** (MPS, 3A, SOT-23-8, ~$0.30 LCSC): 3A at low cost, the standard pick for keyboard RGB supplies. Very commonly stocked at LCSC.
- **SY8113ADC** (Silergy, 2A, SOT-23-5, ~$0.15 LCSC): cheaper but 2A ceiling is tight against worst case. Fine only if firmware always caps RGB current below ~1.5A per tile.


#### 3.3V LDO (clean analog rail)
Needs to: be low-noise (this feeds the ADC + hall sensor chain), handle ~200–300mA (RP2350B + bank-powered sensors), be small.

**Options:**
- **XC6220B332MR** (Torex, 300mA, SOT-23-3, ~$0.10 LCSC): low noise, 300mA headroom, tiny. Right fit for a clean analog supply.
- **XC6206P332MR** (Torex, 200mA, SOT-23-3, ~$0.05 LCSC): same family, cheaper, but 200mA is tight if bank-powered sensor current peaks higher than expected. Fine if sensor power-gating is confirmed solid in firmware.
- **AMS1117-3.3** (800mA, SOT-223): works and it's everywhere, but noisier and physically large. Last resort only.


#### Ideal diode (bootstrap OR'ing, one per tile)
Needs to: OR each tile's clean 5V output onto the shared bootstrap net with near-zero forward drop. ~1A per tile is sufficient. Can't be a plain Schottky - 0.3–0.5V drop on a 5V rail is too much.

**Options:**
- **MAX40203** (ADI, integrated ideal diode, 1A, SOT-23-3, ~$0.40 LCSC): no external FET, handles it all internally, tiny. 1A is comfortable at typical clean buck bootstrap contribution per tile.
- **LM74700QDBVRQ1** (TI, ideal diode controller, SOT-23-6) + external P-FET: more flexible and handles higher currents, but doubles part count per tile. Upgrade path if 1A turns out to be tight.
- Schottky: no.


#### VBUS → bootstrap switch + HV connect

This is handled entirely in hardware with a comparator doing double duty. A comparator watches VBUS with a threshold at ~6V (between the 5V pre-negotiation level and the 9V lowest PD voltage). It drives two things simultaneously:
- **VBUS→bootstrap switch opens** - disconnects VBUS from bootstrap before it can climb past 5V
- **VBUS→HV rail connects** - routes VBUS directly onto the local tile's HV rail

The second action is the key improvement: the tile's clean buck immediately sees HV input and starts making 5V, which feeds bootstrap right back. Bootstrap never actually droops - the hold-up caps only need to cover the few microseconds between the comparator firing and the buck spinning up, not any meaningful hold time. This also means a second cable hotplugged into a running tile self-powers that tile's HV rail and restores bootstrap instantly with no firmware involvement.

**Implementation:** one comparator (TLV1805 or similar, SOT-23-5, ~$0.15) watching VBUS against a resistor-divider reference at ~6V drives:
- A P-FET (AO3415 or similar, 20V/4A, SOT-23) for the VBUS→bootstrap path - gate pulled to GND by default (on), comparator pulls high (off)
- An N-FET or dedicated switch for the VBUS→HV path - off by default, comparator turns it on

No MCU GPIO involved.

*Note: AO3415 is 20V rated - fine for the bootstrap switch because VBUS is only at 5V while that switch is conducting. The HV-path switch needs to be rated for the full negotiated voltage (≥24V).*


#### HV per-side switches (×4 per tile)
Needs to: switch the HV rail (~9–20V) between neighboring tiles, provide soft-start to protect downstream buck input caps from inrush, allow OCP (hardware or firmware), and be MCU-enable controlled. Must be rated ≥24V (20V + ~20% margin) and handle ≥3A (covering a region of multiple tiles, not just one tile's local load).

This is the hardest slot - ">24V + ≥3A + soft-start + cheap + small" is awkward in the integrated eFuse market.

**Options:**

| Option | Part | Cost/switch | Pros | Cons |
| --- | --- | --- | --- | --- |
| Integrated eFuse | TPS1663 (TI, 60V, 3.5A, SOIC-8) | ~$1.50 | OCP, soft-start, fault flag built in | $6/tile at ×4, SOIC-8 is large |
| Discrete (P-FET + RC soft-start + sense R) | 30V+ P-FET + passives | ~$0.25 | cheap, small, flexible, 30V+ P-FETs easy to find | no automatic hardware OCP; firmware OCP via ADC instead |


#### Backfeed protection (multi-port case)
The per-side HV switches handle most of this: boundary switches stay open, so two PD sources at different voltages can't fight over the same HV region. The remaining risk is two USB-C ports plugging in on adjacent tiles simultaneously before the MCU has sorted out topology. Fix: a series blocking element on each VBUS→HV path so neither port backfeeds into the other. A Schottky diode is fine here (this is the HV rail, not 5V, so 0.3V drop is irrelevant).


#### Pre-PD bring-up: don't bother rippling
Per-tile soft-start on the bootstrap input covers inrush during the pre-PD 5V window. The pre-PD window is short, and staged bring-up would need extra sequencing logic for marginal gain. Lean on per-tile soft-start, which is already in the design.

## Select

### USB-PD PHY

Hard gate first: must give the MCU full real-time visibility into PD capabilities and control over negotiation. Fixed-request chips (HUSB238, CH224K) cannot feed the multi-port power budget logic and are not scored.

| Criteria | Weight | FUSB302BMPX | STUSB4500 |
| --- | :---: | :---: | :---: |
| MCU control / real-time negotiation | 10 | 10 | 5 |
| Multi-port budget integration | 9 | 9 | 4 |
| Open-source firmware (RP2040 family) | 7 | 9 | 5 |
| Cost | 5 | 8 | 5 |
| LCSC availability | 5 | 8 | 6 |
| Package / PCB area | 3 | 7 | 7 |
| **Weighted total** | | **345** | **197** |

**Winner: FUSB302BMPX (345/390, 88.5%)**

STUSB4500's NVM-based negotiation trades firmware flexibility for standalone simplicity - the wrong trade for a design where the MCU owns power budget decisions dynamically.

---

### Bucks (clean + big)

**Correction from brainstorm:** MP2161 and RT8272 are eliminated before scoring. Both are rated 18V max; at 80% derating that's 14.4V, well below the 20V HV rail. Using either would be an underated design.

The clean buck must start from the comparator threshold (~5.5V) and run through 20V. The big buck is MCU-gated and only enabled post-PD negotiation (≥9V input), but it still needs to be rated for the full 20V rail it sits on.

**BOM note:** TPS54302 (3A) covers both bucks - the clean buck only draws ~300mA but using one part across both simplifies sourcing and removes a unique BOM line.

| Criteria | Weight | TPS54302 (TI, 4.5–28V, 3A) | MP2315 (MPS, 4.5–24V, 3A) | SY8205 (Silergy, 6–36V, 3A) |
| --- | :---: | :---: | :---: | :---: |
| Input voltage rating (≥21V derated) | 10 | 10 | 5 | 10 |
| Min input ≤5.5V (clean buck startup) | 8 | 9 | 9 | 2 |
| Output current | 7 | 9 | 9 | 9 |
| Cost | 7 | 7 | 9 | 8 |
| LCSC availability | 6 | 7 | 9 | 7 |
| Package / footprint | 5 | 8 | 8 | 8 |
| **Weighted total** | | **366** | **342** | **317** |

**Winner: TPS54302 (366/430, 85.1%), both bucks**

MP2315 (79.5%) fails the voltage rating axis - 24V max derated to 19.2V, below the 20V HV rail. SY8205 (73.7%) has excellent voltage headroom (36V) but its 6V minimum input means the clean buck can't reliably start from the ~5.5V comparator threshold.

---

### 3.3V LDO

Hard requirement: low noise. This rail feeds the ADC chain reading the hall sensors. Ripple here corrupts every keypress measurement.

| Criteria | Weight | XC6220B332MR (300mA) | XC6206P332MR (200mA) | AMS1117-3.3 (800mA) |
| --- | :---: | :---: | :---: | :---: |
| Output noise | 10 | 8 | 9 | 3 |
| Current headroom | 8 | 8 | 4 | 10 |
| Package size | 6 | 9 | 9 | 2 |
| Cost | 6 | 7 | 9 | 9 |
| Dropout voltage | 5 | 7 | 8 | 4 |
| LCSC availability | 5 | 7 | 8 | 10 |
| **Weighted total** | | **310** | **310** | **246** |

XC6220 and XC6206 score identically (310/400, 77.5%). AMS1117 is eliminated by noise and package size (246/400, 61.5%).

**Winner: XC6220B332MR**, selected over XC6206 on engineering judgment: the 100mA difference (300mA vs 200mA) is safety margin against uncertainty in the RP2350B + hall sensor current draw before real hardware measurements. The cost delta (~$0.05/tile) is negligible.

**Revisit:** XC6206 becomes the preferred choice if firmware bank-powering of hall sensors is confirmed and hardware measurements show clean buck current stays under 175mA (20% margin on the 200mA ceiling).

---

### Ideal diode (bootstrap OR'ing)

Plain Schottky is disqualified on hard requirements before scoring - a 0.3–0.5V forward drop on a 5V rail cascades through the LDO headroom budget and is not recoverable. Not scored.

| Criteria | Weight | MAX40203 (integrated, 1A) | LM74700 + external PFET |
| --- | :---: | :---: | :---: |
| Near-zero forward drop | 10 | 9 | 9 |
| Integration / part count | 8 | 10 | 4 |
| Current capacity | 7 | 6 | 9 |
| Cost | 7 | 7 | 5 |
| Package size | 6 | 9 | 5 |
| LCSC availability | 5 | 6 | 7 |
| **Weighted total** | | **345** | **285** |

**Winner: MAX40203 (345/430, 80.2%)**

The 1A ceiling is comfortable for the bootstrap OR'ing load at any realistic tile count. LM74700 + PFET wins on current headroom but doubles part count per tile without justification at this load level. Upgrade to LM74700 + PFET if measured bootstrap current on a real multi-tile board approaches 800mA (80% of 1A ceiling).

---

### HV per-side switches (×4 per tile)

| Criteria | Weight | TPS1663 (integrated eFuse) | Discrete (PFET + RC + sense R) |
| --- | :---: | :---: | :---: |
| OCP speed / reliability | 9 | 10 | 5 |
| Soft-start quality | 8 | 9 | 7 |
| Voltage / VGS headroom | 9 | 10 | 7 |
| Cost per switch (×4/tile) | 8 | 2 | 9 |
| PCB footprint | 7 | 4 | 9 |
| Implementation risk | 6 | 9 | 5 |
| **Weighted total** | | **350** | **329** |

The table favors TPS1663 (350/470, 74.5%) over discrete (329/470, 70.0%), but the margin is narrow and the cost axis does not fully reflect the per-keyboard impact: at ×4 per tile, TPS1663 is ~$6/tile vs ~$1/tile discrete. On a 6-tile board that is $36 vs $6 purely for switching - a meaningful fraction of the $250 total budget.

**Going with discrete** as a deliberate engineering tradeoff: the performance gap is real but the cost and area penalty of TPS1663 locks in $6/tile before any measurements exist to justify it. The failure mode (firmware OCP too slow to catch a fault) is diagnosable on real hardware.

## Budget fallback

If the full design BOM comes in way over budget, there's a coherent cheaper version: ditch the per-side HV switches and the bootstrap rail entirely. HV routes directly to each tile's buck converter (TPS54302 handles 4.5–28V, so it runs straight from 5V VBUS before PD even negotiates). No bootstrap needed because the buck IS the bootstrap, every tile self-powers the moment any port gets VBUS.

What you lose:
- **Hotplug safety:** mating a tile onto a live HV rail is uncontrolled inrush, potentially destructive
- **Multi-PD:** two sources at different voltages on the same rail fight each other, stuck to one cable
- **Fault isolation:** overcurrent on one tile can drag down the whole board

Valid design for "assemble flat, plug in one cable, don't touch it while powered." Not for the modular hotplug use case that was a core goal. Keep this as the "it costs HOW much?" escape hatch. The savings are the 4× AO3401A + 4× NPN + MAX40203 ideal diodes per tile.