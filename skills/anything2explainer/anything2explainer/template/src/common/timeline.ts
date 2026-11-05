// 由 scripts/tts_build.py 生成（占位：跑过配音后会被覆盖）。帧号 1 起含端点。
export const TOTAL_FRAMES = 300;
export const CHAPTER_STARTS: Array<{n: number; title: string; from: number}> = [];
export type Sentence = {id: string; chapter: number; from: number; to: number; text: string};
export const SENTENCES: Sentence[] = [];
