#!/usr/bin/env python3
"""
多源技能仓库同步脚本
从多个上游源提取技能仓库链接并汇总
"""

import json
import re
import os
from datetime import datetime
import urllib.request
import ssl

# 上游源配置
UPSTREAM_SOURCES = {
    "openai_skills": {
        "name": "OpenAI Skills",
        "url": "https://raw.githubusercontent.com/openai/skills/main/README.md",
        "type": "directory_structure"
    },
    "voltagent_awesome": {
        "name": "VoltAgent Awesome Agent Skills",
        "url": "https://raw.githubusercontent.com/VoltAgent/awesome-agent-skills/main/README.md",
        "type": "awesome_list"
    },
    "awesome_dsh_plugin": {
        "name": "Awesome DSH Plugin",
        "url": "https://raw.githubusercontent.com/awesome-dsh-plugin/awesome-dsh-plugin/main/README.md",
        "type": "awesome_list"
    },
    "mattpocock_skills": {
        "name": "Matt Pocock Skills",
        "url": "https://raw.githubusercontent.com/mattpocock/skills/main/README.md",
        "type": "awesome_list"
    }
}

def create_ssl_context():
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context

def fetch_content(url):
    try:
        context = create_ssl_context()
        with urllib.request.urlopen(url, context=context, timeout=30) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        print(f"❌ 获取内容失败 {url}: {e}")
        return None

def extract_github_repos(text):
    pattern = r'github\.com/([a-zA-Z0-9_-]+)/([a-zA-Z0-9_-]+)'
    matches = re.findall(pattern, text)
    repos = set()
    skip = {'issues', 'pulls', 'discussions', 'actions', 'projects',
            'wiki', 'pulse', 'graphs', 'settings', 'sponsors',
            'codespaces', 'security', 'network', 'stargazers', 'watchers',
            'forks', 'branches', 'tags', 'releases', 'packages',
            'milestones', 'labels', 'compare', 'tree', 'blob', 'raw',
            'commits', 'blame', 'edit', 'delete'}
    for owner, repo in matches:
        if repo.lower() in skip:
            continue
        if owner.lower() in {'www', 'apps', 'api', 'docs', 'support',
                              'enterprise', 'features', 'pricing',
                              'customer-stories', 'readme'}:
            continue
        repos.add((owner, repo))
    return repos

def extract_openai_skills(text):
    repos = set()
    skill_patterns = [
        r'skills/\.system/([a-zA-Z0-9_-]+)',
        r'skills/\.curated/([a-zA-Z0-9_-]+)',
        r'skills/\.experimental/([a-zA-Z0-9_-]+)'
    ]
    for pattern in skill_patterns:
        matches = re.findall(pattern, text)
        for skill_name in matches:
            repos.add(('openai', f'skills/{skill_name}'))
    return repos

def parse_awesome_list(text, self_repo=None):
    repos = extract_github_repos(text)
    if self_repo:
        owner, name = self_repo
        repos.discard((owner, name))
    return repos

def load_existing_sources():
    if os.path.exists('SKILL_SOURCES.json'):
        try:
            with open('SKILL_SOURCES.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ 读取现有文件失败: {e}")
    return {"sources": {}, "last_updated": None, "total_count": 0}

def save_sources(sources_data):
    with open('SKILL_SOURCES.json', 'w', encoding='utf-8') as f:
        json.dump(sources_data, f, ensure_ascii=False, indent=2)
    print(f"✅ 已保存 SKILL_SOURCES.json，共 {sources_data['total_count']} 个技能源")

def update_readme(sources_data):
    MARKER_START = "<!-- AUTO-SYNC-SKILLS-START -->"
    MARKER_END = "<!-- AUTO-SYNC-SKILLS-END -->"

    skills_content = f"""{MARKER_START}

## 📦 社区技能仓库聚合

> 此部分由自动化脚本每日从上游源同步更新

**最后更新**: {sources_data['last_updated']} | **技能源总数**: {sources_data['total_count']}

### 数据来源

- [OpenAI Skills](https://github.com/openai/skills)
- [VoltAgent Awesome Agent Skills](https://github.com/VoltAgent/awesome-agent-skills)
- [Awesome DSH Plugin](https://github.com/awesome-dsh-plugin/awesome-dsh-plugin)
- [Matt Pocock Skills](https://github.com/mattpocock/skills)

### 技能仓库列表

"""

    for source_key, source_info in UPSTREAM_SOURCES.items():
        source_name = source_info['name']
        skills_content += f"#### {source_name}\n\n"

        count = 0
        for repo_id, repo_data in sources_data['sources'].items():
            if repo_data.get('upstream_source') == source_key:
                parts = repo_id.split('/')
                if len(parts) == 2:
                    owner, repo = parts
                else:
                    owner = parts[0]
                    repo = '/'.join(parts[1:])

                repo_url = f"https://github.com/{owner}/{repo}"
                skills_content += f"- [{repo}]({repo_url})\n"
                count += 1

        if count == 0:
            skills_content += "- 暂无数据\n"

        skills_content += "\n"

    skills_content += f"{MARKER_END}"

    existing_content = ""
    if os.path.exists('README.md'):
        with open('README.md', 'r', encoding='utf-8') as f:
            existing_content = f.read()

    if MARKER_START in existing_content and MARKER_END in existing_content:
        new_content = re.sub(
            f"{MARKER_START}.*?{MARKER_END}",
            skills_content.replace('\\', '\\\\'),
            existing_content,
            flags=re.DOTALL
        )
    else:
        new_content = existing_content.rstrip() + "\n\n" + skills_content

    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("✅ 已在 README.md 底部追加技能列表")

# 各上游对应的自身仓库（用于 awesome list 排除自身）
SELF_REPOS = {
    "voltagent_awesome": ("VoltAgent", "awesome-agent-skills"),
    "awesome_dsh_plugin": ("awesome-dsh-plugin", "awesome-dsh-plugin"),
    "mattpocock_skills": ("mattpocock", "skills"),
}

def main():
    print("🚀 开始同步技能仓库...")
    print(f"⏰ 当前时间: {datetime.now().isoformat()}")

    sources_data = load_existing_sources()
    all_repos = {}

    for source_key, source_info in UPSTREAM_SOURCES.items():
        print(f"\n📥 正在处理: {source_info['name']}")

        content = fetch_content(source_info['url'])
        if not content:
            continue

        if source_info['type'] == 'directory_structure':
            repos = extract_openai_skills(content)
        else:
            self_repo = SELF_REPOS.get(source_key)
            repos = parse_awesome_list(content, self_repo=self_repo)

        print(f"   发现 {len(repos)} 个仓库")

        for owner, repo in repos:
            repo_id = f"{owner}/{repo}"
            all_repos[repo_id] = {
                "upstream_source": source_key,
                "discovered_at": datetime.now().isoformat(),
                "description": ""
            }

    existing_sources = sources_data.get('sources', {})
    for repo_id, repo_data in all_repos.items():
        if repo_id in existing_sources:
            repo_data['discovered_at'] = existing_sources[repo_id].get('discovered_at', repo_data['discovered_at'])

    sources_data['sources'] = all_repos
    sources_data['last_updated'] = datetime.now().isoformat()
    sources_data['total_count'] = len(all_repos)

    save_sources(sources_data)
    update_readme(sources_data)

    print(f"\n✨ 同步完成！共发现 {len(all_repos)} 个技能仓库")

if __name__ == '__main__':
    main()
