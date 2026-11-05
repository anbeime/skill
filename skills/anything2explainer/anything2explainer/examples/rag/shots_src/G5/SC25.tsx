import React from 'react';
import {useCurrentFrame} from 'remotion';
import {GlitchIn, clamp01, FONT_HEAVY, FONT_ORB, FONT_SERIF, powOutRemain} from '../../common';
import {Box, Pill, TechText, CText, PURPLE, PURPLE_LIGHT, ORANGE, GREY, WHITE, GLOW_PURPLE_S, slideUp, fadeIn, fadeOut, exitAccel, stagger, SoftIn} from '../../ui';
import {bez2, inOut, mixHex, mixK} from './g5util';

/**
 * SC25 混合检索 + RRF（4415–4676，S25）。节拍：4423 混合检索 / 4492 向量找相似 / 4526 BM25 找精确 / 4594 倒数排名融合。
 * 左列「向量检索」4 张卡 / 右列「BM25」4 张卡 → 4594 沿弧线汇入中央 5 张融合结果（紫边）；下方 Times 公式 score(d)=Σ 1/(k+rank_r(d))，k=60（Cormack 等 SIGIR 2009）。
 * QC v1：4664 起 12 帧下摇（0.6·n²）+ 线性淡出，4676 全透明，交给 SC26 的 4685 入场（原「末 2 帧不离场」改掉，避免满画面硬切到空场）。
 */
export const F0 = 4415;
const T_TITLE = 4423, T_L = 4492, T_R = 4526, T_MERGE = 4594, T_EXIT = 4664;
const CARD_W = 260, CARD_H = 42;
const LX = 300, RX = 980, MX = 640;
const COL_Y = [280, 336, 392, 448];
const MID_Y = [296, 342, 388, 434, 480];
type Src = {side: 'L' | 'R'; rank: number; text: string; slot: number; hot?: boolean};
// slot = 融合后名次（0 起）；slot 5 = 淘汰（飞向中央后淡出）。RRF(k=60)：§3 两路命中 1/61+1/63 居首。
const SRC: Src[] = [
  {side: 'L', rank: 1, text: '差旅报销标准 §3', slot: 0},
  {side: 'L', rank: 2, text: '住宿上限说明', slot: 2},
  {side: 'L', rank: 3, text: '交通补贴规定', slot: 4},
  {side: 'L', rank: 4, text: '报销流程 FAQ', slot: 5},
  {side: 'R', rank: 1, text: '差旅补充规定 2025', slot: 1},
  {side: 'R', rank: 2, text: 'X-2000B 保修 2 年', slot: 3, hot: true},
  {side: 'R', rank: 3, text: '差旅报销标准 §3', slot: 0},
  {side: 'R', rank: 4, text: '出差审批表', slot: 5},
];

const Card: React.FC<{cx: number; cy: number; rank: number; text: string; accent: string; stroke?: string; glow?: string; hot?: boolean; rankColor?: string}> = ({cx, cy, rank, text, accent, stroke = WHITE, glow, hot, rankColor}) => {
  const x = cx - CARD_W / 2, y = cy - CARD_H / 2;
  return (
    <>
      <Box x={x} y={y} w={CARD_W} h={CARD_H} r={8} sw={hot ? 2.5 : 2} stroke={hot ? ORANGE : stroke} glow={hot ? '0 0 14px 3px rgba(240,95,65,.5)' : glow} />
      <CText cx={x + 24} cy={cy} size={22} weight={700} family={FONT_ORB} color={rankColor ?? accent} dy={0}>{rank}</CText>
      <div style={{position: 'absolute', left: x + 44, top: y, height: CARD_H, display: 'flex', alignItems: 'center', fontFamily: FONT_HEAVY, fontWeight: 600, fontSize: 21, color: WHITE, whiteSpace: 'nowrap', lineHeight: 1, transform: 'translateY(-1px)'}}>
        {hot ? <span><span style={{color: ORANGE, fontFamily: FONT_ORB, fontWeight: 700, fontSize: 19}}>X-2000B</span> 保修 2 年</span> : text}
      </div>
    </>
  );
};

/** 公式 token：逐个出现（每 3 帧一个，4 帧淡入 + 上浮 10px） */
const Tok: React.FC<{i: number; N: number; children: React.ReactNode; style?: React.CSSProperties}> = ({i, N, children, style}) => {
  const n = N - (T_MERGE + i * 3);
  const k = clamp01(n / 4);
  return <span style={{display: 'inline-block', opacity: k, transform: `translateY(${(10 * (1 - k)).toFixed(1)}px)`, ...style}}>{children}</span>;
};

