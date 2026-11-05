import React from 'react';
import {useCurrentFrame} from 'remotion';
import {GlitchIn, kf, emphasisPulse, easeInOutPow, SENTENCES, TOTAL_FRAMES, FONT_HEAVY, FONT_WIDE, FONT_ORB} from '../../common';
import {SUBS} from '../../common/subs';
import {CText, TechText, Pill, TopCapsule, ArrowH, PURPLE, PURPLE_TECH, GREY, GREY_MID, WHITE, GLOW_PURPLE_S, fadeIn, slideUp, clampFrames} from './util';

// ---------- 时间轴查询 ----------
export const S = (id: string) => {
  const s = SENTENCES.find((x) => x.id === id);
  if (!s) throw new Error(`no sentence ${id}`);
  return s;
};
/** 某句里某个字幕块的起始帧（按文本匹配） */
export const subStart = (id: string, text: string) => {
  const s = S(id);
  const e = SUBS.find((x) => x.from >= s.from && x.from <= s.to && x.text === text);
  return e ? e.from : s.from;
};

/** 12 帧加速上出：n<0 → 原位；位移 (n/11)^2·440px，透明度 1−(n/11)^1.6 → 末帧 0（QC v1 C1 #1/#2） */
const exitOut = (n: number) => {
  if (n < 0) return {dy: 0, op: 1};
  const t = Math.min(1, n / 11);
  return {dy: t * t * 440, op: 1 - Math.pow(t, 1.6)};
};

// ---------- 片头 ----------
export const TITLE_RANGE: [number, number] = [1, S('S01').from - 9];
export const Title: React.FC = () => {
  const N = useCurrentFrame() + TITLE_RANGE[0];
  const [a, b] = TITLE_RANGE;
  const exitN = N - (b - 11); // 末 12 帧上摇出画（QC v1：原 8 帧只走了 59px/63% 亮度就被硬切）
  const dy = -exitOut(exitN).dy;
  const op = exitOut(exitN).op;
  const glow = 0.5 + 0.5 * Math.sin((N / 30) * Math.PI); // 缓慢呼吸
  return (
    <div style={{position: 'absolute', inset: 0, transform: `translateY(${dy}px)`, opacity: op}}>
      <GlitchIn N={N} f0={a + 11} rgbSplit={6} slices={14} seed={3}>
        <div style={{position: 'absolute', left: 0, top: 268, width: 1280, display: 'flex', justifyContent: 'center', alignItems: 'baseline', gap: 26}}>
          <span style={{fontFamily: FONT_WIDE, fontSize: 118, color: WHITE, lineHeight: 1, letterSpacing: 6, textShadow: `0 0 ${18 + 14 * glow}px rgba(102,45,248,${0.55 + 0.3 * glow}), 6px 6px 0 ${PURPLE}`}}>RAG</span>
          <span style={{fontFamily: FONT_HEAVY, fontWeight: 900, fontSize: 96, color: WHITE, lineHeight: 1, transform: 'scaleX(0.85)', transformOrigin: '0 100%', letterSpacing: 2, WebkitTextStroke: '1px #000', paintOrder: 'stroke fill'}}>与知识库</span>
        </div>
      </GlitchIn>
      <div style={{position: 'absolute', inset: 0, opacity: fadeIn(N - (a + 25), 12), transform: `translateY(${slideUp(N - (a + 25), 60)}px)`}}>
        <TechText cx={640} cy={446} text="Retrieval-Augmented Generation" fontSize={38} scaleX={0.82} weight={700} />
      </div>
      <div style={{position: 'absolute', inset: 0, opacity: fadeIn(N - (a + 40), 12)}}>
        <CText cx={640} cy={520} size={30} weight={500} color={GREY} letterSpacing={6}>
          让大模型开卷考试
        </CText>
        <div style={{position: 'absolute', left: 520, top: 496, width: 240, height: 2, background: 'rgba(255,255,255,0.35)', transform: `scaleX(${fadeIn(N - (a + 40), 16)})`}} />
      </div>
    </div>
  );
};

