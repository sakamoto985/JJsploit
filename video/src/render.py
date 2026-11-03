"""Compose the full news report: shots, transitions, overlays, captions. Frames are piped to ffmpeg."""
import json, math, os, sys, functools, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from common import *
import scenes, maps, gfx
from figures import figure, FW, FH

BUILD = os.environ["BUILD_DIR"]
TL = json.load(open(f"{BUILD}/timeline.json"))
ENV = {"F": TL["env_F"], "M": TL["env_M"]}
XFADE = 0.24


# ------------------------------------------------------------------------------------------ shots
def family(v):
    if v.startswith("map_"):
        return "map"
    if v.startswith("gfx_sides"):
        return "sides"
    if v.startswith("twobox"):
        return v
    return v


def build_shots():
    shots = [dict(kind="intro", t0=0, t1=TL["intro"][1])]
    for p in TL["parts"]:
        shots.append(dict(kind="card", t0=p["card"][0], t1=p["card"][1], part=p))
        chs = p["chunks"]
        for i, ch in enumerate(chs):
            t0 = p["card"][1] if i == 0 else (chs[i - 1]["t1"] + ch["t0"]) / 2
            t1 = p["end"] if i == len(chs) - 1 else (ch["t1"] + chs[i + 1]["t0"]) / 2
            prev = shots[-1]
            sents = [s["t0"] for s in ch["sents"]]
            if prev["kind"] == "chunk" and family(prev["beats"][0][0]) == family(ch["visual"]) and family(ch["visual"]) in ("map", "sides", "field", "studio"):
                prev["t1"] = t1
                prev["beats"].append((ch["visual"], max(ch["t0"] - 0.15 - prev["t0"], 0.01), [s - prev["t0"] for s in sents]))
                continue
            shots.append(dict(kind="chunk", t0=t0, t1=t1, part=p, beats=[(ch["visual"], 0.0, [s - t0 for s in sents])]))
    shots.append(dict(kind="outro", t0=TL["outro"][0], t1=TL["outro"][1]))
    return shots


SHOTS = build_shots()


def shot_at(t):
    for i, s in enumerate(SHOTS):
        if s["t0"] <= t < s["t1"]:
            return i
    return len(SHOTS) - 1


def chunk_at(t):
    """Active (or most recent) chunk and its part."""
    best = None
    for p in TL["parts"]:
        for ch in p["chunks"]:
            if ch["t0"] - 0.3 <= t:
                best = (ch, p)
    return best


# ------------------------------------------------------------------------------------------ screens
@functools.lru_cache(maxsize=16)
def studio_screen(part_num, breaking=False):
    w, h = 900, 506
    img = vgrad(w, h, hexc("5A0A18") if breaking else hexc("13284A"), hexc("1A0508") if breaking else hexc("070F1E")).convert("RGB")
    _, emp = maps.base_layers()
    sil = emp.resize((w, int(h)), Image.LANCZOS)
    lay = Image.new("RGBA", (w, h), (200, 16, 46, 0) if not breaking else (255, 255, 255, 0))
    lay.putalpha(sil.point(lambda v: int(v * (0.55 if not breaking else 0.18))))
    comp(img, lay)
    if breaking:
        d = Draw(img)
        d.rectangle((0, 330, w, 420), fill=(255, 255, 255, 255))
        draw_text(img, (w / 2, 377), "BREAKING NEWS", font("black", 64), RED, anchor="mm")
        draw_text(img, (w / 2, 200), "UPDATE FROM RUSSIA", font("black", 58), WHITE, anchor="mm")
    else:
        part = [p for p in TL["parts"] if p["num"] == part_num][0] if part_num else None
        draw_text(img, (40, 60), "THE RUSSIAN", font("black", 64), WHITE, anchor="lm")
        draw_text(img, (40, 130), "CIVIL WAR", font("black", 64), WHITE, anchor="lm")
        draw_text(img, (42, 190), "1917 – 1922", font("bold", 36), GOLD, anchor="lm")
        if part:
            Draw(img).rectangle((0, 400, w, 470), fill=(200, 16, 46, 235))
            draw_text(img, (40, 435), f"PART {part['num']} · {part['title']}", font("black", 36), WHITE, anchor="lm")
    return img.convert("RGBA")


