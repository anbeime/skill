import type {ShotDef, BgSpec} from '../../common';
import {SC21} from './SC21';
import {SC22} from './SC22';
import {SC23} from './SC23';
import {SC24} from './SC24';
import {SC25} from './SC25';
// 组 G5 镜头表 / 背景覆写。数组顺序即层序（后者在上）。帧区间见 rag/分镜表.md 与 rag/script/timeline.md。
export const SHOTS_G5: ShotDef[] = [
  {id: 'SC21', from: 3708, to: 3821, Comp: SC21},
  {id: 'SC22', from: 3822, to: 4056, Comp: SC22},
  {id: 'SC23', from: 4057, to: 4225, Comp: SC23},
  {id: 'SC24', from: 4226, to: 4414, Comp: SC24},
  {id: 'SC25', from: 4415, to: 4676, Comp: SC25},
];
export const BG_G5: BgSpec[] = [];
