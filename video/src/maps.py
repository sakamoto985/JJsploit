"""Animated maps of the Russian Civil War (Albers conic projection of real country outlines)."""
import json, math, functools, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from common import *

GEO = os.environ.get("GEO_DIR")
LON0, LAT1, LAT2, LATO = 95.0, 50.0, 70.0, 55.0
_n = (math.sin(math.radians(LAT1)) + math.sin(math.radians(LAT2))) / 2
_C = math.cos(math.radians(LAT1)) ** 2 + 2 * _n * math.sin(math.radians(LAT1))
_rho0 = math.sqrt(_C - 2 * _n * math.sin(math.radians(LATO))) / _n

FORMER_EMPIRE = ["RUS", "UKR", "BLR", "KAZ", "UZB", "TKM", "KGZ", "TJK", "GEO", "ARM", "AZE"]
CONTEXT = FORMER_EMPIRE + ["FIN", "EST", "LVA", "LTU", "POL", "MDA", "ROU", "MNG", "CHN", "TUR", "IRN", "AFG", "NOR", "SWE",
                           "JPN", "KOR", "PRK", "PAK", "IND", "BGR", "HUN", "SVK", "CZE", "DEU", "AUT", "SRB", "GRC", "IRQ", "SYR", "NPL", "BTN", "MMR", "VNM", "LAO", "BGD", "DNK"]

# content box on screen
BOX = (60, 150, 1860, 860)


def proj_raw(lon, lat):
    if lon < -60:
        lon += 360
    th = _n * math.radians(lon - LON0)
    rho = math.sqrt(max(_C - 2 * _n * math.sin(math.radians(lat)), 0)) / _n
    return rho * math.sin(th), _rho0 - rho * math.cos(th)


# fit the former Russian Empire region into BOX
def _fit():
    xs, ys = [], []
    for iso in ("RUS", "UKR", "KAZ", "BLR"):
        g = json.load(open(f"{GEO}/countries/{iso}.geo.json"))
        for f in g["features"]:
            geom = f["geometry"]
            polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
            for poly in polys:
                for lo, la in poly[0]:
                    if la > 77.5:  # skip far arctic islands for a tighter fit
                        continue
                    x, y = proj_raw(lo, la); xs.append(x); ys.append(y)
    return min(xs), max(xs), min(ys), max(ys)


_x0, _x1, _y0, _y1 = _fit()
SCALE = min((BOX[2] - BOX[0]) / (_x1 - _x0), (BOX[3] - BOX[1]) / (_y1 - _y0))
OX = (BOX[0] + BOX[2]) / 2 - SCALE * (_x1 + _x0) / 2
OY = (BOX[1] + BOX[3]) / 2 + SCALE * (_y1 + _y0) / 2


def P(lon, lat):
    x, y = proj_raw(lon, lat)
    return OX + x * SCALE, OY - y * SCALE


