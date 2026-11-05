import React from 'react';
import {useCurrentFrame} from 'remotion';
import {rnd} from './easing';
import type {BgSpec} from './types';
import {Fog, FOG_DEFAULT_ON} from './Fog';

/**
 * 背景星点粒子层（确定性：位置/速度/寿命全由 (seed, 星号, 周期号) 决定，逐帧只算纯函数，不重掷）。
 * 实测（verify_seg_06/07/08 blob 追踪）：全帧约 45 颗（thr40；MD 目测 60）、漂移 |v| 0.4–3.2 px/帧（均值 1.7）方向随机、
 * 亮度 40–250 逐帧闪烁（同颗 77→86→87→111→92→104→54→71）、1–3px 核 + 软边、寿命 ≥60 帧；
 * seg_23：同帧可见 6–25 颗、寿命 10–30 帧、先 4–6 帧升到峰值再缓落、有批量刷新；seg_24：多数向左 (−1.5…−4.5, −1.5…+3) px/帧、按大小分层视差。
 * 三种 variant：'drift'（默认，随机方向 0.4–3.2）/ 'fast'（seg_24 向左 1.5–4.5 视差）/ 'still'（不动只闪）/ 'none'。
 */
export type StarVariant = 'drift' | 'fast' | 'still' | 'none';
export type StarFieldProps = {
  variant: StarVariant;
  count: number; // 同时存在的粒子数（默认 45）
  speed: number; // 速度倍率（1 = 实测分布）
  lifetime: [number, number]; // 寿命区间（帧）
  twinkle: number; // 逐帧亮度抖动幅度（0.3 = ±30%）
  size: [number, number]; // 核直径 px
  brightness: [number, number]; // 峰值亮度 0–255
  seed: number;
  region: [number, number, number, number]; // 出生区域 x,y,w,h
  opacity: number;
};
// 主会话（QC v1 RQ1）：成片星点密度 ≈原片 50%、无 255 级亮星 → count 45→80、峰值上限 200→255
export const STAR_DEFAULT: StarFieldProps = {variant: 'drift', count: 80, speed: 1, lifetime: [60, 200], twinkle: 0.3, size: [2, 4], brightness: [35, 255], seed: 7, region: [0, 0, 1280, 687], opacity: 1};

type Star = {x: number; y: number; s: number; a: number};
/** 纯函数：给定帧号返回全部可见星点（供 Canvas/测试复用）。 */
export const starsAt = (frame: number, p: StarFieldProps): Star[] => {
  if (p.variant === 'none') return [];
  const out: Star[] = [];
  const [rx, ry, rw, rh] = p.region;
  for (let i = 0; i < p.count; i++) {
    const L = Math.round(p.lifetime[0] + (p.lifetime[1] - p.lifetime[0]) * rnd(p.seed, i, 1));
    const phase = Math.floor(rnd(p.seed, i, 2) * L);
    const tt = frame + phase;
    const cyc = Math.floor(tt / L);
    const age = tt - cyc * L;
    // 每个周期重新生成出生点/速度/大小/峰值亮度
    const x0 = rx + rnd(p.seed, i, cyc, 3) * rw;
    const y0 = ry + rnd(p.seed, i, cyc, 4) * rh;
    const size = p.size[0] + (p.size[1] - p.size[0]) * rnd(p.seed, i, cyc, 5);
    const peak = p.brightness[0] + (p.brightness[1] - p.brightness[0]) * Math.pow(rnd(p.seed, i, cyc, 6), 2); // 偏暗分布：f13060 实测 10 颗峰值 7 颗在 35–90
    let vx = 0, vy = 0;
    if (p.variant === 'drift') {
      const ang = rnd(p.seed, i, cyc, 7) * Math.PI * 2;
      const sp = 0.4 * Math.pow(3.2 / 0.4, rnd(p.seed, i, cyc, 8)); // 对数均匀 0.4–3.2，均值≈1.3–1.7
      vx = Math.cos(ang) * sp * p.speed;
      vy = Math.sin(ang) * sp * p.speed;
    } else if (p.variant === 'fast') {
      const sn = (size - p.size[0]) / (p.size[1] - p.size[0]); // 大的更快（视差）
      vx = -(1.5 + 3.0 * (0.4 * sn + 0.6 * rnd(p.seed, i, cyc, 7))) * p.speed;
      vy = (-1.5 + 4.5 * rnd(p.seed, i, cyc, 8)) * p.speed;
    }
    const x = x0 + vx * age;
    const y = y0 + vy * age;
    if (x < -4 || x > 1284 || y < -4 || y > 724) continue;
    // 包络：前 5 帧升到峰值，最后 12 帧缓落
    const rise = Math.min(1, age / 5);
    const fall = Math.min(1, (L - age) / 12);
    const env = Math.min(rise, fall);
    // 逐帧闪烁：±twinkle 的确定性噪声（仅亮度，位置不重掷）
    const tw = 1 + p.twinkle * (rnd(p.seed, i, frame, 9) * 2 - 1);
    const a = Math.min(1, Math.max(0, (peak / 255) * env * tw)) * p.opacity;
    if (a < 0.03) continue;
    out.push({x, y, s: size, a});
  }
  return out;
};

export const StarField: React.FC<Partial<StarFieldProps> & {frame?: number}> = (props) => {
  const cur = useCurrentFrame();
  const p: StarFieldProps = {...STAR_DEFAULT, ...props};
  const frame = props.frame ?? cur;
  const stars = starsAt(frame, p);
  return (
    <div style={{position: 'absolute', inset: 0, pointerEvents: 'none'}}>
      {stars.map((s, k) => (
        <div
          key={k}
          style={{
            position: 'absolute',
            left: s.x - s.s / 2,
            top: s.y - s.s / 2,
            width: s.s,
            height: s.s,
            borderRadius: '50%',
            background: '#fff',
            opacity: s.a,
            boxShadow: `0 0 ${Math.max(2, s.s * 1.3)}px rgba(255,255,255,0.8)`, // 原片 blob 在 thr35 下面积 5–11px、峰值多在 35–90：软而暗
          }}
        />
      ))}
    </div>
  );
};

/** 背景轨：按原片帧号查 BgSpec（后者优先），渲染 雾底 + 星点。N = 原片帧号。未覆写 → 默认 drift + 雾底开。 */
export const BgTrack: React.FC<{specs: BgSpec[]; defaultStars?: Partial<StarFieldProps>; defaultFog?: boolean}> = ({specs, defaultStars, defaultFog = FOG_DEFAULT_ON}) => {
  const N = useCurrentFrame() + 1;
  let stars: Partial<StarFieldProps> = {...defaultStars};
  let fog = defaultFog;
  for (const s of specs) {
    if (N < s.from || N > s.to) continue;
    if (s.stars !== undefined) stars = typeof s.stars === 'string' ? {variant: s.stars} : {...s.stars};
    if (s.fog !== undefined) fog = s.fog;
  }
  return (
    <>
      {fog ? <Fog /> : null}
      <StarField {...stars} />
    </>
  );
};
