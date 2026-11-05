from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]

def test_identity_reference_is_face_only_not_hair_lock():
    core=(ROOT/'CORE_REQUIREMENTS.md').read_text(encoding='utf-8')
    shot=(ROOT/'skills/paishe/scripts/shot_board.py').read_text(encoding='utf-8')
    assert 'Canonical 原图是“人脸身份参考”，不是“造型参考”' in core
    assert '必须忽略原图中的发长、直卷、刘海、分缝' in core
    assert '原参考图只做人脸身份锚定，不做发型锚定' in shot

def test_locked_editorial_hairstyle_overrides_reference_hair():
    hair=(ROOT/'skills/hairstyle/SKILL.md').read_text(encoding='utf-8')
    paishe=(ROOT/'skills/paishe/SKILL.md').read_text(encoding='utf-8')
    assert 'Canonical 真人参考图只提供人脸身份信息' in hair
    assert '正式发型只执行已锁定的 `hairstyle_design`' in paishe
