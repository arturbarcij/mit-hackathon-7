"""Collect CC-licensed coffee leaf photos (iNaturalist research grade, Wikimedia Commons) for a wild test set.

Usage:
  python wild_collect.py list            # build candidate list, print counts, write wild_candidates.json
  python wild_collect.py download        # download candidates into ../../data_raw/wild/ and write wild_set.csv

Rules: respects API rate limits (>= 1 s between API calls), identifies itself, skips ND licences,
keeps licence and author for every image. Images are never committed (data_raw/ is outside the repo).
"""
import json, os, sys, time, csv, re, urllib.request, urllib.parse, urllib.error

UA = "JaniResearch/1.0 (hackathon research; non-commercial test set)"
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ROOT, "data_raw", "wild")
CAND = os.path.join(HERE, "wild_candidates.json")
CSV = os.path.join(HERE, "wild_set.csv")

OK_LIC = {"cc0", "cc-by", "cc-by-sa", "cc-by-nc", "cc-by-nc-sa"}  # no ND
LIC_NAME = {"cc0": "CC0 1.0", "cc-by": "CC BY 4.0", "cc-by-sa": "CC BY-SA 4.0", "cc-by-nc": "CC BY-NC 4.0", "cc-by-nc-sa": "CC BY-NC-SA 4.0"}

def get_json(url):
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            return json.load(urllib.request.urlopen(req, timeout=60))
        except urllib.error.HTTPError as e:
            if e.code in (429, 503):
                time.sleep(10 * (attempt + 1))
                continue
            raise
    raise RuntimeError("giving up " + url)

def inat(taxon_id, label, extra, cap):
    rows, page, seen = [], 1, set()
    while len(rows) < cap:
        q = {"taxon_id": taxon_id, "quality_grade": "research", "photos": "true",
             "photo_license": ",".join(sorted(OK_LIC)), "per_page": 100, "page": page,
             "order_by": "id", "order": "asc"}
        q.update(extra)
        j = get_json("https://api.inaturalist.org/v1/observations?" + urllib.parse.urlencode(q))
        time.sleep(1.1)
        if not j["results"]:
            break
        for o in j["results"]:
            # one photo per observation (the first with an allowed licence), to avoid near-duplicates
            taken = False
            for p in o.get("photos", []):
                lic = (p.get("license_code") or "").lower()
                if taken or lic not in OK_LIC or p["id"] in seen:
                    continue
                taken = True
                seen.add(p["id"])
                url = p["url"].replace("square", "large")
                loc = o.get("place_guess") or ""
                rows.append({
                    "image_url": url,
                    "page_url": o["uri"],
                    "licence": LIC_NAME[lic],
                    "author": (p.get("attribution") or "").replace("\n", " "),
                    "label_hint": label,
                    "source": "iNaturalist",
                    "photo_id": f"inat_{p['id']}",
                    "country_or_place": loc,
                    "taxon": (o.get("taxon") or {}).get("name", ""),
                    "observed_on": o.get("observed_on") or "",
                })
        if j["total_results"] <= page * 100:
            break
        page += 1
    return rows[:cap]

def commons(queries, cap):
    rows, seen = [], set()
    for qtext, hint in queries:
        cont = {}
        for _ in range(3):
            params = {"action": "query", "format": "json", "generator": "search", "gsrsearch": qtext,
                      "gsrnamespace": 6, "gsrlimit": 50, "prop": "imageinfo",
                      "iiprop": "url|extmetadata|mime", "iiurlwidth": 1024}
            params.update(cont)
            j = get_json("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params))
            time.sleep(1.1)
            for pg in (j.get("query", {}).get("pages", {}) or {}).values():
                ii = (pg.get("imageinfo") or [{}])[0]
                if not ii.get("mime", "").startswith("image/jpeg"):
                    continue
                md = ii.get("extmetadata", {})
                lic = md.get("LicenseShortName", {}).get("value", "")
                if not lic or "ND" in lic.upper().split() or lic.upper().startswith("CC BY-ND"):
                    continue
                title = pg["title"]
                if title in seen:
                    continue
                seen.add(title)
                author = re.sub(r"<[^>]+>", "", md.get("Artist", {}).get("value", "")).strip()
                desc = re.sub(r"<[^>]+>", "", md.get("ImageDescription", {}).get("value", "")).strip()
                text = (title + " " + desc).lower()
                lab = "rust" if ("rust" in text or "vastatrix" in text) else hint
                rows.append({
                    "image_url": ii.get("thumburl") or ii["url"],
                    "page_url": ii.get("descriptionurl", ""),
                    "licence": lic,
                    "author": author,
                    "label_hint": lab,
                    "source": "Wikimedia Commons",
                    "photo_id": "wc_" + re.sub(r"[^A-Za-z0-9]+", "_", title)[:60],
                    "country_or_place": "",
                    "taxon": "",
                    "observed_on": md.get("DateTimeOriginal", {}).get("value", ""),
                })
            if "continue" in j:
                cont = j["continue"]
            else:
                break
    return rows[:cap]

def build():
    cands = []
    cands += inat(328339, "rust (identified as Hemileia vastatrix)", {}, 120)
    # Coffea arabica research grade. First try observations annotated 'no evidence of flowering'
    # (Plant Phenology) to favour vegetative shots, then top up without that filter.
    veg = inat(64342, "coffee_plant_unverified (check: leaf visible? healthy or not?)", {"term_id": 12, "term_value_id": 21}, 140)
    seen_ids = {c["photo_id"] for c in veg}
    more = [c for c in inat(64342, "coffee_plant_unverified (check: leaf visible? healthy or not?)", {"order_by": "random", "order": "desc"}, 140) if c["photo_id"] not in seen_ids]
    cands += (veg + more)[:140]
    cands += commons([("coffee leaf rust", "coffee_leaf_unverified"), ("Hemileia vastatrix", "rust"),
                      ("coffee leaves Coffea arabica", "coffee_leaf_unverified"), ("coffee plant leaf disease", "coffee_leaf_unverified")], 80)
    json.dump(cands, open(CAND, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    from collections import Counter
    print("candidates:", len(cands))
    print(Counter((c["source"], c["label_hint"].split(" ")[0], c["licence"]) for c in cands))

def download():
    cands = json.load(open(CAND, encoding="utf-8"))
    os.makedirs(OUT, exist_ok=True)
    ok = []
    for c in cands:
        sub = "inat" if c["source"] == "iNaturalist" else "commons"
        d = os.path.join(OUT, sub)
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, c["photo_id"] + ".jpg")
        if not os.path.exists(path) or os.path.getsize(path) < 2000:
            try:
                req = urllib.request.Request(c["image_url"], headers={"User-Agent": UA})
                data = urllib.request.urlopen(req, timeout=60).read()
                if len(data) < 2000 or data[:2] != b"\xff\xd8":
                    print("skip (not jpeg)", c["photo_id"]); continue
                open(path, "wb").write(data)
            except Exception as e:
                print("fail", c["photo_id"], repr(e)[:80]); continue
            time.sleep(0.4)
        c["local_file"] = os.path.relpath(path, ROOT).replace("\\", "/")
        ok.append(c)
    cols = ["image_url", "page_url", "licence", "author", "label_hint", "source", "local_file", "photo_id", "country_or_place", "taxon", "observed_on"]
    with open(CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for c in ok:
            w.writerow({k: c.get(k, "") for k in cols})
    print("downloaded and listed:", len(ok), "->", CSV)

if __name__ == "__main__":
    {"list": build, "download": download}[sys.argv[1]]()
