import React from 'react';
import {useCurrentFrame} from 'remotion';
import {GlitchIn, clamp01, BEZ_SCALE_IN, FONT_TECH, powOutRemain} from '../../common';
import {Box, Pill, ArrowH, TechText, Svg, PURPLE, PURPLE_LIGHT, ORANGE, GREY, WHITE, GLOW_PURPLE_S, fadeIn, fadeOut, exitAccel, SoftIn} from '../../ui';
import {VectorPlane, VNEIGHBORS} from './vspace';
import {bez2, inOut, mixHex, mixK, DrawCircle, DrawLine} from './g5util';

/**
 * SC23 语义检索（4057–4225，S23）。节拍：4065 第二步检索 / 4093 问题变向量 / 4137 找最近的邻居 / 4192 语义检索。
 * 坐标平面与 G4 SC17 同一分布（vspace.tsx VSPACE/VGREY）。主区 y 190–600。
 * QC v1：橙查询点/涟漪改画在 Embedding 盒之上的独立 Svg 层（原在 VectorPlane 内被盒子盖住，4093–4099 无可见变化）。
 */
export const F0 = 4057;
const T_PLANE = 4057, T_PTS = 4059, T_PILL = 4065, T_ARROW = 4079, T_EMB = 4085, T_FLY = 4093, T_CIRCLE = 4137, T_LABEL = 4192, T_EXIT = 4214;
const Q: [number, number] = [620, 390];
const EMB = {x: 544, y: 203, w: 132, h: 48};
const LABELS: Array<{text: string; cx: number; cy: number; w: number}> = [
  {text: '报销标准 §3', cx: 486, cy: 300, w: 152},
  {text: '住宿上限', cx: 792, cy: 430, w: 118},
  {text: '交通补贴', cx: 508, cy: 500, w: 118},
];

export const SC23: React.FC = () => {
  const N = useCurrentFrame() + F0;
  const ne = N - T_EXIT;
  const op = ne > 0 ? fadeOut(ne, 12) : 1;
  const dy = ne > 0 ? exitAccel(ne, 0.6) : 0;
  if (op <= 0) return null;
  // 问句 Pill 自左滑入
  const pillDx = -340 * powOutRemain(N - T_PILL, 22, 2.5);
  const pillOp = fadeIn(N - T_PILL, 6);
  const pArrow = clamp01((N - T_ARROW) / 12);
  // 橙点飞行：盒中心 → 弧线 → Q
  const nf = N - T_FLY;
  const tFly = inOut(clamp01(nf / 18));
  const src: [number, number] = [EMB.x + EMB.w / 2, EMB.y + EMB.h / 2];
  const [qx, qy] = bez2(src, [760, 250], Q, tFly);
  const dotS = nf < 0 ? 0 : BEZ_SCALE_IN(clamp01(nf / 8));
  const landed = nf >= 18;
  const ripple = clamp01((nf - 18) / 14);
  // 近邻圈 + 三点变紫
  const pCircle = clamp01((N - T_CIRCLE) / 14);
  return (
    <div style={{position: 'absolute', inset: 0, opacity: op, transform: dy ? `translateY(${dy.toFixed(1)}px)` : undefined}}>
      <VectorPlane N={N} f0={T_PLANE} ptsFrom={T_PTS} extra={VNEIGHBORS}>
        {/* 近邻圈（紫，draw-on 14 帧） */}
        <DrawCircle cx={Q[0]} cy={Q[1]} r={90} p={pCircle} w={2} color={PURPLE_LIGHT} />
        {/* 三近邻点：变紫 + 放大，各隔 6 帧 */}
        {VNEIGHBORS.map(([x, y], i) => {
          const k = mixK(N - (T_CIRCLE + 4 + i * 6));
          const r = 4.2 + 3 * k;
          return <circle key={i} cx={x} cy={y} r={r} fill={mixHex('#D4D4D4', PURPLE, k)} style={k > 0.5 ? {filter: 'drop-shadow(0 0 5px rgba(161,117,241,.9))'} : undefined} />;
        })}
        {/* 标签牵引线 */}
        {LABELS.map((l, i) => {
          const [x, y] = VNEIGHBORS[i];
          const p = clamp01((N - (T_CIRCLE + 8 + i * 6)) / 8);
          return <DrawLine key={i} x0={x} y0={y} x1={l.cx + (x > l.cx ? l.w / 2 - 8 : -l.w / 2 + 8)} y1={l.cy + (y > l.cy ? 14 : -14)} p={p} w={1.5} color={GREY} />;
        })}
      </VectorPlane>

      {/* 左上：问句 Pill → 箭头 → Embedding 盒 */}
      {pillOp > 0 ? (
        <div style={{position: 'absolute', left: pillDx, top: 0, width: 1280, height: 720, opacity: pillOp}}>
          <Pill x={262} y={205} w={226} h={44} fill="#000" sw={2} text="差旅报销上限？" fontSize={24} weight={700} textDy={-2} />
        </div>
      ) : null}
      <ArrowH x={496} y={217} w={44} h={20} p={pArrow} shaft={2.5} />
      <SoftIn N={N} f0={T_EMB}>
        <Box x={EMB.x} y={EMB.y} w={EMB.w} h={EMB.h} r={8} fill={PURPLE} sw={2} glow={GLOW_PURPLE_S} />
        <div style={{position: 'absolute', left: EMB.x, top: EMB.y, width: EMB.w, height: EMB.h, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: FONT_TECH, fontStyle: 'italic', fontWeight: 700, fontSize: 24, color: WHITE, letterSpacing: 0.5, transform: 'scaleX(0.86)'}}>Embedding</div>
      </SoftIn>
      {/* 查询点（橙）+ 落点涟漪：在盒子之上，4093 起自盒中心可见地长出并起飞 */}
      {dotS > 0 ? (
        <Svg bloom={false}>
          {landed && ripple < 1 ? <circle cx={Q[0]} cy={Q[1]} r={8 + 40 * ripple} fill="none" stroke={ORANGE} strokeWidth={2} opacity={1 - ripple} /> : null}
          <circle cx={qx} cy={qy} r={8 * dotS} fill={ORANGE} style={{filter: 'drop-shadow(0 0 6px rgba(240,95,65,.9))'}} />
        </Svg>
      ) : null}

      {/* 三近邻标签 */}
      {LABELS.map((l, i) => (
        <SoftIn key={i} N={N} f0={T_CIRCLE + 12 + i * 6}>
          <Pill x={l.cx - l.w / 2} y={l.cy - 15} w={l.w} h={30} fill="#000" sw={1.5} text={l.text} fontSize={20} weight={600} textDy={-1} />
        </SoftIn>
      ))}

      {/* 右上：语义检索 —— 本镜头唯一 glitch（白名单 §8）；英文副标用 SoftIn */}
      <GlitchIn N={N} f0={T_LABEL} seed={51}>
        <Pill x={820} y={205} w={160} h={44} fill={PURPLE} sw={2} text="语义检索" fontSize={26} weight={700} textDy={-2} glow={GLOW_PURPLE_S} />
      </GlitchIn>
      <SoftIn N={N} f0={T_LABEL}>
        <TechText cx={900} cy={269} text="Dense Retrieval" fontSize={24} scaleX={0.84} weight={700} />
      </SoftIn>
    </div>
  );
};
