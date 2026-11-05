#!/usr/bin/env python3
"""Validate and build a complete couple-photo-orchestrator release ZIP."""
from __future__ import annotations
import argparse, compileall, re, shutil, sys, zipfile
from pathlib import Path
import yaml

REQUIRED_SKILLS=("zongkong","kefu","huanzhuang","paishe","meihua","makeup","hairstyle")
MIN_FILES=80
FORBIDDEN_PARTS={'.pytest_cache','__pycache__'}

def fail(msg): raise SystemExit(msg)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('--version',required=True); ap.add_argument('--output',required=True); a=ap.parse_args()
    root=Path(a.root).resolve(); out=Path(a.output).resolve()
    if not root.is_dir(): fail('release root missing')
    for skill in REQUIRED_SKILLS:
        if not (root/'skills'/skill).is_dir(): fail(f'missing required skill: {skill}')
    files=[p for p in root.rglob('*') if p.is_file()]
    if len(files)<MIN_FILES: fail(f'incomplete package: only {len(files)} files, need >= {MIN_FILES}')
    bad=[p for p in root.rglob('*') if any(part in FORBIDDEN_PARTS for part in p.parts) or p.suffix=='.pyc']
    if bad: fail('forbidden cache artifacts: '+', '.join(str(p.relative_to(root)) for p in bad[:10]))
    # Version checks on active files
    core=(root/'CORE_REQUIREMENTS.md').read_text(encoding='utf-8'); skill=(root/'SKILL.md').read_text(encoding='utf-8'); current=(root/'CURRENT_VERSION.md').read_text(encoding='utf-8')
    if f'Version: {a.version}' not in core: fail('CORE_REQUIREMENTS version mismatch')
    if not re.search(rf'(?m)^version:\s*{re.escape(a.version)}$',skill): fail('root SKILL version mismatch')
    if a.version not in current: fail('CURRENT_VERSION mismatch')
    for child in REQUIRED_SKILLS:
        p=root/'skills'/child/'SKILL.md'
        if p.exists() and not re.search(rf'(?m)^version:\s*{re.escape(a.version)}$',p.read_text(encoding='utf-8')): fail(f'{child} version mismatch')
    for p in root.rglob('*.yaml'):
        try: yaml.safe_load(p.read_text(encoding='utf-8'))
        except Exception as e: fail(f'YAML parse failed: {p.relative_to(root)}: {e}')
    if not compileall.compile_dir(str(root),quiet=1): fail('Python compile failed')
    # clean compile caches created by compileall
    for cache in list(root.rglob('__pycache__')):
        shutil.rmtree(cache)
    if out.exists(): out.unlink()
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        top=root.name
        for p in sorted(root.rglob('*')):
            if p.is_file(): z.write(p,Path(top)/p.relative_to(root))
    print(f"{out}\nfiles={len([p for p in root.rglob('*') if p.is_file()])}\nsize={out.stat().st_size}")
if __name__=='__main__': main()
