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

Candidates to compare: Prowave 400EP14D / 400EP18A, Murata parking-sensor
series (MA40MF14 class), Manorshi 16 mm sealed. **Buy from two vendors** —
sample variation is the project's biggest unknown; the gain chain is sized to
absorb it.

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
- Each transducer has one terminal grounded, hot terminal driven single-ended
  by a half-bridge with **true Hi-Z (coast) mode** — candidate DRV8876 class
  (2 half-bridges per chip → 2 chips total). During a transducer's RX slot its
  bridge coasts and the element floats free.
- Burst: 8–16 cycles at 40 kHz from MCPWM/RMT; optional anti-phase tail for
  active ring-down damping.
- **TX marker**: ~100:1 divider from one driver output into a spare mux input —
  puts t=0 into every capture buffer (kills trigger jitter, calibrates out
  group delays).

### RX

signal path: transducer → 10 k series + BAV99 clamp → 8:1 mux (74HC4051:
4 transducers, TX marker, GND ref, spares) → AC couple → fixed stage G=10 with
bandpass (HP ~15 kHz, LP ~120 kHz, MFB) → PGA MCP6S91 (G=1–32, SPI) →
switchable +20 dB stage (analog-switch bypass) → ADC.

- Analog rail 3.3 V, mid-bias 1.65 V (direct SPI to ESP32, no level shift).
- Total gain 20–70 dB in fine digital steps.
- Op-amps: 5 V/3.3 V RRIO, GBW ≥ 10 MHz (OPA2365 class).
- 0-ohm links between every stage; test point on every node.

### ADC + capture

- ADS7883 class: 12-bit, 3 MSPS, SPI. Run at **2 MSPS** (SCLK 32 MHz,
  16 clk/sample) via ESP32-S3 SPI DMA.
- Capture window 1.2 ms = 2400 samples (4.8 KB), starting ~50 µs before TX.
- Fallback: 1 MSPS changes nothing fundamental (interpolation unaffected).

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

## Verify before schematic freeze

- [ ] DRV8876 (or chosen driver) supports independent half-bridge control and
      true Hi-Z per output; check coast-mode leakage/capacitance loading on RX.
- [ ] ESP32-S3 SPI master DMA: sustained 32 MHz clocking for 2400-sample
      transactions (else drop to 1 MSPS).
- [ ] Candidate transducer datasheets against the requirements table; pick two.
- [ ] MCP6S91 bandwidth at G=32 comfortably covers 40 kHz (spec ~1 MHz — yes,
      but confirm on datasheet rev).
- [ ] 74HC4051 on-resistance/injection acceptable at 40 kHz mV-level signals
      (else TMUX1108).
