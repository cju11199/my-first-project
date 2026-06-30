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
    depthWrite: opts.depthWrite ?? true
  });
}

class GantryScene {
  constructor(canvas) {
    this.canvas = canvas;
    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;

    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(36, 1, 0.1, 30);
    this.camera.position.set(0.05, 0.02, 6.2);
    this.camera.lookAt(0, 0, 0);

    this.state = { angle: 0, target: null, mode: 'kv', beamOn: false, phase: 'ACQUIRE' };
    this.lastW = 0;
    this.lastH = 0;

    this.materials = {
      shell: makeMat(0x5e7692, { roughness: 0.28, metalness: 0.7 }),
      shellDark: makeMat(0x1d2b3c, { roughness: 0.45, metalness: 0.45 }),
      trim: makeMat(0xa8b9cf, { roughness: 0.22, metalness: 0.8 }),
      couch: makeMat(0x2f4158, { roughness: 0.5, metalness: 0.3 }),
      patient: makeMat(0x24364a, { roughness: 0.65, metalness: 0.05 }),
      kv: makeMat(0x43d6ed, { roughness: 0.25, metalness: 0.35, emissive: 0x0c5a66, emissiveIntensity: 0.25 }),
      mv: makeMat(0xe8c25a, { roughness: 0.28, metalness: 0.35, emissive: 0x5f4200, emissiveIntensity: 0.22 }),
      green: makeMat(0x3ddc97, { roughness: 0.35, metalness: 0.2, emissive: 0x0b4c31, emissiveIntensity: 0.32 }),
      target: makeMat(0xff7a45, { roughness: 0.34, metalness: 0.15, emissive: 0x5f1900, emissiveIntensity: 0.36 }),
      beamKv: makeMat(0x7deeff, { transparent: true, opacity: 0.34, metalness: 0, roughness: 0.9, depthWrite: false, emissive: 0x2dd4ee, emissiveIntensity: 0.55 }),
      beamMv: makeMat(0xff9b60, { transparent: true, opacity: 0.38, metalness: 0, roughness: 0.9, depthWrite: false, emissive: 0xff5d24, emissiveIntensity: 0.52 })
    };

    this.build();
    this.resize();
    this.render();
    window.addEventListener('resize', () => {
      this.resize();
      this.render();
    });
  }

  build() {
    this.scene.add(new THREE.HemisphereLight(0xd9eefc, 0x071019, 1.6));
    const key = new THREE.DirectionalLight(0xffffff, 2.2);
    key.position.set(-2.8, 3.8, 5.2);
    this.scene.add(key);
    const rim = new THREE.DirectionalLight(0x73d8ff, 0.75);
    rim.position.set(3.2, -1.5, 4);
    this.scene.add(rim);

    const bore = new THREE.Mesh(new THREE.CylinderGeometry(2.28, 2.28, 0.24, 96), this.materials.shellDark);
    bore.rotation.x = Math.PI / 2;
    bore.position.z = -0.34;
    this.scene.add(bore);

    const boreLip = new THREE.Mesh(new THREE.TorusGeometry(2.28, 0.045, 16, 128), this.materials.trim);
    boreLip.position.z = -0.2;
    this.scene.add(boreLip);

    const couch = new THREE.Mesh(new THREE.BoxGeometry(4.1, 0.14, 0.22), this.materials.couch);
    couch.position.set(0, -0.1, 0.12);
    this.scene.add(couch);

    const pedestal = new THREE.Mesh(new THREE.BoxGeometry(0.62, 0.9, 0.28), this.materials.couch);
    pedestal.position.set(0, -0.74, 0.03);
    this.scene.add(pedestal);

    const patient = new THREE.Mesh(new THREE.SphereGeometry(0.36, 32, 18), this.materials.patient);
    patient.scale.set(1.75, 0.54, 0.34);
    patient.position.set(0, 0.13, 0.22);
    this.scene.add(patient);

    const iso = new THREE.Mesh(new THREE.SphereGeometry(0.055, 24, 12), this.materials.kv);
    iso.position.set(0, 0, 0.55);
    this.scene.add(iso);

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
    this.mvBeam.position.set(0, 0.77, 0.42);
    this.mvBeam.renderOrder = 4;
    this.rig.add(this.mvBeam);

    this.kvBeam = new THREE.Mesh(new THREE.ConeGeometry(0.3, 1.36, 36, 1, true), this.materials.beamKv);
    this.kvBeam.rotation.z = -Math.PI / 2;
    this.kvBeam.position.set(0.78, 0, 0.42);
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
    this.resize();

    const angle = Number.isFinite(this.state.angle) ? this.state.angle : 0;
    this.rig.rotation.z = -angle * DEG;

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
      m.children.forEach(c => c.material = done ? this.materials.green : this.materials.kv);
    });

    const beamOn = !!this.state.beamOn;
    const mode = this.state.mode === 'mv' ? 'mv' : 'kv';
    this.mvBeam.visible = beamOn && mode === 'mv';
    this.kvBeam.visible = beamOn && mode !== 'mv';

    this.render();
  }

  render() {
    this.renderer.render(this.scene, this.camera);
  }
}

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
