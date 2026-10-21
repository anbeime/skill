"""A readable baseline doctor agent.

The SDK handles train/test orchestration and service calls. This file shows a
clear reference flow: decide action -> ask/order exam/diagnose -> train reflection.
"""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from hospital_agent_sdk import AgentBuilder, BasicAgent, load_config
except ModuleNotFoundError:  # Allows local unit tests for pure workflow helpers without the SDK installed.
    AgentBuilder = None

    class BasicAgent:  # type: ignore[no-redef]
        def __init__(self, config: Optional[Dict[str, Any]] = None, memory: Any = None):
            self.config = config or {}
            self.memory = memory

    def load_config(*args: Any, **kwargs: Any) -> Dict[str, Any]:  # type: ignore[no-redef]
        return {}
from .memory import build_memory
from .diagnoser import (
    _diseases_from_case_evidence,
    _diseases_from_differential,
    _infer_department_from_differential,
    _normalize_final_diagnoses,
    _select_default_diagnosis,
    align_treatment_plan_with_mechanism,
    build_contraindicated_drugs,
    enforce_treatment_safety_and_core_drugs,
    reconcile_diagnosis_before_treatment,
)
from .examiner import (
    _exam_batch_limit,
    _fallback_examinations,
    build_exam_decision_records,
    build_exam_core_map,
    build_exam_need_summary,
    build_exam_purpose_map,
    filter_examinations_by_current_evidence,
    prioritize_examinations,
    resolve_exam_name,
    suggest_comprehensive_examinations,
)
from .planner import (
    _domain_specific_history_question,
    _essential_exams_complete,
    _medication_history_incomplete,
    _plan_next_step,
    _question_already_asked,
    advance_workflow_stage,
    build_workflow_self_check,
    _is_complex_case,
    consultation_gap_question,
    consultation_hard_incomplete,
    effective_max_doctor_turns,
    effective_max_exam_rounds,
)
from .utils import (
    as_text_list,
    build_disease_department_map,
    build_global_disease_map,
    build_name_map,
    case_context_fingerprint,
    clean_text,
    load_disease_catalog,
    load_examination_catalog,
    match_standard_name,
    match_standard_or_contained_name,
    normalize_name,
    parse_json_object,
    resolve_ordered_examination_items,
    unique_preserve_order,
)
from .prompt import (
    DEPARTMENT_PROMPT,
    DISEASE_AND_TREATMENT_PROMPT,
    DOCTOR_SYSTEM_PROMPT,
    EVALUATION_REFLECTION_PROMPT,
    EXAM_CATEGORY_PROMPT,
    EXAM_ITEM_PROMPT,
    FINAL_SELF_CHECK_PROMPT,
    JSON_REPAIR_SYSTEM_PROMPT,
    NEXT_ACTION_PROMPT,
    TREATMENT_SAFETY_CORE_CHECK_PROMPT,
    format_prompt,
    DIFFERENTIAL_DIAGNOSIS_PROMPT,
    CASE_PROFILE_PROMPT
)


def _empty_case_profile() -> Dict[str, Any]:
    return {
        "demographics": "未知",
        "chief_complaint_timeline": "未知",
        "personal_exposure_history": "未知",
        "past_history": "未知",
        "medication_allergy_history": "未知",
        "reproductive_history": "未知",
        "psychosocial_status": "未知",
        "family_economic_status": "未知",
        "caregiver_function_preferences": "未知",
        "unvoiced_concerns": "未知",
        "red_flags": [],
        "missing_critical_fields": [],
        "summary": "",
    }


