from io_paths import asset_path
"""混合背景/无灰卡片/标题变化验收：使用成图像素与实际alpha，而非声明标签。"""
from pathlib import Path
from PIL import Image,ImageColor,ImageChops,ImageDraw,ImageOps
import numpy as np
import hashlib,json
from 保脸裁切 import local_faces
from render import processed_image,dark_backdrop,page_config,default_elements,resolved_font,watermark_layer,normalize_tone
LABELS={'black':'纯黑底','full-dark':'整版压暗图','full-bright':'整版亮图','black-big':'黑底＋半页以上大图','paper':'浅色／纸张底'}

def report_path(reports,n,pages_dir):
 r=next(v for v in reports if v['page']==n)
 return Path(r.get('output_file',pages_dir/f'p{n:02}.png'))

def visual_image(e,script,cfg):
 x,y,w,h=e['box']
 if e['kind']=='dark_backdrop':im,_=dark_backdrop(e,script.parent,1440,1920,cfg)
 else:im=processed_image(e,script.parent,(round(w*1440),round(h*1920)),cfg)
 a=im.getchannel('A').point(lambda v:255 if v>=128 else 0);bb=a.getbbox()
 bounds=[round(x*1440)+bb[0],round(y*1920)+bb[1],round(x*1440)+bb[2],round(y*1920)+bb[3]] if bb else None
 return im,a,bounds

def background_rules(data,reports,script,pages_dir):
 rows=[];errors=[];counts={k:0 for k in LABELS}
 for n,p in enumerate(data['pages'],1):
  if p['layout']=='cover':continue
  cfg=page_config(data.get('config',{}),p);es=p.get('elements',default_elements(p));r=next(v for v in reports if v['page']==n)
  with Image.open(report_path(reports,n,pages_dir)) as im:
   a=np.asarray(ImageOps.contain(im.convert('RGB'),(180,240),Image.Resampling.LANCZOS));bright=a.mean(axis=2)
  black=float((a.max(axis=2)<=8).mean());edge=np.concatenate([a[:3].reshape(-1,3),a[-3:].reshape(-1,3),a[:, :3].reshape(-1,3),a[:,-3:].reshape(-1,3)])
  edgeblack=float((edge.max(axis=1)<=8).mean());luma=float(bright.mean());paper_pixels=float(((a.min(axis=2)>140)&(a.max(axis=2)-a.min(axis=2)<60)).mean())
  full=[];big=[]
  for e in es:
   if e['kind'] not in ['image','dark_backdrop']:continue
   x,y,w,h=e['box']
   if e.get('role')=='background' and x<=.005 and y<=.005 and x+w>=.995 and y+h>=.995:
    _,mask,bb=visual_image(e,script,cfg);opaque=mask.histogram()[255]/(1440*1920)
    if opaque>=.98:full.append({'source_id':e['source_id'],'darken':e.get('darken',0),'opaque_area':opaque,'kind':e['kind']})
   if e.get('role')=='background' or e.get('major_image'):
    _,mask,bb=visual_image(e,script,cfg)
    if bb:
     area=(bb[2]-bb[0])*(bb[3]-bb[1])/(1440*1920);opaque=mask.histogram()[255]/(1440*1920)
     if area>=.5 and opaque>=.28:
      big.append({'source_id':e['source_id'],'actual_bounds':bb,'bounds_area':round(area,6),'opaque_area':round(opaque,6),'touches_frame':min(bb[0],bb[1],1440-bb[2],1920-bb[3])<=15,'torn':'torn' in e.get('effects',[]),'cutout':mask.histogram()[0]>0})
  bg=ImageColor.getrgb(p.get('background',cfg.get('background','#000000')));type_='black'
  if full:
   f=full[0];type_='full-dark' if f['darken']>=.30 else 'full-bright'
   if type_=='full-dark' and not .30<=f['darken']<=.70:errors.append(f'P{n:02}整版压暗强度不在30–70%（壁纸例外30–40%）')
  elif min(bg)>180 and paper_pixels>=.12 and luma>=90:type_='paper'
  elif max(bg)<=8 and big:type_='black-big'
  # 按真实像素排除伪装标签/深灰平底；黑底允许大量人物/文本覆盖。
  elif max(bg)>8:errors.append(f'P{n:02}背景既非黑底、整版图，也不满足纸张亮度证据')
  if type_=='black-big' and not any(v['touches_frame'] or v['torn'] or v['cutout'] for v in big):errors.append(f'P{n:02}大图未贴边、毛边或真实抠图')
  if type_=='paper':
   for e in es:
    if e['kind']=='text' and e.get('font','body')=='body' and max(ImageColor.getrgb(e.get('fill','#FFFFFF')))>85:errors.append(f'P{n:02}纸张底正文未用黑字')
  if type_=='full-bright':
   for e in es:
    if e['kind'] not in ['text','caption'] or not e.get('text'):continue
    # 亮图上的全部文字（含小注）须有紧贴文字的小贴条或3–5px描边/投影。
    # 浅篇允许小白/米白/青/黄色贴条；须按字宽逐行绘制，不能伪装成大面积卡片。
    light=normalize_tone(data.get('tone',cfg.get('tone','暗')))=='浅'
    strip=e.get('bg')
    light_strip=light and strip and min(ImageColor.getrgb(strip))>=120 and np.mean(ImageColor.getrgb(strip))>=190 and e.get('effect')!='3d' and e.get('lineheight',e.get('size',60)*1.36)<=e.get('size',60)*1.55
    if strip in ['#000000','#080808',cfg.get('accent')] or light_strip or (3<=e.get('stroke',0)<=5 and e.get('soft_shadow')):continue
    errors.append(f'P{n:02}亮图文字缺少贴条或3–5px粗描边与投影：{e["text"][:16]}')
  counts[type_]+=1;rows.append({'page':n,'background_type':type_,'label':LABELS[type_],'pure_black_ratio':round(black,6),'border_black_ratio':round(edgeblack,6),'mean_rgb_brightness':round(luma,3),'light_paper_pixel_ratio':round(paper_pixels,6),'full_image_evidence':full,'large_image_evidence':big,'rendered':str(report_path(reports,n,pages_dir))})
 longest=run=0
 for r in rows:
  run=run+1 if r['background_type']=='black' else 0;longest=max(longest,run)
 return {'passed':not errors,'measurement':{'size':[180,240],'resize':'LANCZOS','classification':'成图纯黑比例/四周3像素黑比例/平均RGB亮度＋重建实际图像alpha几何；full-page须98%实心覆盖；大图墨迹外接框≥50%且实心像素≥28%；标签不能代替证据。'},'counts':counts,'longest_black_run':longest,'quantity_policy':'建议，非硬门槛；暗色篇整版图片建议1–3页，也允许全篇黑底；档案不强制纸张底。','pages':rows,'errors':errors}

