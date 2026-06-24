# Registry Review — Planning & Content Blueprint

> **Status: PLANNING ONLY. No feature code written yet.** This document is the research +
> design artifact for adding an ARRT-style "Registry Review" study section to the RT Image
> Matching Trainer. It captures (1) the verified ARRT Radiation Therapy exam blueprint,
> (2) a source-backed content outline for every content category, (3) accuracy corrections
> that MUST be resolved before any question is authored, and (4) the implementation plan.

---

## 0. Decisions locked with the owner

| Decision | Choice |
|---|---|
| **Access** | **Gated premium feature** (behind the Clerk `full_access` gate, like `/trainer`). Not indexable. A selling point: "practice + registry prep in one." |
| **Formats** | All four: **Reading/study guides · Flashcards · Interactive quiz engine · Mock registry exam** |
| **v1 scope** | **Full blueprint, shallow** — cover all three categories / eight subcategories with a smaller item set each, weighted to the real exam split |

---

## 1. The exam (verified)

**Credential:** ARRT® Radiation Therapy (the `T` discipline). Computer-based, multiple-choice.

- **200 scored + 30 unscored (pilot)** = 230 items; ~3.5-hour appointment; **scaled passing score 75**.
- Current blueprint in effect **through Jan 31, 2027**. ARRT approved a revision **effective Feb 1, 2027**
  (minor — same category structure; adds 3D/4D simulation, EMR/electronic-device items, "review pertinent
  medical history," CT-sim compliance, mental-health-crisis & critical-findings communication, oxygen
  administration, BLS/ACLS in place of CPR, bone metastases as a named site; swaps a mechanical-safety QA
  check). **v1 should teach the current blueprint and tag 2027-new topics so we can flip them on.**

### Scored-item split (drives the mock-exam sampler weights)

| Category | Scored Qs | % | Subcategories (Qs) |
|---|---|---|---|
| **Patient Care** | 46 | 23% | Patient Interactions & Management (29) · Patient & Medical Record Management (17) |
| **Safety** | 51 | 25.5% | Radiation Physics & Radiobiology (21) · Radiation Protection, Equipment Operation & QA (30) |
| **Procedures** | 103 | 51.5% | Treatment Sites & Tumors (26) · Treatment Volume Localization (18) · Prescription & Dose Calculation (24) · Treatments (35) |

> Official content specs: <https://www.arrt.org/pages/arrt-reference-documents/by-document-type/examination-content-specifications>
> · About the exam: <https://www.arrt.org/pages/resources/exam-information/about-the-exam>
> · 2026/2027 update: <https://www.arrt.org/news/article/2026/04/01/updated-radiation-therapy-documents-2026>
> The official spec PDFs return HTTP 403 to automated fetches, so the outline below was corroborated against
> textbooks/standards rather than scraped from the PDF. Before launch, a human should diff this against the
> downloaded PDF for exact subtopic wording.

---

## 2. Content blueprint (source-backed)

Organized as **category → subcategory → topics**. Each topic line is a fact a quiz item can be drawn from.
Sources are consolidated in §5. This is the spec the question/flashcard/guide authors work from.

### 2A. PATIENT CARE — Patient Interactions & Management (29)

- **Communication & assessment:** patient-centered language matched to health literacy; active listening;
  eliciting/responding to emotional cues; pertinent medical-history review *(2027-new)*; CT-sim compliance
  coaching *(2027-new)*.
- **Patient education & informed consent:** physician owns consent, therapist supports; disclosure of
  risks/benefits/alternatives; verify understanding; document consent.
- **Psychosocial support:** recognize distress/anxiety; coping support; referral to social work / chaplain /
  mental health; **mental-health-crisis escalation** *(2027-new)*.
- **Cultural competence:** interpreter use; diverse health beliefs; family decision-making structures.
- **Age-specific care:** pediatric (developmental communication, child-life, caregiver as surrogate);
  geriatric (frailty screening — G8/VES-13/Edmonton, fall risk, mobility).
- **Monitoring & symptoms:** vital signs (normal ranges + recognition of abnormal); acute symptom
  management (nausea/vomiting, fatigue, dyspnea, pain, syncope); acute vs late radiation side effects.
- **Comfort, positioning & transfer:** dignity/modesty *(2027-emphasis)*; assisted vs dependent transfer;
  body mechanics; managing lines/tubes/O₂ during moves; immobilization devices (thermoplastic masks,
  breast board, vac-bags); breath-hold instruction.
