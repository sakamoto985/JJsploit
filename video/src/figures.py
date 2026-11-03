"""Flat-illustration characters: Filipe (studio anchor) and Miguel (field reporter)."""
import functools
from PIL import Image, ImageDraw
from common import *

FW, FH = 640, 760   # figure canvas (1x)


def _face(d, s, cx, cy, skin, mouth, blink, hair, brow):
    S = lambda v: v * s
    # ears
    for sx in (-1, 1):
        d.ellipse((S(cx + sx * 92 - 16), S(cy - 8), S(cx + sx * 92 + 16), S(cy + 38)), fill=skin)
    # head
    d.ellipse((S(cx - 92), S(cy - 112), S(cx + 92), S(cy + 118)), fill=skin)
    # shading on jaw
    d.chord((S(cx - 92), S(cy - 112), S(cx + 92), S(cy + 118)), 20, 160, fill=lerpc(skin, (0, 0, 0, 255), 0.08))
    d.ellipse((S(cx - 86), S(cy - 108), S(cx + 86), S(cy + 108)), fill=skin)
    # eyes
    ey = cy - 4
    for sx in (-1, 1):
        ex = cx + sx * 36
        if blink:
            d.line((S(ex - 14), S(ey + 2), S(ex + 14), S(ey + 2)), fill=(40, 28, 24, 255), width=int(S(4)))
        else:
            d.ellipse((S(ex - 15), S(ey - 11), S(ex + 15), S(ey + 11)), fill=(250, 248, 244, 255))
            d.ellipse((S(ex - 9), S(ey - 9), S(ex + 9), S(ey + 9)), fill=(52, 34, 24, 255))
            d.ellipse((S(ex - 3 + 3), S(ey - 6), S(ex + 3 + 3), S(ey)), fill=(255, 255, 255, 255))
        # brows
        d.line((S(ex - 20), S(ey - 27 - (sx * 2)), S(ex + 20), S(ey - 29 + (sx * 2))), fill=brow, width=int(S(7)))
    # nose
    d.line((S(cx + 2), S(cy + 8), S(cx - 6), S(cy + 38), S(cx + 8), S(cy + 40)),
           fill=lerpc(skin, (60, 30, 20, 255), 0.35), width=int(S(4)), joint="curve")
    # mouth
    my = cy + 66
    if mouth <= 0:
        d.arc((S(cx - 24), S(my - 14), S(cx + 24), S(my + 8)), 20, 160, fill=(120, 50, 45, 255), width=int(S(5)))
    else:
        h = 6 + mouth * 7
        d.rounded_rectangle((S(cx - 22 - mouth * 2), S(my - 6), S(cx + 22 + mouth * 2), S(my - 6 + h)),
                            radius=S(h / 2.2), fill=(95, 30, 34, 255))
        d.rectangle((S(cx - 16), S(my - 6), S(cx + 16), S(my - 1)), fill=(250, 248, 244, 255))
        if mouth >= 2:
            d.ellipse((S(cx - 12), S(my - 6 + h - 9), S(cx + 12), S(my - 6 + h + 1)), fill=(200, 90, 90, 255))


