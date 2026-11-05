import React from 'react';
import {Box, CText, PURPLE, PURPLE_LIGHT, WHITE, GREY, GREY_LIGHT, GLOW_PURPLE_S, TEXT_GLOW, abs, fadeIn, scaleIn, SoftIn} from '../../ui';
import {GlitchIn, rnd, clamp01, easeOutCubic, easeInOutPow, powOutRemain, FONT_HEAVY, FONT_TECH, FONT_ORB} from '../../common';

/**
 * G8 组（第 4 章下半）本地图元。风格同 ui.tsx：黑填充 + 白描边 2–3px、紫 = 重点、橙红 = 警示/另一方、灰 = 非重点。
 * 全部纯函数；动画量由调用方按 N 计算传入。
 */

/** 入场容器：默认 SoftIn（8 帧淡入 + 10px 上浮）；glitch=true 才用 GlitchIn。闪烁整改（2026-09-06）：SC40/SC41 不在白名单，调用方不开。 */
export const EntryIn: React.FC<{N: number; f0: number; glitch?: boolean; children: React.ReactNode; style?: React.CSSProperties}> = ({glitch = false, ...p}) => (glitch ? <GlitchIn {...p} /> : <SoftIn {...p} />);

// ---- 分镜表 G8 帧区间（1 起含端点） ----
export const FR = {
  SC38: {from: 6991, to: 7167},
  SC39: {from: 7168, to: 7301},
  SC40: {from: 7302, to: 7503},
  SC41: {from: 7504, to: 7753},
  SC42: {from: 7754, to: 7869},
  SC43: {from: 7870, to: 8052},
  SC44: {from: 8053, to: 8148},
} as const;

// ---- 颜色插值 ----
const hex2rgb = (h: string): [number, number, number] => {
  const s = h.replace('#', '');
  return [parseInt(s.slice(0, 2), 16), parseInt(s.slice(2, 4), 16), parseInt(s.slice(4, 6), 16)];
};
/** 两色线性混合（k 0→1：a→b），返回 rgb() 字串 */
export const mix = (a: string, b: string, k: number) => {
  const A = hex2rgb(a), B = hex2rgb(b);
  const t = clamp01(k);
  return `rgb(${A.map((v, i) => Math.round(v + (B[i] - v) * t)).join(',')})`;
};
/** 统一离场（与 G7 g7ui.exitOut 同式）：幂缓入下摇 1.2·ex² + 6.7%/帧淡出，末 6 帧线性收到 0（ex = len 时恰为 0；调用方取 ex = N − (to − len)） */
export const exitOut = (ex: number, len = 14) => {
  if (ex <= 0) return {dy: 0, op: 1};
  return {dy: 1.2 * ex * ex, op: Math.pow(0.933, ex) * (1 - clamp01((ex - (len - 6)) / 6))};
};
/** 千分位（确定性，不依赖 locale） */
export const fmtInt = (v: number) => Math.round(v).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');

/** 定点缩放容器（全幅 div，transformOrigin 0 0） */
export const Anchor: React.FC<{cx: number; cy: number; s?: number; dy?: number; opacity?: number; children: React.ReactNode}> = ({cx, cy, s = 1, dy = 0, opacity = 1, children}) => (
  <div style={{position: 'absolute', left: 0, top: 0, width: 1280, height: 720, transformOrigin: '0 0', opacity, transform: `translate(0,${dy.toFixed(2)}px) translate(${cx}px,${cy}px) scale(${s.toFixed(4)}) translate(${-cx}px,${-cy}px)`}}>{children}</div>
);

