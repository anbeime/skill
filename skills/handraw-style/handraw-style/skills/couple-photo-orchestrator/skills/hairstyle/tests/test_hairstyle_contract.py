from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]

def test_hairstyle_is_early_and_locked_downstream():
    t=(ROOT/'skills/hairstyle/SKILL.md').read_text(encoding='utf-8')
    assert '方向卡' in t and '下游 Look / Shot / 生图只继承' in t

def test_hairstyle_has_full_design_freedom():
    t=(ROOT/'skills/hairstyle/SKILL.md').read_text(encoding='utf-8')
    assert '变长 / 变短' in t
    assert '直发 / 卷发 / 波浪' in t
    assert '刘海策略必须显式决定' in t
