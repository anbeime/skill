/**
 * Append the curated ≥100★ batch into data/projects.json, refresh README
 * project lists/counts, and keep existing rows untouched.
 */
import { readFile, writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const cataloguePath = resolve(ROOT, 'data/projects.json');
const metaPath = '/tmp/jev-batch/meta.json';

const CATEGORY = {
  'different-ai/openwork': 'agent-workflows',
  'vercel/eve': 'agent-workflows',
  'vercel-labs/ai-cli': 'developer-tools',
  'typesafe-ai/skills': 'developer-tools',
  'Anil-matcha/awesome-jev-by-typesafe': 'developer-tools',
  'smithersai/smithers': 'agent-workflows',
  'Sac-Y/Jev-cu': 'browser-computer-use',
  'incoai/splash': 'open-models',
  'AbdelStark/awesome-typesafe': 'developer-tools',
  'cobanov/awesome-jev': 'developer-tools',
  'ekzhang/openjev-sglang': 'open-models',
  'usenotra/notra': 'interfaces',
  'typesafe-ai/system-one-adapter-python': 'sdk-integrations',
  'fatwang2/awesome-jev': 'developer-tools',
  'lakeday-org/perch': 'developer-tools',
  'hr98w/jev-visual': 'open-models',
  'shhivv/third-hand': 'browser-computer-use',
  'kunchenguid/compact-adviser': 'agent-workflows',
  'logicrw/awesome-jev-projects': 'developer-tools',
  'kerpopule/hermes-jev-skills': 'routing-optimization',
  'tamaratran/jev-pruner': 'agent-workflows',
  'Heman10x-NGU/openJev-verdict-2.0': 'open-models',
  'dbreunig/building-with-jev-skill': 'developer-tools',
  'Mapika/decider': 'open-models',
  'mmastrac/djev-spark': 'open-models',
};

const EVIDENCE_OVERRIDE = {
  'typesafe-ai/skills': 'skills/typesafe-ai/SKILL.md',
  'smithersai/smithers': 'apps/server/src/jev.ts',
  'Sac-Y/Jev-cu': 'scripts/jev-decide.mjs',
  'ekzhang/openjev-sglang': 'src/openjev/__init__.py',
  'usenotra/notra': 'README.md',
  'typesafe-ai/system-one-adapter-python': 'src/system_one_adapter/_client.py',
  'fatwang2/awesome-jev': '.github/workflows/jev-review.yml',
  'hr98w/jev-visual': 'jev_visual/scoring.py',
  'kunchenguid/compact-adviser': 'packages/codex-plugin/skills/compact-adviser/SKILL.md',
  'logicrw/awesome-jev-projects': 'SKILL.md',
  'kerpopule/hermes-jev-skills': 'jevkit/choose.py',
  'tamaratran/jev-pruner': 'src/jev.ts',
  'vercel/eve': 'README.md',
  'incoai/splash': 'README.md',
  'AbdelStark/awesome-typesafe': 'README.md',
  'cobanov/awesome-jev': 'README.md',
  'mmastrac/djev-spark': 'README.md',
};

const COPY = {
  'different-ai/openwork': {
    id: 'openwork',
    name: 'Openwork',
    summary: {
      en: 'An open-source cowork-style agent workspace that can run JEV-backed reviews inside CI and skill workflows.',
      zh: '开源的 cowork 风格 Agent 工作区，可在 CI 与 Skill 流程里跑 JEV 驱动的审查。',
      ja: 'CI と Skill ワークフローで JEV レビューを実行できる、オープンソースの cowork 風エージェント作業空間。',
    },
    decision: {
      en: 'Scores or gates test-coverage and review findings before merging agent-produced changes.',
      zh: '在合并 Agent 产出前，对测试覆盖与审查结论做评分或门禁。',
      ja: 'エージェント成果をマージする前に、テストカバレッジやレビュー結果を評価・ゲートします。',
    },
  },
  'vercel/eve': {
    id: 'vercel-eve',
    name: 'Eve',
    summary: {
      en: 'Vercel’s open agent framework for packaging skills, evals, and tool-using workflows.',
      zh: 'Vercel 开源的 Agent 框架，用于打包 Skill、评测与带工具的工作流。',
      ja: 'Skill・評価・ツール付きワークフローをまとめる Vercel のオープンなエージェント枠組み。',
    },
    decision: {
      en: 'Structures agent runs so later steps can apply typed judgments before acting.',
      zh: '把 Agent 运行结构化，便于后续步骤在行动前做类型化判断。',
      ja: 'エージェント実行を構造化し、行動前に型付き判断を差し込めるようにします。',
    },
  },
  'vercel-labs/ai-cli': {
    id: 'vercel-ai-cli',
    name: 'AI CLI',
    summary: {
      en: 'A terminal generator CLI that ships with an agent skill for creating content from the command line.',
      zh: '终端生成 CLI，并附带可从命令行创作内容的 Agent Skill。',
      ja: 'ターミナルからコンテンツ生成するための Agent Skill 付き CLI。',
    },
    decision: {
      en: 'Chooses generation steps and skill instructions before local CLI execution.',
      zh: '在本地 CLI 执行前选择生成步骤与 Skill 说明。',
      ja: 'ローカル CLI 実行前に生成手順と Skill 指示を選びます。',
    },
  },
  'typesafe-ai/skills': {
    id: 'typesafe-skills',
    name: 'TypeSafe Skills',
    summary: {
      en: 'Official agent skills for building against TypeSafe’s System One / JEV API.',
      zh: '面向 TypeSafe System One / JEV API 的官方 Agent Skill 集合。',
      ja: 'TypeSafe の System One / JEV API 向け公式 Agent Skill 集。',
    },
    decision: {
      en: 'Guides agents to frame Noul, Choice, and Score questions against System One.',
      zh: '指导 Agent 把 Noul / Choice / Score 问题正确提交给 System One。',
      ja: 'エージェントが Noul / Choice / Score を System One に正しく投げるよう導きます。',
    },
  },
  'Anil-matcha/awesome-jev-by-typesafe': {
    id: 'awesome-jev-by-typesafe',
    name: 'Awesome JEV by TypeSafe',
    summary: {
      en: 'An evidence-backed playbook of JEV use cases, patterns, prompts, and starter code.',
      zh: '有证据支撑的 JEV 用例、模式、提示词与起步代码手册。',
      ja: '根拠付きの JEV ユースケース・パターン・プロンプト・スターター集。',
    },
    decision: {
      en: 'Helps builders pick which typed decision pattern fits a product workflow.',
      zh: '帮助开发者判断哪种类型化决策模式适合自己的产品流程。',
      ja: 'どの型付き意思決定パターンが製品フローに合うかを選ぶ助けになります。',
    },
  },
  'smithersai/smithers': {
    id: 'smithers',
    name: 'Smithers',
    summary: {
      en: 'An agentic TypeScript workflow framework with a first-class JEV classify path.',
      zh: '以 TypeScript 配置定义工作流的 Agent 框架，内置 JEV 分类路径。',
      ja: 'TypeScript 設定でワークフローを定義し、JEV 分類パスを持つエージェント枠組み。',
    },
    decision: {
      en: 'Classifies workflow steps or review verdicts through a dedicated JEV relay.',
      zh: '通过专用 JEV 中继对工作流步骤或审查结论做分类。',
      ja: '専用の JEV 中継でワークフロー手順やレビュー判定を分類します。',
    },
  },
  'Sac-Y/Jev-cu': {
    id: 'jev-cu',
    name: 'Jev CU',
    summary: {
      en: 'Computer-use helpers that call JEV to decide the next UI action.',
      zh: '用 JEV 决定下一步界面动作的 Computer Use 辅助工具。',
      ja: '次の UI 操作を JEV に決めさせる Computer Use 補助ツール。',
    },
    decision: {
      en: 'Picks a bounded next action from observed UI state before local execution.',
      zh: '根据观察到的界面状态，在本地执行前选出有限下一步动作。',
      ja: '観測した UI 状態から、ローカル実行前に有限の次アクションを選びます。',
    },
  },
  'incoai/splash': {
    id: 'splash',
    name: 'Splash',
    summary: {
      en: 'A local Apple Silicon inference engine oriented around decision-style models.',
      zh: '面向决策类模型的本地 Apple Silicon 推理引擎。',
      ja: '意思決定系モデル向けの Apple Silicon ローカル推論エンジン。',
    },
    decision: {
      en: 'Runs local inference so apps can obtain typed judgments without a remote JEV hop.',
      zh: '在本地完成推理，让应用无需远程 JEV 也能拿到类型化判断。',
      ja: 'ローカル推論で型付き判断を返し、遠隔 JEV なしでも使えるようにします。',
    },
  },
  'AbdelStark/awesome-typesafe': {
    id: 'awesome-typesafe',
    name: 'Awesome TypeSafe',
    summary: {
      en: 'A curated list of official and community resources for TypeSafe, System One, and JEV.',
      zh: 'TypeSafe、System One 与 JEV 的官方与社区资源精选列表。',
      ja: 'TypeSafe・System One・JEV の公式／コミュニティ資源をまとめたキュレーション一覧。',
    },
    decision: {
      en: 'Surfaces which projects and docs are worth opening when building with System One.',
      zh: '帮你判断做 System One 时该先打开哪些项目与文档。',
      ja: 'System One 開発時に開くべきプロジェクト／ドキュメントを示します。',
    },
  },
  'cobanov/awesome-jev': {
    id: 'cobanov-awesome-jev',
    name: 'Awesome JEV (cobanov)',
    summary: {
      en: 'A source-backed list of projects built with JEV / TypeSafe System One.',
      zh: '基于源码核对的 JEV / TypeSafe System One 项目精选列表。',
      ja: 'JEV / TypeSafe System One で作られたプロジェクトの根拠付き一覧。',
    },
    decision: {
      en: 'Highlights repositories that demonstrate concrete typed-decision integration points.',
      zh: '标出能看清类型化决策接入点的仓库。',
      ja: '型付き意思決定の具体的な接続点が見えるリポジトリを示します。',
    },
  },
  'ekzhang/openjev-sglang': {
    id: 'openjev-sglang',
    name: 'OpenJEV SGLang',
    summary: {
      en: 'A JEV-compatible API endpoint built on open models with a prefill-only serving path.',
      zh: '基于开源模型的 JEV 兼容 API，采用 prefill-only 服务路径。',
      ja: 'オープンモデル上の JEV 互換 API。prefill-only の提供経路を使います。',
    },
    decision: {
      en: 'Serves System One–style probability answers from open models instead of hosted JEV.',
      zh: '用开源模型提供 System One 风格的概率答案，替代托管 JEV。',
      ja: 'ホスト型 JEV の代わりに、オープンモデルで System One 風の確率回答を返します。',
    },
  },
  'usenotra/notra': {
    id: 'notra',
    name: 'Notra',
    summary: {
      en: 'A product that turns work artifacts into publishable content with agent skill hooks.',
      zh: '把工作产物转成可发布内容的产品，并挂接 Agent Skill。',
      ja: '作業成果を公開コンテンツに変え、Agent Skill を接続するプロダクト。',
    },
    decision: {
      en: 'Uses skill-guided steps to decide what to extract and how to package content.',
      zh: '用 Skill 引导的步骤决定提取什么内容、如何打包发布。',
      ja: 'Skill 案内の手順で、何を抽出しどう梱包するかを決めます。',
    },
  },
  'typesafe-ai/system-one-adapter-python': {
    id: 'system-one-adapter-python',
    name: 'System One Adapter (Python)',
    summary: {
      en: 'A drop-in TypeSafeClient replacement that backs System One calls with ordinary LLM APIs.',
      zh: '可替换 TypeSafeClient 的适配器，用普通 LLM API 承接 System One 调用。',
      ja: '通常の LLM API で System One 呼び出しを受ける、TypeSafeClient 差し替えアダプタ。',
    },
    decision: {
      en: 'Maps Noul, Choice, and Score questions onto LLM providers and normalizes probabilities.',
      zh: '把 Noul / Choice / Score 问题映射到 LLM 提供方并归一化概率。',
      ja: 'Noul / Choice / Score を LLM プロバイダへ写し、確率を正規化します。',
    },
  },
  'fatwang2/awesome-jev': {
    id: 'fatwang2-awesome-jev',
    name: 'Awesome JEV (fatwang2)',
    summary: {
      en: 'A source-backed JEV directory plus a reusable JEV-only GitHub review workflow.',
      zh: '有源码依据的 JEV 目录，并附带可复用的纯 JEV GitHub Review 工作流。',
      ja: '根拠付き JEV ディレクトリと、再利用可能な JEV 専用 GitHub Review ワークフロー。',
    },
    decision: {
      en: 'Runs JEV over pull-request signals to produce review judgments in CI.',
      zh: '在 CI 里用 JEV 阅读 PR 信号并产出审查判断。',
      ja: 'CI で PR 信号を JEV に渡し、レビュー判断を出します。',
    },
  },
  'lakeday-org/perch': {
    id: 'perch',
    name: 'Perch',
    summary: {
      en: 'Semantic code linting that asks JEV / System One whether findings should fire.',
      zh: '语义代码检查：用 JEV / System One 判断某条发现是否该触发。',
      ja: '発見を発火すべきかを JEV / System One に問うセマンティック lint。',
    },
    decision: {
      en: 'Scores lint candidates against project rules before reporting issues.',
      zh: '在报告问题前，按项目规则给 lint 候选项打分。',
      ja: '問題報告の前に、プロジェクト規則で lint 候補を採点します。',
    },
  },
  'hr98w/jev-visual': {
    id: 'jev-visual',
    name: 'JEV Visual',
    summary: {
      en: 'An educational JEV-like visual inference experiment on Apple Silicon with shared context scoring.',
      zh: '在 Apple Silicon 上的教学向类 JEV 视觉推理实验，共享上下文直接给候选打分。',
      ja: 'Apple Silicon 上の教育向け JEV 風ビジョン推論。共有コンテキストで候補を直接採点。',
    },
    decision: {
      en: 'Scores visual or textual candidates in one forward pass and returns calibrated probabilities.',
      zh: '一次前向为视觉或文本候选打分，并返回校准概率。',
      ja: '1 回の前向き計算で視覚／テキスト候補を採点し、校正確率を返します。',
    },
  },
  'shhivv/third-hand': {
    id: 'third-hand',
    name: 'Third Hand',
    summary: {
      en: 'A Swift client stack that calls JEV while driving local computer-use style helpers.',
      zh: 'Swift 客户端栈：在驱动本地 computer-use 辅助逻辑时调用 JEV。',
      ja: 'ローカル Computer Use 補助を動かしつつ JEV を呼ぶ Swift クライアント。',
    },
    decision: {
      en: 'Requests typed judgments from JEV before applying local automation actions.',
      zh: '在执行本地自动化动作前向 JEV 请求类型化判断。',
      ja: 'ローカル自動化の前に JEV へ型付き判断を求めます。',
    },
  },
  'kunchenguid/compact-adviser': {
    id: 'compact-adviser',
    name: 'Compact Adviser',
    summary: {
      en: 'A coding-agent skill/plugin that advises when to compact context to save tokens.',
      zh: '编码 Agent 的 Skill/插件：建议何时压缩上下文以节省 token。',
      ja: 'いつコンテキストを圧縮してトークンを節約するかを助言するコーディング Agent Skill。',
    },
    decision: {
      en: 'Judges whether the session looks complete enough to compact safely.',
      zh: '判断当前会话是否已足够完整、可以安全压缩。',
      ja: 'セッションが十分完了して安全に圧縮できるかを判断します。',
    },
  },
  'logicrw/awesome-jev-projects': {
    id: 'logicrw-awesome-jev-projects',
    name: 'Awesome JEV Projects',
    summary: {
      en: 'A source-backed JEV ecosystem radar with plain-language discovery and GitHub sync.',
      zh: '有源码依据的 JEV 生态雷达，含白话发现页与 GitHub 同步。',
      ja: '根拠付き JEV エコシステムレーダー。平易な発見 UI と GitHub 同期付き。',
    },
    decision: {
      en: 'Curates which open-source JEV integrations are worth browsing by decision pattern.',
      zh: '按决策模式整理值得浏览的开源 JEV 集成。',
      ja: '意思決定パターン別に、見る価値のある OSS JEV 統合を整理します。',
    },
  },
  'kerpopule/hermes-jev-skills': {
    id: 'hermes-jev-skills',
    name: 'Hermes JEV Skills',
    summary: {
      en: 'JEV-powered routing, memory, compaction, skill selection, and computer/browser use for Hermes agents.',
      zh: '为 Hermes Agent 提供 JEV 驱动的路由、记忆、压缩、Skill 选择与电脑/浏览器操作。',
      ja: 'Hermes エージェント向けに、JEV 駆動のルーティング・記憶・圧縮・Skill 選択・PC/ブラウザ操作。',
    },
    decision: {
      en: 'Chooses models, skills, or next computer actions from bounded JEV questions.',
      zh: '用有限 JEV 问题选择模型、Skill 或下一步电脑动作。',
      ja: '有限の JEV 質問でモデル・Skill・次の PC 操作を選びます。',
    },
  },
  'tamaratran/jev-pruner': {
    id: 'jev-pruner',
    name: 'JEV Pruner',
    summary: {
      en: 'A Claude Code plugin that trims long Bash output with TypeSafe JEV before the model sees it.',
      zh: 'Claude Code 插件：在模型看到长 Bash 输出前，用 TypeSafe JEV 裁剪。',
      ja: '長い Bash 出力をモデルに渡す前に TypeSafe JEV で刈り込む Claude Code プラグイン。',
    },
    decision: {
      en: 'Decides which output slices stay useful versus safe to drop under a token budget.',
      zh: '在 token 预算下判断哪些输出片段仍有用、哪些可丢弃。',
      ja: 'トークン予算の下で、残すべき出力断片と捨ててよい断片を判断します。',
    },
  },
  'Heman10x-NGU/openJev-verdict-2.0': {
    id: 'openjev-verdict-2',
    name: 'OpenJEV Verdict 2.0',
    summary: {
      en: 'A calibrated ~151M non-autoregressive local decision engine aiming at JEV-style typed answers.',
      zh: '约 151M 的校准非自回归本地决策引擎，目标对齐类 JEV 类型化答案。',
      ja: '約 151M の校正済み非自己回帰ローカル意思決定エンジン。JEV 風の型付き回答を目指す。',
    },
    decision: {
      en: 'Produces local Noul/Choice/Score-style probabilities without calling hosted JEV.',
      zh: '不调用托管 JEV，在本地产出 Noul/Choice/Score 风格概率。',
      ja: 'ホスト型 JEV を呼ばず、ローカルで Noul/Choice/Score 風の確率を出します。',
    },
  },
  'dbreunig/building-with-jev-skill': {
    id: 'building-with-jev-skill',
    name: 'Building with JEV Skill',
    summary: {
      en: 'An agent skill for writing and improving programs that call JEV / System One.',
      zh: '帮助编写与改进调用 JEV / System One 程序的 Agent Skill。',
      ja: 'JEV / System One を呼ぶプログラムの作成・改善を助ける Agent Skill。',
    },
    decision: {
      en: 'Advises how to frame state and questions so JEV returns usable typed answers.',
      zh: '指导如何组织 state 与 questions，让 JEV 返回可用的类型化答案。',
      ja: '使える型付き回答になるよう、state と questions の組み立て方を助言します。',
    },
  },
  'Mapika/decider': {
    id: 'decider',
    name: 'Decider',
    summary: {
      en: 'One-pass typed decisions with calibrated probabilities, fine-tuned from Qwen3.5-2B.',
      zh: '一次前向的类型化决策与校准概率，基于 Qwen3.5-2B 微调。',
      ja: 'Qwen3.5-2B 微調整による、1 パスの型付き意思決定と校正確率。',
    },
    decision: {
      en: 'Returns local System One–style answers for Choice, Score, and yes/no style prompts.',
      zh: '对 Choice、Score 与是否类问题返回本地 System One 风格答案。',
      ja: 'Choice / Score / 是否プロンプトにローカルな System One 風回答を返します。',
    },
  },
  'mmastrac/djev-spark': {
    id: 'djev-spark',
    name: 'djev-spark',
    summary: {
      en: 'A DGX Spark container recipe for running DiffusionGemma NVFP4 structured decisions.',
      zh: '在 DGX Spark 上跑 DiffusionGemma NVFP4 结构化决策的容器配方。',
      ja: 'DGX Spark 上で DiffusionGemma NVFP4 構造化意思決定を動かすコンテナレシピ。',
    },
    decision: {
      en: 'Packages local diffusion decision serving so apps can query typed outcomes on-box.',
      zh: '把本地 diffusion 决策服务打包，供应用在机器上查询类型化结果。',
      ja: 'ローカル diffusion 意思決定サービスを梱包し、箱内で型付き結果を問い合わせ可能にします。',
    },
  },
};

function titleFromRepo(full) {
  return full.split('/')[1];
}

function sanitizeId(id) {
  return String(id)
    .toLowerCase()
    .replace(/[^a-z0-9:_-]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 120);
}

const catalogue = JSON.parse(await readFile(cataloguePath, 'utf8'));
const meta = JSON.parse(await readFile(metaPath, 'utf8'));
const existing = new Set(
  catalogue.projects.map((p) => p.repoUrl.replace(/\/$/, '').toLowerCase()),
);
const existingIds = new Set(catalogue.projects.map((p) => p.id));

const added = [];
for (const row of meta) {
  if (row.error) throw new Error(`meta failed for ${row.full_name}: ${row.error}`);
  const full = row.full_name;
  const repoUrl = `https://github.com/${full}`;
  if (existing.has(repoUrl.toLowerCase())) {
    console.log('skip existing', full);
    continue;
  }
  const copy = COPY[full];
  if (!copy) throw new Error(`missing COPY for ${full}`);
  let id = sanitizeId(copy.id);
  if (existingIds.has(id)) id = sanitizeId(`${full.replace('/', '-')}`);
  const path = EVIDENCE_OVERRIDE[full] || row.evidencePath || 'README.md';
  const evidenceUrl = `https://github.com/${full}/blob/${row.sha}/${path}`;
  const owner = full.split('/')[0];
  const project = {
    id,
    name: copy.name || titleFromRepo(full),
    owner,
    category: CATEGORY[full] || 'developer-tools',
    repoUrl,
    evidenceUrl,
    source: {
      type: 'github',
      label: 'GitHub source',
      url: evidenceUrl,
    },
    language: row.language || 'Not declared',
    license: row.license && row.license !== 'NOASSERTION' ? row.license : 'Not declared',
    starsAtCapture: row.stars,
    summary: copy.summary,
    decision: copy.decision,
    verification: 'source-reviewed',
    runtimeVerified: false,
  };
  catalogue.projects.push(project);
  existing.add(repoUrl.toLowerCase());
  existingIds.add(id);
  added.push(full);
}

catalogue.capturedAt = new Date().toISOString().slice(0, 10);
await writeFile(cataloguePath, `${JSON.stringify(catalogue, null, 2)}\n`);
console.log(`catalogue now ${catalogue.projects.length}; added ${added.length}`);
console.log(added.join('\n'));

function rebuildAllProjectsSection(md, locale) {
  const n = catalogue.projects.length;
  const header =
    locale === 'zh'
      ? `## 全部 ${n} 个项目`
      : locale === 'ja'
        ? `## 全 ${n} プロジェクト`
        : `## All ${n} projects`;
  const starLabel = locale === 'zh' ? 'Star' : locale === 'ja' ? 'stars' : 'stars';
  const lines = catalogue.projects.map((p) => {
    const stars = Number(p.starsAtCapture || 0).toLocaleString('en-US');
    if (locale === 'zh') return `- [${p.name}](${p.repoUrl}) · ${stars} Star`;
    return `- [${p.name}](${p.repoUrl}) · ${stars} ${starLabel}`;
  });
  const block = `${header}\n\n${lines.join('\n')}\n`;
  const re =
    locale === 'zh'
      ? /## 全部 \d+ 个项目[\s\S]*?(?=\n## |\n---|\n<div|$)/
      : locale === 'ja'
        ? /## 全 \d+ プロジェクト[\s\S]*?(?=\n## |\n---|\n<div|$)/
        : /## All \d+ projects[\s\S]*?(?=\n## |\n---|\n<div|$)/;
  if (!re.test(md)) throw new Error(`all-projects section missing for ${locale}`);
  return md.replace(re, block);
}

function bumpCounts(md, n) {
  return md
    .replace(/All 100 projects/g, `All ${n} projects`)
    .replace(/全部 100 个项目/g, `全部 ${n} 个项目`)
    .replace(/全 100 プロジェクト/g, `全 ${n} プロジェクト`)
    .replace(/<strong>100<\/strong>/g, `<strong>${n}</strong>`)
    .replace(/#all-100-projects/g, `#all-${n}-projects`)
    .replace(/href="#all-100-projects"/g, `href="#all-${n}-projects"`);
}

const n = catalogue.projects.length;
for (const [file, locale] of [
  ['README.md', 'en'],
  ['README.zh-CN.md', 'zh'],
  ['README.ja.md', 'ja'],
]) {
  let md = await readFile(resolve(ROOT, file), 'utf8');
  md = bumpCounts(md, n);
  md = rebuildAllProjectsSection(md, locale);
  await writeFile(resolve(ROOT, file), md);
  console.log('updated', file);
}
