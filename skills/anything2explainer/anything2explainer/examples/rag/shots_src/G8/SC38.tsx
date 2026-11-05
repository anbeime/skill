import React from 'react';
import {useCurrentFrame} from 'remotion';
import {GlitchIn, clamp01, easeOutCubic, emphasisPulse, rnd} from '../../common';
import {Svg, LineArrow, TechText, CText, Pill, MonoText, PURPLE_LIGHT, GREY, WHITE, GLOW_PURPLE_S, abs, fadeIn, slideUp, SoftIn} from '../../ui';
import {FR, PageCard, EmbedBox, mix, Anchor, exitOut} from './shared';

/**
 * SC38 多模态 RAG（6991–7167）。节拍：6999 标签 + 三张页面缩略图卡 / 7033 箭头→Embedding 盒→向量数字列 / 7112 问句飞向向量列，命中折线图卡。
 * 离场：7153 起 exitOut 14 帧（下摇 + 淡出，末 6 帧线性收 0，7167 恰为 0；QC v1 统一 G8 三处离场）。卡片入场 Δ100 + 8 帧渐入，不再穿字幕带。
 */
const F0 = FR.SC38.from, F1 = FR.SC38.to;
const CARD_X = [195, 325, 455];
const CARD_Y = 425; // 主区行中心（HUD 副标在 y≈94，标签移到卡组上方避免叠成三行）
const KINDS = ['bar', 'line', 'shot'] as const;
const CAPS = ['柱状图', '折线图', '截图'];
const COL_X = [890, 965, 1040];
const ROWS = 6, ROW_Y0 = 347, ROW_H = 30;
const FLY0 = 7112, HIT = FLY0 + 16;

export const SC38: React.FC = () => {
  const N = useCurrentFrame() + F0;
  const ex = exitOut(N - (F1 - 14), 14);
  const hitK = clamp01((N - HIT) / 11);
  const pulse = emphasisPulse(N - HIT - 2, {peak: 1.1});
  // 问句：7106 SoftIn 淡入于右上（闪烁整改：本镜头 glitch 只给「Multimodal RAG」），7112 起 16 帧飞到向量列上方
  const ft = clamp01((N - FLY0) / 16);
  const fe = easeOutCubic(ft);
  const qx = 1060 + (965 - 1060) * fe, qy = 190 + (287 - 190) * fe;
  return (
    <div style={{position: 'absolute', inset: 0, opacity: ex.op, transform: `translateY(${ex.dy.toFixed(2)}px)`}}>
      <GlitchIn N={N} f0={6999}>
        <TechText cx={325} cy={296} text="Multimodal RAG" fontSize={34} />
      </GlitchIn>
      {CARD_X.map((cx, i) => {
        const n = N - (6999 + i * 2);
        if (n < 0) return null;
        const active = i === 1;
        const k = active ? hitK : 0;
        return (
          <div key={i} style={{position: 'absolute', inset: 0, opacity: fadeIn(n, 8), transform: `translateY(${slideUp(n, 100).toFixed(2)}px)`}}>
            <Anchor cx={cx} cy={CARD_Y} s={active ? pulse : 1}>
              <PageCard cx={cx} cy={CARD_Y} kind={KINDS[i]} activeK={k} />
            </Anchor>
            <CText cx={cx} cy={524} size={24} weight={600} color={mix(GREY, PURPLE_LIGHT, k)}>{CAPS[i]}</CText>
          </div>
        );
      })}
      <Svg>
        <LineArrow x0={525} y0={CARD_Y} x1={590} y1={CARD_Y} p={clamp01((N - 7033) / 14)} />
        <LineArrow x0={795} y0={CARD_Y} x1={860} y1={CARD_Y} p={clamp01((N - 7052) / 14)} />
      </Svg>
      <SoftIn N={N} f0={7040}>
        <EmbedBox x={600} y={CARD_Y - 31} w={180} h={62} />
      </SoftIn>
      {hitK > 0 ? <div style={{...abs(COL_X[1] - 36, ROW_Y0 - 26, 72, ROWS * ROW_H + 18), borderRadius: 8, border: `2px solid ${PURPLE_LIGHT}`, boxSizing: 'border-box', boxShadow: GLOW_PURPLE_S, opacity: hitK}} /> : null}
      {COL_X.map((x, c) =>
        Array.from({length: ROWS}, (_, r) => {
          const n = N - (7062 + (c * ROWS + r) * 2);
          if (n < 0) return null;
          const v = rnd(c + 1, r + 1, 38) * 1.8 - 0.9;
          const txt = (v >= 0 ? ' ' : '') + v.toFixed(2);
          return (
            <MonoText key={`${c}-${r}`} x={x - 30} y={ROW_Y0 + r * ROW_H - 14} size={22} color={c === 1 ? mix(WHITE, PURPLE_LIGHT, hitK) : WHITE} opacity={fadeIn(n, 6) * (c === 1 ? 1 : 1 - 0.35 * hitK)}>
              {txt}
            </MonoText>
          );
        }),
      )}
      <SoftIn N={N} f0={FLY0 - 6}>
        <Pill x={qx - 150} y={qy - 22} w={300} h={44} text="Q3 营收趋势图在哪？" fontSize={24} weight={700} sw={2} glow={hitK > 0 ? `0 0 16px 4px rgba(102,45,248,${(0.45 * hitK).toFixed(2)})` : undefined} stroke={mix(WHITE, PURPLE_LIGHT, hitK)} />
      </SoftIn>
    </div>
  );
};
