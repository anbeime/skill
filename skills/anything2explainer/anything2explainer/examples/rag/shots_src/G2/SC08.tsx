import React from 'react';
import {useCurrentFrame} from 'remotion';
import {GlitchIn, emphasisPulse, clamp01, easeInOutPow, FONT_TECH, FONT_WIDE} from '../../common';
import {CText, Box, WHITE, PURPLE, PURPLE_TECH, PURPLE_LIGHT, slideUp, fadeIn, stagger, SoftIn} from '../../ui';
import {LightBar} from './parts';

/**
 * SC08 主角登场 RAG · N 1013–1129（S08 1021–1127：1021「这套方法就是今天的主角」/ 1080「RAG」/ 1096「检索增强生成」）
 * 版式（清场）：中央「RAG」Audiowide 150px 白 + 紫硬投影 (+6,+6)，中心 (640,330)；下方「检索增强生成」Noto 900 48px scaleX .8 (640,452)；
 *       再下三小胶囊 Retrieval / Augmented / Generation（Exo 2 紫斜体，首字母白）y 520–566，中心 x 420 / 640 / 860。
 * 节拍：1017/1035/1053 三轮横向紫光条（每轮 3 条、2 帧错峰、16 帧、α .6/.55/.55 + 白芯）连续扫过（"舞台追光"）；1031 起中央留一条呼吸紫光线；
 *       1050 起「RAG」白描边轮廓以 8–12% 不透明度隐现（光条扫过其上）；
 *       1080「RAG」GlitchIn(rgbSplit 8, slices 20)（本镜头唯一 glitch，白名单 §8 重口味四处之一）+ 光线白闪 3 帧后消失；1092 起 emphasisPulse 1.11；1096 中文副标自下滑入（Δ80/22，不穿过胶囊行）；1104/1106/1108 三胶囊 SoftIn；
 *       1124–1129 整组 6 帧淡出（SC09 硬切）。
 * QC v1 修复：原 1015/1048 两轮 α .3/.2 光条 + 极淡呼吸线 → 1021–1079 观感近黑屏 2 秒；现三轮连续 + 提亮 + 白芯 + RAG 轮廓预示。
 */
const F0 = 1013;
/** 三轮扫光起始帧（轮距 18 帧，单轮含错峰共 20 帧 → 首尾相接） */
const T_SWEEPS = [1017, 1035, 1053];
const SWEEP_ALPHA = [0.6, 0.55, 0.55];
const T_LINE = 1031, T_GHOST = 1050, T_RAG = 1080, T_PULSE = 1092, T_SUB = 1096, T_PILLS = 1104, T_EXIT = 1124;

/** 光条：[y, h, w, 帧偏移] */
const BARS: Array<[number, number, number, number]> = [[292, 6, 420, 0], [334, 10, 560, 2], [378, 6, 380, 4]];
const SWEEP_LEN = 16;
const PILLS: Array<[string, string, number, number]> = [['R', 'etrieval', 420, 200], ['A', 'ugmented', 640, 214], ['G', 'eneration', 860, 214]];

const sweepX = (n: number, w: number) => {
  // 自左 −w 扫到 1280+w，easeInOut
  const t = clamp01(n / SWEEP_LEN);
  return -w + (1280 + 2 * w) * easeInOutPow(1.6)(t);
};

