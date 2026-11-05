"""Synthesise music (news theme), stingers and field ambience; mix with the voice track."""
import os, sys, json, math, wave
import numpy as np

BUILD = os.environ["BUILD_DIR"]
sys.path.insert(0, os.path.dirname(__file__))
TL = json.load(open(f"{BUILD}/timeline.json"))
SR = 48000
DUR = TL["duration"]
N = int(DUR * SR) + SR
rng = np.random.default_rng(11)


def hz(note):
    names = {"C": 0, "C#": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}
    n, o = note[:-1], int(note[-1])
    return 440.0 * 2 ** ((names[n] + 12 * (o + 1) - 69) / 12)


def adsr(n, a=0.01, d=0.1, s=0.7, r=0.2):
    t = np.arange(n) / SR
    dur = n / SR
    env = np.where(t < a, t / a, np.where(t < a + d, 1 - (1 - s) * (t - a) / d, s))
    rel = np.clip((dur - t) / r, 0, 1)
    return env * rel


def tone(f, dur, harm=8, bright=1.0, detune=0.0, env=None):
    n = int(dur * SR); t = np.arange(n) / SR
    out = np.zeros(n)
    for dt in ([0] if not detune else [-detune, 0, detune]):
        ff = f * (1 + dt)
        for k in range(1, harm + 1):
            if ff * k > 9000:
                break
            out += np.sin(2 * np.pi * ff * k * t + k) / (k ** (1.0 / bright + .2))
    out /= max(np.abs(out).max(), 1e-6)
    return out * (env if env is not None else adsr(n))


def smooth(x, w):
    if w <= 1:
        return x
    c = np.cumsum(np.concatenate([[0], x]))
    y = (c[w:] - c[:-w]) / w
    return np.concatenate([y, np.full(w - 1, y[-1])])


def add(buf, sig, t0, gain=1.0):
    i = int(t0 * SR)
    if i >= len(buf):
        return
    j = min(len(buf), i + len(sig))
    buf[i:j] += sig[:j - i] * gain


def timpani(f=55, dur=1.6):
    n = int(dur * SR); t = np.arange(n) / SR
    fr = f * (1 + 0.5 * np.exp(-t * 30))
    ph = 2 * np.pi * np.cumsum(fr) / SR
    body = np.sin(ph) * np.exp(-t * 3.0) + 0.4 * np.sin(2 * ph) * np.exp(-t * 5)
    click = rng.normal(0, 1, n) * np.exp(-t * 60) * 0.5
    return (body + smooth(click, 6)) * 0.9


def brass(notes, dur, gain=1.0):
    out = None
    for nt in notes:
        s = tone(hz(nt), dur, harm=12, bright=1.4, detune=0.003, env=adsr(int(dur * SR), .03, .25, .55, .35))
        out = s if out is None else out + s
    return out / len(notes) * gain


def pad(notes, dur):
    out = None
    for nt in notes:
        s = tone(hz(nt), dur, harm=6, bright=.7, detune=0.004, env=adsr(int(dur * SR), .6, .5, .8, .8))
        out = s if out is None else out + s
    return out / len(notes)


def pluck(f, dur=0.12):
    n = int(dur * SR); t = np.arange(n) / SR
    s = (np.sin(2 * np.pi * f * t) + .5 * np.sin(4 * np.pi * f * t) + .25 * np.sin(6 * np.pi * f * t)) * np.exp(-t * 28)
    return s


def whoosh(dur=0.7, rise=True):
    n = int(dur * SR); t = np.arange(n) / SR
    noise = rng.normal(0, 1, n)
    env = np.sin(np.pi * t / dur) ** 2
    # sweeping band: mix of smoothed versions
    lo = smooth(noise, 40); hi = noise - smooth(noise, 6)
    mix = np.linspace(0, 1, n) if rise else np.linspace(1, 0, n)
    return (lo * (1 - mix) * 3 + hi * mix * .6) * env * 0.5


BPM = 112
BEAT = 60 / BPM
CHORDS = [["D3", "F3", "A3", "D4"], ["Bb2", "D3", "F3", "Bb3"], ["G2", "Bb2", "D3", "G3"], ["A2", "C#3", "E3", "A3"]]
BASS = ["D2", "Bb1", "G1", "A1"]


