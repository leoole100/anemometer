# BOM and cost — 2026-07-04 (rev. self-assembly)

Refdes-level part selection for everything, with cost. Prices are unit
prices at the quantities actually bought, mid-2026, EUR, estimates ±30 % —
spot-checked against distributor listings for the big-ticket items
(AD9235, transducers, GPS, magnetometer).

**Build plan (revised):** single unit, hand-assembled by the builder.
PCBs ordered unassembled (JLCPCB 4-layer, min qty 5, **stencil included in
the order**); one board populated, the other four are rework/rebuild stock.

## Hand-assembly package audit — no BGA anywhere

Nothing on the board is BGA. Packages fall into three classes:

| Class | Parts | Method |
|---|---|---|
| Iron-friendly (leaded) | AD9235 (TSSOP-28), TMUX1108, 74AHC595/08 (TSSOP), MCP6S91, OPA2365 (SOIC-8), AP63205/03, TPS7A20, AL8860, USBLC6, TMUX1101 (SOT/TSOT/SC70), all diodes, USB-C receptacle, R/C field | plain iron |
| Leaded + exposed pad | DRV8876 **PWP** (HTSSOP-16), ESP32-S3-WROOM (castellated + center pad) | iron for the pins; pad soldered through a back-side via window, or hot air. DRV8876 pad is thermal/GND and thermally uncritical here (mA-class average) |
| Leadless — **needs reflow, not iron** | ISM330DHCX (LGA-14), MMC5983MA (LGA-16), SHT41 (DFN-4), TPS61170 (WSON-6), SAM-M10Q (LGA) | stencil + solder paste + hotplate or hot-air station; all pads are at the package edge → inspectable and hot-air-reworkable |

**Recommended path:** paste + stencil + a cheap hotplate/hot-air station
(~€40 one-time if not owned) for the leadless minority — this keeps the
design exactly as reviewed, and is the normal one-off workflow. LGA MEMS
sensors fundamentally cannot be ironed; the alternative would be breakout
daughterboards (SparkFun 9DoF ≈ €28 + SHT41 breakout ≈ €7), which costs
more than the hot-air station and complicates the enclosure.

**Iron-only fallbacks, documented in case reflow is off the table:**
- TPS61170 (WSON) → **LMR64010** (SOT-23-5, 40 V / 1 A / 1.6 MHz,
  FB ref 1.23 V — the existing 120 k / 6.8 k / 18 k injection network works
  unchanged). Caveat: max duty ~88 % ⇒ on USB bench power (4.6 V rail) the
  top of the Vb range sags to ~25 V; on mast power full 30 V is reachable.