def _filipe(mouth, blink):
    im, s = ss_canvas(FW, FH, 3)
    d = ImageDraw.Draw(im)
    S = lambda v: v * s
    cx, cy = FW // 2, 250
    skin = hexc("C68E6A"); suit = hexc("17233D"); suit2 = hexc("223154")
    # torso / suit
    d.rounded_rectangle((S(cx - 250), S(430), S(cx + 250), S(FH + 80)), radius=S(120), fill=suit)
    d.polygon([(S(cx - 250), S(560)), (S(cx - 140), S(420)), (S(cx + 140), S(420)), (S(cx + 250), S(560)),
               (S(cx + 250), S(FH)), (S(cx - 250), S(FH))], fill=suit)
    # neck
    d.rectangle((S(cx - 42), S(330), S(cx + 42), S(440)), fill=lerpc(skin, (0, 0, 0, 255), 0.12))
    # shirt V
    d.polygon([(S(cx - 70), S(420)), (S(cx + 70), S(420)), (S(cx), S(600))], fill=(245, 245, 248, 255))
    # tie
    d.polygon([(S(cx - 18), S(440)), (S(cx + 18), S(440)), (S(cx + 10), S(462)), (S(cx - 10), S(462))], fill=RED)
    d.polygon([(S(cx - 10), S(460)), (S(cx + 10), S(460)), (S(cx + 22), S(600)), (S(cx), S(625)), (S(cx - 22), S(600))], fill=RED)
    # lapels
    d.polygon([(S(cx - 70), S(420)), (S(cx - 120), S(430)), (S(cx - 70), S(560)), (S(cx - 30), S(640))], fill=suit2)
    d.polygon([(S(cx + 70), S(420)), (S(cx + 120), S(430)), (S(cx + 70), S(560)), (S(cx + 30), S(640))], fill=suit2)
    # lapel pin
    d.polygon([(S(x), S(y)) for x, y in star_pts(cx - 118, 520, 9)], fill=GOLD)
    # head
    hair = hexc("2B1D16")
    _face(d, s, cx, cy, skin, mouth, blink, hair, hair)
    # hair (short, side part)
    d.chord((S(cx - 96), S(cy - 130), S(cx + 96), S(cy + 10)), 180, 360, fill=hair)
    d.polygon([(S(cx - 96), S(cy - 60)), (S(cx - 50), S(cy - 92)), (S(cx + 10), S(cy - 70)), (S(cx + 60), S(cy - 86)),
               (S(cx + 96), S(cy - 60)), (S(cx + 94), S(cy - 22)), (S(cx + 84), S(cy - 48)), (S(cx - 84), S(cy - 52)),
               (S(cx - 93), S(cy - 10))], fill=hair)
    # earpiece
    d.ellipse((S(cx + 84), S(cy + 6), S(cx + 100), S(cy + 22)), fill=(30, 30, 30, 255))
    return down(im, s)


