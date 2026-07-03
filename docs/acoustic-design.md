# Acoustic chain design

## Operating frequency: 40 kHz

- Sealed (waterproof) transducers are widely available at 40 kHz
  (parking-sensor ecosystem); sealed 200 kHz air transducers are rare.
- Atmospheric attenuation ~1.3 dB/m at 40 kHz — negligible over ~13 cm.
  At 200 kHz it would be 5–10 dB/m and sampling gets harder.
- Timing resolution is set by correlation interpolation, not carrier period,
  so the higher frequency buys little. λ = 8.6 mm, period 25 µs.

## Transducer requirements

Sealed transceiver type (single element TX+RX), 14–16 mm aluminum can,
f0 = 40 ± 1 kHz. Check on the candidate datasheets:

| Parameter | Requirement |
|---|---|
| SPL @ 10 Vrms, 30 cm | ≥ 103 dB |
| RX sensitivity | ≥ −90 dB re 1 V/Pa (≥ ~0.3 mV/Pa) |
| Beamwidth (−6 dB) | ≥ 70° |
| Capacitance | note it (~2–3 nF), sets drive current |
| Environment | sealed face, −20…+60 °C |

Selected candidates (July 2026 research):

- **Primary: Multicomp MCUSD16A40S12RO** (Farnell 2362677) — sealed 16 mm
  metal-can transceiver, 40 kHz, −65 dB sensitivity, −30…+85 °C. European
  distribution, real datasheet.
- **Second vendor: TCT40-16 sealed / Taidacent 16 mm waterproof transceiver**
  (generic parking-sensor class, ≥106–117 dB SPL @ 10 V/30 cm across vendors —
  consistent with the 105 dB link-budget assumption).

**Buy from two vendors** — sample variation is the project's biggest unknown;
the gain chain is sized to absorb it.

## Geometry: down-facing bounce path

Four transducers in the upper body face down and inward; sound reflects off a
lower plate to the opposite transducer. Two orthogonal pairs = two horizontal
axes.

```
   T1▼                ▼T2      transducers, faces down (rain-proof)
     \                /
      \              /         leg = 64 mm, tilt 51° from vertical
       \____________/
   ─────────┴┴──────────       reflector plate
   |◄─────  D = 100 ─────►|    (mm)
        h = 40 above plate
```

- D = 100 mm, h = 40 mm → leg 64 mm, total path P = 128 mm, ToF ≈ 373 µs.
- Key property: ToF difference depends only on D, not h:
  Δt = 2·D·v/c² ≈ **1.7 µs per m/s**.
- Vertical wind projects with opposite sign on the two legs → cancels to
  first order. Rain can't sit on the transducer faces.
- D is defined by the printed enclosure and enters firmware as one constant —
  shrinking the device later (D = 70 mm still gives 1.2 µs per m/s) needs no
  PCB change.
- Fallback if the bounce path underperforms: direct-path enclosure variant
  (opposed pairs on pylons), same PCB.

Wind formulas (per axis, t_f/t_r = forward/reverse ToF):

    v = (P² / 2D) · (1/t_f − 1/t_r)        (independent of c)
    c = (P / 2)  · (1/t_f + 1/t_r)         (→ air temperature: T[K] = (c/20.05)²)

At 30 m/s: Δt = 51 µs → correlation search window ±120 samples @ 2 MSPS.
Beam drift at 30 m/s: v/c · P ≈ 11 mm lateral — well inside a 70° beam.

## Link budget

Assuming 105 dB SPL @ 10 Vrms @ 30 cm (typical sealed part):

| Item | dB |
|---|---|
| Source SPL (10 Vrms ref) | 105 |
| Drive at ~13.5 Vrms fundamental (30 Vpp square) | +2.6 |
| Distance 30 cm → 12.8 cm | +7.4 |
| Plate reflection | −2 |
| Alignment/spreading allowance | −3 |
| **SPL at receiver** | **≈ 110 dB ≈ 6.3 Pa** |

At 0.3–5 mV/Pa sensitivity → **2–30 mV** at the receiving transducer.
To reach ~1 V amplitude at the ADC: 30–54 dB needed → **provision 20–70 dB**,
digitally set. Uncertainty band is wide on purpose; that's the point.

## Front end

### TX

- Boost converter 5 V → **Vb = 10–30 V, firmware-adjustable** (PWM/DAC into
  feedback node). Load is trivial: |Z| of 2.5 nF at 40 kHz ≈ 1.6 kΩ.
- **One DRV8876 per transducer (4 chips), PWM mode (PMODE = low)**, transducer
  single-ended on OUT1 (other terminal grounded). Drive = alternate
  IN1/IN2 = (1,0)/(0,1); receive = coast IN1=IN2=0, both outputs true Hi-Z,
  element floats free. Verified: coast without sleep exists in PWM mode; the
  independent half-bridge mode (PMODE = Hi-Z) does NOT clearly offer per-output
  Hi-Z, which is why it's one full chip per transducer. Bridge-tying OUT1/OUT2
  for double drive stays available as a fallback if the link budget
  disappoints (needs differential RX pick-off — only if forced).
