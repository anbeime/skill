import React from 'react';
import {useCurrentFrame} from 'remotion';
import {kf, powOutRemain, easeInOutPow, easeOutCubic, clamp01, glitchOpacity, emphasisPulse, FONT_ORB, FONT_HEAVY} from '../../common';
import {CText, TechText, Box, Svg, LineArrow, fadeIn, slideUp, GREY_LIGHT, WHITE, abs, SoftIn} from '../../ui';
import {TrapRag, TrapText, TrapTech, MiniCard, mixStops} from './ui';

/**
 * SC26 第三步 重排（4677–4926）
 * 节拍：4685 第三步重排 / 4707 粗召回几十条 / 4734 Cross-Encoder / 4823 放在一起打分 / 4890 只留几条
 * 画面：顶部 25 张迷你候选卡（召回 25 条，Pinecone top-25 → top-3）→ 梯形层（灰占位 → 4734 变紫 + Cross-Encoder）→
 *      左侧「问题 + 段落」配对卡滑入、右侧相关分 0.92 计数 → 25 卡穿过梯形（在梯形之后，穿层时被遮），22 张变灰落出画，3 张落到底部变紫「Top 3」。
 * QC v1 修复：
 *  - 「召回 25 条」+ 25 卡 + 「重排」灰梯形入场提前到 4685（与流程轨切「重排」同拍），4707 改为卡片逐张波浪脉冲 + 标签脉冲（粗召回几十条）；
 *  - 4734 梯形灰→紫 11 帧 + 「Cross-Encoder 重排」glitch 换字；
 *  - 落卡改画在梯形层之后（穿层时被遮，不再盖住 Cross-Encoder 字样）；配对卡/相关分 4882 起 8 帧淡尽，4890 落卡前已清场。
 */
const F0 = 4677;
const B_TAG = 4685, B_CARDS = 4707, B_TRAP = 4734, B_PAIR = 4823, B_FALL = 4890;
const T_CARDS_IN = B_TAG; // 卡阵列 + 标签 入场
const T_TRAP_IN = B_TAG + 2; // 灰梯形占位 slideUp
const T_PAIR_OUT = 4882; // 配对卡 / 相关分 8 帧淡尽
const NC = 25, CW = 38, CH = 50, PITCH = 41, ROW_Y = 205;
const cardCx = (i: number) => 148 + PITCH * i;
const KEPT = [5, 12, 19];
const KEPT_TX = [540, 640, 740];
const KEPT_W = 86, KEPT_H = 64, KEPT_Y = 478;
const TRAP = {cx: 640, y: 330, wTop: 720, wBot: 360, h: 90};
const easeMove = easeInOutPow(2.5);
const TRAP_ROW: React.CSSProperties = {position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12};

