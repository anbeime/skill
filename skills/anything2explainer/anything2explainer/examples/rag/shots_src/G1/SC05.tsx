import React from 'react';
import {useCurrentFrame} from 'remotion';
import {FONT_HEAVY, FONT_ORB, powOutRemain, easeInOutPow, clamp01} from '../../common';
import {LLMIcon, CText, Pill, Box, DocIcon, PURPLE, PURPLE_LIGHT, GREY, WHITE, ORANGE, TEXT_GLOW, fadeIn, scaleIn, abs, SoftIn} from '../../ui';

/**
 * SC05 重新训练？（613–743）。节拍：621 怎么办 / 637 重新训练 / 670 成本太高 / 692 数据又变了。
 * 清场重排：中央 LLMIcon (640,330) 缩放入场；上方 Orbitron「?」SoftIn；637 紫色循环箭头绕 LLM draw-on 24 帧 + 底部「重新训练」胶囊 SoftIn；
 * 670 左下三根橙色成本柱 2 帧错峰长出 + ¥ 逐个弹出 + 「成本」胶囊；674 右下日历卡缩放入场，692 翻页 10 帧（今天→明天，文档变灰）+ 704「已过期」橙标 SoftIn。
 * 本镜头无 glitch（协议 §8 不在白名单）。末帧不做离场（G2 SC06 硬切）。
 */
const F0 = 613;
const C = {cx: 640, cy: 330};
const R = 128;
const A0 = -70, SWEEP = 320; // 起止角（屏幕坐标，顺时针为正），缺口在顶部对着「?」
const BARS = [
  {x: 176, h: 70},
  {x: 238, h: 118},
  {x: 300, h: 172},
];
const BASE_Y = 560;
const CAL = {x: 950, y: 384, w: 180, h: 186, head: 46};

const pt = (deg: number, r = R) => [C.cx + r * Math.cos((deg * Math.PI) / 180), C.cy + r * Math.sin((deg * Math.PI) / 180)] as const;

/** 循环箭头（SVG）：p 0→1 自起点长出，箭头骑在尖端 */
const LoopArrow: React.FC<{p: number}> = ({p}) => {
  if (p <= 0) return null;
  const segs = 72;
  const end = A0 + SWEEP * p;
  const pts: string[] = [];
  for (let i = 0; i <= segs; i++) {
    const a = A0 + (end - A0) * (i / segs);
    const [x, y] = pt(a);
    pts.push(`${x.toFixed(1)},${y.toFixed(1)}`);
  }
  const [tx, ty] = pt(end);
  const rad = (end * Math.PI) / 180;
  const ux = -Math.sin(rad), uy = Math.cos(rad); // 顺时针切向
  const hl = 20 * clamp01(p * 6), hw = 9 * clamp01(p * 6);
  const bx = tx - ux * hl, by = ty - uy * hl;
  const px = -uy, py = ux;
  return (
    <svg width={1280} height={720} viewBox="0 0 1280 720" style={{position: 'absolute', left: 0, top: 0, overflow: 'visible', filter: 'drop-shadow(0 0 6px rgba(102,45,248,.85))'}}>
      <polyline points={pts.join(' ')} fill="none" stroke={PURPLE_LIGHT} strokeWidth={4} strokeLinecap="round" strokeLinejoin="round" />
      <polygon points={`${tx.toFixed(1)},${ty.toFixed(1)} ${(bx + px * hw).toFixed(1)},${(by + py * hw).toFixed(1)} ${(bx - px * hw).toFixed(1)},${(by - py * hw).toFixed(1)}`} fill={PURPLE_LIGHT} />
    </svg>
  );
};

/** 日历单页：紫色页眉 + 文档小图标 */
const CalPage: React.FC<{title: string; docColor: string; children?: React.ReactNode}> = ({title, docColor, children}) => (
  <div style={{position: 'absolute', inset: 0, borderRadius: 8, overflow: 'hidden', background: '#000'}}>
    <div style={{position: 'absolute', left: 0, top: 0, width: CAL.w - 4, height: CAL.head, background: PURPLE, borderBottom: `2px solid ${WHITE}`}}>
      <CText cx={(CAL.w - 4) / 2} cy={CAL.head / 2} size={28} weight={800} color={WHITE} dy={-2}>
        {title}
      </CText>
    </div>
    <DocIcon x={(CAL.w - 4) / 2 - 27} y={CAL.head + 24} w={54} h={66} lines={4} sw={2} color={docColor} />
    {children}
  </div>
);

