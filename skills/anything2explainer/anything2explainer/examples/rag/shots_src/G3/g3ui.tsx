import React from 'react';
import {FONT_HEAVY, clamp01, rnd} from '../../common';
import {Box, Pill, CText, DocIcon, WHITE, GREY, GREY_LIGHT, PURPLE, PURPLE_LIGHT, ORANGE, abs} from '../../ui';

/** G3 组内补充图元（不改 ui.tsx）：左对齐文字、解析用文档卡（可切块）、四种文件图标、翻开的书、半圆刻度盘、放大镜。全部纯函数、绝对定位。 */

// ---- 工具 ----
const hex2rgb = (h: string) => [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)];
/** 两个 hex 颜色按 k 线性混合 → rgb() 字串（灰→紫 11 帧变色用） */
export const mixColor = (a: string, b: string, k: number) => {
  const A = hex2rgb(a), B = hex2rgb(b), t = clamp01(k);
  return `rgb(${A.map((v, i) => Math.round(v + (B[i] - v) * t)).join(',')})`;
};
/** 紫柔光随 k 增强 */
export const purpleGlow = (k: number) => (k <= 0 ? undefined : `0 0 24px 8px rgba(102,45,248,${(0.6 * clamp01(k)).toFixed(3)})`);

/** 左对齐单行文字（y 为行盒顶） */
export const LText: React.FC<{x: number; y: number; size: number; weight?: number; color?: string; family?: string; opacity?: number; letterSpacing?: number; style?: React.CSSProperties; children: React.ReactNode}> = ({x, y, size, weight = 700, color = WHITE, family = FONT_HEAVY, opacity = 1, letterSpacing = 0, style, children}) => (
  <div style={{position: 'absolute', left: x, top: y, fontFamily: family, fontWeight: weight, fontSize: size, lineHeight: 1, color, opacity, letterSpacing, whiteSpace: 'nowrap', ...style}}>{children}</div>
);
/** 细横条（文本占位线） */
export const Bar: React.FC<{x: number; y: number; w: number; h?: number; color?: string; opacity?: number}> = ({x, y, w, h = 3, color = GREY_LIGHT, opacity = 0.9}) => <div style={{...abs(x, y, w, h), background: color, opacity}} />;

