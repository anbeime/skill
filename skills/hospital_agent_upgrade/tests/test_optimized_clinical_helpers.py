import time

from agent.agent import (
    _DEPARTMENT_EXAMINATION_MAP,
    _assess_diagnostic_confidence,
    _build_exam_order_justifications,
    _consultation_gap_question,
    _inferred_department_from_case,
    _mapped_examination_recommendations,
    _pre_prescription_safety_hook,
    _staged_exam_batch_limit,
    PatientCaseBudget,
    load_workflow_limits,
)
from types import SimpleNamespace

from agent.planner import (
    OPENING_CONSULTATION_QUESTION,
    _essential_exams_complete,
    _has_consultation_minimum,
    _next_consultation_question,
    _plan_next_step,
    consultation_hard_incomplete,
    consultation_gap_question,
    effective_max_doctor_turns,
    effective_max_exam_rounds,
)
from agent.diagnoser import (
    _normalize_final_diagnoses,
    apply_pre_treatment_safety_pause,
    build_contraindicated_drugs,
    enforce_treatment_safety_and_core_drugs,
    align_treatment_plan_with_mechanism,
    reconcile_diagnosis_before_treatment,
)
from agent.examiner import (
    _exam_batch_limit,
    build_exam_core_map,
    filter_examinations_by_current_evidence,
    prioritize_examinations,
    prune_redundant_modalities,
    resolve_exam_name,
    suggest_comprehensive_examinations,
)
from agent.utils import (
    build_disease_department_map,
    build_global_disease_map,
    load_disease_catalog,
    load_examination_catalog,
)
from agent.memory import MarkdownMemory


def test_assess_diagnostic_confidence_requires_objective_evidence():
    confidence = _assess_diagnostic_confidence(
        case_profile={
            "chief_complaint_timeline": "发热咳嗽3天，黄绿痰。",
            "past_history": "糖尿病",
            "medication_allergy_history": "无药物过敏",
            "personal_exposure_history": "无特殊接触史",
        },
        differential=[
            {"suspected_disease": "细菌性肺炎", "subjective_probability": 0.7},
            {"suspected_disease": "肺栓塞", "must_rule_out": True},
        ],
        examinations={"ordered_examinations": [], "examination_results": []},
    )

    assert confidence["recommendation"] == "continue_exam"
    assert "客观检查证据不足" in confidence["missing_evidence"]


def test_assess_diagnostic_confidence_accepts_list_exam_results():
    confidence = _assess_diagnostic_confidence(
        case_profile={
            "chief_complaint_timeline": "胸痛2小时。",
            "past_history": "高血压",
            "medication_allergy_history": "无药物过敏",
            "personal_exposure_history": "未知",
        },
        differential=[
            {"suspected_disease": "急性冠脉综合征", "must_rule_out": True},
            {"suspected_disease": "胸膜炎"},
            {"suspected_disease": "肋软骨炎"},
        ],
        examinations={
            "ordered_examinations": ["心电图（ECG）"],
            "examination_results": [
                {"检查": "心电图（ECG）", "结果": {"status": "abnormal", "result": "ST段抬高"}}
            ],
        },
    )

    assert confidence["recommendation"] == "ready_diagnose"


def test_staged_exam_batch_limit_first_round_orders_targeted_bundle():
    limit = _staged_exam_batch_limit(
        case_state={"exam_rounds": 0, "examination_results": {}},
        base_limit=6,
        remaining_exam_slots=6,
    )

    assert limit == 4


def test_staged_exam_batch_limit_followup_orders_complementary_tests():
    limit = _staged_exam_batch_limit(
        case_state={
            "exam_rounds": 1,
            "examination_results": {
                "心电图（ECG）": {"status": "abnormal", "result": "ST段抬高"}
            },
        },
        base_limit=4,
        remaining_exam_slots=5,
    )

    assert limit == 2


def test_essential_exams_complete_accepts_decisive_single_exam():
    complete = _essential_exams_complete(
        {
            "ordered_examinations": ["心电图（ECG）"],
            "examination_results": {
                "心电图（ECG）": {"status": "abnormal", "result": "ST段抬高"}
            },
        },
        {"chief_complaint_timeline": "突发胸痛2小时，无其他红旗。"},
        differential=[
            {
                "suspected_disease": "急性心肌梗死",
                "confidence_level": "高",
                "recommended_examinations": ["心电图（ECG）"],
                "exam_support": ["心电图ST段抬高"],
            }
        ],
    )

    assert complete is True


def test_prioritize_examinations_puts_urgent_tests_first():
    ordered = prioritize_examinations(
        ["血脂检测组合", "心电图（ECG）", "体格检查"],
        case_profile={"chief_complaint_timeline": "突发胸痛伴大汗", "red_flags": ["疑似急性冠脉综合征"]},
        differential=[{"suspected_disease": "心肌梗死", "must_rule_out": True}],
        exam_need_summary={"missing_dimensions": [{"dimension": "红旗并发症评估"}]},
    )

    assert ordered[0] == "心电图（ECG）"


def test_memory_ranking_uses_semantic_tokens_when_trigger_keywords_are_sparse(tmp_path):
    path = tmp_path / "memory.md"
    path.write_text(
        "# Baseline Doctor Memory\n\n"
        "## General Reflection cardiac\n\n"
        "Trigger Keywords: 胸痛\n\n"
        "### Reflection\n\n"
        "- **general_diagnosis_rules:** 当出现劳力性胸痛时，应优先评估冠脉缺血。\n\n"
        "## General Reflection eye\n\n"
        "Trigger Keywords: 斜视\n\n"
        "### Reflection\n\n"
        "- **general_diagnosis_rules:** 当儿童眼位偏斜时，应评估屈光和弱视。\n",
        encoding="utf-8",
    )
    memory = MarkdownMemory(path, max_notes=1)

    notes = memory.load_notes(
        case_profile={"chief_complaint_timeline": "活动后胸闷，休息后缓解，考虑心绞痛"}
    )

    assert notes
    assert "冠脉缺血" in notes[0]


def test_department_exam_map_targets_patellofemoral_checks():
    available = [
        "髌骨研磨试验（Clarke征）",
        "髌骨浮动试验（Ballottement）",
        "鼻内镜检查",
        "鼻旁窦CT扫描（Sinus CT）",
        "性激素全套检测",
        "勃起功能检测",
        "多普勒超声",
    ]
    core_map = build_exam_core_map(available)
    disease_catalog = load_disease_catalog()

    exams, reasons = _mapped_examination_recommendations(
        case_profile={"chief_complaint_timeline": "膝关节前痛半年，上下楼梯加重。"},
        differential=[{"suspected_disease": "髌骨软化症"}],
        ordered=set(),
        available_examinations=available,
        exam_resolver=lambda name: resolve_exam_name(name, core_map, available),
        disease_to_department=build_disease_department_map(disease_catalog),
        disease_map=build_global_disease_map(disease_catalog),
    )

    assert "髌骨研磨试验（Clarke征）" in exams
    assert "膝关节前痛" in reasons["髌骨研磨试验（Clarke征）"]


def test_department_exam_map_uses_standard_exam_names():
    catalog = load_examination_catalog()
    available = [name for names in catalog.values() for name in names]
    core_map = build_exam_core_map(available)
    unresolved = []

    for rules in _DEPARTMENT_EXAMINATION_MAP.values():
        for rule in rules:
            for name in rule.get("examinations") or []:
                if not resolve_exam_name(name, core_map, available):
                    unresolved.append(name)

    assert unresolved == []


def test_keyword_departments_cover_case_systems_without_differential():
    disease_catalog = load_disease_catalog()
    disease_to_department = build_disease_department_map(disease_catalog)
    disease_map = build_global_disease_map(disease_catalog)

    assert _inferred_department_from_case(
        case_profile={"chief_complaint_timeline": "婴儿胆汁性呕吐，出生后未排胎粪，腹胀。"},
        differential=[],
        disease_to_department=disease_to_department,
        disease_map=disease_map,
    ) == "儿科"
    assert _inferred_department_from_case(
        case_profile={"chief_complaint_timeline": "声嘶半年，喉部异物感，近期喘憋。"},
        differential=[],
        disease_to_department=disease_to_department,
        disease_map=disease_map,
    ) == "耳鼻咽喉科"
    assert _inferred_department_from_case(
        case_profile={"chief_complaint_timeline": "月经过多伴继发性痛经，盆腔疼痛。"},
        differential=[],
        disease_to_department=disease_to_department,
        disease_map=disease_map,
    ) == "妇产科"


def test_keyword_departments_capture_memory_heavy_disease_patterns():
    disease_catalog = load_disease_catalog()
    disease_to_department = build_disease_department_map(disease_catalog)
    disease_map = build_global_disease_map(disease_catalog)

    assert _inferred_department_from_case(
        case_profile={"chief_complaint_timeline": "反复劳力性呼吸困难，考虑特发性肺动脉高压。"},
        differential=[],
        disease_to_department=disease_to_department,
        disease_map=disease_map,
    ) == "心内科"
    assert _inferred_department_from_case(
        case_profile={"chief_complaint_timeline": "HIV/AIDS患者，CD4低，鸟粪暴露后发热干咳，考虑组织胞浆菌病。"},
        differential=[],
        disease_to_department=disease_to_department,
        disease_map=disease_map,
    ) == "感染科"
    assert _inferred_department_from_case(
        case_profile={"chief_complaint_timeline": "儿童下肢按压不褪色紫癜伴腹痛血尿，考虑过敏性紫癜。"},
        differential=[],
        disease_to_department=disease_to_department,
        disease_map=disease_map,
    ) == "免疫科"
    assert _inferred_department_from_case(
        case_profile={"chief_complaint_timeline": "2岁患儿自婴儿期起听力反应弱，叫名字不转头，语言发育迟缓。"},
        differential=[],
        disease_to_department=disease_to_department,
        disease_map=disease_map,
    ) == "耳鼻咽喉科"
    assert _inferred_department_from_case(
        case_profile={"chief_complaint_timeline": "右上腹不适伴血脂异常和肝酶升高，既往胰岛素抵抗。"},
        differential=[],
        disease_to_department=disease_to_department,
        disease_map=disease_map,
    ) == "内分泌科"


def test_department_exam_map_targets_pediatric_congenital_heart_disease():
    available = [
        "超声心动图",
        "心电图（ECG）",
        "胸部X线检查（CXR）",
        "血氨检测",
        "尿有机酸分析",
    ]
    core_map = build_exam_core_map(available)
    disease_catalog = load_disease_catalog()

    exams, reasons = _mapped_examination_recommendations(
        case_profile={"chief_complaint_timeline": "婴儿吃奶喘、多汗，听诊心脏杂音，考虑先天性心脏病。"},
        differential=[],
        ordered=set(),
        available_examinations=available,
        exam_resolver=lambda name: resolve_exam_name(name, core_map, available),
        disease_to_department=build_disease_department_map(disease_catalog),
        disease_map=build_global_disease_map(disease_catalog),
    )

    assert "超声心动图" in exams
    assert "心电图（ECG）" in exams
    assert "泛化代谢筛查" in reasons["超声心动图"]


def test_cad_exam_route_focuses_on_etiology_not_incidental_findings():
    disease_catalog = load_disease_catalog()
    disease_to_department = build_disease_department_map(disease_catalog)
    disease_map = build_global_disease_map(disease_catalog)
    available = [
        "心电图（ECG）",
        "心脏负荷试验",
        "超声心动图",
        "血脂检测组合",
        "炎症标志物检测组合",
        "冠状动脉造影",
        "动态心电图（Holter）",
        "心肌酶谱",
        "N末端B型利钠肽原（NT-proBNP）",
    ]
    core_map = build_exam_core_map(available)
    case_profile = {
        "chief_complaint_timeline": "活动如爬楼或提重物时胸口发紧，休息能缓解，持续8个月，近3周加重。",
        "past_history": "糖尿病",
        "red_flags": [],
    }
    differential = [{"suspected_disease": "冠状动脉粥样硬化性心脏病", "confidence_level": "高"}]

    mapped, _ = _mapped_examination_recommendations(
        case_profile=case_profile,
        differential=differential,
        ordered=set(),
        available_examinations=available,
        exam_resolver=lambda name: resolve_exam_name(name, core_map, available),
        disease_to_department=disease_to_department,
        disease_map=disease_map,
    )
    filtered = filter_examinations_by_current_evidence(
        mapped + ["动态心电图（Holter）", "心肌酶谱", "N末端B型利钠肽原（NT-proBNP）"],
        case_profile=case_profile,
        differential=differential,
        already_ordered=set(),
    )

    assert filtered == [
        "心电图（ECG）",
        "心脏负荷试验",
        "超声心动图",
        "血脂检测组合",
        "炎症标志物检测组合",
        "冠状动脉造影",
    ]


def test_department_exam_map_targets_metabolic_hyperlipidemia_and_amenorrhea():
    disease_catalog = load_disease_catalog()
    disease_to_department = build_disease_department_map(disease_catalog)
    disease_map = build_global_disease_map(disease_catalog)

    metabolic_available = [
        "血脂检测组合",
        "肝功能检查（LFTs）",
        "血糖检测",
        "腹部超声",
        "甲胎蛋白（AFP）检测",
        "凝血功能全套",
    ]
    metabolic_core_map = build_exam_core_map(metabolic_available)
    metabolic_exams, metabolic_reasons = _mapped_examination_recommendations(
        case_profile={"chief_complaint_timeline": "右上腹不适伴血脂异常和肝酶升高，既往胰岛素抵抗。"},
        differential=[],
        ordered=set(),
        available_examinations=metabolic_available,
        exam_resolver=lambda name: resolve_exam_name(name, metabolic_core_map, metabolic_available),
        disease_to_department=disease_to_department,
        disease_map=disease_map,
    )

    assert "血脂检测组合" in metabolic_exams
    assert "甲胎蛋白（AFP）检测" not in metabolic_exams
    assert "代谢综合征背景" in metabolic_reasons["血脂检测组合"]

    gyn_available = [
        "体格检查",
        "性激素全套检测",
        "基础体温（BBT）记录",
        "盆腔超声",
        "人绒毛膜促性腺激素（hCG）检测",
        "尿hCG妊娠试验",
        "全血细胞计数（CBC）",
    ]
    gyn_core_map = build_exam_core_map(gyn_available)
    gyn_exams, _ = _mapped_examination_recommendations(
        case_profile={"chief_complaint_timeline": "停经7个月，节食后体重骤降，工作压力大，考虑继发性闭经。"},
        differential=[],
        ordered=set(),
        available_examinations=gyn_available,
        exam_resolver=lambda name: resolve_exam_name(name, gyn_core_map, gyn_available),
        disease_to_department=disease_to_department,
        disease_map=disease_map,
    )

    assert gyn_exams[:5] == [
        "体格检查",
        "人绒毛膜促性腺激素（hCG）检测",
        "性激素全套检测",
        "基础体温（BBT）记录",
        "盆腔超声",
    ]
    assert "尿hCG妊娠试验" not in gyn_exams