export const SC05: React.FC = () => {
  const N = useCurrentFrame() + F0;
  const sLLM = scaleIn(N - F0, 21);
  const loopP = 1 - Math.pow(1 - clamp01((N - 637) / 24), 1.8);
  const nCost = N - 670;
  const baseW = 200 * (1 - powOutRemain(nCost, 12, 2.5));
  const sCal = scaleIn(N - 674, 21);
  const flip = easeInOutPow(2)(clamp01((N - 692) / 10));
  return (
    <div style={abs(0, 0, 1280, 720)}>
      {/* 中央 LLM */}
      {sLLM > 0 ? (
        <div style={{...abs(0, 0, 1280, 720), transformOrigin: `${C.cx}px ${C.cy}px`, transform: sLLM < 1 ? `scale(${sLLM.toFixed(3)})` : undefined, opacity: clamp01(0.15 + 1.4 * sLLM)}}>
          <LLMIcon cx={C.cx} cy={C.cy} size={170} glow />
        </div>
      ) : null}
      {/* 「?」 */}
      <SoftIn N={N} f0={621}>
        <CText cx={640} cy={150} size={90} weight={700} family={FONT_ORB} color={WHITE} dy={0} shadow={TEXT_GLOW}>
          ?
        </CText>
      </SoftIn>
      {/* 循环箭头 + 「重新训练」 */}
      <LoopArrow p={loopP} />
      <SoftIn N={N} f0={645}>
        <Pill x={565} y={C.cy + R - 21} w={150} h={42} fill="#000" stroke={PURPLE_LIGHT} sw={2} text="重新训练" fontSize={28} weight={700} family={FONT_HEAVY} textDy={-2} />
      </SoftIn>
      {/* 成本柱 */}
      {nCost >= 0 ? (
        <div>
          <div style={{...abs(168, BASE_Y - 1, baseW, 2), background: WHITE}} />
          {BARS.map((b, i) => {
            const n = nCost - 2 * i;
            if (n < 0) return null;
            const h = b.h * (1 - powOutRemain(n, 16, 2.5));
            const k = clamp01((n - 12) / 12);
            const ys = k + 0.25 * Math.sin(Math.PI * k);
            return (
              <React.Fragment key={i}>
                <div style={{...abs(b.x, BASE_Y - h, 46, h), boxSizing: 'border-box', border: `2px solid ${WHITE}`, borderBottom: 'none', background: 'linear-gradient(180deg,#F8DCD2 0%,#EE8F70 35%,#E34F27 70%,#E34F27 100%)'}} />
                {k > 0 ? (
                  <CText cx={b.x + 23} cy={BASE_Y - b.h - 26} size={34} weight={900} color={ORANGE} dy={-2} shadow="0 0 10px rgba(240,95,65,.6)" style={{transform: `translate(-50%,-50%) scale(${ys.toFixed(3)})`}}>
                    ¥
                  </CText>
                ) : null}
              </React.Fragment>
            );
          })}
          <div style={{opacity: fadeIn(nCost, 8)}}>
            <Pill x={218} y={574 + 40 * powOutRemain(nCost, 16, 2.5)} w={100} h={40} fill="#000" stroke={WHITE} sw={2} text="成本" fontSize={26} weight={700} family={FONT_HEAVY} textDy={-2} />
          </div>
        </div>
      ) : null}
      {/* 日历卡 */}
      {sCal > 0 ? (
        <div style={{...abs(0, 0, 1280, 720), transformOrigin: `${CAL.x + CAL.w / 2}px ${CAL.y + CAL.h / 2}px`, transform: sCal < 1 ? `scale(${sCal.toFixed(3)})` : undefined, opacity: clamp01(0.15 + 1.4 * sCal)}}>
          <Box x={CAL.x} y={CAL.y} w={CAL.w} h={CAL.h} r={10} fill="#000" stroke={WHITE} sw={2} style={{overflow: 'hidden'}}>
            {/* 底页：明天（文档灰 + 已过期） */}
            <CalPage title="明天" docColor={GREY}>
              <SoftIn N={N} f0={704}>
                <Pill x={40} y={CAL.head + 72} w={100} h={30} fill={ORANGE} sw={2} text="已过期" fontSize={22} weight={700} family={FONT_HEAVY} textDy={-1} />
              </SoftIn>
            </CalPage>
            {/* 顶页：今天，692 起绕顶边向后翻 90°（负向 rotateX：透视收缩，不溢出卡框） */}
            {flip < 1 ? (
              <div style={{position: 'absolute', inset: 0, transformOrigin: '50% 0%', transform: flip > 0 ? `perspective(700px) rotateX(${(-90 * flip).toFixed(2)}deg)` : undefined, opacity: 1 - 0.25 * flip}}>
                <CalPage title="今天" docColor={WHITE} />
              </div>
            ) : null}
          </Box>
        </div>
      ) : null}
    </div>
  );
};