// ---- 解析用文档卡（SC12 → SC13 共用同一份几何，保证组界不跳变）----
export const DOC_W = 360, DOC_H = 360, DOC_SEG_H = 90, DOC_SEGS = 4;
export const DOC_ITEMS = 13; // 逐行 wipe 的条目数
/** 文档内容（局部坐标，0..360）：标题文字 + 7 段落线 + 小标题条 + 3 段落线 + 3×3 表格。reveal = 已显示条目数（0..13） */
const DocContent: React.FC<{reveal: number}> = ({reveal}) => {
  const paraW = [0.78, 0.7, 0.76, 0.62, 0.74, 0.68, 0.45];
  const paraW2 = [0.72, 0.66, 0.4];
  return (
    <>
      {reveal > 0 ? <LText x={24} y={16} size={22} weight={800}>第 3 章 差旅报销</LText> : null}
      {paraW.map((k, i) => (reveal > i + 1 ? <Bar key={`p${i}`} x={24} y={76 + i * 18} w={k * 312} /> : null))}
      {reveal > 8 ? <Bar x={24} y={212} w={150} h={5} color={WHITE} opacity={1} /> : null}
      {paraW2.map((k, i) => (reveal > i + 9 ? <Bar key={`q${i}`} x={24} y={232 + i * 16} w={k * 312} /> : null))}
      {reveal > 12 ? (
        <div style={{...abs(24, 284, 220, 66), boxSizing: 'border-box', border: `1.5px solid rgba(255,255,255,.85)`}}>
          <div style={{...abs(0, 21, 217, 1.5), background: 'rgba(255,255,255,.85)'}} />
          <div style={{...abs(0, 43, 217, 1.5), background: 'rgba(255,255,255,.85)'}} />
          <div style={{...abs(72, 0, 1.5, 63), background: 'rgba(255,255,255,.85)'}} />
          <div style={{...abs(145, 0, 1.5, 63), background: 'rgba(255,255,255,.85)'}} />
        </div>
      ) : null}
    </>
  );
};
export type DocCardProps = {
  cx: number; cy: number; s?: number; opacity?: number;
  reveal?: number; // 0..13
  labels?: number[]; // 「标题/段落/表格」三枚紫标签的 opacity
  cuts?: number[]; // 三条切割线 draw-on 进度 0..1
  cutOp?: number;
  split?: boolean; gap?: number; // 切块后分离：四段 + 间距（局部 px）
  activeK?: number[]; // 每段 白→紫 边框进度
  tagOp?: number[]; // 每段右上「chunk」标签 opacity
};
/** 解析产物文档卡：黑底白边 r8 sw2（与 ChunkCard 同款），中心 (cx,cy) 以 s 等比缩放 */
export const DocCard: React.FC<DocCardProps> = ({cx, cy, s = 1, opacity = 1, reveal = DOC_ITEMS, labels, cuts, cutOp = 1, split = false, gap = 0, activeK, tagOp}) => {
  const cutStyle = (p: number): React.CSSProperties => ({height: 2, width: DOC_W * clamp01(p), left: 0, position: 'absolute', background: `repeating-linear-gradient(90deg, ${PURPLE_LIGHT} 0 9px, transparent 9px 16px)`});
  return (
    <div style={{...abs(cx - DOC_W / 2, cy - DOC_H / 2, DOC_W, DOC_H), transform: s === 1 ? undefined : `scale(${s.toFixed(4)})`, opacity}}>
      {!split ? (
        <Box x={0} y={0} w={DOC_W} h={DOC_H} r={8} sw={2}>
          <DocContent reveal={reveal} />
          {labels
            ? [
                {t: '标题', y: 6, a: 14, b: 44},
                {t: '段落', y: 118, a: 72, b: 192},
                {t: '表格', y: 302, a: 280, b: 350},
              ].map((l, i) =>
                labels[i] > 0 ? (
                  <div key={l.t} style={{opacity: labels[i]}}>
                    <div style={{...abs(284, l.a, 2, l.b - l.a), background: PURPLE_LIGHT}} />
                    <Pill x={292} y={l.y} w={62} h={28} fill={PURPLE} sw={0} text={l.t} fontSize={22} weight={700} textDy={-1} />
                  </div>
                ) : null,
              )
            : null}
        </Box>
      ) : (
        Array.from({length: DOC_SEGS}, (_, i) => {
          const k = activeK?.[i] ?? 0;
          const top = i * (DOC_SEG_H + gap) - 1.5 * gap;
          return (
            <Box key={i} x={0} y={top} w={DOC_W} h={DOC_SEG_H} r={8} sw={2} stroke={mixColor(WHITE, PURPLE_LIGHT, k)} glow={purpleGlow(k)} style={{overflow: 'hidden'}}>
              <div style={{position: 'absolute', left: 0, top: -i * DOC_SEG_H, width: DOC_W, height: DOC_H}}>
                <DocContent reveal={reveal} />
              </div>
              {tagOp && tagOp[i] > 0 ? (
                <CText cx={314} cy={16} size={22} weight={700} color={WHITE} italic family="'Exo 2 Rag', 'Exo 2 R2', sans-serif" scaleX={0.85} opacity={tagOp[i]} dy={0} shadow="0 0 6px rgba(80,30,200,.7)">
                  chunk
                </CText>
              ) : null}
            </Box>
          );
        })
      )}
      {cuts && !split ? cuts.map((p, k) => (p > 0 ? <div key={k} style={{...cutStyle(p), top: DOC_SEG_H * (k + 1) - 1, opacity: cutOp}} /> : null)) : null}
    </div>
  );
};

