import { mkdir, readFile, writeFile } from 'node:fs/promises';

const catalogue = JSON.parse(await readFile(new URL('../data/projects.json', import.meta.url), 'utf8'));
const projects = [...catalogue.projects].sort((a, b) => b.starsAtCapture - a.starsAtCapture || a.name.localeCompare(b.name));
const categoryCounts = new Map();
for (const project of projects) categoryCounts.set(project.category, (categoryCounts.get(project.category) ?? 0) + 1);

const categories = [
  ['browser-computer-use', ['Browser & computer use', '浏览器与电脑操作', 'ブラウザ・PC 操作']],
  ['sdk-integrations', ['SDK integrations', 'SDK 与框架集成', 'SDK・フレームワーク']],
  ['routing-optimization', ['Routing & optimization', '路由与优化', 'ルーティング']],
  ['open-models', ['Open models', '开放模型', 'オープンモデル']],
  ['search-data', ['Search & data', '搜索与数据', '検索・データ']],
  ['safety-review', ['Safety & review', '安全与审查', '安全性・レビュー']],
  ['agent-workflows', ['Agent workflows', 'Agent 工作流', 'Agent ワークフロー']],
  ['interfaces', ['Interfaces & automation', '界面与自动化', 'UI・自動化']],
  ['developer-tools', ['Developer tools', '开发者工具', '開発者ツール']],
  ['domain-tools', ['Domain tools', '垂直工具', '業務特化ツール']],
];

const configs = [
  {
    file: 'README.md', index: 0, allHeading: `All ${projects.length} projects`, starWord: 'stars', lang: 'en', evidence: 'Source', back: '↑ Back to categories',
    strong: 'Find JEV projects for your use case — see what they do and which implementation to learn from.',
  },
  {
    file: 'README.zh-CN.md', index: 1, allHeading: `全部 ${projects.length} 个项目`, starWord: 'Star', lang: 'zh', evidence: '源码证据', back: '↑ 返回分类',
    strong: '从你的使用场景出发，找到值得参考的 JEV 项目，看懂它解决什么问题、哪部分值得借鉴。',
  },
  {
    file: 'README.ja.md', index: 2, allHeading: `全 ${projects.length} プロジェクト`, starWord: 'Star', lang: 'ja', evidence: '根拠', back: '↑ カテゴリへ戻る',
    strong: '用途に合う JEV プロジェクトを見つけ、何を解決し、どの実装が参考になるかを確認できます。',
  },
];