- Sensors → breakout daughterboards as above.
- SAM-M10Q → hot air only, or omit (it's a stuff option).

## A. Main board — semiconductors

| Ref | Part | Package | Qty | € ea | € ext | Notes |
|---|---|---|---|---|---|---|
| U1 | ESP32-S3-WROOM-1-N16 | module | 1 | 3.20 | 3.20 | no PSRAM (pinmap) |
| U2–U5 | DRV8876PWPR | HTSSOP-16 | 4 | 2.30 | 9.20 | PWP over RGT: probeable, reworkable |
| U6 | TMUX1108PWR | TSSOP-16 | 1 | 1.10 | 1.10 | |
| U7 | TMUX1101DCKR | SC70-6 | 1 | 0.70 | 0.70 | A2 gain switch |
| U8 | MCP6S91-E/SN | SOIC-8 | 1 | 1.60 | 1.60 | |
| U9, U10 | OPA2365AIDR | SOIC-8 | 2 | 2.80 | 5.60 | A1+A2, A3+A4 |
| U11 | **AD9235BRUZ-20** | TSSOP-28 | 1 | **30.00** | 30.00 | see cost note below |
| U12, U13 | SN74AHC595PWR | TSSOP-16 | 2 | 0.35 | 0.70 | |
| U14, U15 | SN74AHC08PWR | TSSOP-14 | 2 | 0.30 | 0.60 | |
| U16 | TPS61170DRVR | SON-6 2×2 | 1 | 1.30 | 1.30 | TX boost |
| U17 | AP63205WU-7 | TSOT-26 | 1 | 0.75 | 0.75 | 5 V buck |
| U18 | AP63203WU-7 | TSOT-26 | 1 | 0.75 | 0.75 | 3.3D buck |
| U19 | TPS7A2033PDBVR | SOT-23-5 | 1 | 0.55 | 0.55 | 3.3VA LDO |
| U20 | AL8860WT-7 | TSOT-25 | 1 | 0.55 | 0.55 | LED buck |
| U21 | USBLC6-2SC6 | SOT-23-6 | 1 | 0.30 | 0.30 | USB ESD |
| D1–D4 | BAV99 | SOT-23 | 4 | 0.04 | 0.16 | input clamps |
| D5, D6 | SS34 | SMA | 2 | 0.06 | 0.12 | input reverse + VBUS OR |
| D7 | SS16 | SMA | 1 | 0.08 | 0.08 | boost rectifier |
| D8 | SMAJ15A | SMA | 1 | 0.15 | 0.15 | input TVS |
| **Subtotal** | | | | | **57.41** | |

**AD9235 cost note:** the -20 grade is ~$34 at LCSC / ~€25–30 at
Mouser-class distributors — the single most expensive component by far.
Plan for the self-assembled single unit: **buy 2** (one fitted, one spare
against a soldering accident — TSSOP-28 is forgiving, but this is the one
part where a lost pin costs €30 and a re-order delay). The cheap-ADC
fallback (AD9226 Chinese module, different footprint) stays a documented
plan B only.

## B. Main board — sensors

| Ref | Part | Qty | € ea | € ext | Notes |
|---|---|---|---|---|---|
| U22 | ISM330DHCXTR | 1 | 7.50 | 7.50 | LGA-14 |
| U23 | MMC5983MA | 1 | 3.00 | 3.00 | ~$2.93 at DigiKey |
| U24 | SHT41-AD1B | 1 | 2.80 | 2.80 | on isolated stub |
| U25 | SAM-M10Q-00B | (1) | 17.00 | (17.00) | **optional stuff group**; ~€17 qty 1 |
| **Subtotal** | | | | **13.30** | (+17.00 with GPS) |

## C. Main board — LEDs, magnetics, passives

| Ref | Part | Qty | € ea | € ext | Notes |
|---|---|---|---|---|---|
| LED1–6 | 2835 white 0.2 W, 5000 K, ≥ 20 lm @ 60 mA (LCSC generic, same bin) | 6 | 0.06 | 0.36 | on top disc |
| L1 | XFL4020-103MEC 10 µH | 1 | 1.80 | 1.80 | boost |
| L2, L3 | 10 µH NR5040-class shielded | 2 | 0.25 | 0.50 | AP6320x |
| L4 | 47 µH SRN6045-class shielded | 1 | 0.40 | 0.40 | AL8860 |
| F1 | 1812L050/33CR polyfuse (0.5 A / 33 V) | 1 | 0.35 | 0.35 | 33 V rating, not 15 V |
| C-bulk | 100 µF/25 V electrolytic | 1 | 0.15 | 0.15 | |
| R/C field | ~115 pcs 0603/0805; X7R 50 V on Vb nodes; C0G for 150 p/470 p/1 n/15 p signal caps; 1 % R, 0.1 % not needed | — | — | 5.50 | includes all stuffing options + 0-ohm links |
| **Subtotal** | | | | **9.06** | |

## D. Main board — connectors

| Ref | Part | Qty | € ea | € ext | Notes |
|---|---|---|---|---|---|
| J1 | USB-C receptacle 16-pin USB2 (HRO TYPE-C-31-M-12) | 1 | 0.25 | 0.25 | bench access; 5.1 k CC pulldowns ×2 in R field |
| J2–J5 | JST-PH 2-pin vertical + housings/crimps | 4 | 0.60 | 2.50 | transducer pigtails |
| J6 | JST-VH 2-pin (12 V in) | 1 | 0.40 | 0.40 | |
| J7 | UART0/EN/IO0: pads only | — | — | — | ROM-loader fallback |
| J8 | JST-PH 4-pin (top disc: LED pair + GPS UART opt.) | 1 | 0.60 | 0.60 | |
| **Subtotal** | | | | **3.75** | |

**Board BOM per populated board: ≈ €83.5 (SMT) + €14.5 connectors/LEDs off-line
→ ≈ €97** (+€17 if GPS stuffed).

## E. Transducers (wired parts, not SMT)

| Part | Qty | € ea | € ext | Notes |
|---|---|---|---|---|
| Multicomp MCUSD16A40S12RO (Farnell 2362677) | 10 | 3.60 | 36.00 | £3.09 @ 10+; 4 fitted + 6 spares |
| TCT40-16-class sealed 16 mm (2nd vendor) | 4 | 2.00 | 8.00 | sample-variation hedge |
| **Subtotal** | | | **44.00** | |

**Datasheet catch (recorded in acoustic-design.md):** Farnell lists the
Multicomp part at **−74 dB** sensitivity, not the −65 dB in our earlier
research. Echo then ≈ 1.3 mV worst case → 50 dB gain needed (authority
70.3 dB ✔), SNR ≈ 41 dB (budget assumed 25–35 ✔). No change needed — this
is exactly what the wide gain range was provisioned for.

## F. PCB + consumables (self-assembly)

| Item | € | Notes |
|---|---|---|
| PCB 4-layer ~100 × 70 mm, 5 pcs (min qty) | 30 | ENIG not needed; boards 2–5 are rebuild stock |
| Stencil (frameless) | 8 | ordered with the PCBs |
| Solder paste + flux + wick | 10 | consumables |
| Hotplate or hot-air station | (40) | one-time tool, only if not owned |
| **Subtotal** | **48** | (+40 tool) |

## G. Deck side

| Item | € | Notes |
|---|---|---|
| CH224K PD-trigger module (ready-made) | 3.00 | set to 12 V |
| Cable 2 × 0.5 mm², 8 m, UV-rated | 6.00 | |
| Printed deck box + 2 cable glands | 4.00 | |
| **Subtotal** | **13.00** | (power bank: existing) |

## H. Enclosure / mechanical

| Item | € | Notes |
|---|---|---|
| Gore-type vent M6 (Amphenol VENT-PS1NGY class) | 2.80 | |
| EPDM grommets 16 mm ×4 | 1.00 | |
| O-ring + flat gasket | 1.00 | development; final build glued |
| Heat-set inserts M3 ×8 + A4 screws | 3.00 | |
| Aluminum disc Ø 120 × 2 mm | 4.00 | reflector insert |
| M8 cable gland | 1.50 | |
| ASA filament ~350 g incl. iterations | 8.00 | |
| Adhesive for final seal (PU/epoxy) | 3.00 | see enclosure-design.md |
| **Subtotal** | **24.30** | |

## Cost rollup (single self-assembled unit)

| | € |
|---|---|
| One parts set, board-complete (§A–D incl. 4 fitted transducers) | 98 |
| Spare AD9235 (see cost note) | 30 |
| Spares kit: 1× each IC under €3, extra passives strip | 15 |
| B-opt — GPS | 17 |
| E-spares — transducer stock (6 primary + 4 alt vendor) | 30 |
| F — PCB ×5 + stencil + consumables | 48 |
| G — deck side | 13 |
| H — enclosure hardware | 24 |
| **Project all-in** | **≈ €275** |
| Trimmed variant (no GPS, no spare ADC, transducer spares 2+2) | ≈ €205 |
| (+ hotplate/hot-air station if not owned) | +40 |

Largest single line items, ranked: AD9235 €30 (€60 with the spare),
transducer stock €44 total, PCB run €38, enclosure hardware €24, GPS €17,
4× DRV8876 €9.2, ISM330DHCX €7.5, 2× OPA2365 €5.6 — everything else is
under €4. The earlier €612 figure was **not** component cost: it was the
5-assembled-boards strategy (€140 assembly service + ~€200 of parts
multiplied across four boards that would mostly sit in a drawer). One set
of electronics for this device is ≈ €100.

**Strategy note (README updated):** hand assembly moves the first-failure
risk from design to soldering. Mitigation is already in the design — the
0-ohm stage-isolation links double as bring-up jumpers: power section
first (no ICs downstream fitted), then digital, then AFE stage by stage,
each verified at its test points before the next is placed. Boards 2–5
plus the spares kit mean any botched stage is a rebuild, not a re-order.

## Ordering checklist

1. JLCPCB: PCB ×5 + stencil.
2. LCSC: §A/C jellybeans (AHC logic, AP6320x, diodes, R/C reels, LEDs,
   TMUX1101, USB-C, inductors).
3. Mouser or DigiKey: AD9235BRUZ-20 ×2, DRV8876 ×5, OPA2365 ×3, MCP6S91 ×2,
   TMUX1108 ×2, TPS61170 ×2, TPS7A20, AL8860, ISM330DHCX, MMC5983MA, SHT41
   (×2 — it's near connectors during gluing), SAM-M10Q ×1, VENT-PS1NGY —
   one order, one shipping fee.
4. Farnell: MCUSD16A40S12RO ×10 (2362677).
5. AliExpress: TCT40-16 sealed ×4, CH224K module, grommets, glands.
6. Local/hardware: Al disc, fasteners, cable, paste if not ordered above.