// ---- 文件图标（SC12 左列，外框 70×76，(x,y) 为左上）----
const DOT = ['#F3A634', '#508DF7', '#E83E2F'];
export const PdfIcon: React.FC<{x: number; y: number; opacity?: number}> = ({x, y, opacity = 1}) => (
  <div style={{...abs(x, y, 70, 76), opacity}}>
    <DocIcon x={5} y={0} w={60} h={76} lines={4} accent={ORANGE} />
    <Box x={38} y={50} w={22} h={16} r={3} fill={ORANGE} sw={0} />
  </div>
);
export const WebIcon: React.FC<{x: number; y: number; opacity?: number}> = ({x, y, opacity = 1}) => (
  <div style={{...abs(x, y, 70, 76), opacity}}>
    <Box x={0} y={10} w={70} h={56} r={6} sw={2}>
      {DOT.map((c, i) => <div key={c} style={{...abs(8 + i * 11, 6, 6, 6), borderRadius: 3, background: c}} />)}
      <div style={{...abs(0, 17, 66, 1.5), background: 'rgba(255,255,255,.7)'}} />
      <Bar x={9} y={27} w={40} />
      <Bar x={9} y={37} w={28} />
    </Box>
  </div>
);
export const TableIcon: React.FC<{x: number; y: number; opacity?: number}> = ({x, y, opacity = 1}) => (
  <div style={{...abs(x, y, 70, 76), opacity}}>
    <Box x={2} y={10} w={66} h={56} r={4} sw={2}>
      {[20.7, 41.3].map((yy) => <div key={yy} style={{...abs(0, yy, 62, 1.5), background: 'rgba(255,255,255,.85)'}} />)}
      {[20.7, 41.3].map((xx) => <div key={xx} style={{...abs(xx, 0, 1.5, 52), background: 'rgba(255,255,255,.85)'}} />)}
      <Bar x={4} y={7} w={12} h={4} />
      <Bar x={25} y={7} w={12} h={4} />
    </Box>
  </div>
);
export const ScanIcon: React.FC<{x: number; y: number; opacity?: number}> = ({x, y, opacity = 1}) => (
  <div style={{...abs(x, y, 70, 76), opacity, transform: 'rotate(-7deg)'}}>
    <Box x={6} y={0} w={58} h={76} r={3} sw={2} dashed>
      <Bar x={10} y={16} w={34} color={GREY} />
      <Bar x={10} y={28} w={28} color={GREY} />
      <Bar x={10} y={40} w={32} color={GREY} />
      <Bar x={10} y={52} w={18} color={GREY} />
      {Array.from({length: 12}, (_, i) => <div key={i} style={{...abs(4 + rnd(31, i) * 48, 4 + rnd(32, i) * 64, 2, 2), background: GREY_LIGHT, opacity: 0.8}} />)}
    </Box>
  </div>
);

// ---- 翻开的书（SC11）：中心 (cx,cy)，宽 ≈260 高 ≈150；lineColor 控制页内文字线颜色（灰白→紫）----
export const BookIcon: React.FC<{cx: number; cy: number; lineColor?: string; opacity?: number}> = ({cx, cy, lineColor = GREY_LIGHT, opacity = 1}) => (
  <svg width={1280} height={720} viewBox="0 0 1280 720" style={{position: 'absolute', left: 0, top: 0, overflow: 'visible', opacity, filter: 'drop-shadow(0 0 3px rgba(255,255,255,0.45))'}}>
    <path d={`M${cx - 4},${cy - 50} Q${cx - 68},${cy - 76} ${cx - 128},${cy - 60} L${cx - 128},${cy + 58} Q${cx - 68},${cy + 42} ${cx - 4},${cy + 68} Z`} fill="#000" stroke={WHITE} strokeWidth={2.5} strokeLinejoin="round" />
    <path d={`M${cx + 4},${cy - 50} Q${cx + 68},${cy - 76} ${cx + 128},${cy - 60} L${cx + 128},${cy + 58} Q${cx + 68},${cy + 42} ${cx + 4},${cy + 68} Z`} fill="#000" stroke={WHITE} strokeWidth={2.5} strokeLinejoin="round" />
    <path d={`M${cx - 4},${cy + 68} L${cx},${cy + 76} L${cx + 4},${cy + 68}`} fill="none" stroke={WHITE} strokeWidth={2.5} strokeLinejoin="round" />
    {[0, 1, 2, 3].map((i) => (
      <g key={i} stroke={lineColor} strokeWidth={3} strokeLinecap="round">
        <line x1={cx - 108} y1={cy - 30 + i * 22} x2={cx - 24 - (i === 3 ? 30 : 0)} y2={cy - 24 + i * 22 + (i === 3 ? -2 : 0)} />
        <line x1={cx + 24} y1={cy - 24 + i * 22} x2={cx + 108 - (i === 3 ? 34 : 0)} y2={cy - 30 + i * 22 + (i === 3 ? 2 : 0)} />
      </g>
    ))}
  </svg>
);

