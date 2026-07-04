# Masthead anemometer + light

Combined masthead device for a small sailing dinghy on Lake Constance:

- 2D ultrasonic anemometer (wind speed + direction), sampled-waveform cross-correlation
- All-round white light (legally required on Lake Constance)
- IMU + compass, SHT41 temperature/humidity, optional GPS
- WiFi → Raspberry Pi running Signal K; only a power cable runs down the mast
- Powered from a USB-C PD power bank (no 12 V net on board)

## Strategy

One-off build. All engineering is done theoretically, then boards are ordered
directly and iteration happens in firmware only — no bench prototyping stage.
Boards are therefore designed for rescue-by-firmware: wide digitally-set gain
ranges, adjustable TX drive, stage-isolation links, test points, OTA from day one.

Assembly (decided 2026-07-04): **hand-assembled by the builder**, single
unit; PCBs ordered unassembled (min qty 5, spares are rebuild stock),
stencil + hotplate reflow for the leadless minority, iron for the rest.
No BGA parts anywhere (audit in docs/bom.md). The stage-isolation links
double as bring-up jumpers: power → digital → AFE, verified stage by stage.

## Documents

- [docs/architecture.md](docs/architecture.md) — system architecture and rationale
- [docs/acoustic-design.md](docs/acoustic-design.md) — transducers, geometry, link budget, front end
- [docs/afe-design.md](docs/afe-design.md) — AFE schematic values + verify-at-capture list
- [docs/power-design.md](docs/power-design.md) — power tree, protection, budget, LED light sizing
- [docs/digital-design.md](docs/digital-design.md) — MCU circuit, strapping, DVP clocking, buses, firmware platform
- [docs/pinmap-parts.md](docs/pinmap-parts.md) — GPIO map and part selection
- [docs/enclosure-design.md](docs/enclosure-design.md) — acoustic geometry in plastic, environment, GPS/LED placement
- [docs/design-review-2026-07-04.md](docs/design-review-2026-07-04.md) — full-numbers design review, findings F1–F4
- [docs/bom.md](docs/bom.md) — refdes-level part selection, package audit, cost (~€275 all-in, self-assembled)

## Status (July 2026)

Concept and architecture fixed. AFE fully valued (docs/afe-design.md).
Design review passed 2026-07-04 with four findings, all fixed on paper:
RX coupling settling (10 nF → 1 nF), per-driver TX sleep (power claim was
~25× off), LED string topology + quantified legal intensity (1S6P, ≥ 3 cd),
sensitivity-spec typo. Power tree and digital/MCU design now valued
(power-design.md, digital-design.md). Next: schematic capture in KiCad
(verify-at-capture list in afe-design.md), then layout.