def theme_bed(t0, t1, buf, gain=1.0):
    """Driving news-bed: 16th pulse + pad + bass, 4-bar loop."""
    bar = 4 * BEAT
    nb = int(math.ceil((t1 - t0) / bar))
    for b in range(nb):
        tb = t0 + b * bar
        ch = CHORDS[b % 4]
        add(buf, pad(ch, bar + 0.6), tb, 0.22 * gain)
        add(buf, tone(hz(BASS[b % 4]), bar * .95, harm=5, bright=.6, env=adsr(int(bar * .95 * SR), .02, .3, .6, .3)), tb, 0.30 * gain)
        for k in range(16):
            f = hz(ch[[0, 2, 1, 3][k % 4]]) * 2
            add(buf, pluck(f), tb + k * BEAT / 4, (0.13 if k % 4 == 0 else 0.08) * gain)
        if b % 2 == 0:
            add(buf, timpani(hz(BASS[b % 4]) * 2, 1.0), tb, 0.10 * gain)


def build_music():
    music = np.zeros(N)
    # ---- intro (0 – 8 s)
    add(music, timpani(55, 2.0), 0.20, 0.9)
    add(music, brass(["D3", "A3", "D4", "F4"], 1.2), 0.20, 0.7)
    for k, nt in enumerate(["D4", "F4", "A4", "D5"]):
        add(music, brass([nt, nt[:-1] + str(int(nt[-1]) - 1)], BEAT * .6), 1.0 + k * BEAT / 2, 0.55)
    IL = TL["intro"][1]
    theme_bed(1.0, IL - 0.6, music, 0.9)
    add(music, whoosh(0.8), 2.0, 0.6)
    add(music, timpani(49, 1.5), 2.65, 0.7)
    add(music, brass(["Bb2", "F3", "Bb3", "D4"], 0.7), 2.65, 0.6)
    add(music, timpani(55, 2.0), 3.4, 0.9)
    add(music, brass(["A2", "E3", "A3", "C#4"], 1.4), 3.4, 0.6)
    if IL >= 7:
        add(music, brass(["D3", "A3", "D4", "F4", "A4"], 3.0), 5.0, 0.7)
        add(music, timpani(55, 3.0), 5.0, 1.0)
    # ---- part cards
    for p in TL["parts"]:
        c0 = p["card"][0]
        add(music, whoosh(0.7), c0 - 0.45, 0.8)
        add(music, timpani(55, 2.0), c0 + 0.15, 0.9)
        ch = CHORDS[(p["num"] - 1) % 4]
        add(music, brass(ch, 1.6), c0 + 0.15, 0.55)
        for k in range(6):
            add(music, pluck(hz(ch[k % 4]) * 2), c0 + 0.15 + k * BEAT / 2, 0.22)
        add(music, whoosh(0.5, rise=False), p["card"][1] - 0.35, 0.4)
    # ---- background bed under the report (quiet; ducked under voice later)
    bed = np.zeros(N)
    for p in TL["parts"]:
        theme_bed(p["card"][1] - 0.2, p["end"] + 0.6, bed, 1.0)
    # fade bed around cards
    env = np.ones(N)
    for p in TL["parts"]:
        a, b = int((p["card"][1] - .2) * SR), int((p["card"][1] + 1.5) * SR)
        env[a:b] *= np.linspace(0, 1, b - a)
        a, b = int((p["end"] - 0.6) * SR), int((p["end"] + 0.6) * SR)
        env[a:b] *= np.linspace(1, 0, b - a)
        env[int((p["end"] + .6) * SR):int((p["end"] + 3.6) * SR)] = 0
    env[:int(8.0 * SR)] = 0
    bed *= env
    # ---- outro
    o0 = TL["outro"][0]
    add(music, timpani(55, 2.0), o0 + 0.1, 0.9)
    add(music, brass(["D3", "A3", "D4", "F4"], 1.6), o0 + 0.1, 0.6)
    OL = TL["outro"][1] - o0
    theme_bed(o0 + 0.1, o0 + OL - 2.6, music, 0.8)
    add(music, brass(["D3", "A3", "D4", "F4", "A4"], 2.4), o0 + OL - 2.5, 0.7)
    add(music, timpani(55, 2.4), o0 + OL - 2.5, 1.0)
    return music, bed


# ------------------------------------------------------------------------------- ambience
def reverb_tail(sig, decay=1.2, mix=0.5):
    n = int(decay * SR)
    ir = rng.normal(0, 1, n) * np.exp(-np.arange(n) / SR * (6.9 / decay))
    ir = smooth(ir, 8)
    L = len(sig) + n
    F = 1 << (L - 1).bit_length()
    wet = np.fft.irfft(np.fft.rfft(sig, F) * np.fft.rfft(ir, F), F)[:L]
    wet /= max(np.abs(wet).max(), 1e-6)
    out = np.zeros(L); out[:len(sig)] += sig * (1 - mix)
    return out + wet * mix * np.abs(sig).max()


