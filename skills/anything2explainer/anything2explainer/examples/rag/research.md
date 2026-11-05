# 《RAG 与知识库》科普视频 · 内容调研文档

> 调研日期：2026-09-06 ｜ 用途：3.5–4 分钟中文 MG 科普视频的事实底稿
> 标注约定：每条事实后附「来源 URL（年份）」；无法在线核实的标【待核】；有争议处写"当前共识/分歧"。
> 说明：本次调研环境仅有网页抓取（无搜索引擎接口），因此以原论文 arXiv 页、官方文档/博客为主要核实来源。

## 0. 执行摘要（给编剧的 1 分钟版）

- **一句话**：RAG = 让大模型先"查资料"再"答题"；知识库 = 把文档切块、变成向量、建好索引的"资料室"。术语来自 Meta 2020 年 NeurIPS 论文。
- **两条流水线**：离线（解析 → 分块 → Embedding → 向量/关键词索引 → 权限元数据）；在线（改写问题 → 粗召回 20–100 条 → 重排留 3–10 条 → 拼上下文 → 带引用作答 → 护栏）。
- **最硬的 6 个数字**：① Anthropic contextual retrieval 把检索失败率降 35%→49%→67%（叠加 BM25、重排）；② 知识库 <20 万 token 可不用 RAG；③ Lost in the Middle 的 U 形曲线；④ RRF 公式 1/(60+rank)；⑤ GraphRAG 全局问题胜率 72–83%；⑥ RAG vs 长上下文：63% 答案相同、Self-Route 省 39–65% 成本。
- **当前共识**：长上下文与 RAG 互补而非替代；"塞得越多越好"已被证伪（Lost in the Middle、Context rot）；2025 年起 RAG 被纳入更大的"上下文工程"框架，检索变成智能体的一个工具（MCP）。
- **最常见的翻车**：切块切断语义、关键词查不到（要混合检索）、查到了没用上（要重排+少放）、表格数字、过期文档、权限泄露、没有评估。
- **推荐比喻**：开卷考试（整体）、图书馆索引卡（向量索引）、把书撕成卡片（分块）、海选+终面（两阶段检索）、三明治/U 形（Lost in the Middle）。
- 全文约 7,600 汉字（含表格与引用），比建议篇幅长；第 1–6 节可按需跳读，第 7 节是可直接使用的素材清单。

## 1. RAG 是什么

**定义与出处**
- RAG = Retrieval-Augmented Generation（检索增强生成）。术语来自 Lewis 等人的论文《Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks》，Facebook AI Research（Meta），发表于 **NeurIPS 2020**。核心思想：把"参数化记忆"（预训练 seq2seq 语言模型，原文用 BART）与"非参数化记忆"（维基百科的稠密向量索引，用 DPR 神经检索器访问）结合，先检索相关段落，再让生成模型以这些段落为条件作答。原文报告在三个开放域问答任务上达到 SOTA，且生成内容比纯参数模型"更具体、更多样、更符合事实"。来源：https://arxiv.org/abs/2005.11401（2020）
- 一句话类比：**闭卷考试 → 开卷考试**。模型不再只靠"背过的东西"作答，而是先翻资料再答题（比喻的失真见第 7 节）。

**RAG 解决 LLM 的三类问题**
1. **幻觉（Hallucination）**：让答案"落地"到检索出的证据上，可附引用、可核查。Lewis 原文即报告 RAG 生成"更符合事实（factual）"。来源：同上（2020）
2. **知识截止 / 时效（Knowledge cutoff）**：模型参数在训练截止后就冻结；知识库可随时增删文档，无需重训。Lewis 原文摘要把"为决策提供出处（provenance）、更新世界知识"列为纯参数模型的未解难题，RAG 的非参数记忆正是对此的回应。来源：同上（2020）
3. **私有数据与权限（Private data / ACL）**：企业内部文档从未进入训练集；RAG 在检索层按用户权限过滤，只把"该用户能看到的"内容交给模型。这是工程实践共识（各向量数据库均提供元数据过滤 / 多租户能力，见第 2 节）。

**与微调、长上下文的对比**（当前共识）

| 维度 | RAG | 微调 Fine-tuning | 长上下文 Long context |
|---|---|---|---|
| 更新频率 | 改文档即生效（分钟级） | 需重新训练（小时/天级） | 每次请求重新塞入 |
| 可溯源 | 强（能指出来自哪段） | 弱（知识"融进"参数） | 中（可指出位置） |
| 单次成本 | 检索开销 + 较短 prompt | 训练成本高，推理便宜 | 每次请求 token 成本随文档量线性增长 |
| 适合 | 知识多、变化快、需引用/权限 | 学"风格/格式/技能"而非事实 | 知识库小、一次性阅读 |

- 长上下文的"分界线"参考：Anthropic 在 Contextual Retrieval 博文中给出经验阈值——知识库 **< 20 万 token（约 500 页）** 时，可直接把整个知识库放进 prompt（配合 prompt caching），不必上 RAG；超过则需要 RAG。来源：https://www.anthropic.com/news/contextual-retrieval（2024）
- 长上下文并非"免费"：Liu 等人《Lost in the Middle》（TACL 2023/2024）发现模型对上下文**开头和结尾**信息利用最好，**中间**显著变差（U 形曲线），即使是专门的长上下文模型也如此。来源：https://arxiv.org/abs/2307.03172（2023）
- 微调 vs RAG：业界共识是"微调教模型**怎么说**，RAG 给模型**说什么**"；二者可叠加（如微调 embedding/reranker 以适配领域）。此为工程经验总结，无单一权威出处。

## 2. 知识库构建（离线 Indexing）流水线

> 一句话：把"人读的文档"变成"机器能按语义查到的碎片"。顺序：解析 → 清洗/去重 → 分块 → 元数据/权限 → Embedding → 建索引（向量 + 关键词）→ 持续更新。

### 2.1 文档解析（Parsing）
- **做什么**：把 PDF / Word / 网页 / 表格 / 扫描件转成带结构的纯文本（Markdown/JSON），保留标题层级、表格、公式、阅读顺序。
- **难点**：PDF 没有"段落"概念，多栏排版、页眉页脚、跨页表格、扫描件都需要**版面分析（layout analysis）+ OCR**。
- **工具举例**：
  - **Docling**（IBM 开源，LF AI & Data 基金会项目，MIT 许可）：支持 PDF/DOCX/PPTX/XLSX/HTML/图片/音频，做版面检测、阅读顺序、表格结构识别、OCR，可直接接 LangChain/LlamaIndex。来源：https://github.com/docling-project/docling（2025–2026）
  - **MinerU**（上海 AI Lab / OpenDataLab）：PDF→Markdown/JSON，公式转 LaTeX、表格转 HTML，OCR 支持 109 种语言；当前版本 3.x，采用 MinerU2.5-Pro VLM 模型，页面自报 OmniDocBench 约 86.47%。来源：https://github.com/opendatalab/MinerU（2026）
  - 其他常见：Unstructured、LlamaParse、PaddleOCR、Marker【工具名列举，未逐一核实版本】。
