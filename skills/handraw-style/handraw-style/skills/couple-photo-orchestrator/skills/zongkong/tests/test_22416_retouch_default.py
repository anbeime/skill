from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]

def test_makeup_node_replaces_prompt_only_retouch_default():
    core=(ROOT/'CORE_REQUIREMENTS.md').read_text(encoding='utf-8')
    assert 'Editorial 专业发型师与化妆师前置设计' in core
    assert '白皙柔焦影楼精修' in core

def test_shot_board_executes_confirmed_makeup():
    t=(ROOT/'skills/paishe/scripts/shot_board.py').read_text(encoding='utf-8')
    assert '正式妆容/皮肤优化' in t
    assert '最终生图还必须执行方向阶段已经锁定的 Editorial 专业化妆师设计' in t

def test_makeup_is_not_skipped_when_beauty_prep_is_skipped():
    t=(ROOT/'skills/makeup/SKILL.md').read_text(encoding='utf-8')
    assert '与用户是否主动调用 `skills/meihua/` 无关' in t
