"""Deterministic workflow planning for the doctor agent."""

from __future__ import annotations

import json
from enum import Enum
from typing import Any, Dict, List, Optional

from .examiner import build_exam_need_summary
from .utils import as_text_list, clean_text, normalize_name


class WorkflowStage(str, Enum):
    """The only permitted clinical workflow transitions."""

    CONSULT = "consult"
    EXAMINE = "examine"
    DIAGNOSE = "diagnose"


# 首轮按条目一次问齐，减少第二轮补问。
OPENING_CONSULTATION_QUESTION = (
    "请按下面几点一次说完，不必等我再追问："
    "1）今天为什么来看病、最主要不适从何时开始、怎么变化、为何现在就诊；"
    "2）最疼或最难受的具体部位、诱因、活动是否受限；"
    "3）既往慢性病/手术，以及目前全部药物（处方药、非处方药、保健品/中草药、激素/免疫抑制剂）和药物过敏史；育龄者请同时说明月经或妊娠可能；"
    "4）有无突然加重、昏厥、呼吸困难或出血；您现在最担心什么。"
)


# 普通病例只把用药安全当硬门槛；复杂病例才额外要求主诉表达和病史四件事。
_REGULAR_HARD_CONSULTATION_GATES = {
    "consultation.medication_allergy",
}
_COMPLEX_HARD_CONSULTATION_GATES = {
    "consultation.patient_expression",
    "consultation.four_history_tasks",
    "consultation.medication_allergy",
}


def consultation_hard_incomplete(
    incomplete: Optional[List[Any]],
    *,
    complex_case: bool = False,
) -> List[str]:
    """Return only consultation gaps that must block consult → examine."""
    gates = _COMPLEX_HARD_CONSULTATION_GATES if complex_case else _REGULAR_HARD_CONSULTATION_GATES
    return [item for item in (incomplete or []) if item in gates]


def consultation_gap_question(gaps: List[str], case_profile: Dict[str, Any]) -> str:
    """Map consultation gaps to the fewest patient-facing questions possible."""
    gap_set = {str(g) for g in gaps}
    needs_story = any(g.endswith("patient_expression") or g.endswith("four_history_tasks") for g in gap_set)
    needs_medication = any(g.endswith("medication_allergy") for g in gap_set)
    needs_danger = any(g.endswith("differential_2_to_3") or g.endswith("dangerous_diagnosis") for g in gap_set)
    needs_support = any(g.endswith("social_family_support") for g in gap_set)
    needs_teach_back = any(g.endswith("teach_back") for g in gap_set)

    if needs_story and needs_medication and needs_danger:
        return (
            "请一次性补充：这次为什么来看病、为什么现在就诊、症状这段时间怎么变化、既往慢性病/手术史、"
            "目前在用的全部药物和药物过敏史；另外请说明有无突然加重、昏厥、呼吸困难、出血等需要立即处理的表现，"
            "以及您现在最担心的问题。"
        )
    if needs_story and needs_medication:
        return (
            "请一次性补充：今天为什么来看病、为何现在就诊、有哪些慢性病/手术史、目前正在使用的全部药物"
            "（含处方药、非处方药、保健品/中草药、激素/免疫抑制剂）以及药物过敏史，"
            "并说说您最担心或最希望优先解决的问题。"
        )
    if needs_story and needs_support:
        return (
            "请一次性补充：今天为什么来看病、为何现在就诊、有哪些慢性病/手术史，以及您最担心的问题；"
            "同时说明主要照护者、日常活动能力、医保/费用、取药复诊是否方便，和对检查治疗的偏好或顾虑。"
        )
    if needs_medication and needs_support:
        return (
            "请一起补充：目前正在使用的全部药物（含处方药、非处方药、保健品/中草药、激素/免疫抑制剂）"
            "及药物过敏史；另外说明主要照护者、日常活动能力、医保/费用、取药复诊是否方便，"
            "以及对检查治疗的偏好或顾虑。"
        )
    if needs_danger and needs_support:
        return (
            "请一起补充：有无突然加重、昏厥、呼吸困难、出血等需要立即处理的表现，您最担心哪些严重问题；"
            "同时说明主要照护者、日常活动能力、医保/费用、取药复诊是否方便，以及对检查治疗的偏好或顾虑。"
        )
    if needs_story:
        return (
            "请用您自己的话完整描述：今天为什么来看病、为何现在就诊、症状怎么变化、有哪些慢性病/手术史，"
            "以及您最担心或最希望优先解决的问题。"
        )
    if needs_medication:
        return (
            "请补充目前正在使用的全部药物（含处方药、非处方药、保健品/中草药、激素/免疫抑制剂）"
            "以及药物过敏史。"
        )
    if needs_danger:
        return (
            "除了目前的不适，您最担心哪些严重问题？请补充有无突然加重、昏厥、呼吸困难、出血或其他需要立即处理的表现。"
        )
    if needs_support:
        return (
            "请补充主要照护者、日常活动能力、对治疗目标的理解，以及医保/费用、取药复诊是否方便、"
            "对检查治疗的偏好或顾虑。"
        )
    if needs_teach_back:
        return "我确认一下：目前最主要的问题、需要先排除的危险情况和下一步检查，您是否都理解？请您复述一下最重要的安排。"
    return "请补充任何尚未提到、但您认为会影响诊断或治疗的重要信息。"


def build_workflow_self_check(
    *, case_profile: Dict[str, Any], chat_history: List[Any],
    differential: Optional[List[Any]] = None, examinations: Optional[Dict[str, Any]] = None,
    final_plan: Optional[Dict[str, Any]] = None,
    min_differential_candidates: int = 2,
) -> Dict[str, Any]:
    """Return an auditable checklist for the four clinical control points."""
    profile = {str(k): clean_text(v) for k, v in case_profile.items()}
    history_ok = _patient_expression_complete(case_profile, chat_history)
    med_ok = not _medication_history_incomplete(case_profile, chat_history)
    social_ok = all(profile.get(k) not in {"", "未知"} for k in ("psychosocial_status", "family_economic_status"))
    caregiver_ok = profile.get("caregiver_function_preferences") not in {"", "未知"}
    diffs = differential or []
    min_diffs = max(2, int(min_differential_candidates or 2))
    consult = {
        "patient_expression": history_ok,
        "four_history_tasks": _four_history_tasks_complete(case_profile, chat_history),
        "system_localization": _system_localization_complete(case_profile, chat_history),
        "differential_2_to_3": len(diffs) >= min_diffs,
        "medication_allergy": med_ok,
        "social_family_support": social_ok and caregiver_ok,
        "dangerous_diagnosis": _has_dangerous_differential(diffs),
        "teach_back": _teach_back_confirmed(chat_history),
    }
    ex = examinations or {}
    exam_plans = ex.get("exam_decision_trace") or []
    valid_exam_plans = bool(exam_plans) and all(isinstance(x, dict) for x in exam_plans)
    exam = {
        "clinical_question": valid_exam_plans and all(clean_text(x.get("clinical_question")) for x in exam_plans),
        "decision_impact": valid_exam_plans and all(
            clean_text(x.get("decision_impact")) and _decision_impact_answers_gate(x.get("decision_impact"))
            for x in exam_plans
        ),
        "alternative_considered": valid_exam_plans and all(clean_text(x.get("alternatives_considered")) for x in exam_plans),
        "contraindication_risk_checked": valid_exam_plans and all(clean_text(x.get("risk_prerequisites")) for x in exam_plans),
        "followup_interval": valid_exam_plans and all(clean_text(x.get("followup_plan")) for x in exam_plans),
    }
    plan = final_plan or {}
    diagnosis = {
        "time_syndrome_risk": bool(
            clean_text(plan.get("clinical_problem_statement"))
            or (clean_text(plan.get("reasoning")) and clean_text(plan.get("key_findings")))
        ),
        "contradictory_evidence": plan.get("unexplained_findings") is not None,
        "competitive_diagnosis": bool(plan.get("competitive_diagnoses")),
        "bias_check": _bias_check_complete(plan),
        "diagnostic_pause": _diagnostic_pause_complete(plan),
        "pre_treatment_safety": _pre_treatment_safety_complete(plan, case_profile),
        "logical_closure": _logical_closure_complete(plan),
        "safety_net": _safety_net_complete(plan.get("safety_net")),
    }
    treatment = {
        "shared_decision": bool(clean_text(plan.get("shared_decision"))),
        "medication_interactions": med_ok and bool(clean_text(plan.get("medication_safety_review"))),
        "executability": _executability_complete(plan),
        "treatment_hierarchy": _treatment_hierarchy_complete(plan),
        "monitoring_followup_red_flags": _safety_net_complete(plan.get("safety_net")),
        "multidisciplinary_review": bool(clean_text(plan.get("multidisciplinary_review"))),
    }
    return {"consultation": consult, "examination": exam, "diagnosis": diagnosis,
            "treatment": treatment,
            "incomplete": [f"{stage}.{key}" for stage, values in
                            (("consultation", consult), ("examination", exam),
                             ("diagnosis", diagnosis), ("treatment", treatment))
                            for key, value in values.items() if not value]}

