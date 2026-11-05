import React from 'react';
import {rnd} from './easing';

/**
 * 12 帧 glitch 入场模板（seg_06/07/08/10/19/20/23/24 逐帧 lum 全部吻合，可作全局常量）：
 * opacity = [0.5,1,0.5,0,0.5,0,0.5,1,0.75,0.5,0.75,1]，第 13 帧起恒 1。多段实测**纯透明度**：无位移、无 RGB 错位、无切片。
 * 档位精确值 0.53–0.55 / 0.77–0.78（三段统一取 0.55/0.78 亦可，用 GLITCH_SEQ_B）。
 * seg_00（"召回"文字 f34–44）、seg_20（"粗排"故障字）、seg_28（片尾 6 帧全帧切片）那类带残影/RGB 错位的版本用 rgbSplit / slices 参数。
 */
export const GLITCH_SEQ = [0.5, 1, 0.5, 0, 0.5, 0, 0.5, 1, 0.75, 0.5, 0.75, 1];
export const GLITCH_SEQ_B = [0.55, 1, 0.55, 0, 0.55, 0, 0.55, 1, 0.78, 0.55, 0.78, 1];
/** n = N − f0：n<0 → 0（未入场）；0..11 → 序列；≥12 → 1。 */
export const glitchOpacity = (n: number, seq: number[] = GLITCH_SEQ) => (n < 0 ? 0 : n >= seq.length ? 1 : seq[n]);

let glitchSeq = 0;
/** 任意内容染成单色（品红/青副本用）：feColorMatrix 取亮度写入指定通道，保留 alpha。 */
const TintDefs: React.FC<{id: string}> = ({id}) => (
  <svg width={0} height={0} style={{position: 'absolute'}}>
    <defs>
      {/* 品红 #D100D6 (209,0,214) */}
      <filter id={`${id}-m`} colorInterpolationFilters="sRGB">
        <feColorMatrix type="matrix" values="0.174 0.586 0.059 0 0  0 0 0 0 0  0.178 0.600 0.061 0 0  0 0 0 1 0" />
      </filter>
      {/* 青 #58FFEE (88,255,238) */}
      <filter id={`${id}-c`} colorInterpolationFilters="sRGB">
        <feColorMatrix type="matrix" values="0.073 0.247 0.025 0 0  0.213 0.715 0.072 0 0  0.199 0.667 0.067 0 0  0 0 0 1 0" />
      </filter>
    </defs>
  </svg>
);

export type GlitchInProps = {
  N: number; // 原片当前帧号
  f0: number; // 入场起始帧（序列第 0 帧）
  children: React.ReactNode;
  seq?: number[];
  /** RGB 错位副本最大偏移 px（0 = 关）。闪烁期内逐帧随机偏移；persistSplit 时入场后保持固定偏移 (−6,−3)/(+3,+5)（seg_28 标题）。 */
  rgbSplit?: number;
  persistSplit?: boolean;
  /** 水平切片错位最大 px（0 = 关）。闪烁期内每帧 3–4 条随机带各自错位（seg_00 残影 ±8、seg_28 片尾 ±80）。 */
  slices?: number;
  sliceBands?: number;
  seed?: number;
  /** 闪烁结束后是否继续切片（默认否）。 */
  persistSlices?: boolean;
  style?: React.CSSProperties;
};

/** 12 帧 glitch 入场容器。n<0 不渲染；n≥12 原样渲染（可选保留 RGB 错位）。children 用绝对定位（容器 = 全画幅 AbsoluteFill）。 */
export const GlitchIn: React.FC<GlitchInProps> = ({N, f0, children, seq = GLITCH_SEQ, rgbSplit = 0, persistSplit = false, slices = 0, sliceBands = 4, seed = 1, persistSlices = false, style}) => {
  const idRef = React.useRef<string | undefined>(undefined);
  if (!idRef.current) idRef.current = `rsglitch-${glitchSeq++}`;
  const id = idRef.current;
  const n = N - f0;
  if (n < 0) return null;
  const active = n < seq.length;
  const op = glitchOpacity(n, seq);
  const box: React.CSSProperties = {position: 'absolute', inset: 0, overflow: 'hidden', ...style};
  if (op <= 0) return <div style={box} />;

  // 切片：把全画幅按 sliceBands 条随机水平带切开，各带独立水平错位
  const sliced = (node: React.ReactNode, key: string) => {
    const doSlice = slices > 0 && (active || persistSlices);
    if (!doSlice) return <div key={key} style={{position: 'absolute', inset: 0}}>{node}</div>;
    const cuts: number[] = [0];
    for (let b = 1; b < sliceBands; b++) cuts.push(rnd(seed, N, b, 11) * 720);
    cuts.push(720);
    cuts.sort((a, b) => a - b);
    return (
      <React.Fragment key={key}>
        {cuts.slice(0, -1).map((y0, b) => {
          const y1 = cuts[b + 1];
          const dx = (rnd(seed, N, b, 12) * 2 - 1) * slices * (rnd(seed, N, b, 13) < 0.35 ? 0 : 1);
          return (
            <div key={b} style={{position: 'absolute', inset: 0, clipPath: `inset(${y0}px 0 ${720 - y1}px 0)`, transform: `translateX(${dx.toFixed(1)}px)`}}>
              {node}
            </div>
          );
        })}
      </React.Fragment>
    );
  };

  const doSplit = rgbSplit > 0 && (active || persistSplit);
  let mOff: [number, number] = [-6, -3];
  let cOff: [number, number] = [3, 5];
  if (doSplit && active) {
    const k = rgbSplit / 6;
    mOff = [-(3 + 6 * rnd(seed, N, 21)) * k, -(1 + 4 * rnd(seed, N, 22)) * k];
    cOff = [(1 + 4 * rnd(seed, N, 23)) * k, (2 + 6 * rnd(seed, N, 24)) * k];
  } else if (doSplit) {
    const k = rgbSplit / 6;
    mOff = [-6 * k, -3 * k];
    cOff = [3 * k, 5 * k];
  }
  return (
    <div style={{...box, opacity: op * (typeof style?.opacity === 'number' ? style.opacity : 1)}}> {/* 主会话（RF3 根因）：序列 opacity 要与传入 style.opacity 相乘，否则外层淡出乘子被覆盖 */}
      {doSplit ? <TintDefs id={id} /> : null}
      {doSplit ? (
        <div style={{position: 'absolute', inset: 0, filter: `url(#${id}-m)`, transform: `translate(${mOff[0].toFixed(1)}px, ${mOff[1].toFixed(1)}px)`}}>{sliced(children, 'm')}</div>
      ) : null}
      {doSplit ? (
        <div style={{position: 'absolute', inset: 0, filter: `url(#${id}-c)`, transform: `translate(${cOff[0].toFixed(1)}px, ${cOff[1].toFixed(1)}px)`}}>{sliced(children, 'c')}</div>
      ) : null}
      {sliced(children, 'main')}
    </div>
  );
};
