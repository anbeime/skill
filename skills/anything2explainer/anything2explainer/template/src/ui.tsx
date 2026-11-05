import React from 'react';
import {FONT_HEAVY, FONT_TECH, FONT_MONO, FONT_ORB, TEXT_DY, LANG} from './common/lib';
import {GlitchIn, powOutRemain, BEZ_SCALE_IN, clamp01, rnd} from './common';

/**
 * 共用图元与调色板（黑填充 + 白描边 2–3px、紫 = 当前重点、橙红 = 指标/警示、灰 = 非重点、绿 = 正确）。镜头组件 `import {…} from '../../ui'`。
 * 所有组件为纯函数式、绝对定位（画布 1280×720）；动画由调用方按 N 计算后传入（opacity/p/s 等）。
 */
// ---- 调色板 ----
export const PURPLE = '#6630F8'; // 标准胶囊紫 (102,48,248)
export const PURPLE_LIGHT = '#A175F1'; // 亮紫（高光端 / 穿过进度条后）
export const PURPLE_TECH = '#6530F4'; // 英文科技字紫
export const PURPLE_DEEP = '#5A3AD5'; // 深紫（曲线 / 硬投影）
export const PURPLE_PALE = '#E6DCFF';
export const ORANGE = '#F05F41'; // 橙红：指标数字 / 另一方 / 强调
export const CORAL = '#F16043';
export const RED_DEEP = '#EC081F'; // 深红警示块
export const GREEN = '#8FF740'; // 绿勾
export const GREY = '#A0A0A1'; // 非激活
export const GREY_MID = '#747474';
export const GREY_LINE = '#4A4A4A'; // 网格线
export const GREY_LIGHT = '#D4D4D4';
export const WHITE = '#FFFFFF';
export const MAGENTA = '#D100D6';
export const CYAN = '#58FFEE';
export const GLOW_PURPLE = '0 0 12px 3px rgba(102,45,248,.35), 0 0 42px 14px rgba(102,45,248,.45)';
export const GLOW_PURPLE_S = '0 0 24px 8px rgba(102,45,248,.6)';
export const GLOW_ORANGE = '0 0 40px rgba(243,95,69,.75), 0 0 100px 10px rgba(243,95,69,.25)';
export const GLOW_RED = '0 0 60px 20px rgba(236,8,31,.42), 0 0 20px 6px rgba(236,8,31,.45)';
export const BLOOM = 'drop-shadow(0 0 3px rgba(255,255,255,0.5))';
export const BLOOM_SOFT = 'drop-shadow(0 0 2px rgba(255,255,255,0.35))';
export const TEXT_GLOW = '0 0 12px rgba(255,255,255,.55), 0 0 4px rgba(255,255,255,.35)';
export const PILL_SHADOW = 'drop-shadow(0 0 2px rgba(200,180,255,.6))';

// ---- 动效小工具（n = N − f0）----
export const fadeIn = (n: number, len = 12) => clamp01(n / len);
export const fadeOut = (n: number, len = 15) => 1 - clamp01(n / len);
/** 自下滑入剩余位移（px）：Δ·(1−n/22)^2.5，用法 top = yEnd + slideUp(n) */
export const slideUp = (n: number, d = 300, N = 22) => d * powOutRemain(n, N, 2.5);
/** 21 帧缩放入场 0→1 */
export const scaleIn = (n: number, N = 21) => BEZ_SCALE_IN(clamp01(n / N));
/** 离场加速位移（px）：c·n²（n 帧），配 exitFade */
export const exitAccel = (n: number, c = 0.5) => (n <= 0 ? 0 : c * n * n);
/** 离场逐帧 6.7% 淡出 */
export const exitFade = (n: number) => (n <= 0 ? 1 : Math.pow(0.933, n));
/** 错峰：第 i 个元素延后 i·step 帧 */
export const stagger = (i: number, step = 2) => i * step;

export const abs = (x: number, y: number, w?: number, h?: number): React.CSSProperties => ({position: 'absolute', left: x, top: y, width: w, height: h});


/** 非闪烁入场（规范：glitch 只给重点词，其余文字/标签一律用它）：len 帧 easeOut 淡入 + dy px 上浮；n<0 不渲染。签名与 GlitchIn 对齐（N,f0,children,style），可直接替换。 */
// ---- 入场 / 离场 / 混色（协议提到的工具必须在共用层真的存在；各组直接 import，不要各写一份）----
/** 首帧即有亮度的淡入：n<0 → 0；n=0 ≈ 25%（len 8）/ 32%（len 6）；easeOut 2.5。镜头首帧入场用它，不要用 fadeIn(0)=0 */
export const softOp = (n: number, len = 8) => (n < 0 ? 0 : 1 - Math.pow(1 - clamp01((n + 1) / (len + 1)), 2.5));
/** 镜头首帧元素用：首帧 ≈57%（lessons：softOp(n+1,6)），保证首帧能被空场判据量到 */
export const firstOp = (n: number, len = 6) => (n < 0 ? 0 : softOp(n + 1, len));
/** 硬切前归零淡出：末 len 帧 1−(n/len)^1.5，N=to 时为 0 */
export const exitOp = (N: number, to: number, len = 8) => {
  const n = N - (to - len);
  return n <= 0 ? 1 : Math.max(0, 1 - Math.pow(n / len, 1.5));
};
/** 带光元素"先灭光"：归零淡出开始前 len 帧把 glow 强度 1→0（N=to−exitLen 时为 0） */
export const glowOffK = (N: number, to: number, len = 6, exitLen = 8) => 1 - clamp01((N - (to - exitLen - len)) / len);
export const mix = (a: number, b: number, t: number) => a + (b - a) * clamp01(t);
/** 两个 #rrggbb 之间按 k 混色，返回 rgb() */
export const mixHex = (a: string, b: string, k: number) => {
  const pa = [1, 3, 5].map((i) => parseInt(a.slice(i, i + 2), 16));
  const pb = [1, 3, 5].map((i) => parseInt(b.slice(i, i + 2), 16));
  const t = clamp01(k);
  return `rgb(${pa.map((v, i) => Math.round(v + (pb[i] - v) * t)).join(',')})`;
};
/** GLOW_PURPLE 的强度版（k 0→1），配 glowOffK 做"先灭光" */
export const glowPurple = (k: number) => `0 0 12px 3px rgba(102,45,248,${(0.35 * clamp01(k)).toFixed(3)}), 0 0 42px 14px rgba(102,45,248,${(0.45 * clamp01(k)).toFixed(3)})`;
export const glowPurpleS = (k: number) => `0 0 24px 8px rgba(102,45,248,${(0.6 * clamp01(k)).toFixed(3)})`;