def test_department_exam_map_ignores_differential_recommended_exam_noise():
    disease_catalog = load_disease_catalog()
    disease_to_department = build_disease_department_map(disease_catalog)
    disease_map = build_global_disease_map(disease_catalog)
    available = [
        "HIV病毒载量检测",
        "全血细胞计数（CBC）",
        "C反应蛋白（CRP）",
        "血培养",
    ]
    core_map = build_exam_core_map(available)

    exams, _ = _mapped_examination_recommendations(
        case_profile={"chief_complaint_timeline": "膝关节前痛半年，上下楼梯加重。"},
        differential=[
            {
                "recommended_examinations": [
                    "HIV病毒载量检测",
                    "血培养",
                    "正电子发射断层显像-计算机断层扫描（PET-CT）",
                ],
            }
        ],
        ordered=set(),
        available_examinations=available,
        exam_resolver=lambda name: resolve_exam_name(name, core_map, available),
        disease_to_department=disease_to_department,
        disease_map=disease_map,
    )

    assert exams == []


def test_department_exam_map_targets_opportunistic_infection_and_iga_vasculitis():
    disease_catalog = load_disease_catalog()

    infection_available = [
        "真菌培养及鉴定",
        "核酸扩增检测（NAAT）",
        "支气管肺泡灌洗液（BALF）分析",
        "胸部CT扫描（Chest CT）",
    ]
    infection_core_map = build_exam_core_map(infection_available)
    infection_exams, infection_reasons = _mapped_examination_recommendations(
        case_profile={"chief_complaint_timeline": "AIDS患者，CD4低，鸟粪暴露后发热干咳，考虑组织胞浆菌病。"},
        differential=[],
        ordered=set(),
        available_examinations=infection_available,
        exam_resolver=lambda name: resolve_exam_name(name, infection_core_map, infection_available),
        disease_to_department=build_disease_department_map(disease_catalog),
        disease_map=build_global_disease_map(disease_catalog),
    )

    assert "真菌培养及鉴定" in infection_exams
    assert "支气管肺泡灌洗液（BALF）分析" in infection_exams
    assert "病原学标本" in infection_reasons["真菌培养及鉴定"]

    vasculitis_available = [
        "全血细胞计数（CBC）",
        "C反应蛋白（CRP）",
        "尿液分析（UA）",
        "免疫球蛋白A（IgA）检测",
        "腹部超声",
    ]
    vasculitis_core_map = build_exam_core_map(vasculitis_available)
    vasculitis_exams, vasculitis_reasons = _mapped_examination_recommendations(
        case_profile={"chief_complaint_timeline": "儿童下肢紫癜伴腹痛、血尿。"},
        differential=[],
        ordered=set(),
        available_examinations=vasculitis_available,
        exam_resolver=lambda name: resolve_exam_name(name, vasculitis_core_map, vasculitis_available),
        disease_to_department=build_disease_department_map(disease_catalog),
        disease_map=build_global_disease_map(disease_catalog),
    )

    assert "免疫球蛋白A（IgA）检测" in vasculitis_exams
    assert "尿液分析（UA）" in vasculitis_exams
    assert "IgA 血管炎路径" in vasculitis_reasons["免疫球蛋白A（IgA）检测"]


def test_department_exam_map_targets_sinus_structural_red_flags():
    available = [
        "鼻内镜检查",
        "鼻旁窦CT扫描（Sinus CT）",
        "眼眶CT扫描（Orbital CT）",
        "视力检查",
        "眼球运动检查",
    ]
    core_map = build_exam_core_map(available)
    disease_catalog = load_disease_catalog()

    exams, reasons = _mapped_examination_recommendations(
        case_profile={"chief_complaint_timeline": "单侧鼻塞伴面部疼痛，近期视力模糊和畏光加重。"},
        differential=[],
        ordered=set(),
        available_examinations=available,
        exam_resolver=lambda name: resolve_exam_name(name, core_map, available),
        disease_to_department=build_disease_department_map(disease_catalog),
        disease_map=build_global_disease_map(disease_catalog),
    )

    assert "鼻内镜检查" in exams
    assert "鼻旁窦CT扫描（Sinus CT）" in exams
    assert "眼眶CT扫描（Orbital CT）" in exams
    assert "视力下降" in reasons["眼眶CT扫描（Orbital CT）"]


def test_department_exam_map_targets_optic_atrophy_and_laryngeal_cyst():
    disease_catalog = load_disease_catalog()
    disease_to_department = build_disease_department_map(disease_catalog)
    disease_map = build_global_disease_map(disease_catalog)

    eye_available = [
        "眼底镜检查",
        "视野检查",
        "色觉检查",
        "视觉诱发电位（VEP）",
        "脑和眼眶MRI",
        "脑和眼眶CT扫描（Brain/Orbital CT）",
    ]
    eye_core_map = build_exam_core_map(eye_available)
    eye_exams, _ = _mapped_examination_recommendations(
        case_profile={"chief_complaint_timeline": "视力下降，矫正视力无改善，中心暗点伴色觉障碍。"},
        differential=[],
        ordered=set(),
        available_examinations=eye_available,
        exam_resolver=lambda name: resolve_exam_name(name, eye_core_map, eye_available),
        disease_to_department=disease_to_department,
        disease_map=disease_map,
    )

    assert "色觉检查" in eye_exams
    assert "视觉诱发电位（VEP）" in eye_exams
    assert "脑和眼眶MRI" in eye_exams

    ent_available = ["喉镜检查", "颈部CT扫描（Neck CT）", "鼻咽喉镜检查"]
    ent_core_map = build_exam_core_map(ent_available)
    ent_exams, ent_reasons = _mapped_examination_recommendations(
        case_profile={"chief_complaint_timeline": "声嘶半年，喉部异物感，近期喘憋，考虑声门上囊肿。"},
        differential=[],
        ordered=set(),
        available_examinations=ent_available,
        exam_resolver=lambda name: resolve_exam_name(name, ent_core_map, ent_available),
        disease_to_department=disease_to_department,
        disease_map=disease_map,
    )

    assert "喉镜检查" in ent_exams
    assert "颈部CT扫描（Neck CT）" in ent_exams
    assert "声门上占位" in ent_reasons["喉镜检查"]

    hearing_available = [
        "听力测定",
        "鼓室压图及声导抗检查",
        "听性脑干反应（ABR）",
        "颞骨高分辨率CT扫描（Temporal Bone HRCT）",
        "耳镜检查",
    ]
    hearing_core_map = build_exam_core_map(hearing_available)
    hearing_exams, hearing_reasons = _mapped_examination_recommendations(
        case_profile={"chief_complaint_timeline": "患儿自婴儿期起听力反应弱，叫名字不转头，说话慢。"},
        differential=[],
        ordered=set(),
        available_examinations=hearing_available,
        exam_resolver=lambda name: resolve_exam_name(name, hearing_core_map, hearing_available),
        disease_to_department=disease_to_department,
        disease_map=disease_map,
    )

    assert hearing_exams[:4] == [
        "听力测定",
        "鼓室压图及声导抗检查",
        "听性脑干反应（ABR）",
        "颞骨高分辨率CT扫描（Temporal Bone HRCT）",
    ]
    assert "婴幼儿期起病" in hearing_reasons["听力测定"]


def test_department_exam_map_targets_copd_and_nail_onycholysis():
    disease_catalog = load_disease_catalog()
    disease_to_department = build_disease_department_map(disease_catalog)
    disease_map = build_global_disease_map(disease_catalog)

    respiratory_available = [
        "肺功能检查（PFTs）",
        "动脉血气（ABG）",
        "胸部X线检查（CXR）",
        "全血细胞计数（CBC）",
        "C反应蛋白（CRP）",
        "痰培养",
    ]
    respiratory_core_map = build_exam_core_map(respiratory_available)
    respiratory_exams, _ = _mapped_examination_recommendations(
        case_profile={"chief_complaint_timeline": "长期咳嗽咳痰，活动后气促，雾霾后黄痰加重，疑慢阻肺。"},
        differential=[],
        ordered=set(),
        available_examinations=respiratory_available,
        exam_resolver=lambda name: resolve_exam_name(name, respiratory_core_map, respiratory_available),
        disease_to_department=disease_to_department,
        disease_map=disease_map,
    )

    assert "肺功能检查（PFTs）" in respiratory_exams
    assert "动脉血气（ABG）" in respiratory_exams
    assert "痰培养" in respiratory_exams

    skin_available = ["皮肤镜检查", "真菌镜检", "真菌培养及鉴定"]
    skin_core_map = build_exam_core_map(skin_available)
    skin_exams, skin_reasons = _mapped_examination_recommendations(
        case_profile={"chief_complaint_timeline": "多个指甲远端甲剥离，甲板翘起发白，可见甲下角质碎屑。"},
        differential=[],
        ordered=set(),
        available_examinations=skin_available,
        exam_resolver=lambda name: resolve_exam_name(name, skin_core_map, skin_available),
        disease_to_department=disease_to_department,
        disease_map=disease_map,
    )

    assert "皮肤镜检查" in skin_exams
    assert "真菌镜检" in skin_exams
    assert "甲病变" in skin_reasons["皮肤镜检查"]


def test_department_exam_map_targets_sacroiliitis_mumps_and_congenital_structural_patterns():
    disease_catalog = load_disease_catalog()
    disease_to_department = build_disease_department_map(disease_catalog)
    disease_map = build_global_disease_map(disease_catalog)

    rheum_available = [
        "体格检查",
        "帕特里克试验（FABER）",
        "骨盆挤压与分离试验",
        "皮耶达卢征",
        "C反应蛋白（CRP）",
        "红细胞沉降率（ESR）",
        "磁共振成像（MRI）",
        "X线检查",
    ]
    rheum_core_map = build_exam_core_map(rheum_available)
    rheum_exams, _ = _mapped_examination_recommendations(
        case_profile={"chief_complaint_timeline": "晨起腰臀僵硬，骶髂区疼痛，帕特里克试验阳性。"},
        differential=[],
        ordered=set(),
        available_examinations=rheum_available,
        exam_resolver=lambda name: resolve_exam_name(name, rheum_core_map, rheum_available),
        disease_to_department=disease_to_department,
        disease_map=disease_map,
    )

    assert "帕特里克试验（FABER）" in rheum_exams
    assert "磁共振成像（MRI）" in rheum_exams

    infection_available = [
        "体格检查",
        "流行性腮腺炎病毒核酸检测（Mumps NAT）",
        "血清学抗体检测",
        "全血细胞计数（CBC）",
    ]
    infection_core_map = build_exam_core_map(infection_available)
    infection_exams, _ = _mapped_examination_recommendations(
        case_profile={"chief_complaint_timeline": "儿童耳下肿痛伴张口疼痛，近期接触腮腺炎患儿。"},
        differential=[],
        ordered=set(),
        available_examinations=infection_available,
        exam_resolver=lambda name: resolve_exam_name(name, infection_core_map, infection_available),
        disease_to_department=disease_to_department,
        disease_map=disease_map,
    )

    assert "流行性腮腺炎病毒核酸检测（Mumps NAT）" in infection_exams
    assert "血清学抗体检测" in infection_exams

    eye_available = [
        "裂隙灯检查",
        "眼压测量（IOP）",
        "角膜厚度测量",
        "超声生物显微镜检查（UBM）",
        "眼前节光学相干断层扫描（AS-OCT）",
        "房角镜检查",
        "眼部B超检查",
        "眼底镜检查",
        "眼前节摄影",
        "基因检测",
    ]
    eye_core_map = build_exam_core_map(eye_available)
    eye_exams, _ = _mapped_examination_recommendations(
        case_profile={"chief_complaint_timeline": "患儿出生即角膜发白，伴畏光流泪。"},
        differential=[],
        ordered=set(),
        available_examinations=eye_available,
        exam_resolver=lambda name: resolve_exam_name(name, eye_core_map, eye_available),
        disease_to_department=disease_to_department,
        disease_map=disease_map,
    )

    assert "角膜厚度测量" in eye_exams
    assert "超声生物显微镜检查（UBM）" in eye_exams

    pediatric_available = ["体格检查", "超声"]
    pediatric_core_map = build_exam_core_map(pediatric_available)
    pediatric_exams, _ = _mapped_examination_recommendations(
        case_profile={"chief_complaint_timeline": "婴儿持续歪头，头偏向一侧，可触及胸锁乳突肌条索样包块。"},
        differential=[],
        ordered=set(),
        available_examinations=pediatric_available,
        exam_resolver=lambda name: resolve_exam_name(name, pediatric_core_map, pediatric_available),
        disease_to_department=disease_to_department,
        disease_map=disease_map,
    )

    assert pediatric_exams == ["体格检查", "超声"]


def test_exam_reason_gate_demotes_vague_rationale():
    justifications = _build_exam_order_justifications(
        examinations=["细菌培养及鉴定"],
        case_profile={"chief_complaint_timeline": ""},
        differential=[],
        llm_reason="常规检查",
    )

    assert justifications["细菌培养及鉴定"]["priority"] == "LOW"


def test_prune_redundant_modalities_avoids_cross_round_hcg_duplicates():
    pruned = prune_redundant_modalities(
        ["尿hCG妊娠试验", "盆腔超声"],
        already_ordered=["人绒毛膜促性腺激素（hCG）检测"],
    )

    assert pruned == ["盆腔超声"]


