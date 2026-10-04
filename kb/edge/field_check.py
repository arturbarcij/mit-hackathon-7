"""Field check for Jani: how a model behaves on protocol-like and field photos, before and
after the sheet gate, per image and per simulated 10-leaf plot (rules.json, first match wins).

Run:  python kb/edge/field_check.py [--model app/public/model] [--per-class 150] [--out kb/edge/out]
Needs numpy, pillow, onnxruntime. Paths are relative to the MIT_Hackathon_7 folder.
Sets:
  bracol_val, bracol_test  whole leaf on a plain background (protocol proxy). BRACOL was in
                           training; these rows were not (pHash-grouped split in manifest.csv).
  uganda                   random sample per class from data_raw/uganda (never trained on).
  wild_inat                iNaturalist Hemileia vastatrix, research grade (never trained on).
"""
import argparse, collections, csv, json, os, random, sys
from pathlib import Path

import numpy as np
import onnxruntime as ort
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from sheet_gate import gate  # noqa: E402

DIS = ["rust", "cercospora", "phoma", "miner"]


def load_model(model_dir):
    mj = json.loads((model_dir / "model.json").read_text(encoding="utf-8"))
    sess = ort.InferenceSession(str(model_dir / "leaf.onnx"), providers=["CPUExecutionProvider"])
    inp = sess.get_inputs()[0]
    dtype = np.float16 if "float16" in inp.type else np.float32
    mean = np.array(mj["input"]["mean"], dtype=np.float32).reshape(3, 1, 1)
    std = np.array(mj["input"]["std"], dtype=np.float32).reshape(3, 1, 1)

    def predict(path):
        im = Image.open(path).convert("RGB")
        w, h = im.size
        s = 224 / min(w, h)
        im = im.resize((max(224, round(w * s)), max(224, round(h * s))), Image.BILINEAR)
        w, h = im.size
        l, t = (w - 224) // 2, (h - 224) // 2
        im = im.crop((l, t, l + 224, t + 224))
        x = ((np.asarray(im, dtype=np.float32).transpose(2, 0, 1) / 255.0) - mean) / std
        z = sess.run(None, {inp.name: x[None].astype(dtype)})[0][0].astype(np.float64) / mj["temperature"]
        p = np.exp(z - z.max())
        p /= p.sum()
        k = int(p.argmax())
        return mj["labels"][k], float(p[k]), bool(p[k] < mj["threshold"])

    return mj, predict


def build_sets(per_class, seed=7):
    rows = []
    for r in csv.DictReader(open(ROOT / "app/ml/manifest.csv", encoding="utf-8")):
        if r["source"] == "bracol" and r["split"] in ("val", "test"):
            rows.append((ROOT / r["path"], f"bracol_{r['split']}", r["label"]))
    rng = random.Random(seed)
    ug = ROOT / "data_raw/uganda"
    if ug.exists():
        files = sorted(os.listdir(ug))
        for prefix, lab in (("1", "healthy"), ("1200", "rust"), ("2300", "phoma")):
            sel = [f for f in files if f.split("_")[0] == prefix]
            rng.shuffle(sel)
            rows += [(ug / f, "uganda", lab) for f in sel[:per_class]]
    ws = ROOT / "kb/research/wild_set.csv"
    if ws.exists():
        for r in csv.DictReader(open(ws, encoding="utf-8")):
            if "Hemileia" in (r.get("taxon") or "") and (ROOT / r["local_file"]).exists():
                rows.append((ROOT / r["local_file"], "wild_inat", "rust"))
    return rows


