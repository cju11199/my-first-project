// truebeam-model.js — procedural Varian TrueBeam, IEC 61217, iso at origin, meters, Y-up.
//
// One low-poly model, two consumers: the marketing preview page AND the trainer
// Machine-view panel. Framework-agnostic builder over a three.js module passed in
// (so callers control the THREE version / importmap). No DOM, no globals — pure scene graph.
//
// COORDINATE FRAME (IEC 61217, the frame the trainer already grades against):
//   origin (0,0,0) = isocenter (SAD = 1.0 m from MV source)
//   +X = patient-left   +Y = up (vertical, gantry zenith)   +Z = toward the gantry stand
//   floor plane at Y = -1.2 m (gantry axis 1.2 m above floor)
//   gantry 0deg = beam straight down (-Y), source 1.0 m above iso.
//
// AXES (all rotating pivots pass THROUGH iso so iso never moves):
//   gantry      → about world Z (lateral/stand axis). +deg = CW viewed from couch foot (+Z→-Z)
//   collimator  → about the MV beam central axis (= world Y only at gantry 0; nested under gantry so it tracks)
//   couch yaw   → about Y · roll → about Z · pitch → about X  (all isocentric)
//   couch trans → lat +X · long +Z · vert +Y  (applied BEFORE the isocentric rotations)
//
// PARENTING (load-bearing):
//   World_Root(iso)
//     ├ Stand_Drive_Base                                (static)
//     ├ Gantry_Rotation_Group  [pivot=iso, rot Z]       ← THE master rotation
//     │   ├ Gantry_Face_Cover
//     │   ├ Treatment_Head_Group
//     │   │   └ Collimator_Rotation [pivot on beam axis] └ MLC_Collimator
//     │   ├ BeamStopper                                  (optional)
//     │   ├ kV_Source_Arm   (root→mid→tube, deploy 0..1)
//     │   ├ kV_Detector_Arm (root→mid→panel, deploy 0..1)
//     │   └ MV_Detector_Arm (telescoping, deploy 0..1)
//     └ Couch_6DOF_Group
//         └ Lat→Long→Vert→Yaw→Roll→Pitch → Couch_Top_Patient
//
// LOW-POLY budget: boxes/cylinders only, low segment counts, merged where static.
// Materials are shared singletons (few draw-call material switches). Target < ~6k tris.

export const IEC = Object.freeze({
  SAD: 1.0,          // source→axis (m)
  MV_SID: 1.5,       // MV source→imager
  KV_SID: 1.5,       // kV source→detector
  FLOOR_Y: -1.2,     // floor plane below iso
  GANTRY_AXIS: 'z',  // gantry rotates about world Z
});

// ── shared materials (built once per scene from the caller's THREE) ───────────
function makeMaterials(THREE) {
  const std = (hex, rough, metal, extra) => Object.assign(
    new THREE.MeshStandardMaterial({ color: hex, roughness: rough, metalness: metal }), extra || {});
  return {
    cream:    std(0xEDE9DF, 0.45, 0.05),                 // dominant body covers
    creamDk:  std(0xD8D3C6, 0.5,  0.08),                 // seams / secondary covers
    shell:    std(0xF4F2EC, 0.42, 0.04),                 // bright white rounded covers (head/gantry shells)
    accessory:std(0xC6B888, 0.55, 0.12),                 // beige collimator / accessory tray (the Varian tan block)
    couchMetal:std(0xB0B6BC, 0.38, 0.6),                 // brushed-metal stepped couch pedestal
    faceDark: std(0x34383D, 0.6,  0.25),                 // recessed gantry face (lightened vs near-black)
    headGray: std(0x4A4D52, 0.55, 0.35),                 // exposed mechanism (snout underside)
    blue:     std(0x1B6FC4, 0.35, 0.1, { emissive: 0x06304f, emissiveIntensity: 0.25 }), // Varian accent
    metal:    std(0x9097A0, 0.35, 0.85),                 // exposed metal / target block
    tungsten: std(0x3A3D42, 0.6,  0.45),                 // dull matte MV jaws + MLC leaf comb
    panel:    std(0xC4C9CF, 0.4,  0.1),                  // imager active face (light gray)
    panelHs:  std(0x303338, 0.55, 0.3),                  // imager housing (matte dark)
    couchMetalMid:std(0x9AA0A6, 0.42, 0.55),             // 6DOF pitch/roll module + couch rails
    carbon:   std(0x1C1E22, 0.4,  0.2),                  // couch carbon-fibre top (charcoal)
    skin:     std(0xB7A99A, 0.7,  0.0),                  // patient phantom
    floorDark:std(0x141821, 0.9,  0.0),                  // vault floor (machine pops)
    foam:     std(0x6FB6C8, 0.7,  0.0),                  // immobilization foam (teal)
    beamLit:  Object.assign(new THREE.MeshBasicMaterial({ color: 0x67e8c0, transparent: true, opacity: 0.18 }), {}),
    // ── educational overlay materials (unlit so they read in any lighting) ──────
    mvBeam:   new THREE.LineBasicMaterial({ color: 0x67e8c0, transparent: true, opacity: 0.9 }),  // MV central ray (teal)
    kvBeam:   new THREE.LineBasicMaterial({ color: 0xffb454, transparent: true, opacity: 0.9 }),  // kV central ray (amber)
    isoMark:  new THREE.MeshBasicMaterial({ color: 0xffffff }),                                   // iso reticle
    axisX:    new THREE.LineBasicMaterial({ color: 0xff4d4d }),  // +X patient-left  (red)
    axisY:    new THREE.LineBasicMaterial({ color: 0x4dff7a }),  // +Y up            (green)
    axisZ:    new THREE.LineBasicMaterial({ color: 0x4d9dff }),  // +Z toward stand  (blue)
  };
}

