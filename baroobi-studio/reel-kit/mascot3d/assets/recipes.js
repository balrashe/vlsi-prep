// Reusable props for mascot reels. Each recipe adds meshes to a group and returns an update(u, t) driven by the
// beat's local time u. Keep props clean and readable: one idea per beat, nothing busy behind the mascot.
import * as THREE from "three";
import { RoundedBoxGeometry } from "three/addons/geometries/RoundedBoxGeometry.js";
import { FontLoader } from "three/addons/loaders/FontLoader.js";
import { TextGeometry } from "three/addons/geometries/TextGeometry.js";
import { rnd, clamp, lerp, io, back, canvasTex } from "./stage.js";

export const phys = (color, o = {}) => new THREE.MeshPhysicalMaterial({ color, roughness: 0.42, clearcoat: 0.6, clearcoatRoughness: 0.25, ...o });
export function rbox(w, h, d, r, m, seg = 4) {
  const mesh = new THREE.Mesh(new RoundedBoxGeometry(w, h, d, seg, Math.min(r, w / 2, h / 2, d / 2)), m);
  mesh.castShadow = true; mesh.receiveShadow = true; return mesh;
}
const rr = (g, x, y, w, h, r) => { g.beginPath(); g.roundRect(x, y, w, h, r); };

// ---- 3D type: glossy bevelled numbers and words ---------------------------------------------------------
let FONT;
export async function loadFont(url = "assets/helvetiker_bold.typeface.json") { FONT = await new FontLoader().loadAsync(url); }
export const MAT = {
  white: () => phys(0xf2ece2, { roughness: 0.18, clearcoat: 1, clearcoatRoughness: 0.08 }),
  gold: () => phys(0xf0b54a, { roughness: 0.18, metalness: 0.75, clearcoat: 1, emissive: 0x6b3d00, emissiveIntensity: 0.35 }),
  orange: () => phys(0xd06a45, { roughness: 0.3, clearcoat: 1, emissive: 0x5a1c00, emissiveIntensity: 0.25 }),
};
export function text3d(str, size, mat) {
  const geo = new TextGeometry(str, { font: FONT, size, depth: size * 0.3, curveSegments: 14, bevelEnabled: true,
    bevelThickness: size * 0.06, bevelSize: size * 0.037, bevelSegments: 8 });
  geo.computeBoundingBox(); const bb = geo.boundingBox;
  geo.translate(-(bb.max.x + bb.min.x) / 2, -bb.min.y, -(bb.max.z + bb.min.z) / 2);
  const m = new THREE.Mesh(geo, mat); m.castShadow = true; m.receiveShadow = true; return m;
}
// show a number/word between a and b: rises in with overshoot, sinks out; gentle turn while held
export function hold3d(m, u, t, a, b, y0) {
  const kin = back((u - a) / 0.4), kout = io((u - b) / 0.22);
  m.visible = u > a && u < b + 0.22; m.scale.setScalar(Math.max(0.001, kin * (1 - kout)));
  m.rotation.y = -0.15 + 0.12 * Math.sin(t * 0.6); m.position.y = y0 + 0.2 * Math.sin(t * 1.1);
}

// ---- falling paper (applications, documents) ---------------------------------------------------------
export function papers(group, n, { label = "Application", spread = 12, window = [0, 2], seed = 0 } = {}) {
  const tex = canvasTex(512, 680, (g) => {
    g.fillStyle = "#f4f0e8"; g.fillRect(0, 0, 512, 680); g.fillStyle = "#26211d"; g.font = "800 34px Inter, sans-serif"; g.fillText(label, 40, 72);
    g.fillStyle = "#d9534a"; g.fillRect(40, 92, 70, 6); g.fillStyle = "#cfc8bb"; for (let y = 140; y < 640; y += 34) g.fillRect(40, y, 260 + ((y * 37) % 150), 11);
  });
  const geo = new THREE.PlaneGeometry(2.3, 3.05, 8, 10);
  const p = geo.attributes.position; for (let i = 0; i < p.count; i++) p.setZ(i, 0.16 * Math.sin(p.getX(i) * 1.3) + 0.04 * p.getY(i) * p.getY(i));
  geo.computeVertexNormals();
  const mat = new THREE.MeshStandardMaterial({ map: tex, side: THREE.DoubleSide, roughness: 0.8, color: 0xd9d4ca });
  const list = Array.from({ length: n }, (_, i) => {
    const m = new THREE.Mesh(geo, mat); m.castShadow = true; m.receiveShadow = true; group.add(m);
    const a = rnd(i + seed) * Math.PI * 2, r = 5 + rnd(i + seed + 9) ** 0.7 * spread;
    return { m, x: Math.cos(a) * r, z: Math.sin(a) * r * 0.7 - 3, t0: window[0] + rnd(i + seed + 3) * (window[1] - window[0]), rz: rnd(i + 4) * 6.28, s: 0.6 + rnd(i + 5) };
  });
  return (u, t) => list.forEach((q, i) => {
    const k = clamp((u - q.t0) / 1.6), e = k * k, sw = Math.sin(t * 3 * q.s + i) * (1 - k);
    q.m.visible = u > q.t0; q.m.position.set(q.x + sw * 1.2, 30 - 29.95 * e + (i % 6) * 0.01, q.z);
    q.m.rotation.set(-Math.PI / 2 + sw * 0.9 + (1 - k) * 0.5, 0, q.rz + (1 - k) * 1.4);
  });
}

