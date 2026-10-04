"""Build the 'Try with sample leaves' demo set.
Reads kb/research/wild_set.csv and data_raw/wild/, writes app/public/demo/*.jpg and manifest.json.
Picks were made by looking at contact sheets (data_raw/wild/_contact/). Labels are source hints, not agronomist labels.
Run from the repo root: python3 kb/content/demo_samples_build.py
"""
import csv, io, json, os, re, urllib.parse
from PIL import Image, ImageOps

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "app", "public", "demo")
LIC = {
    "CC BY 4.0": "https://creativecommons.org/licenses/by/4.0/",
    "CC BY 3.0 us": "https://creativecommons.org/licenses/by/3.0/us/",
    "CC BY-SA 3.0": "https://creativecommons.org/licenses/by-sa/3.0/",
    "CC BY-SA 4.0": "https://creativecommons.org/licenses/by-sa/4.0/",
    "CC0 1.0": "https://creativecommons.org/publicdomain/zero/1.0/",
}
# (row index in wild_set.csv, file name, role, visual note)
PICKS = [
    (14, "sample01_rust.jpg", "rust",
     "One leaf on an open palm, underside. Many orange powdery pustules and a few brown dead patches. Daylight, sharp."),
    (36, "sample02_rust.jpg", "rust",
     "Close-up of a leaf underside. Two round orange powdery lesions, one with a dark centre; one small hole. Sharp."),
    (194, "sample03_rust.jpg", "rust",
     "Leaf held between fingers, underside. Large orange powdery patches along the leaf. Daylight."),
    (13, "sample04_rust.jpg", "rust",
     "Leaf held by hand, upper side. Round yellow spots with orange centres. Daylight, sharp."),
    (35, "sample05_rust.jpg", "rust",
     "Leaf held in fingers, underside. Many small orange spots and some brown edges. Slightly soft focus."),
    (6, "sample06_rust.jpg", "rust",
     "Upper side of one leaf on the plant. Many small pale yellow spots and one hole; no orange powder visible from this side (early or upper-side view)."),
    (216, "sample07_healthy.jpg", "healthy",
     "Several glossy dark green leaves on the plant. No spots visible. Not a single detached leaf."),
    (215, "sample08_healthy.jpg", "healthy",
     "Glossy leaves on the plant with one bright young leaf in front. No spots visible."),
    (217, "sample09_healthy.jpg", "healthy",
     "One detached leaf on a dark cloth (close to our capture protocol). Mostly clean; faint brown marks on the left half, so it may score borderline."),
    (240, "sample10_other.jpg", "other_problem",
     "Leaf underside held in a gloved hand. Dry brown edges all round, no orange powder. Not rust; the source gives no cause (could be scorch, drought or nutrients). App should say: ask the officer."),
    (249, "sample11_berry.jpg", "edge_case_berry",
     "Cluster of ripe red coffee cherries with two leaves. Out of scope: the app must say it cannot judge berries."),
    (212, "sample12_poor.jpg", "edge_case_poor_photo",
     "Many glossy leaves in deep shade. Dark, cluttered, no single leaf fills the frame. Should trigger the retake prompt."),
]

def clean_author(a):
    m = re.match(r"\(c\)\s*(.*?),\s*some rights reserved", a)
    if m:
        return m.group(1)
    return re.sub(r"^Photo by\s+", "", a).strip()

def direct_url(row):
    if row["source"] == "iNaturalist":
        m = re.search(r"/photos/(\d+)/large\.(\w+)", row["image_url"])
        return f"https://inaturalist-open-data.s3.amazonaws.com/photos/{m.group(1)}/medium.{m.group(2)}", row["image_url"]
    fname = urllib.parse.unquote(row["page_url"].split("/wiki/File:")[1])
    q = urllib.parse.quote(fname.replace(" ", "_"))
    return f"https://commons.wikimedia.org/wiki/Special:FilePath/{q}?width=640", f"https://commons.wikimedia.org/wiki/Special:FilePath/{q}"

def save_small(src, dst):
    im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    im.thumbnail((640, 640), Image.LANCZOS)
    for q in (80, 75, 70, 65, 60):
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=q, optimize=True, progressive=True)
        if buf.tell() < 120 * 1024:
            break
    open(dst, "wb").write(buf.getvalue())
    return im.size, buf.tell(), q

def main():
    rows = list(csv.DictReader(open(os.path.join(ROOT, "kb/research/wild_set.csv"), encoding="utf-8")))
    os.makedirs(OUT, exist_ok=True)
    items = []
    for idx, name, role, note in PICKS:
        r = rows[idx]
        assert "NC" not in r["licence"].upper() and "ND" not in r["licence"].upper()
        url, url_full = direct_url(r)
        (w, h), size, q = save_small(os.path.join(ROOT, r["local_file"]), os.path.join(OUT, name))
        author = clean_author(r["author"])
        items.append({
            "file": name,
            "local_path": f"/demo/{name}",
            "image_url": url,
            "image_url_full": url_full,
            "page_url": r["page_url"].replace("http://", "https://"),
            "author": author,
            "licence": r["licence"],
            "licence_url": LIC[r["licence"]],
            "source": r["source"],
            "place": r["country_or_place"] or None,
            "observed_on": r["observed_on"][:10] or None,
            "hint_label": r["label_hint"],
            "visual_note": note,
            "role": role,
            "label_status": "hint, not verified by an agronomist",
            "width": w, "height": h, "bytes": size, "jpeg_quality": q,
            "attribution": f"Photo: {author}, {r['source']}, {r['licence']} ({LIC[r['licence']]}). Resized to {max(w, h)} px.",
            "wild_set_row": idx,
        })
    manifest = {
        "title": "Sample coffee leaves for demo mode",
        "note": "Real photos from public sources (Costa Rica, Brazil, Colombia, Guatemala, Hawaii and others). Not from Kenya and not from Noor's farm. Labels are source hints, not verified by an agronomist. Use local_path first; image_url is the public fallback.",
        "synthetic": False,
        "built_by": "kb/content/demo_samples_build.py",
        "items": items,
    }
    json.dump(manifest, open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    tot = sum(i["bytes"] for i in items)
    for i in items:
        print(i["file"], i["width"], i["height"], i["bytes"], i["jpeg_quality"], i["image_url"])
    print("total_bytes", tot)

if __name__ == "__main__":
    main()
