# BOM and cost — updated 2026-07-04

Refdes-level part selection for the updated, Balanced SMT sensor design. All components are in leaded packages (SOIC, TSSOP, SOT-23) or castellated modules (ESP32-S3), except for the two MEMS sensors which are integrated directly on-board.

**Build plan:** Single unit, hand-assembled by the builder using a standard soldering iron and solder wire (for leaded and through-hole components) and hot air / reflow hotplate (for the two leadless MEMS sensors: LGA-14 IMU and LGA-16 Magnetometer).
*   *Note: Solder stencil and solder paste are omitted. LGA/DFN reflow is done using the pre-tinning + gel flux method with the hotplate/hot air.*
*   *Waterproofing:* The board is waterproofed directly by painting a thin, warmed layer of structural epoxy over the components (excluding the sensors/antennas), eliminating the need for a sealed enclosure.

---

## Package Audit (Leaded + leadless SMT + through-hole LEDs)

All components on the main PCB are leaded or castellated, with the exception of the two MEMS sensors which are integrated directly on-board:

| Component Class | Example Parts | Sample footprint | Soldering Method |
|---|---|---|---|
| **SOIC / TSSOP (Leaded)** | PCM1808 (TSSOP-14), DG412 (SOIC-16), IXDF602 (SOIC-8), TLV9062 (SOIC-8) | TSSOP-14, SOIC-16, SOIC-8 | Standard soldering iron + fine tip + solder wick. No thermal pads underneath. |
| **SOT-23 / TSOT (Leaded)** | AP6320x (TSOT-26), AL8860 (TSOT-25), HT7333 (SOT-89 or TO-92), BAT54S | TSOT-26, SOT-89, SOT-23 | Standard soldering iron. |
| **Castellated Modules** | ESP32-S3-WROOM-1 | Castellated edge module | Solder castellated pads on the board edge with a standard iron. Center ground pad of ESP32 can be left unsoldered (thermal load is minimal here) or soldered from a back-side thermal via hole. |
| **Leadless SMT (Direct SMT)** | ISM330DHCX (LGA-14), MMC5983MA (LGA-16) | LGA-14, LGA-16 | Pre-tinned pad reflow using gel flux + hot air or reflow hotplate. |
| **Through-Hole (THT)** | Cree C503B (5 mm LED) | 5 mm round THT | Hand-soldered with iron. Leads bent 90° for radial outward facing. |

---

## A. Main Board — Semiconductors

| Ref | Part | Package | Qty | € ea | € ext | Notes |
|---|---|---|---|---|---|---|
| U1 | ESP32-S3-WROOM-1-N16 | Module | 1 | 3.20 | 3.20 | Castellated module, no PSRAM. |
| U2 | **IXDF602SI** | SOIC-8 | 1 | 2.00 | 2.00 | Dual gate driver (2 A peak, 1 channel used for TX, powered at V_INPUT). |
| U3 | **DG412DY** | SOIC-16 | 1 | 1.50 | 1.50 | Quad SPST high-voltage analog switch (operating at V_INPUT). |
| U4 | **74HC4051D** | SOIC-16 | 1 | 0.20 | 0.20 | RX Mux (operating at 3.3 V). |
| U7 | **TLV9062IDR** | SOIC-8 | 1 | 0.35 | 0.35 | Dual 10 MHz Rail-to-Rail op-amp (A1 fixed-gain + A2 filter). |
| U9 | **PCM1808PWR** | TSSOP-14 | 1 | 0.80 | 0.80 | 96 kHz 24-bit stereo I2S ADC. |
| U12 | AP63203WU-7 | TSOT-26 | 1 | 0.75 | 0.75 | 3.3D buck converter. |
| U13 | **HT7333-A** | SOT-89 | 1 | 0.15 | 0.15 | 3.3VA low-noise LDO regulator (runs from V_INPUT). |
| U14 | AL8860WT-7 | TSOT-25 | 1 | 0.55 | 0.55 | LED driver (runs from V_INPUT). |
| U15 | USBLC6-2SC6 | SOT-23-6 | 1 | 0.30 | 0.30 | USB ESD protection. |
| D1–D4 | **BAT54S** | SOT-23 | 4 | 0.04 | 0.16 | Input Schottky clamps (protects 74HC4051; replaces BAV99). |
| D5, D6 | SS34 | SMA | 2 | 0.06 | 0.12 | Input reverse + VBUS OR. |
| D8 | SMAJ15A | SMA | 1 | 0.15 | 0.15 | Input TVS diode. |
| **Subtotal** | | | | | **€12.28** | |

---

## B. Main Board — SMT Sensors

