from pathlib import Path
import importlib.util
import yaml
ROOT=Path(__file__).resolve().parents[3]

def test_schema_has_canonical_original_policy():
    t=(ROOT/'skills/kefu/templates/handoff-schema.yaml').read_text(encoding='utf-8')
    assert 'canonical_source: original_user_upload' in t
    assert 'derived_images_never_auto_promote: true' in t
    assert 'canonical_original_references:' in t
    assert 'explicit_promotion: false' in t

def test_render_prompt_keeps_original_identity_and_demotes_derived_images():
    t=(ROOT/'skills/paishe/scripts/shot_board.py').read_text(encoding='utf-8')
    assert 'canonical identity reference' in t
    assert 'composition/pose/style reference' in t
    assert 'composition_reference_role' in t
    assert 'explicit_user_promoted_derived' in t

def test_meihua_does_not_auto_promote():
    t=(ROOT/'skills/meihua/SKILL.md').read_text(encoding='utf-8')
    assert '选择左 / 中 / 右或执行放大本身不等于切换身份参考' in t
    assert '后续拍摄继续以最初真人原图锁定身份' in t

def test_validator_rejects_silent_identity_replacement():
    path=ROOT/'skills/zongkong/scripts/validate_project.py'
    spec=importlib.util.spec_from_file_location('vp',path); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    errors=[]
    m.validate_identity_reference_policy({
      'identity_reference_policy':{'canonical_source':'original_user_upload','derived_images_never_auto_promote':True,'explicit_user_promotion_required':True},
      'identity_map':[{'participant_id':'P01','canonical_original_references':['references/identity/original.png'],'active_identity_references':['images/shot.png'],'active_reference_source':'original_user_upload','explicit_promotion':False}]
    },errors)
    assert any('cannot replace canonical originals without explicit promotion' in e for e in errors)

def test_identity_manager_promote_and_restore(tmp_path):
    handoff=tmp_path/'handoff.yaml'
    handoff.write_text(yaml.safe_dump({'project':{'identity_map':[]}},allow_unicode=True),encoding='utf-8')
    path=ROOT/'skills/zongkong/scripts/identity_reference_manager.py'
    spec=importlib.util.spec_from_file_location('irm',path); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    class A: pass
    a=A(); a.handoff=str(handoff); a.participant_id='P01'; a.reference='references/identity/original.png'; m.register_original(a)
    a.reference='images/derived.png'; m.promote(a)
    d=yaml.safe_load(handoff.read_text(encoding='utf-8')); item=d['project']['identity_map'][0]
    assert item['explicit_promotion'] is True and item['active_identity_references']==['images/derived.png']
    m.restore(a); d=yaml.safe_load(handoff.read_text(encoding='utf-8')); item=d['project']['identity_map'][0]
    assert item['explicit_promotion'] is False and item['active_identity_references']==['references/identity/original.png']
