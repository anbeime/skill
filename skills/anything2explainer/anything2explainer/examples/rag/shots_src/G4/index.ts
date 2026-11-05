import type {ShotDef, BgSpec} from '../../common';
import {SC16} from './SC16';
import {SC17} from './SC17';
import {SC18} from './SC18';
import {SC19} from './SC19';
import {SC20} from './SC20';
// 组 G4 镜头表 / 背景覆写。数组顺序即层序（后者在上）。帧区间见 rag/分镜表.md 与 rag/script/timeline.md。
export const SHOTS_G4: ShotDef[] = [
  {id: 'SC16', from: 2686, to: 2860, Comp: SC16},
  {id: 'SC17', from: 2861, to: 3033, Comp: SC17},
  {id: 'SC18', from: 3034, to: 3298, Comp: SC18},
  {id: 'SC19', from: 3299, to: 3482, Comp: SC19},
  {id: 'SC20', from: 3483, to: 3662, Comp: SC20},
];
export const BG_G4: BgSpec[] = [];
