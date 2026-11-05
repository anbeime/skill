import React from 'react';
import {Pill, Box, CText, ArrowH, abs, PURPLE, PURPLE_LIGHT, PURPLE_TECH, GREY, WHITE, scaleIn, fadeIn} from '../../ui';
import {clamp01, easeInOutPow, easeOutCubic, FONT_HEAVY, FONT_TECH, FONT_ORB, emphasisPulse} from '../../common';

/** G7 组内共用：SC31–SC33 的迷你流水线几何、虚线框、指标 Pill、天平、离场工具。 */

// ---- 数值工具 ----
export const lerp = (a: number, b: number, k: number) => a + (b - a) * k;
export const EASE = easeInOutPow(2.5);
/** 十六进制色插值 → rgb() */
export const mixHex = (a: string, b: string, k: number) => {
  const pa = [1, 3, 5].map((i) => parseInt(a.slice(i, i + 2), 16));
  const pb = [1, 3, 5].map((i) => parseInt(b.slice(i, i + 2), 16));
  const t = clamp01(k);
  return `rgb(${pa.map((v, i) => Math.round(v + (pb[i] - v) * t)).join(',')})`;
};
/** 0→1→0 的闪一下（len 帧，正弦） */
export const flash = (n: number, len = 10) => (n < 0 || n > len ? 0 : Math.sin((Math.PI * n) / len));
/** 统一离场：幂缓入下摇 + 6.7%/帧淡出，末 6 帧线性收到 0（len 帧内结束） */
export const exitOut = (ex: number, len = 14) => {
  if (ex <= 0) return {dy: 0, op: 1};
  return {dy: 1.2 * ex * ex, op: Math.pow(0.933, ex) * (1 - clamp01((ex - (len - 6)) / 6))};
};

// ---- 迷你流水线（SC31/32/33 共用几何）----
export const PIPE = {x0: 170, w: 140, h: 56, gap: 60, cy: 380, arrowW: 48};
export const PIPE_NAMES = ['问题', '检索', '重排', '生成', '回答'];
export const pipeX = (i: number) => PIPE.x0 + i * (PIPE.w + PIPE.gap);
export const arrowX = (i: number) => pipeX(i) + PIPE.w + 6;
/** SC32 裂开后的左右位移 */
export const SPLIT_DX = 80;

/** 流水线小 Pill：黑底白边；hl 0→1 变紫 + 柔光（闪一下） */
export const PipePill: React.FC<{i: number; x: number; cy: number; h?: number; w?: number; hl?: number; opacity?: number; fontSize?: number}> = ({i, x, cy, h = PIPE.h, w = PIPE.w, hl = 0, opacity = 1, fontSize = 26}) => (
  <Pill
    x={x}
    y={cy - h / 2}
    w={w}
    h={h}
    fill={mixHex('#000000', PURPLE, hl)}
    stroke={mixHex('#FFFFFF', PURPLE_LIGHT, hl)}
    sw={2}
    text={PIPE_NAMES[i]}
    fontSize={fontSize}
    weight={700}
    textDy={-2}
    opacity={opacity}
    glow={hl > 0.02 ? `0 0 ${Math.round(24 * hl)}px ${Math.round(8 * hl)}px rgba(102,45,248,${(0.6 * hl).toFixed(3)})` : undefined}
    style={{filter: 'drop-shadow(0 0 2px rgba(255,255,255,.35))'}}
  />
);
export const PipeArrow: React.FC<{x: number; cy: number; p: number; opacity?: number}> = ({x, cy, p, opacity = 1}) => (p <= 0 || opacity <= 0 ? null : <ArrowH x={x} y={cy - 12} w={PIPE.arrowW} h={24} p={p} opacity={opacity} />);

