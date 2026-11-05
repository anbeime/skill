import React from 'react';
import {useCurrentFrame} from 'remotion';
import {GlitchIn, rnd, kf, emphasisPulse, easeOutCubic, FONT_ORB, FONT_HEAVY} from '../../common';
import {CText, TechText, MonoText, Box, ChunkCard, Svg, LineArrow, PURPLE, WHITE, GREY, GREY_LIGHT, GLOW_PURPLE_S, TEXT_GLOW, fadeIn, slideUp, exitAccel, abs} from '../../ui';

/**
 * SC16 第三步 向量化（2686–2860）
 * 节拍：2686 ChunkCard 自左滑入（QC v1：提前到组首帧、改横向入场，避免穿字幕带/进度条）→ 2694 第三步向量化→ 2704 箭头 draw-on → 2720 Embedding 盒 glitch →
 *      2740 第二支箭头 → 2779 向量数字 2 帧错峰出现 → 2800 维度计数 384→1024 → 2853 起 8 帧离场。
 * 数字依据 research §2.5：维度 384（all-MiniLM-L6-v2）…4096；主流 1024–3072。
 */
export const F0 = 2686;
const B_CARD = 2686, B_ARROW1 = 2704, B_BOX = 2720, B_ARROW2 = 2742, B_BRACKET = 2766, B_NUM = 2779, B_DIM = 2800, EXIT = 2853;

// 布局（内容主区 y 175–620）
const CARD = {x: 175, y: 325, w: 170, h: 110};
const BOX = {x: 530, y: 325, w: 220, h: 110};
const CY = 380;
const NUM_X = [872, 980, 1088];
const NUM_Y = [332, 368, 404];

/** 8 个确定性随机向量分量，两位小数，负号用 U+2212 */
const fmt = (v: number) => (v < 0 ? '−' : ' ') + Math.abs(v).toFixed(2);
const NUMS = Array.from({length: 8}, (_, i) => fmt(rnd(16, i, 3) * 1.8 - 0.9));

export const SC16: React.FC = () => {
  const N = useCurrentFrame() + F0;
  // 离场：8 帧线性淡出 + 加速下摇
  const ne = N - EXIT;
  const exitOp = ne <= 0 ? 1 : Math.max(0, 1 - ne / 8);
  const exitDy = exitAccel(ne, 0.6);

  const nCard = N - B_CARD;
  const cardOp = fadeIn(nCard + 2, 6); // 2686 首帧即 α≈.33，避免组界出现空帧
  const cardDx = -slideUp(nCard, 320, 18); // 自左滑入（起点右缘 x≈25，露一小截），不经字幕带/进度条

  const p1 = easeOutCubic((N - B_ARROW1) / 16);
  const p2 = easeOutCubic((N - B_ARROW2) / 16);
  const boxScale = emphasisPulse(N - B_NUM, {peak: 1.08, up: 10, hold: 3, down: 12});

  // 维度计数 384→1024（Orbitron），ease-out
  const dim = Math.round(kf(N, [[B_DIM, 384], [B_DIM + 32, 1024]], easeOutCubic));
  const dimOp = fadeIn(N - B_DIM, 8);

  return (
    <div style={{position: 'absolute', inset: 0, opacity: exitOp, transform: `translateY(${exitDy.toFixed(2)}px)`}}>
      {/* 左：文本块 chunk */}
      {nCard >= 0 ? (
        <div style={{position: 'absolute', inset: 0, opacity: cardOp, transform: `translateX(${cardDx.toFixed(2)}px)`}}>
          <ChunkCard x={CARD.x} y={CARD.y} w={CARD.w} h={CARD.h} lines={5} active seed={3} />
          <CText cx={CARD.x + CARD.w / 2} cy={CARD.y + CARD.h + 26} size={24} weight={600} color={GREY_LIGHT}>文本块</CText>
        </div>
      ) : null}

      {/* 箭头：卡片 → Embedding 盒 → 向量 */}
      <Svg>
        {p1 > 0 ? <LineArrow x0={CARD.x + CARD.w + 10} y0={CY} x1={BOX.x - 12} y1={CY} p={p1} /> : null}
        {p2 > 0 ? <LineArrow x0={BOX.x + BOX.w + 10} y0={CY} x1={840} y1={CY} p={p2} /> : null}
      </Svg>

      {/* 中：Embedding 模型盒（R4 Embedding 盒样式：紫填充 + 白 3px 实线边） */}
      <GlitchIn N={N} f0={B_BOX}>
        <div style={{...abs(BOX.x, BOX.y, BOX.w, BOX.h), transform: `scale(${boxScale.toFixed(4)})`, transformOrigin: '50% 50%'}}>
          <Box x={0} y={0} w={BOX.w} h={BOX.h} r={10} fill={PURPLE} sw={3} glow={GLOW_PURPLE_S} />
          <TechText cx={BOX.w / 2} cy={44} text="Embedding" fontSize={38} color={WHITE} scaleX={0.86} weight={700} glow={false} style={{textShadow: TEXT_GLOW}} />
          <CText cx={BOX.w / 2} cy={82} size={22} weight={500} color={WHITE}>模型</CText>
        </div>
      </GlitchIn>

      {/* 右：一串数字（等宽），逐个 2 帧错峰出现 */}
      <MonoText x={846} y={NUM_Y[0]} size={26} color={GREY_LIGHT} opacity={fadeIn(N - B_BRACKET, 6)}>[</MonoText>
      {NUMS.map((s, i) => {
        const row = Math.floor(i / 3), col = i % 3;
        const n = N - (B_NUM + i * 2);
        if (n < 0) return null;
        const op = fadeIn(n, 4);
        const dx = 10 * (1 - op);
        return (
          <MonoText key={i} x={NUM_X[col] + dx} y={NUM_Y[row]} size={24} color={WHITE} opacity={op} style={{textShadow: '0 0 6px rgba(255,255,255,.35)'}}>
            {s + ','}
          </MonoText>
        );
      })}
      <MonoText x={NUM_X[2]} y={NUM_Y[2]} size={24} color={GREY} opacity={fadeIn(N - (B_NUM + 16), 4)}>{'  …   ]'}</MonoText>

      {/* 维度：× 1024 维（Orbitron 计数） */}
      <div style={{...abs(872, 448, 320, 40), opacity: dimOp, display: 'flex', alignItems: 'baseline', gap: 8, whiteSpace: 'nowrap'}}>
        <span style={{fontFamily: FONT_HEAVY, fontWeight: 600, fontSize: 24, color: GREY, lineHeight: 1}}>×</span>
        <span style={{fontFamily: FONT_ORB, fontWeight: 600, fontSize: 32, color: WHITE, lineHeight: 1, letterSpacing: 1, textShadow: TEXT_GLOW, fontVariantNumeric: 'tabular-nums', minWidth: 84, textAlign: 'right'}}>{dim}</span>
        <span style={{fontFamily: FONT_HEAVY, fontWeight: 600, fontSize: 24, color: GREY, lineHeight: 1}}>维</span>
      </div>
    </div>
  );
};
