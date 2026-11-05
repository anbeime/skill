#!/usr/bin/env python3
"""统一图文检查：不修改输入；技术验收与人工事实/视觉验收分开。"""
import argparse,json,hashlib,re,sys
from pathlib import Path
from PIL import Image,ImageColor
from io_paths import set_assets_root,asset_path,check_relative_spec
from render import page_config,normalize_tone,default_elements
from 验证背景 import background_rules,backdrop_rules,geometry_rules,tone_rules,variation_rules
from 验证排版 import richness_rules,alternation_rules,color_hierarchy_rules,watermark_rules
from 浅色排版 import light_editorial_rules,face_text_rules
from 验证留白 import check as whitespace_check


PAGE_COUNTER=re.compile(r'^\s*\d{1,2}\s*/\s*\d{1,2}\s*$|第\s*\d+\s*页')

def red_lines(n,p,r):
 """本风格的硬红线：不要图注、页眉页脚、页码栏目名、过小的字和孤字行。"""
 out=[]
 for e in p.get('elements',[]):
  if e.get('kind')=='caption':out.append(f'P{n:02}有图注：图上不写出处/说明，出处统一放置顶评论')
  if e.get('kind')=='text':
   if e.get('text_role')=='label':
    if e.get('size',60)<28:out.append(f'P{n:02}人名标签小于28px：{e["text"][:12]}')
    if re.search(r'(?i)wikimedia|commons|博物馆藏|public domain|CC[ -]?BY|CC0|图源|来源',e['text']):out.append(f'P{n:02}标签里写了出处/授权：{e["text"][:12]}（出处放置顶评论）')
   elif e.get('size',60)<48:out.append(f'P{n:02}文字小于48px（像图注/页眉）：{e["text"][:12]}')
   if PAGE_COUNTER.search(e['text']):out.append(f'P{n:02}有页码/栏目编号：{e["text"][:12]}')
 if p.get('layout')!='cover':
  for t in r.get('text',[]):
   b=t.get('ink_bounds')
   if b and (b[1]<40 or b[3]>1895):out.append(f'P{n:02}文字贴着页面上下边（页眉/页脚）：{t["text"][:12]}')
   rows={}
   for g in t.get('glyphs') or []:rows.setdefault(g['line'],[]).append(g['char'])
   if len(rows)>1 and any(len([c for c in v if c not in '，。、：；！？…—·」』》）,.!?:;']) <2 for v in rows.values()):
    out.append(f'P{n:02}有孤字行：{t["text"][:12]}')
 return out


