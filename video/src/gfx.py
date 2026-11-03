"""Full-screen explainer graphics."""
import math, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from common import *


@functools.lru_cache(maxsize=2)
def gfx_bg(tint="navy"):
    top, bot = (hexc("101C33"), hexc("060B16")) if tint == "navy" else (hexc("3A0A14"), hexc("0E0306"))
    img = vgrad(W, H, top, bot).convert("RGB")
    d = Draw(img)
    for x in range(-H, W, 60):
        d.line((x, H, x + H, 0), fill=(255, 255, 255, 7), width=2)
    comp(img, radial(W, H, W * .5, H * .38, 1100, (80, 120, 200, 50) if tint == "navy" else (220, 40, 60, 60), 1.5))
    arr = np.array(img, np.float32)
    arr[..., :3] += np.random.default_rng(2).normal(0, 3, (H, W, 1))
    img = Image.fromarray(arr.clip(0, 255).astype(np.uint8), "RGB")
    comp(img, vignette(W, H, .6))
    return img


def bg_frame(t, tint="navy"):
    img = gfx_bg(tint).copy()
    # drifting light sweep
    x = (t * 120) % (W + 800) - 400
    comp(img, _sweep(), (int(x), 0))
    return img


@functools.lru_cache(maxsize=1)
def _sweep():
    im = Image.new("RGBA", (400, H), (0, 0, 0, 0))
    d = Draw(im)
    d.polygon([(150, 0), (260, 0), (250, H), (140, H)], fill=(255, 255, 255, 10))
    return im.filter(ImageFilter.GaussianBlur(30))


def header(img, t, kicker, title, color=GOLD):
    a = anim(t, 0, .6)
    d = Draw(img)
    d.rectangle((200, 52, 200 + 8, 132), fill=with_alpha(RED, a))
    tracked(img, (230 + (1 - a) * -30, 70), kicker, font("bold", 26), color, track=5, alpha=a)
    draw_text(img, (226 + (1 - a) * -30, 112), title, font("black", 56), WHITE, anchor="lm", alpha=a)