| Ref | Part | Package | Qty | € ea | € ext | Notes |
|---|---|---|---|---|---|---|
| U16 | **ISM330DHCX** | LGA-14 | 1 | 4.50 | 4.50 | 6-axis IMU (Industrial grade, mast motion compensation). |
| U17 | **MMC5983MA** | LGA-16 | 1 | 2.50 | 2.50 | 3-axis Magnetometer (automatic heading reference). |
| **Subtotal** | | | | | **€7.00** | |

---

## C. Main Board — LEDs, Magnetics, Passives

| Ref | Part | Qty | € ea | € ext | Notes |
|---|---|---|---|---|---|
| LED1–6 | **Cree C503B-WAS-COA0Q151** | 6 | 0.35 | 2.10 | 5 mm through-hole white LED with integrated lens (15°/30°). |
| L3 | 10 µH SRN5040-class shielded | 1 | 0.25 | 0.25 | For AP63203. |
| L4 | 47 µH SRN6045-class shielded | 1 | 0.40 | 0.40 | For AL8860. |
| F1 | 1812L050/33CR polyfuse (0.5 A / 33 V) | 1 | 0.35 | 0.35 | |
| C-bulk | 100 µF/25 V electrolytic | 1 | 0.15 | 0.15 | |
| C-coil | 10 µF low-ESR ceramic (0805) | 1 | 0.10 | 0.10 | Required for MMC5983MA CAP pin. |
| R/C Field | ~50 pcs 0603 passives | — | — | 2.50 | Includes 6× 10 Ω ballast resistors. |
| **Subtotal** | | | | **€5.85** | |

---

## D. Main Board — Connectors

| Ref | Part | Qty | € ea | € ext | Notes |
|---|---|---|---|---|---|
| J1 | USB-C receptacle 16-pin (TYPE-C-31-M-12) | 1 | 0.25 | 0.25 | |
| J2–J5 | JST-PH 2-pin vertical + housings/crimps | 4 | 0.60 | 2.50 | Transducer pigtails. |
| J6 | JST-VH 2-pin | 1 | 0.40 | 0.40 | Power input. |
| J8 | JST-PH 2-pin | 1 | 0.50 | 0.50 | Top disc (LED power only). |
| **Subtotal** | | | | **€3.65** | |

**Board BOM per populated board: ≈ €28.78**

---

## E. Transducers & Enclosure Consumables

| Item | Qty | € ea | € ext | Notes |
|---|---|---|---|---|
| Waterproof 40 kHz transducers | 4 | 0.00 | 0.00 | **User Spare Parts (from previous project).** |
| Inserts, screws, Al reflector disc, filament | — | — | 10.00 | Simplified non-sealed enclosure parts. No Gore vent or EPDM grommets needed. |
| Clear Epoxy Potting Compound | 1 | 0.00 | 0.00 | **User Spare Parts (already owned, brushed on board).** |
| **Subtotal** | | | **€10.00** | |

---

## F. PCB & Consumables

| Item | € | Notes |
|---|---|---|
| PCB 4-layer ~100 × 70 mm, 5 pcs | 12.00 | Ordered from budget fab (e.g. JLCPCB/PCBWay). |
| Solder wire, gel flux pen | 8.00 | Used for hand-soldering and pre-tinned reflow. |
| **Subtotal** | **€20.00** | |

---

## G. Deck Side / Cabling

| Item | Qty | € ea | € ext | Notes |
|---|---|---|---|---|
| Junction box / fuse holder | 1 | 2.00 | 2.00 | Basic inline fuse holder in cabin. |
| Power Cable 2 × 0.5 mm², 8 m | 1 | 4.00 | 4.00 | Direct V_INPUT feed up the mast. |
| **Subtotal** | | | **€6.00** | |

---

## Cost Rollup (Single Self-Assembled Unit)

| Category | € (New Balanced 5–19V Design) | € (Previous 12V Design) |
|---|---|---|
| Main Board BOM (semis, sensors, passives) | 28.78 | 28.78 |
| Transducers & Enclosure hardware (using spares) | 10.00 | 10.00 |
| PCBs & Consumables (budget fab + no stencil) | 20.00 | 20.00 |
| Deck-side components (direct V_INPUT feed) | 6.00 | 6.00 |
| **Total Project Cost** | **≈ €64.82** | **≈ €64.28** |
| *No LED Light Variant* | **≈ €56.97** | **≈ €56.43** |

### Key Budget Achievements:
1.  **Direct Schottky Clamping:** Replaced `BAV99` with `BAT54S` to protect multiplexer inputs from higher voltage pulses up to 19 V. Cost change is neutral.
2.  **Wide Voltage Compatibility:** Power budget, AFE clamping, and buck/LDO configurations are certified for 5 V to 19 V inputs.
3.  **Low Total Cost:** The complete unit is built for **≈ €65** (or **≈ €57** without the LED light ring).
