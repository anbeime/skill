import React from 'react';
import {useCurrentFrame} from 'remotion';
import {FONT_HEAVY, powOutRemain, clamp01} from '../../common';
import {Svg, LineArrow, CText, Pill, PURPLE, GREY, GREY_MID, WHITE, ORANGE, fadeIn, scaleIn, abs} from '../../ui';
import {Scene1Frame, LabelTab, BOXES, pastOpacity, mixHex} from './layout';

/**
 * SC02 短板① 知识截止（168–302）。节拍：176 第一 / 186 截止日期 / 233 之后发生的事 / 275 一概不知。
 * 框① 内：176「知识截止」标签 GlitchIn 12 帧（本镜头唯一 glitch，白名单 §8）；水平时间轴 x 730→1150（LineArrow draw-on 20 帧），中点 x940 竖直红标「训练截止」自下弹起，
 * 左侧 3 个白事件点随轴尖端经过依次亮起，右侧 3 个灰「?」点 233 起 2 帧错峰缩放出现；
 * 275「一概不知」：LLM 神经元闪灰一次 + 紫柔光熄灭 8 帧再回 + 三个「?」275/278/281 依次白闪放大一次（QC v1：原仅 4 个神经元点变灰，不可察）。
 */
const F0 = 168;
const B = BOXES[0];
const AXIS_Y = B.y + 78; // 278
const X0 = 730, X1 = 1150, CUT_X = 940;
const LEFT_DOTS = [768, 822, 876];
const RIGHT_DOTS = [1000, 1052, 1104];
/** 275 起三个「?」依次白闪：起点 275+3i，10 帧三角脉冲 0→1→0 */
const Q_FLASH_AT = 275;
const qFlash = (N: number, i: number) => {
  const n = N - (Q_FLASH_AT + 3 * i);
  if (n <= 0 || n >= 10) return 0;
  return n < 5 ? n / 5 : 1 - (n - 5) / 5;
};

/** 框① 内容（SC03/SC04 复用，随 pastOpacity 变暗；全部为 N 的纯函数） */
export const Box1Content: React.FC<{N: number}> = ({N}) => {
  const op = pastOpacity(0, N);
  const p = clamp01((N - 186) / 20);
  const tipX = X0 + (X1 - X0) * p;
  const nCut = N - 196; // 轴尖端过中点后红标弹起
  const cutOp = fadeIn(nCut, 6);
  const cutDy = 50 * powOutRemain(nCut, 14, 2.5);
  return (
    <div style={{opacity: op}}>
      <LabelTab N={N} f0={176} i={0} text="知识截止" w={124} glitch />
      <Svg bloom={false}>
        {p > 0 ? <LineArrow x0={X0} y0={AXIS_Y} x1={X1} y1={AXIS_Y} p={p} rodW={3} headL={18} headW={20} /> : null}
        {LEFT_DOTS.map((x, i) => {
          const o = clamp01((tipX - x) / 14);
          if (o <= 0) return null;
          return <circle key={i} cx={x} cy={AXIS_Y} r={7 * (0.4 + 0.6 * o)} fill={WHITE} opacity={o} />;
        })}
        {/* 训练截止：竖直红刻线 */}
        {cutOp > 0 ? <line x1={CUT_X} y1={AXIS_Y - 30 + cutDy * 0.4} x2={CUT_X} y2={AXIS_Y + 12} stroke={ORANGE} strokeWidth={3} opacity={cutOp} /> : null}
        {RIGHT_DOTS.map((x, i) => {
          const s = scaleIn(N - (233 + 2 * i), 10);
          if (s <= 0) return null;
          const q = qFlash(N, i);
          return <circle key={i} cx={x} cy={AXIS_Y} r={14 * s * (1 + 0.3 * q)} fill="#000" stroke={mixHex(GREY, WHITE, q)} strokeWidth={2 + q} opacity={clamp01(0.2 + s)} style={q > 0 ? {filter: `drop-shadow(0 0 ${Math.round(6 * q)}px rgba(255,255,255,${(0.8 * q).toFixed(2)}))`} : undefined} />;
        })}
      </Svg>
      {RIGHT_DOTS.map((x, i) => {
        const s = scaleIn(N - (233 + 2 * i), 10);
        if (s <= 0) return null;
        const q = qFlash(N, i);
        return (
          <CText key={i} cx={x} cy={AXIS_Y} size={22} weight={800} color={mixHex(GREY, WHITE, q)} dy={-1} shadow={q > 0 ? `0 0 8px rgba(255,255,255,${(0.8 * q).toFixed(2)})` : undefined} style={{transform: `translate(-50%,-50%) scale(${(s * (1 + 0.3 * q)).toFixed(3)})`}}>
            ?
          </CText>
        );
      })}
      {cutOp > 0 ? (
        <div style={{opacity: cutOp}}>
          <Pill x={CUT_X - 56} y={AXIS_Y - 62 + cutDy} w={112} h={30} fill={ORANGE} sw={2} text="训练截止" fontSize={22} weight={700} family={FONT_HEAVY} textDy={-1} />
        </div>
      ) : null}
    </div>
  );
};

/** 275 神经元闪灰：紫→灰 6 帧、再回紫 6 帧 */
export const llmAccentAt = (N: number, f0: number) => {
  const n = N - f0;
  if (n < 0 || n > 12) return PURPLE;
  const k = n <= 6 ? n / 6 : 1 - (n - 6) / 6;
  return mixHex(PURPLE, GREY_MID, k);
};

/** 275 LLM 紫柔光熄灭：4 帧降到 0.1、保持 4 帧、6 帧回到 1（与神经元闪灰同步，放大「一概不知」的可见面积） */
export const llmHaloAt = (N: number, f0: number) => {
  const n = N - f0;
  if (n < 0 || n > 14) return 1;
  if (n < 4) return 1 - 0.9 * (n / 4);
  if (n < 8) return 0.1;
  return 0.1 + 0.9 * ((n - 8) / 6);
};

export const SC02: React.FC = () => {
  const N = useCurrentFrame() + F0;
  return (
    <div style={abs(0, 0, 1280, 720)}>
      <Scene1Frame N={N} accent={llmAccentAt(N, 275)} haloK={llmHaloAt(N, 275)} />
      <Box1Content N={N} />
    </div>
  );
};