- **多模态趋势**：ColPali 等方案跳过文本解析，直接把**页面图像**编码为多向量检索（见第 5 节）。

### 2.2 清洗与去重
- 去页眉页脚、导航栏、广告、重复模板文字；规范空白与编码；**近重复去重**（同一文件多版本、镜像页）避免检索结果被同一内容占满。此为工程通识，无单一出处。

### 2.3 分块 Chunking（RAG 里最"手艺活"的一环）
| 策略 | 做法 | 典型参数 / 出处 |
|---|---|---|
| 固定长度 | 按 token/字符数切，可设 overlap | 常见 256–1024 token；LlamaIndex 默认 chunk_size=1024、overlap=20。来源：https://developers.llamaindex.ai/python/framework/optimizing/basic_strategies/basic_strategies/（2025） |
| 递归分割 | 按分隔符层级（段→句→词）递归切，尽量不切断段落/句子 | LangChain RecursiveCharacterTextSplitter；Chroma 实测建议分隔符加上句号/问号。来源：https://www.trychroma.com/research/evaluating-chunking（2024） |
| 语义分块 | 计算相邻句子 embedding 相似度，在"话题跳变"处切 | LlamaIndex SemanticSplitter，breakpoint_percentile_threshold 默认 95；思路源自 Greg Kamradt。来源：https://developers.llamaindex.ai/python/examples/node_parsers/semantic_chunking/（2025） |
| 父子块（小块检索、大块返回） | 用小块做 embedding 匹配，命中后返回其父块给 LLM | LangChain ParentDocumentRetriever 示例：父块 2000 字符、子块 400 字符；LlamaIndex AutoMergingRetriever 默认三层 2048/512/128。来源：https://github.com/langchain-ai/langchain（源码 docstring，2025）；https://developers.llamaindex.ai/python/examples/retrievers/auto_merging_retriever/（2025） |
| Late Chunking | 先把**整篇**送入长上下文 embedding 模型，再在 token 向量层面切块并池化，让每块向量"带着全文语境" | Jina AI，Günther 等，arXiv 2409.04701（2024，修订 2025）。来源：https://arxiv.org/abs/2409.04701 |
| Contextual Retrieval | 索引前让 LLM 为每个块生成 50–100 token 的"上下文说明"（如"本块来自 ACME 公司 2023 Q2 财报"）再一起 embedding / 建 BM25 | Anthropic 2024-09-19。**实测数字**：Contextual Embeddings 单独把 top-20 检索失败率降低 **35%**（5.7%→3.7%）；+ Contextual BM25 降低 **49%**（→2.9%）；再加重排降低 **67%**（→1.9%）。一次性成本（配合 prompt caching）约 **$1.02 / 百万文档 token**。来源：https://www.anthropic.com/news/contextual-retrieval（2024） |
| 树状摘要（RAPTOR） | 递归聚类 + 摘要成树，检索时可在不同抽象层取材 | Sarthi 等，arXiv 2401.18059（2024）；配 GPT-4 在 QuALITY 上绝对提升 20%。来源：https://arxiv.org/abs/2401.18059 |

- **块大小的实证**：
  - Chroma 技术报告（2024-07）：在 text-embedding-3-large 上，递归分割 **200 token、无重叠**表现很好；不同策略召回率差距可达 9%；OpenAI 助手默认的 800 token / 400 overlap 表现"略低于平均"。来源：https://www.trychroma.com/research/evaluating-chunking（2024）
  - NVIDIA 博客（2025-06）：**页级分块**平均准确率 0.648 最高且最稳定；128 与 2048 token 两个极端最差；中等 512–1024 token 普遍较好，但随数据类型变化。来源：https://developer.nvidia.com/blog/finding-the-best-chunking-strategy-for-accurate-ai-responses/（2025）
  - Pinecone 建议测试区间：128–256 token（细粒度）到 512–1024 token（保留更多上下文）。来源：https://www.pinecone.io/learn/chunking-strategies/（2025）
  - **当前共识**：没有万能块大小；小块检索更准、大块生成更全，因此"小块检索 + 大块/邻块返回"成为主流折中。

### 2.4 元数据与权限
- 每个块携带元数据：来源文件、页码、标题路径、更新时间、作者、**ACL（允许访问的用户/组）**、租户 ID。查询时先按元数据**预过滤**再做向量相似度，避免"先查到再删"带来的泄露与 top-k 不足。来源：LlamaIndex 元数据过滤说明 https://developers.llamaindex.ai/python/framework/optimizing/basic_strategies/basic_strategies/（2025）
- 多租户：Weaviate 为每个租户分配独立分片与向量索引，单节点可承载 5 万+活跃租户。来源：https://docs.weaviate.io/weaviate/concepts/data（2025）
- Qdrant 的"可过滤 HNSW"：为已建 payload 索引的字段在 HNSW 图上增加额外边，使过滤与向量搜索同步进行；建议先建 payload 索引再灌数据。来源：https://qdrant.tech/documentation/concepts/indexing/（2025）
- 安全视角：OWASP LLM Top 10（2025 版）单列 **LLM08 "向量与嵌入弱点"**，明确多租户环境下"一组的 embedding 可能被另一组的查询检出"，要求"细粒度访问控制与权限感知的向量库"。来源：https://genai.owasp.org/llmrisk/llm082025-vector-and-embedding-weaknesses/（2025）

### 2.5 Embedding（把文本变成向量）
- **原理一句话**：用神经网络（多为 Transformer 双编码器）把一段文本映射为固定长度的实数向量，使语义相近的文本在向量空间中距离近（余弦相似度/点积）。稠密检索的奠基工作 DPR（Karpukhin 等，EMNLP 2020）报告 top-20 检索准确率比 BM25 高 9–19 个百分点。来源：https://arxiv.org/abs/2004.04906（2020）
- **维度范围**：从 384 维（all-MiniLM-L6-v2，Hugging Face 月下载 2.5 亿次量级）到 4096 维（Qwen3-Embedding-8B）；主流 1024–3072。来源：https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2（2026 抓取）；https://qwenlm.github.io/blog/qwen3-embedding/（2025）
- **Matryoshka 表示学习（MRL）**：训练时让向量前缀也可用，允许按需截短维度（如 3072→768）以省存储。OpenAI text-embedding-3、Gemini Embedding、Qwen3-Embedding、Voyage 均支持。
- **2025–2026 主流模型**（数字均来自官方页面）：

