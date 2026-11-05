import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {GlitchIn, slideIn, clamp01} from '../../common';
import {Svg, Check, Pill, CText, PURPLE, PURPLE_LIGHT, ORANGE, GREY, slideUp, fadeIn, abs, SoftIn} from '../../ui';
import {PIPE, PIPE_NAMES, pipeX, arrowX, PipePill, PipeArrow, EASE, SPLIT_DX, lerp, exitOut, DashFrame, CornerTag, MetricPill} from './g7ui';
import {FRAME_L32, FRAME_R32, TAG_L32, TAG_R32, CHECK_L, CHECK_R} from './SC32';

/**
 * SC33 指标与 RAGAS（5947–6212）
 * 5947–5961 两框自 SC32 几何变形为两只高框，流水线上移为框内表头（右组重新居中），绿勾淡出；
 * 5953 左列三枚指标 Pill 2 帧错峰滑入；6043 右列四枚；6108 底部「RAGAS」glitch + 两侧横线向外长出 + 灰小字全称；
 * 6198 起整体加速下摇 + 淡出（14 帧）。
 */
const F0 = 5947;
const T_MORPH = 5947, T_LEFT = 5953, T_RIGHT = 6043, T_RAGAS = 6108, T_EXIT = 6198;

const FRAME_L33 = {x: 70, y: 150, w: 580, h: 370};
const FRAME_R33 = {x: 700, y: 150, w: 510, h: 370};
const TAG_L33 = {x: 94, y: 130};
const TAG_R33 = {x: 724, y: 130};
const HEAD_CY = 205, HEAD_H = 48;
const RX33 = [785, 985]; // 右组表头 Pill x（框 700–1210 内居中）

/** 指标文案（英文拼写以 research/RAG调研.md §4 为准） */
const LEFT_METRICS: Array<{en: string; zh: string}> = [
  {en: 'Recall@k', zh: '召回率'},
  {en: 'MRR', zh: '平均倒数排名'},
  {en: 'nDCG', zh: '归一化折损累计增益'},
];
const RIGHT_METRICS: Array<{en: string; zh: string; dim?: boolean}> = [
  {en: 'Faithfulness', zh: '忠实度'},
  {en: 'Answer Relevancy', zh: '答案相关性'},
  {en: 'Context Precision', zh: '上下文精确率', dim: true},
  {en: 'Context Recall', zh: '上下文召回率', dim: true},
];
const LEFT_CY = [282, 368, 454];
const RIGHT_CY = [272, 340, 408, 476];

const rect = (a: {x: number; y: number; w: number; h: number}, b: {x: number; y: number; w: number; h: number}, m: number) => ({x: lerp(a.x, b.x, m), y: lerp(a.y, b.y, m), w: lerp(a.w, b.w, m), h: lerp(a.h, b.h, m)});

export const SC33: React.FC = () => {
  const N = useCurrentFrame() + F0;
  const m = EASE(clamp01((N - T_MORPH) / 14));
  const fL = rect(FRAME_L32, FRAME_L33, m), fR = rect(FRAME_R32, FRAME_R33, m);
  const cy = lerp(PIPE.cy, HEAD_CY, m), h = lerp(PIPE.h, HEAD_H, m);
  const checkOp = 1 - clamp01((N - T_MORPH) / 8);
  const ex = exitOut(N - T_EXIT, 14);
  const ragasLine = slideIn(N - (T_RAGAS + 4), 16, 2);
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      <div style={{position: 'absolute', inset: 0, transform: `translateY(${ex.dy.toFixed(2)}px)`, opacity: ex.op}}>
        <DashFrame {...fL} color={PURPLE_LIGHT} tint="rgba(102,48,248,0.07)" />
        <DashFrame {...fR} color={ORANGE} tint="rgba(240,95,65,0.06)" />
        {/* 表头流水线 */}
        {PIPE_NAMES.map((_, i) => {
          const x = i <= 2 ? pipeX(i) - SPLIT_DX : lerp(pipeX(i) + SPLIT_DX, RX33[i - 3], m);
          return <PipePill key={i} i={i} x={x} cy={cy} h={h} fontSize={lerp(26, 24, m)} />;
        })}
        <PipeArrow x={arrowX(0) - SPLIT_DX} cy={cy} p={1} />
        <PipeArrow x={arrowX(1) - SPLIT_DX} cy={cy} p={1} />
        <PipeArrow x={lerp(arrowX(3) + SPLIT_DX, RX33[0] + PIPE.w + 6, m)} cy={cy} p={1} />
        {/* 标签随框角移动 */}
        <CornerTag x={lerp(TAG_L32.x, TAG_L33.x, m)} y={lerp(TAG_L32.y, TAG_L33.y, m)} text="检索质量" fill={PURPLE} />
        <CornerTag x={lerp(TAG_R32.x, TAG_R33.x, m)} y={lerp(TAG_R32.y, TAG_R33.y, m)} text="生成质量" fill={ORANGE} />
        {/* 绿勾淡出 */}
        {checkOp > 0 ? (
          <Svg opacity={checkOp}>
            <Check {...CHECK_L} size={52} />
            <Check {...CHECK_R} size={52} />
          </Svg>
        ) : null}
        {/* 左列指标 */}
        {LEFT_METRICS.map((mt, i) => {
          const n = N - (T_LEFT + 2 * i);
          if (n < 0) return null;
          return <MetricPill key={mt.en} cx={360} cy={LEFT_CY[i] + slideUp(n, 30)} w={400} h={58} en={mt.en} zh={mt.zh} opacity={fadeIn(n, 10)} />;
        })}
        {/* 右列指标 */}
        {RIGHT_METRICS.map((mt, i) => {
          const n = N - (T_RIGHT + 2 * i);
          if (n < 0) return null;
          return <MetricPill key={mt.en} cx={955} cy={RIGHT_CY[i] + slideUp(n, 30)} w={440} h={54} en={mt.en} zh={mt.zh} dim={mt.dim} opacity={fadeIn(n, 10)} enSize={26} zhSize={23} />;
        })}
        {/* RAGAS */}
        <GlitchIn N={N} f0={T_RAGAS}>
          <Pill x={535} y={538} w={210} h={44} fill={PURPLE} sw={2} text="RAGAS" fontSize={28} weight={800} letterSpacing={2} textDy={-1} style={{filter: 'drop-shadow(0 0 2px rgba(200,180,255,.6))'}} glow="0 0 24px 6px rgba(102,45,248,.45)" />
        </GlitchIn>
        {/* 灰小字全称：非重点，SoftIn（闪烁整改：本镜头 glitch 只给 RAGAS Pill） */}
        <SoftIn N={N} f0={T_RAGAS}>
          <CText cx={640} cy={606} size={22} weight={500} color="#C8C8C8" letterSpacing={0.5}>
            Retrieval-Augmented Generation Assessment
          </CText>
        </SoftIn>
        {ragasLine > 0 ? (
          <>
            <div style={{...abs(535 - 240 * ragasLine, 559, Math.max(0, 240 * ragasLine - 14), 2.5), background: PURPLE_LIGHT, opacity: 0.9}} />
            <div style={{...abs(745 + 14, 559, Math.max(0, 240 * ragasLine - 14), 2.5), background: PURPLE_LIGHT, opacity: 0.9}} />
          </>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};
