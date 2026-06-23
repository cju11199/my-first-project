#!/usr/bin/env node
/* build-trainer.mjs — produce the minified copy of trainer.html that Vercel serves at /trainer.
 *
 * WHY: the readable, fully-commented `trainer.html` is the working source (humans + the automated
 * content PRs keep editing it). Shipping that verbatim leaks the design rationale + novel teaching
 * logic (off-bone motion model, DIBH coach, scoring). This build strips comments/whitespace and
 * minifies the inline JS/CSS so the SERVED page is opaque, while the repo source stays readable.
 *
 * HOW IT RUNS:
 *   - On Vercel: `vercel.json` buildCommand runs `node build-trainer.mjs`, which rewrites
 *     trainer.html IN PLACE in the ephemeral build workspace (the committed source is untouched).
 *     Output directory is the repo root, so /trainer (cleanUrls) serves the minified file.
 *   - Locally (verification): `node build-trainer.mjs --out trainer.min.html` writes a separate
 *     file so the source is never clobbered. trainer.min.html is gitignored.
 *
 * SAFETY (do not break the app — see vercel.json / the task spec):
 *   - mangle.toplevel = false  -> NEVER rename top-level/global names. The 90+ inline onclick=
 *     handlers and any cross-file globals (data-blob vars like PELVIS3D_VOL/BREAST_META, names the
 *     api or clerk-auth touch) reference globals terser can't see; renaming them would break the app.
 *   - compress.toplevel = false + we never enable property mangling -> object keys (CASES.breast,
 *     V.dims, VOLCASE filenames) and dynamic filename string literals are preserved verbatim.
 *   - caseSensitive + keepClosingSlash -> inline SVG (viewBox etc.) and self-closing tags survive.
 *   - conservativeCollapse -> whitespace runs collapse to a single space but are never fully removed,
 *     so significant spacing between inline elements is preserved (visual identity).
 *   - data-require-auth (the Clerk gate hook) and the <script src> tags are structural, untouched.
 */
import { readFile, writeFile } from 'node:fs/promises';
import { minify } from 'html-minifier-terser';

const args = process.argv.slice(2);
const outIdx = args.indexOf('--out');
const SRC = 'trainer.html';
const OUT = outIdx >= 0 ? args[outIdx + 1] : SRC;   // default: in-place (Vercel build)

const html = await readFile(SRC, 'utf8');

const minified = await minify(html, {
  // ---- HTML ----
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
  // ---- inline CSS (clean-css, default safe level) ----
  minifyCSS: true,
  // ---- inline JS + event-handler attributes (terser, conservative) ----
  minifyJS: {
    compress: {
      toplevel: false,             // never drop/rename top-level decls (onclick handlers need them)
      drop_console: false,         // keep diagnostics -> behavioral identity
      drop_debugger: true,
      passes: 2,
    },
    mangle: {
      toplevel: false,             // mangle locals only; globals/cross-file names untouched
      // (mangle.properties intentionally left OFF -> object keys & method names preserved)
    },
    format: { comments: false },
  },
});

await writeFile(OUT, minified, 'utf8');

const before = Buffer.byteLength(html, 'utf8');
const after = Buffer.byteLength(minified, 'utf8');
const pct = (100 * (1 - after / before)).toFixed(1);
console.log(`[build-trainer] ${SRC} -> ${OUT}`);
console.log(`[build-trainer] ${before.toLocaleString()} B -> ${after.toLocaleString()} B  (-${pct}%)`);
