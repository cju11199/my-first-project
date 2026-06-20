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
