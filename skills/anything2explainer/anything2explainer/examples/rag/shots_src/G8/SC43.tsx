import React from 'react';
import {useCurrentFrame} from 'remotion';
import {clamp01, emphasisPulse} from '../../common';
import {Svg, Check, Cross, Pill, PURPLE, PURPLE_LIGHT, GREY, WHITE, ORANGE, fadeIn, scaleIn, SoftIn} from '../../ui';
import {FR, OpenBook, Anchor, exitOut} from './shared';

/**
 * SC43 手册整理得有多好（7870–8052）。左 (360,400) 乱页灰书 + 3 帧一换的快速翻页，标「翻得快」+ 红叉（7927）；右 (920,400) 整齐的书 + 5 个彩色索引标签，标「整理得好」+ 绿勾 + 紫柔光 + 脉冲（7986）。
 * 两书 7878 起 2 帧错峰缩放入场。闪烁整改：SC43 不在白名单，两枚标签 SoftIn 淡入。离场：8038 起 exitOut 14 帧（末 6 帧线性收 0，8052 恰为 0；QC v1）。勾/叉在 p=0 时不渲染（round linecap 会露出端点亮点）。
 */
const F0 = FR.SC43.from, F1 = FR.SC43.to;
const BY = 395, LX = 360, RX = 920;
const TABS = [PURPLE, ORANGE, WHITE, GREY, PURPLE];

export const SC43: React.FC = () => {
  const N = useCurrentFrame() + F0;
  const ex = exitOut(N - (F1 - 14), 14);
  const crossP = clamp01((N - 7931) / 10), checkP = clamp01((N - 7990) / 12);
  const nL = N - 7878, nR = N - 7880;
  const step = Math.max(0, Math.floor((N - 7886) / 3)); // 翻页：3 帧一换
  const pulse = emphasisPulse(N - 7988, {peak: 1.08});
  const glowK = clamp01((N - 7986) / 12);
  return (
    <div style={{position: 'absolute', inset: 0, opacity: ex.op, transform: `translateY(${ex.dy.toFixed(2)}px)`}}>
      {nL >= 0 ? (
        <Anchor cx={LX} cy={BY} s={scaleIn(nL)} opacity={fadeIn(nL, 8)}>
          <OpenBook cx={LX} cy={BY} w={360} h={240} color={GREY} variant="messy" flipPose={step % 4} seed={7 + (step % 5)} />
        </Anchor>
      ) : null}
      {nR >= 0 ? (
        <Anchor cx={RX} cy={BY} s={scaleIn(nR) * pulse} opacity={fadeIn(nR, 8)}>
          <OpenBook cx={RX} cy={BY} w={360} h={240} variant="tidy" tabs={TABS} accent={PURPLE_LIGHT} glow={glowK > 0 ? `drop-shadow(0 0 ${(4 + 12 * glowK).toFixed(1)}px rgba(120,70,248,${(0.35 + 0.5 * glowK).toFixed(2)}))` : undefined} />
        </Anchor>
      ) : null}
      <SoftIn N={N} f0={7927}>
        <Pill x={LX - 110} y={548} w={150} h={44} text="翻得快" fontSize={26} weight={700} stroke={GREY} color={GREY} sw={2} />
      </SoftIn>
      <SoftIn N={N} f0={7986}>
        <Pill x={RX - 120} y={548} w={170} h={44} fill={PURPLE} text="整理得好" fontSize={26} weight={800} sw={2.5} glow="0 0 14px 3px rgba(102,45,248,.35)" />
      </SoftIn>
      {crossP > 0 || checkP > 0 ? (
        <Svg>
          {crossP > 0 ? <Cross cx={LX + 80} cy={570} size={34} sw={6} p={crossP} /> : null}
          {checkP > 0 ? <Check cx={RX + 92} cy={570} size={44} sw={6} p={checkP} /> : null}
        </Svg>
      ) : null}
    </div>
  );
};