def test_filter_examinations_by_current_evidence_rejects_screening_noise():
    filtered = filter_examinations_by_current_evidence(
        ["血培养", "C反应蛋白（CRP）", "全血细胞计数（CBC）", "HIV病毒载量检测", "鼻内镜检查", "听力测定"],
        case_profile={
            "chief_complaint_timeline": "2岁患儿自婴儿期起听力反应弱，说话慢，叫名字不转头。",
            "summary": "慢性听力发育问题，无耳痛流脓，无发热。",
            "red_flags": [],
            "missing_critical_fields": ["新生儿听力筛查结果", "家族听力障碍史"],
        },
        differential=[{"suspected_disease": "先天性中耳畸形"}],
        already_ordered=set(),
    )

    assert filtered == ["听力测定"]


def test_exam_routing_prefers_trichomonas_specific_tests_over_cervical_screening():
    catalog = load_examination_catalog()
    available = [name for names in catalog.values() for name in names]

    exams = suggest_comprehensive_examinations(
        case_profile={
            "chief_complaint_timeline": "黄白泡沫状阴道分泌物伴异味、瘙痒，既往抗真菌治疗无效。",
            "summary": "高度疑似滴虫性阴道炎。",
        },
        differential=[{"suspected_disease": "滴虫性阴道炎"}],
        exam_need_summary={"missing_dimensions": [{"dimension": "确诊或病因证据"}]},
        ordered=[],
        available_examinations=available,
        examination_catalog=catalog,
        max_count=5,
    )

    assert exams[:5] == ["显微镜检查", "快速抗原检测（RAT）", "DNA探针检测", "阴道毛滴虫培养", "阴道细胞学检查"]
    assert "阴道镜检查" not in exams


def test_exam_routing_prefers_cad_workup_for_exertional_chest_tightness():
    catalog = load_examination_catalog()
    available = [name for names in catalog.values() for name in names]

    exams = suggest_comprehensive_examinations(
        case_profile={
            "chief_complaint_timeline": "活动后胸口发紧伴气短8个月，近3周加重，爬楼和提重物诱发。",
            "past_history": "糖尿病，青霉素过敏。",
        },
        differential=[{"suspected_disease": "冠状动脉粥样硬化性心脏病（冠状动脉疾病，CAD）"}],
        exam_need_summary={"missing_dimensions": [{"dimension": "确诊或病因证据"}]},
        ordered=[],
        available_examinations=available,
        examination_catalog=catalog,
        max_count=6,
    )

    assert exams == ["心电图（ECG）", "心脏负荷试验", "超声心动图", "血脂检测组合", "炎症标志物检测组合", "冠状动脉造影"]


def test_exam_routing_prefers_neurosyphilis_workup_over_oncology_workup():
    catalog = load_examination_catalog()
    available = [name for names in catalog.values() for name in names]

    exams = suggest_comprehensive_examinations(
        case_profile={
            "chief_complaint_timeline": "HIV感染者有梅毒病史，反复头痛半年，近三周加重伴记忆力下降和情绪改变。",
            "past_history": "HIV感染，梅毒病史，2型糖尿病。",
        },
        differential=[{"suspected_disease": "神经梅毒"}],
        exam_need_summary={"missing_dimensions": [{"dimension": "确诊或病因证据"}]},
        ordered=[],
        available_examinations=available,
        examination_catalog=catalog,
        max_count=4,
    )

    assert exams[:3] == ["梅毒血清学检查", "脑脊液（CSF）分析", "磁共振成像（MRI）"]
    assert "正电子发射断层显像-计算机断层扫描（PET-CT）" not in exams
    assert "切除活检" not in exams


def test_exam_routing_prefers_joint_effusion_tests_and_generic_xray():
    catalog = load_examination_catalog()
    available = [name for names in catalog.values() for name in names]

    exams = suggest_comprehensive_examinations(
        case_profile={
            "chief_complaint_timeline": "右膝外伤后迅速肿胀疼痛，不能负重，考虑关节积液。",
            "summary": "需排除感染性关节炎、晶体性关节炎和骨折。",
        },
        differential=[{"suspected_disease": "关节积液"}],
        exam_need_summary={"missing_dimensions": [{"dimension": "确诊或病因证据"}]},
        ordered=[],
        available_examinations=available,
        examination_catalog=catalog,
        max_count=5,
    )

    assert "髌骨浮动试验（Ballottement）" in exams
    assert "肌肉骨骼超声（MSKUS）" in exams
    assert "滑液分析" in exams
    assert "骨骼X线检查" not in exams
    assert "关节X线检查" not in exams


def test_exam_routing_prefers_erythema_ab_igne_over_contact_dermatitis_tests():
    catalog = load_examination_catalog()
    available = [name for names in catalog.values() for name in names]

    exams = suggest_comprehensive_examinations(
        case_profile={
            "chief_complaint_timeline": "长期热源烘烤后出现网状红褐色皮损、脱屑，考虑火激红斑。",
            "summary": "局部皮肤问题，需排除恶变时考虑活检。",
        },
        differential=[{"suspected_disease": "火激红斑"}],
        exam_need_summary={"missing_dimensions": [{"dimension": "确诊或病因证据"}]},
        ordered=[],
        available_examinations=available,
        examination_catalog=catalog,
        max_count=4,
    )

    assert exams == ["体格检查", "皮肤活检"]
    assert "斑贴试验" not in exams


def test_exam_routing_prefers_valvular_af_workup_over_generic_heart_failure_bundle():
    catalog = load_examination_catalog()
    available = [name for names in catalog.values() for name in names]

    exams = suggest_comprehensive_examinations(
        case_profile={
            "chief_complaint_timeline": "心跳快且不规则，心悸气促伴头晕。",
            "past_history": "反复链球菌性咽炎史，疑似风湿性瓣膜病。",
        },
        differential=[{"suspected_disease": "心房颤动"}, {"suspected_disease": "风湿性心脏病"}],
        exam_need_summary={"missing_dimensions": [{"dimension": "确诊或病因证据"}]},
        ordered=[],
        available_examinations=available,
        examination_catalog=catalog,
        max_count=5,
    )

    assert exams == ["心电图（ECG）", "超声心动图", "经食管超声心动图（TEE）", "甲状腺功能检查（TFTs）", "体格检查"]


def test_exam_routing_prefers_corneal_ulcer_microbiology_bundle():
    catalog = load_examination_catalog()
    available = [name for names in catalog.values() for name in names]

    exams = suggest_comprehensive_examinations(
        case_profile={
            "chief_complaint_timeline": "隐形眼镜佩戴者角膜划伤后急性剧痛、畏光、视力下降。",
            "summary": "裂隙灯见中央上皮缺损伴致密基质浸润及前房反应。",
        },
        differential=[{"suspected_disease": "角膜溃疡"}],
        exam_need_summary={"missing_dimensions": [{"dimension": "确诊或病因证据"}]},
        ordered=[],
        available_examinations=available,
        examination_catalog=catalog,
        max_count=6,
    )

    assert exams == ["裂隙灯检查", "角膜刮片分析", "显微镜检查", "微生物培养及鉴定", "抗菌药物敏感性试验（AST）", "光学相干断层扫描（OCT）"]


def test_exam_routing_prefers_ckd_bone_disease_bundle_over_bone_marrow_workup():
    catalog = load_examination_catalog()
    available = [name for names in catalog.values() for name in names]

    exams = suggest_comprehensive_examinations(
        case_profile={
            "chief_complaint_timeline": "慢性肾脏病5期患者骨痛、瘙痒、跌倒后腹股沟痛。",
            "past_history": "长期使用磷结合剂和活性维生素D。",
            "summary": "eGFR极低并伴低钙高磷和代谢性酸中毒，考虑肾性骨病。",
        },
        differential=[{"suspected_disease": "终末期肾病"}, {"suspected_disease": "肾性骨营养不良"}],
        exam_need_summary={"missing_dimensions": [{"dimension": "确诊或病因证据"}]},
        ordered=[],
        available_examinations=available,
        examination_catalog=catalog,
        max_count=6,
    )

    assert exams == ["肾功能检查（RFTs）", "肾脏超声", "全血细胞计数（CBC）", "血清电解质", "尿液分析（UA）", "X线检查"]
    assert "骨髓穿刺和活检（BMAB）" not in exams


def test_normalize_final_diagnosis_prefers_patellar_softening_over_fuzzy_osteoarthritis():
    disease_catalog = load_disease_catalog()
    disease_map = build_global_disease_map(disease_catalog)

    diagnoses, demoted = _normalize_final_diagnoses(
        raw_diagnosis=["髌股关节疼痛综合征", "膝关节积液"],
        disease_map=disease_map,
        default_diagnosis="髌骨软化症",
        reasoning="结合膝前痛、上下楼加重及髌骨专科查体，考虑髌骨软化症，伴膝关节积液。",
        differential=[{"suspected_disease": "髌骨软化症", "confidence_level": "高"}],
        matched_disease="髌骨软化症",
        case_profile={"chief_complaint_timeline": "膝前痛半年，上下楼梯加重。"},
        examinations={"ordered_examinations": [], "examination_results": []},
        evidence_matrix=[
            {"problem": "髌股关节疼痛综合征", "conclusion": "confirmed"},
            {"problem": "膝关节积液", "conclusion": "comorbidity_confirmed"},
            {"problem": "髌骨软化症", "conclusion": "pending"},
        ],
    )

    assert diagnoses[0] == "髌骨软化症"
    assert "骨关节炎" not in diagnoses
    assert demoted == []


def test_normalize_final_diagnosis_promotes_paranasal_sinus_cyst_over_infection_label():
    disease_catalog = load_disease_catalog()
    disease_map = build_global_disease_map(disease_catalog)

    diagnoses, demoted = _normalize_final_diagnoses(
        raw_diagnosis=["急性细菌性鼻窦炎（右侧）", "过敏性鼻炎"],
        disease_map=disease_map,
        default_diagnosis="蜂窝织炎",
        reasoning="鼻内镜及鼻旁窦CT提示右侧鼻旁窦囊性病变，伴视力模糊和眶周压迫表现，主诊断考虑鼻旁窦囊肿。",
        differential=[{"suspected_disease": "蜂窝织炎", "confidence_level": "中"}],
        matched_disease="蜂窝织炎",
        case_profile={"chief_complaint_timeline": "单侧鼻塞、面部疼痛伴视力模糊。"},
        examinations={
            "ordered_examinations": ["鼻内镜检查", "鼻旁窦CT扫描（Sinus CT）"],
            "examination_results": [
                {"检查": "鼻旁窦CT扫描（Sinus CT）", "结果": {"status": "abnormal", "result": "右侧鼻旁窦囊性占位，眶内受压迹象。"}}
            ],
        },
        evidence_matrix=[
            {"problem": "急性细菌性鼻窦炎（右侧）", "conclusion": "confirmed"},
            {"problem": "眶内蜂窝织炎", "conclusion": "pending"},
            {"problem": "鼻息肉", "conclusion": "pending"},
        ],
    )

    assert diagnoses[0] == "鼻旁窦囊肿"
    assert "蜂窝织炎" not in diagnoses[:1]
    assert demoted == []


def test_normalize_final_diagnosis_keeps_reasoning_asserted_cad_primary():
    disease_catalog = load_disease_catalog()
    disease_map = build_global_disease_map(disease_catalog)

    diagnoses, _ = _normalize_final_diagnoses(
        raw_diagnosis=[
            "冠状动脉粥样硬化性心脏病（不稳定型心绞痛）",
            "心力衰竭（射血分数保留，HFpEF）",
            "骨关节炎",
            "原发性高血压",
        ],
        disease_map=disease_map,
        default_diagnosis="骨关节炎",
        reasoning="患者核心诊断为不稳定型心绞痛，依据负荷试验和动态心电图缺血证据；骨关节炎仅作为合并症处理。",
        differential=[{"suspected_disease": "冠状动脉粥样硬化性心脏病（冠状动脉疾病，CAD）", "confidence_level": "高"}],
        matched_disease="",
        case_profile={"chief_complaint_timeline": "劳力性胸闷气短8个月，近3周加重。"},
        examinations={
            "ordered_examinations": ["心脏负荷试验", "动态心电图（Holter）"],
            "examination_results": [
                {"检查": "心脏负荷试验", "结果": {"status": "abnormal", "result": "ST段压低2.0mm。"}},
                {"检查": "动态心电图（Holter）", "结果": {"status": "abnormal", "result": "活动期ST段压低。"}},
            ],
        },
        evidence_matrix=[
            {"problem": "冠状动脉粥样硬化性心脏病（不稳定型心绞痛）", "conclusion": "confirmed"},
            {"problem": "骨关节炎", "conclusion": "confirmed"},
        ],
    )

    assert diagnoses[0] == "冠状动脉粥样硬化性心脏病（冠状动脉疾病，CAD）"


def test_normalize_final_diagnosis_promotes_congenital_middle_ear_malformation():
    disease_map = build_global_disease_map(load_disease_catalog())

    diagnoses, _ = _normalize_final_diagnoses(
        raw_diagnosis=["中耳炎"],
        disease_map=disease_map,
        default_diagnosis="中耳炎",
        reasoning="患儿核心问题为先天性听小骨链畸形导致的传导性听力损失，CT+ABR+鼓室图证据确凿。",
        differential=[{"suspected_disease": "先天性中耳畸形", "confidence_level": "高"}],
        matched_disease="",
        case_profile={"chief_complaint_timeline": "出生即听力反应弱，语言发育迟缓。"},
        examinations={
            "ordered_examinations": ["颞骨高分辨率CT扫描（Temporal Bone HRCT）", "鼓室压图及声导抗检查", "听性脑干反应（ABR）"],
            "examination_results": [
                {"检查": "颞骨高分辨率CT扫描（Temporal Bone HRCT）", "结果": {"status": "abnormal", "result": "听小骨链畸形。"}},
                {"检查": "听性脑干反应（ABR）", "结果": {"status": "abnormal", "result": "符合传导性听力损失。"}},
            ],
        },
        evidence_matrix=[{"problem": "先天性中耳畸形", "conclusion": "confirmed"}],
    )

    assert diagnoses == ["先天性中耳畸形"]


