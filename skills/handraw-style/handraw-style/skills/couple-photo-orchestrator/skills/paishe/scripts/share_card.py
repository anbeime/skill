#!/usr/bin/env python3
"""Compile and cache a share card before image rendering."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path
import yaml

FORBIDDEN=("新卡已生成","抽卡结果","当前处于抽卡模式","切换回自主模式","本次生成")
REQUIRED=("story_card_name","share_hook","reproduction_prompt","share_hashtags","share_cta")

def read_yaml(p): return yaml.safe_load(p.read_text(encoding="utf-8")) or {}
def write_yaml(p,v): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(yaml.safe_dump(v,allow_unicode=True,sort_keys=False),encoding="utf-8")

def validate(card):
    if not isinstance(card,dict): raise SystemExit("share card must be an object")
    missing=[k for k in REQUIRED if not card.get(k)]
    if missing: raise SystemExit("share card missing: "+", ".join(missing))
    tags=card["share_hashtags"]
    if isinstance(tags,str): tags=[x for x in tags.split() if x]
    if not isinstance(tags,list) or not 4<=len(tags)<=7 or any(not str(x).startswith("#") for x in tags):
        raise SystemExit("share_hashtags must contain 4-7 #hashtags")
    card["share_hashtags"]=[str(x).strip() for x in tags]
    text=" ".join(str(card.get(k,"")) for k in REQUIRED)
    if any(x in text for x in FORBIDDEN): raise SystemExit("share card contains forbidden workflow language")
    if not str(card["reproduction_prompt"]).lstrip().startswith("@couple-photo-orchestrator"):
        raise SystemExit("reproduction_prompt must start with @couple-photo-orchestrator")
    card["status"]="ready"
    return card

def render(card):
    return "\n".join([
        "【分享文案】",
        f"《{card['story_card_name']}》",
        card['share_hook'],
        "",
        "复刻提示词",
        card['reproduction_prompt'],
        "",
        " ".join(card['share_hashtags']),
        "",
        card['share_cta'],
    ]) + "\n"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("project"); ap.add_argument("board_id"); ap.add_argument("--share-file"); ap.add_argument("--skip",action="store_true")
    a=ap.parse_args(); project=Path(a.project).resolve(); board_path=project/'deliverables'/'shot-boards'/f'{a.board_id}.yaml'
    if not board_path.exists(): raise SystemExit(f"unknown shot board: {a.board_id}")
    board=read_yaml(board_path)
    outdir=project/'deliverables'/'share-cards'; outdir.mkdir(parents=True,exist_ok=True)
    if a.skip:
        card={"status":"skipped","reason":"user_requested_no_share_copy"}; board["share_card"]=card; write_yaml(board_path,board); print("SHARE_CARD_SKIPPED"); return
    if not a.share_file: raise SystemExit("--share-file is required unless --skip is used")
    source=Path(a.share_file); raw=source.read_text(encoding='utf-8')
    card=yaml.safe_load(raw) if source.suffix.lower() in {'.yaml','.yml'} else json.loads(raw)
    card=validate(card)
    yaml_path=outdir/f'{a.board_id}-share-card.yaml'; md_path=outdir/f'{a.board_id}-share-card.md'
    card['markdown_path']=str(md_path.relative_to(project)).replace('\\','/')
    write_yaml(yaml_path,card); md_path.write_text(render(card),encoding='utf-8')
    board['share_card']=card; board['share_card']['yaml_path']=str(yaml_path.relative_to(project)).replace('\\','/')
    write_yaml(board_path,board)
    print(render(card))
if __name__=='__main__': main()
