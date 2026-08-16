"""太史阁 (TaiShiGeAgent)：长期记忆、检索、知识回流，全链路 provenance 留痕。

writeback：把所有卡片 + 扫描报告沉淀为本地 Markdown/JSON 引擎（不引入外部知识库）。
recall：极简向量检索（jieba 缺失时退化为 CJK 二元切分 + 拉丁词），供其他 AI 协同读取。
"""
from __future__ import annotations
import os
import sys
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from common.card_model import Card
from common.logger import ProvenanceLogger
from common.zhijia_client import ZhijiaClient


def _tokenize(text: str) -> list[str]:
    try:
        import jieba  # type: ignore
        return [t for t in jieba.lcut(text) if len(t) > 1]
    except Exception:
        # 退化：CJK 二元切分 + 拉丁词
        toks: list[str] = []
        buf = ""
        for ch in text:
            if "一" <= ch <= "鿿":
                if buf:
                    toks.append(buf)
                    buf = ""
                toks.append(ch)
            elif ch.isalnum():
                buf += ch
            else:
                if buf:
                    toks.append(buf)
                    buf = ""
        return toks


class TaiShiGeAgent:
    def __init__(self, cfg: dict, base_dir: str, logger: ProvenanceLogger, zhijia: ZhijiaClient | None = None):
        self.cfg = cfg
        self.base_dir = base_dir
        self.logger = logger
        self.zhijia = zhijia
        self.out_dir = os.path.join(base_dir, "examples", "snse_survey")

    def writeback(self, cards: list[Card], scan_report: dict) -> None:
        index = [c.to_dict() for c in cards]
        with open(os.path.join(self.out_dir, "cards_index.json"), "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
        # 按类型落盘四色卡片
        by_type = {"blue": [], "green": [], "yellow": [], "red": []}
        for c in cards:
            by_type.setdefault(c.card_type, []).append(c.to_dict())
        for t, lst in by_type.items():
            with open(os.path.join(self.out_dir, f"{t}_cards.json"), "w", encoding="utf-8") as f:
                json.dump(lst, f, ensure_ascii=False, indent=2)
        with open(os.path.join(self.out_dir, "scan_report.json"), "w", encoding="utf-8") as f:
            json.dump(scan_report, f, ensure_ascii=False, indent=2)
        # provenance wiki 页（极简 Markdown）
        os.makedirs(os.path.join(self.out_dir, "provenance"), exist_ok=True)
        with open(os.path.join(self.out_dir, "provenance", "knowledge.md"), "w", encoding="utf-8") as f:
            f.write(f"# SnSe 空位工程导热 — 八官署 provenance\n\n")
            f.write(f"- 论文总数: {scan_report.get('oa_papers_available', 'n/a')}\n")
            f.write(f"- 解析率: {scan_report.get('parsed_oa_ratio', 'n/a')}\n")
            f.write(f"- 防假全文(无local_cache冒充): {scan_report.get('no_local_cache_as_production')}\n\n")
            for c in cards:
                f.write(f"- [{c.card_type}] {c.title}: {c.content[:80]}\n")
        self.logger.log("太史阁", "知识回流", f"沉淀 {len(cards)} 张卡片 + provenance 页")

        # P0-b：把生成的四色卡片真实回流到知易知识库（与密卷房灌源文对称）
        # AGENTS.md 第4节：产出必须回流，下一轮 recall 才能命中本轮结论
        if self.zhijia is not None:
            n_ok = 0
            for c in cards:
                try:
                    r = self.zhijia.import_text(c.content)
                except Exception:
                    r = None
                if isinstance(r, dict) and r.get("success"):
                    n_ok += 1
            if n_ok:
                self.logger.log("太史阁", "知识回流(知易库)", f"真实灌库 {n_ok}/{len(cards)} 张卡片")
            else:
                self.logger.log("太史阁", "知识回流(知易库)", "灌库未生效(平台不可达或返回失败)", status="warn")

    def recall(self, query: str, top_k: int = 5) -> list[str]:
        # 优先：真实平台检索（向量/关键词，知易知识库）。
        # 不预检 health——直接 try search，避免 health 偶发失败导致误回退；
        # 同时把长 query 拆词兜底，确保单关键词也能命中（知易 search 对长精确串不敏感）。
        if self.zhijia is not None:
            real_hits: list[dict] = []
            try:
                seen: set = set()
                for q in [query] + _tokenize(query)[:6]:
                    if not q or q in seen:
                        continue
                    seen.add(q)
                    h = self.zhijia.search(q, limit=top_k)  # type: ignore[union-attr]
                    if h:
                        real_hits.extend(h)
                    if len(real_hits) >= top_k:
                        break
            except Exception:
                real_hits = []
            if real_hits:
                uniq: dict = {}
                for h in real_hits:
                    hid = h.get("id")
                    if hid not in uniq:
                        uniq[hid] = h
                top = list(uniq.values())[:top_k]
                self.logger.log("太史阁", "真实检索命中", f"平台知识库召回 {len(top)} 条（非本地模拟）")
                return [f"#{h.get('id','?')}: {h.get('title','')}" for h in top]
        # 回退：本地 CJK 二元切分（仅当平台真实不可达，诚实标注）
        path = os.path.join(self.out_dir, "cards_index.json")
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            cards = json.load(f)
        q = set(_tokenize(query))
        scored = []
        for c in cards:
            toks = set(_tokenize(c.get("title", "") + c.get("content", "")))
            score = len(q & toks)
            if score:
                scored.append((score, c["id"], c["title"]))
        scored.sort(reverse=True)
        if scored:
            self.logger.log("太史阁", "检索回退(本地)", f"平台不可达，使用本地二元切分召回 {len(scored)} 条", status="warn")
        return [f"#{i}: {t}" for _, i, t in scored[:top_k]]
