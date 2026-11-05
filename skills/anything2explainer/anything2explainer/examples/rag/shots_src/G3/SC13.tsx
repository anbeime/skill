import React from 'react';
import {useCurrentFrame} from 'remotion';
import {easeInOutPow, slideIn, clamp01} from '../../common';
import {CText, LLMIcon, Svg, LineArrow, GREY, abs, scaleIn, fadeOut, exitAccel, fadeIn, SoftIn} from '../../ui';
import {DocCard} from './g3ui';
import {DOC_CX, DOC_CY} from './SC12';

/**
 * SC13 第二步 切块（1891–2054，S13）
 * 承接 SC12 的文档卡（同一 DocCard 几何）：1891–1911 平移到中央 (640,400) 并放大 1.1（easeInOutPow 2.5，20 帧）。
 * 节拍：1899 第二步切块 / 1921 读不完一整本（左侧小 LLMIcon + 灰问号 + 灰虚线）/ 1974 切成 chunk（三条紫虚线 draw-on → 1990 四段分离，边框白→紫，右上「chunk」）
 * 2044 起整组下摇淡出，SC14 硬接。
 */
const F0 = 1891;
const EASE = easeInOutPow(2.5);

export const SC13: React.FC = () => {
  const N = useCurrentFrame() + F0;
  const ex = N - 2044;
  const gOp = ex > 0 ? fadeOut(ex, 10) : 1;
  const gDy = ex > 0 ? exitAccel(ex, 0.9) : 0;
  // 文档卡运镜
  const t = EASE(clamp01((N - F0) / 20));
  const cx = DOC_CX + (640 - DOC_CX) * t;
  const s = 1 + 0.1 * t;
  // 切割与分离
  const cuts = [0, 1, 2].map((k) => clamp01((N - (1974 + 3 * k)) / 10));
  const split = N >= 1990;
  const gap = 12 * slideIn(N - 1990, 18);
  const activeK = [0, 1, 2, 3].map((i) => clamp01((N - (2000 + 2 * i)) / 11));
  const tagOp = [0, 1, 2, 3].map((i) => fadeIn(N - (2004 + 2 * i), 8));
  // 左：读不完的模型
  const llmS = scaleIn(N - 1921);

  return (
    <div style={{position: 'absolute', inset: 0, opacity: gOp, transform: gDy ? `translateY(${gDy.toFixed(1)}px)` : undefined}}>
      {llmS > 0 ? (
        <div style={{...abs(200, 350, 100, 100), transform: `scale(${llmS.toFixed(4)})`}}>
          <LLMIcon cx={50} cy={50} size={100} glow={false} />
        </div>
      ) : null}
      <SoftIn N={N} f0={1925}>
        <CText cx={332} cy={334} size={60} weight={900} color={GREY}>?</CText>
      </SoftIn>
      <Svg bloom={false}>
        <LineArrow x0={308} y0={400} x1={cx - 180 * s - 10} y1={400} p={slideIn(N - 1927, 14)} rodW={2.5} headL={16} headW={16} color={GREY} dashed />
      </Svg>
      <DocCard cx={cx} cy={DOC_CY} s={s} cuts={cuts} cutOp={1 - clamp01((N - 1990) / 6)} split={split} gap={gap} activeK={activeK} tagOp={tagOp} />
    </div>
  );
};
