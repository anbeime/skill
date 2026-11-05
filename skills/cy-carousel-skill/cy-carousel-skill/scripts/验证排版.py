from io_paths import asset_path
"""共同基线、图层、人物碰撞及v2图像密度/原图复用检查。
python3 scripts/验证排版.py
python3 scripts/验证排版.py 页面脚本.json --report pages/render-report.json
"""
from pathlib import Path
from collections import Counter
import argparse,tempfile,json
from PIL import Image,ImageColor,ImageDraw,ImageChops,ImageOps
import numpy as np
from render import render,draw_text,font,default_elements,processed_image,page_config,disc_portrait,muted_accent,watermark_layer,normalize_tone

def colorfulness(image):
 a=np.asarray(ImageOps.contain(image.convert('RGB'),(360,480),Image.Resampling.LANCZOS),dtype=np.float64)
 r,g,b=a.transpose(2,0,1);rg=np.abs(r-g);yb=np.abs(.5*(r+g)-b)
 return float(np.hypot(rg.std(),yb.std())+.3*np.hypot(rg.mean(),yb.mean()))

def watermark_rules(data):
 """复建真实署名alpha与文字alpha，检查字形碰撞；不拿空文本框代替墨迹。"""
 errors=[];hits=[]
 for n,p in enumerate(data['pages'],1):
  if not p.get('watermark',True):continue
  cfg=page_config(data.get('config',{}),p)
  layer,_=watermark_layer(cfg,1440,1920);mask=layer.getchannel('A').point(lambda a:255 if a>=64 else 0)
  for e in p.get('elements',[]):
   if e['kind'] not in ['text','caption']:continue
   e={**e};e.pop('bg',None)
   if e['kind']=='caption':e={'size':28,'font':'sans','spacing':0,'lineheight':36,**e}
   ink=Image.new('RGBA',(1440,1920));draw_text(ink,e,cfg,1440,1920,[])
   overlap=ImageChops.multiply(ink.getchannel('A').point(lambda a:255 if a>=128 else 0),mask).histogram()[255]
   if overlap: hits.append({'page':n,'text':e['text'],'actual_ink_overlap_pixels':overlap});errors.append(f'P{n:02}署名覆盖文字墨迹：{e["text"][:20]}')
 return {'passed':not errors,'collisions':hits,'errors':errors}

