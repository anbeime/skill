import React from 'react';
import {useCurrentFrame} from 'remotion';
import {FONT_HEAVY, GlitchIn, powOutRemain, clamp01} from '../../common';
import {Svg, Cross, Box, Pill, TagBlock, GREY, WHITE, ORANGE, CORAL, RED_DEEP, fadeIn, exitFade, abs, SoftIn} from '../../ui';
import {Scene1Frame, BOXES, mixHex} from './layout';
import {Box1Content} from './SC02';
import {Box2Content} from './SC03';

/**
 * SC04 短板③ 幻觉（446–612）。节拍：454 第三 / 463 不知道的问题 / 499 不会说不知道 / 534 一脸自信地编 / 588 幻觉。
 * 框③ 内聊天式两行：左上问句气泡「差旅报销的上限是多少？」（全局约束 #2 差旅语境）；右下先 SoftIn 淡入灰胶囊「我不知道」被红叉划掉，
 * 534 起答复气泡打字机逐字「每天 1000 元，全国统一」（数字橙、无来源）；588 框右上角 RED_DEEP「幻觉」TagBlock GlitchIn 12 帧（本镜头唯一 glitch，白名单 §8；纯透明度，不带 slices）+ 答复气泡边框变红 8 帧。
 * 末 2 帧（611–612）整组 exitFade，SC05 硬切。
 */
const F0 = 446;
const B = BOXES[2];
const Q_TEXT = '差旅报销的上限是多少？';
const A_TEXT = '每天 1000 元，全国统一';
const A_CHARS = Array.from(A_TEXT);
const Q = {x: 736, y: 490, w: 262, h: 40};
const A = {x: 878, y: 536, w: 268, h: 40};
const DK = {x: 1016, y: 536, w: 130, h: 40}; // 「我不知道」灰胶囊（与答复同位，右对齐）
const TYPE_AT = 534, TYPE_STEP = 2;

/** 聊天气泡：黑底白边圆角（tail 侧小圆角） */
const Bubble: React.FC<{x: number; y: number; w: number; h: number; side: 'left' | 'right'; stroke?: string; glow?: string; opacity?: number; children: React.ReactNode}> = ({x, y, w, h, side, stroke = WHITE, glow, opacity = 1, children}) => (
  <Box x={x} y={y} w={w} h={h} fill="#000" stroke={stroke} sw={2} opacity={opacity} glow={glow} style={{borderRadius: side === 'left' ? '14px 14px 14px 4px' : '14px 14px 4px 14px'}}>
    <div style={{position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', paddingLeft: 14, paddingRight: 14, fontFamily: FONT_HEAVY, fontSize: 22, fontWeight: 600, color: WHITE, lineHeight: 1, whiteSpace: 'nowrap', transform: 'translateY(-1.5px)'}}>{children}</div>
  </Box>
);

export const Box3Content: React.FC<{N: number}> = ({N}) => {
  // 463 问句气泡自左弹入 Δ220
  const nq = N - 463;
  const qdx = -220 * powOutRemain(nq, 22, 2.5);
  // 499 灰胶囊 SoftIn → 505 红叉 12 帧 → 526 起 8 帧淡出
  const dkOp = 1 - clamp01((N - 526) / 8);
  const xp = clamp01((N - 505) / 12);
  // 534 答复气泡 + 打字机
  const na = N - TYPE_AT;
  const count = na < 0 ? 0 : Math.min(A_CHARS.length, Math.floor(na / TYPE_STEP) + 1);
  const typing = na >= 0 && count < A_CHARS.length;
  const caretOn = typing && N % 8 < 5;
  const aIn = 1 - powOutRemain(na, 10, 2.5);
  // 588 边框变红 8 帧
  const red = clamp01((N - 588) / 8);
  const aStroke = mixHex(WHITE, CORAL, red);
  const aGlow = red > 0 ? `0 0 22px 6px rgba(241,96,67,${(0.5 * red).toFixed(2)})` : undefined;
  return (
    <div>
      {nq >= 0 ? (
        <div style={{opacity: fadeIn(nq, 8)}}>
          <Bubble x={Q.x + qdx} y={Q.y} w={Q.w} h={Q.h} side="left">
            {Q_TEXT}
          </Bubble>
        </div>
      ) : null}
      {dkOp > 0 ? (
        <SoftIn N={N} f0={499} style={{opacity: dkOp}}>
          <Pill x={DK.x} y={DK.y} w={DK.w} h={DK.h} fill="#000" stroke={GREY} sw={2} text="我不知道" fontSize={22} weight={600} color={GREY} family={FONT_HEAVY} textDy={-1} />
          <Svg bloom={false}>{xp > 0 ? <Cross cx={DK.x + DK.w / 2} cy={DK.y + DK.h / 2} size={34} sw={6} p={xp} /> : null}</Svg>
        </SoftIn>
      ) : null}
      {na >= 0 ? (
        <div style={{...abs(0, 0, 1280, 720), transformOrigin: `${A.x + A.w}px ${A.y + A.h}px`, transform: aIn < 1 ? `scale(${(0.6 + 0.4 * aIn).toFixed(3)})` : undefined, opacity: fadeIn(na, 5)}}>
          <Bubble x={A.x} y={A.y} w={A.w} h={A.h} side="right" stroke={aStroke} glow={aGlow}>
            {A_CHARS.slice(0, count).map((ch, i) => (
              <span key={i} style={/[0-9]/.test(ch) ? {color: ORANGE, fontWeight: 800} : undefined}>
                {ch}
              </span>
            ))}
            {typing ? <span style={{display: 'inline-block', width: 3, height: 22, marginLeft: 3, background: WHITE, opacity: caretOn ? 1 : 0}} /> : null}
          </Bubble>
        </div>
      ) : null}
      {/* 588 「幻觉」标签：框右上角（白名单 glitch；slices 仅片头/SC08/SC35/SC44 可用，已去掉） */}
      <GlitchIn N={N} f0={588}>
        <TagBlock x={1040} y={B.y - 20} w={110} h={40} color={RED_DEEP} text="幻觉" fontSize={28} />
      </GlitchIn>
    </div>
  );
};

export const SC04: React.FC = () => {
  const N = useCurrentFrame() + F0;
  return (
    <div style={{...abs(0, 0, 1280, 720), opacity: exitFade(N - 610)}}>
      <Scene1Frame N={N} />
      <Box1Content N={N} />
      <Box2Content N={N} />
      <Box3Content N={N} />
    </div>
  );
};
