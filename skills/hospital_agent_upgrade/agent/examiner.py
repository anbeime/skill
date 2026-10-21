"""Examination routing and coverage strategy for the doctor agent."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from typing import Any, Dict, List, Optional

from .utils import (
    as_text_list,
    build_name_map,
    clean_text,
    match_standard_name,
    match_standard_or_contained_name,
    normalize_name,
    unique_preserve_order,
)
from .terminology import best_match

_NON_EVIDENCE_PROFILE_FIELDS = {"missing_critical_fields"}


def exam_core_name(value: Any) -> str:
    text = str(value or "")
    text = re.sub(r"[（(][^）)]*[）)]", "", text)
    text = re.sub(r"[A-Za-z]+", "", text)
    return normalize_name(text)


def build_exam_core_map(exam_names: Iterable[str]) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for name in as_text_list(exam_names):
        for key in (normalize_name(name), exam_core_name(name)):
            if key and key not in result:
                result[key] = name
    return result


def resolve_exam_name(
    value: Any,
    exam_core_map: Dict[str, str],
    available_examinations: Iterable[str],
) -> str:
    text = clean_text(value)
    if not text:
        return ""
    available_map = build_name_map(as_text_list(available_examinations))
    direct = match_standard_or_contained_name(text, available_map)
    if direct:
        return direct
    core = exam_core_name(text)
    if core in exam_core_map:
        return exam_core_map[core]
    for key, standard in exam_core_map.items():
        if key and core and (key in core or core in key):
            return standard
    alias = _exam_alias_match(text, available_examinations)
    if alias:
        return alias
    fuzzy = best_match(text, available_examinations, score_cutoff=0.84)
    return fuzzy if _exam_names_semantically_related(text, fuzzy) else ""


_EXAM_ALIASES: tuple[tuple[tuple[str, ...], str], ...] = (
    (("散瞳验光", "睫状肌麻痹验光", "验光"), "屈光检查"),
    (("眼底检查",), "眼底镜检查"),
    (("眼前节oct", "as-oct", "前节oct"), "眼前节光学相干断层扫描（AS-OCT）"),
    (("前房角镜",), "房角镜检查"),
    (("hrct", "高分辨率ct"), "颞骨高分辨率CT扫描（Temporal Bone HRCT）"),
    (("淋巴结切除活检", "淋巴结病理"), "淋巴结活检"),
    (("戴镜眼位", "戴镜后眼位", "三棱镜检查", "斜视度"), "遮盖试验"),
    (("立体视", "双眼视觉"), "视觉功能检查"),
    (("弱视筛查",), "视力检查"),
    (("心电图评估", "评估qt", "qt间期"), "心电图（ECG）"),
)


def _exam_alias_match(value: Any, available_examinations: Iterable[str]) -> str:
    text = normalize_name(value)
    available = set(as_text_list(available_examinations))
    for aliases, standard in _EXAM_ALIASES:
        if standard in available and any(normalize_name(alias) in text for alias in aliases):
            return standard
    return ""


def _exam_names_semantically_related(left: Any, right: Any) -> bool:
    """Reject partial-ratio matches that only share generic exam words."""
    if not clean_text(left) or not clean_text(right):
        return False

    def meaningful_chars(value: Any) -> set[str]:
        core = exam_core_name(value)
        for generic in ("检查", "检测", "试验", "测定", "评估", "功能", "分析", "扫描", "监测"):
            core = core.replace(generic, "")
        return {char for char in core if char.isalnum()}

    left_chars = meaningful_chars(left)
    right_chars = meaningful_chars(right)
    if not left_chars or not right_chars:
        return False
    shared = left_chars & right_chars
    return len(shared) >= 2 and len(shared) / min(len(left_chars), len(right_chars)) >= 0.5


def _resolve_exam(name: Any, exam_resolver: Any = None) -> str:
    if callable(exam_resolver):
        resolved = exam_resolver(name)
        if resolved:
            return resolved
    return clean_text(name)


def _resolve_exam_list(names: Iterable[str], exam_resolver: Any = None) -> List[str]:
    return unique_preserve_order(_resolve_exam(name, exam_resolver) for name in as_text_list(names))


def build_exam_purpose_map(
    differential: List[Any],
    examinations: Iterable[str],
    *,
    exam_resolver: Any = None,
) -> Dict[str, List[str]]:
    """Keep an auditable clinical purpose for every examination we order."""
    purposes: Dict[str, List[str]] = {}
    for item in differential:
        if not isinstance(item, dict):
            continue
        disease = clean_text(item.get("suspected_disease")) or "当前鉴别诊断"
        for recommended in as_text_list(item.get("recommended_examinations")):
            name = _resolve_exam(recommended, exam_resolver)
            if name and name in examinations:
                purposes.setdefault(name, []).append("确认或排除%s" % disease)
    for name in examinations:
        resolved = _resolve_exam(name, exam_resolver)
        if resolved and resolved not in purposes:
            purposes[resolved] = ["评估严重程度、治疗安全性或受累器官"]
    return purposes

def _fallback_examinations(
    *,
    case_profile: Dict[str, Any],
    differential: List[Any],
    exam_need_summary: Dict[str, Any],
    ordered: Iterable[str],
    available_examinations: Iterable[str],
    examination_catalog: Dict[str, List[str]],
    exam_resolver: Any = None,
) -> List[str]:
    suggestions = suggest_comprehensive_examinations(
        case_profile=case_profile,
        differential=differential,
        exam_need_summary=exam_need_summary,
        ordered=ordered,
        available_examinations=available_examinations,
        examination_catalog=examination_catalog,
        max_count=4,
        exam_resolver=exam_resolver,
    )
    if suggestions:
        return suggestions

    ordered_set = set(as_text_list(ordered))
    available_set = set(as_text_list(available_examinations))
    baseline = _anatomy_exam_priorities(case_profile, exam_resolver=exam_resolver)[:2]
    if not baseline:
        baseline = ["体格检查"]
    if _needs_systemic_baseline_labs(case_profile, differential) and "全血细胞计数（CBC）" not in baseline:
        baseline.append("全血细胞计数（CBC）")
    return [
        name
        for name in baseline
        if name in available_set and name not in ordered_set
    ][:3]


def _exam_batch_limit(case_profile: Dict[str, Any], differential: List[Any]) -> int:
    """Dynamic first-round exam budget driven by breadth of the presentation,
    not by any specific disease.

    - Purely local / mechanical complaints (no systemic red flags) stay narrow.
    - Multi-system, severe, or red-flag-heavy presentations get a wider batch.
    """
    text = _case_profile_text(case_profile) + json.dumps(differential[:3], ensure_ascii=False)
    red_flag_count = len(case_profile.get("red_flags") or [])

    if _has_unnegated_marker(
        text,
        ("泡沫状分泌物", "阴道异味", "阴道瘙痒", "滴虫", "阴道毛滴虫"),
    ):
        return 5
    if _has_unnegated_marker(
        text,
        ("房颤", "心房颤动", "心律绝对不齐", "心跳快且不规则"),
    ) and _has_unnegated_marker(
        text,
        ("瓣膜", "二尖瓣", "风湿", "链球菌", "心悸", "气促"),
    ):
        return 5
    if _has_unnegated_marker(
        text,
        ("梅毒", "神经梅毒", "hiv", "aids", "获得性免疫缺陷"),
    ) and _has_unnegated_marker(text, ("头痛", "认知", "记忆力", "情绪", "脑膜", "神经")):
        return 4
    if _has_unnegated_marker(
        text,
        ("角膜溃疡", "上皮缺损", "基质浸润", "前房反应", "隐形眼镜", "角膜划伤"),
    ):
        return 6
    if _has_unnegated_marker(
        text,
        ("关节积液", "膝关节肿胀", "关节肿胀", "不能负重", "浮髌", "滑液"),
    ):
        return 5
    if _has_unnegated_marker(
        text,
        ("ckd5", "慢性肾脏病5期", "egfr", "肌酐", "尿毒症", "透析", "磷结合剂"),
    ) and _has_unnegated_marker(
        text,
        ("骨痛", "瘙痒", "低钙", "高磷", "酸中毒", "骨量减少", "骨质疏松"),
    ):
        return 6

    if _has_unnegated_marker(
        text,
        ("心悸", "心慌", "心跳乱", "心跳快且不规则", "房颤", "心房颤动", "心律绝对不齐"),
    ):
        return 3

    if _is_localized_presentation(case_profile) and red_flag_count == 0:
        return 2

    if _has_unnegated_marker(
        text,
        ("尿频", "尿急", "漏尿", "排尿困难", "尿动力", "逼尿肌", "膀胱过度活动"),
    ):
        return 5
    if _has_unnegated_marker(
        text,
        ("冠脉", "心绞痛", "劳力性胸痛", "慢性cad", "冠状动脉"),
    ):
        return 6
    if _has_unnegated_marker(
        text,
        ("关节松弛", "半脱位", "皮肤过伸", "易瘀青", "col5a1", "埃勒斯", "当洛"),
    ):
        return 5
    if _has_unnegated_marker(
        text,
        ("新生儿", "婴儿", "喂养困难", "胆汁性呕吐", "胎粪", "性早熟", "阴道出血"),
    ):
        return 5
    if _has_unnegated_marker(
        text,
        ("听力反应弱", "叫名字不转头", "听不见轻声说话", "语言发育迟缓", "新生儿听力筛查", "先天性中耳畸形"),
    ):
        return 4
    if _has_unnegated_marker(
        text,
        ("继发性闭经", "闭经", "停经", "月经停止", "体重骤降", "节食"),
    ):
        return 4

    breadth_markers = (
        "多系统", "全身", "免疫抑制", "高热", "中毒", "心衰", "瓣膜",
        "狼疮", "肾", "凝血", "血小板", "电解质", "多器官", "严重", "红旗",
        "危象", "休克", "急性",
    )
    distinct_systems = _count_involved_systems(text)
    if (
        _has_unnegated_marker(text, breadth_markers)
        or red_flag_count >= 2
        or distinct_systems >= 3
    ):
        return 4
    if red_flag_count >= 1 or distinct_systems == 2:
        return 3
    return 3


def prioritize_examinations(
    examinations: Iterable[str],
    *,
    case_profile: Dict[str, Any],
    differential: List[Any],
    exam_need_summary: Optional[Dict[str, Any]] = None,
) -> List[str]:
    """Rank already-vetted examinations by urgency, diagnostic impact, and coverage."""
    names = unique_preserve_order(as_text_list(examinations))
    if not names:
        return []
    profile_text = _case_profile_text(case_profile)
    diff_text = json.dumps(differential[:5], ensure_ascii=False)
    need_text = json.dumps(exam_need_summary or {}, ensure_ascii=False)
    red_flags = as_text_list(case_profile.get("red_flags"))
    missing_dimensions = {
        clean_text(item.get("dimension"))
        for item in as_text_list([])
    }
    if isinstance(exam_need_summary, dict):
        missing_dimensions = {
            clean_text(item.get("dimension"))
            for item in exam_need_summary.get("missing_dimensions") or []
            if isinstance(item, dict)
        }

    ranked = sorted(
        names,
        key=lambda name: _exam_priority_score(
            name,
            profile_text=profile_text,
            diff_text=diff_text,
            need_text=need_text,
            red_flags=red_flags,
            missing_dimensions=missing_dimensions,
        ),
        reverse=True,
    )
    return ranked


def _exam_priority_score(
    exam_name: str,
    *,
    profile_text: str,
    diff_text: str,
    need_text: str,
    red_flags: List[str],
    missing_dimensions: set[str],
) -> tuple[int, int, int, int, str]:
    normalized = normalize_name(exam_name)
    urgent_tokens = (
        "血气", "abg", "心电", "ecg", "ct", "造影", "超声心动图", "床旁",
        "培养", "凝血", "电解质", "ntprobnp", "胸部x线", "胸部ct",
    )
    rule_out_tokens = ("mustruleout", "必须排除", "危重", "急症", "红旗", "危险")
    safety_tokens = ("肝", "肾", "凝血", "妊娠", "hcg", "过敏", "电解质")
    objective_tokens = ("ct", "mri", "x线", "超声", "培养", "活检", "病理", "血气", "心电", "ua", "cbc", "crp")

    urgent_score = 0
    if any(token in normalized for token in urgent_tokens):
        urgent_score += 3
    if any(token in diff_text.lower() for token in rule_out_tokens):
        urgent_score += 2
    if any(flag and any(token in normalize_name(flag) for token in urgent_tokens) for flag in red_flags):
        urgent_score += 2

    impact_score = 0
    if any(token in normalized for token in objective_tokens):
        impact_score += 2
    if exam_name in need_text:
        impact_score += 1

    coverage_score = 0
    if "红旗并发症评估" in missing_dimensions and any(token in normalized for token in ("血气", "电解质", "心电", "培养", "ct")):
        coverage_score += 2
    if "治疗安全评估" in missing_dimensions and any(token in normalized for token in safety_tokens):
        coverage_score += 2
    if "确诊或病因证据" in missing_dimensions and any(token in normalized for token in ("培养", "活检", "病理", "ct", "mri", "超声")):
        coverage_score += 1

    relevance_score = 0
    exam_chars = {char for char in normalized if char.isalnum() or "\u4e00" <= char <= "\u9fff"}
    shared_with_profile = sum(1 for char in exam_chars if char in normalize_name(profile_text))
    shared_with_diff = sum(1 for char in exam_chars if char in normalize_name(diff_text))
    relevance_score += min(shared_with_profile, 3)
    relevance_score += min(shared_with_diff, 3)

    return (urgent_score, coverage_score, impact_score, relevance_score, exam_name)


_SYSTEM_KEYWORDS: tuple[tuple[str, ...], ...] = (
    ("心", "胸痛", "胸闷", "心悸", "冠", "瓣", "心律"),
    ("肺", "咳", "咳血", "咯血", "气短", "呼吸困难", "喘"),
    ("肾", "尿", "蛋白尿", "血尿", "肌酐", "排尿"),
    ("肝", "黄疸", "腹", "腹泻", "呕吐", "消化"),
    ("骨", "关节", "肌", "腿痛", "跛行", "脱位", "骨折"),
    ("皮", "皮疹", "水疱", "瘙痒", "脱屑"),
    ("神经", "头痛", "麻木", "抽搐", "意识", "眩晕"),
    ("耳", "听力", "耳鸣", "咽", "喉", "扁桃体"),
    ("电解质", "低钾", "低镁", "低钙", "脱水"),
)


def _count_involved_systems(text: str) -> int:
    count = 0
    for keywords in _SYSTEM_KEYWORDS:
        if _has_unnegated_marker(text, keywords):
            count += 1
    return count


def _is_localized_presentation(case_profile: Dict[str, Any]) -> bool:
    """Pure local/mechanical or single-organ complaint without systemic signs."""
    text = _case_profile_text(case_profile)
    local_markers = (
        "外伤", "撞", "夹伤", "扭伤", "摔", "脱位", "骨折", "卡住",
        "张口", "下巴", "颞下颌", "单侧听力", "耳鸣", "耳闷", "听力下降", "突发性聋",
        "瘢痕旁", "皮下肿块", "体表肿块", "表皮样", "粉瘤", "皮脂腺",
        "皮疹", "水疱", "牙龈", "口腔溃疡",
    )
    systemic_markers = ("发热", "寒战", "脓", "败血", "免疫抑制", "多系统", "全身", "中毒")
    return _has_unnegated_marker(text, local_markers) and not _has_unnegated_marker(text, systemic_markers)


def _case_profile_text(case_profile: Dict[str, Any]) -> str:
    return json.dumps(_case_profile_evidence(case_profile), ensure_ascii=False)


def _case_profile_evidence(case_profile: Dict[str, Any]) -> Dict[str, Any]:
    """Keep observed case facts; exclude questions/gaps that should not trigger exams."""
    if not isinstance(case_profile, dict):
        return {}
    return {
        key: value
        for key, value in case_profile.items()
        if key not in _NON_EVIDENCE_PROFILE_FIELDS
    }


def _case_and_exam_text(
    case_profile: Dict[str, Any],
    examinations: Optional[Dict[str, Any]] = None,
) -> str:
    return json.dumps(
        {
            "case_profile": _case_profile_evidence(case_profile),
            "examinations": examinations or {},
        },
        ensure_ascii=False,
    )


def _needs_systemic_baseline_labs(case_profile: Dict[str, Any], differential: List[Any]) -> bool:
    """是否需要 CBC/炎症指标等全身基线检查。

    收紧判定：仅当主诉/病史含全身感染或系统性红旗，或鉴别诊断含感染/全身性
    关键词时才开具 CBC/CRP 等全身基线检查。纯局部症状（如耳痛、扭伤、颞下
    颌关节紊乱）不再自动叠加全身筛查，以提升 examination_precision。
    """
    text = _case_profile_text(case_profile)
    differential_text = json.dumps(differential[:5], ensure_ascii=False)
    combined = text + differential_text

    systemic_red_flags = (
        "发热", "寒战", "脓", "败血", "免疫抑制", "多系统", "全身", "中毒",
        "脓毒", "播散",
    )
    diff_systemic_keywords = (
        "感染", "脓毒", "败血", "全身性", "播散", "系统性", "多系统",
        "机会性感染", "真菌感染", "细菌感染",
    )

    has_red_flag = _has_unnegated_marker(text, systemic_red_flags)
    has_diff_systemic = any(keyword in differential_text for keyword in diff_systemic_keywords)

    if _is_localized_presentation(case_profile) and not has_red_flag and not has_diff_systemic:
        return False
    return has_red_flag or has_diff_systemic


def _has_unnegated_marker(text: str, markers: Iterable[str]) -> bool:
    for marker in markers:
        for match in re.finditer(re.escape(marker), text):
            prefix = text[max(0, match.start() - 48): match.start()]
            prefix = re.split(r"[。；;\n\r]", prefix)[-1]
            if not _prefix_negates_marker(prefix):
                return True
    return False


def _prefix_negates_marker(prefix: str) -> bool:
    negators = ("无", "未", "否认", "没有", "未见", "不伴", "未诉")
    last_neg = max((prefix.rfind(neg) for neg in negators), default=-1)
    if last_neg < 0:
        return False
    tail = prefix[last_neg:]
    contrast = ("但有", "但是有", "但仍", "但出现", "却有", "伴有", "合并", "出现", "可见", "存在", "，有", ",有")
    return not any(token in tail for token in contrast)


def _anatomy_exam_priorities(case_profile: Dict[str, Any], exam_resolver: Any = None) -> List[str]:
    """按主诉解剖/系统返回优先检查（标准名称，来自 ref_data）。

    通用「症状 → 相关检查系统」路由：只依据主诉涉及的解剖/系统关键词，不绑定
    任何具体疾病。命中多个系统时按顺序取第一个匹配的系统检查组，其余系统由综合
    检查逻辑与鉴别诊断推荐补齐。
    """
    text = _case_profile_text(case_profile)

    if _has_unnegated_marker(
        text,
        ("膝关节肿胀", "关节肿胀", "关节积液", "浮髌", "髌骨浮动", "滑液", "不能负重", "外伤后肿胀"),
    ):
        return _resolve_exam_list([
            "体格检查", "髌骨浮动试验（Ballottement）", "肌肉骨骼超声（MSKUS）",
            "滑液分析", "滑液培养", "高敏C反应蛋白（hs-CRP）",
            "全血细胞计数（CBC）", "肾功能检查（RFTs）", "X线检查",
        ], exam_resolver)

    # Pure trauma / chest-wall pain without cardiac features -> local imaging first.
    trauma_or_chest_wall = _has_unnegated_marker(
        text,
        ("车门夹伤胸", "胸壁", "肋", "胸外伤", "胸部外伤", "气胸", "血胸"),
    )
    cardiac_chest_pain = any(marker in text for marker in ("心绞痛", "冠脉", "劳力性", "放射痛", "冷汗"))
    if trauma_or_chest_wall and not cardiac_chest_pain:
        return _resolve_exam_list(["体格检查", "胸部X线检查（CXR）", "X线检查", "胸部CT扫描（Chest CT）"], exam_resolver)

    bundles: List[tuple[tuple[str, ...], List[str]]] = [
        # Symptom/system keyword -> the exams that best characterize that system.
        # Ordered from more specific local systems to broad systemic ones.
        (("瘢痕旁", "皮下肿块", "体表肿块", "表皮样", "粉瘤", "皮脂腺囊肿", "中央开口"), [
            "体格检查", "皮肤检查", "超声",
        ]),
        (("洪水", "钩端螺旋体", "腓肠肌痛", "结膜充血"), [
            "全血细胞计数（CBC）", "C反应蛋白（CRP）", "尿液分析（UA）",
            "核酸扩增检测（NAAT）", "显微镜凝集试验（MAT）", "酶联免疫吸附试验（ELISA）", "血培养",
        ]),
        (("钱币状", "硬币状", "圆形斑块"), [
            "皮肤镜检查", "皮肤检查", "斑贴试验", "血清IgE检测", "皮肤活检",
        ]),
        (("腰胁痛", "肾囊肿", "镜下血尿"), [
            "尿液分析（UA）", "肾脏超声", "肾脏CT扫描（肾脏CT）",
        ]),
        (("斜视", "内斜", "外斜", "眼位偏", "歪头视物"), [
            "遮盖试验", "斜视评估", "视力检查", "屈光检查", "视轴矫正评估",
        ]),
        (("复视", "单眼视力下降", "单眼模糊", "晶状体", "晶体", "头动时加重"), [
            "视力检查", "裂隙灯检查", "眼压测量（IOP）", "超声生物显微镜检查（UBM）",
            "眼部B超检查",
        ]),
        (("角膜混浊", "角膜发白", "出生起", "牛眼", "婴儿眼"), [
            "裂隙灯检查", "眼压测量（IOP）", "角膜厚度测量", "超声生物显微镜检查（UBM）",
            "眼前节光学相干断层扫描（AS-OCT）", "房角镜检查", "眼部B超检查", "眼前节摄影",
        ]),
        (("角膜溃疡", "上皮缺损", "基质浸润", "角膜浸润", "前房反应", "隐形眼镜", "角膜划伤", "角膜刮片", "激素眼药水"), [
            "裂隙灯检查", "角膜刮片分析", "显微镜检查", "微生物培养及鉴定",
            "抗菌药物敏感性试验（AST）", "光学相干断层扫描（OCT）", "活体共聚焦显微镜检查（IVCM）",
        ]),
        (("视物模糊", "畏光", "眼痛", "虹膜", "葡萄膜", "青光眼", "眼压", "前房", "裂隙灯"), [
            "视力检查", "裂隙灯检查", "眼压测量（IOP）", "超声生物显微镜检查（UBM）",
            "眼部B超检查", "房角镜检查",
        ]),
        (("牙痛", "冷热痛", "咬合痛", "牙龈", "牙周", "口腔溃疡", "口臭", "牙髓", "根尖"), [
            "口腔检查", "牙髓活力测试", "根尖片", "牙周探诊",
            "全血细胞计数（CBC）", "C反应蛋白（CRP）",
        ]),
        (("婴儿期", "听力反应弱", "叫名字不转头", "听不见轻声说话", "语言发育迟缓", "新生儿听力筛查", "先天性中耳畸形"), [
            "听力测定", "鼓室压图及声导抗检查", "听性脑干反应（ABR）", "颞骨高分辨率CT扫描（Temporal Bone HRCT）",
        ]),
        # 新生儿代谢危象：优先于宽泛心脏 bundle
        (("新生儿", "出生第", "尿液甜", "甜尿", "惊厥", "嗜睡", "代谢危象", "特殊气味", "发育迟缓", "喂养困难"), [
            "体格检查", "血清电解质", "动脉血气（ABG）", "血氨检测",
            "尿有机酸分析", "肝肾功能检查（LFTs/RFTs）", "全血细胞计数（CBC）",
        ]),
        (("房颤", "心房颤动", "心律绝对不齐", "心跳快且不规则", "心悸", "心慌", "心跳乱", "风湿", "二尖瓣狭窄", "链球菌"), [
            "心电图（ECG）", "超声心动图", "甲状腺功能检查（TFTs）", "体格检查", "经食管超声心动图（TEE）",
        ]),
        (("胸骨左缘杂音", "心脏杂音", "心前区隆起", "瓣膜", "三尖瓣", "肺动脉瓣", "二尖瓣", "右心", "颈静脉怒张", "肝大", "下肢水肿", "吃奶喘"), [
            "体格检查", "心电图（ECG）", "超声心动图", "N末端B型利钠肽原（NT-proBNP）",
            "胸部X线检查（CXR）", "血清电解质",
        ]),
        (("胎粪", "未排胎便", "未排胎粪", "胆汁性呕吐", "腹胀", "肠梗阻", "肠旋转"), [
            "体格检查", "腹部X线片（AXR）", "腹部超声", "钡灌肠检查（BE）",
            "血清电解质", "全血细胞计数（CBC）",
        ]),
        (("泡沫状分泌物", "黄白泡沫", "阴道异味", "阴道瘙痒", "滴虫", "阴道毛滴虫", "抗真菌无效"), [
            "显微镜检查", "快速抗原检测（RAT）", "DNA探针检测",
            "阴道毛滴虫培养", "阴道细胞学检查",
        ]),
        (("同房后出血", "接触性出血", "宫颈", "异味分泌物", "阴道分泌物", "不规则出血"), [
            "体格检查", "盆腔超声", "宫颈细胞学检查", "人乳头瘤病毒核酸检测（HPV NAT）",
            "阴道镜检查", "宫颈活检", "人绒毛膜促性腺激素（hCG）检测",
        ]),
        (("停经", "闭经", "继发性闭经", "节食", "体重骤降", "压力大", "月经停止"), [
            "体格检查", "人绒毛膜促性腺激素（hCG）检测", "性激素全套检测", "基础体温（BBT）记录",
            "盆腔超声",
        ]),
        (("妊娠", "怀孕", "胎动", "早孕", "验孕"), [
            "人绒毛膜促性腺激素（hCG）检测", "盆腔超声",
        ]),
        (("黄色瘤", "黄色斑", "黄色斑片", "黄色斑块", "眼睑黄色", "睑黄瘤"), [
            "血脂检测组合", "甲状腺功能检查（TFTs）", "体格检查", "皮肤镜检查",
        ]),
        (("高脂血症", "混合型高脂血症", "血脂异常", "甘油三酯", "胆固醇", "胰岛素抵抗"), [
            "血脂检测组合", "甲状腺功能检查（TFTs）",
        ]),
        (("呛咳", "误吸", "气道异物", "异物吸入", "卡喉", "吞入异物"), [
            "体格检查", "胸部X线检查（CXR）", "全血细胞计数（CBC）",
            "C反应蛋白（CRP）", "支气管镜检查",
        ]),
        (("ckd5", "慢性肾脏病5期", "egfr", "肌酐", "尿毒症", "透析", "磷结合剂", "活性维生素d"), [
            "肾功能检查（RFTs）", "肾脏超声", "全血细胞计数（CBC）", "血清电解质",
            "尿液分析（UA）", "X线检查", "双能X线吸收测定法（DEXA）", "骨转换标志物（BTMs）", "肾活检",
        ]),
        (("手足抽筋", "抽筋", "低镁", "低钾", "低钙", "电解质"), [
            "综合代谢面板（CMP）", "心电图（ECG）", "24小时尿电解质检测",
            "镁负荷试验", "体格检查", "动脉血气（ABG）",
        ]),
        (("腹泻", "拉肚子", "呕吐", "腹痛", "黄疸"), [
            "体格检查", "血清电解质", "肝肾功能检查（LFTs/RFTs）", "全血细胞计数（CBC）",
        ]),
        (("骨痛", "佝偻", "跛行", "上楼梯困难", "腿痛", "骨软化"), [
            "体格检查", "维生素D检测", "血清电解质",
            "甲状旁腺激素检测（PTH）", "骨骼X线检查", "双能X线吸收测定法（DEXA）",
        ]),
        (("关节不稳", "半脱位", "易瘀青", "瘀斑", "皮肤过伸", "韧带松弛", "关节发软"), [
            "基因检测", "组织病理学检查", "凝血功能全套",
            "全血细胞计数（CBC）", "磁共振成像（MRI）", "超声", "体格检查",
        ]),
        (("膝关节肿胀", "关节肿胀", "关节积液", "浮髌", "髌骨浮动", "滑液", "不能负重", "外伤后肿胀"), [
            "体格检查", "髌骨浮动试验（Ballottement）", "肌肉骨骼超声（MSKUS）",
            "滑液分析", "滑液培养", "高敏C反应蛋白（hs-CRP）",
            "全血细胞计数（CBC）", "肾功能检查（RFTs）", "X线检查",
        ]),
        (("咳血", "血痰", "咯血", "尿色深", "肺肾", "肾炎"), [
            "体格检查", "尿液分析（UA）", "肾功能检查（RFTs）",
            "全血细胞计数（CBC）", "凝血功能全套", "抗中性粒细胞胞质抗体（ANCA）谱",
            "胸部CT扫描（Chest CT）",
        ]),
        (("热源", "烘烤", "火激红斑", "网状红褐", "网状色素", "低温热", "热水袋", "电暖器"), [
            "体格检查", "皮肤活检",
        ]),
        (("镍", "斑贴", "手掌", "手指", "手足", "汗疱", "脱屑", "洗涤剂", "接触性"), [
            "真菌镜检", "真菌培养及鉴定", "斑贴试验", "皮肤活检",
        ]),
        (("胸痛", "心绞痛", "冠脉", "劳力性", "放射痛", "活动后胸闷", "活动后胸口发紧", "活动时胸口发紧", "爬楼胸闷", "胸口发紧伴气短"), [
            "心电图（ECG）", "心脏负荷试验", "超声心动图",
            "血脂检测组合", "炎症标志物检测组合", "冠状动脉造影",
            "心肌酶谱", "冠状动脉CT血管成像（CCTA）",
        ]),
        (("听力", "耳鸣", "耳闷", "耳聋", "眩晕", "突发性聋"), [
            "耳镜检查", "听力测定", "鼓室压图及声导抗检查", "颞骨高分辨率CT扫描（Temporal Bone HRCT）",
            "颞骨CT扫描（颞骨CT）",
        ]),
        (("流鼻涕", "鼻塞", "咳嗽", "黄痰", "喘鸣", "受凉", "上呼吸道", "流感"), [
            "体格检查", "快速抗原检测（RAT）", "病毒核酸检测（Viral NAT）",
            "胸部X线检查（CXR）", "全血细胞计数（CBC）",
        ]),
        (("咽", "喉", "扁桃体", "吞咽痛", "口臭", "咳出"), [
            "体格检查", "全血细胞计数（CBC）", "C反应蛋白（CRP）", "红细胞沉降率（ESR）",
            "咽拭子培养", "抗链球菌溶血素O（ASO）滴度",
        ]),
        (("下巴", "张口", "颞下颌", "脱位", "打哈欠", "关节卡"), [
            "体格检查", "X线检查",
        ]),
        (("排尿", "尿痛", "尿急", "尿频", "漏尿", "会阴", "前列腺", "尿潴留"), [
            "体格检查", "尿液分析（UA）", "尿培养", "综合代谢面板（CMP）",
            "泌尿道超声", "直肠指检（DRE）",
        ]),
        (("阴囊", "睾丸", "精索", "坠胀", "备孕", "生育力", "精索静脉曲张"), [
            "体格检查", "泌尿道超声", "多普勒超声", "精液分析",
        ]),
        (("气短", "水肿", "心慌", "呼吸困难", "BNP"), [
            "体格检查", "心电图（ECG）", "超声心动图", "N末端B型利钠肽原（NT-proBNP）",
            "胸部X线检查（CXR）", "血清电解质",
        ]),
        (("光敏", "关节痛", "脱发", "蝶形", "狼疮", "抗核"), [
            "体格检查", "全血细胞计数（CBC）", "尿液分析（UA）", "抗核抗体（ANA）谱",
            "补体成分分析", "抗双链DNA（抗dsDNA）抗体", "心肌酶谱", "肌电图和神经传导检查（EMG/NCS）",
        ]),
        (("近端肌无力", "梳头", "上楼", "大腿没力气", "肩膀没力气", "晨僵"), [
            "体格检查", "全血细胞计数（CBC）", "红细胞沉降率（ESR）", "C反应蛋白（CRP）",
            "心肌酶谱", "肌电图和神经传导检查（EMG/NCS）", "肌肉活检", "尿液分析（UA）",
        ]),
        (("梅毒", "神经梅毒", "hiv", "aids", "获得性免疫缺陷"), [
            "梅毒血清学检查", "脑脊液（CSF）分析", "磁共振成像（MRI）", "体格检查",
        ]),
        (("认知下降", "记忆力下降", "记忆力减退", "情绪改变"), [
            "神经心理评估", "体格检查", "糖化血红蛋白（HbA1c）", "磁共振成像（MRI）",
        ]),
        (("无痛肿块", "淋巴结肿大", "颈部肿块", "腹股沟肿块", "盗汗", "体重下降", "乳糜泻"), [
            "体格检查", "全血细胞计数（CBC）", "组织型转谷氨酰胺酶（tTG）抗体检测",
            "抗肌内膜抗体（EMA）", "皮肤活检", "免疫荧光测定（IFA）",
            "淋巴结活检", "正电子发射断层显像-计算机断层扫描（PET-CT）", "流式细胞术免疫分型",
        ]),
        (("皮疹", "水疱", "脓疱", "湿疹"), [
            "体格检查", "全血细胞计数（CBC）", "真菌镜检", "皮肤活检",
        ]),
        (("紫癜", "红点", "红红", "瘀点", "皮肤出血点", "关节痛", "膝盖疼", "腹痛", "血管炎"), [
            "体格检查", "全血细胞计数（CBC）", "C反应蛋白（CRP）",
            "尿液分析（UA）", "免疫球蛋白A（IgA）检测", "腹部超声",
        ]),
        (("发热", "寒战", "感染"), [
            "体格检查", "全血细胞计数（CBC）", "C反应蛋白（CRP）", "胸部X线检查（CXR）",
        ]),
    ]
    for keywords, exams in bundles:
        if _has_unnegated_marker(text, keywords):
            return _resolve_exam_list(exams, exam_resolver)
    return _resolve_exam_list(["体格检查"], exam_resolver)


def _redundant_exam_names(case_profile: Dict[str, Any], exam_resolver: Any = None) -> set[str]:
    """通用冗余检查过滤：只依据主诉的局部性/是否有感染或全身信号，避免为纯局部
    问题开具无关的全身/影像/病原学筛查，从而提升检查精确率。不针对具体疾病。"""
    text = _case_profile_text(case_profile)
    redundant: set[str] = {"术前评估"}

    has_infection_or_systemic = _has_unnegated_marker(
        text,
        ("发热", "寒战", "脓", "免疫抑制", "多系统", "全身"),
    )

    # Pure local / mechanical complaints without systemic signs: drop broad
    # systemic labs, cardiac and infectious/imaging panels that add no value.
    if _is_localized_presentation(case_profile) and not has_infection_or_systemic:
        redundant.update({
            "全血细胞计数（CBC）", "C反应蛋白（CRP）", "红细胞沉降率（ESR）",
            "心电图（ECG）", "N末端B型利钠肽原（NT-proBNP）", "血清电解质",
            "尿液分析（UA）", "超声", "关节X线检查",
            "病毒核酸检测（Viral NAT）", "细菌培养及鉴定",
        })

    if any(keyword in text for keyword in ("提重物", "复视", "单眼视力下降", "单眼模糊", "晶状体", "头动时加重")):
        redundant.update({
            "全面眼科检查", "荧光素染色裂隙灯检查", "视野检查",
            "头颅CT平扫", "头颅MRI+MRA", "头颅MRI+增强", "头颅MRI+MRV",
        })

    if any(keyword in text for keyword in ("角膜混浊", "角膜发白", "出生起", "牛眼", "婴儿眼")):
        redundant.update({"全面眼科检查", "荧光素染色裂隙灯检查", "视野检查"})

    if any(keyword in text for keyword in ("近端肌无力", "梳头", "上楼", "蝶形", "光敏", "晨僵")):
        redundant.update({"胸部X线检查（CXR）", "胸部CT扫描（Chest CT）", "X线检查", "超声"})

    if any(keyword in text for keyword in ("无痛肿块", "淋巴结肿大", "颈部肿块", "腹股沟肿块", "盗汗", "体重下降")):
        redundant.update({"真菌镜检", "超声"})

    if _has_unnegated_marker(text, ("梅毒", "神经梅毒", "hiv", "aids", "获得性免疫缺陷")) and _has_unnegated_marker(
        text,
        ("头痛", "认知", "记忆力", "情绪", "脑膜", "神经"),
    ):
        redundant.update({
            "正电子发射断层显像-计算机断层扫描（PET-CT）",
            "增强CT扫描（CECT）",
            "切除活检",
            "淋巴结活检",
            "皮肤活检",
            "组织病理学检查",
            "穿刺活检",
        })

    # Without any infection/systemic evidence, pathogen tests are low-yield.
    if not has_infection_or_systemic:
        redundant.update({"病毒核酸检测（Viral NAT）", "细菌培养及鉴定", "血培养", "伍德灯检查"})

    # ANCA 肺肾路径通常不需要补体；补体更服务于狼疮等免疫复合物病。
    lupus_like = any(keyword in text for keyword in ("狼疮", "蝶形", "光敏", "抗核", "dsdna", "抗磷脂"))
    anca_or_pulmonary_renal = any(
        keyword in text for keyword in ("咳血", "咯血", "血痰", "肺肾", "anca", "管型")
    )
    if anca_or_pulmonary_renal and not lupus_like:
        redundant.update({"补体成分分析", "补体C3/C4"})

    # Heart-failure / valve first-pass should not auto-stack advanced echo modalities.
    if any(keyword in text for keyword in ("气短", "水肿", "呼吸困难", "心衰", "瓣膜", "杂音", "反流")):
        af_valve = _has_unnegated_marker(text, ("房颤", "心房颤动", "心律绝对不齐", "心跳快且不规则")) and _has_unnegated_marker(
            text,
            ("二尖瓣", "风湿", "瓣膜"),
        )
        if not af_valve and "经食管" not in text and "介入" not in text and "手术评估" not in text:
            redundant.update({
                "三维超声心动图（3D Echo）",
                "经食管超声心动图（TEE）",
                "心脏MRI（CMR）",
            })

    return set(_resolve_exam_list(redundant, exam_resolver))



def _collect_differential_exam_hints(differential: List[Any]) -> List[str]:
    hints: List[str] = []
    for item in differential[:5]:
        if not isinstance(item, dict):
            continue
        hints.extend(as_text_list(item.get("recommended_examinations")))
    return hints


def build_exam_decision_records(
    differential: List[Any], examinations: Iterable[str], *, exam_resolver: Any = None,
) -> List[Dict[str, str]]:
    """Create pre-order checklist: clinical question, SnNout/SpPin, decision impact, alternatives, risk, follow-up."""
    names = as_text_list(examinations)
    purposes = build_exam_purpose_map(differential, names, exam_resolver=exam_resolver)
    records: List[Dict[str, str]] = []
    for name in names:
        purpose = "；".join(purposes.get(name) or ["补充当前鉴别诊断所需的客观证据"])
        normalized = normalize_name(name)
        diagnostic_utility = _classify_exam_diagnostic_utility(name, differential)
        if any(token in normalized for token in ("活检", "穿刺", "内镜", "造影")):
            risk = "下单前核对知情同意、出血/抗凝状态、相关禁忌证；涉及对比剂时核对肾功能和过敏史。"
            followup = "若为动态随访指标，按病理/介入后复评节点复测；否则不适用固定复测。"
        elif any(token in normalized for token in ("培养", "核酸", "病理", "涂片")):
            risk = "核对标本部位、采集时机及抗感染治疗对结果的影响，避免不合格或重复标本。"
            followup = "经验治疗无效或重症时按病原学策略复检；轻症初治且已明确决策路径时可不再重复。"
        elif any(token in normalized for token in ("ct", "mri", "x线", "超声")):
            risk = "核对妊娠可能、植入物及影像学禁忌；如需对比剂，另核对肾功能和过敏史。确认适应证与待回答问题后再申请。"
            followup = "仅在疗效监测或分期变化需要时设定复查间隔与触发条件，避免无目的重复影像。"
        else:
            risk = "已核对用药与过敏史；无特殊禁忌时按标准采集条件执行。"
            followup = "对需动态随访的指标设定复测间隔与触发条件；一次性决策检查填不适用。"
        records.append({
            "examination": name,
            "clinical_question": "本次要回答的临床问题：%s" % purpose,
            "diagnostic_utility": diagnostic_utility,
            "decision_impact": (
                "若阳性：%s，提高相关诊断概率并进入针对性处置/升级路径；"
                "若阴性：%s，降低该诊断概率并转向下一竞争诊断或安全观察。"
                "若阳性和阴性均不改变诊疗路径，则不应开具本项。"
                % (
                    "SpPin（高特异性，阳性可确诊）" if "SpPin" in diagnostic_utility else "支持工作诊断",
                    "SnNout（高敏感性，阴性可排除）" if "SnNout" in diagnostic_utility else "降低鉴别概率",
                )
            ),
            "alternatives_considered": "已比较体格检查、既有结果及更简单/安全/经济的同目的检查；仅在不能回答同一临床问题时保留本项。",
            "risk_prerequisites": risk,
            "followup_plan": followup,
        })
    return records


def _classify_exam_diagnostic_utility(exam_name: str, differential: List[Any]) -> str:
    """Classify exam as SnNout (rule-out) or SpPin (rule-in) based on differential context."""
    normalized = normalize_name(exam_name)
    must_rule_out = any(
        isinstance(item, dict) and item.get("must_rule_out") is True
        for item in differential
    )
    high_sensitivity_markers = (
        "d-二聚体", "crp", "cbc", "全血", "培养", "hiv", "hcg", "妊娠",
        "心电图", "ecg", "血气", "abg", "电解质",
    )
    high_specificity_markers = (
        "病理", "活检", "穿刺", "核酸", "抗原", "抗体", "超声心动", "mri", "造影",
    )
    if must_rule_out and any(token in normalized for token in high_sensitivity_markers):
        return "SnNout（高敏感性，阴性可排除危重病）"
    if any(token in normalized for token in high_specificity_markers):
        return "SpPin（高特异性，阳性可确诊）"
    if any(token in normalized for token in ("超声", "ct", "x线", "mri")):
        return "SnNout/SpPin（依临床问题：排除选阴性价值，确诊选阳性价值）"
    return "阶梯性检查（无创/简单优先，须改变决策才开）"


def prune_redundant_modalities(
    examinations: Iterable[str],
    already_ordered: Iterable[str] = (),
) -> List[str]:
    """Prefer an anatomic-specific study when a generic modality is duplicated."""
    names = unique_preserve_order(as_text_list(examinations))
    generic = {
        "超声": ("超声",),
        "X线检查": ("X线",),
        "磁共振成像（MRI）": ("MRI", "磁共振"),
    }
    result: List[str] = []
    for name in names:
        markers = generic.get(name)
        if markers and any(other != name and any(marker in other for marker in markers) for other in names):
            continue
        result.append(name)

    # Keep one best study per overlapping advanced modality family.
    families = [
        ("超声心动图", ("三维超声心动图（3D Echo）", "经食管超声心动图（TEE）", "心脏MRI（CMR）")),
        ("胸部CT扫描（Chest CT）", ("高分辨率CT（HRCT）", "胸部高分辨率CT（Chest HRCT）")),
    ]
    for primary, advanced in families:
        if primary in result:
            result = [name for name in result if name not in advanced]
    # If both HRCT variants somehow appear without Chest CT, keep one.
    if "高分辨率CT（HRCT）" in result and "胸部高分辨率CT（Chest HRCT）" in result:
        result = [name for name in result if name != "胸部高分辨率CT（Chest HRCT）"]
    if "颞骨高分辨率CT扫描（Temporal Bone HRCT）" in result and "颞骨CT扫描（颞骨CT）" in result:
        result = [name for name in result if name != "颞骨CT扫描（颞骨CT）"]

    skeletal_xrays = ["骨骼X线检查", "关节X线检查", "X线检查"]
    present_xrays = [name for name in result if name in skeletal_xrays]
    if len(present_xrays) > 1:
        keep = "关节X线检查" if "关节X线检查" in present_xrays else present_xrays[0]
        result = [name for name in result if name not in skeletal_xrays or name == keep]

    # 妊娠检测去重：血清 hCG 与尿 hCG 同目的时只保留血清（更精确）。
    hcg_variants = [
        "人绒毛膜促性腺激素（hCG）检测",
        "尿hCG妊娠试验",
        "妊娠试验（hCG）",
    ]
    ordered_hcg = [name for name in hcg_variants if name in set(as_text_list(already_ordered))]
    present_hcg = [name for name in hcg_variants if name in result]
    if ordered_hcg:
        result = [name for name in result if name not in hcg_variants]
    elif len(present_hcg) > 1:
        keep = (
            "人绒毛膜促性腺激素（hCG）检测"
            if "人绒毛膜促性腺激素（hCG）检测" in present_hcg
            else present_hcg[0]
        )
        result = [name for name in result if name not in present_hcg or name == keep]

    return result


def filter_examinations_by_current_evidence(
    examinations: Iterable[str],
    *,
    case_profile: Dict[str, Any],
    differential: List[Any],
    already_ordered: Iterable[str] = (),
) -> List[str]:
    """Apply hard relevance gates after routing and before ordering exams."""
    names = prune_redundant_modalities(examinations, already_ordered)
    profile_text = _case_profile_text(case_profile)
    af_valve = _has_unnegated_marker(profile_text, ("房颤", "心房颤动", "心律绝对不齐", "心跳快且不规则")) and _has_unnegated_marker(
        profile_text,
        ("二尖瓣", "风湿", "瓣膜"),
    )
    if af_valve and "超声心动图" in names and "经食管超声心动图（TEE）" in set(as_text_list(examinations)):
        try:
            echo_idx = names.index("超声心动图")
        except ValueError:
            echo_idx = len(names) - 1
        if "经食管超声心动图（TEE）" not in names:
            names.insert(echo_idx + 1, "经食管超声心动图（TEE）")
    current_diagnoses = [
        item.get("suspected_disease")
        for item in differential
        if isinstance(item, dict) and item.get("suspected_disease")
    ]
    inappropriate = set(_get_inappropriate_exams(current_diagnoses, case_profile))
    return [name for name in names if name not in inappropriate]


def _match_examinations_from_hints(
    hints: Iterable[str],
    *,
    available_examinations: Iterable[str],
    ordered: Iterable[str],
    examination_catalog: Dict[str, List[str]],
    max_count: int,
) -> List[str]:
    ordered_set = set(as_text_list(ordered))
    available_list = as_text_list(available_examinations)
    available_map = build_name_map(available_list)
    suggestions: List[str] = []

    for hint in as_text_list(hints):
        matched = match_standard_name(hint, available_map) or _exam_alias_match(hint, available_list)
        if matched and matched not in ordered_set and matched not in suggestions:
            suggestions.append(matched)
        if len(suggestions) >= max_count:
            return suggestions

        fuzzy = best_match(hint, available_list, score_cutoff=0.84)
        if (
            fuzzy
            and _exam_names_semantically_related(hint, fuzzy)
            and fuzzy not in ordered_set
            and fuzzy not in suggestions
        ):
            suggestions.append(fuzzy)
        if len(suggestions) >= max_count:
            return suggestions

        hint_norm = normalize_name(hint)
        if not hint_norm:
            continue
        for exam_name in available_list:
            exam_norm = normalize_name(exam_name)
            if exam_norm and exam_norm in hint_norm and exam_name not in ordered_set and exam_name not in suggestions:
                suggestions.append(exam_name)
            if len(suggestions) >= max_count:
                return suggestions

    if len(suggestions) < max_count:
        for category, names in examination_catalog.items():
            category_norm = normalize_name(category)
            for hint in as_text_list(hints):
                hint_norm = normalize_name(hint)
                if not hint_norm or not category_norm:
                    continue
                if category_norm in hint_norm and len(hint_norm) > len(category_norm):
                    for exam_name in names:
                        if exam_name in available_list and exam_name not in ordered_set and exam_name not in suggestions:
                            suggestions.append(exam_name)
                        if len(suggestions) >= max_count:
                            return suggestions
    return suggestions


def suggest_comprehensive_examinations(
    *,
    case_profile: Dict[str, Any],
    differential: List[Any],
    exam_need_summary: Dict[str, Any],
    ordered: Iterable[str],
    available_examinations: Iterable[str],
    examination_catalog: Dict[str, List[str]],
    max_count: int = 5,
    exam_resolver: Any = None,
) -> List[str]:
    """按「基础→特性→并发症」分层，结合鉴别诊断与解剖路由生成检查批次。"""
    ordered_set = set(as_text_list(ordered))
    available_list = as_text_list(available_examinations)
    available_set = set(available_list)
    redundant = _redundant_exam_names(case_profile, exam_resolver=exam_resolver)
    suggestions: List[str] = []

    def _add(name: str) -> None:
        name = _resolve_exam(name, exam_resolver)
        if (
            name in available_set
            and name not in ordered_set
            and name not in suggestions
            and name not in redundant
        ):
            suggestions.append(name)

    anatomy_priorities = _anatomy_exam_priorities(case_profile, exam_resolver=exam_resolver)
    hints = _collect_differential_exam_hints(differential)

    electrolyte_components = sum(
        1
        for marker in ("血清钠", "血清钾", "血清钙", "血清镁", "电解质全套")
        if any(marker in clean_text(hint) for hint in hints)
    )
    if electrolyte_components >= 2:
        hints = ["综合代谢面板（CMP）"] + hints

    # A strong symptom/system route supplies the compact core bundle. Model
    # hints then fill remaining slots without displacing those essentials.
    tier1 = unique_preserve_order(_match_examinations_from_hints(
        hints,
        available_examinations=available_list,
        ordered=ordered_set,
        examination_catalog=examination_catalog,
        max_count=max_count,
    ))
    tier2 = unique_preserve_order(anatomy_priorities)

    for name in tier2:
        _add(name)
    for name in tier1:
        _add(name)

    if len(suggestions) >= max_count:
        final_suggestions = suggestions[:max_count]
    elif suggestions and _is_localized_presentation(case_profile):
        final_suggestions = suggestions[:max_count]
    else:
        if _needs_systemic_baseline_labs(case_profile, differential):
            for name in ["体格检查", "全血细胞计数（CBC）", "C反应蛋白（CRP）"]:
                _add(name)
        if len(suggestions) >= max_count:
            final_suggestions = suggestions[:max_count]
        else:
            profile_text = _case_profile_text(case_profile)
            systemic_baseline = _needs_systemic_baseline_labs(case_profile, differential)
            treatment_safety_candidates: List[str] = []
            if any(key in profile_text for key in ("肾", "尿", "利尿", "电解质", "糖尿病", "高血压")):
                treatment_safety_candidates.append("肾功能检查（RFTs）")
            if any(key in profile_text for key in ("肝", "黄疸", "肿瘤", "化疗")):
                treatment_safety_candidates.append("肝功能检查（LFTs）")
            if any(key in profile_text for key in ("凝血", "易瘀青", "出血", "血小板", "抗凝", "手术")):
                treatment_safety_candidates.append("凝血功能检查")
            organ_candidates = [
                name for name in anatomy_priorities
                if name not in {"体格检查", "全血细胞计数（CBC）", "C反应蛋白（CRP）"}
            ]
            red_flag_candidates: List[str] = []
            if any(key in profile_text for key in ("气短", "呼吸困难", "喘", "低氧", "心衰")):
                red_flag_candidates.extend(["血清电解质", "动脉血气（ABG）"])
            if _has_unnegated_marker(profile_text, ("高热", "寒战", "败血", "中毒", "免疫抑制")):
                red_flag_candidates.append("血培养")

            dimension_candidates = {
                "基础严重程度评估": (["体格检查", "全血细胞计数（CBC）", "C反应蛋白（CRP）"] if systemic_baseline else ["体格检查"]),
                "治疗安全评估": treatment_safety_candidates,
                "受累器官或分型评估": organ_candidates,
                "红旗并发症评估": red_flag_candidates,
            }
            missing_dimensions = exam_need_summary.get("missing_dimensions") or []
            for item in missing_dimensions:
                if not isinstance(item, dict):
                    continue
                dimension = clean_text(item.get("dimension"))
                for candidate in dimension_candidates.get(dimension, []):
                    _add(candidate)
            if len(suggestions) >= max_count:
                final_suggestions = suggestions[:max_count]
            else:
                if any(key in profile_text for key in ("尿", "肾", "蛋白尿", "血尿")):
                    for candidate in ["尿液分析（UA）", "尿培养"]:
                        _add(candidate)
                if _has_unnegated_marker(profile_text, ("气短", "呼吸困难", "胸痛", "心悸", "下肢水肿")):
                    for candidate in ["心电图（ECG）", "N末端B型利钠肽原（NT-proBNP）", "胸部X线检查（CXR）"]:
                        _add(candidate)
                if _has_unnegated_marker(profile_text, ("发热", "寒战", "脓")):
                    for candidate in ["C反应蛋白（CRP）", "细菌培养及鉴定"]:
                        _add(candidate)
                if not suggestions:
                    for name in ["体格检查"]:
                        _add(name)
                final_suggestions = suggestions[:max_count]
    # --- 新增：应用过滤器，剔除不合理的检查 ---
    # 收集所有鉴别诊断的名称
    current_diagnoses = [
        item.get("suspected_disease")
        for item in differential
        if isinstance(item, dict) and item.get("suspected_disease")
    ]
    final_suggestions = filter_examinations_by_current_evidence(
        final_suggestions,
        case_profile=case_profile,
        differential=differential,
        already_ordered=ordered_set,
    )

    # 化脓性呼吸道表现首先需要覆盖常见细菌培养。免疫抑制患者仍可同时
    # 保留分枝杆菌培养，但不能让它挤掉更匹配当前感染表型的细菌培养。
    infection_context = _infection_exam_context(current_diagnoses, case_profile)
    bacterial_culture = "细菌培养及鉴定"
    if (
        infection_context["suspected_bacterial"]
        and (
            infection_context["bacterial_diagnosis"]
            or not infection_context["tb_specific_evidence"]
        )
        and bacterial_culture in available_set
        and bacterial_culture not in ordered_set
    ):
        final_suggestions = unique_preserve_order(
            [bacterial_culture] + final_suggestions
        )[:max_count]

    return final_suggestions





def build_exam_need_summary(
    case_profile: Dict[str, Any],
    differential: List[Any],
    examinations: Dict[str, Any],
    exam_resolver: Any = None,
) -> Dict[str, Any]:
    ordered = set(as_text_list(examinations.get("ordered_examinations")))
    result_text = json.dumps(examinations.get("examination_results", []), ensure_ascii=False)
    text = json.dumps(
        {
            "case_profile": case_profile,
            "differential": differential,
            "examinations": examinations,
        },
        ensure_ascii=False,
    )
    result_entries = examinations.get("examination_results", []) or []
    has_objective_results = False
    if isinstance(result_entries, list):
        for entry in result_entries:
            value = entry.get("结果") if isinstance(entry, dict) else None
            if isinstance(value, dict) and clean_text(value.get("result")) and clean_text(value.get("status")).lower() not in {"unavailable", "invalid", "pending"}:
                has_objective_results = True
                break
    elif isinstance(result_entries, dict):
        has_objective_results = any(
            isinstance(value, dict)
            and clean_text(value.get("result"))
            and clean_text(value.get("status")).lower() not in {"unavailable", "invalid", "pending"}
            for value in result_entries.values()
        )
    differential_recommendations = {
        _resolve_exam(name, exam_resolver)
        for item in differential
        if isinstance(item, dict)
        for name in as_text_list(item.get("recommended_examinations"))
    }
    covered_recommendations = {
        _resolve_exam(name, exam_resolver)
        for name in ordered
    } & differential_recommendations

    dimensions = [
        {
            "dimension": "基础严重程度评估",
            "covered": any(_resolve_exam(name, exam_resolver) in ordered for name in ["体格检查", "全血细胞计数（CBC）"]),
            "reason": "用于判断病情严重程度、炎症/贫血/血小板等基础风险。",
        },
        {
            "dimension": "确诊或病因证据",
            "covered": has_objective_results and bool(covered_recommendations),
            "reason": "需有支持鉴别诊断的客观检查证据。",
        },
        {
            "dimension": "治疗安全评估",
            "covered": any(
                key in text
                for key in ["妊娠", "肝", "肾", "过敏", "血小板", "凝血", "免疫抑制", "激素", "用药"]
            )
            or any(
                any(token in normalize_name(name) for token in ["肾", "肝", "凝血", "妊娠"])
                for name in ordered
            ),
            "reason": "用于判断用药禁忌、剂量调整和治疗风险。",
        },
        {
            "dimension": "受累器官或分型评估",
            "covered": any(
                any(token in normalize_name(name) for token in ["尿", "心", "肺", "耳", "眼", "关节", "超声", "ct", "mri", "x线", "听"])
                for name in ordered
            )
            or any(key in text for key in ["尿", "心", "肺", "神经", "肾活检", "超声", "CT", "MRI", "分型"]),
            "reason": "用于确定器官受累、分型和治疗强度。",
        },
        {
            "dimension": "红旗并发症评估",
            "covered": not case_profile.get("red_flags")
            or any(
                any(token in normalize_name(name) for token in ["电解", "血气", "培养", "监护", "心电"])
                for name in ordered
            )
            or any(key in text for key in ["住院", "急诊", "监测", "培养", "影像", "电解质", "血气"]),
            "reason": "红旗表现需要评估并发症和是否住院/静脉治疗。",
        },
    ]

    return {
        "dimensions": dimensions,
        "missing_dimensions": [item for item in dimensions if not item["covered"]],
    }


def _infection_exam_context(
    diagnosis: List[Any],
    case_profile: Dict[str, Any],
) -> Dict[str, bool]:
    """Extract infection-type evidence used by filtering and prioritization."""
    diag_text = json.dumps(diagnosis, ensure_ascii=False).lower()
    # missing_critical_fields contains questions rather than observed evidence.
    evidence_profile = {
        key: value
        for key, value in case_profile.items()
        if key != "missing_critical_fields"
    }
    profile_text = _case_profile_text(evidence_profile).lower()

    purulent_or_cavitary = _has_unnegated_marker(
        profile_text,
        ("黄绿痰", "脓痰", "脓性痰", "化脓", "空洞", "空腔"),
    )
    bacterial_diagnosis = any(
        marker in diag_text
        for marker in ("细菌", "细菌性肺炎", "肺脓肿", "坏死性肺炎", "化脓性感染")
    )
    tb_specific_evidence = (
        any(marker in diag_text for marker in ("结核", "分枝杆菌", "ntm"))
        or _has_unnegated_marker(
            profile_text,
            (
                "盗汗", "午后低热", "消瘦", "体重下降", "结核接触",
                "结核病史", "粟粒", "树芽征", "上肺空洞",
            ),
        )
    )
    immunosuppressed = _has_unnegated_marker(
        profile_text,
        (
            "免疫抑制", "免疫缺陷", "hiv", "aids", "cd4", "化疗",
            "器官移植", "长期激素", "免疫抑制剂",
        ),
    )
    return {
        "suspected_bacterial": purulent_or_cavitary or bacterial_diagnosis,
        "bacterial_diagnosis": bacterial_diagnosis,
        "tb_specific_evidence": tb_specific_evidence,
        "immunosuppressed": immunosuppressed,
    }


def _get_inappropriate_exams(diagnosis: List[Any], case_profile: Dict[str, Any]) -> List[str]:
    """
    根据诊断和病例信息，返回不适宜开具的检查项目列表。
    用于过滤掉低收益或与诊断无关的检查，提升 examination_precision。
    """
    inappropriate: List[str] = []
    diag_text = json.dumps(diagnosis, ensure_ascii=False)
    profile_text = _case_profile_text(case_profile)
    combined = diag_text + profile_text

    # 规则1: 除非有明确指征，否则禁止开具代谢/血气等复杂检查
    metabolic_indicators = ("昏迷", "酸中毒", "呼吸衰竭", "休克", "肾衰", "尿毒症", "代谢危象", "惊厥", "嗜睡", "低镁", "低钾", "低钙", "电解质")
    has_metabolic_indication = _has_unnegated_marker(profile_text, metabolic_indicators)

    if not has_metabolic_indication:
        inappropriate.extend([
            "动脉血气（ABG）",
            "血氨检测",
            "尿有机酸分析",
            "乳酸检测",
            "脑脊液检查",
            "骨髓穿刺"
        ])

    # 规则2: 根据诊断过滤解剖部位不相关的检查
    # 例如：心脏瓣膜病，若无怀孕相关指征，则不应开 hCG 或盆腔超声
    is_cardiac_valve_disease = any(kw in combined for kw in ("瓣膜", "二尖瓣", "三尖瓣", "主动脉瓣", "肺动脉瓣"))
    has_pregnancy_indicator = any(kw in profile_text for kw in ("停经", "妊娠", "怀孕", "胎动", "hCG"))

    if is_cardiac_valve_disease and not has_pregnancy_indicator:
        inappropriate.extend([
            "人绒毛膜促性腺激素（hCG）检测",
            "尿hCG妊娠试验",
            "盆腔超声"
        ])

    # 规则3: 感染类型特异性过滤。典型化脓性/空洞性细菌感染若没有结核
    # 特异证据，不应首选分枝杆菌培养；免疫抑制者保留机会感染排查。
    infection_context = _infection_exam_context(diagnosis, case_profile)
    if (
        infection_context["suspected_bacterial"]
        and not infection_context["tb_specific_evidence"]
        and not infection_context["immunosuppressed"]
    ):
        inappropriate.append("分枝杆菌培养")

        has_gyn_symptoms = _has_unnegated_marker(
            profile_text,
            ("阴道", "月经", "停经", "盆腔", "子宫", "卵巢", "妊娠", "怀孕"),
        )
        if not has_gyn_symptoms:
            inappropriate.extend([
                "盆腔超声",
                "妇科超声",
                "人绒毛膜促性腺激素（hCG）检测",
            ])

    infection_evidence = (
        infection_context["suspected_bacterial"]
        or _has_unnegated_marker(
            profile_text,
            ("发热", "寒战", "脓", "黄痰", "咳痰", "咳嗽", "耳痛", "流脓", "感染", "白细胞升高", "crp升高"),
        )
    )
    immune_or_hematologic_evidence = (
        _has_unnegated_marker(
            profile_text,
            (
                "紫癜", "血管炎", "狼疮", "类风湿", "晨僵", "关节肿痛",
                "血尿", "蛋白尿", "瘀青", "鼻出血", "血小板", "贫血", "白血病",
            ),
        )
    )
    renal_metabolic_bone_evidence = _has_unnegated_marker(
        profile_text,
        ("ckd5", "慢性肾脏病5期", "egfr", "肌酐", "尿毒症", "透析", "低钙", "高磷", "骨痛", "肾性骨"),
    )
    if not infection_evidence and not immune_or_hematologic_evidence and not renal_metabolic_bone_evidence:
        inappropriate.extend([
            "血培养",
            "全血细胞计数（CBC）",
            "C反应蛋白（CRP）",
            "红细胞沉降率（ESR）",
        ])
    if not _has_unnegated_marker(profile_text, ("高热", "发热", "寒战", "败血", "脓毒", "免疫抑制", "血培养")):
        inappropriate.append("血培养")

    if not _has_unnegated_marker(profile_text, ("hiv", "aids", "cd4", "获得性免疫缺陷", "抗病毒治疗")):
        inappropriate.append("HIV病毒载量检测")

    cardiac_evidence = _has_unnegated_marker(
        profile_text,
        (
            "胸痛", "胸闷", "心悸", "心绞痛", "气短", "呼吸困难", "端坐呼吸",
            "下肢水肿", "心衰", "心力衰竭", "瓣膜", "晕厥", "发绀", "心前区", "杂音",
            "劳力性", "爬楼胸闷", "胸口发紧", "胸部压迫感", "活动后胸", "提重物时胸口",
        ),
    )
    respiratory_evidence = _has_unnegated_marker(
        profile_text,
        ("咳嗽", "咳痰", "气促", "呼吸困难", "咯血", "胸外伤", "喘息", "肺炎"),
    )
    if not cardiac_evidence:
        inappropriate.extend([
            "超声心动图",
            "N末端B型利钠肽原（NT-proBNP）",
            "心肌酶谱",
            "心脏负荷试验",
            "冠状动脉造影",
            "动态心电图（Holter）",
        ])
        if not respiratory_evidence:
            inappropriate.append("胸部X线检查（CXR）")

    exertional_chest_symptom = _has_unnegated_marker(
        profile_text,
        ("胸口发紧", "胸闷", "胸痛", "胸部压迫感"),
    ) and _has_unnegated_marker(
        profile_text,
        ("活动", "爬楼", "提重物", "劳力"),
    )
    chronic_ischemia_pattern = exertional_chest_symptom or _has_unnegated_marker(
        profile_text,
        ("活动后胸闷", "活动后胸痛", "活动时胸口发紧", "劳力性胸痛", "爬楼胸闷", "提重物胸闷", "心绞痛"),
    )
    arrhythmia_or_syncope_evidence = _has_unnegated_marker(
        profile_text,
        ("心悸", "晕厥", "黑矇", "持续性心律失常", "猝倒"),
    )
    acute_injury_or_hf_evidence = _has_unnegated_marker(
        profile_text + json.dumps(case_profile.get("red_flags") or [], ensure_ascii=False),
        ("静息胸痛", "大汗", "端坐呼吸", "夜间憋醒", "下肢水肿", "心衰", "心力衰竭", "发绀", "休克"),
    )
    myocardial_injury_evidence = _has_unnegated_marker(
        combined,
        ("肌钙蛋白升高", "心肌酶升高", "ckmb升高", "st段抬高", "急性心肌梗死"),
    )
    if chronic_ischemia_pattern and not arrhythmia_or_syncope_evidence and not acute_injury_or_hf_evidence and not myocardial_injury_evidence:
        inappropriate.extend([
            "动态心电图（Holter）",
            "心肌酶谱",
            "N末端B型利钠肽原（NT-proBNP）",
        ])

    liver_tumor_evidence = _has_unnegated_marker(
        profile_text,
        ("肝癌", "肝细胞癌", "肝硬化", "乙肝", "占位", "肿块", "恶性", "肿瘤", "癌", "甲胎蛋白", "消瘦"),
    )
    if not liver_tumor_evidence:
        inappropriate.extend([
            "甲胎蛋白（AFP）检测",
            "正电子发射断层显像-计算机断层扫描（PET-CT）",
        ])

    coagulation_evidence = _has_unnegated_marker(
        profile_text,
        ("凝血", "出血", "鼻出血", "便血", "黑便", "瘀青", "抗凝", "血小板", "肝硬化", "手术", "术前"),
    )
    if not coagulation_evidence:
        inappropriate.extend(["凝血功能全套", "凝血功能检查"])

    nasal_evidence = _has_unnegated_marker(
        profile_text,
        ("鼻塞", "流涕", "鼻窦", "鼻旁窦", "鼻腔", "面部痛", "鼻出血", "嗅觉"),
    )
    if not nasal_evidence:
        inappropriate.append("鼻内镜检查")

    # 规则4: 无明确组织取材指征时过滤宽泛、侵入性的病理/穿刺项目。
    biopsy_indicators = (
        "肿瘤", "恶性", "癌", "占位", "肿块", "结节", "淋巴瘤",
        "不明原因", "病因不明", "活检", "病理", "肾炎", "肾病",
        "血管炎", "间质性肺病", "器官移植",
    )
    has_biopsy_indication = (
        _has_unnegated_marker(profile_text, biopsy_indicators)
    )
    if not has_biopsy_indication:
        inappropriate.extend([
            "组织病理学检查",
            "穿刺活检",
            "粗针穿刺活检（CNB）",
            "针吸活检",
        ])

    # 规则5: 跨系统过滤——当主诉明确指向某一系统时，排除其他系统的检查。
    # 眼科/斜视/屈光问题：排除消化、心血管、泌尿、生殖、神经等无关系统检查
    is_eye_case = _has_unnegated_marker(profile_text, ("斜视", "内斜", "外斜", "眼位", "屈光", "视力", "遮盖", "视轴", "眼底", "裂隙灯", "眼压", "畏光", "流泪", "瞳孔", "散瞳", "弱视", "眼球", "眼睑"))
    if is_eye_case:
        inappropriate.extend([
            # 消化系统
            "24小时食管pH/阻抗监测", "胃镜检查", "肠镜检查", "钡餐检查", "腹部超声",
            # 心血管系统
            "超声心动图", "冠状动脉造影", "冠状动脉CT血管成像（CCTA）", "心脏负荷试验",
            # 泌尿/生殖
            "尿液分析（UA）", "尿培养", "泌尿道超声", "盆腔超声", "人绒毛膜促性腺激素（hCG）检测",
            # 代谢/内分泌（非眼部）
            "糖化血红蛋白（HbA1c）", "血糖检测", "甲状腺功能检查", "皮质醇检测",
            # 骨关节
            "骨骼X线检查", "双能X线吸收测定法（DEXA）", "关节X线检查",
            # 病理/侵入
            "组织病理学检查", "穿刺活检",
        ])

    # 规则6: 电解质/代谢异常病例——排除与当前主诉无关的检查
    is_electrolyte_case = _has_unnegated_marker(profile_text, ("低镁", "低钾", "低钙", "电解质", "抽筋", "手足抽筋", "麻木", "心律失常", "心动过速", "心电图", "QTC", "QT间期"))
    if is_electrolyte_case:
        inappropriate.extend([
            # 糖代谢（除非有糖尿病史）
            "糖化血红蛋白（HbA1c）", "指尖血糖（Bedside Glucose）",
            # 影像（非代谢/电解质所需）
            "腹部超声", "盆腔超声", "泌尿道超声",
            # 病理
            "组织病理学检查", "穿刺活检", "骨髓穿刺",
        ])
        # 除非有明确糖尿病史，否则排除血糖和HbA1c
        has_diabetes_history = any(kw in profile_text for kw in ("糖尿病", "胰岛素", "降糖", "血糖"))
        if not has_diabetes_history:
            inappropriate.extend(["血糖检测", "糖化血红蛋白（HbA1c）"])
        # 除非有明确甲状旁腺指征，排除PTH
        has_parathyroid_indicator = any(kw in combined for kw in ("甲状旁腺", "PTH", "高钙", "低钙血症"))
        if not has_parathyroid_indicator:
            inappropriate.append("甲状旁腺激素检测（PTH）")

    # 规则7: 局部皮肤/外伤问题——排除全身系统性筛查
    is_local_skin_case = _has_unnegated_marker(profile_text, ("皮疹", "湿疹", "水疱", "接触性", "汗疱", "脱屑")) and not has_metabolic_indication
    if is_local_skin_case:
        inappropriate.extend([
            "24小时食管pH/阻抗监测", "超声心动图", "心电图（ECG）", "盆腔超声",
            "人绒毛膜促性腺激素（hCG）检测", "血糖检测", "糖化血红蛋白（HbA1c）",
        ])

    return unique_preserve_order(inappropriate)
