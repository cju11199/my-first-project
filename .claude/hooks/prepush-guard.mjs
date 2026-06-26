#!/usr/bin/env node
// prepush-guard.mjs — Claude Code PreToolUse hook (matcher: Bash).
//
// Before any `git push`, run the same preflight a careless push would skip:
//   1. allowlist sync  — scripts/check-allowlists.mjs (no deps; always runs, always blocks)
//   2. minify parse    — `node build-trainer.mjs --out` (terser must accept trainer.html +
//                        clerk-auth.js, and the served-output gate invariants must survive)
//
// Contract: read the tool-call JSON on stdin. If it isn't a `git push`, exit 0 (allow) fast.
// On a push, run the checks; exit 2 to BLOCK (stderr is fed back to Claude) if any fail.
// build-trainer needs html-minifier-terser + terser — if they aren't installed we WARN and
// skip only that step (the allowlist check still gates), so a deps-less env can't wedge pushes.

import { spawnSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { rmSync } from 'node:fs';

let raw = '';
try { raw = readFileSync(0, 'utf8'); } catch { /* no stdin */ }

let cmd = '';
try { cmd = (JSON.parse(raw).tool_input || {}).command || ''; } catch { /* not JSON */ }

// Only guard real pushes. (Matches `git push …`, ignores `git push --help`, comments, etc.)
if (!/\bgit\s+push\b/.test(cmd) || /--help\b/.test(cmd)) process.exit(0);

const fail = (msg) => { process.stderr.write('[prepush-guard] ' + msg + '\n'); process.exit(2); };

// 1) Allowlist sync — pure fs, always runs.
const al = spawnSync('node', ['scripts/check-allowlists.mjs'], { encoding: 'utf8' });
if (al.status !== 0) {
  fail('allowlist check FAILED — fix before pushing:\n' + (al.stdout || '') + (al.stderr || ''));
}

// 2) Minify parse / served-output gate — only if the build deps are present.
const probe = spawnSync('node', ['-e', "import('html-minifier-terser').then(()=>import('terser')).then(()=>process.exit(0)).catch(()=>process.exit(7))"], { encoding: 'utf8' });
if (probe.status === 0) {
  const b = spawnSync('node', ['build-trainer.mjs', '--out'], { encoding: 'utf8' });
  // Clean the verify artifacts regardless of outcome (they're gitignored, but don't leave them).
  try { rmSync('trainer.min.html', { force: true }); } catch {}
  try { rmSync('clerk-auth.min.js', { force: true }); } catch {}
  if (b.status !== 0) {
    fail('build-trainer.mjs --out FAILED (minify parse or gate invariant) — fix before pushing:\n' + (b.stdout || '') + (b.stderr || ''));
  }
} else {
  process.stderr.write('[prepush-guard] build deps (html-minifier-terser/terser) not installed — skipped minify check; allowlist check passed.\n');
}

process.exit(0);