# ---------------------------------------------------------------- icons (drawn at size s around cx, cy)
def icon(d, kind, cx, cy, s, col, a=1.0):
    c = with_alpha(col, a); bg = (0, 0, 0, 0)
    if kind == "star":
        d.polygon(star_pts(cx, cy, s * .5), fill=c)
    elif kind == "person":
        d.ellipse((cx - s * .18, cy - s * .48, cx + s * .18, cy - s * .12), fill=c)
        d.rounded_rectangle((cx - s * .34, cy - s * .06, cx + s * .34, cy + s * .48), s * .2, fill=c)
    elif kind == "gov":
        d.polygon([(cx - s * .5, cy - s * .22), (cx, cy - s * .5), (cx + s * .5, cy - s * .22)], fill=c)
        for k in range(4):
            x = cx - s * .36 + k * s * .24
            d.rectangle((x - s * .05, cy - s * .16, x + s * .05, cy + s * .32), fill=c)
        d.rectangle((cx - s * .5, cy + s * .34, cx + s * .5, cy + s * .46), fill=c)
    elif kind == "crown":
        d.polygon([(cx - s * .45, cy + s * .3), (cx - s * .45, cy - s * .3), (cx - s * .22, cy), (cx, cy - s * .42), (cx + s * .22, cy),
                   (cx + s * .45, cy - s * .3), (cx + s * .45, cy + s * .3)], fill=c)
    elif kind == "ballot":
        d.rectangle((cx - s * .4, cy - s * .05, cx + s * .4, cy + s * .45), fill=c)
        d.rectangle((cx - s * .25, cy - s * .04, cx + s * .25, cy + s * .02), fill=(10, 16, 30, 255))
        d.polygon([(cx - s * .18, cy - s * .48), (cx + s * .22, cy - s * .48), (cx + s * .22, cy - s * .08), (cx - s * .18, cy - s * .08)], fill=c)
    elif kind == "question":
        draw_text(d._image, (cx, cy), "?", font("black", int(s * .9)), col, anchor="mm", alpha=a)
    elif kind == "house":
        d.polygon([(cx - s * .5, cy - s * .02), (cx, cy - s * .48), (cx + s * .5, cy - s * .02)], fill=c)
        d.rectangle((cx - s * .36, cy - s * .04, cx + s * .36, cy + s * .44), fill=c)
        d.rectangle((cx - s * .1, cy + s * .14, cx + s * .1, cy + s * .44), fill=(10, 16, 30, int(255 * a)))
    elif kind == "village":
        for k, (dx, sc) in enumerate(((-.28, .6), (.22, .75))):
            x = cx + dx * s; ss = s * sc
            d.polygon([(x - ss * .45, cy + s * .1), (x, cy + s * .1 - ss * .5), (x + ss * .45, cy + s * .1)], fill=c)
            d.rectangle((x - ss * .32, cy + s * .08, x + ss * .32, cy + s * .45), fill=c)
    elif kind == "rifles":
        for sgn in (-1, 1):
            d.line((cx - sgn * s * .42, cy + s * .42, cx + sgn * s * .42, cy - s * .42), fill=c, width=int(s * .09))
            d.line((cx - sgn * s * .42, cy + s * .42, cx - sgn * s * .28, cy + s * .28), fill=c, width=int(s * .17))
    elif kind == "family":
        for dx, sc in ((-.3, .8), (.3, .8), (0, .55)):
            x = cx + dx * s; ss = s * sc
            yb = cy + s * .45
            d.ellipse((x - ss * .17, yb - ss * .95, x + ss * .17, yb - ss * .62), fill=c)
            d.rounded_rectangle((x - ss * .27, yb - ss * .56, x + ss * .27, yb), ss * .14, fill=c)
    elif kind == "bowl":
        d.chord((cx - s * .48, cy - s * .38, cx + s * .48, cy + s * .42), 0, 180, fill=c)
        d.rectangle((cx - s * .5, cy - s * .02, cx + s * .5, cy + s * .04), fill=c)
        for k in (-1, 0, 1):
            d.arc((cx + k * s * .14 - s * .06, cy - s * .48, cx + k * s * .14 + s * .06, cy - s * .12), 90, 270, fill=c, width=int(s * .04))
    elif kind == "cross":
        d.rectangle((cx - s * .14, cy - s * .44, cx + s * .14, cy + s * .44), fill=c)
        d.rectangle((cx - s * .44, cy - s * .14, cx + s * .44, cy + s * .14), fill=c)
    elif kind == "blast":
        d.polygon(star_pts(cx, cy, s * .5, -90, .5)[:10] if False else [(cx + s * .5 * (1 if i % 2 == 0 else .45) * math.cos(math.radians(i * 22.5)),
                   cy + s * .5 * (1 if i % 2 == 0 else .45) * math.sin(math.radians(i * 22.5))) for i in range(16)], fill=c)
    elif kind == "walk":
        d.ellipse((cx - s * .1, cy - s * .5, cx + s * .12, cy - s * .28), fill=c)
        d.line((cx, cy - s * .26, cx - s * .04, cy + s * .1), fill=c, width=int(s * .13))
        d.line((cx - s * .04, cy + s * .08, cx - s * .24, cy + s * .48), fill=c, width=int(s * .1))
        d.line((cx - s * .04, cy + s * .08, cx + s * .18, cy + s * .48), fill=c, width=int(s * .1))
        d.line((cx, cy - s * .18, cx + s * .26, cy - s * .05), fill=c, width=int(s * .08))
        d.ellipse((cx + s * .18, cy - s * .18, cx + s * .48, cy + s * .12), fill=c)
        d.line((cx - s * .4, cy - s * .1, cx - s * .4, cy + s * .48), fill=c, width=int(s * .05))
    elif kind == "down":
        pts = [(cx - s * .45, cy - s * .35), (cx - s * .15, cy - s * .05), (cx + s * .05, cy - s * .2), (cx + s * .4, cy + s * .25)]
        d.line(pts, fill=c, width=int(s * .1), joint="curve")
        d.polygon([(cx + s * .48, cy + s * .35), (cx + s * .2, cy + s * .32), (cx + s * .45, cy + s * .08)], fill=c)
    elif kind == "wheat":
        d.line((cx, cy + s * .48, cx, cy - s * .45), fill=c, width=int(s * .06))
        for k in range(4):
            y = cy - s * .35 + k * s * .17
            for sgn in (-1, 1):
                d.ellipse((cx + sgn * s * .02 - (s * .18 if sgn < 0 else 0), y - s * .07, cx + sgn * s * .02 + (s * .18 if sgn > 0 else 0), y + s * .07), fill=c)
    elif kind == "factory":
        d.polygon([(cx - s * .5, cy + s * .45), (cx - s * .5, cy - s * .05), (cx - s * .2, cy + s * .12), (cx - s * .2, cy - s * .05), (cx + s * .1, cy + s * .12),
                   (cx + s * .1, cy - s * .5), (cx + s * .3, cy - s * .5), (cx + s * .3, cy - s * .05), (cx + s * .5, cy - s * .05), (cx + s * .5, cy + s * .45)], fill=c)
    elif kind == "fist":
        d.rounded_rectangle((cx - s * .32, cy - s * .3, cx + s * .32, cy + s * .14), s * .12, fill=c)
        d.rectangle((cx - s * .2, cy + s * .1, cx + s * .2, cy + s * .48), fill=c)
        for k in range(3):
            x = cx - s * .21 + k * s * .21
            d.line((x, cy - s * .3, x, cy - s * .05), fill=(10, 16, 30, int(255 * a)), width=max(1, int(s * .03)))