// ---- 半圆刻度盘（SC11）：p 弧线 draw-on 进度；v 指针位置 0..1（0 = 左，1 = 右）----
export const Dial: React.FC<{cx: number; cy: number; r?: number; p?: number; v?: number; opacity?: number}> = ({cx, cy, r = 80, p = 1, v = 0, opacity = 1}) => {
  const L = Math.PI * r;
  const th = Math.PI - Math.PI * clamp01(v);
  const nx = cx + (r - 18) * Math.cos(th), ny = cy - (r - 18) * Math.sin(th);
  return (
    <svg width={1280} height={720} viewBox="0 0 1280 720" style={{position: 'absolute', left: 0, top: 0, overflow: 'visible', opacity: p <= 0 ? 0 : opacity, filter: 'drop-shadow(0 0 3px rgba(255,255,255,0.45))'}}>
      <path d={`M${cx - r},${cy} A${r},${r} 0 0 1 ${cx + r},${cy}`} fill="none" stroke={WHITE} strokeWidth={4} strokeLinecap="round" strokeDasharray={L} strokeDashoffset={L * (1 - clamp01(p))} opacity={p > 0 ? 1 : 0} />
      {Array.from({length: 11}, (_, k) => {
        const a = Math.PI - (Math.PI * k) / 10;
        const big = k % 5 === 0;
        const r0 = r - (big ? 18 : 11);
        const show = p > 0 && clamp01(p) * 10 >= k - 0.01; // p=0 时 k=0 刻度也不画（QC v1：残留短横）
        return show ? <line key={k} x1={cx + r0 * Math.cos(a)} y1={cy - r0 * Math.sin(a)} x2={cx + (r - 3) * Math.cos(a)} y2={cy - (r - 3) * Math.sin(a)} stroke={WHITE} strokeWidth={big ? 3 : 2} opacity={0.9} /> : null;
      })}
      <line x1={cx - 4} y1={cy} x2={cx + r + 4} y2={cy} stroke={WHITE} strokeWidth={2} opacity={0.5 * clamp01(p)} />
      <line x1={cx} y1={cy} x2={nx} y2={ny} stroke={ORANGE} strokeWidth={4.5} strokeLinecap="round" opacity={p > 0.6 ? 1 : 0} />
      <circle cx={cx} cy={cy} r={7} fill={WHITE} opacity={p > 0.6 ? 1 : 0} />
    </svg>
  );
};

// ---- 放大镜 + 灰问号（SC14 左栏）----
export const Magnifier: React.FC<{cx: number; cy: number; s?: number; opacity?: number}> = ({cx, cy, s = 1, opacity = 1}) => (
  <div style={{...abs(cx - 60, cy - 60, 120, 120), opacity, transform: s === 1 ? undefined : `scale(${s.toFixed(4)})`}}>
    <svg width={120} height={120} viewBox="0 0 120 120" style={{position: 'absolute', left: 0, top: 0, overflow: 'visible', filter: 'drop-shadow(0 0 3px rgba(255,255,255,0.45))'}}>
      <circle cx={52} cy={52} r={32} fill="rgba(0,0,0,.7)" stroke={WHITE} strokeWidth={3} />
      <line x1={75} y1={75} x2={104} y2={104} stroke={WHITE} strokeWidth={7} strokeLinecap="round" />
    </svg>
    <CText cx={52} cy={53} size={40} weight={900} color={GREY} dy={-2}>?</CText>
  </div>
);
