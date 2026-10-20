// Claude's mascot as a soft vinyl-toy model: an inflated pillow body, inset glossy eyes with catchlights,
// two-part pincers and capsule legs with feet. Everything is built in code so poses stay seekable.
import * as THREE from "three";
import { RoundedBoxGeometry } from "three/addons/geometries/RoundedBoxGeometry.js";

const ORANGE = new THREE.Color(0xd06a45);

// tiny surface grain, so highlights break up like a moulded toy instead of looking like plastic CG
function grainNormalMap(size = 256) {
  const h = new Float32Array(size * size);
  const rnd = (i) => { const x = Math.sin(i * 12.9898 + 78.233) * 43758.5453; return x - Math.floor(x); };
  for (let o = 0, amp = 1, cell = 32; o < 4; o++, amp *= 0.5, cell /= 2) {
    for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
      const gx = x / cell, gy = y / cell, x0 = Math.floor(gx), y0 = Math.floor(gy), fx = gx - x0, fy = gy - y0;
      const n = (i, j) => rnd(((x0 + i) % (size / cell)) * 157 + ((y0 + j) % (size / cell)) * 311 + o * 977);
      const sx = fx * fx * (3 - 2 * fx), sy = fy * fy * (3 - 2 * fy);
      h[y * size + x] += amp * ((n(0, 0) * (1 - sx) + n(1, 0) * sx) * (1 - sy) + (n(0, 1) * (1 - sx) + n(1, 1) * sx) * sy);
    }
  }
  const data = new Uint8Array(size * size * 4);
  for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
    const at = (a, b) => h[((b + size) % size) * size + ((a + size) % size)];
    const dx = at(x + 1, y) - at(x - 1, y), dy = at(x, y + 1) - at(x, y - 1);
    const l = Math.hypot(dx, dy, 0.5), i = (y * size + x) * 4;
    data[i] = (-dx / l * 0.5 + 0.5) * 255; data[i + 1] = (-dy / l * 0.5 + 0.5) * 255; data[i + 2] = (0.5 / l * 0.5 + 0.5) * 255; data[i + 3] = 255;
  }
  const t = new THREE.DataTexture(data, size, size, THREE.RGBAFormat);
  t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(3, 3); t.needsUpdate = true;
  return t;
}

// push each face of a rounded box outward so it reads as a soft, slightly inflated form
function pillow(w, h, d, r, bulge, seg = 16) {
  const g = new RoundedBoxGeometry(w, h, d, seg, r);
  const p = g.attributes.position, hw = w / 2, hh = h / 2, hd = d / 2;
  for (let i = 0; i < p.count; i++) {
    let x = p.getX(i), y = p.getY(i), z = p.getZ(i);
    const nx = x / hw, ny = y / hh, nz = z / hd;
    const fz = Math.max(0, (1 - nx * nx) * (1 - ny * ny)), fx = Math.max(0, (1 - ny * ny) * (1 - nz * nz)), fy = Math.max(0, (1 - nx * nx) * (1 - nz * nz));
    z += Math.sign(z) * bulge[2] * fz; x += Math.sign(x) * bulge[0] * fx; y += Math.sign(y) * bulge[1] * fy;
    p.setXYZ(i, x, y, z);
  }
  g.computeVertexNormals();
  return g;
}
// darken toward the underside: cheap baked occlusion that keeps the form readable under soft light
function bakeShade(geo, y0, y1, dark = 0.62) {
  const p = geo.attributes.position, c = new Float32Array(p.count * 3);
  for (let i = 0; i < p.count; i++) {
    const k = Math.min(1, Math.max(0, (p.getY(i) - y0) / (y1 - y0))), s = dark + (1 - dark) * Math.pow(k, 0.7);
    c[i * 3] = s; c[i * 3 + 1] = s * 0.97; c[i * 3 + 2] = s * 0.95;
  }
  geo.setAttribute("color", new THREE.BufferAttribute(c, 3));
  return geo;
}