def icon_img(kind, s, col):
    im, ss = ss_canvas(int(s * 1.2), int(s * 1.2), 3)
    d = Draw(im)
    icon(d, kind, s * 1.2 * ss / 2, s * 1.2 * ss / 2, s * ss, col)
    return down(im, ss)


@functools.lru_cache(maxsize=64)
def _icon_cached(kind, s, col):
    return icon_img(kind, s, col)


def card(img, x, y, w, h, kind, title, sub, a, col=GOLD, fillc=(14, 22, 40, 235), title_col=WHITE, tsize=38, ssize=26):
    if a <= 0:
        return
    yy = y + (1 - a) * 40
    paste(img, panel(w, h, fill=fillc, border=with_alpha(col, .55), r=16), (x, yy), a)
    f = font("black", tsize); f2 = font("med", ssize)
    tl = wrap(title, f, w - 40); sl = wrap(sub, f2, w - 50) if sub else []
    ich = 132 if kind else 0
    content = ich + len(tl) * (tsize + 8) + (14 + len(sl) * (ssize + 10) if sl else 0)
    cy = yy + (h - content) / 2
    if kind:
        ic = _icon_cached(kind, 110, col)
        paste(img, ic, (x + w / 2 - ic.width / 2, cy - 6), a)
        cy += ich
    for i, line in enumerate(tl):
        draw_text(img, (x + w / 2, cy + tsize / 2), line, f, title_col, anchor="mm", alpha=a)
        cy += tsize + 8
    cy += 14
    for i, line in enumerate(sl):
        draw_text(img, (x + w / 2, cy + ssize / 2), line, f2, (200, 210, 225, 255), anchor="mm", alpha=a)
        cy += ssize + 10


def arrow_h(img, x0, x1, y, a, col=GOLD, w=6):
    if a <= 0:
        return
    d = Draw(img)
    xe = x0 + (x1 - x0) * ease(a)
    d.line((x0, y, xe, y), fill=col, width=w)
    d.polygon([(xe + 4, y), (xe - 18, y - 14), (xe - 18, y + 14)], fill=col)


