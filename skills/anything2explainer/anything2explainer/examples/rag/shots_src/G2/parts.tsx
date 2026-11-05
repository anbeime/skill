import React from 'react';
import {FONT_HEAVY, clamp01} from '../../common';
import {Box, CText, WHITE, GREY, GREY_LIGHT, PURPLE, PURPLE_LIGHT, BLOOM_SOFT, abs} from '../../ui';

/**
 * G2 组本地图元（ui.tsx 里没有的 RAG 语义图形）。全部纯函数；动画量（opacity / s / p）由镜头按 N 算好传入。
 * 风格：黑填充 + 白描边 2–3px；线条 = 灰白 3px 短条；紫 = 当前重点。
 */

/** 颜色线性混合（'#rrggbb' × 2，k 0→1） */
export const mixHex = (a: string, b: string, k: number) => {
  const pa = [1, 3, 5].map((i) => parseInt(a.slice(i, i + 2), 16));
  const pb = [1, 3, 5].map((i) => parseInt(b.slice(i, i + 2), 16));
  const t = clamp01(k);
  return `rgb(${pa.map((v, i) => Math.round(v + (pb[i] - v) * t)).join(',')})`;
};

/** 考卷：白边黑底竖卡 + 顶部「试卷」+ 分隔线 + 题目行（圆圈序号 + 两条灰线） */
export const ExamPaper: React.FC<{x: number; y: number; w?: number; h?: number; opacity?: number; rows?: number; title?: string}> = ({x, y, w = 300, h = 380, opacity = 1, rows = 5, title = '试 卷'}) => {
  const pad = 26;
  const rowTop = 96;
  const rowStep = (h - rowTop - 30) / rows;
  return (
    <Box x={x} y={y} w={w} h={h} r={10} sw={3} opacity={opacity} style={{filter: BLOOM_SOFT}}>
      <CText cx={w / 2} cy={46} size={30} weight={800} letterSpacing={2} dy={-2}>{title}</CText>
      <div style={{position: 'absolute', left: pad, top: 74, width: w - pad * 2, height: 2, background: WHITE, opacity: 0.85}} />
      {Array.from({length: rows}, (_, i) => {
        const ty = rowTop + i * rowStep;
        const w1 = (0.62 + 0.18 * ((i * 7) % 3) / 2) * (w - pad * 2 - 34);
        const w2 = (0.34 + 0.22 * ((i * 5 + 1) % 3) / 2) * (w - pad * 2 - 34);
        return (
          <React.Fragment key={i}>
            <div style={{position: 'absolute', left: pad, top: ty, width: 18, height: 18, boxSizing: 'border-box', border: `2px solid ${WHITE}`, borderRadius: 9}} />
            <div style={{position: 'absolute', left: pad + 34, top: ty + 4, width: w1, height: 3, background: GREY_LIGHT, opacity: 0.9}} />
            <div style={{position: 'absolute', left: pad + 34, top: ty + 18, width: w2, height: 3, background: GREY_LIGHT, opacity: 0.7}} />
          </React.Fragment>
        );
      })}
    </Box>
  );
};

/**
 * 翻开的书（两页 + 书脊）：SVG 简笔，白边 3px 黑填充，页面文字线条。
 * 以 (cx,cy) 为中心、w×h 为外接尺寸；s = 中心等比缩放；hl = 右页第 hlLine 行的紫色高亮擦出进度 0→1。
 */
