import React from 'react';
import {FONT_ORB} from './common/lib';
import {clamp01, easeInOutPow} from './common';
import {CText, PURPLE, PURPLE_LIGHT, WHITE, GLOW_PURPLE, abs} from './ui';

/**
 * 光效 / 高光时刻 / 纵深 / 运镜 图元（从样片《RAG 与知识库》各组辅助文件升级而来；规则见 reference/composition-and-light.md）。
 * 镜头里 `import {…} from '../../fx'`。全部纯函数：动画量由镜头按 N 算好传入，或传 N/f0 让组件自己算相对帧。
 * 用途速查：
 *   LightBar / LightSweep  紫光条横扫（高光时刻开场，三轮）
 *   StageLine              中央舞台光线：展宽 → 呼吸 → 节拍帧白闪 3 帧后消失
 *   GhostText              主角文字的白描边轮廓 10% 隐现（预示）
 *   HaloRing               主体脚下的紫色光环（外环内环白描边 + 紫渐变 + 虚线波纹），可分前后半环夹住主体
 *   HeroGlow               给任何矩形主角加双层紫柔光 + 30 帧呼吸
 *   BigNumber / countTo    大数字（Orbitron + 紫硬投影 + 白光），tabular，可计数
 *   Sparkle / GradBall     四角小星 / 顶亮底黑小球
 *   TiltPlane              倾斜平面（纵深层）
 *   CameraRig / camAt      定点推近 / 平移 / 整页滚动的相机（世界坐标 → 屏幕）
 *   SET_PIECE / setPiece   登场型高光时刻的标准相对帧
 */

// ---- 紫光条 ----
/** 单条光条：黑底上的紫色渐变条 + 紫外发光 + 白芯。alpha 为整体透明度。 */
export const LightBar: React.FC<{x: number; y: number; w: number; h: number; alpha?: number; color?: string; core?: boolean}> = ({x, y, w, h, alpha = 0.3, color = PURPLE_LIGHT, core = true}) => (
  <div style={{...abs(x, y, w, h), opacity: alpha}}>
    <div style={{position: 'absolute', inset: 0, borderRadius: h / 2, background: `linear-gradient(90deg, transparent 0%, ${color} 16%, ${color} 84%, transparent 100%)`, boxShadow: `0 0 ${h * 2.4}px ${h * 0.9}px rgba(102,45,248,.6)`}} />
    {core ? <div style={{position: 'absolute', left: w * 0.18, right: w * 0.18, top: h * 0.3, height: h * 0.4, borderRadius: h, background: 'linear-gradient(90deg, transparent 0%, #FFFFFF 28%, #FFFFFF 72%, transparent 100%)', boxShadow: '0 0 6px 1px rgba(255,255,255,.75)'}} /> : null}
  </div>
);
/** 光条 x：n 帧内自左 −w 扫到 1280+w（easeInOut 1.6） */
export const sweepX = (n: number, w: number, len = 16) => -w + (1280 + 2 * w) * easeInOutPow(1.6)(clamp01(n / len));
/** 默认三条光条 [y, h, w, 帧偏移]（样片 SC08） */
export const SWEEP_BARS: Array<[number, number, number, number]> = [[292, 6, 420, 0], [334, 10, 560, 2], [378, 6, 380, 4]];
/**
 * 一轮或多轮横扫：rounds 为各轮起始帧（样片 3 轮，轮距 18 帧首尾相接），alphas 各轮透明度；dy 整体上下平移（让光线对准主角中心）。
 * 每轮 3 条、2 帧错峰、16 帧；末段按 (1−t^6) 收尾，避免硬消失。
 */
export const LightSweep: React.FC<{N: number; rounds: number[]; alphas?: number[]; bars?: Array<[number, number, number, number]>; dy?: number; len?: number}> = ({N, rounds, alphas = [0.6, 0.55, 0.55], bars = SWEEP_BARS, dy = 0, len = 16}) => (
  <>
    {rounds.map((t0, k) =>
      bars.map(([y, h, w, off], i) => {
        const n = N - t0 - off;
        if (n < 0 || n > len) return null;
        return <LightBar key={`${k}-${i}`} x={sweepX(n, w, len)} y={y + dy - h / 2} w={w} h={h} alpha={(alphas[k] ?? 0.55) * (1 - Math.pow(clamp01(n / len), 6))} />;
      }),
    )}
  </>
);