const { scenarios } = JSON.parse(await readFile(new URL('../data/scenarios.json', import.meta.url), 'utf8'));
const byId = new Map(projects.map(project => [project.id, project]));
const ui = {
  en: { quick: 'Find a project', scene: 'By use case', type: 'By project type', online: 'Search online', agent: 'Search with your agent', featured: 'Featured project gallery', all: 'All projects', stats: `${projects.length} projects · ${categoryCounts.size} project types · Updated ${catalogue.capturedAt}`, evidence: 'Source-reviewed; not independently run. Stars belong to the whole repository, not its JEV integration.', intro: 'Start with a task, browse a project type, or ask your agent to recommend useful implementations.', refs: 'Projects to learn from', learn: 'What to reference', flow: 'Where JEV fits', scope: 'These projects illustrate parts of this pattern, not a single ready-made application. Source review does not establish runtime behavior, performance, or BeatAPI compatibility.', freePrompt: 'Want to use JEV in your own app?', freeCta: 'Get started with the free JEV API on BeatAPI →', free: 'Try the free JEV API', freeBody: 'For your own integration, use `jev-1.13-free` with `POST /v1/systemone`: input and output cost $0, even on a zero balance. Use the default auto key group; before your first top-up, the account limit is one successful request per minute. Third-party projects may need configuration or code changes.', contribute: 'Contribute', data: 'Catalogue data', back: 'Back to discovery' },
  zh: { quick: '快速查找', scene: '按使用场景', type: '按项目类型', online: '在线搜索', agent: '用 Agent 搜索', featured: '精选项目 Gallery', all: '全部项目', stats: `${projects.length} 个项目 · ${categoryCounts.size} 种项目类型 · 更新于 ${catalogue.capturedAt}`, evidence: '已核对源码，未独立运行验证。Star 属于整个仓库，不代表其中 JEV 集成的热度。', intro: '带着需求找场景，按类型浏览项目，或让 Agent 帮你选择参考实现。', refs: '可以参考的项目', learn: '值得参考什么', flow: 'JEV 在哪一步', scope: '这些项目分别展示该模式的一部分，并非一套开箱即用的完整应用。源码核对不代表运行、性能或 BeatAPI 接入兼容性已经验证。', freePrompt: '想在自己的项目中接入 JEV？', freeCta: '在 BeatAPI 免费接入 JEV API →', free: '试用免费 JEV API', freeBody: '自行接入时，用 `jev-1.13-free` 调用 `POST /v1/systemone`：输入、输出均为 $0，零余额可用。Key 使用默认 auto 分组；首次充值前，账户每分钟可成功请求 1 次。第三方项目可能需要调整配置或代码。', contribute: '参与贡献', data: '目录数据', back: '返回检索入口' },
  ja: { quick: 'プロジェクトを探す', scene: '用途から', type: 'プロジェクトの種類から', online: 'サイトで検索', agent: 'Agent で検索', featured: '注目プロジェクト', all: '全プロジェクト', stats: `${projects.length} プロジェクト · ${categoryCounts.size} 種類 · 更新 ${catalogue.capturedAt}`, evidence: 'ソース確認済み、独立した実行検証は未実施。Star はリポジトリ全体の数であり、JEV 連携部分の評価ではありません。', intro: '用途や種類から探すか、Agent に参考実装を選んでもらえます。', refs: '参考プロジェクト', learn: '参考にする部分', flow: 'JEV が担当する段階', scope: '各プロジェクトはこのパターンの一部を示すもので、単一の完成アプリではありません。ソース確認は、動作・性能・BeatAPI 互換性の検証を意味しません。', freePrompt: '自分のアプリに JEV を組み込みたいですか？', freeCta: 'BeatAPI で無料の JEV API を使い始める →', free: '無料 JEV API を試す', freeBody: '自分で連携する場合は、`POST /v1/systemone` に `jev-1.13-free` を指定します。入力・出力ともに $0、残高 0 でも利用可能です。キーはデフォルトの auto グループを使います。初回チャージ前はアカウントごとに 1 分あたり成功 1 回まで。外部プロジェクトでは設定やコードの変更が必要な場合があります。', contribute: '貢献する', data: 'カタログデータ', back: '検索入口に戻る' },
};

