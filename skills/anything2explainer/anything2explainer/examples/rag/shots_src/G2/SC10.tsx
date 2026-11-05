import React from 'react';
import {useCurrentFrame} from 'remotion';
import {clamp01, powOutRemain, easeInOutPow} from '../../common';
import {Pill, Svg, LineArrow, Check, DocIcon, LLMIcon, WHITE, GREY, PURPLE, PURPLE_LIGHT, fadeIn, scaleIn, stagger, SoftIn} from '../../ui';
import {mixHex, StepPill} from './parts';

/**
 * SC10 检索 + 生成 = 靠证据 · N 1329–1480（S10 1337–1478：1337「它把检索和生成两个动作接在一起」/ 1413「回答不再只靠记忆」/ 1454「而是靠证据」）
 * 版式：上半 两个大胶囊「检索」「生成」200×70 34px，中心 y 247：自两侧滑入到 x 380 / 900，再向中间靠拢到 470 / 810，
 *       两胶囊之间用 3px 白线自各自边缘长出接到中点、中点紫色接头（r9）+ 4 帧白闪 = "接成一体"。
 *       下半左 LLMIcon (300,445) size 110 + 胶囊「记忆」(368,423)：淡入后 8 帧变灰并下沉 12px；
 *       下半右 三张 DocIcon（首行紫）(748/814/880, 410) + 紫胶囊「证据」(962,423) + 绿勾 (1150,445)；中间白箭头 (528→700, 445)。
 * 节拍：1337 滑入（Δ520/22）；1362 靠拢 18 帧；1380 连接线 16 帧；1392 接头缩放入 6 帧；1396 白闪 4 帧；
 *       1413 记忆组淡入 12 帧；1421 起 11 帧变灰 + 12 帧下沉；1450 箭头 14 帧；1454/1456/1458 文档缩放入；1458「证据」SoftIn（本镜头无 glitch，协议 §8）；1462 绿勾 12 帧；1475–1480 整组 6 帧淡出到 0（opacity = 1 − (n/6)^1.5，与 1481 章节卡「02」淡入相接；复验 C1-3：原 exitFade 0.87→0 硬切）。
 */
const F0 = 1329;
const T_IN = 1337, T_CONV = 1362, T_LINK = 1380, T_JOINT = 1392, T_FLASH = 1396, T_MEM = 1413, T_GREY = 1421, T_ARROW = 1450, T_EV = 1454, T_EVPILL = 1458, T_CHECK = 1462, T_EXIT = 1474;

const PW = 200, PH = 70, PY = 212, CY = PY + PH / 2; // 247
const LY = 445; // 下半组中轴 y
const DOCS_X = [748, 814, 880];
const FLASH_A = [0.85, 0.55, 0.3, 0.12];

