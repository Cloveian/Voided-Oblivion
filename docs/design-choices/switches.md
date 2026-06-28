# Switches

## Identify
I need to decide on what switches i am going to use

### Relevant constraints/nice to haves:
**Must haves**
- Sub-1 ms latency
- Ortho-linear layout
- N-key rollover
- Easily replaceable switches

**Nice to haves**
- Per-key RGB (under-glow)
- Low profile

**Nice to have, but slightly far fetched (harder to achieve)**
- Have submodules
## Brainstorm

### Options:

Choc switches (Low profile)

MX Switches

Analog switches (premade)

[Void switches](https://github.com/riskable/void_switch)

Custom analog switches (hall effect)

## Select

| Criteria                      | Weight | A: Choc | B: MX | C: Premade Hall | D: Void |   E: Custom Hall   |
| ----------------------------- | :----: | :-----: | :---: | :-------------: | :-----: | :----------------: |
| Responsiveness                |   6    |    5    |   5   |        7        |    7    |         7          |
| Versatility                   |   5    |    5    |   5   |        6        |    6    |         6          |
| Easily replaceable (hotswap)  |   7    |    5    |   5   |        5        |    4    | ?(5 to be neutral) |
| Low profile                   |   6    |    7    |   5   |        5        |    4    |         8          |
| Per-key RGB compat            |   5    |    5    |   5   |        5        |    8    |         8          |
| Build time / risk             |   4    |    9    |   9   |        9        |    6    |         3          |
| Cost                          |   4    |    7    |   6   |        2        |    8    |         7          |
| Want-it / feel / "made by me" |   6    |    5    |   2   |        6        |    7    |         8          |
| **Weighted Total**            |        |   251   |  217  |       242       |   262   |        283         |
So the winner is **E: a custom hall effect switch**: a low-profile, modified [Void switch](https://github.com/riskable/void_switch) (analog hall effect). It lands low profile + analog + per-key RGB + "made by me", and the build risk is lower because i have contact with [riskable](https://github.com/riskable) (the Void Switch creator).

**Low-profile recipe** (per riskable's suggestion): N52 4×1mm magnets, skip the levitator, keep travel short (~2mm).