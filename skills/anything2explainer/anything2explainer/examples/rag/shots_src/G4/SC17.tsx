import React from 'react';
import {useCurrentFrame} from 'remotion';
import {easeOutCubic, clamp01} from '../../common';
import {CText, Pill, Svg, PURPLE, PURPLE_LIGHT, WHITE, GREY, GREY_MID, GREY_LINE, GREY_LIGHT, fadeIn, scaleIn, exitAccel, SoftIn} from '../../ui';
import {VSPACE, VSPACE_POINTS, VSPACE_PAIRS} from './vspace';
export {VSPACE, VSPACE_POINTS} from './vspace';

/**
 * SC17 向量空间邻居（2861–3033）
 * 节拍：2869 意思相近（网格 wipe）→ 2878 灰点 1 帧错峰亮起 → 2902 向量就靠得近（三对近点细灰线）→
 *      2931 退款流程 / 怎么把钱要回来（两紫点缩放入场 + 标签 SoftIn 淡入；2950 远点「年假规定」灰）→
 *      2988 是邻居（紫线段 + 虚线高亮圈 draw-on + 「邻居」小 Pill；远点闪一次）→ 3026 起 8 帧离场。
 * 网格/点分布导出自 ./vspace（G5 SC23 复用）。
 */
export const F0 = 2861;
const B_GRID = 2869, B_PTS = 2878, B_PAIRS = 2902, B_AB = 2931, B_FAR = 2950, B_NEAR = 2988, EXIT = 3026;

const {x0, x1, y0, y1, cell, A, B, FAR, LABEL_A, LABEL_B, LABEL_FAR, LABEL_NEAR, RING} = VSPACE;
const COLS = Math.round((x1 - x0) / cell), ROWS = Math.round((y1 - y0) / cell);
const RING_LEN = 2 * Math.PI * RING.r;

