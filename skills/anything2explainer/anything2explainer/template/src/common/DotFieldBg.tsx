import React, {useLayoutEffect, useRef} from 'react';
import {useCurrentFrame, useVideoConfig} from 'remotion';
import type {BgSpec} from './types';

/**
 * 幕底方案二「点阵波」：video-talkcraft `template/motion-systems/backdrop.tsx` 的 dot-field-wave 移植版。
 * `src/config.ts` 的 `bg: 'dots'` 时由 Main 挂载，替换方案一的 雾底 Fog + 星点 StarField（两者不叠加）。
 * - 逐帧确定性：t = frame / fps × speed（talkcraft 默认 speed 1.5），斜向波前每 14 s 扫过一遍（÷speed ≈ 9.3 s）。
 * - 设计坐标 960×540 等比放大覆盖 1280×720：点距 36 → 屏幕 48px，半径 1.5–2 → 2–2.7px；底色 #0b0c11，点色 #cfe0ff，
 *   透明度 (0.2 + 0.6k²)·径向边缘衰减，k 为到波前的归一化距离；叠一层静态噪点（overlay .06）抗色带。
 * - 沿用 BgSpec：区间内 `stars:'none'` → 整层不画，回到纯黑（片头前 10 帧 / 片尾 40 帧与星点方案一致）；`fog` 字段在本方案下无效。
 * - 点阵是屏幕空间的静态纹理，不跟随任何镜头运镜；scripts/frame_metrics.py 会按同一套网格坐标把它从统计里抠掉（`bg` 自动读 config）。
 */
const DW = 960, DH = 540;
export const DOT_STEP = 36, DOT_X0 = 24, DOT_Y0 = 18; // 设计坐标网格（frame_metrics.py 用同一组常量还原屏幕坐标）
const GRAIN_URL =
  "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='160' height='160'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 .5 0'/></filter><rect width='160' height='160' filter='url(%23n)'/></svg>\")";

const drawDots = (ctx: CanvasRenderingContext2D, t: number) => {
  ctx.fillStyle = '#0b0c11';
  ctx.fillRect(-DW, -DH, DW * 3, DH * 3);
  const phase = ((t % 14) / 14) * 1700 - 300;
  for (let y = DOT_Y0; y < DH; y += DOT_STEP) {
    for (let x = DOT_X0; x < DW; x += DOT_STEP) {
      const d = Math.abs(x + y * 0.6 - phase);
      const k = Math.max(0, 1 - d / 280);
      const kk = k * k;
      const edge = Math.min(1, Math.max(0, 1.25 - Math.hypot((x - 480) / 560, (y - 270) / 360)));
      ctx.globalAlpha = (0.2 + 0.6 * kk) * edge;
      ctx.fillStyle = '#cfe0ff';
      ctx.beginPath();
      ctx.arc(x, y, 1.5 + 0.5 * kk, 0, 6.283);
      ctx.fill();
    }
  }
  ctx.globalAlpha = 1;
};

const DotCanvas: React.FC<{t: number}> = ({t}) => {
  const {width, height} = useVideoConfig();
  const ref = useRef<HTMLCanvasElement>(null);
  useLayoutEffect(() => {
    const c = ref.current;
    if (!c) return;
    const ctx = c.getContext('2d');
    if (!ctx) return;
    const s = Math.max(width / DW, height / DH);
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, width, height);
    ctx.setTransform(s, 0, 0, s, (width - DW * s) / 2, (height - DH * s) / 2);
    drawDots(ctx, t);
  }, [t, width, height]);
  return <canvas ref={ref} width={width} height={height} style={{position: 'absolute', inset: 0, width: '100%', height: '100%'}} />;
};

export const DotFieldBg: React.FC<{specs: BgSpec[]; speed?: number; grain?: boolean}> = ({specs, speed = 1.5, grain = true}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const N = frame + 1;
  let show = true;
  for (const s of specs) {
    if (N >= s.from && N <= s.to && s.stars === 'none') show = false;
  }
  if (!show) return null;
  const t = (frame / fps) * speed;
  return (
    <div style={{position: 'absolute', inset: 0, overflow: 'hidden', background: '#0b0b0f'}}>
      <DotCanvas t={t} />
      {grain ? <div style={{position: 'absolute', inset: 0, backgroundImage: GRAIN_URL, backgroundSize: '160px 160px', opacity: 0.06, mixBlendMode: 'overlay', pointerEvents: 'none'}} /> : null}
    </div>
  );
};
