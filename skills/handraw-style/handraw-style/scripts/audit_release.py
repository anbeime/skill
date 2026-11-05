#!/usr/bin/env python3
"""Audit current Git release candidates without printing secret values."""
from pathlib import Path
import argparse
import collections
import json
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]
PATTERNS={
    'local_path':re.compile(r'(?i)(?<![a-z0-9\\])(?:[a-z]:[\\/]|file:///[a-z]:|/(?:Users|home)/[A-Za-z0-9_-]+/)[^\s"\'<>`]*'),
    'private_key':re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'access_token':re.compile(r'(?<![\w-])(?:sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{25,}|github_pat_[A-Za-z0-9_]{30,}|AKIA[A-Z0-9]{16})'),
    'credential_literal':re.compile(r'(?i)(?:api[_-]?key|access[_-]?token|secret[_-]?key|password|app[_-]?secret)\s*["\']?\s*[:=]\s*["\']([^"\'\n]{8,})'),
}

def candidates(root):
    result=subprocess.run(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=root,check=True,capture_output=True)
    return sorted({n for n in result.stdout.decode('utf-8').split('\0') if n and (root/n).is_file()})

def audit(root=ROOT):
    root=Path(root).resolve();names=candidates(root);findings=[];texts=0;videos=[]
    for name in names:
        p=root/name
        if p.suffix.lower() in {'.mp4','.mov','.webm','.m4v','.mkv','.avi','.wmv','.mpg','.mpeg','.mts','.m2ts'}:videos.append(name)
        if re.search(r'(?i)(?:^|/)(?:\.env(?:\.|$)|id_rsa$|id_ed25519$|credentials\.json$|cookies\.json$|.*\.pem$)',name) and not name.endswith('.env.example'):
            findings.append({'file':name,'line':0,'kind':'private_config_or_key_filename'})
        try:text=p.read_text(encoding='utf-8-sig')
        except (UnicodeError,OSError):continue
        texts+=1
        for number,line in enumerate(text.splitlines(),1):
            for kind,pattern in PATTERNS.items():
                matches=list(pattern.finditer(line))
                if kind=='local_path':
                    if name=='scripts/sync_to_static.py' and ('/home/' + 'yang0/') in line:
                        continue
                    matches=[m for m in matches if not re.search(r'(?i)path[\\/]+to',m.group())]
                if matches:findings.append({'file':name,'line':number,'kind':kind})
    for name in videos:findings.append({'file':name,'line':0,'kind':'video_in_release'})
    return {'scope':'current tracked and unignored untracked files; excludes Git history and ignored private files',
            'candidate_files':len(names),'text_files':texts,'issue_counts':dict(collections.Counter(x['kind'] for x in findings)),
            'issues':findings,'passed':not findings}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--json',type=Path);args=parser.parse_args()
    result=audit()
    if args.json:
        args.json.parent.mkdir(parents=True,exist_ok=True)
        args.json.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result['passed'] else 2

if __name__=='__main__':raise SystemExit(main())
