# Paywall implementation plan

Gating the RT Image Matching Trainer behind a paid subscription.

- **Auth + billing:** Clerk + Clerk Billing (Clerk manages Stripe — no Stripe code/webhooks on our side).
- **Plans:** Monthly $14.99 · Annual $120 · 3-day free trial (defined in the Clerk dashboard).
- **Strength:** hard paywall — the ~15 MB of case data is moved to private storage and served only via short-lived signed URLs to active subscribers.
- **Stack:** stays a static site on Vercel + a few serverless functions under `/api`. No framework rewrite; `trainer.html` stays as-is except for how it loads data.
- **Protected storage:** Cloudflare R2 (S3-compatible presigned URLs with expiry).

## Assets to protect (the paid content)

Currently public static files that must move to R2:

- `image_data.js`, `breast_drr_data.js` (loaded at trainer startup)
- `brain3d_data.js`, `pelvis3d_data.js`, `breast3d_data.js`, `spine3d_data.js`
- `brain3d_labels_data.js`, `pelvis3d_labels_data.js`, `breast3d_labels_data.js`, `spine3d_labels_data.js`
- `drr/*.png` (32 DRR images)

Public (stay on CDN): `index.html`, `terms.html`, `privacy.html`, `assets/fonts/*`, and `trainer.html` itself (the shell — useless without the data).

## Phases

- **Phase 0 — Accounts & keys:** Clerk app + Billing plans; R2 bucket + credentials; connect Stripe (for go-live); set Vercel env vars.
- **Phase 1 — Auth + page gating:** Clerk login; "Start free trial" → Clerk checkout (3-day trial) → `/trainer`; `/api/authorize` verifies session + active subscription server-side; trainer bounces non-subscribers.
- **Phase 2 — Lock the data:** upload protected assets to R2; replace the trainer's data/image loaders to fetch via `/api/asset`, which checks the subscription and returns a short-lived R2 signed URL.
- **Phase 3 — Go live:** connect Stripe, switch Clerk + keys to live mode, test a real purchase, launch.

## Environment variables (set in Vercel; see .env.example)

| Var | Used by | Notes |
|-----|---------|-------|
| `CLERK_PUBLISHABLE_KEY` | client | safe to expose |
| `CLERK_SECRET_KEY` | server | secret |
| `R2_ACCOUNT_ID` | server | Cloudflare account id |
| `R2_ACCESS_KEY_ID` | server | R2 API token |
| `R2_SECRET_ACCESS_KEY` | server | secret |
| `R2_BUCKET_NAME` | server | e.g. `rtimagematch-data` |
| `R2_ENDPOINT` | server | `https://<account-id>.r2.cloudflarestorage.com` |

Stripe keys are **not** needed in this app — Clerk Billing owns the Stripe integration.

---

## Progress / session handoff (last updated 2026-06-20)

**Branch:** `claude/vercel-website-paywall-m5c4cm` · **PR:** #62 (draft, CI green).
PR #61 (landing + legal pages) already merged to `main`. Don't merge #62 until the
paywall works — pricing + paywall launch together.

### Done ✅
- **Pricing** finalized & on landing page: Monthly **$14.99**, Annual **$120** (~33% off), **3-day trial**.
- **Email:** `support@rtimagematch.com` via Cloudflare Email Routing (see EMAIL.md).
- **Clerk auth (Phase 1):** `clerk-auth.js` loads Clerk JS, renders header sign-in/user
  button, routes trial CTAs. Publishable key `pk_test_ZmFuY3ktZmxvdW5kZXItNjMuY2xlcmsuYWNjb3VudHMuZGV2JA`
  (instance `fancy-flounder-63.clerk.accounts.dev`). Sign-in methods: email/password + Google.
- **Clerk Billing (Phase 1.5):** plan created in Clerk dashboard — **name "Full Access",
  key `full_access`**, with $14.99/mo + $120/yr + 3-day trial, published. `subscribe.html`
  mounts `Clerk.mountPricingTable()`; gate uses `session.checkAuthorization({ plan: 'full_access' })`.
  **Tested working end-to-end** (signup → trial checkout w/ test card 4242… → trainer; gate bounces non-subscribers).
- **Vercel env vars set by user:** `CLERK_SECRET_KEY` (sk_test_…), `CLERK_PUBLISHABLE_KEY`.

### In progress 🔧 — Phase 2 (hard lockdown of case data via Cloudflare R2)
The data is now ~26 MB across **15** `*_data.js` files + **32** `drr/*.png` (lung + prostate cases
were added since the list above). The **code (D/E/F) is done**; what remains is owner-only dashboard
ops (B/C) that no integration can do for us.

- **A. Create R2 bucket** `rtimagematch-data` — ✅ **done** (exists in the Cloudflare account).
- **D.** ✅ **done** — `api/asset.mjs` (Vercel serverless fn): `authenticateRequest` via
  `@clerk/backend` → `auth.has({plan:'full_access'})`, **plus** a server-side mirror of
  clerk-auth.js `isComped()` (owner emails + verified institution domains, so comped accounts keep
  access once data is off-CDN). Big `*_data.js` → **302 redirect to a 90 s R2 presigned URL**
  (loaded via `<script src>`, no CORS; redirect body is empty so we dodge the response cap);
  `drr/*.png` → **proxied same-origin** (canvas-safe). Allowlisted keys only. `package.json` now
  carries `@clerk/backend@^3`, `@aws-sdk/client-s3@^3`, `@aws-sdk/s3-request-presigner@^3`.
- **E.** ✅ **done** — all 12 `trainer.html` load sites fetch via `/api/asset?f=<key>` (3 static
  dataset `<script>`s, the dynamic CT-volume + 6 label `createElement('script')` loaders, and the
  DRR `new Image().src`, whose `?v=` cache token became `&v=`). CSP gained
  `https://*.r2.cloudflarestorage.com` (script-src + connect-src) for the redirect target.
- **F.** ✅ **done (committed, not yet active)** — `.vercelignore` lists the data files + `drr/`. This
  is the **final switch**: it only takes effect when merged to `main`. Do NOT merge to production
  until B and C are complete or the live trainer breaks for everyone.

**Owner-only ops still to do (dashboard):**
- **B.** Make an R2 API token + set env vars in Vercel for **both** Production and Preview:
  `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME=rtimagematch-data`,
  `R2_ENDPOINT=https://<account-id>.r2.cloudflarestorage.com`. Use **per-environment Clerk keys** too
  (Preview = dev `sk_test_…`, Production = live `sk_live_…`) to match clerk-auth.js host detection.
- **C.** Upload the protected files to R2: run `node --env-file=.env.local scripts/upload-to-r2.mjs`
  (needs an Object **Read & Write** token; the app itself only reads) — or drag-drop them in the
  dashboard (datasets at the bucket root, PNGs under a `drr/` prefix).

**Gotchas:** Vercel serverless response limit ~4.5 MB (image_data.js is 4.1 MB) → presigned R2 URLs
for `.js`, not proxying. DRR PNGs are drawn to canvas → served same-origin (proxy). Volume "atlas"
images are data URIs inside the `.js` (no separate fetch). The interim `middleware.js` hotlink guard
is now redundant (its matched paths 404 once the files leave the CDN) but harmless — left in place.

### Phase 3 (later)
Connect user's real Stripe to Clerk Billing, switch Clerk + keys to live mode, test a real
purchase, then merge #62 and launch.

