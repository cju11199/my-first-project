/* rt-asset-flag.js — reversible feature flag for the Phase-2 R2 asset gate.
 *
 * DEFAULT OFF. When OFF this file is inert: RT_ASSETS.url()/drr() return the plain
 * local filename and RT_ASSETS.boot()/unlock() are no-ops, so trainer.html loads every
 * asset from the local CDN files exactly as it does today (byte-for-byte behavior).
 *
 * When ON, the in-scope case-data assets are fetched through /api/asset (the Clerk-gated
 * R2 proxy): the big *_data.js / *_labels_data.js blobs 302-redirect to a short-lived R2
 * presigned URL, and drr/*.png frames are proxied same-origin. Before any gated fetch we
 * POST /api/unlock with the Clerk session bearer token to mint the rt_unlock cookie that
 * /api/asset verifies.
 *
 * TOGGLE (credential-free, no redeploy):
 *   ON  : append ?r2=1 to the trainer URL  (persists via localStorage rt_assets=1)
 *   OFF : append ?r2=0                      (clears the localStorage flag) — the default
 * There is intentionally NO build-time / production default-on switch here; flipping it on
 * for everyone is a separate, explicit step (see the migration notes).
 *
 * SCOPE: only the exact assets api/asset.js will serve from R2 are rewritten. Out-of-scope
 * files (prostate2d_data.js, lung3d_data.js, prostate3d_data.js and their labels) always
 * load locally, even when ON, so the flag's blast radius == the 42 migrated assets and a
 * gated request can never hit the allow-list's 400.
 */
(function () {
  var qs = location.search || '';
  var on = false;
  try { on = localStorage.getItem('rt_assets') === '1'; } catch (e) {}
  if (/[?&]r2=0(?:&|$)/.test(qs)) { on = false; try { localStorage.removeItem('rt_assets'); } catch (e) {} }
  else if (/[?&]r2=1(?:&|$)/.test(qs)) { on = true; try { localStorage.setItem('rt_assets', '1'); } catch (e) {} }

  // Must stay in sync with api/asset.js JS_ASSETS + DRR_RE.
  var JS = {
    'image_data.js': 1, 'breast_drr_data.js': 1,
    'pelvis3d_data.js': 1, 'brain3d_data.js': 1, 'breast3d_data.js': 1, 'spine3d_data.js': 1,
    'pelvis3d_labels_data.js': 1, 'brain3d_labels_data.js': 1, 'breast3d_labels_data.js': 1, 'spine3d_labels_data.js': 1
  };
  var DRR = /^drr\/[a-z0-9_]+\.png$/;
  function gated(name) { return JS[name] === 1 || DRR.test(name); }

  // Rewrite a local asset name to the gated endpoint, but only for in-scope assets.
  function url(name) { return (on && gated(name)) ? '/api/asset?f=' + encodeURIComponent(name) : name; }

  // PNG variant that carries the original "?v=<token>" cache-bust over as "&v=<token>".
  function drr(path, ver) {
    ver = ver || '';
    if (!(on && DRR.test(path))) return path + ver;           // OFF / out-of-scope: identical
    return '/api/asset?f=' + encodeURIComponent(path) + (ver ? ('&' + ver.replace(/^\?/, '')) : '');
  }

  // Wait for a Clerk session token (clerk-auth.js loads Clerk after this script).
  function clerkToken() {
    return new Promise(function (resolve) {
      var t0 = Date.now();
      (function poll() {
        try {
          if (window.Clerk && window.Clerk.session && window.Clerk.session.getToken) {
            window.Clerk.session.getToken().then(resolve).catch(function () { resolve(null); });
            return;
          }
        } catch (e) {}
        if (Date.now() - t0 > 15000) { resolve(null); return; }  // give up; unlock will 401
        setTimeout(poll, 150);
      })();
    });
  }

  // One-shot: mint the rt_unlock cookie. Memoized; resolves true/false (never rejects).
  var _unlock = null;
  function unlock() {
    if (!on) return Promise.resolve(true);
    if (_unlock) return _unlock;
    _unlock = clerkToken().then(function (tok) {
      return fetch('/api/unlock', {
        method: 'POST',
        headers: tok ? { Authorization: 'Bearer ' + tok } : {},
        credentials: 'same-origin'
      }).then(function (r) {
        if (!r.ok) { console.error('[rt-assets] /api/unlock ' + r.status + ' — gated assets will not load'); return false; }
        return true;
      });
    }).catch(function (e) { console.error('[rt-assets] unlock error', e); return false; });
    return _unlock;
  }

  function loadScript(name) {
    return new Promise(function (resolve, reject) {
      var s = document.createElement('script');
      s.src = url(name);
      s.onload = resolve;
      s.onerror = function () { console.error('[rt-assets] failed to load ' + name); reject(new Error(name)); };
      document.head.appendChild(s);
    });
  }

  // Bootstrap the parse-time case-data scripts (image_data.js + breast_drr_data.js used by the
  // CASES table) AFTER unlock. Resolves once both are loaded; immediate no-op when OFF. Memoized.
  var _boot = null;
  function boot() {
    if (!on) return Promise.resolve();
    if (_boot) return _boot;
    _boot = unlock().then(function () {
      return Promise.all(['breast_drr_data.js', 'image_data.js'].map(loadScript));
    });
    return _boot;
  }

  window.RT_ASSETS = { on: on, url: url, drr: drr, gated: gated, unlock: unlock, boot: boot };
  if (on) console.info('[rt-assets] R2 gate ON — case data via /api/asset (toggle off with ?r2=0)');
})();