def test_normalize_final_diagnosis_keeps_only_one_primary_standard_name():
    disease_map = build_global_disease_map(load_disease_catalog())

    diagnoses, _ = _normalize_final_diagnoses(
        raw_diagnosis=["风湿性心脏病", "二尖瓣狭窄"],
        disease_map=disease_map,
        default_diagnosis="风湿性心脏病",
        reasoning="结合超声证实的风湿性二尖瓣狭窄和心电图/Holter全程房颤，确诊风湿性心脏病合并心房颤动。",
        differential=[{"suspected_disease": "风湿性心脏病", "confidence_level": "高"}],
        matched_disease="",
        case_profile={"chief_complaint_timeline": "心跳快且不规则，心悸气促伴头晕。"},
        examinations={
            "ordered_examinations": ["心电图（ECG）", "超声心动图", "动态心电图（Holter）"],
            "examination_results": [
                {"检查": "心电图（ECG）", "结果": {"status": "abnormal", "result": "心房颤动，P波消失。"}},
                {"检查": "动态心电图（Holter）", "结果": {"status": "abnormal", "result": "全程房颤。"}},
            ],
        },
        evidence_matrix=[
            {"problem": "风湿性心脏病（二尖瓣狭窄）", "conclusion": "confirmed"},
            {"problem": "心房颤动", "conclusion": "confirmed"},
        ],
    )

    assert diagnoses == ["心房颤动"]


def test_normalize_final_diagnosis_prefers_corneal_ulcer_over_generic_keratitis():
    disease_map = build_global_disease_map(load_disease_catalog())

    diagnoses, _ = _normalize_final_diagnoses(
        raw_diagnosis=["角膜炎"],
        disease_map=disease_map,
        default_diagnosis="角膜炎",
        reasoning="有明确角膜划伤和隐形眼镜史，裂隙灯示中央上皮缺损伴致密基质浸润和前房反应，确诊角膜溃疡。",
        differential=[{"suspected_disease": "角膜溃疡", "confidence_level": "高"}],
        matched_disease="",
        case_profile={"chief_complaint_timeline": "急性眼痛畏光，视力下降。"},
        examinations={
            "ordered_examinations": ["裂隙灯检查"],
            "examination_results": [
                {"检查": "裂隙灯检查", "结果": {"status": "abnormal", "result": "中央上皮缺损、基质浸润、前房反应。"}},
            ],
        },
        evidence_matrix=[
            {"problem": "角膜溃疡", "conclusion": "confirmed"},
            {"problem": "细菌性角膜炎", "conclusion": "confirmed"},
        ],
    )

    assert diagnoses[0] == "角膜溃疡"
    assert "角膜炎" not in diagnoses


def test_normalize_final_diagnosis_promotes_esrd_and_osteoporosis():
    disease_map = build_global_disease_map(load_disease_catalog())

    diagnoses, _ = _normalize_final_diagnoses(
        raw_diagnosis=["肾性骨营养不良"],
        disease_map=disease_map,
        default_diagnosis="肾性骨营养不良",
        reasoning="CKD5期伴eGFR 6和尿毒症症状，应按终末期肾病处理；骨髓示骨量减少，存在骨质疏松背景。",
        differential=[{"suspected_disease": "终末期肾病", "confidence_level": "高"}],
        matched_disease="",
        case_profile={"chief_complaint_timeline": "慢性肾脏病5期患者骨痛、瘙痒、跌倒后腹股沟痛。"},
        examinations={
            "ordered_examinations": ["肾功能检查（RFTs）", "血清电解质"],
            "examination_results": [
                {"检查": "肾功能检查（RFTs）", "结果": {"status": "abnormal", "result": "肌酐7.8mg/dL，eGFR 6mL/min。"}},
                {"检查": "血清电解质", "结果": {"status": "abnormal", "result": "低钙高磷。"}},
            ],
        },
        evidence_matrix=[
            {"problem": "慢性肾脏病", "conclusion": "confirmed"},
            {"problem": "肾性骨营养不良", "conclusion": "confirmed"},
        ],
    )

    assert diagnoses == ["终末期肾病"]


def test_normalize_final_diagnosis_prunes_unsupported_osteoporosis_from_hyperlipidemia():
    disease_map = build_global_disease_map(load_disease_catalog())

    diagnoses, demoted = _normalize_final_diagnoses(
        raw_diagnosis=["混合型高脂血症", "骨质疏松症"],
        disease_map=disease_map,
        default_diagnosis="混合型高脂血症",
        reasoning="患者眼睑黄色瘤，血脂检测提示LDL和甘油三酯升高，诊断混合型高脂血症；骨质疏松症缺乏当前骨痛、骨折或DEXA证据。",
        differential=[{"suspected_disease": "混合型高脂血症", "confidence_level": "高"}],
        matched_disease="混合型高脂血症",
        case_profile={"chief_complaint_timeline": "眼睑黄色瘤，上腹胀，担心影响工作。"},
        examinations={
            "ordered_examinations": ["血脂检测组合"],
            "examination_results": [
                {"检查": "血脂检测组合", "结果": {"status": "abnormal", "result": "LDL-C升高，甘油三酯升高。"}}
            ],
        },
        evidence_matrix=[
            {
                "problem": "混合型高脂血症",
                "history_support": ["黄色瘤"],
                "exam_support": ["血脂异常"],
                "conclusion": "confirmed",
            }
        ],
    )

    assert diagnoses == ["混合型高脂血症"]
    assert demoted == []


def test_normalize_final_diagnosis_prunes_unsupported_osteoarthritis_from_joint_effusion():
    disease_map = build_global_disease_map(load_disease_catalog())

    diagnoses, demoted = _normalize_final_diagnoses(
        raw_diagnosis=["关节积液", "骨关节炎"],
        disease_map=disease_map,
        default_diagnosis="关节积液",
        reasoning="外伤后右膝迅速肿胀，浮髌试验阳性，超声见关节腔积液，诊断关节积液；骨关节炎缺乏慢性退变证据。",
        differential=[{"suspected_disease": "关节积液", "confidence_level": "高"}],
        matched_disease="关节积液",
        case_profile={"chief_complaint_timeline": "右膝外伤后迅速肿胀疼痛，不能负重。"},
        examinations={
            "ordered_examinations": ["体格检查", "肌肉骨骼超声（MSKUS）"],
            "examination_results": [
                {"检查": "体格检查", "结果": {"status": "abnormal", "result": "浮髌试验阳性。"}},
                {"检查": "肌肉骨骼超声（MSKUS）", "结果": {"status": "abnormal", "result": "膝关节腔积液。"}},
            ],
        },
        evidence_matrix=[
            {
                "problem": "关节积液",
                "history_support": ["外伤后肿胀"],
                "exam_support": ["浮髌阳性", "超声积液"],
                "conclusion": "confirmed",
            }
        ],
    )

    assert diagnoses == ["关节积液"]
    assert demoted == []


def test_normalize_final_diagnosis_avoids_short_course_bacterial_sinusitis_and_background_asthma():
    disease_catalog = load_disease_catalog()
    disease_map = build_global_disease_map(disease_catalog)

    diagnoses, demoted = _normalize_final_diagnoses(
        raw_diagnosis=["急性细菌性鼻窦炎", "哮喘"],
        disease_map=disease_map,
        default_diagnosis="急性鼻窦炎",
        reasoning=(
            "病程仅2天，鼻涕变稠但不符合细菌性鼻窦炎通常>10天或双相恶化的时间窗；"
            "目前更倾向病毒性上呼吸道感染。哮喘为既往风险背景，听诊未闻及哮鸣音。"
        ),
        differential=[
            {"suspected_disease": "急性细菌性鼻窦炎", "confidence_level": "低"},
            {"suspected_disease": "上呼吸道感染", "confidence_level": "高"},
            {"suspected_disease": "哮喘", "confidence_level": "低"},
        ],
        matched_disease="急性鼻窦炎",
        case_profile={
            "chief_complaint_timeline": "鼻塞、清涕转稠、低热2天，伴胸闷。",
            "past_history": "支气管哮喘",
        },
        examinations={
            "ordered_examinations": ["体格检查"],
            "examination_results": [
                {"检查": "体格检查", "结果": {"status": "normal", "result": "双肺未闻及哮鸣音，无高热。"}}
            ],
        },
        evidence_matrix=[
            {"problem": "急性细菌性鼻窦炎", "conclusion": "excluded"},
            {"problem": "上呼吸道感染", "conclusion": "confirmed"},
            {"problem": "哮喘", "conclusion": "pending"},
        ],
    )

    assert diagnoses == ["上呼吸道感染"]
    assert demoted == []


def test_normalize_final_diagnosis_promotes_optic_atrophy_over_diabetes_background():
    disease_catalog = load_disease_catalog()
    disease_map = build_global_disease_map(disease_catalog)

    diagnoses, demoted = _normalize_final_diagnoses(
        raw_diagnosis=["2型糖尿病（T2DM）"],
        disease_map=disease_map,
        default_diagnosis="2型糖尿病",
        reasoning="患者糖尿病为既往背景；眼底镜见双侧视盘苍白，视野检查见右眼中心暗点，色觉异常，最符合视神经萎缩。",
        differential=[{"suspected_disease": "缺血性视神经病变", "confidence_level": "高"}],
        matched_disease="2型糖尿病",
        case_profile={"chief_complaint_timeline": "视力下降，矫正视力无改善，红绿色觉障碍。", "past_history": "2型糖尿病"},
        examinations={
            "ordered_examinations": ["眼底镜检查", "视野检查", "色觉检查"],
            "examination_results": [
                {"检查": "眼底镜检查", "结果": {"status": "abnormal", "result": "双侧视盘苍白。"}},
                {"检查": "视野检查", "结果": {"status": "abnormal", "result": "右眼中心暗点。"}},
            ],
        },
        evidence_matrix=[{"problem": "2型糖尿病", "conclusion": "confirmed"}],
    )

    assert diagnoses[0] == "视神经萎缩"
    assert "2型糖尿病" not in diagnoses[:1]
    assert demoted == []


def test_normalize_final_diagnosis_drops_generic_amenorrhea_when_specific_label_exists():
    disease_catalog = load_disease_catalog()
    disease_map = build_global_disease_map(disease_catalog)

    diagnoses, demoted = _normalize_final_diagnoses(
        raw_diagnosis=["闭经", "继发性闭经"],
        disease_map=disease_map,
        default_diagnosis="闭经",
        reasoning="患者停经7个月，节食后体重骤降，最符合继发性闭经。",
        differential=[{"suspected_disease": "继发性闭经", "confidence_level": "高"}],
        matched_disease="继发性闭经",
        case_profile={"chief_complaint_timeline": "停经7个月，节食后体重骤降。"},
        examinations={"ordered_examinations": [], "examination_results": []},
        evidence_matrix=[{"problem": "继发性闭经", "conclusion": "confirmed"}],
    )

    assert diagnoses == ["继发性闭经"]
    assert demoted == []


def test_normalize_final_diagnosis_maps_functional_hypothalamic_amenorrhea_to_secondary_amenorrhea():
    disease_catalog = load_disease_catalog()
    disease_map = build_global_disease_map(disease_catalog)

    diagnoses, demoted = _normalize_final_diagnoses(
        raw_diagnosis=["功能性下丘脑性闭经", "体重过低（BMI 17.2 kg/m^2）"],
        disease_map=disease_map,
        default_diagnosis="闭经",
        reasoning="患者表现为典型的下丘脑性闭经，停经7个月，节食后体重骤降，已排除妊娠。",
        differential=[{"suspected_disease": "下丘脑性闭经", "confidence_level": "高"}],
        matched_disease="闭经",
        case_profile={"chief_complaint_timeline": "停经7个月，节食后体重骤降，工作压力大。"},
        examinations={
            "ordered_examinations": ["人绒毛膜促性腺激素（hCG）检测", "性激素全套检测", "体格检查"],
            "examination_results": [
                {"检查": "人绒毛膜促性腺激素（hCG）检测", "结果": {"status": "normal", "result": "hCG阴性。"}},
                {"检查": "性激素全套检测", "结果": {"status": "abnormal", "result": "FSH低，雌二醇低。"}},
                {"检查": "体格检查", "结果": {"status": "abnormal", "result": "BMI 17.2 kg/m^2。"}},
            ],
        },
        evidence_matrix=[
            {
                "problem": "功能性下丘脑性闭经",
                "history_support": ["停经7个月", "节食后体重骤降"],
                "exam_support": ["hCG阴性", "FSH低", "雌二醇低"],
                "conclusion": "confirmed",
            }
        ],
    )

    assert diagnoses == ["继发性闭经"]
    assert demoted == []


def test_normalize_final_diagnosis_promotes_copd_over_asthma_when_fixed_obstruction():
    disease_catalog = load_disease_catalog()
    disease_map = build_global_disease_map(disease_catalog)

    diagnoses, demoted = _normalize_final_diagnoses(
        raw_diagnosis=["哮喘"],
        disease_map=disease_map,
        default_diagnosis="哮喘",
        reasoning="肺功能检查提示支气管扩张剂后FEV1/FVC=0.56，固定性气流受限，结合长期咳嗽咳痰，诊断为慢性阻塞性肺疾病。",
        differential=[{"suspected_disease": "AECOPD", "confidence_level": "高"}],
        matched_disease="哮喘",
        case_profile={"chief_complaint_timeline": "多年咳嗽咳痰，活动后气促，黄痰加重。"},
        examinations={
            "ordered_examinations": ["肺功能检查（PFTs）"],
            "examination_results": [
                {"检查": "肺功能检查（PFTs）", "结果": {"status": "abnormal", "result": "支气管扩张剂后 FEV1/FVC: 0.56，FEV1 48%。"}}
            ],
        },
        evidence_matrix=[{"problem": "哮喘", "conclusion": "confirmed"}],
    )

    assert diagnoses[0] == "慢性阻塞性肺疾病"
    assert "哮喘" not in diagnoses[:1]
    assert demoted == []


