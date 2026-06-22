import { next } from '@vercel/edge';

// ── Interim hotlink / direct-download guard for the paid case data ───────────────────────────
// Until the Phase-2 hard paywall (Clerk-verified R2 presigned URLs, see PAYWALL.md) lands, the
// ~15 MB of case data is still public on the CDN. This edge middleware is a *speed bump*, not a
// paywall: it lets the trainer's own same-origin subresource loads through, and blocks
// cross-site hotlinks, direct URL navigations, and header-less non-browser fetches (curl/bots).
//
// It deliberately fails OPEN on anything ambiguous (and on any error) so it can never break a
// real browser session. Sec-Fetch-Site / User-Agent are spoofable, so a determined scraper that
// forges headers still gets through — that's expected; only Phase 2 enforces a subscription.
//
// Note: Referrer-Policy is `no-referrer` site-wide, so legit loads send NO Referer — the decision
// relies on Sec-Fetch-Site (which Referrer-Policy does not affect), with User-Agent as a fallback.

export const config = {
  matcher: [
    '/image_data.js',
    '/breast_drr_data.js',
    '/prostate2d_data.js',
    '/brain3d_data.js',
    '/pelvis3d_data.js',
    '/breast3d_data.js',
    '/spine3d_data.js',
    '/lung3d_data.js',
    '/prostate3d_data.js',
    '/brain3d_labels_data.js',
    '/pelvis3d_labels_data.js',
    '/breast3d_labels_data.js',
    '/spine3d_labels_data.js',
    '/lung3d_labels_data.js',
    '/prostate3d_labels_data.js',
    '/drr/:path*',
  ],
};

export default function middleware(request) {
  try {
    return allow(request.headers.get('sec-fetch-site'), request.headers.get('user-agent'))
      ? next()
      : forbidden();
  } catch {
    return next(); // never let a middleware bug break a real load
  }
}

// Pure decision so the truth table can be unit-tested off the edge runtime.
export function allow(secFetchSite, userAgent) {
  // Our own trainer page loading the file as a subresource.
  if (secFetchSite === 'same-origin' || secFetchSite === 'same-site') return true;
  // Cross-site hotlink, or a direct URL navigation/typed link — block.
  if (secFetchSite === 'cross-site' || secFetchSite === 'none') return false;
  // No Sec-Fetch-Site (older browsers or non-browser clients): use UA as a tiebreaker so old
  // browsers keep working while plain curl/python/wget are turned away.
  return /Mozilla|AppleWebKit|Gecko|Chrome|Safari|Firefox|Edg|OPR/i.test(userAgent || '');
}

function forbidden() {
  return new Response('Forbidden — this file is served only to the RT Image Matching Trainer.', {
    status: 403,
    headers: { 'content-type': 'text/plain; charset=utf-8' },
  });
}
