"""Li-ion guc modulu: USB-C + TP4056 + DW01A/FS8205A + yuk paylasimi + MT3608 + AP2112K + pil olcumu."""
import json
import os
import sys

sys.path.insert(0, sys.argv[1])
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sch_lib import Sheet  # noqa: E402

OUT = sys.argv[2]
NAME = os.environ.get("PROJ_NAME", "Li-ion_Guc_Modulu")
S = Sheet(NAME, "A3")
P, W, J, L, NC = S.power, S.wire, S.junction, S.label, S.nc

# dikey pasif: pin2 ustte, pin1 altta; yazilar saga
VF = {"Reference": (2.54, -1.27, "left"), "Value": (2.54, 1.27, "left")}
HF = {"Reference": (0, -2.54, None), "Value": (0, 2.54, None)}


def vpart(lib, ref, x, ytop, val, dnp=False):
    """Ustu ytop'ta olan dikey 2 pinli parca. (ust, alt) pinlerini dondurur."""
    p = S.place("LCSC:" + lib, ref, x, ytop + 5.08, val, rot=90, fields=VF, dnp=dnp)
    return p["2"], p["1"]


R100K, R10K, R75K, R100, R1K, R1K2, R5K1 = ("0603WAF1003T5E", "0603WAF1002T5E", "0603WAF7502T5E",
                                             "0603WAF1000T5E", "0603WAF1001T5E", "0603WAF1201T5E",
                                             "0603WAF5101T5E")
R6K2, R150K, R15K, R22K = "0603WAF6201T5E", "0603WAF1503T5E", "0603WAF1502T5E", "0603WAF2202T5E"
C100N, C10U, C22U = "CL10B104KB8NNNC", "CL21A106KAYNNNE", "CL21A226MAQNNNE"

# =================================================================== 1 USB-C
S.block("1 · USB-C GİRİŞ + ESD", 15.24, 20.32, 139.7, 106.68)
USB = S.place("LCSC:TYPE-C6P", "USB1", 40.64, 60.96, "TYPE-C 6P", mirror="y",
              fields={"Reference": (0, -12.7, None), "Value": (0, 12.7, None)})
P("GND", USB["B12"])
P("GND", USB["A12"])
P("GND", USB["7"])
bus_y, jx, end_x = USB["B9"][1], 66.04, 91.44
W(USB["B9"], (end_x, bus_y))
W(USB["A9"], (jx, USB["A9"][1]), (jx, bus_y))
J(jx, bus_y)
L(USB["A5"], "CC1")
L(USB["B5"], "CC2")
D3 = S.place("LCSC:ESDA7P120-1U1M", "D3", 78.74, bus_y + 5.08, "ESDA7P120", rot=270, fields=VF)
J(78.74, bus_y)
P("GND", D3["2"])
P("VBUS", (end_x, bus_y, 270), 0)
t, b = vpart(R5K1, "R3", 33.02, 80.01, "5.1k"); L(t, "CC1"); P("GND", b)
t, b = vpart(R5K1, "R2", 50.8, 80.01, "5.1k"); L(t, "CC2"); P("GND", b)
S.note("CC1/CC2 5.1k: USB-C kaynağından\n5 V talep eder (sink)", 66.04, 82.55)
S.note("D3: VBUS ESD koruması (TVS)", 66.04, 76.2)

# =================================================================== 2 SARJ
S.block("2 · Li-ion ŞARJ (TP4056, 1 A)", 144.78, 20.32, 269.24, 106.68)
U6 = S.place("LCSC:TP4056_C725790", "U6", 213.36, 60.96, "TP4056", mirror="x",
             fields={"Reference": (0, -12.7, None), "Value": (0, 12.7, None)})
vy = U6["4"][1]
W(U6["4"], (147.32, vy))
for x in (162.56, 152.4):
    J(x, vy)
