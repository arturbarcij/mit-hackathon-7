import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

C = str(ROOT / "app/src/content") + "/"
answers = json.load(open(C + "answers.json", encoding="utf-8"))
rules = json.load(open(C + "rules.json", encoding="utf-8"))
season = json.load(open(C + "season.json", encoding="utf-8"))
errors = []

ids = [a["id"] for a in answers]
bank = {a["id"]: a for a in answers}
if len(ids) != len(set(ids)):
    errors.append("duplicate ids")

for r in rules:
    if r["then"] not in bank:
        errors.append("rule target missing: " + r["then"])
if rules[-1]["if"] != {} or rules[-1]["then"] != "ask_officer":
    errors.append("last rule is not the ask_officer catch-all")

_ph = ROOT / "app/src/engine/placeholders/answers.json"
ph = json.load(open(_ph, encoding="utf-8")) if _ph.exists() else json.loads(subprocess.check_output(
    ["git", "-C", str(ROOT), "show", "origin/cursor/engine-offline-core-d90f:app/src/engine/placeholders/answers.json"]))
ph_keys = set()
for p in ph:
    ph_keys |= set(p)
    if p["id"] not in bank:
        errors.append("placeholder id dropped: " + p["id"])
allowed = ph_keys | {"not_sure"}
for a in answers:
    extra = set(a) - allowed
    if extra:
        errors.append(f"{a['id']}: keys not in placeholder shape {extra}")
    for lang in ("en", "sw"):
        if not a["text"].get(lang, "").strip():
            errors.append(f"{a['id']}: missing text.{lang}")
    if a["kind"] in ("result", "out_of_scope"):
        ns = a.get("not_sure", {})
        if not ns.get("en") or not ns.get("sw"):
            errors.append(f"{a['id']}: result card without en+sw not_sure")
    if a["severity"] not in ("ok", "watch", "act", "ask"):
        errors.append(f"{a['id']}: bad severity")
    if a["kind"] in ("result", "out_of_scope") and a["severity"] in ("act", "watch") and not a["sources"] and not a["assumption"]:
        errors.append(f"{a['id']}: advice card with no sources and no assumption")
    if "[placeholder]" in json.dumps(a):
        errors.append(f"{a['id']}: placeholder text left")

valid_src = {"S%d" % i for i in range(1, 10)} | {"SEASON"}
anchors = set(re.findall(r"^## ([a-z-]+):", open(ROOT / "kb/research/GUIDANCE.md").read(), re.M))
for a in answers:
    for s in a["sources"]:
        if s.startswith("GUIDANCE#"):
            if s.split("#", 1)[1] not in anchors:
                errors.append(f"{a['id']}: unknown anchor {s}")
        elif s not in valid_src:
            errors.append(f"{a['id']}: unknown source {s}")

blob = json.dumps(answers, ensure_ascii=False)
dose = re.findall(r"\d+(?:[.,]\d+)?\s*(?:ml|g|kg|l|litres?|grams?|%)\b", blob, re.I)
if dose:
    errors.append(f"dose-like strings: {dose}")
brands = ["Ridomil", "Nordox", "Kocide", "Funguran", "Cuprocaffaro", "Bayleton", "Amistar", "Score", "Cupravit",
          "Champion", "Copper Nordox", "Daconil", "Folicur", "Alto", "Tilt", "Actara", "Karate", "Duduthrin"]
for b in brands:
    if re.search(r"\b" + b + r"\b", blob, re.I):
        errors.append("brand name: " + b)
if "\u2014" in blob or "\u2013" in blob or "\u2014" in json.dumps(rules, ensure_ascii=False):
    errors.append("em or en dash present")
if re.search(r"\d", " ".join(a["text"]["en"] + a["text"]["sw"] for a in answers)):
    errors.append("digit in farmer text: " + str(re.findall(r"[^.]*\d[^.]*", blob)[:3]))

KEYS = {"dominant", "affected_gte", "affected_lte", "uncertain_gte", "uncertain_lte", "distinct_problems_gte", "window"}