export const SoftIn: React.FC<{N: number; f0: number; children: React.ReactNode; len?: number; dy?: number; style?: React.CSSProperties}> = ({N, f0, children, len = 8, dy = 10, style}) => {
  const n = N - f0;
  if (n < 0) return null;
  const t = clamp01((n + 1) / (len + 1)); // 首帧即 ≈25% 可见（终检 v3：n=0 为 0 会让 HUD 换词/入场各空 1 帧）
  const e = 1 - Math.pow(1 - t, 2.5);
  const extra = typeof style?.opacity === 'number' ? style.opacity : 1;
  return (
    <div style={{position: 'absolute', inset: 0, ...style, opacity: e * extra, transform: `translateY(${((1 - e) * dy).toFixed(2)}px)${style?.transform ? ' ' + style.transform : ''}`}}>
      {children}
    </div>
  );
};

// ---- 文字 ----
export type CTextProps = {
  cx: number; cy: number; size: number; weight?: number; family?: string; color?: string; letterSpacing?: number;
  dy?: number; scaleX?: number; italic?: boolean; opacity?: number; shadow?: string; style?: React.CSSProperties; children: React.ReactNode;
};
/** 以墨迹中心 (cx,cy) 摆放的单行文字（Noto CJK 墨迹比行盒中心低 3–7px → dy 默认 −2） */
export const CText: React.FC<CTextProps> = ({cx, cy, size, weight = 700, family = FONT_HEAVY, color = WHITE, letterSpacing = 0, dy = TEXT_DY, scaleX = 1, italic = false, opacity = 1, shadow, style, children}) => (
  <div style={{position: 'absolute', left: cx, top: cy + dy, transform: `translate(-50%,-50%) scaleX(${scaleX})`, whiteSpace: 'nowrap', fontFamily: family, fontWeight: weight, fontSize: size, fontStyle: italic ? 'italic' : 'normal', lineHeight: 1, color, letterSpacing, opacity, textShadow: shadow, ...style}}>
    {children}
  </div>
);
/** 英文技术词：Exo 2 紫斜体 + scaleX 压窄 */
export const TechText: React.FC<{cx: number; cy: number; text: string; fontSize?: number; color?: string; scaleX?: number; weight?: number; letterSpacing?: number; glow?: boolean; opacity?: number; style?: React.CSSProperties}> = ({cx, cy, text, fontSize = 32, color = PURPLE_TECH, scaleX = LANG === 'en' ? 1 : 0.81, weight = 600, letterSpacing = 1, glow = true, opacity = 1, style}) => (
  <CText cx={cx} cy={cy} size={fontSize} weight={weight} family={FONT_TECH} color={color} letterSpacing={letterSpacing} scaleX={scaleX} italic opacity={opacity} dy={0} shadow={glow ? '0 0 6px rgba(80,30,200,.7)' : undefined} style={style}>
    {text}
  </CText>
);
/**
 * 中英配对的副标：主体（中文胶囊 / 章名大字）下面那行另一种语言。一律**灰色小字**，不与主体同色同大小——
 * 紫色只给"当前重点"，常驻/重复出现的副标不是重点；中英两行等大又同色会读成两个主体（用户反馈：中英样式割裂）。
 */
export const TechSub: React.FC<{cx: number; cy: number; text: string; size?: number; opacity?: number; color?: string}> = ({cx, cy, text, size = 22, opacity = 1, color = GREY}) => (
  <TechText cx={cx} cy={cy} text={text} fontSize={size} color={color} glow={false} letterSpacing={1.5} opacity={opacity} />
);

/** 等宽数字/代码文字 */
export const MonoText: React.FC<{x: number; y: number; size?: number; color?: string; opacity?: number; children: React.ReactNode; style?: React.CSSProperties}> = ({x, y, size = 22, color = WHITE, opacity = 1, children, style}) => (
  <div style={{position: 'absolute', left: x, top: y, fontFamily: FONT_MONO, fontSize: size, lineHeight: 1.3, color, opacity, whiteSpace: 'pre', ...style}}>{children}</div>
);

