# Switches
the... keyboard switches ╮(─ω─)╭

## Identify
I need to make actual working switches

How? 
Void switches (decided on [here](../design-choices/switches.md))

so really the step is
## Implement
but really it is 
## Repeat
cuz i need to figure out the best way to go about this.

### Previous experience/tests
I have tryed to print good void switches a number of times in the past, and only occasionally actually made *good* ones. i need to dial in the 'settings' for printing these

### Starting point
riskable's low-profile 'defaults' are these:
- N52 4×1mm magnets, no levitator, ~2mm travel
- 8mm tall switch
- 2mm tall keycap stem
- 0.2mm (1 layer) wall between the magnets is enough, some will fail tho (printing or tearing it when inserting the magnet)

![riskable's 8mm low-profile Void Switch](../media/riskable-8mm-void-switch.png)
(Credit [Riskable](https://github.com/riskable))

### Height budget
In some testing ive done (undocumented) i came up with this:

| Part                  | mm        |
| --------------------- | --------- |
| Keycap past stem      | 2.25      |
| Void switch           | 7.0       |
| Hall sensor           | 1.4       |
| PCB                   | 1.6       |
| Bottom case           | 1.0       |
| **Subtotal**          | **13.25** |
| Stem travel (~2mm)    | +2        |
| **Total**             | **15.25** |

Don't remember the settings tho, and i am sure they weren't 'optimal' anyway so doing *this* is better

## Identify
What 'tuneable' parameters are there?
What testing method?

### Variables
#### Printer
##### Physical
- Printer type (FDM or resin)
- Printer model
- Nozzle size
- Bed surface

##### Slicer settings
- Tune filament first
- Layer height
- Cooling / fan speed
- Print speed
- Dimensional compensation

##### Material
- Filament (plastic) type
- Filament brand
- Filament dryness
- Color (and opacity)
- Lubricant

#### Switch generation parameters
(independent/dependent relative other variables besides 'does it work well')
##### Independent
- Magnet size
- Magnet polarity and orientation
- Travel distance
- Overall switch height (low profile target)

##### Mostly independent
- Stem size
- Stem tolerance

##### Depends on other parts
- PCB mounting and retention (need to do [chassis](chassis.md))
- Keycap interface (depends on [keycaps](keycaps.md))

## Brainstorm
how do i test each parameter, and what parameters are 'base' ones

### General method
- Change one variable at a time, print a batch
- Choose order that means the base is stable
- *Document* the results (crazy, i know)

#### What 'good' means
- Moves smoothly, no binding
- Returns ***every*** time
- ~80%+ of a 'batch' turns out 'good'

#### Printer
| Parameter            | What do i have?                                                                                                 |
| -------------------- | --------------------------------------------------------------------------------------------------------------- |
| Printer type / model | Voron 2.4 350mm$^3$, Anycubic photon mono x2 (i think thats the name), flash-forge AD5 (not mine but i can use) |
| Nozzle size          | (e3d revo nozzels for voron) 0.6mm 0.4mm 0.25mm 0.15mm                                                          |
| Bed surface          | smooth and textured (i like smooth better ⁽ ⁽ ( ⏑‿⏑ ) )                                                         |

#### Slicer settings
| Parameter                | Base?    | How to test                                                                                |
| ------------------------ | -------- | ------------------------------------------------------------------------------------------ |
| Filament tuning          | Yes      | temp tower, flow, retraction                                                               |
| Layer height             | yes      | batch at a few heights, check stem fit and the wall                                        |
| Cooling / fan speed      | no       | batch, look for warping and layer bonding                                                  |
| Print speed              | no       | batch, look for dimensional error                                                          |
| Dimensional compensation | a little | print stem/housing test pieces, measure with calipers, adjust until the clearance is right |

#### Material
| Parameter           | Base?    | How to test                                         |
| ------------------- | -------- | --------------------------------------------------- |
| Filament type       | Yes      | same switch in each type, compare friction and wear |
| Filament brand      | a little | same as above, lower priority                       |
| Filament dryness    | a little | dry vs not dry, same settings                       |
| Color (and opacity) | ehhh     | check how the light looks through it                |
| Lubricant           | no       | with vs without, compare feel                       |

#### Switch generation parameters
| Parameter                     | Base?             | How to test                                                        |
| ----------------------------- | ----------------- | ------------------------------------------------------------------ |
| Magnet size                   | yes               | one of each in the same switch, compare force and ADC range        |
| Travel distance               | mostly, ~2mm      | only change if the signal or feel needs it                         |
| Overall height                | mostly, 15mm goal | check against the height budget                                    |
| Stem size                     | not really        | print a few sizes, keep the smallest that still works              |
| Stem tolerance                | no                | print a few clearances, pick the one with no wobble and no binding |


### Test plans
(I excluded variable that have such a minute effect or are basically impossable to get wrong)

### Plan A: one variable at a time
Slow and careful, the base gets stable before anything else is touched.

#### Phase 1: get the plastic working (no magnets, no sensor)
1. Filament type
2. Printer + nozzle
3. Layer height
#### Phase 2: baseline switch
4. Stem tolerance
5. Stem size
6. Magnet size
7. Other random settings (in the scad generation)
#### Phase 3: other stuff
8. Travel
9. Cooling and print speed
10. Lubricant

### Plan B: batch plates
Print a bunch of variants on one plate (a few clearances × a couple of layer heights), then look at all of them at once.
1. Do filament type + filament tuning first (same as plan A, these affect everything)
2. Plate 1: stem tolerance × layer height, full switch without magnets
3. Pick the best combos, then plate 2: dimensional compensation × print speed
4. Add the magnets to the best few, check feel and ADC
5. Magnet size, stem size, and the Phase 3 stuff one at a time like plan A

Faster (fewer print sessions), but harder to tell *why* something is good since two things changed at once.

### Plan C: 'i think this should work', then tune
1. Pick the settings i think will work from what i already know, and write them down
2. Print a batch of 10 and see how it does
3. Look at how/why the bad ones are bad
4. Change settings targeting the failure
5. Repeat

Quickest way to a working switch, and it uses what i already know, but the first guess could be way off, it can stall on a failure that has several causes, and the settings i end up with might not be optimal.


## Select

| Criteria                         | Weight | A: One at a time | B: Batch plates | C: Educated guess, fix what breaks |
| -------------------------------- | :----: | :--------------: | :-------------: | :--------------------------------: |
| Time to a working switch         |   6    |        2         |        6        |                 8                  |
| Know *why* it works              |   5    |        9         |        4        |                 5                  |
| Settings end up close to optimal |   5    |        8         |        6        |                 4                  |
| Easy to document                 |   4    |        8         |        5        |                 6                  |
| **Weighted Total**               |        |       129        |       106       |                117                 |

Winner: A. One at a time

## Implement

### Phase 1
#### 1. Filament type
In my past attempts i have tried PLA, PETG, ASA, and ABS. PETG by far worked the best, and is also the one suggested by riskable (crazy that the one suggested is the one that works best) 
therefore i am just gonna forgo any new testing because i think it has already been tested thoroughly enough.

#### 2. Printer + Nozzle
my options

| Printer                 | Nozzles           | Notes                   |
| ----------------------- | ----------------- | ----------------------- |
| Voron 2.4               | 0.6,0.4,0.25,0.15 | Mine, works well.       |
| Flashforge AD5          | idk               | Not mine, but has a MMU |
| Anycubic Photon mono X2 | N/A               | Messy                   |
Really the only real option is my Voron.
Nozzle size is the question:
- 0.6mm 
	not a chance
- 0.4mm
	Riskable uses this
- 0.25mm
	haven't tested much
- 0.15mm
	gotten quite a bit of luck with it in the past

##### Test Method
- Tune PA per nozzle first
- Use 'default' switch parameters
- Print like 5 with each nozzle size
- Decide which one is best (feel+stickiness)
- Maybe retest later down the road when other things are tuned


#### 3. Layer height
This depends a lot on the nozzle size, and riskable said something about 'match to the stem thickness' and it is affected by the stem tolerance.

##### Test Method
- uh ngl this one is so subjective that it should really be later in the list
- why not move it then? idk, im just a girl (╥﹏╥)

### Phase 2

#### 4. Stem Tolerance

##### Test Method
- Print a 'gradient' of tolerances (with multiple of the same tolerance)
- Test which ones are good

#### 5-7 

##### Test Method
- Really the same thing: One Parameter, multiple values

### Phase 3

#### 8-10
- More of the same, this is a lot more personal preference based so it can be changed by other things


## Test
Need to do that at some point, is that point now? idk, like i said, i'm just a girl™