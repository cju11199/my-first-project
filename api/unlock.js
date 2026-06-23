/* /api/unlock — mint a short-lived asset-access cookie.
 *
 * Why this exists: a Clerk DEVELOPMENT instance can't reliably authenticate
 * <script src> / <img> sub-resource requests on a *.vercel.app preview (the
 * dev session rides a __clerk_db_jwt querystring, not a first-party cookie,
 * so bare asset requests hit Clerk's handshake and 401). So instead of
 * authenticating every asset request with Clerk, the trainer calls THIS
 * endpoint once via fetch() with an explicit `Authorization: Bearer <token>`
 * (from Clerk.session.getToken()) — Bearer auth works on any instance,
 * networklessly — and we hand back a first-party signed cookie. /api/asset
 * then just verifies that cookie (see asset.js), no Clerk on the hot path.
 *
 * The cookie is HMAC-signed with CLERK_SECRET_KEY (already a server secret;
 * override with ASSET_SIGNING_SECRET if you ever want to rotate independently)
 * and short-lived, so it can't be forged and ages out on its own.
 *
 * Env: CLERK_SECRET_KEY, CLERK_PUBLISHABLE_KEY (+ optional APP_ORIGINS).
 */
import crypto from 'node:crypto';
import { createClerkClient } from '@clerk/backend';

const PLAN_KEY = 'full_access';
const COOKIE_NAME = 'rt_unlock';
const TTL_MS = 60 * 60 * 1000; // 1 hour

const clerk = createClerkClient({
  secretKey: process.env.CLERK_SECRET_KEY,
  publishableKey: process.env.CLERK_PUBLISHABLE_KEY,
});

export default async function handler(req, res) {
  try {
    if (req.method !== 'POST') {
      res.setHeader('Allow', 'POST');
      res.status(405).json({ error: 'method not allowed' });
      return;
    }

    const url = new URL(req.url, `https://${req.headers.host}`);
    const webReq = new Request(url, { method: 'POST', headers: toHeaders(req.headers) });

    const state = await clerk.authenticateRequest(webReq, {
      authorizedParties: buildAuthorizedParties(),
    });
    const signedIn = state.isAuthenticated ?? state.isSignedIn;
    if (!signedIn) {
      // Includes the handshake case: the trainer sends a Bearer token, so a
      // real subscriber should never land here; surface the reason to logs.
      console.warn('[api/unlock] not signed in', { status: state.status, reason: state.reason });
      res.status(401).json({ error: 'sign in required' });
      return;
    }
    const auth = state.toAuth();
    if (!auth?.has?.({ plan: PLAN_KEY })) {
      res.status(403).json({ error: 'subscription required' });
      return;
    }

    const exp = nowMs() + TTL_MS;
    const token = signToken(exp);
    res.setHeader('Set-Cookie', cookie(token, TTL_MS / 1000));
    res.setHeader('Cache-Control', 'private, no-store');
    res.status(200).json({ unlocked: true, exp });
  } catch (err) {
    console.error('[api/unlock]', err);
    res.status(500).json({ error: 'unlock error' });
  }
}

// --- signing (shared format with api/asset.js) -------------------------------
function secret() {
  return process.env.ASSET_SIGNING_SECRET || process.env.CLERK_SECRET_KEY || '';
}
function signToken(exp) {
  const mac = crypto.createHmac('sha256', secret()).update(String(exp)).digest('hex');
  return `${exp}.${mac}`;
}
function cookie(value, maxAgeSec) {
  return `${COOKIE_NAME}=${value}; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=${maxAgeSec}`;
}

// Build a trusted allowlist of origins for Clerk's azp check from Vercel's
// system env (never the inbound Host header, which is attacker-controlled).
function buildAuthorizedParties() {
  const out = new Set();
  const add = (h) => {
    if (!h) return;
    out.add(h.startsWith('http') ? h : `https://${h}`);
  };
  add(process.env.VERCEL_PROJECT_PRODUCTION_URL);
  add(process.env.VERCEL_BRANCH_URL);
  add(process.env.VERCEL_URL);
  add('rtimagematch.com');
  add('www.rtimagematch.com');
  (process.env.APP_ORIGINS || '')
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)
    .forEach(add);
  return [...out];
}

function nowMs() {
  return Date.now();
}

function toHeaders(h) {
  const headers = new Headers();
  for (const [k, v] of Object.entries(h)) {
    if (Array.isArray(v)) v.forEach((vv) => headers.append(k, vv));
    else if (v != null) headers.set(k, v);
  }
  return headers;
}