// ---- floating UI panel (terminal, browser, profile card): rounded body + a canvas face ------------------
// draw(g, w, h, u) is called every frame when `live`, so terminals can type
export function panel(w, h, draw, { frame = 0x1b1a20, glow = 0.35, live = false, px = 1000 } = {}) {
  const g = new THREE.Group();
  g.add(rbox(w, h, 0.3, 0.3, phys(frame, { roughness: 0.35 })));
  const t = canvasTex(px, Math.round(px * h / w), (gg, cw, ch) => draw(gg, cw, ch, 0));
  const face = new THREE.Mesh(new THREE.PlaneGeometry(w - 0.3, h - 0.3),
    new THREE.MeshStandardMaterial({ map: t, emissive: 0xffffff, emissiveMap: t, emissiveIntensity: glow, roughness: 0.5, color: 0xdbdbdb }));
  face.position.z = 0.16; g.add(face);
  g.userData.update = live ? (u) => { const { g: gg, c } = t.userData; draw(gg, c.width, c.height, u); t.needsUpdate = true; } : () => {};
  return g;
}
export function terminalDraw(lines, title = "Claude Code") {
  // lines: [[t, text, colour]] typed out over 0.25 s each
  return (g, w, h, u) => {
    g.fillStyle = "#121117"; g.fillRect(0, 0, w, h); g.fillStyle = "#1d1b24"; g.fillRect(0, 0, w, 70);
    ["#ff5f57", "#febc2e", "#28c840"].forEach((c, i) => { g.beginPath(); g.arc(40 + i * 36, 35, 11, 0, 7); g.fillStyle = c; g.fill(); });
    g.fillStyle = "#8a857c"; g.font = "700 28px Inter, sans-serif"; g.fillText(title, 160, 45);
    g.font = "700 42px 'JetBrains Mono', monospace";
    lines.forEach(([t0, s, c], i) => { if (u < t0) return; const n = Math.floor(clamp((u - t0) / 0.25) * s.length); g.fillStyle = c || "#e8e6e1"; g.fillText(s.slice(0, n), 44, 140 + i * 66); });
  };
}
export function cardDraw(title, sub, accent = "#e08a3a") {
  return (g, w, h) => {
    g.fillStyle = "#fbfaf7"; g.fillRect(0, 0, w, h);
    rr(g, 36, 36, 84, 84, 20); g.fillStyle = accent; g.fill();
    g.fillStyle = "#8a857c"; g.font = "700 30px Inter, sans-serif"; g.fillText(sub, 144, 70);
    g.fillStyle = "#151515"; g.font = "900 46px Inter, sans-serif"; g.fillText(title, 144, 116);
    g.fillStyle = "#dcd7cd"; [0, 1, 2].forEach((k) => { rr(g, 36, 190 + k * 54, w - 120 - k * 120, 20, 10); g.fill(); });
  };
}

// ---- speech bubble that always faces the camera ----------------------------------------------------------
export function bubble(text, width = 8.8) {
  const t = canvasTex(1100, 300, (g, w, h) => {
    g.shadowColor = "rgba(0,0,0,0.25)"; g.shadowBlur = 24; rr(g, 20, 20, w - 40, h - 90, 60); g.fillStyle = "#fff"; g.fill();
    g.beginPath(); g.moveTo(w / 2 - 34, h - 72); g.lineTo(w / 2, h - 22); g.lineTo(w / 2 + 34, h - 72); g.fill();
    g.shadowBlur = 0; g.fillStyle = "#141414"; g.font = "800 74px Inter, sans-serif"; g.textAlign = "center"; g.fillText(text, w / 2, 150);
  });
  return new THREE.Mesh(new THREE.PlaneGeometry(width, width * 300 / 1100), new THREE.MeshBasicMaterial({ map: t, transparent: true, toneMapped: false, color: 0xe8e8e8 }));
}
// pop in at a, out at b (call every frame); `camera` keeps it facing the viewer
export function pop(m, u, a, b, camera) {
  const k = back((u - a) / 0.32), o = io((u - b) / 0.15);
  m.visible = u > a && u < b + 0.15; m.scale.setScalar(Math.max(0.001, k * (1 - o))); if (camera) m.lookAt(camera.position);
}

// ---- walking between marks: [[u, [x,0,z]], ...] -> position, moving?, facing -----------------------------
export function path(marks, u) {
  let i = 0; while (i < marks.length - 1 && u > marks[i + 1][0]) i++;
  const a = marks[i], b = marks[Math.min(i + 1, marks.length - 1)];
  const k = b === a ? 0 : io((u - a[0]) / (b[0] - a[0]));
  const moving = a[1] !== b[1] && u > a[0] && u < b[0];
  return { p: a[1].map((v, j) => lerp(v, b[1][j], k)), moving, ry: Math.atan2(b[1][0] - a[1][0], b[1][2] - a[1][2]) };
}

// ---- arc an object from one point to another (cards flying into a stack) ---------------------------------
export function arc(obj, from, to, u, t0, dur = 0.8, lift = 6) {
  const k = io((u - t0) / dur), mid = [(from[0] + to[0]) / 2, Math.max(from[1], to[1]) + lift, (from[2] + to[2]) / 2];
  const q = (i) => lerp(lerp(from[i], mid[i], k), lerp(mid[i], to[i], k), k);
  obj.position.set(q(0), q(1), q(2)); obj.visible = u > t0; return k;
}
