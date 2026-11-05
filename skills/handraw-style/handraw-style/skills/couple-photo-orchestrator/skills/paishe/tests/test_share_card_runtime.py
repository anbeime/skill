from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]

def test_share_card_compiler_exists_and_precedes_render():
    assert (ROOT/'skills/paishe/scripts/share_card.py').exists()
    t=(ROOT/'skills/paishe/scripts/shot_board.py').read_text(encoding='utf-8')
    assert 'compile Share Card before image rendering' in t

def test_share_card_has_story_title_and_reproduction_heading_contract():
    t=(ROOT/'skills/paishe/scripts/share_card.py').read_text(encoding='utf-8')
    assert 'story_card_name' in t and 'reproduction_prompt' in t
    assert '【分享文案】' in t and '复刻提示词' in t
