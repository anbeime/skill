import type {ShotDef, BgSpec} from '../../common';
import {SC31} from './SC31';
import {SC32} from './SC32';
import {SC33} from './SC33';
import {SC34} from './SC34';
import {SC35} from './SC35';
import {SC36} from './SC36';
import {SC37} from './SC37';
// 组 G7 镜头表 / 背景覆写。数组顺序即层序（后者在上）。帧区间见 rag/分镜表.md 与 rag/script/timeline.md。
export const SHOTS_G7: ShotDef[] = [
  {id: 'SC31', from: 5742, to: 5821, Comp: SC31},
  {id: 'SC32', from: 5822, to: 5946, Comp: SC32},
  {id: 'SC33', from: 5947, to: 6212, Comp: SC33},
  {id: 'SC34', from: 6213, to: 6406, Comp: SC34},
  {id: 'SC35', from: 6407, to: 6450, Comp: SC35},
  {id: 'SC36', from: 6451, to: 6709, Comp: SC36},
  {id: 'SC37', from: 6710, to: 6990, Comp: SC37},
];
export const BG_G7: BgSpec[] = [];