/** 虚线框（圆角 10）：p 为沿周长顺时针 draw-on 进度（conic mask，从顶部中点起） */
export const DashFrame: React.FC<{x: number; y: number; w: number; h: number; color: string; p?: number; opacity?: number; sw?: number; tint?: string}> = ({x, y, w, h, color, p = 1, opacity = 1, sw = 2.5, tint}) => {
  if (p <= 0 || opacity <= 0) return null;
  const deg = (clamp01(p) * 360).toFixed(2);
  const mask = p < 1 ? `conic-gradient(from 0deg at 50% 50%, #000 0deg ${deg}deg, transparent ${deg}deg 360deg)` : undefined;
  // 填充与描边分层：conic mask 只作用于虚线描边，填充随 draw-on 进度线性淡入（避免露出扇形楔块）
  return (
    <>
      {tint ? <div style={{...abs(x, y, w, h), boxSizing: 'border-box', borderRadius: 10, opacity: opacity * clamp01(p), background: tint}} /> : null}
      <div style={{...abs(x, y, w, h), boxSizing: 'border-box', border: `${sw}px dashed ${color}`, borderRadius: 10, opacity, WebkitMaskImage: mask, maskImage: mask}} />
    </>
  );
};

/** 框角标签（紫 / 橙实心小胶囊） */
export const CornerTag: React.FC<{x: number; y: number; text: string; fill: string; w?: number; h?: number; opacity?: number}> = ({x, y, text, fill, w = 156, h = 40, opacity = 1}) => (
  <Pill x={x} y={y} w={w} h={h} fill={fill} stroke={WHITE} sw={2} text={text} fontSize={26} weight={700} textDy={-2} opacity={opacity} style={{filter: 'drop-shadow(0 0 2px rgba(200,180,255,.6))'}} />
);

/** 指标 Pill：英文（Exo 2 紫斜体）+ 中文（Noto 白）；dim → 灰边灰字（非重点） */
export const MetricPill: React.FC<{cx: number; cy: number; w: number; h?: number; en: string; zh?: string; opacity?: number; dim?: boolean; enSize?: number; zhSize?: number}> = ({cx, cy, w, h = 56, en, zh, opacity = 1, dim = false, enSize = 27, zhSize = 24}) => (
  <Box x={cx - w / 2} y={cy - h / 2} w={w} h={h} r={h / 2} stroke={dim ? GREY : WHITE} sw={2} opacity={opacity} style={{filter: dim ? undefined : 'drop-shadow(0 0 2px rgba(255,255,255,.3))'}}>
    <div style={{position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12, whiteSpace: 'nowrap', lineHeight: 1, transform: 'translateY(-1px)'}}>
      <span style={{display: 'inline-block', fontFamily: FONT_TECH, fontStyle: 'italic', fontWeight: 700, fontSize: enSize, letterSpacing: 1, color: dim ? GREY : PURPLE_TECH, transform: 'scaleX(0.86)', textShadow: dim ? undefined : '0 0 6px rgba(80,30,200,.7)'}}>{en}</span>
      {zh ? <span style={{fontFamily: FONT_HEAVY, fontWeight: 600, fontSize: zhSize, color: dim ? GREY : WHITE}}>{zh}</span> : null}
    </div>
  </Box>
);

/** 紫色大问号（Orbitron）：21 帧缩放入场 + 22 帧后强调脉冲 */
export const QMark: React.FC<{N: number; f0: number; cx?: number; cy?: number; opacity?: number; dy?: number}> = ({N, f0, cx = 640, cy = 220, opacity = 1, dy = 0}) => {
  const n = N - f0;
  if (n < 0) return null;
  const s = scaleIn(n) * emphasisPulse(n - 22, {peak: 1.11});
  return (
    <div style={{...abs(cx - 100, cy - 100 + dy, 200, 200), opacity: opacity * fadeIn(n, 6), transform: `scale(${s.toFixed(4)})`, transformOrigin: '50% 50%'}}>
      <CText cx={100} cy={100} size={110} weight={800} family={FONT_ORB} color={PURPLE} dy={0} shadow="0 0 26px rgba(102,45,248,.75), 0 0 6px rgba(160,120,255,.6)">
        ?
      </CText>
    </div>
  );
};

/** 顶亮底黑小球（沿用 R6 GradBall） */
export const GradBall: React.FC<{cx: number; cy: number; r: number; stroke?: number}> = ({cx, cy, r, stroke = 2.5}) => (
  <div style={{...abs(cx - r, cy - r, 2 * r, 2 * r), borderRadius: '50%', boxSizing: 'border-box', border: `${stroke}px solid #FFF`, background: 'linear-gradient(180deg, #F0F0F0 0%, #E8E8E8 3%, #919191 11.7%, #787878 20%, #5B5B5B 28%, #313131 40%, #0F0F0F 50%, #000 58%, #000 100%)'}} />
);

