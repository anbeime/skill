import React from 'react';
/**
 * 底部雾底渐变（背景层，位于内容之下）。列中值实测（f700/f3000/f9000/f12500/f13060 完全一致 → 全片恒定存在，seg_19 的"纯黑"只是未测底部）：
 * y≤430 → 1；y460 6；y500 10；y540 15；y580 19；y620 24；y660 29；y680 31 ≈ 线性 0→#1F1F1F（0.124 灰度/px），全宽，无淡入。
 * 它在网格/内容层之下（seg_22 f12380 与 f12500 内容层下数值不变），字幕/进度条在其上。
 * still 标定 v1（top 430→#1F1F1F）列中值比原片低 2 灰阶 → top 415 / #212121（原片 y440 3、y520 13、y600 22、y680 31）。
 * 各组镜头**不要**再画不透明黑底（会盖掉雾底与星点）；需要全黑处用 BgSpec.fog=false 关掉。
 */
export const FOG_DEFAULT_ON = true; // 待主会话终裁（seg_19 记"纯黑"，实测有雾）
export const Fog: React.FC<{top?: number; bottom?: number; from?: string; to?: string; opacity?: number}> = ({top = 415, bottom = 687, from = '#000000', to = '#212121', opacity = 1}) => (
  // 主会话（QC v1 RQ3）：雾底末色要一直垫到画底 y720——原片进度条压在 ≈#212121 上（轨道 100 / 填充 (114,103,145)），v1 只到 687 使条体叠在纯黑上（78 / (100,89,131)）
  <div style={{position: 'absolute', left: 0, top, width: 1280, height: 720 - top, background: `linear-gradient(180deg, ${from} 0%, ${to} ${(((bottom - top) / (720 - top)) * 100).toFixed(2)}%, ${to} 100%)`, opacity, pointerEvents: 'none'}} />
);
