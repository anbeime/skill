import React from 'react';
import {useCurrentFrame} from 'remotion';
import {GlitchIn, easeInOutPow, clamp01} from '../../common';
import {CText, Pill, Svg, scaleIn, fadeIn, PURPLE_LIGHT, SoftIn} from '../../ui';
import {AnswerCard, SourceCard, DrawPath, CITE_ANCHOR} from './ui';
import {ANS_SC29} from './SC29';

/**
 * SC30 可追溯 = 价值（5565–5696）
 * 节拍：5573 有引用可追溯 / 5631 RAG 真正的价值
 * 画面：答复卡自 SC29 位置 (740,310) 移到中央 (430,192)；角标 [1][2] 各拉一条紫色折线到下方两张来源卡
 *      （右「员工手册 p.12」← [1]，左「差旅补充规定 2025」← [2]）；5631 Pill「可追溯 · 可核查」+ 大字「RAG 的价值」。末 2 帧淡出。
 * QC v1：大字 cy 585→561（下缘 ≈581，距字幕带 56px）；Pill 508→486、来源卡 415→405、折线拐点 388→383 随之上移。
 */
const F0 = 5565;
const B_CITE = 5573, B_VALUE = 5631;
const TO = {x: 430, y: 192};
const SRC_W = 280, SRC_H = 70, SRC_Y = 405;
const SRC = [
  {x: 660, title: '员工手册 p.12', cite: 0, t0: B_CITE + 2}, // [1]
  {x: 340, title: '差旅补充规定 2025', cite: 1, t0: B_CITE + 4}, // [2]
];
const easeMove = easeInOutPow(2.5);

export const SC30: React.FC = () => {
  const N = useCurrentFrame() + F0;
  const opAll = N >= 5695 ? Math.max(0, 1 - (N - 5694) / 3) : 1;

  // ---- 答复卡移位（14 帧） ----
  const mv = easeMove(clamp01((N - F0) / 14));
  const ax = ANS_SC29.x + (TO.x - ANS_SC29.x) * mv;
  const ay = ANS_SC29.y + (TO.y - ANS_SC29.y) * mv;

  return (
    <div style={{position: 'absolute', inset: 0, opacity: opAll}}>
      <AnswerCard x={ax} y={ay} />

      {/* 引用折线 + 来源卡 */}
      <Svg bloom={false}>
        {SRC.map((s, i) => {
          const p = clamp01((N - s.t0) / 14);
          const [dx, dy] = CITE_ANCHOR[s.cite];
          const x0 = ax + dx, y0 = ay + dy + 12;
          const cx = s.x + SRC_W / 2;
          const yBend = 383 + i * 12;
          return <DrawPath key={i} pts={[[x0, y0], [x0, yBend], [cx, yBend], [cx, SRC_Y]]} p={p} color={PURPLE_LIGHT} sw={2.5} />;
        })}
      </Svg>
      {SRC.map((s, i) => {
        const n = N - (s.t0 + 8);
        if (n < 0) return null;
        const active = clamp01((N - (s.t0 + 14)) / 8);
        return <SourceCard key={i} x={s.x} y={SRC_Y} w={SRC_W} h={SRC_H} title={s.title} scale={scaleIn(n)} opacity={fadeIn(n, 6)} active={active} seed={i + 5} />;
      })}

      {/* 结论：可追溯 · 可核查（SoftIn）+ RAG 的价值 —— 本镜头唯一 glitch（白名单 §8；rgbSplit 仅限片头/SC08/SC35/SC44，此处去掉） */}
      <SoftIn N={N} f0={B_VALUE}>
        <Pill x={640 - 125} y={486} w={250} h={36} text="可追溯 · 可核查" fontSize={22} weight={700} sw={2} />
      </SoftIn>
      <GlitchIn N={N} f0={B_VALUE + 2}>
        <CText cx={640} cy={561} size={46} weight={900} scaleX={0.85} letterSpacing={1} dy={-3} shadow="0 0 14px rgba(102,45,248,.55)">RAG 的价值</CText>
      </GlitchIn>
    </div>
  );
};
