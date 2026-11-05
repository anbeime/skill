import React from 'react';
import {useCurrentFrame} from 'remotion';
import {easeInOutPow, emphasisPulse, clamp01} from '../../common';
import {Box, Pill, TechText, Svg, LineArrow, LLMIcon, fadeIn, slideUp, scaleIn, exitAccel, abs} from '../../ui';
import {AnswerCard, EvidenceCard, TypeLine, HLine, typedCount, citeOp, ANS_TOTAL} from './ui';

/**
 * SC29 生成：约束提示词（5314–5564）
 * 节拍：5322 最后生成 / 5342 问题和证据交给大模型 / 5407 只根据资料回答 / 5472 答不出来就说不知道 / 5517 标注来源
 * 画面：左「Prompt」卡（问句 + 证据 [1][2][3] + 三条规则打字机），中 LLMIcon「大模型」，右 答复卡（打字机 + 角标 8 帧淡入；闪烁整改：SC29 不在白名单，角标不再 glitch）。
 *      5342 问句与证据的副本沿箭头飞入大模型；末 14 帧 Prompt 卡 / 大模型 / 箭头加速下摇淡出，答复卡留给 SC30 承接。
 */
const F0 = 5314;
const B_GEN = 5322, B_FEED = 5342, B_RULE1 = 5407, B_RULE2 = 5472, B_RULE3 = 5517;
const T_EXIT = 5551;
const PCARD = {x: 110, y: 195, w: 380, h: 410};
const LLM = {cx: 620, cy: 400, size: 130};
export const ANS_SC29 = {x: 740, y: 310}; // 答复卡 420×180，中心 (950,400)；SC30 从此位置承接
const Q_PILL = {x: 150, y: 228, w: 300, h: 38};
const EVI_X = [150, 262, 374], EVI_Y = 285, EVI_W = 96, EVI_H = 62;
const RULES = ['① 只根据以下资料回答', '② 资料不足就回答：不知道', '③ 每句结论标注来源 [n]'];
const RULE_Y = [392, 452, 512];
const RULE_T0 = [B_RULE1, B_RULE2, B_RULE3];
const easeFly = easeInOutPow(2.5);

