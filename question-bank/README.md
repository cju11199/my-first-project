# Registry Review — Question Bank

A large bank of **original** multiple-choice practice questions for the **ARRT® Radiation Therapy**
certification exam, grouped by the exam's own content categories. This is study **content** (the eventual
`/review` feature's source material); it is **not** wired into any application yet.

> Educational use only. These are original practice questions written for study — **not** actual ARRT exam
> items — and this material is **not affiliated with, endorsed by, or sponsored by the ARRT**. "ARRT" is a
> registered trademark of the American Registry of Radiologic Technologists. Verify clinical specifics
> against the cited sources and the official ARRT content specifications before any high-stakes use.

## Organization (by ARRT content category → subcategory)

The eight files map one-to-one to the eight ARRT subcategories, and the question count per area is
**weighted to the real exam blueprint** (Procedures ≈ 52%, Safety ≈ 25%, Patient Care ≈ 23%).

| File | Category | Subcategory | Prefix | Questions |
|---|---|---|---|---:|
| `01-patient-interactions.md` | Patient Care | Patient Interactions & Management | `PIM` | 45 |
| `02-patient-records.md` | Patient Care | Patient & Medical Record Management | `PMR` | 30 |
| `03-physics-radiobiology.md` | Safety | Radiation Physics & Radiobiology | `PHR` | 50 |
| `04-protection-qa.md` | Safety | Radiation Protection, Equipment Operation & QA | `RPQ` | 70 |
| `05-treatment-sites.md` | Procedures | Treatment Sites & Tumors | `SIT` | 45 |
| `06-volume-localization.md` | Procedures | Treatment Volume Localization | `TVL` | 35 |
| `07-dose-calculation.md` | Procedures | Prescription & Dose Calculation | `DOS` | 45 |
| `08-treatments.md` | Procedures | Treatments | `TRX` | 55 |

**Totals:** Patient Care 75 · Safety 120 · Procedures 180 · **Grand total 375 questions.**

Within each file, questions are further grouped under thematic `## sub-topic` headings and numbered with the
file's prefix (e.g., `PHR-01`, `PHR-02`, …).

## Question format

Each item follows the same structure, which makes it easy to convert into the quiz data model later:

```
### PHR-07 · _calculation_
A 6 MV beam delivers 100 cGy at d_max. If the PDD at 10 cm is 66%, what is the dose at 10 cm depth?

- **A.** 66 cGy
- **B.** 152 cGy
- **C.** 34 cGy
- **D.** 100 cGy

**Answer:** A
**Explanation:** Dose at depth = dose at d_max × (PDD/100) = 100 × 0.66 = 66 cGy.
**Source:** IAEA handbook
```

- **Type tag** on each question: `recall`, `application`, or `calculation`.
- **One** best answer; distractors are built from common misconceptions.
- **Answer key is balanced** across A/B/C/D (≈94 each) so the bank is not gameable.
- **Explanations** give the reasoning / key step; **Sources** are listed *free-first* (IAEA handbook, AAPM
  Task Group reports, NRC 10 CFR 20, NCI PDQ, ICRU, ASRT, CDC), with textbooks named where appropriate.

## Accuracy guardrails applied

- US **NRC 10 CFR 20** dose limits (occupational 50 mSv/yr, public 1 mSv/yr, embryo/fetus 5 mSv over the
  gestation, lens 150 mSv/yr, extremity 500 mSv/yr) — **not** the ICRP figures.
- Inverse-square `D₂ = D₁ × (d₁/d₂)²`; equivalent square `2ab/(a+b)`; SSD→PDD, SAD→TMR/TPR.
- Compton dominant at MV; pair-production threshold 1.02 MeV; `1 Gy = 100 rad`, `1 Sv = 100 rem`.
- Brachytherapy isotopes: **HDR = Ir-192, LDR intracavitary = Cs-137, permanent prostate seeds = I-125.**
- Dose/fractionation numbers are framed as **"commonly used"** (protocol-dependent).

## Verification

A programmatic check confirms every question has four options, an answer, an explanation, and a source, and
that the answer key is evenly distributed. The calculation- and safety-heavy banks (physics, protection/QA,
dose-calculation, treatments) were additionally put through an **independent answer-key review**.

## Status / next steps

- v1 covers the full blueprint at ~375 questions. The bank is easily **expandable** — add more questions
  under the same prefixes and sub-topic headings.
- Before any scored/published use: diff topics against the official ARRT content specifications and have an
  **RT-credentialed SME** review the answer keys (the owner is well-placed to do this).
- When the gated `/review` feature is built, these convert directly into the quiz data model
  (`{id, cat, sub, stem, choices[], answer, explanation, source, difficulty}`) — see
  `../REGISTRY_REVIEW_PLAN.md`.
