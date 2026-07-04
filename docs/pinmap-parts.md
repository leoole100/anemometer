# GPIO map and part selection — updated 2026-07-04

## Module

**ESP32-S3-WROOM-1-N16** (16 MB flash, no PSRAM).
36 GPIOs exposed; special ones: 19/20 (USB), 43/44 (UART0 console), 0/3/45/46 (strapping).

With the transition from a 12-bit parallel DVP ADC to a serial I2S ADC (PCM1808) and the removal of the PGA and GPS modules, the digital pin count is drastically reduced. We have enough free GPIOs to **completely eliminate the control shift registers (74AHC595)** and PGA SPI lines, leaving 19 spare GPIO pins for testing/expansion.

## GPIO map (17 used, 19 spare)

| Pin Type | Function | GPIO | Direction | Boot State / Protection |
|---|---|---|---|---|
| **I2S ADC (PCM1808)** | I2S LRCK (Word Select) | 12 | Output | Low |
| | I2S SCKI (Master Clock) | 13 | Output | Low, via 33 Ω series R |
| | I2S BCK (Bit Clock) | 14 | Output | Low, via 33 Ω series R |
| | I2S DOUT (Data In) | 15 | Input | High-Z |
| **TX Control** | TX PWM_A (40 kHz pulse) | 21 | Output | Low (drives IXDF602 Input) |
| | TX_SEL0 (Transducer 1) | 4 | Output | 100 kΩ pulldown (switch open) |
| | TX_SEL1 (Transducer 2) | 5 | Output | 100 kΩ pulldown (switch open) |
| | TX_SEL2 (Transducer 3) | 6 | Output | 100 kΩ pulldown (switch open) |
| | TX_SEL3 (Transducer 4) | 7 | Output | 100 kΩ pulldown (switch open) |
| **RX Mux** | MUX A0 (74HC4051) | 8 | Output | Low |
| | MUX A1 (74HC4051) | 9 | Output | Low |
| | MUX A2 (74HC4051) | 10 | Output | Low |
| | MUX_EN (74HC4051INH) | 11 | Output | 100 kΩ pulldown (mux disabled) |
| **I2C Bus** | I2C SDA | 1 | Open-drain | 4.7 kΩ pullup |
| | I2C SCL | 2 | Open-drain | 4.7 kΩ pullup |
| | IMU Interrupt (INT1) | 41 | Input | High-Z |
| **Peripherals** | Light PWM (AL8860) | 42 | Output | Low (Default OFF) |
| **Debugging / ROM**| USB D− | 19 | Analog | Native USB-Serial-JTAG |
| | USB D+ | 20 | Analog | Native USB-Serial-JTAG |
| | UART0 TX (Console) | 43 | Output | High |
| | UART0 RX (Console) | 44 | Input | High-Z |
| **Spares / Straps** | GPIO0 (Strap) | 0 | Input | Spare, test pad only |
| | GPIO3 (Strap) | 3 | Input-only | Spare, test pad only |
| | GPIO16 (Spare) | 16 | Input/Output | Spare |
| | GPIO17 (Spare) | 17 | Input/Output | Spare |
| | GPIO18 (Spare) | 18 | Input/Output | Spare |
| | GPIO35 (Spare) | 35 | Input/Output | Spare |
| | GPIO36 (Spare) | 36 | Input/Output | Spare |
| | GPIO37 (Spare) | 37 | Input/Output | Spare |
| | GPIO38 (Spare) | 38 | Input/Output | Spare |
| | GPIO39 (Spare) | 39 | Input/Output | Spare |
| | GPIO40 (Spare) | 40 | Input/Output | Spare |
| | GPIO45 (Strap) | 45 | Input | Test pad only, do not pull high |
| | GPIO46 (Strap) | 46 | Input | Test pad only |
| | GPIO47 (Spare) | 47 | Input/Output | Spare |
| | GPIO48 (Spare) | 48 | Input/Output | Spare |

---

## Part Selection (On-Board SMT)

### Acoustic Chain

*   **Transducers ×4:** Waterproof 40 kHz transducers (User Spares).
*   **TX Driver ×1:** **IXDF602SI** (SOIC-8) dual 2 A gate driver. Powered directly at 12 V.
*   **TX Selector ×1:** **DG412DY** (SOIC-16) quad SPST analog switch. Powered directly at 12 V.
*   **RX Mux ×1:** **74HC4051D** (SOIC-16). Powered at 3.3 V.
*   **Op-Amp:** **TLV9062IDR** ×1 (SOIC-8). Dual 10 MHz rail-to-rail op-amp chip (Stage 1: A1 fixed gain, Stage 2: A2 filter).
*   **I2S ADC:** **PCM1808PWR** (TSSOP-14) 96 kHz 24-bit stereo ADC.
*   **Clamps:** BAV99 ×4 (SOT-23).

### Power Section

*   **3.3 V Digital Buck:** AP63203WU-7 (TSOT-26).
*   **3.3 V Analog LDO:** **HT7333-A** (SOT-89).
*   **LED Driver:** AL8860WT-7 (TSOT-25).

### On-Board Sensors & Light

*   **IMU:** **ISM330DHCX** (LGA-14, $2.5 \times 3.0\text{ mm}$, $0.5\text{ mm}$ pitch).
*   **Magnetometer:** **MMC5983MA** (LGA-16, $2.0 \times 2.0\text{ mm}$, $0.5\text{ mm}$ pitch).
*   **Light:** 6× **Cree C503B** (5 mm through-hole white LEDs, radial 90° mounting, potted in clear epoxy).
