import {rnd} from '../../common';

/**
 * 二维向量空间（SC17 首次出现；第 3 章 G5 的 SC23「把问题也变成向量去索引里找最近的邻居」复用同一分布）。
 * 用法：`import {VSPACE, VSPACE_POINTS} from '../G4/vspace'`。所有量为画布坐标（1280×720），网格 x 240–1040 / y 195–595，格 40。
 * 灰点由 rnd(seed, i, k) 拒绝采样生成（避开两紫点、远点与标签框，点间距 ≥24），VSPACE_POINTS[i].order 为亮起顺序（0 起）。
 */
export const VSPACE = {
  x0: 240, x1: 1040, y0: 195, y1: 595, cell: 40,
  seed: 17, count: 40, r: 5,
  /** 两个相邻紫点（退款流程 / 怎么把钱要回来）与一个远处灰点（年假规定） */
  A: {x: 600, y: 380, label: '退款流程'},
  B: {x: 650, y: 400, label: '怎么把钱要回来'},
  FAR: {x: 900, y: 262, label: '年假规定'},
  /** 标签框（含描边外框），供采样避让与 G5 复位 */
  LABEL_A: {x: 475, y: 306, w: 140, h: 38},
  LABEL_B: {x: 605, y: 439, w: 230, h: 38},
  LABEL_FAR: {x: 830, y: 282, w: 140, h: 36},
  LABEL_NEAR: {x: 676, y: 352, w: 88, h: 36},
  /** 邻居高亮圈 */
  RING: {cx: 625, cy: 390, r: 46},
};
export type VPt = {x: number; y: number; order: number};

const inRect = (x: number, y: number, r: {x: number; y: number; w: number; h: number}, pad = 8) => x > r.x - pad && x < r.x + r.w + pad && y > r.y - pad && y < r.y + r.h + pad;

export const vspacePoints = (): VPt[] => {
  const {x0, x1, y0, y1, seed, count, A, B, FAR} = VSPACE;
  const pts: Array<{x: number; y: number}> = [];
  for (let i = 0; i < count; i++) {
    let placed = false;
    for (let k = 0; k < 60 && !placed; k++) {
      const x = x0 + 14 + rnd(seed, i, k, 1) * (x1 - x0 - 28);
      const y = y0 + 14 + rnd(seed, i, k, 2) * (y1 - y0 - 28);
      if (Math.hypot(x - A.x, y - A.y) < 70 || Math.hypot(x - B.x, y - B.y) < 70 || Math.hypot(x - FAR.x, y - FAR.y) < 34) continue;
      if (inRect(x, y, VSPACE.LABEL_A) || inRect(x, y, VSPACE.LABEL_B) || inRect(x, y, VSPACE.LABEL_FAR) || inRect(x, y, VSPACE.LABEL_NEAR)) continue;
      if (pts.some((p) => Math.hypot(p.x - x, p.y - y) < 24)) continue;
      pts.push({x, y});
      placed = true;
    }
  }
  // 亮起顺序：按 rnd 洗牌
  const idx = pts.map((_, i) => i).sort((a, b) => rnd(seed, a, 99) - rnd(seed, b, 99));
  const order = new Array<number>(pts.length);
  idx.forEach((i, o) => (order[i] = o));
  return pts.map((p, i) => ({x: Math.round(p.x * 10) / 10, y: Math.round(p.y * 10) / 10, order: order[i]}));
};
export const VSPACE_POINTS: VPt[] = vspacePoints();

/** 三对"相近"的灰点（距离 28–64px，互不共点），SC17 在 2902「向量就靠得近」用细灰线连起来 */
export const VSPACE_PAIRS: Array<[number, number]> = (() => {
  const out: Array<[number, number]> = [];
  const used = new Set<number>();
  const P = VSPACE_POINTS;
  for (let i = 0; i < P.length && out.length < 3; i++) {
    if (used.has(i)) continue;
    for (let j = i + 1; j < P.length; j++) {
      if (used.has(j)) continue;
      const d = Math.hypot(P[i].x - P[j].x, P[i].y - P[j].y);
      if (d >= 28 && d <= 64) {
        out.push([i, j]);
        used.add(i);
        used.add(j);
        break;
      }
    }
  }
  return out;
})();