_DEPARTMENT_EXAMINATION_MAP: Dict[str, List[Dict[str, Any]]] = {
    "心内科": [
        {
            "triggers": ("胸痛", "胸闷", "心悸", "心律失常", "晕厥", "冠心病", "心绞痛", "心肌梗死"),
            "examinations": ["心电图（ECG）", "超声心动图", "甲状腺功能检查（TFTs）", "动态心电图（Holter）", "心肌酶谱"],
            "reason": "胸痛、胸闷、心悸或晕厥提示心肌缺血/心律失常/结构性心脏病风险，心电、动态心电和超声心动图可区分节律、缺血和结构异常并直接影响急诊处置。",
        },
        {
            "triggers": ("冠状动脉粥样硬化性心脏病", "cad", "劳力性胸痛", "活动后胸痛", "活动后胸闷", "活动时胸口发紧", "爬楼胸闷", "提重物胸闷", "缺血性心肌病", "陈旧性心肌梗死"),
            "examinations": ["心电图（ECG）", "心脏负荷试验", "超声心动图", "血脂检测组合", "炎症标志物检测组合", "冠状动脉造影"],
            "reason": "劳力性胸痛、活动后胸闷胸紧或已知 CAD/缺血性心肌病提示慢性心肌缺血通路，应优先完成心电图、负荷试验、超声、血脂及炎症风险评估，避免被体表或非靶向检查模板带偏。",
        },
        {
            "triggers": ("心衰", "水肿", "端坐呼吸", "活动后气促", "先天性心脏病", "发绀", "肺动脉", "瓣膜"),
            "examinations": ["心电图（ECG）", "超声心动图", "N末端B型利钠肽原（NT-proBNP）", "胸部X线检查（CXR）"],
            "reason": "水肿、发绀、活动后气促或已知先心/瓣膜病提示心功能或血流动力学异常，超声心动图、BNP 和胸片可评估结构、负荷与肺淤血程度。",
        },
        {
            "triggers": ("肺动脉高压", "特发性肺动脉高压", "遗传性肺动脉高压", "肺栓塞", "右心负荷", "bmpr2", "bmp9"),
            "examinations": ["超声心动图", "CT肺动脉造影（CTPA）", "N末端B型利钠肽原（NT-proBNP）", "右心导管检查（RHC）"],
            "reason": "不明原因呼吸困难合并肺动脉高压/右心负荷线索时，应先用超声心动图和 CTPA 排查结构病变与肺栓塞，再以 NT-proBNP 和右心导管明确血流动力学分型。",
        },
        {
            "triggers": ("室间隔缺损", "房间隔缺损", "动脉导管未闭", "法洛四联症", "右心室双出口", "主动脉瓣狭窄", "二尖瓣反流", "三尖瓣反流", "肺动脉瓣狭窄"),
            "examinations": ["超声心动图", "心电图（ECG）", "胸部X线检查（CXR）"],
            "reason": "明确的先天性心脏病或瓣膜性病名提示结构异常主导病程，应优先分批完成超声心动图、心电图和胸片，先回答解剖与心衰负荷问题，再决定是否升级更复杂成像。",
        },
    ],
    "口腔科": [
        {
            "triggers": ("牙痛", "冷热痛", "咬合痛", "食物嵌塞", "牙髓炎", "根尖周炎", "牙周"),
            "examinations": ["口腔检查", "牙髓活力测试", "根尖片", "牙周探诊"],
            "reason": "牙痛伴冷热刺激痛、咬合痛或食物嵌塞提示牙髓/根尖/牙周来源，口腔检查、牙髓活力、根尖片和牙周探诊能定位病因并决定根管、牙周或抗感染路径。",
        },
        {
            "triggers": ("口腔白斑", "鹅口疮", "口腔念珠菌", "口腔溃疡", "舌痛", "灼口", "地图舌"),
            "examinations": ["口腔检查", "口腔细胞学检查", "真菌镜检", "全血细胞计数（CBC）"],
            "reason": "口腔白斑、反复溃疡或舌部烧灼感需区分真菌感染、黏膜病变和贫血/免疫背景，口腔检查、细胞学/真菌镜检及血常规可改变诊断和用药。",
        },
    ],
    "皮肤科": [
        {
            "triggers": ("皮下肿块", "瘢痕旁", "表皮样", "粉瘤", "皮脂腺", "体表肿块", "中央开口"),
            "examinations": ["体格检查", "皮肤检查", "超声"],
            "reason": "瘢痕旁或皮下局限性肿块应先做局部视诊触诊和体表超声，确认囊性/实性及有无感染，而不是按心肺或全身肿瘤筛查开单。",
        },
        {
            "triggers": ("甲剥离", "银屑病甲", "甲板翘起", "甲下角质碎屑", "甲营养不良", "指甲", "趾甲"),
            "examinations": ["皮肤镜检查", "真菌镜检", "真菌培养及鉴定"],
            "reason": "甲板远端剥离、甲下角质碎屑或甲板翘起提示甲病变，需先用皮肤镜和真菌学检查区分甲剥离、甲癣及银屑病甲，避免把背景皮肤病直接当主诊断。",
        },
        {
            "triggers": ("皮疹", "鳞屑", "银屑病", "副银屑病", "湿疹", "瘙痒", "红斑", "丘疹"),
            "examinations": ["皮肤镜检查", "皮肤检查", "全血细胞计数（CBC）", "C反应蛋白（CRP）"],
            "reason": "皮疹、鳞屑或瘙痒性红斑提示炎症性皮肤病，皮肤检查/皮肤镜能评估形态学特征，血常规和 CRP 用于判断系统炎症或感染可能。",
        },
        {
            "triggers": ("足癣", "股癣", "间擦疹", "腹股沟瘙痒", "趾缝", "真菌", "斑贴", "接触性皮炎", "汗疱疹", "手癣", "花斑癣"),
            "examinations": ["真菌镜检", "真菌培养及鉴定", "斑贴试验", "皮肤活检"],
            "reason": "腹股沟/趾缝瘙痒、潮湿摩擦或接触诱因需区分真菌、细菌、接触性和非感染性间擦疹，真菌学、斑贴和必要皮肤活检能避免经验性误治。",
        },
    ],
    "内分泌科": [
        {
            "triggers": ("混合型高脂血症", "高脂血症", "血脂异常", "高甘油三酯", "高胆固醇", "甘油三酯", "胆固醇", "ldl", "hdl", "胰岛素抵抗", "黄色瘤", "黄色斑", "睑黄瘤"),
            "examinations": ["血脂检测组合", "甲状腺功能检查（TFTs）"],
            "reason": "代谢综合征背景下出现血脂异常或混合型高脂血症线索时，应先完成血脂谱这一核心检查，并同步查甲功排查继发性高脂血症，避免被右上腹不适牵着走而重复肝胆、凝血或肿瘤筛查。",
        },
        {
            "triggers": ("潮热", "盗汗", "围绝经", "闭经", "月经紊乱", "垂体", "产后无乳", "低血压"),
            "examinations": ["性激素全套检测", "甲状腺功能检查（TFTs）", "促肾上腺皮质激素（ACTH）检测", "垂体激素全套检测"],
            "reason": "潮热盗汗、闭经或产后垂体功能减退线索提示性腺/甲状腺/肾上腺轴异常，性激素、甲功、ACTH 和垂体激素可确认内分泌轴受累并指导补充顺序。",
        },
        {
            "triggers": ("糖尿病", "高血糖", "低钾", "低镁", "手足抽筋", "骨质疏松", "佝偻", "骨软化", "维生素d"),
            "examinations": ["血糖检测", "血清电解质", "维生素D检测", "甲状旁腺激素检测（PTH）"],
            "reason": "血糖异常、电解质紊乱、抽筋或骨代谢异常提示代谢/内分泌问题，血糖、电解质、维生素D 和 PTH 能区分代谢病因并指导补充或急救。",
        },
    ],
    "消化内科": [
        {
            "triggers": ("右上腹痛", "腹胀", "纳差", "肝硬化", "乙肝", "黄疸", "肝细胞癌", "腹水"),
            "examinations": ["腹部超声", "肝功能检查（LFTs）", "凝血功能全套", "甲胎蛋白（AFP）检测", "乙型肝炎病毒（HBV）检测组合"],
            "reason": "右上腹痛、黄疸、腹水或乙肝/肝硬化背景提示肝胆病变或肝癌风险，腹部超声、肝功、凝血、AFP 和 HBV 检测可评估病因、严重程度和肿瘤线索。",
        },
        {
            "triggers": ("腹痛", "腹泻", "呕吐", "黑便", "便血", "便秘", "消瘦", "肠炎", "溃疡性结肠炎"),
            "examinations": ["体格检查", "全血细胞计数（CBC）", "粪便隐血试验（FOBT）", "结肠镜检查"],
            "reason": "腹痛、便血、黑便、慢性便秘或消瘦提示消化道炎症、出血或肿瘤风险，血常规、隐血和内镜能判断出血/炎症并定位病变。",
        },
    ],
    "普外科": [
        {
            "triggers": ("无痛性鲜红便血", "痔", "肿物脱出", "肛周疼痛", "流脓", "肛瘘", "肛周脓肿"),
            "examinations": ["直肠指检（DRE）", "肛门镜检查", "肛门超声", "盆腔MRI"],
            "reason": "鲜红便血、肛周疼痛流脓或肿物脱出提示痔、肛瘘或肛周脓肿，DRE/肛门镜可直接观察，肛门超声和盆腔MRI可评估瘘管及深部脓肿。",
        },
        {
            "triggers": ("右上腹痛", "murphy", "胆囊炎", "胆结石", "胆总管", "黄疸"),
            "examinations": ["腹部超声", "肝肾功能检查（LFTs/RFTs）", "全血细胞计数（CBC）", "C反应蛋白（CRP）"],
            "reason": "右上腹痛、Murphy 征或胆石线索提示急性胆囊炎/胆道梗阻，腹部超声和肝胆生化可定位结石梗阻，血常规/CRP 评估炎症程度。",
        },
    ],
    "血液科": [
        {
            "triggers": ("贫血", "乏力", "瘀青", "鼻出血", "反复感染", "白血病", "血小板", "全血细胞减少"),
            "examinations": ["全血细胞计数（CBC）", "外周血涂片", "骨髓检查", "骨髓穿刺和活检（BMAB）"],
            "reason": "贫血、瘀青、鼻出血、反复感染或全血细胞异常提示造血系统疾病，CBC、外周血涂片和骨髓检查可区分缺铁、骨髓衰竭与白血病/增殖性疾病。",
        },
        {
            "triggers": ("淋巴结肿大", "脾大", "盗汗", "消瘦", "淋巴瘤", "骨髓瘤", "单克隆"),
            "examinations": ["淋巴结活检", "正电子发射断层显像-计算机断层扫描（PET-CT）", "血清蛋白电泳（SPEP）", "骨髓穿刺和活检（BMAB）"],
            "reason": "无痛性淋巴结肿大、脾大、盗汗消瘦或浆细胞病线索提示淋巴/浆细胞肿瘤，活检、PET-CT、蛋白电泳和骨髓检查可确诊及分期。",
        },
    ],
    "免疫科": [
        {
            "triggers": ("骶髂", "臀部交替痛", "晨起腰臀僵硬", "炎性腰背痛", "faber", "帕特里克", "皮耶达卢"),
            "examinations": ["体格检查", "帕特里克试验（FABER）", "骨盆挤压与分离试验", "皮耶达卢征", "C反应蛋白（CRP）", "红细胞沉降率（ESR）", "磁共振成像（MRI）", "X线检查"],
            "reason": "骶髂区痛、晨僵或诱发试验阳性提示骶髂关节炎等炎性轴性病变，需先用骶髂诱发试验、炎症指标及 MRI/X 线确认，而不是误走心肺或单纯腰椎间盘模板。",
        },
        {
            "triggers": ("关节痛", "晨僵", "口腔溃疡", "蝶形红斑", "光敏", "狼疮", "系统性红斑狼疮"),
            "examinations": ["抗核抗体（ANA）谱", "抗双链DNA抗体（anti-dsDNA）", "补体成分分析", "尿液分析（UA）", "全血细胞计数（CBC）"],
            "reason": "关节痛、晨僵、口腔溃疡或光敏皮疹提示系统性自身免疫病，ANA/dsDNA/补体、尿检和血常规可评估 SLE 活动度及肾/血液受累。",
        },
        {
            "triggers": ("类风湿", "强直", "腰背痛", "骶髂", "血管炎", "紫癜", "复发性多软骨炎", "耳鼻软骨"),
            "examinations": ["类风湿因子（RF）", "HLA-B27分型", "C反应蛋白（CRP）", "红细胞沉降率（ESR）", "抗中性粒细胞胞质抗体（ANCA）谱"],
            "reason": "炎性关节痛、腰背痛、紫癜或耳鼻软骨炎提示风湿免疫/血管炎谱系，RF、HLA-B27、炎症指标和 ANCA 可区分疾病类型及活动度。",
        },
        {
            "triggers": ("过敏性紫癜", "iga血管炎", "非血小板减少性紫癜", "按压不褪色", "腹痛", "血尿", "蛋白尿"),
            "examinations": ["全血细胞计数（CBC）", "C反应蛋白（CRP）", "尿液分析（UA）", "免疫球蛋白A（IgA）检测", "腹部超声"],
            "reason": "感染后紫癜伴腹痛、关节痛或血尿时应优先走 IgA 血管炎路径，血常规、炎症指标、尿检、IgA 和腹部超声能同时评估肠道及肾脏受累。",
        },
    ],
    "感染科": [
        {
            "triggers": ("腮腺肿大", "耳下肿痛", "张口疼痛", "腮腺炎", "流行性腮腺炎", "mumps", "接触腮腺炎患儿"),
            "examinations": ["体格检查", "流行性腮腺炎病毒核酸检测（Mumps NAT）", "血清学抗体检测", "全血细胞计数（CBC）"],
            "reason": "耳下/腮腺区肿痛伴发热或流行病学接触时，应优先确认腮腺受累并完成 Mumps NAT 与血清学抗体检测，避免把儿童腮腺肿大误导向口腔、鼻科或骨科路径。",
        },
        {
            "triggers": ("发热", "寒战", "感染", "败血症", "血培养", "免疫抑制", "hiv", "机会感染"),
            "examinations": ["全血细胞计数（CBC）", "C反应蛋白（CRP）", "血培养", "HIV病毒载量检测"],
            "reason": "发热寒战、免疫抑制或 HIV 背景提示系统感染或机会感染风险，血常规、CRP、血培养和 HIV 病毒载量能判断感染证据和免疫控制状态。",
        },
        {
            "triggers": ("咽痛", "扁桃体", "链球菌", "颈部淋巴结炎", "口腔念珠菌", "鹅口疮", "钩端螺旋体", "洪水"),
            "examinations": ["咽拭子培养", "抗链球菌溶血素O（ASO）滴度", "真菌镜检", "肝肾功能检查（LFTs/RFTs）"],
            "reason": "咽痛/扁桃体、鹅口疮或洪水接触后发热肌痛提示特定感染暴露，咽拭子、ASO、真菌镜检及肝肾功能可明确病原和重症风险。",
        },
        {
            "triggers": ("组织胞浆菌病", "球孢子菌病", "肺孢子菌", "pjp", "隐球菌", "鸟粪", "蝙蝠粪", "aids", "cd4"),
            "examinations": ["真菌培养及鉴定", "核酸扩增检测（NAAT）", "支气管肺泡灌洗液（BALF）分析", "胸部CT扫描（Chest CT）"],
            "reason": "免疫抑制伴鸟蝙蝠暴露、AIDS 或机会性感染病名时，应优先留取病原学标本并做胸部 CT，避免只围着常规细菌感染或心衰模板开单。",
        },
    ],
    "肾内科": [
        {
            "triggers": ("少尿", "水肿", "蛋白尿", "血尿", "慢性肾脏病", "终末期肾病", "高钾", "酸中毒"),
            "examinations": ["尿液分析（UA）", "肾功能检查（RFTs）", "血清电解质", "肾脏超声", "心电图（ECG）"],
            "reason": "少尿、水肿、蛋白尿/血尿或高钾酸中毒提示肾功能恶化，尿检、肾功、电解质、肾脏超声和心电图可评估病因、分期及高钾心律风险。",
        },
        {
            "triggers": ("多囊肾", "肾囊肿", "肾血管", "肾性骨营养不良", "低钙", "高磷"),
            "examinations": ["肾脏超声", "肾功能检查（RFTs）", "甲状旁腺激素检测（PTH）", "维生素D检测"],
            "reason": "肾囊性病变或 CKD 骨矿物异常线索需评估结构和矿物代谢，肾脏超声、肾功、PTH 和维生素D可指导分期和补充/透析策略。",
        },
    ],
    "神经内科": [
        {
            "triggers": ("抽搐", "意识丧失", "癫痫", "发作后", "脑电", "头痛", "偏头痛"),
            "examinations": ["脑电图（EEG）", "脑MRI", "血清电解质", "心电图（ECG）"],
            "reason": "抽搐、意识丧失、发作后状态或反复头痛提示癫痫/结构性或代谢性诱因，EEG、脑MRI、电解质和心电图可区分神经源性、代谢性与心源性事件。",
        },
        {
            "triggers": ("肢体无力", "麻木", "肌无力", "肌萎缩", "神经传导", "臂丛", "神经根"),
            "examinations": ["肌电图和神经传导检查（EMG/NCS）", "脑MRI", "颈椎MRI", "血清电解质"],
            "reason": "肢体无力、麻木、肌萎缩或根性疼痛提示神经肌肉/中枢或脊髓病变，肌电神经传导、MRI 和电解质可定位病变并排除代谢因素。",
        },
    ],
    "妇产科": [
        {
            "triggers": ("继发性闭经", "闭经", "停经", "月经紊乱", "节食", "体重骤降", "压力大", "下丘脑性闭经"),
            "examinations": ["体格检查", "人绒毛膜促性腺激素（hCG）检测", "性激素全套检测", "基础体温（BBT）记录", "盆腔超声"],
            "reason": "停经/闭经合并体重骤降、节食或心理应激时，应先用单项 hCG 排除妊娠，再完成体格检查、性激素、基础体温和盆腔超声，区分功能性下丘脑-垂体抑制与卵巢/子宫结构性病因，避免血/尿 hCG 重复开具。",
        },
        {
            "triggers": ("痛经", "月经过多", "阴道出血", "单角子宫", "子宫肌瘤", "残角子宫", "妊娠"),
            "examinations": ["盆腔超声", "人绒毛膜促性腺激素（hCG）检测", "全血细胞计数（CBC）"],
            "reason": "痛经、异常出血、妊娠相关线索或子宫畸形提示妇科结构/妊娠问题，盆腔超声、hCG 和血常规可评估妊娠状态、贫血及局部病变。",
        },
        {
            "triggers": ("接触性出血", "宫颈", "阴道分泌物", "外阴", "巴氏腺", "老年性阴道炎", "hpv"),
            "examinations": ["盆腔检查", "盆腔超声", "宫颈细胞学检查", "人乳头瘤病毒核酸检测（HPV NAT）", "阴道镜检查"],
            "reason": "接触性出血、宫颈病变或异常分泌物需排除裂伤、息肉和上皮病变，盆腔超声可识别宫颈裂隙/瘢痕，细胞学、HPV 和阴道镜决定随访或治疗。",
        },
    ],
    "肿瘤科": [
        {
            "triggers": ("肿块", "占位", "消瘦", "恶性", "癌", "肝细胞癌", "直肠癌", "乳腺癌", "肺癌", "淋巴瘤"),
            "examinations": ["切除活检", "增强CT扫描（CECT）", "正电子发射断层显像-计算机断层扫描（PET-CT）", "全血细胞计数（CBC）"],
            "reason": "进行性肿块、消瘦、占位或标准癌种线索提示恶性肿瘤，活检提供病理金标准，增强CT/PET-CT用于分期并指导手术、放化疗或系统治疗。",
        },
        {
            "triggers": ("肝癌", "肝细胞癌", "乙肝", "肝硬化", "甲胎蛋白", "直肠肿块", "结直肠癌"),
            "examinations": ["甲胎蛋白（AFP）检测", "增强腹部CT扫描（Abdominal CECT）", "结肠镜检查", "切除活检"],
            "reason": "肝癌或结直肠肿瘤线索需病灶定位、标志物和病理确认，AFP、增强腹部CT、结肠镜和活检可完成诊断分期闭环。",
        },
    ],
    "眼科": [
        {
            "triggers": ("角膜混浊", "角膜发白", "出生即", "出生后即", "畏光流泪", "白瞳", "角膜直径增大"),
            "examinations": ["裂隙灯检查", "眼压测量（IOP）", "角膜厚度测量", "超声生物显微镜检查（UBM）", "眼前节光学相干断层扫描（AS-OCT）", "房角镜检查", "眼部B超检查", "眼底镜检查", "眼前节摄影", "基因检测"],
            "reason": "出生即角膜混浊、畏光流泪或白瞳提示先天性角膜混浊/继发青光眼等前节结构病变，需系统完成裂隙灯、眼压、角膜厚度、UBM、AS-OCT 与房角/眼底评估。",
        },
        {
            "triggers": ("视神经萎缩", "视盘苍白", "视盘颜色", "中心暗点", "色觉障碍", "视野缩小", "矫正视力无改善"),
            "examinations": ["眼底镜检查", "视野检查", "色觉检查", "视觉诱发电位（VEP）", "脑和眼眶MRI", "脑和眼眶CT扫描（Brain/Orbital CT）"],
            "reason": "视盘苍白、中心暗点、色觉障碍或矫正视力无改善提示视神经通路病变，眼底/视野/色觉/VEP 可确认视神经功能损害，脑和眼眶影像用于排除压迫或颅眶病变。",
        },
        {
            "triggers": ("视物模糊", "畏光", "眼痛", "眼红", "青光眼", "虹膜", "葡萄膜炎", "前房"),
            "examinations": ["视力检查", "裂隙灯检查", "眼压测量（IOP）", "视野检查", "眼底镜检查"],
            "reason": "视物模糊、畏光、眼痛或青光眼/虹膜线索提示前节炎症、眼压或视神经受累，视力、裂隙灯、眼压、视野和眼底可定位并指导激素/降眼压安全。",
        },
        {
            "triggers": ("白瞳", "早产儿视网膜病变", "视网膜", "斜视", "弱视", "屈光", "睑外翻", "流泪"),
            "examinations": ["眼底镜检查", "眼底摄影", "眼部B超检查", "视网膜电图（ERG）", "裂隙灯检查"],
            "reason": "白瞳、早产儿视网膜病变、斜弱视或睑外翻流泪提示视网膜/屈光/眼睑结构问题，眼底、B超、ERG 和裂隙灯能判断致盲风险和手术/激光时机。",
        },
    ],
    "骨科": [
        {
            "triggers": ("髌骨软化", "髌股", "膝前痛", "膝关节前痛", "上下楼", "下楼", "蹲起", "髌骨"),
            "examinations": ["髌骨研磨试验（Clarke征）", "髌骨浮动试验（Ballottement）"],
            "reason": "膝关节前痛或上下楼梯加重提示髌股关节受累，需用髌骨专科体格检查确认疼痛来源并评估积液。",
        },
        {
            "triggers": ("髌腱病", "跳跃膝", "髌骨下极", "运动员", "跳跃训练", "肌腱"),
            "examinations": ["体格检查", "超声", "维多利亚运动研究所髌腱评估量表（VISA-P）评分"],
            "reason": "髌骨下极疼痛、运动负荷相关或跳跃膝线索提示髌腱病，局部体格检查、肌腱超声和 VISA-P 评分可确认肌腱病变并量化功能。",
        },
        {
            "triggers": ("摔倒", "外伤", "骨折", "肘", "肩", "腕", "踝", "肿胀", "畸形", "不能负重"),
            "examinations": ["体格检查", "X线检查", "关节X线检查", "骨骼X线检查"],
            "reason": "外伤后局部剧痛、肿胀、畸形或不能负重提示骨折/脱位，体格检查和针对部位 X 线可明确骨性损伤并决定复位固定策略。",
        },
        {
            "triggers": ("腰背痛", "颈肩臂", "麻木", "神经根", "椎间盘", "压缩性骨折", "长期激素"),
            "examinations": ["体格检查", "磁共振成像（MRI）", "X线检查", "双能X线吸收测定法（DEXA）"],
            "reason": "腰背/颈肩臂痛伴神经症状、外伤或长期激素提示神经压迫、压缩骨折或骨质疏松，MRI/X线和 DEXA 可定位病变并评估骨强度。",
        },
        {
            "triggers": ("关节松弛", "半脱位", "皮肤过伸", "易瘀青", "埃勒斯-当洛综合征"),
            "examinations": ["基因检测", "凝血功能全套", "全血细胞计数（CBC）", "组织病理学检查"],
            "reason": "关节松弛伴易瘀青或皮肤过伸提示结缔组织脆弱性疾病，需同时补齐遗传、凝血和组织证据，避免误当作单纯运动损伤处理。",
        },
    ],
    "耳鼻咽喉科": [
        {
            "triggers": ("视力模糊", "视力下降", "眼球运动", "眼眶", "眶内", "畏光", "剧烈头痛"),
            "examinations": ["鼻内镜检查", "鼻旁窦CT扫描（Sinus CT）", "眼眶CT扫描（Orbital CT）", "视力检查", "眼球运动检查"],
            "reason": "鼻窦症状合并视力下降、眼球运动异常、畏光或剧烈头痛提示鼻窦结构病变可能累及眶内或视神经，需同步用鼻内镜/鼻窦CT定位原发病灶，并用眼眶CT、视力和眼球运动检查评估并发症。",
        },
        {
            "triggers": ("鼻旁窦囊肿", "鼻窦囊肿", "鼻旁窦", "鼻窦", "鼻塞", "鼻腔", "面部胀痛"),
            "examinations": ["鼻内镜检查", "鼻旁窦CT扫描（Sinus CT）"],
            "reason": "鼻腔/鼻窦症状或鼻旁窦囊肿线索提示鼻腔鼻窦结构性病变，需内镜观察开口与黏膜，并用鼻窦CT定位范围和骨性解剖。",
        },
        {
            "triggers": ("声嘶", "嘶哑", "喉囊肿", "异物感", "喘憋", "声门", "喉软化", "喉炎"),
            "examinations": ["喉镜检查", "颈部CT扫描（Neck CT）", "鼻咽喉镜检查"],
            "reason": "声嘶、喉部异物感、喘憋或声门上占位提示喉囊肿等喉部结构性病变或气道狭窄，喉镜直接观察声门/声带，颈部CT评估囊肿范围和气道受压。",
        },
        {
            "triggers": ("婴儿期", "听力反应弱", "叫名字不转头", "听不见轻声说话", "语言发育迟缓", "说话慢", "新生儿听力筛查", "先天性中耳畸形"),
            "examinations": ["听力测定", "鼓室压图及声导抗检查", "听性脑干反应（ABR）", "颞骨高分辨率CT扫描（Temporal Bone HRCT）"],
            "reason": "婴幼儿期起病的听力反应弱、语言发育迟缓或新生儿筛查异常提示先天性/结构性听力损失，需先用听力测定、声导抗和 ABR 完成功能定性定位，再以颞骨 HRCT 评估中耳和骨性结构。",
        },
        {
            "triggers": ("耳痛", "耳鸣", "听力下降", "突发性聋", "眩晕", "中耳炎", "乳突", "耳硬化"),
            "examinations": ["耳镜检查", "听力测定", "鼓室压图及声导抗检查", "颞骨高分辨率CT扫描（Temporal Bone HRCT）"],
            "reason": "耳痛、耳鸣、听力下降或眩晕提示外中内耳病变，耳镜、听力和声导抗可区分传导/感音问题，HRCT用于评估骨性结构和慢性病变。",
        },
    ],
    "儿科": [
        {
            "triggers": ("歪头", "斜颈", "胸锁乳突肌", "颈部包块", "先天性肌性斜颈", "头偏向一侧"),
            "examinations": ["体格检查", "超声"],
            "reason": "婴幼儿歪头、头偏向一侧或胸锁乳突肌增厚提示先天性肌性斜颈，应优先分批完成颈部体格检查与超声，避免直接误判为淋巴瘤或复杂颈部占位。",
        },
        {
            "triggers": ("新生儿", "婴儿", "尿液甜", "甜尿", "胆汁性呕吐", "未排胎粪", "腹胀", "代谢危象", "嗜睡", "惊厥"),
            "examinations": ["血清电解质", "动脉血气（ABG）", "血氨检测", "尿有机酸分析", "腹部X线片（AXR）"],
            "reason": "新生儿甜味尿、胆汁性呕吐、未排胎粪或代谢性神经症状提示代谢危象或肠梗阻，电解质/血气/血氨/尿有机酸和腹部X线可快速区分危重代谢与外科急症。",
        },
        {
            "triggers": ("黄疸", "胆道闭锁", "肝大", "脾大", "灰白便", "克里格勒", "酪氨酸血症"),
            "examinations": ["肝肾功能检查（LFTs/RFTs）", "腹部超声", "基因检测"],
            "reason": "婴儿黄疸、灰白便或胆道闭锁/代谢性肝病线索提示肝胆系统高危病变，肝肾功能、腹部超声和遗传学检查可帮助尽快区分手术性与代谢性病因。",
        },
        {
            "triggers": ("先天性心脏病", "室间隔缺损", "房间隔缺损", "动脉导管未闭", "吃奶喘", "喂养困难", "多汗", "心脏杂音", "发绀"),
            "examinations": ["超声心动图", "心电图（ECG）", "胸部X线检查（CXR）"],
            "reason": "婴儿吃奶喘、多汗、发绀或已知先心病提示血流动力学异常，应优先分批完成超声心动图、心电图和胸片，而不是泛化代谢筛查。",
        },
        {
            "triggers": ("早产", "白瞳", "先天性白内障", "早产儿视网膜病变", "发育迟缓"),
            "examinations": ["眼底镜检查", "裂隙灯检查", "基因检测"],
            "reason": "早产白瞳或先天性眼病线索提示致盲风险，需先做眼底和裂隙灯检查，必要时用基因检测补充病因分层。",
        },
        {
            "triggers": ("抽动", "多动", "注意缺陷", "儿童", "学习困难", "行为", "心理"),
            "examinations": ["心理评估", "脑电图（EEG）", "全血细胞计数（CBC）", "抗链球菌溶血素O（ASO）滴度"],
            "reason": "儿童抽动、多动或行为学习问题需区分抽动障碍、癫痫样发作和感染后免疫相关问题，心理评估、EEG、血常规和 ASO 可支持分层诊断。",
        },
    ],
    "呼吸内科": [
        {
            "triggers": ("慢性阻塞性肺疾病", "慢阻肺", "copd", "aecopd", "fev1/fvc", "固定性阻塞", "雾霾", "黄痰"),
            "examinations": ["肺功能检查（PFTs）", "动脉血气（ABG）", "胸部X线检查（CXR）", "全血细胞计数（CBC）", "C反应蛋白（CRP）", "痰培养"],
            "reason": "慢阻肺/COPD 线索或支气管扩张剂后 FEV1/FVC 降低提示固定性气流受限，肺功能确诊，血气评估通气衰竭，胸片和炎症/痰培养用于判断感染诱发和抗生素选择。",
        },
        {
            "triggers": ("咳嗽", "咳痰", "黄痰", "发热", "气促", "胸闷", "肺炎", "支气管炎", "喘鸣"),
            "examinations": ["体格检查", "全血细胞计数（CBC）", "C反应蛋白（CRP）", "胸部X线检查（CXR）"],
            "reason": "咳嗽咳痰、发热、气促或喘鸣提示呼吸道感染/支气管肺部病变，体格、血常规、CRP 和胸片能区分感染、肺炎和气道阻塞。",
        },
        {
            "triggers": ("哮喘", "喘息", "过敏性肺炎", "鸟", "霉菌", "粉尘", "磨玻璃", "呼吸困难", "睡眠呼吸"),
            "examinations": ["肺功能检查（PFTs）", "胸部高分辨率CT（Chest HRCT）", "胸部X线检查（CXR）", "多导睡眠监测（PSG）"],
            "reason": "喘息、抗原暴露后呼吸困难、磨玻璃影或睡眠呼吸障碍提示气道反应、间质/过敏性肺病或 OSA，肺功能、HRCT、胸片和 PSG 可确定分型。",
        },
        {
            "triggers": ("呛咳", "误吸", "气道异物", "吸入性肺炎"),
            "examinations": ["胸部X线检查（CXR）", "支气管镜检查"],
            "reason": "呛咳后发热、咳嗽或气促时需优先排查误吸和气道异物，胸片与支气管镜比泛化炎症筛查更能直接改变处置路径。",
        },
    ],
    "泌尿外科": [
        {
            "triggers": ("器质性勃起功能障碍", "勃起功能障碍", "勃起困难", "晨勃减少", "性功能", "ed"),
            "examinations": ["性激素全套检测", "勃起功能检测", "多普勒超声"],
            "reason": "勃起困难伴器质性线索需区分内分泌、神经血管和功能状态，性激素、勃起功能检测与多普勒超声可改变病因判断和治疗路径。",
        },
        {
            "triggers": ("尿频", "尿急", "尿痛", "排尿困难", "膀胱", "前列腺", "尿道", "尿路感染", "漏尿", "压力性尿失禁", "尿培养阴性"),
            "examinations": ["尿液分析（UA）", "尿培养", "泌尿道超声", "尿动力学检查（UDS）"],
            "reason": "尿频尿急、漏尿或排尿困难时需先区分感染、梗阻与储尿功能异常；尿检/尿培养、泌尿系超声和尿动力学能避免把复杂下尿路症状都当成单纯感染。",
        },
        {
            "triggers": ("尿道口", "烧灼痛", "接触性出血", "尿道肉阜", "尿道下裂", "尿道上裂", "阴囊", "精索静脉曲张", "睾丸"),
            "examinations": ["体格检查", "泌尿道超声", "多普勒超声", "精液分析", "尿液分析（UA）"],
            "reason": "尿道口病变、阴囊坠胀或精索静脉曲张线索需先做局部查体与泌尿/多普勒超声确认解剖和血流；有备孕或生育力担忧时用精液分析评估功能，尿检仅用于排除尿路感染证据。",
        },
    ],
}

