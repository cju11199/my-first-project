#!/usr/bin/env node
// One-shot uploader: pushes the protected case data to the private R2 bucket so
// /api/asset can serve it. Run once now, and again whenever a *_data.js / drr PNG
// is regenerated.
//
// Usage (from the repo root):
//   node --env-file=.env.local scripts/upload-to-r2.mjs
//
// Needs these in the environment (an "Object Read & Write" R2 API token):
//   R2_ENDPOINT, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET_NAME
// Install deps first if you haven't:  npm install

import { S3Client, PutObjectCommand } from '@aws-sdk/client-s3';
import { readFile, readdir } from 'node:fs/promises';
import path from 'node:path';

const need = ['R2_ENDPOINT', 'R2_ACCESS_KEY_ID', 'R2_SECRET_ACCESS_KEY', 'R2_BUCKET_NAME'];
const missing = need.filter((k) => !process.env[k]);
if (missing.length) {
  console.error('Missing env vars: ' + missing.join(', '));
  console.error('Run: node --env-file=.env.local scripts/upload-to-r2.mjs');
  process.exit(1);
}

const Bucket = process.env.R2_BUCKET_NAME;
const r2 = new S3Client({
  region: 'auto',
  endpoint: process.env.R2_ENDPOINT,
  credentials: {
    accessKeyId: process.env.R2_ACCESS_KEY_ID,
    secretAccessKey: process.env.R2_SECRET_ACCESS_KEY,
  },
});

// Must match the allowlist in api/asset.mjs.
const DATASETS = [
  'image_data.js', 'breast_drr_data.js', 'prostate2d_data.js',
  'brain3d_data.js', 'pelvis3d_data.js', 'breast3d_data.js',
  'spine3d_data.js', 'lung3d_data.js', 'prostate3d_data.js',
  'brain3d_labels_data.js', 'pelvis3d_labels_data.js', 'breast3d_labels_data.js',
  'spine3d_labels_data.js', 'lung3d_labels_data.js', 'prostate3d_labels_data.js',
];

async function put(key, body, contentType) {
  await r2.send(new PutObjectCommand({ Bucket, Key: key, Body: body, ContentType: contentType }));
  console.log('  ✓ ' + key + ' (' + body.length.toLocaleString() + ' B)');
}

const root = process.cwd();
console.log('Uploading datasets to R2 bucket "' + Bucket + '" ...');
for (const f of DATASETS) {
  await put(f, await readFile(path.join(root, f)), 'application/javascript');
}

console.log('Uploading drr/*.png ...');
const pngs = (await readdir(path.join(root, 'drr'))).filter((n) => n.endsWith('.png')).sort();
for (const f of pngs) {
  await put('drr/' + f, await readFile(path.join(root, 'drr', f)), 'image/png');
}

console.log('Done: ' + DATASETS.length + ' datasets + ' + pngs.length + ' DRR PNGs uploaded.');
