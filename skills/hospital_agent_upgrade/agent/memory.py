"""Small Markdown memory for evaluation reflections.

The baseline stores one reflection field per patient. Future prompts read the
latest patient reflections as simple reference notes.
"""

from __future__ import annotations

import json
import math
import re
from ast import literal_eval
from collections import Counter
from hashlib import sha1
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MEMORY_PATH = BASE_DIR / "data" / "memory_data" / "memory.md"

_CHIEF_COMPLAINT_ERROR_PATTERN_MAP: tuple[Dict[str, Any], ...] = (
    {
        "triggers": ("胸痛", "胸闷", "劳力性胸痛", "放射痛"),
        "rules": (
            "**general_examination_rules:** 当主诉为胸痛/胸闷且缺乏感染证据时，应优先做心血管缺血评估，避免先行细菌培养或无关病原学检查。",
        ),
    },
    {
        "triggers": ("膝前痛", "膝关节前痛", "髌骨", "上下楼", "下楼", "蹲起"),
        "rules": (
            "**general_examination_rules:** 当局部膝前痛伴上下楼梯或蹲起加重时，应优先选择膝关节专科体格检查，避免扩展到无症状系统的常规筛查。",
        ),
    },
    {
        "triggers": ("鼻塞", "鼻窦", "鼻旁窦", "面部胀痛", "鼻腔"),
        "rules": (
            "**general_examination_rules:** 当鼻腔鼻窦症状提示结构性病变时，应优先选择鼻内镜和鼻窦影像，避免先开与主诉无关的全身筛查。",
        ),
    },
    {
        "triggers": ("勃起困难", "勃起功能障碍", "晨勃减少", "性功能"),
        "rules": (
            "**general_examination_rules:** 当主诉指向器质性勃起功能障碍时，应先评估性激素和阴茎血流/勃起功能，避免跳到与当前主诉无关的泛化检查。",
        ),
    },
)


def _clean_memory_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


