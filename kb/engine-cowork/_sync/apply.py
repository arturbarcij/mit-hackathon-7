"""Apply a lane's changes tarball onto the laptop tree, refusing files changed by someone else since the baseline.
Usage (from MIT_Hackathon_7/): python3 kb/engine-cowork/_sync/apply.py <changes.tgz> <baseline.json> [--force-new]
Tar members are repo-relative paths. A member is written only if the laptop file is unchanged since the baseline
(sha matches), or is new. Deleting is not supported. Prints a per-file report."""
import hashlib, json, sys, tarfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
tgz, basef = Path(sys.argv[1]), Path(sys.argv[2])
base = json.loads(basef.read_text())
ALLOWED = ("app/src/","app/tests/","app/public/","app/qa/","app/docs/","app/README.md","app/package.json","app/package-lock.json",
           "app/index.html","app/vite.config.ts","app/vitest.config.ts","app/tsconfig","kb/engine-cowork/","kb/judge/","kb/redteam/","kb/runner/","app/scripts/","kb/content/")
ok = refused = 0
with tarfile.open(tgz) as tf:
    for m in tf.getmembers():
        if not m.isfile(): continue
        rel = m.name.lstrip("./")
        if ".." in rel or not rel.startswith(ALLOWED) or rel.startswith("app/backend/"):
            print("REFUSED (path not allowed)", rel); refused += 1; continue
        dest = ROOT/rel
        data = tf.extractfile(m).read()
        if dest.exists():
            cur = hashlib.sha256(dest.read_bytes()).hexdigest()
            if cur == hashlib.sha256(data).hexdigest(): print("same", rel); continue
            if rel in base and cur != base[rel]:
                print("REFUSED (changed on laptop since snapshot)", rel); refused += 1; continue
        dest.parent.mkdir(parents=True, exist_ok=True); dest.write_bytes(data); ok += 1; print("wrote", rel)
print(f"applied {ok}, refused {refused}")
sys.exit(1 if refused else 0)