- **Medical emergencies:** syncope, respiratory distress, **oxygen administration** *(2027-new)*, chest
  pain, contrast reactions, severe N/V; **BLS/ACLS** *(replaces CPR, 2027)*.
- **Contrast media:** ionic vs non-ionic iodinated; reaction severity (minor/moderate/severe);
  pre-screen renal function / allergy / pregnancy.
- **Ethics/legal:** Patient Bill of Rights; autonomy & refusal; HIPAA Privacy/Security; ARRT Standards of
  Ethics; ASRT scope of practice/Code of Ethics.
- **Infection control:** Standard Precautions; hand hygiene/PPE; neutropenic precautions; transmission-based
  precautions.

### 2B. PATIENT CARE — Patient & Medical Record Management (17)

- **Cancer epidemiology & risk factors:** lifestyle/occupational/infectious (HPV, HBV/HCV) risks; common
  sites; TNM staging significance.
- **Medical history review:** prior surgery/chemo/RT (site/dose/dates); comorbidities; medications/allergies;
  pregnancy/lactation; performance status.
- **Pathology interpretation:** histology, grade, margins, nodal status, LVI/PNI; breast ER/PR/HER2.
- **Diagnostic imaging in planning:** CT (electron density for dose calc), MRI (soft-tissue/target),
  PET (metabolic/staging), 3D/4D sim *(2027-new)*.
- **Lab interpretation:** CBC (anemia/infection/bleeding risk), LFTs, renal (BUN/Cr, electrolytes),
  tumor markers (PSA/CEA/CA-19-9/AFP).
- **Prescription documentation:** dose, dose/fraction, fractionation, intent (curative/adjuvant/palliative),
  modality/energy, OAR constraints, physician authorization.
- **Treatment-delivery records:** date, fraction number, MU, daily + cumulative dose, beam parameters,
  interruptions, therapist verification.
- **MU / dose verification:** independent MU check; ICRU ±5% (≤3% preferred); IMRT/VMAT QA.
- **EMR / QA / team communication:** EMR record handling; chart checks; incident/near-miss reporting;
  therapist as daily patient liaison; **critical-findings communication** *(2027-new)*.

### 2C. SAFETY — Radiation Physics & Radiobiology (21)

- **Sources:** Co-60 (T½ 5.27 yr; 1.17 & 1.33 MeV γ); bremsstrahlung; characteristic x-rays.
- **Beam quality:** HVL; kV vs MV ranges; exponential attenuation `I = I₀e^(−μx)`.
- **Photon interactions:** photoelectric (low E, ∝Z³); **Compton (dominant at therapy MV energies)**;
  pair production (threshold 1.02 MeV).
- **Inverse-square law:** dose ∝ 1/d².
- **Units:** Gray (J/kg), Sievert (equivalent dose), Becquerel (activity); legacy rad/rem/roentgen
  (1 Gy = 100 rad, 1 Sv = 100 rem).
- **Calibration:** TG-51 reference dosimetry (photons at 10 cm depth; electron beam quality via R₅₀).
- **Cell survival / LQ model:** `S = e^(−αD−βD²)`; **α/β ≈ 10 Gy tumors/early-responding, ≈ 3 Gy
  late-responding**.
- **Four R's:** Repair, Repopulation, Reoxygenation, Reassortment (redistribution).
- **Oxygen effect:** OER ≈ 2.5–3.0 for low-LET; hypoxia → radioresistance.
- **LET & RBE:** low-LET (photons/electrons) vs high-LET (α, neutrons, carbon); RBE > 1 for high-LET.
- **Fractionation math:** `BED = nd(1 + d/(α/β))`; `EQD2 = BED / (1 + 2/(α/β))`.
- **Deterministic vs stochastic:** threshold/severity-with-dose (erythema, cataract, sterility) vs
  no-threshold/probability-with-dose (cancer, heritable).
- **Tissue tolerances (TD5/5):** spinal cord ~45–50 Gy; lung mean ≤ ~20 Gy / V20 ≤ ~35%; lens ~0.5 Gy.

### 2D. SAFETY — Radiation Protection, Equipment Operation & QA (30)

