import subprocess, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def load(stage):
    return subprocess.check_output(['git', 'show', f':{stage}:README.md']).decode('utf-8', 'replace')

for st in (2, 3):
    t = load(st)
    lines = t.splitlines()
    print(f'===== stage {st} | lines={len(lines)} | MattPocock={t.count("Matt Pocock")} =====')
    for i, l in enumerate(lines):
        if 'Matt Pocock' in l:
            a = max(0, i-2); b = min(len(lines), i+3)
            print(f'--- around line {i} ---')
            for j in range(a, b):
                print(f'  {j}: {lines[j]}')
    print()
