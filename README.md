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

## Documents

- [docs/architecture.md](docs/architecture.md) — system architecture and rationale
- [docs/acoustic-design.md](docs/acoustic-design.md) — transducers, geometry, link budget, front end

## Status (July 2026)

Concept and architecture fixed. AFE fully valued (docs/afe-design.md,
2026-07-04). Next: schematic capture in KiCad (verify-at-capture list in
afe-design.md), then power/digital, then layout.
