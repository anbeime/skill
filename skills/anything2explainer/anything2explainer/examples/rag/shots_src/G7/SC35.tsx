import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {GlitchIn, kf, slideIn, clamp01, FONT_WIDE, FONT_TECH} from '../../common';
import {Svg, LineArrow, Pill, CText, GREY, WHITE, TEXT_GLOW, abs} from '../../ui';
import {exitOut} from './g7ui';

/**
 * SC35 进化（6407–6450）
 * 6413 中央大字「RAG」Audiowide 120px 白 GlitchIn（slices 20 + rgbSplit 8）；6427 起三枚灰 Pill 2 帧错峰从大字右缘飞出成扇形
 * （GraphRAG / Agentic RAG / 多模态 RAG），灰箭头同步长出。QC v1：末 6 帧 exitOut（6444–6450 线性收 0 + 轻微下摇），避免 6451 从满画面切到空帧。
 */
const F0 = 6407, F1 = 6450;
const T_RAG = 6413, T_FAN = 6427, T_EXIT = F1 - 6;
const ORIGIN = {x: 690, y: 340};
const FAN: Array<{en?: string; zh?: string; cx: number; cy: number; w: number}> = [
  {en: 'GraphRAG', cx: 905, cy: 240, w: 210},
  {en: 'Agentic RAG', cx: 945, cy: 340, w: 230},
  {zh: '多模态 RAG', cx: 905, cy: 440, w: 210},
];
const FLY = 14;

export const SC35: React.FC = () => {
  const N = useCurrentFrame() + F0;
  const ex = exitOut(N - T_EXIT, 6);
  return (
    <AbsoluteFill style={{pointerEvents: 'none', opacity: ex.op, transform: `translateY(${ex.dy.toFixed(2)}px)`}}>
      <GlitchIn N={N} f0={T_RAG} slices={20} sliceBands={4} rgbSplit={8} seed={5}>
        <CText cx={520} cy={340} size={120} weight={400} family={FONT_WIDE} color={WHITE} letterSpacing={4} dy={0} shadow={TEXT_GLOW}>
          RAG
        </CText>
      </GlitchIn>
      <Svg bloom={false}>
        {FAN.map((f, i) => {
          const n = N - (T_FAN + 2 * i);
          if (n < 0) return null;
          const p = slideIn(n, FLY, 2.5);
          const tx = f.cx - f.w / 2 - 6, ty = f.cy;
          return <LineArrow key={i} x0={ORIGIN.x} y0={ORIGIN.y} x1={ORIGIN.x + (tx - ORIGIN.x) * p} y1={ORIGIN.y + (ty - ORIGIN.y) * p} p={1} rodW={2.5} headL={16} headW={16} color={GREY} opacity={0.9} />;
        })}
      </Svg>
      {FAN.map((f, i) => {
        const n = N - (T_FAN + 2 * i);
        if (n < 0) return null;
        const p = slideIn(n, FLY, 2.5);
        const cx = kf(p, [[0, ORIGIN.x], [1, f.cx]]), cy = kf(p, [[0, ORIGIN.y], [1, f.cy]]);
        const s = 0.4 + 0.6 * p;
        return (
          <div key={i} style={{...abs(cx - f.w / 2, cy - 24, f.w, 48), opacity: clamp01(n / 6), transform: `scale(${s.toFixed(3)})`, transformOrigin: '50% 50%'}}>
            <Pill x={0} y={0} w={f.w} h={48} fill="#000" stroke={GREY} sw={2} text={f.en ?? f.zh} fontSize={f.en ? 26 : 24} weight={f.en ? 700 : 700} color={GREY} family={f.en ? FONT_TECH : undefined} textDy={f.en ? -1 : -2} letterSpacing={f.en ? 1 : 0} style={f.en ? {fontStyle: 'italic'} : undefined} />
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