t, b = vpart(C10U, "C2", 162.56, vy, "10uF"); P("GND", b)
t, b = vpart(C100N, "C8", 152.4, vy, "100nF"); P("GND", b)
P("VBUS", (147.32, vy, 270), 0)
P("GND", U6["3"])
L(U6["1"], "NTC")
py = U6["2"][1]
W(U6["2"], (182.88, py))
J(187.96, py)
t, b = vpart(R1K2, "R9", 187.96, py, "1.2k"); P("GND", b)
L((182.88, py, 0), "PROG", 0)
L(U6["5"], "BAT+", 10.16)
L(U6["6"], "~{STDBY}", 10.16)
L(U6["7"], "~{CHRG}", 10.16)
P("VBUS", U6["8"])
P("GND", U6["9"])
S.note("R9 (PROG) → şarj akımı: 1.2k ≈ 1 A\n2k ≈ 580 mA · 3k ≈ 400 mA\nTEMP: pil NTC (blok 10)", 152.4, 86.36)
S.note("~{CHRG} / ~{STDBY}: açık-drain çıkış,\nçekme dirençleri blok 8'de", 210.82, 86.36)

# =================================================================== 3 PIL + KORUMA
S.block("3 · PİL + KORUMA (DW01A + FS8205A, opsiyonel)", 274.32, 20.32, 403.86, 106.68)
J7 = S.place("LCSC:B3B-XH-A", "J7", 289.56, 58.42, "PİL 3P", rot=270,
             fields={"Reference": (-2.54, -6.35, None), "Value": (-2.54, 6.35, None)})
L(J7["1"], "BAT+", 5.08)
L(J7["2"], "NTC", 5.08)
L(J7["3"], "BAT-", 5.08)
t, b = vpart(C10U, "C6", 304.8, 66.04, "10uF"); L(t, "BAT+"); P("GND", b)
U2 = S.place("LCSC:DW01A_C351410", "U2", 345.44, 45.72, "DW01A", mirror="y", dnp=True,
             fields={"Reference": (0, -7.62, None), "Value": (0, 7.62, None)})
Q3 = S.place("LCSC:FS8205A_C2830320", "Q3", 345.44, 81.28, "FS8205A", mirror="x", dnp=True,
             fields={"Reference": (0, -8.89, None), "Value": (0, -6.35, None)})
# OC -> G2 (ic), OD -> G1 (dis)
W(U2["3"], (363.22, U2["3"][1]), (363.22, Q3["4"][1]), Q3["4"])
W(U2["1"], (368.3, U2["1"][1]), (368.3, Q3["6"][1]), Q3["6"])
L(U2["2"], "DW_CS", 0)
NC(U2["4"])
L(U2["6"], "BAT-", 2.54)
vx = U2["5"][1]
W(U2["5"], (312.42, vx))
J(325.12, vx)
R5 = S.place("LCSC:" + R100, "R5", 307.34, vx, "100R", fields=HF, dnp=True)
L(R5["1"], "BAT+", 2.54)
t, b = vpart(C100N, "C7", 325.12, vx, "100nF", dnp=True); L(b, "BAT-")
t, b = vpart("0603WAF0000T5E", "R21", 320.04, 66.04, "0R"); L(t, "BAT-"); P("GND", b)
P("GND", Q3["3"])
L(Q3["1"], "BAT-", 2.54)
NC(Q3["2"]); NC(Q3["5"])
t, b = vpart(R1K, "R8", 381.0, 71.12, "1k", dnp=True); L(t, "DW_CS"); P("GND", b)
S.note("Korumalı (devreli) pil: U2, Q3, R5, C7, R8 takılmaz (DNP), R21 = 0Ω köprü\nKorumasız pil: U2, Q3, R5, C7, R8 takılır, R21 SÖKÜLÜR (ikisi birlikte olmaz!)\nJ7: 1 = BAT+  2 = NTC  3 = BAT− (pil kablosuna göre kontrol!)\nBAT- = pil eksi ucu, GND = koruma sonrası (P-)\nDW01A: 4.3 V aşırı şarj · 2.4 V aşırı deşarj\naşırı akım / kısa devre kesmesi", 279.4, 87.63)

