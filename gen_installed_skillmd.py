# -*- coding: utf-8 -*-
"""把用户级已安装技能 (~/.workbuddy/skills) 的 SKILL.md 原样收进仓库。

产出:
  installed-skills/<dir>/SKILL.md  (29 个, 原样复制)
  installed-skills/README.md       (索引 + 资源依赖说明)
  installed-skills/installed-skills.json (结构化备份)
"""
import os, shutil, re, json

BASE = r'C:\Users\topgo\.workbuddy\skills'
COLLECTION = r'C:\D\skill\skillhub-collection'
OUT = os.path.join(COLLECTION, 'installed-skills')

def parse_fm(txt):
    txt = txt.replace('\r\n', '\n').replace('\r', '\n')
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n', txt, re.S)
    if not m:
        hm = re.search(r'^#\s+(.+)$', txt, re.M)
        name = hm.group(1).strip() if hm else '(未命名)'
        desc = txt[hm.end():].strip() if hm else txt.strip()
        desc = re.sub(r'\s+', ' ', desc)[:120]
        return name, desc
    fm = m.group(1)
    lines = fm.split('\n')
    def get_field(key):
        for i, line in enumerate(lines):
            if re.match(rf'^{re.escape(key)}:\s', line) or line == key + ':':
                rest = line[len(key) + 1:].lstrip()
                if rest in ('|', '>'):
                    block = []
                    for j in range(i + 1, len(lines)):
                        nl = lines[j]
                        if nl.strip() == '':
                            continue
                        if nl[0] in ' \t':
                            block.append(nl.strip())
                        else:
                            break
                    return '\n'.join(block).strip()
                return rest.strip().strip('"').strip("'")
        return ''
    name = get_field('name') or ''
    if not name:
        hm = re.search(r'^#\s+(.+)$', txt[m.end():], re.M)
        name = hm.group(1).strip() if hm else ''
    if not name:
        name = '(未命名)'
    desc = get_field('description') or ''
    if not desc:
        body = txt[m.end():].strip()
        desc = body[:120]
    return name, desc

def main():
    # 清空旧的 installed-skills 目录 (只删本脚本产出的)
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT, exist_ok=True)

    dirs = sorted(d for d in os.listdir(BASE) if os.path.isdir(os.path.join(BASE, d)))
    rows = []
    json_data = []
    for d in dirs:
        p = os.path.join(BASE, d)
        skill = os.path.join(p, 'SKILL.md')
        if not os.path.exists(skill):
            continue
        # 复制 SKILL.md 原样
        dst = os.path.join(OUT, d)
        os.makedirs(dst, exist_ok=True)
        shutil.copy2(skill, os.path.join(dst, 'SKILL.md'))

        # 资源清单 (不含 SKILL.md 本体)
        files = []
        scripts = []
        refs = []
        binaries = 0
        for root, _, fs in os.walk(p):
            for f in fs:
                if f == 'SKILL.md':
                    continue
                rel = os.path.relpath(os.path.join(root, f), p).replace('\\', '/')
                files.append(rel)
                low = f.lower()
                if rel.startswith('scripts/') or low.endswith(('.py', '.js', '.sh', '.ts')):
                    scripts.append(rel)
                elif rel.startswith('references/') or low.endswith('.md'):
                    refs.append(rel)
                elif low.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bin', '.exe', '.node', '.zip')):
                    binaries += 1
        name, desc = parse_fm(open(skill, encoding='utf-8').read())
        rows.append((d, name, desc, len(files), len(scripts), len(refs), binaries))
        json_data.append({
            'dir': d,
            'name': name,
            'description': re.sub(r'\s+', ' ', desc)[:300],
            'source_path': f'~/.workbuddy/skills/{d}/',
            'files_total': len(files),
            'scripts': scripts,
            'references': refs,
            'binary_assets': binaries,
            'skill_md_size': os.path.getsize(skill),
        })

    # README
    lines = ['# 本机已安装技能快照（用户级）', '',
             f'> 来源：`~/.workbuddy/skills/`，共 **{len(rows)}** 个已安装技能。',
             '> 这些技能被 TOP 专家团的 9 大团队所引用（见 `teams/`）。',
             '> 本目录仅收录每个技能的 **SKILL.md 定义**（原样复制），不含其引用的脚本/二进制资源；',
             '> 如需完整可运行版本，请从本机对应目录取用（`source_path` 见 `installed-skills.json`）。', '',
             '| # | 目录名 | 名称 | 简介 | 资源文件 | 脚本 | 引用 | 二进制 |',
             '|---|--------|------|------|---------:|-----:|-----:|-------:|']
    for i, (d, name, desc, nf, ns, nr, nb) in enumerate(rows, 1):
        desc1 = re.sub(r'\s+', ' ', desc)[:58]
        lines.append(f'| {i} | `{d}` | {name} | {desc1} | {nf} | {ns} | {nr} | {nb} |')
    lines += ['', '## 目录', '']
    for d, name, desc, *_ in rows:
        desc1 = re.sub(r'\s+', ' ', desc)[:50]
        lines.append(f'- [`{d}/SKILL.md`]({d}/SKILL.md) — {name}：{desc1}')
    lines += ['', '---', '', '_由 `gen_installed_skillmd.py` 自动生成。_']

    with open(os.path.join(OUT, 'README.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    with open(os.path.join(OUT, 'installed-skills.json'), 'w', encoding='utf-8') as f:
        json.dump({'type': 'installed_skills', 'count': len(json_data), 'skills': json_data},
                  f, ensure_ascii=False, indent=2)

    print(f'OK: 生成 {len(rows)} 个 SKILL.md -> {OUT}')
    print(f'含脚本资源的技能: {sum(1 for r in rows if r[4] > 0)}')
    print(f'含二进制资源的技能: {sum(1 for r in rows if r[6] > 0)}')
    big = [(r[0], r[3]) for r in rows if r[3] > 50]
    print('资源较多的技能(>50文件):', big)

if __name__ == '__main__':
    main()