_LOW_VALUE_EXAM_REASON_MARKERS = (
    "常规检查",
    "全面评估",
    "基础筛查",
    "补齐",
    "进一步检查",
    "完善检查",
)


_consultation_gap_question = consultation_gap_question


def _retain_successful_differential(
    case_state: Dict[str, Any],
    refreshed: List[Any],
    fingerprint: str,
) -> List[Any]:
    """Replace cached reasoning only when a refresh produced usable output."""
    if refreshed:
        case_state["preliminary_differential"] = refreshed
        case_state["last_successful_differential"] = refreshed
        case_state["differential_fingerprint"] = fingerprint
        return refreshed
    return (
        case_state.get("preliminary_differential")
        or case_state.get("last_successful_differential")
        or []
    )


def _assess_diagnostic_confidence(
    *,
    case_profile: Dict[str, Any],
    differential: List[Any],
    examinations: Dict[str, Any],
) -> Dict[str, Any]:
    """Estimate whether the case is ready to move from history to tests or to finalization."""
    profile = {str(key): clean_text(value) for key, value in case_profile.items()}
    differentials = [item for item in differential if isinstance(item, dict)]
    ordered_exams = as_text_list(examinations.get("ordered_examinations"))
    results = examinations.get("examination_results") or {}
    actionable_results = 0
    if isinstance(results, list):
        for entry in results:
            payload = entry.get("结果") if isinstance(entry, dict) else None
            if not isinstance(payload, dict):
                continue
            status = clean_text(payload.get("status")).lower()
            result_text = clean_text(payload.get("result"))
            if result_text and status not in {"pending", "unavailable", "invalid"}:
                actionable_results += 1
    elif isinstance(results, dict):
        for value in results.values():
            if not isinstance(value, dict):
                continue
            status = clean_text(value.get("status")).lower()
            result_text = clean_text(value.get("result"))
            if result_text and status not in {"pending", "unavailable", "invalid"}:
                actionable_results += 1

    consult_fields = (
        "chief_complaint_timeline",
        "past_history",
        "medication_allergy_history",
        "personal_exposure_history",
    )
    consult_score = sum(
        1 for field in consult_fields if profile.get(field) not in {"", "未知"}
    ) / float(len(consult_fields))
    diff_score = min(len(differentials), 3) / 3.0
    if any(item.get("must_rule_out") is True for item in differentials):
        diff_score = min(1.0, diff_score + 0.2)
    exam_score = min(actionable_results, 3) / 3.0
    if ordered_exams and not actionable_results:
        exam_score = 0.15

    confidence = round(consult_score * 0.35 + diff_score * 0.4 + exam_score * 0.25, 2)
    missing_evidence: List[str] = []
    if consult_score < 0.5:
        missing_evidence.append("问诊信息不足")
    if len(differentials) < 2:
        missing_evidence.append("鉴别诊断不足")
    if actionable_results < 1:
        missing_evidence.append("客观检查证据不足")

    if confidence >= 0.75 and len(differentials) >= 2 and actionable_results >= 1:
        recommendation = "ready_diagnose"
    elif consult_score < 0.5:
        recommendation = "continue_consult"
    elif actionable_results < 1:
        recommendation = "continue_exam"
    else:
        recommendation = "continue_consult" if len(differentials) < 2 else "continue_exam"

    return {
        "confidence": confidence,
        "consult_score": round(consult_score, 2),
        "diff_score": round(diff_score, 2),
        "exam_score": round(exam_score, 2),
        "missing_evidence": missing_evidence,
        "recommendation": recommendation,
    }


def _staged_exam_batch_limit(
    *,
    case_state: Dict[str, Any],
    base_limit: int,
    remaining_exam_slots: int,
) -> int:
    """Keep examination ordering staged: a targeted bundle first, then complementary follow-up."""
    if remaining_exam_slots <= 0:
        return 0
    base_limit = max(1, int(base_limit or 1))
    exam_rounds = int(case_state.get("exam_rounds", 0) or 0)
    has_actionable_result = _count_actionable_exam_payloads(
        case_state.get("examination_results") or {}
    ) > 0
    if exam_rounds == 0:
        cap = 4
    elif not has_actionable_result:
        cap = 3
    else:
        cap = 2
    return max(1, min(base_limit, remaining_exam_slots, cap))


def _count_actionable_exam_payloads(results: Any) -> int:
    count = 0
    if isinstance(results, list):
        iterable = [
            entry.get("结果") if isinstance(entry, dict) else None
            for entry in results
        ]
    elif isinstance(results, dict):
        iterable = results.values()
    else:
        iterable = []
    for value in iterable:
        if not isinstance(value, dict):
            continue
        status = clean_text(value.get("status")).lower()
        result_text = clean_text(value.get("result"))
        if result_text and status not in {"pending", "unavailable", "invalid"}:
            count += 1
    return count


def _case_and_differential_text(
    *,
    case_profile: Dict[str, Any],
    differential: List[Any],
    chat_history: Optional[List[Any]] = None,
) -> str:
    patient_turns = [
        message.get("text")
        for message in (chat_history or [])
        if isinstance(message, dict) and message.get("from") == "patient"
    ]
    return normalize_name(
        json.dumps(
            {
                "case_profile": {
                    key: value
                    for key, value in (case_profile or {}).items()
                    if key != "missing_critical_fields"
                },
                "differential": _differential_evidence_only(differential),
                "patient_history": patient_turns,
            },
            ensure_ascii=False,
        )
    )


def _differential_evidence_only(differential: List[Any]) -> List[Dict[str, Any]]:
    """Keep diagnosis names/supporting evidence; drop model-suggested exam noise."""
    evidence_fields = (
        "suspected_disease",
        "confidence_level",
        "subjective_probability",
        "must_rule_out",
        "history_support",
        "physical_support",
        "support_points",
        "against_points",
    )
    sanitized: List[Dict[str, Any]] = []
    for item in differential[:5] if differential else []:
        if not isinstance(item, dict):
            continue
        cleaned = {
            key: value
            for key, value in item.items()
            if key in evidence_fields and clean_text(value)
        }
        if cleaned:
            sanitized.append(cleaned)
    return sanitized