// ================= SC38：页面缩略图卡 / Embedding 盒 =================
/** 页面缩略图卡（PDF 页）：黑底白边 + 小图表（柱状/折线/截图窗口）+ 两行文本线；active → 紫边 + 柔光 */
export const PageCard: React.FC<{cx: number; cy: number; w?: number; h?: number; kind: 'bar' | 'line' | 'shot'; activeK?: number; opacity?: number}> = ({cx, cy, w = 110, h = 146, kind, activeK = 0, opacity = 1}) => {
  const stroke = mix(WHITE, PURPLE_LIGHT, activeK);
  const ink = mix(GREY_LIGHT, WHITE, activeK);
  return (
    <div style={{...abs(cx - w / 2, cy - h / 2, w, h), opacity}}>
      <Box x={0} y={0} w={w} h={h} r={6} sw={2.5} stroke={stroke} glow={activeK > 0 ? `0 0 ${Math.round(24 * activeK)}px ${Math.round(8 * activeK)}px rgba(102,45,248,${(0.6 * activeK).toFixed(2)})` : undefined} />
      <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} style={{position: 'absolute', left: 0, top: 0}}>
        {kind === 'bar' ? (
          <g>
            <line x1={16} y1={84} x2={94} y2={84} stroke={ink} strokeWidth={1.5} />
            {[30, 48, 22, 58].map((bh, i) => <rect key={i} x={22 + i * 18} y={84 - bh} width={12} height={bh} fill={i === 3 ? PURPLE : '#000'} stroke={stroke} strokeWidth={1.5} />)}
          </g>
        ) : kind === 'line' ? (
          <g>
            <line x1={16} y1={84} x2={94} y2={84} stroke={ink} strokeWidth={1.5} />
            <line x1={16} y1={22} x2={16} y2={84} stroke={ink} strokeWidth={1.5} />
            <polyline points="20,72 36,60 52,66 70,42 90,28" fill="none" stroke={stroke} strokeWidth={2.5} strokeLinejoin="round" strokeLinecap="round" />
            {[[20, 72], [36, 60], [52, 66], [70, 42], [90, 28]].map(([px, py], i) => <circle key={i} cx={px} cy={py} r={2.6} fill={i === 4 ? PURPLE_LIGHT : WHITE} />)}
          </g>
        ) : (
          <g>
            <rect x={14} y={16} width={82} height={70} rx={4} fill="#000" stroke={stroke} strokeWidth={1.8} />
            <line x1={14} y1={31} x2={96} y2={31} stroke={stroke} strokeWidth={1.4} />
            {[22, 30, 38].map((dx, i) => <circle key={i} cx={dx} cy={23.5} r={2.4} fill={['#F3A634', '#508DF7', '#E83E2F'][i]} />)}
            {[42, 52, 62, 72].map((ly, i) => <rect key={i} x={22} y={ly} width={[56, 40, 62, 30][i]} height={3} fill={ink} opacity={0.85} />)}
          </g>
        )}
        {[104, 118, 132].map((ly, i) => <rect key={i} x={16} y={ly} width={[72, 60, 44][i]} height={3} fill={ink} opacity={0.8} />)}
      </svg>
    </div>
  );
};

/** Embedding 紫盒（沿用推荐片 Embedding 层：紫填充 + 白虚线边 r8） */
export const EmbedBox: React.FC<{x: number; y: number; w?: number; h?: number; opacity?: number}> = ({x, y, w = 180, h = 62, opacity = 1}) => (
  <Box x={x} y={y} w={w} h={h} r={8} fill={PURPLE} stroke={WHITE} sw={2.5} dashed opacity={opacity} glow="0 0 14px 3px rgba(102,45,248,.35)">
    <div style={{position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: FONT_TECH, fontStyle: 'italic', fontWeight: 700, fontSize: 27, color: WHITE, letterSpacing: 1, transform: 'scaleX(0.86)', lineHeight: 1}}>Embedding</div>
  </Box>
);

// ================= SC40/41：刻度尺 + 上下文窗口 =================
export const RULER = {x0: 200, x1: 1080, y: 380, kx: 376}; // 20% 处 = 200K tokens
export const WIN = {x: 850, y: 140, w: 300, h: 160};
export const DOC_N = 6;
export const docHome = (i: number) => ({x: 204 + i * 27, y: 336});
export const docGrid = (i: number) => ({x: 895 + (i % 3) * 90, y: 178 + Math.floor(i / 3) * 58});

