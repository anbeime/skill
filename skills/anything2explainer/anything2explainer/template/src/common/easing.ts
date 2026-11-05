// 共用缓动（数值取自风格来源原片的逐帧实测）。所有函数纯、无副作用；n = 相对起始帧（N − f0）。
export const clamp01 = (v: number) => Math.min(1, Math.max(0, v));

/** 自下滑入进度 0→1：1 − (1 − n/N)^p。seg_25 实测公式 Δ305 / 图标组 Δ320 / 上箭头 Δ172 三处均精确吻合 (1−n/22)^2.5，
 *  比指数式 k^n 更准（指数尾部误差 >10px）。用法：y = yEnd + Δ·(1 − slideIn(n))，或 y = yEnd + Δ·powOutRemain(n)。 */
export const slideIn = (n: number, N = 22, p = 2.5) => 1 - Math.pow(1 - clamp01(n / N), p);
/** 幂缓出"剩余量" (1 − n/N)^p —— 直接乘位移 Δ。seg_27 漏斗层升起用 N=28、p=2.5；天平用 N=21、p=3（easeOutCubic）。 */
export const powOutRemain = (n: number, N = 22, p = 2.5) => Math.pow(1 - clamp01(n / N), p);
/** 指数缓出 1 − k^n（seg_20 横向标签滑入 k≈0.92；seg_26 段首重排版 k≈0.78）。返回进度 0→1。 */
export const expOut = (k: number) => (n: number) => (n <= 0 ? 0 : 1 - Math.pow(k, n));
/** 幂缓入 t^p（离场加速，seg_26 实测幂 1.7–2.0，KL 组 Δ≈0.69·t²、顶胶囊 Δ≈0.37·t^1.71）。t∈[0,1]。
 *  若按"Δ = c·t^p（t 为帧数）"写法，直接用 Math.pow(n, p) 乘系数即可。 */
export const powIn = (p: number) => (t: number) => Math.pow(clamp01(t), p);
/** 幂 easeInOut：t<0.5 → 0.5·(2t)^p；否则 1 − 0.5·(2−2t)^p。seg_25 整页滚动 p=2.5、N=43（cubic-bezier(0.6,0,0.4,1) 可近似）。 */
export const easeInOutPow = (p = 2.5) => (t: number) => {
  t = clamp01(t);
  return t < 0.5 ? 0.5 * Math.pow(2 * t, p) : 1 - 0.5 * Math.pow(2 - 2 * t, p);
};
export const easeOutCubic = (t: number) => 1 - Math.pow(1 - clamp01(t), 3);
export const easeInOutCubic = easeInOutPow(3);
export const easeOutQuad = (t: number) => 1 - Math.pow(1 - clamp01(t), 2);

/** CSS cubic-bezier(x1,y1,x2,y2) 求值（牛顿迭代 + 二分兜底），返回 t∈[0,1] → 进度。 */
export const cubicBezier = (x1: number, y1: number, x2: number, y2: number) => {
  const A = (a1: number, a2: number) => 1 - 3 * a2 + 3 * a1;
  const B = (a1: number, a2: number) => 3 * a2 - 6 * a1;
  const C = (a1: number) => 3 * a1;
  const calc = (u: number, a1: number, a2: number) => ((A(a1, a2) * u + B(a1, a2)) * u + C(a1)) * u;
  const slope = (u: number, a1: number, a2: number) => 3 * A(a1, a2) * u * u + 2 * B(a1, a2) * u + C(a1);
  return (t: number) => {
    t = clamp01(t);
    if (t === 0 || t === 1) return t;
    let u = t;
    for (let i = 0; i < 8; i++) {
      const s = slope(u, x1, x2);
      if (Math.abs(s) < 1e-6) break;
      u -= (calc(u, x1, x2) - t) / s;
    }
    if (u < 0 || u > 1 || Math.abs(calc(u, x1, x2) - t) > 1e-4) {
      let lo = 0, hi = 1;
      for (let i = 0; i < 40; i++) {
        u = (lo + hi) / 2;
        if (calc(u, x1, x2) < t) lo = u; else hi = u;
      }
    }
    return calc(u, y1, y2);
  };
};
/** 21 帧缩放入场曲线 cubic-bezier(0.10,0.10,0.35,1)（分析稿记录值）。用法 scale = s0 + (s1−s0)·BEZ_SCALE_IN(n/21)。 */
export const BEZ_SCALE_IN = cubicBezier(0.1, 0.1, 0.35, 1);

/** 强调缩放脉冲（seg_25 两次实测）：scale 1 → peak(1.11–1.147) → 1，去 up 帧、停 hold 帧、回 down 帧，easeInOut，无透明度变化。
 *  连接线/箭头不参与；与字幕起始同步（字幕起 +2 帧开始）。n<0 或结束后返回 1。 */
export const emphasisPulse = (
  n: number,
  {peak = 1.11, up = 13, hold = 4, down = 13, ease = easeInOutPow(2.5)}: {peak?: number; up?: number; hold?: number; down?: number; ease?: (t: number) => number} = {},
) => {
  if (n <= 0) return 1;
  if (n < up) return 1 + (peak - 1) * ease(n / up);
  if (n < up + hold) return peak;
  if (n < up + hold + down) return peak - (peak - 1) * ease((n - up - hold) / down);
  return 1;
};

/**
 * 关键帧线性插值（t 为原片帧号或相对帧）。
 * ⚠ 首值陷阱：t < 首关键帧时返回**首值**（不是 0）——中段才生效的曲线必须以 [镜头起始帧, 起始值] 开头，
 *   否则镜头前半段会一直停在第一个关键帧的值上。t > 末关键帧时返回末值。
 * 可选 ease：对每段内的归一化进度做缓动（默认线性）。
 */
export const kf = (t: number, pairs: Array<[number, number]>, ease: (u: number) => number = (u) => u) => {
  if (pairs.length === 0) return 0;
  if (t <= pairs[0][0]) return pairs[0][1];
  for (let i = 1; i < pairs.length; i++) {
    const [t0, v0] = pairs[i - 1];
    const [t1, v1] = pairs[i];
    if (t <= t1) return t1 === t0 ? v1 : v0 + (v1 - v0) * ease((t - t0) / (t1 - t0));
  }
  return pairs[pairs.length - 1][1];
};
/** 阶梯保持：t < 首帧 → 首值；否则取最近一个 ≤t 的关键帧值（硬切序列、glitch 状态机用）。 */
export const stepKf = (t: number, pairs: Array<[number, number]>) => {
  if (pairs.length === 0) return 0;
  if (t < pairs[0][0]) return pairs[0][1];
  for (let i = pairs.length - 1; i >= 0; i--) if (t >= pairs[i][0]) return pairs[i][1];
  return pairs[0][1];
};
/** 确定性伪随机 [0,1)（按任意个数字种子），供各组做粒子/抖动，不得用 Math.random。 */
export const rnd = (...seeds: number[]) => {
  let h = 2166136261;
  for (const s of seeds) {
    h ^= Math.floor(s * 1000003) & 0xffffffff;
    h = Math.imul(h, 16777619);
  }
  h ^= h >>> 13;
  h = Math.imul(h, 0x5bd1e995);
  h ^= h >>> 15;
  return ((h >>> 0) % 100000) / 100000;
};
