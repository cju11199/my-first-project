# RT Image Matching Trainer — project memory

Interactive **RT Image Matching Trainer** for radiation-therapy students: practice aligning
treatment-setup imaging (portal/CBCT) to reference data, like a real treatment setup.
Live at **https://rtimagematch.com** (landing) → **/trainer** (app).

> Training simulator, educational use only. Not for clinical decisions. All offsets/values are fictional.

## Stack & hosting

- **Plain static site, no build step.** All files served from the repo root by **Vercel**.
- Pushes to `main` auto-redeploy; PRs get preview URLs. See `DEPLOY.md`.
- `vercel.json`: `cleanUrls` (so `/trainer` → `trainer.html`), security headers
  (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`), and caching
  (png/woff2 cached 1d + SWR; `.js` and the HTML pages `must-revalidate`).
- Custom domain `rtimagematch.com` on Vercel; DNS + email on Cloudflare.

## File map

- `index.html` — marketing **landing page** (`/`), with pricing and a **"See it in action"**
  product-screenshot section (`#see`).
- `assets/shots/` — trainer product visuals, generated headless and used on the landing + `/subscribe`
  (since the trainer is gated, these are how prospects see the product): `trainer-cbct.gif` (a looping
  CBCT 6DOF match converging — the landing-`#see` hero, also on `/subscribe`), plus `trainer-2d2d.webp`,
  `trainer-dibh.webp` (Breast L · DIBH breath-hold coaching — the RPM gating trace; on the landing `#see`
  strip **and** the `/subscribe` 2×2 strip, replacing the older `trainer-fiducial.webp`, which is kept in
  the repo but no longer referenced) and `trainer-progress.webp` stills. WebP cached like png in
  `vercel.json`. The GIF was built with Pillow (shared 96-colour palette to avoid flicker, ~600 px,
  single loop file ~0.6 MB). `trainer-dibh.webp` was captured headless (Puppeteer driving the DIBH case
  via `window.DIBH._dbg` to a steady in-gate breath-hold; 1600×975).
- `trainer.html` — the **trainer app** (`/trainer`). ~220 KB single file: markup + styles + all
  app logic. `<body data-require-auth>` so the auth gate protects it.
- `assets/truebeam/` — **interactive 3D Varian TrueBeam** (WebGL/three.js), a procedural low-poly
  (~2 k tri) model used by a standalone preview page **and** the trainer's **3D Machine View**.
  An **open C-arm** linac (NOT a CT bore): compact rounded white gantry + yoke arm, large rounded
  head with the beige collimator/accessory tray, kV source/imager + MV/EPID arms, and a stepped
  metallic 6DOF couch — all named, hinged parts pivoting through isocenter (IEC 61217, iso at origin,
  metres). `truebeam-model.js` is the framework-agnostic builder (pure-function `drivers` + `setPose`,
  educational beam-line/axis/iso overlays + colour-coded `readout()`); `truebeam-viewer.js` is the
  three.js runtime (OrbitControls, **pause-when-hidden**, render-on-demand) shared by `preview.html`
  and the trainer. `export-glb.mjs` (+ `_three-resolve-hook.mjs` + `utils/`) bakes `truebeam.glb`
  **browser-free** via GLTFExporter against the **vendored** three.js (`vendor/`, r160, MIT); the
  committed `.glb` is valid glTF v2 (KHR_materials_unlit + emissive, named nodes). `kinematics.test.mjs`
  is a committed regression (perpendicular SAD = 1.0000 m at all gantry angles, gantry sign, iso
  invariant under full couch 6DOF). **Trainer wiring:** an inline importmap maps bare `three` →
  vendored module (CSP-safe, `script-src 'self'`); a **3D Machine** start-screen card + a header **3D**
  button (both 2D & CBCT screens) open a `.modal-bg` (`#tb3dModal`, z-index 280) that lazy-imports the
  viewer. It **binds live to the active case** — 2D reads `CONSOLE._dbg.state()` (gantry + couch cm,
  relative to the plan baseline); CBCT reads `CBCT._dbg.shift()` (6DOF mm/deg, so `window.CBCT=CBCT`
  was exposed) — else free-orbits as an explorer with pose presets. Model + `.glb` render verified
  headlessly; live in-trainer tracking still wants a real-browser check (like every 3D/canvas feature).
- `subscribe.html` — Clerk pricing table / checkout (`/subscribe`); shows a trainer-screenshot strip above the table.
- `account.html` — self-service **account & billing** page (`/account`). Mounts Clerk
  `mountUserProfile` (profile · security · **billing**: update card / cancel) themed dark via the
  `appearance` API. Gated on **sign-in only** (not an active subscription) so lapsed subscribers can
  still reach billing; shows a "Start your free trial" banner when `!hasActiveSub()`. Reached from
  the trainer start-screen **⚙ Account** link, the progress dashboard Settings tab, and the landing footer.
- `terms.html`, `privacy.html` — legal pages (`/terms`, `/privacy`; NY governing law,
  `support@rtimagematch.com`).
- `clerk-auth.js` — client-side auth + billing gate (loaded by all pages).
- **Content / SEO guides (indexable):** `guides/index.html` (`/guides` hub) plus seven articles —
  `guides/igrt-image-guided-radiation-therapy.html` (the "what is IGRT" primer / start-here),
  `guides/cbct-6dof-registration.html`, `guides/2d-2d-portal-vs-drr-matching.html`,
  `guides/couch-shifts-6dof-corrections.html`, `guides/prostate-fiducial-marker-matching.html`,
  `guides/kv-vs-mv-imaging-radiation-therapy.html` (kilovoltage vs megavoltage setup imaging — OBI/EPID,
  planar vs CBCT), and `guides/dibh-deep-inspiration-breath-hold.html` (deep-inspiration breath-hold
  cardiac sparing + RPM gating, ties to the Breast L · DIBH case).
  On-brand static pages (no auth) with `TechArticle` + `FAQPage` + `BreadcrumbList` JSON-LD, linked
  from the landing nav/footer, cross-linked to each other (`.next` related-guide cards) and `/trainer`.
  Built as the organic content layer (the trainer itself can't be indexed — it's gated). All seven
  are in `sitemap.xml`. When adding a guide: copy an existing one's `<head>`/CSS verbatim, add it to
  the hub grid + sitemap, and cross-link it from the related guides.
- **SEO:** `robots.txt` (points to sitemap; disallows gated `/trainer` + `/subscribe`),
  `sitemap.xml` (homepage + `/guides` hub + the seven guide articles; legal pages are `noindex`),
  `favicon.svg`, and `og-image.png` (1200×630 share card, regenerated from an HTML template via
  headless Chromium). The landing page carries canonical, Open Graph/Twitter tags, and JSON-LD
  (`WebApplication` + `Organization` + a `FAQPage` mirroring the on-page `#faq` accordion).
  Only `/` + `/guides*` are indexable; trainer/subscribe/legal pages are `noindex`. Vercel
  auto-`noindex`es preview deployments, so canonical URLs are absolute `https://rtimagematch.com/...`.
- **Interim case-data guard (until Phase 2 / R2):** `robots.txt` disallows `/*_data.js$` + `/drr/`
  and `vercel.json` adds `X-Robots-Tag: noindex` for `*_data.js` + `/drr/*` (keeps the raw assets out
  of search without touching the indexable marketing pages). `middleware.js` (Vercel Edge Middleware,
  needs the lone `package.json` dep `@vercel/edge`) is a **hotlink/direct-download speed bump**: it
  allows same-origin subresource loads (`Sec-Fetch-Site`), blocks cross-site hotlinks / direct
  navigations / non-browser fetches (curl), and **fails open** on anything ambiguous so it can't
  break a real session. Headers are spoofable — this is NOT subscription enforcement (that's Phase 2);
  it just stops casual scraping. `allow()` is exported for unit-testing the truth table.
- **Case data (large, loaded on demand), kept out of HTML for caching:**
  - `image_data.js` (~4.3 MB), `breast_drr_data.js` — embedded DRR/portal images for 2D/2D.
  - `prostate2d_data.js` (~140 KB) — kV-style AP + Lateral pelvis radiographs (ray-sum of the pelvis
    CT) + planning fiducial-triad geometry for the 2D/2D prostate fiducial-match case (`PROSTATE2D`).
  - `*3d_data.js` (brain, breast, cervix, pelvis, spine, …) — 3D CT volume datasets for CBCT (data-URI atlases).
  - `*3d_labels_data.js` — structure/label volumes for CBCT contours.
  - `drr/*.png` — DRR images.
  - `assets/fonts/` — self-hosted web fonts.
- `generate_brain_contours.py` — offline helper that generated brain contour data.
- `generate_lung_contours.py` — offline helper that injects the synthetic RLL nodule into the
  thoracic CT and writes `lung3d_data.js` + `lung3d_labels_data.js` (needs numpy/scipy/pillow).
- `generate_spine_cbct.py` — offline helper that **rebuilds the CBCT Spine SBRT case**
  (`spine3d_data.js` + `spine3d_labels_data.js`) from the **same full-res chest CT as the 2D Spine
  case** (TCIA NSCLC-Radiogenomics R01-076, 0.8 mm), replacing the older 2.2 mm atlas. Structures
  come from **TotalSegmentator** run on this exact CT (spinal_cord / esophagus / aorta / lung lobes /
  thoracic vertebrae); the **PTV** is synthesised as the T7 vertebra + 4 mm carved 2 mm around the
  cord (cord-avoiding SBRT PTV), and **body** is the largest thresholded blob. The volume is rebuilt at
  a **moderate 1.6 mm** (NOT the source 0.8 mm — the trainer reslices it live in-browser; full-res
  would be ~30 MB and janky). CT + masks are resampled onto a common 1.6 mm atlas grid in **world
  (patient) coordinates** via affines (LPS↔RAS handled), so any orientation/flip between the pydicom
  CT stack and the nibabel masks is correct; output matches the tiled-atlas format `decodeVol` /
  `_decodeSpineLabels` expect (z-major tiles, X=LR cols, Y=AP rows; bits vertebra1/ptv2/cord4/esoph8/
  aorta16/lung32/body64; `isoIdx` at the T7 centroid). Bumped `VOLCASE.spine` `win` to a real bone
  window (400/1800) now that HU is genuine. **This makes the CBCT Spine case the same patient as the 2D
  Spine case** (and a different patient than the old CBCT spine atlas). `spine3d_*` files were already
  in the three Phase-2 allowlists; **re-run the "Upload data to Blob" Action** after merge. Needs
  pydicom/nibabel/numpy/scipy/pillow + TotalSegmentator. Visual rendering verified headlessly (QC
  stills); live-trainer look needs a real-browser check.
- `generate_prostate_fiducials.py` — offline helper that implants 3 gold fiducials in the pelvis
  plan's prostate and writes `prostate3d_data.js` + `prostate3d_labels_data.js` (numpy/scipy/pillow).
- `generate_prostate_2d.py` — offline helper that ray-sums the pelvis CT into kV-style AP + Lateral
  radiographs and emits the planning fiducial triad → `prostate2d_data.js` (the 2D/2D fiducial case).
- `generate_femur_2d.py` — offline helper for the **2D/2D Femur** case: ray-sums a real thigh CT
  (TCIA **Soft-tissue-Sarcoma** `STS_004`, the same series as the CBCT sarcoma case) into bone-emphasised
  AP + Lateral DRRs of a **single femur** (the femoral shaft is the bony landmark; flat `tilt:null`
  orthogonal pair). Both thighs are in-frame, so it splits the volume at the low-density inter-leg gap
  and keeps only the side carrying the GTV (the bilateral projection is mirror-symmetric / the Lateral
  superimposes both legs otherwise), then crops z to a hip→knee window around the lesion. **Appends**
  `FEMUR_AP_SRC` + `FEMUR_LAT_SRC` to `image_data.js` (so the case rides the existing 2D infra — already
  in the Phase-2 allowlists; **re-run the "Upload data to Blob" Action** after merge so the updated
  `image_data.js` reaches the blob, or the femur DRRs 404). **Licence CC BY 3.0** — attribute
  `doi:10.7937/K9/TCIA.2015.7GO2GSKS`, baked into the appended header. Visual rendering verified
  headlessly (QC stills); live-trainer look needs a real-browser check.
- `generate_spine_2d.py` — offline helper for the **2D/2D Spine SBRT** case: ray-sums AP + Lateral
  bone-emphasised DRRs of the thoracic spine from a **full-resolution diagnostic chest CT** (TCIA
  **NSCLC-Radiogenomics** patient `R01-076`, the 0.8 mm "THINS" axial series). It masks to the body
  (drops couch/arms), crops in-plane to the torso and z to a thoracic window on the spine, converts
  HU→μ (two-segment, bone-emphasised) and ray-sums via the same Beer–Lambert path integral as the femur
  case. DRR quality is wrung from the **rendering** (`project()`/`render()`): the float path-integral is
  LANCZOS-upscaled in 32-bit **before** quantising (no posterisation of the soft-tissue→bone ramp), a
  per-view **percentile contrast stretch** (p45→p99.7) windows the overlapping thoracic soft tissue
  toward black so the vertebral column reads as the bright bony landmark, an **unsharp mask** crisps the
  end-plate/pedicle edges, and it renders at **768 px**. iso sits at a **mid-thoracic vertebra** (bone
  centroid in the posterior-central region). Writes `SPINE_AP_SRC` + `SPINE_LAT_SRC` to `image_data.js`
  (rides the existing 2D infra — already in the Phase-2 allowlists; **re-run the "Upload data to Blob"
  Action** after merge or the spine DRRs 404). Tight SBRT tolerance (`2d2d:spine` `CASE_TOL` 1 mm / 1°).
  Re-run is **idempotent** (strips its own prior block before re-appending); needs the DICOM re-downloaded
  from IDC (`s3://idc-open-data`, `idc-index`) into the scratchpad path. **Licence CC BY 3.0** — attribute
  `doi:10.7937/k9/tcia.2017.7hs46erv`, baked into the appended header. **NOTE:** this re-sourced the case
  off the original 2.2 mm CBCT spine atlas, so the 2D Spine case is now a **different patient** than the
  CBCT Spine case. Visual rendering verified headlessly (QC stills); live-trainer look needs a real-browser check.
- `generate_breast_clips.py` — re-runnable in-place editor for the Breast CBCT surgical clips: reads
  `breast3d_data.js` + `breast3d_labels_data.js`, erases the old large hard-edged density-255 clip blobs
  and re-stamps small (~3–4 mm) feathered bright cores at the same centroids, then rewrites label bit 64
  (clips) + recomputes bit 128 (clips + 5 mm). Shrinks the markers and softens the 255-vs-tissue cliff so
  the moving reslice shimmers/blooms less (needs numpy/scipy/pillow; browser-verify the canvas result).
- `generate_pancreas_cbct.py` — offline helper that ingests a **TCIA Pancreatic-CT-CBCT-SEG** patient
  (planning breath-hold CT DICOM series + RTSTRUCT) and writes `pancreas3d_data.js` +
  `pancreas3d_labels_data.js` (same tiled-atlas format as the other `*3d_*` files) for the **Pancreas
  CBCT** case (rigid 6DOF abdominal soft-tissue match; needs pydicom/numpy/scipy/pillow). The trainer
  plumbing (`VOLCASE.pancreas`, `cbct:pancreas` `CASE_TOL`, `PANCREAS_STRUCTS`, loaders + `cur*`
  switches) is wired and the **picker card is live**. Built from patient `Pancreas-CT-CB_037`
  (planning CT + `*_SDPC` RTSTRUCT) pulled from the **NCI Imaging Data Commons** bucket
  `s3://idc-open-data` (reachable even where the TCIA website is network-blocked; use the `idc-index`
  PyPI pkg, which also carries the authoritative per-collection licence). **Licence CC BY 4.0** —
  commercial use OK with attribution (`doi:10.7937/TCIA.ESHQ-4D90`), baked into the data-file headers.
  The collection is GI-OAR only (stomach/duodenum + small bowel; no target ROI), so the iso sits at
  the GI/pancreatic centroid; the generator crops the **superior-inferior** slab to the abdominal OARs
  but the **in-plane** (LR/AP) extent to the **body** mask (largest connected component, couch excluded)
  so the full patient cross-section stays framed — an OAR-based in-plane crop sliced the body off the
  edge. `pancreas3d_data.js`
  (~2.0 MB) + `pancreas3d_labels_data.js` are committed, `.vercelignore`d, and added to the **three
  Phase-2 allowlists** (`api/asset.mjs` `DATASETS`, `scripts/upload-to-blob.mjs`, `.vercelignore`); like
  every paid case they're served only through `/api/asset` from private Vercel Blob, so the **"Upload data
  to Blob" Action must be re-run** after merge or the case 404s live. Visual rendering still needs a real-browser check.
- `generate_vs_mr.py` — offline helper that ingests a **TCIA Vestibular-Schwannoma-SEG** patient
  (contrast-T1 GammaKnife planning **MR** series + its T1-Gd RTSTRUCT) and writes `acousticmr3d_data.js`
  + `acousticmr3d_labels_data.js` for the **MR Acoustic neuroma** SRS case (`VOLCASE.acousticMR`,
  `cbct:acousticMR` `CASE_TOL` 1 mm/1°, `ACOUSTICMR_STRUCTS`). **First MR case** (not CT): no HU model, so
  intensity is percentile-normalised to 0..255 and the `VOLCASE` entry carries `mr:true` (tuned `win`,
  no real HU). Real **tumour (TV)** target + **cochlea** OAR + skull/body from the RTSTRUCT; cropped to the
  IAC/CPA. Built from patient `VS-SEG-001` via the **IDC** bucket `s3://idc-open-data` (`idc-index`).
  **Licence CC BY 4.0** — attribute `doi:10.7937/TCIA.9YTJ-5Q73`, baked into the data-file headers. Files are
  committed, `.vercelignore`d, and in the **three Phase-2 allowlists**; re-run the **"Upload data to Blob"
  Action** after merge. (CT-only window presets aren't hidden for MR yet — minor follow-up.)
- `generate_liver_sbrt.py` — offline helper that ingests a **TCIA Colorectal-Liver-Metastases** patient
  (contrast CT + a **DICOM SEG** with `Liver` + `Mass` segments) and writes `liver3d_data.js` +
  `liver3d_labels_data.js` for the **Liver SBRT** case (`VOLCASE.liver`, `cbct:liver` `CASE_TOL` 2 mm/2°,
  `LIVER_STRUCTS`). **First SEG-sourced case** (not RTSTRUCT): `rasterize_seg()` reads the multi-frame
  segmentation via per-frame `ImagePositionPatient` + `ReferencedSegmentNumber`. Real **liver organ** +
  real **tumour (Mass)** target — no synthesis. These are wide arms-in-FOV abdominal CTs, so the crop
  frames on the **liver** (focus bbox + margin) for resolution, not the whole torso. Built from patient
  `CRLM-CT-1100` (48 cc met, 114-slice CT) via the **IDC** bucket `s3://idc-open-data`. **Licence CC BY 4.0**
  — attribute `doi:10.7937/QXK2-QG03`, baked into the data-file headers. Files committed, `.vercelignore`d,
  in the **three Phase-2 allowlists**; re-run the **"Upload data to Blob" Action** after merge.
- `generate_gbm_mr.py` — offline helper that ingests a **TCIA UPenn-GBM** patient (post-contrast T1
  "stealth" planning **MR** + a BraTS-style tumour **DICOM-SEG**) and writes `gbm3d_data.js` +
  `gbm3d_labels_data.js` for the **MR Glioblastoma** cranial case (`VOLCASE.gbm`, `cbct:gbm` `CASE_TOL`
  2 mm/2°, `GBM_STRUCTS`). **Second MR case** (after the acoustic neuroma) — reuses that pipeline:
  `mr:true` + `autoWin`, percentile-normalised intensity. **Target = GTV** = enhancing lesion +
  necrotic core (SEG segments *Enhancing Lesion* + *Necrosis*); peritumoral **edema** kept as a
  separate context structure. The SEG carries no body ROI, so the **body** structure is a smoothed
  **external head contour** derived from the MR (this is a full-head MR — skull/scalp/orbits/face all
  present; the mask is blur→threshold→close→fill→largest-CC→open→re-blur so the rendered outline is a
  clean rounded head boundary, not pixel-level fuzz). **SEG-sourced** like
  Liver, but the AIMI/CaPTk SEG is stored at a **180° in-plane orientation** vs the MR
  (`IOP=[-1,0,0,0,-1,0]`); `rasterize_seg()` detects the IOP sign vs the MR's and **flips rows/cols**
  so the labels land on the correct side (a same-orientation SEG is left untouched). Built from patient
  `UPENN-GBM-00019` (radiologist-corrected SEG) via the **IDC** bucket `s3://idc-open-data`. **Licence
  CC BY 4.0** — attribute `doi:10.7937/TCIA.709X-DN49`, baked into the data-file headers. Files
  committed, `.vercelignore`d, in the **three Phase-2 allowlists**; re-run the **"Upload data to Blob"
  Action** after merge. Reachable only from the **start-screen picker** (like the other recent CBCT
  cases — not the in-app dropdown). Visual rendering still needs a real-browser check.
- `generate_sarcoma.py` — offline helper that ingests a **TCIA Soft-tissue-Sarcoma** patient (extremity CT + a `GTV_Mass` RTSTRUCT) and writes `sarcoma3d_data.js` + `sarcoma3d_labels_data.js` for the **Soft-tissue sarcoma** case (`VOLCASE.sarcoma`, `cbct:sarcoma` `CASE_TOL` 2 mm/2°, `SARCOMA_STRUCTS`). Unusual limb anatomy (thigh) — real tumour target, femur as the bony landmark. ROI map skips `GTV_Edema` (else the generic `gtv` alias folds it into the mass); body mask keeps the largest connected component and zeroes outside it to drop the CT couch. Built from patient `STS_004` (picked by an ultracode workflow over 5 candidates for tumour clarity/framing) via the **IDC** bucket `s3://idc-open-data`. **Licence CC BY 3.0** — attribute `doi:10.7937/K9/TCIA.2015.7GO2GSKS`, baked into the data-file headers. Files committed, `.vercelignore`d, in the **three Phase-2 allowlists**; re-run the **"Upload data to Blob" Action** after merge.
- `generate_cervix_cbct.py` — offline helper that ingests a **CPTAC-UCEC** patient (contrast venous-phase
  pelvic CT + a radiologist **UTERUS** tumour-annotation RTSTRUCT) and writes `cervix3d_data.js` +
  `cervix3d_labels_data.js` for the **Gynae / Uterus** CBCT case (`VOLCASE.cervix`, `cbct:cervix` `CASE_TOL`
  4 mm/3°). This case **replaced the old Pelvis CBCT bony-match case** (which was nearly identical to the
  Prostate case — both rode the same prostate-centred pelvis volume); it is now the **free/demo CBCT case**
  (start-screen `free-case` badge + `api/asset.mjs` `PUBLIC_KEYS`, swapped from the pelvis files). The case
  uses the trainer's **default CBCT branch** (`CB_STRUCTS`/`decodeLabels`/`CERVIX3D_LABELS`/`CB_ISO_IDX`) —
  body + the real uterine tumour target, which reuses the generic **`tumor`** legend/contour slot (like
  liver/sarcoma), so no new legend HTML was needed. Rigid 6DOF soft-tissue match (register the uterus, not
  the bony pelvis). Body is thresholded from the CT (the annotation RTSTRUCT carries no external/OAR ROIs);
  the uterus outline-only contours are z-gap-filled into a solid target. The old pelvis slice-stack /
  `realPelvis` fallback machinery went **dormant** (no case key is `pelvis` anymore) — left in place, guarded
  and unreferenced. `pelvis3d_data.js`/`pelvis3d_labels_data.js` stay in the repo + allowlists as the
  regeneration source for the prostate cases. Built from patient `C3N-00872` (venous-phase series; the UTERUS
  annotation references that CT) via the **IDC** bucket `s3://idc-open-data`. **Licence CC BY 4.0** — attribute
  `doi:10.7937/k9/tcia.2018.3r3juisw`, baked into the data-file headers. Files committed, `.vercelignore`d, in
  the **three Phase-2 allowlists** (and `PUBLIC_KEYS` since it's the free case); re-run the **"Upload data to
  Blob" Action** after merge or the case 404s live. Visual rendering still needs a real-browser check.
- `generate_adrenal_cbct.py` — offline helper that ingests an **Adrenal-ACC-Ki67-Seg** patient (contrast
  abdominal CT + a tumour **DICOM-SEG**) and writes `adrenal3d_data.js` + `adrenal3d_labels_data.js` for the
  **Adrenal** CBCT case (`VOLCASE.adrenal`, `cbct:adrenal` `CASE_TOL` 3 mm/2°, `ADRENAL_STRUCTS`). The **third
  off-bone case** (after lung + prostate) and the chosen way to teach "register the target, not the spine" in the
  abdomen — a **liver-met** version was rejected because the met is **isodense** with liver (~23 HU, invisible),
  so the off-bone hide/redraw had nothing to show; an **adrenal mass sits in retroperitoneal fat** (~40 HU vs
  fat ~−80 HU), so the redraw reads with strong contrast, exactly like the lung-nodule-in-air case. SEG-sourced
  like liver (body thresholded from CT, real **Mass** target → generic **`tumor`** slot, no new legend HTML).
  **Off-bone** is config-driven in `VOLCASE.adrenal.offBone` (`driftBit:2`, `hideDens:50` fat, `drawDens:70`
  mass, SI/`Lng`-dominant respiratory drift `y:[4,7]`, capped ~5 mm in `randomize()`); `check()` grades
  translation against `e − targetDrift` (rotations shown, not graded). Its own non-default branch
  (`ADRENAL_LBL`/`ADRENAL_ISO_IDX`/`_decodeAdrenalLabels`/`_adrenalCtrCache`, `cur*` switches), mirroring
  sarcoma/hn. Patient **`Adrenal_Ki67_Seg_052`** was picked over patient 001's 5 mm venous series because its SEG
  is drawn on a **thin 1.25 mm** series → sharp, smear-free coronal/sagittal reformats. Reachable only from the
  **start-screen picker**. Via the **IDC** bucket `s3://idc-open-data`. **Licence CC BY 4.0** — attribute
  `doi:10.7937/1fpg-vm46`, baked into the data-file headers. Files committed, `.vercelignore`d, in the **three
  Phase-2 allowlists**; re-run the **"Upload data to Blob" Action** after merge or the case 404s live. Visual
  rendering still needs a real-browser check.
- `generate_hn_2d.py` — offline helper for the **2D/2D Head & Neck** case: ray-sums AP + Lateral
  bone-emphasised DRRs of the **whole head + neck** from a clean diagnostic head-and-neck CT (TCIA
  **TCGA-THCA** patient `TCGA-DE-A4MA`, "CT HeadNeck 3.0 B31s"; full cranial vault → cervical spine →
  shoulders, clean axial HFS uniform 1.5 mm, **no de-ID redaction box**). Cervical-spine / mandible /
  skull-base bony match (flat `tilt:null` orthogonal pair, rides the existing 2D infra like Femur /
  Spine 2D). Same Beer–Lambert + float-LANCZOS-upscale + percentile-stretch + unsharp render at 768 px,
  with an **anisotropic-spacing aspect correction** (z 1.5 mm vs in-plane 0.98 mm — render width is
  scaled by physical mm, not pixel count, or the skull comes out ~1.5× too wide) and a small black
  vertex margin so the head isn't flush to the top edge. **Appends** `HN_AP_SRC` + `HN_LAT_SRC` to
  `image_data.js` (idempotent — already in the Phase-2 allowlists; **re-run the "Upload data to Blob"
  Action** after merge or the DRRs 404). The source was picked by an **ultracode workflow** that swept
  IDC + external CC-BY databases for a clean full-head+neck box-free CT (the earlier varepop-apollo
  source had a de-ID box on the face). **Licence CC BY 3.0** — attribute `doi:10.7937/k9/tcia.2016.9zfrvf1b`.
  Visual rendering verified headlessly; live-trainer look confirmed in headless Chromium.
- `generate_hn_cbct.py` — offline helper for the **Head & Neck CBCT** case (`VOLCASE.hn`, `cbct:hn`
  `CASE_TOL` 3 mm/3°, `HN_STRUCTS`). **RE-SOURCED** off the original EAY131 / NCI-MATCH neck CT (which had
  non-uniform slice spacing + a partial-head FOV) onto **TCGA-THCA `TCGA-DE-A4MA`** — the SAME clean
  full-head patient as the 2D/2D H&N case — so the two H&N cases are now one patient, the FOV spans the
  full cranial vault through the neck, and there is no de-ID box. Clean uniform axial HFS, so the old
  non-uniform-Z resample + clean-run clipping is gone; the generator just body-masks, builds the target,
  crops a **generous head+neck slab** (`CROP_MARGIN_MM` 62 → near the full vault-to-thorax FOV so you can
  scroll higher/lower for context) + body in-plane, and isotropically resamples to the tiled-atlas format
  (`_decodeHNLabels`, bits body=1 / tumor=2 — unchanged). TCGA-THCA carries **no tumour RTSTRUCT/SEG**, so
  the soft-tissue target is **SYNTHETIC**: a **BILATERAL cervical-nodal PTV** (`synth_target`) — two
  **SEPARATE jugular-chain lobes** (levels **II–IV** both sides) flanking the airway/spine, carving out the
  **central airway** (connected-component detection + dilate) and a **posterior cord/vertebral-body
  keep-out** (cord-sparing). There is **no anterior midline bridge** — an earlier horseshoe bridge read as
  PTV "in front of the chin/neck", so the two chains are kept distinct (a common bilateral elective-neck
  look). Level-aware (II sup/narrow → III mid/widest → IV inf), Va nub optional, bounded to the **cervical
  SI window** `Z_FRAC` 0.30–**0.60** (NOT the whole head — the CT is the full vault; and the **0.60 top
  stops below the chin/oral-cavity**, where the head is narrow and the lobes would otherwise crowd the
  anterior midline), tapered SI caps, body-relative outer standoff, slight L/R jitter, keep-outs re-applied
  **after** z-smoothing. ~70 cc (vs the old ~3 cc unilateral node). The PTV is the single generic
  **`tumor`** slot (reuses the existing legend; iso = the PTV centroid).
  The **bilateral-PTV geometry was designed by an ultracode workflow** (radonc + geometry proposals →
  judge panel → synthesis). Rigid 6DOF daily-IGRT match over the real cervical-spine / mandible /
  skull-base bony anatomy; the synthetic PTV defines the iso/contour. Reachable only from the
  **start-screen picker**. Built from `TCGA-DE-A4MA` via the **IDC** bucket `s3://idc-open-data`.
  **Licence CC BY 3.0** — attribute `doi:10.7937/k9/tcia.2016.9zfrvf1b`, baked into the data-file headers.
  `hn3d_*` files were already `.vercelignore`d + in the **three Phase-2 allowlists**; **re-run the
  "Upload data to Blob" Action** after merge or the case 404s live. CBCT MPR rendering + bilateral
  contours verified in headless Chromium.
- Docs: `README.md`, `DEPLOY.md`, `PAYWALL.md`, `EMAIL.md`, `UNBLOCK.md`, `LICENSE`.

## The trainer app (trainer.html)

Two workflows, picked on the start screen:

- **2D / 2D** — orthogonal-pair (AP/PA + Lateral) portal-to-DRR matching. **5DOF** correction
  (Lat / Lng / Vrt / Roll / Pitch). Tools: **Color Wash**, **Spyglass**, **Contrast**.
  Drag to translate/rotate; **1/2/3** lock to a single axis ("couch lock"); **Ctrl+Z** undo.
  Contrast is applied per-image via `ctx.filter` in `drawRef`/`drawPor` so the letterbox
  background / vignette / crosshair / ring stay unaffected (#69).
  - **2D/2D fiducial match (Varian-style kV)** — the Prostate case (`CASES.prostate.fidMatch:true`)
    is a self-contained `FID2D` module, not a DRR overlay match. Two kV radiographs (AP + Lateral,
    ray-summed from the pelvis CT in `prostate2d_data.js`) show 3 gold seeds at a hidden **6DOF**
    offset; the user **drags a 3-marker triad** onto them in both views. **Plain drag** translates
    all three markers (Sup/Inf/Lat); **Ctrl/⌘+drag** moves the nearest single marker (adds rotation).
    A least-squares rigid fit (**Horn quaternion**, `fit()`) of plan→placed markers reads out the
    couch shift; the readout panel grows a **Yaw** row (`fidPanel`) so all 6DOF show. The hidden
    rotation is a realistic **3–5°/axis** (compounding to ~5–8.5° total, scaled up if needed to clear
    **twice** the accept tolerance so rotation is always required — a translate-only plain-drag solution
    can never seat all three markers, so at least one or two seeds **must** be Ctrl/⌘+dragged
    individually to rotate the triad). `check()`
    grades the **residual misregistration** `fit(M,Qtrue)`: accept = residual **rotation ≤ the case
    rotation tolerance** (`fidRotTol()` → the `2d2d:prostate` `CASE_TOL` entry's r1 = 3°) **and**
    residual translation ≤ the case translation tolerance (`fidTransTol()` → t1 = 2 mm). **Match time
    is not tracked for this case** (timer reads `⏱ —`, `timeMs:null`). The displayed shift is the *recovered correction*
    (coloured by overall match quality, not per-axis magnitude). `applyCase`/`resetShift`/
    `randomizeShift`/`checkMatch` route to `FID2D` when active; the normal drag/keyboard handlers
    and blend/contrast widgets are bypassed (`body.fid-mode`). **Zoom/pan**: `FID2D.geom()` honours
    `v.zoom`/`v.panX`/`v.panY` (the app's centre-anchored transform), so the standard wheel zoom (toward
    cursor), per-view zoom buttons (`.view-tools`) and zoom % label all work on the seeds; Shift+drag or
    middle-mouse pans. `enter()` resets `v.ready=false`+zoom/pan so 100% = true fit. `generate_prostate_2d.py` builds
    the radiographs (`mu**1.6` bone emphasis + gamma) and the triad geometry (spread in all 3 axes so
    the fit is well-conditioned in both projections).
- **CBCT** — 3D cone-beam registration in 3 planes (axial/coronal/sagittal) with **6DOF** couch
  correction (Lat / Lng / Vrt / Pitch / Roll / Yaw). Real 3D CT volumes via MPR reslice.
  - **Fusion**: orange (CT/reference) vs blue (CBCT/moving) overlay (#58, replaced additive blend;
    aligned with the 2D/2D Color Wash so reference = orange and moving = blue across all cases).
    MPR path colorizes via a `sepia → saturate(1.6) → hue-rotate → brightness(0.78)` CSS filter
    (CT `hue-rotate(-20deg)` → orange, CBCT `hue-rotate(180deg)` → blue); saturation is deliberately
    low so bright bone tints instead of blooming into a glowing halo (earlier `saturate(4)/(3)` glowed on bone).
  - **Spyglass**: lens revealing the other image; works on all cases; scrolls slices while active (#59).
  - **Crosshair** (#70): Varian-style 4-quadrant tool — draggable centre splits each pane;
    TL+BR = CT, TR+BL = CBCT for edge-matching. Grayscale (no fusion tint), all 3 panes.
    Exclusive with Fusion/Spyglass.
  - **Window/Level**: header toggle with side Level+Width sliders + presets (Soft Tissue, Bone,
    Abdomen, Lung, Cerebellum); affects only the CT, not the background. Each case opens at a
    per-case default `win:{l,w}` in `VOLCASE` (applied in `applyCase()`), tuned to that volume's
    actual HU histogram for best viewing on open: pelvis 40/460, brain 500/1500 (skull-base bone
    for the IAC match), breast 40/400, spine 400/1800 (standard bone window — the spine case was
    re-sourced from a full-res diagnostic chest CT with real cortical-bone HU). HU model: `HU = density*(2000/255) - 500`,
    `density<=0.5` = air → black.
  - **Contours**: per-structure show/hide; real label-volume contours.
  - **Pan** tool + middle-mouse drag; **Ctrl+R** cycles the primary view (Axial→Coronal→Sagittal);
    the plane rotated into the large left/primary pane is auto-**selected** (`cyclePrimary`→`select`).
  - **Fullscreen** one pane (per-pane ⛶ button or **F** on the selected pane) via `cbSolo` — the soloed
    pane fills the grid (`.cbct-panes.cb-has-solo` + `.cb-soloed`), like the 2D solo view. The
    couch-correction panel is **hidable** (`toggleCbShifts` + the SHIFTS tab) — it reuses the 2D
    `.shifts-collapsed` slide so the three panes reflow to full width.
  - Arrow-key nudge capped at 0.05 cm (0.5 mm)/press.
- Shared: blend sliders, isocenter reticle, live residual-error readout graded vs tolerance,
  **New Offset** generates a fresh setup error, match timer, **How to use** guide on start menu.

### Cases

- **2D/2D:** Brain · Pelvis · Thorax (CT DRR) · Femur (extremity DRR; femoral-shaft landmark) ·
  **Spine SBRT** (thoracic vertebral-column bony match, AP+Lat DRRs ray-summed from a full-resolution
  diagnostic chest CT — `generate_spine_2d.py`; tight 1 mm/1° tolerance) · **Head & Neck** (whole head +
  cervical-spine bony match, AP+Lat DRRs from a clean full-head CT — `generate_hn_2d.py`) · Breast L
  (monoisocentric SCV + medial-tangent, Varian-style) ·
  **Breast L · DIBH** (breath-hold coaching → the same SCV+tangent match).
  - **Enter-room / re-setup decision (Head & Neck case; CONSOLE) — BUILT but DISABLED for now.** The
    mechanism is fully in place but inert: `CONSOLE_PLANS.hn` intentionally OMITS its `resetup` config, so
    `CONSOLE.resetupCfg()` returns null → no gross offsets, the **ENTER ROOM** button stays hidden, and
    `applyShifts` never blocks (H&N is a plain orthogonal-pair bony match). To re-enable, restore
    `resetup:{ actionLimitMm:10, rotLimitDeg:3, grossChance:0.45 }` on `CONSOLE_PLANS.hn`. The dormant
    machinery: when a `resetup` config is set, `applyNewOffset2d` rolls GROSS vs correctable offsets; in
    MATCH the console shows an **ENTER ROOM** button (glows on `trueErrGross()`) and **APPLY SHIFTS is
    blocked + dimmed** on a gross error; `CONSOLE.enterRoom()` on a gross error repositions → ALIGNED, on a
    within-limit error gives corrective feedback. `CONSOLE._dbg` exposes `enterRoom`/`isGross`/`resetupCfg`/
    `setError` for headless tests.
  - **Directional "Move" guidance (all 2D cases; still active):** a live **"Move" line** in the control
    strip (`roomDirections()` → `refreshReadouts`) translates the dialed correction into plain patient
    directions (e.g. "RIGHT 0.4 cm · SUP 1.2 cm · POST 0.3 cm · ROLL CW 2°"), grounded in the file's
    Lat/Lng/Vrt sign conventions.
  - **Breast DIBH (`DIBH` module):** button-driven deep-inspiration breath-hold coach docked as a **strip
    at the bottom of the 2D/2D match screen** (`#dibhStrip`, inside the `.match-col` wrapper that now holds
    `.views` + the strip), *not* a separate overlay — the RPM-style amplitude trace (cm) animates beside the
    image panes. A shaded gating band `[GATE_LO,GATE_HI]` shows the window; the live line is **green in-gate /
    amber out**. The patient model is **fully random each acquisition** (no preset scenarios): `randomizePatient()`
    rolls `pInhaleTarget` (the natural full-inhale level — **usually OUTSIDE the gate**, ~50% over / ~32% under /
    ~18% in, so the first breath rarely lands in-window and the student must coach with the "a little" nudges),
    `pDrift` (hold sag), `pNoise`, and a ~40% `pCough` risk. The breath is driven by a **stiff spring (`SPRING_K`)**
    so the patient reacts quickly to each command. **Coaching commands** (`cmd(...)`, voice or fallback buttons):
    `'in'` (deep breath in → rises to `pInhaleTarget`, auto-settles into a hold), `'hold'` (lock at the current
    amplitude — catches a rising breath mid-inhale), `'up'`/`'down'` (nudge the hold ±`NUDGE`=0.2 cm to fine-tune
    into the gate), `'relax'` (back to free breathing), `'abort'`, and `'beam'` (button only).
    The **two breast fields are acquired separately**, each at its own breath-hold: **Beam On** (only valid
    while **in-gate AND settled**, `stable()`) starts a **timed exposure** (`EXPOSE_DUR≈1.3 s`) that the patient
    must **stay in-gate through** — drift out / cough / relax interrupts it (`failExposure`, penalty). A clean
    exposure captures the current field (`completeExposure` → reveals that view's portal), then re-randomizes
    the patient for the next field; once both are captured, `finishAcq()` computes a 0–100 coaching score and
    **unblocks the match**. The case is **voice-coached and mic-gated** (see DIBHVoice below): the **only on-screen
    button is `Beam On`** (`cmd('beam')`); the coaching commands `cmd('in'|'relax'|'abort')` (`'in'` = "Breathe In &
    Hold") are issued **by voice**. The three coaching buttons live in a hidden `#dibhCoachFallback` group that is
    revealed only if the mic fails mid-session. Gating
    hooks consumed by the core code: `DIBH.acquiring()` (blocks match drag in the `mousedown` handler +
    `checkMatch` until both fields acquired) and `DIBH.hidesPortal(key)` (in `drawPor`, hides each view's portal
    until its field is beamed); per-pane `.viewer-area.awaiting` badges show the un-acquired state.
    `CASES.breastDIBH` = a copy of `CASES.breast` (progress records separately). Entered from
    `launchCase('2d2d','breastDIBH')` (not the in-trainer dropdown) → `DIBH.enter()` (calls `applyCase('breastDIBH')`
    itself); `backToMenu()` calls `DIBH.exit()` (which also tears down voice). `_dbg` exposes the model for headless
    tests (`set`/`state`/`advance`/`beam`/`cmd`). Trace animation + the on-screen layout need real-browser
    (Chrome/Edge) verification — the model logic is headless-tested but visuals can't be.
  - **Voice coaching — Phase 2, BUILT (`DIBHVoice` module):** the Breast DIBH case is **VOICE-COACHED and gated on
    microphone availability** — coaching is done by speaking; `Beam On` is the only button. A thin **Web Speech API**
    adapter maps spoken phrases to `DIBH.cmd('in'|'hold'|'up'|'down'|'relax'|'abort')` (the SAME entry point the
    buttons use). The `COMMANDS` table carries many therapist phrasings — e.g. "take a deep breath in" → in, "hold" →
    hold, "breathe in a little"/"a little more"/"deeper" → up, "breathe out a little"/"a little less" → down, "breathe
    normally"/"breathe out" → relax. **`beam` is intentionally NOT a voice command** — delivery is a deliberate button
    press, so a stray/misheard word can't beam. **Access gate:** `launchCase('2d2d','breastDIBH')` blocks unless `DIBHVoice._possible`
    (`SpeechRecognition && isSecureContext && !standalone-PWA`) AND `requestAccess()` (a `getUserMedia({audio:true})`
    probe) grants a real mic; otherwise the start-card is `.locked` with a 🎤 and a note explains the requirement.
    On entry `DIBH.enter()` calls `DIBHVoice.begin()` to **arm push-to-talk** (the mic stays idle until held). The
    student coaches by **holding the mic button or the SPACE bar** to talk, and presses **ENTER** (or the Beam On
    button) to deliver — both keys handled in `onKeyDown`/`onKeyUp`, gated to `dibhAcquiring()`, with Space
    `preventDefault`ed (no scroll / focused-button activation) and a `spaceHeld` guard. **Hands-free** continuous
    listening is an opt-in checkbox (`onHandsfree`); `finishAcq()` calls `suspend()` to stop once both fields are
    acquired. The mic is released on every exit path: `DIBH.exit()`→`teardown()` (Menu), `pagehide`
    (close/navigate away), and tab `visibilitychange` (hidden → abort, shown → auto-resume only if it was hands-free)
    — so it never stays hot outside the case. User-initiated PTT starts reset `lastStart` so they fire immediately
    (the restart throttle only guards the hands-free auto-restart). **Lifecycle:** `recognizing` driven from
    `onstart`/`onend`; in hands-free Chrome stops on silence so `onend` respawns, but only while `dibhAcquiring()` and
    not after a terminal error; a sustained `network` outage tallies `netFails` and `degrade()`s after 4. **Phrase matching** is
    normalized substring + synonym/mishearing tables; `onresult` collects a candidate per recognition alternative and
    resolves by **safety/specificity priority `abort`→`down`→`up`→`hold`→`in`→`relax`** (abort always wins across
    alternatives; the specific "a little" nudges beat the generic in/relax so "breathe out a little" isn't read as
    "breathe out"); one action per
    utterance (per-utterance lock + `COOLDOWN`≥`idleTimer` + `isFinal` re-arm). **Degradation / safety net:** if the
    mic fails mid-session, `degrade()` reveals the hidden `#dibhCoachFallback` buttons (in/relax/abort) so the student
    is never stuck; terminal codes (`not-allowed`/`audio-capture`/`service-not-allowed`/`language-not-supported`/sustained
    `network`) route there. **No CSP or `Permissions-Policy` change is needed** (speech recognition is a JS API, not a
    fetched origin; mic Permissions-Policy defaults to `self` and the trainer is same-origin). `_match`/`_possible`
    are exposed for headless tests (the phrase matcher is unit-tested); live mic + recognition need real Chrome/Edge.
- **CBCT:** Gynae / Uterus (CPTAC-UCEC; real uterine tumour soft-tissue target — the **free/demo** CBCT case,
  replaced the old Pelvis bony-match case) · Acoustic neuroma (vestibular schwannoma IAC SRS) · Breast (real 3D CT, MPR + contours)
  · Spine SBRT (T7 vertebral target, cord-avoiding PTV) · Lung SBRT (peripheral RLL nodule, **off-bone**) ·
  Prostate (gold fiducial markers, **off-bone**) · Pancreas · Acoustic neuroma · MR · Liver SBRT ·
  Soft-tissue sarcoma · **Head & Neck** (TCGA-THCA `TCGA-DE-A4MA` clean full-head CT — SAME patient as the
  2D H&N case; daily-IGRT 6DOF match over the cervical spine/mandible/skull-base with a **synthetic bilateral
  cervical-nodal PTV** (two separate levels II–IV chains, cord/airway-sparing) — see `generate_hn_cbct.py`) ·
  **Adrenal · off-bone** (Adrenal-ACC-Ki67-Seg; an adrenal mass in retroperitoneal fat that drifts off the spine
  with respiration — the third off-bone case, register the mass not the vertebrae — see `generate_adrenal_cbct.py`) ·
  **Glioblastoma · MR** (UPenn-GBM post-contrast T1; cranial match on the enhancing GTV + necrotic core,
  with peritumoral edema; smoothed external head contour as body — see `generate_gbm_mr.py`):
  - Lung SBRT — a **synthetic**, irregular/spiculated soft-tissue lesion baked into the thoracic CT via
    `generate_lung_contours.py` (`lung3d_data.js` + `lung3d_labels_data.js`); match the soft-tissue target.
  - Prostate — 3 **gold fiducial markers** implanted in the prostate of the existing pelvis plan, baked
    in via `generate_prostate_fiducials.py` (`prostate3d_data.js` + `prostate3d_labels_data.js`, reuses
    the pelvis volume + its prostate/PTV/bladder/rectum/SV labels, adds a `fiducial` bit 32 for the seed
    voxels + a `fidctv` bit 64 = a **0.5 cm contour** around the seeds). The seeds are bright baked voxels
    (gold density 255, sized as ~5 mm solid blobs — `SEED_RMM` 3.6 — so the off-bone redraw samples them
    solidly; a single-voxel seed redrew faint, peak density ~100 vs 255). The case is **off-bone**: bladder/rectal
    filling shifts the prostate + seeds off the bony pelvis, so a bony match fails and the student must register
    the fiducials (`VOLCASE.prostate.offBone` config; see below).
    - **Bladder-filling simulation** (`offBone.fill`): a **Bladder** picker (`#cbFillSelect`, shown only for
      prostate) + each **New Offset** rolls a daily bladder-fill scenario — `empty` (`bladderScale` 0.62),
      `full` (1.30), `veryfull` (1.55). Each scenario renders the bladder at a different **SIZE at its own
      CONSTANT urine density** (NOT a density tint): in the MOVING CBCT only, the bladder label region (bit 4)
      is **scaled about the prostate/iso anchor** (`curIsoIdx()`) by `bladderScale`, so it grows superiorly/
      anteriorly *away* from the gland (a real bladder fills upward); the scaled region is painted at the
      bladder's `urine` density (~64), the prostate gland (bit 1) is **skipped** so the gold seeds are never
      covered, and an emptied bladder repaints the receded part of the planning bladder as soft tissue
      (`erase` 55). Drawn UNDER the seed hide/redraw so the seeds always render on top. Each scenario also sets
      a **deterministic `targetDrift`** matching the fill: a fuller bladder pushes the prostate **posterior/
      inferior** (+y/−z), an emptier one **anterior/superior** (−y/+z). |drift.y| ≥ 3 mm > the 2 mm tol and
      total ≤ 5 mm, so `randomize()` uses the scenario drift directly (no range-random/cap) and the case never
      starts already-accepted. `pendingFill` holds the picker selection (null = random each offset); `curFill`
      is the active scenario. Synthetic forward model on the single planning CT (the size change is a
      centroid-anchored label scale, not a real deformation). `lung` has no `fill` block, so it keeps the
      plain range-random drift.
  - **Off-bone differential motion (config-driven; lung + prostate):** the target moves independently of
    the skeleton, so a bony match leaves it off — only matching the soft-tissue target / fiducials scores.
    Each off-bone case carries a `VOLCASE[case].offBone` config (`driftBit`, `hideDens`, `drawDens`, per-axis
    `drift` ranges mm, plus `okMsg`/`hint`/`setup` strings); `curOffBone()` returns it. `randomize()` picks a
    hidden `targetDrift` {x,y,z} (mm) on top of the usual 6DOF error (lung drift is larger; prostate is "a
    little off bone"). The CBCT (moving) reslice composites two passes: **hides** the planning-position
    feature (overwrites the `driftBit` voxels with `hideDens` — lung air 4 / prostate soft-tissue 70) and
    **redraws** it sampled through the residual *net − drift* transform (`movInvFrom`) at `drawDens`
    (lesion HU 74 / gold 255). Occupancy is **trilinear** (`gtvOcc`, density blended by fractional
    coverage) so the feature has soft edges and moves fluidly with the couch — nearest-neighbour
    (`gtvAt`) shimmered/popped, which made small seeds finicky (so the prostate seeds are baked as ~5 mm
    solid blobs, not single voxels, to redraw cleanly). `check()` grades a **target/fiducial match**:
    translations against `e − targetDrift`, with the 6DOF **rotations shown but not graded**, so acceptance
    is translation-only; the bones-aligned-but-target-off `hint` comes from the config. Prostate drift is
    AP-dominant (`y:[3,5]`, always clearing the 2 mm fiducial tolerance) and total-capped at ~5 mm. Other
    cases keep `targetDrift` `null` (no `offBone` config) so they stay pure rigid 6DOF.

## Auth & paywall (clerk-auth.js)

Client gate using **Clerk** (auth) + **Clerk Billing** (Clerk owns the Stripe integration — no
Stripe code here). Plan key **`full_access`**: $9.99/mo, $72/yr, 3-day trial.

- **Host-detected keys:** production (`rtimagematch.com`) uses the **live** Clerk instance
  (`clerk.rtimagematch.com`, `pk_live_…`); localhost + `*.vercel.app` previews stay on the **dev**
  instance (`fancy-flounder-63.clerk.accounts.dev`, `pk_test_…`). Publishable keys are public by design.
- clerk-js is loaded as a **classic (no-cors) script** — no `crossOrigin` — because some
  AV/VPN HTTPS interceptors strip CORS headers and broke the gate (#66).
- Pages with `<body data-require-auth>` (the trainer) are bounced unless signed in **and**
  authorized for `full_access`.
- **Comp / free-access logic in `isComped()`:**
  - `COMP_USER_IDS` — Clerk user-id allowlist; **checked first** and unspoofable. The owner is
    comped here (full access, no subscription) via their Clerk user id.
  - `COMP_EMAILS` — exact-email allowlist (testers); now **empty**. Any entry must be a
    **VERIFIED** email on the account — an unverified address never grants access.
  - `COMP_DOMAINS` — whole-institution free access for students/staff: `stonybrook.edu`,
    `mountsinai.org` (#71). Requires a **VERIFIED** email at the domain or a subdomain
    (dot-boundary match, so `evilstonybrook.edu` does NOT match `stonybrook.edu`). Use
    institution domains only — a public domain like gmail.com would free everyone.
- `window.RTAuth` exposes `ready`, `hasActiveSub()`, `PLAN_KEY`, `TRAINER_URL` for page scripts
  (e.g. subscribe.html mounts `Clerk.mountPricingTable`).

**Important:** this is the CLIENT (UX) gate only. The hard paywall — serving the ~15 MB of case
data only to subscribers — is **Phase 2, not yet built** (see PAYWALL.md). The data files are
still public on the CDN today.

### Per-user accounts: progress, preferences & achievements

A per-user training profile that follows the account across devices. **No backend** — it persists
to the signed-in user's **Clerk `unsafeMetadata.rt`** (writable client-side, kept compact:
aggregates + a 24-entry recent ring).

- **`clerk-auth.js`** owns the store and exposes `window.RTAuth.profile`:
  `get()`, `save(mutator)` (debounced ~900 ms, merge-safe so it never clobbers other
  `unsafeMetadata` keys), `flush()` (also auto-flushed on `pagehide`/tab-hide), `isReady()`,
  `SCHEMA`. Profile is loaded in `start()` once the Clerk user is available.
- **`trainer.html`** has a self-contained `RTProfile` wrapper that uses `RTAuth.profile` when
  signed-in, else falls back to **`localStorage('rtProfile')`** (so the trainer still records
  progress ungated and in headless tests where `clerk-auth.js` is stubbed).
- **What's tracked** (`rtRecord(mode,caseKey,{accepted,mag,timeMs})`, called from both `checkMatch`
  (2D) and `CBCT.check`): per-case attempts/clears, **best time** + **best residual** (translation
  vector magnitude, mm), totals, **XP & level** (`level = floor(sqrt(xp/40))+1`), a **daily
  streak**, a recent ring, and a **13-badge achievement** catalogue (`RT_ACH`, evaluated each
  attempt, awarded once). XP rewards accepts/first-clears/speed(<30 s)/precision(<0.5 mm)/**case
  tightness** (tighter accept tol → bonus; the `strict` badge clears any case with t1 ≤ 1 mm).
- **Match tolerances are per-case, not a user setting:** `CASE_TOL` (keyed `mode+':'+caseKey`) →
  `rtTol(mode,caseKey)` returns `{t1,t2,r1,r2}` (translation accept/close mm, rotation accept/close °),
  threaded into both checkers + `FID2D` (via `fidRotTol()`/`fidTransTol()`). Anchored to clinical action
  levels — intracranial **SRS (`cbct:brain`) tightest (1 mm / 1°)**, spine SBRT 1 mm, lung SBRT / fiducial
  2 mm, conventional 3–5 mm (breast loosest); `RT_TOL_DEFAULT` is the fallback. The 2D hidden-offset floor
  is ≥ 6 mm so even the loosest case (breast t1 = 5) never starts already-accepted. (The old global
  `prefs.difficulty` relaxed/standard/strict selector + `RT_DIFF` were removed.)
- **Preferences** (`prefs`): a show-stats-on-cards toggle.
- **UI:** a start-screen **summary strip** (level bar · cleared count · streak → opens dashboard),
  per-case-card **cleared badges** (✓ + best time/residual) rendered in `pickMode`, an
  **achievement toast** (`#rtToast`) on unlock, and a **"Your Progress" dashboard modal**
  (`#rtProgModal`, reuses `.modal-bg`) with Overview (level ring + tiles + achievements), Cases
  (per-case tables) and Settings (display, Export JSON / Reset) tabs. All styling
  reuses the existing tokens; section headers are `text-transform:uppercase` (so `innerText`
  asserts come back upper-cased in tests).

## Email (EMAIL.md)

`support@rtimagematch.com` via **Cloudflare Email Routing** (forward-only / receive-only). To send
outbound as the address would require switching to a real mailbox (iCloud+ custom domain, Workspace, etc.).

## Conventions

- No framework, no build step. A minimal `package.json` exists only to supply the `@vercel/edge`
  dependency for `middleware.js` (the interim case-data hotlink guard); Vercel still serves the
  static files as-is (no build command). Phase 2's `/api` serverless functions will extend it.
- Keep `trainer.html` small: large data/images go in separate cacheable `.js`/asset files.
- Self-hosted fonts (no Google Fonts) and a CSP are part of the security/privacy hardening; if you
  add an external origin (e.g. Clerk domains), update the CSP accordingly.
- Per-image canvas filters (not whole-canvas CSS filters) so backgrounds/overlays stay clean.

## Dev tooling (`.claude/` + `scripts/`)

- **`/new-case` skill** (`.claude/skills/new-case/SKILL.md`) — the full add-a-case pipeline
  (IDC sourcing → generator → `trainer.html` wiring → 3 allowlists → build-verify → draft PR →
  post-merge Blob upload). Invoke it whenever adding a 2D/2D or CBCT case.
- **`/check-blob` skill** (`.claude/skills/check-blob/SKILL.md`) — verifies the allowlists are in
  sync and (re-)runs the "Upload data to Blob" Action. The standard **post-merge** step for a case.
- **`scripts/check-allowlists.mjs`** — no-deps checker that the `*_data.js` files match all three
  Phase-2 lists (`upload-to-blob.mjs`, `api/asset.mjs`, `.vercelignore`). Run it before any push.
- **Pre-push hook** (`.claude/settings.json` PreToolUse → `.claude/hooks/prepush-guard.mjs`) —
  before any `git push` it runs the allowlist check (always) + `build-trainer.mjs --out` (if the
  minify deps are installed) and **blocks the push** on failure, so a forgotten allowlist entry or
  a broken minify can't reach a PR.

## Status / next steps (Phase 2 — hard data lockdown)

Not started in code. Plan (PAYWALL.md): move case data to **Cloudflare R2**, add a Vercel
serverless `/api/asset` that verifies the Clerk session + `full_access` via `@clerk/backend`,
returns short-lived R2 **presigned URLs** for the big `.js` files (Vercel ~4.5 MB response limit
rules out proxying `image_data.js`) and **proxies** `drr/*.png` same-origin (canvas-taint/CORS),
rewire `trainer.html` loaders, and `.vercelignore` the data files. R2 env vars are stubbed in
`.env.example`. Phase 3 = connect real Stripe, switch Clerk to live, test a purchase, launch.

> Note: PAYWALL.md's "session handoff" section predates PRs #63–#71. Phase 1 (auth + billing gate,
> #62) is now **merged and live** with host-detected prod/dev keys; the owner allowlist and the
> `COMP_DOMAINS` institution free-access tier were added after.
