from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

def test_beauty_board_is_visual_not_text_choice():
    skill=(ROOT/"skills/meihua/SKILL.md").read_text(encoding="utf-8")
    tpl=(ROOT/"skills/meihua/templates/beauty-board.md").read_text(encoding="utf-8")
    assert "不展示文字档位" in skill
    assert "exactly 3 clear, independent portrait panels" in tpl
    assert "left / center / right" in tpl

def test_beauty_hair_is_not_formal_hair_lock():
    skill=(ROOT/"skills/meihua/SKILL.md").read_text(encoding="utf-8")
    assert "不等于正式拍摄发型确认" in skill
    assert "Editorial 专业发型师设计" in skill

def test_beauty_preview_uses_unconstrained_editorial_hair_design():
    skill=(ROOT/"skills/meihua/SKILL.md").read_text(encoding="utf-8")
    tpl=(ROOT/"skills/meihua/templates/beauty-board.md").read_text(encoding="utf-8")
    assert "可任意变长或变短、变直或变卷" in skill
    assert "原参考图的发长、直卷和发色不构成默认限制" in skill
    assert "Editorial 专业发型师" in tpl

def test_beauty_preview_requires_an_explicit_fringe_design_decision():
    skill=(ROOT/"skills/meihua/SKILL.md").read_text(encoding="utf-8")
    tpl=(ROOT/"skills/meihua/templates/beauty-board.md").read_text(encoding="utf-8")
    assert "刘海设计为必填决策" in skill
    assert "保留原刘海、改造成具体刘海形状，或露额处理" in skill
    assert "必须明确刘海策略" in tpl

def test_beauty_board_must_include_fair_soft_focus_finish():
    skill=(ROOT/"skills/meihua/SKILL.md").read_text(encoding="utf-8")
    tpl=(ROOT/"skills/meihua/templates/beauty-board.md").read_text(encoding="utf-8")
    assert "白皙柔焦精修" in skill
    assert "轻微磨皮" in skill
    assert "柔和柔焦光晕" in skill
    assert "均匀偏白皙的健康肤色" in skill
    assert "白皙柔焦影楼精修" in tpl

def test_beauty_board_has_open_ended_rerender_prompt():
    skill=(ROOT/"skills/meihua/SKILL.md").read_text(encoding="utf-8")
    tpl=(ROOT/"skills/meihua/templates/beauty-board.md").read_text(encoding="utf-8")
    assert "也可以直接告诉我你的具体美化需求" in skill
    assert "做一版美图秀秀风格精修" in skill
    assert "去掉所有可见斑点" in tpl


def test_beauty_prep_is_explicit_only():
    skill=(ROOT/"skills/meihua/SKILL.md").read_text(encoding="utf-8")
    assert "仅在用户主动要求时触发" in skill
    assert "不得主动询问" in skill
