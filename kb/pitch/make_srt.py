#!/usr/bin/env python3
"""Check word budgets and build draft SRTs from the SAY lines in kb/pitch/VIDEO*.md.

Usage: python3 kb/pitch/make_srt.py [--check]
Beat header format:  ### M:SS-M:SS Title (N s)
Speech format:       - SAY [Speaker]: "text"
Placeholders like [PENDING: ml] count as two spoken words (a number).
Captions are drafts: re-time against the real takes in the editor.
"""
import re, sys, pathlib

HERE = pathlib.Path(__file__).parent
MAX_RATE = 2.5          # words per second, hard limit from the brief
CAP_WORDS = 7           # words per caption chunk
VIDEOS = {"video1": "VIDEO1_team.md", "video2": "VIDEO2_demo.md", "video3": "VIDEO3_tech.md"}
hdr = re.compile(r"^### (\d+):(\d\d)-(\d+):(\d\d)\s")
say = re.compile(r'^- SAY \[([^\]]*)\]:\s*"(.*)"\s*$')

def words(t):
    n = 0
    for tok in re.sub(r"\[PENDING[^\]]*\]", " PENDINGNUM ", t).split():
        n += 2 if tok == "PENDINGNUM" else 1
    return n

def ts(s):
    ms = int(round(s * 1000))
    return "%02d:%02d:%02d,%03d" % (ms // 3600000, ms // 60000 % 60, ms // 1000 % 60, ms % 1000)

def chunks(t):
    toks = t.split(); out = []; cur = []
    for w in toks:
        cur.append(w)
        if len(cur) >= CAP_WORDS or re.search(r"[.?!:]$", w) and len(cur) >= 3:
            out.append(" ".join(cur)); cur = []
    if cur: out.append(" ".join(cur))
    return out

ok = True
for key, fn in VIDEOS.items():
    beats = []; cur = None
    for line in (HERE / fn).read_text().splitlines():
        m = hdr.match(line)
        if m:
            a, b, c, d = map(int, m.groups())
            cur = {"s": a * 60 + b, "e": c * 60 + d, "say": []}; beats.append(cur); continue
        m = say.match(line)
        if m and cur is not None:
            cur["say"].append(m.group(2))
    total_w = 0; srt = []; n = 1; end = 0
    for b in beats:
        dur = b["e"] - b["s"]; end = max(end, b["e"])
        txt = " ".join(b["say"]); w = words(txt); total_w += w
        rate = w / dur if dur else 0
        flag = "OVER" if rate > MAX_RATE else "ok"
        if flag == "OVER": ok = False
        print("%s %d:%02d-%d:%02d %2d words %2d s %.2f w/s %s" % (key, b["s"] // 60, b["s"] % 60, b["e"] // 60, b["e"] % 60, w, dur, rate, flag))
        if not txt: continue
        cs = chunks(txt); cw = [words(c) for c in cs]; t = b["s"] + 0.2; avail = dur - 0.4
        for c, k in zip(cs, cw):
            d = avail * k / sum(cw)
            srt.append("%d\n%s --> %s\n%s\n" % (n, ts(t), ts(t + d), c)); n += 1; t += d
    if end > 55: ok = False
    print("%s total %d words, ends %d s%s\n" % (key, total_w, end, "" if end <= 55 else "  OVER 55 s"))
    if "--check" not in sys.argv:
        (HERE / "CAPTIONS").mkdir(exist_ok=True)
        (HERE / "CAPTIONS" / (key + ".srt")).write_text("\n".join(srt))
sys.exit(0 if ok else 1)
