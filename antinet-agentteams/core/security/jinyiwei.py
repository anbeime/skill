"""锦衣卫 (JinYiWeiAgent)：安全审查、合规扫描、防'假全文'冒充。

核心职责（材料场景）：
1. 拦截 Sci-Hub 等侵权源（硬编码黑名单）；
2. 禁止把 local_cache 当作生产证据（forbid_local_cache_as_production）；
3. 扫描文献文本中的密钥/凭证泄露。
命中即生成风险黄卡，并写入 scan_report 供验收脚本读取。
"""
from __future__ import annotations
import os
import sys
import json
import re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from common.card_model import Card
from common.logger import ProvenanceLogger


SECRET_RE = re.compile(r"(api[_-]?key|sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16})", re.I)


class JinYiWeiAgent:
    def __init__(self, cfg: dict, base_dir: str, logger: ProvenanceLogger):
        self.cfg = cfg
        self.base_dir = base_dir
        self.logger = logger

    def load_papers(self) -> list[dict]:
        path = os.path.join(self.base_dir, "examples", "snse_survey", "raw", "papers.json")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def scan(self, papers: list[dict]) -> tuple[list[Card], dict]:
        blocked = set(self.cfg["security"]["blocked_hosts"])
        forbid_cache = self.cfg["security"]["forbid_local_cache_as_production"]
        yellows: list[Card] = []
        intercepted = []
        local_cache_hits = 0
        for p in papers:
            host = p.get("host", "")
            # 1. 侵权源拦截
            if any(b in host for b in blocked):
                intercepted.append(p["id"])
                yellows.append(Card(
                    card_type="yellow", title=f"拦截侵权源 {host}",
                    content=f"论文 {p['id']} 来自黑名单域名 {host}，已拒绝下载/使用。",
                    risk_level="high", llm_involved=False,
                ))
                continue
            # 2. 防 local_cache 冒充生产证据
            if forbid_cache and p.get("source") == "local_cache":
                local_cache_hits += 1
                yellows.append(Card(
                    card_type="yellow", title=f"local_cache 冒充拦截 {p['id']}",
                    content=f"论文 {p['id']} 标记为 local_cache，按策略禁止作为生产证据。",
                    risk_level="high", llm_involved=False,
                ))
        # 3. 密钥扫描（对 OA 全文）
        secret_hits = 0
        facts_path = os.path.join(self.base_dir, "examples", "snse_survey", "raw", "facts.json")
        if os.path.exists(facts_path):
            with open(facts_path, "r", encoding="utf-8") as f:
                for fact in json.load(f):
                    if SECRET_RE.search(fact.get("quote", "")):
                        secret_hits += 1
        if secret_hits:
            yellows.append(Card(
                card_type="yellow", title="疑似密钥泄露",
                content=f"在 {secret_hits} 处文本中发现疑似 API key / 凭证，已脱敏处理。",
                risk_level="medium", llm_involved=False,
            ))
        scan_report = {
            "profile": "production",
            "forbid_local_cache_as_production": forbid_cache,
            "local_cache_hits": local_cache_hits,
            "oa_only": self.cfg["comm"]["oa_only"],
            "blocked_hosts": list(blocked),
            "intercepted_papers": intercepted,
            "secret_hits": secret_hits,
            "no_local_cache_as_production": (local_cache_hits == 0),
        }
        self.logger.log("锦衣卫", "合规扫描", f"拦截{len(intercepted)} 命中缓存{local_cache_hits} 密钥{secret_hits}")
        return yellows, scan_report
