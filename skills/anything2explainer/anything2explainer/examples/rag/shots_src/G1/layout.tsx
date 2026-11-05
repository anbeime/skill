import React from 'react';
import {FONT_HEAVY, FONT_ORB, glitchOpacity, powOutRemain, clamp01, rnd} from '../../common';
import {LLMIcon, CText, Pill, PURPLE, PURPLE_LIGHT, GREY, WHITE, fadeIn, scaleIn, abs} from '../../ui';

/**
 * G1 第 1 章上半（SC01–SC04）共用布局：左侧 LLMIcon + 右侧三个虚线框（①②③）。
 * 所有状态是绝对帧号 N 的纯函数，四个镜头共用同一份代码 → 镜头边界零跳变。
 */
export const LLM = {cx: 400, cy: 360, size: 170};
export const BOX_W = 440;
export const BOX_H = 100;
export const BOXES = [
  {x: 720, y: 200},
  {x: 720, y: 340},
  {x: 720, y: 480},
];
/** 三框自右滑入起始帧（S01「三个短板」字幕块 116） */
export const BOX_IN = 116;
/** 三框依次成为焦点的帧（S02 176 / S03 311 / S04 454） */
export const ACT_AT = [176, 311, 454];
export const LLM_IN = 84; // LLMIcon 21 帧缩放入场起始（字幕 86 −2）

const hex2rgb = (h: string) => [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)];
/** 颜色线性混合 a→b，k∈[0,1] */
export const mixHex = (a: string, b: string, k: number) => {
  const A = hex2rgb(a), B = hex2rgb(b);
  const c = A.map((v, i) => Math.round(v + (B[i] - v) * clamp01(k)));
  return `rgb(${c[0]},${c[1]},${c[2]})`;
};
/** 框 i 的"已成为过去"程度：下一框激活起 11 帧 0→1 */
export const boxPast = (i: number, N: number) => (ACT_AT[i + 1] === undefined ? 0 : clamp01((N - ACT_AT[i + 1]) / 11));
/** 框 i 的"紫色焦点"程度：激活起 11 帧 0→1，下一框激活起 11 帧回落 0 */
export const boxAct = (i: number, N: number) => clamp01((N - ACT_AT[i]) / 11) * (1 - boxPast(i, N));
/** 过去内容的整体透明度（1 → 0.5） */
export const pastOpacity = (i: number, N: number) => 1 - 0.5 * boxPast(i, N);

/** 四角小星（「很聪明」冒星），r = 外半径 */
export const Sparkle: React.FC<{cx: number; cy: number; r: number; opacity?: number; color?: string}> = ({cx, cy, r, opacity = 1, color = WHITE}) => {
  const k = 0.28;
  const d = `M0,${-r} C0,${-r * k} ${r * k},0 ${r},0 C${r * k},0 0,${r * k} 0,${r} C0,${r * k} ${-r * k},0 ${-r},0 C${-r * k},0 0,${-r * k} 0,${-r} Z`;
  return (
    <svg width={r * 2 + 8} height={r * 2 + 8} viewBox={`${-r - 4} ${-r - 4} ${r * 2 + 8} ${r * 2 + 8}`} style={{position: 'absolute', left: cx - r - 4, top: cy - r - 4, opacity, overflow: 'visible'}}>
      <path d={d} fill={color} />
    </svg>
  );
};

