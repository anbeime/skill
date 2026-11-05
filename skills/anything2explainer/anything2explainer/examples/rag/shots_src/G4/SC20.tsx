import React from 'react';
import {useCurrentFrame} from 'remotion';
import {easeOutCubic, clamp01, powOutRemain, FONT_ORB} from '../../common';
import {CText, Pill, Svg, LineArrow, DocIcon, DBIcon, ChunkCard, PURPLE, PURPLE_LIGHT, CORAL, WHITE, GREY, GREY_LIGHT, fadeIn, scaleIn, exitAccel, abs, SoftIn} from '../../ui';

/**
 * SC20 增量更新（3483–3662）
 * 节拍：3491 文档会变（DocIcon + 「v1」角标缩放入场；3505 角标 scaleX 翻页 8 帧 → 「v2」紫，文档内两行改动变紫；
 *      右侧 DBIcon 同步入场）→ 3531 增量更新（两支白箭头 draw-on，紫色循环双弧箭头 draw-on 18 帧后每帧 2° 旋转，
 *      「增量更新」紫 Pill 淡入）→ 3582 过期的故事（库内灰卡「过期」+ 珊瑚色删除线 wipe → 3606 灰卡落下淡出，
 *      3612 新紫卡「v2」自上落入）→ 3661–3662 整组快速淡出接章节卡。
 * 依据 research §2.8：doc_id + 内容哈希跟踪，变更只重嵌入受影响的块（LlamaIndex refresh_ref_docs）。
 */
export const F0 = 3483;
const B_DOC = 3491, B_FLIP = 3505, B_LOOP = 3531, B_STALE = 3582, B_STRIKE = 3590, B_DROP = 3606, B_NEW = 3612, EXIT = 3655; // QC v2 复验 N2：与 HUD/流程轨同起点 3655 淡出，末帧 3662 归零

const DOC = {x: 235, y: 300, w: 130, h: 160};
const LOOP = {cx: 640, cy: 380, r: 58};
const DB = {cx: 960, cy: 380, w: 150, h: 170};
const STALE = {x: 900, y: 362, w: 120, h: 70};
const ARC_DEG = 140;
const ARC_LEN = (LOOP.r * Math.PI * ARC_DEG) / 180;

const polar = (deg: number, r = LOOP.r) => ({x: LOOP.cx + r * Math.cos((deg * Math.PI) / 180), y: LOOP.cy + r * Math.sin((deg * Math.PI) / 180)});
/** 一段顺时针弧 + 末端箭头（p 为 draw-on 进度） */
const ArcArrow: React.FC<{start: number; p: number}> = ({start, p}) => {
  const a0 = polar(start);
  const a1 = polar(start + ARC_DEG);
  const tip = polar(start + ARC_DEG + 12, LOOP.r);
  const inner = polar(start + ARC_DEG, LOOP.r - 11);
  const outer = polar(start + ARC_DEG, LOOP.r + 11);
  return (
    <g stroke={PURPLE_LIGHT} fill="none">
      <path d={`M${a0.x},${a0.y} A${LOOP.r},${LOOP.r} 0 0 1 ${a1.x},${a1.y}`} strokeWidth={4} strokeLinecap="round" strokeDasharray={ARC_LEN} strokeDashoffset={ARC_LEN * (1 - clamp01(p))} />
      {p >= 0.98 ? <polygon points={`${tip.x},${tip.y} ${inner.x},${inner.y} ${outer.x},${outer.y}`} fill={PURPLE_LIGHT} stroke="none" /> : null}
    </g>
  );
};

/** DocIcon 内第 i 行文本线的相对 y（复刻 ui.tsx DocIcon 的排布公式） */
const docLineY = (i: number, lines: number) => {
  const f = DOC.w * 0.3;
  return f + 12 + i * ((DOC.h - f - 22) / Math.max(1, lines - 1 + 0.6));
};

