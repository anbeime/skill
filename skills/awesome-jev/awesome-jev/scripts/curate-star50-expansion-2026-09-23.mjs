import { readFile, writeFile } from 'node:fs/promises';

const catalogueFile = new URL('../data/projects.json', import.meta.url);
const catalogue = JSON.parse(await readFile(catalogueFile, 'utf8'));

const additions = [
  {
    "id": "fx-typesafe-permission-reviewer",
    "name": "fx · TypeSafe Permission Reviewer",
    "owner": "vercel-labs",
    "category": "safety-review",
    "starsAtCapture": 3127,
    "language": "Zig",
    "license": "Apache-2.0",
    "summary": {
      "en": "A Zig coding agent with an optional TypeSafe Jev permission reviewer for pending tool actions.",
      "zh": "Zig 编码 Agent，可选 TypeSafe Jev 权限审查器，用于审核待执行工具动作。",
      "ja": "保留中のツール操作を審査する TypeSafe Jev 権限レビュアー付き Zig コーディング Agent。"
    },
    "decision": {
      "en": "Posts pending actions to System One as Choice questions and maps allow/deny probabilities into the agent permission gate.",
      "zh": "把待执行动作作为 Choice 提交到 System One，并把允许/拒绝概率映射进 Agent 权限门。",
      "ja": "保留中の操作を Choice として System One に送り、許可/拒否確率を Agent の権限ゲートへ写します。"
    },
    "repoUrl": "https://github.com/vercel-labs/fx",
    "evidenceUrl": "https://github.com/vercel-labs/fx/blob/e094531ec3fe23b2a1498132f2cea04df680434b/src/builtins/gateway/typesafe_permission_reviewer.zig",
    "source": {
      "type": "github",
      "label": "GitHub source",
      "url": "https://github.com/vercel-labs/fx/blob/e094531ec3fe23b2a1498132f2cea04df680434b/src/builtins/gateway/typesafe_permission_reviewer.zig"
    },
    "verification": "source-reviewed",
    "runtimeVerified": false
  },
  {
    "id": "agent-beacon-jev-evaluator",
    "name": "Agent Beacon · Jev Evaluator",
    "owner": "asymptote-labs",
    "category": "agent-workflows",
    "starsAtCapture": 1103,
    "language": "Go",
    "license": "MIT",
    "summary": {
      "en": "Cross-harness agent memory that can ask Jev to score bounded, redacted session projections before promoting lessons.",
      "zh": "跨 Harness 的 Agent 记忆系统，可用 Jev 对脱敏会话投影打分后再提升经验。",
      "ja": "複数 Harness 向け Agent メモリ。Jev で編集済みセッション投影を採点してから教訓を昇格できます。"
    },
    "decision": {
      "en": "Sends Noul rubric questions to TypeSafe System One and stores calibrated probabilities with human review gates.",
      "zh": "向 TypeSafe System One 发送 Noul 评分问题，并把校准概率与人工复核门一起保存。",
      "ja": "TypeSafe System One に Noul 採点質問を送り、較正確率を人手レビュー付きで保存します。"
    },
    "repoUrl": "https://github.com/asymptote-labs/agent-beacon",
    "evidenceUrl": "https://github.com/asymptote-labs/agent-beacon/blob/29c504ea4f0163f1281cc6774a0b1d3d9d9436ee/cli/beacon/internal/learning/evaluator.go",
    "source": {
      "type": "github",
      "label": "GitHub source",
      "url": "https://github.com/asymptote-labs/agent-beacon/blob/29c504ea4f0163f1281cc6774a0b1d3d9d9436ee/cli/beacon/internal/learning/evaluator.go"
    },
    "verification": "source-reviewed",
    "runtimeVerified": false
  },
  {
    "id": "quackd-jev-stepper",
    "name": "quackd · Jev Stepper",
    "owner": "rokbenko",
    "category": "domain-tools",
    "starsAtCapture": 229,
    "language": "Python",
    "license": "Apache-2.0",
    "summary": {
      "en": "A robot orchestration CLI with an optional System One stepper that chooses among permitted discrete robot calls.",
      "zh": "机器人编排 CLI，可选 System One 步进器在已许可的离散机器人调用中做选择。",
      "ja": "許可済みの離散ロボット呼び出しから選ぶ任意 System One ステッパー付きロボット制御 CLI。"
    },
    "decision": {
      "en": "Routes Choice and Noul questions through the TypeSafe System One client while the executor keeps safety gates.",
      "zh": "通过 TypeSafe System One 客户端路由 Choice 与 Noul，执行器仍保留安全门。",
      "ja": "Choice と Noul を TypeSafe System One クライアント経由で送り、実行側が安全ゲートを維持します。"
    },
    "repoUrl": "https://github.com/rokbenko/quackd",
    "evidenceUrl": "https://github.com/rokbenko/quackd/blob/1250c05fd29fc388868366678917119d63146242/quackd/agent/decision/systemone.py",
    "source": {
      "type": "github",
      "label": "GitHub source",
      "url": "https://github.com/rokbenko/quackd/blob/1250c05fd29fc388868366678917119d63146242/quackd/agent/decision/systemone.py"
    },
    "verification": "source-reviewed",
    "runtimeVerified": false
  },
  {
    "id": "ai-python-jev-evaluate",
    "name": "AI SDK Python · Jev Evaluate",
    "owner": "vercel-labs",
    "category": "sdk-integrations",
    "starsAtCapture": 185,
    "language": "Python",
    "license": "Apache-2.0",
    "summary": {
      "en": "Vercel's AI SDK for Python with an experimental evaluate path that asks typed questions through typesafe-ai/jev.",
      "zh": "Vercel Python AI SDK 的实验性 evaluate 路径，可通过 typesafe-ai/jev 提问类型化问题。",
      "ja": "typesafe-ai/jev 経由で型付き質問を送る実験的 evaluate を備えた Vercel Python AI SDK。"
    },
    "decision": {
      "en": "Batches Choice, Score, and Boolean questions against shared state via the AI Gateway evaluation protocol.",
      "zh": "通过 AI Gateway 评估协议，对共享状态批量提交 Choice、Score 与布尔问题。",
      "ja": "AI Gateway の評価プロトコルで、共有状態に対し Choice・Score・真偽質問をまとめて送ります。"
    },
    "repoUrl": "https://github.com/vercel-labs/ai-python",
    "evidenceUrl": "https://github.com/vercel-labs/ai-python/blob/7b406c2f6428e97d8366b090f3f37d6ac0d01337/src/ai/ops/evaluation.py",
    "source": {
      "type": "github",
      "label": "GitHub source",
      "url": "https://github.com/vercel-labs/ai-python/blob/7b406c2f6428e97d8366b090f3f37d6ac0d01337/src/ai/ops/evaluation.py"
    },
    "verification": "source-reviewed",
    "runtimeVerified": false
  },
  {
    "id": "fastbrowse-jev",
    "name": "fastbrowse · Jev",
    "owner": "agent-labs-dev",
    "category": "browser-computer-use",
    "starsAtCapture": 97,
    "language": "Python",
    "license": "MIT",
    "summary": {
      "en": "A browser agent that indexes page controls and lets Jev pick the next action while an LLM plans and reads.",
      "zh": "浏览器 Agent：索引页面控件，由 Jev 选择下一步动作，LLM 负责规划与阅读。",
      "ja": "ページ上の操作候補を索引化し、Jev が次の操作を選び、LLM が計画・読解するブラウザ Agent。"
    },
    "decision": {
      "en": "Issues Choice and Noul questions over candidate DOM actions and verifies answer claims against quoted page text.",
      "zh": "对候选 DOM 动作发出 Choice/Noul 问题，并用页面原文引用校验回答主张。",
      "ja": "候補 DOM 操作に Choice/Noul を投げ、ページ原文の引用で回答主張を検証します。"
    },
    "repoUrl": "https://github.com/agent-labs-dev/fastbrowse",
    "evidenceUrl": "https://github.com/agent-labs-dev/fastbrowse/blob/a088eb8b6d83a9643531acd8f5c0c1b0b276953e/src/fastbrowse/jev.py",
    "source": {
      "type": "github",
      "label": "GitHub source",
      "url": "https://github.com/agent-labs-dev/fastbrowse/blob/a088eb8b6d83a9643531acd8f5c0c1b0b276953e/src/fastbrowse/jev.py"
    },
    "verification": "source-reviewed",
    "runtimeVerified": false
  },
  {
    "id": "jevmlx",
    "name": "jevmlx",
    "owner": "bnsd55",
    "category": "open-models",
    "starsAtCapture": 59,
    "language": "Python",
    "license": "MIT",
    "summary": {
      "en": "A local Apple Silicon decision layer that scores constrained fields from MLX logits and speaks System One HTTP.",
      "zh": "在 Apple Silicon 本地从 MLX logits 为受限字段打分，并提供 System One HTTP 接口。",
      "ja": "Apple Silicon 上で MLX logits から制約付きフィールドを採点し、System One HTTP を提供するローカル層。"
    },
    "decision": {
      "en": "Accepts POST /v1/systemone payloads, maps Noul/Choice/Score questions to one-pass schema scoring, and returns probabilities.",
      "zh": "接受 POST /v1/systemone，把 Noul/Choice/Score 映射为单次 schema 打分并返回概率。",
      "ja": "POST /v1/systemone を受け、Noul/Choice/Score を一回の schema 採点へ写して確率を返します。"
    },
    "repoUrl": "https://github.com/bnsd55/jevmlx",
    "evidenceUrl": "https://github.com/bnsd55/jevmlx/blob/9d3621516826a5de4480c9fdab0aa6d59e93e113/jevmlx/serve.py",
    "source": {
      "type": "github",
      "label": "GitHub source",
      "url": "https://github.com/bnsd55/jevmlx/blob/9d3621516826a5de4480c9fdab0aa6d59e93e113/jevmlx/serve.py"
    },
    "verification": "source-reviewed",
    "runtimeVerified": false
  },
  {
    "id": "open-alternative-jev",
    "name": "Open Alternative to Jev",
    "owner": "ikermoel",
    "category": "open-models",
    "starsAtCapture": 51,
    "language": "Python",
    "license": "Apache-2.0",
    "summary": {
      "en": "An open System One-style decider that packs typed questions into one forward pass over local open models.",
      "zh": "开源 System One 风格决策器，把类型化问题打包进本地开放模型的一次前向。",
      "ja": "型付き質問をローカル開放モデルの一回 forward に詰める、オープンな System One 風 Decider。"
    },
    "decision": {
      "en": "Scores Choice options from label logits without generating text, with optional calibration helpers.",
      "zh": "从标签 logits 为 Choice 选项打分且不生成文本，并提供可选校准辅助。",
      "ja": "テキストを生成せずラベル logits から Choice を採点し、任意の較正ヘルパーも備えます。"
    },
    "repoUrl": "https://github.com/ikermoel/open-alternative-jev",
    "evidenceUrl": "https://github.com/ikermoel/open-alternative-jev/blob/4a85df1831b537343c9e133b5150fa3a3b1ce98e/so1/decider.py",
    "source": {
      "type": "github",
      "label": "GitHub source",
      "url": "https://github.com/ikermoel/open-alternative-jev/blob/4a85df1831b537343c9e133b5150fa3a3b1ce98e/so1/decider.py"
    },
    "verification": "source-reviewed",
    "runtimeVerified": false
  },
  {
    "id": "canny-jev-hooks",
    "name": "Canny · Jev Hooks",
    "owner": "qkal",
    "category": "safety-review",
    "starsAtCapture": 50,
    "language": "TypeScript",
    "license": "MIT",
    "summary": {
      "en": "Claude Code and Codex hooks that keep an append-only ledger and optionally ask Jev Noul questions for advisory checks.",
      "zh": "Claude Code / Codex Hooks：维护只追加账本，并可选向 Jev 询问 Noul 做建议性检查。",
      "ja": "追記専用台帳を保ち、任意で Jev に Noul 助言チェックを頼む Claude Code / Codex hooks。"
    },
    "decision": {
      "en": "Posts Noul questions to api.typesafe.ai/v1/systemone and only uses high-confidence answers to relax a stop gate.",
      "zh": "向 api.typesafe.ai/v1/systemone 提交 Noul，仅在高置信时放宽停止门。",
      "ja": "api.typesafe.ai/v1/systemone に Noul を送り、高信頼のときだけ停止ゲートを緩めます。"
    },
    "repoUrl": "https://github.com/qkal/Canny",
    "evidenceUrl": "https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/src/jev.ts",
    "source": {
      "type": "github",
      "label": "GitHub source",
      "url": "https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/src/jev.ts"
    },
    "verification": "source-reviewed",
    "runtimeVerified": false
  },
  {
    "id": "ha-jev",
    "name": "HA-Jev",
    "owner": "AboveColin",
    "category": "domain-tools",
    "starsAtCapture": 50,
    "language": "Python",
    "license": "MIT",
    "summary": {
      "en": "A Home Assistant integration that turns typed Jev questions about house state into sensors and automation actions.",
      "zh": "Home Assistant 集成：把关于家庭状态的类型化 Jev 问题变成传感器与自动化动作。",
      "ja": "家の状態への型付き Jev 質問をセンサーと自動化アクションにする Home Assistant 連携。"
    },
    "decision": {
      "en": "Builds System One payloads via jevclient and updates entities from Noul, Choice, and Score answers under a token budget.",
      "zh": "通过 jevclient 构建 System One 请求，并在额度内用 Noul/Choice/Score 更新实体。",
      "ja": "jevclient で System One ペイロードを作り、トークン予算内で Noul/Choice/Score からエンティティを更新します。"
    },
    "repoUrl": "https://github.com/AboveColin/HA-Jev",
    "evidenceUrl": "https://github.com/AboveColin/HA-Jev/blob/c3d4881121e4d02eacf272d9340447235c6ecc41/custom_components/jev/coordinator.py",
    "source": {
      "type": "github",
      "label": "GitHub source",
      "url": "https://github.com/AboveColin/HA-Jev/blob/c3d4881121e4d02eacf272d9340447235c6ecc41/custom_components/jev/coordinator.py"
    },
    "verification": "source-reviewed",
    "runtimeVerified": false
  }
];

const byRepo = new Map(catalogue.projects.map((project) => [project.repoUrl.toLowerCase(), project]));
for (const project of additions) byRepo.set(project.repoUrl.toLowerCase(), project);

catalogue.projects = [...byRepo.values()].sort(
  (a, b) => b.starsAtCapture - a.starsAtCapture || a.name.localeCompare(b.name),
);
catalogue.capturedAt = '2026-09-23';
catalogue.source.batch = '2026-09-23-star50-cross-search-and-source-review';
catalogue.source.policy =
  'Project-level deduplication. Public JEV-related GitHub repositories at or above 50 stars are included only after fixed-commit source review. Discovery includes GitHub repository search, competitor catalogues (AbdelStark/awesome-typesafe-jev, heyjunpenn/awesome-jev), and direct source inspection. Runtime behavior is not independently verified.';

await writeFile(catalogueFile, `${JSON.stringify(catalogue, null, 2)}\n`);
console.log(`Added or refreshed ${additions.length} projects; catalogue now has ${catalogue.projects.length}.`);
