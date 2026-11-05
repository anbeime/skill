/**
 * 文本宽度估算与自适应字号——纯函数，不测 DOM，所以渲染是确定性的（同一帧在任何机器上一样）。
 *
 * em 宽取自随模板附带的字体实测平均值（fontTools 量 wght 700–900）：
 *   Noto Sans SC：小写 .566 大写 .668 数字 .590 空格 .227 半角标点 .325 汉字 1.000
 *   带重音的拉丁字母（é ü ñ ß…）.49–.69 → 取 .58
 *   U+2000 起的标点 / 箭头 / 数学符号（— … “ ” → ∑ ≤ ×）在 Noto Sans SC 里几乎都是 1em
 *   （例外：en dash .53、em dash .88——按 1 高估是安全方向，只会更早缩字号）
 *   Audiowide 大写 .788 / Orbitron 大写 .815 / Exo 2 大写 .606  → 用 EM_* 系数换算
 * scripts/tts_build.py 里的 text_em() 是同一张表的 Python 版，改这里要同步改那边。
 * 用途：中文一块字幕 ≤16 字（≈704px）本来就装得下，但英文一块 8 个词就可能 1300px 出画，
 * 所以字幕、进度条章名、章节卡标题都过一遍 fitSize 兜底。真正的约束仍在文案侧（见 narration-storyboard.md）。
 */
export const EM_HEAVY = 1;      // Noto Sans SC（正文 / 字幕 / 标题）
export const EM_WIDE = 1.18;    // Audiowide（片名、大写缩写）
export const EM_ORB = 1.2;      // Orbitron（数字 / 章序号）
export const EM_TECH = 0.92;    // Exo 2（英文技术词，斜体窄）

/** 估算一段文字的宽度，单位 em（1em = fontSize px） */
export const textEm = (s: string, emScale = 1): number => {
  let em = 0;
  for (const ch of s) {
    const c = ch.codePointAt(0) ?? 32;
    if (c >= 0x2000) em += 1;                              // CJK、全角标点，以及 U+2000 起的标点 / 箭头 / 数学符号
    else if (ch === ' ') em += 0.227;
    else if (ch >= 'A' && ch <= 'Z') em += 0.668;
    else if (ch >= '0' && ch <= '9') em += 0.59;
    else if (ch >= 'a' && ch <= 'z') em += 0.566;
    else if (c >= 0xc0 && c < 0x250) em += 0.58;           // 带重音的拉丁字母（Latin-1 / Extended-A / B）
    else em += 0.325;                                      // 半角标点
  }
  return em * emScale;
};

/** 字符数（按码点，不按 UTF-16 单元） */
const charCount = (s: string): number => [...s].length;

/**
 * 估算宽度（px）。letterSpacing 是 CSS 的 px 值：Chromium 在每个字符后面都加（含末字），
 * 且不随字号缩放，所以片头 / 章节卡这类带 letterSpacing 的大字必须把它算进去。
 */
export const textW = (s: string, size: number, emScale = 1, letterSpacing = 0): number => textEm(s, emScale) * size + letterSpacing * charCount(s);

/**
 * 超宽就等比缩字号，最低到 minSize（默认 78%）。返回值保留 1 位小数，避免亚像素抖动。
 * letterSpacing 的那部分宽度不随字号变，先从 maxW 里扣掉再解字号。
 * 缩到 minSize 仍然超宽 → 说明文案违反了每块长度预算，改文案，不要指望这里。
 */
export const fitSize = (s: string, maxW: number, size: number, minSize = size * 0.78, emScale = 1, letterSpacing = 0): number => {
  const em = textEm(s, emScale);
  const extra = letterSpacing * charCount(s);
  if (em * size + extra <= maxW) return size;
  return Math.max(minSize, Math.round(((maxW - extra) / Math.max(1e-6, em)) * 10) / 10);
};
