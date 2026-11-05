import React from 'react';
import {FONT_HEAVY, FONT_TECH, FONT_ORB, rnd, clamp01} from '../../common';
import {PURPLE, PURPLE_LIGHT, WHITE, GREY_LIGHT, GREY_LINE, GLOW_PURPLE_S, Box, CText, abs} from '../../ui';

/**
 * G6 组（第 3 章下半：重排 / 组装 / 生成 / 引用）专用图元。
 * 全部纯函数、绝对定位；动画量由镜头按 N 算好后传入。
 */

// ---------- 颜色工具 ----------
const parseColor = (c: string): number[] => {
  if (c.startsWith('#')) {
    const s = c.slice(1);
    return [parseInt(s.slice(0, 2), 16), parseInt(s.slice(2, 4), 16), parseInt(s.slice(4, 6), 16)];
  }
  const m = c.match(/-?\d+(\.\d+)?/g);
  return m ? m.slice(0, 3).map((v) => parseFloat(v)) : [0, 0, 0];
};
/** 两个颜色（#rrggbb 或 rgb(...)）线性混合（k=0 → a，k=1 → b），可嵌套 */
export const mixHex = (a: string, b: string, k: number) => {
  const A = parseColor(a), B = parseColor(b), t = clamp01(k);
  return `rgb(${A.map((v, i) => Math.round(v + (B[i] - v) * t)).join(',')})`;
};

// ---------- 漏斗层（复制 R2 Trap：显式 id、children 可混排字体）----------
/** 非对称水平渐变 stops（R2 SC014 实测）：[t, grey, purple] */
const STOPS: Array<[number, number, number[]]> = [
  [0, 224, [230, 220, 255]], [0.09, 212.3, [206, 190, 253]], [0.18, 200.6, [171, 139, 250]], [0.26, 190.2, [138, 102, 250]], [0.35, 178.5, [122, 72, 247]], [0.43, 168.1, [117, 55, 240]],
  [0.5, 160, [101, 46, 249]], [0.6, 162.5, [102, 45, 248]], [0.69, 171, [111, 59, 247]], [0.77, 184, [131, 87, 246]], [0.86, 197, [163, 133, 245]], [0.93, 210, [200, 185, 252]], [1, 224, [230, 220, 255]],
];
const rgb = (c: number[]) => `rgb(${c.map((v) => Math.round(v)).join(',')})`;
/** k=0 灰、k=1 紫 */
export const mixStops = (k: number): Array<[number, string]> => STOPS.map(([t, g, p]) => [t, rgb(p.map((v) => g + (v - g) * k))] as [number, string]);
export const GREY_STOPS = mixStops(0);
export const PURP_STOPS = mixStops(1);