def test_normalize_final_diagnosis_maps_chronic_coronary_syndrome_back_to_catalog_cad():
    disease_catalog = load_disease_catalog()
    disease_map = build_global_disease_map(disease_catalog)

    diagnoses, demoted = _normalize_final_diagnoses(
        raw_diagnosis=["冠状动脉粥样硬化性心脏病", "慢性心力衰竭", "心律失常"],
        disease_map=disease_map,
        default_diagnosis="冠状动脉粥样硬化性心脏病",
        reasoning="结合病史、心电图及超声心动图，最终诊断考虑慢性冠脉综合征，慢性心力衰竭和心律失常作为合并症处理。",
        differential=[{"suspected_disease": "冠状动脉粥样硬化性心脏病", "confidence_level": "高"}],
        matched_disease="",
        case_profile={"chief_complaint_timeline": "活动后胸闷胸痛反复发作。"},
        examinations={
            "ordered_examinations": ["心电图（ECG）", "超声心动图"],
            "examination_results": [
                {"检查": "心电图（ECG）", "结果": {"status": "abnormal", "result": "ST-T改变。"}},
                {"检查": "超声心动图", "结果": {"status": "abnormal", "result": "左室舒张功能减低。"}},
            ],
        },
        evidence_matrix=[
            {"problem": "冠状动脉粥样硬化性心脏病", "conclusion": "confirmed"},
            {"problem": "慢性心力衰竭", "conclusion": "comorbidity_confirmed"},
            {"problem": "心律失常", "conclusion": "comorbidity_confirmed"},
        ],
    )

    assert diagnoses[0] == "冠状动脉粥样硬化性心脏病（冠状动脉疾病，CAD）"
    assert "慢性冠脉综合征" not in diagnoses
    assert set(demoted) == {"心力衰竭", "心律失常"}


def test_final_diagnosis_closure_rejects_non_catalog_names():
    disease_catalog = load_disease_catalog()
    disease_map = build_global_disease_map(disease_catalog)

    diagnoses, _ = _normalize_final_diagnoses(
        raw_diagnosis=["模型自造冠脉病", "慢性冠脉综合征"],
        disease_map=disease_map,
        default_diagnosis="冠状动脉粥样硬化性心脏病",
        reasoning="最终诊断考虑慢性冠脉综合征，心电图和症状支持冠状动脉疾病。",
        differential=[{"suspected_disease": "冠状动脉粥样硬化性心脏病", "confidence_level": "高"}],
        matched_disease="",
        case_profile={"chief_complaint_timeline": "活动后胸痛，休息后缓解。"},
        examinations={"ordered_examinations": ["心电图（ECG）"], "examination_results": []},
        evidence_matrix=[],
    )

    assert diagnoses == ["冠状动脉粥样硬化性心脏病（冠状动脉疾病，CAD）"]


def test_normalize_final_diagnosis_rescues_cad_when_self_check_drifts_to_osteoarthritis():
    disease_catalog = load_disease_catalog()
    disease_map = build_global_disease_map(disease_catalog)

    diagnoses, _ = _normalize_final_diagnoses(
        raw_diagnosis=["骨关节炎"],
        disease_map=disease_map,
        default_diagnosis="骨关节炎",
        reasoning="患者核心诊断为不稳定型心绞痛，依据充分的负荷试验和动态心电图缺血证据。",
        differential=[{"suspected_disease": "冠状动脉粥样硬化性心脏病", "confidence_level": "高"}],
        matched_disease="",
        case_profile={
            "chief_complaint_timeline": "活动如爬楼或提重物时胸口发紧，休息能缓解，持续8个月，近3周加重。",
            "past_history": "糖尿病",
        },
        examinations={
            "ordered_examinations": ["心脏负荷试验", "动态心电图（Holter）", "心肌酶谱", "体格检查"],
            "examination_results": [
                {
                    "检查": "心脏负荷试验",
                    "结果": {
                        "status": "abnormal",
                        "result": {
                            "心肌缺血": "缺血反应阳性",
                            "运动诱发症状": "伴劳力性胸部压迫感",
                            "心电图ST段改变": "低负荷时出现2.0 mm ST段压低",
                        },
                    },
                },
                {
                    "检查": "动态心电图（Holter）",
                    "结果": {
                        "status": "abnormal",
                        "result": {"心电图ST段改变": "日常活动期间可见ST段水平型压低1.0-1.5 mm"},
                    },
                },
                {
                    "检查": "体格检查",
                    "结果": {
                        "status": "abnormal",
                        "result": {"肌肉骨骼": "双膝关节肿胀、活动受限，可见骨关节炎改变"},
                    },
                },
            ],
        },
        evidence_matrix=[],
    )

    assert diagnoses[0] == "冠状动脉粥样硬化性心脏病（冠状动脉疾病，CAD）"
    assert "骨关节炎" not in diagnoses[:1]


def test_reconcile_diagnosis_before_treatment_filters_plan_to_catalog():
    disease_catalog = load_disease_catalog()
    disease_map = build_global_disease_map(disease_catalog)

    plan = reconcile_diagnosis_before_treatment(
        {
            "diagnosis": ["模型自造冠脉病", "慢性冠脉综合征"],
            "reasoning": "最终诊断考虑慢性冠脉综合征。",
            "treatment_plan": "按冠脉疾病处理。",
            "evidence_matrix": [],
        },
        differential=[{"suspected_disease": "冠状动脉粥样硬化性心脏病", "confidence_level": "高"}],
        default_diagnosis="冠状动脉粥样硬化性心脏病",
        disease_map=disease_map,
        case_profile={"chief_complaint_timeline": "活动后胸痛。"},
        examinations={},
    )

    assert plan["diagnosis"] == ["冠状动脉粥样硬化性心脏病（冠状动脉疾病，CAD）"]


def test_normalize_final_diagnosis_promotes_laryngeal_cyst_from_workup():
    disease_catalog = load_disease_catalog()
    disease_map = build_global_disease_map(disease_catalog)

    diagnoses, demoted = _normalize_final_diagnoses(
        raw_diagnosis=["未明确诊断"],
        disease_map=disease_map,
        default_diagnosis="未明确诊断",
        reasoning="声嘶伴异物感，喉镜及颈部CT发现声门上囊性占位并部分气道受压，最终诊断为喉囊肿。",
        differential=[{"suspected_disease": "喉部占位性病变", "confidence_level": "中"}],
        matched_disease="",
        case_profile={"chief_complaint_timeline": "声嘶半年，喉部异物感，近期喘憋。"},
        examinations={
            "ordered_examinations": ["喉镜检查", "颈部CT扫描（Neck CT）"],
            "examination_results": [
                {"检查": "喉镜检查", "结果": {"status": "abnormal", "result": "声门上囊性病变。"}},
                {"检查": "颈部CT扫描（Neck CT）", "结果": {"status": "abnormal", "result": "喉部囊肿，部分气道受压。"}},
            ],
        },
        evidence_matrix=[],
    )

    assert diagnoses[0] == "喉囊肿"
    assert demoted == []


def test_normalize_final_diagnosis_recovers_renal_cyst_from_non_catalog_pyelo_label():
    disease_map = build_global_disease_map(load_disease_catalog())

    diagnoses, _ = _normalize_final_diagnoses(
        raw_diagnosis=["急性肾盂肾炎"],
        disease_map=disease_map,
        default_diagnosis="未明确诊断",
        reasoning="尿培养阳性并有尿路刺激征，左肾中极囊肿是明确的结构性病变。",
        differential=[{"suspected_disease": "复杂性肾盂肾炎", "confidence_level": "高"}],
        matched_disease="",
        case_profile={"chief_complaint_timeline": "左腰痛伴尿急尿痛。"},
        examinations={
            "ordered_examinations": ["泌尿道超声"],
            "examination_results": [
                {
                    "检查": "泌尿道超声",
                    "结果": {
                        "status": "abnormal",
                        "result": "左肾中极见6.0cm薄壁无回声囊肿，囊内见出血性碎屑。",
                    },
                }
            ],
        },
        evidence_matrix=[
            {
                "problem": "肾囊肿",
                "exam_support": ["泌尿道超声发现左肾囊肿"],
                "conclusion": "comorbidity_confirmed",
            }
        ],
    )

    assert diagnoses[0] == "肾囊肿"


def test_normalize_final_diagnosis_recovers_nummular_eczema_from_contact_dermatitis_label():
    disease_map = build_global_disease_map(load_disease_catalog())

    diagnoses, _ = _normalize_final_diagnoses(
        raw_diagnosis=["过敏性接触性皮炎"],
        disease_map=disease_map,
        default_diagnosis="未明确诊断",
        reasoning="皮肤活检示海绵状皮炎，真菌镜检阴性，当前主诊断应为钱币状湿疹。",
        differential=[{"suspected_disease": "过敏性接触性皮炎", "confidence_level": "高"}],
        matched_disease="",
        case_profile={"chief_complaint_timeline": "四肢圆形斑块伴剧烈瘙痒。"},
        examinations={
            "ordered_examinations": ["皮肤活检", "真菌镜检"],
            "examination_results": [
                {
                    "检查": "皮肤活检",
                    "结果": {
                        "status": "abnormal",
                        "result": "海绵状皮炎，伴嗜酸性粒细胞。",
                    },
                },
                {
                    "检查": "真菌镜检",
                    "结果": {"status": "normal", "result": "真菌镜检阴性。"},
                },
            ],
        },
        evidence_matrix=[],
    )

    assert diagnoses[0] == "钱币状湿疹"


def test_normalize_final_diagnosis_promotes_onycholysis_over_psoriasis():
    disease_catalog = load_disease_catalog()
    disease_map = build_global_disease_map(disease_catalog)

    diagnoses, demoted = _normalize_final_diagnoses(
        raw_diagnosis=["银屑病"],
        disease_map=disease_map,
        default_diagnosis="银屑病",
        reasoning="皮肤镜显示远端甲剥离和甲下角质碎屑；未见典型银白色鳞屑皮损，本次主诊断为甲剥离。",
        differential=[{"suspected_disease": "银屑病甲", "confidence_level": "中"}],
        matched_disease="银屑病",
        case_profile={"chief_complaint_timeline": "多个指甲远端甲板翘起发白，可见甲下角质碎屑。"},
        examinations={
            "ordered_examinations": ["皮肤镜检查"],
            "examination_results": [
                {"检查": "皮肤镜检查", "结果": {"status": "abnormal", "result": "远端甲剥离，甲下角质碎屑。"}}
            ],
        },
        evidence_matrix=[{"problem": "银屑病", "conclusion": "confirmed"}],
    )

    assert diagnoses[0] == "甲剥离"
    assert "银屑病" not in diagnoses[:1]
    assert demoted == []


def test_normalize_final_diagnosis_promotes_sacroiliitis_mumps_and_pediatric_structural_diseases():
    disease_catalog = load_disease_catalog()
    disease_map = build_global_disease_map(disease_catalog)

    diagnoses, _ = _normalize_final_diagnoses(
        raw_diagnosis=["腰椎间盘突出症（腰椎间盘突出）"],
        disease_map=disease_map,
        default_diagnosis="腰椎间盘突出症（腰椎间盘突出）",
        reasoning="患者晨起腰臀僵硬，骶髂区压痛，帕特里克试验阳性，MRI支持双侧骶髂关节炎。",
        differential=[{"suspected_disease": "骶髂炎", "confidence_level": "高"}],
        matched_disease="腰椎间盘突出症（腰椎间盘突出）",
        case_profile={"chief_complaint_timeline": "慢性腰臀痛伴晨僵。"},
        examinations={
            "ordered_examinations": ["帕特里克试验（FABER）", "磁共振成像（MRI）"],
            "examination_results": [
                {"检查": "帕特里克试验（FABER）", "结果": {"status": "abnormal", "result": "阳性。"}},
                {"检查": "磁共振成像（MRI）", "结果": {"status": "abnormal", "result": "双侧骶髂关节炎性改变。"}},
            ],
        },
        evidence_matrix=[],
    )
    assert diagnoses[0] == "骶髂关节炎"

    diagnoses, _ = _normalize_final_diagnoses(
        raw_diagnosis=["未明确诊断"],
        disease_map=disease_map,
        default_diagnosis="未明确诊断",
        reasoning="儿童耳下肿痛，体检见腮腺肿大压痛，Mumps NAT阳性，诊断流行性腮腺炎。",
        differential=[{"suspected_disease": "腮腺炎", "confidence_level": "高"}],
        matched_disease="",
        case_profile={"chief_complaint_timeline": "发热伴双侧耳下肿痛。"},
        examinations={
            "ordered_examinations": ["流行性腮腺炎病毒核酸检测（Mumps NAT）"],
            "examination_results": [
                {"检查": "流行性腮腺炎病毒核酸检测（Mumps NAT）", "结果": {"status": "abnormal", "result": "阳性。"}},
            ],
        },
        evidence_matrix=[],
    )
    assert diagnoses[0] == "流行性腮腺炎"

    diagnoses, _ = _normalize_final_diagnoses(
        raw_diagnosis=["先天性青光眼", "形觉剥夺性弱视"],
        disease_map=disease_map,
        default_diagnosis="先天性青光眼",
        reasoning="患儿出生即角膜混浊，裂隙灯及UBM支持先天性角膜混浊，青光眼为并存风险。",
        differential=[{"suspected_disease": "角膜混浊", "confidence_level": "高"}],
        matched_disease="先天性青光眼",
        case_profile={"chief_complaint_timeline": "出生即角膜发白，畏光流泪。"},
        examinations={
            "ordered_examinations": ["裂隙灯检查", "超声生物显微镜检查（UBM）"],
            "examination_results": [
                {"检查": "裂隙灯检查", "结果": {"status": "abnormal", "result": "双眼角膜混浊。"}},
                {"检查": "超声生物显微镜检查（UBM）", "结果": {"status": "abnormal", "result": "前节发育异常，支持先天性角膜混浊。"}},
            ],
        },
        evidence_matrix=[],
    )
    assert diagnoses[0] == "先天性角膜混浊"

    diagnoses, _ = _normalize_final_diagnoses(
        raw_diagnosis=["非霍奇金淋巴瘤"],
        disease_map=disease_map,
        default_diagnosis="非霍奇金淋巴瘤",
        reasoning="患儿持续歪头，胸锁乳突肌紧张并可触及条索样增厚，超声符合先天性肌性斜颈。",
        differential=[{"suspected_disease": "肌性斜颈", "confidence_level": "高"}],
        matched_disease="非霍奇金淋巴瘤",
        case_profile={"chief_complaint_timeline": "婴儿自出生后逐渐出现歪头。"},
        examinations={
            "ordered_examinations": ["超声"],
            "examination_results": [
                {"检查": "超声", "结果": {"status": "abnormal", "result": "胸锁乳突肌梭形增厚，符合肌性斜颈。"}},
            ],
        },
        evidence_matrix=[],
    )
    assert diagnoses[0] == "先天性肌性斜颈"


