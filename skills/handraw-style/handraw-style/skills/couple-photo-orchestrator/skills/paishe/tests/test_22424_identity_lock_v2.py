from pathlib import Path
import importlib.util
ROOT=Path(__file__).resolve().parents[3]
SHOT=ROOT/'skills/paishe/scripts/shot_board.py'

def load():
    spec=importlib.util.spec_from_file_location('shot_board_22424',SHOT)
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def sample_lock():
    return {'participant_outfits':[{
      'participant_id':'P01','label':'女主','outfit':'white suit',
      'hairstyle_design':'short-to-medium straight hair in low bun',
      'makeup_design':'soft-focus editorial makeup',
      'identity_references':['references/identity/P01-original.png'],
      'identity_reference_meta':{'active_reference_source':'original_user_upload'}
    }]}

def sample_shot(i=1,prompt='wide full-body back-facing pose with reflection'):
    return {'shot_id':i,'participants_present':['P01'],'shot_size':'full-body','composition':'wide environmental portrait','action_event':'turning over one shoulder','pose_structure':'back-facing','prompt':prompt}

def test_global_identity_lock_v2_is_high_priority_and_geometric():
    m=load(); s=m.identity_lock_v2_prompt(sample_lock())
    assert 'IDENTITY LOCK — HIGHEST PRIORITY' in s
    assert 'directly and independently' in s
    assert 'Do NOT derive a face from another generated panel' in s
    assert 'eye shape and eye spacing' in s
    assert 'jawline and chin shape' in s
    assert 'No face drift' in s

def test_each_panel_gets_independent_identity_reset():
    m=load(); board={'visual_lock':sample_lock(),'shots':[sample_shot(i, f'photo {i}') for i in range(1,9)]}
    s=m.grid_prompt(board)
    assert s.count('PANEL IDENTITY RESET') == 8
    assert s.count("restore the exact recognizable facial identity directly") == 8

def test_face_readability_guard_covers_full_body_back_turn_and_reflection():
    m=load(); s=m.face_readability_guard(sample_shot())
    assert 'full-body/environmental framing' in s
    assert 'back-oriented/over-shoulder pose' in s
    assert 'reflection is secondary' in s

def test_original_reference_still_does_not_lock_hair():
    m=load(); s=m.identity_lock_v2_prompt(sample_lock())
    assert 'controls FACE IDENTITY ONLY' in s
    assert 'Execute the locked Editorial hairstyle_design instead' in s

def test_grid_brief_code_records_identity_lock_v2_metadata():
    t=SHOT.read_text(encoding='utf-8')
    assert '"identity_lock_version": 2' in t
    assert 'per-panel direct reconstruction' in t

def test_schema_declares_per_panel_reset_and_forbids_inheritance():
    t=(ROOT/'skills/kefu/templates/handoff-schema.yaml').read_text(encoding='utf-8')
    assert 'identity_lock_version: 2' in t
    assert 'per_panel_identity_reset_required: true' in t
    assert 'panel_to_panel_face_inheritance_forbidden: true' in t