/** 小文档（SVG <g>，30×38，折角 + 3 行）——用单 Svg 承载多枚以避免每枚一个 filter */
export const MiniDoc: React.FC<{x: number; y: number; s?: number; color?: string; opacity?: number; fill?: string}> = ({x, y, s = 1, color = WHITE, opacity = 1, fill = '#000'}) => (
  <g transform={`translate(${x.toFixed(2)} ${y.toFixed(2)}) translate(15 19) scale(${s.toFixed(3)}) translate(-15 -19)`} opacity={opacity}>
    <path d="M0,0 H21 L30,9 V38 H0 Z" fill={fill} stroke={color} strokeWidth={2} strokeLinejoin="round" />
    <path d="M21,0 V9 H30" fill="none" stroke={color} strokeWidth={2} strokeLinejoin="round" />
    <rect x={6} y={16} width={18} height={2.5} fill={color} opacity={0.85} />
    <rect x={6} y={23} width={13} height={2.5} fill={color} opacity={0.85} />
    <rect x={6} y={30} width={16} height={2.5} fill={color} opacity={0.85} />
  </g>
);

/** 刻度尺组（Anthropic 标签 / 尺 / 紫竖线 / 200K 标签 / ≈500 页）——SC40 入场、SC41 承接后离场。N 为绝对帧号。 */
export const RulerPart: React.FC<{N: number; opacity?: number; dy?: number; glitch?: boolean}> = ({N, opacity = 1, dy = 0, glitch = false}) => {
  const p = clamp01((N - 7310) / 22); // 尺 draw-on
  const pe = 1 - Math.pow(1 - p, 2.5);
  const L = RULER.x1 - RULER.x0;
  const reach = RULER.x0 + L * pe;
  const g = 1 - powOutRemain(N - 7373, 16, 2.5); // 紫线自下长出
  const lineH = 80 * g;
  const nPage = N - 7428;
  const pages = nPage < 0 ? 0 : Math.round(500 * easeOutCubic(clamp01(nPage / 20)));
  return (
    <div style={{position: 'absolute', inset: 0, opacity, transform: `translateY(${dy.toFixed(2)}px)`}}>
      <EntryIn N={N} f0={7310} glitch={glitch}>
        <Box x={90} y={120} w={232} h={40} r={20} stroke={GREY} sw={2}>
          <div style={{position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: FONT_TECH, fontStyle: 'italic', fontWeight: 600, fontSize: 25, color: GREY, letterSpacing: 1, lineHeight: 1, transform: 'translateY(-1px) scaleX(0.9)'}}>Anthropic, 2024</div>
        </Box>
      </EntryIn>
      <svg width={1280} height={720} viewBox="0 0 1280 720" style={{position: 'absolute', left: 0, top: 0, filter: 'drop-shadow(0 0 3px rgba(255,255,255,0.45))'}}>
        <defs>
          <clipPath id="g8-ruler-clip">
            {/* p=0 时宽 0：左端封口竖线随尺身一起揭示（QC v1：原来 7302 起孤立可见） */}
            <rect x={RULER.x0 - 4} y={RULER.y - 40} width={p <= 0 ? 0 : Math.max(0, reach - RULER.x0 + 8)} height={80} />
          </clipPath>
        </defs>
        <g clipPath="url(#g8-ruler-clip)" opacity={p <= 0 ? 0 : 1}>
          <line x1={RULER.x0} y1={RULER.y} x2={RULER.x1} y2={RULER.y} stroke={WHITE} strokeWidth={3} />
          {Array.from({length: 11}, (_, i) => {
            const x = RULER.x0 + (L / 10) * i;
            const major = i === 0 || i === 10;
            const h = major ? 22 : i === 2 ? 16 : 11;
            return <line key={i} x1={x} y1={RULER.y - h} x2={x} y2={RULER.y + (major ? 6 : 0)} stroke={i === 2 ? PURPLE_LIGHT : WHITE} strokeWidth={major ? 3 : 2} />;
          })}
        </g>
      </svg>
      <CText cx={RULER.x0} cy={414} size={24} family={FONT_ORB} weight={700} opacity={fadeIn(N - 7314, 8)}>0</CText>
      <CText cx={RULER.x1} cy={414} size={24} family={FONT_ORB} weight={700} opacity={fadeIn(N - 7330, 8)}>1M</CText>
      {g > 0 ? <div style={{...abs(RULER.kx - 2, RULER.y - lineH, 4, lineH), background: PURPLE_LIGHT, boxShadow: GLOW_PURPLE_S}} /> : null}
      <EntryIn N={N} f0={7377} glitch={glitch}>
        <CText cx={RULER.kx} cy={282} size={30} family={FONT_TECH} weight={700} color={PURPLE_LIGHT} italic scaleX={0.86} letterSpacing={1} dy={0} shadow="0 0 8px rgba(120,70,240,.7)">200K tokens</CText>
      </EntryIn>
      <EntryIn N={N} f0={7428} glitch={glitch}>
        <CText cx={RULER.kx} cy={448} size={40} weight={900} scaleX={0.9} shadow={TEXT_GLOW} style={{fontVariantNumeric: 'tabular-nums'}}>{`≈ ${pages} 页`}</CText>
      </EntryIn>
    </div>
  );
};

