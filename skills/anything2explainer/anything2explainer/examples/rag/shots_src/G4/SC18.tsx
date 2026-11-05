import React from 'react';
import {useCurrentFrame} from 'remotion';
import {GlitchIn, rnd, kf, emphasisPulse, easeOutCubic, clamp01, FONT_ORB} from '../../common';
import {CText, TechText, Pill, Svg, LineArrow, Cross, PURPLE, PURPLE_LIGHT, ORANGE, WHITE, GREY, GREY_LINE, GREY_LIGHT, TEXT_GLOW, fadeIn, slideUp, scaleIn, exitAccel, abs, SoftIn} from '../../ui';

/**
 * SC18 第四步 建索引 HNSW（3034–3298）
 * 节拍：3042 第四步建索引（左：12 点竖列 + 「线性扫描」Pill 3044 自左滑入）→ 3073 上亿个向量不能一个个比（Orbitron「1 0000 0000 ×」，
 *      扫描光标下扫两遍 → 红 Cross）→ 3130 HNSW 近似最近邻（三层平行四边形平面 2 帧错峰自下 Δ80 滑入（QC v1：原 Δ300 穿字幕带），点阵亮起，图边淡入）→
 *      3219 线性扫描→几十次跳转（橙色查询路径 22 跳 + 2 次下降逐段 draw-on，3219–3269；目标点紫脉冲，「跳转 ×N」计数终值 22）→ 3291 起 8 帧离场。
 * 依据 research §2.6：HNSW 多层可导航小世界图，上层稀疏快速定位、下层稠密精确逼近，查询复杂度对数级。
 */
export const F0 = 3034;
const B_COL = 3042, B_BIG = 3073, B_SCAN = 3076, B_CROSS = 3117, B_DIM = 3128, B_HNSW = 3130, B_PATH = 3219, EXIT = 3291;

// ---- 左：线性扫描 ----
const LX = 360;
const DOTS = Array.from({length: 12}, (_, i) => 225 + i * 30);
const SCAN: Array<[number, number]> = [[B_SCAN, DOTS[0]], [B_SCAN + 18, DOTS[11]], [B_SCAN + 21, DOTS[0]], [B_SCAN + 39, DOTS[11]]];

// ---- 右：HNSW 三层 ----
const HX = 860, HW = 150, HH = 30, SKEW = 28;
const LAYER_Y = [275, 395, 515];
const LAYER_T0 = [B_HNSW + 4, B_HNSW + 2, B_HNSW]; // 顶/中/底：底层先入
type UV = [number, number];
/** 查询路径节点：顶层 4 跳 / 中层 7 跳 / 底层 11 跳（自左向右漂移 + 底层绕目标螺旋收敛），共 22 跳 + 2 次层间下降 */
const PATH_NODES: UV[][] = [
  [[0.06, 0.30], [0.20, 0.72], [0.34, 0.28], [0.46, 0.66], [0.56, 0.36]],
  [[0.56, 0.36], [0.62, 0.78], [0.70, 0.22], [0.78, 0.60], [0.84, 0.26], [0.90, 0.70], [0.78, 0.86], [0.74, 0.48]],
  [[0.74, 0.48], [0.64, 0.18], [0.60, 0.62], [0.66, 0.86], [0.80, 0.80], [0.92, 0.88], [0.96, 0.56], [0.96, 0.22], [0.82, 0.14], [0.68, 0.30], [0.76, 0.66], [0.86, 0.48]],
];
const COUNTS = [8, 14, 26];
const toXY = (L: number, [u, v]: UV) => ({x: HX - HW - SKEW + 2 * HW * u + 2 * SKEW * v, y: LAYER_Y[L] + HH - 2 * HH * v});
/** 每层点：路径节点在前，其余 rnd 拒绝采样填充；order 为亮起顺序 */
const LAYER_PTS = COUNTS.map((c, L) => {
  const uv: UV[] = [...PATH_NODES[L]];
  for (let i = uv.length, k = 0; i < c && k < 400; k++) {
    const cand: UV = [0.06 + 0.88 * rnd(18, L, i, k, 1), 0.12 + 0.76 * rnd(18, L, i, k, 2)];
    const p = toXY(L, cand);
    if (uv.some((q) => Math.hypot(toXY(L, q).x - p.x, toXY(L, q).y - p.y) < 20)) continue;
    uv.push(cand);
    i++;
  }
  const idx = uv.map((_, i) => i).sort((a, b) => rnd(18, L, a, 77) - rnd(18, L, b, 77));
  const order = new Array<number>(uv.length);
  idx.forEach((i, o) => (order[i] = o));
  return uv.map((q, i) => ({...toXY(L, q), order: order[i]}));
});
/** 层内图边：每点连最近 2 点（去重） */
const LAYER_EDGES = LAYER_PTS.map((pts) => {
  const set = new Set<string>();
  const out: Array<[number, number]> = [];
  pts.forEach((p, i) => {
    const near = pts.map((q, j) => ({j, d: Math.hypot(q.x - p.x, q.y - p.y)})).filter((o) => o.j !== i).sort((a, b) => a.d - b.d).slice(0, 2);
    near.forEach(({j}) => {
      const key = i < j ? `${i}-${j}` : `${j}-${i}`;
      if (!set.has(key)) {
        set.add(key);
        out.push([Math.min(i, j), Math.max(i, j)]);
      }
    });
  });
  return out;
});
/** 查询路径段：{from,to,desc} 以 (layer,index) 表示；跳 2 帧、下降 3 帧 */
type Seg = {a: [number, number]; b: [number, number]; desc: boolean; t0: number; dur: number};
const SEGS: Seg[] = (() => {
  const out: Seg[] = [];
  let t = B_PATH;
  for (let L = 0; L < 3; L++) {
    for (let i = 0; i < PATH_NODES[L].length - 1; i++) {
      out.push({a: [L, i], b: [L, i + 1], desc: false, t0: t, dur: 2});
      t += 2;
    }
    if (L < 2) {
      out.push({a: [L, PATH_NODES[L].length - 1], b: [L + 1, 0], desc: true, t0: t, dur: 3});
      t += 3;
    }
  }
  return out;
})();
const PATH_END = SEGS[SEGS.length - 1].t0 + SEGS[SEGS.length - 1].dur;
const TARGET = LAYER_PTS[2][PATH_NODES[2].length - 1];

