from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]

def test_meihua_is_not_proactively_prompted():
    t=(ROOT/'skills/meihua/SKILL.md').read_text(encoding='utf-8')
    assert '仅在用户主动要求时触发' in t
    assert '不得主动询问' in t

def test_direction_cards_have_early_hair_makeup():
    t=(ROOT/'skills/kefu/templates/direction-drafts.md').read_text(encoding='utf-8')
    assert 'per_participant_styling_fields' in t
    assert 'Pxx 发型定稿' in t and 'Pxx 妆容定稿' in t

def test_female_makeup_default_is_fair_soft_focus_studio_retouch():
    t=(ROOT/'skills/makeup/SKILL.md').read_text(encoding='utf-8')
    for x in ('白皙柔焦影楼精修','明显淡化斑点/泛红/肤色不均','去黑眼圈','轻微磨皮','柔和柔焦光晕','均匀偏白皙的健康肤色'):
        assert x in t

def test_no_second_look_confirmation_contract():
    t=(ROOT/'skills/kefu/templates/handoff-schema.yaml').read_text(encoding='utf-8')
    assert 'Do not ask for a second Group Look confirmation' in t
    assert 'direction_selected' in t

def test_identity_mapping_and_styling_validator():
    schema=(ROOT/'skills/kefu/templates/handoff-schema.yaml').read_text(encoding='utf-8')
    board=(ROOT/'skills/paishe/scripts/shot_board.py').read_text(encoding='utf-8')
    validator=(ROOT/'skills/zongkong/scripts/validate_project.py').read_text(encoding='utf-8')
    assert 'identity_map:' in schema
    assert 'identity swap / face swap' in board
    assert 'missing hairstyle_design' in validator and 'missing makeup_design' in validator
