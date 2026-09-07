# Truth table

What each electrical state actually means. The pin-by-pin reference is in the [pin map](pin-map.md).

## Communication

### UART

| Link                    | Tx  | Rx  | Peripheral     | Notes                            |
| ----------------------- | :-: | :-: | -------------- | -------------------------------- |
| Inter-tile **top**      | 12  | 13  | PIO            | Rx pulled low = neighbour detect |
| Inter-tile **right**    |  6  |  7  | PIO            |                                  |
| Inter-tile **bottom**   |  4  |  5  | PIO            |                                  |
| Inter-tile **left**     | 16  | 17  | PIO            |                                  |
| Top left sub-module     | 22  | 23  | PIO            |                                  |
| Top right sub-module    | 24  | 25  | **UART1** (F2) |                                  |
| Bottom right sub-module | 26  | 27  | PIO            |                                  |
| Bottom left sub-module  | 28  | 29  | **UART0** (F2) |                                  |


### I²C

| Bus  | SDA | SCL | Device                              | Address |
| ---- | :-: | :-: | ----------------------------------- | :-----: |
| I2C0 | 20  | 21  | FUSB302 **PD1** (port 1- portrait)  |  0x22   |
| I2C1 | 30  | 31  | FUSB302 **PD2** (port 2- landscape) |  0x22   |


### SPI

| Bus | SCK | TX | Device | Notes |
| --- | :---: | :---: | --- | --- |
| SPI0 | 34 | 35 | 30× SK9822-EC20, via SN74LVC2T45 | Mode 0, **≤15 MHz** |

### QSPI

| Signal       | GPIO | Notes          |
| ------------ | :--: | -------------- |
| `FLASH CS1n` |  19  | default is low |


## Input

### Digital


|        Purpose        | GPIO | High                             | Low                  |
| :-------------------: | :--: | -------------------------------- | -------------------- |
|     PD1 interrupt     |  15  | idle                             | interrupt pending    |
|     PD2 interrupt     |  18  | idle                             | interrupt pending    |
|      BS+ source       |  36  | clean buck feeding BS+ (post-PD) | VBUS via Q1 (pre-PD) |
| Sub-module rail fault |  37  | OK                               | tripped              |


### Analog

|          Purpose           | GPIO | ADC | Reads                                  |
| :------------------------: | :--: | :-: | -------------------------------------- |
|   Top left sub-module ID   |  42  |  2  | Module class off a divider - 32 levels |
|  Top right sub-module ID   |  43  |  3  |                                        |
| Bottom right sub-module ID |  44  |  4  |                                        |
| Bottom left sub-module ID  |  45  |  5  |                                        |
|         Key mux A          |  40  |  0  | 15 keys, one per select address        |
|         Key mux B          |  41  |  1  | 15 keys                                |


## Output


|         Purpose          | GPIO | High  | Low   | Floating |
| :----------------------: | ---- | ----- | ----- | -------- |
|        PD fet top        | 0    | on    | off   | off      |
|       PD fet right       | 1    | on    | off   | off      |
|      PD fet bottom       | 2    | on    | off   | off      |
|       PD fet left        | 3    | on    | off   | off      |
|   Analog mux select 0    | 8    | bit 1 | bit 0 | n/a      |
|   Analog mux select 1    | 9    | bit 1 | bit 0 | n/a      |
|   Analog mux select 2    | 10   | bit 1 | bit 0 | n/a      |
|   Analog mux select 3    | 11   | bit 1 | bit 0 | n/a      |
|     Noisy 5V enable      | 14   | on    | off   | off      |
| Sub-module power from BS | 32   | on    | off   | off      |
| Sub-module power enable  | 33   | on    | off   | off      |

## Key/LED/Mux table
Row-Col numbers are local for default orientation (portrait, USB port up) (left to right, top to bottom)

| Local Key | Mux | Channel | Row | Col | S0  | S1  | S2  | S3  | LED |
| :-------: | :-: | :-----: | :-: | :-: | :-: | :-: | :-: | :-: | :-: |
|   **0**   |  0  |    5    |  0  |  0  |  1  |  0  |  1  |  0  |  **6**  |
|   **1**   |  0  |    6    |  0  |  1  |  0  |  1  |  1  |  0  |  **7**  |
|   **2**   |  1  |    5    |  0  |  2  |  1  |  0  |  1  |  0  | **18**  |
|   **3**   |  1  |    4    |  0  |  3  |  0  |  0  |  1  |  0  | **19**  |
|   **4**   |  1  |    9    |  0  |  4  |  1  |  0  |  0  |  1  | **30**  |
|   **5**   |  0  |    4    |  1  |  0  |  0  |  0  |  1  |  0  |  **5**  |
|   **6**   |  0  |    7    |  1  |  1  |  1  |  1  |  1  |  0  |  **8**  |
|   **7**   |  1  |    6    |  1  |  2  |  0  |  1  |  1  |  0  | **17**  |
|   **8**   |  1  |    3    |  1  |  3  |  1  |  1  |  0  |  0  | **20**  |
|   **9**   |  1  |   10    |  1  |  4  |  0  |  1  |  0  |  1  | **29**  |
|  **10**   |  0  |    3    |  2  |  0  |  1  |  1  |  0  |  0  |  **4**  |
|  **11**   |  0  |    8    |  2  |  1  |  0  |  0  |  0  |  1  |  **9**  |
|  **12**   |  1  |    7    |  2  |  2  |  1  |  1  |  1  |  0  | **16**  |
|  **13**   |  1  |    8    |  2  |  3  |  0  |  0  |  0  |  1  | **21**  |
|  **14**   |  1  |   11    |  2  |  4  |  1  |  1  |  0  |  1  | **28**  |
|  **15**   |  0  |    2    |  3  |  0  |  0  |  1  |  0  |  0  |  **3**  |
|  **16**   |  0  |   14    |  3  |  1  |  0  |  1  |  1  |  1  | **10**  |
|  **17**   |  0  |    9    |  3  |  2  |  1  |  0  |  0  |  1  | **15**  |
|  **18**   |  1  |    0    |  3  |  3  |  0  |  0  |  0  |  0  | **22**  |
|  **19**   |  1  |   12    |  3  |  4  |  0  |  0  |  1  |  1  | **27**  |
|  **20**   |  0  |    1    |  4  |  0  |  1  |  0  |  0  |  0  |  **2**  |
|  **21**   |  0  |   13    |  4  |  1  |  1  |  0  |  1  |  1  | **11**  |
|  **22**   |  0  |   10    |  4  |  2  |  0  |  1  |  0  |  1  | **14**  |
|  **23**   |  1  |    1    |  4  |  3  |  1  |  0  |  0  |  0  | **23**  |
|  **24**   |  1  |   13    |  4  |  4  |  1  |  0  |  1  |  1  | **26**  |
|  **25**   |  0  |    0    |  5  |  0  |  0  |  0  |  0  |  0  |  **1**  |
|  **26**   |  0  |   12    |  5  |  1  |  0  |  0  |  1  |  1  | **12**  |
|  **27**   |  0  |   11    |  5  |  2  |  1  |  1  |  0  |  1  | **13**  |
|  **28**   |  1  |    2    |  5  |  3  |  0  |  1  |  0  |  0  | **24**  |
|  **29**   |  1  |   14    |  5  |  4  |  0  |  1  |  1  |  1  | **25**  |



---
Back to [firmware index](index.md) · [pin map](pin-map.md)