class MarkdownMemory:
    def __init__(
        self,
        path: Union[str, Path],
        *,
        max_notes: int = 3,
        max_note_chars: int = 1200,
    ):
        self.path = Path(path)
        self.max_notes = int(max_notes)
        self.max_note_chars = int(max_note_chars)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("# Baseline Doctor Memory\n\n", encoding="utf-8")

    def load_notes(
        self,
        limit: Optional[int] = None,
        *,
        case_profile: Optional[Dict[str, Any]] = None,
        focus: Optional[str] = None,
    ) -> List[str]:
        """读取与当前病例触发词最匹配的 general_* 规则。

        focus:
        - None / "all": 诊断/检查/治疗规则混合，按触发词相关性排序。
        - "treatment": 优先 general_treatment_rules 与 general_personalization_rules，
          供综合诊断与治疗、最终自检参考 memory.md 中的治疗经验。
        """
        max_count = int(limit or self.max_notes)
        records = self._read_general_rule_records()
        ranked = self._rank_records(records, case_profile or {}) if records else []

        if focus == "treatment":
            treatment_keys = {"general_treatment_rules", "general_personalization_rules"}
            preferred = [item for item in ranked if item.get("rule_key") in treatment_keys]
            others = [item for item in ranked if item.get("rule_key") not in treatment_keys]
            ranked = preferred + others

        prioritized_notes: List[str] = []
        if focus != "treatment":
            prioritized_notes.extend(self._chief_complaint_error_pattern_notes(case_profile or {}))
            prioritized_notes.extend(self._frequent_error_pattern_notes(case_profile or {}))

        notes: List[str] = []
        seen = set()
        for item in ranked:
            rule = self._normalise_rule(item["rule"])
            if not rule or rule in seen:
                continue
            seen.add(rule)
            notes.append(rule)
            if len(notes) >= max_count:
                return notes
        for rule in prioritized_notes:
            normalized = self._normalise_rule(rule)
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            notes.append(normalized)
            if len(notes) >= max_count:
                break
        return notes

    def _chief_complaint_error_pattern_notes(self, case_profile: Dict[str, Any]) -> List[str]:
        query_text = json.dumps(case_profile or {}, ensure_ascii=False)
        normalized = _clean_memory_text(query_text)
        notes: List[str] = []
        for item in _CHIEF_COMPLAINT_ERROR_PATTERN_MAP:
            triggers = item.get("triggers") or ()
            if any(str(trigger) in normalized for trigger in triggers):
                notes.extend(str(rule) for rule in item.get("rules") or [])
        return notes

    def _frequent_error_pattern_notes(self, case_profile: Dict[str, Any]) -> List[str]:
        blocks = self._read_reflection_blocks()
        if not blocks:
            return []

        query_text = json.dumps(case_profile or {}, ensure_ascii=False)
        query_keywords = set(self._trigger_keywords_from_text(query_text))
        query_domains = self._clinical_domains(query_keywords)
        global_counts: Counter[str] = Counter()
        matched_counts: Counter[str] = Counter()

        for block in blocks:
            block_keywords = set(block.get("trigger_keywords") or [])
            block_domains = self._clinical_domains(block_keywords)
            matches_case = not query_keywords or bool(query_keywords & block_keywords) or bool(query_domains & block_domains)
            for pattern in self._extract_negative_examination_patterns(block.get("block", "")):
                global_counts[pattern] += 1
                if matches_case or self._pattern_matches_case(pattern, query_keywords, query_domains):
                    matched_counts[pattern] += 1

        notes: List[str] = []
        for pattern, count in global_counts.most_common():
            if count < 2:
                continue
            if matched_counts.get(pattern, 0) <= 0 and count < 3:
                continue
            notes.append("**general_examination_rules:** 高频错误模式提醒：%s" % pattern)
        return notes[:3]

    def _rank_records(
        self,
        records: List[Dict[str, Any]],
        case_profile: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Rank reusable rules by trigger overlap plus a lightweight TF-IDF score."""
        query_text = json.dumps(case_profile, ensure_ascii=False)
        query_keywords = set(self._trigger_keywords_from_text(query_text))
        if not query_keywords and not _clean_memory_text(query_text):
            return sorted(records, key=lambda item: item["block_index"], reverse=True)

        documents = [
            "%s %s %s" % (
                record.get("rule_key") or "",
                " ".join(record.get("trigger_keywords") or []),
                record.get("rule") or "",
            )
            for record in records
        ]
        query_tokens = self._memory_tokens(query_text)
        doc_tokens = [self._memory_tokens(document) for document in documents]
        doc_frequency: Counter[str] = Counter()
        for tokens in doc_tokens:
            doc_frequency.update(set(tokens))

        scored: List[Dict[str, Any]] = []
        query_domains = self._clinical_domains(query_keywords)
        for record, document, tokens in zip(records, documents, doc_tokens):
            trigger_keywords = set(record.get("trigger_keywords") or [])
            overlap_score = len(query_keywords & trigger_keywords) * 3.0
            document_keywords = set(self._trigger_keywords_from_text(document))
            domain_score = len(query_domains & self._clinical_domains(document_keywords)) * 1.5
            semantic_score = self._tfidf_cosine(query_tokens, tokens, doc_frequency, len(records))
            scored.append(
                {
                    **record,
                    "trigger_score": overlap_score,
                    "domain_score": domain_score,
                    "semantic_score": semantic_score,
                    "score": overlap_score + domain_score + semantic_score,
                }
            )

        matched = [item for item in scored if item["score"] > 0]
        return sorted(
            matched or scored,
            key=lambda item: (
                float(item.get("trigger_score") or 0.0),
                float(item.get("domain_score") or 0.0),
                float(item.get("semantic_score") or 0.0),
                item["block_index"],
            ),
            reverse=True,
        )

    def _read_reflection_blocks(self) -> List[Dict[str, Any]]:
        text = self.path.read_text(encoding="utf-8")
        blocks: List[Dict[str, Any]] = []
        for block_index, raw_block in enumerate(text.split("\n## ")[1:], start=1):
            block = "## " + raw_block.strip()
            blocks.append(
                {
                    "block": block,
                    "block_index": block_index,
                    "trigger_keywords": self._trigger_keywords_from_block(block),
                }
            )
        return blocks

    def _extract_negative_examination_patterns(self, block: str) -> List[str]:
        patterns: List[str] = []
        for line in block.splitlines():
            stripped = line.strip()
            if not stripped.startswith("- **"):
                continue
            if not any(key in stripped for key in ("general_examination_rules", "Examination", "Future Strategy")):
                continue
            body = self._rule_body(stripped)
            if any(marker in body for marker in ("避免", "不要", "不得", "不应", "无感染证据", "无明确感染证据", "未受累系统")):
                patterns.append(body)
        return patterns

    def _pattern_matches_case(
        self,
        pattern: str,
        query_keywords: set[str],
        query_domains: set[str],
    ) -> bool:
        if not pattern:
            return False
        pattern_keywords = set(self._trigger_keywords_from_text(pattern))
        if query_keywords & pattern_keywords:
            return True
        return bool(query_domains & self._clinical_domains(pattern_keywords))

    @staticmethod
    def _rule_body(line: str) -> str:
        match = re.match(r"-?\s*\*\*[^*]+:\*\*\s*(.*)", str(line or "").strip())
        return _clean_memory_text(match.group(1) if match else line)

    @staticmethod
    def _clinical_domains(keywords: set[str]) -> set[str]:
        """Map related findings to broad systems before free-text similarity."""
        domain_terms = {
            "ophthalmology": ("斜视", "内斜", "外斜", "眼位", "屈光", "视力", "弱视", "眼底", "眼压", "眼球", "眼睑", "瞳孔"),
            "cardiovascular": ("胸痛", "胸闷", "气短", "心悸", "水肿", "瓣膜", "冠脉", "冠心病", "心绞痛", "心肌", "心衰", "缺血", "心律失常", "血压", "血脂"),
            "respiratory_infection": ("发热", "寒战", "感染", "咳嗽", "咳血", "咯血", "血痰", "肺", "咽", "喉", "扁桃体", "脓"),
            "dermatology": ("皮肤", "皮疹", "水疱", "脓疱", "瘙痒", "脱屑", "湿疹", "汗疱"),
            "urinary": ("尿", "排尿", "尿痛", "尿频", "尿急", "前列腺", "膀胱", "肾", "蛋白尿", "血尿"),
            "neurology": ("头痛", "神经", "麻木", "无力", "抽搐", "意识", "惊厥", "嗜睡"),
            "gastrointestinal": ("腹痛", "腹泻", "呕吐", "黄疸", "肝", "胃", "肠"),
            "metabolic": ("低镁", "低钾", "低钙", "高镁", "高钾", "高钙", "电解质", "代谢", "酸中毒", "碱中毒", "血糖"),
        }
        return {
            domain
            for domain, terms in domain_terms.items()
            if any(term in keyword or keyword in term for keyword in keywords for term in terms)
        }

    def _memory_tokens(self, text: Any) -> List[str]:
        """Compact tokenization for mixed Chinese/English medical notes."""
        normalized = _clean_memory_text(text).lower()
        tokens = self._trigger_keywords_from_text(normalized)
        tokens.extend(re.findall(r"[a-z][a-z0-9_+-]{2,}", normalized))
        chinese_terms = re.findall(r"[\u4e00-\u9fff]{2,8}", normalized)
        tokens.extend(chinese_terms)
        for term in chinese_terms:
            if len(term) >= 3:
                tokens.extend(term[index:index + 2] for index in range(len(term) - 1))
        return [token for token in tokens if token]

    @staticmethod
    def _tfidf_cosine(
        query_tokens: List[str],
        doc_tokens: List[str],
        doc_frequency: Counter[str],
        doc_count: int,
    ) -> float:
        if not query_tokens or not doc_tokens:
            return 0.0

        def vector(tokens: List[str]) -> Dict[str, float]:
            counts = Counter(tokens)
            total = max(1, sum(counts.values()))
            result: Dict[str, float] = {}
            for token, count in counts.items():
                idf = math.log((1 + doc_count) / (1 + doc_frequency.get(token, 0))) + 1.0
                result[token] = (count / total) * idf
            return result

        query_vector = vector(query_tokens)
        doc_vector = vector(doc_tokens)
        common = set(query_vector) & set(doc_vector)
        if not common:
            return 0.0
        dot = sum(query_vector[token] * doc_vector[token] for token in common)
        query_norm = math.sqrt(sum(value * value for value in query_vector.values()))
        doc_norm = math.sqrt(sum(value * value for value in doc_vector.values()))
        if not query_norm or not doc_norm:
            return 0.0
        return dot / (query_norm * doc_norm)

    def append_case_reflection(
        self,
        *,
        patient_id: str,
        evaluation_reflection: Optional[Dict[str, Any]] = None,
        case_profile: Optional[Dict[str, Any]] = None,
        **_: Any,
    ) -> None:
        """训练评估后，仅保存完整、可迁移的反思。"""
        if not self._has_reusable_reflection(evaluation_reflection or {}):
            return
        case_block, record_id = self._case_block(evaluation_reflection or {}, case_profile or {})
        self._upsert_case_block(record_id, case_block)

    @staticmethod
    def _has_reusable_reflection(reflection: Dict[str, Any]) -> bool:
        value = reflection.get("reflection") if "reflection" in reflection else reflection
        if not isinstance(value, dict):
            return False
        return any(
            clean
            for clean in (
                str(value.get("general_diagnosis_rules") or "").strip(),
                str(value.get("general_examination_rules") or "").strip(),
                str(value.get("general_treatment_rules") or "").strip(),
                str(value.get("general_personalization_rules") or "").strip(),
            )
        )

    def _case_block(self, reflection: Dict[str, Any], case_profile: Dict[str, Any]) -> tuple[str, str]:
        reflection_value = reflection.get("reflection") if "reflection" in reflection else reflection
        if not isinstance(reflection_value, dict):
            reflection_value = {"summary": reflection_value}

        trigger_keywords = self._trigger_keywords_from_profile(case_profile)
        if not trigger_keywords:
            trigger_keywords = self._trigger_keywords_from_text(str(reflection_value.get("profile") or ""))
        reusable_text = "|".join(
            self._normalise_rule(reflection_value.get(key))
            for key in (
                "general_diagnosis_rules",
                "general_examination_rules",
                "general_treatment_rules",
                "general_personalization_rules",
            )
        )
        record_id = sha1(("、".join(trigger_keywords) + reusable_text).encode("utf-8")).hexdigest()[:12]

        lines = [
            "## General Reflection %s" % record_id,
            "",
            "Trigger Keywords: %s" % "、".join(trigger_keywords),
            "",
            "### Reflection",
            "",
        ]
        for label, key in [
            ("Profile", "profile"),
            ("Diagnosis", "diagnosis_reflection"),
            ("Examination", "examination_reflection"),
            ("Treatment", "treatment_reflection"),
            ("Future Strategy", "future_strategy"),
        ]:
            value = self._truncate(self._normalise_rule(reflection_value.get(key)))
            if value:
                lines.append("- **%s:** %s" % (label, value))

        for key in (
            "general_diagnosis_rules",
            "general_examination_rules",
            "general_treatment_rules",
            "general_personalization_rules",
        ):
            value = self._truncate(self._normalise_rule(reflection_value.get(key)))
            if value:
                lines.append("- **%s:** %s" % (key, value))

        return "\n".join(lines).rstrip() + "\n", record_id


    def _read_general_rule_records(self) -> List[Dict[str, Any]]:
        text = self.path.read_text(encoding="utf-8")
        general_keys = (
            "general_diagnosis_rules",
            "general_examination_rules",
            "general_treatment_rules",
            "general_personalization_rules",
        )
        records: List[Dict[str, Any]] = []
        parts = text.split("\n## ")
        for block_index, raw_block in enumerate(parts[1:], start=1):
            block = "## " + raw_block.strip()
            trigger_keywords = self._trigger_keywords_from_block(block)
            for line in block.splitlines():
                stripped = line.strip()
                for key in general_keys:
                    if stripped.startswith("- **%s:**" % key) or stripped.startswith("**%s:**" % key):
                        rule = self._normalise_rule(stripped.lstrip("- ").strip())
                        if not rule:
                            break
                        records.append(
                            {
                                "rule": rule,
                                "rule_key": key,
                                "trigger_keywords": trigger_keywords,
                                "block_index": block_index,
                            }
                        )
                        break
        return records

    @staticmethod
    def _normalise_rule(value: Any) -> str:
        """Turn historical list literals into one compact prompt-safe rule."""
        text = str(value or "").strip()
        if not text:
            return ""
        prefix_match = re.match(r"(\*\*general_[^*]+:\*\*)\s*(.*)", text)
        prefix, body = (prefix_match.group(1), prefix_match.group(2)) if prefix_match else ("", text)
        if body.startswith("[") and body.endswith("]"):
            try:
                parsed = literal_eval(body)
            except (ValueError, SyntaxError):
                parsed = None
            if isinstance(parsed, list):
                body = "；".join(str(item).strip() for item in parsed if str(item).strip())
        body = re.sub(r"\s+", " ", body).strip()
        if not body or "patient_" in body.lower():
            return ""
        return ("%s %s" % (prefix, body)).strip()

    def _trigger_keywords_from_block(self, block: str) -> List[str]:
        for line in block.splitlines()[:5]:
            if line.strip().lower().startswith("trigger keywords:"):
                _, value = line.split(":", 1)
                return self._split_keywords(value)
        return []

    def _trigger_keywords_from_profile(self, case_profile: Dict[str, Any]) -> List[str]:
        if not case_profile:
            return []
        return self._trigger_keywords_from_text(json.dumps(case_profile, ensure_ascii=False))

    def _trigger_keywords_from_text(self, text: str) -> List[str]:
        normalized = str(text or "")
        lexicon = (
            # 眼科
            "斜视", "内斜", "外斜", "眼位", "屈光", "视力", "弱视", "眼底", "裂隙灯", "眼压", "畏光", "瞳孔", "散瞳", "眼球", "眼睑", "遮盖", "视轴",
            # 心血管
            "胸痛", "胸闷", "气短", "呼吸困难", "心悸", "水肿", "瓣膜", "冠脉", "心衰", "冠心病", "心绞痛", "心肌", "高血压", "血压", "血脂", "缺血", "心律失常",
            # 呼吸/感染
            "发热", "寒战", "感染", "脓", "咽", "喉", "扁桃体", "咳嗽", "肺", "咳血", "咯血", "血痰",
            # 皮肤
            "皮肤", "皮疹", "水疱", "脓疱", "瘙痒", "脱屑", "接触", "过敏", "汗疱", "湿疹",
            # 泌尿/生殖
            "尿", "排尿", "尿痛", "尿频", "尿急", "前列腺", "膀胱", "肾", "蛋白尿", "血尿",
            # 骨/关节
            "关节", "外伤", "骨折", "脱位", "疼痛", "肿胀", "皮肤过伸", "易瘀青", "骨", "钙", "佝偻", "骨软化", "骨质疏松",
            # 耳鼻喉
            "耳", "听力", "耳鸣", "眩晕", "突发性聋",
            # 神经
            "头痛", "神经", "麻木", "无力", "抽搐", "意识", "惊厥", "嗜睡",
            # 消化
            "腹痛", "腹泻", "呕吐", "黄疸", "肝", "胃", "肠",
            # 代谢/电解质
            "低镁", "低钾", "低钙", "高镁", "高钾", "高钙", "电解质", "代谢", "酸中毒", "碱中毒", "血气", "血氨", "血糖", "糖化", "甲状旁腺", "PTH", "维生素D",
            # 特殊人群/背景
            "妊娠", "儿童", "老人", "新生儿", "婴儿", "免疫抑制", "激素", "抗凝", "糖尿病", "高血压", "肿瘤", "化疗",
            # 血液/风湿
            "凝血", "血小板", "贫血", "狼疮", "自身免疫", "补体", "抗核", "ANCA",
            # 妇科
            "停经", "闭经", "痛经", "阴道", "盆腔", "子宫", "卵巢", "胎动",
        )
        hits = [keyword for keyword in lexicon if keyword in normalized]
        # Add compact Chinese symptom tokens after common separators for cases not covered by the lexicon.
        for token in re.findall(r"[\u4e00-\u9fff]{2,6}", normalized):
            if token in hits:
                continue
            if any(keyword in token for keyword in lexicon):
                hits.append(token)
            if len(hits) >= 15:
                break
        return self._split_keywords("、".join(hits))[:15]

    def _split_keywords(self, value: Any) -> List[str]:
        seen = set()
        result: List[str] = []
        for item in re.split(r"[、,，;；\s]+", str(value or "")):
            keyword = item.strip()
            if not keyword or keyword in seen:
                continue
            seen.add(keyword)
            result.append(keyword)
        return result

    def _upsert_case_block(self, record_id: str, new_block: str) -> None:
        text = self.path.read_text(encoding="utf-8")
        parts = text.split("\n## ")
        header = parts[0].rstrip() if parts else "# Baseline Doctor Memory"
        case_blocks = []
        for raw_block in parts[1:]:
            block = "## " + raw_block.strip()
            if not self._is_reflection_block(block, record_id):
                case_blocks.append(block)
        body = "\n\n".join([*case_blocks, new_block]).strip()
        self.path.write_text("%s\n\n%s\n" % (header, body), encoding="utf-8")

    def _is_reflection_block(self, block: str, record_id: str) -> bool:
        first_line = block.splitlines()[0].strip() if block.strip() else ""
        return first_line == "## General Reflection %s" % record_id

    def _truncate(self, value: Any, max_chars: Optional[int] = None) -> str:
        text = str(value or "").strip()
        limit = int(max_chars or self.max_note_chars)
        if len(text) <= limit:
            return text
        return text[: limit - 18].rstrip() + "\n...[truncated]"


def build_memory(config: Dict[str, Any]) -> MarkdownMemory:
    memory_config = config.get("memory") if isinstance(config.get("memory"), dict) else {}
    configured_path = memory_config.get("md_path") if isinstance(memory_config, dict) else None
    max_notes = memory_config.get("max_notes", 3) if isinstance(memory_config, dict) else 3
    max_note_chars = memory_config.get("max_note_chars", 1200) if isinstance(memory_config, dict) else 1200
    memory_path = Path(configured_path) if configured_path else DEFAULT_MEMORY_PATH
    if not memory_path.is_absolute():
        memory_path = BASE_DIR / memory_path
    return MarkdownMemory(
        memory_path,
        max_notes=int(max_notes),
        max_note_chars=int(max_note_chars),
    )
