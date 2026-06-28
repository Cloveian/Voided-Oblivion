# Decisions to make about what features to include and stuff, ya know?

## Identify
I need to decide on what features I am gonna cram into this, which ones I am going to leave room for, and which ones I am not going to cram into it. (not including things that have already been chosen)

### Relevant constraints/nice to haves:
(Extra relevant are bolded)

#### Must haves
- USB type C wired connectivity
- **Sub-1 ms latency**
- 1000Hz polling rate (can have others, but must support 1000Hz)
- **Portable**
- N-key rollover

#### Nice to haves
- **Per-key RGB (under-glow)**
- **Low profile**
- Bluetooth+USB dongle

#### Nice to have, but harder to achieve
- **Have submodules**
	- Fingerprint sensor
	- Screen
	- Rotary encoders
	- 3.5 mm AUX port for sound output

## Brainstorm
so these are the things i would like to include

**Non-submodule**
- Per-key RGB
- FIDO 2 ??
- Bluetooth

**Submodule** (aka-don't have to design at first)
- Fingerprint sensor
- Screen (OLED, e-ink, etc.)
- Rotary encoder
- Maybe 7-segment display(s)
- 3.5 mm AUX port

**Ideas for submodules that i probably wouldn't personally use, but i am going to make this open source so i should keep in mind that someone might want**
- Track pad
- Track ball
- That one weird mouse nub thingy on a lot of ThinkPads
- Touchscreen
- Analog joystick (i could see myself using this if they were the 2/3DS circle pads)
- Scroll dial (not same a rotary encoder)
- Linear sliders
- NFC reader (i can see myself using this)
- Random-ah sensors (ambient light, gyro, IR sensor, RF sensor, etc.)
- Wireless charger

## Select
I need to figure out what each of these features would require of the main design in order to work, I'ma group them by if they have similar requirements.

### Feature base requirements

#### Main module
- Per-key RGB
	would require good power distribution (probably utilize USB-PD) and a data line from the main MCU
- FIDO 2
	would be 90% firmware/software but would require the MCU to have a secure element of some sort
- Bluetooth
	This probably the most difficult one, it would require the MCU to have bluetooth, or some sort of external chip to add bluetooth capability, or even a second MCU, and it would require a battery

#### Submodules
**Basic** (5V/3.3V power and probably just a Rx and Tx line)(modules have their own MCU)
- Rotary encoder
- 7-segment display
- Track pad
- Track ball
- That one weird mouse nub thingy
- Analog joystick
- Scroll dial
- Linear sliders
- NFC reader
- Random-ah sensors

**Slightly more advanced**
needs higher data bandwidth:
- Screen (OLED, e-ink, etc.)
- Touchscreen
- 3.5 mm AUX port


**Quite advanced**
- Fingerprint sensor
	It would require either a sensor with an MCU that can can do its own public+private key encryption and stuff, or a sensor that will give raw output to the main MCU (that would need a secure element) and the main MCU would need to be powerful enough to process the fingerprint image(s)

**Dumb/I don't care about**
- Wireless charging pad
	It would require an enormous amount of power and I don't want to deal with that 


### What I am actually going to for sure implement
- Per-key RGB
- FIDO 2 (only requirement is an MCU with a secure element)
- Submodule connection (Power+Rx&Tx, good enough for screens)
	Pointing devices would tell the main MCU that they are there, and the MCU would update the HID descriptors
### Probably not
- Bluetooth
	It would be a real commitment, and the main problem is that it would need a battery and that fights with low profile, especially when I am going to have RGB.
- 3.5 mm AUX port
	This would require ***a lot*** more from the submodule ports, and the gain from it isn't really there


