from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]

def test_core_allows_full_hair_redesign():
    t=(ROOT/'CORE_REQUIREMENTS.md').read_text(encoding='utf-8')
    assert '发长（变长/变短）' in t
    assert '直发/卷发/波浪' in t
    assert '刘海策略为必填决策' in t

def test_hairstyle_skill_has_full_hair_design_fields():
    t=(ROOT/'skills/hairstyle/templates/hairstyle-plan.md').read_text(encoding='utf-8')
    assert 'length' in t and 'texture' in t and 'parting' in t and 'fringe' in t
    assert '保留原刘海 / 具体新刘海 / 露额' in t

def test_shot_board_executes_planned_hair_and_makeup():
    t=(ROOT/'skills/paishe/scripts/shot_board.py').read_text(encoding='utf-8')
    assert '正式发型' in t
    assert '正式妆容/皮肤优化' in t
