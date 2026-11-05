"""Audit a text-only skill, then optionally build and verify its ZIP."""
from pathlib import Path
import argparse,hashlib,json,re,zipfile
ALLOWED={'.md','.py','.js','.mjs','.cjs','.json','.yaml','.yml','.css','.html','.txt','.sh'}
SPECIAL={'LICENSE','.gitignore'}
SKIP={'.git','__pycache__','node_modules'}
# Generated single-file viewer bundle: still required to be UTF-8 text, but its
# minified contents legitimately contain SVG/encoded strings from three.js.
BUILD_ARTIFACTS={'app.bundle.js'}
# Repo README assets (donate QR + demo media): ship in the repository,
# excluded from the text-only shareable ZIP.
REPO_ASSETS={'wechat-donate.png','demo-before.gif','demo-before.mp4','demo-after.gif','demo-after.mp4'}
MAGIC=[b'\x89PNG\r\n\x1a\n',b'\xff\xd8\xff',b'GIF87a',b'GIF89a',b'glTF',b'BLENDER']

def audit(root):
    root=Path(root).resolve();files=[]
    for p in sorted(root.rglob('*')):
        if any(part in SKIP for part in p.relative_to(root).parts):continue
        if p.is_symlink():raise ValueError('Symlink not permitted: '+str(p))
        if not p.is_file():continue
        if p.name in REPO_ASSETS:continue
        if p.suffix.lower() not in ALLOWED and p.name not in SPECIAL:raise ValueError('Not an allowed source file: '+str(p))
        data=p.read_bytes()
        if any(data.startswith(m) for m in MAGIC):raise ValueError('Binary asset detected: '+str(p))
        text=data.decode('utf-8-sig')
        if p.name not in BUILD_ARTIFACTS:
            if re.search(r'data\s*:\s*image\s*/',text,re.I) or re.search(r'<svg[\s>]',text,re.I):raise ValueError('Embedded image found: '+str(p))
            # Inline @font-face base64 (data:font/...) is the one sanctioned
            # embedded payload: it keeps the viewer blocker-proof.
            if 'data:font/' not in text and re.search(r'[A-Za-z0-9+/]{300,}={0,2}',text):raise ValueError('Opaque encoded payload found: '+str(p))
        files.append(p)
    if not (root/'SKILL.md') in files:raise ValueError('Missing SKILL.md')
    return files

def package(root,out):
    root=Path(root).resolve();files=audit(root);out=Path(out).resolve()
    if out.is_relative_to(root):raise ValueError('Place the archive outside the skill folder')
    out.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        for p in files:z.write(p,root.name+'/'+p.relative_to(root).as_posix())
    with zipfile.ZipFile(out) as z:
        assert z.testzip() is None
        assert len(z.infolist())==len(files)
        for item in z.infolist():z.read(item).decode('utf-8-sig')
    return {'archive':str(out),'files':len(files),'image_files':0,'embedded_images':0,'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('skill');p.add_argument('--out');a=p.parse_args()
    print(json.dumps(package(a.skill,a.out) if a.out else {'files':len(audit(a.skill)),'image_files':0,'embedded_images':0},indent=2))
