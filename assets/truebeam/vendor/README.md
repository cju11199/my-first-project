# Vendored libraries

Self-hosted so the trainer's strict CSP (`script-src 'self'`) can load them — no CDN origin.

- **three.js r160** — `three.module.js` (minified build), `OrbitControls.js`,
  `GLTFExporter.js`, `GLTFLoader.js` from the `examples/jsm` set.
  © three.js authors, **MIT License** (https://github.com/mrdoob/three.js).

The `examples/jsm` modules import the bare specifier `'three'`; pages that use them
resolve it with an inline `<script type="importmap">` pointing at `three.module.js`.
Headless Node export (`export-glb.mjs`) maps the same bare `three` via a
`node:module` resolve hook (`../_three-resolve-hook.mjs`) instead of an importmap.

The `examples/jsm` loaders/exporters also reach a sibling `../utils/` dir. We ship the
minimal subset they statically import, in `assets/truebeam/utils/`:
- `TextureUtils.js` — no-op `decompress` (GLTFExporter dep; the model has no textures).
- `BufferGeometryUtils.js` — just `toTrianglesDrawMode` (GLTFLoader dep; never invoked
  for our plain-TRIANGLES + KHR-lines GLB, but the static import must resolve).