def tone_rules(data,reports,script,pages_dir,background=None):
 """篇级色调：可铺整版照片，不能用亮度均值把亮照片误判成浅色平涂页。"""
 tone=normalize_tone(data.get('tone',data.get('config',{}).get('tone','暗')));errors=[];rows=[]
 if tone not in ('暗','浅'):errors.append('篇级tone只能为暗/浅（支持dark/light别名）')
 background=background or background_rules(data,reports,script,pages_dir)
 classes={r['page']:r for r in background['pages']}
 is_light=lambda c:float(np.mean(c))>=160 and min(c)>=110
 for n,p in enumerate(data['pages'],1):
  cfg=page_config(data.get('config',{}),p);es=p.get('elements',default_elements(p));classification=classes.get(n)
  if normalize_tone(p.get('tone',tone))!=tone:errors.append(f'P{n:02}页面tone与整篇不一致')
  bg=ImageColor.getrgb(p.get('background',cfg.get('background','#000000')))
  if classification:
   kind=classification['background_type'];full=bool(classification['full_image_evidence'])
  else:
   # 封面同样检查；只在真正不透明的整版源图覆盖后才忽略底色。
   full=[]
   for e in es:
    if e['kind'] in ('image','dark_backdrop') and e.get('box')==[0,0,1,1]:
     _,mask,_=visual_image(e,script,cfg)
     if mask.histogram()[255]/(1440*1920)>=.98:full.append(e)
   kind=('full-dark' if full[-1].get('darken',0)>=.3 else 'full-bright') if full else ('paper' if is_light(bg) else 'black')
  with Image.open(report_path(reports,n,pages_dir)) as im:
   pixels=np.asarray(ImageOps.contain(im.convert('RGB'),(180,240),Image.Resampling.LANCZOS),dtype=float)
  flat=[]
  if not full and is_light(bg):flat.append({'kind':'background','color':list(bg)})
  for e in es:
   if e['kind']!='rect' or not e.get('fill'):continue
   c=ImageColor.getrgb(e['fill']);x,y,w,h=e['box']
   if is_light(c) and w*h>=.3:
    visible=float((np.linalg.norm(pixels-np.array(c),axis=2)<16).mean())
    if visible>=.12:flat.append({'kind':'rect','color':list(c),'visible_color_area':round(visible,6)})
  if tone=='暗' and (kind=='paper' or flat):errors.append(f'P{n:02}暗色篇出现浅色平涂／纸张底')
  if tone=='浅' and kind not in ('paper','full-bright'):errors.append(f'P{n:02}浅色篇出现{LABELS[kind]}，只允许浅色底或整版亮图')
  if tone=='浅':
   for e in es:
    if e['kind']=='text' and e.get('font','body') in ('body','serif-medium') and max(ImageColor.getrgb(e.get('fill','#FFFFFF')))>85:errors.append(f'P{n:02}浅色篇正文须黑字')
  rows.append({'page':n,'tone':tone,'background_type':kind,'full_image':bool(full),'light_flat_evidence':flat})
 return {'passed':not errors,'tone':tone,'defaulted':'tone' not in data and 'tone' not in data.get('config',{}),'measurement':'篇级声明＋成图背景分类/全幅alpha/可见浅色平涂几何；整版亮照片属于图像，暗色篇允许，不按全图平均亮度禁止。','pages':rows,'errors':errors}

