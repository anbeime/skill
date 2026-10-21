import sqlite3
db = r'C:\D\zhiyi\backend\data\antinet.db'
con = sqlite3.connect(db)
cur = con.cursor()
cur.execute("""
INSERT INTO knowledge_cards
(title, content, card_type, category, project_id, topic_id, type, tags, core_tags, explore_status, source_url, tier, memory_type)
VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
""", (
 '[A-D25-18] geeklee/srt-whiteboard-animation 技能落库',
 '事实：srt-whiteboard-animation(geeklee/srt-whiteboard-animation, 3.8k★, MIT) 于 2026-10-21 克隆入 skillhub-collection/skills/srt-whiteboard-animation/，已删除 .git；含 SKILL.md/scripts/assets/examples/agents，preview.html 预览台免代码拖拽调整时序与分区。已登记 SKILL_SOURCES.json(upstream_source=manual_video)、README 中英文「数字人与视频配音」段（计数 5→6）、前端 local_skills.json（数字人与视频配音 + 收录开源技能，total_skills 68→69）。功能：输入 .srt 字幕→输出笔迹跟随旁白的白板手绘动画 MP4。',
 'green', 'skillhub 收编', 78, 78, 'blue',
 '["d25", "srt-whiteboard-animation", "skillhub", "fact"]',
 '["d25", "srt-whiteboard-animation", "skillhub"]',
 'done',
 'https://github.com/geeklee/srt-whiteboard-animation',
 'L1', 'light'
))
print('inserted card id =', cur.lastrowid)
con.commit()
con.close()