// line factory (2-point segment in the parent's local space)
function seg(THREE, mat, a, b, name) {
  const g = new THREE.BufferGeometry().setFromPoints([
    new THREE.Vector3(a[0], a[1], a[2]), new THREE.Vector3(b[0], b[1], b[2])]);
  const l = new THREE.LineSegments(g, mat); l.name = name || ''; return l;
}

const box = (THREE, w, h, d, mat, name) => {
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat); m.name = name || ''; return m;
};
const cyl = (THREE, rt, rb, h, mat, seg, name) => {
  const m = new THREE.Mesh(new THREE.CylinderGeometry(rt, rb, h, seg || 24), mat); m.name = name || ''; return m;
};
const grp = (THREE, name) => { const g = new THREE.Group(); g.name = name; return g; };
// partial torus (arcDeg < 360 → an OPEN curved C, never a closed ring/bore)
const torus = (THREE, radius, tube, radSeg, tubSeg, arcDeg, mat, name) => {
  const m = new THREE.Mesh(new THREE.TorusGeometry(radius, tube, radSeg || 16, tubSeg || 40,
    (arcDeg || 360) * Math.PI / 180), mat);
  m.name = name || ''; return m;
};

/**
 * build(THREE, opts) → { root, parts, materials, drivers, setPose(pose), readout(pose), bounds }
 *   opts.beamStopper  (default false — omitted on most clinical units)
 *   opts.patient      (default true  — phantom block on the couch)
 *   opts.beamLine     (default false — faint translucent central-ray cylinder for the preview)
 *   opts.edu          (default false — EDUCATIONAL OVERLAY: bright MV + kV beam central-ray
 *                      lines to iso, an iso reticle, color-coded readouts via readout())
 *   opts.axes         (default false — color-coded IEC 61217 axis gnomon at iso:
 *                      +X red (patient-left), +Y green (up), +Z blue (toward stand))
 * All geometry authored in IEC/iso space; a single basis swap can be baked at the
 * root by the caller (we stay Y-up here, which three.js wants natively).
 */
