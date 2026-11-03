"""Depo icin: semayi uretir, projeye ozel kutuphaneyi (sembol + footprint + 3B) kopyalar,
lib_id / footprint / 3B yollarini goreli hale getirir."""
import os
import re
import shutil
import subprocess
import sys

PLUGIN, REPO, SCRIPTS = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, PLUGIN)
from lcsc_importer import core  # noqa: E402
from lcsc_importer.core import dump_sexpr, parse_sexpr, _q  # noqa: E402

PROJ = "battery-charger"
NICK = "BatteryCharger"
CLI = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
HW = os.path.join(REPO, "hardware")
LIB = os.path.join(HW, "lib")
os.makedirs(LIB, exist_ok=True)

# 1) semayi uret (LCSC takma adiyla), sonra takma adi degistir
env = dict(os.environ, PROJ_NAME=PROJ, PYTHONIOENCODING="utf-8")
subprocess.run([sys.executable, os.path.join(SCRIPTS, "generate_schematic.py"), PLUGIN, HW],
               check=True, env=env)
sch_path = os.path.join(HW, PROJ + ".kicad_sch")
sch = open(sch_path, encoding="utf-8").read()
used = sorted(set(re.findall(r'\(lib_id "LCSC:([^"]+)"\)', sch)))
fps = sorted(set(re.findall(r'\(property "Footprint" "LCSC:([^"]+)"', sch)))
sch = sch.replace('"LCSC:', '"%s:' % NICK)
open(sch_path, "w", encoding="utf-8", newline="\n").write(sch)

# 2) sembol kutuphanesi
def renick(node):
    if isinstance(node, list):
        return [renick(n) for n in node]
    return node.replace('"LCSC:', '"%s:' % NICK) if isinstance(node, str) else node


syms = [renick(core._modern_symbol(name)) for name in used]
lib = ["kicad_symbol_lib", ["version", "20251024"], ["generator", '"kicad_symbol_editor"'],
       ["generator_version", '"10.0"']] + syms
symfile = os.path.join(LIB, NICK + ".kicad_sym")
open(symfile, "w", encoding="utf-8", newline="\n").write(dump_sexpr(lib) + "\n")

# 3) footprint + 3B modeller
src_pretty = os.path.join(core.LIB_DIR, "LCSC.pretty")
src_3d = os.path.join(core.LIB_DIR, "LCSC.3dshapes")
dst_pretty = os.path.join(LIB, NICK + ".pretty")
dst_3d = os.path.join(LIB, NICK + ".3dshapes")
os.makedirs(dst_pretty, exist_ok=True)
os.makedirs(dst_3d, exist_ok=True)
fp_names = [f for f in fps if os.path.exists(os.path.join(src_pretty, f + ".kicad_mod"))]
missing = [f for f in fps if f not in fp_names]
for f in fp_names:
    t = open(os.path.join(src_pretty, f + ".kicad_mod"), encoding="utf-8").read()

    def fix(m):
        p = m.group(1).replace("\\", "/")
        base = os.path.basename(p)
        stem = os.path.splitext(base)[0]
        for ext in (".wrl", ".step"):
            srcm = os.path.join(src_3d, stem + ext)
            if os.path.exists(srcm):
                shutil.copyfile(srcm, os.path.join(dst_3d, stem + ext))
        return '(model "${KIPRJMOD}/lib/%s.3dshapes/%s"' % (NICK, base)
    t = re.sub(r'\(model "([^"]+)"', fix, t)
    open(os.path.join(dst_pretty, f + ".kicad_mod"), "w", encoding="utf-8", newline="\n").write(t)

# 4) proje kutuphane tablolari
open(os.path.join(HW, "sym-lib-table"), "w", encoding="utf-8", newline="\n").write(
    '(sym_lib_table\n\t(version 7)\n\t(lib (name "%s") (type "KiCad") (uri "${KIPRJMOD}/lib/%s.kicad_sym") '
    '(options "") (descr "Bu projede kullanilan LCSC parcalari"))\n)\n' % (NICK, NICK))
open(os.path.join(HW, "fp-lib-table"), "w", encoding="utf-8", newline="\n").write(
    '(fp_lib_table\n\t(version 7)\n\t(lib (name "%s") (type "KiCad") (uri "${KIPRJMOD}/lib/%s.pretty") '
    '(options "") (descr "Bu projede kullanilan LCSC footprintleri"))\n)\n' % (NICK, NICK))

print("semboller:", len(used), "footprint:", len(fp_names), "eksik:", missing,
      "3B:", len(os.listdir(dst_3d)))
