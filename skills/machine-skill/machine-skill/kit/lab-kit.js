// Machine Skill kit: the runtime every machine page is built on.
// One ES module. Paste it verbatim into the first <script type="module"> of a page
// (scripts/inline.mjs does that), or import it. It needs the import map from
// kit/template.html (three@0.170.0 from jsDelivr). MIT licence, see LICENSE.
//
// What it gives a machine page, so every output has the same polish:
//   studio      paper or night seamless, softbox environment, soft key shadow, contact shadow, GTAO, bloom, grade
//   materials   physically based metals, paints, polymers, glass, all with section caps and wear
//   geometry    lathe solids, shells, gears, blade rings, pipes, bolt circles, springs, rounded boxes
//   modes       explode, cutaway (half or quarter, real caps), x-ray, slow motion, labels, break it
//   editorial   prompt bar, serif title, one huge live number with a thin bar, readouts, controls, beat captions
//   effects     sparks, debris, flow particles along paths, exhaust plumes with shock diamonds, heat glow
//   film        ?film=1&shot=name : deterministic clock, camera timeline, cursor, captions, window.__film

import * as THREE from 'three'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js'
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js'
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js'
import { GTAOPass } from 'three/addons/postprocessing/GTAOPass.js'
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js'
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js'
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js'
import { RGBELoader } from 'three/addons/loaders/RGBELoader.js'
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js'
import { HorizontalBlurShader } from 'three/addons/shaders/HorizontalBlurShader.js'
import { VerticalBlurShader } from 'three/addons/shaders/VerticalBlurShader.js'
import * as BGU from 'three/addons/utils/BufferGeometryUtils.js'

export { THREE }
export const LAYER_FX = 1 // transparent effects: kept out of the AO and contact shadow passes

// ---------------------------------------------------------------- math

export const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x))
export const lerp = (a, b, t) => a + (b - a) * t
export const smoothstep = (a, b, x) => { const t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t) }
export const ease = {
  lin: (t) => t,
  io: (t) => t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2,
  in: (t) => t * t * t,
  out: (t) => 1 - Math.pow(1 - t, 3),
  expo: (t) => t >= 1 ? 1 : 1 - Math.pow(2, -10 * t),
  back: (t) => { const c = 1.4; return 1 + (c + 1) * Math.pow(t - 1, 3) + c * Math.pow(t - 1, 2) },
}
/** first order lag toward target with time constant tau (s): spool-up, thermal mass, filters */
export const approach = (v, target, tau, dt) => target + (v - target) * Math.exp(-dt / Math.max(1e-6, tau))
/** piecewise linear table lookup: xs ascending */
export function table(xs, ys, x) {
  if (x <= xs[0]) return ys[0]
  for (let i = 1; i < xs.length; i++) if (x <= xs[i]) return lerp(ys[i - 1], ys[i], (x - xs[i - 1]) / (xs[i] - xs[i - 1]))
  return ys[ys.length - 1]
}
/** one RK4 step of dy/dt = f(t, y) for an array state */
export function rk4(f, t, y, h) {
  const add = (a, b, k) => a.map((v, i) => v + b[i] * k)
  const k1 = f(t, y), k2 = f(t + h / 2, add(y, k1, h / 2)), k3 = f(t + h / 2, add(y, k2, h / 2)), k4 = f(t + h, add(y, k3, h))
  return y.map((v, i) => v + (h / 6) * (k1[i] + 2 * k2[i] + 2 * k3[i] + k4[i]))
}
/** number formatting with thin grouping: fmt(144712) = "144,712", fmt(3.14159, 2) = "3.14" */
export function fmt(v, digits = 0) {
  if (!isFinite(v)) return '--'
  return v.toLocaleString('en-US', { minimumFractionDigits: digits, maximumFractionDigits: digits })
}
/** seeded random, so films are deterministic */
export function rng(seed = 1) { let s = seed >>> 0 || 1; return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296 } }
/** blackbody colour (approximate, linear rgb) for a temperature in kelvin */
export function blackbody(T) {
  const t = clamp(T, 800, 12000) / 100
  let r, g, b
  if (t <= 66) { r = 255; g = 99.47 * Math.log(t) - 161.12; b = t <= 19 ? 0 : 138.52 * Math.log(t - 10) - 305.04 }
  else { r = 329.7 * Math.pow(t - 60, -0.1332); g = 288.12 * Math.pow(t - 60, -0.0755); b = 255 }
  return new THREE.Color(clamp(r / 255), clamp(g / 255), clamp(b / 255)).convertSRGBToLinear()
}

// ---------------------------------------------------------------- procedural textures

function canvasTex(size, draw, { repeat = [1, 1], color = false } = {}) {
  const c = document.createElement('canvas'); c.width = c.height = size
  const g = c.getContext('2d'); draw(g, size)
  const t = new THREE.CanvasTexture(c)
  t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(repeat[0], repeat[1]); t.anisotropy = 8
  t.colorSpace = color ? THREE.SRGBColorSpace : THREE.NoColorSpace
  return t
}
const TEX = {}
function tex(kind) {
  if (TEX[kind]) return TEX[kind]
  const R = rng(kind.length * 977)
  const S = 512
  const make = {
    // turning marks: fine rings along v (lathe u wraps around the axis, so rings run circumferentially)
    turned: (g) => { g.fillStyle = '#808080'; g.fillRect(0, 0, S, S); for (let y = 0; y < S; y++) { const v = 112 + R() * 40 + Math.sin(y * 0.9) * 10; g.fillStyle = `rgb(${v},${v},${v})`; g.fillRect(0, y, S, 1) } },
    // brushed: long streaks along u
    brushed: (g) => { g.fillStyle = '#7a7a7a'; g.fillRect(0, 0, S, S); for (let i = 0; i < 2600; i++) { const v = 90 + R() * 80; g.fillStyle = `rgba(${v},${v},${v},0.35)`; g.fillRect(R() * S, R() * S, 30 + R() * 220, 1) } },
    // cast / bead blasted: soft blotches plus grain
    cast: (g) => { g.fillStyle = '#808080'; g.fillRect(0, 0, S, S); for (let i = 0; i < 380; i++) { const v = 100 + R() * 60, r = 6 + R() * 40; const gr = g.createRadialGradient(0, 0, 0, 0, 0, r); gr.addColorStop(0, `rgba(${v},${v},${v},0.25)`); gr.addColorStop(1, 'rgba(128,128,128,0)'); g.save(); g.translate(R() * S, R() * S); g.fillStyle = gr; g.fillRect(-r, -r, 2 * r, 2 * r); g.restore() } const d = g.getImageData(0, 0, S, S); for (let i = 0; i < d.data.length; i += 4) { const n = (R() - 0.5) * 26; d.data[i] += n; d.data[i + 1] += n; d.data[i + 2] += n } g.putImageData(d, 0, 0) },
    // carbon twill weave (colour)
    carbon: (g) => { const n = 16, w = S / n; for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) { const on = ((i + j) >> 1) % 2 === 0; const gr = on ? g.createLinearGradient(i * w, 0, i * w + w, 0) : g.createLinearGradient(0, j * w, 0, j * w + w); gr.addColorStop(0, '#0d0e10'); gr.addColorStop(0.5, on ? '#3a3d42' : '#2a2c30'); gr.addColorStop(1, '#0d0e10'); g.fillStyle = gr; g.fillRect(i * w, j * w, w, w) } },
    // knurl diamonds (bump)
    knurl: (g) => { g.fillStyle = '#000'; g.fillRect(0, 0, S, S); g.strokeStyle = '#fff'; g.lineWidth = 6; for (let i = -S; i < 2 * S; i += 24) { g.beginPath(); g.moveTo(i, 0); g.lineTo(i + S, S); g.stroke(); g.beginPath(); g.moveTo(i, S); g.lineTo(i + S, 0); g.stroke() } },
    // smudges and dust for glossy parts
    smudge: (g) => { g.fillStyle = '#4a4a4a'; g.fillRect(0, 0, S, S); for (let i = 0; i < 90; i++) { const r = 10 + R() * 60, v = 70 + R() * 50; const gr = g.createRadialGradient(0, 0, 0, 0, 0, r); gr.addColorStop(0, `rgba(${v},${v},${v},0.3)`); gr.addColorStop(1, 'rgba(74,74,74,0)'); g.save(); g.translate(R() * S, R() * S); g.scale(1, 0.4 + R()); g.fillStyle = gr; g.fillRect(-r, -r, 2 * r, 2 * r); g.restore() } },
  }[kind]
  TEX[kind] = canvasTex(S, make, { color: kind === 'carbon' })
  return TEX[kind]
}

// ---------------------------------------------------------------- materials with section caps

const CUT = {
  a: { value: new THREE.Vector4(0, 0, -1, 1e5) }, // removed where dot(n,p)+w < 0 for both planes
  b: { value: new THREE.Vector4(0, 0, -1, 1e5) },
  proj: { value: new THREE.Matrix4() },
  hatch: { value: 0.012 },
}
const ALL_MATS = new Set()
/** section face style: 'red' (museum cutaway paint, the default) or 'metal' (the freshly machined material). Set before creating materials: setCaps('metal') */
const CAPS = { style: 'red', red: new THREE.Color(0.56, 0.085, 0.045) }
export function setCaps(style, color) { CAPS.style = style; if (color) CAPS.red = col(color) }

/**
 * Patch a standard or physical material so that, while a section cut is open, the back faces
 * seen through the opening are drawn as a flat machined cap on the cut plane: plane normal,
 * plane depth, the cap colour and a faint hatch. Every solid stays closed, no cap geometry.
 */