/** 上下文窗口组（框 + 标题 + 6 枚文档自尺飞入 + 绿勾）。N 为绝对帧号。 */
export const WindowPart: React.FC<{N: number; checkOpacity?: number; opacity?: number; glitch?: boolean}> = ({N, checkOpacity = 1, opacity = 1, glitch = false}) => {
  const eio = easeInOutPow(2.5);
  const chk = clamp01((N - 7488) / 12);
  return (
    <div style={{position: 'absolute', inset: 0, opacity}}>
      <EntryIn N={N} f0={7455} glitch={glitch}>
        <Box x={WIN.x} y={WIN.y} w={WIN.w} h={WIN.h} r={10} sw={2.5} />
        {/* 标签放框外左上（QC v1：框内顶部会被 SC41 溢出方块 + 红叉遮死）；x 856–976 与顶部冒出的方块区 (x≥1000) 错开 */}
        <CText cx={WIN.x + 66} cy={WIN.y - 20} size={24} weight={700} color={GREY_LIGHT} dy={-1} shadow="0 0 6px rgba(0,0,0,.95), 0 0 2px rgba(0,0,0,1)">上下文窗口</CText>
      </EntryIn>
      <svg width={1280} height={720} viewBox="0 0 1280 720" style={{position: 'absolute', left: 0, top: 0, overflow: 'visible', filter: 'drop-shadow(0 0 3px rgba(255,255,255,0.45))'}}>
        {Array.from({length: DOC_N}, (_, i) => {
          const nIn = N - (7373 + i * 2);
          if (nIn < 0) return null;
          const s = scaleIn(nIn, 14);
          const t = clamp01((N - (7459 + i * 2)) / 20);
          const e = eio(t);
          const h = docHome(i), gd = docGrid(i);
          const x = h.x + (gd.x - h.x) * e;
          const y = h.y + (gd.y - h.y) * e - 120 * Math.sin(Math.PI * t);
          return <MiniDoc key={i} x={x} y={y} s={s} opacity={fadeIn(nIn, 6)} />;
        })}
        {chk > 0 ? (
          <polyline points="1168,224 1184,240 1214,206" fill="none" stroke="#8FF740" strokeWidth={7} strokeLinecap="round" strokeLinejoin="round" strokeDasharray={70} strokeDashoffset={70 * (1 - chk)} opacity={checkOpacity} />
        ) : null}
      </svg>
    </div>
  );
};