| 模型 | 维度 | 上下文 | 语言 | 备注 / 来源 |
|---|---|---|---|---|
| BAAI bge-m3（开源） | 1024 | 8192 token | 100+ | 同时支持稠密/稀疏/多向量三种检索。https://arxiv.org/abs/2402.03216（2024） |
| Qwen3-Embedding 0.6B/4B/8B（开源，Apache 2.0） | 1024/2560/4096，支持 MRL | 32k token | 100+ | 8B 版发布时（2025-06-05）以 **70.58** 分居 MTEB 多语言榜首。https://qwenlm.github.io/blog/qwen3-embedding/（2025）；https://arxiv.org/abs/2506.05176 |
| OpenAI text-embedding-3-small / -large | 1536 / 3072，可截短 | 8192 token | — | 官方页 MTEB 分数 62.3% / 64.6%（2024 年口径）。https://developers.openai.com/api/docs/guides/embeddings |
| Google gemini-embedding-001 / gemini-embedding-2 | 默认 3072，可截 768/1536 | 2048 / 8192 token | 100+ | 001 版 2025-07 GA，官方称自 3 月实验版起"稳居 MTEB 多语言榜前列"，$0.15/百万 token；embedding-2 为多模态。https://developers.googleblog.com/en/gemini-embedding-available-gemini-api/（2025）；https://ai.google.dev/gemini-api/docs/embeddings（2026） |
| Voyage voyage-4 系列（voyage-4-large/4/4-lite，含开源 voyage-4-nano） | 默认 1024，可选 256–2048 | 32k token | — | 另有代码/金融/法律领域模型。https://docs.voyageai.com/docs/embeddings（2026）；Voyage 于 2025 年并入 MongoDB【待核 官方公告链接】 |

- **MTEB 榜单地位**：MTEB（Muennighoff 等，2022）最初含 8 类任务、58 个数据集、112 种语言；2025 年扩为 **MMTEB**（ICLR 2025）：500+ 任务、250+ 语言。榜单排名月度变动大，视频中只宜说"某模型在发布时登顶"，勿说"当前第一"。来源：https://arxiv.org/abs/2210.07316（2022）；https://arxiv.org/abs/2502.13595（2025）。**2026-09 当前榜首【待核】**。

### 2.6 向量索引（ANN：近似最近邻）
- **为什么要近似**：暴力比对（Flat）是 O(N·d)，百万级向量每次查询都要算百万次距离；ANN 用少量精度换几十到几百倍速度。
- **三类核心结构（一句话原理）**：
  - **HNSW**（Malkov & Yashunin，arXiv 2016，后刊于 IEEE TPAMI【待核 期刊卷期】）：多层"可导航小世界图"，上层稀疏用于快速定位、下层稠密用于精确逼近，作者称查询复杂度达到**对数级**。关键参数 M（每点边数）、ef_construction、ef_search；Qdrant 默认 m=16、ef_construct=100。来源：https://arxiv.org/abs/1603.09320（2016）；https://qdrant.tech/documentation/concepts/indexing/（2025）
  - **IVF**（倒排文件）：先 k-means 把向量分到 nlist 个"格子"（Voronoi 单元），查询时只搜最近的 nprobe 个格子。来源：https://github.com/facebookresearch/faiss/wiki/Faiss-indexes
  - **PQ**（乘积量化）：把 d 维向量切成 M 段，每段用 8 bit 码本近似，内存从每向量 4d 字节压到 M 字节量级（如 768 维 float32 ≈ 3 KB → PQ 后几十字节）。来源：同上；FAISS 起源论文 Johnson 等《Billion-scale similarity search with GPUs》，arXiv 1702.08734（2017）
- **常见向量数据库/引擎**（均支持 HNSW）：FAISS（Meta 开源库，非服务）；Milvus（Zilliz 发起，LF AI & Data 项目，支持 HNSW/IVF/DiskANN/GPU CAGRA，自称支撑"百亿级"向量，文档当前为 3.0.x）；Qdrant；Weaviate；**pgvector**（Postgres 扩展，支持 HNSW 与 IVFFlat，vector 类型最高 16000 维，普通索引 ≤2000 维，当前 0.8.x）；Elasticsearch / OpenSearch（原生 kNN + BM25 + RRF）。来源：https://milvus.io/docs/overview.md（2026）；https://github.com/pgvector/pgvector（2026）；https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion
- **选型共识**：数据 < 千万级且已有 Postgres → pgvector 足够；需要多租户/过滤/横向扩展 → 专用向量库；已有 ES → 直接用其混合检索。此为工程经验。

### 2.7 混合检索（Hybrid Search）
- **BM25**（Robertson、Spärck Jones 等 1970–80 年代概率检索框架，Okapi 系统得名）：基于词频、逆文档频率、文档长度归一化的词袋打分；典型参数 k1∈[1.2, 2.0]，b=0.75。擅长精确词、型号、人名、代码符号。来源：https://en.wikipedia.org/wiki/Okapi_BM25
- **向量检索**擅长同义改写、跨语言、模糊描述；两者互补。BEIR 基准（NeurIPS 2021）指出 BM25 是"稳健基线"，零样本下不少稠密模型反而不如它。来源：https://arxiv.org/abs/2104.08663（2021）
- **RRF 融合公式**（Cormack、Clarke、Büttcher，SIGIR 2009）：
  `RRFscore(d) = Σ_r 1 / (k + rank_r(d))`，原文 k=60，作者称"k=60 接近最优，但取值并不关键"；RRF 平均比最佳单系统高 4–5%。来源：http://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf（2009）。Elasticsearch 的 rank_constant 默认也是 60。来源：https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion
- Weaviate 另提供 relativeScoreFusion（归一化分数加权，alpha 控制两路权重），自 v1.24 起为默认，内部测试召回率约提升 6%。来源：https://weaviate.io/blog/hybrid-search-fusion-algorithms（2023）
- Anthropic 实测：在 contextual embedding 之上叠加 contextual BM25，失败率再从 3.7% 降到 2.9%。来源：https://www.anthropic.com/news/contextual-retrieval（2024）

