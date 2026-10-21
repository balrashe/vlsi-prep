// The studio every mascot reel shares: seamless cyclorama, soft area lights, AO + depth of field + light bloom,
// a contact shadow and landing ripples. Everything is a pure function of time so any frame renders the same.
import * as THREE from "three";
import { RectAreaLightUniformsLib } from "three/addons/lights/RectAreaLightUniformsLib.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";
import { EffectComposer } from "three/addons/postprocessing/EffectComposer.js";
import { RenderPass } from "three/addons/postprocessing/RenderPass.js";
import { GTAOPass } from "three/addons/postprocessing/GTAOPass.js";
import { BokehPass } from "three/addons/postprocessing/BokehPass.js";
import { UnrealBloomPass } from "three/addons/postprocessing/UnrealBloomPass.js";
import { OutputPass } from "three/addons/postprocessing/OutputPass.js";

export const rnd = (i) => { const x = Math.sin(i * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
export const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const lerp = (a, b, k) => a + (b - a) * k;
export const io = (x) => { x = clamp(x); return x < 0.5 ? 4 * x * x * x : 1 - (-2 * x + 2) ** 3 / 2; };
export const ss = (a, b, x) => io((x - a) / (b - a));
export const back = (x) => { x = clamp(x); const c = 1.7; return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2; };
export const vlerp = (a, b, k) => a.map((v, i) => lerp(v, b[i], k));

// seamless cyclorama: a floor that sweeps up into the back wall, so there is no horizon line
function cyc(width = 240, depth = 70, radius = 22, height = 90) {
  const prof = [];
  for (let z = depth; z > 0; z -= 4) prof.push([0, z]);
  for (let a = 0; a <= 24; a++) { const th = a / 24 * Math.PI / 2; prof.push([radius - radius * Math.cos(th), -radius * Math.sin(th)]); }
  for (let y = radius + 6; y <= height; y += 8) prof.push([y, -radius]);
  const cols = 48, pos = [], idx = [];
  prof.forEach(([y, z]) => { for (let c = 0; c <= cols; c++) pos.push(-width / 2 + width * c / cols, y, z - 12); });
  for (let r = 0; r < prof.length - 1; r++) for (let c = 0; c < cols; c++) { const a = r * (cols + 1) + c, b = a + cols + 1; idx.push(a, b, a + 1, b, b + 1, a + 1); }
  const g = new THREE.BufferGeometry(); g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3)); g.setIndex(idx); g.computeVertexNormals();
  return g;
}

// looks: [stage colour, rim light colour]; keep them muted, the mascot is the only saturated thing on screen
export const LOOKS = {
  warm: [0x40352f, 0xffb27a], teal: [0x2f3a38, 0x7fe3d0], violet: [0x37314a, 0xc5a6ff],
  gold: [0x423829, 0xffd27a], green: [0x2e3a31, 0x9fe3b5], blue: [0x2f3546, 0x9fb8ff],
};