// ---- 框 / 胶囊 ----
export type BoxProps = {x: number; y: number; w: number; h: number; r?: number; fill?: string; stroke?: string; sw?: number; dashed?: boolean; opacity?: number; glow?: string; style?: React.CSSProperties; children?: React.ReactNode};
/** 黑底白边矩形（border-box；fill 可为渐变字串；glow 传 boxShadow） */
export const Box: React.FC<BoxProps> = ({x, y, w, h, r = 0, fill = '#000', stroke = WHITE, sw = 2, dashed = false, opacity = 1, glow, style, children}) => (
  <div style={{...abs(x, y, w, h), boxSizing: 'border-box', background: fill, border: sw > 0 ? `${sw}px ${dashed ? 'dashed' : 'solid'} ${stroke}` : undefined, borderRadius: r, opacity, boxShadow: glow, ...style}}>{children}</div>
);
export type PillProps = BoxProps & {text?: React.ReactNode; fontSize?: number; weight?: number; color?: string; family?: string; textDy?: number; letterSpacing?: number; scaleX?: number};
/** 全圆角胶囊 + 居中文字（(x,y,w,h) 含描边外框） */
export const Pill: React.FC<PillProps> = ({text, fontSize = 28, weight = 700, color = WHITE, family = FONT_HEAVY, textDy = TEXT_DY, letterSpacing = 0, scaleX = 1, r, h, ...box}) => (
  <Box {...box} h={h} r={r ?? h / 2}>
    <div style={{position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', transform: `translateY(${textDy}px) scaleX(${scaleX})`, fontFamily: family, fontWeight: weight, fontSize, color, letterSpacing, lineHeight: 1, whiteSpace: 'nowrap'}}>{text}</div>
  </Box>
);
/** 大标签块（沿用「召回/精排」体系简化版）：色块 + 超粗字 scaleX .73 + 同色外发光 */
export const TagBlock: React.FC<{x: number; y: number; w?: number; h?: number; color?: string; text: string; fontSize?: number; opacity?: number; glow?: boolean; skewPx?: number; scaleX?: number}> = ({x, y, w = 237, h = 62, color = PURPLE, text, fontSize = 44, opacity = 1, glow = true, skewPx = 0, scaleX = LANG === 'en' ? 1 : 0.8}) => (
  <div style={{...abs(x, y, w, h), opacity}}>
    <div style={{position: 'absolute', inset: 0, background: color, transform: skewPx ? `skewX(${(-Math.atan2(skewPx, h) * 180) / Math.PI}deg)` : undefined, boxShadow: glow ? `0 0 28px 10px ${color}99` : undefined}} />
    <div style={{position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: FONT_HEAVY, fontWeight: 900, fontSize, color: WHITE, letterSpacing: -1, lineHeight: 1, transform: `translateY(${TEXT_DY}px) scaleX(${scaleX})`, WebkitTextStroke: '1.5px #000', paintOrder: 'stroke fill'}}>{text}</div>
  </div>
);

// ---- SVG 图形 ----
/** 全幅 1280×720 SVG 容器（默认 BLOOM） */
export const Svg: React.FC<{children: React.ReactNode; style?: React.CSSProperties; bloom?: boolean; opacity?: number}> = ({children, style, bloom = true, opacity = 1}) => (
  <svg width={1280} height={720} viewBox="0 0 1280 720" style={{position: 'absolute', left: 0, top: 0, overflow: 'visible', filter: bloom ? BLOOM : undefined, opacity, ...style}}>
    {children}
  </svg>
);
/** 任意方向直箭头（SVG <g>）：p=生长进度 0→1（自根部长出：杆先到、头随之），端点 (x1,y1) 为尖端 */
export const LineArrow: React.FC<{x0: number; y0: number; x1: number; y1: number; p?: number; rodW?: number; headL?: number; headW?: number; color?: string; opacity?: number; dashed?: boolean}> = ({x0, y0, x1, y1, p = 1, rodW = 3, headL = 22, headW = 24, color = WHITE, opacity = 1, dashed = false}) => {
  if (p <= 0) return null;
  const dx = x1 - x0, dy = y1 - y0;
  const L = Math.hypot(dx, dy) || 1;
  const ux = dx / L, uy = dy / L;
  const len = L * clamp01(p);
  const hl = Math.min(headL, len);
  const tx = x0 + ux * len, ty = y0 + uy * len; // 当前尖端
  const bx = tx - ux * hl, by = ty - uy * hl; // 头底中心
  const px = -uy, py = ux;
  const hw = (headW / 2) * (hl / headL);
  return (
    <g opacity={opacity}>
      <line x1={x0} y1={y0} x2={bx + ux * 1} y2={by + uy * 1} stroke={color} strokeWidth={rodW} strokeLinecap="butt" strokeDasharray={dashed ? '8 7' : undefined} />
      <polygon points={`${tx},${ty} ${bx + px * hw},${by + py * hw} ${bx - px * hw},${by - py * hw}`} fill={color} />
    </g>
  );
};
/** 水平箭头 div 版（左端锚 scaleX = 自根部长出）；dir 'left' 时以右端为根 */
export const ArrowH: React.FC<{x: number; y: number; w?: number; h?: number; p?: number; color?: string; dir?: 'right' | 'left'; shaft?: number; opacity?: number}> = ({x, y, w = 70, h = 27, p = 1, color = WHITE, dir = 'right', shaft = 3, opacity = 1}) => (
  <div style={{...abs(x, y, w, h), opacity, transform: `scaleX(${clamp01(p) * (dir === 'left' ? -1 : 1)})`, transformOrigin: dir === 'left' ? '100% 50%' : '0 50%'}}>
    <div style={{position: 'absolute', left: 0, top: h / 2 - shaft / 2, width: w - 20, height: shaft, background: color}} />
    <div style={{position: 'absolute', left: w - 24, top: 0, width: 0, height: 0, borderTop: `${h / 2}px solid transparent`, borderBottom: `${h / 2}px solid transparent`, borderLeft: `24px solid ${color}`}} />
  </div>
);
/** 勾 / 叉（SVG 全幅内使用，p 为 draw-on 进度） */
export const Check: React.FC<{cx: number; cy: number; size?: number; color?: string; sw?: number; p?: number; opacity?: number}> = ({cx, cy, size = 60, color = GREEN, sw = 7, p = 1, opacity = 1}) => {
  if (p <= 0 || opacity <= 0) return null; // p=0 时 linecap 会露出一个圆点（lessons；第五片 G8 报告模板未改）
  const s = size / 60;
  const pts: Array<[number, number]> = [[cx - 26 * s, cy + 2 * s], [cx - 8 * s, cy + 20 * s], [cx + 28 * s, cy - 20 * s]];
  const total = Math.hypot(pts[1][0] - pts[0][0], pts[1][1] - pts[0][1]) + Math.hypot(pts[2][0] - pts[1][0], pts[2][1] - pts[1][1]);
  return <polyline points={pts.map((q) => q.join(',')).join(' ')} fill="none" stroke={color} strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" strokeDasharray={total} strokeDashoffset={total * (1 - clamp01(p))} opacity={opacity} />;
};
export const Cross: React.FC<{cx: number; cy: number; size?: number; color?: string; sw?: number; p?: number; opacity?: number}> = ({cx, cy, size = 50, color = CORAL, sw = 7, p = 1, opacity = 1}) => {
  if (p <= 0 || opacity <= 0) return null; // 同上
  const r = size / 2;
  const d = size * Math.SQRT2;
  return (
    <g opacity={opacity} stroke={color} strokeWidth={sw} strokeLinecap="round">
      <line x1={cx - r} y1={cy - r} x2={cx + r} y2={cy + r} strokeDasharray={d} strokeDashoffset={d * (1 - clamp01(Math.min(1, p * 2)))} />
      <line x1={cx + r} y1={cy - r} x2={cx - r} y2={cy + r} strokeDasharray={d} strokeDashoffset={d * (1 - clamp01(Math.max(0, p * 2 - 1)))} />
    </g>
  );
};

// ---- 语义图标（通用：文档 / 数据库 / 文本块卡 / 模型；按主题在此补 2–5 个）----
/** 文档页：黑底白边 + 折角 + 文本线条（lines 条），label 在下方 */
export const DocIcon: React.FC<{x: number; y: number; w?: number; h?: number; lines?: number; color?: string; fill?: string; sw?: number; label?: string; labelSize?: number; opacity?: number; accent?: string; glow?: string}> = ({x, y, w = 64, h = 80, lines = 4, color = WHITE, fill = '#000', sw = 2, label, labelSize = 22, opacity = 1, accent, glow}) => {
  const f = w * 0.3;
  return (
    <div style={{...abs(x, y, w, h + (label ? labelSize + 14 : 0)), opacity}}>
      <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} style={{position: 'absolute', left: 0, top: 0, overflow: 'visible', filter: glow ? undefined : BLOOM_SOFT}}>
        <path d={`M${sw / 2},${sw / 2} H${w - f - sw / 2} L${w - sw / 2},${f + sw / 2} V${h - sw / 2} H${sw / 2} Z`} fill={fill} stroke={color} strokeWidth={sw} strokeLinejoin="round" />
        <path d={`M${w - f - sw / 2},${sw / 2} V${f + sw / 2} H${w - sw / 2}`} fill="none" stroke={color} strokeWidth={sw} strokeLinejoin="round" />
        {Array.from({length: lines}, (_, i) => {
          const ly = f + 12 + i * ((h - f - 22) / Math.max(1, lines - 1 + 0.6));
          const lw = (i === lines - 1 ? 0.55 : 0.72) * w;
          return <rect key={i} x={w * 0.14} y={ly} width={lw} height={3} fill={accent && i === 0 ? accent : color} opacity={accent && i === 0 ? 1 : 0.85} />;
        })}
      </svg>
      {label ? <CText cx={w / 2} cy={h + labelSize / 2 + 8} size={labelSize} weight={600} color={color} dy={-1}>{label}</CText> : null}
    </div>
  );
};
/** 数据库圆柱（数据库 / 索引 / 存储） */
export const DBIcon: React.FC<{cx: number; cy: number; w?: number; h?: number; color?: string; fill?: string; sw?: number; opacity?: number; label?: string; labelSize?: number; accent?: string}> = ({cx, cy, w = 120, h = 130, color = WHITE, fill = '#000', sw = 2.5, opacity = 1, label, labelSize = 24, accent}) => {
  const ry = w * 0.18;
  const x0 = cx - w / 2, y0 = cy - h / 2;
  return (
    <div style={{...abs(x0, y0, w, h + (label ? labelSize + 14 : 0)), opacity}}>
      <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} style={{position: 'absolute', left: 0, top: 0, overflow: 'visible', filter: BLOOM_SOFT}}>
        <path d={`M${sw},${ry} V${h - ry} A${w / 2 - sw},${ry} 0 0 0 ${w - sw},${h - ry} V${ry}`} fill={fill} stroke={color} strokeWidth={sw} />
        <ellipse cx={w / 2} cy={ry} rx={w / 2 - sw} ry={ry - sw / 2} fill={accent ?? fill} stroke={color} strokeWidth={sw} />
        {[0.42, 0.66].map((t) => <path key={t} d={`M${sw},${h * t} A${w / 2 - sw},${ry} 0 0 0 ${w - sw},${h * t}`} fill="none" stroke={color} strokeWidth={sw * 0.7} opacity={0.8} />)}
      </svg>
      {label ? <CText cx={w / 2} cy={h + labelSize / 2 + 8} size={labelSize} weight={600} color={color} dy={-1}>{label}</CText> : null}
    </div>
  );
};
/** 文本块 chunk 卡：黑底白边圆角 + 若干灰白文本线；active → 紫边 + 柔光 */
export const ChunkCard: React.FC<{x: number; y: number; w?: number; h?: number; lines?: number; active?: boolean; opacity?: number; r?: number; title?: string; seed?: number; sw?: number}> = ({x, y, w = 150, h = 92, lines = 4, active = false, opacity = 1, r = 8, title, seed = 1, sw = 2}) => (
  <Box x={x} y={y} w={w} h={h} r={r} stroke={active ? PURPLE_LIGHT : WHITE} sw={sw} opacity={opacity} glow={active ? GLOW_PURPLE_S : undefined}>
    {title ? <div style={{position: 'absolute', left: 12, top: 8, fontFamily: FONT_HEAVY, fontSize: 15, fontWeight: 600, color: PURPLE_LIGHT, whiteSpace: 'nowrap', lineHeight: 1}}>{title}</div> : null}
    {Array.from({length: lines}, (_, i) => {
      const lw = (0.5 + 0.42 * (((seed * 7 + i * 13) % 10) / 10)) * (w - 24);
      const top = (title ? 30 : 14) + i * ((h - (title ? 40 : 26)) / Math.max(1, lines - 0.3));
      return <div key={i} style={{position: 'absolute', left: 12, top, width: i === lines - 1 ? lw * 0.6 : lw, height: 3, background: active ? WHITE : GREY_LIGHT, opacity: 0.9}} />;
    })}
  </Box>
);
/** 大模型图标：圆角方块 + 内部"神经元"三层点阵，label 可选 */
export const LLMIcon: React.FC<{cx: number; cy: number; size?: number; color?: string; accent?: string; opacity?: number; label?: string; labelSize?: number; glow?: boolean}> = ({cx, cy, size = 140, color = WHITE, accent = PURPLE, opacity = 1, label, labelSize = 28, glow = true}) => {
  const s = size;
  const cols = [0.28, 0.5, 0.72];
  const rows = [[0.3, 0.5, 0.7], [0.22, 0.38, 0.62, 0.78], [0.3, 0.5, 0.7]];
  return (
    <div style={{...abs(cx - s / 2, cy - s / 2, s, s + (label ? labelSize + 16 : 0)), opacity}}>
      <div style={{position: 'absolute', left: 0, top: 0, width: s, height: s, boxSizing: 'border-box', background: '#000', border: `3px solid ${color}`, borderRadius: s * 0.16, boxShadow: glow ? GLOW_PURPLE : undefined}} />
      <svg width={s} height={s} viewBox={`0 0 ${s} ${s}`} style={{position: 'absolute', left: 0, top: 0}}>
        {cols.slice(0, -1).map((cxr, ci) => rows[ci].map((ry, i) => rows[ci + 1].map((ry2, j) => <line key={`${ci}-${i}-${j}`} x1={cxr * s} y1={ry * s} x2={cols[ci + 1] * s} y2={ry2 * s} stroke={GREY} strokeWidth={1.3} opacity={0.7} />)))}
        {cols.map((cxr, ci) => rows[ci].map((ry, i) => <circle key={`${ci}-${i}`} cx={cxr * s} cy={ry * s} r={s * 0.045} fill={ci === 1 ? accent : color} />))}
      </svg>
      {label ? <CText cx={s / 2} cy={s + labelSize / 2 + 10} size={labelSize} weight={700} color={color}>{label}</CText> : null}
    </div>
  );
};
/** 顶部 HUD 胶囊（沿用 (533,28,216,51) 位置，宽随文字）：GlitchIn 入场；tech 为其下方的英文副标（中心 y 92） */
export const TopCapsule: React.FC<{N: number; f0: number; text: string; w?: number; fill?: string; tech?: string; opacity?: number; textSize?: number; glitch?: boolean}> = ({N, f0, text, w = 216, fill = PURPLE, tech, opacity = 1, textSize = 33, glitch = false}) => (
  // 规范：闪烁只给重点词；HUD 换词默认用 SoftIn 淡入，glitch 需显式开
  glitch ? (
  <GlitchIn N={N} f0={f0} style={{opacity}}>
    <Pill x={640 - w / 2} y={28} w={w} h={51} fill={fill} sw={2} text={text} fontSize={textSize} weight={700} letterSpacing={1} textDy={TEXT_DY} style={{filter: PILL_SHADOW}} />
    {tech ? <TechSub cx={640} cy={92} text={tech} /> : null}
  </GlitchIn>
  ) : (
  <SoftIn N={N} f0={f0} style={{opacity}} dy={6}>
    <Pill x={640 - w / 2} y={28} w={w} h={51} fill={fill} sw={2} text={text} fontSize={textSize} weight={700} letterSpacing={1} textDy={TEXT_DY} style={{filter: PILL_SHADOW}} />
    {tech ? <TechSub cx={640} cy={92} text={tech} /> : null}
  </SoftIn>
  )
);

