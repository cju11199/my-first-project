import * as THREE from './vendor/three.module.min.js';

const DEG = Math.PI / 180;

function makeMat(color, opts = {}) {
  return new THREE.MeshStandardMaterial({
    color,
    roughness: opts.roughness ?? 0.34,
    metalness: opts.metalness ?? 0.45,
    transparent: !!opts.transparent,
    opacity: opts.opacity ?? 1,
    emissive: opts.emissive ?? 0x000000,
    emissiveIntensity: opts.emissiveIntensity ?? 0,
    depthWrite: opts.depthWrite ?? true,
    side: opts.side ?? THREE.FrontSide
  });
}

class GantryScene {
  constructor(canvas) {
    this.canvas = canvas;
    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;

    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(34, 1, 0.1, 40);
    // 3/4 view: lifted + slightly off-axis so the bore recedes and the couch/patient
    // sit inside a gantry with real depth (dead-on read as a flat SVG-style disc).
    // The patient lies along Z (the bore axis) and slides head-first into the gantry; the ring
    // rotates about Z. ISO_Z is the transverse plane (ring centre) where the beams converge.
    this.ISO_Z = 0.1;
    // Oblique hero angle: off to the side + above so the ring reads as a ring AND the couch is
    // seen extending out of the bore toward the viewer (dead-down-the-bore would foreshorten it).
    this.orbitTarget = new THREE.Vector3(0, -0.05, 0.2);
    this.camera.position.set(6.4, 3.5, 7.4);
    this.camera.lookAt(this.orbitTarget);
    // drag-to-orbit state: spherical camera about orbitTarget, eased toward the drag goal.
    // theta = azimuth (around +Y), phi = polar from +Y; both eased for smooth, damped motion.
    const off = this.camera.position.clone().sub(this.orbitTarget);
    const r0 = off.length();
    this.orbit = {
      radius: r0, theta: Math.atan2(off.x, off.z), phi: Math.acos(off.y / r0),
      goalRadius: r0, goalTheta: Math.atan2(off.x, off.z), goalPhi: Math.acos(off.y / r0),
      dragging: false, lastX: 0, lastY: 0, home: null
    };
    this.orbit.home = { theta: this.orbit.theta, phi: this.orbit.phi, radius: this.orbit.radius };

    this.state = { angle: 0, target: null, mode: 'kv', beamOn: false, phase: 'ACQUIRE' };
    this.dispAngle = 0;    // eased display angle (trails the commanded gantry for smooth glide)
    this.clock = 0;        // ms, for the beam pulse
    this.lastT = null;
    this.lastW = 0;
    this.lastH = 0;

    this.materials = {
      shell: makeMat(0x5e7692, { roughness: 0.28, metalness: 0.7 }),
      shellDark: makeMat(0x1d2b3c, { roughness: 0.45, metalness: 0.45 }),
      trim: makeMat(0xa8b9cf, { roughness: 0.22, metalness: 0.8 }),
      couch: makeMat(0x2f4158, { roughness: 0.5, metalness: 0.3 }),
      couchTop: makeMat(0x17212e, { roughness: 0.42, metalness: 0.35 }),
      pad: makeMat(0x35485f, { roughness: 0.85, metalness: 0.03 }),
      patient: makeMat(0x24364a, { roughness: 0.65, metalness: 0.05 }),
      skin: makeMat(0xd8a07e, { roughness: 0.72, metalness: 0.02 }),
      gown: makeMat(0xcfd9e6, { roughness: 0.86, metalness: 0.02 }),
      iso: makeMat(0xfff3c4, { roughness: 0.3, metalness: 0.1, emissive: 0xffd45a, emissiveIntensity: 0.9 }),
      laser: makeMat(0xff3b3b, { roughness: 0.5, metalness: 0, transparent: true, opacity: 0.9, emissive: 0xff2020, emissiveIntensity: 0.9, depthWrite: false }),
      kv: makeMat(0x43d6ed, { roughness: 0.25, metalness: 0.35, emissive: 0x0c5a66, emissiveIntensity: 0.25 }),
      mv: makeMat(0xe8c25a, { roughness: 0.28, metalness: 0.35, emissive: 0x5f4200, emissiveIntensity: 0.22 }),
      green: makeMat(0x3ddc97, { roughness: 0.35, metalness: 0.2, emissive: 0x0b4c31, emissiveIntensity: 0.32 }),
      target: makeMat(0xff7a45, { roughness: 0.34, metalness: 0.15, emissive: 0x5f1900, emissiveIntensity: 0.36 }),
      beamKv: makeMat(0x7deeff, { transparent: true, opacity: 0.34, metalness: 0, roughness: 0.9, depthWrite: false, emissive: 0x2dd4ee, emissiveIntensity: 0.55 }),
      beamMv: makeMat(0xff9b60, { transparent: true, opacity: 0.38, metalness: 0, roughness: 0.9, depthWrite: false, emissive: 0xff5d24, emissiveIntensity: 0.52 })
    };

    this.build();
    this.resize();
    this.initOrbit();
    this.updateCamera(0);
    this.render();
    window.addEventListener('resize', () => {
      this.resize();
      this.render();
    });
  }

