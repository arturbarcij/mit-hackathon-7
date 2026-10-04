# Writes tests/engine/fixtures/preprocess_oracle.json: sha256 of the 224x224 RGB uint8 crop that
# torchvision Resize(224) + CenterCrop(224) gives on a PIL image (Pillow BILINEAR with antialias,
# which is what torchvision calls for PIL input), for the demo photos and ml parity samples.
# Pillow-only oracle (no torch needed). Run from app/: python3 scripts/make_preprocess_fixtures.py
import glob, hashlib, json
from PIL import Image

def resized(w, h, size=224):
    short, long = (w, h) if w <= h else (h, w)
    nl = int(size * long / short)
    return (size, nl) if w <= h else (nl, size)

out = {}
for p in sorted(glob.glob('public/demo/*.jpg')) + sorted(glob.glob('ml/parity_samples/*.jpg')):
    im = Image.open(p).convert('RGB')
    nw, nh = resized(*im.size)
    if (nw, nh) != im.size:
        im = im.resize((nw, nh), Image.BILINEAR)
    top, left = int(round((nh - 224) / 2.0)), int(round((nw - 224) / 2.0))
    crop = im.crop((left, top, left + 224, top + 224))
    out[p] = hashlib.sha256(crop.tobytes()).hexdigest()
json.dump({'generated_by': 'app/scripts/make_preprocess_fixtures.py (Pillow %s)' % Image.__version__, 'sha256_rgb224': out},
          open('tests/engine/fixtures/preprocess_oracle.json', 'w'), indent=1)
print(len(out), 'images')