export const TrapRag: React.FC<{id: string; cx: number; y: number; wTop: number; wBot: number; h: number; stops?: Array<[number, string]>; stroke?: number; opacity?: number; textShadow?: string; children?: React.ReactNode; style?: React.CSSProperties}> = ({id, cx, y, wTop, wBot, h, stops = PURP_STOPS, stroke = 2, opacity = 1, textShadow = '0 2px 12px rgba(0,0,0,.45)', children, style}) => {
  const W = wTop + 8, x0 = cx - W / 2;
  const pts = `4,1 ${4 + wTop},1 ${4 + (wTop + wBot) / 2},${1 + h} ${4 + (wTop - wBot) / 2},${1 + h}`;
  return (
    <div style={{...abs(x0, y, W, h + 4), opacity, ...style}}>
      <svg width={W} height={h + 4} style={{position: 'absolute', left: 0, top: 0, overflow: 'visible'}}>
        <defs>
          <linearGradient id={id} x1="0" y1="0" x2="1" y2="0">
            {stops.map(([o, c], i) => <stop key={i} offset={o} stopColor={c} />)}
          </linearGradient>
        </defs>
        <polygon points={pts} fill={`url(#${id})`} stroke="#FFF" strokeWidth={stroke} strokeLinejoin="miter" />
      </svg>
      <div style={{position: 'absolute', left: 0, top: 0, width: W, height: h + 2, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12, color: WHITE, textShadow, whiteSpace: 'nowrap'}}>{children}</div>
    </div>
  );
};
/** 漏斗层内文字（Noto 700） */
export const TrapText: React.FC<{size?: number; children: React.ReactNode; dy?: number}> = ({size = 34, children, dy = -3}) => (
  <span style={{fontFamily: FONT_HEAVY, fontWeight: 700, fontSize: size, lineHeight: 1, transform: `translateY(${dy}px)`, display: 'inline-block'}}>{children}</span>
);
/** 漏斗层内英文技术词（Exo 2 斜体白，压窄） */
export const TrapTech: React.FC<{size?: number; children: React.ReactNode; scaleX?: number}> = ({size = 34, children, scaleX = 0.86}) => (
  <span style={{fontFamily: FONT_TECH, fontStyle: 'italic', fontWeight: 700, fontSize: size, lineHeight: 1, letterSpacing: 1, transform: `scaleX(${scaleX})`, display: 'inline-block'}}>{children}</span>
);

// ---------- 迷你文本块卡（召回候选） ----------
/** 小卡：黑底白边 + 3 条灰线。grey ∈[0,1] 灰化程度；active ∈[0,1] 紫化程度（互斥使用） */
export const MiniCard: React.FC<{x: number; y: number; w: number; h: number; seed: number; grey?: number; active?: number; opacity?: number; r?: number; lines?: number}> = ({x, y, w, h, seed, grey = 0, active = 0, opacity = 1, r = 4, lines = 3}) => {
  const border = mixHex(mixHex(WHITE, '#6A6A6A', grey), WHITE, active);
  const fill = mixHex(mixHex('#000000', '#0C0C0C', grey), PURPLE, active);
  const line = mixHex(mixHex(GREY_LIGHT, '#555555', grey), WHITE, active);
  const pad = Math.max(4, w * 0.14);
  const lineH = Math.max(2, Math.round(h * 0.055));
  return (
    <div style={{...abs(x, y, w, h), boxSizing: 'border-box', background: fill, border: `1.5px solid ${border}`, borderRadius: r, opacity, boxShadow: active > 0.5 ? GLOW_PURPLE_S : undefined}}>
      {Array.from({length: lines}, (_, i) => {
        const lw = (0.55 + 0.4 * rnd(seed, i, 3)) * (w - 2 * pad) * (i === lines - 1 ? 0.7 : 1);
        const top = pad + 2 + i * ((h - 2 * pad - 4) / Math.max(1, lines - 0.4));
        return <div key={i} style={{position: 'absolute', left: pad, top, width: lw, height: lineH, background: line, opacity: 0.9, borderRadius: 1}} />;
      })}
    </div>
  );
};

// ---------- 证据卡（带 [n] 标签） ----------
export const EvidenceCard: React.FC<{x: number; y: number; w?: number; h?: number; label: string; seed?: number; opacity?: number; style?: React.CSSProperties}> = ({x, y, w = 96, h = 62, label, seed = 1, opacity = 1, style}) => (
  <div style={{...abs(x, y, w, h), opacity, ...style}}>
    <Box x={0} y={0} w={w} h={h} r={6} sw={2} />
    <CText cx={22} cy={16} size={22} weight={700} color={PURPLE_LIGHT} dy={-1}>{label}</CText>
    {[0, 1].map((i) => <div key={i} style={{position: 'absolute', left: 12, top: 32 + i * 12, width: (0.55 + 0.35 * rnd(seed, i, 7)) * (w - 24), height: 3, background: GREY_LIGHT, opacity: 0.85}} />)}
  </div>
);