export const SC29: React.FC = () => {
  const N = useCurrentFrame() + F0;

  // ---- 离场（Prompt 卡 / LLM / 箭头）----
  const ne = N - T_EXIT;
  const exitDy = exitAccel(ne, 0.9);
  const exitOp = ne <= 0 ? 1 : Math.max(0, 1 - ne / 13);

  // ---- Prompt 卡入场 ----
  const np = N - (B_GEN - 4);
  const pDy = slideUp(np, 40);
  const pOp = fadeIn(np, 10);

  // ---- LLM ----
  const nl = N - B_GEN;
  const llmS = scaleIn(nl) * emphasisPulse(N - (B_FEED + 26), {peak: 1.12});
  const arrow1 = clamp01((N - (B_FEED - 2)) / 12);
  const arrow2 = clamp01((N - (B_RULE1 - 11)) / 12);

  // ---- 飞入副本：问句 + 3 张证据 ----
  const flyItems = [
    {cx: Q_PILL.x + Q_PILL.w / 2, cy: Q_PILL.y + Q_PILL.h / 2, w: Q_PILL.w, h: Q_PILL.h, kind: 'q' as const},
    ...EVI_X.map((x, i) => ({cx: x + EVI_W / 2, cy: EVI_Y + EVI_H / 2, w: EVI_W, h: EVI_H, kind: i as 0 | 1 | 2})),
  ];
  const flies = flyItems.map((it, i) => {
    const t = N - (B_FEED + 3 * i);
    if (t < 0 || t > 26) return null;
    const u = easeFly(clamp01(t / 24));
    const cx = it.cx + (LLM.cx - it.cx) * u, cy = it.cy + (LLM.cy - it.cy) * u;
    const s = 1 - 0.72 * u;
    const op = 1 - clamp01((u - 0.72) / 0.28);
    return (
      <div key={i} style={{...abs(cx - it.w / 2, cy - it.h / 2, it.w, it.h), transform: `scale(${s.toFixed(3)})`, transformOrigin: '50% 50%', opacity: op}}>
        {it.kind === 'q' ? <Pill x={0} y={0} w={it.w} h={it.h} text="差旅报销的上限是多少？" fontSize={22} weight={600} sw={2} /> : <EvidenceCard x={0} y={0} w={it.w} h={it.h} label={`[${it.kind + 1}]`} seed={it.kind + 3} />}
      </div>
    );
  });

  // ---- 答复卡 ----
  const na = N - (B_RULE1 - 6);
  const ansDy = slideUp(na, 120);
  const ansOp = fadeIn(na, 8);
  const T_TYPE = B_RULE1 + 9;
  const typed = typedCount(N, T_TYPE, ANS_TOTAL, 2);
  const typing = N >= T_TYPE && N < T_TYPE + 2 * ANS_TOTAL + 6;

  return (
    <div style={{position: 'absolute', inset: 0}}>
      {/* ===== 可离场组：Prompt 卡 + LLM + 箭头 ===== */}
      <div style={{position: 'absolute', inset: 0, transform: `translateY(${exitDy.toFixed(2)}px)`, opacity: exitOp}}>
        {np >= 0 ? (
          <div style={{position: 'absolute', inset: 0, transform: `translateY(${pDy.toFixed(2)}px)`, opacity: pOp}}>
            <Box x={PCARD.x} y={PCARD.y} w={PCARD.w} h={PCARD.h} r={12} sw={2} />
            {/* 标题 tab：Prompt */}
            <Box x={130} y={180} w={124} h={32} r={16} sw={2} />
            <TechText cx={192} cy={196} text="Prompt" fontSize={24} scaleX={0.9} weight={700} />
            {/* 问句 + 证据 */}
            <Pill x={Q_PILL.x} y={Q_PILL.y} w={Q_PILL.w} h={Q_PILL.h} text="差旅报销的上限是多少？" fontSize={22} weight={600} sw={2} />
            {EVI_X.map((x, i) => <EvidenceCard key={i} x={x} y={EVI_Y} w={EVI_W} h={EVI_H} label={`[${i + 1}]`} seed={i + 3} />)}
            <HLine x={130} y={368} w={340} />
            {/* 三条规则（打字机） */}
            {RULES.map((r, i) => <TypeLine key={i} x={140} y={RULE_Y[i] - 16} text={r} N={N} f0={RULE_T0[i]} />)}
          </div>
        ) : null}
        {/* LLM */}
        {nl >= 0 ? (
          <div style={{position: 'absolute', inset: 0, transform: `translate(${LLM.cx}px,${LLM.cy}px) scale(${llmS.toFixed(3)}) translate(${-LLM.cx}px,${-LLM.cy}px)`, transformOrigin: '0 0', opacity: fadeIn(nl, 6)}}>
            <LLMIcon cx={LLM.cx} cy={LLM.cy} size={LLM.size} label="大模型" labelSize={26} />
          </div>
        ) : null}
        {/* 箭头 */}
        <Svg>
          <LineArrow x0={PCARD.x + PCARD.w + 6} y0={LLM.cy} x1={LLM.cx - LLM.size / 2 - 6} y1={LLM.cy} p={arrow1} headL={16} headW={18} />
          <LineArrow x0={LLM.cx + LLM.size / 2 + 6} y0={LLM.cy} x1={ANS_SC29.x - 6} y1={LLM.cy} p={arrow2} headL={16} headW={18} />
        </Svg>
        {/* 飞入副本 */}
        {flies}
      </div>

      {/* ===== 答复卡（不离场，SC30 承接） ===== */}
      {na >= 0 ? (
        <div style={{position: 'absolute', inset: 0, transform: `translateY(${ansDy.toFixed(2)}px)`, opacity: ansOp}}>
          <AnswerCard x={ANS_SC29.x} y={ANS_SC29.y} typed={typed} citeShow={N >= B_RULE3} citeOp={citeOp(N, B_RULE3)} cursor={typing} />
        </div>
      ) : null}
    </div>
  );
};
