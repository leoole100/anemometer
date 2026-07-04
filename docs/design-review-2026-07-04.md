# Design review — 2026-07-04

Full re-derivation of the numbers in architecture.md, acoustic-design.md,
afe-design.md and pinmap-parts.md, done before schematic capture. Verdict:
**architecture and AFE topology hold up**; four real issues found (F1–F4),
all fixable on paper without topology changes, plus a set of smaller doc
corrections and new verify-at-capture items. Fixes are applied in the
respective docs and cross-referenced here.

## 1. Checks that passed (recomputed independently)

| Quantity | Doc value | Recomputed | Verdict |
|---|---|---|---|
| Leg length √(50² + 40²) | 64 mm | 64.0 mm | ✔ |
| ToF at P = 128 mm | 373 µs | 128 mm / 343 m/s = 373 µs | ✔ |
| Sensitivity Δt = 2Dv/c² | 1.7 µs per m/s | 2·0.1/343² = 1.70 µs | ✔ |
| Wind formula v = (P²/2D)(1/t_f − 1/t_r) | — | re-derived via path-projected advection v·D/P | ✔ |
| Drive fundamental, 30 Vpp square | +2.6 dB re 10 Vrms | (4/π)·15 Vp = 13.5 Vrms → +2.6 dB | ✔ |
| Distance term 30 → 12.8 cm | +7.4 dB | 20·log(30/12.8) = 7.4 dB | ✔ |
| SPL at RX | 110 dB ≈ 6.3 Pa | 20 µPa·10^(110/20) = 6.32 Pa | ✔ |
| Marker level, 3.3 Vpp via 3.3 M into ~12 k node | ≈ 11 mVpp | 3.3·12k/3.3M ≈ 12 mVpp | ✔ |
| Ring-down τ = Q/(πf), Q = 50 | ≈ 0.4 ms | 398 µs; e^(−373/398) = 0.39 | ✔ |
| Old marker ring-down leak | 5–60× echo | 0.39·30 V / 1 M into 11.5 k ≈ 130 mV vs 2–30 mV | ✔ rejection justified |
| Boost Vb(Vpwm) | 30.3 / 10.5 V | 1.229 + 120k·[1.229/6.8k + (1.229−Vpwm)/20k] → 30.3 / 10.5 V | ✔ |
| Boost burst load | ≈ 90 mW | C·V²·f = 2.5n·30²·40k = 90 mW | ✔ |
| Anti-alias at 3.96 MHz | > 80 dB | SK 40·log(3960/155) = 56 dB + A1 20·log(3960/117) = 31 dB | ✔ |
| A1 LP corner | 117 kHz | 1/(2π·9.1k·150p) = 117 kHz | ✔ |
| A1 shelf zero | ~11 kHz | 1/(2π·1k·15n) = 10.6 kHz | ✔ |
| Input-referred noise | ≈ 19 nV/√Hz → SNR 45 dB | ~16 nV/√Hz (11 k source + bias + OPA2365) → 8 µV rms in 170 kHz; 1.4 mV rms / 8 µV ≈ 45 dB | ✔ |
| ILIM via IPROPI 2.4 k | ≈ 3 A | 3.3 V/(2.4k·455 µA/A) = 3.0 A | ✔ |
| Clamp current during own-channel TX | 2.7 mA | (30 − 3.9)/10k = 2.6 mA | ✔ |
| Clamp charge pumped into 3.3VA | — | ~1.3 mA avg for 0.4 ms into ≥10 µF rail = 54 µV rise; LDO can't sink but never needs to | ✔ negligible |
| Gain need vs authority | 22–46 dB need, 20–70 dB have | 2–30 mV → 0.4 V: 22.5–46 dB | ✔ |
| Measurement frame | 5 Hz | 4 dir × 32 pings × 1.5 ms = 192 ms | ✔ (but see F2) |
| GPIO map | no conflicts | all 33 assignments unique, all exist on WROOM-1 without octal PSRAM | ✔ (count fixed, see D4) |
| SPI sharing PGA + SRs | — | SRs shift junk during PGA frames but RCLK doesn't latch; PGA ignores traffic with CS high | ✔ clean |

Reciprocity check (new, worth recording): both directions of one axis use the
*same two* transducers, the same mux, and the same amplifier chain — the total
electro-acoustic transfer function is identical for t_f and t_r (piezo
reciprocity), so transducer group delay (which is huge: τ_g ≈ 2Q/ω₀ ≈ 0.4 ms
of ring-up) cancels *exactly* in the wind difference. It does **not** cancel in
the ToF **sum**, so the derived sound speed c carries a slowly drifting
electro-mechanical offset (Q and f₀ move with temperature). Consequence for
firmware, not hardware: continuously auto-zero the c-channel against
SHT41-derived c; use acoustic c for fast response only. Wind output is immune.

