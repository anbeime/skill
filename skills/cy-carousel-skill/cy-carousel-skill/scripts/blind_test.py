#!/usr/bin/env python3
"""不标答案的3:4盲测；参考原作由调用者另行提供，绝不自带。"""
from pathlib import Path
from PIL import Image,ImageDraw
import argparse,json,random,math,hashlib
from 图像等比 import cover_cell

def build(reference_dir,candidate_dir,out,kind='inner',seed=20261004,reference_count=9,candidate_count=4,faces=None,reference_list=None):
 reference_dir=Path(reference_dir);candidate_dir=Path(candidate_dir);out=Path(out)
 valid=lambda p:p.suffix.lower() in ('.jpg','.jpeg','.png')
 refs=[reference_dir/p for p in reference_list] if reference_list else sorted(p for p in reference_dir.rglob('*') if p.is_file() and valid(p) and ('preview' in p.parts or p.parent==reference_dir))
 cand=sorted(p for p in candidate_dir.iterdir() if p.is_file() and valid(p))
 def select_kind(paths):
  cover=lambda p:'封面' in p.stem or p.stem in ('p01','01')
  return [p for p in paths if ('备选' not in p.name and '无字' not in p.name) and (cover(p) if kind=='cover' else not cover(p))]
 refs=select_kind(refs);cand=select_kind(cand)
 if len(refs)<reference_count or len(cand)<candidate_count:raise ValueError(f'素材不足：参考{len(refs)}、候选{len(cand)}；不能重复图片凑格数')
 rng=random.Random(seed);items=[('reference',p) for p in rng.sample(refs,reference_count)]+[('candidate',p) for p in rng.sample(cand,candidate_count)];rng.shuffle(items)
 count=len(items);cols=5 if count>10 else 3;cell=(300,400);gap=18;label=28;rows=math.ceil(count/cols)
 canvas=Image.new('RGB',(cols*(cell[0]+gap)+gap,rows*(cell[1]+gap+label)+gap),'#444444');d=ImageDraw.Draw(canvas);audit=[];answers=[]
 for i,(pool,p) in enumerate(items,1):
  base=reference_dir if pool=='reference' else candidate_dir;rel=str(p.relative_to(base));key=pool+'/'+rel
  verified=(faces or {}).get(key)
  if isinstance(verified,dict):
   if verified.get('status')!='success':raise ValueError('人脸审计失败：'+key)
   verified=verified['faces']
  with Image.open(p) as im:pic=cover_cell(im,cell,audit,source_name=key,face_boxes=verified)
  x=gap+(i-1)%cols*(cell[0]+gap);y=gap+(i-1)//cols*(cell[1]+gap+label)
  canvas.paste(pic,(x,y));d.text((x+8,y+cell[1]+4),f'{i:02}',fill='white')
  answers.append({'cell':i,'pool':pool,'file':rel,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 out.parent.mkdir(parents=True,exist_ok=True);canvas.save(out,quality=92)
 answer_dir=out.parent/'盲测答案';answer_dir.mkdir(exist_ok=True)
 (answer_dir/(out.stem+'.json')).write_text(json.dumps({'seed':seed,'kind':kind,'answers':answers,'cells':audit,'style_acceptance':'需要人工判断；机器只验证拼图几何'},ensure_ascii=False,indent=2),encoding='utf-8')
 return {'cells':count,'max_aspect_error':max(v['aspect_error_ratio'] for v in audit),'answer_file':str((answer_dir/(out.stem+'.json')).name)}

if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--reference-dir',type=Path,required=True);ap.add_argument('--candidate-dir',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--kind',choices=['cover','inner'],default='inner');ap.add_argument('--seed',type=int,default=20261004);ap.add_argument('--reference-count',type=int,default=9);ap.add_argument('--candidate-count',type=int,default=4);ap.add_argument('--faces',type=Path);ap.add_argument('--reference-list',type=Path);a=ap.parse_args()
 print(build(a.reference_dir,a.candidate_dir,a.out,a.kind,a.seed,a.reference_count,a.candidate_count,json.loads(a.faces.read_text(encoding='utf-8')) if a.faces else None,json.loads(a.reference_list.read_text(encoding='utf-8')) if a.reference_list else None))