export const SC08: React.FC = () => {
  const N = useCurrentFrame() + F0;
  const ex = N - T_EXIT;
  const exOp = ex <= 0 ? 1 : Math.max(0, 1 - ex / 6);

  // 舞台光线：1031 起 14 帧展宽到 720，呼吸；1080 起 3 帧白闪后消失
  const ln = N - T_LINE;
  const lineW = ln < 0 ? 0 : 720 * (1 - Math.pow(1 - clamp01(ln / 14), 2.5));
  const breathe = 0.45 + 0.15 * Math.sin((N - T_LINE) * 0.28);
  const flash = N >= T_RAG ? N - T_RAG : -1; // 0,1,2 → 白闪；≥3 不画
  const showLine = ln >= 0 && (flash < 3);

  // 「RAG」轮廓预示：1050 起 12 帧淡入到 ~0.10，呼吸 ±0.02，glitch 闪烁期（1080–1091）内保留作底，1092 起撤掉
  const gn = N - T_GHOST;
  const ghostOp = gn < 0 || N >= T_PULSE ? 0 : (0.1 + 0.02 * Math.sin(gn * 0.35)) * fadeIn(gn, 12);

  const rn = N - T_RAG;
  const pulse = emphasisPulse(N - T_PULSE, {peak: 1.11});
  const sn = N - T_SUB;
  const subY = 452 + slideUp(sn, 80, 22);

  return (
    <div style={{position: 'absolute', inset: 0, opacity: exOp}}>
      {/* 光条扫过 ×3（连续） */}
      {T_SWEEPS.map((t0, k) =>
        BARS.map(([y, h, w, off], i) => {
          const n = N - t0 - off;
          if (n < 0 || n > SWEEP_LEN) return null;
          return <LightBar key={`${k}-${i}`} x={sweepX(n, w)} y={y - h / 2} w={w} h={h} alpha={SWEEP_ALPHA[k] * (1 - Math.pow(clamp01(n / SWEEP_LEN), 6))} />;
        }),
      )}
      {/* 舞台光线 */}
      {showLine ? (
        <div style={{position: 'absolute', left: 640 - lineW / 2, top: 331, width: lineW, height: 3, borderRadius: 2, background: flash >= 0 ? WHITE : `linear-gradient(90deg, transparent, ${PURPLE_LIGHT} 20%, ${PURPLE_LIGHT} 80%, transparent)`, opacity: flash >= 0 ? [0.95, 0.7, 0.35][flash] : breathe, boxShadow: flash >= 0 ? '0 0 30px 8px rgba(255,255,255,.55)' : '0 0 18px 4px rgba(102,45,248,.5)'}} />
      ) : null}
      {/* RAG 轮廓隐现（白描边、透明填充、紫雾） */}
      {ghostOp > 0 ? (
        <CText cx={640} cy={330} size={150} weight={400} family={FONT_WIDE} letterSpacing={8} color="transparent" dy={-4} opacity={ghostOp} shadow="0 0 22px rgba(161,117,241,.95)" style={{WebkitTextStroke: `2px ${WHITE}`}}>
          RAG
        </CText>
      ) : null}
      {/* RAG 大字：glitch 入 + 脉冲 */}
      {rn >= 0 ? (
        <div style={{position: 'absolute', inset: 0, transformOrigin: '640px 330px', transform: pulse === 1 ? undefined : `scale(${pulse.toFixed(4)})`}}>
          <GlitchIn N={N} f0={T_RAG} rgbSplit={8} slices={20} sliceBands={4} seed={8}>
            <CText cx={640} cy={330} size={150} weight={400} family={FONT_WIDE} letterSpacing={8} color={WHITE} dy={-4} shadow={`6px 6px 0 ${PURPLE}, 0 0 28px rgba(102,45,248,.45)`}>
              RAG
            </CText>
          </GlitchIn>
        </div>
      ) : null}
      {/* 中文副标 */}
      {sn >= 0 ? (
        <CText cx={640} cy={subY} size={48} weight={900} scaleX={0.8} letterSpacing={4} color={WHITE} opacity={fadeIn(sn, 8)} dy={-3}>
          检索增强生成
        </CText>
      ) : null}
      {/* 三小胶囊：首字母白、其余 Exo 2 紫斜体（SoftIn，2 帧错峰） */}
      {PILLS.map(([head, rest, cx, w], i) => (
        <SoftIn key={head} N={N} f0={T_PILLS + stagger(i, 2)}>
          <Box x={cx - w / 2} y={520} w={w} h={46} r={23} sw={2}>
            <div style={{position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: FONT_TECH, fontStyle: 'italic', fontSize: 27, letterSpacing: 1, lineHeight: 1, whiteSpace: 'nowrap', transform: 'translateY(-1px) scaleX(0.9)', textShadow: '0 0 6px rgba(80,30,200,.7)'}}>
              <span style={{color: WHITE, fontWeight: 900, fontSize: 31}}>{head}</span>
              <span style={{color: PURPLE_TECH, fontWeight: 600}}>{rest}</span>
            </div>
          </Box>
        </SoftIn>
      ))}
    </div>
  );
};
