"""Build kb/research/prices.json from the NCE 'Market Total' PDFs saved as markdown in raw/prices/.
Only numbers printed in the PDFs are used. Prices are USD per 50 kg bag (as printed)."""
import re, json, glob, os, datetime

root = os.path.dirname(os.path.abspath(__file__))
rows, sales = [], []
for f in sorted(glob.glob(os.path.join(root, "raw", "prices", "nce_market_report_*.md"))):
    t = open(f, encoding="utf-8").read()
    m = re.search(r"^url: (.+)$", t, re.M)
    url = m.group(1)
    m = re.search(r"Sale (\d+) of \w+, (\w+) (\d+), (\d{4})", t)
    if not m:
        print("no text:", os.path.basename(f))
        continue
    sale, mon, day, yr = m.groups()
    date = datetime.datetime.strptime(f"{mon} {day} {yr}", "%B %d %Y").date().isoformat()
    for line in t.splitlines():
        g = re.match(r"^(TOTAL:|[A-Z0-9]{1,3}) ([\d,]+) ([\d,]+) ([\d.]+) ([\d.]+) ([\d,.]+) ([\d.]+)$", line.strip())
        if not g:
            continue
        grade, bags, kg, lo, hi, val, avg = g.groups()
        grade = "ALL" if grade == "TOTAL:" else grade
        rows.append({
            "sale": int(sale), "date": date, "grade": grade,
            "bags_offered": int(bags.replace(",", "")),
            "min_usd_per_50kg": float(lo), "max_usd_per_50kg": float(hi),
            "avg_usd_per_50kg": float(avg),
            "source_url": url,
        })
rows.sort(key=lambda r: (r["date"], r["grade"]))
json.dump(rows, open(os.path.join(root, "prices_rows.json"), "w"), indent=1)
print(len(rows), "rows;", sorted({(r["sale"], r["date"]) for r in rows}))

# ---- final file ----
RATE = 129.45  # KES per USD, stated in the saccoreview Sale 39 article (8 Sept 2026)
for r in rows:
    r["kes_per_50kg_derived"] = round(r["avg_usd_per_50kg"] * RATE)
out = {
  "_meta": {
    "accessed": "2026-10-03",
    "what": "Nairobi Coffee Exchange (NCE) weekly 'Market Total' per grade, Tuesday sales 30 to 41 (8 Jul to 22 Sep 2026), plus two sales known only from news reports.",
    "primary_unit": "USD per 50 kg bag, exactly as printed in the NCE PDFs (the PDFs state 'Prices are in USD per 50 Kg').",
    "kes_per_50kg_derived": "avg_usd_per_50kg x 129.45. The rate is the one stated in the saccoreview.co.ke Sale 39 article (8 Sept 2026). It is applied to every week, so it is an approximation, not an NCE figure. The NCE PDFs give no KES.",
    "grades": "AA, AB, C, PB, TT, T, UG1.. are NCE grade codes. 'ALL' is the sale total line.",
    "not_found": [
      "AFA county prices: afa.go.ke returned no search results through Bright Data; no AFA price table found.",
      "NCE PDF for Sale 39 (8 Sep) is image-only (no text); numbers come from the news report below.",
      "NCE PDF for Sale 42 (29 Sep, last sale of 2025/26) not on the market-reports page when fetched; only the Standard report.",
      "Farm-gate (cherry, KES per kg) prices by county or society: only search snippets seen, not opened or saved."
    ],
    "warnings": [
      "The NCE home page shows placeholder-looking tiles (Total Sales KES 1.2M, Average Price KES 320/kg, ABC Exporters, 3,750 kg). They are not used.",
      "News reports in KES per 50 kg bag (KBC 6 Aug: Ksh 44,503; Standard last sale: Sh44,462, 'down from Sh 44,443 last week') do not reconcile with NCE PDF averages x 129.45. Treat media KES figures as unreconciled; use the PDF USD figures."
    ]
  },
  "weekly_by_grade": rows,
  "from_media_only": [
    {"sale": 39, "date": "2026-09-08", "grade": "ALL", "avg_usd_per_50kg": 312.10, "min_usd_per_50kg": 80, "max_usd_per_50kg": 404, "bags": 13484,
     "note": "Ksh 675.2 million traded; rate Ksh129.45 per USD stated.", "source_url": "https://saccoreview.co.ke/nairobi-coffee-exchange-sale-39-fetches-sh675m/"},
    {"sale": 39, "date": "2026-09-08", "grade": "AA", "avg_usd_per_50kg": 360.90, "bags": 1305,
     "source_url": "https://saccoreview.co.ke/nairobi-coffee-exchange-sale-39-fetches-sh675m/"},
    {"sale": "42 (last sale of 2025/26, date not printed in the extract; the article says the season closes 30 Sep 2026)", "grade": "ALL", "avg_kes_per_50kg": 44462, "bags": 17765, "value_kes_million": 841.3,
     "note": "Bags offered: 2,468 AA, 7,049 AB, 3,094 C (CEO Lisper Ndung'u). Standard says previous week Sh44,443.",
     "source_url": "https://www.standardmedia.co.ke/business/business/article/2001559062/farmers-earn-sh841-million-from-coffee-auction"}
  ]
}
json.dump(out, open(os.path.join(root, "prices.json"), "w"), indent=1, ensure_ascii=False)
os.remove(os.path.join(root, "prices_rows.json"))
print("wrote prices.json", len(rows))
