// Minecraft-style baroobi in a dark-oak room, rendered from HyperFrames time (hf-seek), never wall-clock.
// Reads window.DATA: { total, steps:[{start,end,pose}], cues:[[t, shape]] }.
import * as THREE from "https://cdn.jsdelivr.net/npm/three@0.181.2/+esm";

const D = window.DATA;
const W = 1080, H = 1920;
const canvas = document.getElementById("mc");
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true });
renderer.setSize(W, H, false);
renderer.setPixelRatio(1);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.2;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;

const loader = new THREE.TextureLoader();
function tex(name, repeat) {
  const t = loader.load("assets/voxel/" + name);
  t.magFilter = THREE.NearestFilter;
  t.minFilter = THREE.NearestFilter;
  t.generateMipmaps = false;
  t.colorSpace = THREE.SRGBColorSpace;
  if (repeat) {
    t.wrapS = t.wrapT = THREE.RepeatWrapping;
    t.repeat.set(repeat[0], repeat[1]);
  }
  return t;
}
const mat = (t, o = {}) => new THREE.MeshStandardMaterial({ map: t, roughness: 0.92, metalness: 0, ...o });
const clear = new THREE.MeshStandardMaterial({ transparent: true, opacity: 0, depthWrite: false });
function box(w, h, d, mats) {
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mats);
  m.castShadow = true;
  m.receiveShadow = true;
  return m;
}

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x1c120b);

// ---- room ----------------------------------------------------------------
const BLOCK = 7;
const wall = new THREE.Mesh(new THREE.PlaneGeometry(140, 140), mat(tex("dark_oak.png", [140 / BLOCK, 140 / BLOCK])));
wall.position.set(0, 40, -8);
wall.receiveShadow = true;
scene.add(wall);
const panel = box(140, 34, 0.6, mat(tex("panel.png", [140 / BLOCK, 34 / BLOCK])));
panel.position.set(0, 4, -7.6);
scene.add(panel);
const oak = tex("dark_oak.png", [2, 2]);
const table = box(16, 18, 10, mat(oak));
table.position.set(24, 6, -2);
scene.add(table);
const pot = box(4, 4, 4, mat(tex("pot.png")));
pot.position.set(21, 17, -2);
scene.add(pot);
const leafMat = mat(tex("leaves.png"), { transparent: true, alphaTest: 0.5, side: THREE.DoubleSide });
[[21, 21, -2, 3.4], [19.6, 23, -1.2, 2.4], [22.4, 24, -2.6, 2.6], [21, 26, -2, 2]].forEach(([x, y, z, s]) => {
  const l = box(s, s, s, leafMat);
  l.position.set(x, y, z);
  scene.add(l);
});

// ---- character (Minecraft proportions, 1 unit = 1 skin pixel at 8 px/face) --
const faces = {};
for (const m of "XABCDEFGH") {
  faces[m] = tex(`face_${m}.png`);
  faces[m + "_b"] = tex(`face_${m}_b.png`);
}
const headFront = mat(faces.X);
const head = box(8, 8, 8, [
  mat(tex("head_right.png")), mat(tex("head_left.png")), mat(tex("head_top.png")),
  mat(tex("head_bottom.png")), headFront, mat(tex("head_back.png")),
]);
const hairSide = tex("hair_side.png"), hairOpts = { transparent: true, alphaTest: 0.5 };
const hair = box(8.9, 8.9, 8.9, [
  mat(hairSide, hairOpts), mat(hairSide, hairOpts), mat(tex("hair_top.png"), hairOpts),
  clear, mat(tex("hair_front.png"), hairOpts), mat(tex("hair_back.png"), hairOpts),
]);
const headPivot = new THREE.Group();          // pivot at the neck so nods look natural
head.position.y = 4;
hair.position.y = 4.15;
headPivot.add(head, hair);
headPivot.position.set(0, 24, 0);

const bodySide = tex("body_side.png");
const body = box(8, 12, 4, [mat(bodySide), mat(bodySide), mat(tex("body_top.png")), mat(tex("arm_top.png")),
  mat(tex("body_front.png")), mat(tex("body_back.png"))]);
body.position.y = 18;

function makeArm(sign) {
  const side = tex("arm_side.png");
  const a = box(4, 12, 4, [mat(side), mat(side), mat(tex("arm_top.png")), mat(tex("arm_bottom.png")), mat(side), mat(side)]);
  a.position.y = -4;
  const pivot = new THREE.Group();
  pivot.position.set(sign * 6, 22, 0);
  pivot.add(a);
  return pivot;
}
const armL = makeArm(-1), armR = makeArm(1);     // R = viewer's right, the gesturing arm
const char = new THREE.Group();
char.add(body, headPivot, armL, armR);
scene.add(char);

// ---- light: warm key from the right like the reference, cool weak fill ----
scene.add(new THREE.HemisphereLight(0xffe2c4, 0x140b06, 0.55));
const key = new THREE.DirectionalLight(0xffb36b, 3.1);
key.position.set(38, 46, 34);
key.castShadow = true;
key.shadow.mapSize.set(1024, 1024);
Object.assign(key.shadow.camera, { left: -45, right: 45, top: 60, bottom: -10, near: 1, far: 160 });
key.shadow.bias = -0.0008;
scene.add(key);
const fill = new THREE.DirectionalLight(0x8fa6d8, 0.35);
fill.position.set(-40, 30, 30);
scene.add(fill);

