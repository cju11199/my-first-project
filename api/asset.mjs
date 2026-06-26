// api/asset.mjs — Phase 2 hard data paywall (Vercel Blob edition).
//
// The case data (the *_data.js datasets + drr/*.png) lives in a PRIVATE Vercel Blob
// store, NOT on the public CDN. This function is the only way in: it verifies the caller
// has a Clerk session authorized for `full_access` (or is a comped owner / VERIFIED
// institution account, mirroring clerk-auth.js isComped()), then STREAMS the blob back
// same-origin. Streaming keeps the big datasets under the buffered-response cap, and
// serving the DRR PNGs same-origin keeps the <canvas> untainted.
//
// Auth: subresource loads (<script>/<img>) can't set headers, so the client appends a
// freshly-minted Clerk session token as ?t=, which we promote to Authorization: Bearer
// (verified networklessly). Secrets (CLERK_SECRET_KEY, BLOB_READ_WRITE_TOKEN) are
// server-only env vars — never shipped to the client.

import { createClerkClient } from '@clerk/backend';
import { get } from '@vercel/blob';

const PLAN_KEY = 'full_access';

// Comp tiers — mirror clerk-auth.js isComped(): owner via the unspoofable user id
// (checked first); any COMP_EMAILS / COMP_DOMAINS entry must be a VERIFIED email.
const COMP_USER_IDS = [
  'user_3FRbBFuCte2DQkTDzoeZe2VSfXB', // owner — full access, no subscription
  'user_3Fbnfz1v8QBrK8lwY8XN7YnadDk', // comped account
  'user_3FdAKcEGAZ7GEURzye3YCHv0jsW', // comped account
  'user_3FbktcxWR3jnk8ZP6y4bm9ly9C1', // comped account
];
const COMP_EMAILS = ['cju1999@pm.me'];   // tester — must be a VERIFIED email on the account (see compedByEmail)
const COMP_DOMAINS = ['stonybrook.edu', 'mountsinai.org'];

// Allowlisted object keys — anything else 404s, so ?f= can never be coerced into
// fetching an arbitrary key from the store (no path traversal / presign-anything oracle).
const DATASETS = new Set([
  'image_data.js', 'breast_drr_data.js', 'prostate2d_data.js',
  'brain3d_data.js', 'pelvis3d_data.js', 'breast3d_data.js',
  'spine3d_data.js', 'lung3d_data.js', 'prostate3d_data.js', 'pancreas3d_data.js',
  'acousticmr3d_data.js', 'sarcoma3d_data.js',
  'brain3d_labels_data.js', 'pelvis3d_labels_data.js', 'breast3d_labels_data.js',
  'spine3d_labels_data.js', 'lung3d_labels_data.js', 'prostate3d_labels_data.js',
  'pancreas3d_labels_data.js', 'acousticmr3d_labels_data.js', 'sarcoma3d_labels_data.js',
]);
const DRR_KEY = /^drr\/[a-z0-9_]+\.png$/i;

// Free-tier datasets — served WITHOUT a subscription (the 2D Breast + CBCT Pelvis cases).
// EXACT-MATCH Set only: no regex, no prefixes, NO DRR entries. Every key not in this Set
// keeps the unchanged fail-closed isAuthorized->403 path, so no private asset gains a bypass.
const PUBLIC_KEYS = new Set([
  'breast_drr_data.js',
  'pelvis3d_data.js',
  'pelvis3d_labels_data.js',
]);

const clerk = createClerkClient({
  secretKey: process.env.CLERK_SECRET_KEY,
  publishableKey: process.env.CLERK_PUBLISHABLE_KEY,
});

function compedByEmail(emailAddresses) {
  const allowEmails = COMP_EMAILS.map((e) => e.toLowerCase());
  const allowDomains = COMP_DOMAINS.map((d) => d.toLowerCase().replace(/^@/, ''));
  for (const e of emailAddresses || []) {
    const addr = (e.emailAddress || '').toLowerCase();
    if (!addr) continue;
    // Only ever trust a VERIFIED email (matches clerk-auth.js — closes the unverified bypass).
    if (!(e.verification && e.verification.status === 'verified')) continue;
    if (allowEmails.includes(addr)) return true;
    if (allowDomains.length) {
      const at = addr.lastIndexOf('@');
      const dom = at >= 0 ? addr.slice(at + 1) : '';
      for (const ad of allowDomains) {
        // dot-boundary match so evilstonybrook.edu does NOT match stonybrook.edu
        if (ad && (dom === ad || (dom.length > ad.length && dom.endsWith('.' + ad)))) return true;
      }
    }
  }
  return false;
}

async function isAuthorized(request, token) {
  // Promote the ?t= session token to an Authorization header for networkless verification
  // (falls back to the __session cookie when ?t= is absent).
  const headers = new Headers(request.headers);
  if (token) headers.set('authorization', 'Bearer ' + token);
  const req = new Request(request.url, { headers });
  const state = await clerk.authenticateRequest(req, token ? { acceptsToken: 'session_token' } : undefined);
  const auth = state.toAuth();
  if (!auth || !auth.userId) return false;
  // Active subscription (an active trial counts) via Clerk Billing.
  try { if (auth.has && auth.has({ plan: PLAN_KEY })) return true; } catch { /* fall through */ }
  // Comp tiers.
  if (COMP_USER_IDS.includes(auth.userId)) return true;
  try {
    const user = await clerk.users.getUser(auth.userId);
    if (compedByEmail(user.emailAddresses)) return true;
  } catch { /* ignore lookup failure -> unauthorized */ }
  return false;
}

const json = (obj, status) => new Response(JSON.stringify(obj), { status, headers: { 'content-type': 'application/json' } });

export async function GET(request) {
  const url = new URL(request.url);
  const key = url.searchParams.get('f') || '';
  const token = url.searchParams.get('t') || '';
  const isDataset = DATASETS.has(key);
  const isDrr = DRR_KEY.test(key);
  if (!isDataset && !isDrr) return json({ error: 'unknown asset' }, 404);

  // Public free-tier keys skip the subscription check; everything else stays fail-closed.
  const isPublic = PUBLIC_KEYS.has(key);   // exact match on the already-allowlisted key
  if (!isPublic) {
    let ok = false;
    try { ok = await isAuthorized(request, token); }
    catch { return json({ error: 'authorization check failed' }, 500); }
    if (!ok) return json({ error: 'active subscription required' }, 403);
  }

  let result;
  try { result = await get(key, { access: 'private' }); }   // token defaults to BLOB_READ_WRITE_TOKEN
  catch { return json({ error: 'asset fetch failed' }, 502); }
  if (!result || result.statusCode !== 200 || !result.stream) return new Response('Not found', { status: 404 });

  // Stream same-origin. Datasets are <script src> (must be JS MIME + nosniff); DRR PNGs are
  // drawn to <canvas>, so same-origin keeps them untainted.
  return new Response(result.stream, {
    headers: {
      'Content-Type': isDataset ? 'application/javascript; charset=utf-8' : 'image/png',
      'Cache-Control': isPublic
        ? 'public, max-age=2592000, immutable'
        : (isDataset ? 'private, no-store' : 'private, max-age=300'),
      'X-Content-Type-Options': 'nosniff',
    },
  });
}
