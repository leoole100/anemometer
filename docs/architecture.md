# System architecture

## Overview

```
                       MASTHEAD UNIT
  ┌─────────────────────────────────────────────────┐
  │  4x sealed 40 kHz transducers (down-facing)     │
  │        ↕ burst / echo                           │
  │  Analog front end                               │
  │   TX: boost (10–30 V, fw-adjustable) + H-bridge │
  │   RX: mux → clamp → fixed gain → PGA → AA → ADC │
  │        ↓ SPI DMA (~2 MSPS)                      │
  │  ESP32-S3  ── I2C ──  IMU + compass, SHT41      │
  │   correlation,     ── UART ── GPS (optional)    │
  │   Signal K deltas  ── PWM ──  all-round LED     │
  │        ↓ WiFi (UDP)            ↑ 12 V           │
  └────────┼───────────────────────┼────────────────┘
           ↓                       │ 2-wire up the mast
  ┌─────────────────────────────────────────────────┐
  │  Raspberry Pi        USB-C bank → PD trigger    │
  │  (Signal K server)   (requests 12 V)      DECK  │
  └─────────────────────────────────────────────────┘
```

## Decisions and rationale

### Single MCU: ESP32-S3

Chosen over a two-MCU split (STM32G4 measurement + ESP32 comms). The split wins
when iterating hardware at a bench; with the direct-to-PCB strategy all
iteration is firmware, and a single OTA-updatable target beats two codebases,
an inter-MCU protocol designed blind, and SWD access at the masthead.

Consequences:
- Analog front end is external catalog parts (PGA + SPI ADC) instead of the
  G4's internal op-amps. Fully predictable on paper, fixed at layout — hence
  wide adjustment ranges everywhere.
- Capture start is software-triggered (µs jitter from WiFi/RTOS). Neutralized
  by the **TX marker**: an attenuated copy of the TX burst is summed into the
  RX path, so t=0 and the echo are in the same capture buffer on the same
  clock. Trigger jitter cancels exactly.

### Time-of-flight by waveform correlation

Full received waveform sampled at ~2 MSPS, cross-correlated in firmware.
Envelope for the coarse peak (cycle-slip protection), carrier
phase/interpolation for fine timing. Reciprocal (up/down) measurement makes
wind independent of sound speed; the ToF **sum** yields sound speed →
air temperature for free (cross-checked against SHT41).

### Sensors

- SHT41: outside temperature + humidity. Mount with airflow exposure and sun
  shading, away from self-heating parts (ESP32 radio).
- IMU + magnetometer: attitude (mast motion compensation) and heading.
- GPS: optional, u-blox M10 class, UART.

### Power

- PD trigger (CH224K-class) at mast base requests 12 V from the USB-C bank.
- Thin 2-wire cable up the mast (~250 mA at 12 V, total budget 2–3 W).
- At masthead: bucks to 5 V / 3.3 V, boost 10–30 V (firmware-set) for TX.
- Power-bank auto-shutoff risk: if the bank sleeps under light load, firmware
  emits periodic ~100 ms load pulses. Test with the actual bank.

### Data

- Signal K delta JSON over UDP at 5–10 Hz to the Pi (stock UDP connection).
- Paths: environment.wind.speedApparent / angleApparent,
  environment.outside.temperature / humidity / pressure(if added),
  navigation.attitude, navigation.headingMagnetic, navigation.position.
- Light exposed as a Signal K switch path; defaults ON at power-up so it works
  without the Pi.
- Debug pipe is first-class firmware, written first: raw ADC capture buffers
  streamed over WiFi to a laptop (Python analysis), WiFi log console, OTA.

## De-risking rules for the one-spin board

1. ~60 dB total gain authority, digitally set (transducer sensitivity is the
   biggest unknown).
2. TX drive voltage firmware-adjustable 10–30 V.
3. 0-ohm links between every analog stage; test points on every node.
4. Stuffing options for filter RCs; transducers bought from two vendors.
5. Transducers mounted in rubber grommets (structural crosstalk is the classic
   failure and can't be computed in advance); TX marker lets firmware window
   out residual crosstalk.
6. Acoustic geometry lives in the 3D-printed enclosure, not the PCB —
   geometry iterations are free.
7. Order 5 boards assembled; firmware development starts against simulated
   capture buffers while boards are in production.