def color_hierarchy_rules(data,reports,script,pages_dir):
 """现行面积口径：全图RGB欧氏距<70；浅色档案去中性灰；每页0–3%，无下限。"""
 import re
 errors=[];rows=[];all_large=[];secondary_uses=[]
 for number,p in enumerate(data['pages'],1):
  if p['layout']=='cover':continue
  cfg=page_config(data.get('config',{}),p);primary=cfg['accent'];second=cfg.get('secondary_accent','#FF4D4D')
  record=next((r for r in reports if r.get('page')==number),{})
  rendered=Path(record.get('output_file',pages_dir/f'p{number:02}.png'))
  with Image.open(rendered) as image:
   a=np.asarray(ImageOps.contain(image.convert('RGB'),(360,480),Image.Resampling.LANCZOS),dtype=float)
  ratio=lambda color:float(np.mean(np.linalg.norm(a-np.array(ImageColor.getrgb(color)),axis=2)<70))
  area=ratio(primary);second_area=ratio(second);groups=[];keywords=[];large=[];second_items=[]
  elements=p.get('elements',default_elements(p))
  body=max((e.get('size',60) for e in elements if e['kind']=='text' and e.get('font','body')=='body'),default=p.get('body_size',58))
  for i,e in enumerate(elements):
   kind=e['kind'];fill=e.get('fill') or '#FFFFFF';accent=e.get('accent') or primary
   if kind=='text' and e.get('text'):
    marked=re.findall(r'\[\[(.*?)\]\]',e['text'],re.S)
    if fill.lower()==primary.lower():groups.append({'element':i,'type':'text','text':e['text']})
    elif marked and accent.lower()==primary.lower():keywords.extend({'element':i,'text':v} for v in marked)
    if fill.lower()==second.lower() or (marked and accent.lower()==second.lower()):
     second_items.append({'element':i,'text':e['text']});secondary_uses.append({'page':number,'element':i})
    if marked and fill.lower() in [primary.lower(),second.lower()] and accent.lower() in [primary.lower(),second.lower()] and fill.lower()!=accent.lower():
     errors.append(f'P{number:02}同一文字元素混用主强调色与第二色')
    if e.get('callout'):
     item={'element':i,'text':e['text'],'fill':fill,'font':e.get('font'),'white':fill.upper() in ['#FFFFFF','#E6E6E6','#EEEEEE'],'primary':fill.lower()==primary.lower(),'size':e['size'],'italic':e.get('italic',0)}
     large.append(item);all_large.append(item)
   elif kind in ['arrow','rect','ellipse'] and fill.lower()==primary.lower():groups.append({'element':i,'type':kind})
   elif kind=='disc_portrait' and np.linalg.norm(np.array(ImageColor.getrgb(e.get('disc_color',primary)))-np.array(ImageColor.getrgb(primary)))<70:groups.append({'element':i,'type':'disc_portrait'})
  if keywords:groups.append({'type':'keyword_group','keywords':keywords})
  palette=[e.get('fill','#C92928') for e in elements if e['kind'] in ['hand_circle','hand_underline']]+[primary]+([second] if second_items else [])+[e.get('disc_color') or muted_accent(primary) for e in elements if e['kind']=='disc_portrait']
  palette=list(dict.fromkeys(palette));masks=[np.linalg.norm(a-np.array(ImageColor.getrgb(c)),axis=2)<70 for c in palette];legacy_union=float(np.logical_or.reduce(masks).mean())
  # 深色浅篇：RGB近邻会把黑白史料灰阶算成深强调色，另保留原口径并按色度去除中性灰。
  light=normalize_tone(data.get('tone',cfg.get('tone','暗')))=='浅'
  if light:
   spread=a.max(axis=2)-a.min(axis=2)
   masks=[m & (spread>=max(22,(max(ImageColor.getrgb(c))-min(ImageColor.getrgb(c)))*.45)) for m,c in zip(masks,palette)]
  union=float(np.logical_or.reduce(masks).mean())
  if not 0<=union<=.030:errors.append(f'P{number:02}全部设计强调色并集面积{union:.3%}超过3.0%上限')
  rows.append({'page':number,'primary_area_ratio':round(area,6),'legacy_rgb_union_area_ratio':round(legacy_union,6),'accent_union_area_ratio':round(union,6),'measured_palette':palette,'light_chroma_filter':light,'primary_elements':len(groups),'primary_groups':groups,'keyword_count':len(keywords),'secondary_area_ratio':round(second_area,6),'secondary_uses':second_items,'large_sentences':large})
 rawmean=sum(r['primary_area_ratio'] for r in rows)/max(1,len(rows));mean=sum(r['accent_union_area_ratio'] for r in rows)/max(1,len(rows));white=sum(v['white'] for v in all_large);colored=sum(v['primary'] for v in all_large)
 if len(secondary_uses)>2:errors.append(f'第二色重音{len(secondary_uses)}>2处')
 return {'passed':not errors,'measurement':{'size':[360,480],'resize':'LANCZOS','distance':'各页实际使用的设计色：主强调色+圆盘柔和色+该页确实使用的第二色，分别RGB欧氏距<70，像素并集去重；全图测量包含图片/箭头/边框/水印。primary_area_ratio另保留只测主色的原口径，未删除。浅篇另外加色度筛选：max(RGB)-min(RGB)>=max(22,设计色通道差×0.45)，避免把灰阶档案当深色强调；legacy_rgb_union_area_ratio保留未筛旧口径，不能跨口径比较。','elements':'固定账号署名仅计面积，不计叙事重音；叙事重音按大字交替与正文关键词≤1检查'},'summary':{'primary_area_mean':round(rawmean,6),'accent_union_area_mean':round(mean,6),'large_sentences':len(all_large),'white_large_sentences':white,'primary_large_sentences':colored,'secondary_uses':len(secondary_uses)},'pages':rows,'errors':errors}