def _inferred_department_from_case(
    *,
    case_profile: Dict[str, Any],
    differential: List[Any],
    disease_to_department: Dict[str, str],
    disease_map: Dict[str, str],
    chat_history: Optional[List[Any]] = None,
) -> str:
    text = _case_and_differential_text(
        case_profile=case_profile,
        differential=differential,
        chat_history=chat_history,
    )
    if any(token in text for token in ("瘢痕旁", "皮下肿块", "表皮样", "粉瘤", "皮脂腺囊肿", "中央开口")):
        return "皮肤科"
    if any(token in text for token in ("骶髂", "臀部交替痛", "晨起腰臀僵硬", "炎性腰背痛", "faber", "帕特里克", "皮耶达卢")):
        return "免疫科"
    if any(token in text for token in ("腮腺肿大", "耳下肿痛", "张口疼痛", "流行性腮腺炎", "mumps")):
        return "感染科"
    if any(token in text for token in ("歪头", "斜颈", "胸锁乳突肌", "头偏向一侧")) and any(
        token in text for token in ("婴儿", "患儿", "儿童", "出生", "幼儿")
    ):
        return "儿科"
    if any(token in text for token in ("出生即角膜混浊", "角膜混浊", "角膜发白", "角膜直径增大")) and any(
        token in text for token in ("出生", "婴儿", "患儿", "畏光", "流泪", "白瞳")
    ):
        return "眼科"
    developmental_hearing = any(
        token in text
        for token in ("听力反应弱", "叫名字不转头", "听不见轻声说话", "语言发育迟缓", "说话慢", "新生儿听力筛查", "先天性中耳畸形")
    )
    if developmental_hearing and any(
        token in text for token in ("婴儿", "婴儿期", "患儿", "儿童", "新生儿", "发育")
    ):
        return "耳鼻咽喉科"
    if any(token in text for token in ("黄色瘤", "黄色斑", "黄色斑片", "黄色斑块", "眼睑黄色", "睑黄瘤")):
        return "内分泌科"
    if any(token in text for token in ("混合型高脂血症", "高脂血症", "血脂异常", "甘油三酯", "胆固醇")) and any(
        token in text for token in ("胰岛素抵抗", "代谢", "高血压", "肝酶", "右上腹")
    ):
        return "内分泌科"
    nasal_or_sinus = any(token in text for token in ("鼻", "鼻窦", "鼻旁窦", "鼻塞", "面部痛", "额面部"))
    orbital_red_flag = any(token in text for token in ("视力模糊", "视力下降", "眼球运动", "眼眶", "眶内", "畏光", "剧烈头痛"))
    if nasal_or_sinus and orbital_red_flag:
        return "耳鼻咽喉科"
    department = _infer_department_from_differential(
        differential,
        disease_to_department,
        disease_map,
    )
    if department:
        return department
    keyword_departments = (
        (("过敏性紫癜", "iga血管炎", "非血小板减少性紫癜", "按压不褪色", "紫癜伴腹痛", "紫癜伴血尿", "紫癜伴关节痛"), "免疫科"),
        (("组织胞浆菌病", "球孢子菌病", "口腔念珠菌病", "获得性免疫缺陷综合征", "aids", "hiv", "cd4", "机会感染", "鸟粪", "蝙蝠粪", "肺结核", "钩端螺旋体病"), "感染科"),
        (("肺动脉高压", "右心负荷", "bmpr2", "bmp9", "肺栓塞", "肺动脉瓣狭窄"), "心内科"),
        (("新生儿", "婴儿", "患儿", "儿童", "早产", "未排胎粪", "胆汁性呕吐", "尿液甜", "枫糖尿病", "先天性巨结肠", "先天性胆道闭锁", "先天性心脏病", "先天性肌性斜颈", "胸锁乳突肌"), "儿科"),
        (("视物", "视力", "畏光", "眼痛", "眼红", "白瞳", "眼压", "裂隙灯", "虹膜", "青光眼", "斜视", "弱视", "眼睑", "流泪", "角膜混浊", "角膜发白", "先天性角膜混浊", "先天性白内障", "角膜溃疡", "视网膜母细胞瘤", "早产儿视网膜病变"), "眼科"),
        (("牙痛", "牙龈", "牙髓", "根尖", "冷热痛", "咬合痛", "食物嵌塞", "口腔白斑", "鹅口疮", "舌痛", "灼口", "龋齿", "牙周炎", "牙髓炎", "颞下颌关节脱位"), "口腔科"),
        (("婴儿期", "听力反应弱", "叫名字不转头", "听不见轻声说话", "语言发育迟缓", "说话慢", "新生儿听力筛查", "先天性中耳畸形", "骨传导助听器"), "耳鼻咽喉科"),
        (("鼻", "鼻窦", "鼻旁窦", "流涕", "鼻塞", "耳鸣", "耳痛", "听力", "眩晕", "声嘶", "嘶哑", "喉", "咽", "扁桃体", "鼻旁窦囊肿", "喉囊肿", "梅尼埃病", "慢性鼻窦炎", "中耳炎", "突发性聋"), "耳鼻咽喉科"),
        (("月经", "痛经", "阴道", "宫颈", "盆腔", "子宫", "卵巢", "停经", "闭经", "妊娠", "外阴", "围绝经", "潮热", "盗汗", "巴氏腺囊肿", "宫颈上皮内瘤变", "多囊卵巢综合征", "老年性阴道炎", "继发性闭经", "体重骤降", "节食", "下丘脑性闭经"), "妇产科"),
        (("尿道口", "阴囊", "睾丸", "精索", "勃起", "晨勃", "性功能", "阴茎", "排尿", "尿频", "尿急", "尿痛", "尿失禁", "器质性勃起功能障碍", "压力性尿失禁", "急性膀胱炎", "急性细菌性前列腺炎", "尿道综合征", "阴茎硬结症", "肾结石", "输尿管结石"), "泌尿外科"),
        (("膝", "髌", "肘", "腕", "肩", "踝", "腰背", "颈肩", "骨折", "外伤", "运动痛", "上下楼", "不能负重", "关节肿痛", "髌骨软化症", "髌腱病", "肩袖损伤", "腰椎间盘突出", "关节积液", "埃勒斯当洛综合征"), "骨科"),
        (("过敏性紫癜", "iga血管炎", "白塞综合征", "系统性红斑狼疮", "系统性硬化症", "多血管炎性肉芽肿", "类风湿关节炎", "复发性多软骨炎", "骶髂关节炎", "骶髂", "晨僵", "口腔溃疡", "蝶形红斑", "光敏", "狼疮", "类风湿", "强直", "紫癜", "血管炎", "软骨炎", "关节痛"), "免疫科"),
        (("皮疹", "鳞屑", "瘙痒", "红斑", "丘疹", "水疱", "脓疱", "足癣", "股癣", "腹股沟", "趾缝", "斑贴", "汗疱疹", "花斑癣", "副银屑病", "大疱性类天疱疮", "荨麻疹", "甲剥离", "指甲", "趾甲", "甲板", "甲下角质"), "皮肤科"),
        (("抽搐", "意识丧失", "癫痫", "头痛", "偏头痛", "麻木", "无力", "肌萎缩", "神经", "脑电", "发作后", "脑震荡", "臂丛神经损伤", "脊髓性肌萎缩症", "抽动障碍"), "神经内科"),
        (("胸痛", "心悸", "心律", "心电", "冠心", "心绞痛", "晕厥", "心衰", "瓣膜", "先天性心脏", "发绀", "肺动脉高压", "房间隔缺损", "室间隔缺损", "动脉导管未闭", "法洛四联症", "主动脉瓣狭窄", "心房颤动", "扩张型心肌病", "风湿性心脏病", "缺血性心肌病"), "心内科"),
        (("咳嗽", "咳痰", "黄痰", "气促", "呼吸困难", "喘息", "哮喘", "肺炎", "胸片", "磨玻璃", "睡眠呼吸", "慢性阻塞性肺疾病", "过敏性肺炎", "支气管肺炎", "耶氏肺孢子菌肺炎", "肺隐球菌病", "肺念珠菌病", "呛咳", "误吸"), "呼吸内科"),
        (("右上腹", "黄疸", "肝硬化", "乙肝", "腹水", "纳差", "腹泻", "呕吐", "便血", "黑便", "胃痛", "胃炎", "胃溃疡", "胃出血", "酒精性肝病", "自身免疫性肝炎", "乳糜泻", "幽门螺杆菌感染", "反流性食管炎"), "消化内科"),
        (("肛周", "肛门", "痔", "肛瘘", "肛周脓肿", "胆囊炎", "胆结石", "乳腺肿块", "疝", "急腹症", "肛门息肉", "直肠脱垂", "乳腺囊性增生", "蜂窝织炎"), "普外科"),
        (("贫血", "瘀青", "鼻出血", "反复感染", "白血病", "血小板", "淋巴结肿大", "脾大", "盗汗", "骨髓", "多发性骨髓瘤", "骨髓增生异常综合征", "弥漫性大b细胞淋巴瘤", "血管性血友病"), "血液科"),
        (("发热", "寒战", "败血症", "血培养", "免疫抑制", "洪水", "钩端", "链球菌", "念珠菌", "不明原因发热", "巨细胞病毒感染", "腮腺炎", "流行性腮腺炎", "腮腺肿大", "耳下肿痛"), "感染科"),
        (("少尿", "水肿", "蛋白尿", "血尿", "慢性肾", "终末期肾", "高钾", "酸中毒", "肾功能", "多囊肾", "慢性肾脏病", "显微镜下多血管炎", "肾性骨营养不良", "肾血管性高血压"), "肾内科"),
        (("混合型高脂血症", "高脂血症", "血脂异常", "甘油三酯", "胆固醇", "ldl", "hdl", "糖尿病", "血糖", "甲状腺", "垂体", "肾上腺", "低钾", "低镁", "手足抽筋", "骨质疏松", "维生素d", "代谢", "桥本甲状腺炎", "高泌乳素血症", "原发性醛固酮增多症", "嗜铬细胞瘤", "尿崩症", "胰岛素抵抗"), "内分泌科"),
        (("肿块", "占位", "癌", "恶性", "肝细胞癌", "直肠癌", "乳腺癌", "肺癌", "淋巴瘤", "消瘦", "宫颈癌", "结肠癌", "胃癌", "前列腺癌", "甲状腺癌"), "肿瘤科"),
    )
    for triggers, candidate in keyword_departments:
        if any(normalize_name(trigger) in text for trigger in triggers):
            return candidate
    for disease_name, candidate in sorted(
        disease_to_department.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    ):
        if disease_name and disease_name in text:
            return candidate
    return ""


def _mapped_examination_recommendations(
    *,
    case_profile: Dict[str, Any],
    differential: List[Any],
    ordered: set[str],
    available_examinations: List[str],
    exam_resolver: Any,
    disease_to_department: Dict[str, str],
    disease_map: Dict[str, str],
    chat_history: Optional[List[Any]] = None,
) -> tuple[List[str], Dict[str, str]]:
    """Recommend standard exams from a department/system map before free LLM selection."""
    department = _inferred_department_from_case(
        case_profile=case_profile,
        differential=differential,
        disease_to_department=disease_to_department,
        disease_map=disease_map,
        chat_history=chat_history,
    )
    text = _case_and_differential_text(
        case_profile=case_profile,
        differential=differential,
        chat_history=chat_history,
    )
    available = set(as_text_list(available_examinations))
    recommendations: List[str] = []
    reasons: Dict[str, str] = {}
    for rule in _DEPARTMENT_EXAMINATION_MAP.get(department, []):
        triggers = tuple(normalize_name(trigger) for trigger in rule.get("triggers") or ())
        if not any(trigger and trigger in text for trigger in triggers):
            continue
        for raw_exam in as_text_list(rule.get("examinations")):
            exam = exam_resolver(raw_exam) if callable(exam_resolver) else clean_text(raw_exam)
            if not exam or exam not in available or exam in ordered or exam in recommendations:
                continue
            recommendations.append(exam)
            reasons[exam] = clean_text(rule.get("reason"))
    return recommendations, reasons


def _evidence_phrase_for_exam_reason(case_profile: Dict[str, Any], differential: List[Any]) -> str:
    profile_bits = []
    for key in ("chief_complaint_timeline", "summary", "red_flags"):
        value = case_profile.get(key)
        if isinstance(value, list):
            profile_bits.extend(as_text_list(value))
        else:
            cleaned = clean_text(value)
            if cleaned and cleaned != "未知":
                profile_bits.append(cleaned)
    if profile_bits:
        return "；".join(profile_bits[:2])
    for item in differential[:2]:
        if isinstance(item, dict):
            support = as_text_list(item.get("history_support") or item.get("support_points"))
            if support:
                return "；".join(support[:2])
    return ""


def _build_exam_order_justifications(
    *,
    examinations: List[str],
    case_profile: Dict[str, Any],
    differential: List[Any],
    mapped_reasons: Optional[Dict[str, str]] = None,
    llm_reason: str = "",
    exam_resolver: Any = None,
) -> Dict[str, Dict[str, str]]:
    purposes = build_exam_purpose_map(differential, examinations, exam_resolver=exam_resolver)
    evidence = _evidence_phrase_for_exam_reason(case_profile, differential)
    justifications: Dict[str, Dict[str, str]] = {}
    for name in examinations:
        reason = clean_text((mapped_reasons or {}).get(name))
        if not reason:
            purpose = "；".join(purposes.get(name) or [])
            if evidence and purpose:
                reason = "选择%s是因为当前资料提示%s；用于%s，阳性或阴性均会改变诊断概率、治疗安全或处置路径。" % (
                    name,
                    evidence,
                    purpose,
                )
            else:
                reason = clean_text(llm_reason) or "检查理由不足，仅作为低优先级候选。"
        priority = _exam_reason_priority(name=name, reason=reason, case_profile=case_profile, differential=differential)
        justifications[name] = {"reason": reason, "priority": priority}
    return justifications


def _exam_reason_priority(
    *,
    name: str,
    reason: str,
    case_profile: Dict[str, Any],
    differential: List[Any],
) -> str:
    text = clean_text(reason)
    if len(text) < 28:
        return "LOW"
    normalized = normalize_name(text)
    if any(normalize_name(marker) == normalized or normalize_name(marker) in normalized for marker in _LOW_VALUE_EXAM_REASON_MARKERS):
        if not any(token in normalized for token in ("因为", "提示", "用于", "确认", "排除", "改变")):
            return "LOW"
    case_text = normalize_name(json.dumps(case_profile or {}, ensure_ascii=False))
    diff_text = normalize_name(json.dumps(differential[:5] if differential else [], ensure_ascii=False))
    has_case_anchor = any(char in case_text for char in normalize_name(name) if "\u4e00" <= char <= "\u9fff") or any(
        token in normalized for token in ("因为", "主诉", "提示", "伴", "病程", "症状", "阳性", "阴性")
    )
    has_decision_anchor = any(token in normalized for token in ("用于", "确认", "排除", "评估", "阳性", "阴性", "改变", "诊断", "治疗"))
    has_diff_anchor = bool(diff_text and any(token in normalized for token in ("鉴别", "工作诊断", "疾病", "病变", "受累")))
    if has_case_anchor and has_decision_anchor:
        return "HIGH" if has_diff_anchor or len(text) >= 45 else "MEDIUM"
    return "LOW"


def _prioritize_exams_by_reason_strength(
    examinations: List[str],
    justifications: Dict[str, Dict[str, str]],
) -> List[str]:
    priority_rank = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    return sorted(
        examinations,
        key=lambda name: (priority_rank.get(justifications.get(name, {}).get("priority", "LOW"), 2), examinations.index(name)),
    )


def _exam_order_reason_text(justifications: Dict[str, Dict[str, str]], examinations: List[str]) -> str:
    lines = []
    for name in examinations:
        item = justifications.get(name) or {}
        lines.append("%s（%s）：%s" % (name, item.get("priority") or "LOW", item.get("reason") or "理由不足"))
    return "\n".join(lines)


def _pre_prescription_safety_hook(
    plan: Dict[str, Any],
    *,
    case_profile: Dict[str, Any],
    examinations: Dict[str, Any],
) -> Dict[str, Any]:
    """Explicit pre-prescription checklist before calling prescribe_treatment."""
    plan_out = dict(plan)
    treatment_plan = clean_text(plan_out.get("treatment_plan"))
    profile_text = clean_text(json.dumps(case_profile or {}, ensure_ascii=False))
    exam_text = clean_text(json.dumps(examinations or {}, ensure_ascii=False))
    combined = normalize_name(profile_text + " " + exam_text + " " + treatment_plan)
    forbidden_drugs = build_contraindicated_drugs(case_profile, examinations)

    allergy_known = case_profile.get("medication_allergy_history") not in (None, "", "未知")
    renal_hepatic_known = any(
        token in combined
        for token in ("肝肾功能", "肾功能", "肝功能", "肌酐", "egfr", "alt", "ast", "lfts", "rfts")
    )
    interaction_known = any(
        token in combined
        for token in ("现用药", "正在使用", "用药", "抗凝", "激素", "免疫抑制", "相互作用")
    )
    comorbidity_risk = []
    if any(token in combined for token in ("心衰", "心力衰竭", "肾病", "肾功能", "egfr", "抗凝", "胃溃疡")) and any(
        token in combined for token in ("nsaid", "布洛芬", "双氯芬酸", "塞来昔布")
    ):
        comorbidity_risk.append("合并心衰/肾病/抗凝或胃肠风险时避免或慎用 NSAIDs，优先替代镇痛并监测肾功能和出血风险。")
    if any(token in combined for token in ("哮喘", "喘息", "支气管痉挛", "慢阻肺", "copd")) and any(
        token in combined for token in ("nsaid", "非甾体", "布洛芬", "双氯芬酸", "塞来昔布", "阿司匹林")
    ):
        comorbidity_risk.append("哮喘/COPD 或支气管痉挛风险背景下避免或慎用 NSAIDs/阿司匹林类镇痛，优先选择对乙酰氨基酚等替代并监测呼吸症状。")

    checklist = dict(plan_out.get("safety_checklist") or {})
    checklist.update(
        {
            "allergy_contraindications_checked": allergy_known and not any(drug in treatment_plan for drug in forbidden_drugs),
            "comorbidity_contraindications_checked": not comorbidity_risk,
            "renal_hepatic_function_checked": renal_hepatic_known,
            "drug_interactions_checked": interaction_known,
        }
    )
    plan_out["safety_checklist"] = checklist

    safety_notes = []
    if forbidden_drugs:
        safety_notes.append("过敏/禁忌药物：已识别需回避 %s；提交前不得再次处方。" % "、".join(forbidden_drugs))
    elif allergy_known:
        safety_notes.append("过敏史：已核对当前用药/过敏史，未识别目录内明确禁忌药。")
    else:
        safety_notes.append("过敏史：信息仍不完整，处方前需再次核对药物过敏及交叉过敏。")
    safety_notes.extend(comorbidity_risk or ["合并症禁忌：未发现当前方案与已知合并症存在明确禁用冲突。"])
    if renal_hepatic_known:
        safety_notes.append("肝肾功能：已有肝肾功能或相关风险评估，按结果调整剂量/监测。")
    else:
        safety_notes.append("肝肾功能：尚未见明确评估；涉及抗感染、NSAIDs、抗凝、免疫抑制、造影或需肝肾代谢药物时先评估或暂缓。")
    safety_notes.append("相互作用：已将现用药、抗凝/激素/免疫抑制剂和妊娠可能纳入核对；信息缺失时按待核对处理。")

    pause = dict(plan_out.get("pre_treatment_safety_pause") or {})
    pause["allergy_contraindication_check"] = safety_notes[0]
    pause["comorbidity_contraindication_check"] = safety_notes[1]
    pause["renal_hepatic_function_check"] = safety_notes[2]
    pause["drug_interaction_check"] = safety_notes[3]
    plan_out["pre_treatment_safety_pause"] = pause

    review = clean_text(plan_out.get("medication_safety_review"))
    safety_block = "【处方前安全检查】\n" + "\n".join("- %s" % note for note in safety_notes)
    plan_out["medication_safety_review"] = (review + "\n" + safety_block).strip() if review else safety_block
    if "【处方前安全检查】" not in treatment_plan:
        plan_out["treatment_plan"] = (treatment_plan.rstrip() + "\n\n" + safety_block).strip()
    return plan_out


@dataclass(frozen=True)
class WorkflowLimits:
    min_doctor_turns: int = 1
    max_doctor_turns: int = 2
    max_doctor_turns_ceiling: int = 2
    max_exam_rounds: int = 2
    max_exam_rounds_ceiling: int = 2
    max_total_examinations: int = 6
    max_main_loop_iterations: int = 8
    max_llm_calls_per_patient: int = 16
    final_llm_reserve_calls: int = 3
    max_patient_seconds: int = 150
    special_case_max_patient_seconds: int = 180
    llm_call_timeout_seconds: int = 35
    final_llm_call_timeout_seconds: int = 40
    service_call_timeout_seconds: int = 25
    evaluation_call_timeout_seconds: int = 120
    force_diagnosis_buffer_seconds: int = 35
    consult_time_budget_seconds: int = 30
    examine_time_budget_seconds: int = 50
    diagnose_time_budget_seconds: int = 30
    min_differential_candidates: int = 3
    min_objective_exam_results: int = 1
    use_llm_action_planner: bool = False