// ---------- 来源卡（员工手册 p.12 / 差旅补充规定 2025） ----------
export const SourceCard: React.FC<{x: number; y: number; w?: number; h?: number; title: string; active?: number; opacity?: number; scale?: number; seed?: number}> = ({x, y, w = 280, h = 70, title, active = 0, opacity = 1, scale = 1, seed = 2}) => (
  <div style={{...abs(x, y, w, h), opacity, transform: scale === 1 ? undefined : `scale(${scale.toFixed(3)})`, transformOrigin: '50% 50%'}}>
    <Box x={0} y={0} w={w} h={h} r={8} sw={2} stroke={mixHex(WHITE, PURPLE_LIGHT, active)} glow={active > 0.01 ? `0 0 ${Math.round(24 * active)}px ${Math.round(8 * active)}px rgba(102,45,248,${(0.6 * active).toFixed(2)})` : undefined} />
    <div style={{position: 'absolute', left: 16, top: 12, fontFamily: FONT_HEAVY, fontWeight: 700, fontSize: 22, lineHeight: 1, color: WHITE, whiteSpace: 'nowrap'}}>{title}</div>
    {[0, 1].map((i) => <div key={i} style={{position: 'absolute', left: 16, top: 44 + i * 10, width: (0.5 + 0.4 * rnd(seed, i, 5)) * (w - 32), height: 3, background: GREY_LIGHT, opacity: 0.8}} />)}
  </div>
);

// ---------- 答复卡（SC29 → SC30 共用，保证组界无缝） ----------
export const ANS_W = 420, ANS_H = 180;
const L1 = '差旅住宿上限为每天 600 元';
const L2 = '一线城市 800 元';
export const ANS_TOTAL = L1.length + 1 + L2.length + 1; // 打字机总字符数
/** 引用角标中心（相对答复卡左上角）：按 Noto 26px 估算（CJK 26 / 数字 14.9 / 空格 6.8），still 校正后可微调 */
export const CITE_ANCHOR: Array<[number, number]> = [[20 + 318 + 14, 60], [20 + 188 + 14, 108]];
const Cite: React.FC<{n: number; op: number}> = ({n, op}) => (
  <span style={{display: 'inline-block', position: 'relative', top: -9, fontFamily: FONT_ORB, fontWeight: 700, fontSize: 20, color: PURPLE_LIGHT, marginLeft: 2, marginRight: 2, opacity: op, textShadow: '0 0 8px rgba(161,117,241,.6)'}}>[{n}]</span>
);
/**
 * 答复卡：黑底白边 420×180 + 「回答」紫小标签 + 两行 26px 正文；typed = 已打出的字符数（≥ANS_TOTAL 全显）；
 * citeShow = 是否渲染角标（占位，false 时文字不预留位置）；citeOp = 角标不透明度（入场期间只变透明度、不回流）。
 */
export const AnswerCard: React.FC<{x: number; y: number; typed?: number; citeShow?: boolean; citeOp?: number; opacity?: number; cursor?: boolean}> = ({x, y, typed = ANS_TOTAL, citeShow = true, citeOp = 1, opacity = 1, cursor = false}) => {
  const t = Math.max(0, Math.min(ANS_TOTAL, Math.floor(typed)));
  const a = L1.slice(0, Math.min(t, L1.length));
  const comma = t > L1.length ? '，' : '';
  const b = t > L1.length + 1 ? L2.slice(0, t - L1.length - 1) : '';
  const period = t >= ANS_TOTAL ? '。' : '';
  const line1Done = t >= L1.length;
  const showCite = citeShow;
  const cites = citeOp;
  const cur = cursor && t < ANS_TOTAL ? <span style={{display: 'inline-block', width: 3, height: 26, background: WHITE, marginLeft: 2, verticalAlign: -3}} /> : null;
  const lineStyle: React.CSSProperties = {position: 'absolute', left: 20, fontFamily: FONT_HEAVY, fontWeight: 500, fontSize: 26, lineHeight: '36px', color: WHITE, whiteSpace: 'nowrap'};
  return (
    <div style={{...abs(x, y, ANS_W, ANS_H), opacity}}>
      <Box x={0} y={0} w={ANS_W} h={ANS_H} r={12} sw={2} />
      <Box x={16} y={-16} w={72} h={32} r={16} fill={PURPLE} sw={2}>
        <div style={{position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: FONT_HEAVY, fontWeight: 700, fontSize: 22, color: WHITE, lineHeight: 1, transform: 'translateY(-1px)'}}>回答</div>
      </Box>
      <div style={{...lineStyle, top: 42}}>
        {a}
        {line1Done && showCite ? <Cite n={1} op={cites} /> : null}
        {comma}
        {!line1Done || t === L1.length ? cur : null}
      </div>
      <div style={{...lineStyle, top: 90}}>
        {b}
        {t >= ANS_TOTAL - 1 && showCite ? <Cite n={2} op={cites} /> : null}
        {period}
        {line1Done && t > L1.length ? cur : null}
      </div>
    </div>
  );
};