def check_note(script,pages,report=None,assets_root=None,products=False,strict_visual=False):
 script=Path(script).resolve();pages=Path(pages).resolve();report=Path(report or pages/'render-report.json')
 set_assets_root(assets_root);data=json.loads(script.read_text(encoding='utf-8'));reports=json.loads(report.read_text(encoding='utf-8'))
 if products:
  for n,r in enumerate(reports,1):r['output_file']=str(pages/('01-封面.png' if n==1 else f'{n:02}.png'))
 errors=check_relative_spec(data);checks={};sample=data.get('mode')=='sample'
 if len(data['pages'])!=len(reports):errors.append('脚本与渲染报告页数不一致')
 if not sample and not 9<=len(data['pages'])<=13:errors.append('正式稿必须为D封面＋8–12张内页')
 if not data['pages'] or data['pages'][0]['layout']!='cover':errors.append('第一页必须为D主封面')
 else:
  cover=data['pages'][0];titles=[e for e in cover.get('elements',[]) if e['kind']=='text' and e.get('size',0)>=90]
  if len(titles)!=2:errors.append('D主封面必须有两行独立大标题')
  if cover.get('bookmark',data.get('config',{}).get('bookmark',False)):errors.append('系列书签默认关闭；定制例外需单独人工批准')
  if cover.get('border') and titles:
   t=next((v for v in reports[0].get('text',[]) if v['text']==titles[-1]['text'] and v['box']==titles[-1]['box']),{})
   b=t.get('effect_bounds') or t.get('ink_bounds')
   if not b or min(b[0],b[1],1440-b[2],1920-b[3])<60:errors.append('D第二行实际字形/阴影与边框须≥60px')
 expected=hashlib.sha256(json.dumps(data.get('config',{}),ensure_ascii=False,sort_keys=True).encode()).hexdigest()
 for n,p in enumerate(data['pages'],1):
  r=next((v for v in reports if v['page']==n),{})
  cfg=page_config(data.get('config',{}),p);cfg['tone']=normalize_tone(data.get('tone',cfg.get('tone','暗')))
  target=Path(r.get('output_file',pages/f'p{n:02}.png'))
  if not target.is_file():errors.append(f'P{n:02}缺成图');continue
  with Image.open(target) as im:
   if im.size!=(1440,1920):errors.append(f'P{n:02}成品必须1440×1920')
  if r.get('config_script_sha256')!=expected:errors.append(f'P{n:02}配置与渲染报告不一致')
  if any(v['opaque_overlap']>.03 for v in r.get('collisions',[])):errors.append(f'P{n:02}文字与抠图碰撞>3%')
  for e in p.get('elements',default_elements(p)):
   for key in ('path','mask','subject_mask','cutout_path'):
    if e.get(key) and not asset_path(script.parent,e[key]).is_file():errors.append(f'P{n:02}缺素材 {e[key]}')
   if 'face_boxes' in e and (not e.get('face_detection_method') or '待补' in e.get('face_detection_method','')):errors.append(f'P{n:02}脸框方法未经确认：{e.get("source_id")}')
  for t in r.get('text',[]):
   if t.get('font_file',{}).get('fallback'):errors.append(f'P{n:02}授权字库回退，不能视为正式接入成功')
   bounds=t.get('effect_bounds') or t.get('ink_bounds')
   if bounds and (bounds[0]<0 or bounds[1]<0 or bounds[2]>1440 or bounds[3]>1920):errors.append(f'P{n:02}文字墨迹越界：{t["text"][:16]}')
   if t.get('used_height',0)>t.get('capacity_height',0)+1:errors.append(f'P{n:02}正文盒溢出')
   brush='MaShanZheng' in t.get('font_file',{}).get('path','')
   if brush:
    if re.search(r'[0-9]',t['text']) and not t.get('latin_font'):errors.append(f'P{n:02}毛笔标题含数字（加 latin_font 让数字用黑体）')
    if any(v['adjacent_han'] and (v['gap_em']>.2 or v['gap_em']<-.001) for v in t.get('punctuation_gaps',[])):errors.append(f'P{n:02}毛笔标点间距不合格')
    if cfg['tone']=='暗' and t.get('effect')=='3d' and (t.get('depth')!=7 or t.get('bold')!=1 or t.get('external_outline')):errors.append(f'P{n:02}毛笔立体效果不符合清晰版B')
  for c in r.get('components',[]):
   if c['kind']=='disc_portrait' and (c['disc_visible_ratio']<.4 or not c['actual_outside_pixels'] or c.get('outline')):errors.append(f'P{n:02}圆盘露出/越边/无细圈不合格')
  ft=face_text_rules(p,r)
  if not ft['passed']:errors.append(f'P{n:02}字形/贴条挡脸：{ft["collisions"]}')
  errors.extend(red_lines(n,p,r))
 advisories=[]
 # 风格指标（色彩丰富度、强调色占比、交替节奏、留白配额等）只作参考：为凑指标改版式，反而会把页面做坏。
 ADVISORY={'richness','alternation','whitespace','variation','color_area'}
 # 严格视觉（默认关闭）只把留白均值/空带和「与前页骨架相同」升级为交付阻断；色彩丰富度、原图数量等依赖体裁，永远只是建议。
 # 阻断不是让执行者凑指标：确认页面目检没问题时，用 package.py --accept-visual "理由" 放行并留档。
 strict_visual=bool(strict_visual or data.get('config',{}).get('visual_gate'));blockers=[]
 visual_applicable=not sample and normalize_tone(data.get('tone',data.get('config',{}).get('tone','暗')))!='浅'
 def run(name,fn):
  target=advisories if name in ADVISORY else errors
  try:
   result=fn();checks[name]=result;target.extend(result.get('errors',[]))
   if strict_visual and visual_applicable:blockers.extend(m for m in result.get('errors',[]) if visual_blocking(name,m))
  except (OSError,ValueError,KeyError,StopIteration,TypeError) as exc:
   checks[name]={'passed':False,'errors':[str(exc)]};target.append(f'{name}: {exc}')
   # 严格模式下，留白/骨架检查自己出错不能当作「无阻断」放行
   if strict_visual and visual_applicable and name in VISUAL_GATE_CHECKS:blockers.append(f'{name}检查未能运行：{exc}')
 def not_applicable(reason):
  checks['strict_visual']={'applicable':False,'reason':reason+'，严格视觉检查不适用，visual_blockers 恒为空不代表通过'}
  print('严格视觉不适用：'+checks['strict_visual']['reason'],file=sys.stderr)
 run('geometry',lambda:geometry_rules(data,reports,script,pages))
 run('background',lambda:background_rules(data,reports,script,pages))
 run('tone',lambda:tone_rules(data,reports,script,pages,checks.get('background')))
 run('backdrop',lambda:backdrop_rules(data,reports,script,pages))
 run('watermark',lambda:watermark_rules(data))
 if sample:
  run('color_area',lambda:color_hierarchy_rules(data,reports,script,pages))
  if strict_visual:not_applicable('三页小样不跑留白/骨架检查')
  checks['production_quotas']={'applicable':False,'reason':'三页小样只验流程；正式稿8–12内页/15图源/全篇丰富度配额未验收'}
 else:
  run('richness',lambda:richness_rules(data,reports,script,pages))
  if normalize_tone(data.get('tone',data.get('config',{}).get('tone','暗')))=='浅':
   if strict_visual:not_applicable('浅色调不跑留白/骨架检查')
   run('light_editorial',lambda:light_editorial_rules(data,reports,script,pages))
   run('color_area',lambda:color_hierarchy_rules(data,reports,script,pages))
  else:
   run('alternation',lambda:alternation_rules(data,reports,script,pages))
   run('whitespace',lambda:whitespace_check([Path(r.get('output_file',pages/f'p{n:02}.png')) for n,(p,r) in enumerate(zip(data['pages'],reports),1) if p['layout']!='cover']))
   if data.get('config',{}).get('visual_revision_profile') in ('eye-v2','general'):run('variation',lambda:variation_rules(data,reports,script,pages))
 # Precisely scoped user-approved exceptions, never a blanket waiver.
 exceptions=data.get('source_reuse_exceptions',[])
 if exceptions:
  for ex in exceptions:
   sid=ex.get('source_id');count=sum(e.get('source_id')==sid for p in data['pages'] for e in p.get('elements',[]) if e['kind'] in ('image','dark_backdrop','disc_portrait'))
   involved=sum(any(e.get('source_id')==sid for e in p.get('elements',[])) for p in data['pages'])
   if ex.get('user_instruction') and count==ex.get('placements') and involved==ex.get('pages'):
    msg=f'原图{sid}复用{count}>2';errors=[v for v in errors if v!=msg]
    if 'richness' in checks:
     checks['richness']['errors']=[v for v in checks['richness']['errors'] if v!=msg];checks['richness']['passed']=not checks['richness']['errors']
   else:errors.append(f'复用例外与实际摆放不一致：{sid}')
 manifest=script.parent/'素材清单.json'
 if manifest.exists():
  checked=[]
  for asset in load_manifest(manifest):
   source=asset_path(script.parent,asset['path'])
   if not source.is_file():errors.append('清单缺素材：'+asset['path']);continue
   sha=hashlib.sha256(source.read_bytes()).hexdigest();ok=sha==asset['sha256'];checked.append({'path':asset['path'],'sha256_matches':ok})
   if not ok:errors.append('清单素材SHA不一致：'+asset['path'])
  checks['asset_manifest']={'passed':all(v['sha256_matches'] for v in checked),'files':checked}
 errors=list(dict.fromkeys(errors))
 return {'advisories':list(dict.fromkeys(advisories)),'visual_acceptance':visual_acceptance(list(dict.fromkeys(advisories))),'strict_visual':strict_visual,'visual_blockers':list(dict.fromkeys(blockers)),'passed':not errors,'scope':'sample-technical' if sample else 'production-technical','production_ready':False if sample else not errors,'manual_review_required':['历史事实与来源原文','图片使用许可','原尺寸目检','人工盲测'],'pages':len(data['pages']),'exceptions':exceptions,'checks':checks,'errors':errors}