def gunshot(dist=1.0):
    n = int(0.25 * SR); t = np.arange(n) / SR
    s = rng.normal(0, 1, n) * np.exp(-t * 35)
    s = smooth(s, int(4 + dist * 18))
    s += np.sin(2 * np.pi * 80 * t) * np.exp(-t * 25) * .6
    return reverb_tail(s / np.abs(s).max(), 1.4, .55 + .3 * dist)


def explosion():
    n = int(2.5 * SR); t = np.arange(n) / SR
    s = np.cumsum(rng.normal(0, 1, n)); s -= smooth(s, 2000); s /= np.abs(s).max()
    s = s * np.exp(-t * 1.6) + np.sin(2 * np.pi * 38 * t) * np.exp(-t * 2.5) * .8
    return reverb_tail(s, 2.0, .5)


def bell():
    n = int(4.0 * SR); t = np.arange(n) / SR
    f = 196
    s = sum(a * np.sin(2 * np.pi * f * r * t) * np.exp(-t * d) for r, a, d in ((1, 1, .9), (2.0, .5, 1.3), (2.4, .4, 1.6), (3.0, .25, 2), (4.2, .2, 2.6)))
    return s / 2.4


def wind(n, strength=1.0):
    w = np.cumsum(rng.normal(0, 1, n)); w -= smooth(w, 4800); w /= np.abs(w).max() + 1e-6
    hiss = rng.normal(0, 1, n); hiss = smooth(hiss, 30) - smooth(hiss, 300)
    hiss /= np.abs(hiss).max() + 1e-6
    t = np.arange(n) / SR
    mod = 0.6 + 0.4 * np.sin(2 * np.pi * t / 7.3) * np.sin(2 * np.pi * t / 3.1 + 1)
    return (w * .7 + hiss * .35) * mod * strength


def build_ambience():
    sys.argv = sys.argv[:1]
    import render as R
    amb = np.zeros(N)
    for s in R.SHOTS:
        if s["kind"] != "chunk":
            continue
        v = s["beats"][0][0]
        if not (v.startswith("field") or v.startswith("twobox")):
            continue
        kind = s["part"]["field"]
        lvl = 1.0 if v.startswith("field") else 0.45
        t0, t1 = s["t0"], s["t1"]
        n = int((t1 - t0 + 0.6) * SR)
        layer = wind(n, {"city": .5, "ruins": .4, "camp": .45, "quiet": .3}[kind])
        loc = np.random.default_rng(int(t0 * 10))
        ev = np.zeros(n + 6 * SR)
        tt = 0.4
        while tt < t1 - t0:
            if kind == "ruins":
                if loc.random() < .25:
                    add(ev, explosion(), tt, .7)
                else:
                    burst = loc.integers(1, 5)
                    for k in range(burst):
                        add(ev, gunshot(loc.uniform(.5, 1)), tt + k * loc.uniform(.08, .2), loc.uniform(.25, .5))
                tt += loc.uniform(0.8, 2.2)
            elif kind == "city":
                for k in range(loc.integers(1, 3)):
                    add(ev, gunshot(1.0), tt + k * .15, loc.uniform(.12, .25))
                tt += loc.uniform(2.5, 5)
            elif kind == "camp":
                add(ev, explosion(), tt, .3) if loc.random() < .5 else add(ev, gunshot(1.0), tt, .15)
                tt += loc.uniform(3, 6)
            else:
                add(ev, bell(), tt + 1.0, .25)
                tt += 7.5
        layer = layer + ev[:n]
        fade = np.ones(n); f = int(.4 * SR)
        fade[:f] = np.linspace(0, 1, f); fade[-f:] = np.linspace(1, 0, f)
        add(amb, layer * fade, t0 - 0.2, lvl * 0.5)
    return amb


def save(path, x):
    x = np.clip(x, -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())


if __name__ == "__main__":
    voice = np.load(f"{BUILD}/voice.npy")[:N]
    voice = np.pad(voice, (0, N - len(voice)))
    music, bed = build_music()
    amb = build_ambience()
    # ducking: follow the voice envelope
    venv = smooth(np.abs(voice), int(0.05 * SR))
    venv = smooth((venv > 0.02).astype(float), int(0.25 * SR))
    duck_bed = 1 - 0.72 * venv
    duck_amb = 1 - 0.45 * venv
    music /= np.abs(music).max(); bed /= max(np.abs(bed).max(), 1e-6); amb /= max(np.abs(amb).max(), 1e-6)
    mix = voice * 1.0 + music * 0.85 + bed * 0.16 * duck_bed + amb * 0.30 * duck_amb
    mix /= np.abs(mix).max() * 1.05
    save(f"{BUILD}/mix_raw.wav", mix)
    print("audio ok")
