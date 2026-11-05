from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def test_release_builder_has_integrity_gates():
    t=(ROOT/'scripts/build_release.py').read_text(encoding='utf-8')
    assert 'MIN_FILES=80' in t
    for x in ('zongkong','kefu','huanzhuang','paishe','meihua','makeup','hairstyle'): assert x in t
    assert '.pytest_cache' in t and '__pycache__' in t
