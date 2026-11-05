import React from 'react';
import {useCurrentFrame} from 'remotion';
import {clamp01} from '../../common';
import {Box, Pill, DBIcon, Svg, LineArrow, CText, TechText, PURPLE, GREY, GREY_LIGHT, WHITE, slideUp, scaleIn, fadeIn, fadeOut, exitAccel, SoftIn} from '../../ui';
import {Anchor, DrawLine, mixHex, mixK} from './g5util';

/**
 * SC22 理解问题（3822–4056，S22）。节拍：3830 第一步理解问题 / 3865 原话含糊 / 3909 先改写 / 3948 拆成子问题 / 3982 假想一个答案 / 4026 拿它去检索。
 * 流程轨 y112–160 由 G0 绘制，本镜头主区 y 190–620。
 */
export const F0 = 3822;
const T_BUBBLE = 3824, T_VAGUE = 3865, T_C = [3909, 3948, 3982], T_MERGE = 4026, T_EXIT = 4045;
const CARD_X = 424, CARD_W = 376, CARD_H = 90, CY = [258, 400, 542];
const BUBBLE = {x: 130, y: 366, w: 220, h: 68};

const Card: React.FC<{i: number}> = ({i}) => {
  const x = CARD_X, y = CY[i] - CARD_H / 2;
  const hyde = i === 2;
  const tag = ['改写', '拆分', '假想答案'][i];
  const tagW = hyde ? 108 : 76;
  const tech = ['Query Rewriting', 'Multi-Query', 'HyDE'][i];
  return (
    <>
      <Box x={x} y={y} w={CARD_W} h={CARD_H} r={12} sw={2} fill={hyde ? '#1C1C1C' : '#000'} stroke={hyde ? GREY : WHITE} />
      <Pill x={x + 12} y={y + 12} w={tagW} h={28} fill={PURPLE} sw={1.5} text={tag} fontSize={19} weight={700} textDy={-1} />
      {i === 0 ? <CText cx={x + 118 + 132} cy={y + 34} size={24} weight={600} color={WHITE} dy={-1}>差旅费报销标准与上限</CText> : null}
      {i === 1 ? (
        <>
          <Pill x={x + 104} y={y + 12} w={124} h={30} fill="#000" sw={1.5} text="住宿上限？" fontSize={20} weight={600} textDy={-1} />
          <Pill x={x + 238} y={y + 12} w={124} h={30} fill="#000" sw={1.5} text="交通上限？" fontSize={20} weight={600} textDy={-1} />
        </>
      ) : null}
      {i === 2 ? <CText cx={x + 130 + 118} cy={y + 30} size={22} weight={500} color={GREY_LIGHT} italic dy={-1}>差旅住宿每天不超过…</CText> : null}
      <TechText cx={x + CARD_W - 14 - (tech.length * 11.6 * 0.81) / 2} cy={y + CARD_H - 19} text={tech} fontSize={24} scaleX={0.81} weight={700} />
    </>
  );
};

export const SC22: React.FC = () => {
  const N = useCurrentFrame() + F0;
  // 离场（4045 起 12 帧）
  const ne = N - T_EXIT;
  const op = ne > 0 ? fadeOut(ne, 12) : 1;
  const dy = ne > 0 ? exitAccel(ne, 0.6) : 0;
  if (op <= 0) return null;
  // 气泡
  const bDy = slideUp(N - T_BUBBLE, 300);
  const bOp = fadeIn(N - T_BUBBLE, 8);
  // 闪烁整改：原 3865 起 14 帧 rnd 白/灰闪边闪字 → 11 帧白→灰平滑变色（mixK），节拍不变
  const nv = N - T_VAGUE;
  const kv = mixK(nv);
  const stroke = mixHex(WHITE, GREY, kv);
  const textCol = mixHex(WHITE, GREY_LIGHT, kv);
  // 汇合
  const pLines = clamp01((N - (T_MERGE - 6)) / 12);
  const pArrow = clamp01((N - (T_MERGE + 2)) / 14);
  const sDb = scaleIn(N - T_MERGE);
  return (
    <div style={{position: 'absolute', inset: 0, opacity: op, transform: dy ? `translateY(${dy.toFixed(1)}px)` : undefined}}>
      {/* 用户问句气泡（含糊 → 灰边） */}
      {bOp > 0 ? (
        <div style={{position: 'absolute', left: 0, top: bDy, width: 1280, height: 720, opacity: bOp}}>
          <Box x={BUBBLE.x} y={BUBBLE.y} w={BUBBLE.w} h={BUBBLE.h} r={22} sw={2} stroke={stroke} />
          <svg width={40} height={30} viewBox="0 0 40 30" style={{position: 'absolute', left: BUBBLE.x + 26, top: BUBBLE.y + BUBBLE.h - 3, overflow: 'visible'}}>
            <path d="M2 0 L22 0 L6 20 Z" fill="#000" stroke={stroke} strokeWidth={2} strokeLinejoin="round" />
            <line x1={3} y1={0} x2={21} y2={0} stroke="#000" strokeWidth={3} />
          </svg>
          <CText cx={BUBBLE.x + BUBBLE.w / 2} cy={BUBBLE.y + BUBBLE.h / 2} size={28} weight={700} color={textCol} dy={-2}>报销上限？</CText>
        </div>
      ) : null}
      <SoftIn N={N} f0={T_VAGUE}>
        <CText cx={BUBBLE.x + BUBBLE.w / 2 + 14} cy={BUBBLE.y + BUBBLE.h + 40} size={22} weight={500} color={GREY} dy={-1}>原话含糊</CText>
      </SoftIn>

      {/* 三条分支箭头 + 汇合线 */}
      <Svg>
        {CY.map((cy, i) => <LineArrow key={i} x0={BUBBLE.x + BUBBLE.w + 4} y0={400} x1={CARD_X - 6} y1={cy} p={clamp01((N - (T_C[i] - 6)) / 14)} rodW={2.5} headL={16} headW={16} />)}
        {CY.map((cy, i) => <DrawLine key={`m${i}`} x0={CARD_X + CARD_W + 4} y0={cy} x1={900} y1={400 + (i - 1) * 1.5} p={pLines} w={2.5} />)}
        {pLines >= 1 ? <circle cx={900} cy={400} r={5.5} fill={WHITE} /> : null}
        <LineArrow x0={903} y0={400} x1={1030} y1={400} p={pArrow} rodW={3} headL={22} headW={24} />
      </Svg>

      {/* 三张改写卡（闪烁整改：GlitchIn → SoftIn，f0 不变） */}
      {CY.map((_, i) => (
        <SoftIn key={i} N={N} f0={T_C[i]}>
          <Card i={i} />
        </SoftIn>
      ))}

      {/* 右缘 DBIcon */}
      {sDb > 0 ? (
        <Anchor cx={1092} cy={400} s={sDb} opacity={fadeIn(N - T_MERGE, 6)}>
          <DBIcon cx={1092} cy={392} w={104} h={116} accent={PURPLE} label="知识库" labelSize={24} />
        </Anchor>
      ) : null}
    </div>
  );
};
