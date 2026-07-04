# Digital / MCU design — updated 2026-07-04

ESP32-S3 module circuit, strapping, I2S capture-clocking details, sensor bus, and firmware-facing hardware decisions. Companion to pinmap-parts.md (GPIO map) and afe-design.md (control shift registers).

## Module circuit (ESP32-S3-WROOM-1-N16)

| Item | Value / connection |
|---|---|
| 3V3 | 3.3D, 10 µF + 3× 0.1 µF at pins; WiFi bursts need low ESL path to the buck. |
| EN | 10 k → 3.3D + 1 µF → GND (RC ≈ 10 ms), test pad; no button — EN on the program header. |
| GPIO0 | 10 k pullup footprint (DNP), test pad on the program header (boot strap). |
| Antenna | Module keepout per datasheet: no copper any layer under antenna, module overhangs board edge. Enclosure is printed plastic — fine at masthead. |

**Programming/debug** (USB-C receptacle):
1. **USB-C receptacle** (16-pin USB2-only type, e.g. TYPE-C-31-M-12):
   GPIO19/20 → native USB-Serial-JTAG — flashing, console, JTAG through one cable. CC1/CC2 5.1 k pulldowns (UFP), USBLC6-2SC6 ESD array on D±.
   **Bench power for free:** VBUS → SS34 → the protected input node, so the board runs from the laptop alone — electrically identical to the PD 5 V fallback case (everything works, light at reduced headroom). Backfeed into a connected mast cable is blocked by the input-side SS34.
2. **UART0 pads** (43/44 + EN + GPIO0 + GND): ROM-loader fallback if firmware wedges native USB. Pads only, no connector.

---

## Strapping pins — explicit treatment

| GPIO | Strap function | Treatment here | Safe? |
|---|---|---|---|
| 0 | boot mode | spare; header pad + DNP pullup; may be used later as input-only (e.g. Vin ADC) | ✔ |
| 3 | JTAG source | spare, test pad only | ✔ eFuse default ignores it |
| 45 | VDD_SPI voltage | test pad only, never pulled high (high = 1.8 V flash rail = brick) | ✔ |
| 46 | boot mode | test pad only, internal pulldown | ✔ |

---

## Capture clocking (I2S details)

The AD9235 parallel ADC and parallel DVP (LCD_CAM) interface are replaced by a **PCM1808 stereo ADC** connected to the **I2S peripheral** of the ESP32-S3. This uses a standard, natively supported ESP-IDF driver.

- **Clock Generation:** The ESP32-S3 I2S peripheral acts as the master, generating:
  - **MCLK (Master Clock / SCKI pin on PCM1808):** $256 \times F_s = 24.576\text{ MHz}$ (for 96 kHz sample rate). Output on **GPIO13** via a 33 Ω series resistor.
  - **BCK (Bit Clock):** Output on **GPIO14** via a 33 Ω series resistor.
  - **LRCK (Word Select / Left-Right Clock):** Output on **GPIO12** ($96\text{ kHz}$).
- **Serial Data Input (DOUT on PCM1808):** Connected to **GPIO15** (I2S Rx pin).
- **Bit Resolution:** Standard I2S 24-bit slot width. The ESP32-S3 reads this data continuously into DMA buffers.
- **DMA Buffer Size:** 
  - For a 1.2 ms measurement window: $96\text{ kHz} \times 1.2\text{ ms} = 115$ samples.
  - At 4 bytes per sample (32-bit slot), a single capture window requires only **460 bytes** of memory (down from 9.6 KB in the 4 MSPS design). This drastically reduces RAM usage and speeds up cross-correlation computations by ~40×.
- **Group Delay:** The group delay of the PCM1808 delta-sigma modulator is constant and symmetric. Since the forward and reverse directions of each axis use the exact same hardware path, the group delay cancels out perfectly in the reciprocal difference $\Delta t$. For the absolute ToF sum (speed of sound), the delay is constant and calibrated out in firmware.

---

## Control-bus behavior

SPI (35/36) is completely unused (PGA is eliminated). All control pins (mux address, TX select, light PWM) are driven directly by the ESP32-S3's GPIOs.
Reconfiguration of the mux occurs during the inter-slot gap (~0.3 ms).

---

## I2C bus (GPIO1 SDA / GPIO2 SCL)

The two digital motion/heading sensors are integrated directly on the main PCB on the shared I2C bus:

| Device | Addr | Rate | Package | Notes |
|---|---|---|---|---|
| **ISM330DHCX** | 0x6A | 400 kHz | LGA-14 | 6-axis IMU. INT1 → GPIO41. |
| **MMC5983MA** | 0x30 | 400 kHz | LGA-16 | 3-axis Magnetometer. Requires local 10 µF capacitor on CAP pin. |

- Pullups 4.7 k to 3.3D. No address conflicts. Both devices tolerate 400 kHz.
- Environmental sensors (SHT41 and BMP280) and GPS are omitted from the masthead unit to reduce cost and complexity.

---

## Firmware platform decisions

- **Flash map (16 MB):** Factory + OTA0 + OTA1 (~2.5 MB each) + large LittleFS partition. OTA uses rollback if a valid measurement frame is not achieved.
- **Watchdogs:** Task WDT on the measurement task and the Signal K sender. Light PWM is configured before WiFi init.
- **Debug pipe:** UDP raw-capture streamer (streams the 115-sample capture window), WiFi log console, OTA.
- **Boot order:** Light ON → direct GPIO boot states verified → WiFi/OTA → sensors → measurement loop.
