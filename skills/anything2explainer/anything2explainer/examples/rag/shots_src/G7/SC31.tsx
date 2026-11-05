import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {slideIn} from '../../common';
import {SoftIn} from '../../ui';
import {PIPE, PIPE_NAMES, pipeX, arrowX, PipePill, PipeArrow, QMark, flash} from './g7ui';

/**
 * SC31 好不好？（5742–5821）
 * 5748 起 5 个小 Pill 2 帧错峰 SoftIn 淡入（闪烁整改：SC31 不在白名单） + 箭头自根部长出（14 帧）；5778 大问号缩放入场 + 脉冲；5782 起各 Pill 依次闪紫。
 * 末帧不离场（SC32 同几何续接，问号在 SC32 前 12 帧淡出）。
 */
const F0 = 5742;
export const T_PIPE = 5748; // 节拍 5750 −2
const T_Q = 5778; // 节拍 5780 −2

export const SC31: React.FC = () => {
  const N = useCurrentFrame() + F0;
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      {PIPE_NAMES.map((_, i) => (
        <SoftIn key={i} N={N} f0={T_PIPE + 2 * i}>
          <PipePill i={i} x={pipeX(i)} cy={PIPE.cy} hl={flash(N - (5782 + 5 * i), 10)} />
        </SoftIn>
      ))}
      {[0, 1, 2, 3].map((i) => (
        <PipeArrow key={i} x={arrowX(i)} cy={PIPE.cy} p={slideIn(N - (T_PIPE + 5 + 2 * i), 14, 2)} />
      ))}
      <QMark N={N} f0={T_Q} />
    </AbsoluteFill>
  );
};