  // Drag to orbit, wheel to zoom, double-click to reset. Kept lightweight (no OrbitControls
  // vendor file) — pointer deltas feed the spherical goal, the rAF loop eases toward it.
  initOrbit() {
    const c = this.canvas;
    c.style.cursor = 'grab';
    c.style.touchAction = 'none';
    const PHI_MIN = 0.28, PHI_MAX = 1.62, R_MIN = 6.2, R_MAX = 14;
    c.addEventListener('pointerdown', (e) => {
      this.orbit.dragging = true;
      this.orbit.lastX = e.clientX; this.orbit.lastY = e.clientY;
      c.style.cursor = 'grabbing';
      if (c.setPointerCapture) try { c.setPointerCapture(e.pointerId); } catch (_) {}
      this.ensureLoop();
    });
    c.addEventListener('pointermove', (e) => {
      if (!this.orbit.dragging) return;
      const dx = e.clientX - this.orbit.lastX, dy = e.clientY - this.orbit.lastY;
      this.orbit.lastX = e.clientX; this.orbit.lastY = e.clientY;
      this.orbit.goalTheta -= dx * 0.008;
      this.orbit.goalPhi = Math.max(PHI_MIN, Math.min(PHI_MAX, this.orbit.goalPhi - dy * 0.008));
      this.ensureLoop();
    });
    const end = (e) => {
      if (!this.orbit.dragging) return;
      this.orbit.dragging = false;
      c.style.cursor = 'grab';
      if (c.releasePointerCapture && e.pointerId != null) try { c.releasePointerCapture(e.pointerId); } catch (_) {}
    };
    c.addEventListener('pointerup', end);
    c.addEventListener('pointercancel', end);
    c.addEventListener('wheel', (e) => {
      e.preventDefault();
      this.orbit.goalRadius = Math.max(R_MIN, Math.min(R_MAX, this.orbit.goalRadius * (1 + Math.sign(e.deltaY) * 0.08)));
      this.ensureLoop();
    }, { passive: false });
    c.addEventListener('dblclick', () => {
      this.orbit.goalTheta = this.orbit.home.theta;
      this.orbit.goalPhi = this.orbit.home.phi;
      this.orbit.goalRadius = this.orbit.home.radius;
      this.ensureLoop();
    });
  }

  // Ease the spherical camera toward its drag goal and rebuild the camera position.
  updateCamera(dt) {
    const o = this.orbit;
    const k = 1 - Math.pow(0.0008, dt / 1000);   // frame-rate-independent damping
    o.theta += (o.goalTheta - o.theta) * Math.min(1, k);
    o.phi += (o.goalPhi - o.phi) * Math.min(1, k);
    o.radius += (o.goalRadius - o.radius) * Math.min(1, k);
    const sp = Math.sin(o.phi), cp = Math.cos(o.phi);
    this.camera.position.set(
      this.orbitTarget.x + o.radius * sp * Math.sin(o.theta),
      this.orbitTarget.y + o.radius * cp,
      this.orbitTarget.z + o.radius * sp * Math.cos(o.theta)
    );
    this.camera.lookAt(this.orbitTarget);
  }

  cameraSettled() {
    const o = this.orbit;
    return !o.dragging &&
      Math.abs(o.goalTheta - o.theta) < 1e-3 &&
      Math.abs(o.goalPhi - o.phi) < 1e-3 &&
      Math.abs(o.goalRadius - o.radius) < 1e-3;
  }

