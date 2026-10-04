"""Synthetic images for v2 training: exercise-book pages, coffee leaves composited onto them, and
non-leaf clutter. Every image made here is synthetic and is labelled as such in the manifests.

The pages mirror the capture protocol (MASTER_PROMPT 3.2): a leaf photographed on a plain sheet in daylight.
"""
import math
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

CANVAS = 256


def paper(rng: random.Random, size: int = CANVAS) -> Image.Image:
    """Off-white to grey paper, optional faint blue ruled lines and red margin, lighting gradient, noise."""
    base = rng.uniform(150, 245)
    tint = np.array([rng.uniform(-6, 8), rng.uniform(-4, 6), rng.uniform(-12, 4)])
    img = np.ones((size, size, 3)) * (base + tint)
    if rng.random() < 0.6:
        gap = rng.uniform(14, 26)
        off = rng.uniform(0, gap)
        line = np.array([rng.uniform(110, 170), rng.uniform(150, 200), rng.uniform(200, 240)])
        a = rng.uniform(0.15, 0.45)
        y = off
        while y < size:
            r = int(y)
            img[r:r + 1] = img[r:r + 1] * (1 - a) + line * a
            y += gap
        if rng.random() < 0.5:
            x = int(rng.uniform(0.08, 0.25) * size)
            img[:, x:x + 2] = img[:, x:x + 2] * 0.55 + np.array([210, 70, 80]) * 0.45
    if rng.random() < 0.5:
        img = np.rot90(img, rng.choice([1, 3])).copy()
    yy, xx = np.mgrid[0:size, 0:size] / size
    ang = rng.uniform(0, 2 * math.pi)
    grad = (np.cos(ang) * (xx - 0.5) + np.sin(ang) * (yy - 0.5))
    img *= (1 + rng.uniform(0.1, 0.45) * grad)[..., None]
    if rng.random() < 0.5:  # vignette or uneven daylight
        r2 = (xx - rng.uniform(0.2, 0.8)) ** 2 + (yy - rng.uniform(0.2, 0.8)) ** 2
        img *= (1 - rng.uniform(0.1, 0.35) * r2)[..., None]
    img += np.random.default_rng(rng.randrange(1 << 30)).normal(0, rng.uniform(1, 5), img.shape)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))


def leaf_mask(w: int, h: int, rng: random.Random) -> Image.Image:
    """A coffee-leaf-like outline (elliptic, pointed tip, slightly asymmetric) filling a w x h box."""
    pts_top, pts_bot = [], []
    tip, base = rng.uniform(1.2, 2.2), rng.uniform(0.7, 1.2)
    skew = rng.uniform(-0.08, 0.08)
    for k in range(41):
        t = k / 40
        hw = (math.sin(math.pi * t) ** (tip if t > 0.5 else base)) * 0.5
        cx = t * w
        pts_top.append((cx, h * (0.5 + skew * math.sin(math.pi * t) - hw)))
        pts_bot.append((cx, h * (0.5 + skew * math.sin(math.pi * t) + hw * rng.uniform(0.92, 1.0))))
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).polygon(pts_top + pts_bot[::-1], fill=255)
    return m.filter(ImageFilter.GaussianBlur(0.8))


def saturation_mask(img: Image.Image) -> Image.Image:
    """Leaf mask for photos of a leaf on a pale background (BRACOL): coloured pixels are leaf."""
    hsv = np.asarray(img.convert("HSV"), dtype=np.float32)
    m = (hsv[..., 1] > 60) & (hsv[..., 2] > 25)
    return Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MedianFilter(5)).filter(ImageFilter.GaussianBlur(1))


