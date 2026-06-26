#!/usr/bin/env node
// check-allowlists.mjs — verify every case-data file is wired into all three Phase-2
// allowlists, so a new case can't be merged half-plumbed (which 404s it live).
//
// The three lists that must stay in lockstep with the *_data.js files in the repo root:
//   1. scripts/upload-to-blob.mjs   DATASETS [...]      (what the Action uploads to Blob)
//   2. api/asset.mjs                DATASETS new Set([])(what /api/asset will serve)
//   3. .vercelignore                                    (keep the data OFF the public CDN)
//
// Exit 0 = all in sync. Exit 1 = a mismatch (missing or stale entry), with a report.
// No dependencies — pure fs, so it runs anywhere (CI, the pre-push hook, locally).

import { readFile, readdir } from 'node:fs/promises';

const root = process.cwd();

// Every case-data file lives in the repo root and ends with _data.js.
async function dataFiles() {
  const all = await readdir(root);
  return all.filter((f) => /_data\.js$/.test(f)).sort();
}

// Pull the 'something_data.js' string literals out of a source file (covers the array in
// upload-to-blob.mjs and the Set in api/asset.mjs alike — both are quoted literals).
async function literalsIn(path) {
  let txt = '';
  try { txt = await readFile(path, 'utf8'); } catch { return null; }
  const set = new Set();
  for (const m of txt.matchAll(/['"]([a-z0-9_]+_data\.js)['"]/gi)) set.add(m[1]);
  return set;
}

// .vercelignore lists bare filenames, one per line.
async function vercelIgnore() {
  let txt = '';
  try { txt = await readFile('.vercelignore', 'utf8'); } catch { return null; }
  const set = new Set();
  for (const line of txt.split('\n')) {
    const t = line.trim();
    if (/^[a-z0-9_]+_data\.js$/i.test(t)) set.add(t);
  }
  return set;
}

const files = await dataFiles();
const sources = {
  'scripts/upload-to-blob.mjs': await literalsIn('scripts/upload-to-blob.mjs'),
  'api/asset.mjs': await literalsIn('api/asset.mjs'),
  '.vercelignore': await vercelIgnore(),
};

let problems = 0;
const fileSet = new Set(files);
console.log(`Found ${files.length} *_data.js files in the repo root.\n`);

for (const [name, set] of Object.entries(sources)) {
  if (set === null) { console.error(`✗ ${name}: could not read / parse — skipping.`); problems++; continue; }
  const missing = files.filter((f) => !set.has(f));        // file exists but not allowlisted
  const stale = [...set].filter((f) => !fileSet.has(f)).sort(); // listed but no such file
  if (!missing.length && !stale.length) {
    console.log(`✓ ${name}: all ${files.length} in sync.`);
  } else {
    if (missing.length) { console.error(`✗ ${name}: MISSING ${missing.length}: ${missing.join(', ')}`); problems++; }
    if (stale.length)   { console.error(`✗ ${name}: STALE ${stale.length} (no such file): ${stale.join(', ')}`); problems++; }
  }
}

if (problems) {
  console.error(`\n${problems} allowlist problem(s). A case not in all three lists will 404 live (or ship data to the public CDN).`);
  process.exit(1);
}
console.log('\nAll case-data files are wired into upload-to-blob.mjs, api/asset.mjs, and .vercelignore.');
