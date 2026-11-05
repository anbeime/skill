import React from 'react';
import {useCurrentFrame} from 'remotion';
import {GlitchIn, clamp01} from '../../common';
import {CText, Pill, Svg, Cross, WHITE, GREY, PURPLE, slideUp, fadeIn, scaleIn, SoftIn} from '../../ui';
import {ExamPaper, BookIcon, Bulb} from './parts';

/**
 * SC06 开卷考试 · N 744–870（S06 752–868：752「于是工程师们想出了一个办法」/ 828「让模型开卷考试」）
 * 版式：考卷 (280,175,300,380) 居左中；「闭卷」灰章压在考卷左上角；828 起右侧翻开的书 (850,335) 260×170 + 大字「开卷考试」(850,520)。
 * 节拍：750 考卷 slideUp（Δ130/22 + 8 帧淡入；QC v1：原 Δ300 在 752–758 穿过字幕带，现卡底起点 685、4 帧内离开 y637 且此时 opacity ≤ .5）；
 *       752 灯泡 8 帧淡入（glow 4 帧后点亮）→ 770 起 20 帧周期呼吸（glow .56↔1，QC v1：原 786 淡出后 772–827 长静止）→ 826 起 8 帧淡出（书 828 入）；762「闭卷」章 SoftIn；
 *       828 书 21 帧缩放入场 + 「闭卷」被划掉（Cross 10 帧）；830 大字「开卷考试」GlitchIn 12 帧（本镜头唯一 glitch，白名单 §8；rgbSplit 仅片头/SC08/SC35/SC44 可用，已去掉）；865–870 整组 6 帧快速下摇淡出（SC07 硬切）。
 */
const F0 = 744;
const T_PAPER = 750, T_BULB = 752, T_CLOSED = 762, T_OPEN = 828, T_TITLE = 830, T_EXIT = 865;

const PAPER = {x: 280, y: 175, w: 300, h: 380};
const BOOK = {cx: 850, cy: 335, w: 280, h: 180};

export const SC06: React.FC = () => {
  const N = useCurrentFrame() + F0;
  // 离场：6 帧线性淡出 + 幂加速下摇
  const ex = N - T_EXIT;
  const exOp = ex <= 0 ? 1 : Math.max(0, 1 - ex / 6);
  const exDy = ex <= 0 ? 0 : 2.5 * ex * ex;

  // 考卷
  const pn = N - T_PAPER;
  const paperOp = fadeIn(pn, 8);
  const paperY = PAPER.y + slideUp(pn, 130, 22);

  // 灯泡：8 帧淡入（闪烁整改：原 7 帧 stepKf 闪现）→ 常亮 → 770 起 20 帧周期呼吸 → 826 起 8 帧淡出（让位给书）
  const bulbFade = fadeIn(N - T_BULB, 8);
  const bulbOp = bulbFade * (N >= 826 ? Math.max(0, 1 - (N - 826) / 8) : 1);
  const bulbGlow = N < T_BULB + 4 ? 0.4 : N < 770 ? 1 : 0.78 + 0.22 * Math.sin(((N - 770) * 2 * Math.PI) / 20 + Math.PI / 2);

  // 书 + 大字
  const bn = N - T_OPEN;
  const bookS = bn < 0 ? 0 : 0.2 + 0.8 * scaleIn(bn, 21);
  const bookOp = bn < 0 ? 0 : fadeIn(bn, 6);
  const crossP = clamp01((N - T_OPEN) / 10);

  return (
    <div style={{position: 'absolute', inset: 0, opacity: exOp, transform: exDy ? `translateY(${exDy.toFixed(1)}px)` : undefined}}>
      {/* 考卷 */}
      {pn >= 0 ? <ExamPaper x={PAPER.x} y={paperY} w={PAPER.w} h={PAPER.h} opacity={paperOp} /> : null}
      {/* 灯泡：考卷上方（"想出一个办法"） */}
      {bulbOp > 0 ? <Bulb cx={430} cy={138} r={18} opacity={bulbOp} glow={bulbGlow} /> : null}
      {/* 「闭卷」灰章：压在考卷左上角，略旋转（SoftIn 淡入） */}
      <SoftIn N={N} f0={T_CLOSED}>
        <div style={{position: 'absolute', left: 226, top: 196, width: 124, height: 44, transform: 'rotate(-8deg)', transformOrigin: '50% 50%'}}>
          <Pill x={0} y={0} w={124} h={44} fill="#000" stroke={GREY} sw={2.5} text="闭卷" fontSize={26} weight={700} color={GREY} letterSpacing={2} />
        </div>
      </SoftIn>
      {/* 划掉「闭卷」 */}
      {crossP > 0 ? (
        <Svg>
          <Cross cx={288} cy={218} size={54} sw={6} p={crossP} />
        </Svg>
      ) : null}
      {/* 翻开的书 */}
      {bookOp > 0 ? <BookIcon cx={BOOK.cx} cy={BOOK.cy} w={BOOK.w} h={BOOK.h} s={bookS} opacity={bookOp} lines={4} /> : null}
      {/* 大字「开卷考试」：白字 + 紫描边（stroke 外扩），12 帧 GlitchIn（白名单，纯透明度序列） */}
      <GlitchIn N={N} f0={T_TITLE}>
        <CText cx={850} cy={520} size={64} weight={900} scaleX={0.8} letterSpacing={2} color={WHITE} dy={-3} style={{WebkitTextStroke: `3px ${PURPLE}`, paintOrder: 'stroke fill', textShadow: '0 0 18px rgba(102,45,248,.55)'}}>
          开卷考试
        </CText>
      </GlitchIn>
    </div>
  );
};
