"""丞相府 (ChengXiangFuAgent)：策略建议与呈现，产出行动红卡。

基于 Gap 提出构效关系假说 -> 行动红卡（下一步验证 + 证伪实验设计）。
红卡必须 cite 绿卡或蓝卡（溯源铁律）。
- 离线基线：预存 hypotheses.json（llm_involved=False）。
- LLM 在环：若本地模型可达，额外生成一条由真实模型推理的构效假说 + 证伪实验（llm_involved=True）。
"""
from __future__ import annotations
import os
import sys
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from common.card_model import Card
from common.logger import ProvenanceLogger


class ChengXiangFuAgent:
    def __init__(self, cfg: dict, base_dir: str, logger: ProvenanceLogger, llm=None):
        self.cfg = cfg
        self.base_dir = base_dir
        self.logger = logger
        self.llm = llm

    def propose(self, greens: list[Card], kb_ctx: list[str] | None = None) -> list[Card]:
        hypo_path = os.path.join(self.base_dir, "examples", "snse_survey", "raw", "hypotheses.json")
        with open(hypo_path, "r", encoding="utf-8") as f:
            hypos = json.load(f)
        reds: list[Card] = []
        for h in hypos:
            cited = greens[h["green_index"]].id if 0 <= h["green_index"] < len(greens) else None
            reds.append(Card(
                card_type="red",
                title=f"假说与行动：{h['title']}",
                content=h["content"],
                source_id=cited,
                owner=h.get("owner", "课题组"),
                due=h.get("due", "TBD"),
                accept_criteria=h.get("accept_criteria", "验证通过/证伪"),
                llm_involved=False,
            ))
        self.logger.log("丞相府", "生成行动红卡(构效假说)", f"{len(reds)} 张，均 cite 绿卡（规则基线）")

        # —— LLM 在环：由真实本地模型生成构效假说 + 证伪实验（核心放大器）——
        if self.llm is not None and greens:
            cited = greens[0].id
            gap_hint = "；".join(g.title for g in greens[:3])
            sys_p = "你是材料科学构效关系研究助手。请基于给定研究空白，提出一条具体、可检验的构效关系假说，并给出可证伪的实验设计。"
            kb_hint = ""
            if kb_ctx:
                kb_hint = "\n参考知识库已有相关结论：\n" + "\n".join(f"- {x}" for x in kb_ctx[:5])
            usr_p = (f"研究主题：SnSe 空位工程调控热导率。\n已知研究空白：{gap_hint}{kb_hint}\n\n"
                     f"请返回JSON：{{\"hypothesis\": \"一句话假说\", \"falsification\": \"证伪实验设计\", \"next_step\": \"下一步动作\"}}。只返回JSON，中文。")
            out = self.llm.chat(sys_p, usr_p, max_tokens=300, temperature=0.5)
            if out:
                from common.llm_client import extract_json
                j = extract_json(out) or {}
                hypo = j.get("hypothesis", "（LLM 未返回假说）")
                fal = j.get("falsification", "（LLM 未返回证伪设计）")
                step = j.get("next_step", "补充计算/实验验证")
                reds.append(Card(
                    card_type="red",
                    title=f"LLM构效假说：SnSe 空位-热导",
                    content=f"假说：{hypo}\n证伪实验：{fal}\n下一步：{step}",
                    source_id=cited,
                    owner="丞相府(LLM)",
                    due="初赛前",
                    accept_criteria="MP 核验构型稳定 + 实验/计算验证趋势一致",
                    llm_involved=True,
                ))
                self.logger.log("丞相府", "LLM 生成构效假说", "由真实本地模型推理（qwen2.5vl3b）")
        return reds