export const SC25: React.FC = () => {
  const N = useCurrentFrame() + F0;
  // 离场（4664 起 12 帧下摇 + 线性淡出）
  const ne = N - T_EXIT;
  const op = ne > 0 ? fadeOut(ne, 12) : 1;
  const dy = ne > 0 ? exitAccel(ne, 0.6) : 0;
  if (op <= 0) return null;
  const lIn = N >= T_L, rIn = N >= T_R;
  const merging = N >= T_MERGE;
  return (
    <div style={{position: 'absolute', inset: 0, opacity: op, transform: dy ? `translateY(${dy.toFixed(1)}px)` : undefined}}>
      {/* 中央标题 —— 「混合检索」为本镜头唯一 glitch（白名单 §8）；英文副标 SoftIn */}
      <GlitchIn N={N} f0={T_TITLE} seed={81}>
        <Pill x={MX - 105} y={187} w={210} h={50} fill={PURPLE} sw={2} text="混合检索" fontSize={30} weight={800} textDy={-2} glow={GLOW_PURPLE_S} />
      </GlitchIn>
      <SoftIn N={N} f0={T_TITLE}>
        <TechText cx={MX} cy={256} text="Hybrid Search" fontSize={24} scaleX={0.84} weight={700} />
      </SoftIn>

      {/* 左右列标题 Pill（自侧边滑入） */}
      {lIn ? (
        <div style={{position: 'absolute', left: -300 * powOutRemain(N - T_L, 22, 2.5), top: 0, width: 1280, height: 720, opacity: fadeIn(N - T_L, 6) * (merging ? 0.7 : 1)}}>
          <Pill x={LX - 85} y={190} w={170} h={44} fill={PURPLE} sw={2} text="向量检索" fontSize={26} weight={700} textDy={-2} />
        </div>
      ) : null}
      {rIn ? (
        <div style={{position: 'absolute', left: 300 * powOutRemain(N - T_R, 22, 2.5), top: 0, width: 1280, height: 720, opacity: fadeIn(N - T_R, 6) * (merging ? 0.7 : 1)}}>
          <Pill x={RX - 75} y={190} w={150} h={44} fill={ORANGE} sw={2} text="BM25" fontSize={26} weight={800} letterSpacing={1} textDy={-2} />
        </div>
      ) : null}

      {/* 卡片：列内入场 → 汇合飞行 */}
      {SRC.map((c, i) => {
        const t0 = (c.side === 'L' ? T_L : T_R) + 2 + stagger(c.rank - 1, 2);
        const n = N - t0;
        if (n < 0) return null;
        const sx = c.side === 'L' ? LX : RX;
        const sy = COL_Y[c.rank - 1];
        const accent = c.side === 'L' ? PURPLE_LIGHT : ORANGE;
        // 飞行
        const fly0 = T_MERGE + stagger(Math.min(c.slot, 5), 2) + (c.side === 'R' && c.slot === 0 ? 2 : 0);
        const nf = N - fly0;
        const tf = inOut(clamp01(nf / 20));
        const dropped = c.slot === 5;
        const tgt: [number, number] = [MX, dropped ? 510 : MID_Y[c.slot]];
        const ctrl: [number, number] = [(sx + MX) / 2, Math.min(sy, tgt[1]) - 70];
        const [px, py] = nf > 0 ? bez2([sx, sy], ctrl, tgt, tf) : [sx, sy];
        // 淘汰卡 / 重复卡（R 的 §3）在飞行后段淡出
        const dup = c.side === 'R' && c.slot === 0;
        let op = fadeIn(n, 8);
        if (nf > 0 && (dropped || dup)) op *= 1 - clamp01((tf - 0.55) / 0.4);
        if (op <= 0) return null;
        const entryDy = nf > 0 ? 0 : slideUp(n, 220);
        // 到位后灰→紫边 11 帧
        const km = nf >= 20 && !dropped ? mixK(nf - 20) : 0;
        const stroke = km > 0 ? mixHex('#FFFFFF', PURPLE_LIGHT, km) : WHITE;
        const glow = km > 0.5 ? '0 0 12px 2px rgba(161,117,241,.45)' : undefined;
        return (
          <div key={i} style={{position: 'absolute', left: 0, top: entryDy, width: 1280, height: 720, opacity: op}}>
            <Card cx={px} cy={py} rank={km > 0 ? c.slot + 1 : c.rank} text={c.text} accent={accent} stroke={stroke} glow={glow} hot={c.hot} rankColor={km > 0 ? mixHex(accent === ORANGE ? '#F05F41' : '#A175F1', '#A175F1', km) : undefined} />
          </div>
        );
      })}

      {/* 公式：score(d) = Σ_r 1 / (k + rank_r(d)) —— Times New Roman */}
      {N >= T_MERGE ? (
        <div style={{position: 'absolute', left: 0, top: 556, width: 1280, display: 'flex', justifyContent: 'center', alignItems: 'center', fontFamily: FONT_SERIF, fontSize: 34, color: WHITE, filter: 'drop-shadow(0 0 3px rgba(255,255,255,.45))', whiteSpace: 'pre', transform: 'translateY(-50%)'}}>
          <Tok i={0} N={N} style={{fontStyle: 'italic'}}>score(d)</Tok>
          <Tok i={1} N={N} style={{margin: '0 12px'}}>=</Tok>
          <Tok i={2} N={N} style={{display: 'inline-flex', flexDirection: 'column', alignItems: 'center', marginRight: 8}}>
            <span style={{fontSize: 46, lineHeight: 0.9}}>Σ</span>
            <span style={{fontSize: 17, fontStyle: 'italic', lineHeight: 1, marginTop: 2}}>r</span>
          </Tok>
          <Tok i={3} N={N} style={{display: 'inline-flex', flexDirection: 'column', alignItems: 'center', lineHeight: 1}}>
            <span style={{fontSize: 30, padding: '0 4px 3px'}}>1</span>
            <span style={{display: 'block', height: 2, width: '100%', background: WHITE}} />
            <span style={{fontSize: 30, padding: '3px 6px 0', display: 'inline-flex', alignItems: 'baseline'}}>
              <Tok i={4} N={N} style={{fontStyle: 'italic'}}>k</Tok>
              <Tok i={5} N={N} style={{margin: '0 7px'}}>+</Tok>
              <Tok i={6} N={N} style={{fontStyle: 'italic'}}>rank<span style={{fontSize: 17, position: 'relative', top: 4}}>r</span>(d)</Tok>
            </span>
          </Tok>
        </div>
      ) : null}
      <SoftIn N={N} f0={T_MERGE + 24}>
        <CText cx={MX} cy={605} size={24} weight={500} color={GREY} dy={-1} letterSpacing={1}>RRF · k = 60</CText>
      </SoftIn>
    </div>
  );
};
