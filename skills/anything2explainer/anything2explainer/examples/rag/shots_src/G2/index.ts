import type {ShotDef, BgSpec} from '../../common';
import {SC06} from './SC06';
import {SC07} from './SC07';
import {SC08} from './SC08';
import {SC09} from './SC09';
import {SC10} from './SC10';
// 组 G2 镜头表 / 背景覆写。数组顺序即层序（后者在上）。帧区间见 rag/分镜表.md 与 rag/script/timeline.md。
export const SHOTS_G2: ShotDef[] = [
  {id: 'SC06', from: 744, to: 870, Comp: SC06},
  {id: 'SC07', from: 871, to: 1012, Comp: SC07},
  {id: 'SC08', from: 1013, to: 1129, Comp: SC08},
  {id: 'SC09', from: 1130, to: 1328, Comp: SC09},
  {id: 'SC10', from: 1329, to: 1480, Comp: SC10},
];
export const BG_G2: BgSpec[] = [];
