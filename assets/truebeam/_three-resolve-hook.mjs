// _three-resolve-hook.mjs — Node module-resolution hook for headless GLB export.
//
// The vendored three.js `examples/jsm` modules (GLTFExporter.js) import the bare
// specifier `three`. In a browser an inline <script type="importmap"> maps it to the
// vendored build; under Node there is no importmap, so this resolve() hook maps the
// bare `three` specifier to the vendored flat build instead. Registered by
// export-glb.mjs via node:module register(). No effect on any other specifier.
import { pathToFileURL, fileURLToPath } from 'node:url';
import { dirname, resolve as resolvePath } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const VENDOR_THREE = pathToFileURL(resolvePath(__dirname, 'vendor/three.module.js')).href;

export async function resolve(specifier, context, nextResolve) {
  if (specifier === 'three') return { url: VENDOR_THREE, shortCircuit: true };
  return nextResolve(specifier, context);
}