const planePts = (L: number) => {
  const y = LAYER_Y[L];
  return `${HX - HW + SKEW},${y - HH} ${HX + HW + SKEW},${y - HH} ${HX + HW - SKEW},${y + HH} ${HX - HW - SKEW},${y + HH}`;
};

export const SC18: React.FC = () => {
  const N = useCurrentFrame() + F0;
  const ne = N - EXIT;
  const exitOp = ne <= 0 ? 1 : Math.max(0, 1 - ne / 8);
  const exitDy = exitAccel(ne, 0.5);
  if (N < B_COL) return null;

  // 左列
  const scanY = kf(N, SCAN);
  const scanning = N >= B_SCAN && N <= B_SCAN + 39;
  const dimK = clamp01((N - B_DIM) / 10); // Cross 后整列压暗到 .45
  const colOp = 1 - 0.55 * dimK;
  const pCross = easeOutCubic((N - B_CROSS) / 10);

  // 路径
  const segCount = SEGS.filter((s) => !s.desc && N >= s.t0 + s.dur).length; // 只计跳转，不计层间下降（终值 22）
  const nodeReached = (L: number, i: number) => SEGS.some((s) => s.b[0] === L && s.b[1] === i && N >= s.t0 + s.dur) || (L === 0 && i === 0 && N >= B_PATH);
  const tPulse = emphasisPulse(N - (PATH_END + 2), {peak: 1.6, up: 8, hold: 3, down: 12});

  return (
    <div style={{position: 'absolute', inset: 0, opacity: exitOp, transform: `translateY(${exitDy.toFixed(2)}px)`}}>
      {/* ---- 左：线性扫描 ---- */}
      <div style={{position: 'absolute', inset: 0, opacity: colOp}}>
        <Svg>
          {DOTS.map((y, i) => {
            const s = scaleIn(N - (B_COL + i), 10);
            if (s <= 0) return null;
            const hit = scanning && Math.abs(y - scanY) < 16;
            return <circle key={i} cx={LX} cy={y} r={(hit ? 7 : 5.5) * s} fill={hit ? WHITE : GREY_LIGHT} opacity={hit ? 1 : 0.85} />;
          })}
          {scanning ? (
            <g style={{filter: 'drop-shadow(0 0 5px rgba(255,255,255,.9))'}}>
              <rect x={LX - 44} y={scanY - 2} width={88} height={4} rx={2} fill={WHITE} opacity={0.95} />
            </g>
          ) : null}
        </Svg>
        {N >= B_COL + 2 ? (
          <div style={{position: 'absolute', inset: 0, opacity: fadeIn(N - (B_COL + 2), 6), transform: `translateX(${(-slideUp(N - (B_COL + 2), 320, 18)).toFixed(2)}px)`}}>
            <Pill x={LX - 75} y={575} w={150} h={38} text="线性扫描" fontSize={26} weight={700} textDy={-2} />
          </div>
        ) : null}
        <SoftIn N={N} f0={B_BIG}>
          <CText cx={LX} cy={198} size={24} weight={600} family={FONT_ORB} color={WHITE} letterSpacing={1} shadow={TEXT_GLOW} dy={0}>1 0000 0000 ×</CText>
        </SoftIn>
      </div>
      {pCross > 0 ? (
        <Svg>
          <Cross cx={LX} cy={390} size={64} p={pCross} sw={7} opacity={0.95} />
        </Svg>
      ) : null}

      {/* ---- 右：HNSW 三层 ---- */}
      {LAYER_Y.map((_, L) => {
        const n = N - LAYER_T0[L];
        if (n < 0) return null;
        const pts = LAYER_PTS[L];
        const litAll = LAYER_T0[L] + 16 + pts.length;
        const edgeOp = 0.6 * fadeIn(N - (litAll + 2), 10);
        return (
          <div key={L} style={{position: 'absolute', inset: 0, opacity: fadeIn(n, 10), transform: `translateY(${slideUp(n, 80).toFixed(2)}px)`}}>
            <Svg>
              <polygon points={planePts(L)} fill="#000" stroke={WHITE} strokeWidth={2} strokeLinejoin="round" />
              {edgeOp > 0 ? LAYER_EDGES[L].map(([a, b], k) => <line key={k} x1={pts[a].x} y1={pts[a].y} x2={pts[b].x} y2={pts[b].y} stroke={GREY_LINE} strokeWidth={1.2} opacity={edgeOp} />) : null}
              {pts.map((p, i) => {
                const s = scaleIn(N - (LAYER_T0[L] + 16 + p.order), 8);
                if (s <= 0) return null;
                const onPath = i < PATH_NODES[L].length && nodeReached(L, i);
                const isTarget = L === 2 && i === PATH_NODES[2].length - 1;
                const r = isTarget && N >= PATH_END ? 5 * tPulse : onPath ? 5 : 4;
                return <circle key={i} cx={p.x} cy={p.y} r={r * s} fill={isTarget && N >= PATH_END ? PURPLE : onPath ? ORANGE : GREY_LIGHT} stroke={isTarget && N >= PATH_END ? WHITE : 'none'} strokeWidth={1.5} opacity={0.95} />;
              })}
            </Svg>
          </div>
        );
      })}
      {/* 查询路径（橙）：屏幕空间，不随平面滑入 */}
      {N >= B_PATH ? (
        <Svg>
          {SEGS.map((s, k) => {
            const p = clamp01((N - s.t0) / s.dur);
            if (p <= 0) return null;
            const A = LAYER_PTS[s.a[0]][s.a[1]], B = LAYER_PTS[s.b[0]][s.b[1]];
            return <LineArrow key={k} x0={A.x} y0={A.y} x1={B.x} y1={B.y} p={p} color={ORANGE} rodW={2.5} headL={s.desc ? 9 : 11} headW={s.desc ? 9 : 11} dashed={s.desc} />;
          })}
          {N >= PATH_END ? <circle cx={TARGET.x} cy={TARGET.y} r={11 * tPulse} fill="none" stroke={PURPLE_LIGHT} strokeWidth={2} opacity={0.8} /> : null}
        </Svg>
      ) : null}
      {/* 标签 */}
      <GlitchIn N={N} f0={B_HNSW + 6}>
        <TechText cx={792} cy={200} text="HNSW" fontSize={38} scaleX={0.86} weight={800} />
        <TechText cx={968} cy={203} text="Hierarchical NSW" fontSize={26} scaleX={0.86} color={PURPLE_LIGHT} weight={600} glow={false} />
      </GlitchIn>
      {/* 跳转计数 */}
      <SoftIn N={N} f0={B_PATH}>
        <CText cx={1118} cy={372} size={24} weight={600} color={GREY_LIGHT}>跳转</CText>
        <div style={{...abs(1058, 392, 120, 40), display: 'flex', justifyContent: 'center', alignItems: 'center', fontFamily: FONT_ORB, fontWeight: 700, fontSize: 32, color: ORANGE, letterSpacing: 1, textShadow: '0 0 10px rgba(240,95,65,.6)', fontVariantNumeric: 'tabular-nums', whiteSpace: 'nowrap'}}>
          ×{segCount}
        </div>
      </SoftIn>
    </div>
  );
};