# ---------------------------------------------------------------- scenes
def g_1917(img, t):
    header(img, t, "PETROGRAD · 1917", "THE RUSSIAN REVOLUTION")
    a = anim(t, .3, .8)
    # big year with counter
    yr = int(lerp(1905, 1917, ease(clamp((t - .3) / 1.4))))
    f = font("black", 300)
    draw_text(img, (520, 470), str(yr), f, (255, 255, 255, 30), anchor="mm", alpha=a)
    draw_text(img, (520, 460), str(yr), f, RED, anchor="mm", alpha=a)
    items = [("FEBRUARY 1917", "Tsar Nicholas II abdicates — a Provisional Government takes over"),
             ("OCTOBER 1917", "The Bolsheviks seize power in Petrograd")]
    d = Draw(img)
    for i, (k, v) in enumerate(items):
        ai = anim(t, 1.4 + i * 1.1, .6)
        y = 330 + i * 200
        d.line((1000, y - 50, 1000, y + 80), fill=with_alpha(GOLD, ai), width=4)
        d.ellipse((990, y - 18, 1010, y + 2), fill=with_alpha(GOLD, ai))
        draw_text(img, (1040 + (1 - ai) * 40, y - 8), k, font("black", 40), GOLD, anchor="lm", alpha=ai)
        for j, line in enumerate(wrap(v, font("semi", 34), 780)):
            draw_text(img, (1040 + (1 - ai) * 40, y + 40 + j * 44), line, font("semi", 34), WHITE, anchor="lm", alpha=ai)


def g_lenin(img, t):
    header(img, t, "OCTOBER REVOLUTION", "THE BOLSHEVIKS TAKE POWER")
    card(img, 110, 290, 480, 380, "star", "THE BOLSHEVIKS", "Radical socialist party", anim(t, .2), col=RED)
    arrow_h(img, 610, 700, 480, anim(t, .8, .5))
    card(img, 720, 290, 480, 380, "person", "VLADIMIR LENIN", "Bolshevik leader", anim(t, 1.0), col=GOLD)
    arrow_h(img, 1220, 1310, 480, anim(t, 1.8, .5))
    ga = anim(t, 2.0)
    card(img, 1330, 290, 480, 380, "gov", "PROVISIONAL GOVERNMENT", "", ga, col=STEEL)
    sa = anim(t, 3.2, .35)
    if sa > 0:  # stamp
        st = Image.new("RGBA", (520, 160), (0, 0, 0, 0)); d = Draw(st)
        d.rounded_rectangle((10, 10, 510, 150), 14, outline=RED, width=10)
        draw_text(st, (260, 82), "OVERTHROWN", font("black", 74), RED, anchor="mm")
        sc = lerp(1.8, 1.0, sa)
        st = st.rotate(-12, expand=True, resample=Image.BICUBIC)
        st = st.resize((int(st.width * sc), int(st.height * sc)), Image.BILINEAR)
        paste(img, st, (1570 - st.width / 2, 640 - st.height / 2), sa)


def g_path(img, t):
    header(img, t, "1917 – 1918", "FROM REVOLUTION TO CIVIL WAR")
    card(img, 120, 300, 470, 360, "star", "BOLSHEVIK RULE", "A new communist government", anim(t, .2), col=RED)
    arrow_h(img, 610, 700, 480, anim(t, 1.0, .5))
    card(img, 720, 300, 470, 360, "fist", "OPPOSITION", "Many groups reject the new regime", anim(t, 1.3), col=CREAM)
    arrow_h(img, 1210, 1300, 480, anim(t, 2.4, .5))
    a = anim(t, 2.7, .5)
    shake = math.sin(t * 40) * 6 * (1 - clamp((t - 2.7) / .8)) if t > 2.7 else 0
    card(img, int(1320 + shake), 300, 480, 360, "rifles", "CIVIL WAR", "1917 / 1918 – 1922", a, col=RED, fillc=(90, 10, 24, 240))