export const SC26: React.FC = () => {
  const N = useCurrentFrame() + F0;
  const opAll = N >= 4921 ? Math.max(0, 1 - (N - 4920) / 7) : 1;

  // ---- 梯形层：4687 灰占位 slideUp → 4734 灰→紫 11 帧 + 换字 ----
  const nt = N - T_TRAP_IN;
  // QC v2：起点 Δ 260→100（首帧 y=430，底缘 524 <637 不进字幕带）+ 前 6 帧 fadeIn
  const trapY = TRAP.y + slideUp(nt, 100);
  const trapOp = fadeIn(nt, 6);
  const kPur = easeOutCubic(clamp01((N - B_TRAP) / 11));
  // 「重排」单字 ↔ 「Cross-Encoder 重排」用 glitch 序列做硬切换（不做叠影交叉淡化）—— 本镜头唯一 glitch（白名单 §8）
  const glCE = glitchOpacity(N - B_TRAP);
  const showCE = N >= B_TRAP && glCE >= 0.5;

  // ---- 25 张候选卡（4685 升起；4707 波浪脉冲；4890 穿层）----
  const cards = Array.from({length: NC}, (_, i) => {
    const nIn = N - T_CARDS_IN - i * 0.6;
    if (nIn < 0) return null;
    const keptIdx = KEPT.indexOf(i);
    // 入场：自下 26px 升起 + 淡入（不进 rail y112–160、不压「召回 25 条」标签）
    let cx = cardCx(i), y = ROW_Y + 26 * powOutRemain(nIn, 12, 2.5), w = CW, h = CH, grey = 0, active = 0, op = fadeIn(nIn, 6);
    // 4707 波浪脉冲：每卡 0.5 帧错峰，10 帧 sin 抬起 6px + 放大 12%
    const nw = N - B_CARDS - i * 0.5;
    if (nw > 0 && nw < 10) {
      const pw = Math.sin((Math.PI * nw) / 10);
      w = CW * (1 + 0.12 * pw);
      h = CH * (1 + 0.12 * pw);
      y -= 6 * pw + (h - CH) / 2; // 抬起 + 以卡心为锚放大
      active = 0.35 * pw;
    }
    const tf = N - B_FALL - i * 0.25;
    if (tf > 0) {
      if (keptIdx < 0) {
        const u = clamp01(tf / 20);
        y = ROW_Y + (700 - ROW_Y) * u * u;
        grey = clamp01((y - 300) / 80);
        op = 1 - clamp01((y - 520) / 80); // y≥600 完全消失，不触字幕带
      } else {
        const u = easeMove(clamp01(tf / 20));
        y = ROW_Y + (KEPT_Y - ROW_Y) * u;
        cx = cx + (KEPT_TX[keptIdx] - cx) * u;
        w = CW + (KEPT_W - CW) * u;
        h = CH + (KEPT_H - CH) * u;
        active = clamp01((y - 330) / 90);
      }
    }
    if (op <= 0) return null;
    return <MiniCard key={i} x={cx - w / 2} y={y} w={w} h={h} seed={i + 1} grey={grey} active={active} opacity={op} r={active > 0.5 ? 6 : 4} />;
  });

  // ---- 配对卡 + 箭头 + 相关分 ----
  const np = N - B_PAIR;
  const pairX = 60 - 320 * powOutRemain(np, 18, 2.5);
  const pairOp = fadeIn(np, 6) * (N >= T_PAIR_OUT ? 1 - clamp01((N - T_PAIR_OUT) / 8) : 1);
  const arrow1 = clamp01((N - 4838) / 12);
  const arrow2 = clamp01((N - 4842) / 12);
  const score = kf(N, [[4848, 0], [4866, 0.92]]);

  // 「召回 25 条」标签 4707 脉冲
  const sTag = emphasisPulse(N - B_CARDS, {peak: 1.06, up: 8, hold: 3, down: 10});

  return (
    <div style={{position: 'absolute', inset: 0, opacity: opAll}}>
      {/* 顶部标签：Rerank / 召回 25 条（均 4685；标签 4707 脉冲） */}
      <SoftIn N={N} f0={B_TAG}>
        <TechText cx={1080} cy={186} text="Rerank" fontSize={28} />
      </SoftIn>
      <SoftIn N={N} f0={T_CARDS_IN}>
        <div style={{...abs(0, 0, 1280, 720), transformOrigin: '0 0', transform: `translate(210px,186px) scale(${sTag.toFixed(4)}) translate(-210px,-186px)`}}>
          <CText cx={210} cy={186} size={22} weight={600}>
            召回 <span style={{fontFamily: FONT_ORB, fontWeight: 700}}>25</span> 条
          </CText>
        </div>
      </SoftIn>

      {/* 25 张候选卡（画在梯形之前 → 穿层时被梯形遮住，不盖字） */}
      {cards}

      {/* 梯形层（4687 灰占位「重排」→ 4734 变紫 + 「Cross-Encoder 重排」） */}
      {nt >= 0 ? (
        <TrapRag id="g6-sc26-trap" cx={TRAP.cx} y={trapY} wTop={TRAP.wTop} wBot={TRAP.wBot} h={TRAP.h} stops={mixStops(kPur)} opacity={trapOp}>
          <div style={{...TRAP_ROW, opacity: showCE ? 0 : 1}}>
            <TrapText size={34}>重排</TrapText>
          </div>
          <div style={{...TRAP_ROW, opacity: showCE ? 1 : 0}}>
            <TrapTech size={34}>Cross-Encoder</TrapTech>
            <TrapText size={34}>重排</TrapText>
          </div>
        </TrapRag>
      ) : null}

      {/* 配对卡：问题 + 段落（4823 自左滑入，4882 起淡出） */}
      {np >= 0 && pairOp > 0 ? (
        <div style={{...abs(pairX, 340, 240, 70), opacity: pairOp}}>
          <Box x={0} y={0} w={240} h={70} r={8} sw={2} />
          <div style={{position: 'absolute', left: 14, top: 10, fontFamily: FONT_HEAVY, fontWeight: 600, fontSize: 22, lineHeight: 1, color: WHITE, whiteSpace: 'nowrap'}}>差旅报销上限？</div>
          <div style={{...abs(14, 40, 212, 1.5), background: '#4A4A4A'}} />
          <div style={{...abs(14, 48, 150, 3), background: GREY_LIGHT, opacity: 0.85}} />
          <div style={{...abs(14, 57, 96, 3), background: GREY_LIGHT, opacity: 0.85}} />
        </div>
      ) : null}
      {np >= 0 && pairOp > 0 ? (
        <Svg opacity={pairOp}>
          <LineArrow x0={305} y0={375} x1={362} y1={375} p={arrow1} headL={16} headW={18} />
          <LineArrow x0={916} y0={375} x1={980} y1={375} p={arrow2} headL={16} headW={18} />
        </Svg>
      ) : null}
      {/* 相关分 0.92（4846 SoftIn + 18 帧计数） */}
      {pairOp > 0 ? (
        <SoftIn N={N} f0={4846} style={{opacity: pairOp}}>
          <CText cx={1070} cy={330} size={22} weight={600} color={GREY_LIGHT}>相关分</CText>
          <Box x={985} y={347} w={170} h={56} r={8} sw={2} />
          <CText cx={1070} cy={375} size={34} weight={700} family={FONT_ORB} dy={0} style={{fontVariantNumeric: 'tabular-nums'}}>
            {score.toFixed(2)}
          </CText>
        </SoftIn>
      ) : null}

      {/* Top 3 标签（4914） */}
      <SoftIn N={N} f0={4914}>
        <CText cx={640} cy={578} size={26} weight={700} family={FONT_ORB} dy={0} letterSpacing={1}>Top 3</CText>
      </SoftIn>
    </div>
  );
};