## 2. Findings

### F1 — RX coupling cap can't settle within a slot after mux switching (fixed)

The mux changes channel every 1.5 ms slot. The channels sit at different DC
levels (transducer channels ≈ 150 mV from driver leakage × 100 k bleed; GND
ref at 0 V; levels also differ unit-to-unit). Each switch puts a DC step into
the 10 nF / 100 k AC-coupling network, which settles with
τ = (100 k + ~11 k source)·10 nF ≈ **1.1 ms** — about one slot long. At echo time
(373 µs after TX) ~70 % of the step is still present; below the A1 shelf it
passes at gain 1, but the PGA (×32) and A2 (×10) amplify it at DC and can be
driven into clipping at high gain settings, exactly in the worst-case
(low-signal) condition where high gain is in use.

**Fix (applied in afe-design.md):** coupling cap 10 nF → **1 nF**. HP corner
159 Hz → 1.4 kHz (still 28× below 40 kHz; phase shift at 40 kHz ≈ 2°,
identical both directions, cancels reciprocally). Settling τ ≈ 110 µs → step
residue ≈ 3 % at capture start when the mux is switched at the end of the
previous capture. Signal loss through 1 nF (|Z| ≈ 4 k at 40 kHz) ≈ −1 dB,
inside gain authority. Firmware rule added: **switch the mux to the next RX
channel immediately after each capture ends**, buying ~350 µs of extra
settling for free. Marker injection level barely changes (node ≈ 12 k).

### F2 — Driver sleep duty-cycle savings were computed against the wrong duty (fixed)

afe-design.md claimed: wake all four DRV8876 for a "~6 ms sequence", sleep
between → ~20 mW average. But 6 ms is one ping per direction; the full 5 Hz
frame is 4 × 32 × 1.5 ms = **192 ms busy out of 200 ms** (96 % duty). With
all four drivers awake while measuring, average driver power is
0.6 W × 0.96 ≈ **0.58 W — no saving at all**, and the 2–3 W budget breaks.

**Fix (applied in afe-design.md + pinmap-parts.md):** nSLEEP becomes
**per-driver** (4 SR bits instead of 1 — the spare bits exist). Only the
transducer that is about to transmit needs to be awake; the RX-side driver's
outputs are equally Hi-Z in sleep as in coast. Pings are grouped per direction
(32 × N→S, then 32 × S→N, …), so each driver wakes once per frame, ~1 ms
(tWAKE) before its 48 ms block and sleeps after → one driver awake at a time:
≈ 5 mA · Vb · 96 % ≈ **70–150 mW average** (Vb = 15–30 V). Grouping also
keeps the two directions of an axis within ~50 ms of each other, well inside
gust time scales, so the reciprocal assumption (same wind for t_f, t_r) holds.
Fallback if ping count must drop: 8 pings/direction still gives
< 0.03 m/s per-sample noise (jitter /√8) — the spec survives.

### F3 — LED string topology impossible from a 12 V buck; legal target now quantified (fixed)

pinmap-parts.md had "6× mid-power LED ring" on an AL8860 **buck** from the
12 V line. Six white LEDs in series is ~18.6 V — a buck can't make that from
12 V, and after PD fallback (bank without a 12 V profile → 9 V or 5 V) even
2S strings die.

Legal requirement (resolves the open item): the BSO light for this vessel is
a **white all-round "gewöhnliches Licht", required visibility ≈ 2 km** in
dark clear night (Bodenseekreis Merkblatt zur Lichterführung). Via Allard's
law with the COLREGS threshold E = 2·10⁻⁷ lx and transmissivity 0.8/NM:
I_min = E·d²/T^d = 2·10⁻⁷ · 2000² / 0.8^1.08 ≈ **1.0 cd**. Design target
**≥ 3 cd** over ±25° vertical (dinghy heel) → flux out of diffuser
≈ 3 cd · 5.3 sr ≈ 16 lm → ≈ 23 lm from LEDs at ~70 % diffuser transmission —
about **0.2 W of mid-power LED**. The old 1–2 W provision was 5–10× oversized.