def test_normalize_final_diagnosis_promotes_itp_over_excluded_malignancy_labels():
    disease_map = build_global_disease_map(load_disease_catalog())

    diagnoses, demoted = _normalize_final_diagnoses(
        raw_diagnosis=["白血病", "非霍奇金淋巴瘤", "骨质疏松症"],
        disease_map=disease_map,
        default_diagnosis="白血病",
        reasoning=(
            "患者核心表现为孤立性重度血小板减少伴鼻出血、瘀斑。"
            "骨髓象粒红系正常，排除了白血病和再障，未见淋巴瘤证据；"
            "符合免疫性血小板减少症（ITP）诊断标准。"
        ),
        differential=[{"suspected_disease": "免疫性血小板减少症", "confidence_level": "高"}],
        matched_disease="白血病",
        case_profile={"chief_complaint_timeline": "反复鼻出血、皮肤瘀斑，血小板显著降低。"},
        examinations={
            "ordered_examinations": ["全血细胞计数（CBC）", "骨髓穿刺和活检（BMAB）"],
            "examination_results": [
                {"检查": "全血细胞计数（CBC）", "结果": {"status": "abnormal", "result": "血小板8×10^9/L，白细胞和血红蛋白基本正常。"}},
                {"检查": "骨髓穿刺和活检（BMAB）", "结果": {"status": "abnormal", "result": "粒红系正常，未见白血病浸润或再障证据。"}},
            ],
        },
        evidence_matrix=[
            {
                "problem": "免疫性血小板减少症",
                "history_support": ["孤立性出血表现"],
                "exam_support": ["孤立性重度血小板减少", "骨髓排除白血病和再障"],
                "conclusion": "confirmed",
            },
            {"problem": "白血病", "conclusion": "excluded"},
        ],
    )

    assert diagnoses == ["特发性血小板减少性紫癜"]
    assert demoted == []


def test_pre_prescription_safety_hook_adds_checklist_and_blocks_penicillin():
    plan = {
        "diagnosis": ["细菌性肺炎"],
        "treatment_plan": "主要治疗：使用阿莫西林抗感染。",
        "safety_checklist": {},
    }

    checked = _pre_prescription_safety_hook(
        plan,
        case_profile={
            "medication_allergy_history": "青霉素过敏，目前未用其他药。",
            "past_history": "未知",
        },
        examinations={},
    )

    assert "【处方前安全检查】" in checked["treatment_plan"]
    assert "阿莫西林" in checked["pre_treatment_safety_pause"]["allergy_contraindication_check"]
    assert checked["safety_checklist"]["allergy_contraindications_checked"] is False


def test_pre_prescription_safety_hook_flags_nsaids_for_asthma():
    plan = {
        "diagnosis": ["鼻旁窦囊肿"],
        "treatment_plan": "主要治疗：对症可使用布洛芬镇痛，等待耳鼻喉科进一步处理。",
        "safety_checklist": {},
    }

    checked = _pre_prescription_safety_hook(
        plan,
        case_profile={
            "medication_allergy_history": "无药物过敏。",
            "past_history": "支气管哮喘",
        },
        examinations={},
    )

    assert checked["safety_checklist"]["comorbidity_contraindications_checked"] is False
    assert "哮喘/COPD" in checked["pre_treatment_safety_pause"]["comorbidity_contraindication_check"]


def test_treatment_safety_gate_removes_nsaids_for_asthma():
    checked = enforce_treatment_safety_and_core_drugs(
        {
            "diagnosis": ["鼻旁窦囊肿"],
            "treatment_plan": "主要治疗：耳鼻喉科评估手术切除；疼痛时使用布洛芬。",
            "reasoning": "患者有哮喘背景。",
        },
        case_profile={
            "chief_complaint_timeline": "鼻塞面痛伴视力模糊。",
            "past_history": "支气管哮喘",
            "medication_allergy_history": "无药物过敏。",
        },
        examinations={},
        differential=[],
        disease_map=build_global_disease_map(load_disease_catalog()),
    )

    assert "布洛芬" not in checked["treatment_plan"]
    assert any("布洛芬" in item for item in checked["treatment_safety_corrections"])
    assert checked["safety_checklist"]["no_contraindicated_recommendations"] is True


def test_align_treatment_plan_adds_retinoid_for_erythema_ab_igne():
    plan = align_treatment_plan_with_mechanism(
        diagnoses=["火激红斑"],
        treatment_plan="立即停止热源暴露，每日两次使用润肤剂，并观察皮损变化。",
        case_profile={"chief_complaint_timeline": "长期热源烘烤后出现网状红褐色皮损。"},
        examinations={},
    )

    assert "维A酸" in plan
    assert "停止热暴露" in plan or "停止热源暴露" in plan


def test_penicillin_allergy_guard_does_not_rewrite_confirmed_neurosyphilis_treatment():
    plan = "神经梅毒首选水溶性青霉素G静脉滴注。若后续确认青霉素过敏（虽目前否认），再评估脱敏或替代方案。"
    case_profile = {
        "chief_complaint_timeline": "HIV感染者头痛伴认知下降。",
        "past_history": "HIV感染，梅毒病史。",
        "medication_allergy_history": "患者自述无药物过敏史。",
    }

    paused = apply_pre_treatment_safety_pause(plan, diagnoses=["神经梅毒"], case_profile=case_profile)
    forbidden = build_contraindicated_drugs(case_profile, {})
    checked = enforce_treatment_safety_and_core_drugs(
        {"diagnosis": ["神经梅毒"], "treatment_plan": paused, "reasoning": "首选青霉素G。"},
        case_profile=case_profile,
        examinations={},
        differential=[],
        disease_map=build_global_disease_map(load_disease_catalog()),
    )

    assert "（青霉素过敏，改用替代方案）" not in checked["treatment_plan"]
    assert "青霉素G" in checked["treatment_plan"]
    assert "青霉素" not in forbidden


def test_memory_injects_chief_complaint_error_pattern_without_vector_db(tmp_path):
    path = tmp_path / "memory.md"
    path.write_text("# Baseline Doctor Memory\n\n", encoding="utf-8")
    memory = MarkdownMemory(path, max_notes=2)

    notes = memory.load_notes(case_profile={"chief_complaint_timeline": "鼻塞反复，鼻旁窦囊肿待评估"})

    assert notes
    assert "鼻内镜" in notes[0]


def test_workflow_limits_keep_regular_cases_within_two_and_a_half_minutes():
    limits = load_workflow_limits({"workflow": {}})

    assert limits.max_patient_seconds == 150
    assert limits.special_case_max_patient_seconds == 180
    assert limits.min_doctor_turns == 1
    assert limits.max_doctor_turns == 2
    assert limits.max_doctor_turns_ceiling == 2
    assert limits.max_exam_rounds == 2
    assert limits.max_exam_rounds_ceiling == 2
    assert limits.max_main_loop_iterations == 8
    assert limits.force_diagnosis_buffer_seconds <= 40
    assert (
        limits.consult_time_budget_seconds
        + limits.examine_time_budget_seconds
        + limits.diagnose_time_budget_seconds
        <= limits.max_patient_seconds - limits.force_diagnosis_buffer_seconds
    )


def test_workflow_limits_accept_fractional_regular_minutes():
    limits = load_workflow_limits({"workflow": {"max_patient_minutes": 2.5, "special_case_max_patient_minutes": 3}})

    assert limits.max_patient_seconds == 150
    assert limits.special_case_max_patient_seconds == 180


def test_patient_budget_gives_complex_cases_thirty_extra_seconds():
    limits = load_workflow_limits({"workflow": {}})
    budget = PatientCaseBudget(limits)
    budget.started_at = time.monotonic() - 151

    assert budget.active_max_seconds() == 150
    assert budget.remaining() == 0

    budget.set_special_case(True)
    assert budget.active_max_seconds() == 180
    assert budget.remaining() > 0

    budget.started_at = time.monotonic() - 181
    assert budget.remaining() == 0


def test_consultation_gap_question_compresses_core_history_and_safety():
    question = _consultation_gap_question(
        [
            "consultation.patient_expression",
            "consultation.four_history_tasks",
            "consultation.medication_allergy",
            "consultation.dangerous_diagnosis",
        ],
        {},
    )

    assert "一次性补充" in question
    assert "为什么来看病" in question
    assert "全部药物" in question
    assert "突然加重" in question


def test_consultation_gap_question_combines_medication_and_executability():
    question = _consultation_gap_question(
        ["consultation.medication_allergy", "consultation.social_family_support"],
        {},
    )

    assert "全部药物" in question
    assert "药物过敏史" in question
    assert "取药复诊" in question


def test_regular_consult_hard_gate_is_only_medication_safety():
    gaps = [
        "consultation.patient_expression",
        "consultation.system_localization",
        "consultation.four_history_tasks",
        "consultation.medication_allergy",
    ]

    assert consultation_hard_incomplete(gaps) == ["consultation.medication_allergy"]
    assert consultation_hard_incomplete(gaps, complex_case=True) == [
        "consultation.patient_expression",
        "consultation.four_history_tasks",
        "consultation.medication_allergy",
    ]


def _workflow_limits(**overrides):
    values = dict(
        min_doctor_turns=1,
        max_doctor_turns=2,
        max_doctor_turns_ceiling=2,
        max_exam_rounds=2,
        max_exam_rounds_ceiling=2,
        max_patient_seconds=180,
        min_objective_exam_results=1,
        force_diagnosis_buffer_seconds=45,
    )
    values.update(overrides)
    return SimpleNamespace(**values)


def _workflow_budget(*, remaining=120, time_critical=False, force=False):
    return SimpleNamespace(
        remaining=lambda: remaining,
        time_critical=lambda: time_critical,
        consult_time_exceeded=lambda: False,
        examine_time_exceeded=lambda: False,
        should_force_finalize=lambda in_consultation=False: force,
    )


def test_opening_consultation_question_packs_high_yield_history():
    question = _next_consultation_question({}, 0)

    assert question == OPENING_CONSULTATION_QUESTION
    for token in ("为什么来看病", "部位", "既往", "全部药物", "过敏史", "突然加重", "妊娠"):
        assert token in question


def test_consultation_minimum_allows_one_complete_turn():
    limits = _workflow_limits()
    profile = {
        "chief_complaint_timeline": "右膝前痛半年，上下楼梯加重，今天加重所以就诊",
        "medication_allergy_history": "正在用对乙酰氨基酚，无过敏",
    }
    history = [
        {"from": "doctor", "text": OPENING_CONSULTATION_QUESTION},
        {
            "from": "patient",
            "text": "右膝疼半年，正在用对乙酰氨基酚，没有药物过敏。",
        },
    ]

    assert _has_consultation_minimum(profile, history, limits) is True


def test_consultation_minimum_blocks_when_medication_missing():
    limits = _workflow_limits()
    profile = {
        "chief_complaint_timeline": "发热咳嗽3天，今天加重来看病",
        "medication_allergy_history": "未知",
    }
    history = [
        {"from": "doctor", "text": OPENING_CONSULTATION_QUESTION},
        {"from": "patient", "text": "发热咳嗽3天，今天加重所以来看病。"},
    ]

    assert _has_consultation_minimum(profile, history, limits) is False


def test_plan_next_step_moves_to_exam_after_complete_first_round():
    limits = _workflow_limits()
    action, question, reason = _plan_next_step(
        case_state={
            "stage": "consult",
            "exam_rounds": 0,
            "ordered_examinations": [],
            "consultation_check": {"incomplete": []},
            "chat_history": [
                {"from": "doctor", "text": OPENING_CONSULTATION_QUESTION},
                {
                    "from": "patient",
                    "text": (
                        "右膝前痛半年，上下楼加重，今天疼得更明显所以来看病，担心关节损坏。"
                        "否认慢病。正在用对乙酰氨基酚，没有药物过敏。"
                    ),
                },
            ],
            "preliminary_differential": [],
        },
        case_profile={
            "chief_complaint_timeline": "右膝前痛半年，上下楼梯加重，今天加重就诊",
            "past_history": "否认慢病",
            "medication_allergy_history": "正在用对乙酰氨基酚，无过敏",
            "unvoiced_concerns": "担心关节损坏",
        },
        chat_history=[
            {"from": "doctor", "text": OPENING_CONSULTATION_QUESTION},
            {
                "from": "patient",
                "text": (
                    "右膝前痛半年，上下楼加重，今天疼得更明显所以来看病，担心关节损坏。"
                    "否认慢病。正在用对乙酰氨基酚，没有药物过敏。"
                ),
            },
        ],
        limits=limits,
        budget=_workflow_budget(),
    )

    assert action == "order_examination"
    assert question == ""
    assert "检查" in reason


def test_plan_next_step_regular_case_does_not_block_on_four_history():
    limits = _workflow_limits(max_patient_seconds=150)
    history = [
        {"from": "doctor", "text": OPENING_CONSULTATION_QUESTION},
        {
            "from": "patient",
            "text": "右膝疼半年。正在用对乙酰氨基酚，没有药物过敏。",
        },
    ]
    action, question, reason = _plan_next_step(
        case_state={
            "stage": "consult",
            "exam_rounds": 0,
            "ordered_examinations": [],
            "consultation_check": {
                "incomplete": [
                    "consultation.four_history_tasks",
                    "consultation.patient_expression",
                    "consultation.social_family_support",
                ],
            },
            "chat_history": history,
            "preliminary_differential": [],
        },
        case_profile={
            "chief_complaint_timeline": "右膝疼半年",
            "past_history": "未知",
            "medication_allergy_history": "正在用对乙酰氨基酚，无过敏",
            "unvoiced_concerns": "未知",
        },
        chat_history=history,
        limits=limits,
        budget=_workflow_budget(remaining=110),
    )

    assert action == "order_examination"
    assert question == ""
    assert "检查" in reason