export function build(THREE, opts = {}) {
  const M = makeMaterials(THREE);
  const o = Object.assign({ beamStopper: false, patient: true, beamLine: false, edu: false, axes: false, applicator: false }, opts);

  const root = grp(THREE, 'World_Root');        // = isocenter, never transformed
  const parts = {};

  // ── Stand_Drive_Base (static) — tall rounded-rectangle A-frame on the +Z side ─
  // The gantry drum mounts on its upper front face; its top rises above iso (head-height).
  // A tall STAND (not a thin pole) is what stops the machine reading as a CT bore.
  const stand = grp(THREE, 'Stand_Drive_Base');
  // SHORT, set-back drive base mostly HIDDEN behind the curved gantry mass (in the photo the
  // rigid base barely shows). Top kept below the gantry so it never towers over the head.
  const col = box(THREE, 1.02, 1.8, 0.7, M.cream, 'Stand_Column');
  col.position.set(0, IEC.FLOOR_Y + 0.9, 1.22);     // base on floor; top ~y0.6 (below gantry top)
  // rounded vertical fairing softening the column's front so the base doesn't read boxy
  const colFair = cyl(THREE, 0.56, 0.56, 1.72, M.cream, 32, 'Stand_Fairing');
  colFair.position.set(0, IEC.FLOOR_Y + 0.88, 1.02);
  // rounded vertical corner fairings + a domed top cap so the tower reads smooth, not boxy
  const colEdgeL = cyl(THREE, 0.2, 0.2, 1.72, M.cream, 20, 'Stand_Edge_L'); colEdgeL.position.set(-0.50, IEC.FLOOR_Y + 0.88, 1.0);
  const colEdgeR = cyl(THREE, 0.2, 0.2, 1.72, M.cream, 20, 'Stand_Edge_R'); colEdgeR.position.set( 0.50, IEC.FLOOR_Y + 0.88, 1.0);
  const colTop = new THREE.Mesh(new THREE.SphereGeometry(0.58, 28, 16), M.cream);
  colTop.name = 'Stand_Top'; colTop.scale.set(0.9, 0.5, 0.62); colTop.position.set(0, IEC.FLOOR_Y + 1.74, 1.1);
  const ped = box(THREE, 1.4, 0.16, 1.0, M.creamDk, 'Stand_Pedestal');
  ped.position.set(0, IEC.FLOOR_Y + 0.08, 1.12);
  const standBlue = box(THREE, 0.05, 1.0, 0.02, M.blue, 'Stand_BlueAccent');     // thin Varian-blue channel
  standBlue.position.set(0, 0.0, 0.74);
  // small fixed shoulder where the banana's axle enters the stand (tucked behind the banana;
  // small radius so it never reads as a circular drum face toward the couch).
  const bearingCollar = cyl(THREE, 0.34, 0.34, 0.16, M.creamDk, 32, 'Stand_Bearing_Collar');
  bearingCollar.rotation.x = Math.PI / 2; bearingCollar.position.set(0, 0, 1.02);
  stand.add(col, colFair, colEdgeL, colEdgeR, colTop, ped, standBlue, bearingCollar);
  root.add(stand);
  parts.Stand_Drive_Base = stand;

  // ── Floor (cosmetic, static) ────────────────────────────────────────────────
  const floor = box(THREE, 4.0, 0.04, 3.4, M.floorDark, 'Floor');
  floor.position.set(0, IEC.FLOOR_Y - 0.02, 0.3);
  root.add(floor);
  parts.Floor = floor;

  // ── Gantry_Rotation_Group  (pivot = iso, rotates about Z) ───────────────────
  const gantry = grp(THREE, 'Gantry_Rotation_Group');   // pivot already at origin
  root.add(gantry);
  parts.Gantry_Rotation_Group = gantry;

  // ── C-ARM GANTRY (head on a cantilever arm) ─────────────────────────────────
  const banana = grp(THREE, 'Gantry_Banana');
  const V = THREE.Vector3;
  // The gantry does NOT wrap around iso (that read as a ring/bore from the foot). Instead it's a
  // thick rounded ARM that cantilevers the head out from the rotation hub: the head sits at the top
  // of the arm, the arm leans down-and-back to a modest rounded hub at the rotation axis, and the
  // hub joins the fixed stand behind. The MV EPID hangs off the hub on the opposite (lower) side.
  // From the foot you see the head + the arm behind it, no ring and no flat disc.
  const armPath = new THREE.CatmullRomCurve3([
    new V(0, 0.86, 0.12),   // top — fairs into the head drum (head at z0.05)
    new V(0, 0.55, 0.30),
    new V(0, 0.22, 0.48),
    new V(0, -0.06, 0.62),  // root into the hub on the rotation axis
  ]);
  const armTube = new THREE.Mesh(new THREE.TubeGeometry(armPath, 48, 0.34, 24, false), M.shell);
  armTube.name = 'Gantry_Arm';
  banana.add(armTube);
  const shTop = new THREE.Mesh(new THREE.SphereGeometry(0.40, 22, 18), M.shell);
  shTop.name = 'Gantry_Shoulder_Head'; shTop.position.set(0, 0.82, 0.12); banana.add(shTop);
  // modest rounded HUB at the rotation axis (NOT a big disc) — where the arm meets the stand
  const hub = cyl(THREE, 0.42, 0.46, 0.5, M.shell, 40, 'Gantry_Hub');
  hub.rotation.x = Math.PI / 2; hub.position.z = 0.74;
  banana.add(hub);
  gantry.add(banana);
  parts.Gantry_Body = banana;
  parts.Gantry_FacePlate = hub;
  // axle linking the hub back to the stand
  const axle = cyl(THREE, 0.24, 0.26, 0.7, M.creamDk, 28, 'Gantry_Axle');
  axle.rotation.x = Math.PI / 2; axle.position.set(0, 0, 0.95);   // on the rotation axis, hub → stand
  gantry.add(axle);

  // ── Treatment_Head_Group — bulky rounded-rectangular head hanging toward iso ──
  // Group ORIGIN = MV source/target EXACTLY at SAD (1.0 m) above iso (load-bearing for beam geometry).
  const head = grp(THREE, 'Treatment_Head_Group');
  head.position.set(0, IEC.SAD, 0.05);
  const targetBlk = box(THREE, 0.2, 0.1, 0.2, M.metal, 'MV_Target');
  targetBlk.position.y = 0;
  // bulky SMOOTH rounded head: a slightly-tapered round housing + a clean low dome cap (no facets).
  const headHousing = cyl(THREE, 0.37, 0.4, 0.62, M.shell, 30, 'Head_Housing');
  headHousing.position.y = -0.3;
  const headCrown = new THREE.Mesh(new THREE.SphereGeometry(0.37, 26, 16), M.shell);
  headCrown.name = 'Head_Crown'; headCrown.position.y = 0.0; headCrown.scale.set(1, 0.5, 1);   // low smooth dome matching the housing top
  const headNeck = cyl(THREE, 0.3, 0.3, 0.72, M.shell, 22, 'Head_Neck');
  headNeck.rotation.x = Math.PI / 2; headNeck.position.set(0, -0.04, 0.31);    // faired link back to the set-back drum
  head.add(targetBlk, headHousing, headCrown, headNeck);
  gantry.add(head);
  parts.Treatment_Head_Group = head;

  // Collimator_Rotation — pivot ON the beam central axis (local Y line through iso); rotates as a unit.
  const collim = grp(THREE, 'Collimator_Rotation');
  head.add(collim);
  parts.Collimator_Rotation = collim;
  // dark recessed throat in the head's bottom face (the open mouth reads dark)
  const collCavity = box(THREE, 0.34, 0.1, 0.34, M.faceDark, 'Collimator_Cavity'); collCavity.position.y = -0.55;
  // secondary collimator: X jaws (translate along X) + Y jaws (along Z), forming the rectangular aperture
  const jawXL = box(THREE, 0.04, 0.06, 0.34, M.tungsten, 'Jaws_XL'); jawXL.position.set(-0.08, -0.52, 0);
  const jawXR = box(THREE, 0.04, 0.06, 0.34, M.tungsten, 'Jaws_XR'); jawXR.position.set( 0.08, -0.52, 0);
  const jawYA = box(THREE, 0.34, 0.06, 0.04, M.tungsten, 'Jaws_YA'); jawYA.position.set(0, -0.52, -0.08);
  const jawYB = box(THREE, 0.34, 0.06, 0.04, M.tungsten, 'Jaws_YB'); jawYB.position.set(0, -0.52,  0.08);
  // 120-leaf MLC: two opposed combs of ~12 thin leaves each (the iconic fine leaf-end comb)
  const leafN = 12, leafW = 0.026, leafGap = 0.001, leafLen = 0.16, leafThk = 0.05;
  const bankSpan = leafN * (leafW + leafGap);
  function mlcBank(name, sign) {
    const g = grp(THREE, name);
    for (let i = 0; i < leafN; i++) {
      const lf = box(THREE, leafLen, leafThk, leafW, M.tungsten, '');
      lf.position.set(sign * (leafLen / 2), 0, (i - (leafN - 1) / 2) * (leafW + leafGap));
      g.add(lf);
    }
    g.position.set(sign * 0.03, -0.585, 0);   // tips meet near centre (slightly open default)
    return g;
  }
  const mlcL = mlcBank('MLC_BankL', -1), mlcR = mlcBank('MLC_BankR', +1);
  // beige accessory-mount bezel (the signature warm slide-rail frame) on the head underside
  const accFrame = box(THREE, 0.46, 0.05, 0.46, M.accessory, 'Accessory_Mount'); accFrame.position.y = -0.63;
  const accSlot  = box(THREE, 0.3, 0.06, 0.3, M.faceDark, 'Accessory_Slot');     accSlot.position.y = -0.63;  // dark opening
  collim.add(collCavity, jawXL, jawXR, jawYA, jawYB, mlcL, mlcR, accFrame, accSlot);
  parts._jawXL = jawXL; parts._jawXR = jawXR; parts._mlcL = mlcL; parts._mlcR = mlcR; parts._bankSpan = bankSpan;
  // optional electron applicator — a stepped downward-tapering beige funnel (toggle)
  if (o.applicator) {
    const app = grp(THREE, 'Electron_Applicator'); app.position.y = -0.7;
    const rings = [[0.34, 0.0], [0.26, -0.13], [0.18, -0.26], [0.12, -0.36]];
    rings.forEach(([s, y], i) => { const r = box(THREE, s, 0.03, s, M.accessory, 'App_Ring' + i); r.position.y = y; app.add(r); });
    collim.add(app); parts.Electron_Applicator = app;
  }

  // optional faint central-ray for the preview (head source → iso → MV panel)
  if (o.beamLine) {
    const beam = cyl(THREE, 0.02, 0.02, IEC.MV_SID, M.beamLit, 8, 'Beam_CentralRay');
    beam.position.y = IEC.SAD - IEC.MV_SID / 2;  // from source down past iso to panel
    gantry.add(beam);
    parts.Beam_CentralRay = beam;
  }

  // ── BeamStopper (optional) — opposite the head, 180° across iso (below at gantry 0) ─
  if (o.beamStopper) {
    const stop = grp(THREE, 'BeamStopper');
    const arm = box(THREE, 0.12, 0.5, 0.12, M.headGray, 'Stop_Arm');
    arm.position.y = -0.75;
    const blk = box(THREE, 0.4, 0.3, 0.4, M.metal, 'Stop_Block');
    blk.position.y = -1.05;
    stop.add(arm, blk);
    gantry.add(stop);
    parts.BeamStopper = stop;
  }

  // ── Imaging arms — Varian "Exact arm" robotic booms ─────────────────────────
  // Each is a base housing on the gantry + two NESTED rectangular blade stages that
  // telescope outward along its axis (linear deploy 0..1), plus a fold so they stow
  // flat against the gantry. Built mounted on the gantry so they orbit with it; the
  // kV pair lies on the lateral (X) axis, 90° from the MV beam (the orthogonal imager).
  function exactBoom(name, sign) {                  // sign +1 = +X side, -1 = -X side
    const g = grp(THREE, name);
    const base = box(THREE, 0.34, 0.24, 0.3, M.cream, name + '_Base');     base.position.x = sign * 0.06;
    const s1 = grp(THREE, name + '_Stage1');         // first telescoping stage (nests in base when stowed)
    // links extend OUTBOARD (away from iso) from each stage origin, so the stage origin is the
    // INBOARD tip — the payload mounts there with the whole arm strictly behind it (no link
    // reaches in front of the kV detector's active face).
    const l1 = box(THREE, 0.4, 0.18, 0.22, M.creamDk, name + '_Link1');    l1.position.x = sign * 0.2;
    const s2 = grp(THREE, name + '_Stage2');         // second stage (carries the payload)
    const l2 = box(THREE, 0.4, 0.14, 0.16, M.cream, name + '_Link2');      l2.position.x = sign * 0.2;
    s2.add(l2); s1.add(l1, s2); g.add(base, s1);
    return { root: g, s1, s2 };
  }

  // kV Source (OBI X-ray tube) — patient-left (+X). Payload = a tube housing + collimator.
  const kvSrcBoom = exactBoom('kV_Source_Arm', +1);
  kvSrcBoom.root.position.set(0.58, 0, 0.34);   // emerges from the gantry mass (not floating in front)
  const kvTubeMount = grp(THREE, 'kV_Tube'); kvTubeMount.position.x = 0.2;
  const kvTubeHsg = cyl(THREE, 0.13, 0.13, 0.28, M.panelHs, 20, 'kV_Tube_Housing'); kvTubeHsg.rotation.z = Math.PI / 2;
  const kvColl = box(THREE, 0.11, 0.14, 0.14, M.headGray, 'kV_Collimator'); kvColl.position.x = -0.18;  // beam port faces iso
  kvTubeMount.add(kvTubeHsg, kvColl); kvSrcBoom.s2.add(kvTubeMount);
  gantry.add(kvSrcBoom.root);
  parts.kV_Source_Arm = kvSrcBoom.root;

  // kV Detector (flat-panel imager) — patient-right (-X), across iso from the source.
  const kvDetBoom = exactBoom('kV_Detector_Arm', -1);
  kvDetBoom.root.position.set(-0.58, 0, 0.34);   // emerges from the gantry mass (not floating in front)
  // framed flat-panel detector (matches the photo): WHITE housing frame → thin dark recess
  // line → light-grey active face, set slightly proud; faces +X back at the source.
  // kV detector = LANDSCAPE 40x30 framed panel (smaller + wider-than-tall vs the square MV — a TrueBeam tell)
  // Mounted INBOARD (+X, toward iso) of the boom's last link so the ARM sits BEHIND the panel —
  // the active face (+X) reads as a clean flat panel with no boom/pole in front of it.
  const kvPanMount = grp(THREE, 'kV_Panel'); kvPanMount.position.x = 0.28;
  const kvPanFrame = box(THREE, 0.06, 0.40, 0.50, M.shell, 'kV_Panel_Housing');           // white frame slab
  const kvPanGap   = box(THREE, 0.05, 0.34, 0.44, M.panelHs, 'kV_Panel_Recess'); kvPanGap.position.x = 0.015;  // thin dark recess ring
  const kvPanFace  = box(THREE, 0.04, 0.30, 0.40, M.panel, 'kV_Panel_Face');     kvPanFace.position.x = 0.03;  // light-grey active surface
  // short stub linking the boom end to the panel's BACK (−X) edge — the arm-to-panel joint, behind the face
  const kvPanArm   = box(THREE, 0.18, 0.10, 0.12, M.creamDk, 'kV_Panel_Arm'); kvPanArm.position.x = -0.13;
  kvPanMount.add(kvPanFrame, kvPanGap, kvPanFace, kvPanArm); kvDetBoom.s2.add(kvPanMount);
  gantry.add(kvDetBoom.root);
  parts.kV_Detector_Arm = kvDetBoom.root;

  // ── MV_Detector_Arm (EPID/portal imager) — emerges FROM THE GANTRY, opposite the head ──
  // The arm ROOTS in the gantry drum (lower front), reaches in to the rotation axis, then a
  // vertical telescoping boom drops the EPID to ~0.5 m below iso, in line with the MV beam (−Y).
  // (It must NOT float below iso / appear to rise from the floor — it hangs off the drum.)
  const mvDet = grp(THREE, 'MV_Detector_Arm');                 // child of gantry → orbits with it
  // The EPID reads as a CLEAN FLAT PANEL: the support arm attaches at the panel's BACK EDGE
  // (the +Z side toward the gantry) and runs up behind it — NOTHING rises out of the panel face,
  // and the whole assembly stays below the couch (couch underside ~ -0.06 m).
  // structural mount from the drum's lower front to the back post (below the couch)
  const mvMount = box(THREE, 0.16, 0.16, 0.52, M.cream, 'MV_Mount');
  mvMount.position.set(0, -0.3, 0.44);                         // drum (z~0.62) → back post (z~0.32)
  const mvS1 = grp(THREE, 'MV_Stage1'); mvS1.position.set(0, -0.3, 0);    // fixed reference at mount level
  const mvS2 = grp(THREE, 'MV_Stage2');                        // moving stage: panel + its back arm telescope down together
  // back POST behind the panel + a short LINK from the post to the panel's back edge (an L-arm)
  const mvPost = box(THREE, 0.12, 0.34, 0.12, M.creamDk, 'MV_Post'); mvPost.position.set(0, 0.16, 0.32);
  const mvLink = box(THREE, 0.14, 0.07, 0.34, M.cream, 'MV_ArmLink'); mvLink.position.set(0, 0.0, 0.17);
  // EPID flat panel (square aS1200) — face UP toward iso/head, centred under iso (z0); face stays clean
  const mvPanMount = grp(THREE, 'MV_Panel'); mvPanMount.position.set(0, 0, 0);
  const mvPanFrame = box(THREE, 0.6, 0.06, 0.6, M.shell, 'MV_Panel_Housing');
  const mvPanGap   = box(THREE, 0.52, 0.05, 0.52, M.panelHs, 'MV_Panel_Recess'); mvPanGap.position.y = 0.015;
  const mvPanFace  = box(THREE, 0.48, 0.04, 0.48, M.panel, 'MV_Panel_Face');     mvPanFace.position.y = 0.03;
  mvPanMount.add(mvPanFrame, mvPanGap, mvPanFace);
  mvS2.add(mvPost, mvLink, mvPanMount); mvS1.add(mvS2); mvDet.add(mvMount, mvS1);
  gantry.add(mvDet);
  parts.MV_Detector_Arm = mvDet; parts._mvS1 = mvS1; parts._mvS2 = mvS2;
  parts._kvSrcBoom = kvSrcBoom; parts._kvDetBoom = kvDetBoom;

  // ── Couch chain (independent sibling of the gantry) ─────────────────────────
  const couchRoot = grp(THREE, 'Couch_6DOF_Group');
  root.add(couchRoot);
  // stepped brushed-metal pedestal, OFFSET on the -Z side so the table cantilevers in to iso
  // with nothing solid under iso (full gantry clearance) — a free-floating couch, not a CT slab.
  const cz = -1.42;
  const baseLo  = box(THREE, 0.85, 0.12, 0.95, M.couchMetal, 'Couch_Base');       baseLo.position.set(0, IEC.FLOOR_Y + 0.06, cz);
  const baseMid = box(THREE, 0.70, 0.10, 0.78, M.couchMetal, 'Couch_Base_Step');  baseMid.position.set(0, IEC.FLOOR_Y + 0.17, cz);
  const baseCol = box(THREE, 0.50, 0.08, 0.55, M.couchMetal, 'Couch_Base_Collar');baseCol.position.set(0, IEC.FLOOR_Y + 0.26, cz);
  const couchCol= box(THREE, 0.26, 0.90, 0.30, M.couchMetal, 'Couch_Column');     couchCol.position.set(0, IEC.FLOOR_Y + 0.62, cz);
  // the 6DOF pitch/roll module block — the physical TELL of PerfectPitch (a 4DOF couch lacks it)
  const couchMod= box(THREE, 0.46, 0.12, 0.42, M.couchMetalMid, 'Couch_PitchRollModule'); couchMod.position.set(0, IEC.FLOOR_Y + 1.10, cz + 0.06);
  couchRoot.add(baseLo, baseMid, baseCol, couchCol, couchMod);
  parts.Couch_6DOF_Group = couchRoot;

  // nested 6DOF: translations BEFORE isocentric rotations, all rotation pivots at iso
  const cLat  = grp(THREE, 'Couch_Lat');   couchRoot.add(cLat);
  const cLong = grp(THREE, 'Couch_Long');  cLat.add(cLong);
  const cVert = grp(THREE, 'Couch_Vert');  cLong.add(cVert);
  const cYaw  = grp(THREE, 'Couch_Yaw');   cVert.add(cYaw);   // about Y at iso
  const cRoll = grp(THREE, 'Couch_Roll');  cYaw.add(cRoll);   // about Z at iso
  const cPitch= grp(THREE, 'Couch_Pitch'); cRoll.add(cPitch); // about X at iso
  Object.assign(parts, { Couch_Lat: cLat, Couch_Long: cLong, Couch_Vert: cVert,
                         Couch_Yaw: cYaw, Couch_Roll: cRoll, Couch_Pitch: cPitch });

  // Couch_Top_Patient — carbon tabletop + foam + phantom. The table cantilevers from the
  // pedestal (foot side, -Z) to ~iso and STOPS before the gantry — it must NOT pass through the
  // gantry face (that read as a CT bore). Treated point (iso) sits near the head end of the table.
  const top = grp(THREE, 'Couch_Top_Patient');
  // two-section carbon top: THICK proximal section (pedestal side) steps DOWN to a THIN treatment
  // plank cantilevering toward iso. Both top surfaces aligned at ~y0 (iso height). The plank + rails
  // stop just past iso (front edge ~z+0.14, well clear of the set-back gantry face z≈0.5) so the
  // couch can travel inboard (+Z) for an inferior iso before anything nears the gantry.
  const topThick = box(THREE, 0.53, 0.075, 0.72, M.carbon, 'Couch_Top_ThickProx'); topThick.position.set(0, -0.0375, -1.04);
  const topThin  = box(THREE, 0.53, 0.05,  1.2,  M.carbon, 'Couch_Top_ThinTreat');  topThin.position.set(0, -0.025, -0.46);
  const railL = box(THREE, 0.02, 0.035, 1.6, M.couchMetalMid, 'Couch_RailL'); railL.position.set(-0.255, -0.01, -0.675);
  const railR = box(THREE, 0.02, 0.035, 1.6, M.couchMetalMid, 'Couch_RailR'); railR.position.set( 0.255, -0.01, -0.675);
  top.add(topThick, topThin, railL, railR);
  if (o.patient) {
    const pad = box(THREE, 0.46, 0.02, 1.5, M.foam, 'Couch_Pad'); pad.position.set(0, 0.01, -0.6);
    const phantom = box(THREE, 0.3, 0.2, 1.1, M.skin, 'Patient_Phantom'); phantom.position.set(0, 0.12, -0.55);
    top.add(pad, phantom);
  }
  cPitch.add(top);
  parts.Couch_Top_Patient = top;

  // ── EDUCATIONAL OVERLAY ─────────────────────────────────────────────────────
  // Beam central rays are children of the GANTRY group so they orbit with it and
  // always intersect iso. MV ray = gantry local Y (source +SAD → panel below iso);
  // kV ray = gantry local X (the orthogonal imaging axis, source → detector across iso).
  // The axis gnomon + iso reticle are children of root (the fixed iso frame).
  if (o.edu) {
    const beams = grp(THREE, 'Edu_BeamLines');
    // MV central ray: from the MV source (+SAD on local Y) down through iso to the EPID (~-0.5 past iso)
    const mvRay = seg(THREE, M.mvBeam, [0, IEC.SAD, 0], [0, -(IEC.MV_SID - IEC.SAD), 0], 'MV_CentralRay');
    // kV central ray: orthogonal, along local X (source ~+SAD → detector ~-0.5 past iso)
    const kvRay = seg(THREE, M.kvBeam, [IEC.SAD, 0, 0], [-(IEC.KV_SID - IEC.SAD), 0, 0], 'kV_CentralRay');
    beams.add(mvRay, kvRay);
    gantry.add(beams);
    parts.Edu_BeamLines = beams; parts._mvRay = mvRay; parts._kvRay = kvRay;

    // iso reticle — small bright sphere at the fixed origin (never moves)
    const iso = cyl(THREE, 0.02, 0.02, 0.001, M.isoMark, 16, 'Iso_Marker');
    const isoSphere = new THREE.Mesh(new THREE.SphereGeometry(0.018, 12, 10), M.isoMark);
    isoSphere.name = 'Iso_Reticle';
    root.add(isoSphere);
    parts.Iso_Reticle = isoSphere;
  }

  // Color-coded IEC 61217 axis gnomon at iso (fixed frame): +X red, +Y green, +Z blue.
  if (o.axes) {
    const gn = grp(THREE, 'Edu_Axes');
    const L = 0.35;  // axis arm length (m)
    gn.add(seg(THREE, M.axisX, [0, 0, 0], [L, 0, 0], 'Axis_Xpos'));   // +X patient-left (red)
    gn.add(seg(THREE, M.axisY, [0, 0, 0], [0, L, 0], 'Axis_Ypos'));   // +Y up (green)
    gn.add(seg(THREE, M.axisZ, [0, 0, 0], [0, 0, L], 'Axis_Zpos'));   // +Z toward stand (blue)
    // tiny cone tips so direction reads at a glance
    const tip = (mat, x, y, z, rx, rz) => {
      const c = new THREE.Mesh(new THREE.ConeGeometry(0.022, 0.06, 12), mat);
      c.position.set(x, y, z); c.rotation.set(rx || 0, 0, rz || 0); return c;
    };
    gn.add(tip(M.axisX, L, 0, 0, 0, -Math.PI / 2));  // X cone points +X
    gn.add(tip(M.axisY, 0, L, 0, 0, 0));             // Y cone points +Y
    gn.add(tip(M.axisZ, 0, 0, L, Math.PI / 2, 0));   // Z cone points +Z
    root.add(gn);
    parts.Edu_Axes = gn;
  }

  // ── drivers: pure functions over the named pivots ───────────────────────────
  const D2R = Math.PI / 180;
  const clamp01 = v => v < 0 ? 0 : v > 1 ? 1 : v;
  const drivers = {
    gantryAngle(deg)     { gantry.rotation.z = -deg * D2R; },        // +deg = CW from couch foot
    collimatorAngle(deg) { collim.rotation.y =  deg * D2R; },        // about beam axis (local Y)
    kvDeploy(t) {                                                    // 0 stowed → 1 deployed
      t = clamp01(t);
      kvSrcBoom.root.rotation.z = (1 - t) * 0.5;    // stowed: folded up against the gantry
      kvSrcBoom.s1.position.x = t * 0.24;           // telescope stage 1 out (+X, toward the kV source pt)
      kvSrcBoom.s2.position.x = t * 0.26;           // stage 2 further
    },
    kvDetDeploy(t) {
      t = clamp01(t);
      kvDetBoom.root.rotation.z = -(1 - t) * 0.5;   // stowed: folded up (mirror of the source)
      kvDetBoom.s1.position.x = -t * 0.24;          // telescope out (-X, across iso from the source)
      kvDetBoom.s2.position.x = -t * 0.26;
    },
    mvDeploy(t) {                                                    // telescope the EPID down the beam axis
      t = clamp01(t);
      mvS2.position.y = -0.15 - t * 0.13;   // EPID + its back arm telescope down: ~0.45 m (stowed) → ~0.58 m (deployed) below iso
    },
    mlcField(w, h) {                                                 // metres at iso plane (cosmetic)
      const halfOpen = 0.03 + (w || 0) * 0.5;       // MLC bank + X-jaw half-separation grows with width
      parts._mlcL.position.x = -halfOpen; parts._mlcR.position.x = halfOpen;
      parts._jawXL.position.x = -(0.05 + (w || 0) * 0.5); parts._jawXR.position.x = (0.05 + (w || 0) * 0.5);
      parts._mlcL.scale.z = parts._mlcR.scale.z = 0.5 + (h || 0) * 1.0;   // field height (Z)
    },
    couch(c) {
      c = c || {};
      cLat.position.x  =  (c.lat  || 0);    // +X patient-left
      cLong.position.z =  (c.long || 0);    // +Z toward stand
      cVert.position.y =  (c.vert || 0);    // +Y up
      cYaw.rotation.y  =  (c.yaw   || 0) * D2R;
      cRoll.rotation.z =  (c.roll  || 0) * D2R;
      cPitch.rotation.x=  (c.pitch || 0) * D2R;
    },
  };

  // setPose — one call to apply a full machine state (used by trainer + preview)
  function setPose(p) {
    p = p || {};
    if (p.gantryAngle != null)     drivers.gantryAngle(p.gantryAngle);
    if (p.collimatorAngle != null) drivers.collimatorAngle(p.collimatorAngle);
    if (p.kvDeploy != null)        drivers.kvDeploy(p.kvDeploy);
    if (p.kvDetDeploy != null)     drivers.kvDetDeploy(p.kvDetDeploy);
    if (p.mvDeploy != null)        drivers.mvDeploy(p.mvDeploy);
    if (p.mlcField)                drivers.mlcField(p.mlcField.w, p.mlcField.h);
    if (p.couch)                   drivers.couch(p.couch);
  }

  // ── readout: format a pose into educational, color-coded label rows ──────────
  // Pure (no scene mutation) — the trainer panel renders these beside the 3D view.
  // Sign/direction conventions match the trainer's room-directions readouts.
  function readout(p) {
    p = p || {};
    const c = p.couch || {};
    const cm = (m) => (m == null ? 0 : m * 100);                  // metres → cm (couch readouts are cm)
    const f1 = (n) => (n >= 0 ? '+' : '') + n.toFixed(1);
    const dir = (v, pos, neg) => v === 0 ? '—' : (v > 0 ? pos : neg) + ' ' + Math.abs(v).toFixed(1);
    const lat = cm(c.lat), lng = cm(c.long), vrt = cm(c.vert);
    return {
      gantry:   { label: 'Gantry',   value: ((p.gantryAngle || 0)).toFixed(1) + '°', color: '#ffffff' },
      collim:   { label: 'Collimator', value: ((p.collimatorAngle || 0)).toFixed(1) + '°', color: '#cfd6df' },
      // couch translations — color-coded to the IEC axes (X red, Z blue, Y green)
      // direction words match the trainer's patient-move convention (roomDirections): +Lat=RIGHT,
      // +Lng=INF, +Vrt=POST — so the Machine-View panel reads the same way as the 2D/CBCT console.
      lat:      { label: 'Lat (X)', value: f1(lat) + ' cm', dir: dir(lat, 'RIGHT', 'LEFT'), color: '#ff4d4d' },
      lng:      { label: 'Lng (Z)', value: f1(lng) + ' cm', dir: dir(lng, 'INF', 'SUP'),    color: '#4d9dff' },
      vrt:      { label: 'Vrt (Y)', value: f1(vrt) + ' cm', dir: dir(vrt, 'POST', 'ANT'),   color: '#4dff7a' },
      pitch:    { label: 'Pitch',   value: f1(c.pitch || 0) + '°', dir: dir(c.pitch || 0, 'CW', 'CCW'),  color: '#ff4d4d' },
      roll:     { label: 'Roll',    value: f1(c.roll  || 0) + '°', dir: dir(c.roll  || 0, 'CW', 'CCW'),  color: '#4d9dff' },
      yaw:      { label: 'Yaw',     value: f1(c.yaw   || 0) + '°', dir: dir(c.yaw   || 0, 'CW', 'CCW'),  color: '#4dff7a' },
    };
  }

  // sensible default: gantry 0, imagers stowed, couch home
  setPose({ gantryAngle: 0, collimatorAngle: 0, kvDeploy: 0, kvDetDeploy: 0, mvDeploy: 0,
            couch: { lat: 0, long: 0, vert: 0, yaw: 0, roll: 0, pitch: 0 } });

  return {
    root, parts, materials: M, drivers, setPose, readout, IEC,
    bounds: { floorY: IEC.FLOOR_Y, footprint: [4, 3, 3] },
    dispose() {
      root.traverse(n => { if (n.geometry) n.geometry.dispose(); });
      Object.values(M).forEach(m => m.dispose && m.dispose());
    },
  };
}

export default build;
