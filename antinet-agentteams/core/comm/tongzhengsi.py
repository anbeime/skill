"""通政司 (TongZhengSiAgent)：内容抽取与结构化，产出事实蓝卡。

蓝卡必须包含：原文出处（paper_id + location）+ parser，确保可回原文。
- 离线基线：从预存 facts.json 读取抽取结果（规则抽取，llm_involved=False）。
- LLM 在环：若本地模型可达，额外从真实全文抽取一条事实蓝卡（llm_involved=True）。
"""
from __future__ import annotations
import os
import sys
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from common.card_model import Card
from common.logger import ProvenanceLogger


class TongZhengSiAgent:
    def __init__(self, cfg: dict, base_dir: str, logger: ProvenanceLogger, llm=None):
        self.cfg = cfg
        self.base_dir = base_dir
        self.logger = logger
        self.llm = llm

    def extract(self, parsed: dict[str, dict], kb_ctx: list[str] | None = None) -> list[Card]:
        facts_path = os.path.join(self.base_dir, "examples", "snse_survey", "raw", "facts.json")
        with open(facts_path, "r", encoding="utf-8") as f:
            facts = json.load(f)
        blues: list[Card] = []
        for ft in facts:
            parser = parsed.get(ft["paper_id"], {}).get("parser", "unknown")
            blues.append(Card(
                card_type="blue",
                title=f"事实：{ft['paper_id']}",
                content=ft["quote"],
                paper_id=ft["paper_id"],
                location=ft.get("location", "n/a"),
                parser=parser,
                llm_involved=False,  # 规则抽取，如实标注
            ))
        self.logger.log("通政司", "生成事实蓝卡", f"{len(blues)} 张，均带 paper_id+loc 溯源")

        # —— LLM 在环：从真实全文额外抽取一条事实（关键差异化能力）——
        if self.llm is not None:
            for pid, info in parsed.items():
                text = info.get("text", "")
                if not text:
                    continue
                sys_p = "你是材料科学文献抽取器。从论文全文抽取一条可验证的事实性陈述，并给出尽量贴近原文的引用句。"
                kb_hint = ""
                if kb_ctx:
                    kb_hint = "\n\n参考知识库已有相关结论（优先参考）：\n" + "\n".join(f"- {x}" for x in kb_ctx[:5])
                usr_p = f"论文《{info.get('title', pid)}》全文：\n{text[:3000]}{kb_hint}\n\n请返回JSON：{{\"quote\": \"原文引用句\", \"location\": \"如 p2 第2段\"}}。只返回JSON。"
                out = self.llm.chat(sys_p, usr_p, max_tokens=200, temperature=0.2)
                if out:
                    from common.llm_client import extract_json
                    j = extract_json(out)
                    if j and j.get("quote"):
                        blues.append(Card(
                            card_type="blue",
                            title=f"事实(LLM)：{pid}",
                            content=j["quote"],
                            paper_id=pid,
                            location=j.get("location", "LLM抽取"),
                            parser=info.get("parser", "unknown"),
                            llm_involved=True,
                        ))
                        self.logger.log("通政司", "LLM 抽取事实蓝卡", f"{pid}（真实本地模型生成）")
                        break  # 仅抽一条作为示范，避免拖慢链路
        return blues
