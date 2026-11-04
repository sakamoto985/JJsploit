"""Synthesize every sentence with Piper TTS and lay out the master timeline."""
import json, re, subprocess, sys, wave, os
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from script_data import PARTS

PIPER = sys.argv[1]          # dir with piper binary + voices/
OUT = sys.argv[2]            # build dir
SR = 48000
VOICE = {"F": ("en-us-ryan-high.onnx", 1.0), "M": ("en-gb-alan-low.onnx", 0.98)}
SAY = [(r"\bUSSR\b", "U. S. S. R."), (r"\b1917\b", "nineteen seventeen"), (r"\b1920\b", "nineteen twenty"),
       (r"\b1921\b", "nineteen twenty-one"), (r"\b1922\b", "nineteen twenty-two"), ("Petrograd", "Petro-grad")]
os.makedirs(f"{OUT}/tts", exist_ok=True)

def split_sentences(t):
    return [s for s in re.split(r"(?<=[.!?])\s+", t.strip()) if s]

def synth(text, spk, path):
    if not os.path.exists(path):
        say = text
        for a, b in SAY: say = re.sub(a, b, say)
        model, ls = VOICE[spk]
        raw = path + ".raw.wav"
        subprocess.run([f"{PIPER}/piper/piper", "-m", f"{PIPER}/voices/{model}", "-f", raw,
                        "--length_scale", str(ls), "--sentence_silence", "0"], input=say.encode(),
                       check=True, capture_output=True)
        af = "silenceremove=start_periods=1:start_threshold=-50dB,areverse,silenceremove=start_periods=1:start_threshold=-50dB,areverse"
        if spk == "M":   # field correspondent: slightly band-limited "satellite" feel
            af += ",highpass=f=180,lowpass=f=7000,acompressor=threshold=-18dB:ratio=3"
        else:
            af += ",highpass=f=70,acompressor=threshold=-20dB:ratio=2.5"
        af += ",loudnorm=I=-17:TP=-2:LRA=7"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", raw, "-af", af, "-ar", str(SR), "-ac", "1",
                        "-sample_fmt", "s16", path], check=True)
        os.remove(raw)
    with wave.open(path) as w:
        return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768

MEDIA = os.environ.get("MEDIA_DIR", "")          # fi1.mp4.. (Filipe) / mi1.mp4.. (Miguel)
PREFIX = {"F": "fi", "M": "mi"}


def media_path(spk, n):
    p = os.path.join(MEDIA, f"{PREFIX[spk]}{n}.mp4") if MEDIA else ""
    return p if p and os.path.exists(p) else None


def speech_segments(path, noise="-35dB", d=0.2):
    out = subprocess.run(["ffmpeg", "-i", path, "-af", f"silencedetect=noise={noise}:d={d}", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                               capture_output=True, text=True).stdout)
    sil = []; cur = None
    for m in re.finditer(r"silence_(start|end): ([0-9.]+)", out):
        if m.group(1) == "start": cur = float(m.group(2))
        else: sil.append((cur, float(m.group(2)))); cur = None
    if cur is not None: sil.append((cur, dur))
    segs, t0 = [], 0.0
    for a, b in sil:
        if a - t0 > 0.12: segs.append((t0, a))
        t0 = b
    if dur - t0 > 0.12: segs.append((t0, dur))
    return segs, dur


SEG_BIN = os.environ.get("SEG_BIN"); SEG_MODEL = os.environ.get("SEG_MODEL")


def peak_gain(path):
    out = subprocess.run(["ffmpeg", "-i", path, "-af", "volumedetect", "-f", "null", "-"], capture_output=True, text=True).stderr
    m = re.search(r"max_volume: ([-0-9.]+) dB", out)
    return max(0.0, -3.0 - float(m.group(1))) if m else 0.0


