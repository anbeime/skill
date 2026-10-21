import json, subprocess, sys

def load(stage):
    out = subprocess.check_output(['git', 'show', f':{stage}:SKILL_SOURCES.json'])
    return json.loads(out)

a = load(2)
b = load(3)

# base = the more complete side (remote auto-sync, newer) ; over = the other (local)
base = a if len(a) >= len(b) else b
over = b if base is a else a

def deep_merge(base, over):
    if isinstance(base, dict) and isinstance(over, dict):
        res = dict(base)
        for k, v in over.items():
            if k in res:
                res[k] = deep_merge(res[k], v)
            else:
                res[k] = v  # new key from 'over' (e.g. mattpocock) -> keep
        return res
    if isinstance(base, list) and isinstance(over, list):
        res = list(base)
        for item in over:
            if item not in res:
                res.append(item)
        return res
    # scalar / type mismatch: prefer base (authoritative) if present
    return base if base is not None else over

merged = deep_merge(base, over)

# validate
assert isinstance(merged, dict)
with open('SKILL_SOURCES.json', 'w', encoding='utf-8') as f:
    json.dump(merged, f, ensure_ascii=False, indent=2)

# counts
matt = [k for k in merged if k.startswith('mattpocock/skills')]
print('top-level keys:', len(merged))
print('mattpocock entries:', len(matt))
print('base side had', len(a), 'over side had', len(b))
