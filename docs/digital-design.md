# Digital / MCU design — 2026-07-04

ESP32-S3 module circuit, strapping, capture-clocking details, sensor bus and
firmware-facing hardware decisions. Companion to pinmap-parts.md (GPIO map)
and afe-design.md (control shift registers).

## Module circuit (ESP32-S3-WROOM-1-N16)

| Item | Value / connection |
|---|---|
| 3V3 | 3.3D, 10 µF + 3× 0.1 µF at pins; WiFi bursts need low ESL path to the buck |
| EN | 10 k → 3.3D + 1 µF → GND (RC ≈ 10 ms), test pad; no button — EN on the program header |
| GPIO0 | 10 k pullup footprint (DNP), test pad on the program header (boot strap) |
| Antenna | module keepout per datasheet: no copper any layer under antenna, module overhangs board edge; enclosure is printed plastic — fine at masthead |

**Programming/debug:** two headers, both reachable with the enclosure open:

1. **USB header** (GPIO19/20 + 5 V + GND, 4-pin JST-SH): native USB-Serial-JTAG
   — flashing, console, JTAG, all through one connector. Primary bench access.
   A USB-C receptacle is *not* placed — this is a sealed masthead unit; bench
   access happens with the board out.
2. **UART0 header** (43/44 + EN + GPIO0 + GND): ROM-loader fallback if
   firmware wedges native USB.

Day-one OTA (README strategy) makes both of these last-resort paths.

## Strapping pins — explicit treatment

| GPIO | Strap function | Treatment here | Safe? |
|---|---|---|---|
| 0 | boot mode | spare; header pad + DNP pullup; may be used later as input-only (e.g. Vin ADC) | ✔ |
| 3 | JTAG source (only if eFuse JTAG_SEL burned) | 10 k pullup for SR /OE | ✔ eFuse default ignores it |
| 45 | VDD_SPI voltage | **test pad only, never pulled high** (high = 1.8 V flash rail = brick until repowered) | ✔ |
| 46 | boot mode (with 0) | test pad only, internal pulldown | ✔ |

## Capture clocking (DVP details pinned down)

- **ADC clock:** LEDC on GPIO14, 80 MHz APB / 20 = **4.000 MHz, integer
  divisor only** — LEDC's fractional divider dithers cycle lengths; harmless
  for SNR at 40 kHz but pointlessly smears the sampling grid. Integer divide
  is exact and jitter-free.
- **PCLK loopback:** GPIO14 → GPIO13 as a short PCB trace (not "external
  wire" as an afterthought — route it, ~33 Ω source series at GPIO14 feeding
  both ADC CLK and GPIO13).
- **Edge discipline:** AD9235 updates data on the rising CLK edge (tPD a few
  ns). Capture on the **falling** PCLK edge — LCD_CAM has a polarity bit
  (`cam_clk_inv`/sample-edge config), so both options exist in software;
  bring-up verifies with a ramp test (feed VMID sweep, check for missing
  codes / bit skew).
- **Bus width:** LCD_CAM camera mode is 8- or 16-bit. Use **16-bit mode with
  D12–D15 mapped to constant-0 via the GPIO matrix** (the matrix can route
  logic 0/1 to any input signal) — no physical pins wasted, and the 9.6 KB /
  1.2 ms window figure already assumed 2 bytes/sample. ✔ consistent.
- **VSYNC (GPIO12):** LCD_CAM needs a frame signal. Plan A: MCU drives
  GPIO12 itself from firmware to open each 4800-sample frame (pin-to-pin on
  the PCB, zero extra hardware). Plan B if the peripheral allows: internal
  constant + `cam_vsync_filter` disabled. Pin stays reserved either way.
- **Pipeline latency:** 7 clocks = 1.75 µs constant; swallowed by the TX
  marker t₀ reference, as designed.

## Control-bus behavior (recap + one addition)

SPI (35/36) shared by MCP6S91 (CS 37) and 74AHC595 chain (RCLK 38) — clean,
see review §1. Addition: **PGA SPI writes are forbidden between TX and end of
capture** (firmware rule) — MCP6S91 gain steps glitch the analog path; all
gain/mux/driver reconfiguration happens in the inter-slot gap (~0.3 ms),
which is also when the mux is pre-switched (review F1).

## I2C bus (GPIO1 SDA / GPIO2 SCL)

| Device | Addr | Rate | Notes |
|---|---|---|---|
| ISM330DHCX | 0x6A | 400 kHz | INT1 → GPIO41; FIFO + timestamping for mast-motion compensation |
| MMC5983MA | 0x30 | 400 kHz | periodic SET/RESET degauss in firmware; ≥ 3 cm from LED pair |
| SHT41 | 0x44 | 400 kHz | on a thermally isolated stub |

- Pullups 4.7 k to 3.3D. No address conflicts. All three tolerate 400 kHz.
- **SHT41 stub:** PCB peninsula with milled slots (thermal isolation from
  ESP32/regulators), exposed to airflow through a shaded, rain-protected
  labyrinth in the enclosure; **no conformal coat on the sensor**, coat
  boundary marked on silkscreen.
- IMU orientation: axes silkscreened; mount flat, X forward — one fixed
  rotation constant in firmware.

## GPS (optional stuff-option)

SAM-M10Q: 3.3D, V_BCKP → 3.3D via diode + 100 µF (warm start across short
power cuts; no battery in a sealed hot enclosure), UART1 on 39/40 at 38400.
Patch antenna needs sky view — placement conflict with the LED ring is an
enclosure-phase item (pinmap open list). All parts DNP-able as a group.

## Firmware platform decisions (hardware-relevant)

- **Flash map (16 MB):** factory + OTA0 + OTA1 (~2.5 MB each) + large
  LittleFS partition for raw-capture recordings and calibration LUTs.
  OTA with rollback (app must mark itself valid after a successful WiFi
  connect + one valid measurement frame, else auto-rollback).
- **Watchdogs:** task WDT on the measurement task and the Signal K sender;
  light PWM is configured before WiFi init so a wedged radio never darkens
  the legally required light.
- **Debug pipe (first-class, per README):** UDP raw-capture streamer
  (binary, one 9.6 KB window per datagram batch), WiFi log console, OTA —
  written before any DSP work, developed against **simulated capture
  buffers** (synthesized echoes: measured-Q ring-up model + noise + marker)
  while boards are in production.
- **Boot order:** light ON → safe-state SRs verified → WiFi/OTA → sensors →
  measurement loop. The mast light must not depend on anything after step 1.

## Digital BOM adds (beyond pinmap-parts.md)

| Item | Part | Notes |
|---|---|---|
| Program headers | JST-SH 4-pin (USB), 1×6 2.54 mm (UART0/EN/IO0) | |
| I2C pullups | 4.7 k ×2 | |
| EN RC | 10 k + 1 µF | |
| Vin telemetry divider (optional) | 100 k / 10 k + 100 nF → GPIO0 | DNP by default; GPIO0 input-safe after boot |
