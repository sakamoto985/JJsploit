"""Per-frame person mattes for the field correspondent's footage (U^2-Net-P via the onnxruntime C runner)."""
import os, sys, glob, subprocess
import numpy as np
from PIL import Image

build, segb, model = sys.argv[1:4]
tmp = os.path.join(build, "_segtmp"); os.makedirs(tmp, exist_ok=True)
for d in sorted(glob.glob(os.path.join(build, "real", "mi*"))):
    if not os.path.isdir(d):
        continue
    frames = sorted(glob.glob(os.path.join(d, "*.jpg")))
    md = os.path.join(d, "mask"); os.makedirs(md, exist_ok=True)
    if len(glob.glob(os.path.join(md, "*.png"))) == len(frames):
        continue
    raw = {}
    for b in range(0, len(frames), 150):
        batch = frames[b:b + 150]
        with open(os.path.join(tmp, "list.txt"), "w") as L:
            for f in batch:
                x = np.asarray(Image.open(f).convert("RGB").resize((320, 320), Image.BILINEAR), np.float32)
                x /= max(x.max(), 1)
                x = (x - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
                n = os.path.basename(f)
                x.transpose(2, 0, 1).astype(np.float32).tofile(os.path.join(tmp, n + ".in"))
                L.write(f"{os.path.join(tmp, n + '.in')} {os.path.join(tmp, n + '.out')}\n")
        subprocess.run([segb, model, os.path.join(tmp, "list.txt"), "4"], check=True, capture_output=True)
        for f in batch:
            n = os.path.basename(f)
            m = np.fromfile(os.path.join(tmp, n + ".out"), np.float32).reshape(320, 320)
            raw[n] = (m - m.min()) / (m.max() - m.min() + 1e-6)
            os.remove(os.path.join(tmp, n + ".in")); os.remove(os.path.join(tmp, n + ".out"))
    names = [os.path.basename(f) for f in frames]
    for i, n in enumerate(names):   # light temporal smoothing against flicker
        acc = raw[n] * 0.5 + raw[names[max(i - 1, 0)]] * 0.25 + raw[names[min(i + 1, len(names) - 1)]] * 0.25
        Image.fromarray((acc * 255).astype(np.uint8)).save(os.path.join(md, n.replace(".jpg", ".png")))
    print("masks", d, len(names), flush=True)