def g_sides(img, t, beats):
    bt = {b[0]: t - b[1] for b in beats}
    cur = [b for b in beats if b[1] <= t + 1e-6][-1][0]
    fr = 0.5
    tr = bt.get("gfx_sides_red", -1); tw = bt.get("gfx_sides_white", -1)
    if tw >= 0:
        fr = lerp(0.62, 0.38, ease_io(tw / .8))
    elif tr >= 0:
        fr = lerp(0.5, 0.62, ease_io(tr / .8))
    split = int(W * fr)
    a0 = anim(t, 0, .7)
    d = Draw(img)
    # panels slide in
    lx = -W * (1 - a0)
    comp(img, vgrad(split, H, hexc("A30D24"), hexc("4A0612")), (int(lx), 0))
    rp = vgrad(W - split, H, hexc("EDE7DA"), hexc("A9A397"))
    comp(img, rp, (int(split + W * (1 - a0)), 0))
    # big labels
    ca = anim(t, .5, .6)
    draw_text(img, (split / 2 + lx, 200), "THE REDS", font("black", 110), WHITE, anchor="mm", alpha=ca)
    draw_text(img, (split + (W - split) / 2 + W * (1 - a0), 200), "THE WHITES", font("black", 110), INK, anchor="mm", alpha=ca)
    # VS badge
    va = back(anim(t, .9, .5)) if t > .9 else 0
    if va > 0:
        r = 80 * va
        d.ellipse((split - r, 470 - r, split + r, 470 + r), fill=(10, 16, 30, 255), outline=GOLD, width=6)
        draw_text(img, (split, 468), "VS", font("black", int(70 * va) + 1), GOLD, anchor="mm")
    # red details
    if tr >= 0:
        items = [("star", "The Bolsheviks"), ("gov", "Goal: a communist government"), ("person", "Red Army led by Leon Trotsky")]
        for i, (ic, txt) in enumerate(items):
            ai = anim(tr, .6 + i * .9, .5) * (1 - anim(tw, 0, .5) if tw >= 0 else 1)
            y = 340 + i * 130
            paste(img, _icon_cached(ic, 70, CREAM), (110, y - 42), ai)
            f = font("bold", 46 if tw < 0 else 36)
            draw_text(img, (220, y), txt, f, WHITE, anchor="lm", alpha=ai)
    if tw >= 0:
        items = [("crown", "Monarchists"), ("gov", "Conservatives"), ("ballot", "Liberals"), ("fist", "Other anti-Bolshevik forces")]
        x0 = split + 110
        for i, (ic, txt) in enumerate(items):
            ai = anim(tw, .8 + i * .8, .5)
            y = 320 + i * 115
            paste(img, _icon_cached(ic, 64, INK), (x0, y - 38), ai)
            draw_text(img, (x0 + 100, y), txt, font("bold", 44), INK, anchor="lm", alpha=ai)
        # red side summary
        sa = anim(tw, .4, .5)
        draw_text(img, (split / 2, 470), "Bolsheviks", font("bold", 40), CREAM, anchor="mm", alpha=sa)
        draw_text(img, (split / 2, 530), "Leon Trotsky's Red Army", font("med", 32), CREAM, anchor="mm", alpha=sa)
    if tr < 0:
        sa = anim(t, 1.3, .6)
        draw_text(img, (split / 2, 640), "BOLSHEVIKS", font("bold", 40), (255, 220, 220, 255), anchor="mm", alpha=sa)
        draw_text(img, (split + (W - split) / 2, 640), "ANTI-BOLSHEVIKS", font("bold", 40), (60, 60, 70, 255), anchor="mm", alpha=sa)