def backdrop_rules(data,reports,script,pages_dir):
 rows=[];errors=[]
 for n,p in enumerate(data['pages'],1):
  if p['layout']=='cover':continue
  cfg=page_config(data.get('config',{}),p);es=p.get('elements',default_elements(p));texts=[e for e in es if e['kind']=='text' and e.get('text')];records=[]
  fullbright=any(e['kind']=='image' and e.get('role')=='background' and e['box']==[0,0,1,1] and e.get('darken',0)<.3 for e in es)
  for e in texts:
   # 底色文字（text_role=note，强调色逐行底条＋黑字）是允许的写法；其余灰底、白底、彩底块仍不允许
   if e.get('bg') and not fullbright and max(ImageColor.getrgb(e['bg']))>8 and not (e.get('text_role')=='note' and str(e['bg']).lower()==str(cfg.get('accent','')).lower()) and e.get('text_role')!='label':errors.append(f'P{n:02}非亮图文字平涂灰/彩底块：{e["text"][:15]}')
  for e in es:
   if e['kind']=='rect' and e.get('fill') and max(ImageColor.getrgb(e['fill']))>8:
    x,y,w,h=e['box']
    if any(min(x+w,t['box'][0]+t['box'][2])>max(x,t['box'][0]) and min(y+h,t['box'][1]+t['box'][3])>max(y,t['box'][1]) for t in texts):errors.append(f'P{n:02}硬边非黑矩形压在文字下面')
   if e['kind']=='dark_backdrop':
    try:
     im,rec=dark_backdrop(e,script.parent,1440,1920,cfg);records.append(rec)
     if not rec['full_page'] and (rec['top_bottom_alpha']!=[0,0] or rec['fade_fraction']<.25):errors.append(f'P{n:02}压暗底未实际渐变')
    except ValueError as err:errors.append(f'P{n:02} {err}')
   elif e['kind']=='image' and e.get('role')=='background' and e['box']!=[0,0,1,1]:
    x,y,w,h=e['box'];im,mask,_=visual_image(e,script,cfg);hard=float(np.mean(np.asarray(mask)[0]>128))>.85 and float(np.mean(np.asarray(mask)[-1]>128))>.85
    # 毛边、抠图本身不是悬浮硬矩形。检测相交文字实际框的面积>20%。
    if hard and not e.get('effects') and not e.get('mask'):
     for t in texts:
      a,b,u,v=t['box'];area=max(0,min(a+u,x+w)-max(a,x))*max(0,min(b+v,y+h)-max(b,y))
      if area/max(u*v,1e-9)>.2:errors.append(f'P{n:02}文字下面有硬边局部背景：{t["text"][:16]}');break
  rows.append({'page':n,'dark_backdrops':records})
 return {'passed':not errors,'pages':rows,'errors':errors}

