import React from 'react';
import {useCurrentFrame} from 'remotion';
import {GlitchIn, easeInOutPow, emphasisPulse, clamp01, rnd, FONT_HEAVY} from '../../common';
import {CText, TechText, Box, Pill, Svg, fadeIn, slideUp, scaleIn, PURPLE, PURPLE_DEEP, PURPLE_LIGHT, CORAL, GREY, GREY_LIGHT, GREY_LINE, WHITE, abs, SoftIn} from '../../ui';
import {mixHex} from './ui';

/**
 * SC28 组装上下文 · Lost in the Middle（5018–5313）
 * 节拍：5026 第四步组装上下文 / 5060 研究发现 / 5077 中间记得最差 / 5154 Lost in the Middle / 5244 放开头和结尾
 * 画面：左 竖长「上下文」条（8 段证据，2 段紫色关键证据在中间）；右 曲线卡（证据位置 1→20 × 准确率，U 形紫曲线，中点红点「中间最差」）；
 *      5077 曲线按 x 揭示 + 中段变暗；5154 标题「Lost in the Middle」+「Liu et al., TACL 2024」；5244 两段紫色证据移到条的两端并脉冲。
 */
const F0 = 5018;
const B_CTX = 5026, B_CARD = 5060, B_CURVE = 5077, B_TITLE = 5154, B_MOVE = 5244;
const T_CTX_IN = B_CTX - 4;
const easeMove = easeInOutPow(2.5);

// 上下文条
const BAR = {x: 220, y: 200, w: 160, h: 400};
const SEG_X = 236, SEG_W = 128, SEG_H = 36, SEG_GAP = 8, SEG_Y0 = 230;
const slotY = (p: number) => SEG_Y0 + p * (SEG_H + SEG_GAP);
const PURPLE_IDS = [3, 4];

// 曲线卡
const CARD = {x: 640, y: 235, w: 440, h: 300};
const PX0 = 700, PX1 = 1050, PY0 = 265, PY1 = 470;
const xFor = (p: number) => PX0 + ((p - 1) / 19) * (PX1 - PX0);
const yFor = (p: number) => {
  const norm = Math.pow((p - 10.5) / 9.5, 2);
  const v = 0.08 + 0.92 * norm * (p < 10.5 ? 1 : 0.88); // 首因略高于近因（Liu et al. U 形）
  return PY1 - 15 - v * (PY1 - PY0 - 35);
};
const CURVE_PTS: Array<[number, number]> = Array.from({length: 77}, (_, i) => {
  const p = 1 + i * 0.25;
  return [xFor(p), yFor(p)];
});
const X_TICKS = [1, 5, 10, 15, 20];

