# -*- coding: utf-8 -*-
"""纳瓦尔宝典精读 → 知易知识库 建卡脚本。
读 faster-whisper 转写出的 txt(格式 [HH:MM:SS.mmm] 文本)，
切片成通政司蓝卡(每段=视频一个事实/观点,带时间戳溯源)，
再补 1 绿卡(解读)+1 红卡(行动:用 kb_to_mpt 批量出片)。
幂等：专题名已存在则复用，不重复建卡。
"""
import sqlite3, json, time, re, sys

DB = 'backend/data/antinet.db'
VIDEO_URL = "https://www.bilibili.com/video/BV1zgckzzEZT/"
PROJECT_NAME = "纳瓦尔宝典精读 · 知识短视频素材库"
PROJECT_DESC = ("《纳瓦尔宝典》书摘短视频素材库。来源：B站视频《普通人如何实现财富自由？赚钱必读书籍<纳瓦尔宝典>精读》(BV1zgckzzEZT)。"
                "通政司蓝卡=视频逐段事实/观点(本地 faster-whisper small 转写,带时间戳溯源)，"
                "丞相府红卡=用 kb_to_mpt.py 把本库批量生成书摘短视频(复用 E 盘 MoneyPrinterTurbo)。")

def parse_txt(path):
    rows = []
    pat = re.compile(r"\[(\d{2}:\d{2}:\d{2}\.\d{3})\]\s*(.*)")
    ts, buf = None, []
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            m = pat.match(line)
            if m:
                if ts is not None and buf:
                    rows.append((ts, " ".join(buf)))
                ts = m.group(1)
                buf = [m.group(2)]
            else:
                buf.append(line)
    if ts is not None and buf:
        rows.append((ts, " ".join(buf)))
    return rows

def chunk(rows, max_chars=180):
    """把相邻短句聚合成约 180 字的段落，作为一张蓝卡。"""
    chunks, cur, cur_ts = [], [], None
    for ts, text in rows:
        if cur_ts is None:
            cur_ts = ts
        cur.append(text)
        if sum(len(x) for x in cur) >= max_chars:
            chunks.append((cur_ts, " ".join(cur)))
            cur, cur_ts = [], None
    if cur:
        chunks.append((cur_ts, " ".join(cur)))
    return chunks

def main():
    if len(sys.argv) < 2:
        print("用法: python build_naval_cards.py <transcript.txt>"); sys.exit(1)
    txt_path = sys.argv[1]
    rows = parse_txt(txt_path)
    print(f"转写行数: {len(rows)}")
    chunks = chunk(rows)
    print(f"切片段数: {len(chunks)}")

    c = sqlite3.connect(DB); cur = c.cursor()
    cur.execute('PRAGMA foreign_keys=OFF')
    now = int(time.time())

    # 复用专题
    cur.execute("SELECT id FROM research_projects WHERE name=?", (PROJECT_NAME,))
    r = cur.fetchone()
    if r:
        PID = r[0]; print(f"复用专题 id={PID}")
    else:
        cur.execute("INSERT INTO research_projects (name,description,color,icon,status,created_at,updated_at) VALUES (?,?,?,?,?,?,?)",
                    (PROJECT_NAME, PROJECT_DESC, "#7E57C2", "📚", "active", now, now))
        PID = cur.lastrowid; print(f"新建专题 id={PID}")

    def add_card(card_type, title, content, tags, cite_ids=None, ref_type='cite'):
        cur.execute("""INSERT INTO knowledge_cards
            (title,content,card_type,type,category,created_at,updated_at,project_id,tags,source_url)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (title, content, card_type, card_type, '纳瓦尔宝典', now, now, PID,
             json.dumps(tags, ensure_ascii=False), VIDEO_URL))
        cid = cur.lastrowid
        if cite_ids:
            for tgt in cite_ids:
                cur.execute("INSERT INTO card_backlinks (source_card_id,target_card_id,link_text,link_type,weight,created_at) VALUES (?,?,?,?,?,?)",
                            (cid, tgt, '溯源', ref_type, 1.0, now))
        print(f"  {card_type} #{cid} {title[:30]}")
        return cid

    # 蓝卡
    blue_ids = []
    for i, (ts, text) in enumerate(chunks):
        title = text[:18] + ("…" if len(text) > 18 else "")
        content = text + f"\n\n来源：B站《纳瓦尔宝典精读》(BV1zgckzzEZT) 视频时间点 [{ts}]"
        cid = add_card('blue', title, content, ['纳瓦尔宝典','书摘','财富','视频转写'], cite_ids=None)
        blue_ids.append(cid)

    # 同源 sibling 链(稀疏,每卡连前后各1,≤2 出链)
    for i, cid in enumerate(blue_ids):
        for nb in (i-1, i+1):
            if 0 <= nb < len(blue_ids):
                cur.execute("INSERT INTO card_backlinks (source_card_id,target_card_id,link_text,link_type,weight,created_at) VALUES (?,?,?,?,?,?)",
                            (cid, blue_ids[nb], '同源段落', 'sibling', 0.6, now))

    # 绿卡(解读核心方法论,引用前若干蓝卡)
    g1 = add_card('green',
        "纳瓦尔宝典核心方法论：财富=专长×杠杆×复利",
        "《纳瓦尔宝典》把'赚钱'拆成可复制的底层逻辑，视频逐段蓝卡共同支撑三条主线：\n"
        "① 财富来自'以专长(你天生擅长且愿长期投入的事)为单位出售'而非出卖时间——找到'不可替代、不可培训'的产品化能力。\n"
        "② 杠杆分三种：人力杠杆(管人,最难)、资本杠杆(用钱,需信用)、零边际成本杠杆(代码/媒体/版权,普通人最可用)——写代码、做内容、出书是当代最佳杠杆。\n"
        "③ 复利：信任、声誉、关系、知识都按复利增长，耐心持有比频繁切换重要。\n"
        "幸福=活在当下+健康+人际关系+自主(不被外界目标绑架)。财富与幸福的交集=用专长做自己喜欢且被需要的事，并通过杠杆放大。",
        ['纳瓦尔宝典','方法论','财富','杠杆','复利'], cite_ids=blue_ids[:6])

    # 红卡(行动:批量出片)
    r1 = add_card('red',
        "用 kb_to_mpt.py 把本专题批量生成书摘短视频",
        "负责人:TOPGO 期限:2026-09-10 验收:在本机启动 MoneyPrinterTurbo(webui.bat)后，运行 "
        "python kb_to_mpt.py --project-id "+str(PID)+" --mpt-url http://127.0.0.1:8080 ，"
        "把本专题蓝卡自动组装成 video_script 推给 MPT 批量生成《纳瓦尔宝典》系列短视频(口播+字幕+素材)，"
        "并归档成片到 material/videos/。可循环复用到其他书摘专题，实现'书→知识库→视频矩阵'流水线。",
        ['落地','书摘视频','kb_to_mpt','MPT'], cite_ids=[g1])

    # GTD
    cur.execute("""INSERT INTO gtd_tasks (title,description,priority,due_date,category,created_at,updated_at,project_id,source_type,source_card_id,kanban_status)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        ("用 kb_to_mpt 批量生成纳瓦尔宝典短视频", f"对应红卡 #{r1}", 'high', '2026-09-10',
         'projects', now, now, PID, 'card', r1, 'todo'))
    print(f"  gtd #{cur.lastrowid} <- 红卡#{r1}")

    cur.execute("COMMIT")
    print(f"DONE 专题={PID} 蓝卡={len(blue_ids)} 绿卡=1 红卡=1")

if __name__ == "__main__":
    main()