def alternation_rules(data,reports,script,pages_dir):
 """v7.4：按实际大字框的纵向顺序，彩色/白色交替；实际彩色字形与装饰上下呼应。"""
 import re
 base=color_hierarchy_rules(data,reports,script,pages_dir)
 errors=list(base['errors'])
 mean=base['summary']['accent_union_area_mean']
 if not .012<=mean<=.020:errors.append(f'全篇强调色均值{mean:.3%}不在1.2–2.0%')
 rows=[]
 for n,p in enumerate(data['pages'],1):
  if p['layout']=='cover':continue
  cfg=page_config(data.get('config',{}),p);accent=cfg['accent'].lower();second=cfg.get('secondary_accent','#FF4D4D').lower();es=p.get('elements',default_elements(p))
  body=max((e.get('size',60) for e in es if e['kind']=='text' and e.get('font','body')=='body'),default=58)
  rs=next(r for r in reports if r['page']==n);large=[];zones={'upper':[],'lower':[]};keyword_count=0
  def zone(bounds,label):
   if bounds[1]<1920/3:zones['upper'].append(label)
   if bounds[3]>1920*2/3:zones['lower'].append(label)
  for i,e in enumerate(es):
   kind=e['kind'];fill=(e.get('fill') or '#FFFFFF').lower()
   if kind=='text' and e.get('text'):
    if e.get('callout') or e.get('text_role')=='heading' or e.get('evidence_numbers'):
     color='green/accent' if fill==accent else 'red/secondary' if fill==second else 'white'
     light_tone=normalize_tone(data.get('tone',cfg.get('tone')))=='浅' or p.get('paper_texture')
     if not light_tone and not e.get('evidence_numbers'):
      name=e.get('font','body')
      if color=='green/accent' and name not in ('headline','cover-title','heading','brush','display'):errors.append(f'P{n:02}强调色大字未用标题字体')
      if color=='white' and name!='serif-bold':errors.append(f'P{n:02}白色大字未用宋体700')
      if color=='red/secondary' and name!='serif-bold':errors.append(f'P{n:02}红色关键句未用宋体700')
     large.append({'element':i,'y':e['box'][1],'text':e['text'],'color':color,'class':'white' if color=='white' else 'colored','neutral_label':'black/light-tone' if light_tone and color=='white' else 'white','font':e.get('font'),'size':e.get('size',60)})
    marked=re.findall(r'\[\[(.*?)\]\]',e['text'],re.S)
    if fill not in [accent,second] and (e.get('accent',cfg['accent']).lower()==accent):
     keywords=[v for v in marked if v not in e.get('colored_sentences',[])]
     keyword_count+=len(keywords)
     for text in keywords:
      for other in es:
       if other is e or other['kind']!='text' or not (other.get('callout') or other.get('text_role')=='heading') or other.get('fill','').lower()!=accent:continue
       a,b,w,h=e['box'];c,d,u,v=other['box'];horizontal=min(a+w,c+u)-max(a,c)
       gap=max(b-(d+v),d-(b+h),0)*1920
       if horizontal>0 and gap<max(1,e.get('lineheight',78)):errors.append(f'P{n:02}绿色关键词紧挨绿色大字：{text}')
    record=next((r for r in rs['text'] if r.get('text')==e['text'] and r.get('box')==e['box']),{})
    for g in record.get('glyphs',[]):
     if g.get('ink_bounds') and g.get('fill','').lower() in [accent,second]:zone(g['ink_bounds'],{'element':i,'kind':'glyph','char':g['char']})
   elif kind in ['hand_circle','hand_underline']:
    record=next((v for v in rs['components'] if v['kind']==kind and v.get('target_text')==e.get('target_text')),{})
    if record.get('ink_bounds'):zone(record['ink_bounds'],{'element':i,'kind':kind})
   elif kind=='disc_portrait':
    cx,cy=e['center'];r=e['radius'];zone([cx*1440-r,cy*1920-r,cx*1440+r,cy*1920+r],{'element':i,'kind':'muted_disc'})
   elif kind=='arrow' and fill in [accent,second]:
    xy=e['points'];zone([min(x[0] for x in xy)*1440,min(x[1] for x in xy)*1920,max(x[0] for x in xy)*1440,max(x[1] for x in xy)*1920],{'element':i,'kind':'arrow'})
  large.sort(key=lambda v:v['y'])
  for a,b in zip(large,large[1:]):
   if a['class']==b['class']:errors.append(f'P{n:02}相邻大字同类颜色：{a["text"]} / {b["text"]}')
  if len(large)==1 and large[0]['class']=='white':errors.append(f'P{n:02}唯一大字未用强调色')
  if keyword_count>1:errors.append(f'P{n:02}正文绿色关键词{keyword_count}>1')
  if not zones['upper']:errors.append(f'P{n:02}上1/3缺少强调色')
  if not zones['lower']:errors.append(f'P{n:02}下1/3缺少强调色')
  rows.append({'page':n,'large_order':large,'upper_accent':bool(zones['upper']),'lower_accent':bool(zones['lower']),'accent_zone_elements':zones,'body_accent_keywords':keyword_count})
 base.update(profile='v7.4-alternation',passed=not errors,errors=errors,alternation_pages=rows)
 return base

