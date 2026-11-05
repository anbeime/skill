import React from 'react';
import {useCurrentFrame} from 'remotion';
import {slideIn, emphasisPulse, clamp01, FONT_TECH} from '../../common';
import {Box, Pill, CText, TechText, ChunkCard, Svg, LineArrow, PURPLE, PURPLE_LIGHT, ORANGE, GREY, GREY_LIGHT, WHITE, abs, scaleIn, slideUp, fadeIn, exitAccel, SoftIn} from '../../ui';
import {LText, Bar} from './g3ui';

/**
 * SC15 语义切块 + 补上下文 −49%（2309–2685，S15）
 * 节拍：2317 更讲究的做法（左：带层级的文档树卡自左滑入）/ 2346 按语义或标题层级来切（条目逐级 wipe；等距灰线 → 沿标题边界的紫切割线 draw-on）
 *      / 2400 补一句来自哪（中：ChunkCard 上方长出紫色前缀条「员工手册 › 第 3 章 差旅报销」打字机；文档树 3.1 段高亮 + 虚线箭头指向卡片）
 *      / 2498 Anthropic 实验（右：「Anthropic」Pill + Contextual Retrieval）/ 2572 配合关键词检索（「BM25」小 Pill 贴到前缀条旁）
 *      / 2606 降低 49%（Counter 0→49 计数 20 帧 + 橙柔光脉冲；灰小字 Top-20 检索失败率）
 * 2674–2685 末 12 帧离场 opacity = 1 − (n/12)^1.5（末帧归零）+ 轻微下摇 exitAccel(n,0.2)（QC v1 组界裁定；G4 SC16 卡片 2686 起自左入场）。条目 wipe 自 2322 起（原 2346，避免空框停留 26 帧）。数字依据：research/RAG调研.md §2.3 Contextual Retrieval（Anthropic 2024，+BM25 → top-20 失败率 −49%）。
 */
const F0 = 2309;
const TREE = {x: 100, y: 200, w: 400, h: 400};
const PREFIX = '员工手册 › 第 3 章 差旅报销';
const CUTS = [94, 176, 264, 348]; // 沿标题边界（局部 y）
const EVEN = [80, 160, 240, 320]; // 等距（对照）

type Entry = {kind: 'text' | 'bar'; x: number; y: number; text?: string; size?: number; weight?: number; color?: string; w?: number; h?: number};
const ENTRIES: Entry[] = [
  {kind: 'text', x: 24, y: 16, text: '员工手册', size: 24, weight: 800},
  {kind: 'text', x: 44, y: 60, text: '第 3 章 差旅报销', size: 22, weight: 700},
  {kind: 'text', x: 64, y: 104, text: '3.1 住宿上限', size: 22, weight: 600, color: GREY_LIGHT},
  {kind: 'bar', x: 64, y: 138, w: 260},
  {kind: 'bar', x: 64, y: 156, w: 220},
  {kind: 'text', x: 64, y: 186, text: '3.2 交通', size: 22, weight: 600, color: GREY_LIGHT},
  {kind: 'bar', x: 64, y: 220, w: 250},
  {kind: 'bar', x: 64, y: 238, w: 180},
  {kind: 'bar', x: 44, y: 278, w: 160, h: 5, color: WHITE},
  {kind: 'bar', x: 64, y: 306, w: 240},
  {kind: 'bar', x: 64, y: 324, w: 200},
  {kind: 'bar', x: 44, y: 362, w: 140, h: 5, color: WHITE},
];

