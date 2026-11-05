import React from 'react';
import {useCurrentFrame} from 'remotion';
import {clamp01} from '../../common';
import {CText, Pill, TagBlock, Svg, Check, fadeIn, slideUp, scaleIn, ORANGE, PURPLE, abs, SoftIn} from '../../ui';
import {TrapRag, TrapText, GREY_STOPS, PURP_STOPS} from './ui';

/**
 * SC27 像推荐系统的精排（4927–5017）
 * 节拍：4935 像推荐系统里的精排 / 5001 贵 / 5006 但准
 * 画面：左 (380) 三层迷你漏斗「向量召回 → 混合检索 → 重排」，右 (900)「召回 → 粗排 → 精排」，中间 ≈；
 *      5001 橙「贵」、5006 紫「准」+ 绿勾 弹出于精排层右侧。
 * QC v1：TagBlock 缩放 21→8 帧、绿勾 9→6 帧（5014 全部到位）。QC v2：5016–5021 整组淡出 + 下摇 ≤10px 归零（原 5017→5018 硬切到空场）。
 */
const F0 = 4927;
const B_MAIN = 4935, B_EXP = 5001, B_ACC = 5006;
const LX = 380, RX = 900;
// 共线斜边：斜率 0.5px/行，层高 60，间隙 12
const LAYERS = [{y: 290, wTop: 380, wBot: 320}, {y: 362, wTop: 308, wBot: 248}, {y: 434, wTop: 236, wBot: 176}];
const LEFT = ['向量召回', '混合检索', '重排'];
const RIGHT = ['召回', '粗排', '精排'];
const T_ENTER = 4931;

const Funnel: React.FC<{N: number; cx: number; names: string[]; t0: number; idPrefix: string}> = ({N, cx, names, t0, idPrefix}) => (
  <>
    {LAYERS.map((L, k) => {
      const n = N - (t0 + 2 * k);
      if (n < 0) return null;
      return (
        <TrapRag key={k} id={`${idPrefix}-${k}`} cx={cx} y={L.y + slideUp(n, 160)} wTop={L.wTop} wBot={L.wBot} h={60} stops={k === 2 ? PURP_STOPS : GREY_STOPS} opacity={fadeIn(n, 8)}>
          <TrapText size={28}>{names[k]}</TrapText>
        </TrapRag>
      );
    })}
  </>
);

const PopTag: React.FC<{N: number; f0: number; x: number; y: number; color: string; text: string}> = ({N, f0, x, y, color, text}) => {
  const n = N - f0;
  if (n < 0) return null;
  const s = scaleIn(n, 8);
  return (
    <div style={{...abs(x, y, 110, 50), transform: `scale(${s.toFixed(3)})`, transformOrigin: '50% 50%', opacity: fadeIn(n, 3)}}>
      <TagBlock x={0} y={0} w={110} h={50} color={color} text={text} fontSize={32} />
    </div>
  );
};

export const SC27: React.FC = () => {
  const N = useCurrentFrame() + F0;
  // QC v2：5016–5021 整组淡出 1−(n/5)^1.5 + 下摇 ≤10px（Sequence to 延到 5021，与 SC28 5018 起入场重叠）
  const nx = N - 5016;
  const tx = clamp01(nx / 5);
  const opAll = nx <= 0 ? 1 : 1 - Math.pow(tx, 1.5);
  const dyAll = nx <= 0 ? 0 : 10 * tx * tx;
  if (opAll <= 0) return null;
  const checkP = clamp01((N - (B_ACC + 2)) / 6);
  return (
    <div style={{position: 'absolute', inset: 0, opacity: opAll, transform: dyAll ? `translateY(${dyAll.toFixed(2)}px)` : undefined}}>
      {/* 两组漏斗（左先、右晚 2 帧，层间 2 帧错峰） */}
      <Funnel N={N} cx={LX} names={LEFT} t0={T_ENTER} idPrefix="g6-sc27-l" />
      <Funnel N={N} cx={RX} names={RIGHT} t0={T_ENTER + 2} idPrefix="g6-sc27-r" />
      {/* 标题胶囊（闪烁整改：SC27 不在白名单，全部 SoftIn，f0 不变） */}
      <SoftIn N={N} f0={B_MAIN}>
        <Pill x={LX - 75} y={232} w={150} h={36} text="RAG 检索" fontSize={22} weight={700} />
      </SoftIn>
      <SoftIn N={N} f0={B_MAIN + 2}>
        <Pill x={RX - 75} y={232} w={150} h={36} text="推荐系统" fontSize={22} weight={700} />
      </SoftIn>
      {/* ≈ */}
      <SoftIn N={N} f0={B_MAIN + 11}>
        <CText cx={640} cy={392} size={64} weight={700} dy={-4}>≈</CText>
      </SoftIn>
      {/* 贵 / 准 + 绿勾 */}
      <PopTag N={N} f0={B_EXP} x={1050} y={405} color={ORANGE} text="贵" />
      <PopTag N={N} f0={B_ACC} x={1050} y={468} color={PURPLE} text="准" />
      {checkP > 0 ? (
        <Svg>
          <Check cx={1194} cy={493} size={40} sw={6} p={checkP} />
        </Svg>
      ) : null}
    </div>
  );
};