def matches(cond, s, w):
    for k, v in cond.items():
        if k not in KEYS:
            return False
        lst = v if isinstance(v, list) else [v]
        if k == "dominant" and s["dominant"] not in lst: return False
        if k == "window" and w not in lst: return False
        if k == "affected_gte" and not s["affected"] >= v: return False
        if k == "affected_lte" and not s["affected"] <= v: return False
        if k == "uncertain_gte" and not s["uncertain"] >= v: return False
        if k == "uncertain_lte" and not s["uncertain"] <= v: return False
        if k == "distinct_problems_gte" and not s["distinctProblems"] >= v: return False
    return True


def pick(s, w):
    for i, r in enumerate(rules):
        if matches(r["if"], s, w):
            return i, r["then"]
    return None, None


for r in rules:
    bad = set(r["if"]) - KEYS
    if bad:
        errors.append(f"unknown condition key {bad}")

WINDOWS = ["pre_short_rains", "short_rains", "pre_long_rains", "long_rains", "dry"]
PROBLEMS = ["rust", "cercospora", "phoma", "miner"]
hit_rules, combos, outcomes = set(), 0, {}
for w in WINDOWS:
    for rust in range(11):
        for unc in range(11 - rust):
            for other in [None] + PROBLEMS[1:] + ["healthy_only", "not_leaf"]:
                rest = 10 - rust - unc
                counts = dict.fromkeys(["healthy", "rust", "cercospora", "phoma", "miner", "not_leaf"], 0)
                counts["rust"] = rust
                if other in PROBLEMS[1:]:
                    counts[other] = min(1, rest); counts["healthy"] = rest - counts[other]
                elif other == "not_leaf":
                    counts["not_leaf"] = rest
                else:
                    counts["healthy"] = rest
                affected = sum(counts[p] for p in PROBLEMS)
                distinct = sum(1 for p in PROBLEMS if counts[p] > 0)
                if counts["not_leaf"] * 2 >= 10: dom = "not_leaf"
                elif affected:
                    dom = max(PROBLEMS, key=lambda p: (counts[p], -PROBLEMS.index(p)))
                elif counts["healthy"]: dom = "healthy"
                else: dom = "none"
                s = {"n": 10, "uncertain": unc, "dominant": dom, "affected": affected, "distinctProblems": distinct}
                i, then = pick(s, w)
                combos += 1
                if then is None:
                    errors.append(f"no rule matched {s} {w}")
                    continue
                hit_rules.add(i)
                outcomes[(w, rust, unc, other)] = then

unreached = [f"#{i+1} {rules[i]['then']}" for i in range(len(rules)) if i not in hit_rules]
for (w, rust, unc, other), want in [
    (("pre_short_rains", 6, 0, None), "rust_high_pre_rains"),
    (("pre_long_rains", 2, 0, None), "rust_high_pre_rains"),
    (("pre_short_rains", 1, 0, None), "rust_low_pre_rains"),
    (("short_rains", 5, 0, None), "rust_high_in_rains"),
    (("dry", 5, 0, None), "rust_high_dry"),
    (("dry", 1, 0, None), "rust_low"),
    (("dry", 0, 0, None), "healthy_all"),
    (("dry", 0, 1, None), "ask_officer"),
    (("dry", 0, 4, None), "too_many_unsure"),
    (("dry", 3, 0, "miner"), "mixed_problems"),
    (("dry", 0, 0, "not_leaf"), "not_a_leaf"),
    (("dry", 0, 0, "phoma"), "phoma"),
]:
    got = outcomes.get((w, rust, unc, other))
    if got != want:
        errors.append(f"spot check {w} rust={rust} unsure={unc} other={other}: got {got}, want {want}")

print(f"cards={len(answers)} rules={len(rules)} grid={combos} unreached_rules={unreached or 'none'}")
print("season.json identical to research:", open(C + "season.json").read() == open(ROOT / "kb/research/season.json").read())
print("kik cards:", [a["id"] for a in answers if "kik" in a["text"]])
print("assumption cards:", [a["id"] for a in answers if a["assumption"]])
if errors:
    print("FAIL"); [print(" -", e) for e in errors]; sys.exit(1)
print("PASS")
