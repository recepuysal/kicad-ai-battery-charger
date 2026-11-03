"""KiCad netlistini EasyEDA ciziminden cikarilan beklenen baglantilarla karsilastirir."""
import sys
import xml.etree.ElementTree as E

EXPECT = {
    "VBUS": "USB1.A9 USB1.B9 D3.1 R7.2 D2.2 Q1.1 U6.4 U6.8 C2.2 C8.2 TP1.1 R18.1 R6.2 R11.2",
    "GND": ("USB1.A12 USB1.B12 USB1.7 R2.1 R3.1 D3.2 U6.3 U6.9 R9.1 C2.1 C8.1 C6.1 Q3.3 R8.1 "
            "R7.1 U1.2 R1.1 C1.1 C3.1 C4.1 U9.2 C12.1 C9.1 C11.1 C10.1 C13.1 R12.1 Q2.2 R14.1 J1.8 TP4.1 "
            "R16.1 R17.1 R20.1 C14.1 SW2.3 R21.1"),
    "CC1": "USB1.A5 R3.2",
    "CC2": "USB1.B5 R2.2",
    "PROG": "U6.2 R9.2 TP6.1",
    "BAT+": "U6.5 C6.2 J7.1 R5.1 Q1.3 Q4.2 R13.2 TP5.1",
    "BAT-": "J7.3 U2.6 C7.1 Q3.1 R21.2",
    "NTC": "J7.2 U6.1 R18.2 R19.1",
    "BAT_TEMP": "R19.2 R20.2 C14.2 J1.7",
    "DW_VCC": "R5.2 U2.5 C7.2",
    "OD": "U2.1 Q3.6",
    "OC": "U2.3 Q3.4",
    "DW_CS": "U2.2 R8.2",
    "VSYS": "D2.1 Q1.2 Q5.2 R15.1",
    "SW_G": "Q5.1 R15.2 SW2.2",
    "VSW": "Q5.3 C1.2 L2.1 U1.5 U1.4",
    "SWN": "L2.2 U1.1 D1.2",
    "5V_OUT": "J1.1 F1.1",
    "+5V": "D1.1 R4.2 C3.2 C4.2 F1.2 TP2.1 U9.1 U9.3 C12.2 C9.2",
    "FB": "R4.1 R1.2 U1.3",
    "+3V3": "U9.5 C11.2 C10.2 J1.2 TP3.1",
    "CHRG": "U6.7 R6.1 R16.2 J1.3",
    "STDBY": "U6.6 R11.1 R17.2 J1.4",
    "BAT_SENSE": "R10.1 R12.2 C13.2 J1.5",
    "Q4G": "Q4.1 R13.1 Q2.3",
    "DIV": "Q4.3 R10.2",
    "BAT_EN": "Q2.1 R14.2 J1.6",
}
UNCONNECTED = set("U2.4 Q3.2 Q3.5 SW2.1 U1.6 U9.4".split())

got = {}
for n in E.parse(sys.argv[1]).getroot().find("nets"):
    pins = frozenset("%s.%s" % (x.get("ref"), x.get("pin")) for x in n)
    got[n.get("name")] = pins
ok = True
gotsets = {p: name for name, p in got.items()}
for name, s in EXPECT.items():
    want = frozenset(s.split())
    if want in gotsets:
        continue
    ok = False
    best = max(got.items(), key=lambda kv: len(kv[1] & want))
    print("FARKLI %-10s eksik=%s fazla=%s (kicad: %s)" % (
        name, sorted(want - best[1]), sorted(best[1] - want), best[0]))
allwant = set().union(*[set(s.split()) for s in EXPECT.values()]) | UNCONNECTED
for name, p in got.items():
    for x in p:
        if x not in allwant and not x.startswith(("H",)):
            ok = False
            print("BEKLENMEYEN pin %s (net %s)" % (x, name))
for x in UNCONNECTED:
    if not any(x in p and len(p) == 1 for p in got.values()):
        ok = False
        print("BAGLI OLMAMALI:", x)
print("NETLIST OK" if ok else "NETLIST HATALI")
