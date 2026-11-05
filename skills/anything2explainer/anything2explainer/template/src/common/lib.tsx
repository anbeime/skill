import React from 'react';
import {AbsoluteFill, continueRender, delayRender, staticFile} from 'remotion';
import {VIDEO} from '../config';

// 画布与帧号约定：1280×720@30fps；帧号 N 从 1 起（N = useCurrentFrame() + F0，F0 = 镜头 ShotDef.from）。
export const W = 1280;
export const H = 720;
export const FPS = 30;

export const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v));
export const lerp = (t: number, t0: number, t1: number, v0: number, v1: number) => {
  if (t1 === t0) return v1;
  return v0 + (v1 - v0) * clamp((t - t0) / (t1 - t0), 0, 1);
};
/** 分段线性关键帧 [frame, value][]。⚠ 首值陷阱：t < 首关键帧返回首值（不是 0）。 */
export const keyframes = (t: number, kf: Array<[number, number]>) => {
  if (t <= kf[0][0]) return kf[0][1];
  for (let i = 1; i < kf.length; i++) if (t <= kf[i][0]) return lerp(t, kf[i - 1][0], kf[i][0], kf[i - 1][1], kf[i][1]);
  return kf[kf.length - 1][1];
};
export const stepHold = (t: number, kf: Array<[number, number]>) => {
  if (t < kf[0][0]) return 0;
  for (let i = kf.length - 1; i >= 0; i--) if (t >= kf[i][0]) return kf[i][1];
  return 0;
};

// ---- 方向模糊（SVG feGaussianBlur，σ<0.8 在 Chromium 中无效；禁用 feConvolveMatrix）----
let blurSeq = 0;
export const DirBlur: React.FC<{bx: number; by: number; style?: React.CSSProperties; children: React.ReactNode}> = ({bx, by, style, children}) => {
  const idRef = React.useRef<string | undefined>(undefined);
  if (!idRef.current) idRef.current = `dirblur-${blurSeq++}`;
  const id = idRef.current;
  const active = bx > 0.05 || by > 0.05;
  return (
    <AbsoluteFill style={style}>
      {active ? (
        <svg width={0} height={0} style={{position: 'absolute'}}>
          <defs>
            <filter id={id} x="-60%" y="-60%" width="220%" height="220%" colorInterpolationFilters="sRGB">
              <feGaussianBlur stdDeviation={`${Math.max(0, bx)} ${Math.max(0, by)}`} />
            </filter>
          </defs>
        </svg>
      ) : null}
      <AbsoluteFill style={{filter: active ? `url(#${id})` : undefined}}>{children}</AbsoluteFill>
    </AbsoluteFill>
  );
};

// ---- 字体（全部随模板附带，OFL 许可；Noto Sans SC 含完整拉丁字形，英文片同样用它做正文/字幕）----
export const FONT_HEAVY = `'Noto Sans SC', 'PingFang SC', 'Hiragino Sans GB', sans-serif`; // 全部中文：标题 900（常 scaleX .8–.85 压窄）、标签 600–800、字幕 700
export const FONT_TECH = `'Exo 2', 'Helvetica Neue', sans-serif`; // 英文技术词：紫色粗斜体 + scaleX .8
export const FONT_WIDE = `'Audiowide', 'Orbitron', sans-serif`; // 宽体展示字（片名 / 大写缩写）
export const FONT_ORB = `'Orbitron', 'Audiowide', sans-serif`; // 数字 / 章序号 / HUD 计数
export const FONT_MONO = `'SF Mono', Menlo, Consolas, monospace`; // 代码 / 等宽数字
export const FONT_SERIF = `'Times New Roman', Times, serif`; // 公式
export const FONT_EN = `'Helvetica Neue', Helvetica, Arial, sans-serif`;

// ---- 语言开关（src/config.ts 的 VIDEO.lang）----
/** 'zh' 中文片（默认）｜'en' 英文片。影响：字体压窄系数、基线补偿、文案与字幕预算（见 reference/narration-storyboard.md §5）。 */
export const LANG = VIDEO.lang ?? 'zh';
/** 中文标题惯用 scaleX .8–.85 压窄；拉丁字母压窄会变形，英文片一律 1。 */
export const SQUEEZE = LANG === 'en' ? 1 : 0.85;
/** CJK 行盒 ascent 让墨迹比 top 低 3–7px，居中要预扣；拉丁不需要。 */
export const TEXT_DY = LANG === 'en' ? 0 : -2;

/** 在 Main 顶层挂一次；用 delayRender 等字体就绪。 */
export const Fonts: React.FC = () => {
  const [handle] = React.useState(() => delayRender('fonts'));
  React.useEffect(() => {
    Promise.all([
      new FontFace('Noto Sans SC', `url(${staticFile('fonts/NotoSansSC.ttf')})`, {weight: '100 900'} as FontFaceDescriptors).load(),
      new FontFace('Exo 2', `url(${staticFile('fonts/Exo2-Italic.ttf')})`, {weight: '100 900', style: 'italic'} as FontFaceDescriptors).load(),
      new FontFace('Audiowide', `url(${staticFile('fonts/Audiowide-Regular.ttf')})`).load(),
      new FontFace('Orbitron', `url(${staticFile('fonts/Orbitron[wght].ttf')})`, {weight: '400 900'} as FontFaceDescriptors).load(),
    ])
      .then((fs) => {
        fs.forEach((f) => (document.fonts as unknown as {add: (f: FontFace) => void}).add(f));
        continueRender(handle);
      })
      .catch(() => continueRender(handle));
  }, [handle]);
  return null;
};
