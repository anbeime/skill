import type {ShotDef, BgSpec} from '../../common';
import {SC26} from './SC26';
import {SC27} from './SC27';
import {SC28} from './SC28';
import {SC29} from './SC29';
import {SC30} from './SC30';
// 组 G6 镜头表 / 背景覆写。数组顺序即层序（后者在上）。帧区间见 rag/分镜表.md 与 rag/script/timeline.md。
// 第 3 章下半：SC26 重排 4677–4926 / SC27 像精排 4927–5017 / SC28 组装上下文 5018–5313 / SC29 生成 5314–5564 / SC30 可追溯 5565–5696
export const SHOTS_G6: ShotDef[] = [
  {id: 'SC26', from: 4677, to: 4926, Comp: SC26},
  {id: 'SC27', from: 4927, to: 5021, Comp: SC27}, // QC v2：延到 5021 做淡出，与 SC28 重叠 4 帧
  {id: 'SC28', from: 5018, to: 5313, Comp: SC28},
  {id: 'SC29', from: 5314, to: 5564, Comp: SC29},
  {id: 'SC30', from: 5565, to: 5696, Comp: SC30},
];
export const BG_G6: BgSpec[] = [];