export function makeClawd(scene) {
  const grain = grainNormalMap();
  const skin = new THREE.MeshPhysicalMaterial({
    color: ORANGE, vertexColors: true, roughness: 0.46, normalMap: grain, normalScale: new THREE.Vector2(0.06, 0.06),
    clearcoat: 0.35, clearcoatRoughness: 0.45, sheen: 0.7, sheenColor: new THREE.Color(0xffb38f), sheenRoughness: 0.55,
    emissive: ORANGE, emissiveIntensity: 0,
  });
  const skinDark = skin.clone(); skinDark.color = ORANGE.clone().multiplyScalar(0.8);
  const gloss = new THREE.MeshPhysicalMaterial({ color: 0x0d0a09, roughness: 0.06, clearcoat: 1, clearcoatRoughness: 0.03, metalness: 0 });
  const socket = new THREE.MeshPhysicalMaterial({ color: ORANGE.clone().multiplyScalar(0.55), roughness: 0.7, sheen: 0.4, sheenColor: new THREE.Color(0x8a3a20) });
  const spark = new THREE.MeshBasicMaterial({ color: 0xffffff, toneMapped: false });
  const mesh = (geo, m) => { const o = new THREE.Mesh(geo, m); o.castShadow = true; o.receiveShadow = true; return o; };

  const root = new THREE.Group(), body = new THREE.Group(); root.add(body);
  const torso = mesh(bakeShade(pillow(6, 3.7, 3.1, 0.78, [0.1, 0.12, 0.26]), -1.85, 1.85), skin);
  torso.position.y = 3.35; body.add(torso);
  const seamMat = new THREE.MeshPhysicalMaterial({ color: ORANGE.clone().multiplyScalar(0.62), roughness: 0.6 });
  const seam = new THREE.Mesh(new THREE.TorusGeometry(1, 0.035, 8, 96), seamMat); seam.rotation.x = Math.PI / 2; seam.scale.set(3.08, 1.6, 1); seam.position.set(0, 3.35, 0); body.add(seam);
  seam.visible = false;

  // eyes sit in shallow sockets, with a fixed catchlight so they read as alive from any angle
  const eyes = [-1.28, 1.28].map((x) => {
    const g = new THREE.Group(); g.position.set(x, 3.78, 1.68); body.add(g);
    const so = mesh(new THREE.CapsuleGeometry(0.42, 0.62, 8, 28), socket); so.scale.set(1, 1, 0.22); so.position.z = -0.06; g.add(so);
    const e = mesh(new THREE.CapsuleGeometry(0.31, 0.56, 10, 32), gloss); e.scale.set(1, 1, 0.5); g.add(e);
    const s1 = new THREE.Mesh(new THREE.SphereGeometry(0.085, 16, 12), spark); s1.position.set(-0.11, 0.3, 0.16); g.add(s1);
    const s2 = new THREE.Mesh(new THREE.SphereGeometry(0.04, 12, 8), spark); s2.position.set(0.1, 0.12, 0.16); g.add(s2);
    g.userData = { e, s1, s2 }; return g;
  });

  // arms end in pincers: a mitt with an upper and lower jaw on a hinge
  const arms = [-1, 1].map((side) => {
    const shoulder = new THREE.Group(); shoulder.position.set(side * 2.95, 3.1, 0.1); body.add(shoulder);
    const upper = mesh(bakeShade(pillow(1.4, 1.05, 1.2, 0.42, [0.04, 0.04, 0.06], 6), -0.5, 0.5, 0.75), skin);
    upper.position.x = side * 0.62; shoulder.add(upper);
    const hinge = new THREE.Group(); hinge.position.set(side * 1.28, 0.02, 0.05); shoulder.add(hinge);
    const knuckle = mesh(new THREE.SphereGeometry(0.42, 32, 20), skinDark); knuckle.position.copy(hinge.position); knuckle.scale.set(1, 0.95, 1.05); shoulder.add(knuckle);
    const jawGeo = bakeShade(pillow(1.1, 0.5, 0.95, 0.22, [0.03, 0.04, 0.04], 8), -0.25, 0.25, 0.78);
    const top = mesh(jawGeo, skin), bot = mesh(jawGeo, skinDark);
    const jt = new THREE.Group(), jb = new THREE.Group(); hinge.add(jt, jb);
    top.position.set(side * 0.5, 0.27, 0); bot.position.set(side * 0.44, -0.25, 0); bot.scale.set(0.86, 0.85, 0.92);
    jt.add(top); jb.add(bot);
    shoulder.userData = { jt, jb, side }; return shoulder;
  });

  // capsule legs with rounded feet
  const legs = [-2.15, -0.72, 0.72, 2.15].map((x, i) => {
    const g = new THREE.Group(); g.position.set(x, 1.62, i % 2 ? 0.12 : -0.12); body.add(g);
    const leg = mesh(bakeShade(new THREE.CapsuleGeometry(0.4, 0.86, 8, 24), -0.85, 0.6, 0.55), skin); leg.position.y = -0.55; g.add(leg);
    const foot = mesh(bakeShade(new THREE.SphereGeometry(0.5, 28, 18), -0.5, 0.3, 0.6), skinDark); foot.scale.set(1.05, 0.55, 1.25); foot.position.set(0, -1.32, 0.12); g.add(foot);
    return g;
  });

  scene.add(root);
  return { root, body, torso, eyes, arms, legs, skin, skinDark };
}

