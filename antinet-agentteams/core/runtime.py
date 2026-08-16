"""AgentTeamsRuntime：把八官署纯 Python 模块以 AgentTeams Worker 形式在本地装载与编排。

这是「复赛 · 可执行 AgentTeams 代码包」的本地执行内核：
- 零外部依赖（仅 Python 标准库），可完全离线运行；
- 真实调用八官署各官署模块（非模拟），与 AgentTeams 集群内运行时使用同一套代码；
- 通过 run_stage() 暴露每个 Worker 的能力，供 AgentTeams 的 Team Leader 按角色派发；
- 与 AgentTeams 集群部署共用 manifest 中声明的 9 个 CR（Manager/Team/7 Worker）。
"""
from __future__ import annotations

import os
import sys

CORE_DIR = os.path.dirname(os.path.abspath(__file__))
if CORE_DIR not in sys.path:
    sys.path.insert(0, CORE_DIR)

from common.config_loader import load_config
from common.logger import ProvenanceLogger
from common.llm_client import LLMClient
from common.zhijia_client import ZhijiaClient
from security.jinyiwei import JinYiWeiAgent
from archive.mijuanfang import MiJuanFangAgent
from comm.tongzhengsi import TongZhengSiAgent
from audit.jichayuan import JianChaYuanAgent
from strategy.chengxiangfu import ChengXiangFuAgent
from exec.junji_chu import JunJiChuAgent
from memory.taishige import TaiShiGeAgent


# 八官署 → AgentTeams CRD 角色映射（与 manifests/ 中资源一一对应）
ROLE_MAP = {
    "zhihuiling":  {"office": "指挥使", "kind": "Manager"},
    "junsicha":    {"office": "军机处", "kind": "Worker", "team_role": "team_leader", "skill": None},
    "chengxiangfu": {"office": "丞相府", "kind": "Worker", "skill": "four-color-cards"},
    "jinyiwei":    {"office": "锦衣卫", "kind": "Worker", "skill": "security-scan"},
    "mijuanfang":  {"office": "密卷房", "kind": "Worker", "skill": "doc-parse"},
    "tongzhengsi": {"office": "通政司", "kind": "Worker", "skill": "four-color-cards"},
    "jianchayuan": {"office": "监察院", "kind": "Worker", "skill": "four-color-cards"},
    "taishige":    {"office": "太史阁", "kind": "Worker", "skill": "provenance"},
}

# 端到端主链路（军机处拆解后的子任务顺序）
PIPELINE = ["security-scan", "doc-parse", "extract", "review", "propose", "verify", "provenance"]

# 子任务 → 负责官署 / Skill
STAGE_OWNER = {
    "security-scan": ("jinyiwei", "锦衣卫", "security-scan"),
    "doc-parse": ("mijuanfang", "密卷房", "doc-parse"),
    "extract": ("tongzhengsi", "通政司", "four-color-cards"),
    "review": ("jianchayuan", "监察院", "four-color-cards"),
    "propose": ("chengxiangfu", "丞相府", "four-color-cards"),
    "verify": ("junjichu", "军机处", None),
    "provenance": ("taishige", "太史阁", "provenance"),
}