// ---- 漏斗层（召回→重排→生成 之类的分层筛选）----
/** 灰→紫的非对称水平渐变 stops（原片实测：最暗平台在 t≈0.5–0.6，右半升得更慢）。k=0 灰、k=1 紫。 */
const TRAP_STOPS: Array<[number, number, number[]]> = [[0, 224, [230, 220, 255]], [0.18, 190, [170, 140, 250]], [0.45, 160, [110, 60, 248]], [0.6, 160, [102, 45, 248]], [0.8, 178, [125, 85, 248]], [1, 224, [230, 220, 255]]];
export const trapStops = (k: number): Array<[number, string]> => TRAP_STOPS.map(([t, g, p]) => [t, `rgb(${p.map((v) => Math.round(g + (v - g) * k)).join(',')})`] as [number, string]);
let trapSeq = 0;
/** 倒梯形漏斗层：顶宽 wTop、底宽 wBot、高 h，水平渐变填充 + 2px 白边 + 居中文字。k 0→1 灰变紫（11 帧变色用）。 */
export const Trap: React.FC<{cx: number; y: number; wTop: number; wBot: number; h: number; k?: number; stops?: Array<[number, string]>; text?: React.ReactNode; fontSize?: number; textDy?: number; stroke?: number; textShadow?: string; opacity?: number}> = ({cx, y, wTop, wBot, h, k = 1, stops, text, fontSize = 34, textDy = TEXT_DY, stroke = 2, textShadow = '0 2px 12px rgba(0,0,0,.45)', opacity = 1}) => {
  const idRef = React.useRef<string | undefined>(undefined);
  if (!idRef.current) idRef.current = `trap-${trapSeq++}`;
  const id = idRef.current;
  const Wd = wTop + 8, x0 = cx - Wd / 2;
  const pts = `${4},${1} ${4 + wTop},${1} ${4 + (wTop + wBot) / 2},${1 + h} ${4 + (wTop - wBot) / 2},${1 + h}`;
  return (
    <div style={{...abs(x0, y, Wd, h + 4), opacity}}>
      <svg width={Wd} height={h + 4} style={{position: 'absolute', left: 0, top: 0, overflow: 'visible'}}>
        <defs>
          <linearGradient id={id} x1="0" y1="0" x2="1" y2="0">
            {(stops ?? trapStops(k)).map(([o, c], i) => <stop key={i} offset={o} stopColor={c} />)}
          </linearGradient>
        </defs>
        <polygon points={pts} fill={`url(#${id})`} stroke={WHITE} strokeWidth={stroke} strokeLinejoin="miter" />
      </svg>
      {text !== undefined ? <div style={{position: 'absolute', left: 0, top: 0, width: Wd, height: h, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: FONT_HEAVY, fontWeight: 700, fontSize, color: WHITE, lineHeight: 1, textShadow, transform: `translateY(${textDy}px)`}}>{text}</div> : null}
    </div>
  );
};