### 2.8 增量更新与新鲜度
- 以 doc_id + 内容哈希跟踪每篇文档，变更时只重嵌入受影响的块（LlamaIndex `refresh_ref_docs` 即"同 id、不同内容才更新"）。来源：https://developers.llamaindex.ai/python/framework/module_guides/indexing/document_management/（2025）
- 注意 HNSW 删除代价高（FAISS 的 IndexHNSWFlat 不支持删除，需标记删除/重建）。来源：https://github.com/facebookresearch/faiss/wiki/Faiss-indexes
- 时效性问题不只在文档侧：FreshLLMs（Google，2023）显示"所有模型（无论大小）在快速变化的知识和错误前提问题上都表现糟糕"，且"检索证据的数量与顺序都关键"。来源：https://arxiv.org/abs/2310.03214（2023）
- 图结构方案的更新成本是分歧点：GraphRAG 需重建社区摘要，LightRAG（2024）主打"增量更新算法，无需全量重建索引"。来源：https://arxiv.org/abs/2410.05779（2024）

## 3. 在线检索与生成（Query 时）

> 一句话：用户一句话进来 → 改写成"好查的问题" → 粗召回几十条 → 精排留几条 → 拼成有出处的上下文 → 模型带引用作答 → 护栏兜底。

### 3.1 查询改写（Query Transformation）
- **Query Rewriting**：用 LLM 把口语化/含上下文指代的问题改写成适合检索的查询。代表工作 Ma 等《Query Rewriting for Retrieval-Augmented LLMs》提出 Rewrite-Retrieve-Read 框架（EMNLP 2023）。来源：https://arxiv.org/abs/2305.14283（2023）
- **Multi-query**：让 LLM 生成同一问题的多个变体分别检索，取并集，缓解"一种表述查不到"的问题。LangChain MultiQueryRetriever 默认生成 **3** 个版本。来源：LangChain 源码 docstring https://github.com/langchain-ai/langchain（2025）
- **HyDE**（Hypothetical Document Embeddings，Gao 等 2022）：先让 LLM"编"一段可能的答案文档，用它的向量去检索真实文档——"以答找答"比"以问找答"更贴近文档分布。来源：https://arxiv.org/abs/2212.10496（2022）
- **Step-back prompting**（Google DeepMind，ICLR 2024）：先问一个更抽象的"退一步"问题（原理/背景），再回到具体问题；原文在物理/化学 QA 上提升 7–11%，时间推理提升 27%，多跳提升 7%。来源：https://arxiv.org/abs/2310.06117（2023）
- **路由 / 自适应**：Adaptive-RAG（NAACL 2024）用分类器按问题复杂度分流到"不检索 / 单步检索 / 多步检索"。来源：https://arxiv.org/abs/2403.14403（2024）

### 3.2 检索 top-k 的典型值
- 框架默认值：LlamaIndex similarity_top_k 默认 **2**（文档建议块变小则加倍到 4）；LangChain 向量检索器默认 **k=4**。来源：https://developers.llamaindex.ai/python/framework/optimizing/basic_strategies/basic_strategies/（2025）；LangChain 源码 https://github.com/langchain-ai/langchain（2025）
- 生产实践是"**两阶段**"：先粗召回 20–100 条，再重排取 3–10 条。Anthropic 实验比较 5/10/20 块，**20 块最好**；Pinecone 示例取 top-25 再重排到 top-3。来源：https://www.anthropic.com/news/contextual-retrieval（2024）；https://www.pinecone.io/learn/series/rag/rerankers/
- 检索模式：相似度、MMR（最大边际相关，兼顾多样性）、相似度阈值。来源：LangChain 源码（2025）

### 3.3 重排 Rerank
- **为什么需要**：Embedding 双编码器把整段压成一个向量，会丢信息；**Cross-encoder** 把"问题+候选段"拼在一起过一遍 Transformer，直接打相关分，更准但慢——Pinecone 估算：用小 BERT 重排 4000 万条记录在 V100 上要 50+ 小时，而向量检索 <100 ms，因此只能对少量候选重排。来源：https://www.pinecone.io/learn/series/rag/rerankers/
- **模型举例**：
  - **bge-reranker-v2-m3**（BAAI，开源，基于 bge-m3，约 0.6B 参数）：输入问题-段落对，直接输出相关分，多语言。来源：https://huggingface.co/BAAI/bge-reranker-v2-m3（2024）
  - **Qwen3-Reranker 0.6B/4B/8B**（2025-06，Apache 2.0）。来源：https://arxiv.org/abs/2506.05176（2025）
  - **Cohere Rerank**：rerank-v3.5（2024-12-02 发布）、rerank-v4.0-pro / -fast，单一多语言模型，100+ 语言。来源：https://docs.cohere.com/docs/rerank-overview（2026）；https://cohere.com/blog/rerank-3pt5（2024）
- **ColBERT 晚交互（late interaction）**（Khattab & Zaharia，SIGIR 2020）：文档与查询各自编码成**每个 token 一个向量**，查询时用 MaxSim 做细粒度匹配——介于双编码器与 cross-encoder 之间：可离线预计算，又保留词级交互。来源：https://arxiv.org/abs/2004.12832（2020）。BEIR 也发现"重排与晚交互模型平均零样本效果最好"。来源：https://arxiv.org/abs/2104.08663（2021）
- Anthropic 实测：在混合检索之上再加重排，top-20 失败率从 2.9% 降到 1.9%。来源：https://www.anthropic.com/news/contextual-retrieval（2024）

### 3.4 上下文组装
- **去重与合并**：同一父块的多个子块合并、近重复块去掉（父子块/AutoMerging 机制，见 2.3）。
- **排序与位置**：《Lost in the Middle》（Liu 等，TACL 2023）：模型对**开头和结尾**的信息利用最好、**中间**明显变差，呈 U 形；即便专门的长上下文模型也如此。工程上因此把最相关的块放两端，或直接少放。来源：https://arxiv.org/abs/2307.03172（2023）
- **Context rot**（Chroma，2025-07）：测试 18 个模型（含 GPT-4.1、Claude 4、Gemini 2.5、Qwen3），即使简单任务，可靠性也随输入长度非均匀下降；干扰项的负面影响在长输入下被放大。结论：**并非塞得越多越好**。来源：https://www.trychroma.com/research/context-rot（2025）
- Anthropic 对"上下文工程"的表述：目标是找到"**最小的高信号 token 集合**"。来源：https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents（2025）

### 3.5 带引用的生成（Citation / Grounding）
- 做法：给每个块编号或带元数据（文件名、页码、URL），要求模型在句末标注引用；或使用模型原生引用能力。
- Anthropic **Citations** 功能：让模型引用源文档中的具体句子/段落；官方称比多数自建方案"召回准确率最高提升 15%"；客户 Endex 报告"来源幻觉与格式问题从 10% 降到 0%，每次回答引用数增加 20%"。来源：https://claude.com/blog/introducing-citations-api（2025，首发 2025-01【日期待核】）
- 可核查的引用本身就是 RAG 相对纯生成的核心卖点（Lewis 2020 把"提供出处 provenance"列为关键问题）。来源：https://arxiv.org/abs/2005.11401

