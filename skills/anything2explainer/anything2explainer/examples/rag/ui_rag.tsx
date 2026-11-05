import React from 'react';
import {FONT_HEAVY} from '../shared/lib';
import {FONT_TECH, FONT_MONO} from './common/fonts';
import {GlitchIn, powOutRemain, BEZ_SCALE_IN, clamp01} from './common';

/**
 * RAG 片共用图元与调色板（沿用推荐系统片：黑填充 + 白描边 2–3px、紫 = 当前重点、橙红 = 指标/警示、灰 = 非重点）。
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


/** 非闪烁入场（用户裁定：glitch 只给重点词，其余文字/标签一律用它）：len 帧 easeOut 淡入 + dy px 上浮；n<0 不渲染。签名与 GlitchIn 对齐（N,f0,children,style），可直接替换。 */
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
export const CText: React.FC<CTextProps> = ({cx, cy, size, weight = 700, family = FONT_HEAVY, color = WHITE, letterSpacing = 0, dy = -2, scaleX = 1, italic = false, opacity = 1, shadow, style, children}) => (
  <div style={{position: 'absolute', left: cx, top: cy + dy, transform: `translate(-50%,-50%) scaleX(${scaleX})`, whiteSpace: 'nowrap', fontFamily: family, fontWeight: weight, fontSize: size, fontStyle: italic ? 'italic' : 'normal', lineHeight: 1, color, letterSpacing, opacity, textShadow: shadow, ...style}}>
    {children}
  </div>
);
/** 英文技术词：Exo 2 紫斜体 + scaleX 压窄 */
export const TechText: React.FC<{cx: number; cy: number; text: string; fontSize?: number; color?: string; scaleX?: number; weight?: number; letterSpacing?: number; glow?: boolean; opacity?: number; style?: React.CSSProperties}> = ({cx, cy, text, fontSize = 32, color = PURPLE_TECH, scaleX = 0.81, weight = 600, letterSpacing = 1, glow = true, opacity = 1, style}) => (
  <CText cx={cx} cy={cy} size={fontSize} weight={weight} family={FONT_TECH} color={color} letterSpacing={letterSpacing} scaleX={scaleX} italic opacity={opacity} dy={0} shadow={glow ? '0 0 6px rgba(80,30,200,.7)' : undefined} style={style}>
    {text}
  </CText>
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
export const Pill: React.FC<PillProps> = ({text, fontSize = 28, weight = 700, color = WHITE, family = FONT_HEAVY, textDy = -2, letterSpacing = 0, scaleX = 1, r, h, ...box}) => (
  <Box {...box} h={h} r={r ?? h / 2}>
    <div style={{position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', transform: `translateY(${textDy}px) scaleX(${scaleX})`, fontFamily: family, fontWeight: weight, fontSize, color, letterSpacing, lineHeight: 1, whiteSpace: 'nowrap'}}>{text}</div>
  </Box>
);
/** 大标签块（沿用「召回/精排」体系简化版）：色块 + 超粗字 scaleX .73 + 同色外发光 */
export const TagBlock: React.FC<{x: number; y: number; w?: number; h?: number; color?: string; text: string; fontSize?: number; opacity?: number; glow?: boolean; skewPx?: number}> = ({x, y, w = 237, h = 62, color = PURPLE, text, fontSize = 44, opacity = 1, glow = true, skewPx = 0}) => (
  <div style={{...abs(x, y, w, h), opacity}}>
    <div style={{position: 'absolute', inset: 0, background: color, transform: skewPx ? `skewX(${(-Math.atan2(skewPx, h) * 180) / Math.PI}deg)` : undefined, boxShadow: glow ? `0 0 28px 10px ${color}99` : undefined}} />
    <div style={{position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: FONT_HEAVY, fontWeight: 900, fontSize, color: WHITE, letterSpacing: -1, lineHeight: 1, transform: 'translateY(-2px) scaleX(0.8)', WebkitTextStroke: '1.5px #000', paintOrder: 'stroke fill'}}>{text}</div>
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
  const s = size / 60;
  const pts: Array<[number, number]> = [[cx - 26 * s, cy + 2 * s], [cx - 8 * s, cy + 20 * s], [cx + 28 * s, cy - 20 * s]];
  const total = Math.hypot(pts[1][0] - pts[0][0], pts[1][1] - pts[0][1]) + Math.hypot(pts[2][0] - pts[1][0], pts[2][1] - pts[1][1]);
  return <polyline points={pts.map((q) => q.join(',')).join(' ')} fill="none" stroke={color} strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" strokeDasharray={total} strokeDashoffset={total * (1 - clamp01(p))} opacity={opacity} />;
};
export const Cross: React.FC<{cx: number; cy: number; size?: number; color?: string; sw?: number; p?: number; opacity?: number}> = ({cx, cy, size = 50, color = CORAL, sw = 7, p = 1, opacity = 1}) => {
  const r = size / 2;
  const d = size * Math.SQRT2;
  return (
    <g opacity={opacity} stroke={color} strokeWidth={sw} strokeLinecap="round">
      <line x1={cx - r} y1={cy - r} x2={cx + r} y2={cy + r} strokeDasharray={d} strokeDashoffset={d * (1 - clamp01(Math.min(1, p * 2)))} />
      <line x1={cx + r} y1={cy - r} x2={cx - r} y2={cy + r} strokeDasharray={d} strokeDashoffset={d * (1 - clamp01(Math.max(0, p * 2 - 1)))} />
    </g>
  );
};

// ---- 语义图标（RAG 主题）----
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
/** 数据库圆柱（向量数据库 / 索引） */
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
  // 用户裁定（2026-09-06）：闪烁只给重点词；HUD 换词默认用 SoftIn 淡入，glitch 需显式开
  glitch ? (
  <GlitchIn N={N} f0={f0} style={{opacity}}>
    <Pill x={640 - w / 2} y={28} w={w} h={51} fill={fill} sw={2} text={text} fontSize={textSize} weight={700} letterSpacing={1} textDy={-2} style={{filter: PILL_SHADOW}} />
    {tech ? <TechText cx={640} cy={94} text={tech} fontSize={30} scaleX={0.8} /> : null}
  </GlitchIn>
  ) : (
  <SoftIn N={N} f0={f0} style={{opacity}} dy={6}>
    <Pill x={640 - w / 2} y={28} w={w} h={51} fill={fill} sw={2} text={text} fontSize={textSize} weight={700} letterSpacing={1} textDy={-2} style={{filter: PILL_SHADOW}} />
    {tech ? <TechText cx={640} cy={94} text={tech} fontSize={30} scaleX={0.8} /> : null}
  </SoftIn>
  )
);
/** 通用数字计数（tabular）*/
export const Counter: React.FC<{cx: number; cy: number; value: string | number; size?: number; color?: string; opacity?: number; weight?: number}> = ({cx, cy, value, size = 58, color = WHITE, opacity = 1, weight = 700}) => (
  <CText cx={cx} cy={cy} size={size} weight={weight} color={color} opacity={opacity} letterSpacing={-0.5} shadow={TEXT_GLOW} style={{fontVariantNumeric: 'tabular-nums'}}>
    {value}
  </CText>
);
