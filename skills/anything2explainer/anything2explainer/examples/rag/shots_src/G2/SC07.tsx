import React from 'react';
import {useCurrentFrame} from 'remotion';
import {clamp01, powOutRemain} from '../../common';
import {Svg, LineArrow, DocIcon, WHITE, PURPLE_LIGHT, fadeIn, scaleIn, stagger, SoftIn} from '../../ui';
import {BookIcon, Bubble, StepPill} from './parts';

/**
 * SC07 手册流程预告 · N 871–1012（S07 879–1010：879「考试前先把资料整理成一本手册」/ 956「答题时先翻手册」/ 995「再作答」）
 * 版式：三步横排，中轴 y 380：左「资料」= 5 张 DocIcon 扇形堆 (250,380) → 箭头① → 中「手册」= 书 (640,372) 260×170 + 紫胶囊「知识库」
 *       → 箭头② → 右「作答」= 答复气泡 (872,328,328,104) 带引用 [1][2]。上方 (640,150) 问句气泡「差旅报销的上限是多少？」956 起落到书上。
 * 节拍：879 文档 2 帧错峰 21 帧缩放入场；890「资料」SoftIn；893 箭头①自根部长出 16 帧；905 书缩放入场；918「知识库」SoftIn；
 *       940 问句气泡 SoftIn；956 落下（Δ112 / 22 帧）；978 右页第 2 行紫条 wipe 12 帧；995 箭头② 12 帧；996「作答」SoftIn（1004 落定）；998 答复气泡自箭头尖弹出 10 帧；1000 引用角标 8 帧淡入。
 *       本镜头无 glitch（协议 §8 不在白名单）。末帧无离场（SC08 以光条扫过硬切）。
 */
const F0 = 871;
const T_DOCS = 879, T_PILL1 = 890, T_ARR1 = 893, T_BOOK = 905, T_PILL2 = 918, T_Q = 940, T_FLY = 956, T_HL = 978, T_ARR2 = 995, T_ANS = 998, T_CITE = 1000, T_PILL3 = 996;

const AXIS = 380;
/** 文档堆：[left, top, rot°]，后者在上 */
const DOCS: Array<[number, number, number]> = [[186, 340, -14], [212, 332, -7], [240, 328, 0], [268, 332, 7], [296, 342, 14]];
const BOOK = {cx: 640, cy: 372, w: 260, h: 170};
const Q = {w: 290, h: 56, yStart: 150, yEnd: 258};
const ANS = {x: 872, y: 328, w: 328, h: 104};

export const SC07: React.FC = () => {
  const N = useCurrentFrame() + F0;
  const arr1 = clamp01((N - T_ARR1) / 16);
  const bn = N - T_BOOK;
  const bookS = bn < 0 ? 0 : 0.2 + 0.8 * scaleIn(bn, 21);
  const bookOp = bn < 0 ? 0 : fadeIn(bn, 6);
  const hl = clamp01((N - T_HL) / 12);
  // 问句气泡：中心 y 150 → 258
  const qy = N < T_FLY ? Q.yStart : Q.yEnd - (Q.yEnd - Q.yStart) * powOutRemain(N - T_FLY, 22, 2.5);
  const arr2 = clamp01((N - T_ARR2) / 12);
  const an = N - T_ANS;
  const ansS = an < 0 ? 0 : 0.6 + 0.4 * scaleIn(an, 10);
  const ansOp = an < 0 ? 0 : fadeIn(an, 6);
  const citeOp = fadeIn(N - T_CITE, 8);

  return (
    <div style={{position: 'absolute', inset: 0}}>
      {/* 左：文档堆（2 帧错峰、中心缩放） */}
      {DOCS.map(([x, y, rot], i) => {
        const n = N - T_DOCS - stagger(i, 2);
        if (n < 0) return null;
        const s = 0.2 + 0.8 * scaleIn(n, 21);
        return (
          <div key={i} style={{position: 'absolute', left: x, top: y, width: 64, height: 80, opacity: fadeIn(n, 6), transform: `rotate(${rot}deg) scale(${s.toFixed(4)})`, transformOrigin: '50% 60%'}}>
            <DocIcon x={0} y={0} w={64} h={80} lines={4} sw={2.5} />
          </div>
        );
      })}
      <SoftIn N={N} f0={T_PILL1}>
        <StepPill cx={250} y={458} text="资料" />
      </SoftIn>
      {/* 箭头 ① ② */}
      <Svg>
        <LineArrow x0={352} y0={AXIS} x1={478} y1={AXIS} p={arr1} />
        <LineArrow x0={784} y0={AXIS} x1={862} y1={AXIS} p={arr2} />
      </Svg>
      {/* 中：手册（书）+ 紫胶囊「知识库」 */}
      {bookOp > 0 ? <BookIcon cx={BOOK.cx} cy={BOOK.cy} w={BOOK.w} h={BOOK.h} s={bookS} opacity={bookOp} lines={4} hl={hl} hlLine={1} /> : null}
      <SoftIn N={N} f0={T_PILL2}>
        <StepPill cx={640} y={458} text="知识库" w={150} active />
      </SoftIn>
      {/* 上：问句气泡 → 落到书上 */}
      <SoftIn N={N} f0={T_Q}>
        <Bubble x={640 - Q.w / 2} y={qy - Q.h / 2} w={Q.w} h={Q.h} tail="down" text="差旅报销的上限是多少？" fontSize={22} weight={600} />
      </SoftIn>
      {/* 右：答复气泡（自箭头尖 (872,380) 弹出）+ 引用角标 */}
      {ansOp > 0 ? (
        <div style={{position: 'absolute', inset: 0, opacity: ansOp, transformOrigin: '0 0', transform: `translate(${ANS.x}px, ${AXIS}px) scale(${ansS.toFixed(4)}) translate(${-ANS.x}px, ${-AXIS}px)`}}>
          <Bubble x={ANS.x} y={ANS.y} w={ANS.w} h={ANS.h} tail="left" tailAt={0.5}>
            <div style={{position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 8, fontFamily: "'Noto Sans SC','PingFang SC',sans-serif", fontWeight: 600, fontSize: 22, color: WHITE, lineHeight: 1, whiteSpace: 'nowrap', transform: 'translateY(-1px)'}}>
              <div>住宿上限每天 600 元<span style={{color: PURPLE_LIGHT, fontWeight: 800, opacity: citeOp, marginLeft: 2}}>[1]</span></div>
              <div>一线城市 800 元<span style={{color: PURPLE_LIGHT, fontWeight: 800, opacity: citeOp, marginLeft: 2}}>[2]</span></div>
            </div>
          </Bubble>
        </div>
      ) : null}
      <SoftIn N={N} f0={T_PILL3}>
        <StepPill cx={1036} y={458} text="作答" />
      </SoftIn>
    </div>
  );
};