def richness_rules(data,reports,script,pages_dir):
 """v7防单调：成图颜色/黑像素与真实人物alpha；语义人脸经逐张人工确认。"""
 errors=[];usage=Counter();rows=[];hine_pages=set();previous=None
 light_editorial=data.get('config',{}).get('visual_revision_profile')=='light-editorial-v2'
 for number,p in enumerate(data['pages'],1):
  elements=p.get('elements',default_elements(p));cfg=page_config(data.get('config',{}),p)
  for e in elements:
   if e['kind'] in ['image','dark_backdrop','disc_portrait']:
    identity=e.get('source_id',e.get('path',e.get('cutout_path')));usage[identity]+=1
    if identity.startswith('HINE-'):hine_pages.add(number)
  if p['layout']=='cover':continue
  record=next((r for r in reports if r.get('page')==number),{})
  rendered=Path(record.get('output_file',pages_dir/f'p{number:02}.png'))
  with Image.open(rendered) as image:
   arr=np.asarray(ImageOps.contain(image.convert('RGB'),(360,480),Image.Resampling.LANCZOS))
   black=float(np.mean(arr.max(axis=2)<=8));exact=float(np.mean(arr.max(axis=2)==0));cf=colorfulness(image)
  W,H=1440,1920;heroes=[];rectangles=0;colored=[];backgrounds=[];circles=0
  for e in elements:
   if e['kind']=='ellipse' and e.get('circle_backdrop'):circles+=1
   if e['kind'] not in ['image','dark_backdrop','disc_portrait']:continue
   if e['kind']=='disc_portrait':
    _,mask,_,details=disc_portrait(e,script.parent,W,H,cfg);box=mask.getbbox();circles+=1
    if e.get('color_source'):colored.append(e['source_id'])
    heroes.append({'source_id':e['source_id'],'face_verified':e.get('face_verified',False),
     'height_ratio':round((box[3]-box[1])/H,6),'opaque_area_ratio':round(mask.histogram()[255]/(W*H),6),
     'form':'cutout','has_transparency':True,'disc_portrait':True,'face_review':e.get('face_review'),
     'method':'disc_portrait实际人物alpha>=128，不以圆盘或透明框计算人物高度',
     'outside_disc_pixels':details['actual_outside_pixels'],'disc_visible_ratio':details['disc_visible_ratio'],
     'disc_total_pixels':details['disc_total_pixels'],'disc_visible_pixels':details['disc_visible_pixels']})
    if details['disc_visible_ratio']<.40:errors.append(f'P{number:02} 圆盘可见面积{details["disc_visible_ratio"]:.1%}<40%')
    continue
   if e.get('color_source'):colored.append(e['source_id'])
   if e.get('role')=='background' and (e.get('darken',0)>=.35 or data.get('config',{}).get('background_profile')=='mixed-v2'):backgrounds.append(e)
   path=asset_path(script.parent,e['path'])
   with Image.open(path) as original:
    transparent=original.mode=='RGBA' and original.getchannel('A').getextrema()[0]<255
   circle='circle' in e.get('effects',[])
   if e['kind']!='dark_backdrop' and e['box']!=[0,0,1,1] and not transparent and not circle and not e.get('mask'):rectangles+=1
   if not e.get('hero'):continue
   subject={**e};subject.pop('outline',None)
   if e.get('subject_mask'):subject['mask']=e['subject_mask']
   x,y,w,h=e['box'];im=processed_image(subject,script.parent,(round(w*W),round(h*H)),cfg)
   mask=im.getchannel('A').point(lambda a:255 if a>=128 else 0);box=mask.getbbox()
   if box:
    height=(box[3]-box[1])/H;area=mask.histogram()[255]/(W*H)
   else:height=area=0
   heroes.append({'source_id':e['source_id'],'face_verified':e.get('face_verified',False),
                  'height_ratio':round(height,6),'opaque_area_ratio':round(area,6),'form':e.get('hero_form'),
                  'has_transparency':transparent,'face_review':e.get('face_review'),
                  'method':'人物mask实际alpha>=128边界，不按空画框；圆像采用独立人物mask'})
  body=[e.get('size',60) for e in elements if e['kind']=='text' and e.get('font','body')=='body' and e.get('text')]
  body_size=max(body,default=p.get('body_size',58))
  callouts=[{'text':e['text'],'size':e.get('size',60),'ratio_to_body':round(e.get('size',60)/body_size,3),
             'middle_or_lower':e['box'][1]>=.35,'font':e.get('font')} for e in elements
            if e['kind']=='text' and e.get('callout') and e.get('size',60)>=body_size*1.6]
  overlay=[]
  for e in elements:
   if e['kind']!='text' or not (e.get('text_overlay') or data.get('config',{}).get('background_profile')=='mixed-v2'):continue
   a,b,w,h=e['box'];area=w*h
   for bg in backgrounds:
    c,d,u,v=bg['box'];overlap=max(0,min(a+w,c+u)-max(a,c))*max(0,min(b+h,d+v)-max(b,d))
    if overlap/max(area,1e-9)>=.20:overlay.append(e['text']);break
  skeleton=p.get('skeleton');position=p.get('text_position')
  if not skeleton or not position:errors.append(f'P{number:02}缺少骨架/文字位置记录')
  if skeleton and skeleton==previous:errors.append(f'P{number:02}与前页骨架相同')
  previous=skeleton
  if not light_editorial and rectangles>2:errors.append(f'P{number:02}矩形照片{rectangles}>2')
  if not p.get('visual_focus'):errors.append(f'P{number:02}未指定单一视觉焦点')
  rows.append({'page':number,'hero':heroes,'colorfulness':round(cf,3),'pure_black_ratio':round(black,6),
               'exact_zero_black_ratio':round(exact,6),'colored_source_ids':colored,'rectangular_images':rectangles,
               'skeleton':skeleton,'text_position':position,'body_size':body_size,'callouts':callouts,
               'text_on_dark_background':overlay,'accent_circle_portrait':bool(circles and any(v['form']=='circle' or v.get('disc_portrait') for v in heroes))})
 qualifying=lambda v:v['face_verified'] and v['height_ratio']>=.35
 detail_context=[]
 if data.get('config',{}).get('require_face_every_page'):
  for r in rows:
   if any(qualifying(h) for h in r['hero']):continue
   p=data['pages'][r['page']-1];exception=p.get('face_height_exception',{})
   minimum=exception.get('context_minimum',.35)
   # 仅明确要求“动作特写＋小全景”的页面采用有理由的局部例外，默认门槛仍35%。
   context=[e for e in p.get('elements',[]) if e.get('photo_role')=='context' and e.get('face_verified') and e.get('face_boxes')]
   allowed=(p.get('detail_focus')=='gesture-close-up' and bool(exception.get('user_instruction')) and
            isinstance(minimum,(int,float)) and .10<=minimum<.35 and bool(context) and
            any(h['face_verified'] and h['height_ratio']>=minimum for h in r['hero']))
   if allowed:detail_context.append({'page':r['page'],'minimum':minimum,'actual_context_height':max(h['height_ratio'] for h in r['hero'] if h['face_verified']),'reason':exception['user_instruction']})
   else:errors.append(f'P{r["page"]:02}缺少经目检且实际高度≥35%的带脸人物')
 face_pages=sum(any(qualifying(h) for h in r['hero']) for r in rows)
 cutout_pages=sum(any(qualifying(h) and h['form']=='cutout' and h['has_transparency'] for h in r['hero']) for r in rows)
 colorful_pages=sum(bool(r['colored_source_ids']) for r in rows);mean=sum(r['colorfulness'] for r in rows)/max(1,len(rows))
 emphasized=sum(bool(r['callouts']) for r in rows);lower=sum(any(e['middle_or_lower'] for e in r['callouts']) for r in rows)
 on_image=sum(bool(r['text_on_dark_background']) for r in rows);circle_pages=sum(r['accent_circle_portrait'] for r in rows)
 archival=normalize_tone(data.get('tone',data.get('config',{}).get('tone')))=='浅' and data.get('config',{}).get('source_palette')=='archival-monochrome'
 for condition,msg in [(face_pages>=7,'有脸且高≥35%的主角页不足7'),(light_editorial or cutout_pages>=5,'主角抠图页不足5'),
                       (archival or mean>=33,'色彩丰富度均值不足33'),(archival or colorful_pages>=5,'彩色图源页不足5'),
                       (emphasized>=7,'≥1.6倍正文的大字页不足7'),(lower>=3,'中下部大字页不足3'),
                       (on_image>=3,'图底压文字页不足3（mixed包含亮图）'),(light_editorial or circle_pages>=2,'强调色圆底肖像页不足2'),
                       (len(usage)>=15,'不同原图不足15')]:
  if not condition:errors.append(msg)
 errors.extend(f'原图{key}复用{n}>2' for key,n in usage.items() if n>2)
 wm=watermark_rules(data) if data.get('config',{}).get('avoid_watermark_overlap') else None
 if wm:errors.extend(wm['errors'])
 summary={'source_palette_policy':'浅色黑白档案：保留原色，色彩统计记录不设33硬下限' if archival else '常规彩色图源≥5、色彩丰富度≥33','face_pages':face_pages,'cutout_pages':cutout_pages,'colorfulness_mean':round(mean,3),
          'colored_source_pages':colorful_pages,'callout_pages':emphasized,'middle_lower_callout_pages':lower,
          'text_on_dark_background_pages':on_image,'accent_circle_portrait_pages':circle_pages,
          'hine_pages':sorted(hine_pages),'unique_sources':len(usage),'source_usage':dict(usage),'user_requested_detail_context_pages':detail_context}
 return {'profile':'v7-richness','passed':not errors,'measurement':{'size':[360,480],'resize':'LANCZOS',
         'colorfulness':'Hasler–Süsstrunk: sqrt(std(|R-G|)^2+std(|(R+G)/2-B|)^2)+0.3*sqrt(mean_rg^2+mean_yb^2)',
         'pure_black':'成图RGB各通道<=8；另列严格RGB=0占比；含文字/阴影、拒绝暗图充作留白',
         'face':'人工核对人脸，不宣称自动人脸识别；人物高度及面积用实际独立alpha mask测量'},
         'summary':summary,'pages':rows,'watermark_check':wm,'errors':errors}