export const BookIcon: React.FC<{cx: number; cy: number; w?: number; h?: number; s?: number; opacity?: number; hl?: number; hlLine?: number; lines?: number; sw?: number}> = ({cx, cy, w = 260, h = 170, s = 1, opacity = 1, hl = 0, hlLine = 1, lines = 4, sw = 3}) => {
  const x0 = cx - w / 2, y0 = cy - h / 2;
  const hw = w / 2;
  const curl = h * 0.08; // 页面上缘弧度
  const spineTop = y0 + curl + 6, spineBot = y0 + h;
  // 左页：书脊顶 → 左上（外角略高）→ 左下 → 书脊底
  const left = `M${cx},${spineTop} Q${cx - hw * 0.5},${y0 + curl - 4} ${x0},${y0} L${x0},${y0 + h - curl} Q${cx - hw * 0.5},${y0 + h - curl + 6} ${cx},${spineBot} Z`;
  const right = `M${cx},${spineTop} Q${cx + hw * 0.5},${y0 + curl - 4} ${x0 + w},${y0} L${x0 + w},${y0 + h - curl} Q${cx + hw * 0.5},${y0 + h - curl + 6} ${cx},${spineBot} Z`;
  const lineNodes: React.ReactNode[] = [];
  const innerTop = y0 + curl + 26, innerBot = y0 + h - curl - 18;
  const step = (innerBot - innerTop) / Math.max(1, lines - 1);
  for (let side = 0; side < 2; side++) {
    const lx = side === 0 ? x0 + hw * 0.18 : cx + hw * 0.16;
    const lw = hw * 0.66;
    for (let i = 0; i < lines; i++) {
      const ly = innerTop + i * step - side * 1.5;
      const wl = lw * (i === lines - 1 ? 0.6 : 0.85 + 0.15 * ((i + side) % 2));
      lineNodes.push(<rect key={`${side}-${i}`} x={lx} y={ly} width={wl} height={3} fill={GREY_LIGHT} opacity={0.85} />);
    }
  }
  const hlY = innerTop + hlLine * step - 1.5 - 5;
  const hlX = cx + hw * 0.16 - 6;
  const hlW = (hw * 0.66 + 12) * clamp01(hl);
  return (
    <svg width={1280} height={720} viewBox="0 0 1280 720" style={{position: 'absolute', left: 0, top: 0, overflow: 'visible', opacity, filter: BLOOM_SOFT}}>
      <g transform={s === 1 ? undefined : `translate(${cx} ${cy}) scale(${s.toFixed(4)}) translate(${-cx} ${-cy})`}>
        <path d={left} fill="#000" stroke={WHITE} strokeWidth={sw} strokeLinejoin="round" />
        <path d={right} fill="#000" stroke={WHITE} strokeWidth={sw} strokeLinejoin="round" />
        <line x1={cx} y1={spineTop} x2={cx} y2={spineBot} stroke={WHITE} strokeWidth={sw} />
        {hl > 0 ? <rect x={hlX} y={hlY} width={hlW} height={14} rx={3} fill={PURPLE} opacity={0.9} /> : null}
        {lineNodes}
        {/* 底部书脊厚度 */}
        <path d={`M${x0 + 4},${y0 + h - curl + 2} L${x0 + 4},${y0 + h + 8} Q${cx - hw * 0.5},${y0 + h + 14} ${cx},${spineBot + 8} Q${cx + hw * 0.5},${y0 + h + 14} ${x0 + w - 4},${y0 + h + 8} L${x0 + w - 4},${y0 + h - curl + 2}`} fill="none" stroke={WHITE} strokeWidth={sw * 0.7} opacity={0.8} />
      </g>
    </svg>
  );
};

/**
 * 对话气泡：黑底白边圆角 + 小尾巴（tail 方向）。children 为内容（绝对定位于气泡内部，或用 text 走默认居中）。
 */
export const Bubble: React.FC<{x: number; y: number; w: number; h: number; tail?: 'down' | 'left' | 'right' | 'none'; tailAt?: number; stroke?: string; fill?: string; sw?: number; r?: number; opacity?: number; glow?: string; text?: React.ReactNode; fontSize?: number; color?: string; weight?: number; style?: React.CSSProperties; children?: React.ReactNode}> = ({x, y, w, h, tail = 'down', tailAt = 0.5, stroke = WHITE, fill = '#000', sw = 2.5, r = 14, opacity = 1, glow, text, fontSize = 24, color = WHITE, weight = 600, style, children}) => {
  const tw = 16, th = 12;
  let tailPath = '';
  if (tail === 'down') {
    const tx = x + w * tailAt;
    tailPath = `M${tx - tw / 2},${y + h - 1} L${tx - 2},${y + h + th} L${tx + tw / 2},${y + h - 1}`;
  } else if (tail === 'left') {
    const ty = y + h * tailAt;
    tailPath = `M${x + 1},${ty - tw / 2} L${x - th},${ty + 2} L${x + 1},${ty + tw / 2}`;
  } else if (tail === 'right') {
    const ty = y + h * tailAt;
    tailPath = `M${x + w - 1},${ty - tw / 2} L${x + w + th},${ty + 2} L${x + w - 1},${ty + tw / 2}`;
  }
  return (
    <div style={{...abs(0, 0, 1280, 720), opacity, pointerEvents: 'none', ...style}}>
      {tail !== 'none' ? (
        <svg width={1280} height={720} viewBox="0 0 1280 720" style={{position: 'absolute', left: 0, top: 0, overflow: 'visible'}}>
          <path d={tailPath} fill={fill} stroke={stroke} strokeWidth={sw} strokeLinejoin="round" />
        </svg>
      ) : null}
      <Box x={x} y={y} w={w} h={h} r={r} fill={fill} stroke={stroke} sw={sw} glow={glow}>
        {text !== undefined ? (
          <div style={{position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: FONT_HEAVY, fontWeight: weight, fontSize, color, lineHeight: 1.35, whiteSpace: 'nowrap', transform: 'translateY(-1px)', textAlign: 'center'}}>{text}</div>
        ) : null}
        {children}
      </Box>
      {tail !== 'none' ? (
        // 盖住尾巴与框相接处的描边
        <svg width={1280} height={720} viewBox="0 0 1280 720" style={{position: 'absolute', left: 0, top: 0, overflow: 'visible'}}>
          {tail === 'down' ? <rect x={x + w * tailAt - tw / 2 + 1.5} y={y + h - sw - 1} width={tw - 3} height={sw + 1.5} fill={fill} /> : null}
          {tail === 'left' ? <rect x={x + 0.5} y={y + h * tailAt - tw / 2 + 1.5} width={sw + 1.5} height={tw - 3} fill={fill} /> : null}
          {tail === 'right' ? <rect x={x + w - sw - 2} y={y + h * tailAt - tw / 2 + 1.5} width={sw + 1.5} height={tw - 3} fill={fill} /> : null}
        </svg>
      ) : null}
    </div>
  );
};