for (const config of configs) {
  const { lang, index } = config;
  const t = ui[lang];
  const url = new URL(`../${config.file}`, import.meta.url);
  const previous = await readFile(url, 'utf8');
  // Keep the existing visual showcase; catalogue rows and discovery are generated.
  const galleryEnd = previous.indexOf('<!-- featured-gallery:end -->');
  const gallery = previous.slice(previous.indexOf('## '+t.featured), galleryEnd >= 0 ? galleryEnd : previous.indexOf('<a id="all-projects">')).trim();
  if (!gallery.startsWith('## ')) throw new Error(`Missing gallery in ${config.file}`);
  const site = `https://beatapi.io/${lang === 'en' ? '' : lang+'/'}awesome-jev`;
  const compact = n => n >= 1000 ? `${(n/1000).toFixed(1)}K` : String(n);
  const sections = categories.map(([key, labels]) => {
    const group = projects.filter(project => project.category === key);
    return `<a id="${key}"></a>\n\n### ${labels[index]} (${group.length})\n\n${group.map(project => `- **[${project.name}](${project.repoUrl})** · ${compact(project.starsAtCapture)} ${config.starWord} — ${project.summary[lang]} [${config.evidence}](${project.evidenceUrl})`).join('\n')}\n\n[↑ ${t.back}](#discovery)`;
  }).join('\n\n');
  const sceneLinks = scenarios.map(scene => `[${scene.title[lang]}](./scenarios/${scene.id}.${lang}.md)`);
  const categoryLinks = categories.map(([key,labels]) => `[${labels[index]} · ${categoryCounts.get(key) ?? 0}](#${key})`);
  const copy = {
    en: { intro: 'Choose what you want to build. Each guide points to relevant projects and the specific parts worth studying.', browse: 'Browse all 10 project types', agentIntro: 'Describe your task to your agent and get a few relevant repositories, why they fit, and what to reference. No API key needed.', ask: 'Find JEV projects for filtering news. Explain which part of each implementation I can reuse.', install: 'Installation & examples', proof: '50+ GitHub stars per repository · Source-reviewed', catalogue: 'Browse the full catalogue by project type. Use the scenario guides above when you have a specific task in mind.' },
    zh: { intro: '先选你想做的事。每个场景都整理了参考项目，以及具体值得借鉴的实现。', browse: '浏览全部 10 类项目', agentIntro: '把需求告诉 Agent，获得相关仓库、匹配理由和具体参考点。检索不需要 API Key。', ask: '我想用 JEV 筛选新闻，帮我找参考项目，并说明每个项目哪部分实现值得借鉴。', install: '安装方式与提问示例', proof: '每个仓库 50+ Star · 已核对源码', catalogue: '下面按项目类型浏览完整目录。如果已经有具体需求，可以先看上方的场景指南。' },
    ja: { intro: '作りたいものを選んでください。各ガイドで関連プロジェクトと参考になる実装箇所を紹介しています。', browse: '全 10 種類のプロジェクトを見る', agentIntro: 'やりたいことを Agent に伝えると、関連リポジトリ、選定理由、参考箇所を提案します。検索に API キーは不要です。', ask: 'JEV でニュースを絞り込みたい。参考プロジェクトと、各実装の参考になる部分を教えて。', install: 'インストール方法と質問例', proof: '各リポジトリ 50★以上 · ソース確認済み', catalogue: '種類別に全カタログを確認できます。具体的な目的がある場合は、上の用途別ガイドから始めてください。' },
  }[lang];
  const readme = `<p align="center"><img src="./assets/readme/cover.webp" alt="Awesome JEV — curated JEV projects by BeatAPI" width="100%" /></p>

<p align="center">
    <a href="https://linux.do" alt="LINUX DO">
        <img
            src="https://img.shields.io/badge/LINUX-DO-FFB003.svg?logo=data:image/svg%2bxml;base64,DQo8c3ZnIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIgd2lkdGg9IjEwMCIgaGVpZ2h0PSIxMDAiPjxwYXRoIGQ9Ik00Ni44Mi0uMDU1aDYuMjVxMjMuOTY5IDIuMDYyIDM4IDIxLjQyNmM1LjI1OCA3LjY3NiA4LjIxNSAxNi4xNTYgOC44NzUgMjUuNDV2Ni4yNXEtMi4wNjQgMjMuOTY4LTIxLjQzIDM4LTExLjUxMiA3Ljg4NS0yNS40NDUgOC44NzRoLTYuMjVxLTIzLjk3LTIuMDY0LTM4LjAwNC0yMS40M1EuOTcxIDY3LjA1Ni0uMDU0IDUzLjE4di02LjQ3M0MxLjM2MiAzMC43ODEgOC41MDMgMTguMTQ4IDIxLjM3IDguODE3IDI5LjA0NyAzLjU2MiAzNy41MjcuNjA0IDQ2LjgyMS0uMDU2IiBzdHlsZT0ic3Ryb2tlOm5vbmU7ZmlsbC1ydWxlOmV2ZW5vZGQ7ZmlsbDojZWNlY2VjO2ZpbGwtb3BhY2l0eToxIi8+PHBhdGggZD0iTTQ3LjI2NiAyLjk1N3EyMi41My0uNjUgMzcuNzc3IDE1LjczOGE0OS43IDQ5LjcgMCAwIDEgNi44NjcgMTAuMTU3cS00MS45NjQuMjIyLTgzLjkzIDAgOS43NS0xOC42MTYgMzAuMDI0LTI0LjM4N2E2MSA2MSAwIDAgMSA5LjI2Mi0xLjUwOCIgc3R5bGU9InN0cm9rZTpub25lO2ZpbGwtcnVsZTpldmVub2RkO2ZpbGw6IzE5MTkxOTtmaWxsLW9wYWNpdHk6MSIvPjxwYXRoIGQ9Ik03Ljk4IDcwLjkyNmMyNy45NzctLjAzNSA1NS45NTQgMCA4My45My4xMTNRODMuNDI2IDg3LjQ3MyA2Ni4xMyA5NC4wODZxLTE4LjgxIDYuNTQ0LTM2LjgzMi0xLjg5OC0xNC4yMDMtNy4wOS0yMS4zMTctMjEuMjYyIiBzdHlsZT0ic3Ryb2tlOm5vbmU7ZmlsbC1ydWxlOmV2ZW5vZGQ7ZmlsbDojZjlhZjAwO2ZpbGwtb3BhY2l0eToxIi8+PC9zdmc+" /></a>
</p>

<h1 align="center">Awesome JEV</h1>

<p align="center"><strong>${config.strong}</strong></p>

<p align="center">${t.freePrompt} <strong><a href="https://beatapi.io/jev-api">${t.freeCta}</a></strong></p>

<p align="center"><a href="#discovery">${t.quick}</a> · <a href="#featured">${t.featured}</a> · <a href="#agent-search">${t.agent}</a> · <a href="#all-projects">${t.all}</a> · <a href="${site}">${t.online}</a></p>

<p align="center"><a href="./README.md">English</a> · <a href="./README.zh-CN.md">简体中文</a> · <a href="./README.ja.md">日本語</a></p>

<p align="center">${t.stats}<br><sub>${copy.proof}</sub></p>

<a id="discovery"></a>

## ${t.quick}

${copy.intro}

${sceneLinks.slice(0,3).join(' · ')}<br>
${sceneLinks.slice(3).join(' · ')}

[${copy.browse}](#all-projects) · [${t.agent}](#agent-search)

<a id="featured"></a>

${gallery}
<!-- featured-gallery:end -->

<sub>${t.evidence}</sub>

<a id="agent-search"></a>

## ${t.agent}

${copy.agentIntro}

\`\`\`bash
npx skills add BeatAPI/awesome-jev
\`\`\`

> ${copy.ask}

[${copy.install}](./docs/agent-search.${lang}.md)

<a id="categories"></a>
<a id="all-projects"></a>

## ${config.allHeading}

${copy.catalogue}

${categoryLinks.slice(0,5).join(' · ')}<br>
${categoryLinks.slice(5).join(' · ')}

${sections}

## BeatAPI

**[${t.free}](https://beatapi.io/jev-api)** · [API Docs](https://docs.beatapi.io/decisions#free-calls)

${t.freeBody}

[${t.contribute}](./CONTRIBUTING.md) · [${t.data}](./data/projects.json) · [Scenario data](./data/scenarios.json) · [License & notices](./NOTICE.md)

<sub>Curated by [BeatAPI](https://beatapi.io). Independent community catalogue; not affiliated with TypeSafe.</sub>
`;
  await writeFile(url, readme);
  await mkdir(new URL('../scenarios/', import.meta.url), { recursive:true });
  for (const scene of scenarios) {
    const rows = scene.projects.map(ref => {
      const p = byId.get(ref.projectId);
      if (!p) throw new Error(`Unknown scenario project ${ref.projectId}`);
      return `### [${p.name}](${p.repoUrl})\n\n${p.summary[lang]}\n\n**${t.learn}:** ${ref.reference[lang]}\n\n[${config.evidence}](${p.evidenceUrl})`;
    }).join('\n\n');
    await writeFile(new URL(`../scenarios/${scene.id}.${lang}.md`, import.meta.url), `<!-- Generated from data/scenarios.json + data/projects.json. -->\n[← ${t.back}](../${config.file}#discovery)\n\n# ${scene.title[lang]}\n\n${scene.description[lang]}\n\n**${t.flow}**\n\n${scene.flow[lang]}\n\n## ${t.refs}\n\n${rows}\n\n${t.scope}\n\n[${t.free}](https://docs.beatapi.io/decisions#free-calls) · [${t.agent}](../docs/agent-search.${lang}.md)\n`);
  }
}
console.log(`Synced ${projects.length} projects, ${scenarios.length} scenarios and ${configs.length} languages.`);
