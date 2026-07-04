# AFE schematic values — decided 2026-07-04

Resolves the three open AFE items (DRV8876 off-state loading, AD9235 drive
stage, boost feedback network) and fixes every component and value in the
analog chain. Values are schematic-ready; a short verify-at-capture list at
the end covers datasheet numbers assumed from memory (none change topology).

## RX chain (end to end, with values)

```
xdcr ──┬── 10k ──┬─ BAV99 ↕ (3.3VA/GND) ── 1k ── TMUX1108 (CH0–3)
       │         │                                    │COM
      100k      (clamp node)                          1n
       │                                              │
      GND                             node B ─────────┤
                                      100k → VMID ────┤
                                      3.3M ← PWM_A ───┤   (TX marker)
                                                      │
    A1: non-inv G=10.1 ── PGA MCP6S91 ── A2: G=1/10.1 ── A3: SK LP ── 33R ── AD9235 VIN+
        (band-limited)       (G 1–32)      (TMUX1101)      155 kHz          15p ┴
```

| Block | Values | Function at 40 kHz |
|---|---|---|
| Input protection | 10 k series, BAV99 to 3.3VA/GND, then 1 k into mux | clamp current 2.7 mA during own-channel TX; 1 k limits injection into mux above its rail |
| Bleed | 100 k node → GND (×4) | DC path for driver Hi-Z leakage (see below) |
| Mux | TMUX1108, EN from SR | CH0–3 xdcr, CH4 marker cal tap, CH5 GND ref, CH6–7 spare→GND |
| AC couple + bias | **1 nF** (was 10 nF, review F1), 100 k → VMID | HP 1.4 kHz; mux-switch DC-step settling τ ≈ 110 µs; node B ≈ 12 k at 40 kHz; −1 dB series loss at 40 kHz |
| A1 fixed gain | Rf 9.1 k ∥ 150 pF; Rg 1 k + 15 nF series → VMID | G = 10.1 (20 dB); LP 117 kHz; HP shelf ~11 kHz (gain→1 below, not 0 — AC couple kills DC) |
| PGA | MCP6S91, VREF pin → VMID, CS GPIO37 | 0–30 dB in 1/2/4/5/8/10/16/32 steps |
| A2 switched gain | Rf 9.1 k; Rg 1 k + TMUX1101 → VMID; SR bit GAIN_SW | open → G=1, closed → G=10.1 (+20 dB); switch sits at VMID, Ron ≪ Rg |
| A3 AA/driver | Sallen-Key unity: R 1.5 k ×2, C1(fb) 1 nF, C2 470 pF | fc 155 kHz, Q 0.73 |
| ADC interface | 33 Ω series + 15 pF NP0 at VIN+ | switched-cap kickback |
| VMID | 10 k/10 k from 3.3VA + 1 µF, A4 buffer, 10 Ω out, 0.1 µF at loads | 1.65 V reference for whole chain |

Op-amps: **2× OPA2365 dual** (A1+A2, A3+A4). 3.3VA rail throughout.

- Total gain 20.1–70.3 dB, steps ≤ 6 dB with overlap. Link budget needs
  22–46 dB (2–30 mV echo → 0.4 V amplitude at ADC, 80 % of FS).
- Anti-alias at 3.96 MHz (aliases onto 40 kHz at 4 MSPS): SK ≈ 56 dB +
  A1 first-order ≈ 30 dB → > 80 dB. ✔
- Noise: ≈ 19 nV/√Hz input-referred (~12 k node + 10 k series + amp) →
  ≈ 8 µV rms in ~170 kHz ENBW → **SNR ≈ 45 dB at the 2 mV worst-case echo**,
  better than the 25–35 dB assumed in the timing budget.
- A1 gain droop at 40 kHz from the HP shelf: −0.3 dB — identical both
  directions, cancels in reciprocal Δt.
- **Coupling cap changed 10 nF → 1 nF (2026-07-04, design-review F1):**
  mux channels sit at different DC levels (bleed × leakage, GND ref), and
  the old 159 Hz corner settled with τ ≈ 1.1 ms ≈ one slot — the DC-coupled
  PGA (×32) and A2 (×10) could clip at high gain for most of the capture.
  At 1.4 kHz corner the step dies in ~350 µs. Firmware rule: **pre-switch
  the mux to the next RX channel immediately after each capture ends.**
  Phase at 40 kHz (2°) and the −1 dB loss are direction-symmetric.

