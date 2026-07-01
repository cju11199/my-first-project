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

// A camera-facing text label (canvas texture on a Sprite), so it stays upright + readable from any
// orbit angle and through the gantry. `w` is the world width; height follows the 2:1 canvas aspect.
function paintLabel(cv, text, color) {
  const ctx = cv.getContext('2d');
  ctx.clearRect(0, 0, cv.width, cv.height);
  ctx.font = 'bold 78px system-ui, Arial, sans-serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.shadowColor = 'rgba(0,0,0,0.85)';
  ctx.shadowBlur = 10;
  ctx.fillStyle = color;
  ctx.fillText(text, cv.width / 2, cv.height / 2 + 4);
}
function makeLabel(text, color, w = 0.5) {
  const cw = 256, ch = 128;
  const cv = document.createElement('canvas');
  cv.width = cw; cv.height = ch;
  paintLabel(cv, text, color);
  const tex = new THREE.CanvasTexture(cv);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 4;
  const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true, depthTest: false, depthWrite: false }));
  sp.scale.set(w, w * ch / cw, 1);
  sp.renderOrder = 12;
  sp.userData.cv = cv;   // keep the canvas so the text can be repainted (live readout, turntable)
  return sp;
}
// Repaint an existing makeLabel sprite's text in place.
function setLabel(sprite, text, color) {
  paintLabel(sprite.userData.cv, text, color);
  sprite.material.map.needsUpdate = true;
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
    this.FLOOR_Y = -2.15;   // floor sits below the gantry's lowest point (ring bottom ~ −1.9)
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
    this.detectorGlow = 0; // 0..1 envelope: the opposing imaging panel lights up while beam is on
    this.lastBeamOn = false;
    this.fieldAperture = null; this.apertureLeaves = []; this.apertureCfgKey = '';  // MLC field aperture
    this.amberGlow = 0;    // 0..1 collision-clearance tint on the MV head
    this.armDeploy = { kv: 1, epid: 1 };   // 0=retracted flat against the gantry, 1=extended for imaging
    this.lastRtn = 0;      // last drawn couch turntable angle (rebuild the arc only on change)
    this.liveAngleKey = -1; // last gantry integer drawn on the live readout sprite
    this.lastT = null;
    this.lastW = 0;
    this.lastH = 0;

    this.materials = {
      // TrueBeam-style moulded fibreglass covers: warm ivory/pearl with warm-gray + charcoal details.
      ivory: makeMat(0xe9e4d8, { roughness: 0.55, metalness: 0.06 }),
      ivoryBright: makeMat(0xf4f0e6, { roughness: 0.5, metalness: 0.05 }),
      warmGray: makeMat(0xb3b7bd, { roughness: 0.42, metalness: 0.3 }),
      charcoal: makeMat(0x24272c, { roughness: 0.5, metalness: 0.3 }),
      shell: makeMat(0x5e7692, { roughness: 0.28, metalness: 0.7 }),
      shellDark: makeMat(0x1d2b3c, { roughness: 0.45, metalness: 0.45 }),
      trim: makeMat(0xa8b9cf, { roughness: 0.22, metalness: 0.8 }),
      couch: makeMat(0x2f4158, { roughness: 0.5, metalness: 0.3 }),
      couchTop: makeMat(0x17212e, { roughness: 0.42, metalness: 0.35 }),
      pad: makeMat(0x35485f, { roughness: 0.85, metalness: 0.03 }),
      patient: makeMat(0x24364a, { roughness: 0.65, metalness: 0.05 }),
      skin: makeMat(0xd8a07e, { roughness: 0.72, metalness: 0.02 }),
      gown: makeMat(0xcfd9e6, { roughness: 0.86, metalness: 0.02 }),
      iso: makeMat(0xfff3c4, { roughness: 0.3, metalness: 0.1, emissive: 0xffd45a, emissiveIntensity: 1.2 }),
      laser: makeMat(0x2bff77, { roughness: 0.5, metalness: 0, transparent: true, opacity: 0.95, emissive: 0x18ff5a, emissiveIntensity: 1.4, depthWrite: false }),
      kv: makeMat(0x43d6ed, { roughness: 0.25, metalness: 0.35, emissive: 0x0c5a66, emissiveIntensity: 0.25 }),
      mv: makeMat(0xe8c25a, { roughness: 0.28, metalness: 0.35, emissive: 0x5f4200, emissiveIntensity: 0.22 }),
      green: makeMat(0x3ddc97, { roughness: 0.35, metalness: 0.2, emissive: 0x0b4c31, emissiveIntensity: 0.32 }),
      target: makeMat(0xff7a45, { roughness: 0.34, metalness: 0.15, emissive: 0x5f1900, emissiveIntensity: 0.36 }),
      amber: makeMat(0xff9c3a, { roughness: 0.3, metalness: 0.4, emissive: 0x5a2e00, emissiveIntensity: 0.5 }),
      aperture: makeMat(0x2a3f52, { transparent: true, opacity: 0.5, metalness: 0.2, roughness: 0.7, depthWrite: false }),
      leafBlack: makeMat(0x14161c, { transparent: true, opacity: 0.6, metalness: 0.1, roughness: 0.8, depthWrite: false }),
      beamKv: makeMat(0x7deeff, { transparent: true, opacity: 0.34, metalness: 0, roughness: 0.9, depthWrite: false, emissive: 0x2dd4ee, emissiveIntensity: 0.75 }),
      beamMv: makeMat(0xff9b60, { transparent: true, opacity: 0.38, metalness: 0, roughness: 0.9, depthWrite: false, emissive: 0xff5d24, emissiveIntensity: 0.8 })
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
    this.raycaster = new THREE.Raycaster();
    this.makeOverlays();
    const PHI_MIN = 0.28, PHI_MAX = 1.62, R_MIN = 6.2, R_MAX = 14;
    c.addEventListener('pointerdown', (e) => {
      this.orbit.dragging = true;
      this.orbit.moved = 0;
      this.orbit.lastX = e.clientX; this.orbit.lastY = e.clientY;
      c.style.cursor = 'grabbing';
      this.hideTip();
      this.dismissHint();
      if (c.setPointerCapture) try { c.setPointerCapture(e.pointerId); } catch (_) {}
      this.ensureLoop();
    });
    c.addEventListener('pointermove', (e) => {
      if (!this.orbit.dragging) return;
      const dx = e.clientX - this.orbit.lastX, dy = e.clientY - this.orbit.lastY;
      this.orbit.moved += Math.abs(dx) + Math.abs(dy);
      this.orbit.lastX = e.clientX; this.orbit.lastY = e.clientY;
      this.orbit.goalTheta -= dx * 0.008;
      this.orbit.goalPhi = Math.max(PHI_MIN, Math.min(PHI_MAX, this.orbit.goalPhi - dy * 0.008));
      this.ensureLoop();
    });
    const end = (e) => {
      if (!this.orbit.dragging) return;
      this.orbit.dragging = false;
      c.style.cursor = 'grab';
      if (this.orbit.moved < 6) this.pick(e);   // a click (not a drag) → identify the part
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

  // DOM overlays over the canvas: a click-to-identify tooltip + a one-time "drag to orbit" hint.
  makeOverlays() {
    const host = this.canvas.parentNode;
    if (!host) return;
    if (getComputedStyle(host).position === 'static') host.style.position = 'relative';
    const tip = document.createElement('div');
    tip.style.cssText = 'position:absolute;z-index:6;max-width:190px;padding:6px 9px;border-radius:7px;' +
      'background:rgba(8,12,18,.92);border:1px solid #2b3d52;color:#dce7f2;font:500 11px/1.35 system-ui,sans-serif;' +
      'pointer-events:none;opacity:0;transition:opacity .12s;box-shadow:0 4px 14px rgba(0,0,0,.5)';
    host.appendChild(tip); this.tipEl = tip;
    const hint = document.createElement('div');
    hint.textContent = 'drag to orbit · scroll to zoom · double-click to reset';
    hint.style.cssText = 'position:absolute;left:50%;bottom:8px;transform:translateX(-50%);z-index:6;' +
      'padding:4px 10px;border-radius:20px;background:rgba(8,12,18,.7);color:#8fa4bb;' +
      'font:500 10px/1 system-ui,sans-serif;pointer-events:none;transition:opacity .5s;white-space:nowrap';
    host.appendChild(hint); this.hintEl = hint;
    this.hintTimer = setTimeout(() => this.dismissHint(), 6000);
  }

  dismissHint() {
    if (this.hintEl) { this.hintEl.style.opacity = '0'; }
    if (this.hintTimer) { clearTimeout(this.hintTimer); this.hintTimer = null; }
  }

  hideTip() { if (this.tipEl) this.tipEl.style.opacity = '0'; }

  // Raycast the click; walk up to the nearest tagged .userData.tip and show its label.
  pick(e) {
    if (!this.raycaster || !this.tipEl) return;
    const r = this.canvas.getBoundingClientRect();
    const ndc = new THREE.Vector2(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
    this.raycaster.setFromCamera(ndc, this.camera);
    const hits = this.raycaster.intersectObjects(this.scene.children, true);
    for (const h of hits) {
      let o = h.object;
      while (o && !(o.userData && o.userData.tip)) o = o.parent;
      if (o && o.visible !== false) {
        this.tipEl.textContent = o.userData.tip;
        this.tipEl.style.left = Math.min(e.clientX - r.left + 12, r.width - 200) + 'px';
        this.tipEl.style.top = Math.min(e.clientY - r.top + 10, r.height - 60) + 'px';
        this.tipEl.style.opacity = '1';
        clearTimeout(this.tipHideTimer);
        this.tipHideTimer = setTimeout(() => this.hideTip(), 3800);
        return;
      }
    }
    this.hideTip();
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
    // Warm-neutral studio light so the ivory covers read as fibreglass white, not blue plastic.
    this.scene.add(new THREE.HemisphereLight(0xf1ece1, 0x0a0e14, 1.7));
    const key = new THREE.DirectionalLight(0xfff3e2, 2.3);
    key.position.set(-2.8, 3.8, 5.2);
    this.scene.add(key);
    const rim = new THREE.DirectionalLight(0x73d8ff, 0.55);
    rim.position.set(3.2, -1.5, 4);
    this.scene.add(rim);

    // TrueBeam STAND (fixed): an upright sculpted ivory tower — NOT a CT-style drum. The C-arm
    // (on the rig) emerges from a circular hub on its face and sweeps around the patient. Side
    // pods at couch height are where the kV imaging arms stow; a low plinth grounds it.
    const tower = new THREE.Mesh(new THREE.BoxGeometry(1.7, 4.05, 0.95), this.materials.ivory);
    tower.position.set(0, -0.12, -2.15);
    this.scene.add(tower);
    const shoulderL = new THREE.Mesh(new THREE.BoxGeometry(0.55, 1.6, 0.85), this.materials.ivoryBright);
    shoulderL.position.set(-1.05, 0.4, -2.12);
    this.scene.add(shoulderL);
    const shoulderR = shoulderL.clone();
    shoulderR.position.x = 1.05;
    this.scene.add(shoulderR);
    // kV stow pods hugging the lower sides (the arms fold out of these)
    const podL = new THREE.Mesh(new THREE.BoxGeometry(0.5, 1.05, 0.75), this.materials.ivory);
    podL.position.set(-0.95, -1.15, -2.0);
    this.scene.add(podL);
    const podR = podL.clone();
    podR.position.x = 0.95;
    this.scene.add(podR);
    const plinth = new THREE.Mesh(new THREE.BoxGeometry(2.2, 0.22, 1.3), this.materials.charcoal);
    plinth.position.set(0, -2.05, -2.1);
    this.scene.add(plinth);
    // fixed hub collar on the stand face — the circular seam the C-arm root rotates within
    const hubCollar = new THREE.Mesh(new THREE.TorusGeometry(0.86, 0.05, 12, 64), this.materials.warmGray);
    hubCollar.position.z = -1.64;
    this.scene.add(hubCollar);

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

    // couch + patient live in one movable group so they translate/rotate with the couch
    // encoder values, while the machine isocentre, lasers and gantry stay fixed in space.
    this.table = new THREE.Group();
    this.scene.add(this.table);
    this.tableOff = { x: 0, y: 0, z: 0, rtn: 0 };   // current (eased) couch offset, scene units
    this.tableGoal = { x: 0, y: 0, z: 0, rtn: 0 };  // target from the couch encoder state
    this.caseZCur = 0;   // eased per-case longitudinal slide (puts the treated site at iso)
    this.caseZGoal = 0;
    this.feetFirst = false;   // per-case patient orientation (extremities are feet-first)
    // slider = couch top + patient, telescoping along the bore per case; patientGroup can flip
    // 180° for feet-first, pivoting about ISO_Z so the treated site still lands on isocentre.
    this.slider = new THREE.Group();
    this.table.add(this.slider);
    this.patientGroup = new THREE.Group();
    this.patientGroup.position.z = this.ISO_Z;
    this.patientGroup.userData.tip = 'Patient — supine on the couch, treated site at isocentre.';
    this.slider.add(this.patientGroup);
    this.buildCouch();
    this.buildPatient();
    this.buildIso();

    this.rig = new THREE.Group();
    this.scene.add(this.rig);

    // ROTATING HUB — the disc on the stand face the C-arm root grows out of (its circular seam
    // sits inside the fixed hubCollar on the stand).
    const hub = new THREE.Mesh(new THREE.CylinderGeometry(0.82, 0.82, 0.14, 48), this.materials.ivoryBright);
    hub.rotation.x = Math.PI / 2;
    hub.position.z = -1.62;
    this.rig.add(hub);

    // C-ARM — the TrueBeam's signature swoosh: a wide curved arm sweeping (in the beam plane) from
    // the hub up and over to the treatment head. Approximated as chamfer-tilted ivory segments;
    // at G0 it curves in the Y–Z plane and the whole arm rotates about the bore axis with the rig.
    const seg = (w, h, d, x, y, z, rx) => {
      const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), this.materials.ivory);
      m.position.set(x, y, z); m.rotation.x = rx || 0;
      this.rig.add(m); return m;
    };
    seg(1.05, 0.95, 0.42, 0, 0.5, -1.5, 0);             // root, growing off the hub
    seg(1.05, 0.62, 0.62, 0, 1.02, -1.3, -0.5);         // lower bend
    this.mvArm = seg(1.05, 0.56, 0.74, 0, 1.5, -0.94, -0.85);  // upper bend (shoulder)
    seg(1.0, 0.52, 1.15, 0, 1.86, -0.35, 0);            // horizontal neck reaching over the head

    // TREATMENT HEAD — big two-tier cylinder aimed down the beam, with a machined warm-gray
    // collimator plate and charcoal light-field window on its face (per the reference photos).
    this.mvHead = new THREE.Mesh(new THREE.CylinderGeometry(0.55, 0.55, 0.62, 40), this.materials.ivoryBright.clone());
    this.mvHead.position.set(0, 1.32, this.ISO_Z);
    this.rig.add(this.mvHead);
    const headCap = new THREE.Mesh(new THREE.CylinderGeometry(0.44, 0.44, 0.5, 40), this.materials.ivory);
    headCap.position.set(0, 1.76, this.ISO_Z);
    this.rig.add(headCap);
    const collFace = new THREE.Mesh(new THREE.CylinderGeometry(0.4, 0.44, 0.1, 40), this.materials.warmGray);
    collFace.position.set(0, 0.97, this.ISO_Z);
    this.rig.add(collFace);
    this.mvColl = new THREE.Mesh(new THREE.BoxGeometry(0.34, 0.06, 0.3), this.materials.charcoal);
    this.mvColl.position.set(0, 0.915, this.ISO_Z);
    this.rig.add(this.mvColl);

    // ── Retractable imaging arms (Varian Exact™ robotic arms) ─────────────────────────────
    // On the real TrueBeam the kV source + kV flat panel attach to the ROTATING gantry on
    // motorised three-pivot robotic arms, and the EPID rides its own E-arm opposite the head.
    // They EXTEND for imaging and RETRACT flat against the gantry face for treatment. Modelled
    // here as hinged groups anchored at their gantry mounts: children are built in the DEPLOYED
    // pose; apply() swings each group about its hinge (+ a small pull-in) by the eased deploy
    // fraction in this.armDeploy — kV pair out in kV mode, EPID out in MV mode.
    const armMount = (x, y, z) => { const g = new THREE.Group(); g.position.set(x, y, z); this.rig.add(g); return g; };
    const rel = (mesh, gx, gy, gz, grp) => { mesh.position.set(gx - grp.position.x, gy - grp.position.y, gz - grp.position.z); grp.add(mesh); return mesh; };

    // EPID (MV portal imager) opposite the head: charcoal panel + ivory tray on an angled E-arm.
    this.epidGroup = armMount(0, -0.85, -1.35);
    this.epidArm = new THREE.Mesh(new THREE.BoxGeometry(0.26, 1.9, 0.26), this.materials.ivory);
    rel(this.epidArm, 0, -1.0, -0.75, this.epidGroup);
    this.epidArm.rotation.x = Math.atan2(1.55, -1.05);   // long axis runs hub → panel
    this.epid = new THREE.Mesh(new THREE.BoxGeometry(1.0, 0.09, 0.72), this.materials.charcoal.clone());
    rel(this.epid, 0, -1.62, this.ISO_Z, this.epidGroup);
    const epidTray = new THREE.Mesh(new THREE.BoxGeometry(1.05, 0.05, 0.78), this.materials.ivory);
    rel(epidTray, 0, -1.69, this.ISO_Z, this.epidGroup);

    // kV source arm (+X): straight deployed Exact arm with a warm-gray elbow + source cowl.
    const kvTilt = Math.atan2(0.75, 1.45);   // arm run: (±0.75, 0, +1.45) from mount to couch level
    this.kvSGroup = armMount(0.9, 0, -1.35);
    this.kvArm = new THREE.Mesh(new THREE.BoxGeometry(0.22, 0.22, 1.7), this.materials.ivory);
    rel(this.kvArm, 1.17, 0, -0.78, this.kvSGroup);
    this.kvArm.rotation.y = kvTilt;
    const kvElbow = new THREE.Mesh(new THREE.SphereGeometry(0.12, 18, 12), this.materials.warmGray);
    rel(kvElbow, 1.5, 0, -0.05, this.kvSGroup);
    this.kvSource = new THREE.Mesh(new THREE.BoxGeometry(0.36, 0.6, 0.44), this.materials.ivory);
    rel(this.kvSource, 1.6, 0, this.ISO_Z + 0.02, this.kvSGroup);
    const kvWindow = new THREE.Mesh(new THREE.BoxGeometry(0.03, 0.22, 0.22), this.materials.charcoal);
    rel(kvWindow, 1.41, 0, this.ISO_Z, this.kvSGroup);

    // kV detector arm (−X): beige flat panel + ivory back on the mirrored Exact arm.
    this.kvDGroup = armMount(-0.9, 0, -1.35);
    this.kvPanelArm = new THREE.Mesh(new THREE.BoxGeometry(0.22, 0.22, 1.7), this.materials.ivory);
    rel(this.kvPanelArm, -1.17, 0, -0.78, this.kvDGroup);
    this.kvPanelArm.rotation.y = -kvTilt;
    this.kvPanel = new THREE.Mesh(new THREE.BoxGeometry(0.09, 0.98, 0.72),
      makeMat(0xcfbd96, { roughness: 0.6, metalness: 0.08 }));   // beige detector face (per photos)
    rel(this.kvPanel, -1.7, 0, this.ISO_Z, this.kvDGroup);
    const kvPanelBack = new THREE.Mesh(new THREE.BoxGeometry(0.05, 1.03, 0.78), this.materials.ivory);
    rel(kvPanelBack, -1.77, 0, this.ISO_Z, this.kvDGroup);

    // Component labels — ride the arm groups so they follow deploy/retract + gantry rotation.
    this.mvLabel = makeLabel('MV', '#c99b28', 0.46);
    this.mvLabel.position.set(0, 1.32, 0.78);
    this.rig.add(this.mvLabel);
    this.kvLabel = makeLabel('kV', '#2fb9d8', 0.46);
    rel(this.kvLabel, 1.6, 0, 0.72, this.kvSGroup);

    // Deploy-mechanics tooltips on the arm links themselves.
    const armTip = 'Exact™ robotic arm — motorised pivots extend the imager for imaging and retract it flat against the gantry for treatment.';
    this.epidArm.userData.tip = armTip;
    this.kvArm.userData.tip = armTip;
    this.kvPanelArm.userData.tip = armTip;

    // Click-to-identify tooltips: tag components; the raycaster walks up to the nearest .tip.
    this.mvHead.userData.tip = 'MV treatment head — the linac gantry head delivering the treatment beam.';
    this.mvColl.userData.tip = 'Collimator / MLC — shapes the treatment field.';
    this.epid.userData.tip = 'EPID — electronic portal imager (MV detector) opposite the head.';
    this.kvSource.userData.tip = 'kV (OBI) source — kilovoltage X-ray tube for setup imaging.';
    this.kvPanel.userData.tip = 'kV flat panel — the OBI imaging detector opposite the kV source.';

    this.mvBeam = new THREE.Mesh(new THREE.ConeGeometry(0.34, 1.34, 36, 1, true), this.materials.beamMv);
    this.mvBeam.position.set(0, 0.77, this.ISO_Z);
    this.mvBeam.renderOrder = 4;
    this.rig.add(this.mvBeam);

    this.kvBeam = new THREE.Mesh(new THREE.ConeGeometry(0.3, 1.36, 36, 1, true), this.materials.beamKv);
    this.kvBeam.rotation.z = -Math.PI / 2;
    this.kvBeam.position.set(0.78, 0, this.ISO_Z);
    this.kvBeam.renderOrder = 4;
    this.rig.add(this.kvBeam);

    // Delivered-arc coverage ring (Full Treatment only, opt-in via state.arcTrail). Mounted on the FIXED
    // scene (NOT the rig) so it marks the swept gantry range in world space. Backing track + bright arc.
    this._arcTrackMat = makeMat(0xffffff, { transparent: true, opacity: 0, metalness: 0, roughness: 1, depthWrite: false });
    this._arcTrack = new THREE.Mesh(new THREE.RingGeometry(1.90, 2.00, 96, 1, 0, Math.PI * 2), this._arcTrackMat);
    this._arcTrack.position.z = 0.02; this._arcTrack.renderOrder = 3; this._arcTrack.visible = false;
    this.scene.add(this._arcTrack);
    this._arcTrailMat = makeMat(0xff9b60, { transparent: true, opacity: 0, metalness: 0, roughness: 1, depthWrite: false, emissive: 0xff5d24, emissiveIntensity: 0.6 });
    this._arcTrail = new THREE.Mesh(new THREE.RingGeometry(1.90, 2.00, 96, 1, 0, 0.001), this._arcTrailMat);
    this._arcTrail.position.z = 0.03; this._arcTrail.renderOrder = 4; this._arcTrail.visible = false;
    this.scene.add(this._arcTrail);
    this._arcTrailGeoSpan = -1; this._arcTrailGeoStart = 0; this._arcTailFade = 0;
    this._kvFlashUntil = 0; this._kvFlashSeen = undefined;   // transient kV-beam flash (opt-in via state.kvFlash)
    this._reduceMotion = false;
    try { const mq = matchMedia('(prefers-reduced-motion:reduce)'); this._reduceMotion = mq.matches;
      mq.addEventListener && mq.addEventListener('change', e => { this._reduceMotion = e.matches; }); } catch (e) {}
    // MV treatment field aperture at the head — collimator jaw frame + a few MLC leaves shaping an
    // irregular opening. Built lazily per case (configureAperture); shown only for MV cases beaming.
    this.apertureGroup = new THREE.Group();
    this.apertureGroup.position.set(0, 0.76, this.ISO_Z);   // just below the collimator snout
    this.apertureGroup.rotation.x = -Math.PI / 2;            // jaw frame ⟂ to the beam (faces iso)
    this.apertureGroup.visible = false;
    this.rig.add(this.apertureGroup);

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

    // Fixed gantry-angle scale around the ring (space, not the rig): G0 top, G90 right, G180 bottom
    // (the cable-wrap hard stop), G270 left. rig.rotation.z = −angle·DEG maps these to these spots.
    const scale = '#c2d2e6';
    [['G0', 0, 2.32], ['G90', 2.32, 0], ['G180', 0, -2.32], ['G270', -2.32, 0]].forEach(([t, x, y]) => {
      const s = makeLabel(t, scale, 0.42);
      s.position.set(x, y, 0.14);
      this.scene.add(s);
    });
    // Minor 45° ticks + labels (secondary style) between the cardinals. Gantry angle θ maps to
    // (sinθ, cosθ)·r — same as the cardinals (G0 top, G90 right, G180 bottom, G270 left) — so 45 sits
    // between G0/G90, 135 between G90/G180, 225 between G180/G270, 315 between G270/G0.
    [45, 135, 225, 315].forEach(deg => {
      const ux = Math.sin(deg * DEG), uy = Math.cos(deg * DEG);
      const s = makeLabel(String(deg), '#6f8299', 0.26);
      s.position.set(ux * 2.28, uy * 2.28, 0.14);
      this.scene.add(s);
      const tick = new THREE.Mesh(new THREE.BoxGeometry(0.03, 0.12, 0.03), this.materials.charcoal);
      tick.position.set(ux * 2.0, uy * 2.0, 0.12);
      tick.rotation.z = -deg * DEG;
      this.scene.add(tick);
    });
    // Live gantry-angle readout — a sprite near the top of the ring whose texture we repaint on change.
    this.liveAngle = makeLabel('G0', '#8fe6ff', 0.6);
    this.liveAngle.position.set(0, 2.9, 0.14);
    this.scene.add(this.liveAngle);

    this.buildFloor();
    this.buildTurntable();
  }

  // Depth polish: a dark floor plane + faint room grid + a soft contact shadow under the couch. The
  // floor sits BELOW the whole gantry (ring bottom ~ −1.9) so the head doesn't punch through it at G180.
  buildFloor() {
    const floor = new THREE.Mesh(new THREE.PlaneGeometry(11, 9), makeMat(0x121722, { roughness: 0.96, metalness: 0 }));
    floor.rotation.x = -Math.PI / 2;
    floor.position.y = this.FLOOR_Y;
    floor.renderOrder = 0;
    this.scene.add(floor);
    const grid = new THREE.GridHelper(10, 24, 0x2a3a4c, 0x1c2836);
    grid.position.y = this.FLOOR_Y + 0.02;
    grid.material.transparent = true; grid.material.opacity = 0.35; grid.material.depthWrite = false;
    this.scene.add(grid);
    // contact shadow: radial-gradient sprite that tracks the couch translation (not rotation)
    const cv = document.createElement('canvas'); cv.width = cv.height = 128;
    const g2 = cv.getContext('2d');
    const grd = g2.createRadialGradient(64, 64, 4, 64, 64, 62);
    grd.addColorStop(0, 'rgba(0,0,0,0.55)'); grd.addColorStop(1, 'rgba(0,0,0,0)');
    g2.fillStyle = grd; g2.fillRect(0, 0, 128, 128);
    this.contactShadow = new THREE.Sprite(new THREE.SpriteMaterial({ map: new THREE.CanvasTexture(cv), transparent: true, depthWrite: false }));
    this.contactShadow.scale.set(2.4, 1.3, 1);
    this.contactShadow.position.set(0, this.FLOOR_Y + 0.03, 0.3);
    this.contactShadow.material.rotation = Math.PI / 2;   // long axis along the couch (Z)
    this.contactShadow.renderOrder = 1;
    this.scene.add(this.contactShadow);
  }

  // Couch turntable (Rtn) floor indicator: a green arc sweeping the kick angle + a label, shown only
  // when Rtn ≠ 0. Floor-fixed under the pedestal; rebuilt only when the angle changes (see apply()).
  buildTurntable() {
    this.turntableArc = new THREE.Mesh(new THREE.TorusGeometry(1.5, 0.05, 8, 48, 0.001), this.materials.green);
    this.turntableArc.rotation.x = -Math.PI / 2;
    this.turntableArc.position.set(0, this.FLOOR_Y + 0.04, 0.3);
    this.turntableArc.visible = false;
    this.scene.add(this.turntableArc);
    this.turntableLabel = makeLabel('', '#5fe0a0', 0.5);
    this.turntableLabel.position.set(0, this.FLOOR_Y + 0.35, 1.5);
    this.turntableLabel.visible = false;
    this.scene.add(this.turntableLabel);
  }

  // (Re)build the MLC field aperture for a case config {colW,colH,leaves:[{x,width}]} (rig-local units).
  configureAperture(cfg) {
    const key = cfg ? JSON.stringify(cfg) : '';
    if (key === this.apertureCfgKey) return;
    this.apertureCfgKey = key;
    while (this.apertureGroup.children.length) this.apertureGroup.remove(this.apertureGroup.children[0]);
    this.apertureLeaves = [];
    this.fieldApertureOn = !!cfg;
    if (!cfg) return;
    const colW = cfg.colW || 0.5, colH = cfg.colH || 0.42, t = 0.03;
    // jaw frame (four thin bars around the opening)
    const bar = (w, h, x, y) => { const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, 0.05), this.materials.aperture); m.position.set(x, y, 0); this.apertureGroup.add(m); };
    bar(colW + 2 * t, t, 0, colH / 2 + t / 2); bar(colW + 2 * t, t, 0, -colH / 2 - t / 2);
    bar(t, colH, colW / 2 + t / 2, 0); bar(t, colH, -colW / 2 - t / 2, 0);
    (cfg.leaves || []).forEach(lf => {
      const leaf = new THREE.Mesh(new THREE.BoxGeometry(lf.width, colH, 0.04), this.materials.leafBlack);
      leaf.position.set(lf.x, 0, 0.01);
      this.apertureGroup.add(leaf); this.apertureLeaves.push(leaf);
    });
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
    g.userData.tip = 'Treatment couch — 6DOF; encoder Lat/Lng/Vrt/Rtn position the patient at isocentre.';
    this.slider.add(g);  // couch TOP (plate/pad/rails) slides with the patient (telescopes through the pedestal)

    // pedestal + base are floor-fixed at the foot end (the couch top telescopes in/out of them), so
    // they do NOT slide with the per-case longitudinal position or the couch encoder offset. The
    // column runs from just under the couch top down to the floor (like a real treatment-couch stand).
    const topY = -0.28, floorY = this.FLOOR_Y, colH = topY - (floorY + 0.1);
    // PerfectPitch-style stand: ivory moulded pedestal column + charcoal floor base.
    const pedestal = new THREE.Mesh(new THREE.BoxGeometry(0.32, colH, 0.42), this.materials.ivory);
    pedestal.position.set(0, (topY + floorY + 0.1) / 2, 1.2);
    this.scene.add(pedestal);
    const base = new THREE.Mesh(new THREE.BoxGeometry(0.78, 0.12, 0.9), this.materials.charcoal);
    base.position.set(0, floorY + 0.06, 1.2);
    this.scene.add(base);
    // couch turntable — the flush ivory disc in the floor the whole couch kicks (Rtn) about
    const turntable = new THREE.Mesh(new THREE.CylinderGeometry(0.95, 0.95, 0.05, 48), this.materials.ivoryBright);
    turntable.position.set(0, floorY + 0.03, 1.2);
    this.scene.add(turntable);
  }

  // Supine patient lying head-to-foot along Z, resting on the couch (posterior at -Y), draped in a
  // gown. Head-first into the bore (-Z), feet out toward the camera (+Z); iso at the mid-torso.
  buildPatient() {
    // Built in LOCAL coords inside patientGroup (which is pivoted at ISO_Z); Z is the offset from
    // isocentre along the bore (−Z into the machine). SITE_LOCAL mirrors these offsets so any site
    // can be slid onto iso, and patientGroup can rotate 180° about ISO_Z for feet-first.
    const Y = 0.0, Z = 0;
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
    this.patientGroup.add(p);
  }

  // Isocentre marked ON the patient at the ring centre where the beams converge: a glowing point,
  // a transverse target reticle encircling the body cross-section, and green room-laser cross-lines
  // through the body (sup-inf along the bore Z, ant-post Y, lateral X).
  buildIso() {
    const g = new THREE.Group();
    g.position.set(0, 0, this.ISO_Z);
    const dot = new THREE.Mesh(new THREE.SphereGeometry(0.045, 20, 14), this.materials.iso);
    dot.renderOrder = 6; g.add(dot);
    const ring = new THREE.Mesh(new THREE.TorusGeometry(0.14, 0.011, 12, 64), this.materials.iso);
    ring.renderOrder = 6; g.add(ring);   // small transverse reticle in the XY plane, marking iso
    const line = (len, axis) => {
      const m = new THREE.Mesh(new THREE.CylinderGeometry(0.006, 0.006, len, 8), this.materials.laser);
      if (axis === 'x') m.rotation.z = Math.PI / 2;
      if (axis === 'z') m.rotation.x = Math.PI / 2;
      m.renderOrder = 5; return m;
    };
    g.add(line(0.66, 'x'), line(0.62, 'y'), line(1.0, 'z'));
    this.isoMarker = g;
    g.userData.tip = 'Isocentre — where the beams converge; green room lasers mark it on the patient.';
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
    // Transient kV-beam flash (Full Treatment triggered-kV). Edge-detect a new kvFlash stamp and open a
    // 600 ms window (timed on THIS scene's clock, robust to the sender's clock base). conGantry3D never
    // sends kvFlash, so this is inert for the 2D console.
    if (state && 'kvFlash' in state && state.kvFlash && state.kvFlash !== this._kvFlashSeen) {
      this._kvFlashSeen = state.kvFlash;
      this._kvFlashUntil = performance.now() + 600;
    }
    // On a large commanded jump (reset / case switch) snap the display so it doesn't
    // spin the long way round; small deltas glide via the eased loop below.
    const angle = Number.isFinite(this.state.angle) ? this.state.angle : 0;
    if (Math.abs(angDiff(this.dispAngle, angle)) > 90) this.dispAngle = angle;

    // Couch encoder → physical couch offset. Lateral is ~0-centred so it maps directly (a big Lat
    // shifts the couch/patient off the bore axis); vrt/lng are absolute calibration values, so use
    // their deviation from plan (dVrt/dLng); rtn is the couch turntable angle. cm → scene units.
    const c = this.state.couch;
    if (c) {
      const LAT = 0.11, VRT = 0.1, LNG = 0.1, clamp = (v, m) => Math.max(-m, Math.min(m, v));
      this.tableGoal.x = clamp((c.lat || 0) * LAT, 1.2);
      this.tableGoal.y = clamp((c.vrt || 0) * VRT, 0.6);   // c.vrt/c.lng are deltas-from-plan (see console)
      this.tableGoal.z = clamp((c.lng || 0) * LNG, 0.9);
      this.tableGoal.rtn = (c.rtn || 0) * DEG;
    }

    // Per-case isocentre site: slide the couch top + patient along the bore so the treated anatomy
    // (head for brain, pelvis for pelvis, thigh for femur…) sits under the fixed machine isocentre /
    // lasers. caseZ cancels the site's local offset; feet-first (extremities) flips the patient 180°
    // about ISO_Z, so the offset's sign flips too.
    if (this.state.isoRegion !== undefined) {
      this.feetFirst = !!this.state.feetFirst;
      const local = SITE_LOCAL[this.state.isoRegion] ?? 0;
      this.caseZGoal = this.feetFirst ? local : -local;
    }

    // MLC field aperture is per-case (rebuild only on change); null → plain cone beam.
    if (this.state.fieldAperture !== undefined) this.configureAperture(this.state.fieldAperture);
    this.ensureLoop();
  }

  // Apply the current state to the scene. `t` is a monotonic ms clock for the beam pulse.
  apply(dt) {
    this.resize();   // cheap no-op unless the panel actually reflowed (fixes reflow-without-window-resize)

    const angle = Number.isFinite(this.state.angle) ? this.state.angle : 0;
    // ease the displayed angle toward the commanded gantry (shortest wrap-aware arc).
    // NOTE: angDiff(angle, dispAngle) = angle − dispAngle, i.e. points TOWARD the target; the
    // reversed form pushes it away and combines with the >90° snap into a visible stutter.
    const k = 1 - Math.pow(0.0025, dt / 1000);   // ~frame-rate-independent smoothing
    this.dispAngle = this.dispAngle + angDiff(angle, this.dispAngle) * Math.min(1, k);
    this.rig.rotation.z = -this.dispAngle * DEG;

    // ease the couch toward its encoder offset so New Offset / corrections glide, not pop
    const o = this.tableOff, gl = this.tableGoal, kc = Math.min(1, 1 - Math.pow(0.02, dt / 1000));
    o.x += (gl.x - o.x) * kc; o.y += (gl.y - o.y) * kc; o.z += (gl.z - o.z) * kc; o.rtn += (gl.rtn - o.rtn) * kc;
    this.caseZCur += (this.caseZGoal - this.caseZCur) * kc;   // ease the per-case longitudinal slide
    this.table.position.set(o.x, o.y, o.z);
    this.table.rotation.y = o.rtn;
    this.slider.position.z = this.caseZCur;                   // couch top + patient telescope per case
    this.patientGroup.rotation.y = this.feetFirst ? Math.PI : 0;   // head-first vs feet-first
    this.contactShadow.position.x = o.x;                     // shadow tracks couch translation, not rotation
    this.contactShadow.position.z = 0.3 + o.z;

    // Couch turntable (Rtn) floor arc + label — shown only when kicked; rebuilt only on angle change.
    const rtnDeg = o.rtn / DEG;
    if (Math.abs(rtnDeg) > 0.4) {
      if (Math.abs(rtnDeg - this.lastRtn) > 0.4) {
        this.turntableArc.geometry.dispose();
        this.turntableArc.geometry = new THREE.TorusGeometry(1.5, 0.05, 8, 48, Math.abs(o.rtn));
        this.turntableArc.rotation.z = o.rtn < 0 ? -Math.abs(o.rtn) : 0;
        setLabel(this.turntableLabel, 'Rtn ' + (rtnDeg > 0 ? '+' : '') + rtnDeg.toFixed(1) + '°', '#5fe0a0');
        this.lastRtn = rtnDeg;
      }
      this.turntableArc.visible = this.turntableLabel.visible = true;
    } else {
      this.turntableArc.visible = this.turntableLabel.visible = false;
    }

    // Live gantry-angle readout (repaint the sprite only when the integer degree changes).
    const gInt = Math.round(this.dispAngle) % 360;
    if (gInt !== this.liveAngleKey) { this.liveAngleKey = gInt; setLabel(this.liveAngle, 'G' + gInt, '#8fe6ff'); }

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
    const kv = mode === 'kv';
    const now = performance.now();
    const kvActive = now < this._kvFlashUntil;            // transient kV-beam flash window (Full Treatment)
    const reduce = this._reduceMotion;

    // Both the kV (OBI source+panel) and MV (head+EPID) imaging chains stay visible at all times;
    // `mode` still drives which beam fires, which detector glows, and the collision cue below.

    // Exact-arm deploy/retract: the kV pair extends for kV imaging, the EPID for MV portal work;
    // the off-duty imager folds flat against the gantry face, like the real motorised arms. Travel
    // is rate-limited (~1.8 s full swing) so the arms read as slow robotics, not a toggle.
    // state.arms {kv,epid} overrides the mode-based inference when a console wants manual control.
    const armGoal = this.state.arms || { kv: kv, epid: !kv };
    this._armGoal = armGoal;
    const rate = dt / 1800;
    for (const k of ['kv', 'epid']) {
      const g = armGoal[k] ? 1 : 0, cur = this.armDeploy[k];
      this.armDeploy[k] = reduce ? g : Math.max(0, Math.min(1, cur + Math.sign(g - cur) * Math.min(rate, Math.abs(g - cur))));
    }
    const easeArm = t => t * t * (3 - 2 * t);   // smoothstep so the swing starts/ends softly
    const tk = easeArm(this.armDeploy.kv), te = easeArm(this.armDeploy.epid);
    this.kvSGroup.rotation.x = (1 - tk) * 1.32;               // swing down flat against the face
    this.kvDGroup.rotation.x = (1 - tk) * 1.32;
    this.kvSGroup.position.z = this.kvDGroup.position.z = -1.35 - 0.15 * (1 - tk);   // slight pull-in
    this.epidGroup.rotation.x = (1 - te) * 0.49;              // tuck up + in toward the stand
    this.epidGroup.position.y = -0.85 + 0.5 * (1 - te);
    this.epidGroup.position.z = -1.35 - 0.6 * (1 - te);

    // Collision-clearance cue: amber-tint the MV head as it swings toward the couch/patient near the
    // 180° region (steep posterior-oblique angles). Subtle, non-alarming; eased.
    const near = Math.cos((this.dispAngle - 180) * DEG);            // 1 at G180 (head at the couch), −1 at G0
    const amberT = Math.max(0, (near - 0.4) / 0.6);                 // ramps in over the last ~53° toward 180
    this.amberGlow += (amberT - this.amberGlow) * Math.min(1, kc);
    this.mvHead.material.emissive.setHex(0x5a2e00);
    this.mvHead.material.emissiveIntensity = 0.06 + 0.9 * this.amberGlow;
    this.mvHead.material.color.setHex(this.amberGlow > 0.5 ? 0xff9c3a : 0xf4f0e6);   // ivory cowl at rest

    const beam = kv ? this.kvBeam : this.mvBeam;
    const other = kv ? this.mvBeam : this.kvBeam;
    const p = 0.5 + 0.5 * Math.sin(this.clock / 130);   // shared beam/aperture/detector pulse phase
    beam.visible = beamOn;
    // Full Treatment: on a triggered kV, flash the kV beam ALONGSIDE the MV beam (else the off-beam hides).
    const kvFlashShow = (!kv && kvActive && beamOn);
    other.visible = kvFlashShow;
    if (beamOn) {
      beam.material.opacity = 0.24 + 0.26 * p;
      beam.material.emissiveIntensity = (kv ? 0.62 : 0.6) + 0.4 * p;
      beam.scale.setScalar(0.97 + 0.05 * p);
    }
    if (kvFlashShow) {
      const life = Math.max(0, (this._kvFlashUntil - now) / 600);
      const k = (0.35 + 0.45 * p) * life;
      this.kvBeam.material.opacity = 0.18 + 0.4 * k;
      this.kvBeam.material.emissiveIntensity = 0.4 + 0.5 * k;
      this.kvBeam.scale.setScalar(0.97 + 0.05 * p);
    }

    // Field aperture — MV cases only, visible while beaming; leaves pulse with the beam.
    this.apertureGroup.visible = !!this.fieldApertureOn && !kv && beamOn;
    if (this.apertureGroup.visible) {
      this.apertureLeaves.forEach(l => { l.material.opacity = 0.5 + 0.25 * p; });
    }

    // Beam-on gating: light up the OPPOSING imaging detector (EPID for MV, kV panel for kV) so the
    // source→patient→detector geometry reads. One eased envelope, mode-selected target.
    if (beamOn && !this.lastBeamOn) this.detectorGlow = Math.max(this.detectorGlow, 0.01);
    const glowTarget = beamOn ? 1 : 0;
    this.detectorGlow += (glowTarget - this.detectorGlow) * Math.min(1, 1 - Math.pow(0.02, dt / 1000) * 0.5);
    if (this.detectorGlow < 1e-3) this.detectorGlow = 0;
    const det = kv ? this.kvPanel : this.epid;
    const detOff = kv ? this.epid : this.kvPanel;
    det.material.emissive.setHex(kv ? 0x2dd4ee : 0xff5d24);
    det.material.emissiveIntensity = this.detectorGlow * (0.9 + 0.5 * p);
    detOff.material.emissiveIntensity = 0;
    this.lastBeamOn = beamOn;

    // Delivered-arc coverage ring (opt-in via state.arcTrail). Grows as the gantry sweeps the arc, so the
    // beam clearly reads as delivered all the way around; mounted on the fixed scene (world-space gauge).
    const at = this.state.arcTrail;
    if (at && (at.active || this._arcTrailMat.opacity > 0.01)) {
      this._arcTailFade = at.active ? 1 : Math.max(0, this._arcTailFade - dt / 500);
      const fade = at.active ? 1 : this._arcTailFade;
      this._arcTrack.visible = true; this._arcTrackMat.opacity = 0.10 * fade;
      const start = at.start || 0, dir = at.dir < 0 ? -1 : 1, swept = Math.max(0, Math.min(358, at.swept || 0));
      // rig.rotation.z = -A*DEG with the MV head at +Y ⇒ screen math-angle a(A) = PI/2 - A*DEG
      const a0 = Math.PI / 2 - start * DEG, len = -dir * swept * DEG;
      const thetaStart = len < 0 ? a0 + len : a0, thetaLen = Math.max(0.001, Math.abs(len));
      if (Math.abs(swept - this._arcTrailGeoSpan) > 1.2 || Math.abs(start - this._arcTrailGeoStart) > 1.2) {
        this._arcTrail.geometry.dispose();   // throttle rebuilds to ~1.2° swept → avoid GPU churn on the long arc
        this._arcTrail.geometry = new THREE.RingGeometry(1.90, 2.00, Math.max(2, Math.round(swept / 3)), 1, thetaStart, thetaLen);
        this._arcTrailGeoSpan = swept; this._arcTrailGeoStart = start;
      }
      this._arcTrail.visible = swept > 0.5;
      this._arcTrailMat.opacity = (0.55 + (reduce ? 0 : 0.12 * p)) * fade;
    } else {
      this._arcTrack.visible = false; this._arcTrail.visible = false;
      this._arcTrackMat.opacity = 0; this._arcTrailMat.opacity = 0; this._arcTrailGeoSpan = -1;
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
      const o = this.tableOff, gl = this.tableGoal;
      const tableSettled = Math.abs(gl.x - o.x) < 1e-3 && Math.abs(gl.y - o.y) < 1e-3 &&
        Math.abs(gl.z - o.z) < 1e-3 && Math.abs(gl.rtn - o.rtn) < 1e-3 &&
        Math.abs(this.caseZGoal - this.caseZCur) < 1e-3;
      // detector-glow fade-out + amber ease must finish before the loop parks the GPU
      const fxSettled = this.detectorGlow < 1e-3 &&
        Math.abs(Math.max(0, (Math.cos((this.dispAngle - 180) * DEG) - 0.4) / 0.6) - this.amberGlow) < 1e-3;
      // also keep the loop alive while a kV flash is showing or the delivered-arc trail is still fading
      const kvBusy = performance.now() < this._kvFlashUntil;
      const at = this.state.arcTrail;
      const trailBusy = !!(at && at.active) || (this._arcTrailMat && this._arcTrailMat.opacity > 0.01);
      // …and while the Exact imaging arms are still swinging to their deploy/retract pose
      const ag = this._armGoal || { kv: true, epid: true };
      const armsSettled = Math.abs(this.armDeploy.kv - (ag.kv ? 1 : 0)) < 1e-3 &&
        Math.abs(this.armDeploy.epid - (ag.epid ? 1 : 0)) < 1e-3;
      if (gantrySettled && !this.state.beamOn && this.cameraSettled() && tableSettled && fxSettled && !kvBusy && !trailBusy && armsSettled) { this._raf = null; this.lastT = null; return; }
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

// Local Z of each anatomical site along the built patient (relative to ISO_Z; -Z = into the bore).
// Matches the body-part positions in buildPatient(); used to slide the treated site onto isocentre.
const SITE_LOCAL = { head: -0.86, neck: -0.70, chest: -0.28, abdomen: 0, pelvis: 0.25, thigh: 0.72, knee: 1.3 };

const api = {
  instances: {},
  // Lazily create (or fetch) a GantryScene bound to the canvas with id `canvasId`. Multiple canvases
  // are supported so the 3D gantry can appear in the 2D/2D console AND every Full Treatment console.
  _get(canvasId) {
    if (this.instances[canvasId]) return this.instances[canvasId];
    const canvas = document.getElementById(canvasId);
    if (!canvas) return null;
    try {
      const inst = new GantryScene(canvas);
      this.instances[canvasId] = inst;
      const viz = canvas.closest('.con-viz') || canvas.parentElement;
      if (viz) viz.classList.add('has-3d');
      return inst;
    } catch (err) {
      console.warn('3D gantry unavailable; using SVG fallback.', err);
      this.instances[canvasId] = null;   // don't retry a context that can't be created
      return null;
    }
  },
  init() {
    const inst = this._get('conGantry3D');   // the 2D/2D delivery console gantry (default)
    if (inst && window.CONSOLE && window.CONSOLE._dbg && window.CONSOLE._dbg.state) {
      const s = window.CONSOLE._dbg.state();
      const views = window.CONSOLE._dbg.views ? window.CONSOLE._dbg.views().map(v => ({
        slot: v.slot,
        label: v.label,
        angle: (v.angles && v.angles[0]) || (window.CONSOLE._dbg.viewAngles[v.slot] || [0])[0]
      })) : [];
      inst.update({ angle: s.gantry || 0, target: s.motTarget, phase: s.phase, acquired: s.acquired, views });
    }
  },
  update(state) {           // back-compat: drives the default 2D/2D console gantry
    const inst = this._get('conGantry3D');
    if (inst) inst.update(state);
  },
  updateOn(canvasId, state) {   // drive any other gantry canvas (Full Treatment consoles)
    const inst = this._get(canvasId);
    if (inst) inst.update(state);
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
