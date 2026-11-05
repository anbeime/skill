import React from 'react';
import {useCurrentFrame} from 'remotion';
import {FONT_HEAVY, powOutRemain, clamp01} from '../../common';
import {Svg, Cross, CText, Pill, DocIcon, GREY_LIGHT, WHITE, ORANGE, fadeIn, scaleIn, abs, SoftIn} from '../../ui';
import {Scene1Frame, LabelTab, BOXES, LLM, pastOpacity} from './layout';
import {Box1Content} from './SC02';

/**
 * SC03 短板② 私有数据（303–445）。节拍：311 第二 / 320 内网文档 / 380 会议纪要。
 * 框② 内一行：311「读不到私有数据」标签 GlitchIn 12 帧（本镜头唯一 glitch，白名单 §8）；DocIcon×2 + 锁 +「内网文档」（326 SoftIn）｜ 「会议纪要」文档（带「昨天」橙标）。
 * 框与 LLM 之间虚线 330 起自框向 LLM 画出；380 会议纪要文档自右滑入 → 402 起 12 帧向左"试图"靠近 LLM → 406 红叉 draw-on 拦住 → 414 回弹 4px。
 */
const F0 = 303;
const B = BOXES[1];
const ROW_Y = B.y + 50; // 390 行中线
const DOC_W = 36, DOC_H = 46;
const DOC_Y = ROW_Y - DOC_H / 2; // 367
const LOCK_X = 834, LOCK_Y = ROW_Y - 15;
const MEET_X = 1016; // 左推 36 回弹 4 后停在 984，不与「内网文档」文字（右缘 ≈958）重叠
const LINE_X1 = B.x - 2; // 718（框左边）
const LINE_X0 = LLM.cx + LLM.size / 2 + 6; // 491（LLM 右边）
const CROSS_X = 604;

/** 简笔锁（白线）：锁体 26×20 r4 + 半圆锁梁 */
const Lock: React.FC<{x: number; y: number; color?: string}> = ({x, y, color = WHITE}) => (
  <svg width={30} height={34} viewBox="0 0 30 34" style={{position: 'absolute', left: x, top: y, overflow: 'visible'}}>
    <path d="M7,15 V10 A8,8 0 0 1 23,10 V15" fill="none" stroke={color} strokeWidth={2.5} strokeLinecap="round" />
    <rect x={2} y={14} width={26} height={19} rx={4} fill="#000" stroke={color} strokeWidth={2.5} />
    <circle cx={15} cy={23} r={2.4} fill={color} />
  </svg>
);

/** 缩放入场包装（以 (cx,cy) 为原点） */
const ScaleAt: React.FC<{cx: number; cy: number; s: number; children: React.ReactNode}> = ({cx, cy, s, children}) => (s <= 0 ? null : <div style={{...abs(0, 0, 1280, 720), transformOrigin: `${cx}px ${cy}px`, transform: s < 1 ? `scale(${s.toFixed(3)})` : undefined, opacity: clamp01(0.15 + 1.4 * s)}}>{children}</div>);

/** 框② 内容 + 虚线/红叉（SC04 复用，随 pastOpacity 变暗） */
export const Box2Content: React.FC<{N: number}> = ({N}) => {
  const op = pastOpacity(1, N);
  // 虚线：330 起 16 帧自框向 LLM 画出
  const lp = clamp01((N - 330) / 16);
  const lineX0 = LINE_X1 - (LINE_X1 - LINE_X0) * lp;
  // 红叉 406 起 12 帧
  const xp = clamp01((N - 406) / 12);
  // 会议纪要：380 滑入 Δ300 → 402 起 12 帧左移 36 → 414 回弹 4
  const nm = N - 380;
  const slide = 300 * powOutRemain(nm, 22, 2.5);
  const push = -36 * Math.pow(clamp01((N - 402) / 12), 2);
  const bounce = 4 * (1 - powOutRemain(N - 414, 6, 2));
  const meetDx = slide + push + bounce;
  const meetOp = fadeIn(nm, 8);
  return (
    <div style={{opacity: op}}>
      <LabelTab N={N} f0={311} i={1} text="读不到私有数据" w={196} glitch />
      {/* 内网文档 ×2（320/322 缩放入场）+ 锁（326 SoftIn 8 帧淡入上浮）+ 文字 */}
      {[0, 1].map((i) => {
        const x = 742 + 44 * i;
        return (
          <ScaleAt key={i} cx={x + DOC_W / 2} cy={ROW_Y} s={scaleIn(N - (320 + 2 * i), 21)}>
            <DocIcon x={x} y={DOC_Y} w={DOC_W} h={DOC_H} lines={4} sw={2} />
          </ScaleAt>
        );
      })}
      <SoftIn N={N} f0={326}>
        <Lock x={LOCK_X} y={LOCK_Y} />
        <CText cx={914} cy={ROW_Y} size={22} weight={600} color={WHITE} dy={-1}>
          内网文档
        </CText>
      </SoftIn>
      <Svg bloom={false}>
        {lp > 0 ? <line x1={LINE_X1} y1={ROW_Y} x2={lineX0} y2={ROW_Y} stroke={GREY_LIGHT} strokeWidth={2} strokeDasharray="8 7" opacity={0.9} /> : null}
        {xp > 0 ? <Cross cx={CROSS_X} cy={ROW_Y} size={40} sw={6} p={xp} /> : null}
      </Svg>
      {/* 会议纪要文档 + 「昨天」橙标（随文档左推/回弹）+ 文字（只随滑入，不随左推） */}
      {nm >= 0 ? (
        <div style={{opacity: meetOp}}>
          <DocIcon x={MEET_X + meetDx} y={DOC_Y} w={DOC_W} h={DOC_H} lines={4} sw={2} accent={ORANGE} />
          <Pill x={MEET_X + meetDx + 14} y={DOC_Y - 14} w={60} h={28} fill={ORANGE} sw={2} text="昨天" fontSize={22} weight={700} family={FONT_HEAVY} textDy={-1} />
          <CText cx={1108 + slide} cy={ROW_Y} size={22} weight={600} color={WHITE} dy={-1}>
            会议纪要
          </CText>
        </div>
      ) : null}
    </div>
  );
};

export const SC03: React.FC = () => {
  const N = useCurrentFrame() + F0;
  return (
    <div style={abs(0, 0, 1280, 720)}>
      <Scene1Frame N={N} />
      <Box1Content N={N} />
      <Box2Content N={N} />
    </div>
  );
};