/** 通用数字计数（tabular；默认 Orbitron —— 孤立单个 "0" 会被读成 Ø，那种场合传 family={FONT_HEAVY}）*/
export const Counter: React.FC<{cx: number; cy: number; value: string | number; size?: number; color?: string; opacity?: number; weight?: number; family?: string}> = ({cx, cy, value, size = 58, color = WHITE, opacity = 1, weight = 700, family = FONT_ORB}) => (
  <CText cx={cx} cy={cy} size={size} weight={weight} family={family} color={color} opacity={opacity} letterSpacing={-0.5} shadow={TEXT_GLOW} style={{fontVariantNumeric: 'tabular-nums'}}>
    {value}
  </CText>
);

// ---- 语义图标第二组（芯片 / 时间条 / 仪表 / 集群网格 / 机架 / 人形 / 代码卡 / 仓库卡；按主题取用或删减）----
/** GPU 芯片：四边引脚 + 黑底白边圆角本体 + 内部核心方阵（lit 0–1 为点亮比例，行优先；点亮核紫、未点亮灰边）；glow 紫柔光（当主角时开）；label 在下方。size 是含引脚的外接边长。 */
export const GPUChip: React.FC<{cx: number; cy: number; size?: number; color?: string; accent?: string; lit?: number; grid?: number; opacity?: number; label?: string; labelSize?: number; glow?: boolean; pins?: boolean; sw?: number; glowK?: number}> = ({cx, cy, size = 170, color = WHITE, accent = PURPLE, lit = 1, grid = 6, opacity = 1, label, labelSize = 26, glow = true, pins = true, sw = 3, glowK = 1}) => {
  const s = size;
  const pinL = s * 0.075;
  const inner = s - 2 * pinL;
  const x0 = pinL, y0 = pinL;
  const coreArea = inner * 0.62;
  const cell = coreArea / grid;
  const c0 = x0 + (inner - coreArea) / 2;
  const nLit = Math.round(clamp01(lit) * grid * grid);
  const pinsPerSide = 7;
  const pinW = inner / (pinsPerSide * 2.4);
  return (
    <div style={{...abs(cx - s / 2, cy - s / 2, s, s + (label ? labelSize + 16 : 0)), opacity}}>
      {glow && glowK > 0.005 ? <div style={{position: 'absolute', left: x0, top: y0, width: inner, height: inner, borderRadius: inner * 0.12, boxShadow: glowPurple(glowK)}} /> : null}
      <svg width={s} height={s} viewBox={`0 0 ${s} ${s}`} style={{position: 'absolute', left: 0, top: 0, overflow: 'visible', filter: BLOOM_SOFT}}>
        {pins
          ? Array.from({length: pinsPerSide}, (_, i) => {
              const t = x0 + inner * ((i + 0.5) / pinsPerSide) - pinW / 2;
              return (
                <g key={i} fill={color} opacity={0.9}>
                  <rect x={t} y={0} width={pinW} height={pinL} />
                  <rect x={t} y={s - pinL} width={pinW} height={pinL} />
                  <rect x={0} y={t} width={pinL} height={pinW} />
                  <rect x={s - pinL} y={t} width={pinL} height={pinW} />
                </g>
              );
            })
          : null}
        <rect x={x0 + sw / 2} y={y0 + sw / 2} width={inner - sw} height={inner - sw} rx={inner * 0.12} fill="#000" stroke={color} strokeWidth={sw} />
        {Array.from({length: grid * grid}, (_, i) => {
          const r = Math.floor(i / grid), c = i % grid;
          const on = i < nLit;
          return <rect key={i} x={c0 + c * cell + cell * 0.12} y={c0 + r * cell + cell * 0.12} width={cell * 0.76} height={cell * 0.76} rx={cell * 0.12} fill={on ? accent : '#141414'} stroke={on ? 'none' : GREY_LINE} strokeWidth={1} />;
        })}
      </svg>
      {label ? <CText cx={s / 2} cy={s + labelSize / 2 + 10} size={labelSize} weight={700} color={color}>{label}</CText> : null}
    </div>
  );
};

