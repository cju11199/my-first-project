// TextureUtils.js — minimal stub for the vendored flat three layout.
// The procedural TrueBeam model uses NO textures, so GLTFExporter never needs the
// real KTX2/texture decompressor. Provide a no-op so the exporter's static import
// resolves under both the browser importmap and Node headless export.
export function decompress(/* texture, maxTextureSize, renderer */) {
  return null; // no compressed textures in this scene
}
export default { decompress };
