import React from 'react';
import {useCurrentFrame} from 'remotion';
import {clamp01, easeOutCubic, emphasisPulse, FONT_ORB, FONT_WIDE} from '../../common';
import {CText, Pill, TechText, LLMIcon, PURPLE, ORANGE, GREY, TEXT_GLOW, PILL_SHADOW, fadeIn, scaleIn, slideUp, SoftIn} from '../../ui';
import {FR, fmtInt, Anchor, exitOut} from './shared';

/**
 * SC39 百万 token 还需要 RAG？（7168–7301）。节拍：7176 LLMIcon + 「上下文窗口」 / 7189 计数 0→1,000,000（26 帧）+ tokens / 7260 「RAG」紫胶囊 + 橙色大问号（SoftIn 淡入 + 脉冲）。闪烁整改：SC39 不在白名单，全部 SoftIn。
 * QC v1：末 6 帧 exitOut（7295–7301 线性收 0 + 轻微下摇），避免 7302 从满画面切到空帧。数字依据：research §5.4（Gemini / Claude 1M token 上下文）。
 */
const F0 = FR.SC39.from, F1 = FR.SC39.to;
const CNT0 = 7189, CNT_LEN = 26;

export const SC39: React.FC = () => {
  const N = useCurrentFrame() + F0;
  const nIcon = N - 7176;
  const nc = N - CNT0;
  const val = nc < 0 ? 0 : Math.round(1e6 * easeOutCubic(clamp01(nc / CNT_LEN)));
  const qs = emphasisPulse(N - 7274, {peak: 1.15, up: 12, hold: 4, down: 14});
  const ex = exitOut(N - (F1 - 6), 6);
  return (
    <div style={{position: 'absolute', inset: 0, opacity: ex.op, transform: `translateY(${ex.dy.toFixed(2)}px)`}}>
      {nIcon >= 0 ? (
        <Anchor cx={230} cy={380} s={scaleIn(nIcon)} opacity={fadeIn(nIcon, 8)}>
          <LLMIcon cx={230} cy={380} size={110} />
        </Anchor>
      ) : null}
      <SoftIn N={N} f0={7176}>
        <Pill x={530} y={228} w={220} h={44} text="上下文窗口" fontSize={26} weight={700} stroke={GREY} color={GREY} sw={2} />
      </SoftIn>
      <SoftIn N={N} f0={CNT0}>
        <CText cx={640} cy={350} size={96} family={FONT_ORB} weight={700} letterSpacing={2} shadow={TEXT_GLOW} style={{fontVariantNumeric: 'tabular-nums'}}>
          {fmtInt(val)}
        </CText>
      </SoftIn>
      {nc >= 0 ? (
        <div style={{position: 'absolute', inset: 0, opacity: fadeIn(nc, 10), transform: `translateY(${slideUp(nc, 120).toFixed(2)}px)`}}>
          <TechText cx={640} cy={430} text="tokens" fontSize={34} color={GREY} glow={false} />
        </div>
      ) : null}
      <SoftIn N={N} f0={7260}>
        <Pill x={945} y={290} w={150} h={60} fill={PURPLE} text="RAG" fontSize={34} weight={700} family={FONT_WIDE} letterSpacing={3} sw={2.5} style={{filter: PILL_SHADOW}} />
      </SoftIn>
      <SoftIn N={N} f0={7262}>
        <Anchor cx={1020} cy={468} s={qs}>
          <CText cx={1020} cy={468} size={180} family={FONT_ORB} weight={800} color={ORANGE} shadow="0 0 30px rgba(240,95,65,.55), 0 0 8px rgba(240,95,65,.5)" dy={0}>
            ?
          </CText>
        </Anchor>
      </SoftIn>
    </div>
  );
};
