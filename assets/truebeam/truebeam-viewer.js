// truebeam-viewer.js — thin three.js runtime around build() from truebeam-model.js.
//
// ONE viewer class, reused by the marketing preview page AND the trainer Machine-view
// panel. Owns renderer/scene/camera/lights/controls + the render loop, and is
// PAUSE-WHEN-HIDDEN by default so an off-screen panel costs zero GPU:
//   • IntersectionObserver  → stop the loop when the canvas scrolls out of view
//   • document visibilitychange → stop when the tab is hidden
//   • render-on-demand: with no autoRotate and a settled camera we render only on
//     pose/camera change (a dirty flag), so a static panel idles at 0 fps.
//
// Usage:
//   import { TrueBeamViewer } from './truebeam-viewer.js';
//   const v = new TrueBeamViewer(THREE, { OrbitControls, canvas, autoRotate:true });
//   await v.ready;  v.setPose({ gantryAngle: 90, kvDeploy: 1 });
//   // trainer panel: v.setPose(...) each time the gantry angle changes; loop self-pauses.
//   v.destroy();    // releases GL + observers on panel close / page nav
//
// CSP: pure ES modules served from 'self'; no CDN, no eval, no workers. Fits the
// trainer's `script-src 'self'`. three.js + GLTF loaders are vendored alongside.

import { build } from './truebeam-model.js';

export class TrueBeamViewer {
  constructor(THREE, opts = {}) {
    this.THREE = THREE;
    this.opts = opts;
    this.canvas = opts.canvas;
    this._running = false;
    this._dirty = true;
    this._visible = true;
    this._raf = 0;
    this._autoRotate = !!opts.autoRotate;
    this._onPose = opts.onPose || null;

    const w = this.canvas.clientWidth || 480, h = this.canvas.clientHeight || 360;

    this.renderer = new THREE.WebGLRenderer({
      canvas: this.canvas, antialias: true, alpha: true, powerPreference: 'low-power',
    });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    this.renderer.setSize(w, h, false);

    this.scene = new THREE.Scene();
    this.scene.background = opts.background === undefined ? null : opts.background;

    // camera: meters, looking at iso (origin). Default 3/4 vault view.
    this.camera = new THREE.PerspectiveCamera(35, w / h, 0.05, 50);
    this.camera.position.set(2.6, 1.4, -3.0);
    this.camera.lookAt(0, 0, -0.2);

    // lights: cheap — one key dir + hemi fill, no shadows (perf).
    const key = new THREE.DirectionalLight(0xffffff, 1.5); key.position.set(2, 4, -2);
    const hemi = new THREE.HemisphereLight(0xbfd2e6, 0x2a2a33, 0.9);
    this.scene.add(key, hemi);

    // the model — forward educational flags (beam lines to iso, color-coded IEC axes)
    // so the trainer Machine-view panel can request them: new TrueBeamViewer(THREE,{edu:true,axes:true})
    this.model = build(THREE, opts.model || {
      beamLine: !!opts.beamLine,
      edu: !!opts.edu,
      axes: !!opts.axes,
      patient: opts.patient !== false,
    });
    this.scene.add(this.model.root);

    // optional orbit controls (preview page); the trainer panel can pass none
    if (opts.OrbitControls) {
      this.controls = new opts.OrbitControls(this.camera, this.canvas);
      this.controls.enableDamping = true;
      this.controls.dampingFactor = 0.08;
      this.controls.target.set(0, 0, -0.2);
      this.controls.minDistance = 1.5;
      this.controls.maxDistance = 9;
      this.controls.maxPolarAngle = Math.PI * 0.92;
      this.controls.addEventListener('change', () => { this._dirty = true; if (!this._running) this._kick(); });
      this.controls.update();
    }

    this._initObservers();
    this._onResize = this._resize.bind(this);
    window.addEventListener('resize', this._onResize);

    this.ready = Promise.resolve(this);
    this._resize();
    this.start();
  }

  // public: drive the machine. Cheap; flags a redraw and wakes the loop if idle.
  setPose(p) { this.model.setPose(p); this._dirty = true; if (this._visible && !this._running) this._kick(); return this; }
  drivers() { return this.model.drivers; }
  part(name) { return this.model.parts[name]; }
  // educational, color-coded readout rows (gantry/collimator + 6DOF couch) for the panel UI
  readout(pose) { return this.model.readout(pose); }

  setAutoRotate(on) { this._autoRotate = !!on; this._dirty = true; if (on) this.start(); }

  // ── lifecycle: pause-when-hidden ────────────────────────────────────────────
  start() {
    if (this._running || !this._visible) return;
    this._running = true;
    this._last = performance.now();
    this._loop();
  }
  stop() {
    this._running = false;
    if (this._raf) cancelAnimationFrame(this._raf), this._raf = 0;
  }
  _kick() { // render exactly one frame while paused (after a setPose / control change)
    if (this._running) return;
    this._raf = requestAnimationFrame(() => {
      this._raf = 0;
      if (this.controls) this.controls.update();
      this.renderer.render(this.scene, this.camera);
      this._dirty = false;
    });
  }
  _loop() {
    if (!this._running) return;
    this._raf = requestAnimationFrame(() => this._loop());
    const now = performance.now(), dt = (now - this._last) / 1000; this._last = now;

    let needs = this._dirty;
    if (this._autoRotate) { this.model.root.rotation.y += dt * 0.25; needs = true; }
    if (this.controls && this.controls.enableDamping) { this.controls.update(); needs = true; }

    if (needs) { this.renderer.render(this.scene, this.camera); this._dirty = false; }
    // fully static + no autorotate + damping settled → drop to idle to save GPU
    if (!this._autoRotate && !this._dirty && !(this.controls && this.controls.enableDamping)) this.stop();
  }

  _initObservers() {
    // IntersectionObserver: pause when the canvas scrolls out of view
    if ('IntersectionObserver' in window) {
      this._io = new IntersectionObserver((es) => {
        const vis = es.some(e => e.isIntersecting);
        this._visible = vis;
        if (vis) this.start(); else this.stop();
      }, { threshold: 0.01 });
      this._io.observe(this.canvas);
    }
    // tab visibility: pause when hidden, resume when shown
    this._onVis = () => {
      if (document.hidden) this.stop();
      else if (this._visible) this.start();
    };
    document.addEventListener('visibilitychange', this._onVis);
  }

  _resize() {
    const w = this.canvas.clientWidth || 480, h = this.canvas.clientHeight || 360;
    this.renderer.setSize(w, h, false);
    this.camera.aspect = w / h; this.camera.updateProjectionMatrix();
    this._dirty = true; if (!this._running && this._visible) this._kick();
  }

  destroy() {
    this.stop();
    if (this._io) this._io.disconnect();
    document.removeEventListener('visibilitychange', this._onVis);
    window.removeEventListener('resize', this._onResize);
    if (this.controls && this.controls.dispose) this.controls.dispose();
    this.model.dispose();
    this.renderer.dispose();
  }
}

export default TrueBeamViewer;