// ---------- 章节卡 ----------
export const CHAPTER_CARDS: Array<{n: number; title: string; tech: string; from: number; to: number}> = [
  {n: 2, title: '知识库构建', tech: 'Indexing', from: S('S10').to + 3, to: S('S11').from - 9},
  {n: 3, title: '检索与生成', tech: 'Retrieval & Generation', from: S('S20').to + 3, to: S('S21').from - 9},
  {n: 4, title: '评估与进阶', tech: 'Evaluation & Advanced RAG', from: S('S30').to + 3, to: S('S31').from - 9},
];
export const ChapterCard: React.FC<{card: (typeof CHAPTER_CARDS)[number]}> = ({card}) => {
  const N = useCurrentFrame() + card.from;
  const n = N - card.from;
  const exitN = N - (card.to - 11);
  const dy = -exitOut(exitN).dy;
  const op = exitOut(exitN).op;
  const w = kf(n, [[0, 0], [20, 300]], easeInOutPow(2.5));
  return (
    <div style={{position: 'absolute', inset: 0, transform: `translateY(${dy}px)`, opacity: op}}>
      <div style={{position: 'absolute', opacity: fadeIn(n, 8)}}>
        <CText cx={640} cy={268} size={54} weight={700} family={FONT_ORB} color={PURPLE_TECH} letterSpacing={4} shadow="0 0 14px rgba(102,45,248,.6)">{`0${card.n}`}</CText>
      </div>
      <GlitchIn N={N} f0={card.from + 3} rgbSplit={5} seed={card.n}>
        <CText cx={640} cy={372} size={80} weight={900} scaleX={0.85} letterSpacing={3} style={{WebkitTextStroke: '1px #000', paintOrder: 'stroke fill'}}>{card.title}</CText>
      </GlitchIn>
      <div style={{position: 'absolute', left: 640 - w / 2, top: 428, width: w, height: 3, background: WHITE, opacity: 0.85}} />
      <div style={{position: 'absolute', opacity: fadeIn(n - 10, 10)}}>
        <TechText cx={640} cy={470} text={card.tech} fontSize={32} scaleX={0.82} />
      </div>
    </div>
  );
};

// ---------- 顶部 HUD 胶囊 ----------
export type HudEntry = {from: number; to: number; text: string; tech?: string; w?: number};
export const HUD: HudEntry[] = [
  {from: S('S01').from, to: S('S05').to, text: '大模型的短板'},
  {from: S('S06').from, to: S('S07').to, text: '开卷考试'},
  {from: S('S08').from, to: S('S10').to, text: 'RAG', tech: 'Retrieval-Augmented Generation'}, // QC v1：提前到句首，避免 SC08 光条段 HUD 空缺
  // QC v1 C2：章节卡出画到句首之间顶部空 8 帧 → 第 2/3/4 章 HUD 从章节卡结束的下一帧开始
  {from: S('S11').from - 8, to: S('S20').to + 2, text: '知识库构建', tech: 'Indexing'},
  {from: S('S21').from - 8, to: S('S30').to + 2, text: '检索与生成', tech: 'Retrieval & Generation'},
  {from: S('S31').from - 8, to: S('S34').to, text: '评估', tech: 'Evaluation'},
  {from: S('S35').from + 4, to: S('S38').to, text: '进阶', tech: 'Advanced RAG'}, // +4：错开 SC35「RAG」大字 glitch（QC v1 C4）
  {from: S('S39').from + 4, to: S('S41').to, text: '长上下文 vs RAG'}, // +4：错开 SC39 入场暗帧（QC v2 复验）
  {from: S('S42').from + 4, to: S('S44').to, text: '总结'}, // +4：同上
];
// 同章相邻条目之间不留空档（G1 提示 742–751 无胶囊）：上一条延到下一条 from−1；跨章节卡（间隔 ≥30 帧）保持空档，由章节卡接管
for (let i = 0; i < HUD.length - 1; i++) if (HUD[i + 1].from - HUD[i].to < 30) HUD[i].to = HUD[i + 1].from - 1;
export const HUD_RANGE: [number, number] = [HUD[0].from, HUD[HUD.length - 1].to];
export const Hud: React.FC = () => {
  const N = useCurrentFrame() + HUD_RANGE[0];
  const e = HUD.find((h) => N >= h.from && N <= h.to);
  if (!e) return null;
  // QC v1 C3：进章节卡前 HUD 一帧消失 → 末 8 帧淡出（只对跨章节卡的条目生效：下一条 from 与本条 to 间隔 ≥30）
  const idx = HUD.indexOf(e);
  const nextGap = idx < HUD.length - 1 ? HUD[idx + 1].from - e.to : 999;
  const fadeTail = nextGap >= 30 ? 1 - clampFrames(N - (e.to - 8), 8) : 1;
  const w = e.w ?? Math.max(216, Math.round(e.text.replace(/[^一-龥]/g, '').length * 34 + e.text.replace(/[一-龥\s]/g, '').length * 20 + (e.text.match(/\s/g)?.length ?? 0) * 10 + 60));
  // 第 2、3 章胶囊下方紧接流程轨，副标只在无流程轨时显示
  return <TopCapsule N={N} f0={e.from} text={e.text} w={w} tech={e.tech} opacity={fadeTail} />;
};