### 3.6 提示词模板要点（来自官方最佳实践）
- **长资料放最前面**，问题与指令放后面（Anthropic 官方："放在查询、指令和示例之上……对所有模型都有提升"）。
- 用 **XML 标签/结构化字段**包裹每份文档并附元数据（source、page）。
- **先引原文再作答**："让 Claude 先摘出相关引文，再执行任务，有助于聚焦相关内容、忽略其余部分"。
- 明确"**只依据给定资料回答；资料不足时说不知道**"。
来源：https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices（2026，Long context prompting 小节）

### 3.7 护栏（Guardrails）
- **拒答/兜底**：检索分数低于阈值或重排后无高分候选时，返回"知识库中没有相关信息"而不是硬答；CRAG 论文正式化了这一思路——用检索评估器判"正确/错误/模糊"，错误时转外部搜索。来源：https://arxiv.org/abs/2401.15884（2024）
- **权限过滤**：在检索层按 ACL 预过滤（见 2.4），而不是让 LLM"自觉"不说。OWASP 明确要求"权限感知的向量与嵌入存储"。来源：https://genai.owasp.org/llmrisk/llm082025-vector-and-embedding-weaknesses/（2025）
- **注入防护**：知识库文档本身可能含提示注入/投毒内容（OWASP 同页列出"数据投毒"），需对入库内容做来源认证与校验。来源：同上

## 4. 评估

### 4.1 RAGAS 四个核心指标（官方定义）
RAGAS（Es 等，2023；框架强调"无需人工标注的参考答案"也能评估）。来源：https://arxiv.org/abs/2309.15217（2023）

| 指标 | 评什么 | 官方计算方式 | 范围 |
|---|---|---|---|
| **Faithfulness 忠实度** | 答案是否"只说了资料里有的话" | 把答案拆成若干 claim，逐条判断能否由检索上下文推出；**得分 = 被上下文支持的 claim 数 / 总 claim 数** | 0–1 |
| **Answer Relevancy 答案相关性** | 答案是否对题 | 让 LLM 根据答案反向生成 N 个（默认 3 个）问题，与原问题做 embedding 余弦相似度后取平均 | 约 0–1（余弦可为负） |
| **Context Precision 上下文精确率** | 检索结果里相关块是否排在前面 | 对 top-K 每个位置算 precision@k，按"该位置是否相关"加权求平均（排序敏感：无关块排第一扣分最重） | 0–1 |
| **Context Recall 上下文召回率** | 该找到的有没有都找到 | 把**参考答案**拆成 claim，**得分 = 能被检索上下文支持的 claim 数 / 参考答案 claim 总数**（需要参考答案） | 0–1 |

来源：https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/ 、.../answer_relevance/ 、.../context_precision/ 、.../context_recall/（2025–2026）
- 类似框架：TruLens 的 **RAG Triad**（Context Relevance、Groundedness、Answer Relevance）。来源：https://www.trulens.org/getting_started/core_concepts/rag_triad/

### 4.2 检索指标（经典 IR）
- **Recall@k**：正确文档是否出现在前 k 条（RAG 最常看的指标，因为生成只能用到检索出的内容）。
- **MRR**（平均倒数排名）：每个查询取"第一条相关结果的排名倒数"再平均，只关心第一条命中。来源：https://en.wikipedia.org/wiki/Mean_reciprocal_rank
- **nDCG**（归一化折损累计增益，Järvelin & Kekäläinen 2002）：按位置以 log2(i+1) 折损求相关度累计，再除以理想排序的 DCG，范围 0–1；适合多级相关性。来源：https://en.wikipedia.org/wiki/Discounted_cumulative_gain
- Anthropic 博文使用的是"**top-20 检索失败率**"（= 1 − Recall@20）。来源：https://www.anthropic.com/news/contextual-retrieval（2024）

### 4.3 常见 Benchmark
- **BEIR**（NeurIPS 2021 数据集赛道）：18 个数据集的零样本检索基准；结论"BM25 是稳健基线"。来源：https://arxiv.org/abs/2104.08663（2021）
- **MTEB / MMTEB**：Embedding 模型综合榜（MMTEB 500+ 任务、250+ 语言，ICLR 2025）。来源：https://arxiv.org/abs/2502.13595（2025）
- **RAGBench**（Friel 等，2024）：10 万条样例、5 个行业领域（用户手册等真实语料），提出 TRACe 评估框架；发现微调的 RoBERTa 评估器可胜过 LLM 评估器。来源：https://arxiv.org/abs/2407.11005（2024）
- **HotpotQA**（EMNLP 2018）：11.3 万条多跳问答，检验"需要跨多篇文档推理"的能力。来源：https://arxiv.org/abs/1809.09600（2018）
- **ViDoRe**：ColPali 提出的视觉文档检索基准。来源：https://arxiv.org/abs/2407.01449（2024）
- **FreshQA**：考察时效性知识。来源：https://arxiv.org/abs/2310.03214（2023）

### 4.4 线上指标（工程通识，无单一出处）
- 用户显式反馈（👍/👎）、追问率/改写率、引用点击率、"无法回答"占比、人工抽检的幻觉率、P95 延迟、每次问答成本。
- Barnett 等提醒："RAG 系统的验证只有在运行中才可行"，鲁棒性是"演进出来的，而非一开始设计好的"。来源：https://arxiv.org/abs/2401.05856（2024）

## 5. 进阶形态（2024–2026）

### 5.1 GraphRAG（微软，2024）
- 论文《From Local to Global: A Graph RAG Approach to Query-Focused Summarization》（Edge 等，arXiv 2024-04，v2 2025-02）；微软研究院博文 2024-02-13。
- **核心思路**：用 LLM 从文档抽取实体与关系构成知识图 → 用 **Leiden 算法**分层做社区检测 → 为每个社区预生成摘要 → 回答"全局性问题"（如"这批文档的五大主题是什么"）时，让每个社区摘要各出一段部分答案再汇总。
- **实测**：在约 100 万 token（播客）与 170 万 token（新闻）语料上，相对朴素向量 RAG，**全面性胜率 72–83%**、**多样性胜率 62–82%**。来源：https://arxiv.org/abs/2404.16130 ；https://arxiv.org/html/2404.16130（2024）；https://www.microsoft.com/en-us/research/blog/graphrag-unlocking-llm-discovery-on-narrative-private-data/（2024）
- **适用/代价**：适合"要把整批文档串起来理解"的全局问题；代价是建图与社区摘要成本高、更新慢。LightRAG（2024）主打图 + 双层检索 + 增量更新，作为更轻的替代。来源：https://arxiv.org/abs/2410.05779（2024）