/** 时间线条（profiler 轨 / GPU 利用率）：一行分段条，segs 的 f 为占比（和 ≈1），kind: busy 紫 / idle 黑底灰虚边 / comm 橙 / cpu 灰 / sync 浅紫（profiler 面板里的通信段，避免与 idle 橙光撞色，QC v1 C2 #2）；p 为自左 draw-on 比例；label 为左侧轨名（灰 22px）。
 *  glowIdleK（0–1，glowIdle=true 等于 1）给所有 idle 段橙光（"这里是问题"）——**画在裁切容器之外**（否则被 overflow:hidden 裁掉），可渐亮 / 渐灭。 */
export type TlSeg = {f: number; kind: 'busy' | 'idle' | 'comm' | 'cpu' | 'sync'};
export const TimelineBar: React.FC<{x: number; y: number; w: number; h?: number; segs: TlSeg[]; p?: number; label?: string; labelW?: number; labelSize?: number; opacity?: number; sw?: number; glowIdle?: boolean; glowIdleK?: number}> = ({x, y, w, h = 44, segs, p = 1, label, labelW = 110, labelSize = 22, opacity = 1, sw = 2, glowIdle = false, glowIdleK}) => {
  const bw = w - (label ? labelW : 0);
  const gk = clamp01(glowIdleK ?? (glowIdle ? 1 : 0));
  const fill: Record<TlSeg['kind'], string> = {busy: PURPLE, idle: '#000', comm: ORANGE, cpu: GREY_MID, sync: PURPLE_LIGHT};
  let acc = 0;
  const segsX = segs.map((sg) => { const sx = acc * bw; acc += sg.f; return {...sg, sx, sw: sg.f * bw}; });
  const shown = bw * clamp01(p);
  return (
    <div style={{...abs(x, y, w, h), opacity}}>
      {label ? <CText cx={labelW / 2 - 6} cy={h / 2} size={labelSize} weight={600} color={GREY}>{label}</CText> : null}
      {gk > 0.005
        ? segsX.filter((sg) => sg.kind === 'idle' && sg.sx < shown).map((sg, i) => (
            <div key={`g${i}`} style={{position: 'absolute', left: (label ? labelW : 0) + sg.sx, top: 0, width: Math.min(sg.sw, shown - sg.sx), height: h, borderRadius: 4, boxShadow: `0 0 ${Math.round(40 * gk)}px rgba(243,95,69,${(0.75 * gk).toFixed(3)}), 0 0 ${Math.round(100 * gk)}px 10px rgba(243,95,69,${(0.25 * gk).toFixed(3)})`}} />
          ))
        : null}
      <div style={{position: 'absolute', left: label ? labelW : 0, top: 0, width: shown, height: h, overflow: 'hidden'}}>
        {segsX.map((sg, i) => {
          const idle = sg.kind === 'idle';
          return <div key={i} style={{position: 'absolute', left: sg.sx, top: 0, width: sg.sw, height: h, boxSizing: 'border-box', background: fill[sg.kind], border: `${sw}px ${idle ? 'dashed' : 'solid'} ${idle ? GREY : WHITE}`, borderRadius: 4}} />;
        })}
      </div>
    </div>
  );
};