// jumps: [[t0, height, airtime]] in local time; returns lift and squash (positive = squashed)
export function jumpState(jumps, u) {
  let y = 0, sq = 0;
  (jumps || []).forEach(([t0, h, air]) => {
    const a = u - t0;
    if (a > -0.18 && a <= 0) sq += 0.5 * Math.sin(Math.PI * (a + 0.18) / 0.18);
    if (a > 0 && a < air) { const k = a / air; y += h * 4 * k * (1 - k); sq -= 0.26 * (1 - Math.min(1, k * 2.2)); }
    if (a >= air && a < air + 0.5) { const k = (a - air) / 0.5; sq += 0.62 * Math.exp(-5 * k) * Math.cos(k * 10); }
  });
  return { y, sq };
}

// o: { p, ry, u, jumps, walk, phase, look, tilt, wave, armL, armR, tap, snap, glow, blinkOff }
export function pose(C, t, o) {
  const { y, sq } = jumpState(o.jumps, o.u ?? 0);
  const walk = o.walk || 0, ph = (o.phase ?? t) * 10;
  C.root.position.set(o.p[0], o.p[1] + y + walk * Math.abs(Math.sin(ph)) * 0.22, o.p[2]);
  C.root.rotation.y = o.ry || 0;
  C.body.scale.set(1 + sq * 0.15, 1 - sq * 0.21, 1 + sq * 0.15);
  C.body.rotation.x = (o.look || 0) + 0.02 * Math.sin(t * 2.0);
  C.body.rotation.z = (o.tilt || 0) + 0.018 * Math.sin(t * 1.5) + walk * 0.05 * Math.sin(ph);
  C.torso.position.y = 3.35 + 0.07 * Math.sin(t * 3.1);
  C.torso.scale.set(1 + 0.008 * Math.sin(t * 3.1), 1 - 0.008 * Math.sin(t * 3.1), 1);
  // blinks every few seconds, eyes squeeze shut rather than vanish
  const bt = ((t + (o.blinkOff || 0)) % 3.4), bl = bt < 0.14 ? Math.max(0.08, Math.abs(bt - 0.07) / 0.07) : 1;
  C.eyes.forEach((g) => { g.userData.e.scale.y = bl; g.userData.s1.visible = g.userData.s2.visible = bl > 0.5; g.position.y = 3.78 + (o.lookUp || 0) * 0.12; });
  C.arms.forEach((s) => {
    const { jt, jb, side } = s.userData, L = side < 0;
    const lift = (L ? o.armL : o.armR) || 0, wave = !L && o.wave ? 1.9 + 0.4 * Math.sin(t * 12) : 0;
    s.rotation.z = side * (-(lift + wave) + 0.22 * Math.sin(t * 7 + (L ? 0 : 1.3)) * (o.tap || 0) + walk * 0.3 * Math.sin(ph + (L ? 0 : Math.PI)));
    const open = (o.snap ? Math.max(0, Math.sin(t * 7)) ** 2 : 0) * 0.5 + 0.1;
    jt.rotation.z = side * open; jb.rotation.z = -side * open * 0.8;
  });
  C.legs.forEach((l, i) => { const k = Math.max(0, Math.sin(ph + (i % 2) * Math.PI)) * walk; l.position.y = 1.62 + k * 0.5; l.rotation.x = -k * 0.35; });
  C.skin.emissiveIntensity = o.glow || 0; C.skinDark.emissiveIntensity = (o.glow || 0) * 0.8;
}
