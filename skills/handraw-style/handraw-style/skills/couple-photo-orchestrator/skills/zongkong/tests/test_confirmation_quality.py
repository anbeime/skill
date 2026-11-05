from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

def _read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")

def test_orchestrator_direction_selection_is_only_forward_gate():
    text = _read("skills/zongkong/SKILL.md")
    assert "A/B/C 只表示方向" in text
    assert "用户回复 `a / b / c`" in text
    assert "不再插入 Look 二次确认或 Shot 二次确认" in _read("skills/zongkong/references/interaction-modes.md")

def test_kefu_forbids_mode_menu_and_extra_confirmation():
    text = _read("skills/kefu/SKILL.md")
    assert "不得" in text and "模式" in text and "菜单" in text
    assert "不设置二次确认" in text
    assert "direction_selection" in text

def test_confirmation_template_is_nonblocking_header():
    text = _read("skills/kefu/templates/confirmation-sheet.md")
    assert "不得单独作为确认步骤" in text
    assert "必须在同一份回复/文档中继续输出" in text

def test_quality_contract_forbids_location_regression():
    text = _read("skills/zongkong/references/quality-contract.md")
    assert "Location specificity is monotonic" in text
    assert "上海外滩 W 酒店" in text
    assert "厦门鼓浪屿" in text
