#!/usr/bin/env python3
"""
多源技能仓库同步脚本
从 OpenAI Skills 和 VoltAgent Awesome Agent Skills 提取技能仓库链接
"""

import json
import re
import os
from datetime import datetime
from urllib.parse import urlparse
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
    }
}

# 创建 SSL 上下文（处理证书问题）
def create_ssl_context():
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context

def fetch_content(url):
    """获取远程内容"""
    try:
        context = create_ssl_context()
        with urllib.request.urlopen(url, context=context, timeout=30) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        print(f"❌ 获取内容失败 {url}: {e}")
        return None

def extract_github_repos(text):
    """从文本中提取 GitHub 仓库链接"""
    # 匹配 github.com/owner/repo 格式
    pattern = r'github\.com/([a-zA-Z0-9_-]+)/([a-zA-Z0-9_-]+)'
    matches = re.findall(pattern, text)
    
    repos = set()
    for owner, repo in matches:
        # 过滤掉常见非仓库路径
        if repo.lower() in ['issues', 'pulls', 'discussions', 'actions', 'projects', 'wiki', 'pulse', 'graphs', 'settings']:
            continue
        repos.add((owner, repo))
    
    return repos

def extract_openai_skills(text):
    """提取 OpenAI Skills 目录结构中的技能"""
    repos = set()
    
    # 查找 skills/.system/, skills/.curated/, skills/.experimental/ 下的目录
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

def parse_voltagent_readme(text):
    """解析 VoltAgent Awesome List，提取所有技能仓库"""
    repos = set()
    
    # 提取所有 GitHub 链接
    github_repos = extract_github_repos(text)
    repos.update(github_repos)
    
    # 排除自身仓库
    repos.discard(('VoltAgent', 'awesome-agent-skills'))
    
    return repos

def load_existing_sources():
    """加载已存在的技能源文件"""
    if os.path.exists('SKILL_SOURCES.json'):
        try:
            with open('SKILL_SOURCES.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ 读取现有文件失败: {e}")
    return {"sources": {}, "last_updated": None, "total_count": 0}

def save_sources(sources_data):
    """保存技能源文件"""
    with open('SKILL_SOURCES.json', 'w', encoding='utf-8') as f:
        json.dump(sources_data, f, ensure_ascii=False, indent=2)
    print(f"✅ 已保存 SKILL_SOURCES.json，共 {sources_data['total_count']} 个技能源")

def generate_readme(sources_data):
    """生成 README.md 文件"""
    content = f"""# Skill Sources - 技能仓库聚合

自动从多个上游源同步的技能仓库列表。

## 📊 统计信息

- **最后更新**: {sources_data['last_updated']}
- **技能源总数**: {sources_data['total_count']}

## 🔗 上游源

- [OpenAI Skills](https://github.com/openai/skills)
- [VoltAgent Awesome Agent Skills](https://github.com/VoltAgent/awesome-agent-skills)

## 📦 技能仓库列表

"""
  
    for source_key, source_info in UPSTREAM_SOURCES.items():
        source_name = source_info['name']
        content += f"### {source_name}\n\n"
        content += "| 仓库 | 来源 |\n"
        content += "|------|------|\n"
      
        count = 0
        for repo_id, repo_data in sources_data['sources'].items():
            if repo_data.get('upstream_source') == source_key:
                # 处理包含多个斜杠的 repo_id
                parts = repo_id.split('/')
                if len(parts) == 2:
                    owner, repo = parts
                else:
                    owner = parts[0]
                    repo = '/'.join(parts[1:])
              
                repo_url = f"https://github.com/{owner}/{repo}"
                content += f"| [{repo}]({repo_url}) | {source_name} |\n"
                count += 1
      
        if count == 0:
            content += "| - | 暂无数据 |\n"
        content += "\n"
  
    content += """## 🔄 自动同步

本仓库每天自动从上游源同步最新的技能仓库信息。

- **定时触发**: 每天 02\:00 UTC
- **手动触发**: 通过 GitHub Actions 页面

---

*此文件由自动化脚本生成*
"""
  
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ 已更新 README.md")

def main():
    print("🚀 开始同步技能仓库...")
    print(f"⏰ 当前时间: {datetime.now().isoformat()}")
    
    # 加载现有数据
    sources_data = load_existing_sources()
    
    # 处理每个上游源
    all_repos = {}
    
    for source_key, source_info in UPSTREAM_SOURCES.items():
        print(f"\n📥 正在处理: {source_info['name']}")
        
        content = fetch_content(source_info['url'])
        if not content:
            continue
        
        if source_key == 'openai_skills':
            repos = extract_openai_skills(content)
        else:
            repos = parse_voltagent_readme(content)
        
        print(f"   发现 {len(repos)} 个仓库")
        
        for owner, repo in repos:
            repo_id = f"{owner}/{repo}"
            all_repos[repo_id] = {
                "upstream_source": source_key,
                "discovered_at": datetime.now().isoformat(),
                "description": ""
            }
    
    # 合并数据（保留已存在仓库的发现时间）
    existing_sources = sources_data.get('sources', {})
    for repo_id, repo_data in all_repos.items():
        if repo_id in existing_sources:
            # 保留原始发现时间
            repo_data['discovered_at'] = existing_sources[repo_id].get('discovered_at', repo_data['discovered_at'])
    
    # 更新数据
    sources_data['sources'] = all_repos
    sources_data['last_updated'] = datetime.now().isoformat()
    sources_data['total_count'] = len(all_repos)
    
    # 保存文件
    save_sources(sources_data)
    generate_readme(sources_data)
    
    print(f"\n✨ 同步完成！共发现 {len(all_repos)} 个技能仓库")

if __name__ == '__main__':
    main()
