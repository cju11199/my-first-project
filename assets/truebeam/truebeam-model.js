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
    blue:     std(0x0A6CB5, 0.35, 0.1, { emissive: 0x06304f, emissiveIntensity: 0.25 }), // Varian accent
    metal:    std(0x9097A0, 0.35, 0.85),                 // exposed metal / target block
    panel:    std(0xC4C9CF, 0.4,  0.1),                  // imager active face (light gray)
    panelHs:  std(0x303338, 0.55, 0.3),                  // imager housing (matte dark)
    carbon:   std(0x23262B, 0.4,  0.2),                  // couch carbon-fibre top
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
  const o = Object.assign({ beamStopper: false, patient: true, beamLine: false, edu: false, axes: false }, opts);

  const root = grp(THREE, 'World_Root');        // = isocenter, never transformed
  const parts = {};

  // ── Stand_Drive_Base (static) ───────────────────────────────────────────────
  const stand = grp(THREE, 'Stand_Drive_Base');
  // column sits on the +Z (stand) side; gantry cantilevers off its front face toward -Z
  const col = box(THREE, 1.5, 2.6, 1.2, M.cream, 'Stand_Column');
  col.position.set(0, IEC.FLOOR_Y + 1.3, 1.25);     // base on floor, centered ~+Z
  const ped = box(THREE, 1.8, 0.18, 1.5, M.creamDk, 'Stand_Pedestal');
  ped.position.set(0, IEC.FLOOR_Y + 0.09, 1.25);
  stand.add(col, ped);
  root.add(stand);
  parts.Stand_Drive_Base = stand;

  // ── Floor (cosmetic, static) ────────────────────────────────────────────────
  const floor = box(THREE, 4.0, 0.04, 3.4, M.creamDk, 'Floor');
  floor.position.set(0, IEC.FLOOR_Y - 0.02, 0.3);
  floor.material = new THREE.MeshStandardMaterial({ color: 0x141821, roughness: 0.9, metalness: 0 });
  root.add(floor);
  parts.Floor = floor;

  // ── Gantry_Rotation_Group  (pivot = iso, rotates about Z) ───────────────────
  const gantry = grp(THREE, 'Gantry_Rotation_Group');   // pivot already at origin
  root.add(gantry);
  parts.Gantry_Rotation_Group = gantry;

  // Gantry support: a chunky white SHOULDER/yoke off the stand that carries the rotating head —
  // a C-arm, NOT a CT ring. The drum is modest (it must not frame the patient like a bore).
  const drum = cyl(THREE, 0.66, 0.66, 0.66, M.shell, 36, 'Gantry_Drum');   // compact rotating hub
  drum.rotation.x = Math.PI / 2;
  drum.position.set(0, 0, 0.66);
  gantry.add(drum);
  parts.Gantry_Drum = drum;
  // the arm/yoke: a tapered white limb from the hub out to the head at SAD (top at gantry 0),
  // so the head clearly cantilevers over the couch from one side (the reference's defining look).
  const yoke = box(THREE, 0.46, 1.06, 0.5, M.shell, 'Gantry_Arm');
  yoke.position.set(0, 0.5, 0.4);          // spans hub (y0) up toward the head mount (y~1.0)
  gantry.add(yoke);
  parts.Gantry_Arm = yoke;

  // Gantry_Face_Cover — a SOLID WHITE convex hub face (no recess/bore), Varian blue accent + pivot boss.
  const face = grp(THREE, 'Gantry_Face_Cover');
  const facePlate = cyl(THREE, 0.7, 0.58, 0.14, M.shell, 36, 'Face_Outer');    // tapered → convex white front cap
  facePlate.rotation.x = Math.PI / 2; facePlate.position.z = 0.3;
  const blueRing = cyl(THREE, 0.44, 0.44, 0.06, M.blue, 32, 'Face_BlueRing');  // Varian accent
  blueRing.rotation.x = Math.PI / 2; blueRing.position.z = 0.27;
  const hub = cyl(THREE, 0.22, 0.24, 0.18, M.creamDk, 28, 'Face_Hub');         // central pivot boss (light)
  hub.rotation.x = Math.PI / 2; hub.position.z = 0.22;
  face.add(facePlate, blueRing, hub);
  gantry.add(face);
  parts.Gantry_Face_Cover = face;

  // ── Treatment_Head_Group  (hangs off the drum toward iso, along the beam axis) ─
  // At gantry 0 the beam axis is -Y (down); we author the head ABOVE iso (+Y) so the
  // snout points down toward iso. Beam axis (head→iso) = local -Y of the gantry group.
  const head = grp(THREE, 'Treatment_Head_Group');
  // Head GROUP ORIGIN sits exactly at the MV source point = SAD (1.0 m) above iso at G0.
  // The source/target block is centred at the group origin; housing+snout hang toward iso.
  head.position.set(0, IEC.SAD, 0.05);    // group origin = source point, on the beam axis
  const targetBlk = box(THREE, 0.2, 0.1, 0.2, M.metal, 'MV_Target');  // x-ray target = source point
  targetBlk.position.y = 0;               // EXACTLY at SAD (source) — load-bearing for beam geometry
  // Large rounded cream housing — the iconic Varian treatment head, hanging toward iso.
  const headShell = cyl(THREE, 0.34, 0.40, 0.62, M.shell, 28, 'Head_Housing'); // tapered drum along beam (Y)
  headShell.position.y = -0.30;
  const headCrown = new THREE.Mesh(new THREE.SphereGeometry(0.34, 22, 14), M.shell);
  headCrown.name = 'Head_Crown'; headCrown.position.y = 0.01; headCrown.scale.set(1, 0.62, 1);  // rounded top cap
  // short neck tucked inside the shell radius, linking the head to the gantry face (no protruding corners)
  const headNeck = cyl(THREE, 0.3, 0.3, 0.5, M.shell, 20, 'Head_Neck');
  headNeck.rotation.x = Math.PI / 2; headNeck.position.set(0, -0.05, 0.18);      // reaches back toward the drum face
  // beige accessory / collimator tray facing iso (the signature tan block holder)
  const collTray = box(THREE, 0.42, 0.18, 0.42, M.accessory, 'Collimator_Tray');
  collTray.position.y = -0.60;
  const snout = box(THREE, 0.3, 0.12, 0.3, M.headGray, 'Snout');                 // dark mechanism beneath the tray
  snout.position.y = -0.71;
  head.add(headShell, headCrown, headNeck, targetBlk, collTray, snout);
  gantry.add(head);
  parts.Treatment_Head_Group = head;

  // Collimator_Rotation — pivot ON the beam central axis (local Y line through iso).
  // Nested under the head/gantry so it tracks the beam when the gantry rotates.
  const collim = grp(THREE, 'Collimator_Rotation');     // pivot at head local origin, on beam axis
  head.add(collim);
  parts.Collimator_Rotation = collim;

  // MLC_Collimator — leaf bank below the snout; leaves slide perpendicular to beam.
  const mlc = grp(THREE, 'MLC_Collimator');
  mlc.position.y = -0.80;                  // below the collimator tray (toward iso)
  const mlcBody = box(THREE, 0.36, 0.2, 0.36, M.metal, 'MLC_Body');
  const leafL = box(THREE, 0.16, 0.06, 0.34, M.headGray, 'MLC_BankL');
  const leafR = box(THREE, 0.16, 0.06, 0.34, M.headGray, 'MLC_BankR');
  leafL.position.set(-0.05, -0.08, 0); leafR.position.set(0.05, -0.08, 0);  // closed-ish default
  mlc.add(mlcBody, leafL, leafR);
  collim.add(mlc);
  parts.MLC_Collimator = mlc; parts._mlcLeafL = leafL; parts._mlcLeafR = leafR;

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
    const l1 = box(THREE, 0.4, 0.18, 0.22, M.creamDk, name + '_Link1');    // centred on the stage origin
    const s2 = grp(THREE, name + '_Stage2');         // second stage (carries the payload)
    const l2 = box(THREE, 0.4, 0.14, 0.16, M.cream, name + '_Link2');
    s2.add(l2); s1.add(l1, s2); g.add(base, s1);
    return { root: g, s1, s2 };
  }

  // kV Source (OBI X-ray tube) — patient-left (+X). Payload = a tube housing + collimator.
  const kvSrcBoom = exactBoom('kV_Source_Arm', +1);
  kvSrcBoom.root.position.set(0.58, 0, 0.12);
  const kvTubeMount = grp(THREE, 'kV_Tube'); kvTubeMount.position.x = 0.2;
  const kvTubeHsg = cyl(THREE, 0.13, 0.13, 0.28, M.panelHs, 20, 'kV_Tube_Housing'); kvTubeHsg.rotation.z = Math.PI / 2;
  const kvColl = box(THREE, 0.11, 0.14, 0.14, M.headGray, 'kV_Collimator'); kvColl.position.x = -0.18;  // beam port faces iso
  kvTubeMount.add(kvTubeHsg, kvColl); kvSrcBoom.s2.add(kvTubeMount);
  gantry.add(kvSrcBoom.root);
  parts.kV_Source_Arm = kvSrcBoom.root;

  // kV Detector (flat-panel imager) — patient-right (-X), across iso from the source.
  const kvDetBoom = exactBoom('kV_Detector_Arm', -1);
  kvDetBoom.root.position.set(-0.58, 0, 0.12);
  const kvPanMount = grp(THREE, 'kV_Panel'); kvPanMount.position.x = -0.2;
  const kvPanHsg = box(THREE, 0.1, 0.52, 0.52, M.panelHs, 'kV_Panel_Housing');
  const kvPanFace = box(THREE, 0.05, 0.46, 0.46, M.panel, 'kV_Panel_Face'); kvPanFace.position.x = 0.05; // active face → source
  kvPanMount.add(kvPanHsg, kvPanFace); kvDetBoom.s2.add(kvPanMount);
  gantry.add(kvDetBoom.root);
  parts.kV_Detector_Arm = kvDetBoom.root;

  // ── MV_Detector_Arm (EPID/portal imager) — below iso, in line with the head (−Y) ─
  // a vertical telescoping boom (base + 2 nested stages) carrying a large flat panel.
  const mvDet = grp(THREE, 'MV_Detector_Arm'); mvDet.position.y = -0.32;
  const mvBase = box(THREE, 0.28, 0.26, 0.32, M.cream, 'MV_Base');
  const mvS1 = grp(THREE, 'MV_Stage1');
  const mvL1 = box(THREE, 0.22, 0.36, 0.24, M.creamDk, 'MV_Link1');
  const mvS2 = grp(THREE, 'MV_Stage2');
  const mvL2 = box(THREE, 0.18, 0.36, 0.18, M.cream, 'MV_Link2');
  const mvPanMount = grp(THREE, 'MV_Panel'); mvPanMount.position.y = -0.26;
  const mvPanHsg = box(THREE, 0.56, 0.1, 0.56, M.panelHs, 'MV_Panel_Housing');
  const mvPanFace = box(THREE, 0.5, 0.05, 0.5, M.panel, 'MV_Panel_Face'); mvPanFace.position.y = 0.06; // face → iso/head
  mvPanMount.add(mvPanHsg, mvPanFace);
  mvS2.add(mvL2, mvPanMount); mvS1.add(mvL1, mvS2); mvDet.add(mvBase, mvS1);
  gantry.add(mvDet);
  parts.MV_Detector_Arm = mvDet; parts._mvS1 = mvS1; parts._mvS2 = mvS2;
  parts._kvSrcBoom = kvSrcBoom; parts._kvDetBoom = kvDetBoom;

  // ── Couch chain (independent sibling of the gantry) ─────────────────────────
  const couchRoot = grp(THREE, 'Couch_6DOF_Group');
  root.add(couchRoot);
  // stepped brushed-metal pedestal on the -Z (bore) side, reaching up toward iso
  const cz = -1.4;
  const baseLo  = box(THREE, 0.98, 0.12, 1.04, M.couchMetal, 'Couch_Base');       baseLo.position.set(0, IEC.FLOOR_Y + 0.06, cz);
  const baseMid = box(THREE, 0.74, 0.18, 0.82, M.couchMetal, 'Couch_Base_Step');  baseMid.position.set(0, IEC.FLOOR_Y + 0.22, cz);
  const couchCol= box(THREE, 0.48, 0.92, 0.52, M.couchMetal, 'Couch_Column');     couchCol.position.set(0, IEC.FLOOR_Y + 0.77, cz);
  const couchPiv= box(THREE, 0.52, 0.16, 0.66, M.couchMetal, 'Couch_Pivot');      couchPiv.position.set(0, IEC.FLOOR_Y + 1.30, cz + 0.12);
  couchRoot.add(baseLo, baseMid, couchCol, couchPiv);
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
  const tabletop = box(THREE, 0.55, 0.06, 1.7, M.carbon, 'Tabletop');
  tabletop.position.set(0, -0.04, -0.72);   // head end ~z+0.13 (in front of the gantry face), foot at -1.57
  top.add(tabletop);
  if (o.patient) {
    const board = box(THREE, 0.5, 0.04, 1.5, M.foam, 'Immobilization');
    board.position.set(0, -0.005, -0.72);
    const phantom = box(THREE, 0.32, 0.2, 1.2, M.creamDk, 'Patient_Phantom');
    phantom.position.set(0, 0.12, -0.78);   // head of the phantom reaches iso, body extends out toward the foot
    phantom.material = new THREE.MeshStandardMaterial({ color: 0xb7a99a, roughness: 0.7, metalness: 0 });
    top.add(board, phantom);
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
    mvDeploy(t) {                                                    // telescope the EPID below iso
      t = clamp01(t);
      mvS1.position.y = -t * 0.26;          // stage 1 drops
      mvS2.position.y = -t * 0.3;           // stage 2 drops further → panel ~0.5 m beyond iso
    },
    mlcField(w, h) {                                                 // metres at iso plane (cosmetic)
      const s = 0.5; // leaf bank half-separation scales with field width
      parts._mlcLeafL.position.x = -(0.02 + (w || 0) * s);
      parts._mlcLeafR.position.x =  (0.02 + (w || 0) * s);
      parts._mlcLeafL.scale.z = parts._mlcLeafR.scale.z = 0.4 + (h || 0) * 1.2;
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
      lat:      { label: 'Lat (X)', value: f1(lat) + ' cm', dir: dir(lat, 'LEFT', 'RIGHT'), color: '#ff4d4d' },
      lng:      { label: 'Lng (Z)', value: f1(lng) + ' cm', dir: dir(lng, 'SUP', 'INF'),    color: '#4d9dff' },
      vrt:      { label: 'Vrt (Y)', value: f1(vrt) + ' cm', dir: dir(vrt, 'UP', 'DOWN'),    color: '#4dff7a' },
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
