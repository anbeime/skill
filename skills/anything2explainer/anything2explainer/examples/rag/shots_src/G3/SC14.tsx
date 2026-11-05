import React from 'react';
import {useCurrentFrame} from 'remotion';
import {slideIn, rnd, clamp01, FONT_ORB} from '../../common';
import {Box, Pill, CText, TechText, ChunkCard, Svg, Check, Cross, ArrowH, PURPLE, PURPLE_LIGHT, ORANGE, GREY_LIGHT, abs, scaleIn, slideUp, fadeIn, fadeOut, exitAccel, SoftIn} from '../../ui';
import {Magnifier} from './g3ui';

/**
 * SC14 切多大（2055–2308，S14）
 * 节拍：2063 切多大是学问（中央问句）/ 2098 太大不精准（左栏巨卡 + 放大镜找不到 + 红叉）/ 2133 太小被切碎（右栏碎块散落 + 红叉）
 *      / 2173 几百个 token 一块（中栏三张标准 ChunkCard + 绿勾 + Orbitron 数字滚动 → 「几百」）/ 2257 留一点重叠（相邻卡之间紫色半透明重叠带 + 「重叠」）
 * 2298 起整组下摇淡出，SC15 硬接。
 */
const F0 = 2055;
const CARD_X = 565, CARD_Y0 = 258, CARD_H = 92, CARD_GAP = 14;
const PIECES = 14;

export const SC14: React.FC = () => {
  const N = useCurrentFrame() + F0;
  const ex = N - 2298;
  const gOp = ex > 0 ? fadeOut(ex, 10) : 1;
  const gDy = ex > 0 ? exitAccel(ex, 0.9) : 0;
  // 左栏
  const ln = N - 2098;
  const bigX = 130 - slideUp(ln, 300);
  // 中栏数字
  const rolling = N >= 2173 && N < 2194;
  const rollVal = 300 + Math.round(rnd(7, N) * 500);

  return (
    <div style={{position: 'absolute', inset: 0, opacity: gOp, transform: gDy ? `translateY(${gDy.toFixed(1)}px)` : undefined}}>
      {/* 2063 问句（2173 硬切掉） */}
      {N < 2173 ? (
        <SoftIn N={N} f0={2063}>
          <CText cx={640} cy={330} size={44} weight={900} scaleX={0.9}>切多大？</CText>
        </SoftIn>
      ) : null}

      {/* 左栏：太大 */}
      {ln >= 0 ? (
        <div style={{opacity: fadeIn(ln, 6)}}>
          <ChunkCard x={bigX} y={CARD_Y0} w={220} h={330} lines={14} seed={3} />
        </div>
      ) : null}
      <SoftIn N={N} f0={2098}>
        <Pill x={185} y={196} w={110} h={44} sw={2.5} text="太大" fontSize={26} weight={700} />
      </SoftIn>
      <Magnifier cx={240} cy={440} s={scaleIn(N - 2110)} opacity={N >= 2110 ? 1 : 0} />

      {/* 右栏：太小（碎块从中心散开） */}
      {Array.from({length: PIECES}, (_, i) => {
        const n = N - (2133 + i);
        if (n < 0) return null;
        const k = slideIn(n, 18);
        const tx = 1040 + (rnd(41, i) - 0.5) * 230, ty = 420 + (rnd(42, i) - 0.5) * 300;
        const x = 1040 + (tx - 1040) * k, y = 420 + (ty - 420) * k;
        const w = 22 + rnd(44, i) * 16, h = 16 + rnd(45, i) * 12;
        const rot = (rnd(43, i) - 0.5) * 60 * k;
        return (
          <div key={i} style={{...abs(x - w / 2, y - h / 2, w, h), opacity: fadeIn(n, 6), transform: `rotate(${rot.toFixed(1)}deg)`}}>
            <Box x={0} y={0} w={w} h={h} r={3} sw={1.5}>
              <div style={{...abs(5, h / 2 - 2.5, w - 14, 2), background: GREY_LIGHT, opacity: 0.9}} />
            </Box>
          </div>
        );
      })}
      <SoftIn N={N} f0={2133}>
        <Pill x={985} y={196} w={110} h={44} sw={2.5} text="太小" fontSize={26} weight={700} />
      </SoftIn>

      {/* 中栏：常见做法 */}
      {[0, 1, 2].map((i) => {
        const s = scaleIn(N - (2173 + i * 2));
        if (s <= 0) return null;
        const y = CARD_Y0 + i * (CARD_H + CARD_GAP);
        return (
          <div key={i} style={{...abs(CARD_X, y, 150, CARD_H), transform: `scale(${s.toFixed(4)})`}}>
            <ChunkCard x={0} y={0} w={150} h={CARD_H} lines={4} seed={i + 1} />
          </div>
        );
      })}
      <SoftIn N={N} f0={2173}>
        <Pill x={565} y={196} w={150} h={44} fill={PURPLE} sw={2.5} text="常见做法" fontSize={26} weight={700} glow="0 0 18px 4px rgba(102,45,248,.45)" />
      </SoftIn>
      <ArrowH x={516} y={310} w={44} h={20} p={slideIn(N - 2177, 12)} />
      {rolling ? (
        <>
          <CText cx={436} cy={320} size={30} weight={800}>≈</CText>
          <CText cx={484} cy={320} size={30} weight={700} family={FONT_ORB} color={ORANGE} style={{fontVariantNumeric: 'tabular-nums'}}>
            {rollVal}
          </CText>
        </>
      ) : N >= 2194 ? (
        <>
          <CText cx={470} cy={320} size={30} weight={800}>≈ 几百</CText>
          <TechText cx={470} cy={360} text="token" fontSize={28} scaleX={0.84} color={PURPLE_LIGHT} />
        </>
      ) : null}

      {/* 2257 重叠带 */}
      {[0, 1].map((k) => {
        const p = clamp01((N - (2257 + 4 * k)) / 8);
        if (p <= 0) return null;
        const y = CARD_Y0 + CARD_H + k * (CARD_H + CARD_GAP) - 8;
        return <div key={k} style={{...abs(CARD_X, y, 150 * p, CARD_GAP + 16), boxSizing: 'border-box', background: 'rgba(102,48,248,.45)', border: `1.5px solid ${PURPLE_LIGHT}`, borderRadius: 3}} />;
      })}
      <SoftIn N={N} f0={2261}>
        <Pill x={735} y={342} w={76} h={30} fill={PURPLE} sw={0} text="重叠" fontSize={22} weight={700} textDy={-1} />
      </SoftIn>

      {/* 勾 / 叉 */}
      <Svg bloom={false}>
        <Cross cx={320} cy={218} size={24} sw={5} p={slideIn(N - 2106, 10)} />
        <Cross cx={1120} cy={218} size={24} sw={5} p={slideIn(N - 2141, 10)} />
        <Check cx={742} cy={218} size={34} sw={5} p={slideIn(N - 2181, 10)} />
      </Svg>
    </div>
  );
};
