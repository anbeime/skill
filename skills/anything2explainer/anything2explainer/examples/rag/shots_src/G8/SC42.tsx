import React from 'react';
import {useCurrentFrame} from 'remotion';
import {GlitchIn, clamp01, emphasisPulse} from '../../common';
import {Svg, LineArrow, CText, LLMIcon, PURPLE_LIGHT, GREY, WHITE, fadeIn, scaleIn, SoftIn} from '../../ui';
import {ExamPaper, BookIcon} from '../G2/parts';
import {FR, Anchor, exitOut} from './shared';

/**
 * SC42 闭卷→开卷（7754–7869）。第 1 章 SC06 的回调：考卷 / 书本直接复用 G2 `parts.tsx` 的 ExamPaper（左上锚，SC06 为 300×380）与 BookIcon（中心锚 + s，SC06 为 280×180）。
 * 适配：考卷按 0.9 倍（270×342）并用 brightness(.63) 压成灰（闭卷 = 非重点，组件无 color prop、不改 G2 文件）；书本原尺寸。
 * 节拍：7762 灰考卷 / 7764 白边书 / 7766 中央 LLMIcon —— 2 帧错峰 21 帧缩放入场；7798 大字「闭卷」灰 SoftIn 淡入 → 7802 白箭头 draw-on → 7812 「开卷」紫 GlitchIn + 脉冲。闪烁整改：本镜头 glitch 只给「开卷」（重点词），rgbSplit 按 §8 只留片头/SC08/SC35/SC44，此处去掉。
 * 离场：7855 起 exitOut 14 帧（末 6 帧线性收 0，7869 恰为 0；QC v1）。
 */
const F0 = FR.SC42.from, F1 = FR.SC42.to;
const ROW_Y = 415, TXT_Y = 190;
const PAPER = {w: 270, h: 342, cx: 400}; // 0.9 × SC06 (300×380)
const BOOK = {cx: 880, cy: ROW_Y, w: 280, h: 180}; // = SC06 BOOK

export const SC42: React.FC = () => {
  const N = useCurrentFrame() + F0;
  const ex = exitOut(N - (F1 - 14), 14);
  const n0 = N - 7762, n1 = N - 7764, n2 = N - 7766;
  const arrowP = clamp01((N - 7802) / 18);
  const pulse = emphasisPulse(N - 7822, {peak: 1.12});
  return (
    <div style={{position: 'absolute', inset: 0, opacity: ex.op, transform: `translateY(${ex.dy.toFixed(2)}px)`}}>
      {n0 >= 0 ? (
        <Anchor cx={PAPER.cx} cy={ROW_Y} s={scaleIn(n0)} opacity={fadeIn(n0, 8)}>
          <div style={{position: 'absolute', inset: 0, filter: 'brightness(0.63)'}}>
            <ExamPaper x={PAPER.cx - PAPER.w / 2} y={ROW_Y - PAPER.h / 2} w={PAPER.w} h={PAPER.h} />
          </div>
        </Anchor>
      ) : null}
      {n2 >= 0 ? (
        <Anchor cx={640} cy={ROW_Y + 10} s={scaleIn(n2)} opacity={fadeIn(n2, 8)}>
          <LLMIcon cx={640} cy={ROW_Y + 10} size={96} />
        </Anchor>
      ) : null}
      {n1 >= 0 ? <BookIcon cx={BOOK.cx} cy={BOOK.cy} w={BOOK.w} h={BOOK.h} s={Math.max(0.01, scaleIn(n1))} opacity={fadeIn(n1, 8)} lines={4} hl={clamp01((N - 7812) / 12)} hlLine={1} /> : null}
      {/* 大字：闭卷（灰）→ 开卷（紫） */}
      <SoftIn N={N} f0={7798}>
        <CText cx={PAPER.cx} cy={TXT_Y} size={56} weight={900} scaleX={0.85} color={GREY} letterSpacing={2}>闭卷</CText>
      </SoftIn>
      <Svg>
        <LineArrow x0={480} y0={TXT_Y} x1={800} y1={TXT_Y} p={arrowP} rodW={4} headL={26} headW={28} color={WHITE} />
      </Svg>
      <GlitchIn N={N} f0={7812}>
        <Anchor cx={BOOK.cx} cy={TXT_Y} s={pulse}>
          <CText cx={BOOK.cx} cy={TXT_Y} size={56} weight={900} scaleX={0.85} color={PURPLE_LIGHT} letterSpacing={2} shadow="0 0 16px rgba(102,45,248,.8), 0 0 40px rgba(102,45,248,.45)">开卷</CText>
        </Anchor>
      </GlitchIn>
    </div>
  );
};