export const SC10: React.FC = () => {
  const N = useCurrentFrame() + F0;
  // 末 6 帧（1475–1480）整组淡出到 0：n=1..6 → 0.93 / 0.81 / 0.65 / 0.46 / 0.24 / 0
  const exOp = N <= T_EXIT ? 1 : Math.max(0, 1 - Math.pow((N - T_EXIT) / 6, 1.5));

  // 上半：两胶囊中心 x
  const rem = N < T_IN ? 1 : powOutRemain(N - T_IN, 22, 2.5);
  const conv = N < T_CONV ? 0 : easeInOutPow(2.5)(clamp01((N - T_CONV) / 18));
  const cxL = 380 - 520 * rem + 90 * conv;
  const cxR = 900 + 520 * rem - 90 * conv;
  const pillOp = N < T_IN ? 0 : 1;
  // 连接线：自胶囊边缘向中点长出
  const lp = clamp01((N - T_LINK) / 16);
  const lx0 = cxL + PW / 2, rx0 = cxR - PW / 2;
  const jointS = N < T_JOINT ? 0 : scaleIn(N - T_JOINT, 6);
  const fi = N - T_FLASH;
  const flashA = fi >= 0 && fi < FLASH_A.length ? FLASH_A[fi] : 0;

  // 下半左：记忆组
  const mn = N - T_MEM;
  const memOp = mn < 0 ? 0 : fadeIn(mn, 12);
  const gk = clamp01((N - T_GREY) / 11);
  const sink = 12 * easeInOutPow(2.5)(clamp01((N - T_GREY) / 12));
  const memCol = mixHex(WHITE, GREY, gk);
  const memAccent = mixHex(PURPLE, GREY, gk);

  // 下半右：证据组
  const ap = clamp01((N - T_ARROW) / 14);
  const chk = clamp01((N - T_CHECK) / 12);

  return (
    <div style={{position: 'absolute', inset: 0, opacity: exOp}}>
      {/* 上半：检索 / 生成 */}
      {pillOp > 0 ? (
        <>
          <Pill x={cxL - PW / 2} y={PY} w={PW} h={PH} sw={3} text="检索" fontSize={34} weight={800} letterSpacing={4} textDy={-3} />
          <Pill x={cxR - PW / 2} y={PY} w={PW} h={PH} sw={3} text="生成" fontSize={34} weight={800} letterSpacing={4} textDy={-3} />
        </>
      ) : null}
      <Svg>
        {lp > 0 ? (
          <>
            <line x1={lx0} y1={CY} x2={lx0 + (640 - lx0) * lp} y2={CY} stroke={WHITE} strokeWidth={3} />
            <line x1={rx0} y1={CY} x2={rx0 - (rx0 - 640) * lp} y2={CY} stroke={WHITE} strokeWidth={3} />
          </>
        ) : null}
        {jointS > 0 ? <circle cx={640} cy={CY} r={10 * jointS} fill={PURPLE} stroke={WHITE} strokeWidth={2.5} /> : null}
        {flashA > 0 ? (
          <>
            <circle cx={640} cy={CY} r={26 + 10 * fi} fill={WHITE} opacity={flashA * 0.55} />
            <circle cx={640} cy={CY} r={12 + 3 * fi} fill={WHITE} opacity={flashA} />
          </>
        ) : null}
        {/* 记忆 → 证据 箭头 */}
        <LineArrow x0={528} y0={LY} x1={700} y1={LY} p={ap} />
        {/* 绿勾 */}
        {chk > 0 ? <Check cx={1150} cy={LY} size={56} sw={6} p={chk} /> : null}
      </Svg>

      {/* 下半左：记忆（白→灰、下沉） */}
      {memOp > 0 ? (
        <div style={{position: 'absolute', inset: 0, opacity: memOp, transform: sink ? `translateY(${sink.toFixed(2)}px)` : undefined}}>
          <LLMIcon cx={300} cy={LY} size={110} color={memCol} accent={memAccent} glow={gk < 0.5} />
          <Pill x={368} y={LY - 22} w={130} h={44} sw={2} stroke={memCol} text="记忆" fontSize={26} weight={700} color={memCol} />
        </div>
      ) : null}

      {/* 下半右：证据（三文档 2 帧错峰缩放入 + 紫胶囊 + 绿勾） */}
      {DOCS_X.map((x, i) => {
        const n = N - T_EV - stagger(i, 2);
        if (n < 0) return null;
        const s = 0.2 + 0.8 * scaleIn(n, 21);
        return (
          <div key={i} style={{position: 'absolute', left: x, top: LY - 35, width: 56, height: 70, opacity: fadeIn(n, 6), transform: `scale(${s.toFixed(4)})`, transformOrigin: '50% 50%'}}>
            <DocIcon x={0} y={0} w={56} h={70} lines={4} sw={2.5} accent={PURPLE_LIGHT} />
          </div>
        );
      })}
      <SoftIn N={N} f0={T_EVPILL}>
        <StepPill cx={1027} y={LY - 22} text="证据" active />
      </SoftIn>
    </div>
  );
};