def image_rules(data,reports,minimum_sources=15,maximum_reuse=2):
 errors=[];usage=Counter()
 if len(data['pages'])!=len(reports):errors.append('脚本与渲染报告页数不一致')
 for i,p in enumerate(data['pages'],1):
  images=[e for e in p.get('elements',default_elements(p)) if e['kind']=='image']
  for e in images:
   if not e.get('source_id'):errors.append(f'P{i:02} 图片缺少原图source_id：{e["path"]}')
   usage[e.get('source_id',e['path'])]+=1
  if i<=len(reports) and p['layout']!='cover':
   report=reports[i-1]
   if report.get('image_elements',0)<2:errors.append(f'P{i:02} 可见图像元素少于2个')
   if report.get('image_area_ratio',0)<.40:errors.append(f'P{i:02} 图片面积 {report.get("image_area_ratio",0):.1%}<40%')
 if len(usage)<minimum_sources:errors.append(f'不同原图 {len(usage)}<{minimum_sources}')
 errors.extend(f'原图 {key} 复用 {count}>{maximum_reuse}' for key,count in usage.items() if count>maximum_reuse)
 return {'passed':not errors,'unique_sources':len(usage),'source_usage':dict(usage),
 'area_method':'实际alpha>=128像素并集；重叠不重复累加；透明边缘与opacity<=0.25氛围层不计',
 'pages':[{'page':r['page'],'images':r.get('image_elements'),'image_area_ratio':r.get('image_area_ratio')} for r in reports],'errors':errors}

