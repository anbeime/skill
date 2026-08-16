"""监察院 (JianChaYuanAgent)：逻辑审查、质量评估、Gap 抽取，产出解释绿卡。

绿卡必须 cite 蓝卡（溯源铁律）。Gap 类型：contradiction / underexplored / temporal_tension。
- 离线基线：规则判定（llm_involved=False）。
- LLM 在环：若本地模型可达，额外对研究空白做科学意义评级（llm_involved=True）。
"""
from __future__ import annotations
import os
import sys
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from common.card_model import Card
from common.logger import ProvenanceLogger


class JianChaYuanAgent:
    def __init__(self, cfg: dict, base_dir: str, logger: ProvenanceLogger, llm=None):
        self.cfg = cfg
        self.base_dir = base_dir
        self.logger = logger
        self.llm = llm
        self.gap_types = set(cfg["audit"]["gap_types"])

    def review(self, blues: list[Card], kb_ctx: list[str] | None = None) -> list[Card]:
        gaps_path = os.path.join(self.base_dir, "examples", "snse_survey", "raw", "gaps.json")
        with open(gaps_path, "r", encoding="utf-8") as f:
            gaps = json.load(f)
        greens: list[Card] = []
        for g in gaps:
            if g["gap_type"] not in self.gap_types:
                continue
            cited = blues[g["blue_index"]].id if 0 <= g["blue_index"] < len(blues) else None
            greens.append(Card(
                card_type="green",
                title=f"Gap[{g['gap_type']}]：{g['title']}",
                content=g["content"],
                source_id=cited,
                gap_type=g["gap_type"],
                llm_involved=False,
            ))
        self.logger.log("监察院", "生成解释绿卡(Gap)", f"{len(greens)} 张，均 cite 蓝卡（规则基线）")

        # —— LLM 在环：对首个 underexplored gap 做科学意义评级 ——
        if self.llm is not None:
            target = next((g for g in gaps if g["gap_type"] == "underexplored"), None)
            if target:
                cited = blues[target["blue_index"]].id if 0 <= target["blue_index"] < len(blues) else None
                sys_p = "你是材料科学研究评估专家。判断给定研究空白的科学意义等级并简要说明理由。"
                kb_hint = ""
                if kb_ctx:
                    kb_hint = "\n参考知识库已有相关结论：\n" + "\n".join(f"- {x}" for x in kb_ctx[:5])
                usr_p = (f"研究空白：{target['title']}\n背景：{target['content']}{kb_hint}\n\n"
                         f"请返回JSON：{{\"significance\": \"高/中/低\", \"reason\": \"一句话理由\"}}。只返回JSON。")
                out = self.llm.chat(sys_p, usr_p, max_tokens=200, temperature=0.3)
                if out:
                    from common.llm_client import extract_json
                    j = extract_json(out)
                    sig = (j or {}).get("significance", "中")
                    reason = (j or {}).get("reason", "（LLM 未返回理由）")
                    greens.append(Card(
                        card_type="green",
                        title=f"Gap意义评级(LLM)：{target['title']}",
                        content=f"科学意义等级：{sig}。理由：{reason}",
                        source_id=cited,
                        gap_type=target["gap_type"],
                        llm_involved=True,
                    ))
                    self.logger.log("监察院", "LLM 科学意义评级", f"{target['title']} -> {sig}（真实本地模型）")
        return greens
