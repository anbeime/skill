import sqlite3, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
DB = r'C:/D/zhiyi/backend/data/antinet.db'
conn = sqlite3.connect(DB); cur = conn.cursor()
# total cards in topic 19
cur.execute("SELECT COUNT(*) FROM knowledge_cards WHERE topic_id=19")
print('topic19 total cards:', cur.fetchone()[0])
cur.execute("SELECT COUNT(*) FROM knowledge_cards WHERE project_id=19")
print('project19 total cards:', cur.fetchone()[0])
# search for skill-related duplicates
kws = ['mattpocock','diagram-design','diagram design','archify','skillhub','voltagent','inkos','awesome-design','email-concierge','hospital_agent','kb-to-mpt','ip-as-logo','img2threejs','photo-abstract','convert-documents-to-markdown','cathrynlavery']
q = " OR ".join(["title LIKE ?" for _ in kws])
params = [f'%{k}%' for k in kws]
cur.execute(f"SELECT id, title, topic_id, project_id FROM knowledge_cards WHERE ({q})", params)
rows = cur.fetchall()
print(f'\nFound {len(rows)} potentially-duplicate skill-related cards:')
for r in rows:
    print('  ', r)
conn.close()
