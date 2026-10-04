"""Copy finished assets from app/ (producers: ml, geo, content-voice, docs) into web/ (the Lovable repo).

One-way. Run from MIT_Hackathon_7/:  python app/backend/scripts/sync_to_web.py [--dry-run]
Owner: engine agent. Never edits anything outside the listed paths in web/.
"""
import argparse, filecmp, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
APP, WEB = ROOT / "app", ROOT / "web"
PATHS = [  # (source in app/, destination in web/)
    ("public/model", "public/model"),   # ml
    ("public/audio", "public/audio"),   # content-voice
    ("public/geo", "public/geo"),       # geo
    ("src/content", "src/content"),     # content-voice + docs (sources.json)
    ("src/engine", "src/engine"),       # engine (if developed in app/ first)
]

def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--dry-run", action="store_true"); a = ap.parse_args()
    if not (WEB / "package.json").exists():
        print("web/ is not a Lovable clone yet (no package.json). Clone it first."); return 1
    changed = 0
    for src_rel, dst_rel in PATHS:
        src, dst = APP / src_rel, WEB / dst_rel
        if not src.exists():
            print(f"skip  {src_rel} (not produced yet)"); continue
        for f in src.rglob("*"):
            if f.is_dir() or f.name.startswith("."): continue
            t = dst / f.relative_to(src)
            if t.exists() and filecmp.cmp(f, t, shallow=False): continue
            print(("would copy " if a.dry_run else "copy  ") + str(t.relative_to(ROOT)))
            if not a.dry_run:
                t.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(f, t)
            changed += 1
    print(f"{changed} file(s) {'to copy' if a.dry_run else 'copied'}.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