// ================= SC41：图标胶囊 =================
/** 带简笔图标的大胶囊：icon 'search'（放大镜）| 'book'（书页） */
export const IconPill: React.FC<{x: number; y: number; w: number; h: number; fill?: string; stroke?: string; text: string; icon: 'search' | 'book'; fontSize?: number; opacity?: number; glow?: string}> = ({x, y, w, h, fill = '#000', stroke = WHITE, text, icon, fontSize = 34, opacity = 1, glow}) => (
  <Box x={x} y={y} w={w} h={h} r={h / 2} fill={fill} stroke={stroke} sw={2.5} opacity={opacity} glow={glow}>
    <div style={{position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 16}}>
      <svg width={46} height={46} viewBox="0 0 46 46" style={{flex: 'none'}}>
        {icon === 'search' ? (
          <g>
            <circle cx={19} cy={19} r={12.5} fill="none" stroke={WHITE} strokeWidth={3.5} />
            <line x1={28.5} y1={28.5} x2={41} y2={41} stroke={WHITE} strokeWidth={4.5} strokeLinecap="round" />
          </g>
        ) : (
          <g>
            <path d="M4 10 C 12 6, 18 6, 22.5 10 L 22.5 38 C 18 34, 12 34, 4 37 Z" fill="none" stroke={WHITE} strokeWidth={2.6} strokeLinejoin="round" />
            <path d="M42 10 C 34 6, 28 6, 23.5 10 L 23.5 38 C 28 34, 34 34, 42 37 Z" fill="none" stroke={WHITE} strokeWidth={2.6} strokeLinejoin="round" />
            {[16, 22, 28].map((ly, i) => <g key={i}><line x1={8.5} y1={ly} x2={18.5} y2={ly - 1.5} stroke={WHITE} strokeWidth={1.8} opacity={0.8} /><line x1={27.5} y1={ly - 1.5} x2={37.5} y2={ly} stroke={WHITE} strokeWidth={1.8} opacity={0.8} /></g>)}
          </g>
        )}
      </svg>
      <div style={{fontFamily: FONT_HEAVY, fontWeight: 800, fontSize, color: WHITE, lineHeight: 1, whiteSpace: 'nowrap', transform: 'translateY(-2px)', letterSpacing: 1}}>{text}</div>
    </div>
  </Box>
);

