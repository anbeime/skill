import { readFile, writeFile } from 'node:fs/promises';

const file = new URL('../data/projects.json', import.meta.url);
const catalogue = JSON.parse(await readFile(file, 'utf8'));

const githubSource = (evidenceUrl) => ({
  type: 'github',
  label: 'GitHub source',
  url: evidenceUrl,
});

const additions = [
  {
    id: 'jev-ultrafast', name: 'Jev Ultrafast', owner: 'browser-use', category: 'browser-computer-use',
    repoUrl: 'https://github.com/browser-use/jev-ultrafast',
    evidenceUrl: 'https://github.com/browser-use/jev-ultrafast/blob/1231850a0bf1a0c0341fe408ef1668dbbfdfac46/jev_ultrafast/model.py',
    source: { type: 'x', label: 'Original X case', url: 'https://x.com/gregpr07/status/2100411066966749359', author: '@gregpr07', views: 2948266 },
    language: 'Python', license: 'MIT', starsAtCapture: 9549,
    summary: { en: 'A browser agent that uses JEV to choose an action and matching DOM element, calling a text model only when input text is needed.', zh: '用 JEV 一次选出浏览器动作与对应 DOM 元素，只在需要输入文本时再调用文本模型。' },
    decision: { en: 'Chooses the next browser action and target element from the current page state.', zh: '根据当前页面状态选择下一步浏览器动作和目标元素。' },
  },
  {
    id: 'langchain-jev', name: 'LangChain · TypeSafe', owner: 'langchain-ai', category: 'sdk-integrations',
    repoUrl: 'https://github.com/langchain-ai/langchain', evidenceUrl: 'https://github.com/langchain-ai/langchain/blob/eba445b7563d1709427bd8072892975a6ea59fdc/libs/partners/typesafe/langchain_typesafe/classifier.py',
    language: 'Python', license: 'MIT', starsAtCapture: 146702,
    summary: { en: 'An optional JEV classifier integration for Python LangChain workflows.', zh: '面向 Python LangChain 工作流的可选 JEV 分类器集成。' },
    decision: { en: 'Submits binary, categorical, and ordered-score questions and returns typed answers with probabilities.', zh: '提交二元、分类和有序评分问题，并返回带概率的类型化答案。' },
  },
  {
    id: 'ai-hedge-fund-jev', name: 'AI Hedge Fund · JEV Adapter', owner: 'virattt', category: 'domain-tools',
    repoUrl: 'https://github.com/virattt/ai-hedge-fund', evidenceUrl: 'https://github.com/virattt/ai-hedge-fund/blob/154a8b2f46dca0f40764d814e4e747b0ad71f4c4/hedge_fund/llm/client.py',
    language: 'Python', license: 'MIT', starsAtCapture: 63571,
    summary: { en: 'An educational hedge-fund prototype with an optional JEV adapter for structured strategy judgments.', zh: '在教育型 AI 对冲基金原型中加入可选 JEV 适配器，用于结构化策略判断。' },
    decision: { en: 'Converts strategy questions into System One requests and normalizes typed answers for the fund workflow.', zh: '把策略问题转换为 System One 请求，并将类型化答案归一化给基金工作流。' },
  },
  {
    id: 'litellm-jev-router', name: 'LiteLLM · JEV Router', owner: 'BerriAI', category: 'routing-optimization',
    repoUrl: 'https://github.com/BerriAI/litellm', evidenceUrl: 'https://github.com/BerriAI/litellm/blob/56116079c8022da0e8f7ff9ccb017ad5aca5aed2/litellm/router_strategy/complexity_router/jev_classifier.py#L70',
    language: 'Python', license: 'MIT', starsAtCapture: 59192,
    summary: { en: 'LiteLLM can use JEV inside its complexity-based model router.', zh: 'LiteLLM 可在按复杂度路由模型的策略中使用 JEV。' },
    decision: { en: 'Maps a request to a configured complexity class that drives backend model routing.', zh: '把请求映射到配置好的复杂度类别，再据此路由后端模型。' },
  },
  {
    id: 'oh-my-pi-jev', name: 'Oh My Pi · JEV Judgments', owner: 'can1357', category: 'routing-optimization',
    repoUrl: 'https://github.com/can1357/oh-my-pi', evidenceUrl: 'https://github.com/can1357/oh-my-pi/blob/78b753124d11f8dd3ae73e2524125890ff7c977e/packages/ai/src/judgment/typesafe.ts#L4',
    language: 'TypeScript', license: 'MIT', starsAtCapture: 32024,
    summary: { en: 'A coding agent with an optional TypeSafe judgment provider for bounded workflow decisions.', zh: '在编码 Agent 中提供可选 TypeSafe 判断器，处理有边界的工作流决策。' },
    decision: { en: 'Sends agent state and typed questions to JEV and parses structured answers.', zh: '把 Agent 状态与类型化问题发给 JEV，并解析结构化答案。' },
  },
  {
    id: 'composio-typesafe', name: 'Composio · TypeSafe Provider', owner: 'ComposioHQ', category: 'sdk-integrations',
    repoUrl: 'https://github.com/ComposioHQ/composio', evidenceUrl: 'https://github.com/ComposioHQ/composio/blob/4b5920bf7aa55c8a44657b060d4bd25ce7b13a9a/ts/packages/providers/typesafe/src/decide.ts',
    language: 'TypeScript', license: 'MIT', starsAtCapture: 30258,
    summary: { en: 'A TypeSafe provider that uses JEV to choose among tools and bounded argument options.', zh: '用 JEV 在工具与有限参数选项之间做选择的 TypeSafe Provider。' },
    decision: { en: 'Turns tool conditions into structured questions and passes answers to local invocation logic.', zh: '把工具条件转换为结构化问题，再把答案交给本地调用逻辑。' },
  },
  {
    id: 'vercel-ai-typesafe', name: 'Vercel AI SDK · TypeSafe', owner: 'vercel', category: 'sdk-integrations',
    repoUrl: 'https://github.com/vercel/ai', evidenceUrl: 'https://github.com/vercel/ai/blob/73ec7015edd4f04ca9144ce93a8a037a731e5db8/packages/typesafe-ai/src/typesafe-ai-evaluation-model.ts',
    language: 'TypeScript', license: 'Mixed', starsAtCapture: 26858,
    summary: { en: 'The AI SDK TypeSafe provider exposes JEV through the shared evaluate interface.', zh: 'AI SDK 的 TypeSafe Provider 通过统一 evaluate 接口调用 JEV。' },
    decision: { en: 'Maps choice, score, and yes/no questions to System One and parses typed results.', zh: '把 choice、score 与 yes/no 问题映射到 System One，并解析类型化结果。' },
  },
  {
    id: 'cua-jev-use', name: 'Cua · JEV Use', owner: 'trycua', category: 'browser-computer-use',
    repoUrl: 'https://github.com/trycua/cua', evidenceUrl: 'https://github.com/trycua/cua/blob/83f142c4290a0f7d9ed545ae8532858c6e4f8145/libs/cua-driver/examples/jev-use/python/jev_adapter.py#L11',
    language: 'Python', license: 'MIT', starsAtCapture: 24683,
    summary: { en: 'A computer-use example pairing Cua Driver observation and execution with bounded JEV choices.', zh: '把 Cua Driver 的观察与执行能力和 JEV 的有限动作选择结合起来。' },
    decision: { en: 'Reads DOM or visual-region descriptions and returns one supplied candidate action ID.', zh: '读取 DOM 或视觉区域描述，从候选动作中返回一个动作 ID。' },
  },
  {
    id: 'pydantic-ai-typesafe', name: 'Pydantic AI · TypeSafe', owner: 'pydantic', category: 'sdk-integrations',
    repoUrl: 'https://github.com/pydantic/pydantic-ai', evidenceUrl: 'https://github.com/pydantic/pydantic-ai/blob/c4898abb54dc25ae6f6aef208a4c0661b30a455e/pydantic_ai_slim/pydantic_ai/models/typesafe.py',
    language: 'Python', license: 'MIT', starsAtCapture: 20066,
    summary: { en: 'A TypeSafe model integration that maps supported structured outputs to JEV questions.', zh: '把受支持的结构化输出映射为 JEV 问题的 TypeSafe 模型集成。' },
    decision: { en: 'Converts output fields into typed questions and maps JEV answers back to the result model.', zh: '把输出字段转成类型化问题，再将 JEV 答案映射回结果模型。' },
  },
  {
    id: 'eliza-typesafe', name: 'Eliza · TypeSafe Client', owner: 'elizaOS', category: 'sdk-integrations',
    repoUrl: 'https://github.com/elizaOS/eliza', evidenceUrl: 'https://github.com/elizaOS/eliza/blob/ebc808e3a67fb941e29153d89fc896524d32fe3c/packages/agent/src/services/typesafe/client.ts',
    language: 'TypeScript', license: 'MIT', starsAtCapture: 19382,
    summary: { en: 'An optional TypeSafe HTTP adapter in the Eliza agent operating system.', zh: 'Eliza Agent 操作系统中的可选 TypeSafe HTTP 适配器。' },
    decision: { en: 'Sends state and questions only when explicitly called and validates typed answers.', zh: '仅在显式调用时发送状态与问题，并校验类型化答案。' },
  },
  {
    id: 'langchainjs-typesafe', name: 'LangChain.js · TypeSafe', owner: 'langchain-ai', category: 'sdk-integrations',
    repoUrl: 'https://github.com/langchain-ai/langchainjs', evidenceUrl: 'https://github.com/langchain-ai/langchainjs/blob/206d8b992bcf90ce7d46f2158f1ad85fc1d826c0/libs/providers/langchain-typesafe/src/classifier.ts',
    language: 'TypeScript', license: 'MIT', starsAtCapture: 18213,
    summary: { en: 'A TypeSafeClassifier integration for JavaScript LangChain workflows.', zh: '面向 JavaScript LangChain 工作流的 TypeSafeClassifier 集成。' },
    decision: { en: 'Invokes JEV with predefined questions and parses choice, noul, score, and probability fields.', zh: '用预定义问题调用 JEV，并解析 choice、noul、score 与概率字段。' },
  },
  {
    id: 'json-render-jev', name: 'json-render · JEV Compose', owner: 'vercel-labs', category: 'interfaces',
    repoUrl: 'https://github.com/vercel-labs/json-render', evidenceUrl: 'https://github.com/vercel-labs/json-render/blob/3ad381881194e7011ad3ccd6d668033495a06c29/apps/web/lib/jev/compose.ts',
    language: 'TypeScript', license: 'Apache-2.0', starsAtCapture: 16898,
    summary: { en: 'A JEV UI-composition experiment that selects from predefined components and properties.', zh: '用 JEV 从预定义组件与属性中进行选择的 UI 组合实验。' },
    decision: { en: 'Evaluates component configurations before local code assembles the UI specification.', zh: '先判断组件配置，再由本地代码组装 UI 规范。' },
  },
  {
    id: 'quantdinger-jev', name: 'QuantDinger · JEV Gate', owner: 'OpenByteInc', category: 'domain-tools',
    repoUrl: 'https://github.com/OpenByteInc/QuantDinger', evidenceUrl: 'https://github.com/OpenByteInc/QuantDinger/blob/12c04eb2cdb8a9d08dc84502f5261ec3f1c56bf7/backend_api_python/app/services/ai_decision_filter.py',
    language: 'Python', license: 'Apache-2.0', starsAtCapture: 11763,
    summary: { en: 'An open-source trading OS with a JEV decision gate before selected live entries.', zh: '在部分真实交易入场前增加 JEV 决策闸门的开源交易系统。' },
    decision: { en: 'Checks evidence quality, signal consistency, exposure, and budget before an order reaches the exchange.', zh: '在订单进入交易所前检查证据质量、信号一致性、敞口与预算。' },
  },
  {
    id: 'openchamber-jev-router', name: 'OpenChamber · JEV Router', owner: 'openchamber', category: 'routing-optimization',
    repoUrl: 'https://github.com/openchamber/openchamber', evidenceUrl: 'https://github.com/openchamber/openchamber/blob/614d7f76e581a132a86575c03d3fa9aad5e624b6/packages/web/server/lib/routing/jev.js',
    language: 'TypeScript', license: 'MIT', starsAtCapture: 10100,
    summary: { en: 'An optional automatic model router that classifies a message before model selection.', zh: '在选择模型前先对消息分类的可选自动路由器。' },
    decision: { en: 'Selects a task category; local mappings determine the model and reasoning configuration.', zh: '选择任务类别，再由本地映射决定模型与推理配置。' },
  },
  {
    id: 'rig-typesafe', name: 'Rig · TypeSafe Crate', owner: '0xPlaygrounds', category: 'sdk-integrations',
    repoUrl: 'https://github.com/0xPlaygrounds/rig', evidenceUrl: 'https://github.com/0xPlaygrounds/rig/blob/2d16c1b25f6749b3a2cd841beddf767106495069/crates/rig-typesafeai/src/wire.rs#L40',
    language: 'Rust', license: 'MIT', starsAtCapture: 8679,
    summary: { en: 'An experimental Rust crate for expressing JEV questions and answers with Rust types.', zh: '用 Rust 类型表达 JEV 问题与答案的实验性 crate。' },
    decision: { en: 'Sends application state and questions and parses Choice, Score, or Noul answers.', zh: '发送应用状态与问题，并解析 Choice、Score 或 Noul 答案。' },
  },
  {
    id: 'firstmate-jev', name: 'Firstmate · JEV Dispatch', owner: 'kunchenguid', category: 'routing-optimization',
    repoUrl: 'https://github.com/kunchenguid/firstmate', evidenceUrl: 'https://github.com/kunchenguid/firstmate/blob/4812db801628040b609dc25a2a8a91ed5efac662/bin/fm-dispatch-resolve.sh',
    language: 'Shell', license: 'MIT', starsAtCapture: 6771,
    summary: { en: 'An agent crew dispatcher that can match task briefs to rules with JEV.', zh: '可用 JEV 把任务简报匹配到调度规则的 Agent 团队调度器。' },
    decision: { en: 'Matches the task brief to candidate rules before local policy resolves the execution profile.', zh: '先把任务简报匹配到候选规则，再由本地策略确定执行配置。' },
  },
  {
    id: 'agentgateway-jev-guardrail', name: 'Agentgateway · JEV Guardrail', owner: 'agentgateway', category: 'safety-review',
    repoUrl: 'https://github.com/agentgateway/agentgateway', evidenceUrl: 'https://github.com/agentgateway/agentgateway/blob/6b0270efd25b5255932943e48b5ca47583d3ad28/examples/llm-guardrail-jev/guardrail.ts',
    language: 'TypeScript', license: 'Apache-2.0', starsAtCapture: 4936,
    summary: { en: 'A JEV webhook guardrail example for inspecting model requests and responses.', zh: '用 JEV Webhook 检查模型请求与响应的 Guardrail 示例。' },
    decision: { en: 'Scores jailbreaks, harmful content, and secret disclosure before gateway policy accepts a request.', zh: '对越狱、有害内容与密钥泄露评分，再由网关策略决定是否放行。' },
  },
  {
    id: 'latitude-jev-preclassifier', name: 'Latitude · JEV Preclassifier', owner: 'latitude-dev', category: 'safety-review',
    repoUrl: 'https://github.com/latitude-dev/latitude-llm', evidenceUrl: 'https://github.com/latitude-dev/latitude-llm/blob/6b2484c1d74973877fc7d353b8867c7496568d78/packages/domain/flaggers/src/use-cases/run-jev-preclassifier.ts#L1',
    language: 'TypeScript', license: 'MIT', starsAtCapture: 4661,
    summary: { en: 'An optional JEV preclassifier for selecting which conversation checks should run.', zh: '选择一段会话应执行哪些检查的可选 JEV 预分类器。' },
    decision: { en: 'Judges which checks apply before thresholds and rate limits allow them into the evaluation queue.', zh: '先判断哪些检查适用，再由阈值和速率限制决定是否入队。' },
  },
  {
    id: 'ax-typesafe', name: 'Ax · TypeSafe Client', owner: 'ax-llm', category: 'sdk-integrations',
    repoUrl: 'https://github.com/ax-llm/ax', evidenceUrl: 'https://github.com/ax-llm/ax/blob/5c43344f9ef3016db576fa2c3b59d48ef21b4d71/src/ax/ai/typesafe/client.ts#L1',
    language: 'TypeScript', license: 'Apache-2.0', starsAtCapture: 2927,
    summary: { en: 'A TypeSafe integration for boolean, finite-class, and native JEV signatures.', zh: '支持布尔、有限分类以及原生 JEV 请求的 TypeSafe 集成。' },
    decision: { en: 'Maps supported signatures to typed JEV questions or sends native System One requests.', zh: '把签名映射到类型化 JEV 问题，或直接发送原生 System One 请求。' },
  },
  {
    id: 'semif', name: 'SemIf', owner: 'TheoLeeCJ', category: 'open-models',
    repoUrl: 'https://github.com/TheoLeeCJ/SemIf', evidenceUrl: 'https://github.com/TheoLeeCJ/SemIf/blob/ca3ba65f142967030ecb453346e94d6f476a69df/README.md',
    modelUrl: 'https://github.com/TheoLeeCJ/SemIf#models', language: 'Python', license: 'MIT', starsAtCapture: 2047,
    summary: { en: 'An independent open-model implementation of the semantic-if interface pattern.', zh: '用开放模型实现“语义 if”接口模式的独立研究项目。' },
    decision: { en: 'Reads option probabilities directly from open models without a generated answer sentence.', zh: '直接读取开放模型的选项概率，不生成再解析答案文本。' },
  },
  {
    id: 'laya', name: 'Laya', owner: 'convaiinnovations', category: 'open-models',
    repoUrl: 'https://github.com/NandhaKishorM/laya', evidenceUrl: 'https://github.com/NandhaKishorM/laya/blob/d113dca2512fb3eaca313534bc54c7162d87c1d4/README.md',
    modelUrl: 'https://huggingface.co/convaiinnovations/laya', language: 'Python', license: 'Apache-2.0', starsAtCapture: 1795,
    summary: { en: 'An Apache-2.0 open-weight decision model with English, multilingual, and typed-decision checkpoints.', zh: '采用 Apache-2.0 的开放权重决策模型，提供英文、多语言与 typed-decision 检查点。' },
    decision: { en: 'Produces typed choice, score, and noul outputs locally; benchmark comparisons are author-reported.', zh: '在本地输出类型化 choice、score 与 noul；对比数据均按作者披露处理。' },
  },
  {
    id: 'jev-trader', name: 'JEV Trader', owner: 'jarrodwatts', category: 'domain-tools',
    repoUrl: 'https://github.com/jarrodwatts/jev-trader', evidenceUrl: 'https://github.com/jarrodwatts/jev-trader/blob/b587759e459ea049590102e54a0b07800864cdc3/src/model.ts',
    language: 'TypeScript', license: 'MIT', starsAtCapture: 1364,
    summary: { en: 'A market-making experiment that can request one JEV trade decision per Monad block.', zh: '可在 Monad 每个区块请求一次 JEV 交易判断的做市实验。' },
    decision: { en: 'Turns order-book state into a bounded buy, sell, or hold decision before local execution policy.', zh: '把订单簿状态转成 buy、sell 或 hold 的有限判断，再交给本地执行策略。' },
  },
  {
    id: 'agent-desktop-jev', name: 'Agent Desktop · JEV Skill', owner: 'lahfir', category: 'browser-computer-use',
    repoUrl: 'https://github.com/lahfir/agent-desktop', evidenceUrl: 'https://github.com/lahfir/agent-desktop/blob/7a8e4a10281c7319733aa200fd79501f34529716/scripts/jev/act.mjs',
    language: 'JavaScript', license: 'Apache-2.0', starsAtCapture: 1310,
    summary: { en: 'An optional JEV skill that chooses native desktop controls and actions from accessibility data.', zh: '根据系统无障碍数据选择原生桌面控件与动作的可选 JEV Skill。' },
    decision: { en: 'Selects a target and action and estimates presence and risk before local policy executes.', zh: '选择目标与动作并估计存在性和风险，再由本地策略执行。' },
  },
  {
    id: 'vellum-assistant-jev', name: 'Vellum Assistant · JEV', owner: 'vellum-ai', category: 'sdk-integrations',
    repoUrl: 'https://github.com/vellum-ai/vellum-assistant', evidenceUrl: 'https://github.com/vellum-ai/vellum-assistant/blob/ee5ba342719e72b67698c2e1a4a78837321d0b1d/assistant/src/providers/jev/client.ts',
    language: 'TypeScript', license: 'MIT', starsAtCapture: 1292,
    summary: { en: 'An optional JEV provider that submits conversation state and explicit questions.', zh: '提交会话状态与显式问题的可选 JEV Provider。' },
    decision: { en: 'Bundles state and questions for System One and returns structured answers to the assistant.', zh: '把状态与问题打包发送给 System One，再向 Assistant 返回结构化答案。' },
  },
  {
    id: 'nanojev', name: 'NanoJev', owner: 'TianyuCodings', category: 'open-models',
    repoUrl: 'https://github.com/TianyuCodings/NanoJev', evidenceUrl: 'https://github.com/TianyuCodings/NanoJev/blob/71a513bb0163b5634467842b523ee0c0ed6fb1c7/README.md',
    modelUrl: 'https://huggingface.co/C-Tianyu/NanoJev', language: 'Python', license: 'MIT', starsAtCapture: 1104,
    summary: { en: 'A 0.6B open replica of the JEV interface with parallel decisions and a training pipeline.', zh: '提供并行判断、动态候选与完整训练流程的 0.6B 开放 JEV 接口复刻。' },
    decision: { en: 'Scores runtime-defined candidates in one pass and exposes complete probability distributions.', zh: '一次前向过程给运行时动态候选评分，并输出完整概率分布。' },
  },
  {
    id: 'jevlike', name: 'Jevlike', owner: 'vinnylarouge', category: 'open-models',
    repoUrl: 'https://github.com/vinnylarouge/jevlike', evidenceUrl: 'https://github.com/vinnylarouge/jevlike/blob/94f5fd1b0b11d52bbdfdf4e0ee6aa96b568f8452/README.md',
    language: 'Python', license: 'MIT', starsAtCapture: 1018,
    summary: { en: 'An independent starter model that scores a changing list of text or visual options in one pass.', zh: '一次为动态文本或视觉候选列表评分的独立入门模型。' },
    decision: { en: 'Returns one probability per option without reproducing JEV’s undisclosed model or training.', zh: '为每个选项返回概率，但不宣称复刻 JEV 未公开的模型或训练方法。' },
  },
  {
    id: 'openclaw-typesafe', name: 'OpenClaw · TypeSafe Plugin', owner: 'openclaw', category: 'sdk-integrations',
    repoUrl: 'https://github.com/openclaw/openclaw', evidenceUrl: 'https://github.com/openclaw/openclaw/blob/1b3f38e7e4ffeee844ee7a3bbcdaf293c65eb2e1/extensions/typesafe/src/decisions.ts',
    language: 'TypeScript', license: 'Mixed', starsAtCapture: 390113,
    summary: { en: 'A first-party-style OpenClaw plugin that exposes TypeSafe as a typed decision provider.', zh: '把 TypeSafe 暴露为类型化决策 Provider 的 OpenClaw 插件。' },
    decision: { en: 'Validates bounded questions locally, calls JEV, and maps typed answers into OpenClaw’s decision contract.', zh: '本地校验有限问题，调用 JEV，再将类型化答案映射到 OpenClaw 决策协议。' },
  },
  {
    id: 'hermes-agent-jev', name: 'Hermes Agent · JEV', owner: 'NousResearch', category: 'routing-optimization',
    repoUrl: 'https://github.com/NousResearch/hermes-agent', evidenceUrl: 'https://github.com/NousResearch/hermes-agent/blob/6406be0f97322eab711224cf90793c42d7af4e96/evals/compaction/jev_arm.py',
    language: 'Python', license: 'MIT', starsAtCapture: 247244,
    summary: { en: 'Hermes Agent includes JEV plugins plus a source-visible compaction evaluation arm.', zh: 'Hermes Agent 提供多种 JEV 插件，并包含可核对源码的上下文压缩评测分支。' },
    decision: { en: 'Scores whether tool calls and their verbatim outputs must remain in the compacted transcript.', zh: '判断工具调用及其原始输出是否必须保留在压缩后的对话中。' },
  },
  {
    id: 'autogpt-typesafe-blocks', name: 'AutoGPT · TypeSafe Blocks', owner: 'Significant-Gravitas', category: 'sdk-integrations',
    repoUrl: 'https://github.com/Significant-Gravitas/AutoGPT', evidenceUrl: 'https://github.com/Significant-Gravitas/AutoGPT/blob/cdc8611c83a2b5270499c3f93437bfcab2d272c4/autogpt_platform/backend/backend/blocks/typesafe/README.md',
    language: 'Python', license: 'Mixed', starsAtCapture: 187451,
    summary: { en: 'Seven AutoGPT blocks for JEV choice, score, batch questions, routing, yes/no, ranking, and filtering.', zh: '覆盖选择、评分、批量提问、路由、是非、排序和过滤的七个 AutoGPT JEV Block。' },
    decision: { en: 'Turns each bounded workflow question into a typed block output while preserving request and response evidence.', zh: '把有限工作流问题转换为类型化 Block 输出，并保留请求与响应证据。' },
  },
  {
    id: 'experiential-typesafe', name: 'Experiential · TypeSafe Gateway', owner: 'experientiallabs', category: 'sdk-integrations',
    repoUrl: 'https://github.com/experientiallabs/experiential', evidenceUrl: 'https://github.com/experientiallabs/experiential/blob/639f9962976741027433f923c8da970e8d66ab40/exp/runtime/models/providers/typesafe.py',
    language: 'Python', license: 'Apache-2.0', starsAtCapture: 5274,
    summary: { en: 'A native TypeSafe System One provider profile for an open model gateway.', zh: '开放模型网关中的原生 TypeSafe System One Provider 配置。' },
    decision: { en: 'Keeps decision traffic on the native System One wire instead of pretending it is a chat completion.', zh: '让决策请求走原生 System One 协议，而不是伪装成 Chat Completion。' },
  },
  {
    id: 'langwatch-jev', name: 'LangWatch · JEV Instant Evals', owner: 'langwatch', category: 'safety-review',
    repoUrl: 'https://github.com/langwatch/langwatch', evidenceUrl: 'https://github.com/langwatch/langwatch/blob/3a68fdba0bc7c20fd3c13a0ff8d94953944de431/platform/app/src/server/app-layer/instant-evals/classifier/jev.client.ts',
    language: 'TypeScript', license: 'Apache-2.0', starsAtCapture: 4833,
    summary: { en: 'A shipped JEV classifier client for LangWatch Instant Evals with explicit retry and token-budget behavior.', zh: '用于 LangWatch Instant Evals 的 JEV 分类器客户端，明确处理重试与 token 预算。' },
    decision: { en: 'Evaluates all configured checks for one text in a typed request before local evaluation policy continues.', zh: '在一次类型化请求中评估一段文本的所有配置检查，再交给本地评测策略。' },
  },
  {
    id: 'open-science-jev', name: 'Open Science · JEV Classification', owner: 'aipoch', category: 'search-data',
    repoUrl: 'https://github.com/aipoch/open-science', evidenceUrl: 'https://github.com/aipoch/open-science/blob/93414f23fcc41eb6edc117e08b11d8ca6929f462/src/main/settings/classification-settings.ts',
    language: 'TypeScript', license: 'Apache-2.0', starsAtCapture: 4709,
    summary: { en: 'A local-first research workbench with configurable JEV/OpenRouter classification services.', zh: '支持配置 JEV / OpenRouter 分类服务的本地优先科研工作台。' },
    decision: { en: 'Routes bounded skill and connector selection through an explicitly configured classification capability.', zh: '通过显式配置的分类能力完成有限的 Skill 与 Connector 选择。' },
  },
  {
    id: 'caliber-jev-compaction', name: 'Caliber · JEV Compaction', owner: 'caliber-ai-org', category: 'developer-tools',
    repoUrl: 'https://github.com/caliber-ai-org/ai-setup', evidenceUrl: 'https://github.com/caliber-ai-org/ai-setup/blob/b37834125b42bdbb9b742302694f9b035d8df256/plugin/caliber-jev-compaction/lib/request.ts',
    language: 'TypeScript', license: 'MIT', starsAtCapture: 1276,
    summary: { en: 'A packaged JEV compaction plugin for synchronised coding-agent setups.', zh: '面向可同步编码 Agent 配置的 JEV 上下文压缩插件。' },
    decision: { en: 'Builds typed keep/drop questions for tool history before local compaction rewrites the context.', zh: '为工具历史构建类型化保留/删除问题，再由本地压缩逻辑重写上下文。' },
  },
  {
    id: 'jegrep', name: 'jegrep', owner: 'can1357', category: 'search-data',
    repoUrl: 'https://github.com/can1357/jegrep', evidenceUrl: 'https://github.com/can1357/jegrep/blob/a280f14f6da8163bde67e0c49f58b23517a02882/src/jev.rs',
    language: 'Rust', license: 'MIT', starsAtCapture: 31,
    summary: { en: 'Semantic grep for live code trees: describe what you need, get files and original line ranges without building an index.', zh: '面向实时代码树的语义 grep：用自然语言描述目标，无需建索引即可返回文件与原始行号范围。' },
    decision: { en: 'JEV scores folders, files, and bounded code passages; local search strategies manage budgets, thresholds, and fallbacks.', zh: 'JEV 为目录、文件和有限代码片段评分，本地搜索策略负责预算、阈值与回退。' },
  },
];