export const SC15: React.FC = () => {
  const N = useCurrentFrame() + F0;
  // 离场（2674 起 12 帧，末帧 α=0）
  const ex = N - 2673;
  const gOp = ex <= 0 ? 1 : 1 - Math.pow(clamp01(ex / 12), 1.5);
  const gDy = Math.min(10, exitAccel(ex, 0.2)); // 轻微下摇，限幅 ≤10px（QC v2 复验 N1：29px 会把灰旁注推进字幕带）
  // 左：文档树
  const tn = N - 2317;
  const treeX = TREE.x - slideUp(tn, 300);
  const evenOp = 0.45 * fadeIn(N - 2346, 6) * (1 - clamp01((N - 2368) / 8));
  const hlOp = 0.28 * fadeIn(N - 2400, 10);
  // 中：卡片 + 前缀条
  const cardS = scaleIn(N - 2394);
  const barSy = scaleIn(N - 2402, 12);
  const typed = N < 2412 ? 0 : Math.min(PREFIX.length, Math.floor((N - 2412) / 1.2) + 1);
  // 右：Anthropic / −49%
  const cn = N - 2606;
  const val = Math.round(49 * clamp01(cn / 20));
  const cScale = emphasisPulse(N - 2626, {peak: 1.12});

  return (
    <div style={{position: 'absolute', inset: 0, opacity: gOp, transform: gDy ? `translateY(${gDy.toFixed(1)}px)` : undefined}}>
      {/* 左半：带层级的文档树 */}
      {tn >= 0 ? (
        <div style={{...abs(treeX, TREE.y, TREE.w, TREE.h), opacity: fadeIn(tn, 6)}}>
          <Box x={0} y={0} w={TREE.w} h={TREE.h} r={10} sw={2.5}>
            {hlOp > 0 ? <div style={{...abs(14, CUTS[0], TREE.w - 32, CUTS[1] - CUTS[0]), background: `rgba(102,48,248,${hlOp.toFixed(3)})`, borderRadius: 4}} /> : null}
            {ENTRIES.map((e, i) => {
              const op = fadeIn(N - (2322 + 3 * i), 4);
              if (op <= 0) return null;
              return e.kind === 'text' ? (
                <LText key={i} x={e.x} y={e.y} size={e.size!} weight={e.weight} color={e.color} opacity={op}>
                  {e.text}
                </LText>
              ) : (
                <Bar key={i} x={e.x} y={e.y} w={e.w!} h={e.h ?? 3} color={e.color ?? GREY} opacity={op * (e.color ? 1 : 0.9)} />
              );
            })}
            {evenOp > 0 ? EVEN.map((y) => <div key={y} style={{...abs(14, y - 1, TREE.w - 32, 2), opacity: evenOp, background: `repeating-linear-gradient(90deg, ${GREY_LIGHT} 0 9px, transparent 9px 16px)`}} />) : null}
            {CUTS.map((y, k) => {
              const p = clamp01((N - (2368 + 4 * k)) / 12);
              return p > 0 ? <div key={y} style={{...abs(14, y - 1, (TREE.w - 32) * p, 2), background: `repeating-linear-gradient(90deg, ${PURPLE_LIGHT} 0 9px, transparent 9px 16px)`}} /> : null;
            })}
          </Box>
        </div>
      ) : null}
      <SoftIn N={N} f0={2380}>
        <CText cx={300} cy={612} size={22} weight={600} color={GREY}>沿标题边界切，而不是等距</CText>
      </SoftIn>

      {/* 中：chunk 卡 + 上下文前缀条 */}
      <Svg bloom={false}>
        <LineArrow x0={TREE.x + TREE.w} y0={TREE.y + (CUTS[0] + CUTS[1]) / 2} x1={556} y1={450} p={slideIn(N - 2404, 14)} rodW={2.5} headL={16} headW={16} color={PURPLE_LIGHT} dashed />
      </Svg>
      {cardS > 0 ? (
        <div style={{...abs(560, 400, 180, 100), transform: `scale(${cardS.toFixed(4)})`}}>
          <ChunkCard x={0} y={0} w={180} h={100} lines={4} seed={5} active />
        </div>
      ) : null}
      {barSy > 0 ? (
        <div style={{...abs(560, 356, 330, 34), transform: `scaleY(${barSy.toFixed(4)})`, transformOrigin: '50% 100%'}}>
          <Box x={0} y={0} w={330} h={34} r={6} fill={PURPLE} sw={0} glow="0 0 14px 3px rgba(102,45,248,.4)" />
          <LText x={12} y={6} size={22} weight={700}>
            {PREFIX.slice(0, typed)}
          </LText>
        </div>
      ) : null}
      <SoftIn N={N} f0={2572}>
        <Pill x={816} y={320} w={86} h={34} fill={PURPLE} sw={2} text="BM25" fontSize={22} weight={700} family={FONT_TECH} textDy={-1} style={{fontStyle: 'italic'}} glow="0 0 14px 3px rgba(102,45,248,.45)" />
      </SoftIn>

      {/* 右：Anthropic 实验 → −49% */}
      <SoftIn N={N} f0={2498}>
        <Pill x={955} y={300} w={170} h={44} sw={2.5} text="Anthropic" fontSize={26} weight={700} />
      </SoftIn>
      <SoftIn N={N} f0={2500}>
        <TechText cx={1040} cy={372} text="Contextual Retrieval" fontSize={24} scaleX={0.82} />
      </SoftIn>
      {cn >= 0 ? (
        <div style={{...abs(0, 0, 1280, 720), opacity: fadeIn(cn, 8), transform: `translate(1040px,440px) scale(${cScale.toFixed(4)}) translate(-1040px,-440px)`, transformOrigin: '0 0'}}>
          <CText cx={1040} cy={440} size={72} weight={800} color={ORANGE} letterSpacing={-1} shadow="0 0 26px rgba(240,95,65,.75), 0 0 8px rgba(240,95,65,.5)" style={{fontVariantNumeric: 'tabular-nums'}}>
            {`−${val}%`}
          </CText>
        </div>
      ) : null}
      <CText cx={1040} cy={500} size={22} weight={600} color={GREY} opacity={fadeIn(N - 2620, 10) * (N >= 2620 ? 1 : 0)}>
        Top-20 检索失败率
      </CText>
    </div>
  );
};
