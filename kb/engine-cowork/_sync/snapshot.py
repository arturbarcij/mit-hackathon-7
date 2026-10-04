"""Snapshot app/ (code, content, tests, docs, qa) + kb/edge into a tarball with a sha256 baseline. Run from MIT_Hackathon_7/."""
import hashlib, json, sys, tarfile, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
INC = ["app/src","app/tests","app/public","app/qa","app/docs","app/backend/scripts","app/README.md","app/package.json",
       "app/package-lock.json","app/index.html","app/vite.config.ts","app/vitest.config.ts","app/tsconfig.json","app/tsconfig.app.json",
       "app/tsconfig.node.json","app/tsconfig.engine.json","app/.gitignore","app/LICENSE","app/ml/parity_samples","app/ml/metrics.json","app/ml/calibration.json",
       "app/ml/common.py","app/ml/train.py","app/ml/export.py","kb/edge","kb/CONTRACTS.md","kb/MASTER_PROMPT.md","kb/EDGE_PLAN.md",
       "kb/STATUS.md","kb/OWNERSHIP.md","kb/DECISIONS.md","kb/agents","kb/prompts","kb/research/GUIDANCE.md","kb/research/swahili_glossary.md","kb/content"]
SKIP = {"node_modules","__pycache__",".output","dist","out"}
out = ROOT/"kb/engine-cowork/_sync"/sys.argv[1]
base = {}
with tarfile.open(out, "w:gz") as tf:
    for inc in INC:
        p = ROOT/inc
        if not p.exists(): continue
        files = [p] if p.is_file() else [f for f in p.rglob("*") if f.is_file() and not (set(f.relative_to(ROOT).parts) & SKIP)]
        for f in files:
            rel = f.relative_to(ROOT).as_posix()
            if rel.startswith("app/backend/.env"): continue
            base[rel] = hashlib.sha256(f.read_bytes()).hexdigest()
            tf.add(f, arcname=rel)
(ROOT/"kb/engine-cowork/_sync"/(sys.argv[1]+".baseline.json")).write_text(json.dumps(base, indent=0))
print(len(base), "files ->", out, out.stat().st_size, "bytes")
