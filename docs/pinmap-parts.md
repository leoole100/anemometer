# GPIO map and part selection

## Module

**ESP32-S3-WROOM-1-N16** (16 MB flash, **no PSRAM** — octal PSRAM would claim
GPIO 35–37, and the correlation buffers are small enough for internal RAM).

36 GPIOs exposed; special ones: 19/20 (USB), 43/44 (UART0 console),
0/3/45/46 (strapping — inputs or boot-tolerant use only).

## GPIO map (33 used, 3 spare)

| Function | GPIO | Notes |
|---|---|---|
| ADC D0–D11 (DVP data) | 4, 5, 6, 7, 15, 16, 17, 18, 8, 9, 10, 11 | inputs, boot-safe |
| DVP PCLK in | 13 | from ADC clock, external wire |
| ADC clock out (LEDC ~4 MHz) | 14 | drives ADC CLK + PCLK loopback |
| DVP VSYNC | 12 | reserved; MCU-generated or tied — confirm during fw bring-up |
| TX PWM_A / PWM_B (40 kHz burst) | 21, 47 | MCPWM/RMT, gated per-driver by AND gates |
| SPI SCK / MOSI | 35, 36 | shared: PGA + shift registers |
| PGA CS | 37 | MCP6S91 |
| Shift-register latch | 38 | 2× 74AHC595 daisy-chained |
| I2C SDA / SCL | 1, 2 | IMU, mag, SHT41 |
| IMU interrupt | 41 | |
| GPS UART1 TX / RX | 39, 40 | |
| Light PWM | 42 | AL8860 DIM input |
| Boost Vb adjust (LEDC PWM) | 48 | filtered into TPS61170 FB node |
| USB D− / D+ | 19, 20 | flashing/debug fallback |
| UART0 TX / RX (console) | 43, 44 | debug header |
| Shift-register /OE | 3 | 10 k pullup → outputs Hi-Z at boot (safe-state pulldowns on critical nets) |
| Spare / button / test | 0, 45, 46 | strapping-tolerant uses only |

**Shift-register outputs (16):** U1: DRV_EN0–3 (PWM gating), DRV_nSLP0–3
(**per-driver** sleep — only the transmitting driver is awake; corrected from
a common bit in the 2026-07-04 review (F2): ~0.6 W → ~0.1 W average). U2:
BOOST_EN, GAIN_SW, MUX A0–A2, MUX_EN, 2× spare/TP. Static between
measurement slots, so latency doesn't matter — this is what frees ~8 direct
GPIOs. 74AHC595 ×2; /OE from GPIO3 (pullup) + 100 k pulldowns on DRV_EN0–3,
DRV_nSLP0–3, BOOST_EN, MUX_EN give a defined safe state at boot. The TX-marker
enable bit is gone — the marker is now always-on logic-side injection (see
afe-design.md).

**PWM gating:** PWM_A/B are bused to all four DRV8876s through dual AND gates
per driver (2× 74AHC08); DRV_ENn selects which transducer fires. Non-selected
drivers see IN1=IN2=0 = coast (Hi-Z).

## Part selection

### Acoustic chain (from acoustic-design.md)

| Role | Part |
|---|---|
| Transducers ×4 | Multicomp MCUSD16A40S12RO (+ TCT40-16-class 2nd vendor) |
| TX driver ×4 | DRV8876 (PWM mode, coast = Hi-Z) |
| RX mux | TMUX1108 |
| Op-amps A1–A4 | OPA2365 ×2 (duals): fixed gain, +20 dB stage, AA/ADC driver, VMID buffer |
| Gain-switch | TMUX1101 (bypasses A2 gain leg) |
| PGA | MCP6S91 |
| ADC | AD9235BRUZ-20 (12-bit parallel pipeline, run at 4 MSPS) |
| Logic | 74AHC595 ×2 (control SR), 74AHC08 ×2 (PWM gating) |
| Clamps | BAV99 ×4 (one per transducer input; marker tap and ADC input are within rails by construction) |

All resistor/capacitor values: see [afe-design.md](afe-design.md).

### Power

| Role | Part | Notes |
|---|---|---|
| PD trigger (deck) | CH224K module | requests 12 V at mast base |
| 5 V buck | AP63205 | 3.8–32 Vin, 2 A |
| 3.3 V digital buck | AP63203 | ESP32 WiFi peaks ~500 mA |
| 3.3 VA analog | TPS7A20 LDO from 5 V | low-noise, AFE + ADC ~30 mA |
| TX boost 10–30 V | TPS61170 | from 5 V; PWM into FB for fw-set Vb |
| LED driver | AL8860 | buck from input line, Rsense 0.56 Ω → 180 mA; 1S string keeps working down to the 5 V PD fallback (see power-design.md) |

### Sensors & light

| Role | Part | Notes |
|---|---|---|
| IMU | ISM330DHCX | I2C, marine-grade vibration tolerance |
| Magnetometer | MMC5983MA | I2C; layout: away from LED current loops |
| Temp/humidity | SHT41 | airflow-exposed, sun-shaded stub |
| GPS | u-blox SAM-M10Q | integrated patch antenna — sky-facing under diffuser |
| Light | 6× mid-power white LED ring, **1S6P** + 1 Ω ballast each | ≥ 3 cd all-round target (legal ≈ 1 cd); 0.6 W full scale, PWM-dimmed after photometric cal — see power-design.md |

## Open items

- [x] Legal check (resolved 2026-07-04 → power-design.md): BSO white
      all-round *gewöhnliches Licht*, visibility ≈ 2 km → ≈ 1.0 cd minimum
      (Allard); design target ≥ 3 cd over ±25°, PWM-dim calibrated with a
      lux meter (≥ 0.35 lx at 3 m).
- [x] DVP VSYNC (resolved 2026-07-04 → digital-design.md): plan A is an
      MCU-driven GPIO12 frame pulse, PCB pin-to-pin; pin reserved.
- [x] GPS patch antenna vs. LED ring placement (resolved 2026-07-04 →
      enclosure-design.md): shared top disc under the diffuser dome — LEDs
      at the perimeter firing outward, GPS centered patch-up; no horizontal
      shadow, GPS looks through ~2 mm diffuser plastic.
