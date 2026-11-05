import React from 'react';
import {useCurrentFrame} from 'remotion';
import {clamp01, easeOutCubic, FONT_HEAVY, FONT_ORB, powOutRemain} from '../../common';
import {Box, Svg, Cross, CText, ORANGE, CORAL, GREY, GREY_LIGHT, WHITE, PILL_SHADOW, slideUp, fadeIn, fadeOut, exitAccel, stagger, SoftIn} from '../../ui';
import {hlW} from './g5util';

/**
 * SC24 盲区：精确匹配（4226–4414，S24）。节拍：4234 语义检索有盲区 / 4282 型号 编号 专有名词 / 4377 抓不住。
 * 主区 y 175–620。问句「型号 X-2000B 的保修期？」（X-2000B 橙色高亮）；三张相似度结果卡全被划掉；右侧「X-2000B 保修 2 年」被漏掉（40% 灰暗 + 轻晃）。
 */
export const F0 = 4226;
const T_Q = 4234, T_CARDS = 4260, T_HL = 4282, T_MISS = 4300, T_CROSS = 4377, T_EXIT = 4403;
const CARD_W = 210, CARD_H = 120, CARD_Y = 340, CX = [300, 540, 780], MISS_CX = 1080;
const CARDS = [
  {title: 'X-2000A 保修…', score: 0.83},
  {title: 'X-3000 保修…', score: 0.81},
  {title: '保修政策总则', score: 0.79},
];
const Q = {x: 300, y: 214, w: 480, h: 52};

const ResultCard: React.FC<{cx: number; title: string; dim?: boolean; children?: React.ReactNode; seed: number}> = ({cx, title, dim = false, children, seed}) => {
  const x = cx - CARD_W / 2, y = CARD_Y;
  return (
    <>
      <Box x={x} y={y} w={CARD_W} h={CARD_H} r={10} sw={2} stroke={dim ? GREY : WHITE} style={dim ? undefined : {filter: PILL_SHADOW}} />
      <div style={{position: 'absolute', left: x + 14, top: y + 16, fontFamily: FONT_HEAVY, fontWeight: 600, fontSize: 22, color: WHITE, whiteSpace: 'nowrap', lineHeight: 1}}>{title}</div>
      {[0, 1, 2].map((i) => {
        const lw = (0.55 + 0.4 * (((seed * 7 + i * 13) % 10) / 10)) * (CARD_W - 28);
        return <div key={i} style={{position: 'absolute', left: x + 14, top: y + 58 + i * 17, width: i === 2 ? lw * 0.6 : lw, height: 3, background: GREY_LIGHT, opacity: 0.8}} />;
      })}
      {children}
    </>
  );
};

export const SC24: React.FC = () => {
  const N = useCurrentFrame() + F0;
  const ne = N - T_EXIT;
  const op = ne > 0 ? fadeOut(ne, 12) : 1;
  const dy = ne > 0 ? exitAccel(ne, 0.6) : 0;
  if (op <= 0) return null;
  // 问句自左滑入
  const qDx = -420 * powOutRemain(N - T_Q, 22, 2.5);
  const qOp = fadeIn(N - T_Q, 6);
  const hl = hlW(N - T_HL);
  const hlOn = N >= T_HL;
  // 漏掉卡：淡入 40% + 轻晃
  const missOp = 0.4 * fadeIn(N - T_MISS, 20);
  const rot = N >= T_MISS ? 1.4 * Math.sin((N - T_MISS) / 5) : 0;
  return (
    <div style={{position: 'absolute', inset: 0, opacity: op, transform: dy ? `translateY(${dy.toFixed(1)}px)` : undefined}}>
      {/* 问句 Pill */}
      {qOp > 0 ? (
        <div style={{position: 'absolute', left: qDx, top: 0, width: 1280, height: 720, opacity: qOp}}>
          <Box x={Q.x} y={Q.y} w={Q.w} h={Q.h} r={Q.h / 2} sw={2} style={{filter: PILL_SHADOW}} />
          <div style={{position: 'absolute', left: Q.x, top: Q.y, width: Q.w, height: Q.h, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: FONT_HEAVY, fontWeight: 700, fontSize: 28, color: WHITE, whiteSpace: 'pre', lineHeight: 1, transform: 'translateY(-2px)'}}>
            <span>型号 </span>
            <span style={{position: 'relative', display: 'inline-block', padding: '0 6px', margin: '0 2px'}}>
              {/* 闪烁整改：高亮块不再 glitch，8 帧纯淡入（dy 0）+ HL_W 展宽 */}
              {hlOn ? <SoftIn N={N} f0={T_HL} dy={0}><div style={{position: 'absolute', left: 0, top: -5, bottom: -5, width: `${(hl * 100).toFixed(1)}%`, background: ORANGE, borderRadius: 6, boxShadow: '0 0 18px 4px rgba(240,95,65,.45)'}} /></SoftIn> : null}
              <span style={{position: 'relative', color: hlOn && hl > 0.5 ? WHITE : ORANGE, fontFamily: FONT_ORB, fontWeight: 700, fontSize: 26, letterSpacing: 1}}>X-2000B</span>
            </span>
            <span> 的保修期？</span>
          </div>
        </div>
      ) : null}

      {/* 三张结果卡（2 帧错峰自下滑入）+ 分数计数 */}
      {CARDS.map((c, i) => {
        const n = N - (T_CARDS + stagger(i, 2));
        if (n < 0) return null;
        const cdy = slideUp(n, 260);
        const cop = fadeIn(n, 8);
        const k = easeOutCubic(clamp01((n - 4) / 20));
        const score = (c.score * k).toFixed(2);
        return (
          <div key={i} style={{position: 'absolute', left: 0, top: cdy, width: 1280, height: 720, opacity: cop}}>
            <ResultCard cx={CX[i]} title={c.title} seed={i + 3}>
              <Box x={CX[i] + CARD_W / 2 - 80} y={CARD_Y - 14} w={70} h={28} r={14} sw={1.5} stroke={GREY} />
              <CText cx={CX[i] + CARD_W / 2 - 45} cy={CARD_Y} size={18} weight={600} family={FONT_ORB} color={GREY_LIGHT} dy={0} letterSpacing={0.5}>{score}</CText>
            </ResultCard>
          </div>
        );
      })}
      {/* 红叉依次 draw-on */}
      <Svg>
        {/* QC v1：叉心下移到 y=418（卡片中下部灰线区），60×60，不再压标题行（标题 ink ≈356–378） */}
        {CX.map((cx, i) => <Cross key={i} cx={cx} cy={CARD_Y + 78} size={60} color={CORAL} sw={8} p={clamp01((N - (T_CROSS + i * 6)) / 8)} />)}
      </Svg>

      {/* 右侧：漏掉的正确卡 */}
      {missOp > 0 ? (
        <div style={{position: 'absolute', left: 0, top: 0, width: 1280, height: 720, opacity: missOp, transformOrigin: `${MISS_CX}px ${CARD_Y + CARD_H / 2}px`, transform: `rotate(${rot.toFixed(2)}deg)`}}>
          <ResultCard cx={MISS_CX} title="X-2000B 保修 2 年" dim seed={9} />
        </div>
      ) : null}
      <SoftIn N={N} f0={T_CROSS + 3}>
        <CText cx={MISS_CX} cy={CARD_Y + CARD_H + 30} size={22} weight={500} color={GREY} dy={-1}>漏掉了</CText>
      </SoftIn>
    </div>
  );
};
