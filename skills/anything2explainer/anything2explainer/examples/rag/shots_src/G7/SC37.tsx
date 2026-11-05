import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {GlitchIn, slideIn, kf, clamp01, emphasisPulse, FONT_HEAVY, FONT_TECH, FONT_ORB} from '../../common';
import {Svg, Cross, Check, LineArrow, Pill, CText, TechText, LLMIcon, PURPLE, PURPLE_LIGHT, ORANGE, CORAL, GREEN, GREY, WHITE, fadeIn, scaleIn, abs, SoftIn} from '../../ui';
import {EASE, mixHex, exitOut} from './g7ui';

/**
 * SC37 Agentic RAG（6710–6990）
 * 6716 顶部「Agentic RAG」glitch；6720 中心 LLMIcon 缩放入场；6760 环上三节点（检索 / 评估够不够 / 改写问题）2 帧错峰缩放入场，
 * 6766「回答」出口节点；6772 起弧形箭头 draw-on，6784 评估→回答的灰虚线出口；6808 右侧轮次计数「第 N 轮」SoftIn 淡入（数字换位 6 帧淡入）；
 * 6810 起橙球沿环跑 3 圈（每圈 38 帧含停顿）：到「评估」停 8 帧闪红叉两次（6820/6858），第三次（6896）变绿勾，
 * 6904 沿出口滑到「回答」并停住，回答 Pill 变紫 + 脉冲；6879「Deep Research」紫 Pill SoftIn 淡入；6963「=」SoftIn + Deep Research 脉冲。闪烁整改：本镜头 glitch 只给「Agentic RAG」。
 * 设计偏离说明：分镜写「四节点同环」，但「回答」在环上会让球每圈都经过它，语义不通；改为三节点循环 + 「回答」作为评估通过后的出口分支。
 * QC v1：末 8 帧 exitOut（6982–6990 线性收 0 + 轻微下摇），避免组界 6991 从满画面切到空帧。
 */
const F0 = 6710, F1 = 6990;
const T_EXIT = F1 - 8;
const T_LABEL = 6716, T_ICON = 6720, T_NODES = 6760, T_ANS = 6766, T_ARCS = 6772, T_EXITARR = 6784, T_COUNTER = 6808, T_BALL = 6810, T_DR = 6879, T_EQ = 6963;
const C = {x: 600, y: 400}, R = 170;
const D2R = Math.PI / 180;
const P = (deg: number) => ({x: C.x + R * Math.cos(deg * D2R), y: C.y + R * Math.sin(deg * D2R)});
type RingNode = {name: string; deg: number; w: number; clear: number};
const RING: RingNode[] = [
  {name: '检索', deg: -90, w: 130, clear: 24},
  {name: '评估够不够', deg: 30, w: 170, clear: 31},
  {name: '改写问题', deg: 150, w: 150, clear: 28},
];
const ANS = {x: 980, y: 485, w: 130};
/** 球角度时间表（度，单调递增；在各节点前沿停顿） */
const BALL_KF: Array<[number, number]> = [
  [T_BALL, -117], [T_BALL + 2, -117], [6820, 3], [6828, 3], [6836, 123], [6840, 123], [6848, 243], [6850, 243],
  [6858, 363], [6866, 363], [6874, 483], [6878, 483], [6886, 603], [6888, 603], [6896, 723], [6904, 723],
];
const T_OUT = 6904, T_ARRIVE = 6918;
const HOLDS_EVAL = [6820, 6858];
const T_CHECK = 6896;
const ROUND_STARTS = [T_COUNTER, 6848, 6886];
const CROSS_POS = {cx: 850, cy: 425};

/** 环上弧形箭头（a→b 顺时针），p 为 draw-on 进度 */
const ArcArrow: React.FC<{a: number; b: number; p: number; color?: string}> = ({a, b, p, color = WHITE}) => {
  if (p <= 0) return null;
  const headDeg = (14 / R) / D2R;
  const bEnd = b - headDeg;
  const arcLen = ((bEnd - a) * D2R) * R;
  const A = P(a), B = P(bEnd);
  const large = bEnd - a > 180 ? 1 : 0;
  const tip = P(b), base = P(bEnd);
  const nx = Math.cos(bEnd * D2R), ny = Math.sin(bEnd * D2R);
  const hp = clamp01((p - 0.85) / 0.15);
  return (
    <g>
      <path d={`M${A.x},${A.y} A${R},${R} 0 ${large} 1 ${B.x},${B.y}`} fill="none" stroke={color} strokeWidth={3} strokeDasharray={arcLen} strokeDashoffset={arcLen * (1 - clamp01(p / 0.9))} strokeLinecap="butt" />
      {hp > 0 ? <polygon points={`${tip.x},${tip.y} ${base.x + nx * 9 * hp},${base.y + ny * 9 * hp} ${base.x - nx * 9 * hp},${base.y - ny * 9 * hp}`} fill={color} /> : null}
    </g>
  );
};

