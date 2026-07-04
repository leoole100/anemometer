# Power design — 2026-07-04

Deck-to-masthead power chain, all rails valued for schematic capture.
Companion to afe-design.md (AFE rails already fixed there: 3.3VA LDO,
TX boost TPS61170).

## Topology

```
USB-C bank ── CH224K trigger ──╮ DECK BOX
                12 V (9/5 V fallback)
                               │  2-wire, ~7 m up the mast
MASTHEAD ──────────────────────┴───────────────────────────────
 entry: polyfuse 0.5 A ── SS34 reverse ── SMAJ15A TVS ── bulk 100 µF
   │
   ├── AP63205 buck → 5 V ──┬── TPS7A20 LDO → 3.3VA (AFE + ADC)
   │                        └── TPS61170 boost → Vb 10–30 V (TX)
   ├── AP63203 buck → 3.3D (ESP32, logic, sensors, GPS)
   └── AL8860 buck → LED ring (1S6P, 180 mA full scale)
```

Rationale for the split: everything analog hangs off the quiet 5 V
intermediate rail through an LDO; everything that switches hard (radio,
LED PWM) lives on its own buck straight from the input. The LED driver
takes raw input, not 5 V, so its current never modulates the 5 V rail
feeding the AFE.

## Input stage (mast cable entry)

| Item | Part / value | Notes |
|---|---|---|
| Fuse | PTC polyfuse, 0.5 A hold / 1 A trip, ≥ 30 V | peaks ~250 mA |
| Reverse polarity | SS34 series Schottky | 0.3 V · 0.2 A ≈ 60 mW loss — accepted for simplicity; PFET footprint not worth it at this current |
| Surge/ESD | SMAJ15A TVS (15 V standoff, clamps ~24 V) | all downstream parts ≥ 32 V rated |
| Bulk | 100 µF electrolytic + 10 µF X7R | cable inductance + PD hot-plug |
| USB bench feed | SS34 from USB-C VBUS into the node after the input SS34 | board runs from the laptop alone ≙ the 5 V PD fallback case; diodes isolate the two sources |

Cable: 2×0.5 mm² (AWG20) ≈ 0.46 Ω for 14 m loop → 0.1 V drop at peak load.
Even AWG24 (1.2 Ω, 0.3 V) works; specify 0.5 mm² for abrasion margin, not
resistance.

## Rails and loads

| Rail | Source | Loads | Current | Notes |
|---|---|---|---|---|
| 5 V | AP63205 (3.8–32 Vin, 2 A) | TPS7A20 in, TPS61170 in | ~60 mA avg | L 10 µH, Cout 2×22 µF per DS |
| 3.3D | AP63203 (2 A) | ESP32-S3, SRs/gates, sensors, GPS | 160 mA avg, 550 mA pk (WiFi) | L 10 µH, Cout 2×22 µF |
| 3.3VA | TPS7A20 (300 mA) | op-amps 19 mA, PGA 1 mA, AD9235 ~30 mA, mux | ~55 mA | low-noise, PSRR kills buck ripple |
| Vb 10–30 V | TPS61170 | DRV8876 VM ×4 | 5 mA awake + 3 mA burst avg | see afe-design.md |
| LED | AL8860 | 6× LED 1S6P | 0–180 mA at ~3.1 V | see below |

### Power budget (12 V input side)

| Block | Average | Peak |
|---|---|---|
| ESP32-S3 + logic (3.3D via buck, η ≈ 88 %) | 0.47 W | 1.9 W (WiFi burst) |
| Sensors + GPS (3.3D) | 0.13 W | — |
| AFE + ADC (3.3VA via 5 V: LDO burns 34 %) | 0.31 W | — |
| TX drivers + boost (per-driver wake, F2 fix) | 0.10–0.15 W | 0.4 W during burst |
| LED at calibrated dim (~40 % of 180 mA) | 0.28 W | 0.66 W full |
| **Total** | **≈ 1.4 W (117 mA @ 12 V)** | ≈ 3 W momentary |

