#!/usr/bin/env python3
"""Manage canonical vs explicitly promoted identity references in a handoff file."""
from __future__ import annotations
import argparse
from pathlib import Path
import yaml

def read(path): return yaml.safe_load(path.read_text(encoding='utf-8')) or {}
def write(path, value): path.write_text(yaml.safe_dump(value, allow_unicode=True, sort_keys=False), encoding='utf-8')

def mapping(project, pid):
    items=project.setdefault('identity_map',[])
    item=next((x for x in items if isinstance(x,dict) and x.get('participant_id')==pid),None)
    if item is None:
        item={'participant_id':pid,'canonical_original_references':[],'active_identity_references':[],'identity_references':[],'active_reference_source':'original_user_upload','explicit_promotion':False,'promoted_from':None}
        items.append(item)
    return item

def register_original(args):
    p=Path(args.handoff); data=read(p); proj=data.setdefault('project',{}); m=mapping(proj,args.participant_id)
    refs=list(dict.fromkeys((m.get('canonical_original_references') or [])+[args.reference]))
    m['canonical_original_references']=refs
    if not m.get('explicit_promotion'):
        m['active_identity_references']=list(refs); m['identity_references']=list(refs); m['active_reference_source']='original_user_upload'; m['promoted_from']=None
    write(p,data)

def promote(args):
    p=Path(args.handoff); data=read(p); proj=data.setdefault('project',{}); m=mapping(proj,args.participant_id)
    if not m.get('canonical_original_references'):
        raise SystemExit('register original identity reference before promoting a derived image')
    m['active_identity_references']=[args.reference]; m['identity_references']=[args.reference]
    m['active_reference_source']='explicit_user_promoted_derived'; m['explicit_promotion']=True; m['promoted_from']=args.reference
    write(p,data)

def restore(args):
    p=Path(args.handoff); data=read(p); proj=data.setdefault('project',{}); m=mapping(proj,args.participant_id)
    refs=m.get('canonical_original_references') or []
    if not refs: raise SystemExit('no canonical original references recorded')
    m['active_identity_references']=list(refs); m['identity_references']=list(refs)
    m['active_reference_source']='original_user_upload'; m['explicit_promotion']=False; m['promoted_from']=None
    write(p,data)

def main():
    ap=argparse.ArgumentParser(); sp=ap.add_subparsers(dest='cmd',required=True)
    for name,func in [('register-original',register_original),('promote',promote),('restore-original',restore)]:
        s=sp.add_parser(name); s.add_argument('--handoff',required=True); s.add_argument('--participant-id',required=True)
        if name!='restore-original': s.add_argument('--reference',required=True)
        s.set_defaults(func=func)
    a=ap.parse_args(); a.func(a)
if __name__=='__main__': main()
