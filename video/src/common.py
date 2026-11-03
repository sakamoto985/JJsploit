import math, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

W, H, FPS = 1920, 1080, 25

FONT_DIR = "/usr/share/fonts/opentype/inter/"
FONTS = {
    "black": "InterDisplay-Black.otf", "xbold": "Inter-ExtraBold.otf", "bold": "Inter-Bold.otf",
    "semi": "Inter-SemiBold.otf", "med": "Inter-Medium.otf", "reg": "Inter-Regular.otf", "light": "Inter-Light.otf",
}
MONO = "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Bold.ttf"
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"


@functools.lru_cache(maxsize=256)
def font(kind, size):
    if kind == "mono":
        return ImageFont.truetype(MONO, size)
    if kind == "serif":
        return ImageFont.truetype(SERIF, size)
    return ImageFont.truetype(FONT_DIR + FONTS[kind], size)


def hexc(h, a=255):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


NAVY = hexc("0B1426"); DEEP = hexc("060B16"); RED = hexc("C8102E"); DRED = hexc("7A0A1C")
GOLD = hexc("E5B54A"); WHITE = hexc("FFFFFF"); CREAM = hexc("F2EEE6"); STEEL = hexc("8FA3BF")
INK = hexc("101826"); SLATE = hexc("2A3850")


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def ease(x):  # easeOutCubic
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_io(x):
    x = clamp(x)
    return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2


def anim(t, start, dur=0.6):
    return ease((t - start) / dur)


def back(x):  # easeOutBack
    x = clamp(x); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def lerp(a, b, x):
    return a + (b - a) * x


def lerpc(c1, c2, x):
    return tuple(int(lerp(a, b, x)) for a, b in zip(c1, c2))


def with_alpha(c, a):
    return (c[0], c[1], c[2], int(clamp(a, 0, 1) * (c[3] if len(c) > 3 else 255)))


def vgrad(w, h, top, bottom):
    t = np.linspace(0, 1, h)[:, None, None]
    a = np.array(top[:3], np.float32); b = np.array(bottom[:3], np.float32)
    arr = (a + (b - a) * t) * np.ones((1, w, 1))
    return Image.fromarray(arr.astype(np.uint8), "RGB").convert("RGBA")