## TX marker — design change

**Old scheme rejected.** A ~100:1 divider from a driver output, permanently
summed into the RX path, also couples the TX transducer's **ring-down**:
Q ≈ 50 → τ = Q/(πf) ≈ 0.4 ms, so at echo arrival (373 µs) the element still
swings ≈ 0.39 × 30 V ≈ 12 V. Through a 1 M injection that is ~130 mV at the
summing node = **5–60× the echo**. Unusable.

**New scheme: logic-side injection.** PWM_A (GPIO21, 3.3 Vpp) → **3.3 MΩ**
into node B → ≈ 12 mVpp, mid-echo scale. After the burst PWM_A is driven low
(push-pull MCU pin): dead silent during the echo window. Jitter cancellation
is preserved — PWM and capture run on the same chip clock, which is the jitter
being killed; driver + transducer group delay is constant and cancels exactly
in the reciprocal Δt.

- Marker clips above ~40 dB total gain — acceptable by design: clipping is at
  t ≈ 0, OPA2365 recovery ≪ 373 µs, and clipped zero crossings still give t0.
- Stuffing pads for 1 M–10 M on the injection resistor.
- Calibration tap kept: PWM_A via 100 k to mux CH4 (measure RX group delay
  directly; signal is within rails, no clamp needed).

## TX drivers (per DRV8876, ×4)

| Pin | Connection |
|---|---|
| PMODE | GND (PWM mode; coast = Hi-Z verified earlier) |
| IN1 / IN2 | AND(PWM_A, DRV_ENn) / AND(PWM_B, DRV_ENn) — 2× 74AHC08 |
| nSLEEP | **per-driver SR bits DRV_nSLP0–3** (review F2), 100 k pulldown each |
| nFAULT | common 10 k pullup → **test point only** (no clean GPIO: pullup on 46 blocks download-mode entry, on 45 straps VDD_SPI) |
| VREF | 3.3 V |
| IPROPI | 2.4 k → GND → ILIM ≈ 3 A (never engages in normal drive) |
| VM | Vb, 100 nF + 10 µF/50 V each |
| OUT1 | transducer (other terminal GND) |
| OUT2 | N.C. pad — bridge-tie fallback per acoustic-design.md |

**Off-state loading (resolved):** Hi-Z leakage ~1.5 µA class through the
100 k bleed → 150 mV DC, removed by AC coupling. Output capacitance
~400 pF (2× FET Coss) against C0 ≈ 2.4 nF → capacitive divider 0.86 =
**−1.3 dB**, absorbed by gain authority. Low risk confirmed.

**Sleep duty-cycling (corrected 2026-07-04, review F2):** 4 drivers awake
continuously ≈ 20 mA at Vb ≈ 0.6 W — too much for the 2–3 W budget. The
first draft claimed "wake all four for a ~6 ms sequence → 20 mW", but the
measurement occupies 4 × 32 × 1.5 ms = 192 ms of every 200 ms frame (96 %),
so waking all four while measuring saves nothing. Instead: **per-driver
nSLEEP**, pings grouped per direction (32 × N→S, then 32 × S→N, …), only the
transmitting driver awake — the RX-side driver is Hi-Z in sleep exactly as in
coast. Each driver wakes ~1 ms (tWAKE) before its 48 ms block →
≈ 5 mA · Vb · 96 % ≈ **70–150 mW average**. Grouping keeps both directions of
an axis within ~50 ms — inside gust time scales, reciprocity intact.

## Boost 10–30 V (TPS61170, resolved)

FB injection: divider + summed PWM current into the FB node (ref 1.229 V).