def regression():
 cfg={'accent':'#24FE00'};assert font('serif-medium',64,cfg).getmetrics()[0]>0
 with tempfile.TemporaryDirectory() as td:
  root=Path(td);im=Image.new('RGBA',(100,100),(255,0,0,255));im.putpixel((0,0),(0,0,0,0));im.save(root/'person.png')
  page={'layout':'story','watermark':False,'elements':[{'kind':'text','text':'甲，乙。——丙…丁·戊','box':[.05,.05,.8,.1],'size':60},{'kind':'image','path':'person.png','source_id':'original-person','box':[.05,.05,.8,.8],'role':'foreground','fit':'cover'}]}
  script=root/'test.json';script.write_text(json.dumps({'pages':[page]}),encoding='utf-8')
  try:render(script,root/'bad')
  except ValueError as err:assert '碰撞' in str(err)
  else:raise AssertionError('碰撞未拒绝')
  print('PASS: >3%抠图碰撞被拒绝')
  page['elements'][1]['role']='background';page['elements'].append({**page['elements'][1],'crop':[0,0,.9,.9]})
  script.write_text(json.dumps({'pages':[page]}),encoding='utf-8');reports=render(script,root/'ok');out=Image.open(root/'ok/p01.png')
  assert sum(min(px)>230 for px in out.crop((72,96,500,230)).getdata())>100
  assert .639<reports[0]['image_area_ratio']<.641
  print('PASS: 文字在图片上层；图片重叠按像素并集计面积')
  result=image_rules({'pages':[page]},reports,minimum_sources=1,maximum_reuse=1)
  assert result['unique_sources']==1 and any('复用 2>1' in e for e in result['errors'])
  print('PASS: 同图不同裁切计入复用次数')
  canvas=Image.new('RGBA',(1440,1920));draw_text(canvas,{'text':'，。','box':[0,0,.4,.1],'size':64,'spacing':0},cfg,1440,1920,[])
  assert canvas.getchannel('A').getbbox()[1]>64*.65
  print('PASS: 标点共同基线，未上浮')
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('script',type=Path,nargs='?');ap.add_argument('--report',type=Path);ap.add_argument('--out',type=Path);ap.add_argument('--pages',type=Path);ap.add_argument('--assets-root',type=Path);a=ap.parse_args()
 if not a.script:regression()
 else:
  from check_all import check_note
  r=check_note(a.script,a.pages or a.report.parent,a.report,a.assets_root)
  if a.out:a.out.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
  print(json.dumps(r,ensure_ascii=False,indent=2));raise SystemExit(0 if r['passed'] else 1)
