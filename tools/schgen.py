"""Compose KiCad 9 .kicad_sch files programmatically.

Symbols are pulled from the system libraries, flattened (extends resolved),
and embedded. Pin positions are computed from the library data so wires can
be attached exactly. Verify output with:
  kicad-cli sch erc <file>   and   kicad-cli sch export pdf <file>
"""

import math
import re
import uuid
from pathlib import Path

SYSLIB = Path("/usr/share/kicad/symbols")


class Sym(str):
    """Bare s-expression atom (unquoted on output)."""


def parse(text):
    toks = re.findall(r'"(?:[^"\\]|\\.)*"|[()]|[^\s()"]+', text)
    pos = 0

    def rd():
        nonlocal pos
        t = toks[pos]
        pos += 1
        if t == "(":
            out = []
            while toks[pos] != ")":
                out.append(rd())
            pos += 1
            return out
        if t.startswith('"'):
            return t[1:-1].replace('\\"', '"').replace("\\\\", "\\")
        return Sym(t)

    return rd()


def emit(node, ind=0):
    if isinstance(node, list):
        flat = all(not isinstance(c, list) for c in node)
        inner = [emit(c) for c in node]
        if flat and len(" ".join(inner)) < 90:
            return "(" + " ".join(inner) + ")"
        head = []
        i = 0
        while i < len(node) and not isinstance(node[i], list):
            head.append(inner[i])
            i += 1
        lines = ["(" + " ".join(head)]
        for c in node[i:]:
            lines.append("\t" * (ind + 1) + emit(c, ind + 1))
        lines.append("\t" * ind + ")")
        return "\n".join(lines)
    if isinstance(node, Sym):
        return str(node)
    if isinstance(node, str):
        return '"' + node.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return str(node)


def num(x):
    s = f"{float(x):.4f}".rstrip("0").rstrip(".")
    return Sym(s if s else "0")


def find(node, tag):
    return [c for c in node if isinstance(c, list) and c and c[0] == tag]


def find1(node, tag):
    r = find(node, tag)
    return r[0] if r else None


_libcache = {}


def _libsyms(libname):
    if libname not in _libcache:
        tree = parse((SYSLIB / f"{libname}.kicad_sym").read_text())
        _libcache[libname] = {c[1]: c for c in find(tree, "symbol")}
    return _libcache[libname]


def load_symbol(libname, symname):
    """Return flattened symbol definition renamed to 'lib:name'."""
    syms = _libsyms(libname)
    node = syms[symname]
    ext = find1(node, "extends")
    if ext:
        base = load_symbol(libname, ext[1])
        # replace base properties with the child's, keep base drawing
        merged = [c for c in base if not (
            isinstance(c, list) and c and c[0] == "property")]
        props = {p[1]: p for p in find(base, "property")}
        for p in find(node, "property"):
            props[p[1]] = p
        merged[1:1] = list(props.values())
        node = merged
    else:
        node = [c for c in node]  # shallow copy
    old = symname if not ext else node[1].split(":")[-1]
    node[1] = f"{libname}:{symname}"
    for c in node:
        if isinstance(c, list) and c and c[0] == "symbol":
            c[1] = re.sub(f"^{re.escape(old)}", symname, c[1])
    return node


def sym_pins(symdef, unit=1):
    """[(number, name, x, y)] in symbol coords for common + given unit."""
    name = symdef[1].split(":")[-1]
    out = []
    for sub in find(symdef, "symbol"):
        m = re.match(rf"^{re.escape(name)}_(\d+)_\d+$", sub[1])
        if not m or int(m.group(1)) not in (0, unit):
            continue
        for p in find(sub, "pin"):
            at = find1(p, "at")
            n = find1(p, "number")[1]
            nm = find1(p, "name")[1]
            out.append((n, nm, float(at[1]), float(at[2])))
    return out


def _uid():
    return str(uuid.uuid4())


