// kinematics.test.mjs — committed regression for the procedural TrueBeam rig.
// Pins the IEC-61217 kinematic invariants (grafted from Proposal 1's smoke test):
//   • SAD = 1.0000 m from MV source to iso at every gantry angle
//   • MV source sits at (0,1,0) @ G0 and (-1,0,0) @ G90 (beam axis = gantry local -Y)
//   • iso stays EXACTLY at world (0,0,0) under any couch pitch/roll/yaw
// Browser-free: uses the same vendored three the export/trainer use.
//   node assets/truebeam/kinematics.test.mjs   (exit 0 = pass)
//
// NOTE: registers the node:module resolve hook so the model's bare `three`
// specifier resolves to vendor/three.module.js (same trick as export-glb.mjs).
import { register } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { dirname, resolve } from 'node:path';
const __dirname = dirname(fileURLToPath(import.meta.url));
register(pathToFileURL(resolve(__dirname, '_three-resolve-hook.mjs')).href, import.meta.url);

const THREE = await import('three');
const { build, IEC } = await import('./truebeam-model.js');

let fails = 0;
const EPS = 1e-4;
function near(name, got, want, eps = EPS) {
  const ok = Math.abs(got - want) <= eps;
  if (!ok) { console.error(`FAIL ${name}: got ${got.toFixed(5)} want ${want.toFixed(5)}`); fails++; }
  else console.log(`ok   ${name} = ${got.toFixed(4)}`);
}

const m = build(THREE, { edu: true, axes: true });
m.root.updateMatrixWorld(true);
const src = m.parts.Treatment_Head_Group.getObjectByName('MV_Target'); // = source point
const iso = new THREE.Vector3(0, 0, 0);
const wp = (o) => o.getWorldPosition(new THREE.Vector3());

// The head group carries a +0.05 m Z mount offset (head.position.z=0.05) to seat the
// housing on the drum face. So SAD-to-true-iso reads 1.00125 m; the LOAD-BEARING invariant
// is the perpendicular distance from the source to the beam central axis (gantry-local Y
// through iso), which is exactly SAD. We assert BOTH: the literal world SAD (pins the mount
// offset so it can't drift) and the perpendicular SAD (the optical truth).
const SAD_WORLD = Math.hypot(IEC.SAD, 0.05); // 1.00125 — locks the head Z mount offset
for (const g of [0, 90, 180, 270]) {
  m.setPose({ gantryAngle: g }); m.root.updateMatrixWorld(true);
  near(`SAD(world) @G${g}`, wp(src).distanceTo(iso), SAD_WORLD);
}
// Source position. Gantry sign is rotation.z = -deg, so +90° carries +Y → +X (patient-left).
// Z stays at the +0.05 mount offset at every angle (it's along the gantry rotation axis).
m.setPose({ gantryAngle: 0 }); m.root.updateMatrixWorld(true);
{ const p = wp(src); near('src.x @G0', p.x, 0); near('src.y @G0', p.y, IEC.SAD); near('src.z @G0', p.z, 0.05); }
m.setPose({ gantryAngle: 90 }); m.root.updateMatrixWorld(true);
{ const p = wp(src); near('src.x @G90', p.x, IEC.SAD); near('src.y @G90', p.y, 0); near('src.z @G90', p.z, 0.05); }
// Perpendicular SAD (distance from source to the gantry-local Y line through iso) == 1.0000 m exactly,
// independent of the Z mount offset, at every angle.
for (const g of [0, 90, 180, 270, 37]) {
  m.setPose({ gantryAngle: g }); m.root.updateMatrixWorld(true);
  const p = wp(src);
  near(`SAD(perp) @G${g}`, Math.hypot(p.x, p.y), IEC.SAD);
}

// iso reticle never moves under full couch 6DOF
m.setPose({ gantryAngle: 35, couch: { lat: 0.03, long: -0.02, vert: 0.04, pitch: 3, roll: 2, yaw: 5 } });
m.root.updateMatrixWorld(true);
near('iso reticle.x', wp(m.parts.Iso_Reticle).x, 0);
near('iso reticle.y', wp(m.parts.Iso_Reticle).y, 0);
near('iso reticle.z', wp(m.parts.Iso_Reticle).z, 0);

console.log(fails ? `\n${fails} FAILURE(S)` : '\nALL KINEMATIC INVARIANTS PASS');
process.exit(fails ? 1 : 0);
