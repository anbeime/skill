from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'skills/zongkong/scripts'))
from remix_dependencies import resolve

def test_wardrobe_invalidates_hair_and_makeup():
    r=resolve('服装'); assert 'hairstyle' in r['always'] and 'makeup' in r['always']

def test_era_invalidates_full_styling_chain():
    r=resolve('年代'); assert all(x in r['always'] for x in ('wardrobe','hairstyle','makeup','scene','pose_shot'))