class Placed:
    def __init__(self, sch, libid, ref, at, rot, unit, mirror):
        self.sch, self.libid, self.ref = sch, libid, ref
        self.at, self.rot, self.unit, self.mirror = at, rot, unit, mirror

    def pin(self, number):
        """Schematic coords of a pin's connection point."""
        symdef = self.sch.libsyms[self.libid]
        for n, _nm, sx, sy, in sym_pins(symdef, self.unit):
            if n == str(number):
                x, y = sx, -sy
                if self.mirror == "x":
                    y = -y
                if self.mirror == "y":
                    x = -x
                th = math.radians(self.rot)
                # visual CCW rotation in y-down coords
                rx = x * math.cos(th) + y * math.sin(th)
                ry = -x * math.sin(th) + y * math.cos(th)
                return (round(self.at[0] + rx, 4), round(self.at[1] + ry, 4))
        raise KeyError(f"{self.libid} pin {number}")


class Schematic:
    def __init__(self, title, page="A4", rev="A", date="2026-07-03"):
        self.uuid = _uid()
        self.title, self.page, self.rev, self.date = title, page, rev, date
        self.libsyms = {}
        self.items = []
        self.placed = []
        self._wires = []
        self._junctions = []
        self._pwr = 0

    def _embed(self, libname, symname):
        libid = f"{libname}:{symname}"
        if libid not in self.libsyms:
            self.libsyms[libid] = load_symbol(libname, symname)
        return libid

    def add(self, libname, symname, ref, value, at, rot=0, unit=1,
            mirror=None, footprint="", ref_at=None, val_at=None,
            show_value=True, extra_props=None):
        libid = self._embed(libname, symname)
        p = Placed(self, libid, ref, at, rot, unit, mirror)
        self.placed.append((p, value, footprint, ref_at, val_at,
                            show_value, extra_props or {}))
        return p

    def power(self, name, at, rot=0):
        self._pwr += 1
        above = not name.startswith("GND")
        val_at = (at[0], at[1] - 6.35) if above else (at[0], at[1] + 3.81)
        return self.add("power", name, f"#PWR{self._pwr:03d}", name, at, rot,
                        show_value=(name != "PWR_FLAG"), val_at=val_at)

    def wire(self, *pts):
        # raw segments; split at junctions in write() so labels attach
        for a, b in zip(pts, pts[1:]):
            self._wires.append((tuple(a), tuple(b)))

    def _emit_wires(self):
        segs = []
        for a, b in self._wires:
            pts = [a, b]
            for j in self._junctions:
                (ax, ay), (bx, by) = a, b
                on = (min(ax, bx) - 1e-6 <= j[0] <= max(ax, bx) + 1e-6
                      and min(ay, by) - 1e-6 <= j[1] <= max(ay, by) + 1e-6
                      and abs((bx - ax) * (j[1] - ay)
                              - (by - ay) * (j[0] - ax)) < 1e-6
                      and j != a and j != b)
                if on:
                    pts.insert(-1, j)
            pts = [pts[0]] + sorted(
                pts[1:-1], key=lambda p: (abs(p[0] - a[0]) + abs(p[1] - a[1]))
            ) + [pts[-1]]
            segs += list(zip(pts, pts[1:]))
        return [
            [Sym("wire"),
             [Sym("pts"), [Sym("xy"), num(p[0]), num(p[1])],
              [Sym("xy"), num(q[0]), num(q[1])]],
             [Sym("stroke"), [Sym("width"), Sym("0")],
              [Sym("type"), Sym("default")]],
             [Sym("uuid"), _uid()]] for p, q in segs]

    def label(self, text, at, rot=0):
        just = {0: "left bottom", 90: "left bottom",
                180: "right bottom", 270: "left bottom"}[rot]
        self.items.append(
            [Sym("label"), text, [Sym("at"), num(at[0]), num(at[1]), num(rot)],
             [Sym("effects"),
              [Sym("font"), [Sym("size"), num(1.27), num(1.27)]],
              [Sym("justify")] + [Sym(j) for j in just.split()]],
             [Sym("uuid"), _uid()]])

    def junction(self, at):
        self._junctions.append((at[0], at[1]))
        self.items.append(
            [Sym("junction"), [Sym("at"), num(at[0]), num(at[1])],
             [Sym("diameter"), Sym("0")],
             [Sym("color"), Sym("0"), Sym("0"), Sym("0"), Sym("0")],
             [Sym("uuid"), _uid()]])

    def no_connect(self, at):
        self.items.append(
            [Sym("no_connect"), [Sym("at"), num(at[0]), num(at[1])],
             [Sym("uuid"), _uid()]])

    def text(self, s, at, size=1.27):
        self.items.append(
            [Sym("text"), s, [Sym("exclude_from_sim"), Sym("no")],
             [Sym("at"), num(at[0]), num(at[1]), Sym("0")],
             [Sym("effects"),
              [Sym("font"), [Sym("size"), num(size), num(size)]],
              [Sym("justify"), Sym("left"), Sym("bottom")]],
             [Sym("uuid"), _uid()]])

    def _prop(self, name, val, at, hide=False, rot=0):
        eff = [Sym("effects"),
               [Sym("font"), [Sym("size"), num(1.27), num(1.27)]]]
        if hide:
            eff.append([Sym("hide"), Sym("yes")])
        return [Sym("property"), name, val,
                [Sym("at"), num(at[0]), num(at[1]), num(rot)], eff]

    def _sym_node(self, p, value, footprint, ref_at, val_at, show_value,
                  extra):
        x, y = p.at
        ra = ref_at or (x, y - 5.08)
        va = val_at or (x, y + 5.08)
        # keep ref/value text horizontal on rotated symbols
        prot = 90 if p.rot % 180 == 90 else 0
        hide_ref = p.ref.startswith("#")
        node = [Sym("symbol"), [Sym("lib_id"), p.libid],
                [Sym("at"), num(x), num(y), num(p.rot)]]
        if p.mirror:
            node.append([Sym("mirror"), Sym(p.mirror)])
        node += [[Sym("unit"), num(p.unit)],
                 [Sym("exclude_from_sim"), Sym("no")],
                 [Sym("in_bom"), Sym("no" if hide_ref else "yes")],
                 [Sym("on_board"), Sym("yes")],
                 [Sym("dnp"), Sym("no")],
                 [Sym("uuid"), _uid()],
                 self._prop("Reference", p.ref, ra, hide=hide_ref, rot=prot),
                 self._prop("Value", value, va, hide=not show_value, rot=prot),
                 self._prop("Footprint", footprint, (x, y), hide=True),
                 self._prop("Datasheet", "", (x, y), hide=True),
                 self._prop("Description", "", (x, y), hide=True)]
        for k, v in extra.items():
            node.append(self._prop(k, v, (x, y), hide=True))
        for n, _nm, _sx, _sy in sym_pins(self.libsyms[p.libid], p.unit):
            node.append([Sym("pin"), n, [Sym("uuid"), _uid()]])
        node.append(
            [Sym("instances"),
             [Sym("project"), "anemometer",
              [Sym("path"), f"/{self.uuid}",
               [Sym("reference"), p.ref], [Sym("unit"), num(p.unit)]]]])
        return node

    def write(self, path):
        doc = [Sym("kicad_sch"),
               [Sym("version"), Sym("20250114")],
               [Sym("generator"), "eeschema"],
               [Sym("generator_version"), "9.0"],
               [Sym("uuid"), self.uuid],
               [Sym("paper"), self.page],
               [Sym("title_block"),
                [Sym("title"), self.title],
                [Sym("date"), self.date],
                [Sym("rev"), self.rev]],
               [Sym("lib_symbols")] + list(self.libsyms.values())]
        doc += self._emit_wires()
        doc += self.items
        for args in self.placed:
            doc.append(self._sym_node(*args))
        doc.append([Sym("sheet_instances"),
                    [Sym("path"), "/", [Sym("page"), "1"]]])
        doc.append([Sym("embedded_fonts"), Sym("no")])
        Path(path).write_text(emit(doc) + "\n")