Within the 2–3 W envelope with real margin now that F2 (driver sleep) and
F3 (LED sizing) are fixed. Day mode (light off): ≈ 1.1 W.

## PD fallback behavior (bank without 12 V profile)

CH224K falls back 12 → 9 → 5 V. Design consequence check, per rail:

- **5 V buck at 5 V in:** AP63205 goes to ~100 % duty, output ≈ 4.6 V;
  TPS7A20 still makes clean 3.3VA; TPS61170 still boosts to full Vb. ✔
- **3.3D buck:** fine from 5 V. ✔
- **LED:** this is why the ring is **1S** — a single 3.1 V string keeps
  regulating from a 5 V input. 2S/3S would go dark. ✔
- Firmware reads Vin (divider 100 k/10 k → an ESP32 ADC-capable spare TP…
  GPIO0 is strapping-tolerant as input-only after boot; decide at capture —
  optional, nice for telemetry only).

## LED light (legal item resolved — see design-review F3)

Requirement: BSO white all-round *gewöhnliches Licht*, visibility ≈ 2 km →
≈ 1.0 cd minimum (Allard, 2·10⁻⁷ lx threshold). Target **≥ 3 cd over
±25° vertical** for heel + aging margin.

| Item | Value |
|---|---|
| LEDs | 6× mid-power white (0.2 W class, ~120 lm/W), equally spaced ring |
| Topology | 1S6P, 1 Ω ballast per LED (matching between parallel LEDs) |
| Driver | AL8860 buck, Rsense 0.56 Ω → 180 mA full scale |
| Dimming | PWM on DIM pin (GPIO42), **≥ 1 kHz** so the magnetometer's filtering rejects the ripple field |
| Calibration | lux meter at 3 m in dark: ≥ 0.35 lx ⇒ ≥ 3 cd; store duty in NVS |
| Default | ON at full at power-up (works without Pi); dim only after calibration |

Full-scale 0.6 W is ~5× the legal need — margin for diffuser losses being
worse than the 70 % estimate, and a "harbor bright" mode.

## Power-bank keepalive

Steady night draw (~1.4 W) is above typical bank auto-off thresholds
(~1–1.5 W); the risk case is **daytime** (light off, ~1.1 W) with a picky
bank. Firmware keepalive, armed by config: every 8 s, 100 ms LED pulse at
full current (invisible in daylight, +9 mW average) — reuses hardware, no
dummy-load resistor. Verify against the actual bank; if its threshold is
above ~2 W sustained, no firmware trick helps and the bank gets replaced
(note in the manual/README of the build).

## Sequencing and safe state

- All converters enabled at power-up (EN tied); no sequencing requirements
  among bucks. 3.3VA lags 3.3D slightly (extra LDO) — this is the cross-rail
  verify item in the review (§4.1): confirm TMUX1108/MCP6S91/AD9235 logic
  inputs tolerate V_logic > V_supply during the ~ms ramp.
- Boot safe state is owned by the SR /OE pullup + per-net pulldowns
  (afe-design.md): boost EN low, drivers asleep, mux disabled. Light defaults
  ON via firmware as early as possible (it is the legally required function).
- Brownout: ESP32-S3 internal BOD active; bulk cap rides through PD
  renegotiation glitches ~ms class. Longer dropouts = clean reboot, light
  restores at boot (~1 s gap, acceptable).

## Grounding / layout notes (for the layout phase)

- One solid ground plane; *partition by placement*, not splits: AFE strip on
  one board edge (transducer connectors → mux → amps → ADC → ESP32 DVP pins),
  switchers and LED driver on the opposite edge, radio antenna edge free of
  copper per module datasheet.
- TPS61170 and the two AP6320x get tight hot loops; SS16/SS34 close in.
- LED feed/return routed as a tight pair (magnetometer, review §5).
- 3.3VA star from the LDO; VMID buffer local to the AFE strip.
- Kelvin at AL8860 Rsense and IPROPI resistors.
