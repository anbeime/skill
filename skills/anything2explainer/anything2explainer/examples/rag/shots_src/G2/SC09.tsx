import React from 'react';
import {useCurrentFrame} from 'remotion';
import {stepKf, clamp01, emphasisPulse, FONT_ORB, FONT_SERIF} from '../../common';
import {CText, Box, Pill, TechText, WHITE, GREY, GREY_LIGHT, GREY_MID, PURPLE, PURPLE_LIGHT, TEXT_GLOW, BLOOM_SOFT, slideUp, fadeIn, SoftIn} from '../../ui';
import {mixHex} from './parts';

/**
 * SC09 2020 论文 · N 1130–1328（S09 1138–1326：1138「2020年」/ 1152「Facebook AI 的研究者在论文里」/ 1211「正式提出了这个名字」/ 1238「Retrieval-Augmented Generation」）
 * 事实依据（research/RAG调研.md §1）：Lewis et al.,《Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks》, Facebook AI Research (Meta), NeurIPS 2020。
 * 版式：左 论文卡 (140,140,380,460)：三行标题（Times 22/700）+ 作者行「Lewis et al. · NeurIPS 2020」灰 + 摘要灰线两栏 + 右下小柱状图；
 *       右 「2020」Orbitron 96 (860,300) → 胶囊「Facebook AI Research」(690,376,340,50) → 大号 Exo 2 两行 Retrieval-Augmented / Generation (860,495/545)。
 * 节拍：1138 年份 SoftIn + 2016→2020 计数（每 3 帧 +1，14 帧）；1146 论文卡 slideUp（Δ90/22 + 8 帧淡入；QC v1：原 Δ300 在 1151–1158 穿过字幕带）；1152 胶囊 SoftIn（本镜头无 glitch，协议 §8）；
 *       1211 标题下紫色下划线 draw-on 14 帧 + 标题块 emphasisPulse 1.06 + 三词 1211/1215/1219 依次 12 帧白闪（QC v1：原仅 3px 下划线，1167–1240 静止 73 帧）；
 *       1238/1248/1258 标题中 Retrieval / Augmented / Generation 依次 11 帧灰→紫；1238 大号英文 slideUp（Δ160/22）；1323–1328 整组 6 帧淡出。
 */
const F0 = 1130;
const T_YEAR = 1138, T_CARD = 1146, T_PILL = 1152, T_UNDER = 1211, T_WORDS = 1238, T_BIG = 1238, T_EXIT = 1323;
const CARD = {x: 140, y: 140, w: 380, h: 460};
const YEAR_KF: Array<[number, number]> = [[T_YEAR, 2016], [T_YEAR + 3, 2017], [T_YEAR + 6, 2018], [T_YEAR + 9, 2019], [T_YEAR + 13, 2020]];
/** 摘要灰线：[col(0/1), row, 宽度比例] */
const ABS_ROWS = 8;
const ABS_W = [0.98, 0.9, 1, 0.84, 0.95, 1, 0.88, 0.6, 0.97, 0.93, 1, 0.8, 0.9, 0.55];
const CHART_BARS: Array<[number, string]> = [[30, GREY_MID], [44, GREY_MID], [58, PURPLE], [74, PURPLE]];

/** 标题词：k = 灰→紫进度（1238 起）；f = 白闪强度 0→1→0（1211 起，与 k 不重叠） */
const Word: React.FC<{k: number; f?: number; children: React.ReactNode}> = ({k, f = 0, children}) => (
  <span style={{color: f > 0 ? mixHex(GREY_LIGHT, WHITE, f) : mixHex(GREY_LIGHT, PURPLE_LIGHT, k), textShadow: f > 0 ? `0 0 ${Math.round(6 + 10 * f)}px rgba(255,255,255,${(0.85 * f).toFixed(2)})` : k > 0.5 ? '0 0 8px rgba(161,117,241,.6)' : undefined, fontWeight: 700}}>{children}</span>
);
/** 12 帧三角脉冲 0→1→0 */
const tri = (n: number, len = 12) => (n <= 0 || n >= len ? 0 : n < len / 2 ? n / (len / 2) : 1 - (n - len / 2) / (len / 2));