# =================================================================== 4 GUC YOLU
S.block("4 · GÜÇ YOLU + ANAHTAR", 15.24, 111.76, 139.7, 190.5)
y0 = 137.16
P("VBUS", (27.94, y0, 270), 0)
D2 = S.place("LCSC:SS34_C2837271", "D2", 50.8, y0, "SS34", mirror="y",
             fields={"Reference": (0, -5.08, None), "Value": (0, -2.54, None)})
W((27.94, y0), D2["2"])
J(33.02, y0); J(40.64, y0)
t, b = vpart(R100K, "R7", 33.02, y0, "100k"); P("GND", b)
Q1 = S.place("LCSC:AO3401A", "Q1", 60.96, y0 + 5.08, "AO3401A", mirror="x",
             fields={"Reference": (5.08, -1.27, "left"), "Value": (5.08, 1.27, "left")})
W(Q1["1"], (40.64, Q1["1"][1]), (40.64, y0))
Q5 = S.place("LCSC:AO3401A", "Q5", 86.36, y0 - 2.54, "AO3401A", rot=270,
             fields={"Reference": (6.35, -3.81, "left"), "Value": (6.35, -1.27, "left")})
W(D2["1"], (Q1["2"][0], y0), (76.2, y0), Q5["2"])
J(Q1["2"][0], y0); J(76.2, y0)
gy = y0 - 10.16
t, b = vpart(R100K, "R15", 76.2, gy, "100k")
W(Q5["1"], (86.36, gy), (76.2, gy))
SW2 = S.place("LCSC:SS12D10G4071", "SW2", 95.25, gy - 8.89, "SS12D10G4",
              fields={"Reference": (7.62, -1.27, "left"), "Value": (7.62, 1.27, "left")})
W((86.36, gy), (SW2["2"][0], gy), SW2["2"])
J(86.36, gy)
NC(SW2["1"])
P("GND", SW2["3"])
W(Q1["3"], (Q1["3"][0], Q1["3"][1] + 2.54))
L((Q1["3"][0], Q1["3"][1] + 2.54, 90), "BAT+", 0)
W(Q5["3"], (106.68, y0))
L((106.68, y0, 180), "VSW", 0)
L((66.04, y0, 180), "VSYS", 0)
S.note("USB varken: VBUS → D2 → VSYS, Q1 kapalı (Vgs ≈ 0)\nUSB yokken: R7 kapıyı GND'ye çeker,\nQ1 iletir, pil → VSYS (yük paylaşımı)\nSW2 → Q5 yük anahtarı: SW2 kapıyı GND'ye\nçekince Q5 iletir (VSYS → VSW, ~2 A).\nAnahtar akım taşımaz, yalnızca kapıyı sürer.", 20.32, 162.56)

# =================================================================== 5 BOOST
S.block("5 · 5 V BOOST (MT3608)", 144.78, 111.76, 269.24, 190.5)
ry = 139.7
L((160.02, ry, 0), "VSW", 0)
W((160.02, ry), (200.66, ry))
J(172.72, ry); J(187.96, ry)
t, b = vpart(C22U, "C1", 172.72, ry, "22uF"); P("GND", b)
U1 = S.place("LCSC:MT3608", "U1", 205.74, 152.4, "MT3608", mirror="y",
             fields={"Reference": (0, -7.62, None), "Value": (0, 7.62, None)})