def g_divided(img, t):
    header(img, t, "THE WHITE MOVEMENT", "UNITED AGAINST — DIVIDED ON WHAT NEXT")
    a = anim(t, .2, .6)
    paste(img, panel(560, 120, fill=(236, 231, 220, 245), border=(255, 255, 255, 80), r=16), (680, 230 + (1 - a) * 30), a)
    draw_text(img, (960, 290 + (1 - a) * 30), "THE WHITES", font("black", 58), INK, anchor="mm", alpha=a)
    opts = [("crown", "RESTORE THE MONARCHY", 340), ("ballot", "A REPUBLIC / ELECTED ASSEMBLY", 960), ("question", "OTHER POLITICAL SYSTEMS", 1580)]
    d = Draw(img)
    for i, (ic, txt, x) in enumerate(opts):
        ai = anim(t, 1.0 + i * .6, .6)
        if ai > 0:
            y0 = 355; y1 = 455
            xe = lerp(960, x, ease(ai))
            d.line((960, y0, xe, lerp(y0, y1, ease(ai))), fill=with_alpha(GOLD, ai), width=5)
        card(img, x - 280, 460, 560, 270, ic, txt, "", anim(t, 1.3 + i * .6), col=GOLD if i != 0 else CREAM, tsize=34)
    ba = anim(t, 3.6, .6)
    if ba > 0:
        draw_text(img, (960, 410), "Shared goal: defeat the Bolsheviks", font("semi", 30), GOLD, anchor="mm", alpha=ba)


def g_civilians(img, t):
    header(img, t, "THE HUMAN COST", "CIVILIANS CAUGHT IN THE MIDDLE")
    cards = [("rifles", "FIGHTING IN CITIES", "Streets become front lines"), ("village", "FIGHTING IN VILLAGES", "Farms and homes destroyed"),
             ("family", "CIVILIANS", "Caught between the armies")]
    for i, (ic, ti, su) in enumerate(cards):
        card(img, 130 + i * 570, 280, 520, 440, ic, ti, su, anim(t, .3 + i * .7), col=RED if i == 2 else GOLD)


def g_defeats(img, t):
    header(img, t, "1919 – 1920", "THE WHITE ARMIES FALL BACK")
    d = Draw(img)
    la = anim(t, .2, 1.2)
    y = 500
    d.line((140, y, 140 + 1640 * la, y), fill=(255, 255, 255, 120), width=6)
    ev = [("1919", "Kolchak's offensive in the east collapses"), ("OCT 1919", "Yudenich driven back from Petrograd"),
          ("OCT 1919", "Denikin's march on Moscow fails"), ("NOV 1920", "Wrangel's forces evacuate Crimea")]
    for i, (dt, txt) in enumerate(ev):
        ai = anim(t, .8 + i * 2.2, .6)
        x = 260 + i * 470
        up = i % 2 == 0
        if ai <= 0:
            continue
        r = 16 * back(ai)
        d.ellipse((x - r, y - r, x + r, y + r), fill=RED, outline=WHITE, width=4)
        yy = y - 220 if up else y + 50
        paste(img, panel(400, 170, r=14), (x - 200, yy + (1 - ai) * (20 if up else -20)), ai)
        draw_text(img, (x, yy + 40 + (1 - ai) * 20), dt, font("black", 36), GOLD, anchor="mm", alpha=ai)
        for j, line in enumerate(wrap(txt, font("semi", 28), 360)):
            draw_text(img, (x, yy + 90 + j * 36 + (1 - ai) * 20), line, font("semi", 28), WHITE, anchor="mm", alpha=ai)
        d.line((x, y - 16 if up else y + 16, x, yy + 170 if up else yy), fill=with_alpha(GOLD, ai), width=3)
    fa = anim(t, (SENTS[2] - .3) if len(SENTS) > 2 else 8.5, .6)
    if fa > 0:
        draw_text(img, (960, 196), "Fighting continues in some regions — but the Bolsheviks grow stronger", font("semi", 30), CREAM, anchor="mm", alpha=fa)