/** 仪表盘（"fed at full throttle" 的油门 / 利用率表）：240° 弧（−210°→30°），v∈[0,1]；已到弧段紫 + 柔光、其余灰；白指针；value 可选大数字（Orbitron）在表盘下部，label 灰字在表下。半径 r ≥120 才够主角尺寸（整体高 ≈1.7r）。 */
export const Gauge: React.FC<{cx: number; cy: number; r?: number; v: number; color?: string; accent?: string; sw?: number; label?: string; labelSize?: number; value?: string; valueSize?: number; opacity?: number; glow?: boolean}> = ({cx, cy, r = 120, v, color = WHITE, accent = PURPLE, sw = 8, label, labelSize = 24, value, valueSize = 44, opacity = 1, glow = true}) => {
  const a0 = -210, a1 = 30;
  const vv = clamp01(v);
  const toXY = (deg: number, rr: number): [number, number] => [cx + rr * Math.cos((deg * Math.PI) / 180), cy + rr * Math.sin((deg * Math.PI) / 180)];
  const arc = (from: number, to: number, rr: number) => {
    const [ax, ay] = toXY(from, rr), [bx, by] = toXY(to, rr);
    return `M${ax},${ay} A${rr},${rr} 0 ${to - from > 180 ? 1 : 0} 1 ${bx},${by}`;
  };
  const av = a0 + (a1 - a0) * vv;
  const [nx, ny] = toXY(av, r - sw - 10);
  return (
    <div style={{position: 'absolute', inset: 0, opacity, pointerEvents: 'none'}}>
      <svg width={1280} height={720} viewBox="0 0 1280 720" style={{position: 'absolute', left: 0, top: 0, overflow: 'visible', filter: BLOOM_SOFT}}>
        <path d={arc(a0, a1, r)} fill="none" stroke={GREY_LINE} strokeWidth={sw} strokeLinecap="round" />
        {vv > 0.005 ? <path d={arc(a0, av, r)} fill="none" stroke={accent} strokeWidth={sw} strokeLinecap="round" style={glow ? {filter: 'drop-shadow(0 0 10px rgba(102,45,248,.85))'} : undefined} /> : null}
        {Array.from({length: 9}, (_, i) => {
          const d = a0 + ((a1 - a0) * i) / 8;
          const [tx0, ty0] = toXY(d, r - sw - 4), [tx1, ty1] = toXY(d, r - sw - 14);
          return <line key={i} x1={tx0} y1={ty0} x2={tx1} y2={ty1} stroke={color} strokeWidth={2} opacity={0.8} />;
        })}
        <line x1={cx} y1={cy} x2={nx} y2={ny} stroke={color} strokeWidth={4} strokeLinecap="round" />
        <circle cx={cx} cy={cy} r={9} fill="#000" stroke={color} strokeWidth={3} />
      </svg>
      {value ? <CText cx={cx} cy={cy + r * 0.68} size={valueSize} weight={700} family={FONT_ORB} color={WHITE} shadow={TEXT_GLOW}>{value}</CText> : null}
      {label ? <CText cx={cx} cy={cy + r + labelSize + 6} size={labelSize} weight={600} color={GREY}>{label}</CText> : null}
    </div>
  );
};

/** 集群方阵（表现"多"：8 → 80,000 GPUs）：cols×rows 个 ≥6px 方块（SVG，单帧 DOM 预算 ≤600 → 方阵 ≤ ~450 格），前 lit 个点亮为 accent，其余灰边；scatter=true 用确定性乱序点亮（"陆续上线"）。 */
export const ClusterGrid: React.FC<{x: number; y: number; cols: number; rows: number; cell?: number; gap?: number; lit?: number; color?: string; accent?: string; opacity?: number; seed?: number; scatter?: boolean}> = ({x, y, cols, rows, cell = 14, gap = 6, lit, color = GREY_LINE, accent = PURPLE, opacity = 1, seed = 1, scatter = false}) => {
  const n = cols * rows;
  const nl = lit === undefined ? n : Math.max(0, Math.min(n, Math.round(lit)));
  const order = Array.from({length: n}, (_, i) => i);
  if (scatter) for (let i = n - 1; i > 0; i--) { const j = Math.floor(rnd(seed, i) * (i + 1)); const t = order[i]; order[i] = order[j]; order[j] = t; }
  const rank: number[] = new Array(n); order.forEach((idx, k) => { rank[idx] = k; });
  const W2 = cols * (cell + gap) - gap, H2 = rows * (cell + gap) - gap;
  return (
    <div style={{...abs(x, y, W2, H2), opacity}}>
      <svg width={W2} height={H2} viewBox={`0 0 ${W2} ${H2}`} style={{position: 'absolute', left: 0, top: 0, overflow: 'visible'}}>
        {Array.from({length: n}, (_, i) => {
          const r = Math.floor(i / cols), c = i % cols;
          const on = rank[i] < nl;
          return <rect key={i} x={c * (cell + gap) + 0.5} y={r * (cell + gap) + 0.5} width={cell - 1} height={cell - 1} rx={2} fill={on ? accent : '#000'} stroke={on ? accent : color} strokeWidth={1} opacity={on ? 1 : 0.8} />;
        })}
      </svg>
    </div>
  );
};

/** 机架：竖框 + units 层服务器（每层左侧状态灯：前 lit 层紫、其余灰）；glow 紫柔光；label 下方。h ≥170 才够主角。 */
export const RackIcon: React.FC<{cx: number; cy: number; w?: number; h?: number; units?: number; lit?: number; color?: string; accent?: string; sw?: number; opacity?: number; label?: string; labelSize?: number; glow?: boolean}> = ({cx, cy, w = 110, h = 200, units = 6, lit, color = WHITE, accent = PURPLE, sw = 2.5, opacity = 1, label, labelSize = 22, glow = false}) => {
  const nl = lit ?? units;
  const uh = (h - 2 * sw - 8) / units;
  return (
    <div style={{...abs(cx - w / 2, cy - h / 2, w, h + (label ? labelSize + 14 : 0)), opacity}}>
      {glow ? <div style={{position: 'absolute', left: 0, top: 0, width: w, height: h, borderRadius: 8, boxShadow: GLOW_PURPLE}} /> : null}
      <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} style={{position: 'absolute', left: 0, top: 0, overflow: 'visible', filter: BLOOM_SOFT}}>
        <rect x={sw / 2} y={sw / 2} width={w - sw} height={h - sw} rx={8} fill="#000" stroke={color} strokeWidth={sw} />
        {Array.from({length: units}, (_, i) => {
          const y = sw + 4 + i * uh;
          const on = i < nl;
          return (
            <g key={i}>
              <rect x={sw + 6} y={y + 3} width={w - 2 * sw - 12} height={uh - 6} rx={3} fill="#0a0a0a" stroke={GREY_MID} strokeWidth={1.5} />
              <circle cx={sw + 16} cy={y + uh / 2} r={3.5} fill={on ? accent : GREY_LINE} />
              <rect x={sw + 28} y={y + uh / 2 - 1.5} width={w - 2 * sw - 44} height={3} fill={on ? GREY_LIGHT : GREY_LINE} opacity={0.8} />
            </g>
          );
        })}
      </svg>
      {label ? <CText cx={w / 2} cy={h + labelSize / 2 + 6} size={labelSize} weight={600} color={color}>{label}</CText> : null}
    </div>
  );
};