W((187.96, ry), (187.96, U1["5"][1]), U1["5"])
W(U1["4"], (187.96, U1["4"][1]), (187.96, U1["5"][1]))
J(187.96, U1["5"][1])
NC(U1["6"])
L2 = S.place("LCSC:FXL0630-100-M", "L2", 205.74, ry, "10uH 4.5A", fields=HF)
W((200.66, ry), L2["1"])
W(L2["2"], (220.98, ry))
W((220.98, ry), (220.98, U1["1"][1]), U1["1"])
D1 = S.place("LCSC:SS34_C2837271", "D1", 231.14, ry, "SS34", mirror="y",
             fields={"Reference": (0, -5.08, None), "Value": (0, -2.54, None)})
W((220.98, ry), D1["2"])
J(220.98, ry)
W(D1["1"], (266.7, ry))
for x in (238.76, 248.92, 259.08):
    J(x, ry)
t, b = vpart(R75K, "R4", 238.76, ry, "75k")
fb = U1["3"][1]
t2, b2 = vpart(R10K, "R1", 238.76, fb, "10k")
W(b, t2)
W(U1["3"], (238.76, fb))
J(238.76, fb)
P("GND", b2)
P("GND", U1["2"])
t, b = vpart(C22U, "C3", 248.92, ry, "22uF"); P("GND", b)
t, b = vpart(C22U, "C4", 259.08, ry, "22uF"); P("GND", b)
P("+5V", (266.7, ry, 270), 0)
S.note("Vout = 0.6 V × (1 + R4/R1) = 5.1 V\n5 V / 1 A çıkış (3.3 V tüketimi dahil)\nL2 10 µH 4.5 A: pil 3.0 V'ta ~2.2 A tepe akımı", 149.86, 172.72)

# =================================================================== 6 LDO
S.block("6 · 3.3 V LDO (AP2112K)", 274.32, 111.76, 403.86, 152.4)
U9 = S.place("LCSC:AP2112K-3.3TRG1", "U9", 340.36, 132.08, "AP2112K-3.3",
             fields={"Reference": (0, -7.62, None), "Value": (0, 7.62, None)})
iy = U9["1"][1]
P("+5V", (284.48, iy, 270), 0)
W((284.48, iy), U9["1"])
for x in (297.18, 307.34, 320.04):
    J(x, iy)
t, b = vpart(C10U, "C12", 297.18, iy, "10uF"); P("GND", b)
t, b = vpart(C100N, "C9", 307.34, iy, "100nF"); P("GND", b)
W(U9["3"], (320.04, U9["3"][1]), (320.04, iy))
P("GND", U9["2"])
oy = U9["5"][1]
W(U9["5"], (391.16, oy))
for x in (365.76, 375.92):
    J(x, oy)
t, b = vpart(C10U, "C11", 365.76, oy, "10uF"); P("GND", b)
t, b = vpart(C100N, "C10", 375.92, oy, "100nF"); P("GND", b)
P("+3V3", (391.16, oy, 270), 0)
NC(U9["4"])
S.note("Giriş +5V (boost çıkışı): pil 3.0 V'a inse de 3.3 V sabit kalır", 279.4, 148.59)

# =================================================================== 10 NTC
S.block("10 · PİL SICAKLIĞI (NTC)", 274.32, 157.48, 403.86, 190.5)
ny = 170.18
P("VBUS", (284.48, ny, 270), 0)
R18 = S.place("LCSC:" + R6K2, "R18", 294.64, ny, "6.2k", fields=HF)
W((284.48, ny), R18["1"])
R19 = S.place("LCSC:" + R100K, "R19", 325.12, ny, "100k", fields=HF)
W(R18["2"], R19["1"])
J(307.34, ny)
W((307.34, ny), (307.34, ny + 5.08))
L((307.34, ny + 5.08, 90), "NTC", 0)
W(R19["2"], (360.68, ny))
J(340.36, ny); J(350.52, ny)
t, b = vpart(R150K, "R20", 340.36, ny, "150k"); P("GND", b)
t, b = vpart(C100N, "C14", 350.52, ny, "100nF"); P("GND", b)
L((360.68, ny, 180), "BAT_TEMP", 0)
S.note("NTC pil içinde (10k B3435), diğer ucu BAT−\nTP4056: 0–45 °C dışında şarjı durdurur\nBAT_TEMP = 0.6 × V_NTC (yalnızca USB takılıyken)", 279.4, 180.34)

