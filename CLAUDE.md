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

- `index.html` — marketing **landing page** (`/`), with pricing.
- `trainer.html` — the **trainer app** (`/trainer`). ~220 KB single file: markup + styles + all
  app logic. `<body data-require-auth>` so the auth gate protects it.
- `subscribe.html` — Clerk pricing table / checkout (`/subscribe`).
- `account.html` — self-service **account & billing** page (`/account`). Mounts Clerk
  `mountUserProfile` (profile · security · **billing**: update card / cancel) themed dark via the
  `appearance` API. Gated on **sign-in only** (not an active subscription) so lapsed subscribers can
  still reach billing; shows a "Start your free trial" banner when `!hasActiveSub()`. Reached from
  the trainer start-screen **⚙ Account** link, the progress dashboard Settings tab, and the landing footer.
- `terms.html`, `privacy.html` — legal pages (`/terms`, `/privacy`; NY governing law,
  `support@rtimagematch.com`).
- `clerk-auth.js` — client-side auth + billing gate (loaded by all pages).
- **Content / SEO guides (indexable):** `guides/index.html` (`/guides` hub) plus articles
  `guides/cbct-6dof-registration.html` and `guides/2d-2d-portal-vs-drr-matching.html`. On-brand
  static pages (no auth) with `TechArticle` + `FAQPage` + `BreadcrumbList` JSON-LD, linked from
  the landing nav/footer and cross-linked to each other and `/trainer`. Built as the organic
  content layer (the trainer itself can't be indexed — it's gated).
- **SEO:** `robots.txt` (points to sitemap; disallows gated `/trainer` + `/subscribe`),
  `sitemap.xml` (homepage only — legal pages are `noindex`), `favicon.svg`, and `og-image.png`
  (1200×630 share card, regenerated from an HTML template via headless Chromium). The landing page
  carries canonical, Open Graph/Twitter tags, and JSON-LD (`WebApplication` + `Organization`).
  Only `/` is indexable; trainer/subscribe/legal pages are `noindex`. Vercel auto-`noindex`es
  preview deployments, so canonical URLs are absolute `https://rtimagematch.com/...`.
- **Case data (large, loaded on demand), kept out of HTML for caching:**
  - `image_data.js` (~4.3 MB), `breast_drr_data.js` — embedded DRR/portal images for 2D/2D.
  - `*3d_data.js` (brain, breast, pelvis, spine) — 3D CT volume datasets for CBCT (data-URI atlases).
  - `*3d_labels_data.js` — structure/label volumes for CBCT contours.
  - `drr/*.png` — DRR images.
  - `assets/fonts/` — self-hosted web fonts.
- `generate_brain_contours.py` — offline helper that generated brain contour data.
- `generate_lung_contours.py` — offline helper that injects the synthetic RLL nodule into the
  thoracic CT and writes `lung3d_data.js` + `lung3d_labels_data.js` (needs numpy/scipy/pillow).
- Docs: `README.md`, `DEPLOY.md`, `PAYWALL.md`, `EMAIL.md`, `LICENSE`.

## The trainer app (trainer.html)

Two workflows, picked on the start screen:

