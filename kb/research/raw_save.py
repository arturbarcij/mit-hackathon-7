"""Split a saved Bright Data scrape_batch output into one markdown file per URL.

Usage: python raw_save.py <agent-tools output file> <job>
Writes kb/research/raw/<job>/<slug>.md with a header (URL, accessed date, tool).
Prints a one-line summary (chars, first heading) per page so empty results are obvious.
"""
import json, re, sys, os, datetime

src, job = sys.argv[1], sys.argv[2]
raw = open(src, encoding="utf-8", errors="replace").read()
today = "2026-10-03"
out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "raw", job)
os.makedirs(out_dir, exist_ok=True)

# Find the JSON array inside the untrusted-content wrapper.
start = raw.find("[")
end = raw.rfind("]")
data = json.loads(raw[start:end + 1])
if isinstance(data, dict):
    data = [data]

def slug(url):
    s = re.sub(r"^https?://(www\.)?", "", url)
    s = re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")
    return s[:90]

for item in data:
    url = item.get("url") or item.get("link") or "unknown"
    content = item.get("content") or item.get("markdown") or item.get("result") or ""
    if not isinstance(content, str):
        content = json.dumps(content, ensure_ascii=False)
    name = slug(url) + ".md"
    header = f"---\nurl: {url}\naccessed: {today}\ntool: Bright Data scrape_as_markdown (MCP)\njob: {job}\n---\n\n"
    with open(os.path.join(out_dir, name), "w", encoding="utf-8") as f:
        f.write(header + content)
    first = next((l.strip() for l in content.splitlines() if l.strip()), "")[:80]
    print(f"{len(content):>8} chars  {name}  | {first}")