// ---- camera framings: hard cut per beat, slow push-in inside a beat --------
const camera = new THREE.PerspectiveCamera(30, W / H, 0.5, 400);
const HEAD_Y = 28, HEAD_ON_SCREEN = D.headOn || 0.76;   // head centre sits 76% down the frame, under the cards (v2 panels: lower)
function frame(t, i, st) {
  const close = i % 2 === 1;
  const dist = close ? 104 : 124;
  const fov = (close ? 26 : 30) - 0.8 * Math.min(1, (t - st.start) / Math.max(0.5, st.end - st.start));
  camera.fov = fov;
  camera.updateProjectionMatrix();
  const half = Math.tan((fov * Math.PI) / 360) * dist;
  const ty = HEAD_Y + (HEAD_ON_SCREEN * 2 - 1) * half;
  const x = close ? 5 : 8;                    // he sits left of centre, clear of the progress grid
  camera.position.set(x, ty + 5, dist);       // a touch above eye line so the curls on top read
  camera.lookAt(x * 0.4, ty, 0);
  camera.rotateZ(close ? -0.035 : -0.05);    // slight dutch angle
}

// ---- performance from data ---------------------------------------------------
const OPEN = { X: 0, A: 0, B: 0.3, C: 0.65, D: 1, E: 0.6, F: 0.35, G: 0.3, H: 0.6 };
function cueAt(t) {
  let lo = 0, hi = D.cues.length - 1, v = "X";
  while (lo <= hi) {
    const mid = (lo + hi) >> 1;
    if (D.cues[mid][0] <= t) { v = D.cues[mid][1]; lo = mid + 1; } else hi = mid - 1;
  }
  return v;
}
const talk = (t) => [0, 0.05, 0.1, 0.15, 0.2].reduce((a, d) => a + OPEN[cueAt(t - d)], 0) / 5;
const hash = (n) => { const x = Math.sin(n * 91.345 + 7.13) * 43758.5453; return x - Math.floor(x); };
const blinks = [];
for (let t = 1.4, n = 0; t < D.total; t += 2.4 + hash(n++) * 1.8) blinks.push(t);
const blinking = (t) => blinks.some((b) => t >= b && t < b + 0.12);

const POSES = {
  rest:  { L: [0.05, -0.06], R: [0.05, 0.06], roll: 0 },
  point: { L: [0.05, -0.06], R: [-2.2, 0.38], roll: 0.03 },
  wave:  { L: [0.05, -0.06], R: [-0.25, 2.55], roll: -0.02, wave: true },
  thumb: { L: [0.05, -0.06], R: [-1.35, 0.16], roll: 0.02 },
  shrug: { L: [-0.65, -0.95], R: [-0.65, 0.95], roll: 0.13 },
};
const easeOutBack = (k) => 1 + 2.4 * Math.pow(k - 1, 3) + 1.4 * Math.pow(k - 1, 2);
function stepAt(t) {
  let i = 0;
  while (i < D.steps.length - 1 && t >= D.steps[i + 1].start) i++;
  return i;
}

function renderAt(t) {
  const i = stepAt(t), st = D.steps[i];
  const cur = POSES[st.pose] || POSES.rest, prev = POSES[(D.steps[i - 1] || st).pose] || POSES.rest;
  const k = easeOutBack(Math.min(1, Math.max(0, (t - st.start) / 0.2)));
  const mix = (a, b) => a + (b - a) * k;
  const sway = 0.04 * Math.sin(t * 2.6);
  armL.rotation.set(mix(prev.L[0], cur.L[0]) + sway * 0.5, 0, mix(prev.L[1], cur.L[1]));
  armR.rotation.set(mix(prev.R[0], cur.R[0]) - sway, 0,
    mix(prev.R[1], cur.R[1]) + (cur.wave ? 0.2 * Math.sin(t * 11) : 0));
  const tk = talk(t);
  headPivot.rotation.set(0.07 * tk + 0.015 * Math.sin(t * 1.7), -0.22 + 0.05 * Math.sin(t * 0.55),
    0.05 + mix(prev.roll, cur.roll) + 0.015 * Math.sin(t * 0.9));
  body.scale.y = 1 + 0.006 * Math.sin(t * 2.2);
  const shape = cueAt(t);
  headFront.map = faces[shape + (blinking(t) ? "_b" : "")];
  frame(t, i, st);
  renderer.render(scene, camera);
}

window.__hf = window.__hf || {};
window.__hf.buildReady = window.__hf.buildReady || {};
window.__hf.buildReady.voxel = new Promise((resolve) => {
  THREE.DefaultLoadingManager.onLoad = () => {
    renderer.compile(scene, camera);
    renderAt(window.__hfThreeTime || 0);
    resolve();
  };
});
window.addEventListener("hf-seek", (e) => renderAt(e.detail.time));
