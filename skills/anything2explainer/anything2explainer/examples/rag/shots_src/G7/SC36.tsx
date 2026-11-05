import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {GlitchIn, slideIn, clamp01, rnd, emphasisPulse, FONT_HEAVY} from '../../common';
import {Svg, LineArrow, Pill, CText, TechText, Box, DocIcon, PURPLE, PURPLE_LIGHT, GREY, GREY_LIGHT, WHITE, slideUp, fadeIn, scaleIn, abs, SoftIn} from '../../ui';
import {exitOut} from './g7ui';

/**
 * SC36 GraphRAG（6451–6709）
 * 6451 左侧三张文档滑入；6457 顶部「GraphRAG」glitch + 6469 灰小字「Microsoft Research, 2024」；
 * 6496 文档→图谱箭头，6497 起 14 个节点按 rnd 顺序 1 帧错峰亮起，6508 起边 draw-on，6518 节点标签；
 * 6574 三个社区紫圆 2 帧错峰缩放入场 + 6580 三张「社区摘要」卡 SoftIn 淡入 + 6590 连线；
 * 6608 右侧问句 Pill 自右滑入 + 6618 三支箭头指向摘要卡；6677「全局问题」Pill SoftIn 淡入 + 脉冲（闪烁整改：本镜头 glitch 只给「GraphRAG」）；6696 起整体离场。
 */
const F0 = 6451;
const T_DOCS = 6451, T_LABEL = 6457, T_SUB = 6469, T_ARROW = 6496, T_NODES = 6497, T_EDGES = 6508, T_NLABEL = 6518;
const T_COMM = 6574, T_CARDS = 6580, T_CONN = 6590, T_Q = 6608, T_QARR = 6618, T_GLOBAL = 6677, T_EXIT = 6696;

type Node = {x: number; y: number; c: number; label?: string};
const NODES: Node[] = [
  // 社区 A
  {x: 370, y: 295, c: 0, label: '公司 A'}, {x: 320, y: 260, c: 0}, {x: 420, y: 255, c: 0}, {x: 325, y: 340, c: 0}, {x: 415, y: 340, c: 0},
  // 社区 B
  {x: 560, y: 295, c: 1, label: '产品 X'}, {x: 515, y: 255, c: 1}, {x: 610, y: 260, c: 1}, {x: 605, y: 340, c: 1}, {x: 520, y: 345, c: 1},
  // 社区 C
  {x: 465, y: 475, c: 2}, {x: 405, y: 505, c: 2}, {x: 525, y: 505, c: 2}, {x: 465, y: 545, c: 2},
];
const EDGES: Array<[number, number]> = [
  [0, 1], [0, 2], [0, 3], [0, 4], [1, 2], [3, 4],
  [5, 6], [5, 7], [5, 8], [5, 9], [7, 8],
  [10, 11], [10, 12], [10, 13], [11, 13], [12, 13],
  [0, 5], [4, 10], [9, 10],
];
const COOP_EDGE = 16; // [0,5] 「合作」
const COMM = [{cx: 370, cy: 298}, {cx: 562, cy: 298}, {cx: 465, cy: 508}];
const COMM_R = 76;
const CARD = {x: 660, w: 140, h: 64, cy: [300, 400, 500]};
const CONN: Array<[number, number, number, number]> = [
  [446, 298, CARD.x, 300],
  [616, 352, CARD.x, 392],
  [541, 508, CARD.x, 500],
];
const Q = {cx: 1030, cy: 400, w: 310, h: 52};
/** 节点亮起顺序（rnd 确定性洗牌 → 排名） */
const ORDER = NODES.map((_, i) => i).sort((a, b) => rnd(a, 36) - rnd(b, 36));
const RANK = NODES.map((_, i) => ORDER.indexOf(i));

