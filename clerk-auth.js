/* Clerk auth for the RT Image Matching Trainer (static site, no build step).
 *
 * - Loads Clerk JS from the instance's frontend API.
 * - Landing page: renders a Sign in button / user menu in the header,
 *   and routes "Start free trial" / "Launch" CTAs through sign-up.
 * - Any page with <body data-require-auth>: gates the page — signed-out
 *   visitors are sent to sign-in. (Subscription enforcement is added in
 *   Phase 2 once Clerk Billing plans exist; for now this checks sign-in.)
 *
 * The publishable key is public by design and safe to ship in client code.
 */
(function () {
  var PUBLISHABLE_KEY = 'pk_test_ZmFuY3ktZmxvdW5kZXItNjMuY2xlcmsuYWNjb3VudHMuZGV2JA';
  var FRONTEND_API = 'fancy-flounder-63.clerk.accounts.dev';
  var TRAINER_URL = '/trainer';

  function loadClerk() {
    return new Promise(function (resolve, reject) {
      if (window.Clerk) return resolve();
      var s = document.createElement('script');
      s.async = true;
      s.crossOrigin = 'anonymous';
      s.setAttribute('data-clerk-publishable-key', PUBLISHABLE_KEY);
      s.src = 'https://' + FRONTEND_API + '/npm/@clerk/clerk-js@5/dist/clerk.browser.js';
      s.onload = resolve;
      s.onerror = function () { reject(new Error('Failed to load Clerk')); };
      document.head.appendChild(s);
    });
  }

  function renderHeader() {
    var slot = document.getElementById('clerk-auth');
    if (!slot) return;
    slot.innerHTML = '';
    if (window.Clerk && window.Clerk.user) {
      var launch = document.createElement('a');
      launch.href = TRAINER_URL;
      launch.className = 'cta';
      launch.innerHTML = 'Launch&nbsp;&rarr;';
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

  // "Start free trial" / "Launch the trainer" CTAs.
  // Signed in  -> go to the trainer (subscription check happens there).
  // Signed out -> open sign-up, then return to the trainer.
  function wireCtas() {
    var ctas = document.querySelectorAll('[data-cta="trial"]');
    Array.prototype.forEach.call(ctas, function (el) {
      el.addEventListener('click', function (e) {
        e.preventDefault();
        if (window.Clerk && window.Clerk.user) {
          window.location.href = TRAINER_URL;
        } else {
          window.Clerk.openSignUp({ forceRedirectUrl: TRAINER_URL });
        }
      });
    });
  }

  function enforceGate() {
    if (!document.body.hasAttribute('data-require-auth')) return;
    if (window.Clerk && window.Clerk.user) {
      document.documentElement.classList.remove('auth-pending');
    } else {
      // Not signed in -> send to sign-in, return here afterward.
      window.Clerk.redirectToSignIn({ signInForceRedirectUrl: window.location.pathname });
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
      })
      .catch(function (err) {
        console.error(err);
        // If auth can't load on a gated page, fail closed.
        if (document.body.hasAttribute('data-require-auth')) window.location.href = '/';
      });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start);
  } else {
    start();
  }
})();
