// export-glb.mjs — headless .glb export of the procedural TrueBeam (no browser).
//
//   node assets/truebeam/export-glb.mjs [out.glb] [--pose k=v,...] [--no-edu]
//
// Builds the model from truebeam-model.js against the VENDORED flat three.js
// (assets/truebeam/vendor/three.module.js + GLTFExporter.js) and serializes via
// GLTFExporter (binary). Deterministic, GPU-free, browser-free — CI regenerates
// truebeam.glb on any node host. The exporter's bare `three` specifier and its
// `../utils/TextureUtils.js` dep are satisfied by a self-registered resolve hook +
// the no-op stub in ../utils, so the SAME vendored modules the trainer loads are used.
//
// THREE_PATH (optional) overrides the vendored layout with a real three package dir
// (the one holding build/three.module.js + examples/jsm/exporters/GLTFExporter.js).

import { writeFileSync } from 'node:fs';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { dirname, resolve } from 'node:path';
import { register } from 'node:module';

const __dirname = dirname(fileURLToPath(import.meta.url));
const VENDOR_THREE = resolve(__dirname, 'vendor/three.module.js');

// Resolve the exporter's bare `three` import to the vendored module (headless, CSP-safe).
// Registered before any import of GLTFExporter below. THREE_PATH wins if set.
if (!process.env.THREE_PATH) {
  const hook = pathToFileURL(resolve(__dirname, '_three-resolve-hook.mjs')).href;
  register(hook, import.meta.url);
}

// GLTFExporter's binary path expects browser FileReader/Blob. Node 22 has Blob
// globally; shim a minimal FileReader (readAsArrayBuffer) so the exporter runs headless.
if (typeof globalThis.FileReader === 'undefined') {
  globalThis.FileReader = class {
    readAsArrayBuffer(blob) {
      blob.arrayBuffer().then(ab => {
        this.result = ab; this.onloadend && this.onloadend({ target: this });
      }).catch(err => { this.error = err; this.onerror && this.onerror(err); });
    }
    readAsDataURL(blob) {
      blob.arrayBuffer().then(ab => {
        const b64 = Buffer.from(ab).toString('base64');
        this.result = `data:${blob.type || 'application/octet-stream'};base64,${b64}`;
        this.onloadend && this.onloadend({ target: this });
      }).catch(err => { this.error = err; this.onerror && this.onerror(err); });
    }
  };
}

async function loadThree() {
  const cands = [];
  if (process.env.THREE_PATH) cands.push(resolve(process.env.THREE_PATH, 'build/three.module.js'));
  cands.push(VENDOR_THREE);
  cands.push('three');
  for (const c of cands) {
    try { return await import(c.startsWith('/') ? pathToFileURL(c).href : c); } catch (_) {}
  }
  throw new Error('three.js not found — vendored module missing and no THREE_PATH.');
}
async function loadExporter() {
  const cands = [];
  if (process.env.THREE_PATH)
    cands.push(resolve(process.env.THREE_PATH, 'examples/jsm/exporters/GLTFExporter.js'));
  cands.push(resolve(__dirname, 'vendor/GLTFExporter.js'));
  cands.push('three/examples/jsm/exporters/GLTFExporter.js');
  for (const c of cands) {
    try { return (await import(c.startsWith('/') ? pathToFileURL(c).href : c)).GLTFExporter; } catch (_) {}
  }
  throw new Error('GLTFExporter not found (vendored or under THREE_PATH/examples).');
}

function parsePose(argv) {
  const i = argv.indexOf('--pose'); if (i < 0) return null;
  const pose = {}, couch = {};
  for (const kv of (argv[i + 1] || '').split(',')) {
    const [k, v] = kv.split('='); if (!k) continue; const num = Number(v);
    if (['lat', 'long', 'vert', 'yaw', 'roll', 'pitch'].includes(k)) couch[k] = num; else pose[k] = num;
  }
  if (Object.keys(couch).length) pose.couch = couch;
  return pose;
}

(async () => {
  const THREE = await loadThree();
  const GLTFExporter = await loadExporter();
  const { build } = await import(pathToFileURL(resolve(__dirname, 'truebeam-model.js')).href);

  const out = process.argv[2] && !process.argv[2].startsWith('--')
    ? resolve(process.argv[2]) : resolve(__dirname, 'truebeam.glb');
  const pose = parsePose(process.argv);
  const edu = !process.argv.includes('--no-edu');   // educational overlay baked by default

  const m = build(THREE, { beamStopper: false, patient: true, edu, beamLine: edu, axes: edu });
  if (pose) m.setPose(pose);
  m.root.updateMatrixWorld(true);

  const exporter = new GLTFExporter();
  const glb = await new Promise((res, rej) =>
    exporter.parse(m.root, res, rej, { binary: true, onlyVisible: true, truncateDrawRange: true }));
  const buf = Buffer.from(glb);
  writeFileSync(out, buf);

  let meshes = 0, lines = 0, tris = 0;
  m.root.traverse(n => {
    if (n.isLineSegments || n.isLine) { lines++; return; }
    if (n.isMesh) { meshes++;
      const g = n.geometry; const c = g.index ? g.index.count : g.attributes.position.count; tris += c / 3; }
  });
  console.log(`wrote ${out}  (${(buf.length / 1024).toFixed(1)} KB, ${meshes} meshes, ${lines} lines, ~${tris | 0} tris${edu ? ', +edu' : ''})`);
})().catch(e => { console.error(e); process.exit(1); });