def person_crop(path, dur):
    """16:9 crop framing the speaker (head + torso), found with the person-segmentation model."""
    from PIL import Image
    png = f"{OUT}/real/_probe.png"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{dur / 2:.2f}", "-i", path, "-frames:v", "1", png], check=True)
    im = Image.open(png).convert("RGB"); W0, H0 = im.size
    if not (SEG_BIN and SEG_MODEL):
        return None
    x = np.asarray(im.resize((320, 320)), np.float32); x /= x.max()
    x = (x - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
    x.transpose(2, 0, 1).astype(np.float32).tofile(png + ".in")
    subprocess.run([SEG_BIN, SEG_MODEL, png + ".in", png + ".out"], check=True, capture_output=True)
    m = np.fromfile(png + ".out", np.float32).reshape(320, 320); m = (m - m.min()) / (m.max() - m.min() + 1e-6)
    ys, xs = np.where(m > 0.5)
    if len(ys) < 200:
        return None
    top = ys.min() / 320 * H0
    cx = np.median(xs[ys < np.percentile(ys, 30)]) / 320 * W0     # centre on the head/upper body
    ch = min(H0, max((H0 - top) * 1.25, H0 * 0.5)); cw = ch * 16 / 9
    if cw > W0:
        cw = W0; ch = cw * 9 / 16
    y0 = max(0, min(top - ch * 0.10, H0 - ch)); x0 = max(0, min(cx - cw / 2, W0 - cw))
    return int(cw) // 2 * 2, int(ch) // 2 * 2, int(x0), int(y0)


def real_line(path, sents, tag):
    """Trim the recording to speech, normalise it, extract frames; return audio + sentence offsets."""
    g = peak_gain(path)
    probe = path
    if g > 1:
        probe = f"{OUT}/real/_gain.wav"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", path, "-af", f"volume={g:.1f}dB", "-ac", "1", probe], check=True)
    segs, dur = speech_segments(probe)
    segs = [s for s in segs if s[1] - s[0] > 0.18] or [(0, dur)]
    a0 = max(0.0, segs[0][0] - 0.18); a1 = min(dur, segs[-1][1] + 0.25)
    wav = f"{OUT}/real/{tag}.wav"; fdir = f"{OUT}/real/{tag}"
    if not os.path.exists(wav):
        af = f"volume={g:.1f}dB,highpass=f=80,afftdn=nf=-25,acompressor=threshold=-20dB:ratio=2.5,loudnorm=I=-17:TP=-2:LRA=7"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{a0:.3f}", "-t", f"{a1 - a0:.3f}", "-i", path, "-af", af,
                        "-ar", str(SR), "-ac", "1", "-sample_fmt", "s16", wav], check=True)
    if not os.path.isdir(fdir):
        os.makedirs(fdir)
        crop = person_crop(path, dur)
        cf = f"crop={crop[0]}:{crop[1]}:{crop[2]}:{crop[3]}," if crop else ""
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{a0:.3f}", "-t", f"{a1 - a0:.3f}", "-i", path,
                        "-vf", f"fps=25,{cf}scale=1280:720:force_original_aspect_ratio=increase:flags=lanczos,crop=1280:720,unsharp=5:5:0.6", "-q:v", "3",
                        f"{fdir}/%05d.jpg"], check=True)
    with wave.open(wav) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    # sentence boundaries: split speech time by text length, snapped to the nearest pause
    segs = [(max(s0 - a0, 0), min(s1 - a0, a1 - a0)) for s0, s1 in segs]
    sp0, sp1 = segs[0][0], segs[-1][1]
    pauses = [(segs[i][1] + segs[i + 1][0]) / 2 for i in range(len(segs) - 1)]
    lens = np.cumsum([len(x) for x in sents]); lens = lens / lens[-1]
    bounds = [sp0]
    for f in lens[:-1]:
        tgt = sp0 + (sp1 - sp0) * f
        near = [p for p in pauses if abs(p - tgt) < 0.9 and p > bounds[-1] + 0.3]
        bounds.append(min(near, key=lambda p: abs(p - tgt)) if near else tgt)
    bounds.append(sp1)
    offs = [(bounds[i], bounds[i + 1]) for i in range(len(sents))]
    nfr = len([f for f in os.listdir(fdir) if f.endswith(".jpg")])
    # tighten: keep speech, shorten long pauses to MAXP, then speed up by SPEED (picture follows the same map)
    keep = []
    s0 = max(0.0, sp0 - 0.08)
    for i in range(len(segs) - 1):
        gap = segs[i + 1][0] - segs[i][1]
        if gap > MAXP:
            keep.append((s0, segs[i][1] + MAXP / 2)); s0 = segs[i + 1][0] - MAXP / 2
    keep.append((s0, min(sp1 + 0.12, len(a) / SR)))
    pieces, mp, dst = [], [], 0.0
    for k0, k1 in keep:
        pieces.append(a[int(k0 * SR):int(k1 * SR)])
        mp.append((dst / SPEED, k0, (k1 - k0) / SPEED)); dst += k1 - k0
    xf = int(0.008 * SR)
    for i in range(1, len(pieces)):
        if len(pieces[i]) > xf and len(pieces[i - 1]) > xf:
            pieces[i][:xf] *= np.linspace(0, 1, xf); pieces[i - 1][-xf:] *= np.linspace(1, 0, xf)
    cat = np.concatenate(pieces)
    if abs(SPEED - 1) > 1e-3:
        tw = f"{OUT}/real/_tempo_in.wav"; to = f"{OUT}/real/_tempo_out.wav"
        with wave.open(tw, "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(cat, -1, 1) * 32767).astype(np.int16).tobytes())
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", tw, "-af", f"atempo={SPEED}", "-ar", str(SR), to], check=True)
        with wave.open(to) as w:
            cat = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768

    def to_dst(x):
        for d0, k0, ln in mp:
            if x <= k0 + ln * SPEED:
                return d0 + max(x - k0, 0) / SPEED
        return mp[-1][0] + mp[-1][2]
    offs = [(to_dst(o0), to_dst(o1)) for o0, o1 in offs]
    return cat, offs, fdir, nfr, mp


INTRO, CARD, OUTRO = 7.0, 2.4, 7.5
GAP_SENT, GAP_TURN, GAP_SAME = 0.28, 0.3, 0.4
SPEED = float(os.environ.get("SPEED", "1.18")); MAXP = float(os.environ.get("MAXP", "0.22"))
os.makedirs(f"{OUT}/real", exist_ok=True)
t = INTRO
timeline = dict(intro=[0, INTRO], parts=[], sr=SR, lines=[])
clips = []
idx = 0
count = {"F": 0, "M": 0}
for p in PARTS:
    part = dict(num=p["num"], title=p["title"], years=p["years"], headline=p["headline"],
                field=p["field"], place=p["place"], card=[t, t + CARD], chunks=[])
    t += CARD + 0.25
    # group consecutive same-speaker chunks into the original script lines
    groups = []
    for spk, text, vis in p["chunks"]:
        if groups and groups[-1][0] == spk:
            groups[-1][1].append((text, vis))
        else:
            groups.append((spk, [(text, vis)]))
    prev = None
    for spk, items in groups:
        if prev is not None:
            t += GAP_TURN
        count[spk] += 1
        n = count[spk]
        mp = media_path(spk, n)
        line = dict(spk=spk, n=n, t0=t, media=None)
        if mp:
            all_sents = [s for text, _ in items for s in split_sentences(text)]
            a, offs, fdir, nfr, vmap = real_line(mp, all_sents, f"{PREFIX[spk]}{n}")
            clips.append((t, a, spk))
            line.update(media=fdir, nframes=nfr, map=vmap, speed=SPEED)
            k = 0
            for text, vis in items:
                ch = dict(spk=spk, text=text, visual=vis, sents=[], line=len(timeline["lines"]))
                for s in split_sentences(text):
                    ch["sents"].append(dict(text=s, t0=t + offs[k][0], t1=t + offs[k][1])); k += 1
                ch["t0"], ch["t1"] = ch["sents"][0]["t0"], ch["sents"][-1]["t1"]
                part["chunks"].append(ch)
            t += len(a) / SR
        else:
            for ci, (text, vis) in enumerate(items):
                if ci:
                    t += GAP_SAME
                ch = dict(spk=spk, text=text, visual=vis, sents=[], line=len(timeline["lines"]))
                start = t
                for si, s in enumerate(split_sentences(text)):
                    if si: t += GAP_SENT
                    a = synth(s, spk, f"{OUT}/tts/{idx:03d}_{si}_{spk}.wav")
                    clips.append((t, a, spk))
                    ch["sents"].append(dict(text=s, t0=t, t1=t + len(a) / SR))
                    t += len(a) / SR
                ch["t0"], ch["t1"] = start, t
                part["chunks"].append(ch)
                idx += 1
        line["t1"] = t
        timeline["lines"].append(line)
        prev = spk
    t += 0.5
    part["end"] = t
    timeline["parts"].append(part)
timeline["outro"] = [t, t + OUTRO]
timeline["duration"] = t + OUTRO

voice = np.zeros(int(timeline["duration"] * SR) + SR, np.float32)
env = {"F": np.zeros(int(timeline["duration"] * 25) + 50, np.float32), "M": None}
env["M"] = env["F"].copy()
for t0, a, spk in clips:
    i = int(t0 * SR); voice[i:i + len(a)] += a
    hop = SR // 25
    for k in range(len(a) // hop):
        env[spk][int(t0 * 25) + k] = float(np.sqrt(np.mean(a[k*hop:(k+1)*hop] ** 2)))
for k in env:
    e = env[k]; e /= max(e.max(), 1e-6)
    timeline["env_" + k] = [round(float(x), 3) for x in e]
np.save(f"{OUT}/voice.npy", voice)
json.dump(timeline, open(f"{OUT}/timeline.json", "w"))
print("duration %.1fs, %d clips" % (timeline["duration"], len(clips)))
