from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

def test_core_has_participant_structure_gate():
    text = (ROOT / "CORE_REQUIREMENTS.md").read_text(encoding="utf-8")
    assert "人物结构确认 Gate" in text
    assert "1 女 + 1 男" in text
    assert "总人数" in text and "性别构成" in text and "人物关系/角色结构" in text

def test_direction_card_has_relationship_and_per_person_wardrobe():
    text = (ROOT / "skills/kefu/templates/direction-drafts.md").read_text(encoding="utf-8")
    assert "人物关系描述" in text
    assert "女方服装" in text and "男方服装" in text
    assert "per_participant_wardrobe_fields" in text
    assert "禁止输出单一合并" in text

def test_handoff_schema_tracks_gender_and_relationship_description():
    text = (ROOT / "skills/kefu/templates/handoff-schema.yaml").read_text(encoding="utf-8")
    assert "gender_composition:" in text
    assert "relationship_description:" in text
    assert "participant_structure_confirmed:" in text
    assert "gender:" in text
