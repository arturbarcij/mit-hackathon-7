"""Append entries to sources.json. Usage: python add_sources.py new_entries.json
Skips ids that already exist. Also lets you extend used_in on existing ids via {"id": "S17", "add_used_in": ["GUIDANCE.md section 4"]}."""
import json, sys, os

here = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(here, "sources.json")
data = json.load(open(path, encoding="utf-8"))
have = {s["id"]: s for s in data["sources"]}
new = json.load(open(sys.argv[1], encoding="utf-8"))
for e in new:
    if "add_used_in" in e:
        s = have[e["id"]]
        for u in e["add_used_in"]:
            if u not in s.setdefault("used_in", []):
                s["used_in"].append(u)
        continue
    if e["id"] in have:
        print("skip existing", e["id"])
        continue
    data["sources"].append(e)
# Write one source per line as before.
head = json.dumps(data["_meta"], ensure_ascii=False, indent=2)
lines = ",\n".join("    " + json.dumps(s, ensure_ascii=False) for s in data["sources"])
open(path, "w", encoding="utf-8").write('{\n  "_meta": ' + head.replace("\n", "\n  ") + ',\n  "sources": [\n' + lines + "\n  ]\n}\n")
json.load(open(path, encoding="utf-8"))
print("sources now:", len(data["sources"]))
