import sqlite3
db = r'C:\D\zhiyi\backend\data\antinet.db'
con = sqlite3.connect(db)
cur = con.cursor()
for cid in (8271, 8274, 8269, 8270):
    cur.execute("SELECT content,explore_status,card_type FROM knowledge_cards WHERE id=?", (cid,))
    row = cur.fetchone()
    if not row:
        print('NO CARD', cid)
        continue
    content, st, ct = row
    print('==== CARD', cid, '| status=', st, '| type=', ct, '====')
    print((content or '')[:500])
    print()
con.close()
