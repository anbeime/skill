"""四色卡片数据模型（事实蓝 / 解释绿 / 风险黄 / 行动红）。

溯源铁律：绿卡必须 cite 蓝卡，红卡必须 cite 绿卡或蓝卡；无来源不得入库。
"""
from __future__ import annotations
import json
import uuid
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Card:
    card_type: str                       # blue / green / yellow / red
    title: str
    content: str
    source_id: Optional[str] = None     # 所依据的上游卡片 id（溯源）
    paper_id: Optional[str] = None      # 蓝卡：原文出处文档 id
    location: Optional[str] = None      # 蓝卡：原文位置（页/段）
    parser: Optional[str] = None        # 蓝卡：解析器来源
    gap_type: Optional[str] = None      # 绿卡：contradiction/underexplored/temporal_tension
    risk_level: Optional[str] = None    # 黄卡：high/medium/low
    owner: Optional[str] = None         # 红卡：负责人
    due: Optional[str] = None           # 红卡：期限
    accept_criteria: Optional[str] = None  # 红卡：验收标准
    llm_involved: bool = True           # 该卡片是否经 LLM 在环生成（否则如实标注）
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Card":
        return cls(**d)


def save_cards(cards: list[Card], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump([c.to_dict() for c in cards], f, ensure_ascii=False, indent=2)


def load_cards(path: str) -> list[Card]:
    with open(path, "r", encoding="utf-8") as f:
        return [Card.from_dict(d) for d in json.load(f)]


if __name__ == "__main__":
    c = Card(card_type="blue", title="测试蓝卡", content="x", paper_id="P1", location="p3")
    print(json.dumps(c.to_dict(), ensure_ascii=False))
