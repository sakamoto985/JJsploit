"""Remove photo backgrounds with U^2-Net (human segmentation) via a tiny onnxruntime C runner."""
import sys, subprocess, numpy as np, os
from PIL import Image, ImageFilter
seg, model, src, dst = sys.argv[1:5]
xmin = int(sys.argv[5]) if len(sys.argv) > 5 else 0
im = Image.open(src).convert("RGB")
x = np.asarray(im.resize((320, 320), Image.LANCZOS), np.float32)
x = x / x.max()
x = (x - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
x.transpose(2, 0, 1).astype(np.float32).tofile(dst + ".in")
subprocess.run([seg, model, dst + ".in", dst + ".out"], check=True)
m = np.fromfile(dst + ".out", np.float32).reshape(320, 320)
m = (m - m.min()) / (m.max() - m.min())
mask = Image.fromarray((m * 255).astype(np.uint8)).resize(im.size, Image.BICUBIC)
a = np.asarray(mask, np.float32) / 255
a = np.clip((a - 0.35) / 0.4, 0, 1)            # tighten the matte
a[:, :xmin] = 0
mask = Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2))
out = im.convert("RGBA"); out.putalpha(mask)
out = out.crop(out.getbbox())
out.save(dst)
os.remove(dst + ".in"); os.remove(dst + ".out")
print(dst, out.size)
