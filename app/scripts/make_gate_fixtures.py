# Writes the synthetic sheet-gate images and python_gate.json (Python reference results) for tests/engine/gate.test.ts.
# Run from app/: python3 scripts/make_gate_fixtures.py  (needs pillow, numpy)
import json, sys, os, glob
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'kb', 'edge'))
from sheet_gate import gate
out = 'tests/engine/fixtures/gate'
rng = np.random.default_rng(7)
def page(w=400, h=300, col=(236, 234, 228)):
    a = np.full((h, w, 3), col, np.float32) + rng.normal(0, 4, (h, w, 3))
    return a
def save(name, a):
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(f'{out}/{name}.png')
def leaf_on(a, cx, cy, rx, ry, col=(52, 110, 40)):
    h, w, _ = a.shape
    yy, xx = np.mgrid[0:h, 0:w]
    m = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1
    a[m] = np.array(col, np.float32) + rng.normal(0, 8, (m.sum(), 3))
    return a
save('syn_leaf_on_page', leaf_on(page(), 200, 150, 95, 58))
save('syn_rust_leaf_on_page', leaf_on(leaf_on(page(), 200, 150, 100, 62), 225, 140, 20, 13, (170, 110, 30)))
save('syn_leaf_on_page_portrait', leaf_on(page(300, 400), 150, 200, 48, 75))
save('syn_plain_page', page())
save('syn_lined_page', (lambda a: (a.__setitem__((slice(None, None, 15), slice(None)), (150, 170, 210)) or a))(page()))
save('syn_skin_hand', leaf_on(page(col=(205, 150, 120)), 200, 150, 95, 58))
save('syn_skin_only', page(col=(198, 140, 110)))
save('syn_noise', rng.uniform(0, 255, (300, 400, 3)))
save('syn_clutter_blocks', np.kron(rng.uniform(0, 255, (12, 16, 3)), np.ones((25, 25, 1))))
save('syn_tiny_leaf_on_page', leaf_on(page(), 200, 150, 30, 20))
save('syn_leaf_off_corner', leaf_on(page(), 380, 280, 150, 110))
save('syn_leaf_fills_frame', leaf_on(page(), 200, 150, 260, 200))
save('syn_leaf_off_edge', leaf_on(page(), 390, 150, 120, 80))
save('syn_dark_table', page(col=(70, 50, 35)))
save('syn_leaf_on_soil', leaf_on(page(col=(110, 80, 55)), 200, 150, 95, 58))
imgs = sorted(glob.glob('public/demo/*.jpg')) + sorted(glob.glob('ml/parity_samples/*.jpg')) + sorted(glob.glob(f'{out}/*.png'))
res = {}
for p in imgs:
    g = gate(p); im = Image.open(p)
    res[p] = {**g, 'size': list(im.size)}
    print(p, im.size, g)
json.dump({'generated_by': 'app/scripts/make_gate_fixtures.py with kb/edge/sheet_gate.py', 'results': res}, open(f'{out}/python_gate.json', 'w'), indent=1)
