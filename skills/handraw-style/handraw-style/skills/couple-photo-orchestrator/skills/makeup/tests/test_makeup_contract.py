from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]

def test_makeup_is_mandatory_even_without_meihua():
    t=(ROOT/'skills/makeup/SKILL.md').read_text(encoding='utf-8')
    assert '只要进入正式拍摄流程就必须执行' in t
    assert '与用户是否主动调用 `skills/meihua/` 无关' in t

def test_makeup_has_skin_optimization():
    t=(ROOT/'skills/makeup/SKILL.md').read_text(encoding='utf-8')
    assert '白皙柔焦影楼精修' in t
    assert '明显淡化斑点/泛红/肤色不均' in t
    assert '去黑眼圈' in t

def test_makeup_is_theme_adaptive():
    t=(ROOT/'skills/makeup/SKILL.md').read_text(encoding='utf-8')
    assert '妆面风格必须随主题变化' in t
    assert '正式发型' in t


def test_female_default_finish():
    t=(ROOT/'skills/makeup/SKILL.md').read_text(encoding='utf-8')
    assert '白皙柔焦影楼精修' in t and '均匀偏白皙的健康肤色' in t
