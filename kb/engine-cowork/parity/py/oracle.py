"""Oracle for preprocess.ts parity.

For every real image (images/*.jpg) and a set of synthetic images, writes:
  work/<name>.rgba     decoded pixels (PIL convert("RGB"), alpha 255), raw uint8
  work/<name>.resized  PIL output of transforms.Resize(224), raw uint8 RGB
  work/<name>.crop     after CenterCrop(224), raw uint8 RGB
  work/<name>.tensor   full eval_transform output, raw float32 NCHW
  work/<name>.rg2      (large inputs only) Pillow resize with reducing_gap=2.0, then crop
  work/index.json
Uses torchvision when importable, else a PIL + numpy emulation (flagged in index.json).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import PIL
from PIL import Image

HERE = Path(__file__).resolve().parents[1]
import os
IMAGES = Path(os.environ.get("ORACLE_IMAGES", HERE / "images"))
WORK = Path(os.environ.get("ORACLE_WORK", HERE / "work"))
NO_SYNTH = bool(os.environ.get("ORACLE_NO_SYNTH"))
WORK.mkdir(exist_ok=True)

MEAN = (0.485, 0.456, 0.406)
STD = (0.229, 0.224, 0.225)
SIZE = 224

try:
    import torch
    import torchvision
    from torchvision import transforms

    def eval_transform():
        return transforms.Compose([
            transforms.Resize(SIZE),
            transforms.CenterCrop(SIZE),
            transforms.ToTensor(),
            transforms.Normalize(MEAN, STD),
        ])

    resize_t = transforms.Resize(SIZE)
    crop_t = transforms.CenterCrop(SIZE)
    ORACLE = f"torchvision {torchvision.__version__} torch {torch.__version__}"

    def run_resize(im):
        return resize_t(im)

    def run_crop(im):
        return crop_t(im)

    def run_tensor(im):
        return eval_transform()(im).unsqueeze(0).numpy().astype(np.float32)
except Exception as ex:  # emulation until torch is installed
    ORACLE = f"emulation (torchvision unavailable: {ex!r})"

    def _size(w, h):
        short, long = (w, h) if w <= h else (h, w)
        nl = int(SIZE * long / short)
        return (SIZE, nl) if w <= h else (nl, SIZE)

    def run_resize(im):
        nw, nh = _size(*im.size)
        if (nw, nh) == im.size:
            return im
        return im.resize((nw, nh), Image.BILINEAR)

    def run_crop(im):
        w, h = im.size
        top = int(round((h - SIZE) / 2.0))
        left = int(round((w - SIZE) / 2.0))
        return im.crop((left, top, left + SIZE, top + SIZE))

    def run_tensor(im):
        a = np.asarray(run_crop(run_resize(im)), dtype=np.uint8).astype(np.float32)
        x = a / np.float32(255)
        m = np.array(MEAN, dtype=np.float32)
        s = np.array(STD, dtype=np.float32)
        x = (x - m) / s
        return x.transpose(2, 0, 1)[None].astype(np.float32)


def synth(name: str, w: int, h: int, kind: str, seed: int) -> Image.Image:
    rng = np.random.default_rng(seed)
    if kind == "noise":
        a = rng.integers(0, 256, size=(h, w, 3), dtype=np.uint8)
    elif kind == "grad":
        yy, xx = np.mgrid[0:h, 0:w]
        a = np.stack([
            (xx * 255 // max(w - 1, 1)),
            (yy * 255 // max(h - 1, 1)),
            ((xx + yy) * 255 // max(w + h - 2, 1)),
        ], axis=-1).astype(np.uint8)
    elif kind == "edges":  # hard edges and extremes, worst case for clipping
        a = np.zeros((h, w, 3), dtype=np.uint8)
        a[::2, :, 0] = 255
        a[:, ::3, 1] = 255
        a[(np.arange(h)[:, None] + np.arange(w)[None, :]) % 7 == 0, 2] = 255
    else:
        raise ValueError(kind)
    return Image.fromarray(a, "RGB")


SYNTH = [
    ("s_224x224_noise", 224, 224, "noise"),
    ("s_225x224_noise", 225, 224, "noise"),   # no resize, crop offset round(0.5) = 0
    ("s_227x224_noise", 227, 224, "noise"),   # round(1.5) = 2
    ("s_229x224_noise", 229, 224, "noise"),   # round(2.5) = 2 (half to even)
    ("s_224x231_noise", 224, 231, "noise"),   # round(3.5) = 4
    ("s_225x225_noise", 225, 225, "noise"),
    ("s_3x5_noise", 3, 5, "noise"),           # tiny upscale
    ("s_1x1_noise", 1, 1, "noise"),
    ("s_100x150_grad", 100, 150, "grad"),     # upscale
    ("s_223x500_noise", 223, 500, "noise"),
    ("s_300x200_edges", 300, 200, "edges"),
    ("s_449x449_noise", 449, 449, "noise"),
    ("s_1001x777_noise", 1001, 777, "noise"),
    ("s_13x997_noise", 13, 997, "noise"),
    ("s_4000x50_noise", 4000, 50, "noise"),   # extreme aspect
    ("s_50x4000_grad", 50, 4000, "grad"),
    ("s_641x479_edges", 641, 479, "edges"),
    ("s_4000x3000_noise", 4000, 3000, "noise"),
    ("s_3024x4032_grad", 3024, 4032, "grad"),
]


def write(name: str, im: Image.Image, source: str, idx: list):
    rgb = im.convert("RGB")
    a = np.asarray(rgb, dtype=np.uint8)
    h, w = a.shape[:2]
    rgba = np.concatenate([a, np.full((h, w, 1), 255, np.uint8)], axis=-1)
    (WORK / f"{name}.rgba").write_bytes(rgba.tobytes())
    r = run_resize(rgb)
    (WORK / f"{name}.resized").write_bytes(np.asarray(r, dtype=np.uint8).tobytes())
    c = run_crop(r)
    (WORK / f"{name}.crop").write_bytes(np.asarray(c, dtype=np.uint8).tobytes())
    t = run_tensor(rgb)
    assert t.shape == (1, 3, SIZE, SIZE), t.shape
    (WORK / f"{name}.tensor").write_bytes(t.tobytes())
    entry = {"name": name, "w": w, "h": h, "rw": r.size[0], "rh": r.size[1], "source": source}
    if min(w, h) >= 4 * SIZE:
        rg = rgb.resize(r.size, Image.BILINEAR, reducing_gap=2.0)
        (WORK / f"{name}.rg2").write_bytes(np.asarray(run_crop(rg), dtype=np.uint8).tobytes())
        entry["rg2"] = True
    idx.append(entry)


def main():
    idx: list = []
    for p in sorted(IMAGES.glob("*.jpg")):
        with Image.open(p) as im:
            write(p.stem, im, f"real:{p.name}", idx)
    for i, (name, w, h, kind) in enumerate([] if NO_SYNTH else SYNTH):
        write(name, synth(name, w, h, kind, 1000 + i), f"synthetic:{kind}", idx)
    meta = {"oracle": ORACLE, "pillow": PIL.__version__, "numpy": np.__version__, "items": idx}
    (WORK / "index.json").write_text(json.dumps(meta, indent=1))
    print(ORACLE, "pillow", PIL.__version__, "items", len(idx))


if __name__ == "__main__":
    sys.exit(main())
