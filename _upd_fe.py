import json

# ---- local_skills.json ----
fe = r'C:\D\skill\skillhub-collection\public\data\local_skills.json'
d = json.load(open(fe, encoding='utf-8'))

cats = d['categories']
skill = 'srt-whiteboard-animation'

for cat in ('数字人与视频配音', '收录开源技能'):
    c = cats[cat]
    if skill not in c['skills']:
        c['skills'].append(skill)
        c['count'] = len(c['skills'])

d['metadata']['total_skills'] = d['metadata'].get('total_skills', 0) + 1
json.dump(d, open(fe, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('local_skills.json updated; total_skills =', d['metadata']['total_skills'])
print('数字人与视频配音:', cats['数字人与视频配音']['count'], '| 收录开源技能:', cats['收录开源技能']['count'])

# ---- SKILL_SOURCES.json ----
ss = r'C:\D\skill\skillhub-collection\SKILL_SOURCES.json'
s = json.load(open(ss, encoding='utf-8'))
src = s['sources']
key = 'geeklee/srt-whiteboard-animation'
if key not in src:
    src[key] = {
        'upstream_source': 'manual_video',
        'discovered_at': '2026-10-21T00:00:00.000000',
        'description': '输入 .srt 字幕，输出笔迹跟随旁白的白板手绘动画 MP4（分镜→线稿→标注→分区→逐幕渲染→合成，预览台免代码拖拽调整）'
    }
    s['total_count'] = len(src)
    json.dump(s, open(ss, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print('SKILL_SOURCES.json added', key, '| total_count =', s['total_count'])
else:
    print('SKILL_SOURCES.json already has', key)
