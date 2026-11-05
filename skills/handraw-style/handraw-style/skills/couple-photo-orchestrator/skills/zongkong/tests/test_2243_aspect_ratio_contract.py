from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

def test_contact_sheet_generation_has_no_size_constraint():
    core = (ROOT / "CORE_REQUIREMENTS.md").read_text(encoding="utf-8")
    zong = (ROOT / "skills" / "zongkong" / "SKILL.md").read_text(encoding="utf-8")
    shot = (ROOT / "skills" / "paishe" / "scripts" / "shot_board.py").read_text(encoding="utf-8")
    assert "不再指定单格比例或整板比例" in core
    assert "不再指定单格比例" in zong
    assert "Do not specify or force any panel aspect ratio" in shot
    assert 'DEFAULT_PANEL_RATIO = None' in shot
