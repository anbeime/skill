import sqlite3, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
DB = r'C:/D/zhiyi/backend/data/antinet.db'
conn = sqlite3.connect(DB); cur = conn.cursor()
# distinct explore_status values
cur.execute("SELECT explore_status, COUNT(*) FROM knowledge_cards GROUP BY explore_status")
print('explore_status values:', cur.fetchall())
ids = [7476,7657,7668,7721,7725,7726,7727,7728,7729,7730,7771,7828,7905,7911,7925,7931,7938,8269,8270,8271,8273,8274]
qmarks = ','.join('?'*len(ids))
cur.execute(f"SELECT id, title, topic_id, project_id, explore_status, card_type FROM knowledge_cards WHERE id IN ({qmarks})", ids)
print('\n=== existing skill cards status ===')
for r in cur.fetchall():
    print(' ', r)
# content snippets for 8269-8274 + 7905 + 7911
for cid in [8269,8270,8271,8273,8274,7905,7911]:
    cur.execute("SELECT title, explore_status, content FROM knowledge_cards WHERE id=?", (cid,))
    t,st,ct = cur.fetchone()
    print(f'\n--- #{cid} [{st}] {t} ---')
    print((ct or '')[:600])
conn.close()