# =================================================================== 7 PIL OLCUM
S.block("7 · PİL GERİLİMİ ÖLÇÜMÜ", 15.24, 195.58, 139.7, 279.4)
top = 210.82
L((30.48, top, 0), "BAT+", 0)
Q4 = S.place("LCSC:AO3401A", "Q4", 50.8, 220.98, "AO3401A", mirror="x",
             fields={"Reference": (5.08, -1.27, "left"), "Value": (5.08, 1.27, "left")})
sx = Q4["2"][0]
W((30.48, top), (sx, top), Q4["2"])
J(40.64, top)
t, b = vpart(R100K, "R13", 40.64, top, "100k")
W(Q4["1"], b)
Q2 = S.place("LCSC:PJA3406-AU-R1-000A1", "Q2", 39.37, 238.76, "PJA3406",
             fields={"Reference": (5.08, -1.27, "left"), "Value": (5.08, 1.27, "left")})
W(b, Q2["3"])
J(*b[:2])
P("GND", Q2["2"])
W(Q2["1"], (25.4, Q2["1"][1]))
J(30.48, Q2["1"][1])
L((25.4, Q2["1"][1], 0), "BAT_EN", 0)
t, b = vpart(R100K, "R14", 30.48, Q2["1"][1], "100k"); P("GND", b)
t, b = vpart(R10K, "R10", sx, Q4["3"][1], "10k")
W(Q4["3"], t)
mid = b[1] + 2.54
t2, b2 = vpart(R10K, "R12", sx, mid + 2.54, "10k")
W(b, t2)
P("GND", b2)
W((sx, mid), (81.28, mid))
J(sx, mid); J(68.58, mid)
t, b = vpart(C100N, "C13", 68.58, mid, "100nF"); P("GND", b)
L((81.28, mid, 180), "BAT_SENSE", 0)
S.note("BAT_EN = 1 → Q2 iletir, Q4 açılır, ölçüm yapılır\nBAT_EN = 0 → bölücü kapalı (pil boşalmaz)\nBAT_SENSE = VBAT / 2  (4.2 V → 2.1 V)", 20.32, 260.35)

# =================================================================== 8 MCU KONNEKTORU
S.block("8 · İŞLEMCİ KONNEKTÖRÜ", 144.78, 195.58, 269.24, 279.4)
J1 = S.place("LCSC:B8B-XH-A", "J1", 162.56, 236.22, "B8B-XH-A", mirror="y",
             fields={"Reference": (0, -12.7, None), "Value": (0, 12.7, None)})
F1 = S.place("LCSC:FSMD100-2920-R", "F1", 179.07, J1["1"][1], "1.1A PTC",
             fields={"Reference": (0, -5.08, None), "Value": (0, -2.54, None)})
W(J1["1"], F1["1"])
P("+5V", F1["2"])
P("+3V3", J1["2"])
for pin, net in (("3", "~{CHRG}"), ("4", "~{STDBY}"), ("5", "BAT_SENSE"), ("6", "BAT_EN"), ("7", "BAT_TEMP")):
    L(J1[pin], net, 12.7)
P("GND", J1["8"], 2.54)
# ~CHRG / ~STDBY cekmeleri USB'den: USB yokken ikisi de 0 okunur (USB yok bilgisi)
for rt, rb, x, net in (("R6", "R16", 228.6, "~{CHRG}"), ("R11", "R17", 246.38, "~{STDBY}")):
    P("VBUS", (x, 222.25, 270), 0)
    t, b = vpart(R15K, rt, x, 222.25, "15k")
    t2, b2 = vpart(R22K, rb, x, 237.49, "22k")
    W(b, t2)
    J(x, 234.95)
    W((x, 234.95), (x + 2.54, 234.95))
    L((x + 2.54, 234.95, 180), net, 0)
    P("GND", b2)
