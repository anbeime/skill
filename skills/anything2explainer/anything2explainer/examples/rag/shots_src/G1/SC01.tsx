import React from 'react';
import {useCurrentFrame} from 'remotion';
import {Scene1Frame} from './layout';

/** SC01 大模型与三个短板（78–167）：86 LLMIcon 缩放入场 + 柔光脉冲 + 冒星；116 三个虚线框自右滑入（2 帧错峰）+ 编号徽章 8 帧淡入（本镜头无 glitch，协议 §8） */
const F0 = 78;
export const SC01: React.FC = () => {
  const N = useCurrentFrame() + F0;
  return <Scene1Frame N={N} />;
};