### 5.2 Agentic RAG / Deep Research
- **从"一次检索"到"多轮检索 + 自我反思"**：
  - ReAct（ICLR 2023）：推理轨迹与动作（如查维基）交替进行。来源：https://arxiv.org/abs/2210.03629
  - Self-Ask（2022）：模型先自问自答一串后续问题，再合成答案，可接搜索引擎；提出"组合性鸿沟"。来源：https://arxiv.org/abs/2210.03350
  - **Self-RAG**（Asai 等，ICLR 2024）：训练模型输出"反思 token"，按需决定是否检索、并对检索结果与自身生成打分批判。来源：https://arxiv.org/abs/2310.11511（2023）
  - **CRAG**（Yan 等，2024）：轻量检索评估器给出置信度 → 正确/错误/模糊三种动作，错误时转网页搜索；对文档做"分解-再重组"去噪。来源：https://arxiv.org/abs/2401.15884（2024）
  - Agentic RAG 综述（Singh 等，2025）：把"反思、规划、工具使用、多智能体协作"嵌入 RAG 流水线。来源：https://arxiv.org/abs/2501.09136（2025）
- **Deep Research 产品化**：Google Gemini Deep Research 2024-12-11 上线（生成多步研究计划→反复搜索→带引用报告）；OpenAI Deep Research 2025-02 上线，自主浏览网页 5–30 分钟后输出带引用报告。来源：https://blog.google/products/gemini/google-gemini-deep-research/（2024）；https://en.wikipedia.org/wiki/Deep_research（2025）
- 本质：**RAG 的检索环节从"一次向量查询"变成"智能体的一个工具调用"，可反复调用、可换数据源**。

### 5.3 多模态 RAG
- **ColPali**（Faysse 等，ICLR 2025）：用视觉语言模型直接把**文档页面图像**编码成多向量（ColBERT 式晚交互），跳过 OCR/版面解析，保留表格、图表、版式信息；配套 ViDoRe 基准。后续 ColQwen2 基于 Qwen2-VL。来源：https://arxiv.org/abs/2407.01449（2024）；https://huggingface.co/vidore/colqwen2-v1.0
- 多模态 embedding：Gemini Embedding 2 支持文本+图像等多模态输入（8192 token）。来源：https://ai.google.dev/gemini-api/docs/embeddings（2026）
- 表格是老大难：TableRAG（Google，NeurIPS 2024）指出整表塞入 prompt 不可扩展，改为"schema 检索 + 单元格检索"处理百万 token 级表格。来源：https://arxiv.org/abs/2410.04739（2024）

### 5.4 长上下文 vs RAG：当前共识与分歧
- **上下文窗口现状**：Gemini 自称"首个 1M token 模型"；Claude Sonnet 4 于 2025-08-12 开放 1M token（"75,000 行代码"或"几十篇论文"）。来源：https://ai.google.dev/gemini-api/docs/long-context ；https://claude.com/blog/1m-context（2025）
- **对比研究**：Li 等（Google，EMNLP 2024 Industry）：资源充足时长上下文平均更准，但 RAG **成本显著更低**；两者在 63% 的问题上给出完全相同的答案，因此提出 **Self-Route**（先 RAG，模型自判"答不了"再走长上下文），成本降低 65%（Gemini-1.5-Pro）/ 39%（GPT-4o）而效果接近长上下文。来源：https://arxiv.org/abs/2407.16833 ；https://arxiv.org/html/2407.16833（2024）
- Databricks（2024-08，2000+ 次实验、13 个模型）：多给文档先涨后跌，多数模型在 32k–64k 后性能下滑，仅少数（GPT-4o、Claude 3.5 Sonnet 等）保持；失败形态各异（拒答、答错、复读）。来源：https://www.databricks.com/blog/long-context-rag-performance-llms（2024）
- **当前共识**（综合上述）：① 小知识库（<20 万 token）直接长上下文 + 缓存；② 大知识库、需权限/引用/低成本 → RAG；③ 长上下文让 RAG 可以"多放几块"，二者是**互补**而非替代；④ "塞得越多越好"被 Lost-in-the-middle 与 Context rot 否定。**分歧点**：随着 1M 窗口与更好的长上下文训练普及，"中等规模知识库是否还需要 RAG"仍在变化。

### 5.5 上下文工程（Context Engineering，2025）
- 出处：2025 年 6 月 Shopify CEO Tobi Lütke 推文主张用"context engineering"取代"prompt engineering"——"核心技能是为任务提供全部上下文，使其能被 LLM 合理解决"；Andrej Karpathy 随后附议："上下文工程是把恰到好处的信息填进上下文窗口以供下一步使用的精妙艺术与科学"。来源（二手引用）：https://simonwillison.net/2025/Jun/27/context-engineering/ ；https://www.philschmid.de/context-engineering（2025-06-30）；原推链接【待核】
- LangChain 博文（2025-06-23）定义："构建动态系统，以正确格式提供正确信息与工具，使 LLM 能合理完成任务"。来源：https://www.langchain.com/blog/the-rise-of-context-engineering
- Anthropic 工程博文（2025-09-29）：上下文工程 = "在推理时为 LLM 策划并维护最优 token 集合的策略"；核心原则"最小的高信号 token 集合"；提出 **just-in-time 检索**——智能体只保留轻量标识（文件路径、查询、链接），运行时按需用工具加载，而非预先全部检索塞入。来源：https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents（2025）
- **与 RAG 的关系**：RAG 是上下文工程的一个子集/手段——"往窗口里放什么"这一问题的检索式解法。

### 5.6 Memory 与 RAG
- **MemGPT**（Packer 等，2023）：借鉴操作系统虚拟内存，把对话/文档在"主上下文"与"外部存储"间分层分页调度。来源：https://arxiv.org/abs/2310.08560（2023）
- **Mem0**（2025-04）：从对话中抽取并存储要点，按需检索；报告比 OpenAI 记忆方案 LLM-judge 分数相对提升 26%，比全量上下文 p95 延迟低 91%、token 成本省 90%+；图记忆变体再高约 2%。来源：https://arxiv.org/abs/2504.19413（2025）
- **关系**：Memory 本质是"对**自身历史交互**做 RAG"（写入端多了抽取/更新/遗忘），知识库 RAG 则针对**外部文档**；两者共用 embedding + 向量检索基础设施。

