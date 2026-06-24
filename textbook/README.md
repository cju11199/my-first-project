# Registry Review study guide (textbook)

A student-friendly, plain-language textbook covering all eight ARRT® Radiation Therapy exam content
areas. Built as the reading-material layer for the planned gated **Registry Review** feature
(see `../REGISTRY_REVIEW_PLAN.md` and `../REGISTRY_REVIEW_SOURCES.md`).

## Files
- `Registry_Review_RT_Exam_Study_Guide.pdf` — the rendered book (~103 pp, ~28,000 words, 19 diagrams).
- `front.md`, `chapters/ch1.md` … `chapters/ch8.md`, `back.md` — the editable source.
- `quickref.md` (Appendix A — formulas & key values), `glossary.md` (Appendix B — terms & abbreviations).
- `figures/*.svg` — labeled diagrams (Chapters 3, 6, and 7).
- `make_figures.py` (ch3), `make_figures_ch6.py` (ch6), `make_figures_ch7.py` (ch7) — generate the SVGs.
- `style.css` — print stylesheet (cover, contents with page numbers, callout boxes, tables, figures).
- `build.py` — assembles the Markdown and renders the PDF with WeasyPrint (appends the appendices if present).

## Rebuild
```
pip install markdown weasyprint pymupdf
python3 make_figures.py        # Chapter 3 diagrams
python3 make_figures_ch6.py    # Chapter 6 diagrams
python3 make_figures_ch7.py    # Chapter 7 diagrams
python3 build.py               # assemble + render the PDF
```

Chapters 3 (Radiation Physics & Radiobiology) and 7 (Prescription & Dose Calculation) are the most
expanded/illustrated, since physics and the dose-calc math are where students struggle most.
Chapter 3 has ten diagrams; Chapter 7 has seven; Chapter 6 (Treatment Volume Localization) has two
(nested ICRU target volumes; image-match → 6DOF couch correction).

**In-text citations:** key facts in each chapter carry a bracketed `[n]` that maps to a single,
continuously numbered reference list at the end of the chapter (free clickable sources first, then
"for deeper reading"). The build was checked so every `[n]` resolves to a real list entry.

## Notes
- Accuracy guardrails from the plan are applied: US NRC dose limits (not ICRP), inverse-square as
  `D₂ = D₁·(d₁/d₂)²`, HDR = Ir-192 / LDR = Cs-137 / I-125 seeds, doses framed as "commonly used."
- Independent educational content; original explanations, not actual ARRT items; not ARRT-affiliated.
- Before any public/scored use, diff against the official ARRT content specifications PDF and have an
  RT-credentialed SME review each chapter.
- When the gated feature is built, serve this **behind the auth gate** rather than as a public file.
