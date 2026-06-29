// BufferGeometryUtils.js — minimal vendored subset for the flat three layout.
//
// The vendored GLTFLoader statically imports `toTrianglesDrawMode` from this module.
// The full three.js examples/jsm/utils/BufferGeometryUtils.js is large; the procedural
// TrueBeam GLB only ever contains plain TRIANGLES + KHR lines, so that function is never
// actually invoked at load time — but the static import must resolve under both the
// browser importmap and the Node headless export. We ship just `toTrianglesDrawMode`
// (verbatim three r160 behaviour: convert TRIANGLE_STRIP / TRIANGLE_FAN indices to a
// flat TRIANGLES index buffer). Self-contained; depends only on the vendored `three`.
import { BufferGeometry } from 'three';

const TrianglesDrawMode = 0;
const TriangleStripDrawMode = 1;
const TriangleFanDrawMode = 2;

export function toTrianglesDrawMode(geometry, drawMode) {
  if (drawMode === TrianglesDrawMode) {
    console.warn('toTrianglesDrawMode: Geometry already defined as triangles.');
    return geometry;
  }
  if (drawMode === TriangleFanDrawMode || drawMode === TriangleStripDrawMode) {
    let index = geometry.getIndex();
    if (index === null) {
      const indices = [];
      const position = geometry.getAttribute('position');
      if (position !== undefined) {
        for (let i = 0; i < position.count; i++) indices.push(i);
        geometry.setIndex(indices);
        index = geometry.getIndex();
      } else {
        console.error('toTrianglesDrawMode: Undefined position attribute. Processing not possible.');
        return geometry;
      }
    }
    const numberOfTriangles = index.count - 2;
    const newIndices = [];
    if (drawMode === TriangleFanDrawMode) {
      for (let i = 1; i <= numberOfTriangles; i++) {
        newIndices.push(index.getX(0));
        newIndices.push(index.getX(i));
        newIndices.push(index.getX(i + 1));
      }
    } else {
      for (let i = 0; i < numberOfTriangles; i++) {
        if (i % 2 === 0) {
          newIndices.push(index.getX(i));
          newIndices.push(index.getX(i + 1));
          newIndices.push(index.getX(i + 2));
        } else {
          newIndices.push(index.getX(i + 2));
          newIndices.push(index.getX(i + 1));
          newIndices.push(index.getX(i));
        }
      }
    }
    if ((newIndices.length / 3) !== numberOfTriangles) {
      console.error('toTrianglesDrawMode: Unable to generate correct amount of triangles.');
    }
    const newGeometry = geometry.clone();
    newGeometry.setIndex(newIndices);
    newGeometry.clearGroups();
    return newGeometry;
  }
  console.error('toTrianglesDrawMode: Unknown draw mode:', drawMode);
  return geometry;
}

export { BufferGeometry };
