# Registry Review study guide (textbook)

A student-friendly, plain-language textbook covering all eight ARRT® Radiation Therapy exam content
areas. Built as the reading-material layer for the planned gated **Registry Review** feature
(see `../REGISTRY_REVIEW_PLAN.md` and `../REGISTRY_REVIEW_SOURCES.md`).

## Files
- `Registry_Review_RT_Exam_Study_Guide.pdf` — the rendered book (91 pp, ~26,000 words).
- `front.md`, `chapters/ch1.md` … `chapters/ch8.md`, `back.md` — the editable source.
- `figures/*.svg` — labeled diagrams (Chapter 3 physics + Chapter 7 dose-calculation illustrations).
- `make_figures.py`, `make_figures_ch7.py` — generate the SVG diagrams.
- `style.css` — print stylesheet (cover, contents with page numbers, callout boxes, tables, figures).
- `build.py` — assembles the Markdown and renders the PDF with WeasyPrint.

## Rebuild
```
pip install markdown weasyprint pymupdf
python3 make_figures.py        # Chapter 3 diagrams
python3 make_figures_ch7.py    # Chapter 7 diagrams
python3 build.py               # assemble + render the PDF
```

Chapters 3 (Radiation Physics & Radiobiology) and 7 (Prescription & Dose Calculation) are
expanded and illustrated, since physics and the dose-calc math are where students struggle most.
Chapter 3 has ten diagrams (decay scheme, bremsstrahlung, photon interactions, dominance map,
inverse-square, attenuation/HVL, depth dose, cell-survival, oxygen effect, deterministic vs
stochastic). Chapter 7 has seven (SSD vs SAD geometry, equivalent square, MU-equation anatomy,
wedge isodose tilt, field-junction gap, electron depth dose, dose-volume histogram).

## Notes
- Accuracy guardrails from the plan are applied: US NRC dose limits (not ICRP), inverse-square as
  `D₂ = D₁·(d₁/d₂)²`, HDR = Ir-192 / LDR = Cs-137 / I-125 seeds, doses framed as "commonly used."
- Independent educational content; original explanations, not actual ARRT items; not ARRT-affiliated.
- Before any public/scored use, diff against the official ARRT content specifications PDF and have an
  RT-credentialed SME review each chapter.
- When the gated feature is built, serve this **behind the auth gate** rather than as a public file.