// ---------- 流程轨（第 2、3 章）----------
export type RailSpec = {steps: string[]; switches: number[]; from: number; to: number};
export const RAILS: RailSpec[] = [
  {steps: ['解析', '切块', '向量化', '建索引', '更新'], switches: [S('S12').from, S('S13').from, S('S16').from, S('S18').from, S('S20').from], from: S('S12').from - 8, to: S('S20').to + 2},
  {steps: ['理解问题', '检索', '重排', '组装', '生成'], switches: [S('S22').from, S('S23').from, S('S26').from, S('S28').from, S('S29').from], from: S('S22').from - 8, to: S('S29').to + 2},
];
const RAIL_CX = [240, 440, 640, 840, 1040];
const RAIL_W = 150, RAIL_H = 44, RAIL_Y = 118;
export const Rail: React.FC<{spec: RailSpec}> = ({spec}) => {
  const N = useCurrentFrame() + spec.from;
  let active = -1;
  spec.switches.forEach((f, i) => { if (N >= f) active = i; });
  const railOut = 1 - clampFrames(N - (spec.to - 8), 8); // 末 8 帧淡出
  return (
    <div style={{position: 'absolute', inset: 0, opacity: railOut}}>
      {spec.steps.map((t, i) => {
        const state = i === active ? 'active' : i < active ? 'done' : 'todo';
        const pulse = i === active ? emphasisPulse(N - spec.switches[i], {peak: 1.1, up: 10, hold: 3, down: 10}) : 1;
        const fill = state === 'active' ? PURPLE : state === 'done' ? '#2A2A2A' : '#000';
        const stroke = state === 'active' ? WHITE : state === 'done' ? GREY_MID : GREY;
        const color = state === 'todo' ? GREY : WHITE;
        return (
          <React.Fragment key={t}>
            <div style={{position: 'absolute', left: RAIL_CX[i] - RAIL_W / 2, top: RAIL_Y + slideUp(N - (spec.from + i * 2), 40, 16), width: RAIL_W, height: RAIL_H, transform: `scale(${pulse})`, opacity: fadeIn(N - (spec.from + i * 2), 8)}}>
              <Pill x={0} y={0} w={RAIL_W} h={RAIL_H} fill={fill} stroke={stroke} sw={2} text={t} fontSize={24} weight={700} color={color} letterSpacing={1} textDy={-1.5} glow={state === 'active' ? GLOW_PURPLE_S : undefined} />
            </div>
            {i < spec.steps.length - 1 ? (
              <ArrowH x={RAIL_CX[i] + RAIL_W / 2 + 6} y={RAIL_Y + RAIL_H / 2 - 9} w={38} h={18} p={clampFrames(N - (spec.from + 4 + i * 2), 10)} color={i < active ? WHITE : GREY} shaft={2} />
            ) : null}
          </React.Fragment>
        );
      })}
    </div>
  );
};

// ---------- 片尾 ----------
// QC v1 C4（高）：v1 的压黑层在 G0（最低层）且从 SC44 结束后才开始 → 内容在 8148|8149 硬切消失。
// v2：压黑层挂在内容之上（Main 里 SHOTS_G0_TOP 排在所有内容组之后、进度条之下），从 SC44 末 32 帧开始 30 帧压黑，内容在被完全盖住后才结束；
//     最后 30 帧再用 aboveBar 层把进度条也压黑 → 末段纯黑。
export const ENDING_RANGE: [number, number] = [S('S44').to - 30, TOTAL_FRAMES];
export const Ending: React.FC = () => {
  const N = useCurrentFrame() + ENDING_RANGE[0];
  const n = N - ENDING_RANGE[0];
  const op = fadeIn(n, 30);
  return <div style={{position: 'absolute', inset: 0, background: '#000', opacity: op}} />;
};
export const ENDING_TOP_RANGE: [number, number] = [TOTAL_FRAMES - 30, TOTAL_FRAMES];
export const EndingTop: React.FC = () => {
  const N = useCurrentFrame() + ENDING_TOP_RANGE[0];
  const op = fadeIn(N - ENDING_TOP_RANGE[0], 20);
  return <div style={{position: 'absolute', inset: 0, background: '#000', opacity: op}} />;
};
