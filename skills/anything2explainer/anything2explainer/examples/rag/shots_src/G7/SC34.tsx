import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {slideIn, clamp01, easeOutCubic, FONT_HEAVY} from '../../common';
import {Svg, Cross, Box, Pill, CText, PURPLE, PURPLE_LIGHT, CORAL, RED_DEEP, GREEN, GREY, WHITE, slideUp, fadeIn, fadeOut, scaleIn, SoftIn} from '../../ui';
import {Balance} from './g7ui';

/**
 * SC34 忠实度 > 流畅度（6213–6406）
 * 6219 答复卡自下滑入，6223 起三行打字机（1.2 帧/字）；6255 绿标「流畅」SoftIn 淡入（闪烁整改：SC34 不在白名单）；6268 来源卡滑入，6278 引线 draw-on；
 * 6286 红叉划断引线 + 6290「证据错误」红标 SoftIn 淡入；6323 天平缩放入场，6344 梁向「忠实度」倾斜 12°（easeOutCubic 21 帧）+ 忠实度盘紫亮；
 * 6395 起 12 帧线性淡出（SC35 6413 才出字，留 6 帧空场）。
 */
const F0 = 6213;
const T_CARD = 6219, T_TYPE = 6223, T_FLUENT = 6255, T_SRC = 6268, T_LINE = 6278, T_CROSS = 6286, T_TAG = 6290;
const T_BAL = 6323, T_TILT = 6344, T_GLOW = 6352, T_EXIT = 6395;

const ANS = {x: 190, y: 232, w: 400, h: 158};
const SRC = {x: 220, y: 470, w: 340, h: 92};
type Seg = {t: string; c?: string};
/** 答复三行（全片统一「差旅报销」语境，见分镜表全局约束 2） */
const LINES: Seg[][] = [
  [{t: '住宿上限每天 600 元'}, {t: '[1]', c: PURPLE_LIGHT}, {t: '，'}],
  [{t: '一线城市 800 元'}, {t: '[2]', c: PURPLE_LIGHT}, {t: '。'}],
  [{t: '超出部分请先向部门审批。'}],
];
const lineLen = (l: Seg[]) => l.reduce((a, s) => a + s.t.length, 0);

/** 打字机：按可见字数截断分段 */
const Typed: React.FC<{segs: Seg[]; count: number; x: number; y: number}> = ({segs, count, x, y}) => {
  let used = 0;
  return (
    <div style={{position: 'absolute', left: x, top: y, fontFamily: FONT_HEAVY, fontSize: 24, fontWeight: 500, lineHeight: 1, whiteSpace: 'nowrap', color: WHITE}}>
      {segs.map((s, i) => {
        const avail = Math.max(0, count - used);
        const txt = s.t.slice(0, avail);
        used += s.t.length;
        return txt ? (
          <span key={i} style={{color: s.c ?? WHITE}}>
            {txt}
          </span>
        ) : null;
      })}
    </div>
  );
};

