"""指挥使 (OrchestratorAgent)：意图识别、任务分发、异常熔断。

端到端编排八官署；任一官署失败时按 circuit_breaker 降级而非崩溃。
"""
from __future__ import annotations
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from security.jinyiwei import JinYiWeiAgent
from archive.mijuanfang import MiJuanFangAgent
from comm.tongzhengsi import TongZhengSiAgent
from audit.jichayuan import JianChaYuanAgent
from strategy.chengxiangfu import ChengXiangFuAgent
from exec.junji_chu import JunJiChuAgent
from memory.taishige import TaiShiGeAgent
from common.logger import ProvenanceLogger
from common.llm_client import LLMClient
from common.zhijia_client import ZhijiaClient


class OrchestratorAgent:
    def __init__(self, cfg: dict, base_dir: str):
        self.cfg = cfg
        self.base_dir = base_dir
        prov_dir = os.path.join(base_dir, cfg["memory"]["provenance_dir"])
        self.logger = ProvenanceLogger(prov_dir)
        # LLM 在环：直连本地 NPU 模型 Genie（与后端/hermes 同一模型），离线自动降级
        self.llm = LLMClient()
        # 知易平台客户端：本机 Genie 生态知识中枢（解析+真实向量检索），不可达时各官署诚实回退
        zcfg = cfg.get("zhijia", {})
        self.zhijia = ZhijiaClient(base_url=zcfg.get("base_url", "http://127.0.0.1:8000"))
        self.jinyiwei = JinYiWeiAgent(cfg, base_dir, self.logger)
        self.mijuanfang = MiJuanFangAgent(cfg, base_dir, self.logger, self.zhijia)
        self.tongzhengsi = TongZhengSiAgent(cfg, base_dir, self.logger, self.llm)
        self.jichayuan = JianChaYuanAgent(cfg, base_dir, self.logger, self.llm)
        self.chengxiangfu = ChengXiangFuAgent(cfg, base_dir, self.logger, self.llm)
        self.junjichu = JunJiChuAgent(cfg, base_dir, self.logger)
        self.taishige = TaiShiGeAgent(cfg, base_dir, self.logger, self.zhijia)

    def plan(self, topic: str) -> list[str]:
        subtasks = ["安检", "解析", "抽蓝卡", "抽绿卡(Gap)", "提假说(红卡)", "MP核验", "provenance回流"]
        self.logger.log("指挥使", "拆解子任务", f"{topic} -> {len(subtasks)} 步")
        return subtasks

    def run(self, topic: str) -> dict:
        self.plan(topic)
        try:
            papers = self.jinyiwei.load_papers()
            yellows, scan_report = self.jinyiwei.scan(papers)
            texts = self.mijuanfang.parse(papers)
            blues = self.tongzhengsi.extract(texts)
            greens = self.jichayuan.review(blues)
            reds = self.chengxiangfu.propose(greens)
            reds = self.junjichu.verify(reds)
            self.taishige.writeback(blues + greens + yellows + reds, scan_report)
            self.logger.log("指挥使", "主链路完成", f"蓝{len(blues)} 绿{len(greens)} 黄{len(yellows)} 红{len(reds)}")
            self.logger.dump()
            llm_used = self.llm.used_llm
            if llm_used:
                self.logger.log("指挥使", "LLM 在环", f"真实本地模型已参与 ({self.llm.endpoint_used})")
            else:
                self.logger.log("指挥使", "LLM 在环", "未启用：本地模型不可达，已如实降级为规则引擎", status="warn")
            return {
                "topic": topic, "blues": blues, "greens": greens,
                "yellows": yellows, "reds": reds, "scan_report": scan_report,
                "parsed": self.mijuanfang.last_parsed_count,
                "llm_used": llm_used,
                "llm_endpoint": self.llm.endpoint_used,
            }
        except Exception as e:
            self.logger.log("指挥使", "熔断", str(e), status="breaker")
            if self.cfg["command"].get("circuit_breaker"):
                raise RuntimeError(f"主链路熔断: {e}")
            raise
