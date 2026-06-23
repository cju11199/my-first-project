#!/usr/bin/env node
/* build-trainer.mjs — produce the minified copies of trainer.html + clerk-auth.js that
 * Vercel serves, while the readable, commented sources stay in the repo.
 *
 * WHY: the readable, fully-commented sources are the working files (humans + the automated
 * content PRs keep editing them). Shipping them verbatim leaks the design rationale + novel
 * teaching logic (off-bone motion model, DIBH coach, scoring) and narrates the auth/comp scheme.
 * This build strips comments/whitespace and minifies the inline JS/CSS so the SERVED files are
 * opaque, while the repo sources stay readable.
 *
 * NOTE on clerk-auth.js: minification strips the comments that narrate the comp/paywall scheme
 * and mangles the internal structure, but string literals (the comp emails/domains, the public
 * publishable keys) are preserved verbatim — this obscures structure, it does NOT hide those
 * values. The hard gate is the Phase-2 server-side check, not this.
 *
 * HOW IT RUNS:
 *   - On Vercel: `vercel.json` buildCommand runs `node build-trainer.mjs`, which rewrites both
 *     files IN PLACE in the ephemeral build workspace (the committed sources are untouched).
 *     Output directory is the repo root, so /trainer (cleanUrls) + clerk-auth.js serve minified.
 *   - Locally (verification): `node build-trainer.mjs --out` writes trainer.min.html +
 *     clerk-auth.min.js alongside, so the sources are never clobbered. Both are gitignored.
 *
 * SAFETY (do not break the app):
 *   - mangle.toplevel = false  -> NEVER rename top-level/global names. The 90+ inline onclick=
 *     handlers and cross-file globals (data-blob vars like PELVIS3D_VOL, window.RTAuth) reference
 *     globals terser can't see; renaming them would break the app.
 *   - compress.toplevel = false + we never enable property mangling -> object keys (CASES.breast,
 *     VOLCASE filenames, the Clerk option keys {plan}/{forceRedirectUrl}/...), the RTAuth API
 *     surface, and dynamic filename string literals are preserved verbatim.
 *   - caseSensitive + keepClosingSlash -> inline SVG (viewBox etc.) and self-closing tags survive.
 *   - conservativeCollapse -> whitespace runs collapse to a single space but are never fully
 *     removed, so significant spacing between inline elements is preserved (visual identity).
 *   - data-require-auth (the Clerk gate hook) and the <script src> tags are structural, untouched.
 */
import { readFile, writeFile } from 'node:fs/promises';
import { minify as minifyHtml } from 'html-minifier-terser';
import { minify as minifyJs } from 'terser';

const verify = process.argv.includes('--out');   // local verify: write *.min.* alongside, leave sources intact

// Shared terser settings for both the trainer's inline JS and the standalone clerk-auth.js.
const TERSER = {
  compress: { toplevel: false, drop_console: false, drop_debugger: true, passes: 2 },
  mangle: { toplevel: false },          // mangle locals only; globals / cross-file names untouched
  format: { comments: false },          // (mangle.properties stays OFF -> object keys & API names preserved)
};

function report(file, before, after) {
  const pct = (100 * (1 - after / before)).toFixed(1);
  console.log(`[build-trainer] ${file}: ${before.toLocaleString()} B -> ${after.toLocaleString()} B  (-${pct}%)`);
}

// ---- trainer.html (inline JS via terser + CSS via clean-css + HTML) ----
{
  const html = await readFile('trainer.html', 'utf8');
  const out = await minifyHtml(html, {
    removeComments: true,            // strip the design-rationale comments (the point of this build)
    collapseWhitespace: true,
    conservativeCollapse: true,      // keep >=1 space so inline-text spacing is preserved
    caseSensitive: true,             // do NOT lowercase SVG camelCase attrs (viewBox, ...)
    keepClosingSlash: true,          // keep self-closing slashes (inline SVG)
    // leave attributes alone — quotes, booleans, "redundant"/empty attrs all preserved verbatim
    removeAttributeQuotes: false,
    collapseBooleanAttributes: false,
    removeRedundantAttributes: false,
    removeEmptyAttributes: false,
    removeOptionalTags: false,
    sortAttributes: false,
    sortClassName: false,
    minifyCSS: true,
    minifyJS: TERSER,
  });
  await writeFile(verify ? 'trainer.min.html' : 'trainer.html', out, 'utf8');
  report('trainer.html', Buffer.byteLength(html, 'utf8'), Buffer.byteLength(out, 'utf8'));
}

// ---- clerk-auth.js (standalone classic script; all logic is inside one IIFE) ----
{
  const js = await readFile('clerk-auth.js', 'utf8');
  const res = await minifyJs(js, TERSER);
  if (res.error) throw res.error;
  await writeFile(verify ? 'clerk-auth.min.js' : 'clerk-auth.js', res.code, 'utf8');
  report('clerk-auth.js', Buffer.byteLength(js, 'utf8'), Buffer.byteLength(res.code, 'utf8'));
}