class PatientCaseBudget:
    """Track per-patient time and LLM budget to avoid runaway loops."""

    def __init__(self, limits: WorkflowLimits):
        self.limits = limits
        self.started_at = time.monotonic()
        self.started_at_wallclock = datetime.now(timezone.utc).astimezone().isoformat()
        self.llm_calls = 0
        self.llm_calls_by_prompt: Dict[str, int] = {}
        self.loop_iterations = 0
        self.special_case = False
        self.current_stage = "consult"
        self.stage_started_at: Dict[str, float] = {"consult": self.started_at}
        self._last_loop_signature: Optional[tuple] = None
        self._stall_count = 0

    def set_special_case(self, enabled: bool) -> None:
        self.special_case = bool(enabled)

    def active_max_seconds(self) -> int:
        if self.special_case:
            return max(self.limits.max_patient_seconds, self.limits.special_case_max_patient_seconds)
        return self.limits.max_patient_seconds

    def record_stage(self, stage: str) -> None:
        if stage and stage != self.current_stage:
            self.current_stage = stage
            self.stage_started_at.setdefault(stage, time.monotonic())

    def stage_elapsed(self, stage: Optional[str] = None) -> float:
        key = stage or self.current_stage
        return time.monotonic() - self.stage_started_at.get(key, self.started_at)

    def consult_time_exceeded(self) -> bool:
        return self.stage_elapsed("consult") > self.limits.consult_time_budget_seconds

    def examine_time_exceeded(self) -> bool:
        return self.stage_elapsed("examine") > self.limits.examine_time_budget_seconds

    def note_loop_progress(self, signature: tuple) -> bool:
        """Return True when the same state repeats and a stall should force advance."""
        if signature == self._last_loop_signature:
            self._stall_count += 1
        else:
            self._stall_count = 0
        self._last_loop_signature = signature
        return self._stall_count >= 2

    def elapsed(self) -> float:
        return time.monotonic() - self.started_at

    def target_remaining(self) -> float:
        return max(0.0, self.limits.max_patient_seconds - self.elapsed())

    def remaining(self) -> float:
        return max(0.0, self.active_max_seconds() - self.elapsed())

    def time_critical(self) -> bool:
        """剩余时间已进入收口缓冲窗口。普通病例按 2.5 分钟，复杂病例按 3 分钟。"""
        return self.remaining() <= self.limits.force_diagnosis_buffer_seconds

    def should_force_finalize(self, in_consultation: bool = False) -> bool:
        """是否需要强制进入检查/诊断收口。

        LLM 调用次数与主循环迭代次数是硬上限。
        时间预算是软目标：在问诊阶段不以时间硬切断，只在已经离开问诊阶段时用于推动收口。
        """
        if self.llm_calls >= self.limits.max_llm_calls_per_patient:
            return True
        if self.loop_iterations >= self.limits.max_main_loop_iterations:
            return True
        if self.remaining() <= 0:
            return True
        if not in_consultation and self.time_critical():
            return True
        return False

    def can_call_llm(self, *, use_final_reserve: bool = False) -> bool:
        """Keep the last calls exclusively for the final diagnosis and JSON repair."""
        call_limit = self.limits.max_llm_calls_per_patient
        if not use_final_reserve:
            call_limit = max(0, call_limit - self.limits.final_llm_reserve_calls)
        if self.llm_calls >= call_limit:
            return False
        # 预留约一次最终诊断调用的时间；缓冲窗口内仍允许调用，由阶段机决定动作。
        if self.remaining() <= 15:
            return False
        return True

    def record_llm_call(self, prompt_name: str = "") -> None:
        self.llm_calls += 1
        key = clean_text(prompt_name) or "unknown"
        self.llm_calls_by_prompt[key] = self.llm_calls_by_prompt.get(key, 0) + 1

    def next_loop(self) -> None:
        self.loop_iterations += 1


def _workflow_minutes_to_seconds(
    value: Any,
    default_minutes: float,
    *,
    minimum: float = 1.0,
    maximum: float = 3.0,
) -> int:
    try:
        minutes = float(value)
    except (TypeError, ValueError):
        minutes = default_minutes
    minutes = min(maximum, max(minimum, minutes))
    return max(60, int(round(minutes * 60)))