def _miguel(mouth, blink):
    im, s = ss_canvas(FW, FH, 3)
    d = ImageDraw.Draw(im)
    S = lambda v: v * s
    cx, cy = FW // 2, 270
    skin = hexc("B97A56"); coat = hexc("4A4632"); coat2 = hexc("3A3727"); fur = hexc("6B5844"); fur2 = hexc("54443A")
    # coat body
    d.rounded_rectangle((S(cx - 265), S(450), S(cx + 265), S(FH + 80)), radius=S(130), fill=coat)
    d.polygon([(S(cx - 265), S(580)), (S(cx - 150), S(440)), (S(cx + 150), S(440)), (S(cx + 265), S(580)),
               (S(cx + 265), S(FH)), (S(cx - 265), S(FH))], fill=coat)
    d.line((S(cx), S(560), S(cx), S(FH)), fill=coat2, width=int(S(6)))
    for by in (600, 670, 740):
        d.ellipse((S(cx - 40 - 9), S(by - 9), S(cx - 40 + 9), S(by + 9)), fill=coat2)
    # neck + scarf
    d.rectangle((S(cx - 40), S(350), S(cx + 40), S(450)), fill=lerpc(skin, (0, 0, 0, 255), 0.12))
    scarf = hexc("8C8E91")
    d.rounded_rectangle((S(cx - 110), S(410), S(cx + 110), S(480)), radius=S(30), fill=scarf)
    d.polygon([(S(cx + 30), S(460)), (S(cx + 85), S(460)), (S(cx + 95), S(640)), (S(cx + 40), S(640))], fill=scarf)
    for yy in (600, 615, 630):
        d.line((S(cx + 45), S(yy), S(cx + 92), S(yy)), fill=hexc("6E7073"), width=int(S(3)))
    # fur collar
    d.chord((S(cx - 200), S(400), S(cx - 40), S(560)), 90, 300, fill=fur)
    d.chord((S(cx + 40), S(400), S(cx + 200), S(560)), 240, 450, fill=fur)
    # press badge
    d.rounded_rectangle((S(cx + 130), S(600), S(cx + 210), S(650)), radius=S(6), fill=(235, 235, 230, 255))
    d.rectangle((S(cx + 130), S(600), S(cx + 210), S(614)), fill=RED)
    d.text((S(cx + 170), S(636)), "PRESS", font=font("black", int(S(15))), fill=(20, 20, 30, 255), anchor="mm")
    # head
    hair = hexc("1E1611")
    _face(d, s, cx, cy, skin, mouth, blink, hair, hair)
    # stubble shading
    d.chord((S(cx - 80), S(cy + 20), S(cx + 80), S(cy + 116)), 0, 180, fill=lerpc(skin, (60, 40, 30, 255), 0.18))
    # redraw mouth on top of stubble
    dm = ImageDraw.Draw(im)
    my = cy + 66
    if mouth <= 0:
        dm.arc((S(cx - 24), S(my - 14), S(cx + 24), S(my + 8)), 20, 160, fill=(110, 45, 40, 255), width=int(S(5)))
    else:
        h = 6 + mouth * 7
        dm.rounded_rectangle((S(cx - 22 - mouth * 2), S(my - 6), S(cx + 22 + mouth * 2), S(my - 6 + h)),
                             radius=S(h / 2.2), fill=(95, 30, 34, 255))
        dm.rectangle((S(cx - 16), S(my - 6), S(cx + 16), S(my - 1)), fill=(250, 248, 244, 255))
    # ushanka hat
    d.rounded_rectangle((S(cx - 112), S(cy - 158), S(cx + 112), S(cy - 60)), radius=S(50), fill=fur)
    d.rounded_rectangle((S(cx - 120), S(cy - 78), S(cx + 120), S(cy - 42)), radius=S(18), fill=fur2)
    for sx in (-1, 1):  # ear flaps
        d.rounded_rectangle((S(cx + sx * 104 - 26), S(cy - 56), S(cx + sx * 104 + 26), S(cy + 70)), radius=S(22), fill=fur2)
    for i in range(14):  # fur texture
        x = cx - 100 + i * 15
        d.line((S(x), S(cy - 140), S(x + 6), S(cy - 120)), fill=fur2, width=int(S(3)))
    # hand + microphone
    mx, my2 = cx - 150, 520
    d.rounded_rectangle((S(mx - 12), S(my2 - 40), S(mx + 12), S(my2 + 130)), radius=S(8), fill=(25, 25, 28, 255))
    d.ellipse((S(mx - 30), S(my2 - 100), S(mx + 30), S(my2 - 30)), fill=(40, 40, 44, 255))
    for k in range(5):
        d.line((S(mx - 24), S(my2 - 90 + k * 12), S(mx + 24), S(my2 - 90 + k * 12)), fill=(70, 70, 76, 255), width=int(S(2)))
    d.rounded_rectangle((S(mx - 34), S(my2 - 28), S(mx + 34), S(my2 + 30)), radius=S(6), fill=RED)
    d.text((S(mx), S(my2 + 1)), "HNN", font=font("black", int(S(22))), fill=WHITE, anchor="mm")
    # glove
    d.rounded_rectangle((S(mx - 40), S(my2 + 50), S(mx + 40), S(my2 + 130)), radius=S(30), fill=hexc("2A2620"))
    return down(im, s)


@functools.lru_cache(maxsize=64)
def figure(who, mouth, blink, scale=1.0):
    im = _filipe(mouth, blink) if who == "F" else _miguel(mouth, blink)
    if scale != 1.0:
        im = im.resize((int(FW * scale), int(FH * scale)), Image.LANCZOS)
    return im


def mouth_level(env, frame, who_speaking):
    if not who_speaking:
        return 0
    i = min(frame, len(env) - 1)
    v = env[i]
    return 0 if v < 0.08 else 1 if v < 0.3 else 2 if v < 0.6 else 3


def blink_at(frame, seed):
    # blink ~ every 3.3s for 3 frames
    period = 83 + (seed * 17) % 23
    return (frame + seed * 31) % period < 3