// ================= SC43：书本（乱页/整齐两变体，SC42 的考卷/书本已改用 G2/parts 的 ExamPaper/BookIcon） =================
export type OpenBookProps = {
  cx: number; cy: number; w?: number; h?: number; color?: string; opacity?: number;
  /** 'tidy' 层级清晰；'messy' 页面歪斜线条杂乱 */
  variant?: 'tidy' | 'messy' | 'plain';
  /** 右页侧边彩色索引标签 */
  tabs?: string[];
  /** messy：翻页姿态（0..3 循环）与内容随机种子 */
  flipPose?: number; seed?: number;
  /** 右页高亮行颜色 */
  accent?: string;
  glow?: string;
};
/** 翻开的书（SVG 简笔）：两页弧顶 + 书脊 + 底部书体线；tidy/messy 两种内容 */
export const OpenBook: React.FC<OpenBookProps> = ({cx, cy, w = 360, h = 240, color = WHITE, opacity = 1, variant = 'plain', tabs, flipPose = -1, seed = 1, accent, glow}) => {
  const hw = w / 2;
  const leftPage = `M 12 36 C 80 14, 140 12, ${hw - 2} 26 L ${hw - 2} ${h - 26} C 140 ${h - 40}, 80 ${h - 38}, 12 ${h - 12} Z`;
  const rightPage = `M ${w - 12} 36 C ${w - 80} 14, ${w - 140} 12, ${hw + 2} 26 L ${hw + 2} ${h - 26} C ${w - 140} ${h - 40}, ${w - 80} ${h - 38}, ${w - 12} ${h - 12} Z`;
  const lines: React.ReactNode[] = [];
  if (variant === 'tidy') {
    // 左页：标题条 + 层级缩进；右页：标题条 + 行 + 高亮行
    const L = (x0: number, y: number, len: number, hgt: number, col: string, op = 0.9, key: string) => <rect key={key} x={x0} y={y} width={len} height={hgt} rx={hgt / 2} fill={col} opacity={op} />;
    const lx = 34, lw = hw - 26 - lx, rx = hw + 26, rw = w - 34 - rx;
    lines.push(L(lx, 54, lw * 0.6, 6, color, 1, 'lh'));
    [[0, 1], [14, 0.7], [14, 0.75], [0, 0.95], [14, 0.65], [14, 0.7]].forEach(([ind, f], i) => lines.push(L(lx + ind, 74 + i * 20, (lw - ind) * f, 3, color, ind ? 0.65 : 0.9, `l${i}`)));
    lines.push(L(rx, 54, rw * 0.55, 6, color, 1, 'rh'));
    [[0, 0.95], [14, 0.7], [14, 0.6], [0, 1], [14, 0.72], [14, 0.66]].forEach(([ind, f], i) => lines.push(L(rx + ind, 74 + i * 20, (rw - ind) * f, 3, i === 3 && accent ? accent : color, ind ? 0.65 : 0.9, `r${i}`)));
  } else if (variant === 'messy') {
    const lx = 34, lw = hw - 26 - lx, rx = hw + 26, rw = w - 34 - rx;
    for (let i = 0; i < 6; i++) {
      const fL = 0.35 + 0.65 * rnd(seed, i, 1), aL = (rnd(seed, i, 2) - 0.5) * 14, oyL = (rnd(seed, i, 3) - 0.5) * 8;
      const fR = 0.35 + 0.65 * rnd(seed, i, 4), aR = (rnd(seed, i, 5) - 0.5) * 14, oyR = (rnd(seed, i, 6) - 0.5) * 8;
      const yl = 60 + i * 22 + oyL, yr = 60 + i * 22 + oyR;
      lines.push(<rect key={`ml${i}`} x={lx} y={yl} width={lw * fL} height={3} fill={color} opacity={0.8} transform={`rotate(${aL.toFixed(1)} ${lx} ${yl})`} />);
      lines.push(<rect key={`mr${i}`} x={rx} y={yr} width={rw * fR} height={3} fill={color} opacity={0.8} transform={`rotate(${aR.toFixed(1)} ${rx} ${yr})`} />);
    }
  }
  // messy：翻动中的页（锚在书脊）
  let flip: React.ReactNode = null;
  if (flipPose >= 0) {
    const c = [0.82, 0.3, -0.35, -0.8][flipPose % 4];
    const lift = 34 * (1 - Math.abs(c));
    const fx = hw + (hw - 16) * c;
    flip = <path d={`M ${hw} 26 L ${fx.toFixed(1)} ${(30 - lift).toFixed(1)} L ${fx.toFixed(1)} ${(h - 14 - lift * 0.6).toFixed(1)} L ${hw} ${h - 26} Z`} fill="#000" stroke={color} strokeWidth={2.2} strokeLinejoin="round" opacity={0.95} />;
  }
  return (
    <div style={{...abs(cx - w / 2 - 30, cy - h / 2 - 30, w + 60, h + 60), opacity}}>
      <svg width={w + 60} height={h + 60} viewBox={`-30 -30 ${w + 60} ${h + 60}`} style={{position: 'absolute', left: 0, top: 0, overflow: 'visible', filter: glow ?? 'drop-shadow(0 0 3px rgba(255,255,255,0.4))'}}>
        {variant === 'messy' ? (
          <g>
            <rect x={hw + 30} y={4} width={110} height={150} rx={3} fill="#000" stroke={color} strokeWidth={2} transform={`rotate(12 ${hw + 85} 80)`} opacity={0.8} />
            <rect x={20} y={2} width={110} height={150} rx={3} fill="#000" stroke={color} strokeWidth={2} transform={`rotate(-9 75 80)`} opacity={0.8} />
          </g>
        ) : null}
        <path d={`M 14 ${h - 4} L ${hw} ${h - 18} L ${w - 14} ${h - 4}`} fill="none" stroke={color} strokeWidth={1.6} opacity={0.6} />
        <path d={`M 8 ${h - 8} L ${hw} ${h - 22} L ${w - 8} ${h - 8}`} fill="none" stroke={color} strokeWidth={3} />
        <path d={leftPage} fill="#000" stroke={color} strokeWidth={2.5} strokeLinejoin="round" />
        <path d={rightPage} fill="#000" stroke={color} strokeWidth={2.5} strokeLinejoin="round" />
        <line x1={hw} y1={26} x2={hw} y2={h - 26} stroke={color} strokeWidth={2} opacity={0.7} />
        {lines}
        {tabs ? tabs.map((tc, i) => <rect key={`t${i}`} x={w - 18} y={44 + i * 30} width={30} height={20} rx={3} fill={tc} stroke={WHITE} strokeWidth={1.5} />) : null}
        {flip}
      </svg>
    </div>
  );
};