def plot_sim(pools, rules, sev, trials=4000, seed=1):
    def summarise(leaves):
        c = collections.Counter(leaves)
        n = len(leaves)
        affected = sum(c[d] for d in DIS)
        s = dict(affected=affected, uncertain=c["unsure"] + c["not_leaf"],
                 distinct=sum(1 for d in DIS if c[d] > 0), window="pre_short_rains")
        if c["not_leaf"] > n / 2:
            s["dominant"] = "not_leaf"
        elif affected:
            s["dominant"] = max(DIS, key=lambda d: (c[d], -DIS.index(d)))
        else:
            s["dominant"] = "healthy" if c["healthy"] else "none"
        return s

    def matches(cond, s):
        for k, v in cond.items():
            if (k == "dominant" and s["dominant"] != v) or (k == "affected_gte" and s["affected"] < v) \
               or (k == "affected_lte" and s["affected"] > v) or (k == "uncertain_gte" and s["uncertain"] < v) \
               or (k == "distinct_problems_gte" and s["distinct"] < v) or (k == "window" and s["window"] != v):
                return False
        return True

    def decide(s):
        return next((r["then"] for r in rules if matches(r.get("if", {}), s)), "ask_officer")

    rng = random.Random(seed)
    scen = {"healthy_plot_10h": {"healthy": 10}, "rust_plot_6r4h": {"rust": 6, "healthy": 4}, "rust_plot_10r": {"rust": 10}}
    out = {}
    for dom, pool in pools.items():
        for name, mix in scen.items():
            if any(not pool.get(c) for c in mix):
                continue
            for gated in (False, True):
                cards = collections.Counter()
                for _ in range(trials):
                    leaves = [rng.choice(pool[c])[1 if gated else 0] for c, k in mix.items() for _ in range(k)]
                    cards[decide(summarise(leaves))] += 1
                out[f"{dom}|{name}|gate={'on' if gated else 'off'}"] = {
                    "spray_advice": sum(v for k, v in cards.items() if sev.get(k) == "act") / trials,
                    "all_clear": cards["healthy_all"] / trials,
                    "ask_officer": sum(v for k, v in cards.items() if sev.get(k) == "ask") / trials,
                    "top_cards": dict(cards.most_common(3)),
                }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=str(ROOT / "app/public/model"))
    ap.add_argument("--per-class", type=int, default=150)
    ap.add_argument("--out", default=str(HERE / "out"))
    ap.add_argument("--limit", type=int, default=0, help="max images per set (smoke test only)")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    mj, predict = load_model(Path(a.model))
    rules = json.loads((ROOT / "app/src/content/rules.json").read_text(encoding="utf-8"))
    answers = json.loads((ROOT / "app/src/content/answers.json").read_text(encoding="utf-8"))
    answers = answers if isinstance(answers, list) else list(answers.values())
    sev = {x["id"]: x.get("severity") for x in answers if "id" in x}
    agg = collections.defaultdict(collections.Counter)
    pools = collections.defaultdict(lambda: collections.defaultdict(list))
    with open(out / "per_image.csv", "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["path", "set", "true", "pred", "conf", "abstained", "gate_ok", "gate_reason"])
        seen = collections.Counter()
        for path, ds, true in build_sets(a.per_class):
            if a.limit and seen[ds] >= a.limit:
                continue
            seen[ds] += 1
            try:
                pred, conf, ab = predict(path)
                g = gate(path)
            except Exception as e:  # unreadable or truncated download
                print("skip", path, e)
                continue
            wr.writerow([str(path.relative_to(ROOT)), ds, true, pred, f"{conf:.4f}", int(ab), int(g["ok"]), g["reason"] or ""])
            c = agg[f"{ds}/{true}"]
            acc = not ab
            c["n"] += 1; c["gate_pass"] += g["ok"]; c["accepted"] += acc
            c["accepted_correct"] += acc and pred == true
            c["conf_wrong"] += acc and pred != true
            c["conf_wrong_after_gate"] += acc and pred != true and g["ok"]
            c["healthy_flagged_disease"] += true == "healthy" and acc and pred in DIS
            c["rust_called_healthy"] += true == "rust" and acc and pred == "healthy"
            leaf = "unsure" if ab else pred
            dom = "field" if ds in ("uganda", "wild_inat") else ds
            pools[dom][true].append((leaf, leaf if g["ok"] else "unsure"))
    summary = {"model": mj.get("version"), "temperature": mj["temperature"], "threshold": mj["threshold"],
               "per_set_class": {k: dict(v) for k, v in sorted(agg.items())},
               "plots": plot_sim({k: dict(v) for k, v in pools.items()}, rules, sev)}
    (out / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    lines = [f"# Field check, model {mj.get('version')} (T={mj['temperature']}, threshold={mj['threshold']:.3f})", "",
             "| set/true | n | gate pass | accepted | accepted correct | confident wrong | wrong after gate |",
             "|---|---:|---:|---:|---:|---:|---:|"]
    for k, v in sorted(agg.items()):
        lines.append(f"| {k} | {v['n']} | {v['gate_pass']} | {v['accepted']} | {v['accepted_correct']} | {v['conf_wrong']} | {v['conf_wrong_after_gate']} |")
    lines += ["", "| plots (4,000 simulated 10-leaf plots each) | spray advice | all clear | ask officer |", "|---|---:|---:|---:|"]
    for k, v in summary["plots"].items():
        lines.append(f"| {k} | {v['spray_advice']:.1%} | {v['all_clear']:.1%} | {v['ask_officer']:.1%} |")
    (out / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