for (const project of additions) {
  project.source ??= githubSource(project.evidenceUrl);
  project.verification = 'source-reviewed';
  project.runtimeVerified = false;
}

const normalizedExisting = catalogue.projects.map((project) => {
  const { xUrl, xAuthor, views, ...rest } = project;
  return {
    ...rest,
    source: project.source ?? {
      type: 'x', label: 'Original X case', url: xUrl, author: xAuthor, views,
    },
  };
});

const byId = new Map(normalizedExisting.map((project) => [project.id, project]));
for (const project of additions) byId.set(project.id, project);

// Keep the first public release locked to the 44-item set approved on 2026-09-20.
// These later discoveries remain in the refresh notes for a follow-up batch.
for (const id of [
  'openclaw-typesafe',
  'hermes-agent-jev',
  'autogpt-typesafe-blocks',
  'experiential-typesafe',
  'langwatch-jev',
  'open-science-jev',
  'caliber-jev-compaction',
]) byId.delete(id);

for (const [id, update] of Object.entries({
  'jev-model-router': { starsAtCapture: 30822, evidenceUrl: 'https://github.com/davila7/claude-code-templates/blob/61bfcd1586bf1076f6d3cfa0436317c912811e6c/cli-tool/components/mods/productivity/jev-model-router/hooks/jev-model-router.ts' },
  'fast-jev-compaction': { starsAtCapture: 4463 },
})) Object.assign(byId.get(id), update);

const projects = [...byId.values()].sort((a, b) => {
  if (a.id === 'jev-ultrafast') return -1;
  if (b.id === 'jev-ultrafast') return 1;
  return b.starsAtCapture - a.starsAtCapture || a.name.localeCompare(b.name);
});

await writeFile(file, `${JSON.stringify({
  schemaVersion: 3,
  capturedAt: '2026-09-20',
  source: {
    name: 'BeatAPI Awesome JEV curation',
    batch: '2026-09-20-github-and-x-refresh',
    policy: 'Project-level deduplication. Direct JEV GitHub matches at or above 1,000 stars are included after fixed-source review; lower-star projects may be included for distinctive practical value. X and GitHub are discovery signals, not runtime verification.',
  },
  projects,
}, null, 2)}\n`);

console.log(`Wrote ${projects.length} source-reviewed projects.`);