def test_plan_next_step_second_round_compresses_remaining_hard_gaps():
    limits = _workflow_limits()
    history = [
        {"from": "doctor", "text": OPENING_CONSULTATION_QUESTION},
        {
            "from": "patient",
            "text": "发热咳嗽3天黄绿痰，今天加重来看病，担心肺炎。有糖尿病。",
        },
    ]
    action, question, reason = _plan_next_step(
        case_state={
            "stage": "consult",
            "exam_rounds": 0,
            "ordered_examinations": [],
            "consultation_check": {
                "incomplete": ["consultation.medication_allergy"],
            },
            "chat_history": history,
            "preliminary_differential": [],
        },
        case_profile={
            "chief_complaint_timeline": "发热咳嗽3天黄绿痰，今天加重来看病",
            "past_history": "糖尿病",
            "medication_allergy_history": "未知",
            "unvoiced_concerns": "担心肺炎",
        },
        chat_history=history,
        limits=limits,
        budget=_workflow_budget(),
    )

    assert action == "ask_patient"
    assert "药物" in question
    assert "过敏" in question
    assert "压缩" in reason or "用药" in reason


def test_effective_max_turns_stay_within_three_minute_loop():
    limits = _workflow_limits()
    complex_profile = {"summary": "免疫抑制，HIV/AIDS，持续低氧"}
    complex_diff = [{"suspected_disease": "机会性感染", "must_rule_out": True, "confidence_level": "高"}]

    assert effective_max_doctor_turns({}, [], limits=limits) == 2
    assert effective_max_doctor_turns(complex_profile, complex_diff, limits=limits) == 2
    assert effective_max_exam_rounds({}, [], limits=limits) == 2
    assert effective_max_exam_rounds(complex_profile, complex_diff, limits=limits) == 2


def test_consultation_gap_question_is_shared_from_planner():
    question = consultation_gap_question(
        ["consultation.medication_allergy"],
        {},
    )

    assert "全部药物" in question
    assert "药物过敏史" in question


def test_exam_routing_ignores_negated_dyspnea_for_chest_wall_mass():
    catalog = load_examination_catalog()
    available = [name for names in catalog.values() for name in names]
    disease_catalog = load_disease_catalog()

    profile = {
        "chief_complaint_timeline": "5天前发现上胸部旧手术瘢痕旁有个小肿块，按压微痛。无发热、呼吸困难或出血。",
        "past_history": "糖尿病前期和胃食管反流史",
        "summary": "上胸部瘢痕旁微痛性肿块，无全身感染征象，担心复发或感染。",
    }

    exams = suggest_comprehensive_examinations(
        case_profile=profile,
        differential=[{"suspected_disease": "表皮样囊肿"}],
        exam_need_summary={"missing_dimensions": [{"dimension": "确诊或病因证据"}]},
        ordered=[],
        available_examinations=available,
        examination_catalog=catalog,
        max_count=4,
    )
    mapped, _ = _mapped_examination_recommendations(
        case_profile=profile,
        differential=[{"suspected_disease": "表皮样囊肿"}],
        ordered=set(),
        available_examinations=available,
        exam_resolver=lambda name: name,
        disease_to_department=build_disease_department_map(disease_catalog),
        disease_map=build_global_disease_map(disease_catalog),
    )

    assert "超声心动图" not in exams
    assert "N末端B型利钠肽原（NT-proBNP）" not in exams
    assert "胸部X线检查（CXR）" not in exams
    assert "血清电解质" not in exams
    assert "超声心动图" not in mapped
    assert any(name in exams for name in ("体格检查", "皮肤检查", "超声"))
    assert _inferred_department_from_case(
        case_profile=profile,
        differential=[{"suspected_disease": "表皮样囊肿"}],
        disease_to_department=build_disease_department_map(disease_catalog),
        disease_map=build_global_disease_map(disease_catalog),
    ) == "皮肤科"


def test_exam_routing_adult_keratitis_prefers_microbiology_over_congenital_workup():
    catalog = load_examination_catalog()
    available = [name for names in catalog.values() for name in names]

    exams = suggest_comprehensive_examinations(
        case_profile={
            "chief_complaint_timeline": "急性眼痛、畏光、流泪，角膜浸润扩大。",
            "past_history": "类风湿关节炎，长期使用含激素眼药水。",
            "summary": "免疫抑制患者出现化脓性角膜浸润，需病原学确诊。",
        },
        differential=[{"suspected_disease": "角膜溃疡"}],
        exam_need_summary={"missing_dimensions": [{"dimension": "确诊或病因证据"}]},
        ordered=[],
        available_examinations=available,
        examination_catalog=catalog,
        max_count=5,
    )

    assert "裂隙灯检查" in exams
    assert "角膜刮片分析" in exams
    assert "微生物培养及鉴定" in exams
    assert "超声生物显微镜检查（UBM）" not in exams
    assert "角膜厚度测量" not in exams


def test_prune_redundant_xrays_keeps_one_skeletal_study_with_mri():
    pruned = prune_redundant_modalities(
        ["骨骼X线检查", "关节X线检查", "体格检查", "磁共振成像（MRI）", "X线检查"]
    )

    assert "磁共振成像（MRI）" in pruned
    assert "体格检查" in pruned
    assert "X线检查" not in pruned
    skeletal = [name for name in pruned if "X线" in name]
    assert len(skeletal) == 1


def test_safety_pause_does_not_fire_from_diet_template_heart_failure_words():
    plan = (
        "1. 择期手术切除表皮样囊肿。\n\n"
        "【饮食与营养执行细则】\n"
        "以地中海/DASH模式为主；有水肿或心衰表现时按医嘱限液并每日称重。"
    )
    paused = apply_pre_treatment_safety_pause(
        plan,
        diagnoses=["表皮样囊肿"],
        case_profile={
            "chief_complaint_timeline": "上胸部瘢痕旁小肿块。",
            "past_history": "糖尿病前期",
            "medication_allergy_history": "无药物过敏",
        },
    )

    assert "瓣膜病/心衰背景" not in paused


def test_align_treatment_rewrites_absolute_bed_rest_to_early_activity():
    plan = align_treatment_plan_with_mechanism(
        diagnoses=["骶髂关节炎"],
        treatment_plan="急性期严格限制负重活动，建议卧床休息并使用硬板床。对乙酰氨基酚镇痛。",
        case_profile={
            "chief_complaint_timeline": "臀部交替痛伴晨僵。",
            "family_economic_status": "自费压力大，希望选择便宜药物。",
        },
        examinations={},
    )

    assert "绝对卧床" not in plan
    assert "卧床休息" not in plan
    assert "早期活动" in plan or "尽早活动" in plan or "适度活动" in plan
    assert "对乙酰氨基酚" in plan


def test_align_treatment_does_not_escalate_stable_t2dm_cognition_to_dka():
    plan = align_treatment_plan_with_mechanism(
        diagnoses=["2型糖尿病（T2DM）"],
        treatment_plan=(
            "立即住院转入内分泌科。液体复苏后小剂量胰岛素静脉滴注，按DKA/HHS处理。"
            "待代谢稳定后再做认知训练。"
        ),
        case_profile={
            "chief_complaint_timeline": "记忆力减退2年，近月加重，伴慢性血糖控制不佳。无呕吐、深大呼吸或意识障碍。",
            "past_history": "2型糖尿病、高血压、阿尔茨海默病家属史。",
            "summary": "慢性认知下降为主诉，尿酮弱阳性但无酸中毒证据。",
        },
        examinations={"examination_results": [{"检查": "尿液分析（UA）", "结果": {"status": "abnormal", "result": "尿酮弱阳性"}}]},
    )

    assert "立即住院" not in plan
    assert "DKA" not in plan
    assert "口服" in plan
    assert "认知" in plan


def test_align_treatment_covers_staph_and_mechanical_causes_for_corneal_ulcer():
    plan = align_treatment_plan_with_mechanism(
        diagnoses=["角膜溃疡"],
        treatment_plan="停用激素眼药水，予左氧氟沙星滴眼液频繁点眼，口服对乙酰氨基酚止痛。",
        case_profile={
            "chief_complaint_timeline": "眼痛畏光流泪，倒睫摩擦角膜，眼压偏高。",
            "past_history": "类风湿关节炎，长期点激素眼药水。",
        },
        examinations={"examination_results": [{"检查": "裂隙灯检查", "结果": {"status": "abnormal", "result": "中央浸润伴倒睫，眼压升高。"}}]},
    )

    assert any(token in plan for token in ("头孢唑林", "万古霉素", "金葡"))
    assert "倒睫" in plan
    assert "眼压" in plan


def test_align_treatment_rewrites_vegan_protein_and_adds_eczema_contact_care():
    vegan_plan = align_treatment_plan_with_mechanism(
        diagnoses=["钩端螺旋体病"],
        treatment_plan="青霉素G静脉注射7天，饮食优先蛋、鱼、瘦肉等优质蛋白。",
        case_profile={
            "chief_complaint_timeline": "洪水接触后发热肌痛。",
            "family_economic_status": "纯素饮食，不吃鱼肉。",
        },
        examinations={},
    )
    eczema_plan = align_treatment_plan_with_mechanism(
        diagnoses=["钱币状湿疹"],
        treatment_plan="糠酸莫米松乳膏薄涂，口服氯雷他定，温水洗澡后润肤。",
        case_profile={
            "chief_complaint_timeline": "四肢圆形斑块剧痒。",
            "personal_exposure_history": "斑贴试验示香精混合物强阳性、镍弱阳性。",
        },
        examinations={"examination_results": [{"检查": "斑贴试验", "结果": {"status": "abnormal", "result": "香精强阳性，镍弱阳性。"}}]},
    )

    assert "鱼、瘦肉" not in vegan_plan
    assert "豆腐" in vegan_plan or "豆" in vegan_plan
    assert "湿包" in eczema_plan or "湿敷" in eczema_plan
    assert "镍" in eczema_plan


def test_normalize_final_diagnosis_promotes_alzheimer_over_t2dm_for_chronic_cognition():
    disease_map = build_global_disease_map(load_disease_catalog())

    diagnoses, _ = _normalize_final_diagnoses(
        raw_diagnosis=["2型糖尿病（T2DM）"],
        disease_map=disease_map,
        default_diagnosis="未明确诊断",
        reasoning="慢性记忆力减退两年，血糖控制不佳但无酸中毒，当前主诊断应为阿尔茨海默病。",
        differential=[{"suspected_disease": "阿尔茨海默病", "confidence_level": "高"}],
        matched_disease="",
        case_profile={
            "chief_complaint_timeline": "记忆力减退2年，近月加重，生活需提醒。",
            "past_history": "2型糖尿病。",
        },
        examinations={
            "ordered_examinations": ["神经心理评估"],
            "examination_results": [
                {"检查": "神经心理评估", "结果": {"status": "abnormal", "result": "情景记忆显著受损，符合阿尔茨海默病。"}}
            ],
        },
        evidence_matrix=[{"problem": "阿尔茨海默病", "conclusion": "confirmed"}],
    )

    assert diagnoses[0] == "阿尔茨海默病"


def test_essential_exams_incomplete_when_new_af_lacks_thyroid_function():
    complete = _essential_exams_complete(
        {
            "ordered_examinations": ["心电图（ECG）", "超声心动图"],
            "examination_results": {
                "心电图（ECG）": {"status": "abnormal", "result": {"心律": "心房颤动", "心率": "124次/分"}},
                "超声心动图": {"status": "abnormal", "result": {"心脏瓣膜反流": "中重度二尖瓣反流"}},
            },
        },
        {"chief_complaint_timeline": "心悸气短8个月，活动后加重。"},
        differential=[
            {
                "suspected_disease": "心房颤动",
                "confidence_level": "高",
                "subjective_probability": 0.85,
                "exam_support": ["心电图确诊房颤"],
                "recommended_examinations": ["甲状腺功能检查（TFTs）"],
            }
        ],
    )

    assert complete is False


def test_exam_batch_limit_allows_tft_in_palpitation_first_pass():
    limit = _exam_batch_limit(
        {"chief_complaint_timeline": "心悸气短8个月，心跳乱，上坡提东西难受。"},
        [{"suspected_disease": "心房颤动"}],
    )

    assert limit >= 3


def test_exam_routing_includes_tft_for_unexplained_palpitations():
    catalog = load_examination_catalog()
    available = [name for names in catalog.values() for name in names]

    exams = suggest_comprehensive_examinations(
        case_profile={"chief_complaint_timeline": "心悸气短8个月，心跳乱，活动后加重。"},
        differential=[{"suspected_disease": "心房颤动"}],
        exam_need_summary={"missing_dimensions": [{"dimension": "确诊或病因证据"}]},
        ordered=[],
        available_examinations=available,
        examination_catalog=catalog,
        max_count=3,
    )

    assert "心电图（ECG）" in exams
    assert "超声心动图" in exams
    assert "甲状腺功能检查（TFTs）" in exams


def test_plan_next_step_orders_followup_when_new_af_lacks_tft():
    limits = _workflow_limits()
    history = [
        {"from": "doctor", "text": OPENING_CONSULTATION_QUESTION},
        {"from": "patient", "text": "心悸气短8个月，高血压药没规律吃，没有药物过敏。"},
    ]
    action, question, reason = _plan_next_step(
        case_state={
            "stage": "examine",
            "exam_rounds": 1,
            "ordered_examinations": ["心电图（ECG）", "超声心动图"],
            "examination_results": {
                "心电图（ECG）": {"status": "abnormal", "result": {"心律": "心房颤动"}},
                "超声心动图": {"status": "abnormal", "result": {"心脏瓣膜反流": "中重度二尖瓣反流"}},
            },
            "consultation_check": {"incomplete": []},
            "chat_history": history,
            "preliminary_differential": [
                {
                    "suspected_disease": "心房颤动",
                    "confidence_level": "高",
                    "subjective_probability": 0.85,
                    "exam_support": ["心电图确诊房颤"],
                    "support_points": ["快速房颤"],
                    "recommended_examinations": ["甲状腺功能检查（TFTs）"],
                }
            ],
        },
        case_profile={
            "chief_complaint_timeline": "心悸气短8个月，心跳乱，活动后加重。",
            "past_history": "高血压",
            "medication_allergy_history": "高血压药不规律，无过敏",
        },
        chat_history=history,
        limits=limits,
        budget=_workflow_budget(),
    )

    assert action == "order_examination"
    assert question == ""
    assert "检查" in reason or "证据" in reason


