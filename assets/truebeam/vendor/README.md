# Vendored libraries

Self-hosted so the trainer's strict CSP (`script-src 'self'`) can load them — no CDN origin.

- **three.js r160** — `three.module.js` (minified build), `OrbitControls.js`,
  `GLTFExporter.js`, `GLTFLoader.js` from the `examples/jsm` set.
  © three.js authors, **MIT License** (https://github.com/mrdoob/three.js).

The `examples/jsm` modules import the bare specifier `'three'`; pages that use them
resolve it with an inline `<script type="importmap">` pointing at `three.module.js`.