| Part | Value |
|---|---|
| Rtop (Vb → FB) | 120 k |
| Rbot (FB → GND) | 6.8 k |
| Rinj (filter → FB) | 18 k (+ ~2 k filter source impedance = 20 k effective) |
| PWM filter | 2× (1 k + 1 µF), fc 159 Hz, from GPIO48 LEDC |
| Cff across Rtop | 10 pF footprint, DNP |
| L | 10 µH, XFL4020-103 class (ΔI ≈ 0.35 A pp, Ipk ≈ 0.25 A) |
| D | SS16 (60 V, 1 A Schottky) |
| Cout | 2× 4.7 µF/50 V X7R + 100 nF; Cin 10 µF |
| EN | SR bit BOOST_EN, 100 k pulldown |

Vb = 1.229 + 120k·[1.229/6.8k + (1.229 − Vpwm)/20k]:
**Vpwm 0 → 30.3 V, Vpwm 3.3 → 10.5 V.**

- Relation is **inverse** (duty 0 = max Vb). Firmware rule: set PWM duty
  *before* raising BOOST_EN. Boot is safe regardless (EN pulled down).
- EN low: async boost still passes Vin − Vd ≈ 4.3 V to Vb; drivers are below
  UVLO then, but asleep anyway. Harmless.
- Load is trivial (≈ 90 mW during a burst, ≪ 1 % duty). Duty at 30 V from
  5 V: ≈ 0.84 — verify against max-duty spec.

## ADC configuration (AD9235, resolved)

| Item | Choice |
|---|---|
| AVDD / DRVDD | 3.3VA / 3.3D (spec 2.7–3.6 V) |
| SENSE | AVDD → internal VREF = 0.5 V → **span 1 Vpp** |
| Drive | single-ended: VIN+ = 1.65 ± 0.5 V from A3; VIN− = VMID via 33 Ω + 0.1 µF |
| CLK | GPIO14 via 33 Ω (also loops to DVP PCLK GPIO13) |
| MODE | offset binary, duty-cycle stabilizer ON (resistor per DS) |
| OEB | GND |
| REFT/REFB | 0.1 µF each to GND + 10 µF across |

1 Vpp span costs 6 dB SNR vs 2 Vpp — irrelevant (need ~45 dB, 12-bit gives
~70), and it keeps the single-ended swing (1.15–2.65 V) comfortably linear
for a 3.3 V RRIO driver.

## Shift registers and control (updated)

2× **74AHC595** (AHC for 3.3 V speed margin), SPI shared with PGA
(MOSI 36 / SCK 35), RCLK GPIO38, /SRCLR → 3.3 V,
**/OE → GPIO3 with 10 k pullup** → outputs Hi-Z at boot; 100 k pulldowns
define safe state on DRV_EN0–3, DRV_nSLP0–3, BOOST_EN, MUX_EN.
GPIO3 was a spare; spares are now 0, 45, 46.

| U1 bits | U2 bits |
|---|---|
| DRV_EN0–3, DRV_nSLP0–3 | BOOST_EN, GAIN_SW, MUX A0–A2, MUX_EN, 2× spare/TP |

## Verify at schematic capture (datasheet PDF in hand)

Numbers assumed from memory; none change topology, only resistor tweaks:

1. DRV8876 AIPROPI (455 µA/A assumed), coast quiescent current, tWAKE.
2. TMUX1108 Ron (~125 Ω assumed) and abs-max at the 3.9 V clamp level.
3. AD9235 SENSE polarity (SENSE=AVDD → VREF 0.5 V assumed) and MODE levels.
4. TPS61170 max duty at 1.2 MHz allows 30 V from 5 V (D ≈ 0.84).
5. MCP6S91 VREF pin range and output swing at 3.3 V supply, G = 32.
6. OPA2365 overdrive recovery from marker clipping (expect < 1 µs).

Added by the 2026-07-04 design review:

7. Cross-rail sequencing: TMUX1108 select/EN, MCP6S91 SPI and AD9235 CLK are
   driven from 3.3D while the parts sit on 3.3VA (LDO, rises later) — confirm
   each part tolerates V_logic > V_supply during ramp (TMUX11xx claims logic
   levels independent of supply).
8. DRV8876 ITRIP/current-regulation deglitch time ≫ the ~ns capacitive edge
   spikes of the 2.5 nF load, so the 3 A ITRIP can never chop a burst edge.
9. AD9235 minimum conversion rate (datasheet min 1 MSPS; running 4 MSPS) and
   duty-cycle-stabilizer behavior at 4 MHz.
