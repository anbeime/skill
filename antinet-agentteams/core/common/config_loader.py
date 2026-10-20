"""配置加载器：优先 PyYAML，缺失时回退内置默认配置（零外部依赖）。"""
from __future__ import annotations
import os
import json

DEFAULT_CONFIG = {
    "project": {
        "name": "materials-agent",
        "track": "GOAI 赛道一 · Agent Infra (新智基座)",
        "topic_example": "SnSe 空位工程导热",
    },
    "command": {"max_subtasks": 8, "llm_fallback": "heuristic", "circuit_breaker": True},
    "security": {
        "blocked_hosts": [
            "sci-hub.se", "sci-hub.st", "sci-hub.ru", "sci-hub.wf", "sci-hub.ren",
        ],
        "forbid_local_cache_as_production": True,
        "scan_secrets": True,
    },
    "archive": {"parsers": ["pymupdf", "pdfplumber", "mineru"], "target_parsed_ratio": 0.5},
    "comm": {"oa_sources": ["sciverse", "openalex", "arxiv", "pmc"], "oa_only": True},
    "audit": {"gap_types": ["contradiction", "underexplored", "temporal_tension"]},
    "exec": {"mp_api_enabled": False, "mp_api_key_env": "MP_API_KEY"},
    "memory": {"provenance_dir": "examples/snse_survey/provenance", "vector_enabled": False},
    # 知易平台（本机 Genie 生态知识中枢）：提供真实 PDF 解析 + 向量检索（= 本地 MinerU + Qdrant 真身）
    "zhijia": {"base_url": "http://127.0.0.1:8000", "enabled": True},
}


def load_config(path: str | None = None) -> dict:
    """加载配置。优先读 YAML，失败回退默认。"""
    if path and os.path.exists(path):
        try:
            import yaml  # type: ignore
            with open(path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f)
                if isinstance(cfg, dict):
                    return cfg
        except Exception:
            pass
    return DEFAULT_CONFIG


if __name__ == "__main__":
    cfg = load_config(os.path.join(os.path.dirname(__file__), "..", "..", "configs", "production.yaml"))
    print(json.dumps(cfg, ensure_ascii=False, indent=2))
