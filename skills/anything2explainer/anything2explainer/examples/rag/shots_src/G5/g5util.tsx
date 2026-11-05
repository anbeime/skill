import React from 'react';
import {clamp01, easeInOutPow} from '../../common';
import {WHITE} from '../../ui';

/** G5 组内小工具（不改 ui.tsx；可迁入 ui.tsx 的项写在 BUILD_NOTES）。 */

/** 十六进制颜色线性混合 k∈[0,1] → rgb() 字串 */
export const mixHex = (a: string, b: string, k: number) => {
  const p = (h: string) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
  const [r1, g1, b1] = p(a), [r2, g2, b2] = p(b);
  const t = clamp01(k);
  return `rgb(${Math.round(r1 + (r2 - r1) * t)},${Math.round(g1 + (g2 - g1) * t)},${Math.round(b1 + (b2 - b1) * t)})`;
};
/** 灰→紫 11 帧变色曲线（STYLE_GUIDE MIX） */
const MIX = [0, 0.1, 0.18, 0.3, 0.37, 0.47, 0.55, 0.63, 0.71, 0.83, 0.88, 0.98, 1];
export const mixK = (n: number) => (n < 0 ? 0 : n >= MIX.length ? 1 : MIX[n]);
/** 高亮块左锚展宽 21 帧曲线（R3 HL_W） */
const HLW = [0.05, 0.14, 0.21, 0.31, 0.41, 0.5, 0.56, 0.65, 0.7, 0.75, 0.81, 0.85, 0.88, 0.9, 0.93, 0.95, 0.97, 0.98, 0.985, 0.99, 1];
export const hlW = (n: number) => (n < 0 ? 0 : n >= HLW.length ? 1 : HLW[n]);

/** 二次贝塞尔点 */
export const bez2 = (p0: [number, number], c: [number, number], p1: [number, number], t: number): [number, number] => {
  const u = 1 - t;
  return [u * u * p0[0] + 2 * u * t * c[0] + t * t * p1[0], u * u * p0[1] + 2 * u * t * c[1] + t * t * p1[1]];
};
export const inOut = easeInOutPow(2.5);

/** SVG 直线 draw-on（stroke-dasharray）：p 0→1 自 (x0,y0) 端长出 */
export const DrawLine: React.FC<{x0: number; y0: number; x1: number; y1: number; p?: number; w?: number; color?: string; dashed?: boolean; opacity?: number}> = ({x0, y0, x1, y1, p = 1, w = 2, color = WHITE, dashed = false, opacity = 1}) => {
  if (p <= 0) return null;
  const L = Math.hypot(x1 - x0, y1 - y0);
  const q = clamp01(p);
  if (dashed) {
    // 虚线：用 clipPath 不方便，改为按进度截断端点
    return <line x1={x0} y1={y0} x2={x0 + (x1 - x0) * q} y2={y0 + (y1 - y0) * q} stroke={color} strokeWidth={w} strokeDasharray="8 7" opacity={opacity} />;
  }
  return <line x1={x0} y1={y0} x2={x1} y2={y1} stroke={color} strokeWidth={w} strokeDasharray={L} strokeDashoffset={L * (1 - q)} opacity={opacity} strokeLinecap="butt" />;
};
/** SVG 圆 draw-on（从顶点顺时针画出） */
export const DrawCircle: React.FC<{cx: number; cy: number; r: number; p?: number; w?: number; color?: string; opacity?: number; dashed?: boolean}> = ({cx, cy, r, p = 1, w = 2, color = WHITE, opacity = 1, dashed = false}) => {
  if (p <= 0) return null;
  const C = 2 * Math.PI * r;
  return <circle cx={cx} cy={cy} r={r} fill="none" stroke={color} strokeWidth={w} strokeDasharray={dashed ? `${C * clamp01(p)} ${C}` : C} strokeDashoffset={dashed ? 0 : C * (1 - clamp01(p))} transform={`rotate(-90 ${cx} ${cy})`} opacity={opacity} />;
};
/** 以中心为锚的缩放/位移包裹（div），用于 scaleIn / emphasisPulse */
export const Anchor: React.FC<{cx: number; cy: number; s?: number; dx?: number; dy?: number; opacity?: number; children: React.ReactNode; style?: React.CSSProperties}> = ({cx, cy, s = 1, dx = 0, dy = 0, opacity = 1, children, style}) => (
  <div style={{position: 'absolute', left: 0, top: 0, width: 1280, height: 720, transformOrigin: '0 0', transform: `translate(${dx.toFixed(2)}px,${dy.toFixed(2)}px) translate(${cx}px,${cy}px) scale(${s.toFixed(4)}) translate(${-cx}px,${-cy}px)`, opacity, pointerEvents: 'none', ...style}}>
    {children}
  </div>
);