def test_valvular_af_treatment_replaces_doac_with_warfarin():
    plan = align_treatment_plan_with_mechanism(
        diagnoses=["心房颤动"],
        treatment_plan="主要治疗：控制心室率用美托洛尔；抗凝推荐利伐沙班或达比加群酯。",
        case_profile={"chief_complaint_timeline": "心悸气短8个月，心电图为房颤。"},
        examinations={
            "ordered_examinations": ["心电图（ECG）", "超声心动图"],
            "examination_results": [
                {"检查": "心电图（ECG）", "结果": {"status": "abnormal", "result": {"心律": "心房颤动"}}},
                {"检查": "超声心动图", "结果": {"status": "abnormal", "result": {"心脏瓣膜反流": "中重度二尖瓣反流"}}},
            ],
        },
    )

    assert "华法林" in plan
    assert "利伐沙班" not in plan
    assert "达比加群" not in plan


def test_hyperthyroid_af_adds_antithyroid_treatment():
    plan = align_treatment_plan_with_mechanism(
        diagnoses=["心房颤动"],
        treatment_plan="主要治疗：美托洛尔控制心室率，华法林抗凝。",
        case_profile={"chief_complaint_timeline": "心悸气短8个月。"},
        examinations={
            "ordered_examinations": ["甲状腺功能检查（TFTs）"],
            "examination_results": [
                {
                    "检查": "甲状腺功能检查（TFTs）",
                    "结果": {
                        "status": "abnormal",
                        "result": {
                            "促甲状腺激素": "0.01 mIU/L［参考值：0.4-4.0 mIU/L］",
                            "血清游离甲状腺素": "3.6 ng/dL［参考值：0.8-1.8 ng/dL］",
                        },
                        "abnormal_indicators": ["促甲状腺激素", "血清游离甲状腺素"],
                    },
                }
            ],
        },
    )

    assert any(token in plan for token in ("甲巯咪唑", "丙硫氧嘧啶", "抗甲状腺"))


def test_cxl_deferred_when_pregnancy_unknown():
    plan = align_treatment_plan_with_mechanism(
        diagnoses=["圆锥角膜"],
        treatment_plan="主要治疗：禁止揉眼；建议尽快行角膜胶原交联术（CXL）；试戴RGP。",
        case_profile={
            "demographics": "未知",
            "reproductive_history": "未知",
            "chief_complaint_timeline": "视物模糊两年，揉眼加重。",
        },
        examinations={},
    )

    assert "尽快行角膜胶原交联" not in plan
    assert "暂缓" in plan or "妊娠" in plan
    assert "RGP" in plan or "硬性" in plan


def test_cxl_blocked_when_pregnancy_confirmed():
    checked = enforce_treatment_safety_and_core_drugs(
        {
            "diagnosis": ["圆锥角膜"],
            "treatment_plan": "主要治疗：建议尽快行角膜胶原交联术（CXL）阻止进展。",
            "reasoning": "圆锥角膜进展期。",
        },
        case_profile={
            "demographics": "育龄女性",
            "reproductive_history": "目前妊娠20周",
            "chief_complaint_timeline": "视物模糊两年。",
        },
        examinations={},
        differential=[],
        disease_map=build_global_disease_map(load_disease_catalog()),
    )

    assert "尽快行角膜胶原交联" not in checked["treatment_plan"]
    assert checked["safety_checklist"]["no_contraindicated_recommendations"] is True


def test_cxl_allowed_when_pregnancy_excluded():
    plan = align_treatment_plan_with_mechanism(
        diagnoses=["圆锥角膜"],
        treatment_plan="主要治疗：禁止揉眼；建议尽快行角膜胶原交联术（CXL）；试戴RGP。",
        case_profile={
            "demographics": "28岁男性",
            "reproductive_history": "不适用",
            "chief_complaint_timeline": "视物模糊两年。",
        },
        examinations={},
    )

    assert "角膜胶原交联" in plan or "CXL" in plan


def test_sps_removed_for_volume_overloaded_ckd():
    checked = enforce_treatment_safety_and_core_drugs(
        {
            "diagnosis": ["慢性肾脏病"],
            "treatment_plan": (
                "紧急处置：口服聚苯乙烯磺酸钠散（15g tid）降钾；"
                "同时予呋塞米 20-40mg bid 减轻水肿。"
            ),
            "reasoning": "CKD3b 伴高钾和容量负荷。",
        },
        case_profile={
            "chief_complaint_timeline": "尿起泡、夜尿多，近2个月脚踝和小腿肿、活动后气短。",
            "past_history": "高血脂和糖耐量受损",
            "medication_allergy_history": "无过敏，偶尔吃止痛药",
        },
        examinations={
            "ordered_examinations": ["血清电解质", "肾功能检查（RFTs）"],
            "examination_results": [
                {
                    "检查": "血清电解质",
                    "结果": {"status": "abnormal", "result": {"血钾": "5.7 mmol/L [参考范围：3.5-5.0]"}},
                },
                {
                    "检查": "肾功能检查（RFTs）",
                    "结果": {"status": "abnormal", "result": {"估算肾小球滤过率": "36 mL/min/1.73m2"}},
                },
            ],
        },
        differential=[],
        disease_map=build_global_disease_map(load_disease_catalog()),
    )

    assert "口服聚苯乙烯磺酸钠" not in checked["treatment_plan"]
    assert "聚苯乙烯磺酸钠散" not in checked["treatment_plan"]
    assert checked["safety_checklist"]["no_contraindicated_recommendations"] is True
    assert any(token in checked["treatment_plan"] for token in ("呋塞米", "环硅酸锆钠", "限钾"))


def test_normalize_final_diagnosis_promotes_cervical_laceration_over_polyp():
    disease_map = build_global_disease_map(load_disease_catalog())

    diagnoses, _ = _normalize_final_diagnoses(
        raw_diagnosis=["宫颈息肉"],
        disease_map=disease_map,
        default_diagnosis="宫颈息肉",
        reasoning="患者核心症状为性交后出血，结合超声提示宫颈局灶性异常，最符合宫颈息肉表现。",
        differential=[{"suspected_disease": "宫颈息肉", "confidence_level": "高"}],
        matched_disease="宫颈息肉",
        case_profile={"chief_complaint_timeline": "性交后反复出血8个月，2天前出血增多。"},
        examinations={
            "ordered_examinations": ["盆腔超声", "切除活检", "人绒毛膜促性腺激素（hCG）检测"],
            "examination_results": [
                {
                    "检查": "盆腔超声",
                    "结果": {
                        "status": "abnormal",
                        "result": "宫颈间质内可见不规则高回声条带，伴局灶性裂隙样缺损，瘢痕附近宫颈管内多普勒血流增多。",
                    },
                },
                {
                    "检查": "切除活检",
                    "结果": {"status": "normal", "result": "未见可见病变，未见异型性或恶性证据。"},
                },
            ],
        },
        evidence_matrix=[{"problem": "宫颈息肉", "conclusion": "confirmed"}],
    )

    assert diagnoses[0] == "陈旧性宫颈裂伤"
    assert "宫颈息肉" not in diagnoses


def test_cervical_laceration_treatment_recommends_repair_not_polypectomy():
    plan = align_treatment_plan_with_mechanism(
        diagnoses=["陈旧性宫颈裂伤"],
        treatment_plan="主要治疗：若TCT/HPV阴性且症状持续，建议行宫腔镜下宫颈息肉摘除术。",
        case_profile={"chief_complaint_timeline": "性交后反复出血8个月。"},
        examinations={
            "examination_results": [
                {
                    "检查": "盆腔超声",
                    "结果": {
                        "status": "abnormal",
                        "result": "宫颈间质局灶性裂隙样缺损，瘢痕附近血流增多。",
                    },
                }
            ]
        },
    )

    assert any(token in plan for token in ("裂伤修补", "修补术", "裂伤缝合"))
    assert "宫颈息肉摘除术" not in plan
    assert "宫腔镜下宫颈息肉摘除" not in plan


def test_gastric_varices_uses_glue_and_standard_antibiotic():
    plan = align_treatment_plan_with_mechanism(
        diagnoses=["胃底静脉曲张"],
        treatment_plan=(
            "内镜治疗：生命体征相对稳定后行套扎术（EVL）或硬化剂注射止血。"
            "抗感染预防：首选左氧氟沙星或氨曲南。"
            "【禁忌药替代-青霉素过敏】可优先考虑美罗培南。"
        ),
        case_profile={
            "chief_complaint_timeline": "黑便和呕血2天，有肝硬化、门脉高压。",
            "past_history": "肝硬化，门脉高压",
            "medication_allergy_history": "对青霉素过敏",
        },
        examinations={
            "examination_results": [
                {
                    "检查": "腹部超声",
                    "结果": {"status": "abnormal", "result": {"脾脏": "脾脏增大", "腹腔积液": "少量游离液体"}},
                }
            ]
        },
    )

    assert "组织胶" in plan
    assert "套扎术（EVL）" not in plan
    assert "硬化剂注射止血" not in plan
    assert "头孢曲松" in plan
    assert "可优先考虑美罗培南" not in plan


def test_normalize_final_diagnosis_promotes_hypothyroidism_over_hyperlipidemia():
    disease_map = build_global_disease_map(load_disease_catalog())

    diagnoses, _ = _normalize_final_diagnoses(
        raw_diagnosis=["混合型高脂血症"],
        disease_map=disease_map,
        default_diagnosis="混合型高脂血症",
        reasoning="双侧眼睑黄色斑块结合高脂血症，诊断混合型高脂血症；他汀治疗为主。",
        differential=[{"suspected_disease": "混合型高脂血症", "confidence_level": "高"}],
        matched_disease="混合型高脂血症",
        case_profile={
            "chief_complaint_timeline": "双侧上眼睑内侧黄色斑片18个月、近4个月变大。",
            "past_history": "血脂异常",
        },
        examinations={
            "ordered_examinations": ["血脂检测组合", "甲状腺功能检查（TFTs）"],
            "examination_results": [
                {
                    "检查": "血脂检测组合",
                    "结果": {
                        "status": "abnormal",
                        "result": {"LDL胆固醇": "182 mg/dL", "总胆固醇": "268 mg/dL", "甘油三酯": "196 mg/dL"},
                    },
                },
                {
                    "检查": "甲状腺功能检查（TFTs）",
                    "结果": {
                        "status": "abnormal",
                        "result": {
                            "促甲状腺激素": "12.8 mIU/L［参考值：0.4-4.0 mIU/L］",
                            "血清游离甲状腺素": "0.5 ng/dL［参考值：0.8-1.8 ng/dL］",
                        },
                        "abnormal_indicators": ["促甲状腺激素", "血清游离甲状腺素"],
                    },
                },
            ],
        },
        evidence_matrix=[{"problem": "混合型高脂血症", "conclusion": "confirmed"}],
    )

    assert diagnoses[0] == "甲状腺功能减退症"


def test_xanthelasma_treatment_adds_surgery_and_levothyroxine():
    plan = align_treatment_plan_with_mechanism(
        diagnoses=["甲状腺功能减退症"],
        treatment_plan="启动阿托伐他汀；待血脂控制3-6个月后，若患者仍强烈要求，可考虑手术切除。",
        case_profile={
            "chief_complaint_timeline": "双侧上眼睑内侧黄色斑片18个月，近4个月变大，担心外观。",
            "past_history": "血脂异常",
        },
        examinations={
            "examination_results": [
                {
                    "检查": "甲状腺功能检查（TFTs）",
                    "结果": {
                        "status": "abnormal",
                        "result": {
                            "促甲状腺激素": "12.8 mIU/L［参考值：0.4-4.0 mIU/L］",
                            "血清游离甲状腺素": "0.5 ng/dL［参考值：0.8-1.8 ng/dL］",
                        },
                    },
                }
            ]
        },
    )

    assert any(token in plan for token in ("左甲状腺素", "优甲乐", "甲状腺素替代"))
    assert any(token in plan for token in ("手术切除", "手术刮除", "切除术"))
    assert "3-6个月后再" not in plan and "3-6个月后，若患者仍强烈要求" not in plan


def test_exam_routing_includes_tft_for_xanthelasma_dyslipidemia():
    catalog = load_examination_catalog()
    available = [name for names in catalog.values() for name in names]

    exams = suggest_comprehensive_examinations(
        case_profile={
            "chief_complaint_timeline": "双侧上眼睑内侧黄色斑片18个月、近4个月变大。",
            "past_history": "血脂异常，未规律吃降脂药。",
            "summary": "眼睑黄色瘤样皮损，需排查继发性高脂血症。",
        },
        differential=[{"suspected_disease": "混合型高脂血症"}],
        exam_need_summary={"missing_dimensions": [{"dimension": "确诊或病因证据"}]},
        ordered=[],
        available_examinations=available,
        examination_catalog=catalog,
        max_count=4,
    )

    assert "甲状腺功能检查（TFTs）" in exams
    assert "血脂检测组合" in exams


def test_xanthelasma_department_prefers_endocrinology_over_ophthalmology():
    disease_catalog = load_disease_catalog()

    assert _inferred_department_from_case(
        case_profile={
            "chief_complaint_timeline": "双侧上眼睑内侧黄色斑片18个月，不影响视力。",
            "past_history": "血脂异常",
        },
        differential=[{"suspected_disease": "混合型高脂血症"}],
        disease_to_department=build_disease_department_map(disease_catalog),
        disease_map=build_global_disease_map(disease_catalog),
    ) == "内分泌科"