export const SC34: React.FC = () => {
  const N = useCurrentFrame() + F0;
  const op = fadeOut(N - T_EXIT, 12);
  // 答复卡
  const nc = N - T_CARD;
  const cardDy = slideUp(nc, 300), cardOp = fadeIn(nc, 8);
  const typedTotal = Math.floor(Math.max(0, N - T_TYPE) / 1.2);
  const offsets = [0, lineLen(LINES[0]), lineLen(LINES[0]) + lineLen(LINES[1])];
  // 来源卡
  const ns = N - T_SRC;
  const srcDy = slideUp(ns, 80, 18), srcOp = fadeIn(ns, 8);
  const lineP = slideIn(N - T_LINE, 12, 2);
  const crossP = slideIn(N - T_CROSS, 10, 2);
  // 天平
  const nb = N - T_BAL;
  const theta = (12 * Math.PI / 180) * easeOutCubic(clamp01((N - T_TILT) / 21));
  const glow = clamp01((N - T_GLOW) / 11);
  return (
    <AbsoluteFill style={{pointerEvents: 'none', opacity: op}}>
      {/* 答复卡 */}
      {nc >= 0 ? (
        <div style={{position: 'absolute', inset: 0, transform: `translateY(${cardDy.toFixed(2)}px)`, opacity: cardOp}}>
          <Box x={ANS.x} y={ANS.y} w={ANS.w} h={ANS.h} r={12} sw={2} style={{filter: 'drop-shadow(0 0 3px rgba(255,255,255,.35))'}} />
          <Pill x={ANS.x + 10} y={ANS.y - 16} w={78} h={30} fill={PURPLE} sw={2} text="回答" fontSize={20} weight={700} textDy={-2} />
          {LINES.map((l, i) => (
            <Typed key={i} segs={l} count={typedTotal - offsets[i]} x={ANS.x + 24} y={ANS.y + 30 + i * 40} />
          ))}
        </div>
      ) : null}
      <SoftIn N={N} f0={T_FLUENT}>
        <Pill x={ANS.x + ANS.w - 92} y={ANS.y - 16} w={82} h={30} fill="#000" stroke={GREEN} sw={2} text="流畅" fontSize={20} weight={700} color={GREEN} textDy={-2} glow="0 0 14px 2px rgba(143,247,64,.35)" />
      </SoftIn>
      {/* 来源卡 */}
      {ns >= 0 ? (
        <div style={{position: 'absolute', inset: 0, transform: `translateY(${srcDy.toFixed(2)}px)`, opacity: srcOp}}>
          <Box x={SRC.x} y={SRC.y} w={SRC.w} h={SRC.h} r={10} sw={2} stroke={GREY} />
          <div style={{position: 'absolute', left: SRC.x + 16, top: SRC.y + 12, fontFamily: FONT_HEAVY, fontSize: 20, fontWeight: 600, color: PURPLE_LIGHT, lineHeight: 1, whiteSpace: 'nowrap'}}>来源 [1] · 员工手册 p.12</div>
          <div style={{position: 'absolute', left: SRC.x + 16, top: SRC.y + 46, fontFamily: FONT_HEAVY, fontSize: 24, fontWeight: 600, color: WHITE, lineHeight: 1, whiteSpace: 'nowrap'}}>
            住宿标准：每天 <span style={{color: CORAL}}>500</span> 元
          </div>
        </div>
      ) : null}
      {/* 引线 + 红叉 */}
      {lineP > 0 ? (
        <Svg>
          <line x1={ANS.x + ANS.w / 2} y1={ANS.y + ANS.h} x2={ANS.x + ANS.w / 2} y2={ANS.y + ANS.h + 80 * lineP} stroke={WHITE} strokeWidth={2.5} strokeDasharray="6 5" opacity={0.9} />
          {crossP > 0 ? <Cross cx={ANS.x + ANS.w / 2} cy={ANS.y + ANS.h + 40} size={30} color={CORAL} sw={6} p={crossP} /> : null}
        </Svg>
      ) : null}
      <SoftIn N={N} f0={T_TAG}>
        <Pill x={ANS.x + ANS.w / 2 + 24} y={ANS.y + ANS.h + 23} w={130} h={34} fill={RED_DEEP} sw={2} text="证据错误" fontSize={22} weight={700} textDy={-2} glow="0 0 24px 6px rgba(236,8,31,.42)" />
      </SoftIn>
      {/* 天平 */}
      {nb >= 0 ? <Balance cx={900} py={300} theta={theta} labels={['忠实度', '流畅度']} leftGlow={glow} s={scaleIn(nb)} opacity={fadeIn(nb, 8)} /> : null}
      {/* 「>」 关系提示 */}
      {N >= T_TILT + 14 ? (
        <CText cx={900} cy={588} size={26} weight={700} color={WHITE} opacity={fadeIn(N - (T_TILT + 14), 10)} dy={-1} shadow="0 0 8px rgba(255,255,255,.35)">
          忠实度 <span style={{color: PURPLE_LIGHT}}>&gt;</span> 流畅度
        </CText>
      ) : null}
    </AbsoluteFill>
  );
};
