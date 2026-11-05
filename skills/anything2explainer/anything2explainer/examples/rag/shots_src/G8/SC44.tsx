import React from 'react';
import {useCurrentFrame} from 'remotion';
import {GlitchIn, clamp01} from '../../common';
import {CText, Pill, PURPLE, PURPLE_LIGHT, WHITE, fadeIn, slideUp, SoftIn} from '../../ui';
import {FR, Castle, ellipsePerim} from './shared';

/**
 * SC44 知识库 = 护城河（8053–8148）。中央城堡自下滑入（Δ170，8061）；顶上紫 Pill「知识库」SoftIn 淡入（8069；闪烁整改：本镜头 glitch 只给大字）；护城河椭圆环 draw-on 20 帧（8071）+ 波纹 2 帧一相位；
 * 8077 大字「知识库 = 护城河」Noto 900 60px scaleX .85 白 + 紫描边 GlitchIn rgbSplit 6。末 2 帧不离场（G0 片尾接管淡出）。
 */
const F0 = FR.SC44.from;
const CX = 640, BASE_Y = 420;
const MOAT = {cx: 640, cy: 428, rxo: 335, ryo: 78, rxi: 245, ryi: 44};
const PERIM_O = ellipsePerim(MOAT.rxo, MOAT.ryo), PERIM_I = ellipsePerim(MOAT.rxi, MOAT.ryi);

export const SC44: React.FC = () => {
  const N = useCurrentFrame() + F0;
  const nC = N - 8061;
  const castleDy = slideUp(nC, 170); // QC v1：Δ300→170，起点城堡底 y≈590 不穿字幕带
  const mp = clamp01((N - 8071) / 20);
  const mpe = 1 - Math.pow(1 - mp, 2);
  const phase = Math.floor(Math.max(0, N - 8071) / 2) * 5; // 波纹相位：2 帧一步
  const fillOp = 0.85 * clamp01((N - 8079) / 12);
  return (
    <>
      {nC >= 0 ? (
        <svg width={1280} height={720} viewBox="0 0 1280 720" style={{position: 'absolute', left: 0, top: 0, overflow: 'visible', filter: 'drop-shadow(0 0 3px rgba(255,255,255,0.45))', opacity: fadeIn(nC, 10), transform: `translateY(${castleDy.toFixed(2)}px)`}}>
          <defs>
            <linearGradient id="g8-moat" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#3A1E8C" />
              <stop offset="55%" stopColor={PURPLE} />
              <stop offset="100%" stopColor="#8F62F5" />
            </linearGradient>
            <clipPath id="g8-moat-back">
              <rect x={0} y={0} width={1280} height={MOAT.cy} />
            </clipPath>
            <clipPath id="g8-moat-front">
              <rect x={0} y={MOAT.cy} width={1280} height={720 - MOAT.cy} />
            </clipPath>
          </defs>
          {/* 护城河：后半环（城堡之后） */}
          <g clipPath="url(#g8-moat-back)">
            <path d={ringPath()} fill="url(#g8-moat)" fillRule="evenodd" opacity={fillOp} />
            <ellipse cx={MOAT.cx} cy={MOAT.cy} rx={MOAT.rxo} ry={MOAT.ryo} fill="none" stroke={WHITE} strokeWidth={2.5} strokeDasharray={PERIM_O} strokeDashoffset={PERIM_O * (1 - mpe)} />
            <ellipse cx={MOAT.cx} cy={MOAT.cy} rx={MOAT.rxi} ry={MOAT.ryi} fill="none" stroke={WHITE} strokeWidth={2.5} strokeDasharray={PERIM_I} strokeDashoffset={PERIM_I * (1 - mpe)} />
          </g>
          <Castle cx={CX} baseY={BASE_Y} />
          {/* 护城河：前半环（城堡之前）+ 波纹 */}
          <g clipPath="url(#g8-moat-front)">
            <path d={ringPath()} fill="url(#g8-moat)" fillRule="evenodd" opacity={fillOp} />
            <ellipse cx={MOAT.cx} cy={MOAT.cy} rx={MOAT.rxo} ry={MOAT.ryo} fill="none" stroke={WHITE} strokeWidth={2.5} strokeDasharray={PERIM_O} strokeDashoffset={PERIM_O * (1 - mpe)} />
            <ellipse cx={MOAT.cx} cy={MOAT.cy} rx={MOAT.rxi} ry={MOAT.ryi} fill="none" stroke={WHITE} strokeWidth={2.5} strokeDasharray={PERIM_I} strokeDashoffset={PERIM_I * (1 - mpe)} />
          </g>
          {[0.3, 0.55, 0.8].map((t, i) => (
            <ellipse key={i} cx={MOAT.cx} cy={MOAT.cy} rx={MOAT.rxi + (MOAT.rxo - MOAT.rxi) * t} ry={MOAT.ryi + (MOAT.ryo - MOAT.ryi) * t} fill="none" stroke={PURPLE_LIGHT} strokeWidth={1.6} strokeDasharray="16 22" strokeDashoffset={phase * (i % 2 ? -1 : 1) + i * 9} opacity={0.55 * fillOp} />
          ))}
        </svg>
      ) : null}
      <SoftIn N={N} f0={8069}>
        <Pill x={CX - 85} y={122} w={170} h={46} fill={PURPLE} text="知识库" fontSize={28} weight={800} letterSpacing={3} sw={2.5} glow="0 0 14px 3px rgba(102,45,248,.35)" />
      </SoftIn>
      <GlitchIn N={N} f0={8077} rgbSplit={6}>
        <CText cx={640} cy={574} size={60} weight={900} scaleX={0.85} letterSpacing={2} style={{WebkitTextStroke: `2.5px ${PURPLE}`, paintOrder: 'stroke fill'}} shadow="0 0 18px rgba(102,45,248,.7)">
          知识库 = 护城河
        </CText>
      </GlitchIn>
    </>
  );
};

/** 环带路径（外椭圆 + 内椭圆，evenodd 挖空） */
const ringPath = () => {
  const e = (rx: number, ry: number) => `M ${MOAT.cx - rx} ${MOAT.cy} a ${rx} ${ry} 0 1 0 ${rx * 2} 0 a ${rx} ${ry} 0 1 0 ${-rx * 2} 0 Z`;
  return `${e(MOAT.rxo, MOAT.ryo)} ${e(MOAT.rxi, MOAT.ryi)}`;
};
