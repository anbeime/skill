import sqlite3
db = r'C:\D\zhiyi\backend\data\antinet.db'
con = sqlite3.connect(db)
cur = con.cursor()
cur.execute("PRAGMA table_info(knowledge_cards)")
print('COLS:', [r[1] for r in cur.fetchall()])
cur.execute("SELECT * FROM knowledge_cards WHERE id=8271")
names = [d[0] for d in cur.description]
row = cur.fetchone()
print('--- 8271 ---')
for n, v in zip(names, row):
    print(n, '=', repr(v)[:200])
cur.execute("SELECT id, card_type, explore_status, substr(content,1,80) FROM knowledge_cards WHERE content LIKE ?", ('%srt-whiteboard%',))
print('existing srt cards:', cur.fetchall())
con.close()
