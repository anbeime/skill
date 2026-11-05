import React from 'react';
import {useCurrentFrame} from 'remotion';
import {FR, RulerPart, WindowPart} from './shared';

/**
 * SC40 20 万 token ≈ 500 页（7302–7503）。节拍：7310 「Anthropic, 2024」+ 尺 draw-on / 7373 紫竖线自下长出 + 「200K tokens」+ 6 枚文档落在 0–200K 段 /
 * 7428 「≈ 500 页」计数 0→500 / 7455 上下文窗口框 SoftIn 淡入（闪烁整改：SC40 不在白名单，RulerPart/WindowPart 的 glitch 开关不开），7459 起文档 2 帧错峰飞入窗口，7488 绿勾。
 * 不离场：SC41 用同一组件承接（硬切无缝）。数字依据：research §1 / §7.1 #3（Anthropic Contextual Retrieval 2024：<200K tokens ≈ 500 页）。
 */
const F0 = FR.SC40.from;

export const SC40: React.FC = () => {
  const N = useCurrentFrame() + F0;
  return (
    <>
      <RulerPart N={N} />
      <WindowPart N={N} />
    </>
  );
};