def variation_rules(data,reports,script,pages_dir):
 errors=[];rows=[];sizes=[];top_left=middle=without_top=bigeyes=0
 for n,p in enumerate(data['pages'],1):
  if p['layout']=='cover':continue
  cfg=page_config(data.get('config',{}),p);es=p.get('elements',default_elements(p));r=next(v for v in reports if v['page']==n);brush=[];eye=[];small=0;discs=[]
  for e in es:
   if e['kind']=='text' and e.get('callout'):
    _,fi=resolved_font(e.get('font','body'),e.get('size',60),cfg)
    if 'MaShanZheng' in fi['path']:
     x,y,w,h=e['box'];brush.append({'text':e['text'],'box':e['box'],'size':e['size']});sizes.append(e['size'])
   if e['kind']=='image' and e.get('object_role')=='eye-miniature':
    _,_,bb=visual_image(e,script,cfg);width=(bb[2]-bb[0])/1440 if bb else 0
    eye.append({'source_id':e['source_id'],'actual_ink_width_ratio':round(width,6),'eye_count':e.get('eye_count'),'shadow':bool(e.get('soft_shadow'))})
    small+=width<.5
   if e['kind']=='disc_portrait':
    rec=next(v for v in r['components'] if v['kind']=='disc_portrait' and v['source_id']==e['source_id']);di=e['radius']*2/1440
    discs.append({'diameter_ratio':di,'visible_ratio':rec['disc_visible_ratio']})
    if not .30<=di<=.36 or rec['disc_visible_ratio']<.4:errors.append(f'P{n:02}圆盘尺寸/露出不合格')
  is_top=any(e['box'][1]<.17 and e['box'][0]<.5 for e in brush);is_mid=any(e['box'][1]>=.3 for e in brush)
  top_left+=is_top;middle+=is_mid;without_top+=not any(e['box'][1]<.17 for e in brush)
  bigeyes+=any(v['eye_count']==1 and v['actual_ink_width_ratio']>=.5 and v['shadow'] for v in eye)
  if small>2:errors.append(f'P{n:02}小器物{small}>2个')
  wm=r.get('watermark') or {}
  if wm.get('style')!='neutral' or wm.get('text')!=cfg.get('watermark_text',str(cfg.get('account_name','账号名')).replace('{','').replace('}','')) or wm.get('size',100)>26 or len(set(ImageColor.getrgb(wm.get('color','#FF0000'))))!=1:errors.append(f'P{n:02}预览水印不是灰色小字账号名')
  rows.append({'page':n,'brush_headlines':brush,'small_objects':small,'eye_objects':eye,'discs':discs,'neutral_watermark':wm})
 if top_left>5:errors.append(f'左上毛笔标题{top_left}>5页')
 if middle<2:errors.append('中下毛笔标题不足2页')
 if without_top<2:errors.append('无顶部毛笔标题不足2页')
 if not sizes or max(sizes)/min(sizes)>1.6 or len(set(sizes))<3:errors.append('毛笔字号须至少三档、跨度≤1.6倍')
 if data.get('config',{}).get('visual_revision_profile')=='eye-v2' and bigeyes<2:errors.append('单眼实物宽≥50%且带柔影的页不足2页')
 return {'passed':not errors,'summary':{'top_left_brush_pages':top_left,'middle_lower_brush_pages':middle,'without_top_brush_pages':without_top,'large_single_eye_pages':bigeyes,'brush_size_min_max':[min(sizes),max(sizes)] if sizes else None},'pages':rows,'errors':errors}

