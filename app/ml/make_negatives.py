"""Synthetic 'not_leaf' backgrounds (paper, table, soil, skin-tone, grey). Seeded, labelled synthetic.

Real hand / paper / soil photos are better. Drop any you have into data_raw/own_negatives/
and manifest.py will pick them up as real (non-synthetic) negatives.
Output: data_raw/synthetic_bg/*.jpg
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data_raw" / "synthetic_bg"
rng = np.random.default_rng(42)
S = 224


def noise(scale, amp):
    n = rng.normal(0, 1, (S // scale + 2, S // scale + 2))
    im = Image.fromarray(((n - n.min()) / (np.ptp(n) + 1e-9) * 255).astype("uint8")).resize((S, S), Image.BICUBIC)
    return (np.asarray(im, dtype=np.float32) / 255 - 0.5) * amp


def grad():
    a = rng.uniform(0, 2 * np.pi)
    y, x = np.mgrid[0:S, 0:S] / S
    return (np.cos(a) * x + np.sin(a) * y - 0.5) * rng.uniform(0.05, 0.3)


def make(kind):
    if kind == "paper":
        base = np.array(rng.uniform([225, 222, 210], [255, 255, 250]))
        img = base[None, None, :] * (1 + grad())[..., None] + noise(2, 12)[..., None] + noise(32, 20)[..., None]
        if rng.random() < 0.4:  # ruled lines of an exercise book
            for yy in range(rng.integers(8, 20), S, rng.integers(14, 24)):
                img[yy : yy + 1, :, :] -= np.array([40, 20, 10])
    elif kind == "wood":
        base = np.array(rng.uniform([90, 60, 30], [170, 120, 80]))
        y = np.arange(S)[:, None] + noise(16, 60)
        stripes = np.sin(y / rng.uniform(2, 6)) * 12
        img = base[None, None, :] + stripes[..., None] + noise(4, 16)[..., None]
    elif kind == "soil":
        base = np.array(rng.uniform([60, 40, 25], [120, 85, 55]))
        img = base[None, None, :] + noise(2, 50)[..., None] + noise(12, 40)[..., None]
    elif kind == "skin":
        base = np.array(rng.uniform([90, 55, 35], [235, 190, 160]))
        img = base[None, None, :] * (1 + grad())[..., None] + noise(24, 25)[..., None] + noise(2, 6)[..., None]
    else:  # grey / sky / cloth
        base = rng.uniform(80, 220, 3) * np.array([1, 1, rng.uniform(0.9, 1.2)])
        img = base[None, None, :] + grad()[..., None] * 100 + noise(16, 30)[..., None]
    im = Image.fromarray(np.clip(img, 0, 255).astype("uint8"))
    if rng.random() < 0.4:
        im = im.filter(ImageFilter.GaussianBlur(rng.uniform(0.5, 3)))
    return im


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    kinds = ["paper", "wood", "soil", "skin", "grey"]
    n = 0
    for k in kinds:
        for i in range(160):
            make(k).save(OUT / f"{k}_{i:03d}.jpg", quality=int(rng.integers(55, 92)))
            n += 1
    print(f"wrote {n} synthetic backgrounds to {OUT}")


if __name__ == "__main__":
    main()
