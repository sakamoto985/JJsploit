"""Studio set and illustrated field locations (procedurally painted)."""
import math, functools, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from common import *
from figures import figure, FW, FH

# ----------------------------------------------------------------------------------------- studio
SW, SH = 2400, 1350
SCREEN = (1360, 230, 900, 506)   # x, y, w, h (studio space)
ANCHOR_X, ANCHOR_TOP = 860, 318


@functools.lru_cache(maxsize=1)
def studio_layers():
    bg = vgrad(SW, SH, hexc("0A1830"), hexc("050A14")).convert("RGB")
    d = Draw(bg)
    # vertical light columns
    glow = Image.new("RGBA", (SW, SH), (0, 0, 0, 0)); g = Draw(glow)
    for i, x in enumerate(range(80, SW, 230)):
        g.rectangle((x, 60, x + 26, 940), fill=(70, 130, 220, 120))
    glow = glow.filter(ImageFilter.GaussianBlur(18))
    comp(bg, glow)
    for x in range(80, SW, 230):
        d.rectangle((x + 9, 60, x + 17, 940), fill=(150, 195, 255, 150))
    # skyline silhouette band (stylised domes) on the back wall
    sky = Image.new("RGBA", (SW, SH), (0, 0, 0, 0)); s = Draw(sky)
    rng = random.Random(4)
    x = 0
    while x < SW:
        w = rng.randint(60, 160); h = rng.randint(80, 260)
        s.rectangle((x, 900 - h, x + w, 960), fill=(22, 44, 84, 255))
        if rng.random() < 0.35:  # onion dome
            cx = x + w / 2; r = w * 0.32
            s.ellipse((cx - r, 900 - h - r * 1.6, cx + r, 900 - h + r * 0.2), fill=(22, 44, 84, 255))
            s.polygon([(cx - r * 0.5, 900 - h - r * 1.2), (cx, 900 - h - r * 2.6), (cx + r * 0.5, 900 - h - r * 1.2)], fill=(22, 44, 84, 255))
            s.line((cx, 900 - h - r * 2.6, cx, 900 - h - r * 3.2), fill=(22, 44, 84, 255), width=4)
        x += w + rng.randint(0, 30)
    comp(bg, sky)
    # floor
    d.rectangle((0, 940, SW, SH), fill=(6, 12, 24, 255))
    d.line((0, 940, SW, 940), fill=(60, 110, 190, 160), width=3)
    # screen bezel + glow
    x, y, w, h = SCREEN
    sg = Image.new("RGBA", (SW, SH), (0, 0, 0, 0)); Draw(sg).rectangle((x - 20, y - 20, x + w + 20, y + h + 20), fill=(90, 140, 255, 90))
    comp(bg, sg.filter(ImageFilter.GaussianBlur(40)))
    d.rectangle((x - 14, y - 14, x + w + 14, y + h + 14), fill=(16, 20, 28, 255))
    d.rectangle((SW // 2 + 600, y + h + 14, SW // 2 + 620, 940), fill=(16, 20, 28, 255))
    # top light rig
    d.rectangle((0, 0, SW, 46), fill=(8, 12, 20, 255))
    for x0 in range(140, SW, 300):
        d.rounded_rectangle((x0, 30, x0 + 70, 70), 8, fill=(30, 34, 44, 255))
        d.ellipse((x0 + 20, 52, x0 + 50, 68), fill=(255, 240, 200, 255))
    # desk layer
    desk = Image.new("RGBA", (SW, SH), (0, 0, 0, 0)); dd = Draw(desk)
    x0, x1, top = 300, 1440, 900
    dd.polygon([(x0, top), (x1, top), (x1 + 60, SH), (x0 - 60, SH)], fill=(18, 30, 54, 255))
    dd.polygon([(x0 - 30, top - 26), (x1 + 30, top - 26), (x1, top + 6), (x0, top + 6)], fill=(200, 215, 235, 255))
    dd.polygon([(x0 - 30, top - 26), (x1 + 30, top - 26), (x1 + 26, top - 18), (x0 - 26, top - 18)], fill=(255, 255, 255, 255))
    dd.rectangle((x0 - 20, top + 60, x1 + 20, top + 86), fill=RED)
    dg = Image.new("RGBA", (SW, SH), (0, 0, 0, 0)); Draw(dg).rectangle((x0, top + 40, x1, top + 110), fill=(255, 40, 70, 120))
    comp(desk, dg.filter(ImageFilter.GaussianBlur(25)))
    cx = (x0 + x1) // 2
    dd.rounded_rectangle((cx - 170, top + 140, cx + 170, top + 300), 18, fill=(10, 18, 34, 255), outline=(255, 255, 255, 60), width=3)
    draw_text(desk, (cx, top + 222), "HNN", font("black", 110), WHITE, anchor="mm")
    dd.rectangle((cx - 120, top + 290, cx + 120, top + 298), fill=RED)
    # papers + laptop on desk
    dd.polygon([(1080, top - 26), (1240, top - 26), (1225, top - 38), (1095, top - 38)], fill=(240, 240, 240, 255))
    dd.polygon([(520, top - 26), (700, top - 26), (690, top - 110), (530, top - 110)], fill=(40, 46, 58, 255))
    draw_text(desk, (610, top - 68), "HNN", font("black", 26), (120, 130, 150, 255), anchor="mm")
    return bg, desk


def studio_frame(screen_img, frame, env, speaking, cam=(1.0, 0.5, 0.5), out=(W, H)):
    """cam = (zoom, cx, cy) — zoom 1.0 shows the whole studio width."""
    bg, desk = studio_layers()
    img = bg.copy()
    x, y, w, h = SCREEN
    if screen_img is not None:
        comp(img, screen_img.resize((w, h), Image.BILINEAR), (x, y))
    from figures import mouth_level, blink_at
    m = mouth_level(env, frame, speaking)
    bob = math.sin(frame / 19.0) * 3 + (env[min(frame, len(env) - 1)] * 5 if speaking else 0)
    from figures import use_photos, photo, rim
    if use_photos():
        pw = 820
        pulse = 1 + 0.006 * (env[min(frame, len(env) - 1)] if speaking else 0)
        ph = photo("F", pw)
        if pulse > 1.001:
            ph = ph.resize((int(ph.width * pulse), int(ph.height * pulse)), Image.BILINEAR)
        g, pad = rim("F", pw, (90, 150, 255))
        x = ANCHOR_X - ph.width // 2; y = int(400 + bob * 0.6 - (ph.height - photo("F", pw).height) * 0.3)
        comp(img, g, (x - pad, y - pad))
        comp(img, ph, (x, y))
    else:
        fig = figure("F", m, blink_at(frame, 3))
        comp(img, fig, (ANCHOR_X - FW // 2, int(ANCHOR_TOP + bob)))
    comp(img, desk)
    zoom, cx, cy = cam
    cw = SW / zoom; ch = cw * 9 / 16
    left = clamp(cx * SW - cw / 2, 0, SW - cw); top = clamp(cy * SH - ch / 2, 0, SH - ch)
    return img.resize(out, Image.BILINEAR, box=(left, top, left + cw, top + ch))


# ----------------------------------------------------------------------------------------- field
BW, BH = 2200, 1238
HORIZON = 760


def _house(d, x, base, w, h, wall, roof, ruined=False, rng=None, window=(255, 200, 120, 255)):
    rh = h * 0.55
    if ruined:
        pts = [(x, base), (x, base - h * rng.uniform(.5, 1)), (x + w * .25, base - h * rng.uniform(.6, 1.1)),
               (x + w * .4, base - h * rng.uniform(.2, .5)), (x + w * .6, base - h * rng.uniform(.5, .9)),
               (x + w * .8, base - h * rng.uniform(.1, .4)), (x + w, base - h * rng.uniform(.3, .7)), (x + w, base)]
        d.polygon(pts, fill=wall)
        for k in range(3):  # charred beams
            bx = x + rng.uniform(.1, .9) * w
            d.line((bx, base - h * rng.uniform(.3, .6), bx + rng.uniform(-60, 60), base - h * rng.uniform(.9, 1.4)), fill=roof, width=int(w * 0.04) + 2)
        for k in range(2):
            wx = x + w * (0.2 + 0.4 * k)
            d.rectangle((wx, base - h * .55, wx + w * .18, base - h * .3), fill=(20, 14, 12, 255))
    else:
        d.rectangle((x, base - h, x + w, base), fill=wall)
        d.polygon([(x - w * .08, base - h), (x + w / 2, base - h - rh), (x + w * 1.08, base - h)], fill=roof)
        for k in range(2):
            wx = x + w * (0.18 + 0.44 * k)
            d.rectangle((wx, base - h * .7, wx + w * .2, base - h * .4), fill=window)
            d.line((wx + w * .1, base - h * .7, wx + w * .1, base - h * .4), fill=wall, width=3)
        for k in range(int(h // 14)):  # log lines
            d.line((x, base - k * 14, x + w, base - k * 14), fill=lerpc(wall, (0, 0, 0, 255), .18), width=2)


def _church(d, x, base, s, col):
    d.rectangle((x - 60 * s, base - 160 * s, x + 60 * s, base), fill=col)
    d.rectangle((x - 30 * s, base - 260 * s, x + 30 * s, base - 150 * s), fill=col)
    d.ellipse((x - 42 * s, base - 330 * s, x + 42 * s, base - 240 * s), fill=col)
    d.polygon([(x - 22 * s, base - 318 * s), (x, base - 380 * s), (x + 22 * s, base - 318 * s)], fill=col)
    d.line((x, base - 380 * s, x, base - 420 * s), fill=col, width=max(2, int(5 * s)))
    d.line((x - 14 * s, base - 405 * s, x + 14 * s, base - 405 * s), fill=col, width=max(2, int(4 * s)))
    for sx in (-1, 1):
        cx = x + sx * 90 * s
        d.rectangle((cx - 20 * s, base - 130 * s, cx + 20 * s, base), fill=col)
        d.ellipse((cx - 26 * s, base - 175 * s, cx + 26 * s, base - 120 * s), fill=col)
        d.polygon([(cx - 12 * s, base - 168 * s), (cx, base - 205 * s), (cx + 12 * s, base - 168 * s)], fill=col)


def _tree(d, x, base, h, col, rng, depth=0, ang=-90, w=None):
    w = w or h * 0.05
    x2 = x + math.cos(math.radians(ang)) * h; y2 = base + math.sin(math.radians(ang)) * h
    d.line((x, base, x2, y2), fill=col, width=max(1, int(w)))
    if depth < 5 and h > 12:
        for k in range(rng.randint(2, 3)):
            _tree(d, x + (x2 - x) * rng.uniform(.5, 1), base + (y2 - base) * rng.uniform(.5, 1), h * rng.uniform(.5, .72), col, rng,
                  depth + 1, ang + rng.uniform(-38, 38), w * 0.62)


def _ground(img, top, c1, c2, seed, ruts=True):
    w, h = img.size
    g = vgrad(w, h - top, c1, c2)
    rng = np.random.default_rng(seed)
    n = rng.normal(0, 1, ((h - top) // 6 + 1, w // 6 + 1)).astype(np.float32)
    n = np.array(Image.fromarray(((n * 20) + 128).clip(0, 255).astype(np.uint8)).resize((w, h - top), Image.BICUBIC), np.float32) - 128
    arr = np.array(g, np.float32); arr[..., :3] += n[..., None] * 0.5
    g = Image.fromarray(arr.clip(0, 255).astype(np.uint8), "RGBA")
    if ruts:
        d = Draw(g)
        for k in range(2):
            d.line((w * .45 + k * 70, 0, w * .2 + k * 260, h - top), fill=lerpc(c1, (0, 0, 0, 255), .15), width=10)
    comp(img, g, (0, top))


def _layer():
    return Image.new("RGBA", (BW, BH), (0, 0, 0, 0))


@functools.lru_cache(maxsize=4)
def field_bg(kind):
    rng = random.Random({"city": 1, "ruins": 2, "camp": 3, "quiet": 4}[kind])
    if kind == "city":
        img = vgrad(BW, BH, hexc("5E6B7E"), hexc("B9B4AC")).convert("RGB")
        far, mid, gnd = hexc("7D8798"), hexc("4C4A4C"), (hexc("D9DEE6"), hexc("A9B0BC"))
    elif kind == "ruins":
        img = vgrad(BW, BH, hexc("3B2A24"), hexc("C07A45")).convert("RGB")
        far, mid, gnd = hexc("6E4C3A"), hexc("2C211D"), (hexc("6B5A4C"), hexc("3A2F28"))
    elif kind == "camp":
        img = vgrad(BW, BH, hexc("3E4E66"), hexc("C9B8A0")).convert("RGB")
        far, mid, gnd = hexc("6C7686"), hexc("34332F"), (hexc("CFD5DC"), hexc("9EA5AF"))
    else:
        img = vgrad(BW, BH, hexc("2B3355"), hexc("C98F78")).convert("RGB")
        far, mid, gnd = hexc("5A5A78"), hexc("2A2638"), (hexc("B9BCD0"), hexc("7E8098"))
    # sun / light glow
    glow = radial(BW, BH, BW * .3, HORIZON - 120, 900, (255, 220, 170, 110 if kind != "ruins" else 160))
    comp(img, glow)
    # far skyline
    L = _layer(); d = Draw(L)
    x = -50
    while x < BW:
        w = rng.randint(80, 200); h = rng.randint(40, 150)
        if rng.random() < .15:
            _church(d, x + w / 2, HORIZON - 10, rng.uniform(.5, .8), far)
        else:
            d.rectangle((x, HORIZON - 10 - h, x + w, HORIZON), fill=far)
            if rng.random() < .3:
                d.rectangle((x + w * .3, HORIZON - 10 - h - 90, x + w * .3 + 18, HORIZON - h), fill=far)  # chimney
        x += w + rng.randint(-20, 40)
    comp(img, L.filter(ImageFilter.GaussianBlur(3)))
    # haze
    hz = Image.new("RGBA", (BW, BH), (0, 0, 0, 0)); Draw(hz).rectangle((0, HORIZON - 160, BW, HORIZON + 40), fill=with_alpha(far, .35))
    comp(img, hz.filter(ImageFilter.GaussianBlur(60)))
    _ground(img, HORIZON, gnd[0], gnd[1], rng.randint(0, 99), ruts=kind != "ruins")
    # mid layer
    L = _layer(); d = Draw(L)
    if kind in ("city", "quiet"):
        xs = [60, 420, 760, 1500, 1860] if kind == "city" else [40, 380, 1180, 1520, 1880]
        for i, x in enumerate(xs):
            wall = lerpc(mid, (120, 90, 70, 255), .5) if kind == "city" else lerpc(mid, (110, 90, 110, 255), .45)
            _house(d, x, HORIZON + 60 + i % 2 * 30, rng.randint(240, 300), rng.randint(170, 220), wall, mid, rng=rng,
                   window=(255, 196, 110, 255) if kind == "quiet" else (60, 60, 70, 255))
        _church(d, 1150 if kind == "city" else 820, HORIZON + 40, 1.0, lerpc(mid, far, .4))
        for x in (330, 1380, 2050):
            _tree(d, x, HORIZON + 140, 230, mid, rng)
        for x in range(0, BW, 380):  # telegraph poles
            d.line((x + 200, HORIZON + 160, x + 200, HORIZON - 200), fill=mid, width=8)
            d.line((x + 170, HORIZON - 180, x + 230, HORIZON - 180), fill=mid, width=6)
        d.line((0, HORIZON - 175, BW, HORIZON - 165), fill=mid, width=2)
    elif kind == "ruins":
        for i, x in enumerate([0, 330, 700, 1250, 1600, 1950]):
            _house(d, x, HORIZON + 70 + (i % 2) * 40, rng.randint(240, 320), rng.randint(200, 280),
                   lerpc(mid, (110, 80, 60, 255), .35), (20, 14, 12, 255), ruined=True, rng=rng)
        for x in (520, 1100, 1800):
            _tree(d, x, HORIZON + 150, 210, (24, 18, 16, 255), rng)
        for k in range(40):  # rubble
            x = rng.uniform(0, BW); y = HORIZON + rng.uniform(80, 420); r = rng.uniform(8, 30)
            d.polygon([(x - r, y), (x - r * .3, y - r * .9), (x + r, y - r * .2), (x + r * .6, y + r * .3)],
                      fill=lerpc(mid, (90, 70, 60, 255), rng.uniform(0, .6)))
        for x in (300, 1500):  # broken cart wheel
            d.ellipse((x, HORIZON + 300, x + 120, HORIZON + 420), outline=(30, 22, 18, 255), width=10)
    elif kind == "camp":
        for i, x in enumerate([80, 460, 860, 1640, 1990]):  # tents
            y = HORIZON + 80 + (i % 2) * 40; w = 300; h = 190
            d.polygon([(x, y), (x + w / 2, y - h), (x + w, y)], fill=hexc("6A6B4E"))
            d.polygon([(x + w / 2 - 30, y), (x + w / 2, y - h * .7), (x + w / 2 + 30, y)], fill=hexc("2C2C22"))
            d.line((x + w / 2, y - h, x + w / 2, y - h - 30), fill=hexc("2C2C22"), width=5)
        for k in range(8):  # crates
            x = 1250 + (k % 4) * 70 - (k // 4) * 30; y = HORIZON + 260 - (k // 4) * 60
            d.rectangle((x, y - 60, x + 66, y), fill=hexc("7A5B38")); d.rectangle((x, y - 60, x + 66, y), outline=hexc("4E3A22"), width=4)
            d.line((x, y - 60, x + 66, y), fill=hexc("4E3A22"), width=3)
        # map table
        d.rectangle((620, HORIZON + 250, 1000, HORIZON + 270), fill=hexc("4E3A22"))
        d.polygon([(630, HORIZON + 252), (990, HORIZON + 252), (960, HORIZON + 230), (660, HORIZON + 230)], fill=hexc("E6D9B8"))
        for x in (640, 970):
            d.rectangle((x, HORIZON + 270, x + 14, HORIZON + 380), fill=hexc("4E3A22"))
        # flag pole
        d.line((1180, HORIZON + 200, 1180, HORIZON - 260), fill=hexc("2C2C22"), width=10)
        for x in (300, 2000):
            _tree(d, x, HORIZON + 120, 240, mid, rng)
        # rail line + wagon (railways matter!)
        d.line((0, HORIZON + 30, BW, HORIZON + 10), fill=(60, 56, 50, 255), width=6)
        d.rectangle((1380, HORIZON - 90, 1720, HORIZON + 10), fill=hexc("5B3B2A"))
        d.rectangle((1380, HORIZON - 100, 1720, HORIZON - 88), fill=hexc("3A271C"))
        for x in (1420, 1680):
            d.ellipse((x - 26, HORIZON - 10, x + 26, HORIZON + 42), fill=(30, 28, 26, 255))
    comp(img, L.filter(ImageFilter.GaussianBlur(1.2)))
    # grain + vignette (painterly)
    arr = np.array(img, np.float32)
    arr[..., :3] += np.random.default_rng(9).normal(0, 4, (BH, BW, 1))
    img = Image.fromarray(arr.clip(0, 255).astype(np.uint8), "RGB")
    comp(img, vignette(BW, BH, .55))
    return img


@functools.lru_cache(maxsize=8)
def smoke_puff(seed, size=260, col=(70, 64, 60)):
    rng = np.random.default_rng(seed)
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0)); d = Draw(im)
    for k in range(9):
        r = rng.uniform(.18, .32) * size; x = size / 2 + rng.normal(0, size * .1); y = size / 2 + rng.normal(0, size * .1)
        d.ellipse((x - r, y - r, x + r, y + r), fill=col + (60,))
    return im.filter(ImageFilter.GaussianBlur(size * .08))


@functools.lru_cache(maxsize=4)
def soldier_sprite(phase, col=(28, 24, 22, 255), s=1.0):
    im, ss = ss_canvas(110, 260, 2); d = Draw(im)
    S = lambda v: v * ss * s
    d.ellipse((S(38), S(10), S(70), S(44)), fill=col)                   # head
    d.polygon([(S(30), S(14)), (S(78), S(14)), (S(70), S(4)), (S(38), S(4))], fill=col)  # cap
    d.rounded_rectangle((S(30), S(44), S(80), S(150)), S(12), fill=col)  # coat
    d.polygon([(S(28), S(120)), (S(82), S(120)), (S(90), S(175)), (S(20), S(175))], fill=col)
    sw = 16 if phase else -16
    d.line((S(45), S(170), S(45 + sw), S(250)), fill=col, width=int(S(14)))
    d.line((S(65), S(170), S(65 - sw), S(250)), fill=col, width=int(S(14)))
    d.line((S(70), S(60), S(98), S(2)), fill=col, width=int(S(6)))
    d.line((S(70), S(60), S(62), S(110)), fill=col, width=int(S(9)))
    return down(im, ss)


def _flag(t, w=260, h=160, col=RED):
    im = Image.new("RGBA", (w + 20, h + 60), (0, 0, 0, 0)); d = Draw(im)
    top = []; bot = []
    for i in range(21):
        x = i / 20 * w
        off = math.sin(t * 5 - i * 0.55) * (i / 20) * 18
        top.append((x, 20 + off)); bot.append((x, 20 + h + off * 1.1))
    d.polygon(top + bot[::-1], fill=col)
    for i in range(0, 20, 2):
        x0 = i / 20 * w; x1 = (i + 1) / 20 * w
        d.polygon([top[i], top[i + 1], bot[i + 1], bot[i]], fill=lerpc(col, (0, 0, 0, 255), .08 + .08 * math.sin(t * 5 - i * .55)))
    return im


SNOW = None


def field_frame(kind, t, frame, env, speaking, reporter=True, out=(W, H), push=0.0):
    global SNOW
    bg = field_bg(kind)
    img = bg.copy()
    # animated set dressing
    if kind in ("ruins", "city"):
        for k in range(14 if kind == "ruins" else 6):
            base_x = [250, 760, 1300, 1700, 2000, 520][k % 6] + (k // 6) * 40
            life = (t * 0.12 + k * 0.37) % 1.0
            y = HORIZON + 40 - life * 900
            x = base_x + life * 260 + math.sin(t + k) * 20
            sz = int(180 + life * 420)
            p = smoke_puff(k % 5, 260, (60, 52, 48) if kind == "ruins" else (110, 112, 118)).resize((sz, sz), Image.BILINEAR)
            paste(img, p, (x - sz / 2, y - sz / 2), alpha=(1 - life) * (0.95 if kind == "ruins" else .6))
    if kind == "ruins":
        for k, fx in enumerate((380, 1380, 1760)):
            fl = 0.65 + 0.35 * math.sin(t * 13 + k * 2) * math.sin(t * 7.3 + k)
            comp(img, _fire_glow(int(fl * 10)), (fx - 220, HORIZON - 260))
        # distant muzzle flashes
        if (frame * 7919) % 97 < 3:
            fxx = (frame * 131) % BW
            comp(img, radial(240, 240, 120, 120, 120, (255, 230, 160, 200)), (fxx - 120, HORIZON - 180))
    if kind in ("ruins", "camp"):
        for k in range(3 if kind == "ruins" else 4):
            speed = 40 + k * 12
            x = ((t * speed + k * 620) % (BW + 400)) - 200
            y = HORIZON + 30 + k * 18
            spr = soldier_sprite(int(t * 3 + k) % 2, (30, 26, 24, 255) if kind == "ruins" else (40, 40, 36, 255))
            sc = 0.55 + k * 0.08
            spr = spr.resize((int(spr.width * sc), int(spr.height * sc)), Image.BILINEAR)
            comp(img, spr, (int(x), int(y - spr.height)))
    if kind == "camp":
        comp(img, _flag(t), (1185, HORIZON - 262))
        fl = 0.7 + 0.3 * math.sin(t * 11) * math.sin(t * 5.1)
        comp(img, _fire_glow(int(fl * 10)).resize((300, 300)), (300, HORIZON + 160))
    # camera: slow push + handheld shake
    z = 1.06 + push + 0.05 * min(t / 20.0, 1.5)
    cw = BW / z; ch = cw * 9 / 16
    sx = math.sin(t * 1.3) * 6 + math.sin(t * 3.1) * 3; sy = math.cos(t * 1.7) * 5 + math.sin(t * 2.3) * 2
    left = clamp((BW - cw) / 2 + sx, 0, BW - cw); top = clamp((BH - ch) * 0.35 + sy, 0, BH - ch)
    frame_img = img.resize(out, Image.BILINEAR, box=(left, top, left + cw, top + ch))
    sc = out[0] / W
    # particles (screen space)
    if SNOW is None:
        rng = np.random.default_rng(3)
        SNOW = rng.uniform(0, 1, (260, 4))
    p = Image.new("RGBA", out, (0, 0, 0, 0)); d = Draw(p)
    col = (255, 255, 255) if kind != "ruins" else (255, 190, 140)
    n = 260 if kind in ("city", "camp") else 120 if kind == "quiet" else 140
    for i in range(n):
        x0, y0, spd, sz = SNOW[i]
        size = (1.5 + sz * 4) * sc
        y = ((y0 + t * (0.04 + spd * 0.08)) % 1.0) * out[1]
        x = ((x0 + math.sin(t * .7 + i) * .01 + t * 0.01 * (spd - .3)) % 1.0) * out[0]
        a = int(120 + sz * 120)
        d.ellipse((x - size, y - size, x + size, y + size), fill=col + (a,))
    comp(frame_img, p)
    from figures import use_photos, photo, rim, mic_sprite
    if reporter and use_photos():
        tint = {"city": (150, 160, 185), "ruins": (230, 140, 80), "camp": (170, 175, 190), "quiet": (150, 130, 170)}[kind]
        pw = 860
        lv = env[min(frame, len(env) - 1)] if speaking else 0
        ph = photo("M", pw, tint, 0.10)
        pulse = 1 + 0.006 * lv
        if pulse > 1.001:
            ph = ph.resize((int(ph.width * pulse), int(ph.height * pulse)), Image.BILINEAR)
        bob = math.sin(frame / 15.0) * 3 + lv * 4
        x = 1400 - ph.width / 2 + sx * 0.5; y = 105 + bob
        g, pad = rim("M", pw, tint)
        if sc != 1:
            ph = ph.resize((int(ph.width * sc), int(ph.height * sc)), Image.BILINEAR)
            g = g.resize((int(g.width * sc), int(g.height * sc)), Image.BILINEAR)
        comp(frame_img, g, (int((x - pad) * sc), int((y - pad) * sc)))
        comp(frame_img, ph, (int(x * sc), int(y * sc)))
        mic = mic_sprite()
        if sc != 1:
            mic = mic.resize((int(mic.width * sc), int(mic.height * sc)), Image.BILINEAR)
        comp(frame_img, mic, (int((1180 + sx * .5) * sc), int((640 + bob * .5) * sc)))
    elif reporter:
        from figures import mouth_level, blink_at
        m = mouth_level(env, frame, speaking)
        scale = 1.3
        fig = figure("M", m, blink_at(frame, 7), scale)
        bob = math.sin(frame / 15.0) * 4 + (env[min(frame, len(env) - 1)] * 6 if speaking else 0)
        if sc != 1:
            fig = fig.resize((int(fig.width * sc), int(fig.height * sc)), Image.BILINEAR)
        comp(frame_img, fig, (int((1440 - FW * scale / 2 + sx * 0.5) * sc), int((40 + bob) * sc)))
    return frame_img


@functools.lru_cache(maxsize=12)
def _fire_glow(level):
    a = 90 + level * 12
    g = radial(440, 440, 220, 260, 220, (255, 140, 50, a), 1.6)
    d = Draw(g)
    rng = random.Random(level)
    for k in range(6):
        x = 220 + rng.uniform(-50, 50); h = 60 + level * 8 + rng.uniform(0, 50)
        d.polygon([(x - 22, 300), (x + rng.uniform(-12, 12), 300 - h), (x + 22, 300)], fill=(255, 170 + rng.randint(0, 60), 60, 220))
    return g
