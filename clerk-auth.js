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
  // Add your Clerk user id (preferred — opaque; Clerk Dashboard -> Users -> your
  // user -> copy User ID) and/or the email you sign in with (lowercase).
  var COMP_USER_IDS = []; // e.g. 'user_2abcDEF456...'
  var COMP_EMAILS = ['cju1999@pm.me', 'cju11199@pm.me']; // owner — full access, no subscription
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
      // Exact-email allowlist (owner/testers): any email on the account, verified or not.
      if (allowEmails.indexOf(addr) !== -1) return true;
      // Domain allowlist (students): require a VERIFIED email at the domain (or a
      // subdomain) so it can't be faked with an unverified address.
      var v = emails[i].verification;
      if (v && v.status === 'verified' && allowDomains.length) {
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
    if (!window.Clerk || !window.Clerk.user) {
      window.Clerk.redirectToSignIn({ signInForceRedirectUrl: window.location.pathname });
    } else if (hasActiveSub()) {
      document.documentElement.classList.remove('auth-pending');
    } else {
      // Signed in but not subscribed -> send to checkout.
      window.location.href = SUBSCRIBE_URL;
    }
  }

  function start() {
    loadClerk()
      .then(function () { return window.Clerk.load(); })
      .then(function () {
        renderHeader();
        wireCtas();
        enforceGate();
        window.Clerk.addListener(function () { renderHeader(); });
        readyResolve(window.Clerk);
      })
      .catch(function (err) {
        console.error(err);
        if (document.body.hasAttribute('data-require-auth')) window.location.href = '/';
      });
  }

  // Expose helpers for page-specific scripts (e.g. /subscribe).
  window.RTAuth = {
    ready: ready,
    hasActiveSub: hasActiveSub,
    PLAN_KEY: PLAN_KEY,
    TRAINER_URL: TRAINER_URL
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start);
  } else {
    start();
  }
})();
