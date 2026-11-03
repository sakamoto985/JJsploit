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

INTRO, CARD, OUTRO = 8.0, 3.0, 10.0
GAP_SENT, GAP_TURN, GAP_SAME = 0.28, 0.55, 0.4
t = INTRO
timeline = dict(intro=[0, INTRO], parts=[], sr=SR)
clips = []
idx = 0
for p in PARTS:
    part = dict(num=p["num"], title=p["title"], years=p["years"], headline=p["headline"],
                field=p["field"], place=p["place"], card=[t, t + CARD], chunks=[])
    t += CARD + 0.25
    prev = None
    for spk, text, vis in p["chunks"]:
        if prev is not None:
            t += GAP_TURN if prev != spk else GAP_SAME
        ch = dict(spk=spk, text=text, visual=vis, sents=[])
        start = t
        for si, s in enumerate(split_sentences(text)):
            if si: t += GAP_SENT
            a = synth(s, spk, f"{OUT}/tts/{idx:03d}_{si}_{spk}.wav")
            clips.append((t, a, spk))
            ch["sents"].append(dict(text=s, t0=t, t1=t + len(a) / SR))
            t += len(a) / SR
        ch["t0"], ch["t1"] = start, t
        part["chunks"].append(ch)
        prev = spk
        idx += 1
    t += 0.9
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
