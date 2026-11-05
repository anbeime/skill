import React from 'react';
import {useCurrentFrame} from 'remotion';
import {emphasisPulse, easeOutCubic, easeInOutPow, powOutRemain} from '../../common';
import {CText, Pill, Svg, LineArrow, Check, Cross, DBIcon, ChunkCard, PURPLE, ORANGE, WHITE, GREY, GREY_LIGHT, GREEN, CORAL, fadeIn, scaleIn, exitAccel, abs, SoftIn} from '../../ui';

/**
 * SC19 向量数据库 + 元数据/权限（3299–3482）
 * 节拍：3307 存进向量数据库（DBIcon 缩放入场，3312 三张 ChunkCard 自左滑入）→ 3345 元数据和权限标签
 *      （每张卡贴两枚标签：「来源：员工手册 p.12」白 / 「ACL：财务组」橙，SoftIn 淡入 4 帧错峰；3360 起卡片沿弧线飞入库，
 *      18 帧一张、错峰 12 帧，库随之轻微脉冲；3402 库上出现 ACL 小标）→ 3405 谁能看什么（右侧两个用户图标滑入，
 *      连线 draw-on：财务组 绿勾 / 实习生 红叉）→ 3432 这一步定下来（库边框紫柔光脉冲）→ 3475 起 8 帧离场。
 * 依据 research §2.4：块携带来源/页码/ACL 等元数据，查询时先按元数据预过滤；OWASP LLM08 要求权限感知的向量库。
 */
export const F0 = 3299;
const B_DB = 3307, B_CARDS = 3312, B_TAGS = 3345, B_FLY = 3360, B_ACL = 3402, B_USERS = 3405, B_LOCK = 3432, EXIT = 3475;

const DB = {cx: 640, cy: 330, w: 160, h: 170};
const CARD = {x: 60, w: 210, h: 96};
const CARDS = [
  {y: 205, src: '来源：员工手册 p.12', srcW: 250, acl: 'ACL：财务组', seed: 1},
  {y: 350, src: '来源：差旅补充规定 2025', srcW: 290, acl: 'ACL：财务组', seed: 2},
  {y: 495, src: '来源：员工手册 p.12', srcW: 250, acl: 'ACL：财务组', seed: 3},
];
const USERS = [
  {cx: 930, cy: 300, label: '财务组', ok: true},
  {cx: 930, cy: 480, label: '实习生', ok: false},
];
const flyEase = easeInOutPow(2.2);

/** 用户小图标：圆头 + 肩线（SVG 全幅内） */
const UserIcon: React.FC<{cx: number; cy: number; color?: string; s?: number}> = ({cx, cy, color = WHITE, s = 1}) => (
  <g transform={`translate(${cx} ${cy}) scale(${s}) translate(${-cx} ${-cy})`} stroke={color} strokeWidth={2.5} fill="#000">
    <circle cx={cx} cy={cy - 16} r={13} />
    <path d={`M${cx - 27},${cy + 26} a27,27 0 0 1 54,0 Z`} strokeLinejoin="round" />
  </g>
);