// ---------- draw-on 折线（SVG 内使用） ----------
export const DrawPath: React.FC<{pts: Array<[number, number]>; p?: number; color?: string; sw?: number; opacity?: number; dashed?: boolean}> = ({pts, p = 1, color = PURPLE_LIGHT, sw = 2.5, opacity = 1, dashed = false}) => {
  if (p <= 0 || pts.length < 2) return null;
  let total = 0;
  for (let i = 1; i < pts.length; i++) total += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
  const dash = dashed ? `6 6` : `${total}`;
  return <polyline points={pts.map((q) => q.join(',')).join(' ')} fill="none" stroke={color} strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" strokeDasharray={dashed ? dash : total} strokeDashoffset={dashed ? undefined : total * (1 - clamp01(p))} opacity={opacity} />;
};

// ---------- 打字机 ----------
/** 自 f0 起每 per 帧出 1 字，返回可见字符数 */
export const typedCount = (N: number, f0: number, len: number, per = 2) => (N < f0 ? 0 : Math.min(len, Math.floor((N - f0) / per) + 1));
/** 打字机文本行（Noto 24），末尾方块光标随打字闪烁 */
export const TypeLine: React.FC<{x: number; y: number; text: string; N: number; f0: number; per?: number; size?: number; color?: string; opacity?: number; weight?: number}> = ({x, y, text, N, f0, per = 2, size = 24, color = WHITE, opacity = 1, weight = 500}) => {
  if (N < f0) return null;
  const n = typedCount(N, f0, text.length, per);
  const typing = n < text.length;
  const blink = typing || Math.floor((N - f0) / 8) % 2 === 0 && N - f0 < text.length * per + 40;
  return (
    <div style={{position: 'absolute', left: x, top: y, fontFamily: FONT_HEAVY, fontWeight: weight, fontSize: size, lineHeight: 1.3, color, whiteSpace: 'nowrap', opacity}}>
      {text.slice(0, n)}
      {blink ? <span style={{display: 'inline-block', width: 3, height: size, background: color, marginLeft: 3, verticalAlign: -3}} /> : null}
    </div>
  );
};

/** 分割线（灰细线） */
export const HLine: React.FC<{x: number; y: number; w: number; color?: string; opacity?: number}> = ({x, y, w, color = GREY_LINE, opacity = 1}) => <div style={{...abs(x, y, w, 1.5), background: color, opacity}} />;

/** 角标入场不透明度：8 帧 easeOut 淡入（与 ui.tsx SoftIn 同曲线）。闪烁整改：原 12 帧 glitchOpacity，SC29 不在白名单 */
export const citeOp = (N: number, f0: number, len = 8) => {
  const n = N - f0;
  if (n < 0) return 0;
  return 1 - Math.pow(1 - clamp01(n / len), 2.5);
};