// ---- 舞台光线 ----
/**
 * 中央光线：f0 起 14 帧展宽到 w（幂 2.5 缓出），之后 α 呼吸 .45±.15；flashAt 起 3 帧白闪（.95/.7/.35）然后消失。
 * 用法：主角 GlitchIn 的节拍帧 = flashAt。
 */
export const StageLine: React.FC<{N: number; f0: number; flashAt?: number; cx?: number; cy?: number; w?: number; h?: number}> = ({N, f0, flashAt = Infinity, cx = 640, cy = 331, w = 720, h = 3}) => {
  const n = N - f0;
  if (n < 0) return null;
  const flash = N >= flashAt ? N - flashAt : -1;
  if (flash >= 3) return null;
  const lineW = w * (1 - Math.pow(1 - clamp01(n / 14), 2.5));
  const breathe = 0.45 + 0.15 * Math.sin(n * 0.28);
  return (
    <div style={{position: 'absolute', left: cx - lineW / 2, top: cy - h / 2, width: lineW, height: h, borderRadius: h, background: flash >= 0 ? WHITE : `linear-gradient(90deg, transparent, ${PURPLE_LIGHT} 20%, ${PURPLE_LIGHT} 80%, transparent)`, opacity: flash >= 0 ? [0.95, 0.7, 0.35][flash] : breathe, boxShadow: flash >= 0 ? '0 0 30px 8px rgba(255,255,255,.55)' : '0 0 18px 4px rgba(102,45,248,.5)'}} />
  );
};

// ---- 幽灵轮廓 ----
/** 主角文字的白描边、透明填充、紫雾轮廓：opacity 由调用方给（样片 (0.1+0.02·sin)·fadeIn(n,12)，glitch 期间保留作底，pulse 起撤掉） */
export const GhostText: React.FC<{cx: number; cy: number; size: number; family?: string; weight?: number; letterSpacing?: number; opacity: number; dy?: number; scaleX?: number; children: React.ReactNode}> = ({cx, cy, size, family, weight = 400, letterSpacing = 8, opacity, dy = -4, scaleX = 1, children}) => {
  if (opacity <= 0) return null;
  return (
    <CText cx={cx} cy={cy} size={size} weight={weight} family={family} letterSpacing={letterSpacing} color="transparent" dy={dy} scaleX={scaleX} opacity={opacity} shadow="0 0 22px rgba(161,117,241,.95)" style={{WebkitTextStroke: `2px ${WHITE}`}}>
      {children}
    </CText>
  );
};
/** 幽灵轮廓的标准透明度：f0 起 12 帧淡入到 0.10 并呼吸，到 until 帧撤掉 */
export const ghostOpacity = (N: number, f0: number, until: number) => {
  const n = N - f0;
  if (n < 0 || N >= until) return 0;
  return (0.1 + 0.02 * Math.sin(n * 0.35)) * clamp01(n / 12);
};

// ---- 光环 ----
const ellipsePerim = (rx: number, ry: number) => Math.PI * (3 * (rx + ry) - Math.sqrt((3 * rx + ry) * (rx + 3 * ry)));
let haloSeq = 0;
/**
 * 主体脚下的紫色光环（样片 SC44 护城河）：外环 rxo×ryo、内环 rxi×ryi；p 为白描边 draw-on 进度 0→1；fillOp 为紫渐变填充透明度；
 * phase 为虚线波纹相位（样片 floor(n/2)*5）。half='back' 只画 cy 以上的后半环、'front' 只画前半环——先 back、再主体、再 front 即可让主体"站在环里"。
 */
