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
  - `*3d_data.js` (brain, breast, pelvis, spine) — 3D CT volume datasets for CBCT (data-URI atlases).
  - `*3d_labels_data.js` — structure/label volumes for CBCT contours.
  - `drr/*.png` — DRR images.
  - `assets/fonts/` — self-hosted web fonts.
- `generate_brain_contours.py` — offline helper that generated brain contour data.
- `generate_lung_contours.py` — offline helper that injects the synthetic RLL nodule into the
  thoracic CT and writes `lung3d_data.js` + `lung3d_labels_data.js` (needs numpy/scipy/pillow).
- `generate_prostate_fiducials.py` — offline helper that implants 3 gold fiducials in the pelvis
  plan's prostate and writes `prostate3d_data.js` + `prostate3d_labels_data.js` (numpy/scipy/pillow).
- `generate_prostate_2d.py` — offline helper that ray-sums the pelvis CT into kV-style AP + Lateral
  radiographs and emits the planning fiducial triad → `prostate2d_data.js` (the 2D/2D fiducial case).
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
- `generate_sarcoma.py` — offline helper that ingests a **TCIA Soft-tissue-Sarcoma** patient (extremity CT + a `GTV_Mass` RTSTRUCT) and writes `sarcoma3d_data.js` + `sarcoma3d_labels_data.js` for the **Soft-tissue sarcoma** case (`VOLCASE.sarcoma`, `cbct:sarcoma` `CASE_TOL` 2 mm/2°, `SARCOMA_STRUCTS`). Unusual limb anatomy (thigh) — real tumour target, femur as the bony landmark. ROI map skips `GTV_Edema` (else the generic `gtv` alias folds it into the mass); body mask keeps the largest connected component and zeroes outside it to drop the CT couch. Built from patient `STS_004` (picked by an ultracode workflow over 5 candidates for tumour clarity/framing) via the **IDC** bucket `s3://idc-open-data`. **Licence CC BY 3.0** — attribute `doi:10.7937/K9/TCIA.2015.7GO2GSKS`, baked into the data-file headers. Files committed, `.vercelignore`d, in the **three Phase-2 allowlists**; re-run the **"Upload data to Blob" Action** after merge.
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
    rotation is a realistic **2–3.5°/axis** (compounding to ~4–6° total, scaled up if needed to exceed
    the accept tolerance so rotation is always required — not solvable by translation alone). `check()`
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
    for the IAC match), breast 40/400, spine 80/700 (this volume's bone only reaches ~370 HU, so
    the old 400/1800 bone window crushed it flat). HU model: `HU = density*(2000/255) - 500`,
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

- **2D/2D:** Brain · Pelvis · Thorax (CT DRR) · Breast L (monoisocentric SCV + medial-tangent, Varian-style)
  · **Breast L · DIBH** (breath-hold coaching → the same SCV+tangent match).
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
- **CBCT:** Pelvis · Acoustic neuroma (vestibular schwannoma IAC SRS) · Breast (real 3D CT, MPR + contours)
  · Spine SBRT (T7 vertebral target, cord-avoiding PTV) · Lung SBRT (peripheral RLL nodule, **off-bone**) ·
  Prostate (gold fiducial markers, **rigid**):
  - Lung SBRT — a **synthetic**, irregular/spiculated soft-tissue lesion baked into the thoracic CT via
    `generate_lung_contours.py` (`lung3d_data.js` + `lung3d_labels_data.js`); match the soft-tissue target.
  - Prostate — 3 **gold fiducial markers** implanted in the prostate of the existing pelvis plan, baked
    in via `generate_prostate_fiducials.py` (`prostate3d_data.js` + `prostate3d_labels_data.js`, reuses
    the pelvis volume + its prostate/PTV/bladder/rectum/SV labels, adds a `fiducial` bit 32 for the seed
    voxels + a `fidctv` bit 64 = a **0.5 cm contour** around the seeds). The seeds are bright baked voxels;
    the case is a **rigid 6DOF** match (no `offBone` config, so the seeds move with the bone and render as
    plain trilinear-sampled CT — maximally stable). The off-bone-drift variant was removed at the owner's request.
  - **Off-bone differential motion (config-driven; lung only today):** the target moves independently of
    the skeleton, so a bony match leaves it off — only matching the soft-tissue target / fiducials scores.
    Each off-bone case carries a `VOLCASE[case].offBone` config (`driftBit`, `hideDens`, `drawDens`, per-axis
    `drift` ranges mm, plus `okMsg`/`hint`/`setup` strings); `curOffBone()` returns it. `randomize()` picks a
    hidden `targetDrift` {x,y,z} (mm) on top of the usual 6DOF error (lung drift is larger; prostate is "a
    little off bone"). The CBCT (moving) reslice composites two passes: **hides** the planning-position
    feature (overwrites the `driftBit` voxels with `hideDens` — lung air 4 / prostate soft-tissue 70) and
    **redraws** it sampled through the residual *net − drift* transform (`movInvFrom`) at `drawDens`
    (lesion HU 74 / gold 255). Occupancy is **trilinear** (`gtvOcc`, density blended by fractional
    coverage) so the feature has soft edges and moves fluidly with the couch — nearest-neighbour
    (`gtvAt`) shimmered/popped, which made small seeds finicky. `check()` grades a **target/fiducial match**:
    translations against `e − targetDrift`, with the 6DOF **rotations shown but not graded**, so acceptance
    is translation-only; the bones-aligned-but-target-off `hint` comes from the config. Other cases keep
    `targetDrift` `null` (no `offBone` config) so they stay pure rigid 6DOF.

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