export const SC20: React.FC = () => {
  const N = useCurrentFrame() + F0;
  // 末 2 帧整组快速淡出（3663 章节卡 glitch 入）
  const ne = N - EXIT;
  const exitOp = ne < 0 ? 1 : 1 - Math.pow(Math.min(1, ne / 7), 1.5); // 3655–3662 八帧归零
  const exitDy = Math.min(12, exitAccel(ne, 0.25));
  if (N < B_DOC) return null;

  const sDoc = scaleIn(N - B_DOC);
  const sDb = scaleIn(N - (B_DOC + 4));
  // 版本角标翻页：|cos| 8 帧，中点换字/换色
  const nf = N - B_FLIP;
  const flipK = nf < 0 ? 0 : Math.min(1, nf / 8);
  const flipSx = nf < 0 || nf >= 8 ? 1 : Math.abs(Math.cos(Math.PI * flipK));
  const isV2 = nf >= 4;
  // 文档内改动的两行（紫）
  const chg = [easeOutCubic((N - (B_FLIP + 6)) / 8), easeOutCubic((N - (B_FLIP + 9)) / 8)];

  // 箭头 + 循环
  const pA1 = easeOutCubic((N - B_LOOP) / 14);
  const pA2 = easeOutCubic((N - (B_LOOP + 4)) / 14);
  const pArc = easeOutCubic((N - (B_LOOP + 6)) / 18);
  const rot = Math.max(0, N - (B_LOOP + 24)) * 2;

  // 过期卡 / 新卡
  const nStale = N - B_STALE;
  const sStale = scaleIn(nStale, 14);
  const pStrike = easeOutCubic((N - B_STRIKE) / 8);
  const nDrop = N - B_DROP;
  const dropDy = exitAccel(nDrop, 0.9);
  const dropOp = nDrop <= 0 ? 1 : Math.max(0, 1 - nDrop / 10);
  const nNew = N - B_NEW;
  const newDy = -220 * powOutRemain(nNew, 18, 2.5);
  const newOp = fadeIn(nNew, 8);

  return (
    <div style={{position: 'absolute', inset: 0, opacity: exitOp, transform: `translateY(${exitDy.toFixed(2)}px)`}}>
      {/* 左：文档 + 版本角标 */}
      {sDoc > 0 ? (
        <div style={{position: 'absolute', inset: 0, transform: `translate(${DOC.x + DOC.w / 2}px, ${DOC.y + DOC.h / 2}px) scale(${sDoc.toFixed(4)}) translate(${-(DOC.x + DOC.w / 2)}px, ${-(DOC.y + DOC.h / 2)}px)`, transformOrigin: '0 0'}}>
          <DocIcon x={DOC.x} y={DOC.y} w={DOC.w} h={DOC.h} lines={6} sw={2.5} label="差旅补充规定" labelSize={24} />
          {/* 改动的两行（覆盖原灰白线） */}
          {[2, 3].map((li, k) => {
            const w = 0.72 * DOC.w * clamp01(chg[k]);
            if (w <= 0) return null;
            return <div key={li} style={{...abs(DOC.x + DOC.w * 0.14, DOC.y + docLineY(li, 6), w, 3), background: PURPLE_LIGHT, boxShadow: '0 0 6px rgba(161,117,241,.8)'}} />;
          })}
          {/* 版本角标（Orbitron），翻页换 v2 */}
          <div style={{...abs(DOC.x + DOC.w - 34, DOC.y - 16, 68, 32), transform: `scaleX(${flipSx.toFixed(4)})`, transformOrigin: '50% 50%'}}>
            <Pill x={0} y={0} w={68} h={32} text={isV2 ? 'v2' : 'v1'} fontSize={22} weight={700} family={FONT_ORB} fill={isV2 ? PURPLE : '#000'} stroke={WHITE} sw={2} textDy={0} letterSpacing={1} glow={isV2 ? '0 0 14px 4px rgba(102,45,248,.5)' : undefined} />
          </div>
        </div>
      ) : null}

      {/* 中：白箭头 + 紫色循环箭头 */}
      <Svg>
        {pA1 > 0 ? <LineArrow x0={DOC.x + DOC.w + 14} y0={LOOP.cy} x1={LOOP.cx - LOOP.r - 26} y1={LOOP.cy} p={pA1} /> : null}
        {pA2 > 0 ? <LineArrow x0={LOOP.cx + LOOP.r + 26} y0={LOOP.cy} x1={DB.cx - DB.w / 2 - 14} y1={LOOP.cy} p={pA2} /> : null}
        {pArc > 0 ? (
          <g transform={`rotate(${rot.toFixed(1)} ${LOOP.cx} ${LOOP.cy})`} style={{filter: 'drop-shadow(0 0 6px rgba(102,45,248,.8))'}}>
            <ArcArrow start={-160} p={pArc} />
            <ArcArrow start={20} p={pArc} />
          </g>
        ) : null}
      </Svg>
      <SoftIn N={N} f0={B_LOOP + 8}>
        <Pill x={LOOP.cx - 80} y={LOOP.cy + LOOP.r + 30} w={160} h={42} text="增量更新" fontSize={28} weight={700} fill={PURPLE} sw={2} textDy={-2} glow="0 0 16px 5px rgba(102,45,248,.45)" />
      </SoftIn>

      {/* 右：知识库 + 库内卡片 */}
      {sDb > 0 ? (
        <div style={{position: 'absolute', inset: 0, transform: `translate(${DB.cx}px, ${DB.cy}px) scale(${sDb.toFixed(4)}) translate(${-DB.cx}px, ${-DB.cy}px)`, transformOrigin: '0 0'}}>
          <DBIcon cx={DB.cx} cy={DB.cy} w={DB.w} h={DB.h} label="知识库" labelSize={24} accent={PURPLE} sw={2.5} />
        </div>
      ) : null}
      {/* 过期灰卡 + 删除线 */}
      {sStale > 0 && dropOp > 0 ? (
        <div style={{position: 'absolute', inset: 0, opacity: 0.6 * dropOp, transform: `translate(${STALE.x + STALE.w / 2}px, ${STALE.y + STALE.h / 2 + dropDy}px) scale(${sStale.toFixed(4)}) translate(${-(STALE.x + STALE.w / 2)}px, ${-(STALE.y + STALE.h / 2)}px)`, transformOrigin: '0 0'}}>
          <ChunkCard x={STALE.x} y={STALE.y} w={STALE.w} h={STALE.h} lines={3} seed={5} />
          <Pill x={STALE.x + STALE.w - 40} y={STALE.y - 14} w={64} h={28} text="过期" fontSize={22} weight={700} color={GREY_LIGHT} stroke={GREY} textDy={-1} />
        </div>
      ) : null}
      {pStrike > 0 && dropOp > 0 ? (
        <Svg>
          <line x1={STALE.x + 6} y1={STALE.y + STALE.h / 2 + dropDy} x2={STALE.x + 6 + (STALE.w - 12) * pStrike} y2={STALE.y + STALE.h / 2 + dropDy} stroke={CORAL} strokeWidth={3} strokeLinecap="round" opacity={dropOp} />
        </Svg>
      ) : null}
      {/* 新卡（紫）自上落入 */}
      {nNew >= 0 ? (
        <div style={{position: 'absolute', inset: 0, opacity: newOp, transform: `translateY(${newDy.toFixed(2)}px)`}}>
          <ChunkCard x={STALE.x} y={STALE.y} w={STALE.w} h={STALE.h} lines={3} active seed={8} />
          <Pill x={STALE.x + STALE.w - 40} y={STALE.y - 14} w={62} h={28} text="v2" fontSize={22} weight={700} family={FONT_ORB} fill={PURPLE} sw={2} textDy={0} letterSpacing={1} />
        </div>
      ) : null}
      {/* 旁注：只重嵌入改动的块 */}
      <CText cx={DB.cx} cy={DB.cy + DB.h / 2 + 62} size={22} weight={500} color={GREY} opacity={fadeIn(N - (B_NEW + 12), 10)}>只重嵌入改动的块</CText>
    </div>
  );
};