/** 横向紫光条（R6 光条的水平版）：紫渐隐两端 + 白芯 + 紫柔光；(x,y) 为左上，w×h；alpha 为整体不透明度（SC08 用 .55–.6） */
export const LightBar: React.FC<{x: number; y: number; w: number; h: number; alpha?: number; color?: string; core?: boolean}> = ({x, y, w, h, alpha = 0.3, color = PURPLE_LIGHT, core = true}) => (
  <div style={{...abs(x, y, w, h), opacity: alpha}}>
    <div style={{position: 'absolute', inset: 0, borderRadius: h / 2, background: `linear-gradient(90deg, transparent 0%, ${color} 16%, ${color} 84%, transparent 100%)`, boxShadow: `0 0 ${h * 2.4}px ${h * 0.9}px rgba(102,45,248,.6)`}} />
    {core ? <div style={{position: 'absolute', left: w * 0.18, right: w * 0.18, top: h * 0.3, height: h * 0.4, borderRadius: h, background: 'linear-gradient(90deg, transparent 0%, #FFFFFF 28%, #FFFFFF 72%, transparent 100%)', boxShadow: '0 0 6px 1px rgba(255,255,255,.75)'}} /> : null}
  </div>
);

/** 灯泡（白线简笔）：圆泡 + 螺口 + 三道短光芒；(cx,cy) 为圆心，r 半径；glow 0→1 控制内发光 */
export const Bulb: React.FC<{cx: number; cy: number; r?: number; opacity?: number; glow?: number}> = ({cx, cy, r = 20, opacity = 1, glow = 1}) => (
  <svg width={1280} height={720} viewBox="0 0 1280 720" style={{position: 'absolute', left: 0, top: 0, overflow: 'visible', opacity, filter: BLOOM_SOFT}}>
    <circle cx={cx} cy={cy} r={r} fill={mixHex('#000000', PURPLE_LIGHT, glow * 0.9)} stroke={WHITE} strokeWidth={2.5} />
    <rect x={cx - r * 0.45} y={cy + r * 0.82} width={r * 0.9} height={r * 0.5} rx={3} fill="#000" stroke={WHITE} strokeWidth={2.5} />
    <line x1={cx - r * 0.3} y1={cy + r * 1.55} x2={cx + r * 0.3} y2={cy + r * 1.55} stroke={WHITE} strokeWidth={2.5} />
    {[-90, -135, -45].map((a) => {
      const rad = (a * Math.PI) / 180;
      const r1 = r * 1.35, r2 = r * 1.75;
      return <line key={a} x1={cx + Math.cos(rad) * r1} y1={cy + Math.sin(rad) * r1} x2={cx + Math.cos(rad) * r2} y2={cy + Math.sin(rad) * r2} stroke={WHITE} strokeWidth={2.5} strokeLinecap="round" opacity={glow} />;
    })}
  </svg>
);

/** 步骤下方的小胶囊标签（黑底白边 / 紫底），统一 130×44 26px */
export const StepPill: React.FC<{cx: number; y: number; text: string; w?: number; active?: boolean; grey?: boolean; opacity?: number}> = ({cx, y, text, w = 130, active = false, grey = false, opacity = 1}) => (
  <div style={{...abs(0, 0, 1280, 720), opacity}}>
    <Box x={cx - w / 2} y={y} w={w} h={44} r={22} fill={active ? PURPLE : '#000'} stroke={grey ? GREY : WHITE} sw={2} style={{filter: active ? 'drop-shadow(0 0 2px rgba(200,180,255,.6))' : undefined}}>
      <div style={{position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: FONT_HEAVY, fontWeight: 700, fontSize: 26, color: grey ? GREY : WHITE, lineHeight: 1, transform: 'translateY(-2px)', whiteSpace: 'nowrap'}}>{text}</div>
    </Box>
  </div>
);