def g_suffering(img, t):
    header(img, t, "1918 – 1921", "MILLIONS SUFFER")
    tiles = [("bowl", "HUNGER"), ("cross", "DISEASE"), ("blast", "VIOLENCE"), ("walk", "DISPLACEMENT")]
    for i, (ic, ti) in enumerate(tiles):
        card(img, 110 + i * 440, 250, 400, 320, ic, ti, "", anim(t, .2 + i * .55), col=RED if i % 2 == 0 else GOLD)
    ea = anim(t, 3.6, .6)
    if ea > 0:
        paste(img, panel(1300, 150, fill=(70, 10, 22, 235), border=(255, 120, 120, 90), r=16), (310, 600 + (1 - ea) * 30), ea)
        paste(img, _icon_cached("down", 90, CREAM), (360, 620 + (1 - ea) * 30), ea)
        draw_text(img, (500, 650 + (1 - ea) * 30), "ECONOMIC COLLAPSE", font("black", 46), WHITE, anchor="lm", alpha=ea)
        draw_text(img, (500, 705 + (1 - ea) * 30), "Industry, trade and transport break down", font("med", 30), CREAM, anchor="lm", alpha=ea)


def g_warcomm(img, t):
    header(img, t, "1918 – 1921", "HARSH MEASURES: “WAR COMMUNISM”", color=GOLD)
    cards = [("wheat", "GRAIN REQUISITIONING", "Food seized from peasants to feed the army and cities"),
             ("factory", "STATE CONTROL", "Industry nationalised and run by the state"),
             ("fist", "RISING TENSIONS", "Anger and peasant revolts spread")]
    for i, (ic, ti, su) in enumerate(cards):
        card(img, 130 + i * 570, 270, 520, 470, ic, ti, su, anim(t, .3 + i * 1.2), col=RED if i == 2 else GOLD, tsize=36)


def g_ussr(img, t):
    t0 = (SENTS[1] - 0.6) if len(SENTS) > 1 else 0
    pre = t < t0 + .2
    if t0 > 0:
        pa = anim(t, .2, .6) * (1 - anim(t, t0 - .2, .4))
        if pa > 0:
            draw_text(img, (960, 330 - (1 - pa) * 20), "BOLSHEVIKS SECURE CONTROL", font("black", 84), WHITE, anchor="mm", alpha=pa)
            draw_text(img, (960, 430), "over most of the former Russian Empire", font("semi", 44), GOLD, anchor="mm", alpha=pa)
            Draw(img).rectangle((960 - 300 * pa, 500, 960 + 300 * pa, 506), fill=(255, 255, 255, int(200 * pa)))
    t = t - t0
    if t < 0:
        return
    a = anim(t, .2, .8)
    # rotating rays
    rays = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = Draw(rays)
    cx, cy = 960, 400
    for k in range(24):
        ang = math.radians(k * 15 + t * 6)
        d.polygon([(cx, cy), (cx + math.cos(ang - .05) * 1400, cy + math.sin(ang - .05) * 1400), (cx + math.cos(ang + .05) * 1400, cy + math.sin(ang + .05) * 1400)],
                  fill=(255, 210, 120, int(18 * a)))
    comp(img, rays)
    sa = back(anim(t, .4, .7)) if t > .4 else 0
    if sa > 0:
        st = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
        Draw(st).polygon(star_pts(150, 155, 140 * sa), fill=GOLD)
        paste(img, st, (cx - 150, 70))
    letters = "USSR"
    f = font("black", 230)
    total = sum(f.getlength(c) for c in letters) + 30 * 3
    x = cx - total / 2
    for i, c in enumerate(letters):
        la = anim(t, 1.0 + i * .18, .5)
        draw_text(img, (x, 500 + (1 - la) * 60), c, f, WHITE, anchor="lm", alpha=la, shadow=(6, 8, (0, 0, 0, 160)))
        x += f.getlength(c) + 30
    ta = anim(t, 2.2, .6)
    draw_text(img, (cx, 645), "UNION OF SOVIET SOCIALIST REPUBLICS", font("bold", 44), GOLD, anchor="mm", alpha=ta)
    ba = anim(t, 3.4, .6)
    if ba > 0:
        paste(img, panel(560, 70, fill=(200, 16, 46, 240), border=(255, 255, 255, 60), r=35), (cx - 280, 685 + (1 - ba) * 20), ba)
        draw_text(img, (cx, 720 + (1 - ba) * 20), "ESTABLISHED 30 DECEMBER 1922", font("black", 30), WHITE, anchor="mm", alpha=ba)


