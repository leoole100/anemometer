"""Pipeline demo: RX first gain stage (AC couple, mid-rail bias, G=10 AC).

Run:  python3 tools/gen_afe_demo.py
Then: kicad-cli sch erc hardware/afe_demo.kicad_sch
      kicad-cli sch export pdf hardware/afe_demo.kicad_sch
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from schgen import Schematic

s = Schematic("RX first stage — generator pipeline demo")

# --- amplifier stage (unit A) ---------------------------------------------
u1 = s.add("Amplifier_Operational", "OPA2325", "U1", "OPA2365",
           at=(152.4, 101.6))
out, inm, inp = u1.pin(1), u1.pin(2), u1.pin(3)

# input node A: bias divider + AC coupling cap + opamp +in
ax, ay = inp[0] - 10.16, inp[1]
s.wire((ax, ay), inp)
s.junction((ax, ay))

c1 = s.add("Device", "C", "C1", "100n", at=(ax - 3.81 - 5.08, ay), rot=90,
           ref_at=(ax - 8.89, ay - 6.35), val_at=(ax - 8.89, ay - 3.81))
s.wire(c1.pin(2), (ax, ay))
lbl_in = (c1.pin(1)[0] - 5.08, ay)
s.wire(c1.pin(1), lbl_in)
s.label("RX_MUX_OUT", lbl_in, rot=180)

r1 = s.add("Device", "R", "R1", "10k", at=(ax, ay - 10.16),
           ref_at=(ax + 2.54, ay - 12.7), val_at=(ax + 2.54, ay - 8.89))
s.wire(r1.pin(2), (ax, ay))
s.power("+3.3VA", r1.pin(1))

r2 = s.add("Device", "R", "R2", "10k", at=(ax, ay + 10.16),
           ref_at=(ax + 2.54, ay + 7.62), val_at=(ax + 2.54, ay + 11.43))
s.wire(r2.pin(1), (ax, ay))
s.power("GND", r2.pin(2))

# feedback: out -> R3 -> (-in); (-in) -> R4 -> C2 -> GND
fb_y = min(inm[1], inp[1]) - 12.7
fx = inm[0] - 5.08
s.wire(inm, (fx, inm[1]))
s.junction((fx, inm[1]))
s.wire((fx, inm[1]), (fx, fb_y))

r3 = s.add("Device", "R", "R3", "9.1k", at=((fx + out[0]) / 2, fb_y), rot=90,
           ref_at=((fx + out[0]) / 2 - 3.81, fb_y - 2.54),
           val_at=((fx + out[0]) / 2 + 3.81, fb_y - 2.54))
s.wire((fx, fb_y), r3.pin(1))

ox = out[0] + 5.08
s.wire(r3.pin(2), (ox, fb_y), (ox, out[1]))
s.wire(out, (ox + 7.62, out[1]))
s.junction((ox, out[1]))
s.label("RX_ST1_OUT", (ox + 7.62, out[1]))

r4 = s.add("Device", "R", "R4", "1k", at=(fx, inm[1] + 10.16),
           ref_at=(fx + 2.54, inm[1] + 7.62),
           val_at=(fx + 2.54, inm[1] + 11.43))
s.wire((fx, inm[1]), r4.pin(1))
c2 = s.add("Device", "C", "C2", "1u", at=(fx, inm[1] + 21.59),
           ref_at=(fx + 2.54, inm[1] + 19.05),
           val_at=(fx + 2.54, inm[1] + 22.86))
s.wire(r4.pin(2), c2.pin(1))
s.power("GND", c2.pin(2))

# --- unused unit B: follower to ground ------------------------------------
u1b = s.add("Amplifier_Operational", "OPA2325", "U1", "OPA2365",
            at=(152.4, 139.7), unit=2)
o2, m2, p2 = u1b.pin(7), u1b.pin(6), u1b.pin(5)
gx = p2[0] - 5.08
s.wire(p2, (gx, p2[1]))
s.power("GND", (gx, p2[1]))
loop_y = 139.7 - 8.89
s.wire(m2, (m2[0] - 2.54, m2[1]), (m2[0] - 2.54, loop_y),
       (o2[0] + 2.54, loop_y), (o2[0] + 2.54, o2[1]), o2)

# --- unit C: power pins + decoupling --------------------------------------
u1c = s.add("Amplifier_Operational", "OPA2325", "U1", "OPA2365",
            at=(114.3, 139.7), unit=3)
vp, vm = u1c.pin(8), u1c.pin(4)
s.power("+3.3VA", vp)
s.power("GND", vm)

c3 = s.add("Device", "C", "C3", "100n", at=(96.52, 139.7),
           ref_at=(99.06, 137.16), val_at=(99.06, 140.97))
s.power("+3.3VA", c3.pin(1))
s.power("GND", c3.pin(2))

# --- ERC anchors: PWR_FLAG on both rails ----------------------------------
s.power("+3.3VA", (78.74, 134.62))
f1 = s.power("PWR_FLAG", (73.66, 134.62))
s.wire((78.74, 134.62), (73.66, 134.62))
s.power("GND", (78.74, 147.32))
f2 = s.power("PWR_FLAG", (73.66, 147.32))
s.wire((78.74, 147.32), (73.66, 147.32))

s.text("Demo: one RX gain stage (AC G=10, DC G=1, mid-rail bias)",
       (73.66, 165.1), size=2)

out_path = Path(__file__).parent.parent / "hardware" / "afe_demo.kicad_sch"
s.write(out_path)
print(f"wrote {out_path}")
