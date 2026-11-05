import React from 'react';
import {useCurrentFrame} from 'remotion';
import {easeInOutPow, emphasisPulse, slideIn, clamp01} from '../../common';
import {Pill, CText, TechText, DocIcon, DBIcon, ArrowH, PURPLE, PURPLE_LIGHT, GREY, GREY_LIGHT, ORANGE, abs, scaleIn, fadeOut, exitAccel, SoftIn} from '../../ui';
import {BookIcon, Dial, mixColor} from './g3ui';

/**
 * SC11 手册 = 知识库（1526–1654，S11）
 * 节拍：1534 好不好用（刻度盘 draw-on）/ 1568 一半取决于手册（指针摆到 50%、书脉冲）/ 1606 知识库怎么建（胶囊翻转 → 紫「知识库」+ Knowledge Base；右侧 文档→库 小示意）
 * 流程轨 1655 才出现，本镜头可用 y 110–620；1646 起整组下摇淡出，与 SC12 硬接。
 */
const F0 = 1526;
const EASE = easeInOutPow(2.5);
const BOOK = {cx: 640, cy: 410};

export const SC11: React.FC = () => {
  const N = useCurrentFrame() + F0;
  // 离场
  const ex = N - 1646;
  const gOp = ex > 0 ? fadeOut(ex, 9) : 1;
  const gDy = ex > 0 ? exitAccel(ex, 0.9) : 0;
  // 书：21 帧缩放入场 + 1570 强调脉冲；1606 后页内文字线灰→紫（11 帧）
  const bookS = scaleIn(N - F0) * emphasisPulse(N - 1570, {peak: 1.09});
  const kb = clamp01((N - 1612) / 11);
  // 胶囊翻转（1606 起 12 帧，中点换字换色）
  const ft = N - 1606;
  const flipX = ft >= 0 && ft < 12 ? Math.abs(Math.cos((Math.PI * ft) / 12)) : 1;
  const isKB = ft >= 6;
  // 刻度盘
  const dialP = clamp01((N - 1534) / 16);
  const needle = 0.5 * EASE(clamp01((N - 1566) / 28));
  // 右侧示意（1612 起）
  const arrowP = slideIn(N - 1620, 14);

  return (
    <div style={{position: 'absolute', inset: 0, opacity: gOp, transform: gDy ? `translateY(${gDy.toFixed(1)}px)` : undefined}}>
      {/* 中央：书 */}
      <div style={{...abs(0, 0, 1280, 720), transform: `translate(${BOOK.cx}px,${BOOK.cy}px) scale(${bookS.toFixed(4)}) translate(${-BOOK.cx}px,${-BOOK.cy}px)`, transformOrigin: '0 0'}}>
        <BookIcon cx={BOOK.cx} cy={BOOK.cy} lineColor={mixColor(GREY_LIGHT, PURPLE_LIGHT, kb)} />
      </div>
      {/* 书上方胶囊：手册 → 知识库 */}
      <SoftIn N={N} f0={1538}>
        <div style={{...abs(555, 228, 170, 50), transform: `scaleX(${flipX.toFixed(4)})`}}>
          <Pill x={0} y={0} w={170} h={50} fill={isKB ? PURPLE : '#000'} sw={2.5} text={isKB ? '知识库' : '手册'} fontSize={28} weight={700} textDy={-2} glow={isKB ? '0 0 18px 4px rgba(102,45,248,.45)' : undefined} />
        </div>
      </SoftIn>
      <SoftIn N={N} f0={1614}>
        <TechText cx={640} cy={300} text="Knowledge Base" fontSize={28} scaleX={0.82} />
      </SoftIn>

      {/* 左：RAG 效果 刻度盘 */}
      <Dial cx={250} cy={440} r={80} p={dialP} v={needle} />
      <SoftIn N={N} f0={1540}>
        <CText cx={250} cy={482} size={26} weight={700}>RAG 效果</CText>
      </SoftIn>
      <SoftIn N={N} f0={1592}>
        <Pill x={212} y={322} w={76} h={30} fill={ORANGE} sw={0} text="一半" fontSize={22} weight={800} textDy={-1} glow="0 0 18px 4px rgba(240,95,65,.45)" />
      </SoftIn>

      {/* 右：文档 → 库（怎么建？） */}
      {[0, 1, 2].map((i) => {
        const s = scaleIn(N - (1612 + i * 2));
        return s > 0 ? (
          <div key={i} style={{...abs(886 + i * 14, 392 - i * 8, 40, 52), transform: `scale(${s.toFixed(4)})`}}>
            <DocIcon x={0} y={0} w={40} h={52} lines={3} glow="none" />
          </div>
        ) : null;
      })}
      <ArrowH x={972} y={396} w={56} h={24} p={arrowP} />
      {(() => {
        const s = scaleIn(N - 1622);
        return s > 0 ? (
          <div style={{...abs(1050, 362, 80, 90), transform: `scale(${s.toFixed(4)})`}}>
            <DBIcon cx={40} cy={45} w={80} h={90} accent={PURPLE} />
          </div>
        ) : null;
      })()}
      <SoftIn N={N} f0={1628}>
        <CText cx={1010} cy={488} size={26} weight={700} color={GREY}>怎么建？</CText>
      </SoftIn>
    </div>
  );
};