  build() {
    this.scene.add(new THREE.HemisphereLight(0xd9eefc, 0x071019, 1.6));
    const key = new THREE.DirectionalLight(0xffffff, 2.2);
    key.position.set(-2.8, 3.8, 5.2);
    this.scene.add(key);
    const rim = new THREE.DirectionalLight(0x73d8ff, 0.75);
    rim.position.set(3.2, -1.5, 4);
    this.scene.add(rim);

    // OPEN bore: a tube the couch slides down (axis along Z) with a dark interior + back cap,
    // so the patient recedes head-first into a visible tunnel instead of sitting on a flat wall.
    const boreWall = makeMat(0x141d29, { roughness: 0.6, metalness: 0.3, side: THREE.DoubleSide });
    const bore = new THREE.Mesh(new THREE.CylinderGeometry(2.14, 2.14, 1.8, 96, 1, true), boreWall);
    bore.rotation.x = Math.PI / 2;
    bore.position.z = -1.05;
    this.scene.add(bore);
    const boreBack = new THREE.Mesh(new THREE.CircleGeometry(2.14, 96), this.materials.shellDark);
    boreBack.position.z = -1.92;
    this.scene.add(boreBack);

    const boreLip = new THREE.Mesh(new THREE.TorusGeometry(2.16, 0.05, 16, 128), this.materials.trim);
    boreLip.position.z = -0.16;
    this.scene.add(boreLip);

    // Cable-wrap HARD STOP at gantry 180° (bottom): a real linac can't transit straight
    // down through the couch — mark the no-go zone with a red hazard arc + centre pip.
    const stopMat = makeMat(0xff5a3c, { roughness: 0.4, metalness: 0.2, emissive: 0x5a1400, emissiveIntensity: 0.5 });
    const stopArc = new THREE.Mesh(
      new THREE.TorusGeometry(2.02, 0.05, 12, 64, 26 * DEG),
      stopMat
    );
    stopArc.rotation.z = -Math.PI / 2 - 13 * DEG;   // centre the 26° arc on the bottom (180°)
    stopArc.position.z = 0.08;
    this.scene.add(stopArc);
    const stopPip = new THREE.Mesh(new THREE.SphereGeometry(0.055, 16, 10), stopMat);
    stopPip.position.set(0, -2.02, 0.08);
    this.scene.add(stopPip);

    this.buildCouch();
    this.buildPatient();
    this.buildIso();

    this.rig = new THREE.Group();
    this.scene.add(this.rig);

    const ring = new THREE.Mesh(new THREE.TorusGeometry(1.72, 0.18, 24, 128), this.materials.shell);
    ring.position.z = 0.04;
    this.rig.add(ring);

    const inner = new THREE.Mesh(new THREE.TorusGeometry(1.27, 0.035, 12, 96), this.materials.trim);
    inner.position.z = 0.16;
    this.rig.add(inner);

    const mvArm = new THREE.Mesh(new THREE.BoxGeometry(0.16, 0.48, 0.22), this.materials.shell);
    mvArm.position.set(0, 1.33, 0.18);
    this.rig.add(mvArm);
    const mvHead = new THREE.Mesh(new THREE.BoxGeometry(0.68, 0.42, 0.5), this.materials.shell);
    mvHead.position.set(0, 1.79, 0.28);
    this.rig.add(mvHead);
    const mvColl = new THREE.Mesh(new THREE.BoxGeometry(0.36, 0.16, 0.38), this.materials.shellDark);
    mvColl.position.set(0, 1.5, 0.38);
    this.rig.add(mvColl);

    const epidArm = new THREE.Mesh(new THREE.BoxGeometry(0.13, 0.56, 0.18), this.materials.shell);
    epidArm.position.set(0, -1.29, 0.12);
    this.rig.add(epidArm);
    const epid = new THREE.Mesh(new THREE.BoxGeometry(0.82, 0.18, 0.48), this.materials.shell);
    epid.position.set(0, -1.8, 0.22);
    this.rig.add(epid);

    const kvArm = new THREE.Mesh(new THREE.BoxGeometry(0.55, 0.12, 0.18), this.materials.shell);
    kvArm.position.set(1.31, 0, 0.16);
    this.rig.add(kvArm);
    const kvSource = new THREE.Mesh(new THREE.BoxGeometry(0.32, 0.46, 0.36), this.materials.shell);
    kvSource.position.set(1.76, 0, 0.25);
    this.rig.add(kvSource);

    const kvPanelArm = new THREE.Mesh(new THREE.BoxGeometry(0.58, 0.1, 0.16), this.materials.shell);
    kvPanelArm.position.set(-1.31, 0, 0.12);
    this.rig.add(kvPanelArm);
    const kvPanel = new THREE.Mesh(new THREE.BoxGeometry(0.18, 0.78, 0.42), this.materials.shell);
    kvPanel.position.set(-1.82, 0, 0.2);
    this.rig.add(kvPanel);

    this.mvBeam = new THREE.Mesh(new THREE.ConeGeometry(0.34, 1.34, 36, 1, true), this.materials.beamMv);
    this.mvBeam.position.set(0, 0.77, this.ISO_Z);
    this.mvBeam.renderOrder = 4;
    this.rig.add(this.mvBeam);

    this.kvBeam = new THREE.Mesh(new THREE.ConeGeometry(0.3, 1.36, 36, 1, true), this.materials.beamKv);
    this.kvBeam.rotation.z = -Math.PI / 2;
    this.kvBeam.position.set(0.78, 0, this.ISO_Z);
    this.kvBeam.renderOrder = 4;
    this.rig.add(this.kvBeam);

    this.targetMarker = new THREE.Group();
    const targetDot = new THREE.Mesh(new THREE.SphereGeometry(0.065, 16, 10), this.materials.target);
    targetDot.position.set(0, 2.06, 0.42);
    const targetStem = new THREE.Mesh(new THREE.BoxGeometry(0.035, 0.22, 0.035), this.materials.target);
    targetStem.position.set(0, 1.92, 0.42);
    this.targetMarker.add(targetDot, targetStem);
    this.scene.add(this.targetMarker);

    this.acqMarkers = [
      this.makeViewMarker(this.materials.kv),
      this.makeViewMarker(this.materials.kv)
    ];
    this.acqMarkers.forEach(m => this.scene.add(m));
  }