- **ALARA + Time/Distance/Shielding.**
- **Dose limits — USE NRC/NCRP VALUES (see §3, Flag #1):** occupational **50 mSv/yr (5 rem)**, cumulative
  10 mSv × age; public **1 mSv/yr (100 mrem)**; **declared-pregnant worker / embryo-fetus 5 mSv (0.5 rem)
  over gestation, ~0.5 mSv/month**; lens 50 mSv/yr; extremities/skin 500 mSv/yr.
- **Facility shielding (NCRP-151):** primary vs secondary barriers; workload W, use factor U, occupancy T;
  lead/concrete; controlled vs uncontrolled areas.
- **Personnel dosimetry:** TLD (reusable, LiF) vs film badge (permanent record, non-reusable) vs OSL;
  monthly monitoring; collar/waist placement.
- **Linac components:** electron gun, target (W), primary collimator, flattening filter (or FFF),
  dual monitor ion chambers, jaws, MLC.
- **Interlocks:** door, beam-off, motion-disable; redundant circuits.
- **Linac QA (TG-142):** daily (output constancy ±3%, symmetry, lasers, interlocks), monthly, annual;
  tighter tolerances for IMRT and SRS/SBRT.
- **Imaging QA:** CBCT/kV isocenter congruence ≤ ~1 mm (TG-179); image quality (HU linearity, MTF).
- **CT-sim QA (TG-66):** laser/geometry accuracy, HU calibration (water 0, air −1000), uniformity.

### 2E. PROCEDURES — Treatment Sites & Tumors (26)

> Anatomy, pathology, staging (AJCC 8th), routes of spread, nodal drainage, and typical dose/fractionation
> per site. **Dose numbers vary by protocol — author as "typical/commonly used," not absolutes (Flag #5).**

- **CNS:** glioblastoma (60 Gy/30 fx + temozolomide; CTV = enhancing + FLAIR + margin); vestibular
  schwannoma (SRS 12–13 Gy ×1); brain mets (SRS 15–24 Gy ×1 vs WBRT 30 Gy/10).
- **Head & neck:** SCC (70 Gy/35 + cisplatin; HPV status changes oropharynx staging/prognosis; cervical
  node levels I–VI); nasopharynx (EBV; IMRT 70 Gy); larynx (early glottic 63–66 Gy; voice preservation).
- **Thorax:** NSCLC (definitive 60–66 Gy + chemo; peripheral early-stage **SBRT** 45–60 Gy/3–5);
  SCLC (limited-stage 45 Gy BID concurrent; **PCI** 25 Gy/10 to responders).
- **Breast:** IDC (whole-breast 50/25 or hypofx 40–42.5/15 + boost; nodal levels I–III, IMN, SCV;
  left-sided → cardiac dose concern → DIBH); inflammatory (T4d, post-mastectomy + nodes).
- **GI:** esophagus (50.4 Gy + chemo); gastric (45 Gy adjuvant); pancreas (50.4 Gy); rectum (neoadjuvant
  long-course 50.4 + boost, or short-course 25/5; small bowel dose-limiting).
- **GU:** prostate (Gleason/Grade Group; 78–80 Gy or hypofx/SBRT 35–40/5; ± ADT; rectum/bladder OAR;
  **fiducials** common); bladder (tri-modality 64–66 Gy); RCC (radioresistant; SBRT for oligomets).
- **Gyn:** cervix (45 Gy pelvis + cisplatin + **brachytherapy to point A**, ~80–85 Gy EQD2 total);
  endometrium (vaginal-cuff brachy ± pelvic 45–50 Gy); ovarian (RT mostly palliative).
- **Lymphoma:** Hodgkin (ISRT 20–30 Gy consolidation; mediastinal mass); DLBCL (30–40 Gy to bulky/residual
  after R-CHOP).
- **Sarcoma:** STS (neoadjuvant 50 Gy or adjuvant 60–66 Gy; hematogenous → lung; nodes rare).
- **Pediatric:** rhabdomyosarcoma, Wilms (flank 10.8 Gy), neuroblastoma — RT de-escalated, risk-adapted.
- **Skin:** melanoma (RT mostly for mets/nodal); BCC/SCC (electrons; 50–70 Gy if RT primary).
- **Bone metastases** *(2027-named site)*: 30 Gy/10, 20 Gy/5, or **8 Gy ×1**; Batson plexus spread.

### 2F. PROCEDURES — Treatment Volume Localization (18) ★ closest to this trainer

- **CT simulation:** treatment-position scan; slice thickness 2–3 mm (SRS) to 3–5 mm; scan range;
  IV/oral contrast; metal artifacts.
- **3D vs 4D-CT:** 3D = static; **4D-CT** = phase-sorted volumes → motion management *(2027-emphasis)*.
- **Immobilization:** thermoplastic masks (repositioning < ~3 mm), breast board, vac-bag, headframe;
  reproducibility → smaller margins.
- **Reference marks / tattoos / isocenter:** India-ink tattoos at isocenter + reference points; isocenter
  = intersection of gantry/collimator/couch axes; three-plane laser alignment; record CT coordinates.
- **ICRU volumes (50/62/83):**
  - **GTV** = visible/palpable disease (no margin; 0 if resected).
  - **CTV** = GTV + microscopic-spread margin (site-specific; + elective nodes).
  - **ITV** = CTV + internal-motion margin (from 4D-CT; union of phases).
  - **PTV** = CTV/ITV + setup margin; van Herk recipe; smaller with IGRT.
  - **OAR / PRV** = organ + motion/setup margin.
- **IGRT modalities (this is the trainer's wheelhouse):**
  - **2D/2D planar kV** — orthogonal AP + Lat matched to **DRRs**; low dose; **bone match** or
    **fiducial match**; weak soft-tissue contrast. *(= the trainer's 2D/2D + prostate fiducial cases.)*
  - **MV portal / EPID** — treatment-beam imaging; lower contrast; declining.
  - **kV CBCT** — 3D volumetric; **soft-tissue match**; **6DOF** couch correction; cumulative dose.
    *(= the trainer's CBCT cases.)*
  - **Implanted fiducials** — gold seeds (prostate/pancreas/lung/liver); Calypso transponders.
  - **SGRT / optical surface** — zero dose; intrafraction monitoring; **DIBH** coaching.
    *(= the trainer's DIBH case.)*
- **Adaptive RT / re-sim:** triggered by weight loss / tumor shrinkage / filling changes.

### 2G. PROCEDURES — Prescription & Dose Calculation (24)

- **Prescription & specification:** ICRU reference point; total dose, dose/fraction, fractionation; beam
  energy selection (depth/penetration); beam modifiers (wedge angle, dynamic wedge).
- **Geometry:** field size/shape; **equivalent square = 2ab/(a+b)** (or 4·Area/Perimeter); depth;
  **SSD (→ PDD tables)** vs **SAD/isocentric (→ TMR/TPR tables)**.
- **Depth-dose functions:** **PDD** = dose(d)/dose(dmax) ×100 (SSD); **TMR/TPR** (SAD, distance-independent);
  **TAR** (historical).
- **Inverse square:** `D₂ = D₁ · (d₁/d₂)²` (distances d). **(See Flag #2 — fix notation.)**
- **MU calculation:**
  - SAD: `MU = Dose / (D₀ · TMR · Sc · Sp · WF · TF)`
  - SSD: `MU = Dose / (D₀ · PDD/100 · Sc · Sp · WF · TF)`
  - Electrons normalize at dmax.
- **Scatter:** collimator Sc (in-air, head scatter) vs phantom Sp; total Scp = Sc·Sp.
- **Modifiers:** wedge transmission factor; tray/block transmission; MLC.
- **Corrections:** tissue inhomogeneity (lung/bone — effective-depth / Batho / convolution).
- **Field junctions:** gap to avoid hot/cold spots at depth (e.g., craniospinal).
- **Electrons:** **R90 (therapeutic range) ≈ E/3.2–E/4 cm**; R50; Rp (practical range); dmax & range
  increase with energy.
- **Plan metrics:** Homogeneity Index, Conformity Index, DVH.

### 2H. PROCEDURES — Treatments (35)

- **EBRT techniques:** 3D-CRT; **IMRT** (fluence modulation, step-and-shoot vs sliding window);
  **VMAT** (continuous arc, fast); **SBRT/SRS** (few fx, high dose/fx, rigid immobilization, ±1–2 mm);
  **TBI** (~12 Gy/6 fx, lung shielding); **electrons** (superficial, dmax normalization).
- **Particle therapy:** protons — **Bragg peak / SOBP**, minimal exit dose.
- **Brachytherapy:** **HDR (Ir-192, T½ 74 d, stepping source)** vs **LDR (Cs-137 intracavitary, I-125
  permanent prostate seeds)**; applicators (tandem & ovoid / Fletcher-Suit; interstitial; intraluminal);
  **point A / point B**; ICRU 38/89. **(See Flag #3 — keep HDR=Ir-192, LDR=Cs-137 straight.)**
- **IGRT / verification at delivery:** portal imaging, CBCT, fiducial/soft-tissue match; **record-and-verify**
  systems and tolerances.
- **Machine operation:** linac beam generation; beam modifiers; daily setup workflow.
- **On-treatment management:** acute toxicity (mucositis/esophagitis/dermatitis/myelosuppression);
  imaging frequency vs margin trade-off; supportive care.

---

## 3. Accuracy corrections to resolve BEFORE authoring questions

The research agents were broadly accurate but introduced several errors typical of secondary sources.
**These must be fixed in the authored content — do not copy the raw agent text:**

1. **Dose limits — use US NRC/NCRP, not ICRP.** One agent cited ICRP figures (20 mSv/yr occupational,
   0.1 mSv/yr public, 1 mSv fetus). **ARRT tests NRC values:** occupational **50 mSv/yr (5 rem)**,
   cumulative **10 mSv × age (1 rem × age)**, public **1 mSv/yr (100 mrem)**, **embryo/fetus 5 mSv
   (0.5 rem) over the gestation, ~0.5 mSv/month** after declaration, lens 150 mSv/yr (older) → 50 mSv/yr,
   extremity/skin 500 mSv/yr. Author to NRC 10 CFR 20.
2. **Inverse-square notation.** An agent wrote `D₂ = D₁ × (D₁/D₂)²`; correct is
   `D₂ = D₁ × (d₁/d₂)²` where d = distances (the numeric example, 100 cGy→82.6 cGy at 110 cm, is right).
3. **HDR vs LDR isotopes.** "Cs-137 at 10–20 Gy/min" conflates sources. **HDR = Ir-192** (high dose rate);
   **Cs-137 = LDR intracavitary**; **I-125 = permanent prostate seeds**. Keep these distinct.
4. **Lung inhomogeneity worked example** in the dose agent's output is hand-wavy ("≈110–120 cGy").
   Qualitatively correct (less attenuation in lung → higher downstream dose) but the number is illustrative;
   recompute properly or present conceptually.
5. **Site dose/fractionation numbers vary by protocol/trial.** Always phrase as "a commonly used regimen,"
   cite NCCN/RTOG-NRG, and avoid implying a single correct dose. Good MCQ targets are the *relationships*
   (HPV→prognosis, left breast→cardiac→DIBH, SBRT=few-fx-high-dose) rather than exact cGy.
6. **Field-junction gap example** in the dose agent's output is muddled; re-derive `gap = (L/2)(d/SSD)`
   per field before using.
7. **"Bragg-Ionanescu model"** mentioned by the safety agent is not a real term — ignore; the LQ model and
   the Bragg peak are separate, correctly-described concepts.
8. **2027-tagged additions** are inferred from ARRT news posts, not the verified PDF. Tag them
   `blueprint: "2027"` in data and keep them OFF in the scored mock until the PDF is diffed.

**Recommended gate:** every authored question carries a `source` field; a radiation-therapy SME (or the owner,
who is RT-credentialed) signs off per subcategory before it enters the scored mock pool.

---

## 4. Implementation plan (for when we build — not now)

Matches existing conventions: no build step, static files, large data in a separate cacheable `.js`,
gated by `clerk-auth.js`, progress in Clerk `unsafeMetadata`.

### New files
- **`review.html`** — `<body data-require-auth>` gated hub; loads `clerk-auth.js`; self-contained
  markup/styles + a small `RTReview` controller reusing trainer design tokens. Four modes (tabs):
  1. **Study Guides** — one short page per subcategory (8).
  2. **Flashcards** — flip cards, filter by category, shuffle.
  3. **Quiz** — choose category or "mixed," N MCQs, instant grading + **explanations**, per-category score.
  4. **Mock Registry Exam** — 100–200 items **sampled to the 23/25.5/51.5% blueprint weights**, timed,
     scaled-score-style readout + per-category breakdown.
- **`review_data.js`** — the bank: `{ guides, flashcards, questions }` keyed by `cat`/`sub`. Each question:
  `{ id, cat, sub, stem, choices[], answer, explanation, source, blueprint:"current"|"2027", difficulty }`.
  Auto-`noindex` via the existing `robots.txt` `/*_data.js$` rule + `vercel.json` `X-Robots-Tag`.

### Edited files
- **`robots.txt`** — add `Disallow: /review` (gated, like `/trainer`, `/subscribe`).
- **`clerk-auth.js`** — extend `unsafeMetadata.rt` with a `review` block (quiz attempts, best mock %,
  per-category mastery, flashcards seen), reusing the existing debounced `save`/`flush` store.
- **`trainer.html`** — start-screen **"📚 Registry Review"** entry; surface review progress in the dashboard.
- **`index.html` / `subscribe.html`** — marketing: list registry prep as a subscription benefit.
- **`vercel.json`** — `cleanUrls` already maps `/review` → `review.html`; confirm headers inherit.

### Content volume target (v1, full-blueprint-shallow)
Weighted to the blueprint so the mock can sample realistically:

| Subcategory | Guides | Flashcards | MCQs (v1) |
|---|---|---|---|
| Patient Interactions & Mgmt | 1 | ~15 | ~20 |
| Patient & Medical Record Mgmt | 1 | ~10 | ~12 |
| Radiation Physics & Radiobiology | 1 | ~15 | ~18 |
| Radiation Protection, Equip & QA | 1 | ~18 | ~22 |
| Treatment Sites & Tumors | 1 | ~18 | ~20 |
| Treatment Volume Localization | 1 | ~14 | ~16 |
| Prescription & Dose Calculation | 1 | ~14 | ~18 (incl. worked calcs) |
| Treatments | 1 | ~20 | ~26 |
| **Total** | **8** | **~124** | **~152** |

### Legal / trademark guardrail (every page)
"ARRT®" and "Registry" are trademarks of the American Registry of Radiologic Technologists. **Disclaimer
required:** *not affiliated with, endorsed by, or sponsored by ARRT; original practice questions, not actual
exam items; educational use only.* Mirror the existing training-simulator disclaimer style.

### Suggested phasing
1. **Scaffold** — `review.html` shell, 4-mode UI, `review_data.js` schema, gating, progress store; seed
   **one fully-built subcategory** (recommend **Treatment Volume Localization** — strongest tie to the trainer).
2. **Content fill** — author the other 7 subcategories per §2, applying the §3 corrections; SME sign-off.
3. **Mock exam + polish** — blueprint-weighted sampler, timer, scaled-score readout, entry points,
   marketing copy, disclaimer.

---

## 5. Authoritative sources (corroboration base)

**Standards / official**
- ARRT exam content specs & exam info — arrt.org (links in §1)
- ICRU Reports 50, 62, 83 (target volumes / dose reporting); ICRU 38/89 (brachytherapy) — icru.org
- AAPM Task Groups: TG-51 (reference dosimetry), TG-66 (CT-sim QA), TG-71 (MU calc), TG-76 (respiratory
  motion), TG-100, TG-101 (SBRT), TG-142 (linac QA), TG-168 (IGRT), TG-179 (CBCT) — aapm.org
- NCRP Report 151 (shielding); US NRC 10 CFR 20 (dose limits); CDC (ALARA, infection control, ARS)
- AJCC Cancer Staging Manual, 8th ed.; NCCN Clinical Practice Guidelines
- ASRT Practice Standards & Code of Ethics; ARRT Standards of Ethics

**Textbooks**
- Khan & Gibbons, *The Physics of Radiation Therapy*
- Washington & Leaver, *Principles and Practice of Radiation Therapy* (6th ed.)
- Gunderson & Tepper, *Clinical Radiation Oncology*
- Bentel, *Radiation Therapy Planning*

> Full per-topic source URLs from the four research passes are preserved in the session transcript and should
> be migrated into each question's `source` field during authoring. The official ARRT spec PDF must be
> human-downloaded and diffed against §2 before launch (the 403 prevented automated verification of exact
> subtopic wording and the 2027 changes).

---

## 6. Open questions for the owner (before building)
1. **Mock-exam length** — full 200 to mirror the real exam, or a 100-item "half" plus the option to go full?
2. **Calculation questions** — include worked MU/equivalent-square/BED items in v1 (needs a tiny formula
   renderer), or defer calc-heavy items to v2?
3. **SME sign-off** — will you (RT-credentialed) review each subcategory's items, or should we line up an
   external reviewer before the scored pool goes live?