/** 人形（头 + 肩）：团队角色；accent 给肩部填充（当前重点）；glow 紫光；label 下方。size ≥96。 */
export const PersonIcon: React.FC<{cx: number; cy: number; size?: number; color?: string; fill?: string; sw?: number; label?: string; labelSize?: number; accent?: string; opacity?: number; glow?: boolean}> = ({cx, cy, size = 96, color = WHITE, fill = '#000', sw = 2.5, label, labelSize = 22, accent, opacity = 1, glow = false}) => {
  const s = size;
  const hr = s * 0.2;
  return (
    <div style={{...abs(cx - s / 2, cy - s / 2, s, s + (label ? labelSize + 14 : 0)), opacity}}>
      <svg width={s} height={s} viewBox={`0 0 ${s} ${s}`} style={{position: 'absolute', left: 0, top: 0, overflow: 'visible', filter: glow ? 'drop-shadow(0 0 10px rgba(102,45,248,.75))' : BLOOM_SOFT}}>
        <path d={`M${sw},${s - sw} V${s * 0.8} A${s / 2 - sw},${s * 0.3} 0 0 1 ${s - sw},${s * 0.8} V${s - sw} Z`} fill={accent ?? fill} stroke={color} strokeWidth={sw} strokeLinejoin="round" />
        <circle cx={s / 2} cy={hr + sw + s * 0.06} r={hr} fill={fill} stroke={color} strokeWidth={sw} />
      </svg>
      {label ? <CText cx={s / 2} cy={s + labelSize / 2 + 6} size={labelSize} weight={600} color={color}>{label}</CText> : null}
    </div>
  );
};

/** 代码卡：黑底白边圆角 + 左上语言标签（22px，**画在卡外上方 17px**，有流程轨的章注意 y）+ 等宽代码线条；hot 行橙色发光（"热点"）；active → 紫边柔光。 */
export const CodeCard: React.FC<{x: number; y: number; w?: number; h?: number; tag?: string; tagColor?: string; lines?: number; hot?: number; active?: boolean; seed?: number; opacity?: number; r?: number; glowK?: number}> = ({x, y, w = 220, h = 150, tag, tagColor = PURPLE, lines = 5, hot = -1, active = false, seed = 1, opacity = 1, r = 10, glowK = 1}) => (
  <Box x={x} y={y} w={w} h={h} r={r} stroke={active ? PURPLE_LIGHT : WHITE} sw={2} opacity={opacity} glow={active && glowK > 0.005 ? glowPurpleS(glowK) : undefined}>
    {tag ? <Pill x={14} y={-17} w={Math.max(76, Math.round(tag.length * 13.5) + 30)} h={34} fill={tagColor} sw={2} text={tag} fontSize={22} weight={700} /> : null}
    {Array.from({length: lines}, (_, i) => {
      const indent = ((seed * 3 + i * 5) % 3) * 14;
      const lw = (0.35 + 0.5 * (((seed * 7 + i * 13) % 10) / 10)) * (w - 40 - indent);
      const top = 30 + i * ((h - 44) / lines);
      const isHot = i === hot;
      return <div key={i} style={{position: 'absolute', left: 18 + indent, top, width: lw, height: 4, borderRadius: 2, background: isHot ? ORANGE : GREY_LIGHT, opacity: isHot ? 1 : 0.85, boxShadow: isHot ? GLOW_ORANGE : undefined}} />;
    })}
  </Box>
);

/** 开源仓库卡：黑底白边圆角 + 左侧分叉小图标 + 仓库名（700）+ 一行灰说明；active → 紫边柔光 + 分叉底点紫。 */
export const RepoCard: React.FC<{x: number; y: number; w?: number; h?: number; name: string; desc?: string; active?: boolean; opacity?: number; nameSize?: number; descSize?: number}> = ({x, y, w = 360, h = 84, name, desc, active = false, opacity = 1, nameSize = 28, descSize = 22}) => {
  const sc = active ? PURPLE_LIGHT : WHITE;
  return (
    <Box x={x} y={y} w={w} h={h} r={12} stroke={sc} sw={2} opacity={opacity} glow={active ? GLOW_PURPLE_S : undefined}>
      <svg width={44} height={44} viewBox="0 0 44 44" style={{position: 'absolute', left: 16, top: h / 2 - 22}}>
        <path d="M12,14 V20 Q12,26 18,26 H26 Q32,26 32,20 V14 M22,26 V31" fill="none" stroke={sc} strokeWidth={2.5} />
        <circle cx={12} cy={9} r={5} fill="#000" stroke={sc} strokeWidth={2.5} />
        <circle cx={32} cy={9} r={5} fill="#000" stroke={sc} strokeWidth={2.5} />
        <circle cx={22} cy={36} r={5} fill={active ? PURPLE : '#000'} stroke={sc} strokeWidth={2.5} />
      </svg>
      <div style={{position: 'absolute', left: 74, top: desc ? 14 : h / 2 - nameSize / 2 - 2, fontFamily: FONT_HEAVY, fontSize: nameSize, fontWeight: 700, color: WHITE, lineHeight: 1, whiteSpace: 'nowrap'}}>{name}</div>
      {desc ? <div style={{position: 'absolute', left: 74, top: 14 + nameSize + 8, fontFamily: FONT_HEAVY, fontSize: descSize, fontWeight: 500, color: GREY, lineHeight: 1, whiteSpace: 'nowrap'}}>{desc}</div> : null}
    </Box>
  );
};