export const SC09: React.FC = () => {
  const N = useCurrentFrame() + F0;
  const ex = N - T_EXIT;
  const exOp = ex <= 0 ? 1 : Math.max(0, 1 - ex / 6);

  const year = stepKf(N, YEAR_KF);
  const cn = N - T_CARD;
  const cardY = CARD.y + slideUp(cn, 90, 22);
  const cardOp = cn < 0 ? 0 : fadeIn(cn, 8);
  const under = clamp01((N - T_UNDER) / 14);
  const fl = [0, 1, 2].map((i) => tri(N - (T_UNDER + 4 * i), 12));
  const titleS = emphasisPulse(N - T_UNDER, {peak: 1.06, up: 8, hold: 4, down: 10});
  const kw = [0, 1, 2].map((i) => clamp01((N - (T_WORDS + 10 * i)) / 11));
  const gn = N - T_BIG;
  const bigDy = slideUp(gn, 160, 22);
  const bigOp = gn < 0 ? 0 : fadeIn(gn, 10);

  return (
    <div style={{position: 'absolute', inset: 0, opacity: exOp}}>
      {/* 论文卡 */}
      {cardOp > 0 ? (
        <Box x={CARD.x} y={cardY} w={CARD.w} h={CARD.h} r={8} sw={3} opacity={cardOp} style={{filter: BLOOM_SOFT}}>
          {/* 标题三行 */}
          <div style={{position: 'absolute', left: 20, right: 20, top: 30, textAlign: 'center', fontFamily: FONT_SERIF, fontSize: 22, lineHeight: '28px', color: GREY_LIGHT, fontWeight: 700, whiteSpace: 'nowrap', transformOrigin: '50% 50%', transform: titleS === 1 ? undefined : `scale(${titleS.toFixed(4)})`}}>
            <div><Word k={kw[0]} f={fl[0]}>Retrieval</Word>-<Word k={kw[1]} f={fl[1]}>Augmented</Word> <Word k={kw[2]} f={fl[2]}>Generation</Word></div>
            <div>for Knowledge-Intensive</div>
            <div>NLP Tasks</div>
          </div>
          {/* 下划线（1211 draw-on，左锚） */}
          {under > 0 ? <div style={{position: 'absolute', left: 40, top: 122, width: (CARD.w - 80) * under, height: 2.5, background: PURPLE_LIGHT, boxShadow: '0 0 8px rgba(102,45,248,.7)'}} /> : null}
          {/* 作者行 */}
          <div style={{position: 'absolute', left: 0, right: 0, top: 138, textAlign: 'center', fontFamily: FONT_SERIF, fontSize: 22, lineHeight: '26px', color: GREY, whiteSpace: 'nowrap'}}>Lewis et al. · NeurIPS 2020</div>
          <div style={{position: 'absolute', left: 24, top: 176, width: CARD.w - 48, height: 1.5, background: GREY, opacity: 0.7}} />
          {/* 摘要两栏灰线 */}
          {Array.from({length: ABS_ROWS}, (_, i) => (
            <React.Fragment key={i}>
              <div style={{position: 'absolute', left: 24, top: 194 + i * 17, width: 156 * ABS_W[i], height: 3, background: GREY_MID}} />
              <div style={{position: 'absolute', left: 200, top: 194 + i * 17, width: 156 * ABS_W[(i + 5) % ABS_W.length], height: 3, background: GREY_MID}} />
            </React.Fragment>
          ))}
          {/* 左下继续文本；右下小图表 */}
          {Array.from({length: 6}, (_, i) => <div key={`b${i}`} style={{position: 'absolute', left: 24, top: 344 + i * 17, width: 156 * ABS_W[(i + 2) % ABS_W.length], height: 3, background: GREY_MID}} />)}
          <div style={{position: 'absolute', left: 200, top: 340, width: 156, height: 96, boxSizing: 'border-box', border: `1.5px solid ${GREY}`}}>
            {CHART_BARS.map(([h, c], i) => <div key={i} style={{position: 'absolute', left: 16 + i * 32, bottom: 12, width: 20, height: h, background: c, opacity: c === PURPLE ? 0.9 : 0.8}} />)}
            <div style={{position: 'absolute', left: 8, right: 8, bottom: 11, height: 1.5, background: GREY}} />
          </div>
        </Box>
      ) : null}

      {/* 右：年份计数 */}
      <SoftIn N={N} f0={T_YEAR}>
        <CText cx={860} cy={300} size={96} weight={700} family={FONT_ORB} letterSpacing={4} color={WHITE} shadow={TEXT_GLOW} style={{fontVariantNumeric: 'tabular-nums'}} dy={-2}>
          {year}
        </CText>
      </SoftIn>
      {/* 胶囊 Facebook AI Research */}
      <SoftIn N={N} f0={T_PILL}>
        <Pill x={690} y={376} w={340} h={50} sw={2.5} text="Facebook AI Research" fontSize={26} weight={700} letterSpacing={0.5} style={{filter: BLOOM_SOFT}} />
      </SoftIn>
      {/* 大号英文两行 */}
      {bigOp > 0 ? (
        <div style={{position: 'absolute', inset: 0, opacity: bigOp}}>
          <TechText cx={860} cy={495 + bigDy} text="Retrieval-Augmented" fontSize={42} scaleX={0.82} weight={700} />
          <TechText cx={860} cy={545 + bigDy} text="Generation" fontSize={42} scaleX={0.82} weight={700} />
        </div>
      ) : null}
    </div>
  );
};