def geometry_rules(data,reports,script,pages_dir):
 """现稿读渲染器实际变换审计；旧稿无审计时复核脚本的等比运算，不冒充历史像素重渲染。"""
 from 图像等比 import ratio_audit,fit_geometry
 rows=[];errors=[]
 for n,p in enumerate(data['pages'],1):
  cfg=page_config(data.get('config',{}),p);transforms=[]
  record=next((r for r in reports if r.get('page')==n),{})
  output=Path(record.get('output_file',pages_dir/f'p{n:02}.png'))
  if output.exists():
   if record.get('sha256') and hashlib.sha256(output.read_bytes()).hexdigest()!=record['sha256']:errors.append(f'P{n:02}成图SHA与报告不一致')
   if record.get('page_script_sha256') and hashlib.sha256(json.dumps(p,ensure_ascii=False,sort_keys=True).encode()).hexdigest()!=record['page_script_sha256']:errors.append(f'P{n:02}渲染报告对应旧页面脚本')
   with Image.open(output) as im:
    if im.size!=(1440,1920):errors.append(f'P{n:02}成品尺寸{im.size}不等于1440×1920')
  for e in p.get('elements',default_elements(p)):
   if e['kind'] in ['image','dark_backdrop']:
    try:
     with Image.open(asset_path(script.parent,e['path'])) as im:
      size=im.size;transparent=im.mode=='RGBA' and im.getchannel('A').getextrema()[0]<255
     if data.get('config',{}).get('cover_only') and e.get('fit','contain')=='contain' and not transparent:errors.append(f'P{n:02}矩形照片使用contain留空边')
     if e.get('crop'):
      b=[round(v*(size[0] if i%2==0 else size[1])) for i,v in enumerate(e['crop'])];size=(b[2]-b[0],b[3]-b[1])
     x,y,w,h=e['box'];target=(round(w*1440),round(h*1920))
     if e.get('fit','contain')=='cover' or e['kind']=='dark_backdrop':
      t=fit_geometry(size,target,tuple(e.get('focus',[.5,.5])))
      with Image.open(asset_path(script.parent,e['path'])) as im:original=im.size
      faces,_=local_faces(e,original,size);x0,y0,x1,y1=t['source_crop_box']
      for f in faces:
       a,b,c,d=f['box'];inter=max(0,min(c,x1)-max(a,x0))*max(0,min(d,y1)-max(b,y0))
       if inter and not (a>=x0-.01 and b>=y0-.01 and c<=x1+.01 and d<=y1+.01):errors.append(f'P{n:02}当前focus截断Vision人脸框#{f["id"]}')
     else:
      q=ImageOps.contain(Image.new('L',size),target);t=ratio_audit(size,q.size,'contain',frame_size=list(target))
     transforms.append({'source':e['path'],**t})
    except (ValueError,OSError,KeyError) as exc:errors.append(f'P{n:02}图片几何：{exc}')
   elif e['kind']=='disc_portrait':
    try:
     with Image.open(asset_path(script.parent,e['cutout_path'])) as im:
      bb=im.getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox();size=(bb[2]-bb[0],bb[3]-bb[1])
     vertical=e.get('breakout_direction','top') in ['top','bottom'];dim=2*round(e.get('portrait_radius',e['radius']))+round(e.get('breakout',100));scale=dim/size[1 if vertical else 0]
     target=tuple(round(v*scale) for v in size);transforms.append({'source':e['cutout_path'],**ratio_audit(size,target,'disc-portrait-contain')})
    except (ValueError,OSError,KeyError) as exc:errors.append(f'P{n:02}圆盘人物几何：{exc}')
  rec=next((r for r in reports if r.get('page')==n),{});actual=rec.get('image_transforms',[])
  for t in actual:
   if t.get('face_check',{}).get('partial_face_ids'):errors.append(f'P{n:02}裁切截断人脸框')
   if not all(v.get('complete',True) for v in t.get('face_check',{}).get('faces',[])):errors.append(f'P{n:02}圆盘裁切截脸')
   try:ratio_audit(t['source_region_size'],t['resized_size'],t['method'])
   except ValueError as exc:errors.append(f'P{n:02}成图审计：{exc}')
  if actual and len(actual)!=len(transforms):errors.append(f'P{n:02}成图图片变换审计条数不一致')
  rows.append({'page':n,'transforms':actual or transforms,'audit_basis':'renderer-actual' if actual else 'legacy-script-geometry','rendered_transform_count':len(actual)})
 return {'passed':not errors,'max_aspect_error_ratio':max((t.get('aspect_error_ratio',abs((t['resized_size'][0]/t['resized_size'][1])/(t['source_region_size'][0]/t['source_region_size'][1])-1)) for r in rows for t in r['transforms']),default=0),'measurement':'容差1%；contain比较实际缩放尺寸；cover比较裁切区域与成图尺寸；圆盘比较等比人物缩放前后，圆形遮罩/旋转/遮挡不当作拉伸。','pages':rows,'errors':errors}