def load_manifest(path):
 data=json.loads(Path(path).read_text(encoding='utf-8'))
 example='{"assets":[{"path":"assets/a.png","sha256":"<64位十六进制>"}]}'
 if not isinstance(data,dict) or not isinstance(data.get('assets'),list):raise ValueError(f'素材清单.json 顶层必须是含 assets 数组的对象，例如 {example}')
 for i,a in enumerate(data['assets']):
  if not isinstance(a,dict) or not all(isinstance(a.get(k),str) for k in ('path','sha256')):raise ValueError(f'素材清单.json 的 assets[{i}] 必须是含 path 和 sha256 的对象，例如 {example}')
 return data['assets']


VISUAL_GATE_CHECKS=('whitespace','richness')


def visual_blocking(name,message):
 return name=='whitespace' or (name=='richness' and '骨架相同' in message)


def visual_acceptance(advisories):
 n=len(advisories)
 return f'未验收，存在 {n} 条建议项；技术通过不代表视觉质量通过，须人工逐页看原尺寸图' if n else '未验收；机器不判断视觉质量，须人工逐页看原尺寸图'


def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('script',type=Path);g=ap.add_mutually_exclusive_group(required=True);g.add_argument('--pages',type=Path);g.add_argument('--products',type=Path);ap.add_argument('--report',type=Path);ap.add_argument('--assets-root',type=Path);ap.add_argument('--out',type=Path);ap.add_argument('--strict-visual',action='store_true',help='留白/连续同骨架升级为交付阻断');a=ap.parse_args()
 try:r=check_note(a.script,a.pages or a.products,a.report or (a.script.parent/'渲染基准.json' if a.products else None),a.assets_root,bool(a.products),a.strict_visual)
 except (OSError,ValueError,KeyError) as exc:r={'passed':False,'errors':[str(exc)]}
 if a.out:a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({'passed':r['passed'],'scope':r.get('scope'),'errors':r['errors'],'advisories':r.get('advisories',[]),'visual_acceptance':r.get('visual_acceptance'),'visual_blockers':r.get('visual_blockers',[])},ensure_ascii=False,indent=2))
 if r.get('visual_acceptance'):print('视觉验收：'+r['visual_acceptance'],file=sys.stderr)
 return 0 if r['passed'] and not r.get('visual_blockers') else 1
if __name__=='__main__':raise SystemExit(main())
