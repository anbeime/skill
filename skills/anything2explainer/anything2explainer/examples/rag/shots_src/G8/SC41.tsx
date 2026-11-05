import React from 'react';
import {useCurrentFrame} from 'remotion';
import {clamp01, easeInOutPow, rnd, powOutRemain} from '../../common';
import {Svg, Cross, CText, Pill, PURPLE, PURPLE_LIGHT, ORANGE, WHITE, GLOW_PURPLE_S, fadeIn, fadeOut, scaleIn, exitAccel, SoftIn} from '../../ui';
import {FR, RulerPart, WindowPart, WIN, IconPill, mix} from './shared';

/**
 * SC41 搭档不是对手（7504–7753）。承接 SC40 的刻度尺 + 上下文窗口。
 * 节拍：7512 文档溢出窗口（150 枚小方块 rnd 顺序堆到右侧画外）+ 绿勾→红叉 / 7593 三枚橙色 Pill「权限」「时效」「成本」错峰 8 帧 SoftIn 淡入 /
 * 7641 刻度尺组下沉淡出、左「RAG · 找」紫胶囊自左滑入 / 7675 右「长上下文 · 读」自右滑入 + 白色「+」/ 7709 两胶囊靠拢 20px、「+」变紫柔光、「搭档」胶囊 SoftIn 淡入。闪烁整改：SC41 不在白名单，全部 SoftIn。
 * 离场：7744 起 10 帧淡出（含末 2 帧）。
 */
const F0 = FR.SC41.from, F1 = FR.SC41.to;
const OV_N = 120; // 120 枚 × 3 节点 = 360 SVG 节点（单帧 DOM ≤ 600 红线）
// 溢出方块：前 36 枚填满窗口内部，10 枚冒出窗口顶部，其余向右堆出画外（x 1110→1420）。出现时刻 ≈ 距窗口距离 + 抖动（≈24 帧内）
const OV = Array.from({length: OV_N}, (_, k) => {
  const u = rnd(k, 41.1), v = rnd(k, 41.2), j = rnd(k, 41.3);
  if (k < 36) return {x: WIN.x + 14 + u * (WIN.w - 40), y: WIN.y + 30 + v * (WIN.h - 56), t: j * 8, r: (u - 0.5) * 16};
  if (k < 46) return {x: WIN.x + 150 + u * (WIN.w - 180), y: WIN.y - 34 + v * 30, t: 6 + j * 8, r: (v - 0.5) * 30}; // x≥1000：避开框外左上的「上下文窗口」标签
  const x = WIN.x + WIN.w - 40 + u * 310;
  return {x, y: 100 + v * 215, t: 8 + ((x - 1100) / 300) * 12 + j * 5, r: (v - 0.5) * 40};
});
const ORANGE_PILLS = ['权限', '时效', '成本'];
const LP = {w: 340, h: 90, cx: 435, cy: 450}; // 左胶囊终位中心
const RP = {w: 380, h: 90, cx: 865, cy: 450};

export const SC41: React.FC = () => {
  const N = useCurrentFrame() + F0;
  const eio = easeInOutPow(2.5);
  const exO = fadeOut(N - (F1 - 9), 10);
  // 刻度尺组离场（7641）
  const nx = N - 7633; // QC v1：提前 8 帧，减少与「RAG · 找」滑入的叠帧
  const rulerOp = fadeOut(nx, 15), rulerDy = exitAccel(nx, 0.5);
  // 绿勾→红叉
  const chkOp = fadeOut(N - 7528, 6);
  const crossP = clamp01((N - 7534) / 12);
  // 靠拢 + 「+」变色
  const cv = eio(clamp01((N - 7709) / 16));
  const plusK = clamp01((N - 7709) / 11);
  const lx = LP.cx - 600 * powOutRemain(N - 7641, 22, 2.5) + 20 * cv;
  const rx = RP.cx + 600 * powOutRemain(N - 7675, 22, 2.5) - 20 * cv;
  return (
    <div style={{position: 'absolute', inset: 0, opacity: exO}}>
      <RulerPart N={N} opacity={rulerOp} dy={rulerDy} />
      <WindowPart N={N} checkOpacity={chkOp} />
      {/* 溢出方块（单 Svg） */}
      <Svg bloom={false}>
        {OV.map((o, k) => {
          const n = N - (7512 + o.t);
          if (n < 0) return null;
          const s = scaleIn(n, 6);
          return (
            <g key={k} transform={`translate(${o.x.toFixed(1)} ${o.y.toFixed(1)}) rotate(${o.r.toFixed(1)}) scale(${s.toFixed(3)})`} opacity={fadeIn(n, 3)}>
              <path d="M-8,-10 H4 L8,-6 V10 H-8 Z" fill="#000" stroke={WHITE} strokeWidth={1.6} strokeLinejoin="round" />
              <rect x={-4} y={0.5} width={8} height={1.8} fill={WHITE} opacity={0.8} />
            </g>
          );
        })}
      </Svg>
      {crossP > 0 ? (
        <Svg>
          <Cross cx={WIN.x + WIN.w / 2} cy={WIN.y + WIN.h / 2} size={96} sw={9} p={crossP} />
        </Svg>
      ) : null}
      {ORANGE_PILLS.map((t, i) => (
        <SoftIn key={t} N={N} f0={7593 + i * 8}>
          <Pill x={690} y={150 + i * 56} w={112} h={42} fill={ORANGE} text={t} fontSize={26} weight={800} sw={2} glow="0 0 18px 4px rgba(240,95,65,.4)" />
        </SoftIn>
      ))}
      {/* 两大胶囊 + 「+」 */}
      {N >= 7641 ? <IconPill x={lx - LP.w / 2} y={LP.cy - LP.h / 2} w={LP.w} h={LP.h} fill={PURPLE} text="RAG · 找" icon="search" glow={GLOW_PURPLE_S} /> : null}
      {N >= 7675 ? <IconPill x={rx - RP.w / 2} y={RP.cy - RP.h / 2} w={RP.w} h={RP.h} text="长上下文 · 读" icon="book" /> : null}
      {N >= 7675 ? (
        <CText cx={640} cy={450} size={64} weight={900} color={mix(WHITE, PURPLE_LIGHT, plusK)} opacity={fadeIn(N - 7675, 10)} shadow={plusK > 0 ? `0 0 ${Math.round(22 * plusK)}px rgba(102,45,248,${(0.9 * plusK).toFixed(2)}), 0 0 ${Math.round(48 * plusK)}px rgba(102,45,248,${(0.5 * plusK).toFixed(2)})` : undefined} dy={-4}>
          +
        </CText>
      ) : null}
      <SoftIn N={N} f0={7711}>
        <Pill x={560} y={537} w={160} h={46} fill={PURPLE} text="搭档" fontSize={28} weight={800} letterSpacing={4} sw={2.5} glow="0 0 14px 3px rgba(102,45,248,.35)" />
      </SoftIn>
    </div>
  );
};