/** LLM 图标（缩放入场 + 紫柔光脉冲 + SC01 三颗小星）。accent 为神经元颜色、haloK 为柔光强度 0–1（SC02 275 闪灰 / 熄灭用） */
export const LLMBlock: React.FC<{N: number; accent?: string; label?: string; haloK?: number}> = ({N, accent = PURPLE, label = '大模型', haloK = 1}) => {
  const n = N - LLM_IN;
  if (n < 0) return null;
  const s = scaleIn(n, 21);
  // 柔光脉冲：入场完成后 100–134 帧一次呼吸（外圈 halo 透明度 0→1→0.35 常亮）
  const ph = N < 100 ? 0 : N < 114 ? clamp01((N - 100) / 14) : N < 118 ? 1 : 0.35 + 0.65 * clamp01(1 - (N - 118) / 16);
  const halo = `0 0 ${Math.round(28 + 26 * ph)}px ${Math.round(8 + 10 * ph)}px rgba(102,45,248,${(0.35 + 0.4 * ph).toFixed(2)})`;
  const half = LLM.size / 2;
  return (
    <div style={{...abs(0, 0, 1280, 720), transformOrigin: `${LLM.cx}px ${LLM.cy}px`, transform: s < 1 ? `scale(${s.toFixed(3)})` : undefined, opacity: clamp01(0.15 + 1.4 * s)}}>
      <div style={{...abs(LLM.cx - half, LLM.cy - half, LLM.size, LLM.size), borderRadius: LLM.size * 0.16, boxShadow: halo, opacity: haloK}} />
      <LLMIcon cx={LLM.cx} cy={LLM.cy} size={LLM.size} accent={accent} label={label} labelSize={28} glow={false} />
      {/* 「很聪明」：三颗小星 96/100/104 起 8 帧淡入，156–166 淡出（SC02 起不再出现） */}
      {[0, 1, 2].map((i) => {
        const f0 = 96 + 4 * i;
        const k = N - f0;
        if (k < 0) return null;
        const sx = LLM.cx - 84 + rnd(31, i) * 168;
        const sy = LLM.cy - half - 22 - rnd(32, i) * 46;
        const r = 9 + rnd(33, i) * 6;
        const grow = 0.4 + 0.6 * (1 - powOutRemain(k, 10, 2.5));
        const tw = 1 + 0.12 * Math.sin((N + i * 7) * 0.5);
        const op = fadeIn(k, 8) * (1 - clamp01((N - 156) / 10));
        if (op <= 0) return null;
        return <Sparkle key={i} cx={sx} cy={sy} r={r * grow * tw} opacity={op} />;
      })}
    </div>
  );
};

/** 虚线框 i（含编号徽章）：116+2i 自右滑入 Δ300；编号徽章滑入完成后（n 12 起）8 帧淡入（闪烁整改：原 glitchOpacity）；边框灰→紫随 boxAct；过去后回灰 */
export const DashedBox: React.FC<{i: number; N: number}> = ({i, N}) => {
  const n = N - (BOX_IN + 2 * i);
  if (n < 0) return null;
  const b = BOXES[i];
  const dx = 300 * powOutRemain(n, 22, 2.5);
  const x = b.x + dx;
  const act = boxAct(i, N);
  const stroke = mixHex(GREY, PURPLE_LIGHT, act);
  const op = fadeIn(n, 8);
  const badgeOp = fadeIn(n - 12, 8);
  return (
    <div style={{opacity: op}}>
      <div style={{...abs(x, b.y, BOX_W, BOX_H), boxSizing: 'border-box', border: `2px dashed ${stroke}`, borderRadius: 6, background: 'rgba(0,0,0,0.42)', boxShadow: act > 0 ? `0 0 18px 4px rgba(102,45,248,${(0.45 * act).toFixed(2)})` : undefined}} />
      {/* 编号徽章：框左上角，Orbitron 数字 */}
      <div style={{...abs(x - 17, b.y - 17, 34, 34), boxSizing: 'border-box', borderRadius: 17, background: '#000', border: `2px solid ${stroke}`, opacity: badgeOp}}>
        <CText cx={17} cy={17} size={22} weight={700} family={FONT_ORB} color={mixHex(GREY, WHITE, act)} dy={-1}>
          {String(i + 1)}
        </CText>
      </div>
    </div>
  );
};

/**
 * 框标题胶囊（骑在框顶边上）：默认 f0 起自下滑入 Δ40 + 8 帧淡入；填色随 k（0 灰 → 1 紫）。
 * glitch=true → 12 帧 GlitchIn 模板（纯透明度序列、定点不滑）。闪烁白名单（协议 §8）：只有 SC02「知识截止」/ SC03「读不到私有数据」显式开。
 */
export const LabelTab: React.FC<{N: number; f0: number; i: number; text: string; w: number; glitch?: boolean}> = ({N, f0, i, text, w, glitch = false}) => {
  const n = N - f0;
  if (n < 0) return null;
  const b = BOXES[i];
  const k = boxAct(i, N);
  const dy = glitch ? 0 : 40 * powOutRemain(n, 16, 2.5);
  const op = glitch ? glitchOpacity(n) : fadeIn(n, 8);
  if (op <= 0) return null;
  return (
    <div style={{opacity: op}}>
      <Pill x={b.x + 30} y={b.y - 17 + dy} w={w} h={34} fill={mixHex('#3A3A3A', PURPLE, k)} sw={2} text={text} fontSize={24} weight={700} family={FONT_HEAVY} textDy={-2} />
    </div>
  );
};

/** 场景骨架：LLM + 三个虚线框 */
export const Scene1Frame: React.FC<{N: number; accent?: string; haloK?: number}> = ({N, accent, haloK}) => (
  <>
    <LLMBlock N={N} accent={accent} haloK={haloK} />
    {[0, 1, 2].map((i) => <DashedBox key={i} i={i} N={N} />)}
  </>
);
