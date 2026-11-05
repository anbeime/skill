import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {slideIn, clamp01} from '../../common';
import {Svg, Check, PURPLE, PURPLE_LIGHT, ORANGE, fadeOut, exitAccel, abs, SoftIn} from '../../ui';
import {PIPE, PIPE_NAMES, pipeX, arrowX, PipePill, PipeArrow, QMark, EASE, SPLIT_DX} from './g7ui';
import {DashFrame, CornerTag} from './g7ui';

/**
 * SC32 拆成两半（5822–5946）
 * 5822–5834 SC31 的问号上浮淡出；5830 流水线从「重排｜生成」之间裂开：左三右二各移 80px（easeInOutPow 16 帧），
 * 中缝 x=740 白竖线闪一下、中间箭头淡出；5869 左紫虚线框 draw-on + 「检索质量」SoftIn 淡入 + 绿勾（闪烁整改：SC32 不在白名单）；5907 右橙虚线框 + 「生成质量」+ 绿勾。
 * 末帧不离场（SC33 同几何续接并变形）。
 */
const F0 = 5822;
export const T_SPLIT = 5830;
const T_L = 5869, T_R = 5907;

/** SC32 终态几何（SC33 从这里开始变形） */
export const FRAME_L32 = {x: 66, y: 335, w: 588, h: 150};
export const FRAME_R32 = {x: 826, y: 335, w: 388, h: 150};
export const TAG_L32 = {x: 90, y: 298};
export const TAG_R32 = {x: 850, y: 298};
export const CHECK_L = {cx: 360, cy: 448};
export const CHECK_R = {cx: 1020, cy: 448};
const FLASH_SEQ = [1, 0.55, 1, 0.3, 0.8, 0.45, 0.6, 0.25, 0];

export const SC32: React.FC = () => {
  const N = useCurrentFrame() + F0;
  const k = EASE(clamp01((N - T_SPLIT) / 16));
  const dxL = -SPLIT_DX * k, dxR = SPLIT_DX * k;
  const midArrowOp = 1 - clamp01((N - (T_SPLIT - 3)) / 5);
  const fl = N - T_SPLIT;
  const lineOp = fl < 0 || fl >= FLASH_SEQ.length ? 0 : FLASH_SEQ[fl];
  const pL = slideIn(N - T_L, 20, 2), pR = slideIn(N - T_R, 20, 2);
  const qn = N - F0;
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      {/* 承接 SC31 的问号：上浮 + 淡出 */}
      {qn < 13 ? <QMark N={N} f0={5778} opacity={fadeOut(qn, 12)} dy={-exitAccel(qn, 0.45)} /> : null}
      {/* 虚线框（在 Pill 之下） */}
      <DashFrame {...FRAME_L32} color={PURPLE_LIGHT} p={pL} tint="rgba(102,48,248,0.07)" />
      <DashFrame {...FRAME_R32} color={ORANGE} p={pR} tint="rgba(240,95,65,0.06)" />
      {/* 流水线 */}
      {PIPE_NAMES.map((_, i) => (
        <PipePill key={i} i={i} x={pipeX(i) + (i <= 2 ? dxL : dxR)} cy={PIPE.cy} />
      ))}
      <PipeArrow x={arrowX(0) + dxL} cy={PIPE.cy} p={1} />
      <PipeArrow x={arrowX(1) + dxL} cy={PIPE.cy} p={1} />
      <PipeArrow x={arrowX(2)} cy={PIPE.cy} p={1} opacity={midArrowOp} />
      <PipeArrow x={arrowX(3) + dxR} cy={PIPE.cy} p={1} />
      {/* 中缝白竖线闪一下 */}
      {lineOp > 0 ? <div style={{...abs(738, 322, 4, 116), background: '#FFF', opacity: lineOp, boxShadow: '0 0 12px 3px rgba(255,255,255,.7)'}} /> : null}
      {/* 标签 */}
      <SoftIn N={N} f0={T_L + 2}>
        <CornerTag {...TAG_L32} text="检索质量" fill={PURPLE} />
      </SoftIn>
      <SoftIn N={N} f0={T_R + 2}>
        <CornerTag {...TAG_R32} text="生成质量" fill={ORANGE} />
      </SoftIn>
      {/* 绿勾占位 */}
      {N > T_L + 12 ? (
        <Svg>
          <Check {...CHECK_L} size={52} p={slideIn(N - (T_L + 12), 10, 2)} />
          {N > T_R + 12 ? <Check {...CHECK_R} size={52} p={slideIn(N - (T_R + 12), 10, 2)} /> : null}
        </Svg>
      ) : null}
    </AbsoluteFill>
  );
};
