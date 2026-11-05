import React from 'react';
import {useCurrentFrame} from 'remotion';
import {slideIn} from '../../common';
import {Box, CText, TechText, Svg, LineArrow, ArrowH, WHITE, abs, slideUp, fadeIn, fadeOut, exitAccel, SoftIn} from '../../ui';
import {DocCard, DOC_ITEMS, PdfIcon, WebIcon, TableIcon, ScanIcon} from './g3ui';

/**
 * SC12 第一步 解析（1655–1890，S12）
 * 节拍：1663 第一步解析（解析器框淡入）/ 1690 PDF 网页 表格 扫描件（四图标 2 帧错峰左滑入 + 汇聚箭头 draw-on）
 *      / 1760 干净的文本（文档卡自右滑入，条目每 2 帧逐行 wipe）/ 1819 保留标题段落表格结构（三枚紫标签淡入，间隔 12 帧）
 * 1880 起左/中组左滑淡出，文档卡留到 1890 末帧，SC13 以同一 DocCard 几何承接。
 */
const F0 = 1655;
const ICON_Y = [232, 332, 432, 532];
const ICON_LABEL = ['PDF', '网页', '表格', '扫描件'];
const ICONS = [PdfIcon, WebIcon, TableIcon, ScanIcon];
export const DOC_CX = 980, DOC_CY = 400;

export const SC12: React.FC = () => {
  const N = useCurrentFrame() + F0;
  // 左/中组离场（1880 起 10 帧）
  const ex = N - 1880;
  const gOp = ex > 0 ? fadeOut(ex, 10) : 1;
  const gDx = ex > 0 ? -exitAccel(ex, 0.6) : 0;
  // 文档卡
  const dn = N - 1760;
  const docCx = DOC_CX + slideUp(dn, 320);
  const docOp = dn < 0 ? 0 : fadeIn(dn, 6);
  const reveal = Math.max(0, Math.min(DOC_ITEMS, Math.floor((N - 1766) / 2) + 1));
  const labels = [0, 1, 2].map((k) => fadeIn(N - (1819 + 12 * k), 8) * gOp);

  return (
    <>
      <div style={{position: 'absolute', inset: 0, opacity: gOp, transform: gDx ? `translateX(${gDx.toFixed(1)}px)` : undefined}}>
        {/* 左列四种文件 */}
        {ICONS.map((Icon, i) => {
          const n = N - (1690 + i * 2);
          if (n < 0) return null;
          const dx = slideUp(n, 300);
          return (
            <div key={i} style={{...abs(-dx, 0, 1280, 720), opacity: fadeIn(n, 6)}}>
              <Icon x={130} y={ICON_Y[i] - 38} />
              <CText cx={215} cy={ICON_Y[i]} size={26} weight={700} opacity={fadeIn(n - 4, 6)} style={{transform: 'translate(0,-50%)'}}>
                {ICON_LABEL[i]}
              </CText>
            </div>
          );
        })}
        {/* 汇聚箭头 → 解析器 */}
        <Svg>
          {ICON_Y.map((y, i) => (
            <LineArrow key={i} x0={306} y0={y} x1={556} y1={400 + (i - 1.5) * 20} p={slideIn(N - (1704 + i * 3), 14)} rodW={2.5} headL={18} headW={18} />
          ))}
        </Svg>
        {/* 解析器 */}
        <SoftIn N={N} f0={1663}>
          <Box x={560} y={352} w={160} h={96} r={14} sw={2.5} />
          <CText cx={640} cy={400} size={28} weight={700} color={WHITE}>解析器</CText>
          <TechText cx={640} cy={478} text="Parsing" fontSize={26} scaleX={0.82} />
        </SoftIn>
        <ArrowH x={728} y={388} w={60} h={24} p={slideIn(N - 1752, 14)} />
      </div>
      {/* 右：解析产物文档卡（不随左组离场） */}
      {dn >= 0 ? <DocCard cx={docCx} cy={DOC_CY} reveal={reveal} labels={labels} opacity={docOp} /> : null}
    </>
  );
};
