import type {ShotDef, BgSpec} from '../../common';
import {SC38} from './SC38';
import {SC39} from './SC39';
import {SC40} from './SC40';
import {SC41} from './SC41';
import {SC42} from './SC42';
import {SC43} from './SC43';
import {SC44} from './SC44';
// 组 G8 镜头表 / 背景覆写。数组顺序即层序（后者在上）。帧区间见 rag/分镜表.md 与 rag/script/timeline.md。
export const SHOTS_G8: ShotDef[] = [
  {id: 'SC38', from: 6991, to: 7167, Comp: SC38},
  {id: 'SC39', from: 7168, to: 7301, Comp: SC39},
  {id: 'SC40', from: 7302, to: 7503, Comp: SC40},
  {id: 'SC41', from: 7504, to: 7753, Comp: SC41},
  {id: 'SC42', from: 7754, to: 7869, Comp: SC42},
  {id: 'SC43', from: 7870, to: 8052, Comp: SC43},
  {id: 'SC44', from: 8053, to: 8148, Comp: SC44},
];
export const BG_G8: BgSpec[] = [];