def radial(w, h, cx, cy, r, color, power=2.0):
    y, x = np.mgrid[0:h, 0:w]
    d = np.sqrt((x - cx) ** 2 + (y - cy) ** 2) / r
    a = np.clip(1 - d, 0, 1) ** power
    arr = np.zeros((h, w, 4), np.uint8)
    arr[..., :3] = color[:3]
    arr[..., 3] = (a * (color[3] if len(color) > 3 else 255)).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def vignette(w, h, strength=0.65):
    y, x = np.mgrid[0:h, 0:w]
    d = np.sqrt(((x - w / 2) / (w / 2)) ** 2 + ((y - h / 2) / (h / 2)) ** 2) / 1.414
    a = np.clip((d - 0.35) / 0.65, 0, 1) ** 1.6 * strength
    arr = np.zeros((h, w, 4), np.uint8)
    arr[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def noise_tex(w, h, amount=10, seed=1):
    rng = np.random.default_rng(seed)
    n = rng.normal(0, amount, (h, w)).astype(np.float32)
    arr = np.zeros((h, w, 4), np.uint8)
    arr[..., :3] = 128
    arr[..., 3] = np.clip(np.abs(n) * 2, 0, 255).astype(np.uint8)
    arr[..., 0] = arr[..., 1] = arr[..., 2] = np.where(n > 0, 255, 0).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def Draw(img):
    """Blending draw for RGB canvases (PIL only blends RGBA fills on RGB images)."""
    return ImageDraw.Draw(img, "RGBA") if img.mode == "RGB" else ImageDraw.Draw(img)


def comp(dst, src, xy=(0, 0)):
    x, y = int(round(xy[0])), int(round(xy[1]))
    if src.mode == "RGB":
        dst.paste(src if dst.mode == "RGB" else src.convert("RGBA"), (x, y))
    elif dst.mode == "RGB":
        dst.paste(src, (x, y), src)
    else:
        dst.alpha_composite(src, (max(x, 0), max(y, 0)), (max(-x, 0), max(-y, 0), src.width, src.height))


def text_size(txt, f):
    b = f.getbbox(txt)
    return b[2] - b[0], b[3] - b[1]


def _text_layer(img, xy, txt, f, fill, anchor, alpha):
    a = clamp(alpha) * (fill[3] / 255 if len(fill) > 3 else 1)
    if a <= 0.003:
        return
    d = ImageDraw.Draw(img)
    if a >= 0.997:
        Draw(img).text(xy, txt, font=f, fill=tuple(fill[:3]) + (255,), anchor=anchor)
        return
    l, t, r, b = d.textbbox(xy, txt, font=f, anchor=anchor)
    l, t = int(l) - 2, int(t) - 2
    lay = Image.new("RGBA", (int(r) - l + 4, int(b) - t + 4), tuple(fill[:3]) + (0,))
    m = Image.new("L", lay.size, 0)
    ImageDraw.Draw(m).text((xy[0] - l, xy[1] - t), txt, font=f, fill=int(255 * a), anchor=anchor)
    lay.putalpha(m)
    comp(img, lay, (l, t))


def draw_text(img, xy, txt, f, fill, anchor="la", spacing=0, alpha=1.0, shadow=None):
    if shadow:
        _text_layer(img, (xy[0] + shadow[0], xy[1] + shadow[1]), txt, f, shadow[2], anchor, alpha)
    _text_layer(img, xy, txt, f, fill, anchor, alpha)


def tracked(img, xy, txt, f, fill, track=4, anchor="l", alpha=1.0):
    """Text with letter spacing. anchor l/m/r on x; y is the vertical middle."""
    widths = [f.getlength(c) for c in txt]
    total = sum(widths) + track * (len(txt) - 1)
    x = xy[0] - (total / 2 if anchor == "m" else total if anchor == "r" else 0)
    for c, wdt in zip(txt, widths):
        if c != " ":
            _text_layer(img, (x, xy[1]), c, f, fill, "lm", alpha)
        x += wdt + track
    return total


def tracked_len(txt, f, track=4):
    return sum(f.getlength(c) for c in txt) + track * (len(txt) - 1)


def wrap(txt, f, maxw):
    words, lines, cur = txt.split(), [], ""
    for w_ in words:
        test = (cur + " " + w_).strip()
        if f.getlength(test) <= maxw:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def ss_canvas(w, h, s=3):
    return Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0)), s


def down(img, s):
    return img.resize((img.width // s, img.height // s), Image.LANCZOS)


def star_pts(cx, cy, r, rot=-90, inner=0.382):
    pts = []
    for i in range(10):
        rr = r if i % 2 == 0 else r * inner
        a = math.radians(rot + i * 36)
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return pts


def paste(dst, src, xy, alpha=1.0):
    """Alpha-composite src (RGBA) onto dst (RGBA) at integer xy with extra opacity."""
    if alpha <= 0.003:
        return
    x, y = int(round(xy[0])), int(round(xy[1]))
    if src.mode == "RGB":
        src = src.convert("RGBA")
    if alpha < 0.997:
        a = src.getchannel("A").point(lambda v: int(v * alpha))
        src = src.copy(); src.putalpha(a)
    if x < dst.width and y < dst.height:
        comp(dst, src, (x, y))


def rrect(d, box, r, fill=None, outline=None, width=1):
    d.rounded_rectangle(box, r, fill=fill, outline=outline, width=width)


def panel(w, h, fill=(14, 22, 40, 235), border=(255, 255, 255, 40), r=18, s=2):
    im, s = ss_canvas(w, h, s)
    d = ImageDraw.Draw(im)
    rrect(d, (0, 0, w * s - 1, h * s - 1), r * s, fill=fill, outline=border, width=2 * s)
    return down(im, s)