  // Treatment couch: carbon-fibre top plate + mattress pad + side rails + pedestal, running along
  // Z (INTO the bore). It extends from the pedestal outside the bore (+Z, toward camera) through
  // the ring plane and into the tunnel (-Z). Y is vertical; couch sits just posterior (below +Y).
  buildCouch() {
    const g = new THREE.Group();
    const zc = -0.15;                    // couch centre depth (spans out toward camera + into bore)
    const plate = new THREE.Mesh(new THREE.BoxGeometry(0.66, 0.05, 3.0), this.materials.couchTop);
    plate.position.set(0, -0.255, zc);
    g.add(plate);
    const pad = new THREE.Mesh(new THREE.BoxGeometry(0.58, 0.07, 2.6), this.materials.pad);
    pad.position.set(0, -0.205, zc);
    g.add(pad);
    [-0.31, 0.31].forEach(dx => {                       // side rails
      const rail = new THREE.Mesh(new THREE.BoxGeometry(0.04, 0.055, 3.0), this.materials.trim);
      rail.position.set(dx, -0.235, zc);
      g.add(rail);
    });
    // pedestal + base sit at the foot end, OUTSIDE the bore (toward the camera)
    const pedestal = new THREE.Mesh(new THREE.BoxGeometry(0.42, 0.7, 0.5), this.materials.couch);
    pedestal.position.set(0, -0.62, 1.2);
    g.add(pedestal);
    const base = new THREE.Mesh(new THREE.BoxGeometry(0.66, 0.1, 0.78), this.materials.couch);
    base.position.set(0, -0.96, 1.2);
    g.add(base);
    this.scene.add(g);
  }