export const SC17: React.FC = () => {
  const N = useCurrentFrame() + F0;
  const ne = N - EXIT;
  const exitOp = ne <= 0 ? 1 : Math.max(0, 1 - ne / 8);
  const exitDy = exitAccel(ne, 0.5);

  // 网格 wipe（自左向右 20 帧）
  const gridW = (x1 - x0) * easeOutCubic((N - B_GRID) / 20);
  // 紫点缩放
  const sA = scaleIn(N - B_AB), sB = scaleIn(N - (B_AB + 4));
  const sFar = scaleIn(N - B_FAR, 14);
  // 邻居连线 / 高亮圈
  const pLine = easeOutCubic((N - B_NEAR) / 12);
  const pRing = easeOutCubic((N - (B_NEAR + 6)) / 14);
  // 远点闪一次（两次明暗，16 帧）
  const nBlink = N - (B_NEAR + 8);
  const farOp = nBlink < 0 || nBlink > 16 ? 1 : 1 - 0.75 * Math.abs(Math.sin((Math.PI * nBlink) / 8));

  if (N < B_GRID) return null;
  return (
    <div style={{position: 'absolute', inset: 0, opacity: exitOp, transform: `translateY(${exitDy.toFixed(2)}px)`}}>
      <Svg bloom={false}>
        <defs>
          <clipPath id="g4-sc17-grid">
            <rect x={x0 - 2} y={y0 - 2} width={Math.max(0, gridW + 4)} height={y1 - y0 + 4} />
          </clipPath>
        </defs>
        {/* 网格：#4A4A4A 1px，.5 对齐 */}
        <g clipPath="url(#g4-sc17-grid)">
          {Array.from({length: COLS + 1}, (_, k) => <line key={`v${k}`} x1={x0 + 0.5 + k * cell} y1={y0} x2={x0 + 0.5 + k * cell} y2={y1} stroke={GREY_LINE} strokeWidth={1} />)}
          {Array.from({length: ROWS + 1}, (_, k) => <line key={`h${k}`} x1={x0} y1={y0 + 0.5 + k * cell} x2={x1} y2={y0 + 0.5 + k * cell} stroke={GREY_LINE} strokeWidth={1} />)}
          <rect x={x0 + 0.5} y={y0 + 0.5} width={x1 - x0} height={y1 - y0} fill="none" stroke={GREY_MID} strokeWidth={1.5} />
        </g>
      </Svg>

      <Svg>
        {/* 灰点：rnd 顺序 1 帧错峰亮起（10 帧缩放） */}
        {VSPACE_POINTS.map((p, i) => {
          const s = scaleIn(N - (B_PTS + p.order), 10);
          if (s <= 0) return null;
          const paired = VSPACE_PAIRS.some(([a, b]) => a === i || b === i) && N >= B_PAIRS;
          return <circle key={i} cx={p.x} cy={p.y} r={VSPACE.r * s} fill={paired ? GREY_LIGHT : GREY} opacity={0.9} />;
        })}
        {/* 三对相近点的细灰线（2902 起 3 帧错峰 draw-on） */}
        {VSPACE_PAIRS.map(([a, b], k) => {
          const p = easeOutCubic((N - (B_PAIRS + k * 3)) / 10);
          if (p <= 0) return null;
          const P = VSPACE_POINTS[a], Q = VSPACE_POINTS[b];
          return <line key={k} x1={P.x} y1={P.y} x2={P.x + (Q.x - P.x) * p} y2={P.y + (Q.y - P.y) * p} stroke={GREY_LIGHT} strokeWidth={1.5} strokeDasharray="4 4" opacity={0.85} />;
        })}
        {/* 远点（灰） */}
        {sFar > 0 ? <circle cx={FAR.x} cy={FAR.y} r={7 * sFar} fill={GREY} stroke={GREY_LIGHT} strokeWidth={1.5} opacity={farOp} /> : null}
        {/* 邻居连线 + 高亮圈 */}
        {pLine > 0 ? <line x1={A.x} y1={A.y} x2={A.x + (B.x - A.x) * pLine} y2={A.y + (B.y - A.y) * pLine} stroke={PURPLE_LIGHT} strokeWidth={3} strokeLinecap="round" /> : null}
        {pRing > 0 ? (
          <circle cx={RING.cx} cy={RING.cy} r={RING.r} fill="none" stroke={PURPLE_LIGHT} strokeWidth={2} strokeDasharray={`${RING_LEN}`} strokeDashoffset={RING_LEN * (1 - clamp01(pRing))} transform={`rotate(-90 ${RING.cx} ${RING.cy})`} opacity={0.95} />
        ) : null}
        {/* 两个紫点（白边 + 紫柔光） */}
        <g style={{filter: 'drop-shadow(0 0 6px rgba(102,45,248,.95))'}}>
          {sA > 0 ? <circle cx={A.x} cy={A.y} r={8 * sA} fill={PURPLE} stroke={WHITE} strokeWidth={2} /> : null}
          {sB > 0 ? <circle cx={B.x} cy={B.y} r={8 * sB} fill={PURPLE} stroke={WHITE} strokeWidth={2} /> : null}
        </g>
      </Svg>

      {/* 标签 */}
      <SoftIn N={N} f0={B_AB + 6}>
        <Pill x={LABEL_A.x} y={LABEL_A.y} w={LABEL_A.w} h={LABEL_A.h} text={A.label} fontSize={26} weight={700} textDy={-2} />
      </SoftIn>
      <SoftIn N={N} f0={B_AB + 12}>
        <Pill x={LABEL_B.x} y={LABEL_B.y} w={LABEL_B.w} h={LABEL_B.h} text={B.label} fontSize={26} weight={700} textDy={-2} />
      </SoftIn>
      <SoftIn N={N} f0={B_FAR + 4} style={{opacity: farOp}}>
        <Pill x={LABEL_FAR.x} y={LABEL_FAR.y} w={LABEL_FAR.w} h={LABEL_FAR.h} text={FAR.label} fontSize={24} weight={600} color={GREY_LIGHT} stroke={GREY} textDy={-2} />
      </SoftIn>
      <SoftIn N={N} f0={B_NEAR + 14}>
        <Pill x={LABEL_NEAR.x} y={LABEL_NEAR.y} w={LABEL_NEAR.w} h={LABEL_NEAR.h} text="邻居" fontSize={24} weight={700} fill={PURPLE} sw={2} textDy={-2} glow="0 0 14px 4px rgba(102,45,248,.5)" />
      </SoftIn>

      {/* 角注：二维投影示意（真实向量几百到几千维） */}
      <CText cx={x1 - 70} cy={y1 + 13} size={24} weight={500} color={GREY} opacity={fadeIn(N - (B_GRID + 16), 10)}>2D 投影示意</CText>
    </div>
  );
};