/** 天平托盘：吊线 + 浅碟 + 标签胶囊（k 0→1 紫亮起） */
const Pan: React.FC<{x: number; y: number; hang: number; label: string; k: number}> = ({x, y, hang, label, k}) => {
  const top = y + hang, dw = 120, bw = 98, dep = 20;
  return (
    <>
      <svg style={{...abs(0, 0, 1280, 720), overflow: 'visible', filter: 'drop-shadow(0 0 3px rgba(255,255,255,0.45))'}}>
        <line x1={x} y1={y} x2={x - dw / 2} y2={top} stroke="#FFF" strokeWidth={2} />
        <line x1={x} y1={y} x2={x + dw / 2} y2={top} stroke="#FFF" strokeWidth={2} />
        <path d={`M${x - dw / 2},${top} H${x + dw / 2} L${x + bw / 2 + 4},${top + dep - 4} Q${x + bw / 2},${top + dep} ${x + bw / 2 - 5},${top + dep} H${x - bw / 2 + 5} Q${x - bw / 2},${top + dep} ${x - bw / 2 - 4},${top + dep - 4} Z`} fill="#000" stroke="#FFF" strokeWidth={2} strokeLinejoin="round" />
      </svg>
      <Pill x={x - 54} y={top - 34} w={108} h={38} fill={k > 0 ? mixHex('#000000', PURPLE, k) : '#000'} stroke={k > 0 ? mixHex(GREY, WHITE, k) : GREY} sw={2} text={label} fontSize={24} weight={700} color={k > 0 ? WHITE : GREY} textDy={-2} glow={k > 0.02 ? `0 0 ${Math.round(30 * k)}px ${Math.round(10 * k)}px rgba(102,45,248,${(0.6 * k).toFixed(3)})` : undefined} />
    </>
  );
};

/**
 * 白线条天平（沿用 R6 SC025 造型，缩小版）：支点 (cx,py)、横梁半长 arm、吊线长 hang；theta>0 → 左盘下沉。
 * labels[0] 左盘（紫，leftGlow 0→1 亮起），labels[1] 右盘（灰）。
 */
export const Balance: React.FC<{cx: number; py: number; arm?: number; hang?: number; theta: number; labels: [string, string]; leftGlow?: number; opacity?: number; s?: number}> = ({cx, py, arm = 150, hang = 82, theta, labels, leftGlow = 0, opacity = 1, s = 1}) => {
  const cos = Math.cos(theta), sin = Math.sin(theta);
  const L = {x: cx - arm * cos, y: py + arm * sin};
  const R = {x: cx + arm * cos, y: py - arm * sin};
  const colH = 220;
  return (
    <div style={{position: 'absolute', inset: 0, opacity, transform: `scale(${s.toFixed(4)})`, transformOrigin: `${cx}px ${py + 120}px`}}>
      {/* 立柱 + 底座 */}
      <div style={{...abs(cx - 8, py, 16, colH), boxSizing: 'border-box', borderLeft: '1.5px solid #FFF', borderRight: '1.5px solid #FFF', background: 'linear-gradient(180deg, #000 0%, #000 42%, #F4F4F4 103%)'}} />
      <Box x={cx - 40} y={py + colH} w={80} h={16} r={6} sw={2} fill="linear-gradient(180deg, #5F5F5F 0%, #020202 100%)" />
      <Box x={cx - 110} y={py + colH + 16} w={220} h={24} r={8} sw={2} fill="linear-gradient(180deg, #5F5F5F 0%, #020202 100%)" />
      {/* 横梁 */}
      <div style={{...abs(cx - arm, py - 2.5, 2 * arm, 5), background: '#FFF', transform: `rotate(${((theta * 180) / Math.PI).toFixed(3)}deg)`, transformOrigin: '50% 50%', boxShadow: '0 0 8px 1px rgba(255,255,255,0.65)'}} />
      <Pan x={L.x} y={L.y} hang={hang} label={labels[0]} k={leftGlow} />
      <Pan x={R.x} y={R.y} hang={hang} label={labels[1]} k={0} />
      <GradBall cx={L.x} cy={L.y} r={9} stroke={2} />
      <GradBall cx={R.x} cy={R.y} r={9} stroke={2} />
      <GradBall cx={cx} cy={py} r={17} stroke={2.5} />
    </div>
  );
};

export {easeOutCubic};