  // Supine patient lying head-to-foot along Z, resting on the couch (posterior at -Y), draped in a
  // gown. Head-first into the bore (-Z), feet out toward the camera (+Z); iso at the mid-torso.
  buildPatient() {
    const Y = 0.0, Z = this.ISO_Z;       // torso centreline through isocentre (0,0,ISO_Z)
    const p = new THREE.Group();
    const cyl = (rt, rb, len, mat) => {  // capsule-ish limb lying along Z
      const m = new THREE.Mesh(new THREE.CylinderGeometry(rt, rb, len, 20), mat);
      m.rotation.x = Math.PI / 2;        // orient length along Z
      return m;
    };
    const head = new THREE.Mesh(new THREE.SphereGeometry(0.15, 24, 18), this.materials.skin);
    head.scale.set(0.92, 1, 1.15);
    head.position.set(0, Y + 0.02, Z - 0.86);          // head deepest into the bore
    p.add(head);
    const neck = cyl(0.07, 0.08, 0.12, this.materials.skin); neck.position.set(0, Y, Z - 0.7); p.add(neck);
    const torso = cyl(0.2, 0.235, 0.72, this.materials.gown); torso.position.set(0, Y, Z - 0.28); p.add(torso);
    const shoulder = new THREE.Mesh(new THREE.SphereGeometry(0.235, 20, 14), this.materials.gown);
    shoulder.scale.set(1.05, 1, 0.7); shoulder.position.set(0, Y, Z - 0.62); p.add(shoulder);
    const pelvis = cyl(0.235, 0.2, 0.34, this.materials.gown); pelvis.position.set(0, Y - 0.01, Z + 0.25); p.add(pelvis);
    [-1, 1].forEach(s => {                               // legs, separated left/right along X
      const thigh = cyl(0.11, 0.085, 0.62, this.materials.gown);
      thigh.position.set(s * 0.12, Y - 0.03, Z + 0.72); p.add(thigh);
      const shin = cyl(0.075, 0.05, 0.6, this.materials.skin);
      shin.position.set(s * 0.11, Y - 0.05, Z + 1.3); p.add(shin);
      const arm = cyl(0.07, 0.06, 0.62, this.materials.gown);
      arm.position.set(s * 0.27, Y - 0.04, Z - 0.24); p.add(arm);
    });
    this.scene.add(p);
  }

  // Isocentre marked ON the patient at the ring centre where the beams converge: a glowing point,
  // a transverse target reticle encircling the body cross-section, and red room-laser cross-lines
  // through the body (sup-inf along the bore Z, ant-post Y, lateral X).
  buildIso() {
    const g = new THREE.Group();
    g.position.set(0, 0, this.ISO_Z);
    const dot = new THREE.Mesh(new THREE.SphereGeometry(0.045, 20, 14), this.materials.iso);
    dot.renderOrder = 6; g.add(dot);
    const ring = new THREE.Mesh(new THREE.TorusGeometry(0.28, 0.014, 12, 64), this.materials.iso);
    ring.renderOrder = 6; g.add(ring);   // transverse reticle in the XY plane, encircling the torso
    const line = (len, axis) => {
      const m = new THREE.Mesh(new THREE.CylinderGeometry(0.006, 0.006, len, 8), this.materials.laser);
      if (axis === 'x') m.rotation.z = Math.PI / 2;
      if (axis === 'z') m.rotation.x = Math.PI / 2;
      m.renderOrder = 5; return m;
    };
    g.add(line(0.66, 'x'), line(0.62, 'y'), line(1.0, 'z'));
    this.isoMarker = g;
    this.scene.add(g);
  }

  makeViewMarker(mat) {
    const group = new THREE.Group();
    const tick = new THREE.Mesh(new THREE.BoxGeometry(0.04, 0.28, 0.035), mat);
    tick.position.set(0, 2.08, 0.46);
    group.add(tick);
    return group;
  }

  resize() {
    const w = this.canvas.clientWidth || 128;
    const h = this.canvas.clientHeight || 116;
    if (w === this.lastW && h === this.lastH) return;
    this.lastW = w;
    this.lastH = h;
    this.renderer.setSize(w, h, false);
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
  }

  update(state = {}) {
    this.state = { ...this.state, ...state };
    // On a large commanded jump (reset / case switch) snap the display so it doesn't
    // spin the long way round; small deltas glide via the eased loop below.
    const angle = Number.isFinite(this.state.angle) ? this.state.angle : 0;
    if (Math.abs(angDiff(this.dispAngle, angle)) > 90) this.dispAngle = angle;
    this.ensureLoop();
  }