S.note("1  +5V        5 V çıkış (boost, F1 1.1 A PTC)\n2  +3V3       3.3 V çıkış (LDO)\n"
       "3  CHRG       açık-drain durum\n4  STDBY      açık-drain durum\n"
       "5  BAT_SENSE  analog, VBAT/2\n6  BAT_EN     yüksek = ölçümü aç\n"
       "7  BAT_TEMP   analog, pil sıcaklığı\n8  GND", 218.44, 200.66)
S.note("CHRG STDBY  durum\n  0     0    USB yok (pilden çalışıyor)\n  0     1    şarj oluyor\n"
       "  1     0    şarj tamam\n  1     1    USB var, pil yok / sıcaklık hatası\n"
       "Çekmeler VBUS'tan (15k/22k ≈ 3.1 V):\nUSB yokken hatlar 0 olur, TP4056'ya sızıntı olmaz", 149.86, 256.54)

# =================================================================== 9 TEST + MEKANIK
S.block("9 · TEST NOKTALARI + MONTAJ", 274.32, 195.58, 403.86, 248.92)
tp_fp = "TestPoint:TestPoint_Pad_D2.0mm"
for i, (net, kind) in enumerate((("VBUS", "p"), ("+5V", "p"), ("+3V3", "p"), ("GND", "g"),
                                 ("BAT+", "l"), ("PROG", "l"))):
    x = 289.56 + i * 15.24
    tp = S.place("LCSC:TestPoint", "TP%d" % (i + 1), x, 218.44, net, props={"Footprint": tp_fp},
                 fields={"Reference": (0, -8.89, None), "Value": (0, -6.35, None)})
    if kind == "g":
        P("GND", tp["1"], 2.54)
    elif kind == "p":
        W(tp["1"], (x, 223.52))
        S.place("power:" + net, "#PWR", x, 223.52, rot=180, fields={"Value": (0, 3.81, None)})
    else:
        L(tp["1"], net, 5.08)
for i in range(4):
    S.place("LCSC:MountingHole", "H%d" % (i + 1), 289.56 + i * 15.24, 241.3, "M3",
            props={"Footprint": "MountingHole:MountingHole_3.2mm_M3"},
            fields={"Reference": (0, -3.81, None), "Value": (0, 3.81, None)})
# PWR_FLAG: kaynaklar
for i, net in enumerate(("VBUS", "GND", "+5V", "+3V3")):
    x = 383.54 if i < 2 else 396.24
    y = 208.28 + (i % 2) * 15.24
    S.place("power:PWR_FLAG", "#FLG", x, y, fields={"Value": (0, -3.81, None)})
    if net == "GND":
        S.place("power:GND", "#PWR", x, y, fields={"Value": (0, 3.81, None)})
    else:
        S.place("power:" + net, "#PWR", x, y + 2.54, rot=180, fields={"Value": (0, 3.81, None)})
        W((x, y), (x, y + 2.54))

os.makedirs(OUT, exist_ok=True)
S.save(os.path.join(OUT, NAME + ".kicad_sch"), [
    ("title", "Li-ion Güç Modülü (USB-C şarj, koruma, 5 V / 3.3 V)"),
    ("date", "2026-11-03"), ("rev", "1.0"),
    ("comment1", "TP4056 şarj · DW01A+FS8205A koruma · MT3608 5 V · AP2112K 3.3 V"),
    ("comment2", "EasyEDA çiziminden aktarıldı")])
pro = os.path.join(OUT, NAME + ".kicad_pro")
if not os.path.exists(pro):
    with open(pro, "w", encoding="utf-8") as f:
        json.dump({"meta": {"filename": NAME + ".kicad_pro", "version": 3},
                   "sheets": [[S.root, "Root"]]}, f, indent=2)
print("ok")
