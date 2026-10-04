# Python reference for tests/engine/demo.e2e.test.ts: torchvision-equivalent eval transform
# (Pillow BILINEAR Resize(224), CenterCrop(224), Normalize) + Python onnxruntime on the shipped
# public/model/leaf.onnx, softmax(logits / T). Writes tests/engine/fixtures/demo_python_ort.json.
# Run from app/: python3 scripts/make_demo_python_ort.py  (needs pillow, numpy, onnxruntime)
import glob, json
import numpy as np
import onnxruntime as ort
from PIL import Image

spec = json.load(open('public/model/model.json'))
sess = ort.InferenceSession('public/model/leaf.onnx', providers=['CPUExecutionProvider'])
mean = np.array(spec['input']['mean'], np.float32)
std = np.array(spec['input']['std'], np.float32)

def prep(p):
    im = Image.open(p).convert('RGB')
    w, h = im.size
    short, long_ = (w, h) if w <= h else (h, w)
    nl = int(224 * long_ / short)
    nw, nh = (224, nl) if w <= h else (nl, 224)
    if (nw, nh) != im.size:
        im = im.resize((nw, nh), Image.BILINEAR)
    t, l = int(round((nh - 224) / 2.0)), int(round((nw - 224) / 2.0))
    a = np.asarray(im.crop((l, t, l + 224, t + 224))).astype(np.float32) / 255.0
    return ((a - mean) / std).transpose(2, 0, 1)[None].astype(np.float32)

rows = {}
for p in sorted(glob.glob('public/demo/*.jpg')):
    z = sess.run(None, {sess.get_inputs()[0].name: prep(p)})[0][0].astype(np.float64) / spec['temperature']
    e = np.exp(z - z.max())
    pr = e / e.sum()
    rows[p.split('/')[-1]] = {l: round(float(pr[i]), 5) for i, l in enumerate(spec['labels'])}
json.dump({'generated_by': 'app/scripts/make_demo_python_ort.py', 'onnxruntime': ort.__version__,
           'model_version': spec['version'], 'temperature': spec['temperature'], 'probs': rows},
          open('tests/engine/fixtures/demo_python_ort.json', 'w'), indent=1)
print(len(rows), 'images')
