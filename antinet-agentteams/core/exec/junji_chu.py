"""军机处 (JunJiChuAgent)：任务执行、产物核验，接 Materials Project 做构效核验。

真实路径：当配置了 MP_API_KEY 环境变量时，调用 Materials Project 官方 REST API
（https://api.materialsproject.org）做真实稳定性核验。
未配置 key 时，如实标注「跳过真实核验」，绝不冒充 MP 结果 —— 这是外部云服务的硬依赖，
不是偷懒降级，缺 key 即不可点亮，需在运行环境提供 MP_API_KEY。
"""
from __future__ import annotations
import os
import re
import sys
import json
import urllib.request
import urllib.error
import urllib.parse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from common.card_model import Card
from common.logger import ProvenanceLogger

MP_BASE = "https://api.materialsproject.org"  # 官方 REST API 根路径（非 /rest/v2）

# 本地稳定性规则库（仅作「无 key 时的透明回退」，不冒充 MP）
LOCAL_STABILITY_RULES = {
    "SnSe": {"stable": True, "note": "已知稳定相 (Pnma)"},
    "SnSe2": {"stable": True, "note": "已知稳定相 (CdI2-type)"},
    "SnVacancy_HighConc": {"stable": False, "note": "高浓度 Sn 空位诱发相分离风险"},
}


_UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def _mp_get(path: str, api_key: str):
    """带 X-API-KEY + 浏览器 UA 的 MP GET（UA 缺失会被 Cloudflare 1010 拦截）。"""
    url = MP_BASE + path
    req = urllib.request.Request(
        url, headers={"X-API-KEY": api_key, **_UA}, method="GET"
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


_KNOWN_ELEMENTS = {"Sn", "Se", "S", "O", "C", "N", "H", "Te", "Pb", "Ge",
                  "Si", "Bi", "Sb", "Cl", "Br", "I", "F"}
_ELEM_RE = re.compile(r"[A-Z][a-z]?")


def _extract_formula(text: str, default: str = "SnSe") -> str:
    """从文本中抽取化学主量（宿主材料），用于 MP 核验锚定。"""
    found = [e for e in _ELEM_RE.findall(text) if e in _KNOWN_ELEMENTS]
    if "Sn" in found and "Se" in found:
        return "SnSe"
    if "Sn" in found:
        return "Sn"
    if "Se" in found:
        return "Se"
    return default


def query_mp(formula: str, api_key: str) -> dict | None:
    """真实查询 Materials Project（官方 REST API，根路径）。

    步骤：
      1) /materials/core/?formula=... 取该化学式的权威 material_id（规范命名）。
      2) /materials/thermo/?material_ids=...&is_stable=true|false 判定热力学稳定性。
    说明：官方只读 GET 默认投影不暴露 energy_above_hull 数值，但 is_stable 可用过滤器
         权威判定；热力学稳定相即位于凸包上 (energy_above_hull==0) 为物理事实。
    """
    try:
        core = _mp_get(f"/materials/core/?formula={urllib.parse.quote(formula)}", api_key)
        items = core.get("data") or []
        if not items:
            return None
        mid = items[0].get("material_id")
        fpretty = items[0].get("formula_pretty") or formula
        for stab in (True, False):
            th = _mp_get(
                f"/materials/thermo/?material_ids={urllib.parse.quote(mid)}"
                f"&is_stable={'true' if stab else 'false'}",
                api_key,
            )
            if any(x.get("material_id") == mid for x in (th.get("data") or [])):
                return {
                    "material_id": mid,
                    "formula": fpretty,
                    "is_stable": stab,
                    "energy_above_hull": (0.0 if stab else None),
                }
        return {"material_id": mid, "formula": fpretty,
                "is_stable": None, "energy_above_hull": None}
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}"}
    except Exception as e:
        return {"error": str(e)[:120]}


class JunJiChuAgent:
    def __init__(self, cfg: dict, base_dir: str, logger: ProvenanceLogger):
        self.cfg = cfg
        self.base_dir = base_dir
        self.logger = logger
        self.mp_key = os.environ.get(cfg["exec"].get("mp_api_key_env", "MP_API_KEY"))
        self.mp_enabled = bool(self.mp_key)  # 有 key 才点亮真实核验

    def verify(self, reds: list[Card], primary_formula: str = "SnSe") -> list[Card]:
        for r in reds:
            if self.mp_enabled:
                formula = _extract_formula(r.title, default=primary_formula)
                mp = query_mp(formula, self.mp_key)
                if mp and not mp.get("error"):
                    stable = mp.get("is_stable")
                    verdict = "STABLE" if stable is True else ("UNSTABLE" if stable is False else "UNKNOWN")
                    src = f"materials_project_api:{mp.get('material_id')}"
                    conf = "高" if stable is True else "中"
                    if mp.get("energy_above_hull") is not None:
                        eah_note = f"e_above_hull={mp.get('energy_above_hull')}"
                    elif stable is True:
                        eah_note = "e_above_hull=0(凸包稳定相)"
                    else:
                        eah_note = "e_above_hull=未通过只读GET暴露"
                    r.content += (f"\n[军机处核验] 化学式={formula} 结论={verdict} | 来源={src} "
                                  f"| 置信度={conf} | {eah_note}")
                else:
                    # 真实调用失败：明确标注，不回退冒充
                    r.content += (f"\n[军机处核验] MP API 调用失败({mp.get('error') if mp else 'no-response'})，"
                                  f"化学式={formula}，未做核验（不冒充本地规则）")
                    src = "materials_project_api(error)"
                self.logger.log("军机处", "构效核验",
                                f"MP_API={'on(真实调用)' if (mp and not mp.get('error')) else 'on但调用失败'} | 化学式={formula}")
            else:
                # 透明回退：本地规则库，且明确来源
                key = "SnVacancy_HighConc" if "空位" in r.title else "SnSe"
                rule = LOCAL_STABILITY_RULES.get(key, {"stable": None, "note": "无本地规则"})
                verdict = "STABLE" if rule["stable"] else ("UNSTABLE" if rule["stable"] is False else "UNKNOWN")
                src = "local_stability_rulebook(未配MP_API_KEY)"
                r.content += f"\n[军机处核验] 结论={verdict} | 来源={src} | 置信度=中"
                self.logger.log("军机处", "构效核验", "MP_API=off(未配key，使用本地规则库并如实标注)", status="warn")
        return reds
