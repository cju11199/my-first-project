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
  // enforceGate() bounces blocked free accounts here. subscribe.html MUST stay un-gated
  // (no <body data-require-auth>) — adding the auth gate to it would loop a blocked user
  // infinitely between /trainer and /subscribe.
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

  // A signed-in account that is CONCLUSIVELY not entitled — i.e. it is a registered
  // ("hidden") free account with no active `full_access` subscription and is not comped.
  // Returns true ONLY when we are certain (the Clerk plan check ran and said "no"); a
  // signed-out visitor, a comped user, a subscriber, or an INDETERMINATE check (Clerk not
  // ready / checkAuthorization threw) all return false — we never hard-bounce on uncertainty,
  // so a transient Clerk hiccup can't lock a paying subscriber out. (Paid case DATA is
  // independently protected server-side by /api/asset, so falling through to free-mode in the
  // indeterminate case cannot expose anything paid.)
  function isBlockedFreeAccount() {
    var u = window.Clerk && window.Clerk.user;
    if (!u) return false;            // signed out -> keep the 'Try free' demo (unaffected)
    if (isComped()) return false;    // comped owner / tester / institution -> allowed
    var s = window.Clerk && window.Clerk.session;
    if (s && typeof s.checkAuthorization === 'function') {
      try {
        // Conclusive: authorized === entitled. Block only when it definitively returns false.
        return !s.checkAuthorization({ plan: PLAN_KEY });
      } catch (e) {
        return false;                // indeterminate -> do NOT hard-block
      }
    }
    return false;                    // session/check unavailable -> indeterminate -> do NOT hard-block
  }

  function enforceGate() {
    if (!document.body.hasAttribute('data-require-auth')) return;
    var de = document.documentElement;
    // SECURITY: a signed-in free account that is not comped and has no active subscription is
    // BLOCKED from the trainer — bounce to /subscribe. Redirect BEFORE clearing 'auth-pending'
    // so no trainer content flashes pre-navigation. (Signed-out visitors are NOT blocked here:
    // they fall through to free-mode and keep the 'Try free' demo of the free cases.)
    if (isBlockedFreeAccount()) {
      window.location.replace(SUBSCRIBE_URL);
      return;
    }
    // Subscribers/comped get full access; signed-out visitors get the free-mode demo (only the
    // free cases are playable; paid case data stays protected server-side at /api/asset).
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
        // Re-evaluate on every auth-state change, not just the initial load: if a
        // subscription lapses (or an account signs in) WHILE sitting on the trainer, the gate
        // re-runs and bounces / drops to free-mode without needing a reload. enforceGate is
        // idempotent and fail-open on indeterminate, so this can't wrongly bounce a subscriber.
        window.Clerk.addListener(function () { renderHeader(); enforceGate(); });
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
    // True when the signed-in user has free access via the comp allowlists (owner / tester email /
    // institution domain) rather than a paid subscription. Exposed so /subscribe can keep comped
    // users away from the pricing table — comping is an access grant only, it does NOT cancel or
    // prevent a Clerk Billing subscription, so a comped user who checks out would still be charged.
    isComped: isComped,
    // True when the visitor is NOT entitled to full access (signed out, or signed in without a
    // subscription). Folds in isComped() via hasActiveSub(), so subscribers/comped -> false.
    isFreeMode: function () { return !hasActiveSub(); },
    // True once a Clerk user exists (signed in), regardless of subscription state. Used by the
    // trainer's post-clear "save your progress" nudge, which only targets signed-OUT visitors.
    isSignedIn: function () { return !!(window.Clerk && window.Clerk.user); },
    // Open Clerk's sign-up flow, returning to the trainer afterwards (the anonymous localStorage
    // progress is migrated into the new account on reload — see RTProfile.migrate in trainer.html).
    promptSignUp: function () {
      if (window.Clerk && typeof window.Clerk.openSignUp === 'function') {
        window.Clerk.openSignUp({ forceRedirectUrl: TRAINER_URL });
      }
    },
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
