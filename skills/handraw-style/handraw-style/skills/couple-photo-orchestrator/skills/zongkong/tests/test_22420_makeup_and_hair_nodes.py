from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]

def test_makeup_child_skill_present():
    assert (ROOT/'skills/makeup/SKILL.md').exists()
    assert (ROOT/'skills/makeup/templates/makeup-plan.md').exists()

def test_full_flow_has_hair_then_makeup():
    t=(ROOT/'CORE_REQUIREMENTS.md').read_text(encoding='utf-8')
    assert '方向卡生成阶段' in t
    assert 'Editorial 发型师' in t and 'Editorial 化妆师' in t
    assert '用户选择 A/B/C 后' in t

def test_handoff_supports_makeup_design():
    t=(ROOT/'skills/kefu/templates/handoff-schema.yaml').read_text(encoding='utf-8')
    assert 'makeup_design:' in t

def test_beauty_prep_remains_optional():
    t=(ROOT/'skills/meihua/SKILL.md').read_text(encoding='utf-8')
    assert '仅在用户主动要求时触发' in t

def test_final_makeup_is_not_optional():
    t=(ROOT/'skills/makeup/SKILL.md').read_text(encoding='utf-8')
    assert '只要进入正式拍摄流程就必须执行' in t