def _polys(iso):
    g = json.load(open(f"{GEO}/countries/{iso}.geo.json"))
    out = []
    for f in g["features"]:
        geom = f["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        for poly in polys:
            ring = poly[0]
            if iso == "RUS" and min(p[0] for p in ring) < -150 and max(p[0] for p in ring) > 150:
                pass
            out.append([P(lo, la) for lo, la in ring])
    return out


@functools.lru_cache(maxsize=1)
def base_layers():
    s = 2
    sea = vgrad(W, H, hexc("0B1A2E"), hexc("07111F")).convert("RGB")
    d = Draw(sea)
    # graticule
    for lon in range(0, 200, 10):
        pts = [P(lon, la) for la in range(30, 86, 2)]
        d.line(pts, fill=(40, 70, 110, 70), width=1)
    for lat in range(30, 90, 10):
        pts = [P(lo, lat) for lo in range(0, 200, 2)]
        d.line(pts, fill=(40, 70, 110, 70), width=1)
    land = Image.new("RGBA", (W * s, H * s), (0, 0, 0, 0)); ld = Draw(land)
    emp = Image.new("L", (W * s, H * s), 0); ed = Draw(emp)
    for iso in CONTEXT:
        if not os.path.exists(f"{GEO}/countries/{iso}.geo.json"):
            continue
        inside = iso in FORMER_EMPIRE
        for poly in _polys(iso):
            pts = [(x * s, y * s) for x, y in poly]
            if len(pts) < 3:
                continue
            ld.polygon(pts, fill=(58, 72, 92, 255) if inside else (34, 44, 60, 255), outline=(20, 28, 40, 255))
            if inside:
                ed.polygon(pts, fill=255)
    land = down(land, s)
    emp = emp.resize((W, H), Image.LANCZOS)
    # coast glow
    glow = Image.new("RGBA", (W, H), (90, 150, 230, 0)); glow.putalpha(land.getchannel("A").filter(ImageFilter.GaussianBlur(6)).point(lambda v: v // 3))
    comp(sea, glow)
    comp(sea, land)
    # empire outline (former Russian Empire region)
    edge = emp.filter(ImageFilter.FIND_EDGES).point(lambda v: 255 if v > 40 else 0)
    ol = Image.new("RGBA", (W, H), (180, 200, 230, 0)); ol.putalpha(edge.point(lambda v: v * 0.55))
    comp(sea, ol)
    comp(sea, vignette(W, H, .5))
    return sea, emp


CITIES = {
    "Petrograd": (30.3, 59.94), "Moscow": (37.62, 55.75), "Kazan": (49.1, 55.8), "Omsk": (73.4, 55.0),
    "Arkhangelsk": (40.5, 64.54), "Murmansk": (33.1, 68.97), "Vladivostok": (131.9, 43.12), "Odessa": (30.73, 46.48),
    "Irkutsk": (104.3, 52.3), "Tsaritsyn": (44.5, 48.7), "Kiev": (30.52, 50.45), "Sevastopol": (33.52, 44.6),
    "Yekaterinburg": (60.6, 56.84), "Rostov": (39.7, 47.23), "Krasnoyarsk": (92.87, 56.0), "Novonikolayevsk": (82.9, 55.0),
    "Chita": (113.5, 52.03), "Khabarovsk": (135.07, 48.48), "Perm": (56.25, 58.0), "Samara": (50.1, 53.2), "Vologda": (39.9, 59.2),
    "Baku": (49.87, 40.4), "Kharkov": (36.23, 49.99), "Voronezh": (39.2, 51.67),
}

RAILS = [
    ["Moscow", "Perm", "Yekaterinburg", "Omsk", "Novonikolayevsk", "Krasnoyarsk", "Irkutsk", "Chita", "Khabarovsk", "Vladivostok"],
    ["Moscow", "Petrograd"], ["Moscow", "Vologda", "Arkhangelsk"], ["Petrograd", "Murmansk"],
    ["Moscow", "Kazan", "Yekaterinburg"], ["Moscow", "Samara", "Omsk"], ["Moscow", "Voronezh", "Rostov"],
    ["Moscow", "Kharkov", "Sevastopol"], ["Moscow", "Kiev", "Odessa"], ["Voronezh", "Tsaritsyn"],
]

CORE = [(27, 60.5), (31, 62.5), (38, 63.0), (46, 61.8), (52, 59.5), (55, 56.5), (53, 53.5), (48, 51.8), (42, 51.0),
        (36, 51.4), (31, 52.5), (28.5, 55), (27, 58)]


LABEL_SIDE = {"Petrograd": "l", "Odessa": "l", "Kiev": "l", "Sevastopol": "l", "Rostov": "l"}


def _city(img, name, t_in, label=True, color=WHITE, size=9, ring=True, label_side=None):
    label_side = label_side or LABEL_SIDE.get(name, "r")
    a = anim(t_in, 0, .5)
    if a <= 0:
        return
    x, y = P(*CITIES[name])
    d = Draw(img)
    if ring:
        rr = size + 18 * ((t_in * 0.8) % 1.0)
        d.ellipse((x - rr, y - rr, x + rr, y + rr), outline=with_alpha(color, (1 - (t_in * 0.8) % 1.0) * a), width=2)
    r = size * back(a)
    d.ellipse((x - r, y - r, x + r, y + r), fill=with_alpha(color, a), outline=(0, 0, 0, int(200 * a)), width=2)
    if label:
        f = font("bold", 26)
        tx = x + 16 if label_side == "r" else x - 16
        anc = "lm" if label_side == "r" else "rm"
        draw_text(img, (tx + 2, y + 2), name.upper(), f, (0, 0, 0, 255), anchor=anc, alpha=a * .8)
        draw_text(img, (tx, y), name.upper(), f, WHITE, anchor=anc, alpha=a)


def _poly_fill(img, pts_ll, color, a, blur=0, mask=None):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    Draw(lay).polygon([P(*p) for p in pts_ll], fill=with_alpha(color, a))
    if blur:
        lay = lay.filter(ImageFilter.GaussianBlur(blur))
    if mask is not None:
        lay.putalpha(Image.fromarray((np.array(lay.getchannel("A"), np.uint16) * np.array(mask, np.uint16) // 255).astype(np.uint8)))
    comp(img, lay)


def _polyline_partial(pts, frac):
    if frac >= 1:
        return pts
    segs = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    total = sum(segs) * frac
    out = [pts[0]]
    for i, sl in enumerate(segs):
        if total >= sl:
            out.append(pts[i + 1]); total -= sl
        else:
            r = total / sl if sl else 0
            out.append((pts[i][0] + (pts[i + 1][0] - pts[i][0]) * r, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * r))
            break
    return out


def _arrow(img, p0, p1, frac, color, width=8, label=None, lab_off=(0, -30), curve=0.25):
    a = clamp(frac * 3)
    if frac <= 0:
        return
    mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
    nx, ny = -(p1[1] - p0[1]), (p1[0] - p0[0])
    c = (mx + nx * curve, my + ny * curve)
    pts = [((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * c[0] + u ** 2 * p1[0], (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * c[1] + u ** 2 * p1[1])
           for u in np.linspace(0, ease(frac), 40)]
    d = Draw(img)
    d.line(pts, fill=(0, 0, 0, int(150 * a)), width=width + 6, joint="curve")
    d.line(pts, fill=with_alpha(color, a), width=width, joint="curve")
    if len(pts) > 2:
        (x0, y0), (x1, y1) = pts[-3], pts[-1]
        ang = math.atan2(y1 - y0, x1 - x0); L = 30
        tri = [(x1 + math.cos(ang) * 10, y1 + math.sin(ang) * 10),
               (x1 + math.cos(ang + 2.5) * L, y1 + math.sin(ang + 2.5) * L),
               (x1 + math.cos(ang - 2.5) * L, y1 + math.sin(ang - 2.5) * L)]
        d.polygon(tri, fill=with_alpha(color, a), outline=(0, 0, 0, int(150 * a)))
    if label and frac > 0.15:
        la = anim(frac, .15, .3)
        f = font("black", 24)
        tw = f.getlength(label)
        x, y = p0[0] + lab_off[0], p0[1] + lab_off[1]
        d.rounded_rectangle((x - tw / 2 - 14, y - 22, x + tw / 2 + 14, y + 22), 8, fill=with_alpha(color, la))
        draw_text(img, (x, y), label, f, (255, 255, 255, 255) if color != CREAM else INK, anchor="mm", alpha=la)


def _boom(img, x, y, t, seed):
    ph = (t * 1.2 + seed * 0.37) % 1.0
    r = 10 + ph * 50
    d = Draw(img)
    d.ellipse((x - r, y - r, x + r, y + r), outline=(255, 180, 80, int(255 * (1 - ph))), width=4)
    rr = 12 * (1 - ph)
    d.polygon(star_pts(x, y, 14 + 6 * (1 - ph), seed * 20, .45), fill=(255, 210, 120, int(255 * (1 - ph * .7))))


def _tag(img, x, y, title, sub, color, a, w=None):
    if a <= 0:
        return
    f1 = font("black", 30); f2 = font("med", 22)
    w = w or max(f1.getlength(title), f2.getlength(sub)) + 40
    p = panel(int(w), 92, fill=(10, 16, 30, 230), border=with_alpha(color, .9), r=10)
    paste(img, p, (x, y + (1 - a) * 20), a)
    d = Draw(img)
    d.rectangle((x, y + (1 - a) * 20 + 8, x + 6, y + (1 - a) * 20 + 84), fill=with_alpha(color, a))
    draw_text(img, (x + 22, y + 32 + (1 - a) * 20), title, f1, color, anchor="lm", alpha=a)
    draw_text(img, (x + 22, y + 66 + (1 - a) * 20), sub, f2, CREAM, anchor="lm", alpha=a)


def _title(img, txt, sub, a):
    f = font("black", 44)
    tracked(img, (200, 66 - (1 - a) * 20), txt, f, WHITE, track=3, alpha=a)
    if sub:
        draw_text(img, (202, 108), sub, font("med", 26), GOLD, anchor="lm", alpha=a)


def render_map(beats, t, frame):
    """beats: list of (visual, t_start_relative). t: seconds since shot start."""
    base, emp = base_layers()
    img = base.copy()
    cur = [b for b in beats if b[1] <= t + 1e-6][-1]
    names = [b[0] for b in beats]
    bt = {b[0]: t - b[1] for b in beats}
    v = cur[0]
    # slow drift zoom handled by caller
    if v in ("map_core", "map_rail"):
        tc = bt["map_core"] if "map_core" in bt else 99
        a = anim(tc, 0.2, 1.0)
        pulse = 0.55 + 0.1 * math.sin(t * 3)
        _poly_fill(img, CORE, RED, a * pulse, blur=8, mask=emp)
        _title(img, "RED HEARTLAND", "Bolshevik-held core of Russia, 1918–1919", anim(tc, 0, .6))
        _city(img, "Moscow", tc - 0.8, color=GOLD, size=12)
        _city(img, "Petrograd", tc - 1.6, color=GOLD, size=12)
        if v == "map_rail":
            tr = bt["map_rail"]
            for i, line in enumerate(RAILS):
                fr = clamp((tr - 0.2 - i * 0.18) / 1.6)
                if fr <= 0:
                    continue
                pts = _polyline_partial([P(*CITIES[c]) for c in line], ease(fr))
                d = Draw(img)
                d.line(pts, fill=(0, 0, 0, 160), width=9, joint="curve")
                d.line(pts, fill=(235, 225, 200, 255), width=5, joint="curve")
                # cross ties
                for k in range(len(pts) - 1):
                    (x0, y0), (x1, y1) = pts[k], pts[k + 1]
                    L = math.dist(pts[k], pts[k + 1]); n = int(L // 18)
                    for j in range(n):
                        u = j / max(n, 1); x = x0 + (x1 - x0) * u; y = y0 + (y1 - y0) * u
                        nx, ny = -(y1 - y0) / L * 6, (x1 - x0) / L * 6
                        d.line((x - nx, y - ny, x + nx, y + ny), fill=(235, 225, 200, 200), width=2)
                # train
                if fr >= 1:
                    full = [P(*CITIES[c]) for c in line]
                    u = ((tr * 0.12 + i * 0.3) % 1.0)
                    pp = _polyline_partial(full, u)[-1]
                    d.rounded_rectangle((pp[0] - 9, pp[1] - 9, pp[0] + 9, pp[1] + 9), 4, fill=RED, outline=WHITE, width=2)
            _tag(img, 1250, 150, "RAILWAYS", "Moving troops & supplies from the centre", GOLD, anim(tr, 1.2, .6))
            for c in ("Kazan", "Omsk", "Vladivostok", "Arkhangelsk", "Odessa", "Tsaritsyn"):
                _city(img, c, tr - 1.0, size=6, ring=False)
    elif v in ("map_foreign", "map_foreign2"):
        tf = bt.get("map_foreign", t)
        _poly_fill(img, CORE, RED, .45, blur=8, mask=emp)
        _title(img, "FOREIGN INTERVENTION", "Allied and Japanese troops land in Russia, 1918–1920", anim(tf, 0, .6))
        UK, FR, US, JP = hexc("1F4FA8"), hexc("2E6BD8"), hexc("3C7DC4"), hexc("D0D0D0")
        arrows = [
            ("BRITAIN", (14, 72), "Murmansk", hexc("2B5CC4"), (0, -36)),
            ("BRITAIN", (20, 71), "Arkhangelsk", hexc("2B5CC4"), (0, 36)),
            ("FRANCE", (20, 42), "Odessa", hexc("4A7FE0"), (0, 40)),
            ("USA", (34, 74), "Arkhangelsk", hexc("6D8FB0"), (0, -36)),
            ("JAPAN", (150, 36), "Vladivostok", hexc("E8E8E8"), (0, 40)),
            ("USA", (156, 42), "Vladivostok", hexc("6D8FB0"), (40, -40)),
            ("BRITAIN", (44, 33), "Baku", hexc("2B5CC4"), (0, 36)),
        ]
        for i, (lab, src, dst, col, off) in enumerate(arrows):
            fr = clamp((tf - 0.4 - i * 0.55) / 1.2)
            p0 = P(*src); p1 = P(*CITIES[dst])
            _arrow(img, p0, p1, fr, col if lab != "JAPAN" else hexc("C8C8C8"), label=lab, lab_off=off)
            if fr >= 1:
                _city(img, dst, (tf - 1.6 - i * .55), size=8, color=GOLD, label=False)
        for c, side in (("Murmansk", "r"), ("Arkhangelsk", "r"), ("Odessa", "l"), ("Vladivostok", "l"), ("Baku", "r")):
            _city(img, c, tf - 1.5, size=6, ring=False, label_side=side)
        if v == "map_foreign2":
            t2 = bt["map_foreign2"]
            a = anim(t2, 0.1, .6)
            p = panel(720, 190, fill=(10, 16, 30, 236), border=(229, 181, 74, 200), r=14)
            paste(img, p, (1130, 110 + (1 - a) * 30), a)
            draw_text(img, (1160, 150 + (1 - a) * 30), "WHY INTERVENE?", font("black", 30), GOLD, anchor="lm", alpha=a)
            for k, line in enumerate(["• Opposed the communist government", "• Feared communism would spread"]):
                ak = anim(t2, .5 + k * .5, .5)
                draw_text(img, (1160, 205 + k * 44 + (1 - ak) * 14), line, font("semi", 30), WHITE, anchor="lm", alpha=ak)
    elif v == "map_fronts":
        tf = bt["map_fronts"]
        _poly_fill(img, CORE, RED, .5, blur=8, mask=emp)
        _title(img, "WAR ON MANY FRONTS", "Fighting stretches across thousands of kilometres", anim(tf, 0, .6))
        spots = [(30, 58.5), (40, 64), (38, 48), (45, 47), (55, 55), (61, 56), (73, 55), (104, 52), (132, 44), (44, 42), (30, 50), (50, 52), (85, 54)]
        for i, (lo, la) in enumerate(spots):
            if tf > 0.4 + i * 0.25:
                x, y = P(lo, la)
                _boom(img, x, y, tf, i)
        # distance ruler Moscow -> Vladivostok
        a = anim(tf, 2.0, .8)
        if a > 0:
            p0 = P(*CITIES["Moscow"]); p1 = P(*CITIES["Vladivostok"])
            pts = _polyline_partial([p0, p1], a)
            d = Draw(img)
            for k in range(0, 40):
                u0, u1 = k / 40, (k + .5) / 40
                if u1 > a:
                    break
                d.line((p0[0] + (p1[0] - p0[0]) * u0, p0[1] + (p1[1] - p0[1]) * u0, p0[0] + (p1[0] - p0[0]) * u1, p0[1] + (p1[1] - p0[1]) * u1), fill=GOLD, width=4)
            mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
            la = anim(tf, 2.6, .5)
            p = panel(540, 64, fill=(10, 16, 30, 230), border=(229, 181, 74, 200), r=10)
            paste(img, p, (mx - 270, my + 50), la)
            draw_text(img, (mx, my + 82), "MOSCOW → VLADIVOSTOK  ≈ 9,000 km by rail", font("bold", 22), WHITE, anchor="mm", alpha=la)
        _city(img, "Moscow", tf, size=8, color=GOLD)
    elif v == "map_whites":
        tw = bt["map_whites"]
        _poly_fill(img, CORE, RED, .55, blur=8, mask=emp)
        _title(img, "THE WHITES: DIVIDED", "Separate armies, far apart, poorly coordinated (1919)", anim(tw, 0, .6))
        fronts = [
            ("KOLCHAK", "Siberia & the Urals", [(58, 58), (66, 61), (85, 60), (90, 54), (75, 51), (60, 52)], (900, 470)),
            ("DENIKIN", "South Russia", [(36, 48), (42, 50), (48, 47), (46, 43), (38, 44)], (250, 690)),
            ("YUDENICH", "Northwest", [(25, 58), (29, 60.5), (31, 59), (28, 56.8)], (130, 300)),
            ("MILLER", "North (Arkhangelsk)", [(36, 64), (42, 67), (48, 65), (45, 62), (38, 62)], (760, 200)),
        ]
        cents = []
        for i, (nm, sub, poly, tagpos) in enumerate(fronts):
            a = anim(tw, 0.4 + i * 0.5, .6)
            _poly_fill(img, poly, CREAM, a * (0.75 + .1 * math.sin(t * 2 + i)), blur=6, mask=emp)
            cx = sum(p[0] for p in poly) / len(poly); cy = sum(p[1] for p in poly) / len(poly)
            cents.append(P(cx, cy))
            _tag(img, tagpos[0], tagpos[1], nm, sub, CREAM, a, w=330)
        # broken links between white armies
        a = anim(tw, 3.0, .8)
        if a > 0:
            d = Draw(img)
            for i in range(len(cents)):
                p0, p1 = cents[i], cents[(i + 1) % len(cents)]
                for k in range(0, 30, 2):
                    u0, u1 = k / 30, (k + 1) / 30
                    if u0 > a:
                        break
                    d.line((p0[0] + (p1[0] - p0[0]) * u0, p0[1] + (p1[1] - p0[1]) * u0, p0[0] + (p1[0] - p0[0]) * u1, p0[1] + (p1[1] - p0[1]) * u1), fill=(242, 238, 230, 140), width=3)
                mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
                d.ellipse((mx - 22, my - 22, mx + 22, my + 22), fill=(200, 16, 46, int(230 * a)))
                d.line((mx - 9, my - 9, mx + 9, my + 9), fill=(255, 255, 255, int(255 * a)), width=5)
                d.line((mx - 9, my + 9, mx + 9, my - 9), fill=(255, 255, 255, int(255 * a)), width=5)
        _city(img, "Moscow", tw, size=9, color=GOLD)
    elif v == "map_red":
        tr = bt["map_red"]
        _title(img, "RED VICTORY", "By 1921, organised White resistance is largely defeated", anim(tr, 0, .6))
        # expanding red mask from Moscow, clipped to former empire
        cx, cy = P(*CITIES["Moscow"])
        rad = 80 + ease_io(clamp((tr - 0.4) / 5.0)) * 2000
        lay = radial(W, H, cx, cy, rad, (200, 16, 46, 255), 0.25)
        a = np.array(lay.getchannel("A"), np.uint16) * np.array(emp, np.uint16) // 255
        lay.putalpha(Image.fromarray((a * 0.62).astype(np.uint8)))
        comp(img, lay)
        pockets = [(73, 50), (132, 44), (68, 40), (42, 42.5)]  # Central Asia, Far East, Caucasus — fighting continued
        for i, (lo, la) in enumerate(pockets):
            if tr > 3.5 + i * 0.4:
                x, y = P(lo, la); _boom(img, x, y, tr, i + 3)
        _tag(img, 1240, 150, "FIGHTING CONTINUES", "in some regions — Central Asia, Far East", GOLD, anim(tr, 4.0, .6), w=560)
        _city(img, "Moscow", tr, size=10, color=GOLD)
        _city(img, "Petrograd", tr - .3, size=8, color=GOLD)
    return img