export const SC36: React.FC = () => {
  const N = useCurrentFrame() + F0;
  const ex = exitOut(N - T_EXIT, 14);
  const nodeK = (i: number) => scaleIn(N - (T_NODES + RANK[i]), 10);
  const edgeP = (e: number) => slideIn(N - (T_EDGES + e), 14, 2);
  const labelOp = fadeIn(N - T_NLABEL, 10);
  const qn = N - T_Q;
  const qdx = qn < 0 ? 999 : 200 * Math.pow(1 - clamp01(qn / 22), 2.5);
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      <div style={{position: 'absolute', inset: 0, transform: `translateY(${ex.dy.toFixed(2)}px)`, opacity: ex.op}}>
        {/* 顶部标签 */}
        <GlitchIn N={N} f0={T_LABEL}>
          <TechText cx={640} cy={158} text="GraphRAG" fontSize={44} weight={700} scaleX={0.86} />
        </GlitchIn>
        <CText cx={640} cy={196} size={22} weight={500} color={GREY} opacity={fadeIn(N - T_SUB, 10)} letterSpacing={0.5}>
          Microsoft Research, 2024
        </CText>
        {/* 左：文档 */}
        {[0, 1, 2].map((i) => {
          const n = N - (T_DOCS + 2 * i);
          if (n < 0) return null;
          return <DocIcon key={i} x={100 + 30 * i} y={345 + 15 * i + slideUp(n, 200)} w={64} h={80} lines={4} opacity={fadeIn(n, 8)} />;
        })}
        {/* 社区圆（在节点之下） */}
        {COMM.map((c, i) => {
          const n = N - (T_COMM + 2 * i);
          if (n < 0) return null;
          const s = scaleIn(n);
          return (
            <div key={i} style={{...abs(c.cx - COMM_R, c.cy - COMM_R, 2 * COMM_R, 2 * COMM_R), borderRadius: '50%', transform: `scale(${s.toFixed(3)})`, opacity: fadeIn(n, 8), background: 'radial-gradient(circle, rgba(102,48,248,.34) 0%, rgba(102,48,248,.16) 55%, rgba(102,48,248,0) 74%)', border: '1.5px solid rgba(161,117,241,.6)', boxSizing: 'border-box'}} />
          );
        })}
        {/* 图谱 + 箭头 + 连线 */}
        <Svg>
          <LineArrow x0={238} y0={400} x1={298} y1={400} p={slideIn(N - T_ARROW, 14, 2)} rodW={3} headL={18} headW={20} />
          {EDGES.map(([a, b], e) => {
            const p = edgeP(e);
            if (p <= 0) return null;
            const A = NODES[a], B = NODES[b];
            const len = Math.hypot(B.x - A.x, B.y - A.y);
            return <line key={e} x1={A.x} y1={A.y} x2={B.x} y2={B.y} stroke={e === COOP_EDGE ? PURPLE_LIGHT : GREY} strokeWidth={e >= 16 ? 2 : 1.6} strokeDasharray={len} strokeDashoffset={len * (1 - p)} opacity={0.85} />;
          })}
          {NODES.map((nd, i) => {
            const k = nodeK(i);
            if (k <= 0) return null;
            return <circle key={i} cx={nd.x} cy={nd.y} r={9 * k} fill={nd.label ? PURPLE_LIGHT : WHITE} stroke={WHITE} strokeWidth={nd.label ? 2 : 0} />;
          })}
          {CONN.map(([x0, y0, x1, y1], i) => {
            const p = slideIn(N - (T_CONN + 3 * i), 12, 2);
            if (p <= 0) return null;
            return <line key={i} x1={x0} y1={y0} x2={x0 + (x1 - x0) * p} y2={y0 + (y1 - y0) * p} stroke={PURPLE_LIGHT} strokeWidth={1.5} strokeDasharray="5 5" opacity={0.75} />;
          })}
          {[0, 1, 2].map((i) => (
            <LineArrow key={i} x0={Q.cx - Q.w / 2 - 2} y0={Q.cy} x1={CARD.x + CARD.w + 8} y1={CARD.cy[i]} p={slideIn(N - (T_QARR + 3 * i), 14, 2)} rodW={2.5} headL={16} headW={16} color={PURPLE_LIGHT} />
          ))}
        </Svg>
        {/* 节点标签 */}
        {labelOp > 0
          ? NODES.filter((nd) => nd.label).map((nd) => (
              <CText key={nd.label} cx={nd.x} cy={nd.y - 26} size={23} weight={700} color={WHITE} opacity={labelOp} dy={-1} shadow="0 0 6px rgba(0,0,0,.95), 0 0 2px rgba(0,0,0,1)">
                {nd.label}
              </CText>
            ))
          : null}
        {labelOp > 0 ? (
          <CText cx={465} cy={276} size={22} weight={700} color={PURPLE_LIGHT} opacity={labelOp} dy={-1} shadow="0 0 6px rgba(0,0,0,.95)">
            合作
          </CText>
        ) : null}
        {/* 社区摘要卡 */}
        {[0, 1, 2].map((i) => (
          <SoftIn key={i} N={N} f0={T_CARDS + 4 * i}>
            <Box x={CARD.x} y={CARD.cy[i] - CARD.h / 2} w={CARD.w} h={CARD.h} r={8} sw={2} stroke={PURPLE_LIGHT} glow="0 0 14px 2px rgba(102,45,248,.35)">
              <div style={{position: 'absolute', left: 12, top: 10, fontFamily: FONT_HEAVY, fontSize: 19, fontWeight: 700, color: WHITE, lineHeight: 1, whiteSpace: 'nowrap'}}>社区摘要 {['①', '②', '③'][i]}</div>
              <div style={{position: 'absolute', left: 12, top: 38, width: 100, height: 3, background: GREY_LIGHT, opacity: 0.85}} />
              <div style={{position: 'absolute', left: 12, top: 48, width: 66, height: 3, background: GREY_LIGHT, opacity: 0.85}} />
            </Box>
          </SoftIn>
        ))}
        {/* 问句 */}
        {qn >= 0 ? (
          <Pill x={Q.cx - Q.w / 2 + qdx} y={Q.cy - Q.h / 2} w={Q.w} h={Q.h} fill="#000" sw={2} text="这批文档整体讲了什么？" fontSize={24} weight={700} textDy={-2} opacity={fadeIn(qn, 8)} style={{filter: 'drop-shadow(0 0 3px rgba(255,255,255,.35))'}} />
        ) : null}
        <SoftIn N={N} f0={T_GLOBAL}>
          <div style={{...abs(Q.cx - 75, 450, 150, 40), transform: `scale(${emphasisPulse(N - (T_GLOBAL + 4), {peak: 1.11}).toFixed(4)})`, transformOrigin: '50% 50%'}}>
            <Pill x={0} y={0} w={150} h={40} fill={PURPLE} sw={2} text="全局问题" fontSize={22} weight={700} textDy={-2} glow="0 0 24px 8px rgba(102,45,248,.6)" />
          </div>
        </SoftIn>
      </div>
    </AbsoluteFill>
  );
};