export const SC37: React.FC = () => {
  const N = useCurrentFrame() + F0;
  // 球位置
  const deg = kf(N, BALL_KF, EASE);
  const onRing = N < T_OUT;
  const outT = EASE(clamp01((N - T_OUT) / (T_ARRIVE - T_OUT)));
  const ringPos = P(deg);
  const ball = onRing ? ringPos : {x: ringPos.x + (ANS.x - ringPos.x) * outT, y: ringPos.y + (ANS.y - ringPos.y) * outT};
  const ballOp = fadeIn(N - T_BALL, 4);
  // 评估处红叉闪两次：停顿 +1..+3 亮、+4 灭、+5..+7 亮、+8 灭
  const crossOn = HOLDS_EVAL.some((h) => {
    const d = N - h;
    return (d >= 1 && d <= 3) || (d >= 5 && d <= 7);
  });
  const checkP = slideIn(N - T_CHECK - 1, 6, 2);
  const evalStroke = crossOn ? CORAL : checkP > 0 ? GREEN : WHITE;
  // 改写问题脉冲（球停在它前沿时）
  const rewritePulse = emphasisPulse(N - 6835, {peak: 1.1, up: 5, hold: 2, down: 6}) * emphasisPulse(N - 6873, {peak: 1.1, up: 5, hold: 2, down: 6});
  // 出口箭头：灰虚线 → 绿实线
  const exitP = slideIn(N - T_EXITARR, 14, 2);
  const exitGreen = clamp01((N - (T_CHECK + 4)) / 6);
  // 回答 Pill 变紫 + 脉冲
  const ansK = clamp01((N - T_ARRIVE) / 8);
  const ansPulse = emphasisPulse(N - T_ARRIVE, {peak: 1.12});
  // 轮次
  const round = N >= ROUND_STARTS[2] ? 3 : N >= ROUND_STARTS[1] ? 2 : 1;
  const drPulse = emphasisPulse(N - (T_EQ + 2), {peak: 1.1});
  const iconS = scaleIn(N - T_ICON);
  const ex = exitOut(N - T_EXIT, 8);
  return (
    <AbsoluteFill style={{pointerEvents: 'none', opacity: ex.op, transform: `translateY(${ex.dy.toFixed(2)}px)`}}>
      {/* 顶部标签行 */}
      <GlitchIn N={N} f0={T_LABEL}>
        <TechText cx={640} cy={160} text="Agentic RAG" fontSize={44} weight={700} scaleX={0.86} />
      </GlitchIn>
      <SoftIn N={N} f0={T_DR}>
        <div style={{...abs(915, 138, 250, 44), transform: `scale(${drPulse.toFixed(4)})`, transformOrigin: '50% 50%'}}>
          <Pill x={0} y={0} w={250} h={44} fill={PURPLE} sw={2} text="Deep Research" fontSize={26} weight={700} family={FONT_TECH} letterSpacing={1} textDy={-1} style={{fontStyle: 'italic', filter: 'drop-shadow(0 0 2px rgba(200,180,255,.6))'}} glow="0 0 24px 6px rgba(102,45,248,.45)" />
        </div>
      </SoftIn>
      <SoftIn N={N} f0={T_EQ}>
        <CText cx={840} cy={160} size={44} weight={700} color={WHITE} dy={-2} shadow="0 0 10px rgba(255,255,255,.5)">
          =
        </CText>
      </SoftIn>
      {/* 环底：弧形箭头 + 出口箭头 */}
      <Svg>
        {N >= T_NODES ? <circle cx={C.x} cy={C.y} r={R} fill="none" stroke={GREY} strokeWidth={1.2} strokeDasharray="4 8" opacity={0.28 * fadeIn(N - T_NODES, 12)} /> : null}
        {RING.map((nd, i) => {
          const nx = RING[(i + 1) % 3];
          const a = nd.deg + nd.clear;
          const b = (nx.deg < nd.deg ? nx.deg + 360 : nx.deg) - nx.clear;
          return <ArcArrow key={i} a={a} b={b} p={slideIn(N - (T_ARCS + 4 * i), 14, 2)} />;
        })}
        {exitP > 0 ? (
          <>
            <LineArrow x0={P(30).x + 92} y0={ANS.y} x1={ANS.x - ANS.w / 2 - 6} y1={ANS.y} p={exitP} rodW={2.5} headL={16} headW={16} color={GREY} dashed opacity={1 - exitGreen} />
            {exitGreen > 0 ? <LineArrow x0={P(30).x + 92} y0={ANS.y} x1={ANS.x - ANS.w / 2 - 6} y1={ANS.y} p={1} rodW={3} headL={16} headW={16} color={GREEN} opacity={exitGreen} /> : null}
          </>
        ) : null}
      </Svg>
      {/* 橙球（在节点之下，穿过节点时被遮） */}
      {N >= T_BALL ? <div style={{...abs(ball.x - 9, ball.y - 9, 18, 18), borderRadius: '50%', background: ORANGE, border: '2px solid #FFF', boxSizing: 'border-box', opacity: ballOp, boxShadow: '0 0 14px 4px rgba(240,95,65,.6)'}} /> : null}
      {/* 环上节点 */}
      {RING.map((nd, i) => {
        const n = N - (T_NODES + 2 * i);
        if (n < 0) return null;
        const pos = P(nd.deg);
        const s = scaleIn(n) * (i === 2 ? rewritePulse : 1);
        const stroke = i === 1 ? evalStroke : WHITE;
        return (
          <div key={nd.name} style={{...abs(pos.x - nd.w / 2, pos.y - 24, nd.w, 48), transform: `scale(${s.toFixed(4)})`, transformOrigin: '50% 50%', opacity: fadeIn(n, 6)}}>
            <Pill x={0} y={0} w={nd.w} h={48} fill="#000" stroke={stroke} sw={2} text={nd.name} fontSize={24} weight={700} textDy={-2} glow={stroke === CORAL ? '0 0 18px 4px rgba(241,96,67,.5)' : stroke === GREEN ? '0 0 18px 4px rgba(143,247,64,.4)' : undefined} style={{filter: 'drop-shadow(0 0 2px rgba(255,255,255,.35))'}} />
          </div>
        );
      })}
      {N >= T_ANS ? (
        <div style={{...abs(ANS.x - ANS.w / 2, ANS.y - 24, ANS.w, 48), transform: `scale(${(scaleIn(N - T_ANS) * ansPulse).toFixed(4)})`, transformOrigin: '50% 50%', opacity: fadeIn(N - T_ANS, 6)}}>
          <Pill x={0} y={0} w={ANS.w} h={48} fill={mixHex('#000000', PURPLE, ansK)} stroke={mixHex('#FFFFFF', PURPLE_LIGHT, ansK)} sw={2} text="回答" fontSize={24} weight={700} textDy={-2} glow={ansK > 0.02 ? `0 0 ${Math.round(26 * ansK)}px ${Math.round(8 * ansK)}px rgba(102,45,248,${(0.6 * ansK).toFixed(3)})` : undefined} style={{filter: 'drop-shadow(0 0 2px rgba(255,255,255,.35))'}} />
        </div>
      ) : null}
      {/* 中心大模型 */}
      {iconS > 0 ? (
        <div style={{position: 'absolute', inset: 0, transform: `scale(${iconS.toFixed(4)})`, transformOrigin: `${C.x}px ${C.y}px`, opacity: fadeIn(N - T_ICON, 8)}}>
          <LLMIcon cx={C.x} cy={C.y} size={110} />
        </div>
      ) : null}
      {/* 红叉 / 绿勾（评估结果） */}
      {crossOn || checkP > 0 ? (
        <Svg>
          {crossOn ? <Cross {...CROSS_POS} size={30} color={CORAL} sw={6} /> : null}
          {checkP > 0 ? <Check {...CROSS_POS} size={46} p={checkP} /> : null}
        </Svg>
      ) : null}
      {/* 轮次计数 */}
      <SoftIn N={N} f0={T_COUNTER}>
        <div style={{...abs(920, 270, 160, 60), display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, whiteSpace: 'nowrap', lineHeight: 1}}>
          <span style={{fontFamily: FONT_HEAVY, fontWeight: 700, fontSize: 26, color: WHITE}}>第</span>
          <span style={{display: 'inline-block', width: 40, textAlign: 'center'}} />
          <span style={{fontFamily: FONT_HEAVY, fontWeight: 700, fontSize: 26, color: WHITE}}>轮</span>
        </div>
        {[0, 1, 2].map((i) => (
          <div key={i} style={{...abs(982 + (i - 1) * 22 - 5, 338, 10, 10), borderRadius: '50%', background: round > i ? PURPLE_LIGHT : 'transparent', border: `1.5px solid ${round > i ? PURPLE_LIGHT : GREY}`, boxSizing: 'border-box', boxShadow: round > i ? '0 0 8px 2px rgba(161,117,241,.5)' : undefined}} />
        ))}
      </SoftIn>
      {N >= T_COUNTER ? (
        <SoftIn N={N} f0={ROUND_STARTS[round - 1]} len={6} dy={6}>
          <CText cx={1000} cy={300} size={46} weight={700} family={FONT_ORB} color={PURPLE_LIGHT} dy={0} shadow="0 0 14px rgba(102,45,248,.7)" style={{fontVariantNumeric: 'tabular-nums'}}>
            {round}
          </CText>
        </SoftIn>
      ) : null}
    </AbsoluteFill>
  );
};
