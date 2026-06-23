/* /api/asset — the hard paywall.
 *
 * Serves the protected case data ONLY to clients holding a valid `rt_unlock`
 * cookie, which is minted by /api/unlock after a Clerk Bearer-auth check of an
 * active `full_access` subscription. Verifying the lightweight HMAC cookie here
 * (instead of calling Clerk per asset) keeps this off Clerk's hot path and
 * sidesteps the dev-instance sub-resource handshake problem entirely.
 *
 * Two delivery modes by asset type:
 *   - Big *_data.js files  -> 302 redirect to a short-lived R2 presigned URL,
 *       signed with ResponseContentType=text/javascript so the script executes
 *       regardless of how the object's content-type was stored in R2, and
 *       sidestepping the ~4.5 MB Vercel serverless response cap (image_data.js
 *       is 4.3 MB). Classic <script src> follows the cross-origin redirect fine.
 *   - drr/*.png frames     -> proxied byte-for-byte, same-origin, so the <canvas>
 *       blend slider stays untainted (no CORS/crossOrigin dance).
 *
 * Env: R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET_NAME, R2_ENDPOINT,
 * and CLERK_SECRET_KEY (reused as the cookie-signing secret; or override with
 * ASSET_SIGNING_SECRET).
 */
import crypto from 'node:crypto';
import { S3Client, GetObjectCommand } from '@aws-sdk/client-s3';
import { getSignedUrl } from '@aws-sdk/s3-request-presigner';

const COOKIE_NAME = 'rt_unlock';
const SIGNED_URL_TTL = 300; // seconds

// Allow-list of protected assets. Anything not here is rejected (no arbitrary
// R2 key reads / path traversal). *.js -> presigned redirect; drr/*.png -> proxy.
const JS_ASSETS = new Set([
  'image_data.js',
  'breast_drr_data.js',
  'pelvis3d_data.js',
  'brain3d_data.js',
  'breast3d_data.js',
  'spine3d_data.js',
  'pelvis3d_labels_data.js',
  'brain3d_labels_data.js',
  'breast3d_labels_data.js',
  'spine3d_labels_data.js',
]);
const DRR_RE = /^drr\/[a-z0-9_]+\.png$/;

// R2 is S3-compatible. region 'auto' is what Cloudflare expects.
const s3 = new S3Client({
  region: 'auto',
  endpoint: process.env.R2_ENDPOINT,
  credentials: {
    accessKeyId: process.env.R2_ACCESS_KEY_ID,
    secretAccessKey: process.env.R2_SECRET_ACCESS_KEY,
  },
});
const BUCKET = process.env.R2_BUCKET_NAME;

export default async function handler(req, res) {
  try {
    const url = new URL(req.url, `https://${req.headers.host}`);
    const f = url.searchParams.get('f') || '';

    const isJs = JS_ASSETS.has(f);
    const isPng = DRR_RE.test(f);
    if (!isJs && !isPng) {
      res.status(400).json({ error: 'unknown asset' });
      return;
    }

    // --- gate: verify the unlock cookie (set by /api/unlock) --------------
    if (!hasValidUnlock(req)) {
      res.setHeader('Cache-Control', 'private, no-store');
      res.status(401).json({ error: 'locked' });
      return;
    }

    // --- deliver ----------------------------------------------------------
    if (isJs) {
      const signed = await getSignedUrl(
        s3,
        new GetObjectCommand({
          Bucket: BUCKET,
          Key: f,
          // Force a JS MIME type on the presigned response so the <script>
          // executes even if the object was uploaded as application/octet-stream.
          ResponseContentType: 'text/javascript',
        }),
        { expiresIn: SIGNED_URL_TTL },
      );
      // no-store so a CDN/SW never pins a 302 whose signature later expires.
      res.setHeader('Cache-Control', 'private, no-store');
      res.redirect(302, signed);
      return;
    }

    // PNG proxy (same-origin, canvas-safe).
    const obj = await s3.send(new GetObjectCommand({ Bucket: BUCKET, Key: f }));
    const bytes = Buffer.from(await obj.Body.transformToByteArray());
    res.setHeader('Content-Type', obj.ContentType || 'image/png');
    res.setHeader('Cache-Control', 'private, max-age=300');
    res.status(200).send(bytes);
  } catch (err) {
    console.error('[api/asset]', err);
    res.status(500).json({ error: 'asset error' });
  }
}

// --- unlock-cookie verification (shared format with api/unlock.js) -----------
function hasValidUnlock(req) {
  const raw = readCookie(req.headers.cookie, COOKIE_NAME);
  if (!raw) return false;
  const dot = raw.lastIndexOf('.');
  if (dot < 0) return false;
  const exp = raw.slice(0, dot);
  const mac = raw.slice(dot + 1);
  const expect = crypto.createHmac('sha256', secret()).update(exp).digest('hex');
  if (!timingEqualHex(mac, expect)) return false;
  const expMs = Number(exp);
  return Number.isFinite(expMs) && expMs > Date.now();
}

function secret() {
  return process.env.ASSET_SIGNING_SECRET || process.env.CLERK_SECRET_KEY || '';
}

function readCookie(header, name) {
  if (!header) return null;
  for (const part of header.split(';')) {
    const eq = part.indexOf('=');
    if (eq < 0) continue;
    if (part.slice(0, eq).trim() === name) return part.slice(eq + 1).trim();
  }
  return null;
}

function timingEqualHex(a, b) {
  if (typeof a !== 'string' || typeof b !== 'string' || a.length !== b.length) return false;
  try {
    return crypto.timingSafeEqual(Buffer.from(a, 'hex'), Buffer.from(b, 'hex'));
  } catch {
    return false;
  }
}