def _has_consultation_minimum(case_profile: Dict[str, Any], chat_history: List[Any], limits: Any) -> bool:
    """Allow exam after one high-yield consult turn when medication safety is known."""
    doctor_turns = sum(
        1
        for message in chat_history
        if isinstance(message, dict) and message.get("from") == "doctor"
    )
    min_turns = max(1, int(getattr(limits, "min_doctor_turns", 1) or 1))
    if doctor_turns < min_turns:
        return False
    return not _medication_history_incomplete(case_profile, chat_history)


def _has_actionable_exam_results(case_state: Dict[str, Any]) -> bool:
    """Do not treat an order acknowledgement as diagnostic evidence."""
    ordered = set(as_text_list(case_state.get("ordered_examinations")))
    raw_results = case_state.get("examination_results") or {}
    if not ordered or not isinstance(raw_results, dict):
        return False
    for name in ordered:
        result = raw_results.get(name)
        if not isinstance(result, dict):
            continue
        status = clean_text(result.get("status")).lower()
        text = clean_text(result.get("result"))
        if status not in {"unavailable", "invalid", "pending"} and text:
            return True
    return False


def advance_workflow_stage(
    *,
    case_state: Dict[str, Any],
    case_profile: Dict[str, Any],
    chat_history: List[Any],
    limits: Any,
    exam_resolver: Any = None,
    consultation_check: Optional[Dict[str, Any]] = None,
) -> WorkflowStage:
    """Advance monotonically without allowing an LLM to skip clinical stages."""
    current = WorkflowStage(case_state.get("stage", WorkflowStage.CONSULT.value))
    if consultation_check is None:
        consultation_check = case_state.get("consultation_check")
    consultation_ready = _has_consultation_minimum(case_profile, chat_history, limits)
    if consultation_check is not None:
        hard_gaps = consultation_hard_incomplete(
            consultation_check.get("incomplete"),
            complex_case=_is_complex_case(
                case_profile,
                case_state.get("preliminary_differential") or [],
            ),
        )
        consultation_ready = consultation_ready and not hard_gaps
    if current == WorkflowStage.CONSULT and consultation_ready:
        return WorkflowStage.EXAMINE
    if current == WorkflowStage.EXAMINE and _essential_exams_complete(
        case_state,
        case_profile,
        differential=case_state.get("preliminary_differential") or [],
        exam_resolver=exam_resolver,
        limits=limits,
    ):
        return WorkflowStage.DIAGNOSE
    return current


def _patient_expression_complete(case_profile: Dict[str, Any], chat_history: List[Any]) -> bool:
    text = " ".join(clean_text(m.get("text")) for m in chat_history if isinstance(m, dict) and m.get("from") == "patient")
    timeline = clean_text(case_profile.get("chief_complaint_timeline"))
    return bool(text and timeline and timeline not in {"未知", ""}) and len(text) >= 12


def _four_history_tasks_complete(case_profile: Dict[str, Any], chat_history: List[Any]) -> bool:
    """病史四件事：就诊原因、为何此时就诊、疾病/合并症清单、未说出口的真实诉求。"""
    patient_text = " ".join(
        clean_text(m.get("text")) for m in chat_history if isinstance(m, dict) and m.get("from") == "patient"
    )
    timeline = clean_text(case_profile.get("chief_complaint_timeline"))
    past = clean_text(case_profile.get("past_history"))
    unvoiced = clean_text(case_profile.get("unvoiced_concerns"))
    why_now_markers = ("今天", "现在", "最近", "加重", "担心", "害怕", "来看病", "就诊", "为何", "为什么")
    concern_markers = ("担心", "害怕", "最怕", "会不会是", "肿瘤", "癌", "严重", "希望")
    has_visit_reason = bool(timeline and timeline not in {"", "未知"}) or len(patient_text) >= 12
    has_why_now = any(token in patient_text for token in why_now_markers) or any(
        token in timeline for token in why_now_markers
    )
    has_comorbidity = past not in {"", "未知"} or any(
        token in patient_text for token in ("既往", "慢性", "以前", "一直有", "基础病", "手术", "没有其他病", "否认慢病")
    )
    has_unvoiced = unvoiced not in {"", "未知"} or any(token in patient_text for token in concern_markers)
    return bool(has_visit_reason and has_why_now and has_comorbidity and has_unvoiced)


def _system_localization_complete(case_profile: Dict[str, Any], chat_history: List[Any]) -> bool:
    """Check that the current chief complaint is localized enough before ordering tests."""
    text = _case_profile_text_for_consult(case_profile, chat_history)
    if any(token in text for token in ("腰", "骶", "臀", "腹股沟", "髋", "跌倒", "关节痛")):
        return any(token in text for token in ("位置", "放射", "翻身", "站立", "走路", "负重", "腿麻", "无力", "大小便"))
    if any(token in text for token in ("眼", "视力", "畏光", "眼红", "眼痛")):
        return any(token in text for token in ("视力", "单眼", "双眼", "分泌物", "外伤", "隐形", "激素眼药"))
    if any(token in text for token in ("包块", "肿块", "小包", "疤", "皮肤")):
        return any(token in text for token in ("位置", "大小", "发红", "发热", "波动", "渗液", "压痛", "瘢痕"))
    if any(token in text for token in ("口腔", "溃疡", "牙龈", "嘴巴")):
        return any(token in text for token in ("牙龈", "舌", "咽", "发热", "喝水", "进食", "皮疹", "流口水"))
    if any(token in text for token in ("咳嗽", "鼻塞", "流鼻涕", "黄痰", "喉咙痛")):
        return any(token in text for token in ("高热", "喘", "胸痛", "呼吸", "精神", "接触", "痰", "鼻涕"))
    if any(token in text for token in ("记不住", "迷路", "口渴", "尿多", "忘事")):
        return any(token in text for token in ("突然", "逐渐", "日常", "找路", "夜尿", "血糖", "漏服", "体重"))
    return True


def _decision_impact_answers_gate(value: Any) -> bool:
    text = clean_text(value)
    if not text:
        return False
    has_positive = any(token in text for token in ("阳性", "若阳性", "结果阳性", "阳性将"))
    has_negative = any(token in text for token in ("阴性", "若阴性", "结果阴性", "阴性将"))
    return has_positive and has_negative


