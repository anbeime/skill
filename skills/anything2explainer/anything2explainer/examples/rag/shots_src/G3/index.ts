import type {ShotDef, BgSpec} from '../../common';
import {SC11} from './SC11';
import {SC12} from './SC12';
import {SC13} from './SC13';
import {SC14} from './SC14';
import {SC15} from './SC15';
// 组 G3 镜头表 / 背景覆写。数组顺序即层序（后者在上）。帧区间见 rag/分镜表.md 与 rag/script/timeline.md。
export const SHOTS_G3: ShotDef[] = [
  {id: 'SC11', from: 1526, to: 1654, Comp: SC11},
  {id: 'SC12', from: 1655, to: 1890, Comp: SC12},
  {id: 'SC13', from: 1891, to: 2054, Comp: SC13},
  {id: 'SC14', from: 2055, to: 2308, Comp: SC14},
  {id: 'SC15', from: 2309, to: 2685, Comp: SC15},
];
export const BG_G3: BgSpec[] = [];
