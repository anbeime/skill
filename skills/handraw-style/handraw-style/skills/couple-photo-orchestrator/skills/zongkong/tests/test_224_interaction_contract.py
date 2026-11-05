from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

def test_224_no_mode_menu_and_direction_state_contract():
    text = (ROOT / "skills/zongkong/references/interaction-modes.md").read_text(encoding="utf-8")
    assert "禁止" in text and "方式 A" in text
    assert "A/B/C 只表示方向" in text
    assert "B / b / 2" in text
    assert "pending_direction_cards" in text
    assert "自适应布局八宫格" in text

def test_first_turn_template_is_spacetime_anchored():
    text = (ROOT / "skills/kefu/templates/direction-drafts.md").read_text(encoding="utf-8")
    assert "时空坐标" in text
    assert "A/B" in text and "现代现实世界著名真实地点" in text
    assert "few_shot_exclusion_set" in text