def _bias_check_complete(plan: Dict[str, Any]) -> bool:
    competitive = plan.get("competitive_diagnoses") or []
    if not competitive:
        return False
    steps = " ".join(as_text_list(plan.get("reasoning_steps"))) + clean_text(plan.get("reasoning"))
    bias_markers = ("锚定", "可得性", "证实", "确认偏误", "偏倚", "竞争性", "不一致", "反面证据", "别的可能")
    return any(token in steps for token in bias_markers) or bool(plan.get("unexplained_findings") is not None)


def _diagnostic_pause_complete(plan: Dict[str, Any]) -> bool:
    pause = plan.get("diagnostic_pause")
    if isinstance(pause, dict):
        return bool(clean_text(pause.get("working_diagnosis"))) and bool(
            pause.get("supporting_evidence") or pause.get("contradictory_evidence")
        )
    steps = " ".join(as_text_list(plan.get("reasoning_steps")))
    pause_markers = ("诊断性暂停", "工作诊断", "plan b", "plan_b", "备选方案", "遗漏鉴别")
    return any(token in steps.lower() for token in pause_markers)


def _pre_treatment_safety_complete(plan: Dict[str, Any], case_profile: Dict[str, Any]) -> bool:
    pause = plan.get("pre_treatment_safety_pause")
    if isinstance(pause, dict):
        return bool(clean_text(pause.get("medication_allergy_interactions"))) and bool(
            clean_text(pause.get("pregnancy_renal_hepatic")) or clean_text(pause.get("social_executability"))
        )
    med_review = clean_text(plan.get("medication_safety_review"))
    profile = {str(k): clean_text(v) for k, v in case_profile.items()}
    has_med = profile.get("medication_allergy_history") not in {"", "未知"}
    safety_markers = ("妊娠", "过敏", "肝", "肾", "相互作用", "禁忌", "安全暂停")
    combined = med_review + clean_text(plan.get("treatment_plan"))
    return has_med and any(token in combined for token in safety_markers)


def _logical_closure_complete(plan: Dict[str, Any]) -> bool:
    treatment = clean_text(plan.get("treatment_plan"))
    reasoning = clean_text(plan.get("reasoning"))
    diagnosis = as_text_list(plan.get("diagnosis"))
    if not diagnosis or not treatment:
        return False
    closure_markers = ("逻辑", "闭环", "一致", "解释", "支持诊断", "对应检查")
    combined = treatment + reasoning + " ".join(as_text_list(plan.get("reasoning_steps")))
    return any(token in combined for token in closure_markers) or bool(plan.get("evidence_matrix"))


def _treatment_hierarchy_complete(plan: Dict[str, Any]) -> bool:
    treatment = clean_text(plan.get("treatment_plan"))
    if not treatment:
        return False
    tier_markers = (
        "主要治疗", "病因", "对症", "支持", "经验", "生命支持", "紧急",
        "合并症", "安全禁忌", "监测", "随访",
    )
    hits = sum(1 for token in tier_markers if token in treatment)
    return hits >= 2


def _executability_complete(plan: Dict[str, Any]) -> bool:
    text = clean_text(plan.get("executability_assessment")) or clean_text(plan.get("shared_decision"))
    if not text:
        return False
    markers = ("经济", "医保", "取药", "复诊", "照护", "依从", "可及", "负担", "家属")
    return sum(1 for token in markers if token in text) >= 2

def _has_dangerous_differential(differential: List[Any]) -> bool:
    for item in differential:
        if not isinstance(item, dict):
            continue
        if item.get("must_rule_out") is True and clean_text(item.get("risk_if_missed")):
            return True
        text = " ".join(str(item.get(k) or "") for k in ("suspected_disease", "key_treatment_points", "contradictory_points"))
        if any(token in text for token in ("危险", "红旗", "必须排除", "急症", "危重", "排除")):
            return True
    return False


def _teach_back_confirmed(chat_history: List[Any]) -> bool:
    doctors = [clean_text(m.get("text")) for m in chat_history if isinstance(m, dict) and m.get("from") == "doctor"]
    patients = [clean_text(m.get("text")) for m in chat_history if isinstance(m, dict) and m.get("from") == "patient"]
    if not doctors or not patients:
        return False
    asked = any(any(token in q for token in ("复述", "理解", "明白", "确认一下", "最担心")) for q in doctors)
    return asked and any(any(token in a for token in ("明白", "理解", "知道", "好的", "是的", "会")) for a in patients[-2:])