- Remaining low-risk check at schematic time: DRV8876 off-state leakage and
  output capacitance loading the floating element (series 10 k + the
  transducer's own 2.5 nF dominate; expect negligible).
- Burst: 8–16 cycles at 40 kHz from MCPWM/RMT; optional anti-phase tail for
  active ring-down damping.
- **TX marker**: ~100:1 divider from one driver output into a spare mux input —
  puts t=0 into every capture buffer (kills trigger jitter, calibrates out
  group delays).

### RX

signal path: transducer → 10 k series + BAV99 clamp → 8:1 mux (TMUX1108,
better leakage/Ron than 74HC4051: 4 transducers, TX marker, GND ref, spares)
→ AC couple → fixed stage G=10 with bandpass (HP ~15 kHz, LP ~120 kHz, MFB)
→ PGA MCP6S91 (G=1–32, SPI; bandwidth 1–18 MHz, still ≥1 MHz at G=32 —
verified, fine for 40 kHz) → switchable +20 dB stage (analog-switch bypass)
→ ADC driver → ADC.

- Analog rail 3.3 V, mid-bias 1.65 V (direct SPI to ESP32, no level shift).
- Total gain 20–70 dB in fine digital steps.
- Op-amps: 5 V/3.3 V RRIO, GBW ≥ 10 MHz (OPA2365 class).
- 0-ohm links between every stage; test point on every node.

### ADC + capture

**Design change from first draft.** A per-conversion CS-framed SPI ADC
(ADS7883 class) cannot be clocked gap-free by the S3's SPI master DMA — each
16-clock frame needs a CS edge the DMA stream can't generate, and per-
transaction software overhead kills 2 MSPS. Instead:

- **Parallel pipeline ADC captured by the ESP32-S3 LCD_CAM camera (DVP)
  peripheral** — fully hardware-clocked DMA capture, no CPU in the loop.
  Prior art: S3-based oscilloscope/logic-analyzer projects use exactly this
  peripheral for continuous parallel capture.
- ADC: AD9235-20 class (12-bit pipeline, 1–20 MSPS, ~90 mW at 3 V).
  Run at **4 MSPS** — clock from LEDC/MCPWM, wired to both ADC CLK and CAM
  PCLK so converter and capture share one clock. (Known-cheap alternative
  with community track record: AD9226 module, but 5 V / ~475 mW.)
- Pipeline latency (7 clocks) is a constant offset; the TX marker calibrates
  it out anyway.
- Capture window 1.2 ms = 4800 samples (9.6 KB), starting ~50 µs before TX.
- Pin cost: 12 data + PCLK ≈ 13 GPIOs. Budget sketch across all functions
  lands ~33 of the module's ~36 usable pins — feasible, but pin mapping is a
  first-class layout task, and a WROOM-1 variant without octal PSRAM is
  required (octal claims GPIO 35–37).

## Measurement cycle

- Slot 1.5 ms per direction (373 µs flight + ring-down margin; sealed
  transducers are high-Q — the just-fired element needs settling time before
  its own RX slot).
- Sequence N→S, S→N, E→W, W→E; 32 pings per direction averaged →
  **5 Hz output**, per-sample resolution well under 0.05 m/s:
  per-ping timing jitter ~50–150 ns at 25–35 dB SNR, /√32 → <25 ns ≈ 0.015 m/s.

## Correlation algorithm (firmware)

1. Find TX marker → t0 on the capture's own clock.
2. Quadrature mix to baseband (40 kHz I/Q, LPF) → complex envelope.
3. Coarse ToF: envelope correlation against a template (template = averaged
   real echoes, captured at first power-up; self-calibrating).
4. Fine ToF: carrier phase of the complex correlation at the coarse peak.
   Cycle-slip guard: envelope timing must be good to ±12.5 µs (half cycle) —
   holds above ~20 dB SNR even with the slow (~narrowband) envelope rise of
   high-Q sealed transducers. This is exactly why fine timing uses phase, not
   envelope.
5. Reciprocal formulas → v_axis, c. Two axes → speed + direction.
6. Per-ping quality metrics (peak SNR, phase consistency) reject outliers
   (rain hits on the plate, spray).
7. Direction calibration LUT for wake/geometry effects — populated from
   drive/sail runs against GPS, applied in firmware.

Compute: ~2400-sample complex correlation over ±130 lags ≈ ms-scale on the
S3 with 16-bit fixed point — fits the slot budget with decimation to spare.

## Verify list — resolved 2026-07-03

- [x] Driver Hi-Z: DRV8876 coast (both outputs Hi-Z, no sleep) confirmed in
      PWM mode; per-output Hi-Z in independent half-bridge mode NOT confirmed
      → design changed to one chip per transducer, PWM mode. Residual check at
      schematic time: off-state leakage/output capacitance (low risk).
- [x] S3 capture: SPI-ADC-per-sample-CS ruled out; switched to parallel ADC
      (AD9235-20 class) on the LCD_CAM DVP peripheral at 4 MSPS. DMA length
      is limited only by internal memory — 9.6 KB windows are trivial.
- [x] Transducers: Multicomp MCUSD16A40S12RO primary + TCT40-16-class generic
      as second vendor; specs consistent with link budget.
- [x] MCP6S91: 1–18 MHz bandwidth, ≥~1 MHz worst case at G=32 — fine at 40 kHz.
- [x] Mux: TMUX1108 selected over 74HC4051 (leakage/Ron/injection).

## Open items for schematic phase

- [ ] Full GPIO map (≈33 pins needed; WROOM-1 without octal PSRAM).
- [ ] DRV8876 off-state loading on the floating transducer.
- [ ] AD9235 input driving stage (last op-amp → ADC input range/CM level).
- [ ] Boost converter part selection and adjustable-feedback network.
