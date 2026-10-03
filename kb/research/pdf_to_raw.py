"""Download a PDF directly and save extracted text as markdown with a header.
Usage: python pdf_to_raw.py <url> <job> <name>
Used only when Bright Data returns raw PDF bytes instead of text."""
import sys, os, subprocess, io
from pypdf import PdfReader

url, job, name = sys.argv[1:4]
here = os.path.dirname(os.path.abspath(__file__))
out = os.path.join(here, "raw", job)
os.makedirs(out, exist_ok=True)
tmp = os.path.join(out, name + ".pdf.tmp")
r = subprocess.run(["curl.exe", "-sL", "-A", "Mozilla/5.0", "-o", tmp, "-w", "%{http_code} %{content_type} %{size_download}", url], capture_output=True, text=True)
print("curl:", r.stdout)
try:
    reader = PdfReader(tmp)
    text = []
    for i, p in enumerate(reader.pages, 1):
        text.append(f"\n\n===== PAGE {i} =====\n\n" + (p.extract_text() or ""))
    body = "".join(text)
    header = f"---\nurl: {url}\naccessed: 2026-10-03\ntool: direct download (Bright Data returned raw PDF bytes); text extracted with pypdf\njob: {job}\npages: {len(reader.pages)}\n---\n"
    open(os.path.join(out, name + ".md"), "w", encoding="utf-8").write(header + body)
    print("pages", len(reader.pages), "chars", len(body))
finally:
    if os.path.exists(tmp):
        os.remove(tmp)