class AgentSession:
    """一次 AgentTeams Team 任务会话：装载各官署 Worker，按角色派发子任务。"""

    def __init__(self, base_dir: str, config_path: str | None = None, workspace: str | None = None):
        self.base_dir = os.path.abspath(base_dir)
        self.cfg = load_config(config_path or os.path.join(self.base_dir, "configs", "production.yaml"))
        prov_dir = workspace or os.path.join(self.base_dir, self.cfg["memory"]["provenance_dir"])
        self.logger = ProvenanceLogger(prov_dir)
        self.llm = LLMClient()
        # 知易平台客户端：本机 Genie 生态知识中枢（真实 PDF 解析 + 向量检索）
        zcfg = self.cfg.get("zhijia", {})
        self.zhijia = ZhijiaClient(base_url=zcfg.get("base_url", "http://127.0.0.1:8000"))
        # 装载 7 个官署 Worker（与 manifest 中 7 个 Worker CR 对应）
        self.jinyiwei = JinYiWeiAgent(self.cfg, self.base_dir, self.logger)
        self.mijuanfang = MiJuanFangAgent(self.cfg, self.base_dir, self.logger, self.zhijia)
        self.tongzhengsi = TongZhengSiAgent(self.cfg, self.base_dir, self.logger, self.llm)
        self.jichayuan = JianChaYuanAgent(self.cfg, self.base_dir, self.logger, self.llm)
        self.chengxiangfu = ChengXiangFuAgent(self.cfg, self.base_dir, self.logger, self.llm)
        self.junjichu = JunJiChuAgent(self.cfg, self.base_dir, self.logger)
        self.taishige = TaiShiGeAgent(self.cfg, self.base_dir, self.logger, self.zhijia)
        self.state: dict = {}

    # ------------------------------------------------------------------
    # 各官署 Worker 能力（run_stage 按依赖惰性执行，复用中间产物）
    # ------------------------------------------------------------------
    def _ensure(self, name):
        if name in self.state:
            return self.state[name]
        if name == "papers":
            papers = self.jinyiwei.load_papers()
            self.state["papers"] = papers
            return papers
        if name == "security-scan":  # 锦衣卫：合规安检
            papers = self._ensure("papers")
            yellows, scan = self.jinyiwei.scan(papers)
            self.state["security-scan"] = {"yellows": yellows, "scan_report": scan}
            return self.state["security-scan"]
        if name == "doc-parse":  # 密卷房：多格式解析
            papers = self._ensure("papers")
            texts = self.mijuanfang.parse(papers)
            self.state["doc-parse"] = texts
            return texts
        if name == "extract":  # 通政司：事实蓝卡
            texts = self._ensure("doc-parse")
            blues = self.tongzhengsi.extract(texts, kb_ctx=self.state.get("kb_ctx"))
            self.state["extract"] = blues
            return blues
        if name == "review":  # 监察院：解释绿卡（Gap）
            blues = self._ensure("extract")
            greens = self.jichayuan.review(blues, kb_ctx=self.state.get("kb_ctx"))
            self.state["review"] = greens
            return greens
        if name == "propose":  # 丞相府：行动红卡（构效假说）
            greens = self._ensure("review")
            reds = self.chengxiangfu.propose(greens, kb_ctx=self.state.get("kb_ctx"))
            self.state["propose"] = reds
            return reds
        if name == "verify":  # 军机处：构效核验（MP provenance）
            reds = self._ensure("propose")
            reds = self.junjichu.verify(reds)
            self.state["verify"] = reds
            return reds
        if name == "provenance":  # 太史阁：留痕回流
            sec = self._ensure("security-scan")
            cards = (
                self.state.get("extract", [])
                + self.state.get("review", [])
                + self.state.get("security-scan", {}).get("yellows", [])
                + self.state.get("verify", [])
            )
            self.taishige.writeback(cards, sec["scan_report"])
            self.state["provenance"] = True
            return True
        raise KeyError(f"unknown stage: {name}")

    def run_stage(self, stage: str):
        """按 AgentTeams 角色派发单个 Worker 子任务（幂等）。"""
        owner = STAGE_OWNER.get(stage)
        if owner:
            self.logger.log("军机处", "派发", f"@{owner[1]}({owner[0]}) <- {stage}"
                           + (f" / skill:{owner[2]}" if owner[2] else ""))
        return self._ensure(stage)

    def run_full(self, topic: str | None = None) -> dict:
        """指挥使(Manger) → 军机处(Team Leader) → 各 Worker 端到端主链路。"""
        topic = topic or self.cfg["project"].get("topic_example", "SnSe 空位工程导热")
        self.logger.log("指挥使", "意图识别", f"任务「{topic}」-> 路由至 antinet 团队")
        # P0-a：先读库再干活（AGENTS.md 第4节）——结合本机知易知识库
        kb_ctx = self.taishige.recall(topic)
        self.state["kb_ctx"] = kb_ctx
        if kb_ctx:
            self.logger.log("指挥使", "读库", f"任务「{topic}」召回历史知识 {len(kb_ctx)} 条，注入下游官署上下文")
        else:
            self.logger.log("指挥使", "读库", "平台知识库无命中，进入零样本链路", status="warn")
        self.logger.log("军机处", "任务拆解",
                        " -> ".join(PIPELINE) + "（每个子任务 @ 对应官署 Worker）")
        for stage in PIPELINE:
            self.run_stage(stage)
        self.logger.dump()
        sec = self.state["security-scan"]
        return {
            "topic": topic,
            "blues": self.state.get("extract", []),
            "greens": self.state.get("review", []),
            "reds": self.state.get("verify", []),
            "yellows": sec["yellows"],
            "scan_report": sec["scan_report"],
            "llm_used": self.llm.used_llm,
            "llm_endpoint": self.llm.endpoint_used,
        }