// ================= SC44：城堡 + 护城河 =================
/** 简笔城堡（SVG <g>，锚点：底边中心 (cx, baseY)）：主塔 + 两侧塔 + 城齿 + 门洞 */
export const Castle: React.FC<{cx: number; baseY: number; color?: string; fill?: string}> = ({cx, baseY, color = WHITE, fill = '#000'}) => {
  const crenel = (x0: number, w: number, top: number, n: number, ch = 14) => {
    const cw = w / (n * 2 - 1);
    return Array.from({length: n}, (_, i) => <rect key={i} x={x0 + i * 2 * cw} y={top - ch} width={cw} height={ch} fill={fill} stroke={color} strokeWidth={2.5} strokeLinejoin="round" />);
  };
  const mw = 110, mh = 210, sw = 66, sh = 150;
  const mx = cx - mw / 2, my = baseY - mh;
  const lx = cx - mw / 2 - 12 - sw, rx = cx + mw / 2 + 12, sy = baseY - sh;
  return (
    <g>
      {/* 连墙 */}
      <rect x={lx + sw - 4} y={baseY - 96} width={mx - (lx + sw) + 8} height={96} fill={fill} stroke={color} strokeWidth={2.5} />
      <rect x={mx + mw - 4} y={baseY - 96} width={rx - (mx + mw) + 8} height={96} fill={fill} stroke={color} strokeWidth={2.5} />
      {/* 侧塔 */}
      <rect x={lx} y={sy} width={sw} height={sh} fill={fill} stroke={color} strokeWidth={2.5} />
      {crenel(lx, sw, sy, 3, 12)}
      <rect x={rx} y={sy} width={sw} height={sh} fill={fill} stroke={color} strokeWidth={2.5} />
      {crenel(rx, sw, sy, 3, 12)}
      {/* 主塔 */}
      <rect x={mx} y={my} width={mw} height={mh} fill={fill} stroke={color} strokeWidth={3} />
      {crenel(mx, mw, my, 4, 16)}
      {/* 门洞 */}
      <path d={`M ${cx - 20} ${baseY} V ${baseY - 36} A 20 20 0 0 1 ${cx + 20} ${baseY - 36} V ${baseY} Z`} fill={PURPLE} stroke={color} strokeWidth={2.5} />
      {/* 窗 */}
      {[my + 50, my + 100].map((wy, i) => <rect key={i} x={cx - 8} y={wy} width={16} height={26} rx={8} fill="#000" stroke={color} strokeWidth={2} />)}
      <rect x={lx + sw / 2 - 6} y={sy + 40} width={12} height={20} rx={6} fill="#000" stroke={color} strokeWidth={2} />
      <rect x={rx + sw / 2 - 6} y={sy + 40} width={12} height={20} rx={6} fill="#000" stroke={color} strokeWidth={2} />
      {/* 旗杆 */}
      <line x1={cx} y1={my - 16} x2={cx} y2={my - 38} stroke={color} strokeWidth={2.5} />
      <path d={`M ${cx} ${my - 38} L ${cx + 24} ${my - 32} L ${cx} ${my - 26} Z`} fill={PURPLE} stroke={color} strokeWidth={2} />
    </g>
  );
};

/** 椭圆周长（Ramanujan） */
export const ellipsePerim = (a: number, b: number) => Math.PI * (3 * (a + b) - Math.sqrt((3 * a + b) * (a + 3 * b)));