def paste(bg: Image.Image, fg: Image.Image, mask: Image.Image, rng: random.Random, shadow: bool = True) -> Image.Image:
    size = bg.size[0]
    angle = rng.uniform(-180, 180)
    fg = fg.convert("RGBA")
    fg.putalpha(mask)
    fg = fg.rotate(angle, resample=Image.BICUBIC, expand=True)
    x = rng.randint(min(0, size - fg.width), max(0, size - fg.width))
    y = rng.randint(min(0, size - fg.height), max(0, size - fg.height))
    out = bg.convert("RGB")
    if shadow:
        k = rng.uniform(0.25, 0.5)
        a = fg.getchannel("A").filter(ImageFilter.GaussianBlur(rng.uniform(3, 9))).point(lambda v: int(v * k))
        out.paste(Image.new("RGB", fg.size, (20, 20, 25)), (x + rng.randint(2, 10), y + rng.randint(2, 10)), a)
    out.paste(fg.convert("RGB"), (x, y), fg.getchannel("A"))
    return out


def composite_leaf(img: Image.Image, source: str, rng: random.Random, background: Image.Image | None = None) -> Image.Image:
    """Coffee image -> leaf on a page (or on the given background), leaf length 35 to 90% of the frame."""
    bg = background if background is not None else paper(rng)
    size = bg.size[0]
    length = int(size * rng.uniform(0.35, 0.9))
    if source == "bracol":
        m = saturation_mask(img)
        box = m.getbbox() or (0, 0, img.width, img.height)
        img, m = img.crop(box), m.crop(box)
        s = length / max(img.size)
        nw, nh = max(8, int(img.width * s)), max(8, int(img.height * s))
        return paste(bg, img.resize((nw, nh), Image.BICUBIC), m.resize((nw, nh), Image.BILINEAR), rng)
    width = int(length * rng.uniform(0.38, 0.6))
    return paste(bg, img.resize((length, width), Image.BICUBIC), leaf_mask(length, width, rng), rng)


def clutter(img: Image.Image, rng: random.Random) -> Image.Image:
    """Non-leaf things that end up in a photo of a page: pen strokes, coloured rectangles, a skin-tone blob."""
    d = ImageDraw.Draw(img, "RGBA")
    size = img.size[0]
    for _ in range(rng.randint(0, 4)):
        pts = [(rng.uniform(0, size), rng.uniform(0, size)) for _ in range(rng.randint(2, 6))]
        col = rng.choice([(20, 30, 120), (15, 15, 15), (160, 20, 30), (30, 90, 40)])
        d.line(pts, fill=col + (rng.randint(120, 230),), width=rng.randint(1, 4), joint="curve")
    for _ in range(rng.randint(0, 3)):
        x, y = rng.uniform(-0.2, 0.9) * size, rng.uniform(-0.2, 0.9) * size
        w, h = rng.uniform(0.1, 0.5) * size, rng.uniform(0.1, 0.5) * size
        col = tuple(rng.randint(0, 255) for _ in range(3))
        d.rectangle([x, y, x + w, y + h], fill=col + (rng.randint(150, 255),))
    if rng.random() < 0.45:
        x, y = rng.uniform(-0.3, 0.8) * size, rng.uniform(-0.3, 0.8) * size
        w, h = rng.uniform(0.25, 0.7) * size, rng.uniform(0.2, 0.5) * size
        skin = rng.choice([(95, 60, 45), (140, 95, 70), (190, 140, 110), (225, 185, 160)])
        blob = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(blob).ellipse([x, y, x + w, y + h], fill=skin + (255,))
        blob = blob.filter(ImageFilter.GaussianBlur(rng.uniform(1, 4)))
        img = Image.alpha_composite(img.convert("RGBA"), blob).convert("RGB")
    return img


def blank_page(rng: random.Random, with_clutter: bool | None = None) -> Image.Image:
    img = paper(rng)
    if with_clutter if with_clutter is not None else rng.random() < 0.7:
        img = clutter(img, rng)
    return img


def random_crop(img: Image.Image, rng: random.Random, min_frac: float = 0.2, max_frac: float = 0.7, out: int = CANVAS) -> Image.Image:
    """Square crop covering min_frac to max_frac of the shorter side, resized to out x out."""
    s = int(min(img.size) * rng.uniform(min_frac, max_frac))
    x, y = rng.randint(0, img.width - s), rng.randint(0, img.height - s)
    return img.crop((x, y, x + s, y + s)).resize((out, out), Image.BICUBIC)