def g_timeline(img, t):
    header(img, t, "THE LEGACY", "FROM CIVIL WAR TO SUPERPOWER")
    d = Draw(img)
    y = 470
    la = anim(t, .2, 2.5)
    d.line((120, y, 120 + 1680 * la, y), fill=GOLD, width=8)
    pts = [("1917", "Revolution"), ("1918", "Civil war spreads"), ("1920", "Whites defeated"), ("1922", "USSR founded"), ("1900s", "A major world power")]
    for i, (yr, txt) in enumerate(pts):
        x = 200 + i * 380
        ai = anim(t, .4 + i * .55, .5)
        if ai <= 0:
            continue
        big = i == 4
        r = (26 if big else 18) * back(ai)
        d.ellipse((x - r, y - r, x + r, y + r), fill=RED if not big else GOLD, outline=WHITE, width=4)
        lab = "20TH CENTURY" if big else yr
        draw_text(img, (x, y - 80 + (1 - ai) * 20), lab, font("black", 46 if not big else 40), WHITE if not big else GOLD, anchor="mm", alpha=ai)
        draw_text(img, (x, y + 70 - (1 - ai) * 20), txt, font("semi", 30), CREAM, anchor="mm", alpha=ai)
    qa = anim(t, 4.0, .7)
    if qa > 0:
        draw_text(img, (960, 700), "A communist state that shaped world history", font("bold", 40), WHITE, anchor="mm", alpha=qa)


def g_recap(img, t):
    header(img, t, "THE TAKEAWAY", "COMPETING VISIONS FOR A NATION")
    card(img, 150, 230, 760, 270, "star", "THE REDS", "Fought to keep Bolshevik rule", anim(t, .3), col=RED)
    card(img, 1010, 230, 760, 270, "fist", "THE WHITES & OTHERS", "Fought to defeat the Bolsheviks", anim(t, .8), col=CREAM)
    qa = anim(t, 2.0, .7)
    if qa > 0:
        paste(img, panel(1620, 170, fill=(14, 22, 40, 240), border=(229, 181, 74, 140), r=16), (150, 540 + (1 - qa) * 20), qa)
        draw_text(img, (200, 570 + (1 - qa) * 20), "“", font("serif", 110), GOLD, anchor="lt", alpha=qa)
        lines = ["Revolutions can lead to years of conflict when groups", "have competing visions for a country’s future."]
        for i, l in enumerate(lines):
            draw_text(img, (300, 595 + i * 52 + (1 - qa) * 20), l, font("semi", 38), WHITE, anchor="lm", alpha=qa)


GFX = {"gfx_1917": g_1917, "gfx_lenin": g_lenin, "gfx_path": g_path, "gfx_divided": g_divided, "gfx_civilians": g_civilians,
       "gfx_defeats": g_defeats, "gfx_suffering": g_suffering, "gfx_warcomm": g_warcomm, "gfx_ussr": g_ussr,
       "gfx_timeline": g_timeline, "gfx_recap": g_recap}


SENTS = []


def render_gfx(beats, t, sents=None):
    global SENTS
    SENTS = sents or []
    v = beats[0][0]
    if v.startswith("gfx_sides"):
        img = bg_frame(t)
        g_sides(img, t, beats)
        return img
    img = bg_frame(t, "red" if v in ("gfx_ussr",) else "navy")
    GFX[v](img, t)
    return img
