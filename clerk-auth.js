/* Clerk auth + billing for the RT Image Matching Trainer (static site, no build).
 *
 * - Loads Clerk JS from the instance's frontend API.
 * - Landing header: Sign in button / user menu.
 * - "Start free trial" CTAs route by state:
 *     signed out      -> sign up, then /subscribe
 *     no subscription  -> /subscribe (Clerk pricing table / checkout)
 *     subscribed       -> /trainer
 * - Pages with <body data-require-auth> are gated: must be signed in AND
 *   have an active `full_access` subscription, else bounced.
 *
 * Note: this is the CLIENT gate (UX). The hard paywall — serving the case
 * data only to subscribers — is enforced server-side in /api (Phase 2).
 *
 * The publishable key is public by design and safe to ship in client code.
 */
(function () {
  // Register the PWA service worker (install shell + offline fallback). It never
  // caches gated pages, case data, /api, or cross-origin requests — see sw.js —
  // so the auth gate and Phase-2 paywall are unaffected. Safe no-op if unsupported.
  if ('serviceWorker' in navigator && window.isSecureContext) {
    window.addEventListener('load', function () {
      navigator.serviceWorker.register('/sw.js').catch(function () {});
    });
  }

  // PWA install: capture the browser's install prompt (Chromium) and wire any
  // [data-install-app] control. The control stays hidden where install isn't
  // offered (iOS Safari / Firefox / already installed), so it's never a dead button.
  var deferredInstall = null;
  function toggleInstall(show) {
    var els = document.querySelectorAll('[data-install-app]');
    for (var i = 0; i < els.length; i++) els[i].hidden = !show;
  }
  window.addEventListener('beforeinstallprompt', function (e) {
    e.preventDefault();
    deferredInstall = e;
    toggleInstall(true);
  });
  window.addEventListener('appinstalled', function () {
    deferredInstall = null;
    toggleInstall(false);
  });
  document.addEventListener('click', function (e) {
    var btn = e.target && e.target.closest && e.target.closest('[data-install-app]');
    if (!btn || !deferredInstall) return;
    e.preventDefault();
    deferredInstall.prompt();
    deferredInstall.userChoice.then(function () {
      deferredInstall = null;
      toggleInstall(false);
    });
  });

  // Production (rtimagematch.com) uses the live Clerk instance; Vercel previews
  // and localhost stay on the development instance so they remain testable.
  var HOST = (location.hostname || '').toLowerCase();
  var IS_DEV = HOST === 'localhost' || HOST === '127.0.0.1' || /\.vercel\.app$/.test(HOST);
  var PUBLISHABLE_KEY = IS_DEV
    ? 'pk_test_ZmFuY3ktZmxvdW5kZXItNjMuY2xlcmsuYWNjb3VudHMuZGV2JA'
    : 'pk_live_Y2xlcmsucnRpbWFnZW1hdGNoLmNvbSQ';
  var FRONTEND_API = IS_DEV
    ? 'fancy-flounder-63.clerk.accounts.dev'
    : 'clerk.rtimagematch.com';
  var PLAN_KEY = 'full_access';
  var TRAINER_URL = '/trainer';
  var SUBSCRIBE_URL = '/subscribe';

  // Comped accounts: full access WITHOUT a paid subscription (owner, testers).
  // PREFERRED: Clerk user id (opaque + unspoofable; Clerk Dashboard -> Users ->
  // your user -> copy User ID). COMP_EMAILS also works but requires the email to
  // be VERIFIED on the account (see isComped) — an unverified address never grants access.
  var COMP_USER_IDS = [
    'user_3FRbBFuCte2DQkTDzoeZe2VSfXB', // owner — full access, no subscription
    'user_3Fbnfz1v8QBrK8lwY8XN7YnadDk', // comped account
    'user_3FdAKcEGAZ7GEURzye3YCHv0jsW', // comped account
    'user_3FbktcxWR3jnk8ZP6y4bm9ly9C1', // comped account
  ];
  var COMP_EMAILS = ['cju1999@pm.me']; // tester (verified emails only; checked against VERIFIED addresses in isComped)
  // Whole-domain free access (students/staff): anyone with a VERIFIED email at one
  // of these domains (or a subdomain) gets in free — no subscription. Institution
  // domains only; a public domain (gmail.com) would free everyone.
  var COMP_DOMAINS = ['stonybrook.edu', 'mountsinai.org'];

  var readyResolve;
  var ready = new Promise(function (r) { readyResolve = r; });

  function loadClerk() {
    return new Promise(function (resolve, reject) {
      if (window.Clerk) return resolve();
      var s = document.createElement('script');
      s.async = true;
      // No crossOrigin: load clerk-js as a classic (no-cors) script. Some
      // antivirus/VPN HTTPS interceptors mangle CORS-mode loads (stripping the
      // Access-Control-Allow-Origin header), which made the gate fail to load
      // Clerk. A classic script doesn't need CORS and loads like a direct hit.
      s.setAttribute('data-clerk-publishable-key', PUBLISHABLE_KEY);
      s.src = 'https://' + FRONTEND_API + '/npm/@clerk/clerk-js@5/dist/clerk.browser.js';
      s.onload = resolve;
      s.onerror = function () { reject(new Error('Failed to load Clerk')); };
      document.head.appendChild(s);
    });
  }

  // True if the signed-in user has an active subscription to the plan
  // (Clerk Billing counts an active trial as authorized).
  // Owner / comped accounts bypass the subscription requirement.
  function isComped() {
    var u = window.Clerk && window.Clerk.user;
    if (!u) return false;
    if (COMP_USER_IDS.indexOf(u.id) !== -1) return true;
    var allowEmails = COMP_EMAILS.map(function (e) { return e.toLowerCase(); });
    var allowDomains = COMP_DOMAINS.map(function (d) { return d.toLowerCase().replace(/^@/, ''); });
    var emails = u.emailAddresses || [];
    for (var i = 0; i < emails.length; i++) {
      var addr = (emails[i].emailAddress || '').toLowerCase();
      if (!addr) continue;
      // Only ever trust a VERIFIED email: an unverified address can be claimed by
      // signing up with someone else's email, so neither the owner/tester allowlist
      // nor the domain allowlist may grant access on an unverified address.
      var v = emails[i].verification;
      if (!(v && v.status === 'verified')) continue;
      // Exact-email allowlist (owner/testers).
      if (allowEmails.indexOf(addr) !== -1) return true;
      // Domain allowlist (students): VERIFIED email at the domain (or a subdomain).
      if (allowDomains.length) {
        var at = addr.lastIndexOf('@');
        var dom = at >= 0 ? addr.slice(at + 1) : '';
        for (var j = 0; j < allowDomains.length; j++) {
          var ad = allowDomains[j];
          if (ad && (dom === ad ||
              (dom.length > ad.length && dom.slice(dom.length - ad.length - 1) === '.' + ad))) {
            return true;
          }
        }
      }
    }
    return false;
  }

  function hasActiveSub() {
    try {
      if (isComped()) return true;
      var s = window.Clerk && window.Clerk.session;
      if (s && typeof s.checkAuthorization === 'function') {
        return !!s.checkAuthorization({ plan: PLAN_KEY });
      }
      console.warn('[auth] checkAuthorization unavailable on session');
    } catch (e) {
      console.warn('[auth] subscription check failed', e);
    }
    return false;
  }

  function renderHeader() {
    var slot = document.getElementById('clerk-auth');
    if (!slot) return;
    slot.innerHTML = '';
    if (window.Clerk && window.Clerk.user) {
      var launch = document.createElement('a');
      launch.href = hasActiveSub() ? TRAINER_URL : SUBSCRIBE_URL;
      launch.className = 'cta';
      launch.innerHTML = hasActiveSub() ? 'Launch&nbsp;&rarr;' : 'Subscribe';
      var ub = document.createElement('span');
      ub.id = 'clerk-userbtn';
      slot.appendChild(launch);
      slot.appendChild(ub);
      window.Clerk.mountUserButton(ub, { afterSignOutUrl: '/' });
    } else {
      // Signed out: a direct "Try free" entry into the trainer (free mode — no account
      // needed for the free cases), plus the usual Sign in.
      var tryFree = document.createElement('a');
      tryFree.href = TRAINER_URL;
      tryFree.className = 'cta';
      tryFree.innerHTML = 'Try&nbsp;free&nbsp;&rarr;';
      slot.appendChild(tryFree);
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'link-btn';
      btn.textContent = 'Sign in';
      btn.addEventListener('click', function () {
        window.Clerk.openSignIn({ forceRedirectUrl: TRAINER_URL });
      });
      slot.appendChild(btn);
    }
  }

  function routeTrial() {
    if (!window.Clerk || !window.Clerk.user) {
      window.Clerk.openSignUp({ forceRedirectUrl: SUBSCRIBE_URL });
    } else if (hasActiveSub()) {
      window.location.href = TRAINER_URL;
    } else {
      window.location.href = SUBSCRIBE_URL;
    }
  }

  function wireCtas() {
    var ctas = document.querySelectorAll('[data-cta="trial"]');
    Array.prototype.forEach.call(ctas, function (el) {
      el.addEventListener('click', function (e) { e.preventDefault(); routeTrial(); });
    });
  }

  function enforceGate() {
    if (!document.body.hasAttribute('data-require-auth')) return;
    // Free-tier model: NEVER bounce. Subscribers/comped get full access; everyone else
    // (signed out OR signed in without a subscription) is let into the trainer in "free mode"
    // where only the free cases are playable (the data gate at /api/asset still protects paid
    // case data server-side, so letting them in cannot expose anything paid).
    var de = document.documentElement;
    de.classList.remove('auth-pending');
    if (window.Clerk && window.Clerk.user && hasActiveSub()) {
      de.classList.remove('free-mode');
    } else {
      de.classList.add('free-mode');
    }
  }

  /* ---------------------------------------------------------------------------
   * Per-user profile (training progress + preferences).
   * Stored in Clerk `unsafeMetadata.rt` so it follows the user across devices
   * with no backend. unsafeMetadata is writable from the client and capped at a
   * few KB, so the payload is kept compact (aggregates + a short recent ring).
   * SECURITY: unsafeMetadata is CLIENT-WRITABLE — treat `rt` as cosmetic UX state
   * ONLY. Never gate access, billing, or any trust/entitlement decision on it
   * (isComped()/hasActiveSub() do not). Anything trust-bearing (leaderboards,
   * certificates, CE credit, discounts) must be set server-side in publicMetadata
   * via an authenticated /api endpoint (Phase 2), never here.
   * ------------------------------------------------------------------------- */
  var PROFILE_SCHEMA = 1;
  var _profile = null;        // in-memory working copy
  var _profileReady = false;
  var _saveTimer = null;
  var _saveInFlight = false;
  var _saveAgain = false;

  function _blankProfile() {
    return { schema: PROFILE_SCHEMA, stats: {}, prefs: {}, ach: {},
             totals: { attempts: 0, accepts: 0 }, xp: 0,
             streak: { count: 0, best: 0, last: null }, recent: [],
             createdAt: Date.now() };
  }

  function _loadProfile() {
    var u = window.Clerk && window.Clerk.user;
    var raw = u && u.unsafeMetadata && u.unsafeMetadata.rt;
    if (raw && typeof raw === 'object') {
      try { _profile = JSON.parse(JSON.stringify(raw)); }
      catch (e) { _profile = _blankProfile(); }
      if (!_profile.schema) _profile.schema = PROFILE_SCHEMA;
      // make sure expected containers exist (forward-compatible)
      ['stats', 'prefs', 'ach'].forEach(function (k) { if (!_profile[k]) _profile[k] = {}; });
      if (!_profile.totals) _profile.totals = { attempts: 0, accepts: 0 };
      if (!_profile.streak) _profile.streak = { count: 0, best: 0, last: null };
      if (!_profile.recent) _profile.recent = [];
      if (typeof _profile.xp !== 'number') _profile.xp = 0;
    } else {
      _profile = _blankProfile();
    }
    _profileReady = true;
    return _profile;
  }

  function _persistProfile() {
    var u = window.Clerk && window.Clerk.user;
    if (!u || !_profile) return Promise.resolve();
    if (_saveInFlight) { _saveAgain = true; return Promise.resolve(); }
    _saveInFlight = true;
    // Merge so we never clobber other unsafeMetadata keys another feature may own.
    var meta = {};
    var cur = u.unsafeMetadata || {};
    for (var k in cur) { if (Object.prototype.hasOwnProperty.call(cur, k)) meta[k] = cur[k]; }
    meta.rt = _profile;
    return u.update({ unsafeMetadata: meta })
      .catch(function (e) { console.warn('[profile] save failed', e); })
      .then(function () {
        _saveInFlight = false;
        if (_saveAgain) { _saveAgain = false; return _persistProfile(); }
      });
  }

  function getProfile() {
    if (!_profileReady) _loadProfile();
    return _profile;
  }

  // Apply a mutation, then persist (debounced to avoid hammering the API).
  function saveProfile(mutator) {
    var p = getProfile();
    if (typeof mutator === 'function') { try { mutator(p); } catch (e) {} }
    if (_saveTimer) clearTimeout(_saveTimer);
    _saveTimer = setTimeout(function () { _saveTimer = null; _persistProfile(); }, 900);
    return p;
  }

  function flushProfile() {
    if (_saveTimer) { clearTimeout(_saveTimer); _saveTimer = null; }
    return _persistProfile();
  }

  // Best-effort flush when the page is hidden / unloaded so progress isn't lost.
  window.addEventListener('pagehide', function () { flushProfile(); });
  document.addEventListener('visibilitychange', function () {
    if (document.visibilityState === 'hidden') flushProfile();
  });

  function start() {
    loadClerk()
      .then(function () { return window.Clerk.load(); })
      .then(function () {
        renderHeader();
        wireCtas();
        enforceGate();
        if (window.Clerk.user) _loadProfile();
        window.Clerk.addListener(function () { renderHeader(); });
        readyResolve(window.Clerk);
      })
      .catch(function (err) {
        console.error(err);
        if (document.body.hasAttribute('data-require-auth')) window.location.href = '/';
      });
  }

  // Expose helpers for page-specific scripts (e.g. /subscribe, /trainer).
  window.RTAuth = {
    ready: ready,
    hasActiveSub: hasActiveSub,
    // True when the visitor is NOT entitled to full access (signed out, or signed in without a
    // subscription). Folds in isComped() via hasActiveSub(), so subscribers/comped -> false.
    isFreeMode: function () { return !hasActiveSub(); },
    PLAN_KEY: PLAN_KEY,
    TRAINER_URL: TRAINER_URL,
    SUBSCRIBE_URL: SUBSCRIBE_URL,
    // Per-user progress/preferences store (Clerk unsafeMetadata-backed).
    profile: {
      get: getProfile,
      save: saveProfile,
      flush: flushProfile,
      isReady: function () { return _profileReady; },
      SCHEMA: PROFILE_SCHEMA
    }
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start);
  } else {
    start();
  }
})();
