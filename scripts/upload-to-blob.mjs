#!/usr/bin/env node
// Uploads the protected case data into the PRIVATE Vercel Blob store so /api/asset can
// serve it. The keys must match the allowlist in api/asset.mjs exactly (no random suffix).
//
// Two ways to run it:
//   • Locally:  vercel env pull .env.local   (gets BLOB_READ_WRITE_TOKEN)
//               node --env-file=.env.local scripts/upload-to-blob.mjs
//   • Browser-only: the "Upload data to Blob" GitHub Action (.github/workflows/upload-blob.yml)
//     — needs no local files; set the repo secret BLOB_READ_WRITE_TOKEN, then click Run.
//
// Re-runnable any time the data is regenerated (allowOverwrite:true).

import { put } from '@vercel/blob';
import { readFile, readdir } from 'node:fs/promises';
import path from 'node:path';

if (!process.env.BLOB_READ_WRITE_TOKEN) {
  console.error('Missing BLOB_READ_WRITE_TOKEN.');
  console.error('Local: run `vercel env pull .env.local` then `node --env-file=.env.local scripts/upload-to-blob.mjs`.');
  process.exit(1);
}

// Must match the DATASETS allowlist in api/asset.mjs.
const DATASETS = [
  'image_data.js', 'breast_drr_data.js', 'prostate2d_data.js',
  'brain3d_data.js', 'pelvis3d_data.js', 'breast3d_data.js',
  'spine3d_data.js', 'lung3d_data.js', 'prostate3d_data.js', 'pancreas3d_data.js',
  'acousticmr3d_data.js',
  'brain3d_labels_data.js', 'pelvis3d_labels_data.js', 'breast3d_labels_data.js',
  'spine3d_labels_data.js', 'lung3d_labels_data.js', 'prostate3d_labels_data.js',
  'pancreas3d_labels_data.js', 'acousticmr3d_labels_data.js',
];

async function up(key, body, contentType) {
  await put(key, body, { access: 'private', addRandomSuffix: false, allowOverwrite: true, contentType });
  console.log('  ✓ ' + key + ' (' + body.length.toLocaleString() + ' B)');
}

const root = process.cwd();
console.log('Uploading ' + DATASETS.length + ' datasets to private Vercel Blob …');
for (const f of DATASETS) await up(f, await readFile(path.join(root, f)), 'application/javascript');

console.log('Uploading drr/*.png …');
const pngs = (await readdir(path.join(root, 'drr'))).filter((n) => n.endsWith('.png')).sort();
for (const f of pngs) await up('drr/' + f, await readFile(path.join(root, 'drr', f)), 'image/png');

console.log('Done: ' + DATASETS.length + ' datasets + ' + pngs.length + ' DRR PNGs uploaded (private).');
