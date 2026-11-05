import React from 'react';
import {useCurrentFrame} from 'remotion';
import {clamp01, emphasisPulse, FONT_HEAVY} from '../../common';
import {Box, DBIcon, DocIcon, Svg, Check, CText, PURPLE, GREY, GREY_LIGHT, WHITE, GREEN, GLOW_PURPLE_S, PILL_SHADOW, slideUp, scaleIn, fadeIn, SoftIn} from '../../ui';
import {Anchor, mixHex, mixK} from './g5util';

/**
 * SC21 提问的那一刻（3708–3821，S21）。节拍：3716 手册建好了 / 3741 用户提问 / 3781 考试才开始。
 * 第 3 章流程轨 3822 才出现，本镜头可用 y 110–620。末 2 帧不离场（SC22 硬切）。
 */
export const F0 = 3708;
const T_DB = 3710, T_CHECK = 3716, T_BOX = 3718, T_TYPE = 3741, T_SEND = 3763, T_EXAM = 3775, T_FLIP = 3783;
const QUESTION = '差旅报销的上限是多少？';

export const SC21: React.FC = () => {
  const N = useCurrentFrame() + F0;
  // 知识库 + 绿勾
  const sDb = scaleIn(N - T_DB);
  const pCheck = clamp01((N - T_CHECK) / 12);
  // 输入框
  // QC v1：Δ 300→240 且延后 3 帧再 6 帧淡入 → 可见时框底 ≤605，不再穿字幕带 y637–690
  const boxDy = slideUp(N - T_BOX, 240);
  const boxOp = fadeIn(N - T_BOX - 3, 6);
  const chars = N < T_TYPE ? 0 : Math.min(QUESTION.length, Math.floor((N - T_TYPE) / 2) + 1);
  const cursorOn = Math.floor((N - F0) / 8) % 2 === 0;
  // 发送按钮：灰→紫 11 帧 + 脉冲
  const kSend = mixK(N - T_SEND);
  const sendFill = mixHex(GREY, PURPLE, kSend);
  const sSend = emphasisPulse(N - (T_SEND + 2), {peak: 1.16, up: 10, hold: 4, down: 12});
  // 考卷：缩放入场 → 翻开
  const sExam = scaleIn(N - T_EXAM, 14);
  const flip = clamp01((N - T_FLIP) / 8); // 封面 scaleX 1→0
  const open = clamp01((N - T_FLIP - 6) / 6); // 翻开的封面（左侧）0→1
  const EX = 945, EY = 246, EW = 70, EH = 88;
  return (
    <div style={{position: 'absolute', inset: 0}}>
      {/* 左上：知识库（手册）+ 绿勾 */}
      {sDb > 0 ? (
        <Anchor cx={300} cy={300} s={sDb} opacity={fadeIn(N - T_DB, 6)}>
          <DBIcon cx={300} cy={290} w={96} h={104} accent={PURPLE} label="知识库" labelSize={24} />
        </Anchor>
      ) : null}
      <Svg>
        <Check cx={372} cy={246} size={54} color={GREEN} sw={7} p={pCheck} />
      </Svg>

      {/* 右上：考卷（3775 缩放入场，3783 翻开） */}
      {sExam > 0 ? (
        <Anchor cx={EX + EW / 2} cy={EY + EH / 2} s={sExam} opacity={fadeIn(N - T_EXAM, 6)}>
          <DocIcon x={EX} y={EY} w={EW} h={EH} lines={5} accent={PURPLE} />
          {/* 翻开后的封面（左侧，背面灰）：以右边为轴 0→1 */}
          {open > 0 ? (
            <div style={{position: 'absolute', left: EX - EW, top: EY, width: EW, height: EH, boxSizing: 'border-box', background: '#141414', border: `2px solid ${GREY_LIGHT}`, borderRadius: 3, transformOrigin: '100% 50%', transform: `scaleX(${open.toFixed(3)})`}}>
              {[0, 1, 2, 3].map((i) => <div key={i} style={{position: 'absolute', left: 10, top: 22 + i * 14, width: i === 3 ? 26 : 46, height: 3, background: GREY, opacity: 0.8}} />)}
            </div>
          ) : null}
          {/* 封面：以左边为轴 1→0 */}
          {flip < 1 ? (
            <div style={{position: 'absolute', left: EX, top: EY, width: EW, height: EH, boxSizing: 'border-box', background: '#000', border: `2px solid ${WHITE}`, borderRadius: 3, transformOrigin: '0 50%', transform: `scaleX(${(1 - flip).toFixed(3)})`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: FONT_HEAVY, fontWeight: 800, fontSize: 22, color: WHITE, letterSpacing: 2, writingMode: 'vertical-rl'}}>
              考卷
            </div>
          ) : null}
        </Anchor>
      ) : null}
      {/* 闪烁整改：SC21 不在白名单，「考试开始」改 SoftIn（f0 不变） */}
      <SoftIn N={N} f0={T_FLIP}>
        <CText cx={EX + EW / 2} cy={EY + EH + 23} size={24} weight={600} color={WHITE}>考试开始</CText>
      </SoftIn>

      {/* 中央：聊天输入框 720×80 @ (640,420) */}
      {boxOp > 0 ? (
        <div style={{position: 'absolute', left: 0, top: boxDy, width: 1280, height: 720, opacity: boxOp}}>
          <Box x={280} y={380} w={720} h={80} r={20} sw={2} style={{filter: PILL_SHADOW}} />
          {/* 文本 + 光标 */}
          <div style={{position: 'absolute', left: 312, top: 380, height: 80, display: 'flex', alignItems: 'center', fontFamily: FONT_HEAVY, fontWeight: 500, fontSize: 30, color: WHITE, letterSpacing: 1, whiteSpace: 'pre'}}>
            <span style={{transform: 'translateY(-2px)'}}>{QUESTION.slice(0, chars)}</span>
            <span style={{display: 'inline-block', width: 3, height: 36, marginLeft: 3, background: WHITE, opacity: cursorOn ? 1 : 0}} />
          </div>
          {/* 发送按钮 */}
          <div style={{position: 'absolute', left: 950 - 26, top: 420 - 26, width: 52, height: 52, borderRadius: 26, background: sendFill, boxShadow: kSend > 0.5 ? GLOW_PURPLE_S : undefined, transform: `scale(${sSend.toFixed(4)})`}}>
            <svg width={52} height={52} viewBox="0 0 52 52" style={{position: 'absolute', left: 0, top: 0}}>
              <path d="M14 26 L38 15 L30 26 L38 37 Z" fill={WHITE} stroke={WHITE} strokeWidth={1.5} strokeLinejoin="round" />
              <line x1={14} y1={26} x2={30} y2={26} stroke={sendFill} strokeWidth={1.5} />
            </svg>
          </div>
        </div>
      ) : null}
    </div>
  );
};
