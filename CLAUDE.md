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
- `terms.html`, `privacy.html` — legal pages (`/terms`, `/privacy`; NY governing law,
  `support@rtimagematch.com`).
- `clerk-auth.js` — client-side auth + billing gate (loaded by all pages).
- **Case data (large, loaded on demand), kept out of HTML for caching:**
  - `image_data.js` (~4.3 MB), `breast_drr_data.js` — embedded DRR/portal images for 2D/2D.
  - `*3d_data.js` (brain, breast, pelvis, spine) — 3D CT volume datasets for CBCT (data-URI atlases).
  - `*3d_labels_data.js` — structure/label volumes for CBCT contours.
  - `drr/*.png` — DRR images.
  - `assets/fonts/` — self-hosted web fonts.
- `generate_brain_contours.py` — offline helper that generated brain contour data.
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
  · Spine SBRT (T7 vertebral target, cord-avoiding PTV).

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