export const HaloRing: React.FC<{cx?: number; cy?: number; rxo?: number; ryo?: number; rxi?: number; ryi?: number; p?: number; fillOp?: number; phase?: number; half?: 'back' | 'front' | 'both'; opacity?: number; ripples?: boolean}> = ({cx = 640, cy = 428, rxo = 335, ryo = 78, rxi = 245, ryi = 44, p = 1, fillOp = 0.85, phase = 0, half = 'both', opacity = 1, ripples = true}) => {
  const idRef = React.useRef<string | undefined>(undefined);
  if (!idRef.current) idRef.current = `halo-${haloSeq++}`;
  const id = idRef.current;
  const pe = 1 - Math.pow(1 - clamp01(p), 2);
  const PO = ellipsePerim(rxo, ryo), PI = ellipsePerim(rxi, ryi);
  const e = (rx: number, ry: number) => `M ${cx - rx} ${cy} a ${rx} ${ry} 0 1 0 ${rx * 2} 0 a ${rx} ${ry} 0 1 0 ${-rx * 2} 0 Z`;
  const ring = `${e(rxo, ryo)} ${e(rxi, ryi)}`;
  const clip = half === 'back' ? `url(#${id}-back)` : half === 'front' ? `url(#${id}-front)` : undefined;
  return (
    <svg width={1280} height={720} viewBox="0 0 1280 720" style={{position: 'absolute', left: 0, top: 0, overflow: 'visible', filter: 'drop-shadow(0 0 3px rgba(255,255,255,0.45))', opacity}}>
      <defs>
        <linearGradient id={`${id}-g`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#3A1E8C" />
          <stop offset="55%" stopColor={PURPLE} />
          <stop offset="100%" stopColor="#8F62F5" />
        </linearGradient>
        <clipPath id={`${id}-back`}><rect x={0} y={0} width={1280} height={cy} /></clipPath>
        <clipPath id={`${id}-front`}><rect x={0} y={cy} width={1280} height={720 - cy} /></clipPath>
      </defs>
      <g clipPath={clip}>
        <path d={ring} fill={`url(#${id}-g)`} fillRule="evenodd" opacity={fillOp} />
        <ellipse cx={cx} cy={cy} rx={rxo} ry={ryo} fill="none" stroke={WHITE} strokeWidth={2.5} strokeDasharray={PO} strokeDashoffset={PO * (1 - pe)} />
        <ellipse cx={cx} cy={cy} rx={rxi} ry={ryi} fill="none" stroke={WHITE} strokeWidth={2.5} strokeDasharray={PI} strokeDashoffset={PI * (1 - pe)} />
        {ripples ? [0.3, 0.55, 0.8].map((t, i) => (
          <ellipse key={i} cx={cx} cy={cy} rx={rxi + (rxo - rxi) * t} ry={ryi + (ryo - ryi) * t} fill="none" stroke={PURPLE_LIGHT} strokeWidth={1.6} strokeDasharray="16 22" strokeDashoffset={phase * (i % 2 ? -1 : 1) + i * 9} opacity={0.55 * fillOp} />
        )) : null}
      </g>
    </svg>
  );
};

// ---- 主角柔光 ----
/** 给矩形主角加双层紫柔光：放在主角组件之下，同位同尺寸。N 传入时 30 帧周期呼吸 ±15%；k 为强度 0→1（激活 8 帧渐亮用）。 */
export const HeroGlow: React.FC<{x: number; y: number; w: number; h: number; r?: number; N?: number; k?: number; color?: string}> = ({x, y, w, h, r = 16, N, k = 1, color}) => {
  const breathe = N === undefined ? 1 : 1 + 0.15 * Math.sin((2 * Math.PI * N) / 30);
  const a = clamp01(k) * breathe;
  if (a <= 0.01) return null;
  const glow = color ? `0 0 ${(12 * a).toFixed(0)}px ${(3 * a).toFixed(0)}px ${color}59, 0 0 ${(42 * a).toFixed(0)}px ${(14 * a).toFixed(0)}px ${color}73` : GLOW_PURPLE;
  return <div style={{...abs(x, y, w, h), borderRadius: r, boxShadow: glow, opacity: color ? clamp01(k) : a}} />;
};

// ---- 大数字 ----
export const fmtInt = (v: number) => Math.round(v).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
/** len 帧内从 a 计数到 b（幂 2 缓出），返回取整字符串（千分位） */
export const countTo = (n: number, a: number, b: number, len = 20) => fmtInt(a + (b - a) * (1 - Math.pow(1 - clamp01(n / len), 2)));
/** 大数字：Orbitron tabular + 紫硬投影 6px + 紫柔光（片名同款"重"字处理）；unit 为下方小字 */
export const BigNumber: React.FC<{cx: number; cy: number; value: string | number; size?: number; color?: string; family?: string; weight?: number; letterSpacing?: number; shadow?: string; unit?: string; unitSize?: number; unitColor?: string; opacity?: number; dy?: number}> = ({cx, cy, value, size = 110, color = WHITE, family = FONT_ORB, weight = 700, letterSpacing = 2, shadow = `6px 6px 0 ${PURPLE}, 0 0 28px rgba(102,45,248,.45)`, unit, unitSize = 24, unitColor = '#A0A0A1', opacity = 1, dy = -2}) => (
  <>
    <CText cx={cx} cy={cy} size={size} weight={weight} family={family} color={color} letterSpacing={letterSpacing} opacity={opacity} dy={dy} shadow={shadow} style={{fontVariantNumeric: 'tabular-nums'}}>
      {value}
    </CText>
    {unit ? <CText cx={cx} cy={cy + size * 0.62 + unitSize / 2} size={unitSize} weight={600} color={unitColor} opacity={opacity}>{unit}</CText> : null}
  </>
);

// ---- 小件 ----
/** 四角小星（"冒星"），r = 外半径 */
export const Sparkle: React.FC<{cx: number; cy: number; r: number; opacity?: number; color?: string}> = ({cx, cy, r, opacity = 1, color = WHITE}) => {
  const k = 0.28;
  const d = `M0,${-r} C0,${-r * k} ${r * k},0 ${r},0 C${r * k},0 0,${r * k} 0,${r} C0,${r * k} ${-r * k},0 ${-r},0 C${-r * k},0 0,${-r * k} 0,${-r} Z`;
  return (
    <svg width={r * 2 + 8} height={r * 2 + 8} viewBox={`${-r - 4} ${-r - 4} ${r * 2 + 8} ${r * 2 + 8}`} style={{position: 'absolute', left: cx - r - 4, top: cy - r - 4, opacity, overflow: 'visible'}}>
      <path d={d} fill={color} />
    </svg>
  );
};
/** 顶亮底黑小球（节点 / 小球跑圈用） */
export const GradBall: React.FC<{cx: number; cy: number; r: number; stroke?: number}> = ({cx, cy, r, stroke = 2.5}) => (
  <div style={{...abs(cx - r, cy - r, 2 * r, 2 * r), borderRadius: '50%', boxSizing: 'border-box', border: `${stroke}px solid #FFF`, background: 'linear-gradient(180deg, #F0F0F0 0%, #E8E8E8 3%, #919191 11.7%, #787878 20%, #5B5B5B 28%, #313131 40%, #0F0F0F 50%, #000 58%, #000 100%)'}} />
);

// ---- 纵深：倾斜平面 ----
/**
 * 倾斜平面（层级 / 空间分层用）：以 (cx,cy) 为中心的 w×h 平面，skewX(skew°) scaleY(sy) 成"躺着"的平行四边形；
 * children 用平面内坐标（原点左上、尺寸 w×h）绝对定位，会跟着一起变形。多层叠放：层距 90px，靠后的层 opacity 0.6。
 */
export const TiltPlane: React.FC<{cx: number; cy: number; w?: number; h?: number; skew?: number; sy?: number; stroke?: string; sw?: number; fill?: string; opacity?: number; children?: React.ReactNode}> = ({cx, cy, w = 420, h = 260, skew = -20, sy = 0.5, stroke = WHITE, sw = 2, fill = 'rgba(0,0,0,.85)', opacity = 1, children}) => (
  <div style={{...abs(cx - w / 2, cy - h / 2, w, h), transform: `scaleY(${sy}) skewX(${skew}deg)`, transformOrigin: '50% 50%', opacity}}>
    <div style={{position: 'absolute', inset: 0, boxSizing: 'border-box', border: `${sw}px solid ${stroke}`, background: fill, filter: 'drop-shadow(0 0 2px rgba(255,255,255,.35))'}} />
    {children}
  </div>
);

// ---- 运镜 ----
export type CamKey = {f: number; x: number; y: number; s: number};
/** 相机关键帧插值：f 之间 easeInOutPow(2.5)，首值之前停在第一帧、末值之后停在最后一帧（避免 kf 首值陷阱：第一帧必须写镜头起始状态） */
export const camAt = (N: number, keys: CamKey[], ease = easeInOutPow(2.5)) => {
  if (N <= keys[0].f) return keys[0];
  for (let i = 1; i < keys.length; i++) {
    const a = keys[i - 1], b = keys[i];
    if (N <= b.f) {
      const t = ease(clamp01((N - a.f) / Math.max(1, b.f - a.f)));
      return {f: N, x: a.x + (b.x - a.x) * t, y: a.y + (b.y - a.y) * t, s: a.s + (b.s - a.s) * t};
    }
  }
  return keys[keys.length - 1];
};
/**
 * 相机：children 用世界坐标（默认相机 x=640,y=360,s=1 时与画布重合）。定点推近 = 同一 (x,y) 改 s（1→1.33，30–40 帧）；
 * 平移/整页滚动 = 改 (x,y)；承接 = 上一镜头末与下一镜头首用相同 keys。scale 对 box-shadow/描边同样放大，推近超过 1.4 时描边会显粗。
 */
export const CameraRig: React.FC<{N: number; keys: CamKey[]; children: React.ReactNode; style?: React.CSSProperties}> = ({N, keys, children, style}) => {
  const c = camAt(N, keys);
  return (
    <div style={{position: 'absolute', inset: 0, transformOrigin: '0 0', transform: `translate(640px,360px) scale(${c.s.toFixed(4)}) translate(${(-c.x).toFixed(2)}px,${(-c.y).toFixed(2)}px)`, ...style}}>
      {children}
    </div>
  );
};

// ---- 高光时刻标准时序 ----
/** 登场型高光时刻相对帧（T0 = 镜头起始/清场帧，T1 = 主角节拍帧；样片 SC08：T0=1013、T1=1080） */
export const SET_PIECE = {
  sweeps: [4, 22, 40], // 三轮 LightSweep 起始（相对 T0）
  line: 18, // StageLine 起始（相对 T0）
  ghost: 37, // GhostText 起始（相对 T0）
  pulse: 12, // emphasisPulse 起始（相对 T1）
  sub: 16, // 中文副标 slideUp Δ80/22（相对 T1）
  pills: 24, // 拆词/标签 SoftIn 2 帧错峰（相对 T1）
  minLen: 90, // 高光时刻镜头最短帧数
};
export const setPiece = (T0: number, T1: number) => ({
  sweeps: SET_PIECE.sweeps.map((d) => T0 + d),
  line: T0 + SET_PIECE.line,
  ghost: T0 + SET_PIECE.ghost,
  flash: T1,
  pulse: T1 + SET_PIECE.pulse,
  sub: T1 + SET_PIECE.sub,
  pills: T1 + SET_PIECE.pills,
});

// ---- 圆形光斑 / 暗角 / 主角组合（共用层图元，各组直接 import）----
/** 圆形紫柔光斑（radial-gradient）：图形主角脚下/身后的大面积光，比 HeroGlow 的矩形 box-shadow 更适合圆形/人形主角（Gauge、PersonIcon、环）。N 传入时 30 帧呼吸 ±15%，k 为强度 0→1 */
export const GlowBlob: React.FC<{cx: number; cy: number; r: number; N?: number; k?: number; alpha?: number}> = ({cx, cy, r, N, k = 1, alpha = 0.34}) => {
  const breathe = N === undefined ? 1 : 1 + 0.15 * Math.sin((2 * Math.PI * N) / 30);
  const a = clamp01(k) * breathe * alpha;
  if (a <= 0.005) return null;
  return <div style={{position: 'absolute', left: cx - r, top: cy - r, width: 2 * r, height: 2 * r, borderRadius: '50%', background: `radial-gradient(circle, rgba(102,45,248,${a.toFixed(3)}) 0%, rgba(102,45,248,${(a * 0.55).toFixed(3)}) 34%, rgba(102,45,248,0) 70%)`}} />;
};
/** 屏幕空间顶/底暗角（推近时同步淡入 18 帧）：k 0→1。放在 CameraRig 之外（屏幕空间，不随相机）。
 *  顶带默认从 y=top(100) 起、高 topH(100)，**不压 HUD 胶囊（y 28–100）**；底带 560–687（止于进度条：条体半透明，压暗其后方会让条变暗，QC v1 C1）。 */
export const Vignette: React.FC<{k: number; alpha?: number; top?: number; topH?: number}> = ({k, alpha = 0.4, top = 100, topH = 100}) => {
  if (k <= 0.005) return null;
  const a = (alpha * clamp01(k)).toFixed(3);
  return (
    <>
      <div style={{position: 'absolute', left: 0, top, width: 1280, height: topH, background: `linear-gradient(180deg, rgba(0,0,0,${a}) 0%, rgba(0,0,0,0) 100%)`}} />
      <div style={{position: 'absolute', left: 0, top: 560, width: 1280, height: 127, background: `linear-gradient(0deg, rgba(0,0,0,${a}) 0%, rgba(0,0,0,0) 100%)`}} />
    </>
  );
};
