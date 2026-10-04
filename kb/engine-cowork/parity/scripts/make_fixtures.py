"""Generate parity fixtures: PNG + JPEG(q90) images and the expected eval_transform tensor.

Usage: python make_fixtures.py <out_dir>
Writes <name>.png, <name>.jpg, <name>.png.bin, <name>.jpg.bin (raw float32 NCHW 1x3x224x224),
<name>.png.rgb (224*224*3 uint8 after Resize+CenterCrop, before ToTensor) and fixtures.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import PIL
import torch
import torchvision
from PIL import Image, ImageDraw
from torchvision import transforms

INPUT_SIZE = 224
MEAN = (0.485, 0.456, 0.406)
STD = (0.229, 0.224, 0.225)


def eval_transform():
    # identical to app/ml/train.py
    return transforms.Compose([
        transforms.Resize(INPUT_SIZE),
        transforms.CenterCrop(INPUT_SIZE),
        transforms.ToTensor(),
        transforms.Normalize(MEAN, STD),
    ])


def crop_only():
    return transforms.Compose([transforms.Resize(INPUT_SIZE), transforms.CenterCrop(INPUT_SIZE)])


SIZES = [
    (640, 480), (480, 640), (1000, 750), (3000, 4000), (300, 300), (224, 224),
    (1920, 1080), (1013, 777), (777, 1013), (225, 224), (4032, 3024), (150, 400),
]


def gradient(w, h, rng):
    x = np.linspace(0, 1, w, dtype=np.float32)[None, :]
    y = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    r = (x * 255)
    g = (y * 255)
    b = ((x + y) / 2 * 255)
    arr = np.stack([np.broadcast_to(r, (h, w)), np.broadcast_to(g, (h, w)), np.broadcast_to(b, (h, w))], -1)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


def noise(w, h, rng):
    return Image.fromarray(rng.integers(0, 256, (h, w, 3), dtype=np.uint8), "RGB")


def checker(w, h, rng):
    cell = max(1, min(w, h) // 37)  # odd cell count, sharp edges
    yy, xx = np.mgrid[0:h, 0:w]
    m = ((xx // cell + yy // cell) % 2).astype(np.uint8)
    arr = np.stack([m * 255, m * 255, m * 255], -1)
    # a second finer checker in red to stress the filter
    cell2 = max(1, cell // 3)
    m2 = ((xx // cell2 + yy // cell2) % 2).astype(np.uint8)
    arr[..., 0] = np.where(m2 == 1, 255, arr[..., 0])
    return Image.fromarray(arr.astype(np.uint8), "RGB")


def leaf(w, h, rng):
    im = Image.new("RGB", (w, h), (243, 238, 226))  # off-white paper
    d = ImageDraw.Draw(im)
    # paper texture
    tex = rng.integers(-6, 7, (h, w, 1), dtype=np.int16)
    base = np.array(im, dtype=np.int16) + tex
    im = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8), "RGB")
    d = ImageDraw.Draw(im)
    cx, cy = w / 2, h / 2
    rx, ry = w * 0.32, h * 0.42
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=(58, 112, 41), outline=(34, 70, 25), width=max(2, w // 300))
    # midrib
    d.line([cx, cy - ry, cx, cy + ry], fill=(120, 160, 90), width=max(1, w // 200))
    # orange rust spots
    for _ in range(14):
        sx = cx + rng.uniform(-rx * 0.8, rx * 0.8)
        sy = cy + rng.uniform(-ry * 0.8, ry * 0.8)
        r = max(2, min(w, h) * rng.uniform(0.008, 0.03))
        d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(222, 140, 30))
    return im


GENS = {"gradient": gradient, "noise": noise, "checker": checker, "leaf": leaf}


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(42)
    tfm = eval_transform()
    crop = crop_only()
    meta = []
    i = 0
    kinds = list(GENS)
    for w, h in SIZES:
        # two content kinds per size => 24 fixtures
        for kind in (kinds[i % 4], kinds[(i + 1) % 4]):
            name = f"{i:02d}_{kind}_{w}x{h}"
            im = GENS[kind](w, h, rng)
            png = out / f"{name}.png"
            jpg = out / f"{name}.jpg"
            im.save(png, optimize=False)
            im.save(jpg, quality=90)
            for p in (png, jpg):
                with Image.open(p) as im2:
                    im2 = im2.convert("RGB")
                    x = tfm(im2).unsqueeze(0).numpy().astype(np.float32)
                    c = np.array(crop(im2), dtype=np.uint8)
                x.tofile(str(p) + ".bin")
                c.tofile(str(p) + ".rgb")
            meta.append({"name": name, "kind": kind, "width": w, "height": h,
                         "png": png.name, "jpg": jpg.name, "png_bytes": png.stat().st_size, "jpg_bytes": jpg.stat().st_size})
            i += 1
    (out / "fixtures.json").write_text(json.dumps({
        "pillow": PIL.__version__, "torch": torch.__version__, "torchvision": torchvision.__version__,
        "size": INPUT_SIZE, "mean": MEAN, "std": STD, "fixtures": meta}, indent=2))
    print(f"wrote {len(meta)} fixtures to {out}")


if __name__ == "__main__":
    main()
