import React from 'react';
import {rnd, clamp01, BEZ_SCALE_IN, easeOutCubic} from '../../common';
import {GREY_LINE, GREY_LIGHT} from '../../ui';

/**
 * 向量空间 2D 平面（SC17 / SC23 共用，分布必须一致）。
 * ⚠ G4 开工时 SC17.tsx 尚不存在，此处按分镜表参数实现；若 G4 另有 VSPACE，请主会话统一为一份（建议以本文件为准，G4 import 之）。
 * 网格：#4A4A4A 1px，x 240–1040（步 40），y 190–600（步 41）。灰点 40 个 rnd(seed=17) 均匀散布，
 * 中心 (620,390) 半径 110 内不落灰点（留给 SC17 的两枚紫点 (600,380)/(650,400) 与 SC23 的查询点）；
 * 另有 3 枚"近邻"点 VNEIGHBORS（SC17 里也应画成灰点，SC23 中变紫）。
 */
export const VSPACE = {x0: 240, x1: 1040, y0: 190, y1: 600, stepX: 40, stepY: 41, seed: 17, count: 40, hole: {cx: 620, cy: 390, r: 110}, margin: 18};
export const VNEIGHBORS: Array<[number, number]> = [[572, 338], [690, 420], [580, 452]];

export type VPoint = {x: number; y: number; order: number};
const genGrey = (): VPoint[] => {
  const {x0, x1, y0, y1, seed, count, hole, margin} = VSPACE;
  const pts: VPoint[] = [];
  let i = 0, tries = 0;
  while (pts.length < count && tries < count * 20) {
    tries++;
    const x = x0 + margin + rnd(seed, tries, 1) * (x1 - x0 - 2 * margin);
    const y = y0 + margin + rnd(seed, tries, 2) * (y1 - y0 - 2 * margin);
    if (Math.hypot(x - hole.cx, y - hole.cy) < hole.r) continue;
    // 与已有点保持 ≥ 26px
    if (pts.some((p) => Math.hypot(p.x - x, p.y - y) < 26)) continue;
    pts.push({x: Math.round(x), y: Math.round(y), order: i++});
  }
  // 亮起顺序打乱（1 帧错峰）
  const ord = pts.map((_, k) => k).sort((a, b) => rnd(seed, a, 3) - rnd(seed, b, 3));
  ord.forEach((k, o) => (pts[k].order = o));
  return pts;
};
export const VGREY: VPoint[] = genGrey();

/** 网格 + 灰点。f0 = 网格 wipe 起始帧（18 帧自左向右揭示）；ptsFrom = 灰点开始逐帧亮起的帧；extra = 额外灰点（如 VNEIGHBORS），随灰点一起亮。 */
export const VectorPlane: React.FC<{N: number; f0: number; ptsFrom: number; extra?: Array<[number, number]>; opacity?: number; children?: React.ReactNode}> = ({N, f0, ptsFrom, extra = [], opacity = 1, children}) => {
  const {x0, x1, y0, y1, stepX, stepY} = VSPACE;
  const wipe = easeOutCubic(clamp01((N - f0) / 18));
  const wx = (x1 - x0 + 4) * wipe;
  const cols: number[] = [];
  for (let x = x0; x <= x1 + 0.1; x += stepX) cols.push(x + 0.5);
  const rows: number[] = [];
  for (let y = y0; y <= y1 + 0.1; y += stepY) rows.push(y + 0.5);
  const all: Array<{x: number; y: number; t0: number}> = [
    ...VGREY.map((p) => ({x: p.x, y: p.y, t0: ptsFrom + p.order})),
    ...extra.map(([x, y], i) => ({x, y, t0: ptsFrom + 6 + i * 9})),
  ];
  return (
    <svg width={1280} height={720} viewBox="0 0 1280 720" style={{position: 'absolute', left: 0, top: 0, opacity}}>
      <defs>
        <clipPath id="g5-vplane-clip"><rect x={x0 - 2} y={y0 - 2} width={Math.max(0, wx)} height={y1 - y0 + 4} /></clipPath>
      </defs>
      <g clipPath="url(#g5-vplane-clip)" stroke={GREY_LINE} strokeWidth={1}>
        {cols.map((x) => <line key={`c${x}`} x1={x} y1={y0} x2={x} y2={y1} />)}
        {rows.map((y) => <line key={`r${y}`} x1={x0} y1={y} x2={x1} y2={y} />)}
        <rect x={x0 + 0.5} y={y0 + 0.5} width={x1 - x0} height={y1 - y0} fill="none" stroke="#6A6A6A" strokeWidth={1.5} />
      </g>
      {all.map((p, i) => {
        const n = N - p.t0;
        if (n < 0) return null;
        const s = BEZ_SCALE_IN(clamp01(n / 8));
        return <circle key={i} cx={p.x} cy={p.y} r={4.2 * s} fill={GREY_LIGHT} opacity={0.85} />;
      })}
      {children}
    </svg>
  );
};
