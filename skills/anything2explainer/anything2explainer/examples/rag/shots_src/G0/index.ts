import type {ShotDef, BgSpec} from '../../common';
import {TOTAL_FRAMES} from '../../common';
import {Title, TITLE_RANGE, ChapterCard, CHAPTER_CARDS, Hud, HUD_RANGE, Rail, RAILS, Ending, ENDING_RANGE, EndingTop, ENDING_TOP_RANGE} from './Overlay';
// G0 = 主会话覆盖层：片头 / 章节卡 ×3 / 顶部 HUD 胶囊 / 第 2、3 章流程轨 / 片尾压黑。层序最低（Main 里排最前）。
export const SHOTS_G0: ShotDef[] = [
  {id: 'G0-Title', from: TITLE_RANGE[0], to: TITLE_RANGE[1], Comp: Title},
  ...CHAPTER_CARDS.map((c) => ({id: `G0-Chapter${c.n}`, from: c.from, to: c.to, Comp: (() => ChapterCard({card: c})) as unknown as React.FC})),
  {id: 'G0-Hud', from: HUD_RANGE[0], to: HUD_RANGE[1], Comp: Hud},
  ...RAILS.map((r, i) => ({id: `G0-Rail${i + 2}`, from: r.from, to: r.to, Comp: (() => Rail({spec: r})) as unknown as React.FC})),
];
// 压在全部内容组之上的覆盖层（Main 把它排在 G1–G8 之后）：片尾压黑（进度条之下）+ 末 30 帧连进度条一起压黑（aboveBar）
export const SHOTS_G0_TOP: ShotDef[] = [
  {id: 'G0-Ending', from: ENDING_RANGE[0], to: ENDING_RANGE[1], Comp: Ending},
  {id: 'G0-EndingTop', from: ENDING_TOP_RANGE[0], to: ENDING_TOP_RANGE[1], Comp: EndingTop, layer: 'aboveBar'},
];
export const BG_G0: BgSpec[] = [
  {from: 1, to: 10, fog: false, stars: 'none'},
  {from: TOTAL_FRAMES - 40, to: TOTAL_FRAMES, fog: false, stars: 'none'},
];
