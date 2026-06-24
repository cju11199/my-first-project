#!/usr/bin/env python3
import re, os, markdown
from weasyprint import HTML

BASE = os.path.dirname(os.path.abspath(__file__))
CH = os.path.join(BASE, "chapters")

def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()

# Assemble: front matter -> chapters 1..8 -> back matter
parts = [read(os.path.join(BASE, "front.md"))]
for i in range(1, 9):
    parts.append(read(os.path.join(CH, f"ch{i}.md")))
parts.append(read(os.path.join(BASE, "back.md")))
big_md = "\n\n".join(parts)

md = markdown.Markdown(extensions=["tables", "fenced_code", "attr_list",
                                   "sane_lists", "toc"],
                       extension_configs={"toc": {"toc_depth": 1}})
body_html = md.convert(big_md)
toc_html = md.toc  # <div class="toc"><ul>... top-level headings ...</ul></div>

# Tag callout blockquotes so they can be colored differently
body_html = re.sub(r'<blockquote>\s*<p><strong>Key Point',
                   '<blockquote class="keypoint"><p><strong>Key Point', body_html)
body_html = re.sub(r'<blockquote>\s*<p><strong>Common mix-up',
                   '<blockquote class="mixup"><p><strong>Common mix-up', body_html)

cover = """
<section class="cover">
  <div class="kicker">Radiation Therapy Board Prep</div>
  <h1>Registry Review</h1>
  <div class="sub">A Student's Friendly Guide to the ARRT&reg; Radiation Therapy Certification Exam</div>
  <div class="meta">
    First Edition &middot; 2026<br>
    All eight content areas &middot; worked examples &middot; self-check questions<br>
    A companion study guide to the RT Image Matching Trainer
  </div>
  <div class="disclaim">
    Educational use only. Not affiliated with, endorsed by, or sponsored by the ARRT.
    &ldquo;ARRT&rdquo; is a registered trademark of the American Registry of Radiologic Technologists.
    Practice explanations are original and are not actual exam questions.
  </div>
</section>
"""

contents = f'<section class="toc"><h1>Contents</h1>{toc_html}</section>'

html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>Registry Review</title></head>
<body>{cover}{contents}{body_html}</body></html>"""

out_html = os.path.join(BASE, "book.html")
with open(out_html, "w", encoding="utf-8") as f:
    f.write(html)

pdf_path = os.path.join(BASE, "Registry_Review_RT_Exam_Study_Guide.pdf")
HTML(string=html, base_url=BASE).write_pdf(pdf_path, stylesheets=[os.path.join(BASE, "style.css")])

words = len(re.sub(r"<[^>]+>", " ", body_html).split())
print("PDF:", pdf_path)
print("PDF bytes:", os.path.getsize(pdf_path))
print("Approx body words:", words)
print("TOC entries:", toc_html.count("<a "))
