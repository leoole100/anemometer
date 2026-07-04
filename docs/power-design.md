# Power design — updated 2026-07-04

Deck-to-masthead power chain, all rails valued for schematic capture. Companion to afe-design.md (AFE rails fixed there: 3.3VA LDO, 5–19 V wide-range direct drive).

## Topology

```
Input (USB-C or 12 V Network) ───────────────────────────────────╮ DECK BOX
                  5 V to 19 V (Variable Input)
                                                                 │  2-wire, ~7 m up the mast
MASTHEAD ────────────────────────────────────────────────────────┴
 entry: polyfuse 0.5 A ── SS34 reverse ── SMAJ15A TVS ── bulk 100 µF ──┬── V_INPUT (5–19 V) (IXDF602, DG412, AL8860)
                                                                       ├── AP63203 buck → 3.3D (ESP32, logic, sensors, ADC digital)
                                                                       └── HT7333 LDO → 3.3VA (AFE, ADC analog)
```

Rationale: The design is highly resilient to input voltage swings. By powering the gate driver ($IXDF602$), selector switch ($DG412$), and LED driver ($AL8860$) directly from the raw input `V_INPUT` (which can vary between 5 V and 19 V depending on whether it is fed by a 5 V USB line, a PD trigger bank, or a boat battery), we completely eliminate the boost converter. A single buck regulator generates the 3.3 V logic rail, and a low-cost LDO generates the quiet analog rail.

---

## Input stage (mast cable entry)

| Item | Part / value | Notes |
|---|---|---|
| **Fuse** | PTC polyfuse, 0.5 A hold / 1 A trip, ≥ 30 V | Peak currents ~200 mA at 5 V; lower at 19 V. |
| **Reverse polarity** | SS34 series Schottky | 0.3 V drop. |
| **Surge/ESD** | SMAJ15A TVS (15 V standoff, clamps ~24 V) | All downstream parts ≥ 30 V rated. |
| **Bulk** | 100 µF electrolytic + 10 µF X7R | Cable inductance + hot-plug. |

---

## Rails and loads

| Rail | Source | Loads | Current | Notes |
|---|---|---|---|---|
| **V_INPUT** | Protected Input | IXDF602 V+, DG412 V+, AL8860 input, AP63203 input, HT7333 input | 35–150 mA | Derived from USB-C power bank or boat battery (5–19 V). |
| **3.3D** | AP63203 (2 A buck) | ESP32-S3, SMT sensors (IMU, Mag), PCM1808 digital core | 120 mA avg, 450 mA pk | L 10 µH, Cout 2×22 µF. Operates down to Vin = 3.8 V. |
| **3.3VA** | HT7333-A (150 mA LDO) | Op-amp 1.5 mA, PCM1808 analog domain ~10 mA | ~12 mA | Low-noise, SOT-89 package. Operates down to Vin = 3.4 V. |
| **LED** | AL8860 | 6× Cree C503B (1S6P) | 0–180 mA at ~3.2 V | Driven from V_INPUT (operates down to 4.5 V). |

---

### Power budget (V_INPUT side)

| Block | Average (at 5 V) | Average (at 12 V) | Average (at 19 V) | Notes |
|---|---|---|---|---|
| ESP32-S3 + Sensors (3.3D buck) | 0.50 W (100 mA) | 0.45 W (38 mA) | 0.45 W (24 mA) | High-efficiency buck. |
| AFE + PCM1808 (3.3VA LDO) | 0.06 W (12 mA) | 0.15 W (12 mA) | 0.23 W (12 mA) | LDO drops excess voltage as heat. |
| TX driver (direct drive) | 0.02 W (4 mA) | 0.05 W (4 mA) | 0.08 W (4 mA) | Transducer energy scales with voltage. |
| LED at calibrated dim (~40%) | 0.28 W (56 mA) | 0.28 W (23 mA) | 0.28 W (15 mA) | AL8860 buck conversion. |
| **Total** | **0.86 W (172 mA)** | **0.93 W (78 mA)** | **1.04 W (55 mA)** | System stays cool under all conditions. |

---

## LED light (calibrated legal target)

*   **LEDs:** 6× Cree C503B high-brightness 5 mm through-hole white LEDs with integrated optics.
*   **Topology:** 1S6P, 10 Ω ballast per LED.
*   **Driver:** AL8860 buck, Rsense 0.56 Ω → 180 mA full scale.
*   **Dimming:** PWM on DIM pin (GPIO42), **≥ 1 kHz** so the magnetometer rejects the ripple field.
*   **Calibration:** Lux meter at 3 m in dark: ≥ 0.35 lx ⇒ ≥ 3 cd.
*   **Default:** ON at power-up; dim only after calibration.

---

## Sequencing and safe state

*   **Cross-Rail Safety:** The LDO ($3.3VA$) rises slightly slower than the buck ($3.3D$). However, because the ESP32-S3 startup sequence and bootloader execution take ~50-100 ms before GPIOs are driven, all power rails are fully stable before any active digital pins are enabled.
*   **Safe State at Boot:** The ESP32-S3 GPIO pins start in high-impedance mode at power-up. We place **100 kΩ pulldown resistors** directly on the `MUX_EN` and `TX_SEL0-3` lines. This ensures the RX mux is shut down and the DG412 switches are open (Hi-Z) by default at boot.
*   **Brownout:** ESP32-S3 internal BOD active. Input bulk cap rides through short glitches.

---

## Grounding / layout notes

- **Single Solid Ground Plane:** No splits. Partition by placement: analog AFE strip on one board edge (transducer connectors → mux → amps → PCM1808 ADC), power switchers and LED driver on the opposite edge.
- **Switching loops:** AP63203 and AL8860 switching nodes kept as short as possible; diodes placed directly adjacent.
- **LED feed/return:** Routed as a tight parallel pair to minimize magnetic field coupling to the magnetometer.
- **Kelvin Connections:** Kelvin sense routing at AL8860 Rsense.