# ------------------------------------------------------------------------------------------ overlays
@functools.lru_cache(maxsize=1)
def logo_bug():
    im, s = ss_canvas(470, 80, 2)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, 120 * s, 80 * s), 8 * s, fill=RED)
    d.text((60 * s, 41 * s), "HNN", font=font("black", 46 * s), fill=WHITE, anchor="mm")
    d.rounded_rectangle((112 * s, 10 * s, 470 * s - 1, 70 * s), 6 * s, fill=(8, 14, 28, 220))
    d.text((134 * s, 30 * s), "HISTORY NEWS NETWORK", font=font("bold", 18 * s), fill=GOLD, anchor="lm")
    d.text((134 * s, 54 * s), "SPECIAL REPORT", font=font("black", 24 * s), fill=WHITE, anchor="lm")
    return down(im, s)


@functools.lru_cache(maxsize=1)
def ticker_strip():
    items = ["Bolsheviks seize power in Petrograd — October 1917",
             "Treaty of Brest-Litovsk takes Russia out of the First World War — March 1918",
             "Trotsky leads the new Red Army as Commissar for War — 1918",
             "Allied troops land at Murmansk and Arkhangelsk — 1918",
             "Japanese and American forces arrive in Vladivostok — 1918",
             "Admiral Kolchak declared 'Supreme Ruler' in Omsk — November 1918",
             "Yudenich's advance on Petrograd repulsed — October 1919",
             "Wrangel's forces evacuate Crimea — November 1920",
             "Famine strikes the Volga region — 1921",
             "USSR formally established — 30 December 1922"]
    f = font("semi", 28)
    parts = []
    for it in items:
        parts.append(it)
    sep = "   ◆   "
    txt = sep.join(parts) + sep
    wdt = int(f.getlength(txt)) + 10
    im = Image.new("RGBA", (wdt, 60), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = 0
    for it in parts:
        d.text((x, 30), it, font=f, fill=(235, 238, 245, 255), anchor="lm")
        x += f.getlength(it)
        d.text((x, 30), sep, font=f, fill=GOLD, anchor="lm")
        x += f.getlength(sep)
    return im, int(x)


@functools.lru_cache(maxsize=1)
def lower_base():
    im = Image.new("RGBA", (W, 160), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    # headline bar
    d.rectangle((40, 0, W - 40, 82), fill=(250, 250, 252, 248))
    d.rectangle((40, 82, W - 40, 88), fill=RED)
    # ticker bar
    d.rectangle((0, 98, W, 160), fill=(8, 14, 28, 245))
    d.rectangle((0, 98, 230, 160), fill=RED)
    d.text((115, 129), "1917–1922", font=font("black", 30), fill=WHITE, anchor="mm")
    return im


@functools.lru_cache(maxsize=32)
def chip(spk, place, breaking=False):
    f1 = font("black", 28); f2 = font("semi", 20)
    if breaking:
        name, role, col = "BREAKING", "NEWS UPDATE", RED
    elif spk == "F":
        name, role, col = "FILIPE", "STUDIO ANCHOR", NAVY
    else:
        name, role, col = "MIGUEL", "LIVE · " + place, hexc("1D3B6E")
    w = int(max(f1.getlength(name), f2.getlength(role))) + 50
    im = Image.new("RGBA", (w, 82), col); d = ImageDraw.Draw(im)
    d.text((24, 30), name, font=f1, fill=WHITE, anchor="lm")
    d.text((24, 60), role, font=f2, fill=GOLD if not breaking else WHITE, anchor="lm")
    return im


@functools.lru_cache(maxsize=16)
def headline_img(txt, maxw):
    size = 44
    while font("black", size).getlength(txt) > maxw and size > 26:
        size -= 2
    f = font("black", size)
    im = Image.new("RGBA", (int(f.getlength(txt)) + 10, 82), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((0, 43), txt, font=f, fill=INK, anchor="lm")
    return im


def caption_pieces():
    f = font("semi", 40)
    pieces = []
    for p in TL["parts"]:
        for ch in p["chunks"]:
            for s in ch["sents"]:
                lines = wrap(s["text"], f, 1500)
                if len(lines) <= 2:
                    pieces.append((s["t0"], s["t1"], s["text"], ch["spk"]))
                    continue
                words = s["text"].split()
                # split near the middle, preferring a comma
                mid = len(words) // 2
                cands = [i for i, w_ in enumerate(words[:-1]) if w_.endswith(",")]
                cut = min(cands, key=lambda i: abs(i + 1 - mid)) + 1 if cands and min(abs(i + 1 - mid) for i in cands) < len(words) * .25 else mid
                a, b = " ".join(words[:cut]), " ".join(words[cut:])
                tm = s["t0"] + (s["t1"] - s["t0"]) * len(a) / (len(a) + len(b))
                pieces.append((s["t0"], tm, a, ch["spk"]))
                pieces.append((tm, s["t1"], b, ch["spk"]))
    return pieces


CAPS = caption_pieces()


@functools.lru_cache(maxsize=256)
def caption_img(txt, spk):
    f = font("semi", 40)
    lines = wrap(txt, f, 1500)
    lw = max(f.getlength(l) for l in lines)
    w = int(lw) + 60; h = len(lines) * 52 + 26
    im, s = ss_canvas(w, h, 2)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w * s, h * s), 12 * s, fill=(0, 0, 0, 175))
    d.rectangle((0, 12 * s, 6 * s, h * s - 12 * s), fill=GOLD if spk == "M" else (120, 170, 255, 255))
    for i, l in enumerate(lines):
        d.text((w * s / 2, (13 + 26 + i * 52) * s), l, font=font("semi", 40 * s), fill=WHITE, anchor="mm")
    return down(im, s)


def overlays(img, t, shot):
    frame = int(t * FPS)
    vis = shot["beats"][0][0]
    part = shot["part"]
    a = anim(t - shot["t0"], 0, .4) if SHOTS.index(shot) > 0 and SHOTS[SHOTS.index(shot) - 1]["kind"] == "card" else 1.0
    # logo bug (compact on full-screen graphics)
    if vis.startswith("map_") or vis.startswith("gfx_"):
        paste(img, logo_bug().crop((0, 0, 120, 80)), (48, 40), a)
    else:
        paste(img, logo_bug(), (48, 40), a)
    # LIVE pill
    live = vis.startswith("field") or vis.startswith("twobox")
    d = Draw(img)
    if live:
        d.rounded_rectangle((W - 210, 44, W - 48, 96), 8, fill=(200, 16, 46, int(240 * a)))
        if (frame // 12) % 2 == 0:
            d.ellipse((W - 192, 60, W - 172, 80), fill=(255, 255, 255, int(255 * a)))
        draw_text(img, (W - 120, 71), "LIVE", font("black", 32), WHITE, anchor="mm", alpha=a)
    tracked(img, (W - 50, 120 if live else 70), "HISTORICAL RE-CREATION · " + part["years"].replace(" ", ""), font("bold", 18), (255, 255, 255, 200), track=2, anchor="r", alpha=a)
    # lower block
    base = lower_base()
    yb = 930
    paste(img, base, (0, yb), a)
    # ticker
    strip, period = ticker_strip()
    off = int((t * 110) % period)
    tick = Image.new("RGBA", (W - 240, 60), (0, 0, 0, 0))
    tick.alpha_composite(strip, (-off, 0))
    if strip.width - off < W:
        tick.alpha_composite(strip, (period - off, 0))
    paste(img, tick, (240, yb + 99), a)
    # chip + headline
    cp = chunk_at(t)
    spk = cp[0]["spk"] if cp else "F"
    breaking = vis == "studio_breaking" and (frame // 15) % 2 == 0
    c = chip(spk, part["place"], vis == "studio_breaking" and t - shot["t0"] < 2.5 and breaking)
    paste(img, c, (40, yb), a)
    hl = headline_img(part["headline"], W - 120 - c.width - 40)
    paste(img, hl, (40 + c.width + 28, yb), a)
    # captions
    for c0, c1, txt, sp in CAPS:
        if c0 - 0.05 <= t < c1 + 0.15:
            ci = caption_img(txt, sp)
            paste(img, ci, (W / 2 - ci.width / 2, yb - 22 - ci.height), 1.0)
            break


# ------------------------------------------------------------------------------------------ shot renderers
def r_studio(shot, t, frame, vis, out=(W, H)):
    lt = t - shot["t0"]; dur = shot["t1"] - shot["t0"]
    p = shot["part"]
    scr = studio_screen(p["num"], vis == "studio_breaking")
    if vis == "studio":
        cam = (1.42 + 0.04 * lt / max(dur, 1), 0.36, 0.42)
    elif vis == "studio_wide":
        cam = (lerp(1.25, 1.0, ease_io(lt / 4)), 0.5, 0.5)
    else:
        cam = (1.0 + 0.05 * lt / max(dur, 1), 0.5, 0.5)
    return scenes.studio_frame(scr, frame, ENV["F"], True, cam=cam, out=out)


def r_field(shot, t, frame, out=(W, H)):
    lt = t - shot["t0"]
    return scenes.field_frame(shot["part"]["field"], lt + shot["part"]["num"] * 7, frame, ENV["M"], True, out=out)


@functools.lru_cache(maxsize=1)
def static_tiles():
    rng = np.random.default_rng(5)
    return [Image.fromarray((rng.random((242, 430)) * 255).astype(np.uint8)).resize((860, 484), Image.NEAREST).convert("RGB") for _ in range(4)]


def r_twobox(shot, t, frame, vis):
    lt = t - shot["t0"]; dur = shot["t1"] - shot["t0"]
    img = gfx.bg_frame(t)
    pw, ph = 860, 484
    x0, x1, y = 80, W - 80 - pw, 210
    cp = chunk_at(t); spk = cp[0]["spk"] if cp else "F"
    left = r_studio(shot, t, frame, "studio", out=(1150, 647)).crop((145, 60, 145 + pw, 60 + ph))
    connecting = vis == "twobox_connect" and lt < dur * 0.62
    if connecting:
        right = static_tiles()[frame % 4].copy()
        d = Draw(right)
        d.rectangle((0, 0, pw, ph), fill=(10, 20, 40, 150))
        dots = "." * (1 + (frame // 8) % 3)
        draw_text(right, (pw / 2, ph / 2 - 20), "CONNECTING" + dots, font("black", 48), WHITE, anchor="mm")
        draw_text(right, (pw / 2, ph / 2 + 36), "SATELLITE LINK · RUSSIA", font("bold", 24), GOLD, anchor="mm")
    else:
        right = r_field(shot, t, frame, out=(pw, ph))
        if vis == "twobox_connect" and lt - dur * 0.62 < 0.25:
            right = Image.blend(static_tiles()[frame % 4], right.convert("RGB"), clamp((lt - dur * .62) / .25))
    for i, (im, x, name, role, who) in enumerate(((left, x0, "FILIPE", "STUDIO", "F"), (right, x1, "MIGUEL", "RUSSIA", "M"))):
        a = anim(lt, i * .15, .5) if SHOTS[SHOTS.index(shot) - 1]["kind"] != "chunk" or not SHOTS[SHOTS.index(shot) - 1]["beats"][0][0].startswith("twobox") else 1
        yy = y + (1 - a) * 40
        act = who == spk
        d = Draw(img)
        d.rectangle((x - 6, yy - 6, x + pw + 6, yy + ph + 6), fill=GOLD if act else (60, 80, 110, 255))
        img.paste(im.convert("RGB"), (int(x), int(yy)))
        d.rectangle((x - 6, yy + ph + 6, x + pw + 6, yy + ph + 70), fill=(8, 14, 28, 240))
        draw_text(img, (x + 20, yy + ph + 38), name, font("black", 34), WHITE, anchor="lm")
        draw_text(img, (x + 24 + font("black", 34).getlength(name) + 10, yy + ph + 40), role, font("bold", 24), GOLD if act else STEEL, anchor="lm")
        if act:
            lv = ENV[who][min(frame, len(ENV[who]) - 1)]
            for k in range(5):
                hh = 6 + lv * 36 * (0.6 + 0.4 * math.sin(frame * .9 + k * 1.7))
                d.rectangle((x + pw - 120 + k * 18, yy + ph + 38 - hh / 2, x + pw - 110 + k * 18, yy + ph + 38 + hh / 2), fill=GOLD)
    return img


def r_card(shot, t):
    p = shot["part"]
    lt = t - shot["t0"]; dur = shot["t1"] - shot["t0"]
    img = gfx.bg_frame(t, "red")
    d = Draw(img)
    # diagonal bars sweeping
    for k in range(6):
        x = lerp(-900, W + 300, ease((lt - k * 0.06) / 0.9)) - k * 140
        d.polygon([(x, 0), (x + 120, 0), (x - 280, H), (x - 400, H)], fill=(255, 255, 255, 18))
    a = anim(lt, .15, .5); a2 = anim(lt, .35, .6); a3 = anim(lt, .6, .5)
    out = clamp((lt - (dur - .45)) / .45)
    xo = -out * 120
    tracked(img, (160 + (1 - a) * -80 + xo, 380), f"PART {p['num']}", font("black", 64), GOLD, track=12, alpha=a * (1 - out))
    d.rectangle((160 + xo, 430, 160 + xo + 760 * ease(a2), 438), fill=(255, 255, 255, int(255 * (1 - out))))
    draw_text(img, (152 + (1 - a2) * 60 + xo, 530), p["title"], font("black", 130), WHITE, anchor="lm", alpha=a2 * (1 - out))
    draw_text(img, (160 + xo, 650), p["years"], font("bold", 52), CREAM, anchor="lm", alpha=a3 * (1 - out))
    # big ghost number
    draw_text(img, (W - 120, 560), str(p["num"]), font("black", 620), (255, 255, 255, 20), anchor="rm", alpha=a)
    paste(img, logo_bug(), (48, 40), a)
    return img


def r_intro(t):
    img = gfx.bg_frame(t)
    d = Draw(img)
    # light streaks
    for k in range(7):
        y = 140 + k * 120
        x = (t * (900 + k * 140) + k * 400) % (W + 1400) - 700
        d.rectangle((x, y, x + 500, y + 3), fill=(255, 255, 255, 40))
    _, emp = maps.base_layers()
    ma = anim(t, 2.8, 1.5)
    if ma > 0:
        lay = Image.new("RGBA", (W, H), (200, 16, 46, 0))
        lay.putalpha(emp.point(lambda v: int(v * .42 * ma)))
        comp(img, lay)
    # logo
    la = back(anim(t, .2, .7)) if t > .2 else 0
    move = ease_io(clamp((t - 1.7) / .8))
    if la > 0:
        sz = lerp(1.0, 0.55, move)
        im, s = ss_canvas(360, 200, 2)
        dd = ImageDraw.Draw(im)
        dd.rounded_rectangle((0, 0, 360 * s, 200 * s), 18 * s, fill=RED)
        dd.text((180 * s, 104 * s), "HNN", font=font("black", 130 * s), fill=WHITE, anchor="mm")
        im = down(im, s)
        sc = sz * la
        im = im.resize((max(1, int(360 * sc)), max(1, int(200 * sc))), Image.BILINEAR)
        cy = lerp(H / 2 - 40, 210, move)
        paste(img, im, (W / 2 - im.width / 2, cy - im.height / 2))
    sa = anim(t, 1.0, .6)
    tracked(img, (W / 2, lerp(H / 2 + 110, 330, move)), "HISTORY NEWS NETWORK", font("bold", 30), GOLD, track=10, anchor="m", alpha=sa)
    ta = anim(t, 2.6, .7)
    if ta > 0:
        d.rectangle((W / 2 - 300 * ease(ta), 395, W / 2 + 300 * ease(ta), 445), fill=RED)
        tracked(img, (W / 2, 420), "SPECIAL REPORT", font("black", 32), WHITE, track=10, anchor="m", alpha=ta)
    ha = anim(t, 3.4, .8)
    draw_text(img, (W / 2, 560 + (1 - ha) * 40), "THE RUSSIAN CIVIL WAR", font("black", 130), WHITE, anchor="mm", alpha=ha, shadow=(0, 8, (0, 0, 0, 150)))
    ya = anim(t, 4.2, .7)
    tracked(img, (W / 2, 690), "1917  –  1922", font("black", 56), GOLD, track=8, anchor="m", alpha=ya)
    ba = anim(t, 5.0, .7)
    draw_text(img, (W / 2, 790), "Live from the studio and from the field", font("med", 36), CREAM, anchor="mm", alpha=ba)
    fo = clamp((t - 7.4) / .6)
    if fo > 0:
        d.rectangle((0, 0, W, H), fill=(255, 255, 255, int(255 * fo * .0)))
    return img


def r_outro(t):
    img = gfx.bg_frame(t)
    lt = t
    a = anim(lt, .2, .7)
    draw_text(img, (W / 2, 250), "THANK YOU FOR WATCHING", font("black", 96), WHITE, anchor="mm", alpha=a)
    tracked(img, (W / 2, 330), "THE RUSSIAN CIVIL WAR · A SPECIAL REPORT", font("bold", 30), GOLD, track=6, anchor="m", alpha=a)
    rows = [("STUDIO ANCHOR", "FILIPE"), ("FIELD CORRESPONDENT", "MIGUEL")]
    for i, (r, n) in enumerate(rows):
        ra = anim(lt, 1.0 + i * .5, .6)
        x = W / 2 - 420 + i * 840 / 1
        x = W / 2 + (-260 if i == 0 else 260)
        paste(img, figure("F" if i == 0 else "M", 0, False, 0.42), (x - FW * .42 / 2, 400 + (1 - ra) * 30), ra)
        draw_text(img, (x, 750 + (1 - ra) * 30), n, font("black", 54), WHITE, anchor="mm", alpha=ra)
        draw_text(img, (x, 800 + (1 - ra) * 30), r, font("bold", 26), GOLD, anchor="mm", alpha=ra)
    ca = anim(lt, 2.5, .8)
    draw_text(img, (W / 2, 900), "HNN · History News Network is fictional — this is a historical news re-creation of events from 1917–1922.",
              font("med", 26), (190, 200, 215, 255), anchor="mm", alpha=ca)
    draw_text(img, (W / 2, 945), "Voices: synthesised (Piper TTS) · Maps: Natural Earth-derived outlines · Illustration & animation: procedural",
              font("med", 22), (150, 160, 180, 255), anchor="mm", alpha=ca)
    fo = clamp((lt - (TL["outro"][1] - TL["outro"][0] - 1.6)) / 1.4)
    if fo > 0:
        Draw(img).rectangle((0, 0, W, H), fill=(0, 0, 0, int(255 * fo)))
    return img


def render_shot(si, t):
    shot = SHOTS[si]
    frame = int(round(t * FPS))
    k = shot["kind"]
    if k == "intro":
        return r_intro(t)
    if k == "outro":
        return r_outro(t - shot["t0"])
    if k == "card":
        return r_card(shot, t)
    lt = t - shot["t0"]
    cur = [b for b in shot["beats"] if b[1] <= lt + 1e-6]
    vis = (cur[-1] if cur else shot["beats"][0])[0]
    fam = family(shot["beats"][0][0])
    if fam.startswith("studio"):
        img = r_studio(shot, t, frame, vis)
    elif fam == "field":
        img = r_field(shot, t, frame)
    elif fam.startswith("twobox"):
        img = r_twobox(shot, t, frame, vis)
    elif fam == "map":
        img = maps.render_map([(b[0], b[1]) for b in shot["beats"]], lt, frame)
        z = 1.0 + 0.035 * min(lt / 10, 1)
        if z > 1.001:
            cw, ch = W / z, H / z
            img = img.resize((W, H), Image.BILINEAR, box=((W - cw) / 2, (H - ch) * .4, (W - cw) / 2 + cw, (H - ch) * .4 + ch))
    else:
        img = gfx.render_gfx([(b[0], b[1]) for b in shot["beats"]], lt, sents=shot["beats"][0][2])
    img = img.convert("RGB") if img.mode != "RGB" else img
    overlays(img, t, shot)
    return img


def render_frame(n):
    t = n / FPS
    si = shot_at(t)
    img = render_shot(si, t)
    s = SHOTS[si]
    if si > 0 and t - s["t0"] < XFADE:
        prev = render_shot(si - 1, t)
        img = Image.blend(prev, img, ease_io((t - s["t0"]) / XFADE))
    return img


if __name__ == "__main__":
    start, end, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    if out.endswith(".png"):
        for n in range(start, end):
            render_frame(n).save(out.replace("%d", str(n)))
        sys.exit()
    p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for n in range(start, end):
        p.stdin.write(render_frame(n).tobytes())
        if n % 250 == 0:
            print(f"[{start}-{end}] frame {n}", flush=True)
    p.stdin.close(); p.wait()
