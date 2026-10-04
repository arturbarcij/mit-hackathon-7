"""Image-validity gate for the Jani capture protocol (one leaf flat on a plain page).

Reference implementation for the engine. Port it to TypeScript on a canvas of at most 256 px.
A photo passes only if:
  - at least 30% of pixels look like plain paper (bright, low saturation),
  - the leaf does not run off the frame (at most 15% of the outer 6% band is leaf),
  - the leaf covers at least 8% of the image.
Failing photos get a retake card ("lay the leaf flat on a plain page"), never a diagnosis.
The thresholds were set by the lead on Sat 3 Oct night, looking at the same images that
field_check.py scores. Treat its numbers as in-sample until fresh photos confirm them.
Same idea as the image-validity check in Wadhwani AI's CottonAce.
"""
import numpy as np
from PIL import Image

PAPER_MIN, EDGE_TOUCH_MAX, LEAF_MIN = 0.30, 0.15, 0.08


def gate(path_or_image):
    im = path_or_image if isinstance(path_or_image, Image.Image) else Image.open(path_or_image)
    im = im.convert("RGB")
    im.thumbnail((256, 256))
    a = np.asarray(im).astype(np.float32) / 255.0
    mx, mn = a.max(2), a.min(2)
    sat = (mx - mn) / (mx + 1e-6)
    paper = (mx > 0.45) & (sat < 0.18)
    leaf = (sat > 0.22) & (~paper)
    h, w = leaf.shape
    b = max(2, int(0.06 * min(h, w)))
    border = np.zeros((h, w), dtype=bool)
    border[:b], border[-b:], border[:, :b], border[:, -b:] = True, True, True, True
    paper_frac, touch, leaf_frac = float(paper.mean()), float(leaf[border].mean()), float(leaf.mean())
    ok = paper_frac >= PAPER_MIN and touch <= EDGE_TOUCH_MAX and leaf_frac >= LEAF_MIN
    reason = None
    if not ok:
        reason = "no_page" if paper_frac < PAPER_MIN else ("leaf_cut_off" if touch > EDGE_TOUCH_MAX else "leaf_too_small")
    return {"ok": ok, "reason": reason, "paper": round(paper_frac, 3), "edge_touch": round(touch, 3), "leaf": round(leaf_frac, 3)}


if __name__ == "__main__":
    import sys
    for p in sys.argv[1:]:
        print(p, gate(p))
