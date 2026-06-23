// api/asset.mjs — Phase 2 hard data paywall.
//
// The ~26 MB of case data (the *_data.js datasets + drr/*.png) lives in a PRIVATE
// Cloudflare R2 bucket, NOT on the public CDN. This serverless function is the only
// way in: it verifies the caller has a Clerk session authorized for `full_access`
// (or is a comped owner / institution account, mirroring clerk-auth.js isComped()),
// then serves the asset two ways:
//   • big *_data.js datasets -> 302 redirect to a short-lived R2 presigned URL.
//        Loaded via <script src>, so no CORS is needed, and a redirect (empty body)
//        keeps us under Vercel's ~4.5 MB serverless response cap (image_data.js is 4.1 MB).
//   • drr/*.png             -> proxied byte-for-byte SAME-ORIGIN, because they are
//        drawn to <canvas> and a cross-origin image would taint it.
//
// This is the actual lock. clerk-auth.js is only the client UX gate. Set the R2_* and
// CLERK_* env vars in Vercel (see .env.example); use per-environment values so Preview
// uses the dev Clerk instance and Production uses the live one (matches clerk-auth.js).

import { createClerkClient } from '@clerk/backend';
import { S3Client, GetObjectCommand } from '@aws-sdk/client-s3';
import { getSignedUrl } from '@aws-sdk/s3-request-presigner';

const PLAN_KEY = 'full_access';

// Comp tiers — keep in sync with clerk-auth.js isComped().
const COMP_USER_IDS = [];
const COMP_EMAILS = ['cju1999@pm.me', 'cju11199@pm.me'];
const COMP_DOMAINS = ['stonybrook.edu', 'mountsinai.org'];

// Allowlisted R2 object keys. Anything else -> 404, so the `f` param can never be
// coerced into fetching an arbitrary key from the bucket.
const DATASETS = new Set([
  'image_data.js', 'breast_drr_data.js', 'prostate2d_data.js',
  'brain3d_data.js', 'pelvis3d_data.js', 'breast3d_data.js',
  'spine3d_data.js', 'lung3d_data.js', 'prostate3d_data.js',
  'brain3d_labels_data.js', 'pelvis3d_labels_data.js', 'breast3d_labels_data.js',
  'spine3d_labels_data.js', 'lung3d_labels_data.js', 'prostate3d_labels_data.js',
]);
const DRR_KEY = /^drr\/[a-z0-9_]+\.png$/i;

const clerk = createClerkClient({
  secretKey: process.env.CLERK_SECRET_KEY,
  publishableKey: process.env.CLERK_PUBLISHABLE_KEY,
});

const r2 = new S3Client({
  region: 'auto',
  endpoint: process.env.R2_ENDPOINT,
  credentials: {
    accessKeyId: process.env.R2_ACCESS_KEY_ID,
    secretAccessKey: process.env.R2_SECRET_ACCESS_KEY,
  },
});

// Mirror of clerk-auth.js isComped(): owner emails (any email on the account,
// verified or not) + VERIFIED institution-domain emails, matched on a dot boundary
// so evilstonybrook.edu does NOT match stonybrook.edu.
function compedByEmail(emailAddresses) {
  const allowEmails = COMP_EMAILS.map((e) => e.toLowerCase());
  const allowDomains = COMP_DOMAINS.map((d) => d.toLowerCase().replace(/^@/, ''));
  for (const e of emailAddresses || []) {
    const addr = (e.emailAddress || '').toLowerCase();
    if (!addr) continue;
    if (allowEmails.includes(addr)) return true;
    const verified = e.verification && e.verification.status === 'verified';
    if (verified && allowDomains.length) {
      const at = addr.lastIndexOf('@');
      const dom = at >= 0 ? addr.slice(at + 1) : '';
      for (const ad of allowDomains) {
        if (ad && (dom === ad || (dom.length > ad.length && dom.endsWith('.' + ad)))) return true;
      }
    }
  }
  return false;
}

async function authorized(req) {
  const proto = String(req.headers['x-forwarded-proto'] || 'https').split(',')[0];
  const host = req.headers['x-forwarded-host'] || req.headers.host;
  // authenticateRequest reads the first-party __session cookie (or Bearer token).
  const request = new Request(`${proto}://${host}${req.url}`, { headers: req.headers });
  const state = await clerk.authenticateRequest(request);
  const auth = state.toAuth();
  // detail is a TEMPORARY debug aid surfaced only when ?debug=1 (see handler). Remove before merge.
  const detail = {
    status: state.status, reason: state.reason || null,
    signedIn: !!(auth && auth.userId), userId: (auth && auth.userId) || null,
    plan: false, emails: [],
  };
  if (!detail.signedIn) return { ok: false, detail };
  // Active subscription (an active trial counts) via Clerk Billing.
  try { if (auth.has && auth.has({ plan: PLAN_KEY })) { detail.plan = true; return { ok: true, detail }; } } catch { /* fall through */ }
  // Comp tiers.
  if (COMP_USER_IDS.includes(auth.userId)) return { ok: true, detail };
  try {
    const user = await clerk.users.getUser(auth.userId);
    detail.emails = (user.emailAddresses || []).map((e) => ({ email: e.emailAddress, verified: e.verification && e.verification.status === 'verified' }));
    if (compedByEmail(user.emailAddresses)) return { ok: true, detail };
  } catch (err) { detail.getUserError = String((err && err.message) || err); }
  return { ok: false, detail };
}

export default async function handler(req, res) {
  const key = typeof req.query.f === 'string' ? req.query.f : '';
  const isDataset = DATASETS.has(key);
  const isDrr = DRR_KEY.test(key);
  if (!isDataset && !isDrr) return res.status(404).json({ error: 'unknown asset' });

  const debug = !!req.query.debug;
  let result;
  try {
    result = await authorized(req);
  } catch (e) {
    return res.status(500).json({ error: 'authorization check failed', detail: debug ? String((e && e.message) || e) : undefined });
  }
  if (!result.ok) {
    return res.status(403).json({ error: 'active subscription required', debug: debug ? result.detail : undefined });
  }

  const Bucket = process.env.R2_BUCKET_NAME;
  try {
    if (isDataset) {
      // Short-lived presigned URL; the <script src> follows the 302 (empty body -> no size cap).
      const url = await getSignedUrl(r2, new GetObjectCommand({ Bucket, Key: key }), { expiresIn: 90 });
      res.setHeader('Cache-Control', 'private, no-store');
      res.setHeader('Location', url);
      return res.status(302).end();
    }
    // DRR PNG: proxy the bytes same-origin so the <canvas> stays untainted.
    const obj = await r2.send(new GetObjectCommand({ Bucket, Key: key }));
    const body = Buffer.from(await obj.Body.transformToByteArray());
    res.setHeader('Content-Type', 'image/png');
    res.setHeader('Cache-Control', 'private, max-age=300');
    return res.status(200).send(body);
  } catch {
    return res.status(502).json({ error: 'asset fetch failed' });
  }
}
