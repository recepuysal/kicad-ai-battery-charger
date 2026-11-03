"""KiCad sematik ureteci icin ortak yardimcilar."""
import math
import re
import uuid

from lcsc_importer import core
from lcsc_importer.core import _q, _num, dump_sexpr, parse_sexpr, _block_span

STOCK = r"C:\Program Files\KiCad\10.0\share\kicad\symbols\%s.kicad_sym"
U = lambda: _q(str(uuid.uuid4()))
DIR = {0: (-1, 0), 180: (1, 0), 90: (0, 1), 270: (0, -1)}   # pinden disari (sema koord.)


class Sheet:
    def __init__(self, name, paper="A4"):
        self.name, self.paper = name, paper
        self.root = str(uuid.uuid4())
        self.lib_symbols, self.items, self.seen = [], [], {}
        self.cnt = {}

    # ------------------------------------------------------------ kutuphane
    def lib_sym(self, lib_id):
        if lib_id in self.seen:
            return self.seen[lib_id]
        lib, name = lib_id.split(":")
        if lib == "LCSC":
            s = core._modern_symbol(name)
        else:
            txt = open(STOCK % lib, encoding="utf-8").read()
            m = re.search(r'\n\t\(symbol "%s"\n' % re.escape(name), txt)
            s = parse_sexpr(txt[m.start() + 2:_block_span(txt, m.start() + 2)])
            if isinstance(s[0], list):
                s = s[0]
        s = list(s)
        s[1] = _q(lib_id)
        self.lib_symbols.append(s)
        pins = {}
        for c in s:
            if isinstance(c, list) and c and c[0] == "symbol":
                for g in c:
                    if isinstance(g, list) and g and g[0] == "pin":
                        at = next(h for h in g if isinstance(h, list) and h[0] == "at")
                        num = next(h for h in g if isinstance(h, list) and h[0] == "number")[1].strip('"')
                        pins[num] = (float(at[1]), float(at[2]), int(float(at[3])))
        self.seen[lib_id] = (s, pins)
        return self.seen[lib_id]

    @staticmethod
    def xf(px, py, rot, mirror):
        if mirror == "y":
            px = -px
        elif mirror == "x":
            py = -py
        r = math.radians(rot)
        rx = px * math.cos(r) - py * math.sin(r)
        ry = px * math.sin(r) + py * math.cos(r)
        return round(rx, 4), round(-ry, 4)

    @staticmethod
    def xang(a, rot, mirror):
        if mirror == "y":
            a = (180 - a) % 360
        elif mirror == "x":
            a = (-a) % 360
        return (a + rot) % 360

    # ------------------------------------------------------------ yerlestir
    def place(self, lib_id, ref, x, y, value=None, rot=0, mirror=None, fields=None, props=None):
        s, pins = self.lib_sym(lib_id)
        if ref.startswith("#"):
            self.cnt[ref] = self.cnt.get(ref, 0) + 1
            ref = "%s%02d" % (ref, self.cnt[ref])
        out_props = []
        for c in s:
            if not (isinstance(c, list) and c and c[0] == "property"):
                continue
            key = c[1].strip('"')
            if key.startswith("ki_"):
                continue
            val = c[2]
            if key == "Reference":
                val = _q(ref)
            if key == "Value" and value:
                val = _q(value)
            if props and key in props:
                val = _q(props[key])
            p = ["property", c[1], val]
            for sub in c[3:]:
                if isinstance(sub, list) and sub[0] == "at":
                    if fields and key in fields:
                        dx, dy = fields[key][:2]
                    else:
                        dx, dy = self.xf(float(sub[1]), float(sub[2]), rot, mirror)
                    sub = ["at", _num(x + dx), _num(y + dy), "90" if rot in (90, 270) else "0"]
                elif isinstance(sub, list) and sub[0] == "effects" and fields and key in fields:
                    sub = [e for e in sub if not (isinstance(e, list) and e[0] == "justify")]
                    j = fields[key][2]
                    if j and rot == 90:
                        j = {"left": "right", "right": "left"}[j]
                    if j and mirror == "y" and rot == 0:
                        j = {"left": "right", "right": "left"}[j]
                    if j:
                        sub.append(["justify", j])
                p.append(sub)
            out_props.append(p)
        inst = ["symbol", ["lib_id", _q(lib_id)], ["at", _num(x), _num(y), str(rot)]]
        if mirror:
            inst.append(["mirror", mirror])
        virt = ref.startswith("#") or lib_id.endswith(":MountingHole")
        inst += [["unit", "1"], ["exclude_from_sim", "no"], ["in_bom", "no" if virt else "yes"],
                 ["on_board", "no" if ref.startswith("#") else "yes"], ["dnp", "no"], ["uuid", U()]]
        inst += out_props
        inst += [["pin", _q(n), ["uuid", U()]] for n in pins]
        inst.append(["instances", ["project", _q(self.name), ["path", _q("/" + self.root),
                                                             ["reference", _q(ref)], ["unit", "1"]]]])
        self.items.append(inst)
        res = {}
        for n, (px, py, a) in pins.items():
            dx, dy = self.xf(px, py, rot, mirror)
            res[n] = (round(x + dx, 4), round(y + dy, 4), self.xang(a, rot, mirror))
        return res

    # ------------------------------------------------------------ cizim
    def wire(self, *pts):
        pts = [p[:2] for p in pts]
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            if (x1, y1) != (x2, y2):
                self.items.append(["wire", ["pts", ["xy", _num(x1), _num(y1)], ["xy", _num(x2), _num(y2)]],
                                   ["stroke", ["width", "0"], ["type", "default"]], ["uuid", U()]])

    def junction(self, x, y):
        self.items.append(["junction", ["at", _num(x), _num(y)], ["diameter", "0"],
                           ["color", "0", "0", "0", "0"], ["uuid", U()]])

    def stub(self, pin, ln=2.54):
        x, y, a = pin
        dx, dy = DIR[a]
        ex, ey = round(x + dx * ln, 4), round(y + dy * ln, 4)
        self.wire((x, y), (ex, ey))
        return ex, ey, a

    def label(self, pin, net, ln=2.54):
        ex, ey, a = self.stub(pin, ln)
        ang, just = {0: (180, "right"), 180: (0, "left"), 90: (0, "left"), 270: (0, "left")}[a]
        self.items.append(["label", _q(net), ["at", _num(ex), _num(ey), str(ang)],
                           ["effects", ["font", ["size", "1.27", "1.27"]], ["justify", just, "bottom"]],
                           ["uuid", U()]])

    def power(self, name, pin, ln=2.54):
        """Guc sembolu; pinden disari dogru yonlenir. GND asagi, digerleri yukari bakar."""
        ex, ey, a = self.stub(pin, ln) if ln else pin
        if name == "GND":
            rot = {90: 0, 0: 270, 180: 90, 270: 180}[a]
            off = {0: (0, 3.81, None), 270: (-3.81, 0, "right"), 90: (3.81, 0, "left"), 180: (0, -3.81, None)}[rot]
        else:
            rot = {270: 0, 0: 90, 180: 270, 90: 180}[a]
            off = {0: (0, -3.81, None), 90: (-3.81, 0, "right"), 270: (3.81, 0, "left"), 180: (0, 3.81, None)}[rot]
        self.place("power:" + name, "#PWR", ex, ey, rot=rot, fields={"Value": off})

    def nc(self, pin):
        self.items.append(["no_connect", ["at", _num(pin[0]), _num(pin[1])], ["uuid", U()]])

    def text(self, s, x, y, size=1.27, bold=False, color=None, italic=False):
        font = ["font", ["size", _num(size), _num(size)]]
        if bold:
            font.append(["bold", "yes"])
        if italic:
            font.append(["italic", "yes"])
        if color:
            font.append(["color"] + [str(c) for c in color])
        self.items.append(["text", _q(s).replace(chr(10), "\\n"), ["exclude_from_sim", "no"],
                           ["at", _num(x), _num(y), "0"], ["effects", font, ["justify", "left", "top"]],
                           ["uuid", U()]])

    def block(self, title, x1, y1, x2, y2):
        blue = (0, 72, 132, 1)
        self.items.append(["rectangle", ["start", _num(x1), _num(y1)], ["end", _num(x2), _num(y2)],
                           ["stroke", ["width", "0.254"], ["type", "dash"], ["color", "0", "72", "132", "1"]],
                           ["fill", ["type", "none"]], ["uuid", U()]])
        self.text(title, x1 + 2.54, y1 + 2.54, size=2, bold=True, color=blue)

    def note(self, s, x, y):
        self.text(s, x, y, size=1.27, italic=True, color=(90, 90, 90, 1))

    # ------------------------------------------------------------ kaydet
    def save(self, path, title_block):
        tb = ["title_block"] + [[k, _q(v)] for k, v in title_block if not k.startswith("comment")]
        tb += [["comment", str(i + 1), _q(v)] for i, (k, v) in
               enumerate([kv for kv in title_block if kv[0].startswith("comment")])]
        sch = ["kicad_sch", ["version", core.SCH_VERSION], ["generator", '"eeschema"'],
               ["generator_version", '"10.0"'], ["uuid", _q(self.root)], ["paper", _q(self.paper)], tb,
               ["lib_symbols"] + self.lib_symbols] + self.items + [
               ["sheet_instances", ["path", '"/"', ["page", '"1"']]], ["embedded_fonts", "no"]]
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(dump_sexpr(sch) + "\n")
