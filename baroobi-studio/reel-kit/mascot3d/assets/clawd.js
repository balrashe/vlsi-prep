// Claude's mascot as a soft vinyl-toy model of the Claude Code logo glyph: a chunky block body, glossy eye
// slits with catchlights, square stub arms and four thin legs. Built in code so poses stay seekable.
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
  const spark = new THREE.MeshBasicMaterial({ color: 0xffffff, toneMapped: false });
  const mesh = (geo, m) => { const o = new THREE.Mesh(geo, m); o.castShadow = true; o.receiveShadow = true; return o; };

  // proportions follow the Claude Code logo glyph ( ▐▛███▜▌ / ▝▜█████▛▘ /  ▘▘ ▝▝ ): a 6x4 block, two tall eye
  // slits near the top corners, a square stub arm each side at mid height, four thin legs split two and two
  const root = new THREE.Group(), body = new THREE.Group(); root.add(body);
  const torso = mesh(bakeShade(pillow(6, 4, 3, 0.34, [0.05, 0.05, 0.08], 12), -2, 2, 0.7), skin);
  torso.position.y = 3; body.add(torso);

  // eyes: glossy dark slits set just proud of the face, with a small catchlight so they read as alive
  const eyes = [-1.75, 1.75].map((x) => {
    const g = new THREE.Group(); g.position.set(x, 3.5, 1.5); body.add(g);
    const e = mesh(new RoundedBoxGeometry(0.52, 1.02, 0.16, 4, 0.07), gloss); g.add(e);
    const s1 = new THREE.Mesh(new THREE.SphereGeometry(0.06, 16, 12), spark); s1.position.set(-0.1, 0.32, 0.09); g.add(s1);
    const s2 = new THREE.Mesh(new THREE.SphereGeometry(0.03, 12, 8), spark); s2.position.set(0.09, 0.18, 0.09); g.add(s2);
    g.userData = { e, s1, s2 }; return g;
  });

  // arms: one square stub each side, hinged at the body edge
  const arms = [-1, 1].map((side) => {
    const shoulder = new THREE.Group(); shoulder.position.set(side * 3, 2.5, 0); body.add(shoulder);
    const stub = mesh(bakeShade(pillow(1.1, 1, 1, 0.2, [0.02, 0.02, 0.02], 6), -0.5, 0.5, 0.75), skin);
    stub.position.x = side * 0.5; shoulder.add(stub);
    shoulder.userData = { side }; return shoulder;
  });

  // legs: four thin short posts, two under each half with a gap in the middle
  const legs = [-2.25, -1.25, 1.25, 2.25].map((x) => {
    const g = new THREE.Group(); g.position.set(x, 1, 0); body.add(g);
    const leg = mesh(bakeShade(new RoundedBoxGeometry(0.5, 1.08, 0.8, 4, 0.12), -0.54, 0.4, 0.55), skinDark); leg.position.y = -0.5; g.add(leg);
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
  C.torso.position.y = 3 + 0.06 * Math.sin(t * 3.1);
  C.torso.scale.set(1 + 0.008 * Math.sin(t * 3.1), 1 - 0.008 * Math.sin(t * 3.1), 1);
  // blinks every few seconds, eyes squeeze shut rather than vanish
  const bt = ((t + (o.blinkOff || 0)) % 3.4), bl = bt < 0.14 ? Math.max(0.08, Math.abs(bt - 0.07) / 0.07) : 1;
  C.eyes.forEach((g) => { g.userData.e.scale.y = bl; g.userData.s1.visible = g.userData.s2.visible = bl > 0.5; g.position.y = 3.5 + 0.06 * Math.sin(t * 3.1) + (o.lookUp || 0) * 0.1; });
  C.arms.forEach((s) => {
    const { side } = s.userData, L = side < 0;
    const lift = (L ? o.armL : o.armR) || 0, wave = !L && o.wave ? 1.9 + 0.4 * Math.sin(t * 12) : 0;
    s.rotation.z = side * (-(lift + wave) + 0.22 * Math.sin(t * 7 + (L ? 0 : 1.3)) * (o.tap || 0) + walk * 0.3 * Math.sin(ph + (L ? 0 : Math.PI)))
      + (o.snap ? side * 0.12 * Math.sin(t * 5) : 0);
  });
  C.legs.forEach((l, i) => { const k = Math.max(0, Math.sin(ph + (i % 2) * Math.PI)) * walk; l.position.y = 1 + k * 0.45; l.rotation.x = -k * 0.35; });
  C.skin.emissiveIntensity = o.glow || 0; C.skinDark.emissiveIntensity = (o.glow || 0) * 0.8;
}