export const SC28: React.FC = () => {
  const N = useCurrentFrame() + F0;
  const opAll = N >= 5308 ? Math.max(0, 1 - (N - 5307) / 7) : 1;

  // ---- 上下文条 ----
  const nc = N - T_CTX_IN;
  const ctxDy = slideUp(nc, 40); // 条高 400，用小位移上浮 + 淡入，避免穿过字幕带
  const ctxOp = fadeIn(nc, 10);
  const dimK = clamp01((N - B_CURVE) / 12);
  const mv = easeMove(clamp01((N - B_MOVE) / 18));
  const nPulse = N - (B_MOVE + 18);
  const pulse = emphasisPulse(nPulse, {peak: 1.08, up: 10, hold: 3, down: 12});
  const glowK = nPulse < 0 ? 0 : nPulse < 10 ? nPulse / 10 : Math.max(0.4, 1 - (nPulse - 10) / 25);
  const slotOf = (id: number) => (id === 3 ? 3 - 3 * mv : id === 4 ? 4 + 3 * mv : id < 3 ? id + mv : id - mv);

  // ---- 曲线卡 ----
  const ncd = N - B_CARD;
  const cardS = scaleIn(ncd);
  const cardOp = fadeIn(ncd, 6);
  const wipe = clamp01((N - B_CURVE) / 24);
  const dotS = scaleIn(N - (B_CURVE + 12), 8);

  return (
    <div style={{position: 'absolute', inset: 0, opacity: opAll}}>
      {/* ===== 左：上下文条 ===== */}
      {nc >= 0 ? (
        <div style={{position: 'absolute', inset: 0, transform: `translateY(${ctxDy.toFixed(2)}px)`, opacity: ctxOp}}>
          <Box x={BAR.x} y={BAR.y} w={BAR.w} h={BAR.h} r={10} sw={2} />
          {Array.from({length: 8}, (_, id) => {
            const p = slotOf(id);
            const y = slotY(p);
            const isP = PURPLE_IDS.includes(id);
            const mid = 1 - clamp01((Math.abs(p - 3.5) - 1.5) / 1); // 中段 slot 2–5 → 1
            const dim = dimK * mid;
            const fill = isP ? mixHex(PURPLE, '#2E2550', dim) : mixHex('#000000', '#050505', dim);
            const border = isP ? mixHex(WHITE, '#6A6A6A', dim) : mixHex(WHITE, '#5A5A5A', dim);
            const line = isP ? mixHex(WHITE, '#8A8A8A', dim) : mixHex(GREY_LIGHT, '#4A4A4A', dim);
            const s = isP ? pulse : 1;
            const glow = isP && glowK > 0 ? `0 0 ${Math.round(22 * glowK)}px ${Math.round(7 * glowK)}px rgba(102,45,248,${(0.6 * glowK).toFixed(2)})` : undefined;
            return (
              <div key={id} style={{...abs(SEG_X, y, SEG_W, SEG_H), boxSizing: 'border-box', background: fill, border: `1.5px solid ${border}`, borderRadius: 4, boxShadow: glow, transform: s === 1 ? undefined : `scale(${s.toFixed(3)})`, transformOrigin: '50% 50%', opacity: 1 - 0.35 * dim}}>
                {[0, 1].map((i) => <div key={i} style={{position: 'absolute', left: 10, top: 10 + i * 11, width: (0.5 + 0.42 * rnd(id + 1, i, 9)) * (SEG_W - 20) * (i === 1 ? 0.7 : 1), height: 3, background: line, opacity: 0.9}} />)}
              </div>
            );
          })}
          <Pill x={250} y={184} w={100} h={32} text="上下文" fontSize={22} weight={700} sw={2} />
        </div>
      ) : null}

      {/* ===== 右：曲线卡（5060 缩放入场） ===== */}
      {ncd >= 0 ? (
        <div style={{position: 'absolute', inset: 0, transform: `translate(${CARD.x + CARD.w / 2}px,${CARD.y + CARD.h / 2}px) scale(${cardS.toFixed(3)}) translate(${-(CARD.x + CARD.w / 2)}px,${-(CARD.y + CARD.h / 2)}px)`, transformOrigin: '0 0', opacity: cardOp}}>
          <Box x={CARD.x} y={CARD.y} w={CARD.w} h={CARD.h} r={8} sw={2} />
          <Svg bloom={false}>
            <defs>
              <clipPath id="g6-sc28-wipe">
                <rect x={PX0 - 4} y={PY0 - 10} width={Math.max(0, (PX1 - PX0 + 8) * wipe)} height={PY1 - PY0 + 20} />
              </clipPath>
            </defs>
            {/* 网格 */}
            {X_TICKS.map((p) => {
              const x = Math.round(xFor(p)) + 0.5;
              return <line key={`v${p}`} x1={x} y1={PY0} x2={x} y2={PY1} stroke={GREY_LINE} strokeWidth={1} />;
            })}
            {[0, 1, 2, 3].map((k) => {
              const y = Math.round(PY0 + (k * (PY1 - PY0)) / 4) + 0.5;
              return <line key={`h${k}`} x1={PX0} y1={y} x2={PX1} y2={y} stroke={GREY_LINE} strokeWidth={1} />;
            })}
            {/* 坐标轴 */}
            <line x1={PX0} y1={PY0 - 6} x2={PX0} y2={PY1} stroke={WHITE} strokeWidth={2} />
            <line x1={PX0} y1={PY1} x2={PX1 + 6} y2={PY1} stroke={WHITE} strokeWidth={2} />
            {/* U 形曲线（clipPath 按 x 揭示） */}
            <g clipPath="url(#g6-sc28-wipe)">
              <polyline points={CURVE_PTS.map((q) => `${q[0].toFixed(1)},${q[1].toFixed(1)}`).join(' ')} fill="none" stroke={PURPLE_DEEP} strokeWidth={3.5} strokeLinejoin="round" strokeLinecap="round" />
              <polyline points={CURVE_PTS.map((q) => `${q[0].toFixed(1)},${q[1].toFixed(1)}`).join(' ')} fill="none" stroke={PURPLE_LIGHT} strokeWidth={1.2} strokeLinejoin="round" strokeLinecap="round" opacity={0.7} />
            </g>
            {/* 中点红点 */}
            {dotS > 0 ? <circle cx={xFor(10.5)} cy={yFor(10.5)} r={6.5 * dotS} fill={CORAL} stroke="#FFF" strokeWidth={1.5} /> : null}
          </Svg>
          {/* 刻度与轴名 */}
          {X_TICKS.map((p) => (
            <CText key={p} cx={xFor(p)} cy={PY1 + 20} size={22} weight={500} color={GREY_LIGHT} dy={-1}>{p}</CText>
          ))}
          <CText cx={(PX0 + PX1) / 2} cy={PY1 + 48} size={22} weight={600} color={WHITE}>证据位置</CText>
          <CText cx={664} cy={(PY0 + PY1) / 2} size={22} weight={600} color={WHITE} style={{transform: 'translate(-50%,-50%) rotate(-90deg)'}}>准确率</CText>
          <SoftIn N={N} f0={B_CURVE + 14}>
            <CText cx={xFor(10.5)} cy={yFor(10.5) - 30} size={22} weight={700} color={WHITE} shadow="0 0 8px rgba(0,0,0,.8)">中间最差</CText>
          </SoftIn>
        </div>
      ) : null}

      {/* ===== 标题 + 出处（5154）—— 「Lost in the Middle」为本镜头唯一 glitch（白名单 §8）；出处 SoftIn ===== */}
      <GlitchIn N={N} f0={B_TITLE}>
        <TechText cx={CARD.x + CARD.w / 2} cy={566} text="Lost in the Middle" fontSize={34} weight={700} />
      </GlitchIn>
      <SoftIn N={N} f0={B_TITLE + 4}>
        <CText cx={CARD.x + CARD.w / 2} cy={600} size={22} weight={500} color={GREY} family={FONT_HEAVY}>Liu et al., TACL 2024</CText>
      </SoftIn>
    </div>
  );
};