def load_workflow_limits(config: Optional[Dict[str, Any]]) -> WorkflowLimits:
    workflow = (config or {}).get("workflow") or {}
    if not isinstance(workflow, dict):
        workflow = {}
    max_patient_seconds = _workflow_minutes_to_seconds(
        workflow.get("max_patient_minutes", 2.5),
        2.5,
    )
    special_case_max_patient_seconds = max(
        max_patient_seconds,
        _workflow_minutes_to_seconds(
            workflow.get("special_case_max_patient_minutes", 3),
            3,
        ),
    )
    # Reserve enough time for final generation, optional JSON repair, and submit.
    default_buffer = min(40, max(30, int(max_patient_seconds * 0.23)))
    configured_buffer = int(workflow.get("force_diagnosis_buffer_seconds", default_buffer))
    force_diagnosis_buffer_seconds = min(
        configured_buffer,
        default_buffer if max_patient_seconds <= 600 else configured_buffer,
        max(30, max_patient_seconds // 4),
    )
    min_turns = int(workflow.get("min_doctor_turns", 1))
    max_turns = int(workflow.get("max_doctor_turns", 2))
    max_turns_ceiling = int(workflow.get("max_doctor_turns_ceiling", 2))
    if max_turns_ceiling < max_turns:
        max_turns_ceiling = max_turns
    max_turns_ceiling = min(5, max_turns_ceiling)
    max_turns = min(max_turns_ceiling, max(1, max_turns))
    min_turns = max(1, min(min_turns, max_turns))

    max_exam = int(workflow.get("max_exam_rounds", 2))
    max_exam_ceiling = int(workflow.get("max_exam_rounds_ceiling", 2))
    max_exam_ceiling = min(5, max(max_exam, max_exam_ceiling))
    max_exam = min(max_exam_ceiling, max(1, max_exam))

    max_loop = int(workflow.get("max_main_loop_iterations", 8))
    theoretical_max = max_turns_ceiling + max_exam_ceiling + 4
    max_loop = min(max(6, max_loop), min(11, theoretical_max))

    consult_budget = int(workflow.get("consult_time_budget_seconds", 30))
    examine_budget = int(workflow.get("examine_time_budget_seconds", 50))
    diagnose_budget = int(workflow.get("diagnose_time_budget_seconds", 30))
    stage_total = consult_budget + examine_budget + diagnose_budget
    if stage_total > max_patient_seconds - force_diagnosis_buffer_seconds:
        scale = (max_patient_seconds - force_diagnosis_buffer_seconds) / max(stage_total, 1)
        consult_budget = int(consult_budget * scale)
        examine_budget = int(examine_budget * scale)
        diagnose_budget = int(diagnose_budget * scale)

    return WorkflowLimits(
        min_doctor_turns=min_turns,
        max_doctor_turns=max_turns,
        max_doctor_turns_ceiling=max_turns_ceiling,
        max_exam_rounds=max_exam,
        max_exam_rounds_ceiling=max_exam_ceiling,
        max_total_examinations=max(1, int(workflow.get("max_total_examinations", 6))),
        max_main_loop_iterations=max_loop,
        max_llm_calls_per_patient=int(workflow.get("max_llm_calls_per_patient", 16)),
        final_llm_reserve_calls=max(1, int(workflow.get("final_llm_reserve_calls", 3))),
        max_patient_seconds=max_patient_seconds,
        special_case_max_patient_seconds=special_case_max_patient_seconds,
        llm_call_timeout_seconds=int(workflow.get("llm_call_timeout_seconds", 35)),
        final_llm_call_timeout_seconds=int(workflow.get("final_llm_call_timeout_seconds", 40)),
        service_call_timeout_seconds=int(workflow.get("service_call_timeout_seconds", 25)),
        evaluation_call_timeout_seconds=int(workflow.get("evaluation_call_timeout_seconds", 120)),
        force_diagnosis_buffer_seconds=force_diagnosis_buffer_seconds,
        consult_time_budget_seconds=consult_budget,
        examine_time_budget_seconds=examine_budget,
        diagnose_time_budget_seconds=diagnose_budget,
        min_differential_candidates=int(workflow.get("min_differential_candidates", 3)),
        min_objective_exam_results=int(workflow.get("min_objective_exam_results", 1)),
        use_llm_action_planner=bool(workflow.get("use_llm_action_planner", False)),
    )


class MyDoctorAgent(BasicAgent):
    """Baseline doctor agent with explicit, easy-to-read steps."""

    def __init__(self, config: Optional[Dict[str, Any]] = None, memory: Any = None):
        super().__init__(config=config, memory=memory)
        self.workflow_limits = load_workflow_limits(config)

        # 标准目录来自 data/ref_data。所有类别、科室、检查、疾病都尽量从这些标准名称中选择。
        self.examination_catalog = load_examination_catalog()
        self.disease_catalog = load_disease_catalog()
        self.exam_categories = list(self.examination_catalog.keys())
        self.all_examination_names = [
            name for names in self.examination_catalog.values() for name in names
        ]
        self.departments = list(self.disease_catalog.keys())
        self.exam_category_map = build_name_map(self.exam_categories)
        self.department_map = build_name_map(self.departments)
        self.disease_to_department = build_disease_department_map(self.disease_catalog)
        self.global_disease_map = build_global_disease_map(self.disease_catalog)
        self.exam_core_map = build_exam_core_map(self.all_examination_names)

    async def train(self, patient_id: str) -> Dict[str, Any]:
        return await self._run_agent(patient_id=patient_id, mode="train")

    async def test(self, patient_id: str) -> Dict[str, Any]:
        return await self._run_agent(patient_id=patient_id, mode="test")



    async def _run_differential(
        self,
        *,
        patient_id: str,
        memory_notes: List[Any],
        chat_history: List[Any],
        examinations: Dict[str, Any],
        case_profile: Dict[str, Any],
        budget: Optional[PatientCaseBudget] = None,
    ) -> List[Any]:
        """跑一次鉴别诊断并返回 differential 列表，供开检查/最终诊断复用。"""
        differential_prompt = format_prompt(
            DIFFERENTIAL_DIAGNOSIS_PROMPT,
            {
                "memory_notes": memory_notes,
                "chat_history": chat_history,
                "examinations": examinations,
                "case_profile": case_profile,
            },
        )
        differential_decision = await self._call_llm(
            prompt=differential_prompt,
            default={"differential": []},
            prompt_name="differential_diagnosis",
            patient_id=patient_id,
            budget=budget,
        )
        return differential_decision.get("differential") or []



    def _match_differential_disease(self, differential: List[Any]) -> str:
        all_diseases = []
        for diseases in self.disease_catalog.values():
            all_diseases.extend(diseases)

        disease_map = build_name_map(all_diseases)

        for item in differential:
            if not isinstance(item, dict):
                continue
            candidates = [
                item.get("suspected_disease"),
                item.get("diagnosis"),
                item.get("disease"),
            ]
            for candidate in candidates:
                disease = match_standard_or_contained_name(candidate, disease_map)
                if disease:
                    return disease

        return ""


    async def _build_case_profile(
        self,
        *,
        patient_id: str,
        chat_history: List[Any],
        examinations: Dict[str, Any],
        budget: Optional[PatientCaseBudget] = None,
    ) -> Dict[str, Any]:
        profile_prompt = format_prompt(
            CASE_PROFILE_PROMPT,
            {
                "chat_history": chat_history,
                "examinations": examinations,
            },
        )
        return await self._call_llm(
            prompt=profile_prompt,
            default=_empty_case_profile(),
            prompt_name="case_profile",
            patient_id=patient_id,
            budget=budget,
        )

    async def _run_agent(self, patient_id: str, mode: str) -> Dict[str, Any]:
        self._configure_service_timeouts()
        limits = self.workflow_limits
        budget = PatientCaseBudget(limits)
        memory_notes = self._load_memory_notes()

        case_state: Dict[str, Any] = {
            "patient_id": patient_id,
            "mode": mode,
            "memory_notes": memory_notes,
            "chat_history": [],
            "ordered_examinations": [],
            "invalid_examinations": [],
            "examination_results": {},
            "decision_trace": [],
            "exam_decision_trace": [],
            "exam_purposes": {},
            "exam_rounds": 0,
            "stage": "consult",
            "case_profile": None,
            "case_profile_fingerprint": "",
            "preliminary_differential": [],
            "last_successful_differential": [],
            "differential_fingerprint": "",
            "service_action_errors": [],
        }

        # 步骤 1：循环判断下一步动作。这里只决定“问诊 / 开检查 / 诊断”。
        while True:
            budget.next_loop()
            if budget.should_force_finalize(in_consultation=case_state.get("stage") == "consult"):
                break

            chat_history = case_state.get("chat_history", [])
            examinations = self._examination_context(case_state)
            # The structured profile summarizes history. Examination results are
            # passed separately to every downstream prompt, so they must not
            # invalidate and regenerate the profile after each exam batch.
            profile_fingerprint = case_context_fingerprint(chat_history, {})
            doctor_turns = sum(1 for m in case_state["chat_history"] if m.get("from") == "doctor")

            if not chat_history and case_state.get("case_profile") is None:
                # The first action is always the opening question; an empty-case
                # summarization call adds no clinical information.
                case_profile = _empty_case_profile()
                case_state["case_profile"] = case_profile
                case_state["case_profile_fingerprint"] = profile_fingerprint
                case_state["case_profile_turn"] = 0
            elif (
                case_state.get("case_profile") is not None
                and case_state.get("case_profile_fingerprint") == profile_fingerprint
            ):
                case_profile = case_state["case_profile"]
            elif (
                case_state.get("case_profile") is not None
                and case_state.get("case_profile_turn", 0) >= doctor_turns
                and case_state.get("stage") == "consult"
                and not budget.should_force_finalize(in_consultation=True)
            ):
                # Reuse existing profile during consultation to save LLM budget;
                # it will be refreshed when entering the diagnosis stage.
                case_profile = case_state["case_profile"]
            else:
                case_profile = await self._build_case_profile(
                    patient_id=patient_id,
                    chat_history=chat_history,
                    examinations=examinations,
                    budget=budget,
                )
                case_state["case_profile"] = case_profile
                case_state["case_profile_fingerprint"] = profile_fingerprint
                case_state["case_profile_turn"] = doctor_turns
                memory_notes = self._load_memory_notes(case_profile)
                case_state["memory_notes"] = memory_notes

            # Let the deterministic stage machine own the order of care.  The
            # model may refine a question/reason, but cannot jump a stage.
            # doctor_turns already calculated above. To keep each case close to
            # the 3-minute target, build the differential only when it can
            # directly drive the next action.
            early_differential_turns = max(
                limits.max_doctor_turns,
                limits.min_doctor_turns,
            )
            if (
                doctor_turns >= early_differential_turns
                and case_state.get("stage") != "consult"
                and not case_state.get("preliminary_differential")
                and budget.can_call_llm()
            ):
                preliminary = await self._run_differential(
                    patient_id=patient_id,
                    memory_notes=memory_notes,
                    chat_history=chat_history,
                    examinations=examinations,
                    case_profile=case_profile,
                    budget=budget,
                )
                _retain_successful_differential(
                    case_state,
                    preliminary,
                    case_context_fingerprint(chat_history, examinations),
                )
            consult_check = build_workflow_self_check(
                case_profile=case_profile,
                chat_history=chat_history,
                differential=case_state.get("preliminary_differential") or [],
                min_differential_candidates=2,
            )
            consult_incomplete = [item for item in consult_check.get("incomplete", []) if item.startswith("consultation.")]
            complex_case = _is_complex_case(
                case_profile,
                case_state.get("preliminary_differential") or [],
            )
            hard_consult_incomplete = consultation_hard_incomplete(
                consult_incomplete,
                complex_case=complex_case,
            )
            case_state["consultation_check"] = {
                "incomplete": consult_incomplete,
                "hard_incomplete": hard_consult_incomplete,
            }
            case_state["stage"] = advance_workflow_stage(
                case_state=case_state,
                case_profile=case_profile,
                chat_history=chat_history,
                limits=limits,
                exam_resolver=self._resolve_exam,
                consultation_check={"incomplete": consult_incomplete},
            ).value
            budget.record_stage(case_state["stage"])

            doctor_turns = sum(1 for m in case_state["chat_history"] if m.get("from") == "doctor")
            differential = case_state.get("preliminary_differential") or []
            max_consult_turns = effective_max_doctor_turns(
                case_profile, differential, limits=limits,
            )
            max_exam_rounds = effective_max_exam_rounds(
                case_profile, differential, limits=limits,
            )
            budget.set_special_case(
                _is_complex_case(case_profile, differential)
            )
            diagnostic_confidence = _assess_diagnostic_confidence(
                case_profile=case_profile,
                differential=differential,
                examinations=examinations,
            )
            case_state["diagnostic_confidence"] = diagnostic_confidence
            planned_action, planned_question, planned_reason = _plan_next_step(
                case_state=case_state,
                case_profile=case_profile,
                chat_history=chat_history,
                limits=limits,
                budget=budget,
                in_consultation=doctor_turns < max_consult_turns,
                exam_resolver=self._resolve_exam,
                max_consult_turns=max_consult_turns,
                max_exam_rounds=max_exam_rounds,
            )
            fallback_action = {
                "action": planned_action,
                "question": planned_question,
                "reason": planned_reason,
            }

            decision = fallback_action
            if limits.use_llm_action_planner and budget.can_call_llm() and not budget.should_force_finalize():
                action_prompt = format_prompt(
                    NEXT_ACTION_PROMPT,
                    {
                        "memory_notes": memory_notes,
                        "chat_history": chat_history,
                        "examinations": examinations,
                        "case_profile": case_profile,
                        "workflow_limits": {
                            "max_doctor_turns": limits.max_doctor_turns,
                            "max_exam_rounds": limits.max_exam_rounds,
                            "remaining_seconds": int(budget.remaining()),
                            "target_remaining_seconds": int(budget.target_remaining()),
                            "max_patient_minutes": limits.max_patient_seconds // 60,
                            "special_case": budget.special_case,
                            "special_case_max_patient_minutes": limits.special_case_max_patient_seconds // 60,
                            "use_llm_action_planner": limits.use_llm_action_planner,
                        },
                    },
                )
                llm_decision = await self._call_llm(
                    prompt=action_prompt,
                    default=fallback_action,
                    prompt_name="next_action",
                    patient_id=patient_id,
                    budget=budget,
                )
                llm_action = str(llm_decision.get("action", "")).strip().lower()
                if llm_action == planned_action:
                    decision = {
                        "action": llm_action,
                        "question": clean_text(llm_decision.get("question")),
                        "reason": clean_text(llm_decision.get("reason")) or planned_reason,
                    }

            action = str(decision.get("action", "")).strip().lower()
            if action not in {"ask_patient", "order_examination", "final_diagnosis"}:
                action = planned_action

            if (
                action == "final_diagnosis"
                and diagnostic_confidence.get("recommendation") == "continue_exam"
                and case_state.get("exam_rounds", 0) < max_exam_rounds
                and not budget.should_force_finalize(in_consultation=doctor_turns < max_consult_turns)
            ):
                action = "order_examination"
                decision = {
                    "action": action,
                    "question": "",
                    "reason": "诊断置信度评估提示仍缺客观证据，先补齐关键检查。",
                }
            elif (
                action == "order_examination"
                and diagnostic_confidence.get("recommendation") == "ready_diagnose"
                and _essential_exams_complete(
                    case_state,
                    case_profile,
                    differential=differential,
                    exam_resolver=self._resolve_exam,
                    limits=limits,
                )
            ):
                action = "final_diagnosis"
                decision = {
                    "action": action,
                    "question": "",
                    "reason": "诊断置信度与关键检查均已满足，提前进入综合诊断。",
                }

            loop_signature = (
                action,
                doctor_turns,
                int(case_state.get("exam_rounds", 0)),
                len(as_text_list(case_state.get("ordered_examinations"))),
                case_state.get("stage"),
            )
            if budget.note_loop_progress(loop_signature):
                if case_state.get("stage") == "consult":
                    action = "order_examination" if int(case_state.get("exam_rounds", 0)) < max_exam_rounds else "final_diagnosis"
                elif case_state.get("stage") == "examine":
                    action = "final_diagnosis"
                else:
                    action = "final_diagnosis"
                decision = {
                    "action": action,
                    "question": "",
                    "reason": "检测到流程停滞，强制推进到下一阶段以避免死循环。",
                }

            if (
                case_state.get("stage") == "consult"
                and action != "ask_patient"
                and doctor_turns < max_consult_turns
            ):
                # 时间紧张且已达最低轮次：只堵用药等硬安全缺口，其余放行进入检查。
                must_keep_asking = bool(hard_consult_incomplete)
                if budget.time_critical() and doctor_turns >= limits.min_doctor_turns:
                    must_keep_asking = _medication_history_incomplete(case_profile, chat_history)
                if must_keep_asking:
                    domain_question = _domain_specific_history_question(case_profile, chat_history)
                    if (
                        domain_question
                        and not budget.time_critical()
                        and not _question_already_asked(domain_question, case_state["chat_history"])
                    ):
                        action = "ask_patient"
                        decision = {
                            "action": action,
                            "question": domain_question,
                            "reason": "当前主诉需要先补齐特异性饮食、用药、过敏或职业背景。",
                        }
                    else:
                        gap_source = hard_consult_incomplete or consult_incomplete
                        action = "ask_patient"
                        decision = {
                            "action": action,
                            "question": _consultation_gap_question(gap_source, case_profile),
                            "reason": "问诊自检仍有关键缺口，先补齐病史四件事、危险鉴别或安全信息。",
                        }
                elif action not in {"order_examination", "final_diagnosis"}:
                    action = "order_examination"
                    decision = {
                        "action": action,
                        "question": "",
                        "reason": "问诊已达最低轮次且时间紧张，转入检查以控制总时长。",
                    }
            elif action == "final_diagnosis" and doctor_turns < limits.min_doctor_turns:
                action = "ask_patient"
                decision = {
                    "action": action,
                    "question": "请补充您的既往病史、目前正在使用的药物（含激素/免疫抑制剂）以及过敏史。",
                    "reason": "关键病史不足，先补充用药史和既往史。",
                }
            elif (
                action == "final_diagnosis"
                and doctor_turns < max_consult_turns
                and _medication_history_incomplete(case_profile, chat_history)
            ):
                action = "ask_patient"
                decision = {
                    "action": action,
                    "question": "请补充医生或家属是否在给孩子/您使用处方药，尤其是激素、免疫抑制剂或长期口服药物，并说明过敏史。",
                    "reason": "当前用药史不完整，需先明确激素/免疫抑制剂及处方药情况。",
                }
            elif (
                action == "final_diagnosis"
                and not case_state.get("ordered_examinations")
                and doctor_turns >= limits.min_doctor_turns
                and case_state.get("exam_rounds", 0) < max_exam_rounds
                and not budget.should_force_finalize(in_consultation=doctor_turns < max_consult_turns)
            ):
                action = "order_examination"
                decision = {
                    "action": action,
                    "question": "",
                    "reason": "尚未开具任何辅助检查，需先完成标准评估后再诊断。",
                }
            elif action == "final_diagnosis" and not _essential_exams_complete(
                case_state,
                case_profile,
                differential=case_state.get("preliminary_differential"),
                exam_resolver=self._resolve_exam,
                limits=limits,
            ):
                if case_state.get("exam_rounds", 0) < max_exam_rounds:
                    action = "order_examination"
                    decision = {
                        "action": action,
                        "question": "",
                        "reason": "关键检查尚未齐备，先补齐标准评估清单。",
                    }
            elif (
                doctor_turns >= max_consult_turns
                and action == "ask_patient"
            ):
                if (
                    not case_state.get("ordered_examinations")
                    and case_state.get("exam_rounds", 0) < max_exam_rounds
                    and not budget.should_force_finalize(in_consultation=doctor_turns < max_consult_turns)
                ):
                    action = "order_examination"
                    decision = {
                        "action": action,
                        "question": "",
                        "reason": "问诊轮次已满，转入小批量开具当前最关键的辅助检查。",
                    }
                else:
                    action = "final_diagnosis"
                    decision = {
                        "action": action,
                        "question": "",
                        "reason": "已达最大问诊轮次（%d），基于现有信息进入诊断。" % max_consult_turns,
                    }
            elif (
                action == "order_examination"
                and case_state.get("exam_rounds", 0) >= max_exam_rounds
            ):
                action = "final_diagnosis"
                decision = {
                    "action": action,
                    "question": "",
                    "reason": "已达最大开检查轮次（%d），基于现有信息进入诊断。" % max_exam_rounds,
                }

            question = clean_text(decision.get("question"))
            if action == "ask_patient" and case_state.get("stage") == "consult" and doctor_turns >= 1:
                gap_source = hard_consult_incomplete or consult_incomplete
                compressed_question = _consultation_gap_question(gap_source, case_profile)
                if compressed_question:
                    question = compressed_question
                    decision["reason"] = "压缩合并问诊缺口，减少追问轮次。"
            if action == "ask_patient" and not question:
                question = "请您描述这次最主要的不适、开始时间和伴随症状。"
            if action == "ask_patient" and _question_already_asked(question, case_state["chat_history"]):
                action = (
                    "order_examination"
                    if case_state.get("exam_rounds", 0) < max_exam_rounds
                    else "final_diagnosis"
                )
                question = ""
                decision["reason"] = "该问题已问过且已有患者回答，避免重复追问，转入下一步流程。"

            decision = {
                "action": action,
                "question": question if action == "ask_patient" else "",
                "reason": clean_text(decision.get("reason")),
            }
            case_state["decision_trace"].append(decision)

            # 步骤 2A：如果继续问诊，就把本轮问题发给患者，并保存问答历史。
            if action == "ask_patient":
                answer = await self._call_service_action(
                    action_name="ask_patient",
                    patient_id=patient_id,
                    awaitable=self.actions.ask_patient(
                        patient_id,
                        {
                            "question": decision["question"],
                            "chat_history": case_state["chat_history"],
                        },
                    ),
                    default="患者服务暂未返回补充回答。",
                    case_state=case_state,
                    budget=budget,
                    reserve_seconds=limits.force_diagnosis_buffer_seconds,
                )
                answer = clean_text(answer) or "患者服务暂未返回补充回答。"
                case_state["chat_history"].extend(
                    [
                        {"from": "doctor", "text": decision["question"]},
                        {"from": "patient", "text": answer},
                    ]
                )
                case_state["preliminary_differential"] = []
                case_state["differential_fingerprint"] = ""
                continue

            # 步骤 2B：如果开检查，先选检查类别，再从该类别里选具体标准检查名称。
            if action == "order_examination":
                chat_history = case_state.get("chat_history", [])
                examinations = self._examination_context(case_state)
                differential_fingerprint = case_context_fingerprint(chat_history, examinations)

                if (
                    case_state.get("preliminary_differential")
                    and case_state.get("differential_fingerprint") == differential_fingerprint
                ):
                    differential = case_state["preliminary_differential"]
                else:
                    refreshed_differential = await self._run_differential(
                        patient_id=patient_id,
                        memory_notes=memory_notes,
                        chat_history=chat_history,
                        examinations=examinations,
                        case_profile=case_profile,
                        budget=budget,
                    )
                    differential = _retain_successful_differential(
                        case_state,
                        refreshed_differential,
                        differential_fingerprint,
                    )
                    case_state["preliminary_differential"] = differential

                diagnostic_confidence = _assess_diagnostic_confidence(
                    case_profile=case_profile,
                    differential=differential,
                    examinations=self._examination_context(case_state),
                )
                case_state["diagnostic_confidence"] = diagnostic_confidence
                if (
                    diagnostic_confidence.get("recommendation") == "ready_diagnose"
                    and _essential_exams_complete(
                        case_state,
                        case_profile,
                        differential=differential,
                        exam_resolver=self._resolve_exam,
                        limits=limits,
                    )
                ):
                    case_state["stage"] = "diagnose"
                    break

                exam_need_summary = build_exam_need_summary(
                    case_profile=case_profile,
                    differential=differential,
                    examinations=examinations,
                    exam_resolver=self._resolve_exam,
                )
                case_state["exam_need_summary"] = exam_need_summary

                already_ordered = set(as_text_list(case_state["ordered_examinations"]))
                remaining_exam_slots = max(
                    0, limits.max_total_examinations - len(already_ordered)
                )
                if remaining_exam_slots <= 0:
                    break
                base_exam_batch_limit = min(
                    _exam_batch_limit(case_profile, differential), remaining_exam_slots
                )
                exam_batch_limit = _staged_exam_batch_limit(
                    case_state=case_state,
                    base_limit=base_exam_batch_limit,
                    remaining_exam_slots=remaining_exam_slots,
                )
                mapped_examinations, mapped_exam_reasons = _mapped_examination_recommendations(
                    case_profile=case_profile,
                    differential=differential,
                    ordered=already_ordered,
                    available_examinations=self.all_examination_names,
                    exam_resolver=self._resolve_exam,
                    disease_to_department=self.disease_to_department,
                    disease_map=self.global_disease_map,
                    chat_history=chat_history,
                )
                comprehensive_examinations = suggest_comprehensive_examinations(
                    case_profile=case_profile,
                    differential=differential,
                    exam_need_summary=exam_need_summary,
                    ordered=already_ordered,
                    available_examinations=self.all_examination_names,
                    examination_catalog=self.examination_catalog,
                    max_count=exam_batch_limit,
                    exam_resolver=self._resolve_exam,
                )
                if mapped_examinations:
                    comprehensive_examinations = unique_preserve_order(
                        mapped_examinations + comprehensive_examinations
                    )

                examinations_to_order: List[str] = []
                exam_reason = ""
                use_comprehensive_fast_path = bool(mapped_examinations or comprehensive_examinations)

                if mapped_examinations:
                    examinations_to_order = comprehensive_examinations[:exam_batch_limit]
                    exam_reason = "先按系统定位匹配标准检查，再补当前鉴别所需的关键客观证据。"
                elif use_comprehensive_fast_path:
                    examinations_to_order = comprehensive_examinations[:exam_batch_limit]
                    exam_reason = "按鉴别诊断与检查维度缺口小批量补齐当前最关键检查。"
                elif budget.can_call_llm():
                    category_prompt = format_prompt(
                        EXAM_CATEGORY_PROMPT,
                        {
                            "memory_notes": memory_notes,
                            "chat_history": chat_history,
                            "examinations": examinations,
                            "differential": differential,
                            "exam_categories": self.exam_categories,
                            "case_profile": case_profile,
                            "exam_need_summary": exam_need_summary,
                        },
                    )
                    category_decision = await self._call_llm(
                        prompt=category_prompt,
                        default={"category": self.exam_categories[0] if self.exam_categories else "", "reason": ""},
                        prompt_name="exam_category",
                        patient_id=patient_id,
                        budget=budget,
                    )
                    category = match_standard_name(category_decision.get("category"), self.exam_category_map)
                    if not category:
                        category = self.exam_categories[0] if self.exam_categories else ""
                        for candidate, names in self.examination_catalog.items():
                            if any(name not in case_state["ordered_examinations"] for name in names):
                                category = candidate
                                break

                    item_prompt = format_prompt(
                        EXAM_ITEM_PROMPT,
                        {
                            "memory_notes": memory_notes,
                            "chat_history": chat_history,
                            "examinations": examinations,
                            "differential": differential,
                            "category": category,
                            "exam_items": self.examination_catalog.get(category, []),
                            "case_profile": case_profile,
                            "exam_need_summary": exam_need_summary,
                        },
                    )
                    item_decision = await self._call_llm(
                        prompt=item_prompt,
                        default={"examinations": [], "reason": category_decision.get("reason", "")},
                        prompt_name="exam_item",
                        patient_id=patient_id,
                        budget=budget,
                    )
                    allowed_exam_map = build_name_map(self.examination_catalog.get(category, []))
                    examinations_to_order = []
                    for item in as_text_list(item_decision.get("examinations")):
                        standard_name = match_standard_name(item, allowed_exam_map)
                        if not standard_name or standard_name in already_ordered or standard_name in examinations_to_order:
                            continue
                        examinations_to_order.append(standard_name)
                    if comprehensive_examinations:
                        examinations_to_order = unique_preserve_order(
                            comprehensive_examinations + examinations_to_order
                        )[:exam_batch_limit]
                    exam_reason = clean_text(item_decision.get("reason") or category_decision.get("reason"))
                elif comprehensive_examinations:
                    examinations_to_order = comprehensive_examinations[:3]
                    exam_reason = "LLM 预算不足，使用鉴别诊断推荐检查补齐剩余关键项。"

                examinations_to_order = [
                    name for name in examinations_to_order if name not in already_ordered
                ]
                examinations_to_order = filter_examinations_by_current_evidence(
                    examinations_to_order,
                    case_profile=case_profile,
                    differential=differential,
                    already_ordered=already_ordered,
                )
                examinations_to_order = prioritize_examinations(
                    examinations_to_order,
                    case_profile=case_profile,
                    differential=differential,
                    exam_need_summary=exam_need_summary,
                )[:exam_batch_limit]
                if not examinations_to_order:
                    examinations_to_order = _fallback_examinations(
                        case_profile=case_profile,
                        differential=differential,
                        exam_need_summary=exam_need_summary,
                        ordered=already_ordered,
                        available_examinations=self.all_examination_names,
                        examination_catalog=self.examination_catalog,
                        exam_resolver=self._resolve_exam,
                    )
                    if examinations_to_order:
                        exam_reason = exam_reason or "按检查维度缺口补齐最低限度评估。"
                    examinations_to_order = filter_examinations_by_current_evidence(
                        examinations_to_order,
                        case_profile=case_profile,
                        differential=differential,
                        already_ordered=already_ordered,
                    )
                    examinations_to_order = prioritize_examinations(
                        examinations_to_order,
                        case_profile=case_profile,
                        differential=differential,
                        exam_need_summary=exam_need_summary,
                    )[:exam_batch_limit]

                exam_justifications = _build_exam_order_justifications(
                    examinations=examinations_to_order,
                    case_profile=case_profile,
                    differential=differential,
                    mapped_reasons=mapped_exam_reasons,
                    llm_reason=exam_reason,
                    exam_resolver=self._resolve_exam,
                )
                examinations_to_order = _prioritize_exams_by_reason_strength(
                    examinations_to_order,
                    exam_justifications,
                )[:exam_batch_limit]

                exam_plan = {
                    "category": "mapped_standard" if mapped_examinations else ("comprehensive" if use_comprehensive_fast_path else "llm_selected"),
                    "examinations": examinations_to_order,
                    "reason": _exam_order_reason_text(exam_justifications, examinations_to_order),
                }
                case_state["exam_purposes"].update(
                    build_exam_purpose_map(
                        differential,
                        examinations_to_order,
                        exam_resolver=self._resolve_exam,
                    )
                )
                decision_records = build_exam_decision_records(
                    differential,
                    examinations_to_order,
                    exam_resolver=self._resolve_exam,
                )
                for record in decision_records:
                    justification = exam_justifications.get(record.get("examination") or "", {})
                    record.update(
                        {
                            "category": exam_plan["category"],
                            "reason": justification.get("reason") or exam_reason,
                            "priority": justification.get("priority") or "LOW",
                        }
                    )
                case_state["exam_decision_trace"].extend(decision_records)
                if not examinations_to_order:
                    break

                exam_response = await self._call_service_action(
                    action_name="order_examination",
                    patient_id=patient_id,
                    awaitable=self.actions.order_examination(
                        patient_id,
                        examinations_to_order,
                        reason=exam_plan.get("reason", ""),
                    ),
                    default=self._fallback_exam_response(examinations_to_order),
                    case_state=case_state,
                    budget=budget,
                    reserve_seconds=limits.force_diagnosis_buffer_seconds,
                )
                if not isinstance(exam_response, dict):
                    exam_response = self._fallback_exam_response(examinations_to_order)
                service_failed = bool(exam_response.get("service_failed"))
                # `order_examination` can time out after the scheduling event was
                # accepted but before results arrive.  Keep the scheduled items
                # in state so the planner does not repeatedly open the same
                # order and the final submission still reflects the clinical
                # checks that were ordered.
                resolved_ordered = resolve_ordered_examination_items(
                    exam_response, examinations_to_order
                )
                if service_failed:
                    resolved_ordered = examinations_to_order
                case_state["ordered_examinations"] = unique_preserve_order(
                    case_state["ordered_examinations"] + resolved_ordered
                )
                case_state["invalid_examinations"].extend(
                    as_text_list(exam_response.get("invalid_items"))
                )
                results = exam_response.get("results") or {}
                if isinstance(results, dict):
                    case_state["examination_results"].update(results)
                case_state["exam_rounds"] = case_state.get("exam_rounds", 0) + 1
                # Keep the last successful differential as a timeout fallback;
                # the empty current value forces a refresh against new results.
                case_state["preliminary_differential"] = []
                case_state["differential_fingerprint"] = ""

                if _essential_exams_complete(
                    case_state,
                    case_profile,
                    differential=case_state.get("preliminary_differential"),
                    exam_resolver=self._resolve_exam,
                    limits=limits,
                ):
                    case_state["stage"] = "diagnose"
                    break
                continue

            break

        # 步骤 3：进入诊断。先做鉴别诊断，再据此选科室、选病并生成治疗方案。
        chat_history = case_state.get("chat_history", [])
        examinations = self._examination_context(case_state)

        final_profile_fingerprint = case_context_fingerprint(chat_history, {})
        final_fingerprint = case_context_fingerprint(chat_history, examinations)
        if (
            case_state.get("case_profile") is not None
            and case_state.get("case_profile_fingerprint") == final_profile_fingerprint
        ):
            case_profile = case_state["case_profile"]
        elif budget.can_call_llm():
            case_profile = await self._build_case_profile(
                patient_id=patient_id,
                chat_history=chat_history,
                examinations=examinations,
                budget=budget,
            )
            case_state["case_profile_fingerprint"] = final_profile_fingerprint
        else:
            case_profile = case_state.get("case_profile") or _empty_case_profile()
        case_state["case_profile"] = case_profile
        memory_notes = self._load_memory_notes(case_profile, focus="treatment")
        case_state["memory_notes"] = memory_notes

        # 诊断步骤 0：不限科室先做鉴别诊断，作为后续科室/疾病选择的核心线索。
        # Results obtained during the examination stage can invalidate the
        # preliminary differential.  Always refresh it before final diagnosis.
        if (
            case_state.get("preliminary_differential")
            and case_state.get("differential_fingerprint") == final_fingerprint
        ):
            differential = case_state["preliminary_differential"]
        elif budget.can_call_llm():
            refreshed_differential = await self._run_differential(
                patient_id=patient_id,
                memory_notes=memory_notes,
                chat_history=chat_history,
                examinations=examinations,
                case_profile=case_profile,
                budget=budget,
            )
            differential = _retain_successful_differential(
                case_state,
                refreshed_differential,
                final_fingerprint,
            )
        else:
            differential = (
                case_state.get("preliminary_differential")
                or case_state.get("last_successful_differential")
                or []
            )
        case_state["preliminary_differential"] = differential
        case_state["differential"] = differential


        matched_disease = self._match_differential_disease(differential)
        inferred_department = _infer_department_from_differential(
            differential,
            self.disease_to_department,
            self.global_disease_map,
        )
        department_decision = {"department": "", "reason": ""}
        department = inferred_department
        # 诊断步骤 1：优先由鉴别诊断中的标准病名直接定位科室；只有无法定位时
        # 才额外请求 LLM，减少每例固定调用并降低 /test 超时风险。
        if not department and matched_disease:
            department = self.disease_to_department.get(normalize_name(matched_disease), "")
        if not department and budget.can_call_llm():
            department_prompt = format_prompt(
                DEPARTMENT_PROMPT,
                {
                    "memory_notes": memory_notes,
                    "chat_history": chat_history,
                    "examinations": examinations,
                    "differential": differential,
                    "departments": self.departments,
                    "case_profile": case_profile,
                },
            )
            department_decision = await self._call_llm(
                prompt=department_prompt,
                default={"department": self.departments[0] if self.departments else "", "reason": ""},
                prompt_name="department",
                patient_id=patient_id,
                budget=budget,
            )
            department = match_standard_name(department_decision.get("department"), self.department_map)
        if inferred_department:
            department = inferred_department
        elif not department:
            department = self.departments[0] if self.departments else ""

        # 诊断步骤 2：综合诊断候选来自鉴别诊断前列 + 科室目录。
        diseases = self.disease_catalog.get(department, [])
        evidence_candidates = _diseases_from_case_evidence(
            case_profile,
            examinations,
            self.global_disease_map,
        )
        disease_candidates = unique_preserve_order(
            evidence_candidates
            + _diseases_from_differential(differential, self.global_disease_map)
        )
        diseases_for_prompt = unique_preserve_order(disease_candidates + diseases)[:60]

        disease_prompt = format_prompt(
            DISEASE_AND_TREATMENT_PROMPT,
            {
                "memory_notes": memory_notes,
                "chat_history": chat_history,
                "examinations": examinations,
                "differential": differential,
                "department": department,
                "diseases": diseases_for_prompt,
                "case_profile": case_profile,
            },
        )

        # The ranked differential owns the primary diagnosis. Text extraction is
        # only a fallback because incidental exam wording may mention other diseases.
        default_diagnosis = _select_default_diagnosis(
            matched_disease=matched_disease,
            evidence_candidates=evidence_candidates,
            differential=differential,
            disease_map=self.global_disease_map,
        )
        if default_diagnosis != "未明确诊断":
            default_diagnosis = (
                match_standard_or_contained_name(default_diagnosis, self.global_disease_map)
                or default_diagnosis
            )

        final_plan = await self._call_llm(
            prompt=disease_prompt,
            default={
                "diagnosis": [default_diagnosis] if default_diagnosis != "未明确诊断" else [],
                "treatment_plan": "基于现有问诊和检查结果，继续完善评估并制定个体化治疗方案。",
                "reasoning": "LLM 未返回可解析的最终方案，使用保守兜底结果。",
                "reasoning_steps": [],
                "competitive_diagnoses": [],
                "safety_net": {"reassessment": "待补充", "red_flags": []},
            },
            prompt_name="disease_and_treatment",
            patient_id=patient_id,
            budget=budget,
            use_final_reserve=True,
        )

        def _enforce_evidence_based_diagnosis(plan: Dict[str, Any], default_diagnosis: str) -> Dict[str, Any]:
            """Reconcile working diagnosis and strip deferral treatment when evidence supports action."""
            return reconcile_diagnosis_before_treatment(
                plan,
                differential=differential,
                default_diagnosis=default_diagnosis,
                disease_map=self.global_disease_map,
                case_profile=case_profile,
                examinations=examinations,
            )

        final_plan = _enforce_evidence_based_diagnosis(final_plan, default_diagnosis)

        checklist = final_plan.get("safety_checklist") or {}
        unexplained = final_plan.get("unexplained_findings") or []
        fix_prompt = format_prompt(FINAL_SELF_CHECK_PROMPT, {
            "case_profile": case_profile,
            "memory_notes": memory_notes,
            "examinations": examinations,
            "differential": differential,
            "current_plan": final_plan,
            "unexplained_findings": unexplained,
            "safety_checklist": checklist,
        })
        if budget.can_call_llm() and budget.remaining() > limits.force_diagnosis_buffer_seconds + 25:
            reviewed_plan = await self._call_llm(
                prompt=fix_prompt,
                default=final_plan,
                prompt_name="final_self_check",
                patient_id=patient_id,
                budget=budget,
            )
            if isinstance(reviewed_plan, dict):
                final_plan = {**final_plan, **reviewed_plan}

        pre_submit_check = build_workflow_self_check(
            case_profile=case_profile,
            chat_history=chat_history,
            differential=differential,
            examinations={**examinations, "exam_decision_trace": case_state.get("exam_decision_trace", [])},
            final_plan=final_plan,
        )
        critical_gaps = [
            item for item in pre_submit_check.get("incomplete", [])
            if item.startswith("diagnosis.") or item.startswith("treatment.")
        ]
        if (
            critical_gaps
            and budget.can_call_llm()
            and budget.remaining() > limits.force_diagnosis_buffer_seconds + 20
        ):
            repair_prompt = format_prompt(FINAL_SELF_CHECK_PROMPT, {
                "case_profile": case_profile,
                "memory_notes": memory_notes,
                "examinations": examinations,
                "differential": differential,
                "current_plan": {**final_plan, "incomplete_checklist_items": critical_gaps},
                "unexplained_findings": final_plan.get("unexplained_findings") or [],
                "safety_checklist": final_plan.get("safety_checklist") or {},
            })
            repaired_plan = await self._call_llm(
                prompt=repair_prompt,
                default=final_plan,
                prompt_name="final_checklist_repair",
                patient_id=patient_id,
                budget=budget,
            )
            if isinstance(repaired_plan, dict):
                final_plan = {**final_plan, **repaired_plan}

        final_plan = _enforce_evidence_based_diagnosis(final_plan, default_diagnosis)

        raw_diagnosis_input = final_plan.get("diagnosis")
        evidence_matrix_input = final_plan.get("evidence_matrix") or []
        print(
            "[diagnosis_normalize] patient_id=%s | raw_diagnosis=%s | matched_disease=%s"
            % (patient_id, raw_diagnosis_input, matched_disease)
        )
        print(
            "[diagnosis_normalize] patient_id=%s | evidence_matrix=%s"
            % (
                patient_id,
                [
                    {
                        "problem": item.get("problem") if isinstance(item, dict) else item,
                        "conclusion": item.get("conclusion") if isinstance(item, dict) else None,
                    }
                    for item in evidence_matrix_input
                ],
            )
        )
        diagnoses, demoted_to_pending = _normalize_final_diagnoses(
            raw_diagnosis=raw_diagnosis_input,
            disease_map=self.global_disease_map,
            default_diagnosis=default_diagnosis,
            reasoning=clean_text(final_plan.get("reasoning")),
            differential=differential,
            matched_disease=matched_disease,
            case_profile=case_profile,
            examinations=examinations,
            evidence_matrix=evidence_matrix_input,
        )
        print(
            "[diagnosis_normalize] patient_id=%s | final_diagnoses=%s | demoted_to_pending=%s"
            % (patient_id, diagnoses, demoted_to_pending)
        )
        final_plan["diagnosis"] = diagnoses
        # Pathophysiology states / generic categories demoted from the primary
        # slot are preserved as pending problems so treatment can still reference
        # them without inflating the diagnosis list (which the evaluator
        # penalizes).
        if demoted_to_pending:
            existing_pending = list(final_plan.get("pending_problems") or [])
            for item in demoted_to_pending:
                if item and item not in existing_pending:
                    existing_pending.append(item)
            final_plan["pending_problems"] = existing_pending
        diagnosis = diagnoses[0] if diagnoses else "未明确诊断"

        final_plan = await self._enforce_treatment_safety_and_core_drugs(
            final_plan,
            ground_truth=None,
            case_profile=case_profile,
            examinations=examinations,
            differential=differential,
            memory_notes=memory_notes,
            budget=budget,
            patient_id=patient_id,
        )

        primary_department = self.disease_to_department.get(normalize_name(diagnosis))
        if primary_department:
            department = primary_department

        treatment_plan = clean_text(final_plan.get("treatment_plan"))
        if not treatment_plan:
            treatment_plan = "当前信息不足以制定特异性治疗方案；建议补充关键病史、体格检查和必要辅助检查后再决策。"
        treatment_plan = align_treatment_plan_with_mechanism(
            diagnoses=diagnoses,
            treatment_plan=treatment_plan,
            case_profile=case_profile,
            examinations=examinations,
        )
        reasoning = clean_text(final_plan.get("reasoning"))
        if not reasoning:
            reasoning = clean_text(department_decision.get("reason")) or "基于问诊和检查结果形成诊疗方案。"

        final_plan = {
            "department": department,
            "diagnosis": diagnoses,
            "treatment_plan": treatment_plan,
            "reasoning": reasoning,
            "evidence_matrix": final_plan.get("evidence_matrix") or [],
            "pending_problems": final_plan.get("pending_problems") or [],
            "key_findings": final_plan.get("key_findings") or [],
            "unexplained_findings": final_plan.get("unexplained_findings") or [],
            "reasoning_steps": final_plan.get("reasoning_steps") or [],
            "diagnostic_pause": final_plan.get("diagnostic_pause") or {},
            "pre_treatment_safety_pause": final_plan.get("pre_treatment_safety_pause") or {},
            "competitive_diagnoses": final_plan.get("competitive_diagnoses") or [],
            "shared_decision": clean_text(final_plan.get("shared_decision")),
            "medication_safety_review": clean_text(final_plan.get("medication_safety_review")),
            "multidisciplinary_review": clean_text(final_plan.get("multidisciplinary_review")),
            "safety_net": final_plan.get("safety_net") or {},
            "safety_checklist": final_plan.get("safety_checklist") or {},
            "treatment_safety_corrections": final_plan.get("treatment_safety_corrections") or [],
        }

        # 提交前最后一道硬门禁：机制对齐可能修改治疗文本，因此必须在所有
        # 方案变换完成后再次执行安全规则，并仅提交校验后的字段。
        final_plan = await self._enforce_treatment_safety_and_core_drugs(
            final_plan,
            ground_truth=None,
            case_profile=case_profile,
            examinations=examinations,
            differential=differential,
            memory_notes=memory_notes,
            budget=budget,
            patient_id=patient_id,
        )
        # 安全层只负责治疗修正，不能覆盖已经标准化的最终诊断。
        final_plan["diagnosis"] = diagnoses
        final_plan = _pre_prescription_safety_hook(
            final_plan,
            case_profile=case_profile,
            examinations=examinations,
        )
        treatment_plan = clean_text(final_plan.get("treatment_plan"))
        reasoning = clean_text(final_plan.get("reasoning"))

        final_plan["self_check"] = build_workflow_self_check(
            case_profile=case_profile,
            chat_history=chat_history,
            differential=differential,
            examinations={**examinations, "exam_decision_trace": case_state.get("exam_decision_trace", [])},
            final_plan=final_plan,
        )
        case_state["final_plan"] = final_plan

        final_result = await self._call_service_action(
            action_name="prescribe_treatment",
            patient_id=patient_id,
            awaitable=self.actions.prescribe_treatment(
                patient_id=patient_id,
                diagnosis=diagnoses,
                treatment_plan=treatment_plan,
                reasoning=reasoning,
            ),
            default={
                "patient_id": patient_id,
                "diagnosis": diagnoses,
                "treatment_plan": treatment_plan,
                "reasoning": reasoning,
            },
            case_state=case_state,
            budget=budget,
        )
        if not isinstance(final_result, dict):
            final_result = {}
        final_result["patient_id"] = patient_id
        final_result["diagnosis"] = diagnoses
        final_result["treatment_plan"] = treatment_plan
        final_result["reasoning"] = reasoning
        final_result["ordered_examinations"] = unique_preserve_order(
            as_text_list(final_result.get("ordered_examinations"))
            + as_text_list(case_state.get("ordered_examinations"))
        )
        final_result["conversation_rounds"] = sum(
            1
            for message in case_state.get("chat_history", [])
            if isinstance(message, dict) and message.get("from") == "doctor"
        )
        final_result["process_started_at"] = budget.started_at_wallclock
        final_result["process_duration_seconds"] = round(budget.elapsed(), 3)
        final_result["llm_calls"] = budget.llm_calls
        final_result["llm_calls_by_prompt"] = dict(budget.llm_calls_by_prompt)
        final_result["finished"] = True
        if self.logger is not None:
            self.logger.write_event(
                event_type="CASE_METRICS",
                agent_id=getattr(self.context, "config", None).team_id
                if getattr(getattr(self, "context", None), "config", None) is not None
                else "doctor",
                patient_id=patient_id,
                payload={
                    "patient_id": patient_id,
                    "process_started_at": final_result["process_started_at"],
                    "process_duration_seconds": final_result["process_duration_seconds"],
                    "llm_calls": final_result["llm_calls"],
                    "llm_calls_by_prompt": final_result["llm_calls_by_prompt"],
                },
            )

        # 步骤 4：训练模式下先评估，再基于评估做一次反思，最后把反思写入 memory。
        evaluation_report = None
        evaluation_reflection = None
        if mode == "train":
            evaluation_report = await self._call_service_action(
                action_name="evaluation",
                patient_id=patient_id,
                awaitable=self.actions.evaluation(
                    patient_id=patient_id,
                    final_result=final_result,
                ),
                default={},
                case_state=case_state,
                timeout_seconds=limits.evaluation_call_timeout_seconds,
            )
            if not isinstance(evaluation_report, dict):
                evaluation_report = {}
            case_state["evaluation_report"] = evaluation_report

            reflection_prompt = format_prompt(
                EVALUATION_REFLECTION_PROMPT,
                {
                    "chat_history": case_state.get("chat_history", []),
                    "evaluation_details": self._evaluation_details(evaluation_report or {}),
                },
            )
            evaluation_reflection = await self._call_llm(
                prompt=reflection_prompt,
                default={"reflection": {"profile": "", "future_strategy": ""}},
                prompt_name="evaluation_reflection",
                patient_id=patient_id,
                budget=budget,
            )
            case_state["evaluation_reflection"] = evaluation_reflection

        if mode == "train" and self.memory:
            self.memory.append_case_reflection(
                patient_id=patient_id,
                evaluation_reflection=evaluation_reflection,
                case_profile=case_state.get("case_profile"),
            )

        return final_result


    def _load_memory_notes(
        self,
        case_profile: Optional[Dict[str, Any]] = None,
        *,
        focus: Optional[str] = None,
    ) -> List[Any]:
        if not self.memory or not hasattr(self.memory, "load_notes"):
            return []
        try:
            return self.memory.load_notes(case_profile=case_profile, focus=focus)
        except TypeError:
            try:
                return self.memory.load_notes(case_profile=case_profile)
            except TypeError:
                return self.memory.load_notes()

    async def _enforce_treatment_safety_and_core_drugs(
        self,
        plan: Dict[str, Any],
        ground_truth: Optional[Dict[str, Any]],
        case_profile: Dict[str, Any],
        *,
        examinations: Dict[str, Any],
        differential: List[Any],
        memory_notes: List[Any],
        budget: Optional[PatientCaseBudget] = None,
        patient_id: str = "",
    ) -> Dict[str, Any]:
        """禁忌症与核心药物强制检查：LLM 修正（可选）+ 规则层兜底。"""
        forbidden_drugs = build_contraindicated_drugs(
            case_profile,
            examinations,
            ground_truth=ground_truth,
        )
        working = dict(plan)
        treatment_text = clean_text(working.get("treatment_plan"))
        vague = not treatment_text or any(
            marker in treatment_text
            for marker in (
                "继续完善评估",
                "个体化治疗方案",
                "基于现有问诊和检查结果",
                "因诊断未明",
            )
        )
        if vague and budget is not None and budget.can_call_llm():
            safety_prompt = format_prompt(
                TREATMENT_SAFETY_CORE_CHECK_PROMPT,
                {
                    "case_profile": case_profile,
                    "memory_notes": memory_notes,
                    "differential": differential,
                    "diagnosis": working.get("diagnosis") or [],
                    "treatment_plan": treatment_text or "（空）",
                    "forbidden_drugs": forbidden_drugs,
                },
            )
            patched = await self._call_llm(
                prompt=safety_prompt,
                default=working,
                prompt_name="treatment_safety_core_check",
                patient_id=patient_id,
                budget=budget,
            )
            if isinstance(patched, dict):
                working = {**working, **patched}

        return enforce_treatment_safety_and_core_drugs(
            working,
            case_profile=case_profile,
            examinations=examinations,
            differential=differential,
            disease_map=self.global_disease_map,
            ground_truth=ground_truth,
        )

    def _resolve_exam(self, name: Any) -> str:
        return resolve_exam_name(name, self.exam_core_map, self.all_examination_names)

    def _configure_service_timeouts(self) -> None:
        """Keep SDK HTTP waits aligned with this agent's per-case budget."""
        if self.clients is None:
            return
        client_timeouts = {
            "dataset_client": self.workflow_limits.service_call_timeout_seconds,
            "patient_client": self.workflow_limits.service_call_timeout_seconds,
            "exam_client": self.workflow_limits.service_call_timeout_seconds,
            "evaluate_client": self.workflow_limits.evaluation_call_timeout_seconds,
        }
        for attr, timeout_seconds in client_timeouts.items():
            client = getattr(self.clients, attr, None)
            http = getattr(client, "http", None)
            if http is not None and hasattr(http, "timeout_seconds"):
                http.timeout_seconds = int(max(1, timeout_seconds))

    async def _call_service_action(
        self,
        *,
        action_name: str,
        patient_id: str,
        awaitable: Any,
        default: Any,
        case_state: Dict[str, Any],
        timeout_seconds: Optional[int] = None,
        budget: Optional[PatientCaseBudget] = None,
        reserve_seconds: int = 0,
    ) -> Any:
        timeout = int(timeout_seconds or self.workflow_limits.service_call_timeout_seconds)
        if budget is not None:
            available = int(budget.remaining()) - max(0, int(reserve_seconds)) - 2
            timeout = min(timeout, max(1, available))
        try:
            return await asyncio.wait_for(awaitable, timeout=timeout)
        except Exception as exc:
            case_state.setdefault("service_action_errors", []).append(
                {
                    "action": action_name,
                    "patient_id": patient_id,
                    "error_type": type(exc).__name__,
                    "error": clean_text(exc),
                }
            )
            return default

    @staticmethod
    def _fallback_exam_response(examinations_to_order: List[str]) -> Dict[str, Any]:
        return {
            "service_failed": True,
            "results": {
                name: {
                    "result": "检查服务暂未返回结果。",
                    "status": "unavailable",
                    "abnormal_indicators": [],
                }
                for name in examinations_to_order
            }
        }

    async def _call_llm(
        self,
        *,
        prompt: str,
        default: Dict[str, Any],
        prompt_name: str = "",
        patient_id: str = "",
        budget: Optional[PatientCaseBudget] = None,
        use_final_reserve: bool = False,
    ) -> Dict[str, Any]:
        if budget is not None and not budget.can_call_llm(use_final_reserve=use_final_reserve):
            self._write_prompt_log(
                prompt_name=prompt_name,
                patient_id=patient_id,
                system_prompt=DOCTOR_SYSTEM_PROMPT,
                user_prompt=prompt,
                response="[LLM_SKIPPED] call or time budget unavailable",
            )
            return self._llm_failure_default(default, "调用预算不足，未执行LLM请求")

        timeout_seconds = (
            self.workflow_limits.final_llm_call_timeout_seconds
            if use_final_reserve
            else self.workflow_limits.llm_call_timeout_seconds
        )
        if budget is not None:
            timeout_seconds = min(timeout_seconds, max(1, int(budget.remaining()) - 5))
        try:
            response = await asyncio.wait_for(
                self.llm.call(prompt, system_prompt=DOCTOR_SYSTEM_PROMPT, temperature=0.2),
                timeout=timeout_seconds,
            )
        except Exception as exc:
            failure = "%s: %s" % (type(exc).__name__, clean_text(exc) or "request failed")
            self._write_prompt_log(
                prompt_name=prompt_name,
                patient_id=patient_id,
                system_prompt=DOCTOR_SYSTEM_PROMPT,
                user_prompt=prompt,
                response="[LLM_CALL_FAILED] %s" % failure,
            )
            return self._llm_failure_default(default, failure)
        finally:
            if budget is not None:
                budget.record_llm_call(prompt_name)

        parsed = parse_json_object(response)
        if parsed is not None:
            self._write_prompt_log(
                prompt_name=prompt_name,
                patient_id=patient_id,
                system_prompt=DOCTOR_SYSTEM_PROMPT,
                user_prompt=prompt,
                response=response,
            )
            return parsed

        if budget is not None and not budget.can_call_llm(use_final_reserve=use_final_reserve):
            self._write_prompt_log(
                prompt_name=prompt_name,
                patient_id=patient_id,
                system_prompt=DOCTOR_SYSTEM_PROMPT,
                user_prompt=prompt,
                response=response + "\n\n[JSON_REPAIR_SKIPPED] call budget unavailable",
            )
            return self._llm_failure_default(default, "响应无法解析且JSON修复预算不足")

        repair_prompt = "请修复以下内容为合法 JSON 对象：\n\n%s" % response
        repair_timeout_seconds = self.workflow_limits.llm_call_timeout_seconds
        if budget is not None:
            repair_timeout_seconds = min(
                repair_timeout_seconds,
                max(1, int(budget.remaining()) - 5),
            )
        try:
            repaired = await asyncio.wait_for(
                self.llm.call(repair_prompt, system_prompt=JSON_REPAIR_SYSTEM_PROMPT, temperature=0),
                timeout=repair_timeout_seconds,
            )
        except Exception as exc:
            failure = "JSON repair %s: %s" % (type(exc).__name__, clean_text(exc) or "request failed")
            self._write_prompt_log(
                prompt_name=prompt_name,
                patient_id=patient_id,
                system_prompt=DOCTOR_SYSTEM_PROMPT,
                user_prompt=prompt,
                response=response + "\n\n[JSON_REPAIR_FAILED] " + failure,
            )
            return self._llm_failure_default(default, failure)
        finally:
            if budget is not None:
                budget.record_llm_call("%s:json_repair" % prompt_name if prompt_name else "json_repair")

        parsed = parse_json_object(repaired)
        result = (
            parsed
            if parsed is not None
            else self._llm_failure_default(default, "JSON修复后仍无法解析")
        )
        self._write_prompt_log(
            prompt_name=prompt_name,
            patient_id=patient_id,
            system_prompt=DOCTOR_SYSTEM_PROMPT,
            user_prompt=prompt,
            response=response + "\n\n[JSON_REPAIRED_RESPONSE]\n" + clean_text(repaired),
        )
        return result

    @staticmethod
    def _llm_failure_default(default: Dict[str, Any], failure: str) -> Dict[str, Any]:
        result = dict(default)
        result["_llm_failure_reason"] = failure
        reasoning = clean_text(result.get("reasoning"))
        if reasoning.startswith("LLM 未返回可解析的最终方案"):
            result["reasoning"] = "最终诊疗LLM调用失败（%s），使用证据排序兜底结果。" % failure
        return result

    def _write_prompt_log(
        self,
        *,
        prompt_name: str,
        patient_id: str,
        system_prompt: str,
        user_prompt: str,
        response: str,
    ) -> None:
        if not bool(self.config.get("log_llm_prompts", False)):
            return
        if self.logger is None:
            return
        output_dir = getattr(self.logger, "output_dir", None)
        if output_dir is None:
            return
        prompt_dir = Path(output_dir) / "llm_prompts"
        prompt_dir.mkdir(parents=True, exist_ok=True)
        filename = "%s_%s.txt" % (prompt_name, patient_id)
        path = prompt_dir / filename
        content = "\n".join(
            [
                "timestamp: %s" % datetime.now(timezone.utc).astimezone().isoformat(),
                "prompt_name: %s" % prompt_name,
                "patient_id: %s" % patient_id,
                "",
                "system_prompt:",
                system_prompt,
                "",
                "user_prompt:",
                user_prompt,
                "",
                "response:",
                response,
                "",
                "=" * 80,
                "",
            ]
        )
        with path.open("a", encoding="utf-8") as file:
            file.write(content)

    def _examination_context(self, case_state):
        ordered = unique_preserve_order(case_state.get("ordered_examinations", []))
        raw = case_state.get("examination_results", {}) or {}
        results = []
        for name in ordered:
            value = raw.get(name)
            if value is None:
                continue
            results.append({"检查": name, "结果": value})
        return {"ordered_examinations": ordered, "examination_results": results}

    def _evaluation_details(self, evaluation_report: Dict[str, Any]) -> Dict[str, Any]:
        exam_detail = evaluation_report.get("examinationDetail", {}) or {}
        ordered = as_text_list(exam_detail.get("ordered"))
        expected = as_text_list(exam_detail.get("expected"))
        matched = as_text_list(exam_detail.get("matched"))
        matched_set = {normalize_name(name) for name in matched}
        # 多开：开了但没命中期望集，会拉低 examination_precision。
        redundant = [name for name in ordered if normalize_name(name) not in matched_set]
        # 漏开：期望集里有但没命中，会拉低 examination_coverage。
        missed = [name for name in expected if normalize_name(name) not in matched_set]
        return {
            "diagnosisDetail": evaluation_report.get("diagnosisDetail", {}),
            "examinationDetail": {
                **exam_detail,
                "redundant_examinations": redundant,
                "missed_examinations": missed,
            },
            "treatmentDetail": evaluation_report.get("treatmentDetail", {}),
        }


if __name__ == "__main__":
    if AgentBuilder is None:
        raise RuntimeError("hospital_agent_sdk is required to start the doctor agent service.")
    config = load_config("config.yaml")
    memory = build_memory(config)
    agent = MyDoctorAgent(config=config, memory=memory)
    AgentBuilder(agent).start()