**Fix (applied in pinmap-parts.md, detail in power-design.md):** **1S6P**
ring (six parallel LEDs, 1 Ω ballast each), AL8860 with Rsense 0.56 Ω →
180 mA full scale ≈ 0.6 W, PWM-dimmed down to the photometrically calibrated
legal-plus-margin level (expect ~40 %). 1S works from any PD fallback voltage
down to 5 V — the light survives a bank that only offers 5 V. Verification
plan: lux meter at 3 m in the dark ≥ 0.35 lx ⇒ ≥ 3 cd.

### F4 — Sensitivity requirement typo, −90 dB ≠ 0.3 mV/Pa (fixed)

acoustic-design.md required "RX sensitivity ≥ −90 dB re 1 V/Pa (≥ ~0.3 mV/Pa)".
−90 dB re 1 V/Pa is 0.032 mV/Pa; 0.3 mV/Pa is **−70 dB**. The link budget's
2–30 mV echo range assumes 0.3–5 mV/Pa, and the selected Multicomp part is
−65 dB (0.56 mV/Pa), so the *intent* was −70 dB. A true −90 dB part would
give a 0.2 mV echo needing 74 dB — outside the 70.3 dB gain authority.
**Fix (applied):** requirement now reads ≥ −70 dB re 1 V/Pa. No parts change.

## 3. Smaller doc corrections (applied)

- **D1 — sample-rate consistency:** capture is 4 MSPS (AD9235 + DVP);
  correlation numbers (±120-sample window, 2400-sample buffers) are at the
  **2 MSPS post-decimation** rate after the quadrature mix. architecture.md
  and acoustic-design.md now say so explicitly instead of mixing "2 MSPS"
  and "4 MSPS".
- **D2 — BAV99 count:** ×4 (one per transducer input), not ×5 — the marker
  cal tap is within rails by construction and the ADC input is driven by a
  3.3 V RRIO amp that cannot exceed the rail.
- **D3 — 74HC/74AHC:** pinmap said 74HC595/74HC08 in two places while
  afe-design said 74AHC — AHC everywhere (3.3 V speed margin).
- **D4 — GPIO count:** map is **33 used / 3 spare** (0, 45, 46), not 32/4.

## 4. New verify-at-capture items (added to afe-design.md)

1. **Cross-rail sequencing:** 3.3D (buck from 12 V) and 3.3VA (LDO from 5 V)
   rise at different times. TMUX1108 select/EN, MCP6S91 SPI and AD9235 CLK
   are 3.3D-driven while the parts sit on 3.3VA — confirm each part's logic
   inputs are tolerant of V_logic > V_supply during ramp-up (TI TMUX11xx
   claims logic levels independent of supply; confirm on the PDF, same for
   MCP6S91 and AD9235 digital inputs).
2. **DRV8876 ITRIP deglitch:** the capacitive load draws ~ns edge spikes;
   confirm the current-regulation deglitch time is ≫ the spike width so
   ITRIP (3 A) can never chop a burst edge.
3. **AD9235 minimum conversion rate** (datasheet min 1 MSPS — 4 MSPS is
   comfortably above, confirm) and duty-cycle-stabilizer behavior at 4 MHz.
4. **AL8860 minimum on-time** at 12 V → ~3.1 V, 180 mA (hysteretic control,
   expect fine; confirm switching stays out of audible range if it matters).

## 5. Gaps deferred to later phases (tracked, not blocking schematic)

- **Enclosure environment:** masthead unit will see spray and 100 % RH with
  daily thermal cycling → condensation is the realistic killer. Plan: Gore
  (PTFE) pressure-equalization vent, conformal coat on the PCB except the
  SHT41 stub and connector, drain path at the lowest point of the housing.
- **Magnetometer vs LED current:** 180 mA DC nearby will bias the MMC5983MA;
  route LED feed/return as a tight pair, keep ≥ 3 cm distance, and rely on
  hard-iron cal — but also PWM-dim at a frequency the mag's filtering rejects
  (choose dim frequency ≥ 1 kHz, not tens of Hz).
- **Correlation template drift:** template = averaged real echoes; transducer
  Q/f₀ drift with temperature reshapes the envelope. Fine timing is phase-based
  and immune; refresh the template slowly (exponential average of accepted
  echoes) rather than fixing it at first power-up.
- **Coherent averaging note:** accumulate the *complex correlation* over the
  32 pings of a direction, then do one peak search — cheaper than 32 peak
  searches and gains SNR coherently (ping-to-ping phase wander from wind
  variation ~2° at 0.1 m/s change — safely coherent).
- **c-channel auto-zero** against SHT41 (see reciprocity note in §1).