def _safety_net_complete(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    return bool(clean_text(value.get("reassessment")) and (value.get("escalation_triggers") or value.get("red_flags")))


def _medication_history_incomplete(
    case_profile: Dict[str, Any],
    chat_history: Optional[List[Any]] = None,
) -> bool:
    if _medication_and_allergy_answered_in_chat(chat_history or []):
        return False

    med = clean_text(case_profile.get("medication_allergy_history"))
    if not med or med == "未知":
        return True
    actionable_markers = (
        "正在用", "在用", "用药", "胰岛素", "降压药", "抗病毒药", "他汀", "吸入剂",
        "退热药", "免疫抑制", "激素", "不过敏", "无过敏", "对青霉素过敏", "皮疹",
        "没有长期用药", "长期没吃药", "平时没吃药",
    )
    if not any(marker in med for marker in actionable_markers):
        for marker in ("未知", "未获", "不清楚", "不详", "未提及", "未说明"):
            if marker in med:
                return True
    for field in case_profile.get("missing_critical_fields") or []:
        field_text = str(field)
        if any(key in field_text for key in ("用药", "药物", "激素", "免疫抑制", "过敏", "处方")):
            if not any(marker in med for marker in actionable_markers):
                return True
    return False


def _medication_and_allergy_answered_in_chat(chat_history: List[Any]) -> bool:
    patient_text = " ".join(
        clean_text(message.get("text"))
        for message in chat_history
        if isinstance(message, dict) and message.get("from") == "patient"
    )
    if not patient_text:
        return False
    medication_markers = (
        "泼尼松",
        "激素",
        "免疫抑制",
        "处方药",
        "非处方",
        "保健品",
        "中草药",
        "长期口服",
        "口服药",
        "每天在吃",
        "每天都吃",
        "正在吃",
        "正在用",
        "在用",
        "一直在吃",
        "用药",
        "药膏",
        "长期没吃药",
        "没有长期吃药",
        "没吃长期药",
        "没有长期用药",
        "无长期用药",
        "平时没吃药",
        "没有用药",
        "打胰岛素",
        "吃降压",
        "服用降压",
        "全部药物",
        "所有药物",
    )
    allergy_markers = (
        "过敏史", "药物过敏", "没有过敏", "无过敏", "不过敏", "对药物没有过敏",
        "过敏不清楚", "药物过敏不清楚", "过敏记不清", "过敏不详",
        "不知道有没有过敏", "不确定有没有过敏", "不知道是否过敏", "不确定是否过敏",
        "对青霉素过敏", "对头孢过敏", "对阿莫西林过敏", "没发现过敏", "未发现过敏",
        "不记得对什么药过敏", "起过皮疹", "起皮疹",
    )
    has_medication = any(marker in patient_text for marker in medication_markers)
    has_allergy = any(marker in patient_text for marker in allergy_markers)
    has_specific_allergy = "过敏" in patient_text and any(
        marker in patient_text
        for marker in ("对", "青霉素", "头孢", "阿莫西林", "皮疹", "荨麻疹", "面部肿胀")
    )
    return has_medication and (has_allergy or has_specific_allergy)


def _question_already_asked(question: Any, chat_history: List[Any]) -> bool:
    normalized_question = normalize_name(question)
    if not normalized_question:
        return False
    for message in chat_history:
        if not isinstance(message, dict) or message.get("from") != "doctor":
            continue
        if normalize_name(message.get("text")) == normalized_question:
            return True
    return False



def _is_complex_case(case_profile: Dict[str, Any], differential: List[Any]) -> bool:
    """高复杂度病例仍走同一 3 分钟闭环，只在问诊/检查组合上取上限。"""
    text = json.dumps(
        {"profile": case_profile, "differential": differential[:5]},
        ensure_ascii=False,
    ).lower()
    complex_markers = (
        "免疫抑制", "hiv", "aids", "cd4", "休克", "脓毒",
        "新生儿", "婴儿", "播散", "多器官", "持续低氧", "血流动力学",
    )
    if any(marker in text for marker in complex_markers):
        return True
    for item in differential:
        if not isinstance(item, dict):
            continue
        if item.get("must_rule_out") is True and clean_text(item.get("confidence_level")) == "高":
            return True
    return False


def effective_max_doctor_turns(
    case_profile: Dict[str, Any],
    differential: List[Any],
    *,
    limits: Any,
) -> int:
    """常规最多 2 轮问诊；复杂病例也不再扩到 3 轮，以把单例收口在 3 分钟内。"""
    ceiling = min(5, int(getattr(limits, "max_doctor_turns_ceiling", 2) or 2))
    default = min(ceiling, int(getattr(limits, "max_doctor_turns", 2) or 2))
    if _is_complex_case(case_profile, differential):
        return max(int(getattr(limits, "min_doctor_turns", 1) or 1), ceiling)
    return max(int(getattr(limits, "min_doctor_turns", 1) or 1), default)


def effective_max_exam_rounds(
    case_profile: Dict[str, Any],
    differential: List[Any],
    *,
    limits: Any,
) -> int:
    """常规 2 轮针对性开检查；复杂病例也不扩到 3 轮，改为首轮多开关键项。"""
    ceiling = min(5, int(getattr(limits, "max_exam_rounds_ceiling", 2) or 2))
    default = min(ceiling, int(getattr(limits, "max_exam_rounds", 2) or 2))
    if _is_complex_case(case_profile, differential):
        return max(1, ceiling)
    return max(1, default)


def _diagnosis_ready_for_finalize(
    case_state: Dict[str, Any],
    differential: List[Any],
    *,
    limits: Any,
) -> bool:
    """疾病证据链已充分时允许提前进入诊断/治疗，控制总时长。"""
    if not differential or not isinstance(differential[0], dict):
        return False
    doctor_turns = sum(
        1 for message in (case_state.get("chat_history") or [])
        if isinstance(message, dict) and message.get("from") == "doctor"
    )
    if doctor_turns < limits.min_doctor_turns:
        return False
    if not _has_actionable_exam_results(case_state):
        return False
    top = differential[0]
    confidence = clean_text(top.get("confidence_level"))
    prob = top.get("subjective_probability")
    exam_support = as_text_list(top.get("exam_support"))
    support = as_text_list(top.get("support_points"))
    high_conf = confidence == "高" or (isinstance(prob, (int, float)) and prob >= 0.65)
    return bool(exam_support or support) and high_conf


def _arrhythmia_etiology_workup_incomplete(
    case_state: Dict[str, Any],
    case_profile: Optional[Dict[str, Any]] = None,
) -> bool:
    """New AF still needs thyroid function before the workup is etiologically complete."""
    result_text = normalize_name(json.dumps(case_state.get("examination_results") or {}, ensure_ascii=False))
    profile_text = normalize_name(json.dumps(case_profile or {}, ensure_ascii=False))
    combined = result_text + " " + profile_text
    has_af = any(token in combined for token in ("心房颤动", "房颤", "p波消失", "心律绝对不齐"))
    if not has_af:
        return False
    ordered = normalize_name(" ".join(as_text_list(case_state.get("ordered_examinations"))))
    has_tft = any(token in ordered for token in ("甲状腺功能", "tfts", "甲功"))
    return not has_tft


def _has_decisive_disease_evidence(
    case_state: Dict[str, Any],
    differential: Optional[List[Any]],
    *,
    exam_resolver: Any = None,
    case_profile: Optional[Dict[str, Any]] = None,
) -> bool:
    """Allow diagnosis after one decisive test when it identifies a concrete disease."""
    if _arrhythmia_etiology_workup_incomplete(case_state, case_profile):
        return False
    if not differential or not isinstance(differential[0], dict):
        return False
    if not _has_actionable_exam_results(case_state):
        return False
    top = differential[0]
    disease = clean_text(top.get("suspected_disease"))
    if not disease or disease in {"未明确诊断", "待查", "不明原因"}:
        return False
    confidence = clean_text(top.get("confidence_level"))
    prob = top.get("subjective_probability")
    high_conf = confidence == "高" or (isinstance(prob, (int, float)) and prob >= 0.7)
    if not high_conf:
        return False
    ordered = set(as_text_list(case_state.get("ordered_examinations")))
    resolved_ordered = {
        exam_resolver(name) if callable(exam_resolver) else name
        for name in ordered
    }
    recommended = {
        exam_resolver(name) if callable(exam_resolver) else name
        for name in as_text_list(top.get("recommended_examinations"))
    }
    if as_text_list(top.get("exam_support")):
        return True
    result_text = normalize_name(json.dumps(case_state.get("examination_results") or {}, ensure_ascii=False))
    if recommended and resolved_ordered & recommended and any(
        normalize_name(support) in result_text
        for support in as_text_list(top.get("support_points"))
    ):
        return True
    return bool(result_text and normalize_name(disease) in result_text)


def _plan_next_step(
    *,
    case_state: Dict[str, Any],
    case_profile: Dict[str, Any],
    chat_history: List[Any],
    limits: Any,
    budget: Any,
    in_consultation: bool = False,
    exam_resolver: Any = None,
    max_consult_turns: Optional[int] = None,
    max_exam_rounds: Optional[int] = None,
) -> tuple[str, str, str]:
    """Deterministic workflow planner: regular cases close in 2.5 minutes, complex in 3.

    普通病例问诊默认 1 轮；仅用药安全硬缺口才补第 2 轮。复杂病例才追问四史/假设驱动问题。
    """
    doctor_turns = sum(1 for message in chat_history if message.get("from") == "doctor")
    exam_rounds = int(case_state.get("exam_rounds", 0))
    ordered = as_text_list(case_state.get("ordered_examinations"))
    differential = case_state.get("preliminary_differential") or []
    complex_case = _is_complex_case(case_profile, differential)
    if max_consult_turns is None:
        max_consult_turns = effective_max_doctor_turns(case_profile, differential, limits=limits)
    if max_exam_rounds is None:
        max_exam_rounds = effective_max_exam_rounds(case_profile, differential, limits=limits)
    stage = advance_workflow_stage(
        case_state=case_state,
        case_profile=case_profile,
        chat_history=chat_history,
        limits=limits,
        exam_resolver=exam_resolver,
    )
    case_state["stage"] = stage.value
    time_critical = bool(getattr(budget, "time_critical", lambda: False)())
    pace_tight = (
        time_critical
        or budget.remaining() < (limits.max_patient_seconds * 0.5)
        or getattr(budget, "consult_time_exceeded", lambda: False)()
    )

    if budget.should_force_finalize(in_consultation=in_consultation):
        if stage == WorkflowStage.DIAGNOSE:
            return "final_diagnosis", "", "时间/调用预算将尽，进入综合诊断。"
        if stage == WorkflowStage.EXAMINE:
            if exam_rounds < max_exam_rounds and (
                not ordered or not _has_actionable_exam_results(case_state)
            ):
                return "order_examination", "", "时间将尽，尽快补齐关键客观证据后诊断。"
            return "final_diagnosis", "", "时间预算将尽，基于现有信息进入诊断。"
        # CONSULT under time pressure
        if doctor_turns < limits.min_doctor_turns:
            return (
                "ask_patient",
                _next_consultation_question(
                    case_profile, doctor_turns, differential=differential, chat_history=chat_history
                ),
                "时间紧张，优先完成最低问诊轮次以获取关键信息。",
            )
        hard_gaps = consultation_hard_incomplete(
            (case_state.get("consultation_check") or {}).get("incomplete"),
            complex_case=complex_case,
        )
        if hard_gaps and doctor_turns < max_consult_turns:
            return (
                "ask_patient",
                consultation_gap_question(hard_gaps, case_profile),
                "时间紧张，压缩补齐问诊硬缺口。",
            )
        if _medication_history_incomplete(case_profile, chat_history) and doctor_turns < max_consult_turns:
            return (
                "ask_patient",
                "请补充目前正在使用的药物（含处方药、非处方药、保健品/中草药）以及药物过敏史。",
                "时间紧张，优先补齐用药安全史。",
            )
        if exam_rounds < max_exam_rounds and not ordered:
            return "order_examination", "", "问诊已达最低轮次，时间将尽，转入检查。"
        return "final_diagnosis", "", "时间预算将尽，基于现有信息进入诊断。"

    # 阶段时间预算：问诊/检查超时则推进（仅用药史硬缺口可短暂停留）
    if stage == WorkflowStage.CONSULT and getattr(budget, "consult_time_exceeded", lambda: False)():
        if doctor_turns < limits.min_doctor_turns:
            pass  # 仍须完成最低轮次
        elif _medication_history_incomplete(case_profile, chat_history) and doctor_turns < max_consult_turns:
            return (
                "ask_patient",
                "请补充目前正在使用的药物（含处方药、非处方药、保健品/中草药）以及药物过敏史。",
                "问诊阶段时间预算将尽，仅补齐用药安全史。",
            )
        elif exam_rounds < max_exam_rounds and not ordered:
            return "order_examination", "", "问诊阶段时间预算已用尽，转入检查。"
        return "final_diagnosis", "", "问诊阶段时间预算已用尽，基于现有信息进入诊断。"

    if stage == WorkflowStage.EXAMINE and getattr(budget, "examine_time_exceeded", lambda: False)():
        return "final_diagnosis", "", "检查阶段时间预算已用尽，进入综合诊断。"

    if stage == WorkflowStage.CONSULT and not chat_history:
        return (
            "ask_patient",
            OPENING_CONSULTATION_QUESTION,
            "首轮按条目一次问齐主诉、部位、用药安全和红旗，避免拆成多轮追问。",
        )

    if stage == WorkflowStage.CONSULT and doctor_turns < limits.min_doctor_turns:
        return (
            "ask_patient",
            _next_consultation_question(case_profile, doctor_turns, differential=differential, chat_history=chat_history),
            "按需补齐病史四件事、用药安全与假设驱动关键点。",
        )

    if stage == WorkflowStage.CONSULT and doctor_turns >= max_consult_turns:
        if exam_rounds < max_exam_rounds and not ordered:
            return "order_examination", "", "问诊已达轮次上限，必须转入检查。"
        return "final_diagnosis", "", "问诊已达轮次上限，基于现有信息进入诊断。"

    hard_gaps = consultation_hard_incomplete(
        (case_state.get("consultation_check") or {}).get("incomplete"),
        complex_case=complex_case,
    )
    if stage == WorkflowStage.CONSULT and hard_gaps and doctor_turns < max_consult_turns:
        return (
            "ask_patient",
            consultation_gap_question(hard_gaps, case_profile),
            "压缩补齐问诊硬缺口后转入检查。",
        )

    if stage == WorkflowStage.CONSULT and _medication_history_incomplete(case_profile, chat_history) and doctor_turns < max_consult_turns:
        return (
            "ask_patient",
            "请补充目前正在使用的药物（含处方药、非处方药、保健品/中草药、激素/免疫抑制剂）以及药物过敏史。",
            "用药与过敏史前置，影响检查和治疗安全。",
        )

    # 普通病例不追软问题；复杂病例才在时间允许时补一条假设/定位问题。
    allow_soft_questions = (
        complex_case
        and stage == WorkflowStage.CONSULT
        and doctor_turns < max_consult_turns
        and exam_rounds == 0
        and not pace_tight
    )

    contradiction_question = _narrative_contradiction_question(case_profile, chat_history)
    if allow_soft_questions and contradiction_question:
        return "ask_patient", contradiction_question, "叙述出现不一致线索，回到开放式问题避免过早闭合。"

    hypothesis_question = _hypothesis_driven_question(differential, chat_history)
    if allow_soft_questions and hypothesis_question:
        return "ask_patient", hypothesis_question, "用针对性问题检验最可能诊断与必须排除的危险诊断。"

    domain_question = _domain_specific_history_question(case_profile, chat_history)
    if allow_soft_questions and domain_question:
        return "ask_patient", domain_question, "当前主诉需要补充特异性饮食、用药或职业背景。"

    caregiver_question = _caregiver_executability_question(case_profile, chat_history)
    if allow_soft_questions and caregiver_question:
        return "ask_patient", caregiver_question, "前置家庭照护、功能状态与可及性，支持共同决策。"

    unclear_question = _unclear_history_recovery_question(case_profile, chat_history)
    if allow_soft_questions and unclear_question:
        return "ask_patient", unclear_question, "病史不清时改用时间线/生活史/家属补充继续采集。"

    if (
        allow_soft_questions
        and _has_actionable_gaps(case_profile)
    ):
        question = _question_from_missing_fields(case_profile, chat_history)
        if question:
            return "ask_patient", question, "补齐仍影响决策的关键信息。"

    if stage == WorkflowStage.EXAMINE and _diagnosis_ready_for_finalize(
        case_state, differential, limits=limits
    ) and _essential_exams_complete(
        case_state,
        case_profile,
        differential=differential,
        exam_resolver=exam_resolver,
        limits=limits,
    ):
        return "final_diagnosis", "", "疾病证据链已明确，提前进入诊断治疗以控制总时长。"

    if stage == WorkflowStage.EXAMINE and exam_rounds < max_exam_rounds and not _essential_exams_complete(
        case_state,
        case_profile,
        differential=differential,
        exam_resolver=exam_resolver,
        limits=limits,
    ):
        return "order_examination", "", "按鉴别诊断与检查维度缺口补齐客观证据。"

    if stage == WorkflowStage.DIAGNOSE:
        return "final_diagnosis", "", "问诊与检查已满足综合评估要求，进入诊断。"
    if stage == WorkflowStage.EXAMINE:
        if exam_rounds >= max_exam_rounds:
            return "final_diagnosis", "", "检查轮次已达上限，进入综合诊断。"
        return "order_examination", "", "关键检查结果尚未齐备，继续补齐客观证据。"
    # 问诊已达最低轮次且硬信息基本齐：进入检查，避免拖到 3 轮。
    if doctor_turns >= limits.min_doctor_turns and exam_rounds < max_exam_rounds:
        return "order_examination", "", "问诊信息已足够，转入检查以节省总时长。"
    return (
        "ask_patient",
        _next_consultation_question(case_profile, doctor_turns, differential=differential, chat_history=chat_history),
        "继续补齐关键问诊信息。",
    )


def _next_consultation_question(
    case_profile: Dict[str, Any],
    doctor_turns: int,
    *,
    differential: Optional[List[Any]] = None,
    chat_history: Optional[List[Any]] = None,
) -> str:
    """漏斗式问诊：主诉时间线 -> 系统定位与治疗安全 -> 假设驱动/可执行性。"""
    history = chat_history or []
    if doctor_turns == 0:
        return OPENING_CONSULTATION_QUESTION
    if doctor_turns == 1:
        system_question = _system_localization_question(case_profile, history)
        if system_question:
            return system_question
        return (
            "请补充最疼或最难受的具体部位、诱因、活动是否受限；"
            "同时说一下既往慢性病/手术史、目前正在使用的全部药物和药物过敏史，"
            "以及有没有突然加重、昏厥、呼吸困难或出血。"
        )
    hypothesis = _hypothesis_driven_question(differential or [], history)
    if doctor_turns == 2:
        if _medication_history_incomplete(case_profile, history):
            combined_question = _combined_safety_and_gap_question(case_profile, history)
            if combined_question:
                return combined_question
        if hypothesis:
            return hypothesis
        missing_question = _question_from_missing_fields(case_profile, history)
        if missing_question:
            return missing_question
        caregiver = _caregiver_executability_question(case_profile, history)
        if caregiver:
            return caregiver
        return "请补充近期接触/旅居/职业暴露，以及会影响检查或治疗选择的重要阴性症状。"
    if doctor_turns == 3:
        caregiver = _caregiver_executability_question(case_profile, history)
        if caregiver:
            return caregiver
        if hypothesis:
            return hypothesis
        missing_question = _question_from_missing_fields(case_profile, history)
        if missing_question:
            return missing_question
        return "请补充主要照护者、日常活动能力、对检查治疗的偏好，以及医保/费用与取药复诊是否方便？"
    if hypothesis:
        return hypothesis
    missing_question = _question_from_missing_fields(case_profile, history)
    if missing_question:
        return missing_question
    return "请补充任何您认为重要、但尚未提到的症状、诱因、用药或家庭支持情况。"


def _system_localization_question(case_profile: Dict[str, Any], chat_history: List[Any]) -> str:
    """第二轮固定追问：把主诉定位到系统/部位，并同时获取危险阴性。"""
    text = _case_profile_text_for_consult(case_profile, chat_history)
    safety_tail = "另外请一起说明既往慢性病/手术史、目前用药和药物过敏史，以及最担心的危险表现。"
    question = ""
    if any(token in text for token in ("眼", "视力", "畏光", "流泪", "眼红", "眼痛")):
        question = (
            "请补充是单眼还是双眼、视力有没有下降，是否有分泌物、异物感、外伤/隐形眼镜/激素眼药水使用，"
            "以及疼痛和畏光是否持续加重。" + safety_tail
        )
    elif any(token in text for token in ("淋巴结", "无痛肿块", "腹股沟肿块", "颈部肿块", "盗汗", "体重掉", "体重下降", "消瘦")):
        question = (
            "请补充肿块出现多久、是否持续增大、是否有发热/盗汗/体重下降，"
            "以及皮疹分布、瘙痒程度、腹泻腹痛和既往自身免疫或肿瘤病史。" + safety_tail
        )
    elif any(token in text for token in ("近端肌无力", "梳头", "上楼", "光敏", "蝶形", "红疹", "晨僵")):
        question = (
            "请补充肌无力是否对称、主要影响肩髋带还是远端肢体，是否有吞咽/呼吸困难、雷诺现象、口腔溃疡或脱发。"
            + safety_tail
        )
    elif any(token in text for token in ("腰", "骶", "臀", "腿痛", "髋", "关节痛", "跌倒", "扭伤")):
        question = (
            "请补充疼痛最明确的位置（腰、骶髂、臀部、腹股沟还是腿）、是否向下放射，"
            "翻身/站立/走路是否受限，以及有无腿麻无力、大小便异常或发热。" + safety_tail
        )
    elif any(token in text for token in ("包块", "肿块", "小包", "疤", "皮肤", "红肿", "压痛")):
        question = (
            "请补充包块的具体位置、大小变化、是否发红发热或有波动感、是否渗液，"
            "以及与旧手术瘢痕或摩擦刺激的关系。" + safety_tail
        )
    elif any(token in text for token in ("口腔", "溃疡", "牙龈", "嘴巴", "吃不下", "吞咽痛")):
        question = (
            "请补充溃疡主要在嘴唇、牙龈、舌头还是咽部，有无发热、口臭、流口水或手足皮疹，"
            "现在喝水和进食大概还能到平时的几成。" + safety_tail
        )
    elif any(token in text for token in ("咳嗽", "鼻塞", "流鼻涕", "黄痰", "喘", "喉咙痛")):
        question = (
            "请补充是否有高热、喘鸣、胸痛、呼吸急促或精神差，痰/鼻涕颜色和量怎样变化，"
            "以及家里或学校最近有没有类似感染接触。" + safety_tail
        )
    elif any(token in text for token in ("记不住", "迷路", "口渴", "尿多", "认不出路", "忘事")):
        question = (
            "请补充记忆问题是突然还是逐渐加重、是否影响做饭付钱找路等日常功能，"
            "同时有无体重变化、夜尿增多、视物模糊或近期漏服降糖药。" + safety_tail
        )
    elif any(token in text for token in ("胸痛", "胸闷", "心悸", "呼吸困难")):
        question = (
            "请补充症状与活动/休息的关系、持续多久、能否放射到背部或手臂，"
            "以及有无晕厥、大汗、下肢水肿或近期感染。" + safety_tail
        )
    if question and not _question_already_asked(question, chat_history):
        return question
    return ""


def _case_profile_text_for_consult(case_profile: Dict[str, Any], chat_history: List[Any]) -> str:
    patient_text = " ".join(
        clean_text(message.get("text"))
        for message in chat_history
        if isinstance(message, dict) and message.get("from") == "patient"
    )
    return json.dumps(case_profile, ensure_ascii=False) + patient_text


def _combined_safety_and_gap_question(case_profile: Dict[str, Any], chat_history: List[Any]) -> str:
    """第三轮优先把主诉系统关键缺口和治疗安全史合并成一个问题。"""
    text = _case_profile_text_for_consult(case_profile, chat_history)
    safety_tail = "另外请一起说明既往慢性病/手术史、目前在用药物、是否用过激素/免疫抑制剂，以及药物过敏史。"
    question = ""
    if any(token in text for token in ("眼", "视力", "畏光", "眼红", "眼痛")):
        question = "请补充视力是否下降、是否戴隐形眼镜或近期眼外伤、是否长期断续使用激素眼药水；" + safety_tail
    elif any(token in text for token in ("淋巴结", "无痛肿块", "腹股沟肿块", "颈部肿块", "盗汗", "体重下降", "消瘦")):
        question = "请补充肿块是否持续增大、是否伴发热盗汗体重下降、既往乳糜泻/贫血或肿瘤病史；" + safety_tail
    elif any(token in text for token in ("近端肌无力", "梳头", "上楼", "光敏", "蝶形", "红疹", "晨僵")):
        question = "请补充有无吞咽或呼吸困难、雷诺现象、口腔溃疡、脱发、尿色/尿量变化；" + safety_tail
    elif any(token in text for token in ("腰", "骶", "臀", "腹股沟", "跌倒", "关节")):
        question = "请补充跌倒后是否完全不能负重、夜间痛醒、晨僵、发热或近期感染史；" + safety_tail
    elif any(token in text for token in ("包块", "肿块", "疤", "皮肤")):
        question = "请补充包块是否越来越大、是否破溃流液、是否反复在同一位置出现；" + safety_tail
    elif any(token in text for token in ("记不住", "口渴", "尿多", "忘事")):
        question = "请补充血糖药是否经常漏服、近期食欲体重和睡眠变化，以及是否有人发现您判断力或定向力明显下降；" + safety_tail
    elif any(token in text for token in ("口腔", "溃疡", "牙龈")):
        question = "请补充现在尿量、精神状态、有没有发热或皮疹，以及近期吃过什么止痛药或口腔药；" + safety_tail
    elif any(token in text for token in ("咳嗽", "黄痰", "鼻塞", "喉咙痛")):
        question = "请补充是否有呼吸急促、喘鸣、胸痛、基础哮喘或免疫抑制用药；" + safety_tail
    if question and not _question_already_asked(question, chat_history):
        return question
    fallback = "请补充目前症状相关的关键诱因或危险信号，并一起说明正在使用的药物、激素/免疫抑制剂和药物过敏史。"
    if not _question_already_asked(fallback, chat_history):
        return fallback
    return ""


def _hypothesis_driven_question(differential: List[Any], chat_history: List[Any]) -> str:
    """用鉴别诊断的 history_gaps / 危险诊断生成假设-验证问题。"""
    gaps: List[str] = []
    dangerous: List[str] = []
    contradictory: List[str] = []
    for item in differential:
        if not isinstance(item, dict):
            continue
        disease = clean_text(item.get("suspected_disease")) or "当前鉴别"
        for gap in as_text_list(item.get("history_gaps")):
            gap_text = clean_text(gap)
            if gap_text and gap_text not in gaps:
                gaps.append(gap_text)
        for point in as_text_list(item.get("contradictory_points")):
            point_text = clean_text(point)
            if point_text and point_text not in {"无", "none", "无矛盾"} and point_text not in contradictory:
                contradictory.append("%s：%s" % (disease, point_text))
        if item.get("must_rule_out") is True:
            risk = clean_text(item.get("risk_if_missed")) or "漏诊风险高"
            dangerous.append("%s（%s）" % (disease, risk))
    for gap in gaps:
        question = "为验证当前鉴别假设，请具体说明：%s" % gap
        if not _question_already_asked(question, chat_history):
            return question
    if contradictory:
        question = (
            "现有信息与部分鉴别存在矛盾。请补充：%s；"
            "另外，是否还有其他您尚未提到的症状或情况？"
            % "；".join(contradictory[:2])
        )
        if not _question_already_asked(question, chat_history):
            return question
    if dangerous:
        question = (
            "除目前不适外，请补充有无突然加重、昏厥、呼吸困难、大出血或其他危险表现；"
            "我们需要优先排除：%s。" % "、".join(dangerous[:2])
        )
        if not _question_already_asked(question, chat_history):
            return question
    bias_question = "除了目前考虑的方向，您有没有想到其他可能的解释，或有什么症状与当前判断不太一致？"
    if differential and not _question_already_asked(bias_question, chat_history):
        return bias_question
    return ""


def _narrative_contradiction_question(case_profile: Dict[str, Any], chat_history: List[Any]) -> str:
    """当叙述出现矛盾或不一致线索时，主动回到开放式问题。"""
    patient_msgs = [
        clean_text(m.get("text"))
        for m in chat_history
        if isinstance(m, dict) and m.get("from") == "patient" and clean_text(m.get("text"))
    ]
    if len(patient_msgs) < 2:
        return ""
    contradiction_markers = ("但是", "不过", "又说", "不对", "记不清", "好像不是", "矛盾", "改口")
    doctor_text = " ".join(
        clean_text(m.get("text")) for m in chat_history if isinstance(m, dict) and m.get("from") == "doctor"
    )
    profile_flags = " ".join(as_text_list(case_profile.get("missing_critical_fields"))) + clean_text(
        case_profile.get("summary")
    )
    triggered = any(token in " ".join(patient_msgs[-2:]) for token in contradiction_markers) or any(
        token in profile_flags for token in ("矛盾", "不一致", "不清")
    )
    if not triggered:
        return ""
    question = "前面有些描述似乎不太一致。请您重新按时间顺序完整说一遍：症状如何开始、如何变化，中间有没有加重或缓解？"
    if "开放" in doctor_text and _question_already_asked(question, chat_history):
        return ""
    if not _question_already_asked(question, chat_history):
        return question
    return ""


def _unclear_history_recovery_question(case_profile: Dict[str, Any], chat_history: List[Any]) -> str:
    """病史不清时，换时间线/生活史/家属补充，而不是终止问诊。"""
    patient_text = " ".join(
        clean_text(m.get("text")) for m in chat_history if isinstance(m, dict) and m.get("from") == "patient"
    )
    unclear_markers = ("不清楚", "记不清", "不详", "不知道", "说不清", "忘了", "病史不清")
    if not any(token in patient_text for token in unclear_markers):
        missing = [str(item) for item in (case_profile.get("missing_critical_fields") or [])]
        if not any(any(token in field for token in ("主诉", "时间", "病程", "病史")) for field in missing):
            return ""
    candidates = [
        "我们换个方式：请按今天、昨天、近一周的时间线，回忆每天最突出的不适和活动受限情况。",
        "如果您本人记不清，可否请家属补充起病经过、既往病和用药情况？",
        "请从日常生活变化说起：睡眠、进食、活动耐力、工作或家务最近有什么改变？",
    ]
    for question in candidates:
        if not _question_already_asked(question, chat_history):
            return question
    return ""


def _caregiver_executability_question(case_profile: Dict[str, Any], chat_history: List[Any]) -> str:
    """固定询问照护者、功能、治疗目标理解、经济/取药可及性与偏好。"""
    profile = {str(k): clean_text(v) for k, v in case_profile.items()}
    needs_caregiver = profile.get("caregiver_function_preferences") in {"", "未知"}
    needs_social = any(profile.get(k) in {"", "未知"} for k in ("psychosocial_status", "family_economic_status"))
    if not (needs_caregiver or needs_social):
        return ""
    question = (
        "请补充：谁是主要照护者、您日常活动是否受限、对治疗目标的理解，"
        "以及医保/费用、取药复诊是否方便、对检查和治疗有什么偏好或顾虑？"
    )
    if _question_already_asked(question, chat_history):
        return ""
    return question


def _has_actionable_gaps(case_profile: Dict[str, Any]) -> bool:
    missing = case_profile.get("missing_critical_fields") or []
    return bool(missing)


def _question_from_missing_fields(
    case_profile: Dict[str, Any],
    chat_history: List[Any],
) -> str:
    missing = [str(item) for item in (case_profile.get("missing_critical_fields") or [])]
    question_bank = [
        ("主诉", "请您再具体描述本次最主要的不适、起病时间和演变过程，以及为什么选择现在就诊。"),
        ("诉求", "除了症状本身，您最担心的是什么？有没有特别害怕的严重疾病或希望优先解决的问题？"),
        ("用药", "请补充目前正在使用的药物（含处方药、非处方药、保健品/中草药、激素/免疫抑制剂）以及过敏史。"),
        ("过敏", "请说明是否有药物、食物或其他过敏史。"),
        ("既往", "请补充既往慢性疾病、手术史或长期用药情况。"),
        ("暴露", "近期是否有特殊接触史、旅居史、职业暴露或感染接触？"),
        ("妊娠", "请问目前月经、妊娠可能、避孕或生育计划相关情况。"),
        ("儿童", "请补充患儿年龄、精神状态、进食饮水及监护人观察到的变化。"),
        ("照护", "请补充主要照护者、日常功能状态，以及对检查和治疗的偏好。"),
        ("经济", "请补充您的医保类型与家庭经济情况，取药复诊是否方便，对检查和治疗费用是否有顾虑？"),
        ("心理", "请补充您目前的情绪状态、主要担忧，以及家人是否能在治疗中提供支持？"),
    ]
    for keyword, question in question_bank:
        if any(keyword in field for field in missing):
            if not _question_already_asked(question, chat_history):
                return question
    for field in missing:
        question = "请补充：%s" % field
        if not _question_already_asked(question, chat_history):
            return question
    return ""


# 通用「主诉系统 → 需要深挖的病史维度」映射。每条只按解剖/系统关键词触发，
# 询问该系统下对诊断和治疗安全最关键、但常被遗漏的病史，不绑定任何具体疾病。
_SYSTEM_HISTORY_PROBES: tuple[tuple[tuple[str, ...], tuple[str, ...], str], ...] = (
    (
        ("单眼", "视力下降", "复视", "畏光", "眼压", "晶状体", "提重物"),
        ("外伤", "隐形眼镜", "激素眼药水", "眼痛", "过敏", "用药"),
        "请补充既往眼病或眼科手术史、近期用力/提重物后是否立刻发作，以及目前用药、激素眼药水和药物过敏史。",
    ),
    (
        ("近端肌无力", "梳头", "上楼", "光敏", "蝶形", "雷诺", "晨僵"),
        ("吞咽", "呼吸困难", "雷诺", "口腔溃疡", "脱发", "尿"),
        "请补充肌无力是否对称进展，有无吞咽/呼吸困难、雷诺现象、口腔溃疡、脱发、尿色或尿量变化，以及用药和过敏史。",
    ),
    (
        ("淋巴结", "无痛肿块", "颈部肿块", "腹股沟肿块", "盗汗", "体重下降", "消瘦"),
        ("发热", "盗汗", "体重", "腹泻", "乳糜泻", "肿瘤", "免疫"),
        "请补充肿块持续时间和大小变化、有无发热盗汗体重下降、腹泻腹痛，以及既往乳糜泻/贫血、肿瘤或免疫用药史。",
    ),
    (
        ("腿痛", "骨痛", "跛行", "肌无力", "上楼梯困难", "身高", "发育", "低钙", "低磷", "维生素D"),
        ("素食", "奶", "日晒", "维生素", "营养", "抗癫痫", "长期用药", "饮食"),
        "请补充平时饮食结构（是否素食、奶制品和强化食品摄入）、日晒时长，以及是否长期用药（尤其影响骨代谢的药物）和药物过敏史。",
    ),
    (
        ("关节松弛", "关节不稳", "半脱位", "易瘀青", "皮肤过伸", "韧带松弛", "反复扭伤"),
        ("凝血", "瘀", "出血", "家族", "运动", "支具", "手术"),
        "请补充是否反复关节半脱位/扭伤、皮肤过伸或易瘀青出血、家族类似情况，以及当前运动训练强度和是否考虑过手术/支具。",
    ),
    (
        ("咳血", "血痰", "咯血", "气短", "呼吸困难"),
        ("肾", "尿", "过敏", "职业", "粉尘", "吸烟", "用药"),
        "请补充是否伴尿量或尿色改变、既往肾病或高血压史、药物过敏史、当前用药，以及职业/粉尘/吸烟等暴露情况。",
    ),
    (
        ("腹泻", "拉肚子", "呕吐", "抽筋", "手足抽搐", "乏力", "电解质"),
        ("食欲", "手术", "胰", "补", "饮水", "用药", "饮食"),
        "请补充近期腹泻/呕吐次数与持续时间、饮水进食情况、是否有胃肠手术或消化吸收疾病、正在服用的药物，以及是否补充过电解质。",
    ),
    (
        ("尿", "排尿", "尿频", "尿急", "尿痛", "膀胱", "前列腺"),
        ("发热", "分泌物", "性", "用药", "饮水", "夜尿"),
        "请补充是否伴发热或异常分泌物、饮水与排尿习惯（含夜尿）、既往泌尿系统病史，以及近期用药和性生活相关暴露史。",
    ),
    (
        ("皮疹", "水疱", "瘙痒", "湿疹", "脱屑", "皮肤"),
        ("接触", "过敏", "职业", "反复", "免疫", "用药", "发热"),
        "请补充皮损的诱因与接触史（金属/洗涤剂/新用品）、是否反复发作、有无发热或免疫抑制/用药背景，以及过敏史。",
    ),
    (
        ("胸痛", "胸闷", "心悸", "心慌", "晕厥"),
        ("诱因", "活动", "用药", "高血压", "血脂", "吸烟", "家族"),
        "请补充胸部症状与活动/情绪的关系、持续时间与缓解方式、心血管危险因素（高血压/血脂/吸烟/家族史）和当前用药。",
    ),
)


def _domain_specific_history_question(case_profile: Dict[str, Any], chat_history: List[Any]) -> str:
    """基于主诉系统给出一个高价值的深挖问题（通用，不针对具体疾病）。

    仅当主诉命中某个系统、且该系统的关键病史维度尚未在既往回答中出现时才追问，
    避免重复提问，也避免把问题写死到某个单一疾病上。
    """
    text = str(case_profile)
    patient_text = " ".join(
        clean_text(message.get("text"))
        for message in chat_history
        if isinstance(message, dict) and message.get("from") == "patient"
    )
    combined = text + patient_text

    for symptom_keywords, answered_markers, question in _SYSTEM_HISTORY_PROBES:
        if not any(keyword in combined for keyword in symptom_keywords):
            continue
        already_answered = any(marker in patient_text for marker in answered_markers)
        if already_answered:
            continue
        if not _question_already_asked(question, chat_history):
            return question

    return ""


def _essential_exams_complete(
    case_state: Dict[str, Any],
    case_profile: Dict[str, Any],
    *,
    differential: Optional[List[Any]] = None,
    exam_resolver: Any = None,
    limits: Any = None,
) -> bool:
    ordered = set(as_text_list(case_state.get("ordered_examinations")))
    if not ordered:
        return False
    if not _has_actionable_exam_results(case_state):
        return False

    actionable_count = _count_actionable_exam_results(case_state)
    min_objective = 1
    if limits is not None:
        min_objective = max(1, int(getattr(limits, "min_objective_exam_results", 1) or 1))
    if actionable_count < min_objective:
        return False

    if _arrhythmia_etiology_workup_incomplete(case_state, case_profile):
        return False

    if _has_decisive_disease_evidence(
        case_state,
        differential or [],
        exam_resolver=exam_resolver,
        case_profile=case_profile,
    ):
        return True

    min_exams = 3 if case_profile.get("red_flags") else 2
    if len(ordered) < min_exams:
        return False

    exam_need_summary = build_exam_need_summary(
        case_profile=case_profile,
        differential=differential or [],
        examinations={
            "ordered_examinations": list(ordered),
            "examination_results": case_state.get("examination_results") or {},
        },
        exam_resolver=exam_resolver,
    )
    missing_dimensions = exam_need_summary.get("missing_dimensions") or []
    critical_dimensions = {"基础严重程度评估", "确诊或病因证据", "治疗安全评估"}
    uncovered_critical = [
        item
        for item in missing_dimensions
        if isinstance(item, dict) and item.get("dimension") in critical_dimensions
    ]
    if uncovered_critical:
        return False
    recommended = set()
    for item in differential or []:
        if not isinstance(item, dict):
            continue
        for name in as_text_list(item.get("recommended_examinations")):
            resolved = exam_resolver(name) if callable(exam_resolver) else name
            recommended.add(resolved)
    if recommended:
        resolved_ordered = {
            exam_resolver(name) if callable(exam_resolver) else name
            for name in ordered
        }
        resolved_recommended = {
            exam_resolver(name) if callable(exam_resolver) else name
            for name in recommended
        }
        if not resolved_ordered & resolved_recommended:
            return False
    return len(missing_dimensions) <= 1


def _count_actionable_exam_results(case_state: Dict[str, Any]) -> int:
    ordered = set(as_text_list(case_state.get("ordered_examinations")))
    raw_results = case_state.get("examination_results") or {}
    if not ordered or not isinstance(raw_results, dict):
        return 0
    count = 0
    for name in ordered:
        result = raw_results.get(name)
        if not isinstance(result, dict):
            continue
        status = clean_text(result.get("status")).lower()
        text = clean_text(result.get("result"))
        if status not in {"unavailable", "invalid", "pending"} and text:
            count += 1
    return count
