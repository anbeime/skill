import sqlite3, json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
DB = r'C:/D/zhiyi/backend/data/antinet.db'
try:
    conn = sqlite3.connect(DB)
except Exception as e:
    print('DB open error:', e); sys.exit(1)
cur = conn.cursor()
# tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur.fetchall()]
print('TABLES:', tables)
# research_projects / topics
for t in ('research_projects','topics','projects'):
    if t in tables:
        try:
            cur.execute(f"SELECT * FROM {t} LIMIT 50")
            cols = [d[0] for d in cur.description]
            print(f'\n=== {t} cols={cols} ===')
            for row in cur.fetchall():
                print(dict(zip(cols, row)))
        except Exception as e:
            print(t, 'err', e)
# knowledge_cards schema + topic 19 cards
if 'knowledge_cards' in tables:
    cur.execute("PRAGMA table_info(knowledge_cards)")
    print('\nknowledge_cards cols:', [c[1] for c in cur.fetchall()])
    # count per project_id / topic_id
    for col in ('project_id','topic_id'):
        try:
            cur.execute(f"SELECT {col}, COUNT(*) FROM knowledge_cards GROUP BY {col}")
            print(f'\ncount by {col}:', cur.fetchall())
        except Exception as e:
            print(col,'err',e)
    # sample cards in topic 19
    for col in ('project_id','topic_id'):
        try:
            cur.execute(f"SELECT id, title, {col} FROM knowledge_cards WHERE {col}=19 LIMIT 30")
            rows = cur.fetchall()
            print(f'\ncards where {col}=19 (sample {len(rows)}):')
            for r in rows:
                print('  ', r)
        except Exception as e:
            print(col,'err',e)
conn.close()