export const SC19: React.FC = () => {
  const N = useCurrentFrame() + F0;
  const ne = N - EXIT;
  const exitOp = ne <= 0 ? 1 : Math.max(0, 1 - ne / 8);
  const exitDy = exitAccel(ne, 0.5);
  if (N < B_DB) return null;

  // 库：缩放入场 × 收卡脉冲 × 3432 强调脉冲
  const sDb = scaleIn(N - B_DB);
  let sPulse = 1;
  CARDS.forEach((_, i) => {
    sPulse *= emphasisPulse(N - (B_FLY + i * 12 + 15), {peak: 1.05, up: 4, hold: 2, down: 8});
  });
  const sLock = emphasisPulse(N - B_LOCK, {peak: 1.1, up: 12, hold: 4, down: 14});
  const lockGlow = N < B_LOCK ? 0 : Math.min(1, (sLock - 1) / 0.1 + 0.15);
  const sAll = sDb * sPulse * sLock;

  return (
    <div style={{position: 'absolute', inset: 0, opacity: exitOp, transform: `translateY(${exitDy.toFixed(2)}px)`}}>
      {/* 库后方紫柔光（3432 起） */}
      {lockGlow > 0 ? <div style={{...abs(DB.cx - DB.w / 2 + 10, DB.cy - DB.h / 2 + 10, DB.w - 20, DB.h - 20), borderRadius: '50% / 30%', boxShadow: '0 0 30px 14px rgba(102,45,248,.55), 0 0 70px 30px rgba(102,45,248,.3)', opacity: lockGlow}} /> : null}

      {/* 三张卡（+ 标签）：自左滑入 → 贴标签 → 沿弧线飞入库 */}
      {CARDS.map((c, i) => {
        const nIn = N - (B_CARDS + i * 2);
        if (nIn < 0) return null;
        const slideX = -320 * powOutRemain(nIn, 22, 2.5);
        const inOp = fadeIn(nIn, 8);
        // 飞行
        const t = (N - (B_FLY + i * 12)) / 18;
        const e = t <= 0 ? 0 : flyEase(Math.min(1, t));
        const cx0 = CARD.x + CARD.w / 2, cy0 = c.y + CARD.h / 2;
        const dx = (DB.cx - cx0) * e;
        const dy = (DB.cy - cy0) * e - 90 * Math.sin(Math.PI * e);
        const sc = 1 - 0.78 * e;
        const flyOp = e < 0.7 ? 1 : Math.max(0, 1 - (e - 0.7) / 0.28);
        if (flyOp <= 0) return null;
        return (
          <div key={i} style={{...abs(CARD.x, c.y, CARD.w, CARD.h), opacity: inOp * flyOp, transform: `translate(${(slideX + dx).toFixed(2)}px, ${dy.toFixed(2)}px) scale(${sc.toFixed(4)})`, transformOrigin: '50% 50%'}}>
            <ChunkCard x={0} y={0} w={CARD.w} h={CARD.h} lines={4} seed={c.seed} />
            {/* 标签（伸出卡片右缘，指向库） */}
            <SoftIn N={N} f0={B_TAGS + i * 4} style={{overflow: 'visible'}}>
              <Pill x={CARD.w - 24} y={12} w={c.srcW} h={30} text={c.src} fontSize={22} weight={600} textDy={-1.5} style={{filter: 'drop-shadow(0 2px 2px rgba(0,0,0,.6))'}} />
              <Pill x={CARD.w - 24} y={52} w={150} h={30} text={c.acl} fontSize={22} weight={700} fill={ORANGE} sw={2} textDy={-1.5} glow="0 0 12px 3px rgba(240,95,65,.45)" />
            </SoftIn>
          </div>
        );
      })}

      {/* 库 */}
      {sDb > 0 ? (
        <div style={{position: 'absolute', inset: 0, transform: `translate(${DB.cx}px, ${DB.cy}px) scale(${sAll.toFixed(4)}) translate(${-DB.cx}px, ${-DB.cy}px)`, transformOrigin: '0 0'}}>
          <DBIcon cx={DB.cx} cy={DB.cy} w={DB.w} h={DB.h} label="向量数据库" labelSize={26} accent={PURPLE} sw={2.5} />
          {/* ACL 小标（卡片入库后） */}
          <SoftIn N={N} f0={B_ACL} style={{overflow: 'visible'}}>
            <Pill x={DB.cx + 28} y={DB.cy - DB.h / 2 - 14} w={68} h={30} text="ACL" fontSize={22} weight={800} fill={ORANGE} sw={2} textDy={-1} letterSpacing={1} glow="0 0 12px 3px rgba(240,95,65,.45)" />
          </SoftIn>
        </div>
      ) : null}

      {/* 右：谁能看什么 */}
      {USERS.map((u, i) => {
        const n = N - (B_USERS + i * 4);
        if (n < 0) return null;
        const dxIn = 300 * powOutRemain(n, 22, 2.5);
        const op = fadeIn(n, 10);
        const pArrow = easeOutCubic((N - (B_USERS + 8 + i * 6)) / 14);
        const pMark = easeOutCubic((N - (B_USERS + 20 + i * 6)) / 12);
        return (
          <React.Fragment key={i}>
            <div style={{position: 'absolute', inset: 0, opacity: op, transform: `translateX(${dxIn.toFixed(2)}px)`}}>
              <Svg>
                <UserIcon cx={u.cx} cy={u.cy} color={u.ok ? WHITE : GREY} />
              </Svg>
              <CText cx={u.cx + 88} cy={u.cy + 4} size={26} weight={700} color={u.ok ? WHITE : GREY_LIGHT}>{u.label}</CText>
            </div>
            <Svg>
              {pArrow > 0 ? <LineArrow x0={DB.cx + DB.w / 2 + 12} y0={DB.cy + (u.ok ? -10 : 20)} x1={u.cx - 40} y1={u.cy} p={pArrow} color={u.ok ? WHITE : GREY} rodW={u.ok ? 3 : 2.5} headL={18} headW={20} dashed={!u.ok} opacity={u.ok ? 1 : 0.85} /> : null}
              {pMark > 0 ? (u.ok ? <Check cx={u.cx + 180} cy={u.cy} size={46} p={pMark} sw={6} color={GREEN} /> : <Cross cx={u.cx + 180} cy={u.cy} size={36} p={pMark} sw={6} color={CORAL} />) : null}
            </Svg>
          </React.Fragment>
        );
      })}
    </div>
  );
};
