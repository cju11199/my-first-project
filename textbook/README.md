# Registry Review study guide (textbook)

A student-friendly, plain-language textbook covering all eight ARRT® Radiation Therapy exam content
areas. Built as the reading-material layer for the planned gated **Registry Review** feature
(see `../REGISTRY_REVIEW_PLAN.md` and `../REGISTRY_REVIEW_SOURCES.md`).

## Files
- `Registry_Review_RT_Exam_Study_Guide.pdf` — the rendered book (86 pp, ~25,600 words).
- `front.md`, `chapters/ch1.md` … `chapters/ch8.md`, `back.md` — the editable source.
- `style.css` — print stylesheet (cover, contents with page numbers, callout boxes, tables).
- `build.py` — assembles the Markdown and renders the PDF with WeasyPrint.

## Rebuild
```
pip install markdown weasyprint pymupdf
python3 build.py
```

## Notes
- Accuracy guardrails from the plan are applied: US NRC dose limits (not ICRP), inverse-square as
  `D₂ = D₁·(d₁/d₂)²`, HDR = Ir-192 / LDR = Cs-137 / I-125 seeds, doses framed as "commonly used."
- Independent educational content; original explanations, not actual ARRT items; not ARRT-affiliated.
- Before any public/scored use, diff against the official ARRT content specifications PDF and have an
  RT-credentialed SME review each chapter.
- When the gated feature is built, serve this **behind the auth gate** rather than as a public file.