- **2D / 2D** — orthogonal-pair (AP/PA + Lateral) portal-to-DRR matching. **5DOF** correction
  (Lat / Lng / Vrt / Roll / Pitch). Tools: **Color Wash**, **Spyglass**, **Contrast**.
  Drag to translate/rotate; **1/2/3** lock to a single axis ("couch lock"); **Ctrl+Z** undo.
  Contrast is applied per-image via `ctx.filter` in `drawRef`/`drawPor` so the letterbox
  background / vignette / crosshair / ring stay unaffected (#69).
- **CBCT** — 3D cone-beam registration in 3 planes (axial/coronal/sagittal) with **6DOF** couch
  correction (Lat / Lng / Vrt / Pitch / Roll / Yaw). Real 3D CT volumes via MPR reslice.
  - **Fusion**: teal (CT/reference) vs orange (CBCT/moving) overlay (#58, replaced additive blend).
    MPR path colorizes via a `sepia → saturate(1.6) → hue-rotate → brightness(0.78)` CSS filter;
    saturation is deliberately low so bright bone tints instead of blooming into a glowing
    cyan/orange halo (earlier `saturate(4)/(3)` glowed on bone).
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
  - **Pan** tool + middle-mouse drag; **Ctrl+R** cycles the primary view (Axial→Coronal→Sagittal).
  - Arrow-key nudge capped at 0.05 cm (0.5 mm)/press.
- Shared: blend sliders, isocenter reticle, live residual-error readout graded vs tolerance,
  **New Offset** generates a fresh setup error, match timer, **How to use** guide on start menu.

### Cases

- **2D/2D:** Brain · Pelvis · Thorax (CT DRR) · Breast L (monoisocentric SCV + medial-tangent, Varian-style).
- **CBCT:** Pelvis · Acoustic neuroma (vestibular schwannoma IAC SRS) · Breast (real 3D CT, MPR + contours)
  · Spine SBRT (T7 vertebral target, cord-avoiding PTV) · Lung SBRT (peripheral RLL nodule — a
  **synthetic**, irregular/spiculated soft-tissue lesion baked into the thoracic CT via
  `generate_lung_contours.py`, `lung3d_data.js` + `lung3d_labels_data.js`; teaches matching the
  soft-tissue target, **off the bone**).
  - **Off-bone differential motion (lung only):** the tumour moves independently of the skeleton,
    so a bony (spine) match leaves the GTV off-target — only matching the soft-tissue lesion scores.
    `randomize()` picks a hidden per-case `targetDrift` {x,y,z} (cm voxels) on top of the usual
    6DOF setup error. The CBCT (moving) reslice composites two passes: it **hides** the
    planning-position lesion (baked hard-edged into the CT at `LESION_HU`, so it can be cleanly
    overwritten with lung density) and **redraws** it sampled through the residual *net − drift*
    transform (`movInvFrom`, `gtvAt` bit-1 GTV lookup), i.e. the lesion follows the tumour, the
    skeleton follows the couch. `check()` grades this as a **PTV/target match**: translations
    against `e − targetDrift`, with the 6DOF **rotations shown but not graded** (a small off-bone
    target can't be put on the PTV by rotating about iso), so acceptance is translation-only; when
    the bones are aligned but the GTV isn't, it shows a hint to match the tumour not the skeleton.
    Generic to all other cases (`targetDrift` stays `null`), so they remain pure rigid 6DOF.

## Auth & paywall (clerk-auth.js)

Client gate using **Clerk** (auth) + **Clerk Billing** (Clerk owns the Stripe integration — no
Stripe code here). Plan key **`full_access`**: $14.99/mo, $120/yr, 3-day trial.

- **Host-detected keys:** production (`rtimagematch.com`) uses the **live** Clerk instance
  (`clerk.rtimagematch.com`, `pk_live_…`); localhost + `*.vercel.app` previews stay on the **dev**
  instance (`fancy-flounder-63.clerk.accounts.dev`, `pk_test_…`). Publishable keys are public by design.
- clerk-js is loaded as a **classic (no-cors) script** — no `crossOrigin` — because some
  AV/VPN HTTPS interceptors strip CORS headers and broke the gate (#66).
- Pages with `<body data-require-auth>` (the trainer) are bounced unless signed in **and**
  authorized for `full_access`.
- **Comp / free-access logic in `isComped()`:**
  - `COMP_USER_IDS` — Clerk user-id allowlist (currently empty).
  - `COMP_EMAILS` — owner emails, full access no subscription: `cju1999@pm.me`, `cju11199@pm.me`
    (matches any email on the account, verified or not).
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
  attempt, awarded once). XP rewards accepts/first-clears/speed(<30 s)/precision(<0.5 mm)/strict.
- **Preferences** (`prefs`): **difficulty** `relaxed | standard | strict` drives the match
  tolerances live via `rtTol()` (threaded into both checkers' pass/colour thresholds); a
  show-stats-on-cards toggle.
- **UI:** a start-screen **summary strip** (level bar · cleared count · streak → opens dashboard),
  per-case-card **cleared badges** (✓ + best time/residual) rendered in `pickMode`, an
  **achievement toast** (`#rtToast`) on unlock, and a **"Your Progress" dashboard modal**
  (`#rtProgModal`, reuses `.modal-bg`) with Overview (level ring + tiles + achievements), Cases
  (per-case tables) and Settings (difficulty, display, Export JSON / Reset) tabs. All styling
  reuses the existing tokens; section headers are `text-transform:uppercase` (so `innerText`
  asserts come back upper-cased in tests).

## Email (EMAIL.md)

`support@rtimagematch.com` via **Cloudflare Email Routing** (forward-only / receive-only). To send
outbound as the address would require switching to a real mailbox (iCloud+ custom domain, Workspace, etc.).

## Conventions

- No framework, no build, no package.json (until the `/api` serverless functions of Phase 2 land).
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
