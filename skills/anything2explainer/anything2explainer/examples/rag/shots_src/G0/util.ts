export * from '../../ui';
import {clamp01} from '../../common';
/** 0→1 线性，len 帧 */
export const clampFrames = (n: number, len: number) => clamp01(n / len);