### 5.7 MCP 与工具化检索
- **MCP**（Model Context Protocol，Anthropic 2024-11-25 开源）："连接 AI 应用与外部系统的开放标准"，官方比喻为"**AI 应用的 USB-C 接口**"；首批预置服务器含 Google Drive、Slack、GitHub、Postgres 等；现已被 Claude、ChatGPT、VS Code、Cursor 等支持。来源：https://www.anthropic.com/news/model-context-protocol（2024）；https://modelcontextprotocol.io/introduction（2026）
- **意义**：知识库不再只是"一个向量库"，而是通过 MCP 等协议暴露为模型可调用的**检索工具**（搜数据库、查文档、调 API），由智能体决定何时查、查什么——这与 Anthropic 的 just-in-time 上下文思路一致。

## 6. 常见失败模式与工程经验（每条一句话）

学术依据：Barnett 等《Seven Failure Points When Engineering a RAG System》（2024）归纳的七类失败点：内容缺失、相关文档未排进 top-k、在候选中但未进上下文、在上下文中但未被提取、格式错误、具体程度不对、答案不完整。来源：https://arxiv.org/abs/2401.05856（2024）

1. **分块切断语义**：固定长度把一句话、一张表切成两半，任一半都无法独立回答问题 → 用递归/语义分块、父子块、contextual retrieval 补语境（Anthropic 实测失败率降 35–67%）。来源：https://www.anthropic.com/news/contextual-retrieval
2. **检索召回不到**：用户用的词和文档不一样、缩写/型号/人名 → 上混合检索（BM25 + 向量）+ 查询改写 + 多查询。来源：BEIR https://arxiv.org/abs/2104.08663
3. **检索到但没用上**（"Not extracted"）：相关块在上下文中间被忽略，或被噪声块淹没 → 重排、少而精、把关键块放两端、先引原文再答。来源：Lost in the Middle https://arxiv.org/abs/2307.03172 ；Barnett FP4
4. **多跳问题**：答案需要串联多篇文档，一次检索拿不全 → 多轮/智能体式检索（Self-Ask、Self-RAG、CRAG）、GraphRAG。来源：HotpotQA https://arxiv.org/abs/1809.09600
5. **表格与数字**：表格被打平成文字后行列对应关系丢失，数字被错读 → 保留表格结构（HTML/Markdown）、schema+单元格检索、或走视觉检索。来源：TableRAG https://arxiv.org/abs/2410.04739 ；ColPali https://arxiv.org/abs/2407.01449
6. **过期文档**：旧版本与新版本同时在库，模型引用了作废内容 → 元数据带版本/时间、去重、增量刷新、时效性优先排序。来源：FreshLLMs https://arxiv.org/abs/2310.03214 ；LlamaIndex refresh_ref_docs
7. **权限泄露**：多租户共用索引、先查后过滤 → 检索前按 ACL 预过滤、租户物理隔离。来源：OWASP LLM08:2025
8. **评估缺失**：上线前只看 demo，不知道召回率与忠实度 → 建 100–300 条黄金问答集，跟踪 Recall@k、Faithfulness 等。来源：RAGAS https://arxiv.org/abs/2309.15217 ；Barnett（"验证只能在运行中进行"）
9. **成本/延迟**：每问都过大模型重排 + 长上下文 → 两阶段检索、Self-Route 按需走长上下文（省 39–65%）、prompt caching（contextual retrieval 一次性成本 $1.02/百万 token）。来源：https://arxiv.org/html/2407.16833 ；https://www.anthropic.com/news/contextual-retrieval
10. **文档解析失真**（补充）：PDF 多栏、页眉页脚、扫描件 OCR 错误直接污染下游一切 → 用 Docling/MinerU 等版面解析工具并抽检。来源：见 2.1

## 7. 可用于视频的"数字与比喻清单"

### 7.1 有出处的数字/事实（可信度：★★★ 原论文/官方；★★ 官方博客实测，单一数据集；★ 二手或待核）
| # | 可直接讲的事实 | 出处 | 可信度 |
|---|---|---|---|
| 1 | RAG 一词来自 2020 年 Meta（Facebook AI）的 NeurIPS 论文，最初是"语言模型 + 维基百科向量索引" | https://arxiv.org/abs/2005.11401 | ★★★ |
| 2 | Anthropic 实测：给每个块补 50–100 token 的"上下文说明"，top-20 检索失败率降 35%；再叠加 BM25 降 49%；再加重排降 67%（5.7%→1.9%） | https://www.anthropic.com/news/contextual-retrieval（2024） | ★★（Anthropic 自有数据集） |
| 3 | 知识库不到 20 万 token（≈500 页）时，可以不用 RAG，直接整个塞进 prompt | 同上 | ★★ |
| 4 | Lost in the Middle：模型对上下文开头和结尾记得最牢，中间最容易漏——U 形曲线 | https://arxiv.org/abs/2307.03172（2023） | ★★★ |
| 5 | Context rot：2025 年测 18 个前沿模型，输入越长越不可靠，哪怕任务很简单 | https://www.trychroma.com/research/context-rot（2025） | ★★ |
| 6 | 典型 chunk 大小 256–1024 token；LlamaIndex 默认 1024；Chroma 实测 200 token 无重叠效果好；NVIDIA 实测"按页切"最稳 | LlamaIndex 文档；Chroma 2024；NVIDIA 2025 | ★★ |
| 7 | HNSW 查询复杂度是对数级：百万向量也只需几十步"跳跃"即可逼近最近邻 | https://arxiv.org/abs/1603.09320（2016） | ★★★（"几十步"为对数级的口语化，非原文数字） |
| 8 | RRF 融合公式 1/(60+排名)，k=60 来自 2009 年 SIGIR 论文的试验，作者说"取值不关键" | http://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf | ★★★ |
| 9 | 稠密检索开山作 DPR：top-20 准确率比 BM25 高 9–19 个百分点（2020）；但 BEIR（2021）发现零样本下 BM25 仍是难以击败的基线 | https://arxiv.org/abs/2004.04906 ；https://arxiv.org/abs/2104.08663 | ★★★ |
| 10 | Embedding 维度从 384（MiniLM）到 4096（Qwen3-8B）；Qwen3-Embedding-8B 发布时以 70.58 分登顶 MTEB 多语言榜 | https://qwenlm.github.io/blog/qwen3-embedding/（2025） | ★★★（"发布时"限定） |
| 11 | 重排很贵：小 BERT 重排 4000 万条要 50+ 小时，向量检索 <100 ms——所以只能"粗召回 25 条，精排留 3 条" | https://www.pinecone.io/learn/series/rag/rerankers/ | ★★ |
| 12 | GraphRAG 在 100 万 token 语料上，回答全局性问题时全面性胜率 72–83% | https://arxiv.org/abs/2404.16130（2024） | ★★★（LLM 评审） |
| 13 | RAG vs 长上下文：63% 的问题两者答案完全一样；先 RAG、答不了再长上下文，可省 39–65% 成本 | https://arxiv.org/abs/2407.16833（2024） | ★★★ |
| 14 | Weaviate 单节点可跑 5 万+ 租户，各自独立索引——权限隔离靠架构而非靠模型"自觉" | https://docs.weaviate.io/weaviate/concepts/data | ★★ |
| 15 | OWASP 2025 把"向量与嵌入弱点"列为 LLM 十大风险之一（LLM08） | https://genai.owasp.org/llmrisk/llm082025-vector-and-embedding-weaknesses/ | ★★★ |
| 16 | pgvector 让 Postgres 直接存向量：vector 类型最高 16000 维，支持 HNSW/IVFFlat | https://github.com/pgvector/pgvector | ★★★ |

