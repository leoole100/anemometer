# AFE schematic values — updated 2026-07-04

Resolves the AFE component and value selection for the Balanced, 5–19 V wide-range direct-drive, fixed-gain architecture.

## RX chain (end to end, with values)

```
xdcr ──┬── 10k ──┬─ BAT54S ↕ (3.3D/GND) ── 1k ── 74HC4051 (CH0–3)
       │         │                                    │COM
      100k      (clamp node)                          1n
       │                                              │
      GND                             node B ─────────┤
                                      100k → VMID ────┤
                                      3.3M ← PWM_A ───┤   (TX marker)
                                                      │
                            A1: non-inv G=101 ── A2: SK LP ── 1uF ── PCM1808 VINL
                                (band-limited)       48 kHz
```

| Block | Values | Function at 40 kHz |
|---|---|---|
| Input protection | 10 k series, BAT54S Schottky to 3.3D/GND, then 1 k into mux | Clamp current is 1.57 mA max at 19 V drive; BAT54S clamps the voltage to $3.6\text{ V}$ (well within the 74HC4051's $V_{CC}+0.5\text{ V}$ absolute maximum limit). |
| Bleed | 100 k node → GND (×4) | DC path for transducer static charge and switch leakage. |
| Mux | **74HC4051D** (SOIC-16), EN from GPIO11 | CH0–3 xdcr, CH4 marker cal tap, CH5 GND ref, CH6–7 spare→GND (operating at 3.3 V). |
| AC couple + bias | 1 nF, 100 k → VMID | HP 1.4 kHz; mux-switch DC-step settling τ ≈ 110 µs; node B ≈ 12 k at 40 kHz. |
| A1 fixed gain | Rf 100 k ∥ 15 pF; Rg 1 k + 15 nF series → VMID | G = 101 (40 dB); LP 106 kHz; HP shelf ~11 kHz (gain→1 below 10 kHz). |
| A2 AA/driver | Sallen-Key unity: R 3.3 k ×2, C1(fb) 1.5 nF, C2 680 pF | fc 48 kHz, Q 0.74 (optimized for 96 kSPS sampling; Nyquist at 48 kHz). |
| ADC interface | 1 µF series AC-coupling cap directly into PCM1808 VINL | PCM1808 input impedance is ~20 kΩ; internal bias network sets input DC level automatically. |
| VMID | 10 k/10 k from 3.3VA + 10 µF ∥ 0.1 µF directly to GND | 1.65 V reference for the analog chain. |

Op-amp: **1× TLV9062 dual** (A1 + A2) in a SOIC-8 package.

---

## TX driver and selector

The transducers are driven directly at the input rail voltage (`V_INPUT`, ranging from 5 V to 19 V) to maximize transmit power without a boost converter.

```
                  V_INPUT (5–19 V)
                      │
   PWM_A (LEDC) ── IXDF602 ── V_INPUTpp square ── DG412 (pins 1,8,9,16)
   (GPIO21)       (SOIC-8)                       │
                                                 ├── NO1 → xdcr 1
                                                 ├── NO2 → xdcr 2
                                                 ├── NO3 → xdcr 3
                                                 └── NO4 → xdcr 4
                                                 (Gate bits TX_SEL0–3 directly from GPIOs)
```

| Component | Part / Connection | Function |
|---|---|---|
| **Gate Driver** | **IXDF602SI** (SOIC-8) | Powered by raw `V_INPUT` (4.5–35 V range) and GND. Input is $3.3\text{ V}$ PWM_A (GPIO21) from the ESP32. Output is a 2 A peak, 0 to `V_INPUT` square wave at 40 kHz. |
| **Selector Switch** | **DG412DY** (SOIC-16) | Quad SPST normally-open analog switches. $V^+$ tied to `V_INPUT`, $V^-$ tied to GND, $V_L$ tied to $3.3D$. Handles up to 44 V. |
| **Logic Inputs** | IN1–IN4 connected to direct GPIOs `TX_SEL0–3` | Decides which transducer is connected to the driver. Only one switch is closed at a time. |
| **Off-State Isolation** | When `TX_SELn` is low, the switch is open | Transducer is isolated from the driver output, allowing it to float and act as an RX element. Leakage is <1 nA. |

---

## ADC configuration (PCM1808, TSSOP-14)

Replaces the parallel and PCM1860 ADCs, using the standard I2S protocol supported natively by the ESP32-S3's I2S peripheral.

| Pin | Connection | Function |
|---|---|---|
| **VCC / VDD** | 3.3VA (analog LDO) / 3.3D (digital buck) | Operates on 3.3 V analog and 3.3 V digital supplies. |
| **VINL / VINR** | AC-coupled via 1 µF from A2 / ground | Left channel receives AFE signal. Right channel grounded. |
| **SCKI** | GPIO13 via 33 Ω | Master Clock from ESP32 ($256 \times F_s = 24.576\text{ MHz}$ for 96 kHz Fs). |
| **BCK** | GPIO14 via 33 Ω | Bit Clock input from ESP32-S3. |
| **LRCK** | GPIO12 | Word Select input from ESP32-S3 (96 kHz). |
| **DOUT** | GPIO15 | Serial Data Output to ESP32-S3 I2S Rx pin. |
| **MD0 / MD1** | HW Strap (Pins 6, 7) | Tie both to GND (Sets device to **I2S Slave Mode**). |

---

## Verify at schematic capture

1. **DG412 logic threshold compatibility:** The $V_L$ pin connected to $3.3D$ ensures that logic inputs IN1–IN4 are compatible with the $3.3\text{ V}$ outputs of the ESP32-S3 even when $V^+$ is at $19\text{ V}$.
2. **HT7333 LDO Input Voltage:** Ensure the LDO input is connected to the protected `V_INPUT` node (not the buck regulator output) to provide a completely separate, low-noise analog rail.
3. **BAT54S clamping:** Connect the common cathode/anode pin (Pin 3) of the SOT-23 BAT54S to `CLAMP_n`, Pin 1 (anode of diode 1) to `GND`, and Pin 2 (cathode of diode 2) to `3.3D`.