  // Apply the current state to the scene. `t` is a monotonic ms clock for the beam pulse.
  apply(dt) {
    this.resize();   // cheap no-op unless the panel actually reflowed (fixes reflow-without-window-resize)

    const angle = Number.isFinite(this.state.angle) ? this.state.angle : 0;
    // ease the displayed angle toward the commanded gantry (shortest wrap-aware arc)
    const k = 1 - Math.pow(0.0025, dt / 1000);   // ~frame-rate-independent smoothing
    this.dispAngle += angDiff(this.dispAngle, angle) * Math.min(1, k);
    this.rig.rotation.z = -this.dispAngle * DEG;

    const showTarget = this.state.target !== null && this.state.target !== undefined && this.state.phase === 'ACQUIRE';
    this.targetMarker.visible = showTarget;
    if (showTarget) this.targetMarker.rotation.z = -this.state.target * DEG;

    const views = Array.isArray(this.state.views) ? this.state.views : [];
    this.acqMarkers.forEach((m, i) => {
      const v = views[i];
      m.visible = !!v;
      if (!v) return;
      m.rotation.z = -(v.angle || 0) * DEG;
      const done = !!(this.state.acquired && this.state.acquired[i]);
      const base = v.mv ? this.materials.mv : this.materials.kv;   // gold for MV/EPID views, blue for kV
      m.children.forEach(c => c.material = done ? this.materials.green : base);
    });

    const beamOn = !!this.state.beamOn;
    const mode = this.state.mode === 'mv' ? 'mv' : 'kv';
    const beam = mode === 'mv' ? this.mvBeam : this.kvBeam;
    const other = mode === 'mv' ? this.kvBeam : this.mvBeam;
    other.visible = false;
    beam.visible = beamOn;
    if (beamOn) {
      // pulse the live beam so an exposure reads as active, not a static cone
      const p = 0.5 + 0.5 * Math.sin(this.clock / 130);
      beam.material.opacity = 0.24 + 0.26 * p;
      beam.material.emissiveIntensity = (mode === 'mv' ? 0.4 : 0.42) + 0.4 * p;
      beam.scale.setScalar(0.97 + 0.05 * p);
    }
  }

  ensureLoop() {
    if (this._raf) return;
    const tick = (t) => {
      const dt = this.lastT == null ? 16 : Math.min(64, t - this.lastT);
      this.lastT = t;
      this.clock += dt;
      this.updateCamera(dt);
      this.apply(dt);
      this.render();
      // keep animating while the gantry is gliding, a beam is pulsing, or the camera is
      // still orbiting toward its drag goal; otherwise idle to save the GPU.
      const gantrySettled = Math.abs(angDiff(this.dispAngle, this.state.angle || 0)) < 0.05;
      if (gantrySettled && !this.state.beamOn && this.cameraSettled()) { this._raf = null; this.lastT = null; return; }
      this._raf = requestAnimationFrame(tick);
    };
    this._raf = requestAnimationFrame(tick);
  }

  render() {
    this.renderer.render(this.scene, this.camera);
  }
}

// shortest signed angular difference b→a in degrees, in (-180, 180]
function angDiff(a, b) { let d = (a - b) % 360; if (d > 180) d -= 360; if (d <= -180) d += 360; return d; }

const api = {
  instance: null,
  init() {
    const canvas = document.getElementById('conGantry3D');
    if (!canvas || this.instance) return;
    try {
      this.instance = new GantryScene(canvas);
      const viz = canvas.closest('.con-viz');
      if (viz) viz.classList.add('has-3d');
      if (window.CONSOLE && window.CONSOLE._dbg && window.CONSOLE._dbg.state) {
        const s = window.CONSOLE._dbg.state();
        const views = window.CONSOLE._dbg.views ? window.CONSOLE._dbg.views().map(v => ({
          slot: v.slot,
          label: v.label,
          angle: (v.angles && v.angles[0]) || (window.CONSOLE._dbg.viewAngles[v.slot] || [0])[0]
        })) : [];
        this.update({ angle: s.gantry || 0, target: s.motTarget, phase: s.phase, acquired: s.acquired, views });
      }
    } catch (err) {
      console.warn('3D gantry unavailable; using SVG fallback.', err);
    }
  },
  update(state) {
    if (!this.instance) this.init();
    if (this.instance) this.instance.update(state);
  }
};

if (typeof window !== 'undefined' && typeof document !== 'undefined') {
  window.Gantry3D = api;
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => api.init(), { once: true });
  } else {
    api.init();
  }
}

export { api as Gantry3D };
