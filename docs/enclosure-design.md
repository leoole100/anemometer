# Enclosure design — 2026-07-04

The enclosure *is* the acoustic instrument (D lives here, not on the PCB) and
the environmental survival plan. 3D-printed, iterations are free by strategy.

## Stack (top to bottom)

```
      ╭───────────╮   translucent diffuser dome (light + GPS radome)
      │ GPS ▣     │   ← SAM-M10Q centered, patch up
      │ ◠◠◠◠◠◠    │   ← 6-LED ring at perimeter, facing outward
      ├───────────┤   O-ring
      │           │
      │  main PCB │   electronics bay (WiFi antenna at wall, SHT41 labyrinth)
      │           │
      ├───────────┤   Gore vent + drain at bay floor
      │ T1 T2 T3 T4│   transducer collar, faces down-inward 51°
      ╰──╲──────╱──╯
     ╱    ╲    ╱    ╲  4 struts at 45° to the measurement axes
    ────────────────   reflector plate Ø ~120, D = 100 between pairs
         ║
         ║  mast tube socket + M8 cable gland
```

Overall ≈ Ø 120 × 200 mm. Diffuser Ø ≈ 50 mm.

## Resolutions of open items

**GPS vs LED ring (pinmap open item — resolved):** both live under the
diffuser dome on one small top PCB disc: LEDs at the perimeter firing
outward, SAM-M10Q centered with the patch facing up. A ~16 mm central
obstruction inside a perimeter ring casts **no horizontal shadow**, so the
all-round light character is preserved; the GPS looks up through ~2 mm of
diffuser plastic (acceptable attenuation for an M10 with clear sky at a
masthead — verify fix quality at bring-up, the module is a stuff option
anyway). LED feed to the top disc is a twisted pair, and the magnetometer
sits on the far end of the main PCB (review §5).

## Acoustic section

- **Transducer mounting:** EPDM rubber grommets in the collar (the
  structural-crosstalk de-risking rule), faces flush with the collar
  underside — no cavity in front of the face (cavities ring). Cable exits
  potted with neutral-cure silicone.
- **Geometry:** D = 100.0 mm nominal between opposite faces, 51° tilt.
  Print tolerance directly biases the wind scale factor
  (v ∝ 1/D via P²/2D): ±0.5 mm print accuracy = ±0.5 % of reading —
  acceptable; the drive/sail GPS calibration LUT absorbs it anyway.
  Measure as-printed D with calipers and put it in the firmware config.
- **Struts:** 4, teardrop cross-section, at 45° to both measurement axes —
  outside every TX→plate→RX beam. Teardrop (blunt edge up) sheds rain and
  minimizes its own vortex shedding into the measurement volume.
- **Reflector plate:** flat, with a **2 mm aluminum disc insert** on top of
  the printed carrier — stiff, flat, and printable-surface-independent. A
  water film on the plate is acoustically harmless (air→water is nearly
  total reflection already); edge drain groove so pooling doesn't build a
  meniscus lens. Drops hitting the plate are transient outliers → already
  handled by per-ping quality rejection.
- **Multipath sanity:** wanted path 128 mm; the shortest parasitic
  (TX → plate → collar underside → plate → RX) is ≥ ~210 mm → arrives
  ≥ 230 µs late, far outside the ±60 µs correlation search window. The
  collar underside center still gets shallow V-grooves to scatter, cheap
  insurance.
- **Fallback variant** (direct-path pylons, per acoustic-design.md) reuses
  the same collar PCB/connector interface — only the printed parts change.

## Environmental

- **Material:** ASA (UV-stable, prints fine); black body, white/natural
  diffuser. No PLA anywhere (masthead heat), no PETG for the body (UV).
- **Condensation (the realistic killer):** sealed bays breathe through one
  **Gore/PTFE pressure-equalization vent** at the electronics bay floor
  (facing down); PCB conformal-coated except SHT41 stub, connectors and
  test-point field (coat boundary on silkscreen); a 2 mm weep hole at the
  absolute low point of the transducer collar (open cavity, not sealed).
- **SHT41 exposure:** double-walled side labyrinth into the electronics bay
  wall — outside air reaches the stub with no line of sight for sun or
  spray; stub thermally slotted from the main PCB (digital-design.md).
- **Sealing (two-stage, decision 2026-07-04):** during development the
  joints run on O-ring/gasket + A4 screws into heat-set inserts, opened as
  often as needed (USB-C on the main PCB is reachable with the bay lid off).
  Once the unit is calibrated and proven on the water, the joints are
  **glued shut** (PU adhesive or epoxy; solvent-free — ASA crazes) for the
  permanent seal. After gluing, all access is OTA + WiFi debug pipe; the
  Gore vent stays, a glued box still has to breathe.
- **Cable entry:** M8 gland at the mast socket, drip loop inside the mast.
- **Mast mount:** printed socket sleeve for the dinghy's mast-top fitting
  with a positive rotational index (device X-axis = boat forward within a
  couple of degrees; the rest is heading calibration in firmware).

## Print/iteration plan

1. Print collar + plate first, without electronics — check fit of grommets,
   transducers, struts.
2. First acoustic tests happen with the real boards in this print on a desk;
   geometry tweaks (h, plate size, groove pattern) are new prints, firmware
   constant D re-measured each time.
3. Diffuser dome printed in natural + vase-ish walls; verify ≥ 0.35 lx at
   3 m (power-design.md) before sealing the design.