export function createStage({ W = 1080, H = 1920, canvas } = {}) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true });
  renderer.setSize(W, H, false); renderer.setPixelRatio(1);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.0;
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  RectAreaLightUniformsLib.init();
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x15110f);
  scene.environment = new THREE.PMREMGenerator(renderer).fromScene(new RoomEnvironment(), 0.04).texture;
  scene.environmentIntensity = 0.28;
  const camera = new THREE.PerspectiveCamera(30, W / H, 0.5, 300);

  // the cyc is seen from below on the sweep, so it must be double sided or the stage turns into a black void
  const stageMat = new THREE.MeshStandardMaterial({ color: LOOKS.warm[0], roughness: 0.88, side: THREE.DoubleSide });
  const stage = new THREE.Mesh(cyc(), stageMat); stage.receiveShadow = true; scene.add(stage);

  const key = new THREE.RectAreaLight(0xfff3e8, 5.5, 22, 16); key.position.set(-16, 20, 22); key.lookAt(0, 4, 0); scene.add(key);
  const rim = new THREE.RectAreaLight(LOOKS.warm[1], 14, 6, 22); rim.position.set(14, 12, -10); rim.lookAt(0, 4, 0); scene.add(rim);
  const top = new THREE.RectAreaLight(0xffffff, 1.6, 20, 20); top.position.set(0, 32, 2); top.lookAt(0, 0, 0); scene.add(top);
  const sun = new THREE.DirectionalLight(0xffffff, 1.6); sun.position.set(-10, 28, 16); sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048); sun.shadow.radius = 8; sun.shadow.bias = -0.0003; sun.shadow.normalBias = 0.02;
  Object.assign(sun.shadow.camera, { left: -20, right: 20, top: 20, bottom: -20, near: 1, far: 80 }); scene.add(sun, sun.target);
  scene.add(new THREE.HemisphereLight(0xdfe6ff, 0x2a1d16, 0.25));
  // a soft pool on the floor and a glow on the wall behind, so the stage reads as a lit studio
  const pool = new THREE.SpotLight(0xffe6d2, 420, 80, 0.5, 1, 1.6); pool.position.set(0, 40, 8); pool.target.position.set(0, 0, -2); scene.add(pool, pool.target);
  const wash = new THREE.SpotLight(0xffb48a, 600, 90, 0.42, 1, 1.4); wash.position.set(0, 6, 20); wash.target.position.set(0, 14, -34); scene.add(wash, wash.target);

  const composer = new EffectComposer(renderer);
  composer.setSize(W, H);
  composer.addPass(new RenderPass(scene, camera));
  const ao = new GTAOPass(scene, camera, W / 2, H / 2); ao.blendIntensity = 0.85;
  ao.updateGtaoMaterial({ radius: 1.6, distanceExponent: 1.6, thickness: 2, scale: 1, samples: 16 });
  composer.addPass(ao);
  const bokeh = new BokehPass(scene, camera, { focus: 30, aperture: 0.0016, maxblur: 0.006 });
  composer.addPass(bokeh);
  composer.addPass(new UnrealBloomPass(new THREE.Vector2(W / 2, H / 2), 0.18, 0.5, 0.95));
  composer.addPass(new OutputPass());

  // contact shadow under the mascot: fades and shrinks as he leaves the floor
  const blobTex = canvasTex(256, 256, (g) => {
    const gr = g.createRadialGradient(128, 128, 0, 128, 128, 128);
    gr.addColorStop(0, "rgba(0,0,0,0.75)"); gr.addColorStop(0.55, "rgba(0,0,0,0.35)"); gr.addColorStop(1, "rgba(0,0,0,0)");
    g.fillStyle = gr; g.fillRect(0, 0, 256, 256);
  }, false);
  const blob = new THREE.Mesh(new THREE.PlaneGeometry(9.5, 5.2), new THREE.MeshBasicMaterial({ map: blobTex, transparent: true, depthWrite: false }));
  blob.rotation.x = -Math.PI / 2; scene.add(blob);

  // landing ripples: two thin rings per landing, the second a beat later
  const ringGeo = new THREE.RingGeometry(0.96, 1, 128);
  const ripples = Array.from({ length: 8 }, () => {
    const m = new THREE.Mesh(ringGeo, new THREE.MeshBasicMaterial({ color: 0xffe2cc, transparent: true, depthWrite: false, toneMapped: false }));
    m.rotation.x = -Math.PI / 2; m.visible = false; scene.add(m); return m;
  });

  const S = {
    THREE, renderer, scene, camera, composer, bokeh, stageMat, rim, W, H,
    look(name) { const [st, rm] = LOOKS[name] || LOOKS.warm; stageMat.color.setHex(st); rim.color.setHex(rm); },
    // shadow follows a mascot (C from makeClawd)
    shadow(C) {
      const lift = C.root.position.y;
      blob.position.set(C.root.position.x, 0.025, C.root.position.z + 0.2);
      blob.scale.setScalar(1 - Math.min(0.45, lift * 0.09)); blob.material.opacity = 1 - Math.min(0.75, lift * 0.18);
      blob.rotation.z = -C.root.rotation.y;
    },
    // events: [[t, x, z, colour?]] in the same clock as u
    ripples(events, u) {
      let n = 0; ripples.forEach((r) => (r.visible = false));
      events.forEach(([t0, x, z, c]) => [0, 0.12].forEach((lag, j) => {
        const k = (u - t0 - lag) / 0.8; if (k <= 0 || k >= 1 || n >= ripples.length) return;
        const r = ripples[n++]; r.visible = true; r.position.set(x, 0.03 + j * 0.004, z);
        r.scale.setScalar(1.6 + io(k) * (j ? 4.5 : 6.5)); r.material.color.setHex(c || 0xffe2cc); r.material.opacity = (1 - k) * (j ? 0.45 : 0.8);
      }));
    },
    // camera keys: [[u, [x,y,z], [lookx,looky,lookz]], ...]; eased between keys, a breath of drift, focus on `focusAt`
    camera(keys, u, t, focusAt = [0, 3.5, 0]) {
      let i = 0; while (i < keys.length - 1 && u > keys[i + 1][0]) i++;
      const a = keys[i], b = keys[Math.min(i + 1, keys.length - 1)];
      const k = b === a ? 0 : io((u - a[0]) / (b[0] - a[0]));
      const p = vlerp(a[1], b[1], k), l = vlerp(a[2], b[2], k);
      camera.position.set(p[0] + Math.sin(t * 0.6) * 0.1, p[1] + Math.sin(t * 0.8) * 0.07, p[2]);
      camera.lookAt(l[0], l[1], l[2]);
      bokeh.uniforms.focus.value = camera.position.distanceTo(new THREE.Vector3(...focusAt));
    },
    render() { composer.render(); },
  };
  return S;
}

export function canvasTex(w, h, draw, srgb = true) {
  const c = document.createElement("canvas"); c.width = w; c.height = h;
  const g = c.getContext("2d"); draw(g, w, h);
  const t = new THREE.CanvasTexture(c); if (srgb) t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8;
  t.userData = { c, g, draw }; return t;
}
