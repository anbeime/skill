#!/usr/bin/env python3
"""把已检查的自有稿整理成发布文件；输出新目录，不上传/发布。"""
from pathlib import Path
from PIL import Image,ImageDraw
import argparse,json,shutil,math,hashlib
from check_all import check_note
from 图像等比 import cover_cell

def deliver(note,pages,out,report=None,assets_root=None,cover_c=None,strict_visual=False,accept_visual=None):
 note=Path(note);pages=Path(pages);out=Path(out)
 if out.exists() and any(out.iterdir()):raise ValueError('交付目录非空，拒绝覆盖现有成品')
 result=check_note(note/'页面脚本.json',pages,report,assets_root,strict_visual=strict_visual)
 if not result['passed']:raise ValueError('检查未通过，禁止交付：'+str(result['errors']))
 blockers=result.get('visual_blockers',[]);reason=(accept_visual or '').strip()
 if accept_visual is not None and not reason:raise ValueError('--accept-visual 需要写明放行理由')
 if blockers and not reason:raise ValueError('严格视觉检查未通过，禁止交付：'+str(blockers)+'；逐页目检后确认可交付，请加 --accept-visual "理由" 放行（理由会写入交付清单.json）')
 required=['标题.txt','正文.txt','置顶评论.txt','来源.md']
 for f in required:
  if not (note/f).is_file() or not (note/f).read_text(encoding='utf-8').strip():raise ValueError('缺文稿：'+f+'（打包需要分别命名的 '+'、'.join(required)+'，均为非空 UTF-8 文本）')
 data=json.loads((note/'页面脚本.json').read_text(encoding='utf-8'));out.mkdir(parents=True,exist_ok=True);files=[]
 for i in range(1,len(data['pages'])+1):
  name='01-封面.png' if i==1 else f'{i:02}.png';source=pages/f'p{i:02}.png';target=out/name
  shutil.copy2(source,target);files.append(target)
 if cover_c:
  with Image.open(cover_c) as im:
   if im.size!=(1440,1920):raise ValueError('C备选尺寸必须1440×1920')
  shutil.copy2(cover_c,out/'封面备选-无字版.png')
 for f in required:shutil.copy2(note/f,out/f)
 cols=5 if len(files)>6 else 3;cell=(360,480);gap=14;label=28;rows=math.ceil(len(files)/cols)
 grid=Image.new('RGB',(cols*(360+gap)+gap,rows*(480+label+gap)+gap),'#333333');d=ImageDraw.Draw(grid);audit=[]
 for i,p in enumerate(files):
  with Image.open(p) as im:pic=cover_cell(im,cell,audit,source_name=p.name)
  x=gap+i%cols*(360+gap);y=gap+i//cols*(480+label+gap);grid.paste(pic,(x,y));d.text((x,y+485),f'{i+1:02}',fill='white')
 grid.save(out/'全套预览.jpg',quality=93)
 manifest={'technical_passed':True,'visual_acceptance':result.get('visual_acceptance'),'advisories':result.get('advisories',[]),'scope':result['scope'],'strict_visual':bool(result.get('strict_visual')),'visual_accepted':{'reason':reason,'blockers':blockers} if blockers else None,'published':False,'human_review':'事实/许可/目检/盲测须另行验收','cover':'01-封面.png','preview_cells':audit,'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files},'placeholder_account':data.get('config',{}).get('account_name','{账号名}')=='{账号名}'}
 (out/'交付清单.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');return manifest

if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--note',type=Path,required=True);ap.add_argument('--pages',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--report',type=Path);ap.add_argument('--assets-root',type=Path);ap.add_argument('--cover-c',type=Path);ap.add_argument('--strict-visual',action='store_true',help='留白/连续同骨架有问题时拒绝交付');ap.add_argument('--accept-visual',metavar='理由',help='放行严格视觉阻断，理由写入交付清单');a=ap.parse_args()
 r=deliver(a.note,a.pages,a.out,a.report,a.assets_root,a.cover_c,strict_visual=a.strict_visual,accept_visual=a.accept_visual);print(json.dumps({'technical_passed':True,'visual_acceptance':r.get('visual_acceptance'),'advisories':r.get('advisories',[]),'visual_accepted':r.get('visual_accepted'),'scope':r['scope'],'images':len(r['files']),'published':False},ensure_ascii=False))