### 7.2 适合动画表现的 5 个比喻
| 比喻 | 对应概念 | 贴切之处 | 失真之处（讲解时可顺带点破） |
|---|---|---|---|
| **开卷考试** | RAG 整体 | 模型不再靠死记（参数），而是先翻资料再答；资料可随时更新 | 开卷考试的资料是"全给你"，RAG 是"只发给你几页"——发错页就答错（检索失败）；且考生可能不看资料硬答（幻觉仍会发生） |
| **图书馆索引卡 / 书脊上的分类号** | 分块 + Embedding + 向量索引 | 每张卡（块）有个"坐标"（向量），相近主题的卡挨在一起；找书先查卡不翻书 | 图书分类是人工、离散、单维的；embedding 是连续高维空间（几百到几千维），"相近"是语义而非题目 |
| **把书撕成卡片** | Chunking | 直观呈现"切太碎丢上下文、切太大找不准"的两难；父子块 = 卡片背面写着"来自第几章" | 真实分块不"撕"原书，原文仍保留；撕法（按页/段/语义）可以很聪明 |
| **两轮面试：海选 + 终面** | 两阶段检索（向量粗召回 + cross-encoder 重排） | 海选快但看简历（单向量）粗糙；终面慢但面对面（问题与文档同时读）更准，所以只面少数人 | 现实里"终面"也可能选错；且候选没进海选就永远没机会（召回决定上限） |
| **U 形注意力 / 三明治** | Lost in the Middle | 开头和结尾的资料最容易被记住，夹在中间的被忽略；动画可把最关键的一块放两端 | 这是统计趋势不是硬规则；新模型有改善（Databricks 数据：GPT-4o、Claude 3.5 Sonnet 退化很小） |
| （备选）**USB-C 接口** | MCP / 工具化检索 | 官方比喻：一个标准口接所有数据源 | 只解决"怎么连"，不解决"查什么、查得准不准" |

## 8. 术语中英对照表

| 中文 | English | 备注 |
|---|---|---|
| 检索增强生成 | Retrieval-Augmented Generation (RAG) | Lewis 等 2020 |
| 知识库 | Knowledge base | |
| 索引 / 建索引 | Indexing | 离线阶段 |
| 文档解析 / 版面分析 | Document parsing / Layout analysis | |
| 光学字符识别 | OCR (Optical Character Recognition) | |
| 分块 | Chunking | |
| 块重叠 | Chunk overlap | |
| 递归分割 | Recursive character splitting | |
| 语义分块 | Semantic chunking | |
| 父子块 / 小到大检索 | Parent-child chunks / Small-to-big retrieval | |
| 晚分块 | Late chunking | Jina 2024 |
| 上下文检索 | Contextual retrieval | Anthropic 2024 |
| 嵌入 / 向量表示 | Embedding | |
| 稠密检索 / 稀疏检索 | Dense retrieval / Sparse retrieval | 向量 / BM25 |
| 双编码器 / 交叉编码器 | Bi-encoder / Cross-encoder | 检索 / 重排 |
| 晚交互 | Late interaction | ColBERT |
| 近似最近邻 | Approximate Nearest Neighbor (ANN) | |
| 分层可导航小世界图 | HNSW (Hierarchical Navigable Small World) | |
| 倒排文件 / 乘积量化 | IVF (Inverted File) / PQ (Product Quantization) | |
| 向量数据库 | Vector database | Milvus, Qdrant, Weaviate, pgvector… |
| 混合检索 | Hybrid search | BM25 + 向量 |
| 倒数排名融合 | Reciprocal Rank Fusion (RRF) | k=60 |
| 元数据过滤 / 访问控制 | Metadata filtering / ACL (Access Control List) | |
| 多租户 | Multi-tenancy | |
| 查询改写 / 多查询 / 假设文档嵌入 | Query rewriting / Multi-query / HyDE | |
| 重排 | Rerank / Reranking | |
| 迷失在中间 | Lost in the Middle | Liu 等 2023 |
| 上下文腐化 | Context rot | Chroma 2025 |
| 引用 / 落地 | Citation / Grounding | |
| 幻觉 | Hallucination | |
| 忠实度 / 答案相关性 / 上下文精确率 / 上下文召回率 | Faithfulness / Answer relevancy / Context precision / Context recall | RAGAS |
| 图检索增强生成 | GraphRAG | 微软 2024 |
| 智能体式 RAG | Agentic RAG | |
| 上下文工程 | Context engineering | 2025 |
| 模型上下文协议 | Model Context Protocol (MCP) | Anthropic 2024 |

---
## 附：本次未能在线核实、需二次确认的点
1. HNSW 论文的期刊刊出信息（IEEE TPAMI 卷期年份）——arXiv 页未列，Semantic Scholar 接口限流。
2. RAPTOR 是否为 ICLR 2024 正式论文（arXiv 页未标注；OpenReview 有人机验证）。
3. Self-RAG：Semantic Scholar 标注 venue 为 ICLR（year 字段显示 2023，实际会议为 ICLR 2024），"oral"身份未核。
4. Tobi Lütke 与 Karpathy 关于 context engineering 的原推链接（X 需付费访问），目前引用 Simon Willison / Philipp Schmid 的转述。
5. Anthropic Citations 首发日期（记忆为 2025-01-23；claude.com 页面显示 2025-06-23，可能为迁移日期）。
6. Voyage AI 并入 MongoDB 的官方公告链接（2025-02，页面 404/超时）。
7. MTEB 多语言榜 2026-09 当前榜首模型。
8. OpenAI Deep Research 首发日（Wikipedia 显示 2025-02-03，美西时间为 02-02）。
9. Unstructured / LlamaParse / PaddleOCR / Marker 等解析工具仅作名称列举，未核实当前版本与能力。