function capPatch(m, capColor, capRough = 0.38, capMetal = null) {
  m.userData.capColor = new THREE.Color(capColor)
  const uCap = { value: m.userData.capColor }
  const uCapR = { value: capRough }
  const uCapM = { value: capMetal ?? m.metalness }
  m.onBeforeCompile = (sh) => {
    sh.uniforms.uCutA = CUT.a; sh.uniforms.uCutB = CUT.b; sh.uniforms.uCutProj = CUT.proj; sh.uniforms.uHatch = CUT.hatch
    sh.uniforms.uCapColor = uCap; sh.uniforms.uCapRough = uCapR; sh.uniforms.uCapMetal = uCapM
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>', '#include <common>\nvarying vec3 vLabW;')
      .replace('#include <project_vertex>', `#include <project_vertex>
      { vec4 lw = vec4(transformed, 1.0);
        #ifdef USE_INSTANCING
        lw = instanceMatrix * lw;
        #endif
        vLabW = (modelMatrix * lw).xyz; }`)
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', `#include <common>
      varying vec3 vLabW;
      uniform vec4 uCutA; uniform vec4 uCutB; uniform mat4 uCutProj; uniform float uHatch;
      uniform vec3 uCapColor; uniform float uCapRough; uniform float uCapMetal;
      void labClip(vec4 P, vec3 ro, vec3 rd, inout float t0, inout float t1, inout int id, int k) {
        float dn = dot(P.xyz, rd), d0 = dot(P.xyz, ro) + P.w;
        if (abs(dn) < 1e-8) { if (d0 >= 0.0) { t0 = 1.0; t1 = 0.0; } return; }
        float th = -d0 / dn;
        if (dn > 0.0) { if (th < t1) { t1 = th; id = k; } } else t0 = max(t0, th);
      }`)
      .replace('#include <clipping_planes_fragment>', `#include <clipping_planes_fragment>
      // a back face of a closed solid is only ever seen through the opening the cut made: shade it as the
      // section face (plane normal, cap colour) at its own depth, so ordinary depth testing keeps it honest
      bool labCap = false; vec3 labHit = vLabW; vec3 labN = uCutA.xyz;
      if (!gl_FrontFacing && uCutA.w < 1e4) {
        labCap = true;
        vec3 ro = cameraPosition, toF = vLabW - ro; float tf = length(toF); vec3 rd = toF / max(tf, 1e-6);
        float t0 = 0.0, t1 = 1e9; int id = -1;
        labClip(uCutA, ro, rd, t0, t1, id, 0); labClip(uCutB, ro, rd, t0, t1, id, 1);
        if (id == 1) labN = uCutB.xyz;
        else if (id < 0) labN = abs(dot(uCutA.xyz, vLabW) + uCutA.w) < abs(dot(uCutB.xyz, vLabW) + uCutB.w) ? uCutA.xyz : uCutB.xyz;
        labHit = vLabW - labN * (dot(labN, vLabW) + (id == 1 ? uCutB.w : uCutA.w));
      }`)
      .replace('#include <color_fragment>', `#include <color_fragment>
      if (labCap) {
        float hs = dot(labHit, vec3(0.7071, 0.7071, 0.0)) / uHatch;
        float hl = smoothstep(0.0, 0.08, abs(fract(hs) - 0.5) - 0.42);
        diffuseColor.rgb = uCapColor * (0.94 + 0.06 * hl);
      }`)
      .replace('#include <roughnessmap_fragment>', '#include <roughnessmap_fragment>\nif (labCap) roughnessFactor = uCapRough;')
      .replace('#include <metalnessmap_fragment>', '#include <metalnessmap_fragment>\nif (labCap) metalnessFactor = uCapMetal;')
      .replace('#include <normal_fragment_maps>', `#include <normal_fragment_maps>
      if (labCap) { vec3 nw = normalize(-labN); normal = normalize((viewMatrix * vec4(nw, 0.0)).xyz); if (dot(normal, normalize(vViewPosition)) > 0.0) normal = -normal; }`)
    if (m.userData.extraShader) m.userData.extraShader(sh)
  }
  m.customProgramCacheKey = () => 'labcap' + (m.userData.extraKey || '')
  m.side = THREE.DoubleSide
  m.shadowSide = THREE.FrontSide
  m.clippingPlanes = LAB_PLANES
  m.clipIntersection = true
  m.clipShadows = true
  ALL_MATS.add(m)
  return m
}
const LAB_PLANES = [new THREE.Plane(new THREE.Vector3(0, 0, -1), 1e5), new THREE.Plane(new THREE.Vector3(0, 0, -1), 1e5)]

/**
 * Material library. Base colours are measured linear reflectances for metals (F0) and
 * albedos for dielectrics, so steel looks like steel next to titanium next to copper.
 * Every preset takes overrides: any MeshPhysicalMaterial field plus
 *   finish: 'turned' | 'brushed' | 'cast' | 'smudge' | 'knurl' | null   (micro roughness texture)
 *   rep: [u, v] texture repeat     cap: cap colour     noCap: true for open shells and glass
 */
export const MAT = {
  steel: (o) => mat({ color: [0.56, 0.57, 0.58], metalness: 1, roughness: 0.3, finish: 'turned', ...o }),
  steelDark: (o) => mat({ color: [0.24, 0.245, 0.25], metalness: 1, roughness: 0.42, finish: 'cast', ...o }),
  stainless: (o) => mat({ color: [0.67, 0.66, 0.64], metalness: 1, roughness: 0.2, finish: 'brushed', ...o }),
  chrome: (o) => mat({ color: [0.78, 0.79, 0.8], metalness: 1, roughness: 0.06, finish: null, ...o }),
  aluminium: (o) => mat({ color: [0.88, 0.89, 0.9], metalness: 1, roughness: 0.38, finish: 'cast', ...o }),
  aluminiumMachined: (o) => mat({ color: [0.9, 0.9, 0.91], metalness: 1, roughness: 0.22, finish: 'turned', ...o }),
  anodised: (o) => mat({ color: o?.color ?? [0.08, 0.09, 0.1], metalness: 0.85, roughness: 0.34, finish: 'cast', clearcoat: 0.2, ...o }),
  titanium: (o) => mat({ color: [0.54, 0.5, 0.45], metalness: 1, roughness: 0.32, finish: 'brushed', ...o }),
  inconel: (o) => mat({ color: [0.47, 0.44, 0.41], metalness: 1, roughness: 0.42, finish: 'cast', ...o }),
  copper: (o) => mat({ color: [0.95, 0.64, 0.54], metalness: 1, roughness: 0.28, finish: 'turned', ...o }),
  brass: (o) => mat({ color: [0.91, 0.78, 0.42], metalness: 1, roughness: 0.24, finish: 'turned', ...o }),
  gold: (o) => mat({ color: [1.0, 0.77, 0.34], metalness: 1, roughness: 0.18, finish: 'brushed', ...o }),
  bluedSteel: (o) => mat({ color: [0.08, 0.16, 0.5], metalness: 1, roughness: 0.16, finish: null, ...o }),
  castIron: (o) => mat({ color: [0.3, 0.3, 0.3], metalness: 0.9, roughness: 0.62, finish: 'cast', ...o }),
  paint: (o) => mat({ color: o?.color ?? [0.8, 0.8, 0.8], metalness: 0, roughness: 0.32, clearcoat: 0.6, clearcoatRoughness: 0.2, finish: 'smudge', ...o }),
  satin: (o) => mat({ color: o?.color ?? [0.04, 0.04, 0.045], metalness: 0, roughness: 0.55, finish: 'cast', ...o }),
  plastic: (o) => mat({ color: o?.color ?? [0.05, 0.05, 0.055], metalness: 0, roughness: 0.42, finish: 'cast', ...o }),
  rubber: (o) => mat({ color: [0.025, 0.025, 0.027], metalness: 0, roughness: 0.82, finish: 'cast', ...o }),
  ceramic: (o) => mat({ color: [0.82, 0.8, 0.76], metalness: 0, roughness: 0.5, finish: 'cast', ...o }),
  carbon: (o) => mat({ color: [1, 1, 1], map: tex('carbon'), metalness: 0.2, roughness: 0.36, clearcoat: 1, clearcoatRoughness: 0.05, finish: null, rep: [6, 6], ...o }),
  glass: (o) => mat({ color: [1, 1, 1], metalness: 0, roughness: 0.03, transmission: 1, thickness: 0.004, ior: 1.5, transparent: true, finish: null, noCap: true, ...o }),
  sapphire: (o) => mat({ color: [0.96, 0.97, 1], metalness: 0, roughness: 0.0, transmission: 1, thickness: 0.002, ior: 1.77, transparent: true, finish: null, noCap: true, ...o }),
  ruby: (o) => mat({ color: [0.9, 0.08, 0.15], metalness: 0, roughness: 0.05, transmission: 0.6, thickness: 0.001, ior: 1.77, finish: null, ...o }),
  enamel: (o) => mat({ color: [0.93, 0.92, 0.88], metalness: 0, roughness: 0.12, clearcoat: 1, clearcoatRoughness: 0.03, finish: null, ...o }),
  fluid: (o) => mat({ color: o?.color ?? [0.3, 0.12, 0.05], metalness: 0, roughness: 0.08, clearcoat: 1, finish: null, ...o }),
  glow: (o) => mat({ color: [0, 0, 0], emissive: o?.emissive ?? [1, 0.5, 0.15], emissiveIntensity: o?.emissiveIntensity ?? 4, metalness: 0, roughness: 1, finish: null, ...o }),
}

function col(c) { return Array.isArray(c) ? new THREE.Color(c[0], c[1], c[2]) : new THREE.Color(c) }

/** build a material from a preset description (see MAT) */
export function mat(o) {
  const { finish, rep, cap, noCap, capRough, color, emissive, ...rest } = o
  const m = new THREE.MeshPhysicalMaterial({ ...rest })
  m.color = col(color ?? [0.8, 0.8, 0.8])
  if (emissive !== undefined) m.emissive = col(emissive)
  if (finish) {
    const t = tex(finish).clone(); t.needsUpdate = true
    t.repeat.set(...(rep ?? (finish === 'turned' ? [1, 24] : finish === 'brushed' ? [2, 6] : [3, 3])))
    m.roughnessMap = t
    if (finish === 'knurl') { m.bumpMap = t; m.bumpScale = 0.6 }
  }
  m.envMapIntensity = rest.envMapIntensity ?? 1
  if (noCap) {
    m.side = THREE.FrontSide
    m.clippingPlanes = LAB_PLANES; m.clipIntersection = true; m.clipShadows = true
    ALL_MATS.add(m)
    return m
  }
  // cap colour: freshly machined face of the same material, a touch brighter and smoother
  const metalCap = m.metalness > 0.5 ? m.color.clone().lerp(new THREE.Color(0.8, 0.8, 0.8), 0.35) : m.color.clone().multiplyScalar(0.9)
  const capC = cap !== undefined ? col(cap) : CAPS.style === 'metal' ? metalCap : CAPS.red.clone()
  return capPatch(m, capC, capRough ?? (CAPS.style === 'metal' ? 0.36 : 0.55), CAPS.style === 'metal' && m.metalness > 0.5 ? 1 : 0)
}

/**
 * Heat tint: emissive glow from a temperature attribute or a uniform, blackbody coloured.
 * Use for nozzles, turbine blades, brake discs: m.userData.heat.value = kelvin
 */
export function heatGlow(m, T0 = 900) {
  const uT = { value: T0 }
  m.userData.heat = uT
  m.userData.extraKey = 'heat'
  m.userData.extraShader = (sh) => {
    sh.uniforms.uHeatT = uT
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', '#include <common>\nuniform float uHeatT;')
      .replace('#include <emissivemap_fragment>', `#include <emissivemap_fragment>
      { float T = uHeatT; float k = smoothstep(750.0, 1600.0, T);
        float t = clamp(T, 800.0, 6000.0) / 100.0;
        vec3 bb = vec3(1.0, clamp((99.47 * log(t) - 161.12) / 255.0, 0.0, 1.0), t <= 19.0 ? 0.0 : clamp((138.52 * log(t - 10.0) - 305.04) / 255.0, 0.0, 1.0));
        bb = pow(bb, vec3(2.2));
        if (!labCap) totalEmissiveRadiance += bb * k * k * 6.0; }`)
  }
  m.needsUpdate = true
  return m
}

// ---------------------------------------------------------------- geometry

export const GEO = {
  /**
   * closed solid of revolution around +Y from [r, y] points (a closed profile; the last point joins the first).
   * Any winding works (it is made counter clockwise so faces point out), and corners sharper than
   * `crease` degrees stay crisp while gentle curves shade smooth.
   */
  lathe(pts, seg = 96, { crease = 32, phi0 = 0, phiLen = Math.PI * 2 } = {}) {
    let p = pts.map(([r, y]) => new THREE.Vector2(Math.max(0, r), y))
    if (p[0].distanceTo(p[p.length - 1]) < 1e-9) p.pop()
    let area = 0; for (let i = 0; i < p.length; i++) { const a = p[i], b = p[(i + 1) % p.length]; area += a.x * b.y - b.x * a.y }
    if (area < 0) p.reverse()
    // start at a crease (the open start and end of the profile then shade separately, as they should),
    // and duplicate every other crease point so each side gets its own normal (zero length segments add no area)
    const cosT = Math.cos(THREE.MathUtils.degToRad(crease)), n0 = p.length
    const isCrease = (i) => { const a = p[(i - 1 + n0) % n0], b = p[i], c = p[(i + 1) % n0]; return b.clone().sub(a).normalize().dot(c.clone().sub(b).normalize()) < cosT }
    let s0 = 0; for (let i = 0; i < n0; i++) if (isCrease(i)) { s0 = i; break }
    p = [...p.slice(s0), ...p.slice(0, s0)]
    const out = [p[0].clone()]
    for (let i = 1; i < n0; i++) { out.push(p[i].clone()); if (isCrease(i)) out.push(p[i].clone()) }
    out.push(p[0].clone())
    const g = new THREE.LatheGeometry(out, seg, phi0, phiLen)
    g.computeVertexNormals()
    if (phiLen >= Math.PI * 2 - 1e-6) {
      // weld the seam normals
      const n = g.attributes.normal, P = out.length
      for (let j = 0; j < P; j++) { const a = j, b = seg * P + j; const v = new THREE.Vector3(n.getX(a) + n.getX(b), n.getY(a) + n.getY(b), n.getZ(a) + n.getZ(b)).normalize(); n.setXYZ(a, v.x, v.y, v.z); n.setXYZ(b, v.x, v.y, v.z) }
    }
    return g
  },
  /**
   * a wall of thickness t following an open profile [[r, y], ...] (a nozzle, a casing, a cowl):
   * the outer line, then the same line offset inward, closed at both ends. Real solids cut cleanly.
   */
  shell(pts, t, seg = 96, inward = true) {
    const out = pts.map((p) => new THREE.Vector2(p[0], p[1]))
    const inn = out.map((p, i) => {
      const a = out[Math.max(0, i - 1)], b = out[Math.min(out.length - 1, i + 1)]
      const tx = b.x - a.x, ty = b.y - a.y, l = Math.hypot(tx, ty) || 1
      const nx = ty / l, ny = -tx / l // outward normal for a profile running in +y
      const s = inward ? -1 : 1
      return new THREE.Vector2(Math.max(0, p.x + s * nx * t), p.y + s * ny * t)
    })
    return GEO.lathe([...out.map((v) => [v.x, v.y]), ...inn.reverse().map((v) => [v.x, v.y])], seg)
  },
  /** hollow cylinder along +Y */
  tube(rOut, rIn, h, seg = 96, y0 = -h / 2) {
    return GEO.lathe([[rIn, y0], [rOut, y0], [rOut, y0 + h], [rIn, y0 + h]], seg)
  },
  /** cylinder with chamfered edges along +Y */
  disc(r, h, ch = Math.min(r, h) * 0.08, seg = 96, rIn = 0) {
    return GEO.lathe([[rIn, -h / 2], [r - ch, -h / 2], [r, -h / 2 + ch], [r, h / 2 - ch], [r - ch, h / 2], [rIn, h / 2]], seg)
  },
  rbox(w, h, d, r = Math.min(w, h, d) * 0.08, s = 4) { return new RoundedBoxGeometry(w, h, d, s, r) },
  /** spur or helical gear around +Z, with an involute-like tooth (enough for a convincing mesh), centred on z */
  gear({ teeth = 24, module = 0.002, width = 0.008, bore = 0, helix = 0, rim = 0, spokes = 0 } = {}) {
    const rp = (teeth * module) / 2, ra = rp + module, rf = rp - 1.25 * module
    const da = (Math.PI * 2) / teeth, steps = 6
    // half tooth width (as a fraction of the angular pitch) from root to tip: convex, involute-like flank
    const hw = (r) => da * lerp(0.31, 0.13, Math.pow(clamp((r - rf) / (ra - rf)), 0.85))
    const pts = []
    for (let i = 0; i < teeth; i++) {
      const c = (i + 0.5) * da
      pts.push([rf, i * da])
      for (let k = 0; k <= steps; k++) { const r = lerp(rf, ra, k / steps); pts.push([r, c - hw(r)]) }
      for (let k = 1; k < 3; k++) pts.push([ra, c - hw(ra) + (2 * hw(ra) * k) / 3])
      for (let k = steps; k >= 0; k--) { const r = lerp(rf, ra, k / steps); pts.push([r, c + hw(r)]) }
    }
    const sh = new THREE.Shape()
    pts.forEach(([r, a], k) => { const x = r * Math.cos(a), y = r * Math.sin(a); k ? sh.lineTo(x, y) : sh.moveTo(x, y) })
    sh.closePath()
    if (bore > 0) { const h = new THREE.Path(); h.absarc(0, 0, bore, 0, Math.PI * 2, true); sh.holes.push(h) }
    if (spokes > 0 && rim > 0) {
      const ri = rf - rim, rh = Math.max(bore * 1.9, rp * 0.28)
      for (let s = 0; s < spokes; s++) {
        const w = 0.22 * (rp / Math.max(ri, 1e-6))
        const a0 = (s / spokes) * Math.PI * 2 + w, a1 = ((s + 1) / spokes) * Math.PI * 2 - w
        const h = new THREE.Path(); h.absarc(0, 0, ri, a0, a1, false); h.absarc(0, 0, rh, a1 - w * 0.4, a0 + w * 0.4, true); h.closePath(); sh.holes.push(h)
      }
    }
    const g = new THREE.ExtrudeGeometry(sh, { depth: width, bevelEnabled: true, bevelThickness: module * 0.15, bevelSize: module * 0.12, bevelSegments: 2, curveSegments: 24, steps: helix ? 6 : 1 })
    g.translate(0, 0, -width / 2)
    if (helix) {
      const p = g.attributes.position
      for (let i = 0; i < p.count; i++) { const z = p.getZ(i), a = (z / width) * helix, x = p.getX(i), y = p.getY(i); p.setXY(i, x * Math.cos(a) - y * Math.sin(a), x * Math.sin(a) + y * Math.cos(a)) }
      g.computeVertexNormals()
    }
    g.userData.pitchRadius = rp
    return g
  },
  /**
   * one blade as a closed cambered, twisted airfoil solid, spanning radius r0..r1 along +Y,
   * chord along the axis (Z) by default. twist in rad root to tip, chord can be [root, tip].
   */
  blade({ r0 = 0.1, r1 = 0.5, chord = 0.08, thick = 0.08, camber = 0.06, twist = 0.6, pitch = 0.4, sweep = 0, nS = 14, nC = 16, lean = 0 } = {}) {
    const c0 = Array.isArray(chord) ? chord[0] : chord, c1 = Array.isArray(chord) ? chord[1] : chord
    const pos = [], idx = []
    const ring = nC * 2
    for (let s = 0; s <= nS; s++) {
      const u = s / nS, r = lerp(r0, r1, u), c = lerp(c0, c1, u), ang = pitch + twist * (u - 0.5) * -1
      const tk = Array.isArray(thick) ? lerp(thick[0], thick[1], u) : thick, cb = Array.isArray(camber) ? lerp(camber[0], camber[1], u) : camber
      for (let k = 0; k < ring; k++) {
        const top = k < nC, j = top ? k : ring - 1 - k, x = j / (nC - 1) // 0 leading .. 1 trailing
        const th = 5 * tk * (0.2969 * Math.sqrt(x) - 0.126 * x - 0.3516 * x * x + 0.2843 * x ** 3 - 0.1036 * x ** 4)
        const yc = 4 * cb * x * (1 - x)
        const yy = (yc + (top ? th : -th)) * c, xx = (x - 0.35) * c
        // rotate the section by the blade angle in the chord plane (z = axial, x = tangential)
        const z = xx * Math.cos(ang) - yy * Math.sin(ang) + sweep * u * u
        const tx = xx * Math.sin(ang) + yy * Math.cos(ang) + lean * u * u
        pos.push(tx, r, z)
      }
    }
    for (let s = 0; s < nS; s++) for (let k = 0; k < ring; k++) {
      const a = s * ring + k, b = s * ring + ((k + 1) % ring), c = a + ring, d = b + ring
      idx.push(a, c, b, b, c, d)
    }
    // end caps
    const cap = (s, flip) => { const base = s * ring, cIdx = pos.length / 3; let cx = 0, cy = 0, cz = 0; for (let k = 0; k < ring; k++) { cx += pos[(base + k) * 3]; cy += pos[(base + k) * 3 + 1]; cz += pos[(base + k) * 3 + 2] } pos.push(cx / ring, cy / ring, cz / ring); for (let k = 0; k < ring; k++) { const a = base + k, b = base + ((k + 1) % ring); flip ? idx.push(cIdx, b, a) : idx.push(cIdx, a, b) } }
    cap(0, false); cap(nS, true)
    const g = new THREE.BufferGeometry()
    g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setIndex(idx)
    g.computeVertexNormals()
    // uv: span along v, chord along u
    const uv = []; for (let i = 0; i < pos.length / 3; i++) uv.push((i % ring) / ring, Math.floor(i / ring) / nS)
    g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2))
    return g
  },
  /**
   * a bladed row: n blades around an axis. axis 'z' = blades radial in XY, chord along Z.
   * axis 'y' = blades radial in XZ, chord along Y (an engine built along Y). Same options as blade().
   */
  rotor({ count = 24, axis = 'y', phase = 0, ...b } = {}) {
    const one = GEO.blade(b)
    if (axis === 'y') one.applyMatrix4(new THREE.Matrix4().set(0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 1))
    if (axis === 'x') one.applyMatrix4(new THREE.Matrix4().set(0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1))
    return count === 1 ? one : GEO.ring(one, count, axis, phase)
  },
  /** volume (m3) and centroid of a closed mesh: for real masses (m = rho V) and inertias */
  volume(geo) {
    const p = geo.attributes.position, idx = geo.index ? geo.index.array : null, n = idx ? idx.length : p.count
    let V = 0; const c = new THREE.Vector3(), a = new THREE.Vector3(), b = new THREE.Vector3(), d = new THREE.Vector3()
    for (let i = 0; i < n; i += 3) {
      const i0 = idx ? idx[i] : i, i1 = idx ? idx[i + 1] : i + 1, i2 = idx ? idx[i + 2] : i + 2
      a.fromBufferAttribute(p, i0); b.fromBufferAttribute(p, i1); d.fromBufferAttribute(p, i2)
      const v = a.dot(b.clone().cross(d)) / 6; V += v
      c.addScaledVector(a.clone().add(b).add(d), v / 4)
    }
    return { V: Math.abs(V), centroid: c.divideScalar(V || 1) }
  },
  /** n copies of a geometry rotated around an axis ('y' or 'z'), merged */
  ring(geo, n, axis = 'z', phase = 0) {
    const out = []
    for (let i = 0; i < n; i++) { const g = geo.clone(); const m = new THREE.Matrix4(); const a = phase + (i / n) * Math.PI * 2; axis === 'y' ? m.makeRotationY(a) : axis === 'x' ? m.makeRotationX(a) : m.makeRotationZ(a); g.applyMatrix4(m); out.push(g) }
    return BGU.mergeGeometries(out)
  },
  merge(list) { return BGU.mergeGeometries(list.map((g) => g.index ? g.toNonIndexed() : g)) },
  /** a pipe through points (closed solid wall, ends capped) */
  pipe(points, r, { seg = 64, radial = 16, tension = 0.5 } = {}) {
    const curve = new THREE.CatmullRomCurve3(points.map((p) => new THREE.Vector3(...p)), false, 'catmullrom', tension)
    const g = new THREE.TubeGeometry(curve, seg, r, radial, false)
    // cap both ends so the pipe is a closed solid
    const caps = []
    for (const [t, s] of [[0, -1], [1, 1]]) {
      const c = new THREE.CircleGeometry(r, radial)
      const tan = curve.getTangentAt(t).multiplyScalar(s)
      c.applyQuaternion(new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 0, 1), tan))
      c.translate(...curve.getPointAt(t).toArray())
      caps.push(c)
    }
    const m = GEO.merge([g, ...caps]); m.userData.curve = curve
    return m
  },
  /** hex bolt heads (or socket caps) on a circle around +Y at height y, merged */
  bolts(n, R, size, h, { y = 0, socket = false, phase = 0 } = {}) {
    const one = socket ? GEO.lathe([[0, 0], [size, 0], [size, h * 0.9], [size * 0.92, h], [size * 0.45, h], [size * 0.45, h * 0.55], [0, h * 0.55]], 24) : new THREE.CylinderGeometry(size, size, h, 6).translate(0, h / 2, 0)
    const out = []
    for (let i = 0; i < n; i++) { const a = phase + (i / n) * Math.PI * 2; out.push(one.clone().translate(R * Math.cos(a), y, R * Math.sin(a))) }
    return GEO.merge(out)
  },
  /** coil spring along +Y */
  spring(R, wire, turns, len, seg = 400) {
    const pts = []
    for (let i = 0; i <= seg; i++) { const t = i / seg, a = t * turns * Math.PI * 2; pts.push(new THREE.Vector3(R * Math.cos(a), t * len, R * Math.sin(a))) }
    return new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), seg, wire, 10, false)
  },
  /** extruded 2D outline (THREE.Shape) along +Z, with a small bevel */
  extrude(shape, depth, bevel = depth * 0.06) {
    const g = new THREE.ExtrudeGeometry(shape, { depth, bevelEnabled: bevel > 0, bevelThickness: bevel, bevelSize: bevel, bevelSegments: 2, curveSegments: 32 })
    g.translate(0, 0, -depth / 2); g.computeVertexNormals(); return g
  },
}

// ---------------------------------------------------------------- studio

/** Khronos PBR Neutral tone mapping (what three's NeutralToneMapping does), and its inverse per channel */
function neutral(c) {
  const s0 = 0.8 - 0.04, d = 0.15
  const x = Math.min(c[0], c[1], c[2]), off = x < 0.08 ? x - 6.25 * x * x : 0.04
  let r = c.map((v) => v - off)
  const peak = Math.max(...r)
  if (peak < s0) return r
  const d1 = 1 - s0, np = 1 - (d1 * d1) / (peak + d1 - s0)
  r = r.map((v) => v * (np / peak))
  const g = 1 - 1 / (d * (peak - np) + 1)
  return r.map((v) => v * (1 - g) + np * g)
}
function untonemap(target, exposure = 1) {
  // find the linear colour that comes out of the tone mapper as the target (so canvas paper == CSS paper)
  let x = [target.r, target.g, target.b]
  for (let it = 0; it < 60; it++) { const y = neutral(x.map((v) => v * exposure)); x = x.map((v, i) => Math.max(0, v + (target.toArray()[i] - y[i]) * 0.9)) }
  return new THREE.Color(x[0], x[1], x[2])
}

function studioEnvironment(renderer, theme) {
  // a softbox studio: big top light, a key strip, two rim strips, and black flags so metals keep contrast
  const paper = theme === 'paper'
  const s = new THREE.Scene()
  const room = new THREE.Mesh(new THREE.SphereGeometry(30, 32, 16), new THREE.MeshBasicMaterial({ color: paper ? 0x9c9a95 : 0x0a0b0d, side: THREE.BackSide }))
  s.add(room)
  const floor = new THREE.Mesh(new THREE.CircleGeometry(30, 32), new THREE.MeshBasicMaterial({ color: paper ? 0xd8d6d0 : 0x141517 }))
  floor.rotation.x = -Math.PI / 2; floor.position.y = -2; s.add(floor)
  const box = (w, h, x, y, z, k, tint = [1, 1, 1]) => {
    const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ color: new THREE.Color(...tint).multiplyScalar(k), side: THREE.DoubleSide }))
    m.position.set(x, y, z); m.lookAt(0, 0, 0); s.add(m)
  }
  box(14, 10, 0, 14, 2, paper ? 2.6 : 3.2)                  // overhead soft box
  box(4, 14, -12, 4, 8, paper ? 4.5 : 6, [1, 0.96, 0.9])    // warm key strip, front left
  box(2.2, 14, 13, 5, -6, paper ? 6 : 9, [0.88, 0.94, 1])   // cool rim, back right
  box(2.2, 14, -11, 5, -9, paper ? 3.5 : 5)                 // second rim, back left
  box(8, 3, 6, 1.5, 12, paper ? 1.4 : 1.6)                  // low front fill
  // black flags: long dark reflections give metal its shape on a white set
  box(5, 16, 12, 4, 7, 0.02); box(4, 16, -13, 4, -2, 0.02); box(16, 3, 0, -1, -14, 0.03)
  const pm = new THREE.PMREMGenerator(renderer)
  const rt = pm.fromScene(s, 0.02)
  pm.dispose()
  return rt.texture
}

const CSS = `
:root { --paper:#f3f2ee; --ink:#141414; --mute:#8c8b87; --faint:#c9c7c1; --line:#e4e2dc; --accent:#e4572e; --panel:rgba(255,255,255,0.0);
  --serif:'Instrument Serif','EB Garamond',Georgia,serif; --sans:'Inter',system-ui,-apple-system,sans-serif; --mono:'JetBrains Mono',ui-monospace,Menlo,monospace }
.lab-night { --paper:#0d0e10; --ink:#f1efe9; --mute:#8e8c86; --faint:#4a4945; --line:#2a2a2a }
html,body { margin:0; height:100%; background:var(--paper); color:var(--ink); font-family:var(--sans); overflow:hidden; -webkit-font-smoothing:antialiased }
#lab-gl { position:fixed; inset:0; width:100%; height:100%; display:block; outline:none; touch-action:none }
.lab-ui { position:fixed; inset:0; pointer-events:none; z-index:2 }
.lab-ui * { box-sizing:border-box }
.lab-ui .on { pointer-events:auto }
.lab-prompt { position:absolute; left:4.2vw; top:4.2vh; max-width:58vw; padding:0.85em 1.2em; background:rgba(0,0,0,0.035); border-radius:3px; font-size:clamp(12px,1.02vw,19px); color:#55534f; line-height:1.35; letter-spacing:-0.005em }
.lab-night .lab-prompt { background:rgba(255,255,255,0.05); color:#aaa79f }
.lab-prompt b { color:var(--ink); font-weight:600 }
.lab-prompt .caret { display:inline-block; width:0.08em; height:1.05em; background:var(--ink); vertical-align:-0.18em; margin-left:1px; animation:labblink 1s steps(1) infinite }
@keyframes labblink { 50% { opacity:0 } }
.lab-pills { position:absolute; right:4.2vw; top:5.4vh; display:flex; gap:1.4em; font-size:clamp(11px,0.95vw,18px); color:var(--ink) }
.lab-pills span::before { content:''; display:inline-block; width:0.5em; height:0.5em; border-radius:50%; background:var(--ink); margin-right:0.45em; vertical-align:0.08em }
.lab-pills span.off { color:var(--faint) } .lab-pills span.off::before { background:none; box-shadow:inset 0 0 0 1px var(--faint) }
.lab-side { position:absolute; right:4.2vw; top:50%; transform:translateY(-50%); width:clamp(250px,22.5vw,440px) }
.lab-no { font-size:clamp(11px,0.95vw,18px); color:var(--mute); margin-bottom:0.3em }
.lab-title { font-family:var(--serif); font-size:clamp(34px,3.9vw,76px); line-height:0.98; letter-spacing:-0.01em; font-weight:400 }
.lab-title i { display:block; color:#6d6b66; font-style:italic }
.lab-night .lab-title i { color:#a4a199 }
.lab-metric { margin-top:clamp(18px,3.6vh,44px) }
.lab-metric .lbl { font-size:clamp(12px,1.02vw,19px); color:var(--mute) } .lab-metric .lbl b { color:var(--ink); font-weight:500 }
.lab-big { font-family:var(--serif); font-size:clamp(64px,7.4vw,142px); line-height:1.02; letter-spacing:-0.02em; font-variant-numeric:lining-nums tabular-nums; white-space:nowrap }
.lab-big i { font-size:0.4em; color:#7a7873; margin-left:0.12em; letter-spacing:0 }
.lab-bar { position:relative; height:clamp(4px,0.42vh,7px); background:var(--line); margin:0.2em 0 0.9em }
.lab-bar > div { position:absolute; left:0; top:0; bottom:0; background:var(--ink); transition:none }
.lab-bar.bad > div { background:var(--accent) }
.lab-sub { font-size:clamp(12px,1.02vw,19px); color:#4d4b47; font-variant-numeric:tabular-nums; line-height:1.5 }
.lab-night .lab-sub { color:#bdbab2 }
.lab-sub .bad { color:var(--accent) }
.lab-ctl { margin-top:clamp(16px,3.2vh,40px) }
.lab-ctl .row { display:flex; justify-content:space-between; font-size:clamp(12px,1.02vw,19px); color:var(--mute); margin-bottom:0.55em } .lab-ctl .row b { color:var(--ink); font-weight:600; font-variant-numeric:tabular-nums }
.lab-ctl input[type=range] { -webkit-appearance:none; appearance:none; width:100%; height:2.6em; background:transparent; margin:0; cursor:pointer }
.lab-ctl input[type=range]::-webkit-slider-runnable-track { height:0.62em; background:linear-gradient(to right,var(--ink) 0 var(--p,0%),var(--line) var(--p,0%) 100%); border-radius:0.31em }
.lab-ctl input[type=range]::-webkit-slider-thumb { -webkit-appearance:none; width:2.3em; height:2.3em; border-radius:50%; background:#fff; margin-top:-0.84em; box-shadow:0 1px 2px rgba(0,0,0,0.18),0 4px 14px rgba(0,0,0,0.12),inset 0 0 0 1px rgba(0,0,0,0.06) }
.lab-ctl input[type=range]::-moz-range-track { height:0.62em; background:var(--line); border-radius:0.31em } .lab-ctl input[type=range]::-moz-range-progress { height:0.62em; background:var(--ink); border-radius:0.31em }
.lab-ctl input[type=range]::-moz-range-thumb { width:2.3em; height:2.3em; border-radius:50%; background:#fff; border:none; box-shadow:0 1px 2px rgba(0,0,0,0.18),0 4px 14px rgba(0,0,0,0.12) }
.lab-ctl .ends { display:flex; justify-content:space-between; font-size:clamp(11px,0.9vw,17px); color:var(--faint); margin-top:0.1em }
.lab-modes { position:absolute; left:4.2vw; bottom:4.2vh; display:flex; gap:0.5em; flex-wrap:wrap; font-size:clamp(11px,0.88vw,16px) }
.lab-modes button { font:inherit; color:var(--ink); background:transparent; border:1px solid var(--line); border-radius:999px; padding:0.5em 1.05em; cursor:pointer; transition:background .2s, color .2s, border-color .2s }
.lab-modes button:hover { border-color:var(--faint) }
.lab-modes button.act { background:var(--ink); color:var(--paper); border-color:var(--ink) }
.lab-modes button.brk { color:var(--accent); border-color:rgba(228,87,46,0.35) } .lab-modes button.brk.act { background:var(--accent); color:#fff; border-color:var(--accent) }
.lab-modes kbd { font:inherit; color:var(--faint); margin-left:0.45em; font-size:0.85em }
.lab-modes button.act kbd { color:rgba(255,255,255,0.45) }
.lab-how { position:absolute; right:4.2vw; bottom:4.2vh; width:clamp(250px,22.5vw,440px); font-size:clamp(11px,0.82vw,15px); color:var(--mute); line-height:1.5 }
.lab-how summary { cursor:pointer; color:var(--ink); list-style:none; font-weight:500 } .lab-how summary::-webkit-details-marker { display:none } .lab-how summary::after { content:' +'; color:var(--faint) }
.lab-how[open] summary::after { content:' \\2212' }
.lab-how .eq { font-family:var(--mono); font-size:0.92em; color:#4d4b47; margin:0.5em 0; white-space:pre-wrap }
.lab-night .lab-how .eq { color:#bdbab2 }
.lab-scale { position:absolute; left:4.2vw; bottom:calc(4.2vh + 3.4em); font-size:clamp(10px,0.8vw,14px); color:var(--mute); font-variant-numeric:tabular-nums }
.lab-scale div { height:1px; background:var(--mute); margin-top:0.35em; position:relative } .lab-scale div::before,.lab-scale div::after { content:''; position:absolute; top:-3px; width:1px; height:7px; background:var(--mute) } .lab-scale div::after { right:0 }
.lab-labels { position:absolute; inset:0 } .lab-labels svg { position:absolute; inset:0; width:100%; height:100% }
.lab-lab { position:absolute; font-size:clamp(11px,0.86vw,16px); color:var(--ink); white-space:nowrap; transform:translate(0,-50%); transition:opacity .35s; line-height:1.25; text-shadow:0 0 3px var(--paper), 0 0 8px var(--paper), 0 0 14px var(--paper) }
.lab-lab small { display:block; color:var(--mute); font-size:0.86em; font-variant-numeric:tabular-nums }
.lab-lab.left { transform:translate(-100%,-50%); text-align:right }
.lab-beat { position:absolute; left:4.2vw; bottom:4.6vh; display:flex; align-items:center; gap:0.85em; font-size:clamp(16px,1.9vw,36px); letter-spacing:-0.01em; opacity:0; transition:none }
.lab-beat .n { font-size:0.5em; border:1px solid var(--faint); color:var(--mute); padding:0.42em 0.62em; line-height:1; font-variant-numeric:tabular-nums }
.lab-beat b { font-weight:500 } .lab-beat span { color:var(--mute) }
.lab-cursor { position:absolute; left:0; top:0; width:clamp(18px,1.45vw,28px); opacity:0; filter:drop-shadow(0 2px 3px rgba(0,0,0,0.25)); transform-origin:2px 2px }
.lab-flash { position:absolute; inset:0; background:var(--accent); opacity:0; mix-blend-mode:multiply }
.lab-brand { position:absolute; right:4.2vw; bottom:4.2vh; font-size:clamp(10px,0.78vw,14px); color:var(--faint) }
.lab-film .lab-how, .lab-film .lab-scale { display:none }
.lab-film .lab-modes button:not([data-k=break]) { display:none }
.lab-film:not(.lab-embed) .lab-modes { left:auto; right:4.2vw }
.lab-embed .lab-beat { display:none }
.lab-hidden { opacity:0 !important }
@media (max-width: 760px) {
  .lab-side { top:auto; bottom:12vh; transform:none; right:16px; left:16px; width:auto }
  .lab-prompt { left:16px; right:16px; max-width:none; top:16px }
  .lab-pills, .lab-how, .lab-scale { display:none }
  .lab-modes { left:16px; right:16px; bottom:16px }
  .lab-big { font-size:56px }
}
`

const CURSOR_SVG = `<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M3 2 L3 19.5 L7.6 15.4 L10.6 22 L13.6 20.7 L10.7 14.3 L16.8 14.1 Z" fill="#111" stroke="#fff" stroke-width="1.3" stroke-linejoin="round"/></svg>`

// ---------------------------------------------------------------- the Lab

/**
 * new Lab({
 *   prompt: 'a turbofan jet engine',        // the one line the user typed (shown in the prompt bar)
 *   no: 1, title: 'Turbofan', sub: 'ground run',
 *   size: 3.4,                              // characteristic length of the real machine in metres
 *   theme: 'paper' | 'night',
 *   view: { az: 35, el: 14, dist: 2.2, target: [0, 0, 0], fov: 30 },   // dist in multiples of size
 *   frame: 'left' | 'center',               // where the subject sits (left leaves room for the side column)
 *   ground: 0,                              // y (metres, machine frame) of the floor
 *   pills: ['three.js', 'Physics', 'Film'],
 * })
 */
export class Lab {
  constructor(o = {}) {
    this.o = o
    this.size = o.size ?? 1
    this.theme = o.theme ?? 'paper'
    this.q = new URLSearchParams(location.search)
    this.filmMode = this.q.has('film')
    this.embed = this.q.has('embed')
    this.time = 0
    this.timeScale = 1
    this.parts = []
    this.labels = []
    this.tickers = []
    this.ghosts = []
    this.state = { explode: 0, cut: 0, xray: 0, slow: 0, labels: 0, broken: 0 }
    this.target = { explode: 0, cut: 0, xray: 0, slow: 0, labels: 0 }
    this.broken = false
    this.brokenAt = -1
    this.metrics = {}
    this.controls = {}
    this.loading = 0
    // display scale: the machine is shown about 2.4 units across, whatever its real size
    this.k = 2.4 / this.size
    this._initDOM()
    this._initGL()
    this._initStudio()
    this.sparks = new Sparks(this)
    this.debris = []
    window.__lab = this
  }

  // ---------- DOM
  _initDOM() {
    const st = document.createElement('style'); st.textContent = CSS; document.head.appendChild(st)
    if (this.theme === 'night') document.documentElement.classList.add('lab-night')
    if (this.filmMode) document.documentElement.classList.add('lab-film')
    if (this.q.has('embed')) document.documentElement.classList.add('lab-embed')
    const o = this.o
    const ui = document.createElement('div'); ui.className = 'lab-ui'
    ui.innerHTML = `
      <div class="lab-labels"><svg></svg></div>
      <div class="lab-prompt"><b>/machine</b> <span class="txt"></span><span class="caret" style="display:none"></span></div>
      <div class="lab-pills">${(o.pills ?? ['three.js', 'Physics', 'Film']).map((p) => `<span>${p}</span>`).join('')}</div>
      <div class="lab-side">
        <div class="lab-no">No. ${String(o.no ?? 1).padStart(2, '0')}</div>
        <div class="lab-title">${o.title ?? 'Machine'}<i>${o.sub ?? ''}</i></div>
        <div class="lab-metric"></div>
        <div class="lab-ctls"></div>
      </div>
      <div class="lab-scale"><span></span><div></div></div>
      <div class="lab-modes on"></div>
      <details class="lab-how on"><summary>How it is computed</summary><div class="body"></div></details>
      <div class="lab-beat"><span class="n"></span><div><b></b> <span></span></div></div>
      <div class="lab-flash"></div>
      <div class="lab-cursor">${CURSOR_SVG}</div>`
    document.body.appendChild(ui)
    this.ui = ui
    this.$ = (s) => ui.querySelector(s)
    this.$('.lab-prompt .txt').textContent = o.prompt ?? ''
    if (this.embed && !this.filmMode) for (const s of ['.lab-modes', '.lab-how', '.lab-scale']) this.$(s).style.display = 'none'
    if (o.frame === 'center') this.$('.lab-side').style.display = 'none'
    // the primary metric block
    this.metricEl = this.$('.lab-metric')
  }

  /**
   * The hero number: lab.hero({ label: 'Thrust', unit: 'kN', max: 350, digits: 0 })
   * then lab.setHero(value, { state: 'spooling up', sub: 'N1 94.9 % · TGT 959 °C', bad: false })
   */
  hero(o) {
    this.heroO = { digits: 0, ...o }
    this.metricEl.innerHTML = `<div class="lbl">${o.label} · <b class="st"></b></div><div class="lab-big"><span class="v">0</span><i>${o.unit ?? ''}</i></div><div class="lab-bar"><div></div></div><div class="lab-sub"></div>`
    this._hv = this.metricEl.querySelector('.v'); this._hs = this.metricEl.querySelector('.st'); this._hb = this.metricEl.querySelector('.lab-bar'); this._hsub = this.metricEl.querySelector('.lab-sub')
  }
  setHero(v, { state, sub, bad = false } = {}) {
    const h = this.heroO; if (!h) return
    if (this._building) { this._heroPending = [v, { state, sub, bad }]; return }
    this.heroValue = v
    this._hv.textContent = fmt(v, h.digits)
    if (state !== undefined) this._hs.textContent = state
    if (sub !== undefined) this._hsub.innerHTML = sub
    this._hb.firstElementChild.style.width = `${clamp(v / h.max) * 100}%`
    this._hb.classList.toggle('bad', bad)
  }

  /** lab.slider({ id:'throttle', label:'Throttle', min:0, max:100, value:20, unit:'%', ends:['Idle','Take-off'], onInput }) */
  slider(o) {
    const wrap = document.createElement('div'); wrap.className = 'lab-ctl on'
    wrap.innerHTML = `<div class="row"><span>${o.label}</span><b></b></div><input type="range" min="${o.min}" max="${o.max}" step="${o.step ?? (o.max - o.min) / 1000}" value="${o.value}"><div class="ends"><span>${o.ends?.[0] ?? ''}</span><span>${o.ends?.[1] ?? ''}</span></div>`
    this.$('.lab-ctls').appendChild(wrap)
    const inp = wrap.querySelector('input'), out = wrap.querySelector('b')
    const c = { el: inp, wrap, value: o.value, o }
    const show = () => { out.textContent = (o.fmt ? o.fmt(c.value) : fmt(c.value, o.digits ?? 0)) + (o.unit ? ` ${o.unit}` : ''); inp.style.setProperty('--p', `${((c.value - o.min) / (o.max - o.min)) * 100}%`) }
    c.set = (v) => { c.value = clamp(v, o.min, o.max); inp.value = c.value; show(); o.onInput?.(c.value) }
    inp.addEventListener('input', () => { c.value = Number(inp.value); show(); o.onInput?.(c.value) })
    show()
    this.controls[o.id] = c
    return c
  }

  /** the "How it is computed" note: plain words plus the equations the solver uses */
  how(html, eqs = []) {
    this.$('.lab-how .body').innerHTML = `<div>${html}</div>${eqs.map((e) => `<div class="eq">${e}</div>`).join('')}`
  }

  /** mode buttons; the break-it handler comes from lab.breakIt() */
  _modes() {
    const m = this.$('.lab-modes')
    const defs = [['run', 'Pause', 'Space'], ['explode', 'Explode', 'E'], ['cut', 'Cut away', 'C'], ['xray', 'X-ray', 'X'], ['slow', 'Slow', 'S'], ['labels', 'Labels', 'L']]
    if (this._break) defs.push(['break', this._break.label ?? 'Break it', 'B'])
    m.innerHTML = defs.map(([k, t, key]) => `<button data-k="${k}" class="${k === 'break' ? 'brk' : ''}">${t}<kbd>${key}</kbd></button>`).join('')
    m.addEventListener('click', (e) => { const b = e.target.closest('button'); if (b) this.toggle(b.dataset.k) })
    addEventListener('keydown', (e) => {
      if (e.target.tagName === 'INPUT' && e.key !== ' ') return
      const k = { ' ': 'run', e: 'explode', c: 'cut', x: 'xray', s: 'slow', l: 'labels', b: 'break' }[e.key.toLowerCase()]
      if (k) { e.preventDefault(); this.toggle(k) }
    })
  }
  toggle(k, on) {
    if (k === 'run') { this.paused = on ?? !this.paused; this._syncButtons(); return }
    if (k === 'break') { if (on ?? !this.broken) this.breakNow(); else this.resetBreak(); this._syncButtons(); return }
    this.target[k] = (on ?? this.target[k] < 0.5) ? 1 : 0
    this._syncButtons()
  }
  _syncButtons() {
    for (const b of this.ui.querySelectorAll('.lab-modes button')) {
      const k = b.dataset.k
      b.classList.toggle('act', k === 'run' ? !!this.paused : k === 'break' ? this.broken : this.target[k] > 0.5)
      if (k === 'run') b.firstChild.textContent = this.paused ? 'Run' : 'Pause'
    }
  }

  /** lab.breakIt({ label:'Overspeed', run(lab){...}, reset(lab){...} }): the solver decides what fails */
  breakIt(o) { this._break = o }
  breakNow() { if (this.broken) return; this.broken = true; this.brokenAt = this.time; this._break?.run?.(this); this._flash = 1 }
  resetBreak() { this.broken = false; this.brokenAt = -1; for (const d of this.debris) d.restore(); this.debris = []; this._break?.reset?.(this) }

  // ---------- GL
  _initGL() {
    const ss = Number(this.q.get('ss') || 1)
    const r = new THREE.WebGLRenderer({ antialias: false, alpha: false, powerPreference: 'high-performance', preserveDrawingBuffer: this.filmMode })
    r.setPixelRatio(this.filmMode ? ss : Math.min(devicePixelRatio, 2))
    r.setSize(innerWidth, innerHeight)
    r.toneMapping = THREE.NoToneMapping // OutputPass applies it
    r.toneMappingExposure = this.o.exposure ?? 1
    r.shadowMap.enabled = true
    r.shadowMap.type = THREE.VSMShadowMap
    r.localClippingEnabled = true
    r.domElement.id = 'lab-gl'
    r.domElement.tabIndex = 0
    document.body.prepend(r.domElement)
    this.renderer = r
    this.scene = new THREE.Scene()
    const v = this.o.view ?? {}
    this.camera = new THREE.PerspectiveCamera(v.fov ?? 30, innerWidth / innerHeight, 0.02, 400)
    this.camera.layers.enable(LAYER_FX)
    this.root = new THREE.Group(); this.root.scale.setScalar(this.k); this.scene.add(this.root)
    this.machine = new THREE.Group(); this.root.add(this.machine)
    this.fx = new THREE.Group(); this.root.add(this.fx)
    this.controlsOrbit = new OrbitControls(this.camera, r.domElement)
    this.controlsOrbit.enableDamping = true; this.controlsOrbit.dampingFactor = 0.07
    this.controlsOrbit.minDistance = 0.6; this.controlsOrbit.maxDistance = 30
    this.controlsOrbit.maxPolarAngle = Math.PI * 0.495
    this.controlsOrbit.addEventListener('start', () => { this._userAt = performance.now() })
    this.setView(this.o.view ?? {})
    // post: MSAA HDR render, GTAO, bloom, tone map, grade
    const size = r.getDrawingBufferSize(new THREE.Vector2())
    const rt = new THREE.WebGLRenderTarget(size.x, size.y, { type: THREE.HalfFloatType, samples: 4 })
    const comp = new EffectComposer(r, rt)
    comp.addPass(new RenderPass(this.scene, this.camera))
    const ao = new GTAOPass(this.scene, this.camera, size.x, size.y)
    ao.blendIntensity = this.theme === 'paper' ? 0.85 : 1
    ao.updateGtaoMaterial({ radius: 0.35, distanceExponent: 1.6, thickness: 1.2, scale: 1, samples: 16 })
    ao.updatePdMaterial({ lumaPhi: 10, depthPhi: 2, normalPhi: 3, radius: 6, rings: 2, samples: 16 })
    // effects and see-through parts are not solid: keep them out of the normal/depth pass
    const aoRender = ao.render.bind(ao)
    ao.render = (...a) => { this.camera.layers.disable(LAYER_FX); const hidden = []; this.scene.traverse((m) => { if (m.isMesh && m.visible && m.userData.noAO) { m.visible = false; hidden.push(m) } }); aoRender(...a); for (const m of hidden) m.visible = true; this.camera.layers.enable(LAYER_FX) }
    if (ao.normalMaterial) { ao.normalMaterial.clippingPlanes = LAB_PLANES; ao.normalMaterial.clipIntersection = true; ao.normalMaterial.side = THREE.DoubleSide }
    comp.addPass(ao)
    this.ao = ao
    const bloom = new UnrealBloomPass(new THREE.Vector2(size.x / 2, size.y / 2), this.theme === 'paper' ? 0.22 : 0.42, 0.55, this.theme === 'paper' ? 1.6 : 1.0)
    comp.addPass(bloom); this.bloom = bloom
    const out = new OutputPass(); comp.addPass(out)
    r.toneMapping = THREE.NeutralToneMapping
    const grade = new ShaderPass({
      uniforms: { tDiffuse: { value: null }, uTime: { value: 0 }, uVig: { value: this.theme === 'paper' ? 0.1 : 0.32 }, uGrain: { value: this.theme === 'paper' ? 0.012 : 0.02 }, uSat: { value: this.o.saturation ?? 1.06 }, uRes: { value: new THREE.Vector2(size.x, size.y) } },
      vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
      fragmentShader: `uniform sampler2D tDiffuse; uniform float uTime, uVig, uGrain, uSat; uniform vec2 uRes; varying vec2 vUv;
        float h(vec2 p){ return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }
        void main(){ vec3 c = texture2D(tDiffuse, vUv).rgb;
          float l = dot(c, vec3(0.2126, 0.7152, 0.0722)); c = mix(vec3(l), c, uSat);
          vec2 q = vUv - 0.5; q.x *= uRes.x / uRes.y; c *= 1.0 - uVig * smoothstep(0.35, 1.25, length(q));
          c += (h(vUv * uRes + fract(uTime) * 91.7) - 0.5) * uGrain;
          gl_FragColor = vec4(c, 1.0); }`,
    })
    comp.addPass(grade); this.grade = grade
    this.composer = comp
    addEventListener('resize', () => this._resize())
  }
  _resize() {
    const w = innerWidth, h = innerHeight
    this.camera.aspect = w / h; this.camera.updateProjectionMatrix()
    this.renderer.setSize(w, h); this.composer.setSize(w, h)
    const s = this.renderer.getDrawingBufferSize(new THREE.Vector2())
    this.ao.setSize(s.x, s.y); this.grade.uniforms.uRes.value.set(s.x, s.y)
  }

  _initStudio() {
    const paper = this.theme === 'paper'
    const bg = untonemap(new THREE.Color(this.o.bg ?? (paper ? 0xf3f2ee : 0x0d0e10)).convertSRGBToLinear(), this.o.exposure ?? 1)
    this.bgColor = bg
    this.scene.background = bg.clone()
    this.scene.environment = studioEnvironment(this.renderer, this.theme)
    this.scene.environmentIntensity = this.o.envIntensity ?? (paper ? 0.82 : 0.9)
    if (this.o.hdri) {
      this.loading++
      new RGBELoader().load(`https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/1k/${this.o.hdri}_1k.hdr`, (t) => {
        t.mapping = THREE.EquirectangularReflectionMapping
        const pm = new THREE.PMREMGenerator(this.renderer); this.scene.environment = pm.fromEquirectangular(t).texture; pm.dispose(); t.dispose(); this.loading--
      }, undefined, () => { this.loading-- })
    }
    // seamless floor: same colour as the backdrop far away, takes shadows and contact shadow near the machine
    const gy = (this.o.ground ?? 0) * this.k
    this.groundY = gy
    const fm = new THREE.MeshStandardMaterial({ color: paper ? 0xf0efea : 0x121315, roughness: paper ? 0.92 : 0.55, metalness: 0, envMapIntensity: paper ? 0.25 : 0.6 })
    fm.onBeforeCompile = (sh) => {
      sh.uniforms.uBg = { value: bg }
      sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vFW;').replace('#include <project_vertex>', '#include <project_vertex>\nvFW = (modelMatrix * vec4(transformed, 1.0)).xyz;')
      sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nuniform vec3 uBg; varying vec3 vFW;')
        .replace('#include <dithering_fragment>', '#include <dithering_fragment>\nfloat fr = smoothstep(4.5, 16.0, length(vFW.xz)); gl_FragColor.rgb = mix(gl_FragColor.rgb, uBg, fr);')
    }
    const floor = new THREE.Mesh(new THREE.CircleGeometry(40, 96), fm)
    floor.rotation.x = -Math.PI / 2; floor.position.y = gy; floor.receiveShadow = true; floor.userData.studio = true
    this.scene.add(floor); this.floor = floor
    // lights: soft key with VSM shadow, cool rim, gentle fill (the environment does most of the work)
    const key = new THREE.DirectionalLight(0xfff3e6, paper ? 2.4 : 2.6)
    key.position.set(-3.2, 6.5, 4.2); key.castShadow = true
    key.shadow.mapSize.set(2048, 2048); key.shadow.radius = 7; key.shadow.blurSamples = 16
    key.shadow.bias = -0.0004; key.shadow.normalBias = 0.02
    const sc = key.shadow.camera; sc.left = -3.2; sc.right = 3.2; sc.top = 3.2; sc.bottom = -3.2; sc.near = 0.5; sc.far = 20
    this.scene.add(key, key.target); this.key = key
    const rim = new THREE.DirectionalLight(0xdbe8ff, paper ? 0.9 : 1.8); rim.position.set(4, 3, -5); this.scene.add(rim)
    const fill = new THREE.HemisphereLight(0xffffff, paper ? 0xd9d5cc : 0x202020, paper ? 0.2 : 0.15); this.scene.add(fill)
    this._contact = new ContactShadow(this, paper ? 0.7 : 0.85)
  }

  setView(v) {
    this.view = { az: 35, el: 14, dist: 2.2, target: [0, 0, 0], fov: 30, frameX: this.o.frame === 'center' ? 0 : -0.16, ...this.o.view, ...v }
    this._applyView(this.view)
  }
  _applyView(v) {
    const t = new THREE.Vector3(...v.target).multiplyScalar(this.k)
    const d = v.dist * 2.4
    const az = THREE.MathUtils.degToRad(v.az), el = THREE.MathUtils.degToRad(v.el)
    this.camera.fov = v.fov ?? 30
    // shift the frame so the subject sits left of the side column
    this.camera.setViewOffset(innerWidth, innerHeight, -(v.frameX ?? 0) * innerWidth, 0, innerWidth, innerHeight)
    this.camera.position.set(t.x + d * Math.cos(el) * Math.sin(az), t.y + d * Math.sin(el), t.z + d * Math.cos(el) * Math.cos(az))
    this.controlsOrbit.target.copy(t)
    this.camera.lookAt(t)
    this.camera.updateProjectionMatrix()
  }

  // ---------- parts
  /**
   * Add a mesh or group to the machine and register it for explode, x-ray and labels.
   *   lab.add(obj, { name, parent, explode:[dx,dy,dz] (metres), delay:0..1, xray:'shell', label:'Fan', at:[x,y,z], value:()=>'1,240 rpm' })
   */
  add(obj, o = {}) {
    ;(o.parent ?? this.machine).add(obj)
    obj.traverse((m) => { if (m.isMesh) { m.castShadow = o.shadow !== false; m.receiveShadow = true } })
    const p = { obj, name: o.name ?? obj.name, base: obj.position.clone(), off: new THREE.Vector3(...(o.explode ?? [0, 0, 0])), delay: o.delay ?? ((this.parts.length * 0.618) % 1) * 0.3, count: o.count, xray: o.xray, intro: o.intro, order: this.parts.length }
    this.parts.push(p)
    if (o.label) this.label(obj, o.label, { at: o.at, value: o.value, side: o.side })
    if (o.xray === 'shell') obj.traverse((m) => { if (m.isMesh) this.ghosts.push(m) })
    return obj
  }
  /** a single mesh from geometry + material, added: lab.mesh(GEO.disc(...), MAT.steel(), { pos, rot, ...addOptions }) */
  mesh(geo, material, o = {}) {
    const m = new THREE.Mesh(geo, material)
    if (o.pos) m.position.set(...o.pos)
    if (o.rot) m.rotation.set(...o.rot)
    if (o.scale) Array.isArray(o.scale) ? m.scale.set(...o.scale) : m.scale.setScalar(o.scale)
    if (o.add === false) return m
    return this.add(m, o)
  }
  /** keep moving parts in sync: set obj.position via lab.place(obj, x, y, z) so explode offsets still apply */
  place(obj, x, y, z) { const p = this.parts.find((q) => q.obj === obj); if (p) p.base.set(x, y, z); else obj.position.set(x, y, z) }

  /** a pinned label with a leader line: lab.label(obj, 'HP turbine', { at:[x,y,z] in obj frame, value:()=>'1,712 K' }) */
  label(obj, text, o = {}) {
    const el = document.createElement('div'); el.className = 'lab-lab'; el.innerHTML = `${text}<small></small>`
    this.$('.lab-labels').appendChild(el)
    const L = { obj, at: new THREE.Vector3(...(o.at ?? [0, 0, 0])), el, small: el.querySelector('small'), value: o.value, side: o.side }
    this.labels.push(L)
    return L
  }

  onTick(f) { this.tickers.push(f) }

  // ---------- effects factories
  flow(o) { const f = new Flow(this, o); return f }
  plume(o) { return new Plume(this, o) }
  /** throw a part off as a rigid body: lab.shed(mesh, velocity [m/s], spin [rad/s]) */
  shed(obj, v = [0, 2, 0], w = [3, 1, 2]) { const d = new Debris(this, obj, v, w); this.debris.push(d); return d }

  // ---------- frame
  _update(dt) {
    const s = this.state, tg = this.target
    const rate = (k, tau) => { s[k] = approach(s[k], tg[k], tau, dt) ; if (Math.abs(s[k] - tg[k]) < 1e-4) s[k] = tg[k] }
    rate('explode', 0.45); rate('cut', 0.42); rate('xray', 0.3); rate('slow', 0.35); rate('labels', 0.25)
    this.timeScale = lerp(1, 0.08, s.slow)
    const sdt = this.paused ? 0 : dt * this.timeScale
    this.time += sdt
    this.sdt = sdt
    for (const f of this.tickers) f(sdt, this, dt)
    // explode with stagger, then the intro assembly (parts fly in from far)
    const e = s.explode, A = this._assembly ?? 0
    for (const p of this.parts) {
      const ee = ease.io(clamp((e * 1.35) - p.delay * 0.35))
      const ai = A > 0 ? ease.out(clamp((1 - A) * 1.6 - (p.order / Math.max(1, this.parts.length)) * 0.6)) : 1
      const far = p.intro ? new THREE.Vector3(...p.intro) : p.off.clone().normalize().multiplyScalar(this.size * 1.6).add(new THREE.Vector3(0, this.size * 0.9, 0))
      p.obj.position.copy(p.base).addScaledVector(p.off, ee).addScaledVector(far, 1 - ai)
      p.obj.visible = ai > 0.001 || A === 0
    }
    this._buildHUD(A)
    this._updateCut()
    this._updateXray(dt)
    for (const d of this.debris) d.update(sdt)
    this.sparks.update(sdt)
    this._flash = Math.max(0, (this._flash ?? 0) - dt * 2.2)
    this.$('.lab-flash').style.opacity = String(this._flash * 0.18)
  }
  /** total physical parts: each registered part counts its meshes, or the count it was given (a blade ring = 24) */
  partCount() { return this.parts.reduce((n, p) => n + (p.count ?? (() => { let k = 0; p.obj.traverse((m) => { if (m.isMesh && !m.userData.ghost && m.layers.mask & 1) k++ }); return Math.max(1, k) })()), 0) }
  _buildHUD(A) {
    if (!this.heroO) return
    const building = A > 0.0005
    if (building) {
      const N = this._pc ?? (this._pc = this.partCount())
      let n = 0, cur = this.parts[0]?.name ?? ''
      for (const p of this.parts) { const ai = ease.out(clamp((1 - A) * 1.6 - (p.order / Math.max(1, this.parts.length)) * 0.6)); const c = p.count ?? 1; if (ai > 0.92) { n += p._c ?? (p._c = p.count ?? (() => { let k = 0; p.obj.traverse((m) => { if (m.isMesh && m.layers.mask & 1) k++ }); return Math.max(1, k) })()); cur = p.name || cur } void c }
      if (!this._building) { this._building = true; this._saveHero = this.metricEl.innerHTML }
      this._hs.textContent = cur
      this.metricEl.querySelector('.lbl').firstChild.textContent = 'Building · '
      this._hv.textContent = fmt(n)
      this.metricEl.querySelector('.lab-big i').textContent = `of ${fmt(N)} parts`
      this._hb.firstElementChild.style.width = `${(n / N) * 100}%`
      this._hb.classList.remove('bad')
      this._hsub.textContent = `${fmt(this.tris ?? 0)} triangles · ${this.matCount ?? 0} materials`
    } else if (this._building) {
      this._building = false
      this.metricEl.querySelector('.lbl').firstChild.textContent = `${this.heroO.label} · `
      this.metricEl.querySelector('.lab-big i').textContent = this.heroO.unit ?? ''
      if (this._heroPending) this.setHero(...this._heroPending)
    }
  }
  _updateCut() {
    const c = this.o.cut ?? {}
    const a = new THREE.Vector3(...(c.a ?? [0, 0, 1])).normalize(), b = new THREE.Vector3(...(c.b ?? c.a ?? [0, 0, 1])).normalize()
    const ctr = new THREE.Vector3(...(c.center ?? [0, 0, 0]))
    const sweep = this.size * (c.reach ?? 0.8) * (1 - ease.io(this.state.cut)) + (c.offset ?? 0)
    // planes in machine space -> world
    this.machine.updateWorldMatrix(true, false)
    const M = this.machine.matrixWorld, N = new THREE.Matrix3().getNormalMatrix(M)
    const mk = (dir, plane, U) => {
      if (this.state.cut <= 0.0005) { plane.set(new THREE.Vector3(0, 0, -1), 1e5); U.value.set(0, 0, -1, 1e5); return }
      const n = dir.clone().negate(), p0 = ctr.clone().addScaledVector(dir, sweep)
      const pl = new THREE.Plane().setFromNormalAndCoplanarPoint(n, p0).applyMatrix4(M, N)
      plane.copy(pl); U.value.set(pl.normal.x, pl.normal.y, pl.normal.z, pl.constant)
    }
    mk(a, LAB_PLANES[0], CUT.a); mk(b, LAB_PLANES[1], CUT.b)
    CUT.hatch.value = 0.006 * this.k * this.size * 0.25
  }
  _updateXray() {
    const x = this.state.xray
    for (const m of this.ghosts) {
      if (!m.userData.ghost) {
        const g = new THREE.Mesh(m.geometry, GHOST.clone()); g.layers.set(LAYER_FX); g.renderOrder = 5
        g.userData.edges = new THREE.LineSegments(new THREE.EdgesGeometry(m.geometry, 28), new THREE.LineBasicMaterial({ color: this.theme === 'paper' ? 0x2a3442 : 0xbcd4ff, transparent: true, opacity: 0, depthWrite: false }))
        g.userData.edges.layers.set(LAYER_FX)
        m.add(g, g.userData.edges); m.userData.ghost = g
        const mats = Array.isArray(m.material) ? m.material : [m.material]
        m.userData.solidMats = mats
      }
      const g = m.userData.ghost
      g.visible = x > 0.002; g.userData.edges.visible = x > 0.002
      g.material.uniforms.uA.value = x; g.material.uniforms.uPaper.value = this.theme === 'paper' ? 1 : 0
      g.userData.edges.material.opacity = x * (this.theme === 'paper' ? 0.35 : 0.3)
      for (const sm of m.userData.solidMats) {
        const want = x > 0.002
        if (sm.transparent !== want && !sm.userData.wasTransparent) { sm.transparent = want; sm.depthWrite = !want; sm.needsUpdate = true }
        if (sm.transmission === 0 || sm.transmission === undefined) sm.opacity = 1 - x
      }
      m.userData.noAO = x > 0.5
      m.castShadow = x < 0.5
    }
  }
  _updateLabels() {
    const on = this.state.labels
    const W = innerWidth, H = innerHeight
    const svg = this.$('.lab-labels svg')
    let lines = ''
    const ctr = new THREE.Vector3().setFromMatrixPosition(this.machine.matrixWorld).project(this.camera)
    const items = []
    for (const L of this.labels) {
      const p = L.at.clone(); L.obj.updateWorldMatrix(true, false); p.applyMatrix4(L.obj.matrixWorld)
      const s = p.project(this.camera)
      const vis = on > 0.01 && s.z < 1 && L.obj.visible !== false
      if (!vis) { L.el.style.opacity = '0'; continue }
      const x = (s.x * 0.5 + 0.5) * W, y = (-s.y * 0.5 + 0.5) * H
      const side = L.side ?? (s.x < ctr.x ? 'left' : 'right')
      items.push({ L, x, y, side })
    }
    // spread labels vertically per side so they never overlap
    for (const side of ['left', 'right']) {
      const list = items.filter((i) => i.side === side).sort((a, b) => a.y - b.y)
      const gap = Math.max(34, H * 0.045)
      let last = -1e9
      for (const it of list) { it.ly = Math.max(it.y, last + gap); last = it.ly }
      const xs = side === 'left' ? Math.min(...list.map((i) => i.x)) - W * 0.06 : Math.max(...list.map((i) => i.x)) + W * 0.06
      for (const it of list) it.lx = clamp(xs, W * 0.05, W * 0.7)
    }
    for (const it of items) {
      const { L, x, y, lx, ly, side } = it
      L.el.className = 'lab-lab' + (side === 'left' ? ' left' : '')
      L.el.style.left = `${lx + (side === 'left' ? -8 : 8)}px`; L.el.style.top = `${ly}px`; L.el.style.opacity = String(on)
      if (L.value) L.small.textContent = L.value()
      const ink = this.theme === 'paper' ? '20,20,20' : '240,238,232'
      lines += `<path d="M${x.toFixed(1)},${y.toFixed(1)} L${(lx + (side === 'left' ? 12 : -12)).toFixed(1)},${ly.toFixed(1)} L${lx.toFixed(1)},${ly.toFixed(1)}" stroke="rgba(${ink},${(0.55 * on).toFixed(3)})" stroke-width="1" fill="none"/><circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="3" fill="rgba(${ink},${on.toFixed(3)})" stroke="${this.theme === 'paper' ? '#fff' : '#000'}" stroke-width="1.2"/>`
    }
    svg.innerHTML = lines
  }
  _updateScale() {
    const el = this.$('.lab-scale'); if (el.style.display === 'none') return
    // one real metre (or a nice fraction) on screen at the target distance
    const d = this.camera.position.distanceTo(this.controlsOrbit.target)
    const pxPerUnit = innerHeight / (2 * Math.tan(THREE.MathUtils.degToRad(this.camera.fov / 2)) * d)
    const pxPerM = pxPerUnit * this.k
    const nice = [0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100]
    let L = nice[0]; for (const n of nice) if (n * pxPerM <= 140) L = n
    el.querySelector('div').style.width = `${(L * pxPerM).toFixed(1)}px`
    el.querySelector('span').textContent = L >= 1 ? `${L} m` : L >= 0.01 ? `${Math.round(L * 100)} cm` : `${Math.round(L * 1000)} mm`
  }

  render(dt) {
    this._update(dt)
    if (!this.filmMode) {
      const idle = performance.now() - (this._userAt ?? -1e9) > 9000
      if (idle && this.o.autoOrbit !== false && !this._cam) { this.controlsOrbit.autoRotate = true; this.controlsOrbit.autoRotateSpeed = 0.35 } else this.controlsOrbit.autoRotate = false
      this.controlsOrbit.update(dt)
    }
    this.camera.updateMatrixWorld()
    CUT.proj.value.multiplyMatrices(this.camera.projectionMatrix, this.camera.matrixWorldInverse)
    this._contact.update()
    this.grade.uniforms.uTime.value = this.time
    this.composer.render(dt)
    this._updateLabels()
    this._updateScale()
  }

  /** start the loop (or film mode). Call after building the machine and registering controls. */
  start() {
    this._modes()
    this._syncButtons()
    // cut and labels reach: frame the shadow camera to the machine
    const box = new THREE.Box3().setFromObject(this.machine)
    const sz = box.getSize(new THREE.Vector3()).length() * 0.65
    const sc = this.key.shadow.camera; sc.left = -sz; sc.right = sz; sc.top = sz; sc.bottom = -sz; sc.updateProjectionMatrix()
    this.key.target.position.copy(box.getCenter(new THREE.Vector3()))
    this.key.position.copy(this.key.target.position).add(new THREE.Vector3(-3.2, 6.5, 4.2))
    this.renderer.compile(this.scene, this.camera)
    let tris = 0; const mats = new Set()
    this.machine.traverse((m) => { if (m.isMesh) { const g = m.geometry; tris += (g.index ? g.index.count : g.attributes.position.count) / 3 * (m.isInstancedMesh ? m.count : 1); (Array.isArray(m.material) ? m.material : [m.material]).forEach((x) => mats.add(x)) } })
    this.tris = Math.round(tris); this.matCount = mats.size
    if (this.filmMode) { this._initFilm(); return }
    this._typePrompt(1.1)
    this._assembly = 1
    const t0 = performance.now(); let last = t0
    const loop = (now) => {
      const dt = clamp((now - last) / 1000, 0, 0.05); last = Math.max(last, now)
      if (this._assembly > 0) this._assembly = Math.max(0, 1 - (now - t0 - 500) / 2600)
      this.render(dt)
      requestAnimationFrame(loop)
    }
    requestAnimationFrame(loop)
  }
  _typePrompt(sec) {
    const el = this.$('.lab-prompt .txt'), full = this.o.prompt ?? ''
    const t0 = performance.now()
    const step = () => { const k = clamp((performance.now() - t0) / (sec * 1000)); el.textContent = full.slice(0, Math.round(full.length * k)); if (k < 1) requestAnimationFrame(step) }
    step()
  }

  // ---------- film
  /**
   * Film = shots (camera keys) + events (beats, modes, slider moves, cursor, break it).
   *   lab.film('main', { len: 28, shots: [{ t:0, az, el, dist, target, fov }...], events: [{ t, beat:['Bold.','grey.'], set:{explode:1}, slider:{id, to, dur}, cursor:{to:'slider:throttle'|[x,y], click:true}, do(lab){} }] })
   * Without a call, lab.autoFilm() builds the standard 28 s story from the machine.
   */
  film(name, f) { (this.films ??= {})[name] = f; return this }
  autoFilm(o = {}) {
    const v = this.view, sl = Object.keys(this.controls)[0]
    const c = sl ? this.controls[sl] : null
    const T = (dz) => ({ ...v, ...dz })
    const f = {
      len: 28,
      assemble: [0.4, 4.2],
      shots: [
        { t: 0, ...T({ az: v.az - 28, el: v.el + 6, dist: v.dist * 1.08 }) },
        { t: 4.5, ...T({ az: v.az - 8, dist: v.dist * 1.0 }) },
        { t: 10, ...T({ az: v.az + 6, el: v.el + 2, dist: v.dist * 0.94 }) },
        { t: 15, ...T({ az: v.az + 18, el: v.el + 8, dist: v.dist * 0.9 }) },
        { t: 20, ...T({ az: v.az + 30, el: v.el + 12, dist: v.dist * 1.04 }) },
        { t: 24.5, ...T({ az: v.az + 8, el: v.el + 4, dist: v.dist * 1.0 }) },
        { t: 28, ...T({ az: v.az - 28, el: v.el + 6, dist: v.dist * 1.08 }) },
      ],
      events: [
        { t: 0, type: [0.2, 1.6], beat: ['01', 'One sentence is the whole brief.', 'Typed into Claude Code.'] },
        { t: 2.2, beat: ['02', 'Claude builds the machine.', `Part by part, ${this.parts.length} of them.`] },
        ...(c ? [
          { t: 6.2, beat: ['03', o.runBeat ?? 'It runs on real physics.', o.runSub ?? 'Every number comes from the solver.'], cursor: { to: `slider:${sl}:${(c.value - c.o.min) / (c.o.max - c.o.min)}`, dur: 0.9 } },
          { t: 7.4, cursor: { to: `slider:${sl}:${o.sliderTo ?? 1}`, dur: 2.4, drag: true }, slider: { id: sl, to: c.o.min + (c.o.max - c.o.min) * (o.sliderTo ?? 1), dur: 2.4 } },
          { t: 10.4, cursor: { hide: true } },
        ] : [{ t: 6.2, beat: ['03', 'It runs on real physics.', 'Every number comes from the solver.'] }]),
        { t: 11.2, beat: ['04', 'Cut it open.', 'Real section caps, live.'], set: { cut: 1, labels: 1 } },
        { t: 16.2, set: { cut: 0, labels: 0 } },
        { t: 16.4, beat: ['05', 'Take it apart.', 'Every part on its own axis.'], set: { explode: 1 } },
        { t: 20.6, set: { explode: 0 } },
        ...(this._break ? [
          { t: 21.4, beat: ['06', o.breakBeat ?? 'Then break it.', o.breakSub ?? 'The solver decides what fails.'], cursor: { to: 'button:break', dur: 0.8 }, set: o.breakCut ? { cut: 1 } : undefined },
          { t: 22.4, cursor: { click: true }, do: (lab) => lab.breakNow() },
          { t: 22.9, cursor: { hide: true } },
          { t: 26.2, do: (lab) => lab.resetBreak(), slider: c ? { id: sl, to: c.o.value, dur: 0.01 } : null, set: o.breakCut ? { cut: 0 } : undefined },
        ] : []),
      ],
    }
    return this.film('main', { ...f, ...o.override })
  }
  _initFilm() {
    const shot = this.q.get('shot') || 'main'
    if (!this.films?.[shot]) this.autoFilm()
    const F = this.films[shot] ?? this.films.main
    this.F = F
    this.ft = 0
    this._fired = new Set()
    // reset everything the film touches so a take is identical every time
    const init = { slider: Object.fromEntries(Object.entries(this.controls).map(([k, c]) => [k, c.value])) }
    this._filmInit = init
    this.$('.lab-prompt .txt').textContent = this.o.prompt ?? ''
    window.__film = {
      ready: true,
      len: F.len,
      loaded: () => this.loading <= 0 && document.fonts.status === 'loaded',
      start: () => { this.ft = 0; this.render(0) },
      step: (dt) => this._filmStep(dt),
      seek: (t) => { while (this.ft < t - 1e-6) this._filmStep(Math.min(1 / 30, t - this.ft)) },
    }
  }
  _filmStep(dt) {
    const F = this.F
    this.ft += dt
    const t = this.ft
    // assembly window
    if (F.assemble) { const [a0, a1] = F.assemble; this._assembly = t < a0 ? 1 : clamp(1 - (t - a0) / (a1 - a0)) } else this._assembly = 0
    // events
    F.events.forEach((e, i) => {
      if (t >= e.t && !this._fired.has(i)) {
        this._fired.add(i)
        if (e.set) for (const [k, v] of Object.entries(e.set)) this.target[k] = v
        if (e.snap) for (const [k, v] of Object.entries(e.snap)) { this.target[k] = v; this.state[k] = v }
        if (e.slider) this._sl = { ...e.slider, t0: t, from: this.controls[e.slider.id].value }
        if (e.beat) this._beat = { n: e.beat[0], a: e.beat[1], b: e.beat[2], t0: t }
        if (e.type) this._type = { t0: t + e.type[0], dur: e.type[1] }
        if (e.cursor) this._cursorEv(e.cursor, t)
        e.do?.(this)
      }
    })
    if (this._sl) { const s = this._sl, k = s.dur > 0 ? ease.io(clamp((t - s.t0) / s.dur)) : 1; this.controls[s.id].set(lerp(s.from, s.to, k)); if (k >= 1) this._sl = null }
    // camera
    const S = F.shots
    let i = 0; while (i < S.length - 2 && t > S[i + 1].t) i++
    const A = S[i], B = S[Math.min(i + 1, S.length - 1)]
    const k = B.t > A.t ? (B.ease ? ease[B.ease] : ease.io)(clamp((t - A.t) / (B.t - A.t))) : 1
    const mix = (x, y) => Array.isArray(x) ? x.map((q, j) => lerp(q, y[j], k)) : lerp(x, y, k)
    const v = {}; for (const key of ['az', 'el', 'dist', 'fov', 'frameX']) v[key] = mix(A[key] ?? this.view[key], B[key] ?? this.view[key]); v.target = mix(A.target ?? this.view.target, B.target ?? this.view.target)
    this._applyView(v)
    this._updateBeat(t)
    this._updateType(t)
    this._updateCursor(t)
    this.render(dt)
  }
  _updateBeat(t) {
    const el = this.$('.lab-beat'), b = this._beat
    if (!b) { el.style.opacity = '0'; return }
    el.querySelector('.n').textContent = b.n; el.querySelector('b').textContent = b.a; el.querySelector(':scope > div > span').textContent = b.b
    const k = clamp((t - b.t0) / 0.45)
    el.style.opacity = String(ease.out(k)); el.style.transform = `translateY(${(1 - ease.out(k)) * 10}px)`
  }
  _updateType(t) {
    const el = this.$('.lab-prompt .txt'), full = this.o.prompt ?? '', caret = this.$('.lab-prompt .caret')
    if (!this._type) return
    const k = clamp((t - this._type.t0) / this._type.dur)
    el.textContent = full.slice(0, Math.round(full.length * k)); caret.style.display = k < 1 || t - this._type.t0 < this._type.dur + 0.6 ? 'inline-block' : 'none'
    caret.style.animation = 'none'; caret.style.opacity = (Math.floor(t * 2) % 2 === 0 || k < 1) ? '1' : '0'
  }
  _cursorPos(spec) {
    if (Array.isArray(spec)) return { x: spec[0] * innerWidth, y: spec[1] * innerHeight }
    const [kind, id, frac] = spec.split(':')
    if (kind === 'slider') { const r = this.controls[id].el.getBoundingClientRect(); const f = Number(frac ?? 0.5); const th = r.height * 0.88; return { x: r.left + th / 2 + (r.width - th) * f + 2, y: r.top + r.height / 2 + 4 } }
    if (kind === 'button') { const b = this.ui.querySelector(`.lab-modes button[data-k="${id}"]`); const r = b.getBoundingClientRect(); return { x: r.left + r.width * 0.55, y: r.top + r.height * 0.6 } }
    if (kind === 'part') { const p = this.parts.find((q) => q.name === id); const w = new THREE.Vector3().setFromMatrixPosition(p.obj.matrixWorld).project(this.camera); return { x: (w.x * 0.5 + 0.5) * innerWidth, y: (-w.y * 0.5 + 0.5) * innerHeight } }
    return { x: innerWidth / 2, y: innerHeight / 2 }
  }
  _cursorEv(c, t) {
    const cur = this._cur ?? (this._cur = { x: innerWidth * 0.62, y: innerHeight * 0.78, a: 0, click: -1 })
    if (c.hide) { cur.hideAt = t; return }
    if (c.click) { cur.click = t; if (c.to) Object.assign(cur, { from: { x: cur.x, y: cur.y }, to: c.to, t0: t, dur: c.dur ?? 0.8 }); return }
    cur.hideAt = undefined
    if (cur.a === 0) { const p = this._cursorPos(c.to); cur.x = p.x + innerWidth * 0.06; cur.y = p.y + innerHeight * 0.12 }
    Object.assign(cur, { from: { x: cur.x, y: cur.y }, to: c.to, t0: t, dur: c.dur ?? 0.8, showAt: cur.a < 0.5 ? t : cur.showAt })
  }
  _updateCursor(t) {
    const el = this.$('.lab-cursor'), c = this._cur
    if (!c) { el.style.opacity = '0'; return }
    if (c.to) { const p = this._cursorPos(c.to); const k = ease.io(clamp((t - c.t0) / c.dur)); c.x = lerp(c.from.x, p.x, k); c.y = lerp(c.from.y, p.y, k) }
    const target = c.hideAt !== undefined && t > c.hideAt ? 0 : 1
    c.a = target ? Math.min(1, c.a + 0.12) : Math.max(0, c.a - 0.08)
    const press = c.click >= 0 && t - c.click < 0.25 ? 0.82 : 1
    el.style.opacity = String(c.a); el.style.transform = `translate(${c.x}px, ${c.y}px) scale(${press})`
  }
}

// ---------------------------------------------------------------- x-ray ghost

const GHOST = new THREE.ShaderMaterial({
  uniforms: { uA: { value: 0 }, uPaper: { value: 1 } },
  transparent: true, depthWrite: false, side: THREE.DoubleSide,
  vertexShader: 'varying vec3 vN; varying vec3 vV; void main(){ vec4 mv = modelViewMatrix * vec4(position,1.0); vN = normalize(normalMatrix * normal); vV = -mv.xyz; gl_Position = projectionMatrix * mv; }',
  fragmentShader: `uniform float uA, uPaper; varying vec3 vN; varying vec3 vV;
    void main(){ float f = pow(1.0 - abs(dot(normalize(vN), normalize(vV))), 2.2);
      vec3 c = mix(vec3(0.55, 0.75, 1.0), vec3(0.16, 0.22, 0.3), uPaper);
      gl_FragColor = vec4(c, (0.05 + 0.5 * f) * uA * mix(1.0, 0.7, uPaper)); }`,
})

// ---------------------------------------------------------------- contact shadow

class ContactShadow {
  // depth seen from below the floor, blurred twice: the soft dark pool under the machine
  constructor(lab, opacity) {
    this.lab = lab
    const S = 512, W = 7
    this.rt = new THREE.WebGLRenderTarget(S, S); this.rt.texture.generateMipmaps = false
    this.rtB = new THREE.WebGLRenderTarget(S, S); this.rtB.texture.generateMipmaps = false
    this.cam = new THREE.OrthographicCamera(-W / 2, W / 2, W / 2, -W / 2, 0, 2.4)
    this.cam.rotation.x = Math.PI / 2
    this.cam.position.y = lab.groundY
    const plane = new THREE.Mesh(new THREE.PlaneGeometry(W, W).rotateX(Math.PI / 2), new THREE.MeshBasicMaterial({ map: this.rt.texture, transparent: true, opacity, depthWrite: false, toneMapped: false, color: lab.theme === 'paper' ? 0x3a3530 : 0x000000 }))
    plane.position.y = lab.groundY + 0.002; plane.scale.y = -1; plane.renderOrder = 1; plane.layers.set(LAYER_FX)
    plane.material.onBeforeCompile = (sh) => { sh.fragmentShader = sh.fragmentShader.replace('#include <map_fragment>', 'vec4 sampledDiffuseColor = texture2D(map, vMapUv); diffuseColor.a *= sampledDiffuseColor.a;') }
    lab.scene.add(plane, this.cam)
    this.plane = plane
    this.depthMat = new THREE.MeshDepthMaterial()
    this.depthMat.onBeforeCompile = (sh) => { sh.uniforms.darkness = { value: 2.2 }; sh.fragmentShader = 'uniform float darkness;\n' + sh.fragmentShader.replace('gl_FragColor = vec4( vec3( 1.0 - fragCoordZ ), opacity );', 'gl_FragColor = vec4( vec3( 0.0 ), ( 1.0 - fragCoordZ ) * darkness );') }
    this.depthMat.depthTest = false; this.depthMat.depthWrite = false
    this.depthMat.clippingPlanes = LAB_PLANES; this.depthMat.clipIntersection = true
    this.hb = new THREE.ShaderMaterial(HorizontalBlurShader); this.hb.depthTest = false
    this.vb = new THREE.ShaderMaterial(VerticalBlurShader); this.vb.depthTest = false
    this.quad = new THREE.Mesh(new THREE.PlaneGeometry(W, W).rotateX(Math.PI / 2), this.hb); this.quad.frustumCulled = false; this.quad.position.y = lab.groundY + 0.01
  }
  blur(amount) {
    const r = this.lab.renderer
    this.quad.material = this.hb; this.hb.uniforms.tDiffuse.value = this.rt.texture; this.hb.uniforms.h.value = amount / 256
    r.setRenderTarget(this.rtB); r.render(this.quad, this.cam)
    this.quad.material = this.vb; this.vb.uniforms.tDiffuse.value = this.rtB.texture; this.vb.uniforms.v.value = amount / 256
    r.setRenderTarget(this.rt); r.render(this.quad, this.cam)
  }
  update() {
    const lab = this.lab, r = lab.renderer, sc = lab.scene
    const bg = sc.background, ov = sc.overrideMaterial
    const hide = []; sc.traverse((o) => { if ((o.userData.studio || o === this.plane) && o.visible) { o.visible = false; hide.push(o) } })
    sc.background = null; sc.overrideMaterial = this.depthMat
    const cc = r.getClearAlpha(); r.setClearAlpha(0)
    r.setRenderTarget(this.rt); r.clear(); r.render(sc, this.cam)
    sc.overrideMaterial = ov
    this.blur(1.2); this.blur(0.5)
    r.setRenderTarget(null); r.setClearAlpha(cc)
    sc.background = bg
    for (const o of hide) o.visible = true
  }
}

// ---------------------------------------------------------------- sparks

class Sparks {
  constructor(lab, max = 1600) {
    this.lab = lab; this.max = max; this.n = 0
    this.p = new Float32Array(max * 3); this.v = new Float32Array(max * 3); this.life = new Float32Array(max); this.age = new Float32Array(max)
    const g = new THREE.BufferGeometry()
    g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(max * 3), 3))
    g.setAttribute('aV', new THREE.BufferAttribute(new Float32Array(max * 3), 3))
    g.setAttribute('aK', new THREE.BufferAttribute(new Float32Array(max), 1))
    const m = new THREE.ShaderMaterial({
      uniforms: { uSize: { value: 0.012 }, uPx: { value: innerHeight } },
      transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
      vertexShader: `attribute vec3 aV; attribute float aK; varying float vK; uniform float uSize, uPx;
        void main(){ vK = aK; vec4 mv = modelViewMatrix * vec4(position, 1.0); gl_Position = projectionMatrix * mv; gl_PointSize = uSize * uPx / -mv.z * (0.4 + aK); }`,
      fragmentShader: `varying float vK; void main(){ vec2 q = gl_PointCoord - 0.5; float a = smoothstep(0.5, 0.0, length(q)); vec3 c = mix(vec3(1.0, 0.25, 0.04), vec3(1.0, 0.85, 0.5), vK); gl_FragColor = vec4(c * 4.0 * a * vK, 1.0); }`,
    })
    this.pts = new THREE.Points(g, m); this.pts.frustumCulled = false; this.pts.layers.set(LAYER_FX)
    lab.scene.add(this.pts)
    this.R = rng(7)
  }
  /** emit n sparks at a world point (use lab.machine.localToWorld) with speed s (display units/s) */
  emit(pos, n = 80, s = 3, dir = null) {
    const R = this.R
    for (let i = 0; i < n; i++) {
      const j = this.n++ % this.max
      this.p.set([pos.x, pos.y, pos.z], j * 3)
      const d = new THREE.Vector3(R() - 0.5, R() - 0.2, R() - 0.5).normalize()
      if (dir) d.lerp(dir, 0.6).normalize()
      const sp = s * (0.3 + R())
      this.v.set([d.x * sp, d.y * sp, d.z * sp], j * 3)
      this.life[j] = 0.4 + R() * 1.1; this.age[j] = 0
    }
  }
  update(dt) {
    const g = this.pts.geometry, P = g.attributes.position.array, K = g.attributes.aK.array
    const gy = this.lab.groundY
    for (let j = 0; j < this.max; j++) {
      if (this.life[j] <= 0) { K[j] = 0; continue }
      this.age[j] += dt
      if (this.age[j] > this.life[j]) { this.life[j] = 0; K[j] = 0; continue }
      this.v[j * 3 + 1] -= 9.8 * 0.5 * dt
      for (let a = 0; a < 3; a++) this.p[j * 3 + a] += this.v[j * 3 + a] * dt
      if (this.p[j * 3 + 1] < gy) { this.p[j * 3 + 1] = gy; this.v[j * 3 + 1] *= -0.35; this.v[j * 3] *= 0.6; this.v[j * 3 + 2] *= 0.6 }
      P[j * 3] = this.p[j * 3]; P[j * 3 + 1] = this.p[j * 3 + 1]; P[j * 3 + 2] = this.p[j * 3 + 2]
      K[j] = 1 - this.age[j] / this.life[j]
    }
    this.pts.material.uniforms.uPx.value = innerHeight * this.lab.renderer.getPixelRatio()
    g.attributes.position.needsUpdate = true; g.attributes.aK.needsUpdate = true
  }
}

// ---------------------------------------------------------------- debris (a part that breaks off)

class Debris {
  constructor(lab, obj, v, w) {
    this.lab = lab; this.obj = obj
    this.parent = obj.parent; this.saved = { p: obj.position.clone(), q: obj.quaternion.clone() }
    // move to world (scene) space, keep pose
    obj.updateWorldMatrix(true, false)
    const M = obj.matrixWorld.clone()
    lab.scene.attach(obj)
    obj.matrix.copy(M); obj.matrix.decompose(obj.position, obj.quaternion, obj.scale)
    const k = lab.k
    this.v = new THREE.Vector3(...v).multiplyScalar(k); this.w = new THREE.Vector3(...w)
    this.box = new THREE.Box3()
  }
  update(dt) {
    if (dt <= 0) return
    const o = this.obj
    this.v.y -= 9.81 * this.lab.k * dt
    o.position.addScaledVector(this.v, dt)
    const q = new THREE.Quaternion().setFromEuler(new THREE.Euler(this.w.x * dt, this.w.y * dt, this.w.z * dt)); o.quaternion.premultiply(q)
    this.box.setFromObject(o)
    if (this.box.min.y < this.lab.groundY) { o.position.y += this.lab.groundY - this.box.min.y; if (this.v.y < 0) this.v.y *= -0.25; this.v.x *= 0.7; this.v.z *= 0.7; this.w.multiplyScalar(0.8) }
  }
  restore() { this.parent.attach(this.obj); this.obj.position.copy(this.saved.p); this.obj.quaternion.copy(this.saved.q) }
}

// ---------------------------------------------------------------- flow particles along paths

class Flow {
  /**
   * Streamlines that move: each particle is a short streak drawn along its path, bright at the head,
   * fading at the tail (reads like smoke in a wind tunnel, not dust).
   * lab.flow({ paths: [[[x,y,z],...], ...] (machine metres), count: 500, length: 0.06 (fraction of a path),
   *            color: (pathIndex, u) => [r,g,b], speed: 0.3 (path lengths per second), parent })
   *   f.speed and f.opacity are set each frame from the solver; f.colorFn can change live
   */
  constructor(lab, o) {
    this.lab = lab; this.o = o
    this.curves = o.paths.map((p) => p.isCurve ? p : new THREE.CatmullRomCurve3(p.map((q) => new THREE.Vector3(...q))))
    // sample every path once into a lookup table (getPointAt per frame is too slow)
    const S = 256
    this.lut = this.curves.map((c) => { const a = new Float32Array((S + 1) * 3); const v = new THREE.Vector3(); for (let i = 0; i <= S; i++) { c.getPointAt(i / S, v); a[i * 3] = v.x; a[i * 3 + 1] = v.y; a[i * 3 + 2] = v.z } return a })
    this.S = S
    const lens = this.curves.map((c) => c.getLength())
    const n = o.count ?? 500; this.n = n
    this.seg = o.segments ?? 8
    this.len = o.length ?? 0.07
    const R = rng(o.seed ?? 3)
    this.pi = new Uint16Array(n); this.u = new Float32Array(n); this.sp = new Float32Array(n)
    const tot = lens.reduce((x, y) => x + y, 0)
    for (let i = 0; i < n; i++) {
      let r = R() * tot, k = 0; while (r > lens[k] && k < lens.length - 1) { r -= lens[k]; k++ }
      this.pi[i] = k; this.u[i] = R(); this.sp[i] = 0.85 + R() * 0.3
    }
    this.speed = o.speed ?? 0.3
    this.colorFn = o.color ?? (() => [0.3, 0.55, 1])
    const V = n * this.seg * 2
    const g = new THREE.BufferGeometry()
    g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(V * 3), 3))
    g.setAttribute('color', new THREE.BufferAttribute(new Float32Array(V * 4), 4))
    const paper = lab.theme === 'paper'
    const m = new THREE.LineBasicMaterial({ vertexColors: true, transparent: true, depthWrite: false, blending: paper ? THREE.NormalBlending : THREE.AdditiveBlending, toneMapped: false })
    this.lines = new THREE.LineSegments(g, m); this.lines.frustumCulled = false; this.lines.layers.set(LAYER_FX); this.lines.renderOrder = 3
    ;(o.parent ?? lab.machine).add(this.lines)
    this.opacity = 1
    lab.onTick((dt) => this.update(dt))
  }
  _at(k, u, out, o) { const L = this.lut[k], f = clamp(u) * this.S, i = Math.min(this.S - 1, Math.floor(f)), t = f - i; for (let a = 0; a < 3; a++) out[o + a] = L[i * 3 + a] + (L[i * 3 + 3 + a] - L[i * 3 + a]) * t }
  update(dt) {
    const g = this.lines.geometry, P = g.attributes.position.array, C = g.attributes.color.array
    const seg = this.seg, op = this.opacity
    this.lines.visible = op > 0.003
    if (!this.lines.visible) return
    let v = 0
    for (let i = 0; i < this.n; i++) {
      const k = this.pi[i]
      this.u[i] = (this.u[i] + dt * this.speed * this.sp[i] * (this.o.perPath ? this.o.perPath[k] ?? 1 : 1)) % 1
      const head = this.u[i]
      const c = this.colorFn(k, head)
      const life = smoothstep(0, 0.08, head) * smoothstep(1, 0.9, head)
      for (let j = 0; j < seg; j++) {
        const u0 = head - (this.len * j) / seg, u1 = head - (this.len * (j + 1)) / seg
        this._at(k, u0, P, v * 3); this._at(k, u1, P, v * 3 + 3)
        const a0 = (1 - j / seg) * life * op, a1 = (1 - (j + 1) / seg) * life * op
        C.set([c[0], c[1], c[2], u0 < 0 ? 0 : a0, c[0], c[1], c[2], u1 < 0 ? 0 : a1], v * 4)
        v += 2
      }
    }
    g.attributes.position.needsUpdate = true; g.attributes.color.needsUpdate = true
  }
}

// ---------------------------------------------------------------- exhaust plume with shock diamonds

class Plume {
  /**
   * lab.plume({ parent, pos:[x,y,z], dir:'-y'|'+x'..., radius (exit, m), length (m), color:'rocket'|'jet'|'methalox', shocks: 6 })
   *   p.power = 0..1 (throttle), p.shocks = spacing in exit diameters, p.hot = 0..1
   */
  constructor(lab, o) {
    this.lab = lab
    const R = o.radius, L = o.length
    const geo = new THREE.CylinderGeometry(1, 1, 1, 64, 64, true).translate(0, -0.5, 0)
    this.u = { uT: { value: 0 }, uP: { value: 1 }, uShock: { value: o.shocks ?? 1.4 }, uKind: { value: o.color === 'jet' ? 1 : 0 }, uR: { value: R }, uL: { value: L }, uPaper: { value: lab.theme === 'paper' ? 1 : 0 }, uTint: { value: new THREE.Color(1, 1, 1) }, uSpread: { value: o.spread ?? 1 } }
    const m = new THREE.ShaderMaterial({
      uniforms: this.u, transparent: true, depthWrite: false, blending: lab.theme === 'paper' ? THREE.NormalBlending : THREE.AdditiveBlending, side: THREE.DoubleSide,
      vertexShader: `uniform float uR, uL, uP, uSpread; varying vec3 vP; varying vec3 vN; varying vec3 vV;
        void main(){ vec3 p = position; float y = -p.y; // 0 at exit, 1 at the tail
          float r = uR * (1.0 + y * (0.35 + 1.4 * y) * mix(0.6, 1.0, uP) * uSpread) ; p.xz *= r; p.y = -y * uL * mix(0.35, 1.0, uP);
          vP = vec3(p.x / uR, y, p.z / uR); vec4 mv = modelViewMatrix * vec4(p, 1.0); vN = normalize(normalMatrix * vec3(p.x, 0.0, p.z)); vV = -mv.xyz; gl_Position = projectionMatrix * mv; }`,
      fragmentShader: `uniform float uT, uP, uShock, uKind, uPaper; uniform vec3 uTint; varying vec3 vP; varying vec3 vN; varying vec3 vV;
        float h(vec3 p){ return fract(sin(dot(p, vec3(127.1, 311.7, 74.7))) * 43758.5453); }
        float n3(vec3 p){ vec3 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
          return mix(mix(mix(h(i), h(i + vec3(1,0,0)), f.x), mix(h(i + vec3(0,1,0)), h(i + vec3(1,1,0)), f.x), f.y), mix(mix(h(i + vec3(0,0,1)), h(i + vec3(1,0,1)), f.x), mix(h(i + vec3(0,1,1)), h(i + vec3(1,1,1)), f.x), f.y), f.z); }
        void main(){ float y = vP.y; float f = abs(dot(normalize(vN), normalize(vV)));
          float core = pow(f, 1.6);
          float turb = n3(vec3(vP.x * 3.0, y * 9.0 - uT * 14.0, vP.z * 3.0)) * 0.6 + n3(vec3(vP.x * 7.0, y * 22.0 - uT * 30.0, vP.z * 7.0)) * 0.4;
          float diam = 0.5 + 0.5 * cos(y * 6.2831 * uShock * 2.2);
          float shock = pow(diam, 6.0) * smoothstep(0.75, 0.05, y) * core;
          float fade = smoothstep(1.0, 0.25, y) * smoothstep(0.0, 0.02, y);
          vec3 a = uKind > 0.5 ? vec3(0.55, 0.65, 1.0) : vec3(0.35, 0.45, 1.0);
          vec3 b = uKind > 0.5 ? vec3(1.0, 0.55, 0.25) : vec3(1.0, 0.45, 0.2);
          vec3 c = mix(a, b, smoothstep(0.05, 0.6, y)) * (0.35 + 0.9 * turb) * core * fade;
          c += vec3(1.0, 0.85, 0.65) * shock * 2.4 * (uKind > 0.5 ? 0.2 : 1.0);
          c *= uP * uTint;
          // on paper: normal blending, alpha from the light the gas emits, an HDR core that tone maps to white hot
          float al = clamp(max(c.r, max(c.g, c.b)) * 0.9, 0.0, 0.92);
          gl_FragColor = uPaper > 0.5 ? vec4(c * 1.8 / max(al, 0.12), al) : vec4(c, 1.0); }`,
    })
    const mesh = new THREE.Mesh(geo, m); mesh.layers.set(LAYER_FX); mesh.renderOrder = 4; mesh.frustumCulled = false
    const grp = new THREE.Group(); grp.add(mesh)
    if (o.pos) grp.position.set(...o.pos)
    const dir = { '-y': [0, 0, 0], '+y': [Math.PI, 0, 0], '+x': [0, 0, Math.PI / 2], '-x': [0, 0, -Math.PI / 2], '+z': [-Math.PI / 2, 0, 0], '-z': [Math.PI / 2, 0, 0] }[o.dir ?? '-y']
    grp.rotation.set(...dir)
    ;(o.parent ?? lab.machine).add(grp)
    this.group = grp; this.mesh = mesh
    this.power = 1
    lab.onTick((dt) => { this.u.uT.value += dt; this.u.uP.value = this.power; mesh.visible = this.power > 0.01 })
  }
  set shocks(v) { this.u.uShock.value = v }
  set tint(c) { this.u.uTint.value.setRGB(c[0], c[1], c[2]) }
}

// ---------------------------------------------------------------- global handle for pages that paste the kit inline
const LabKit = { THREE, Lab, MAT, mat, setCaps, GEO, heatGlow, blackbody, clamp, lerp, smoothstep, ease, approach, table, rk4, fmt, rng, LAYER_FX }
if (typeof window !== 'undefined') window.LabKit = LabKit
export default LabKit
