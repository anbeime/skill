#!/usr/bin/env python3
"""1440x1920, JSON page script -> PNG. Coordinates normalized, text stays editable."""
from io_paths import asset_path
from PIL import Image,ImageDraw,ImageFont,ImageOps,ImageEnhance,ImageFilter,ImageChops
from pathlib import Path
from 图像等比 import ratio_audit,fit_geometry
from 保脸裁切 import local_faces,safe_focus
import argparse,json,re,math,random,hashlib,warnings,colorsys
import numpy as np
FONT_ROOT=Path(__file__).resolve().parents[1]/'assets/fonts'
SKILL_ROOT=Path(__file__).resolve().parents[1]
TITLE_FONT_KEYS={'headline','cover-title','heading'}
def normalize_tone(value):
 return {'light':'浅','dark':'暗','浅':'浅','暗':'暗'}.get(value,value)
PUNCTUATION=set('“”‘’。，、？！…：:；;!?.,「」『』《》（）()——·')
CLOSING_PUNCTUATION=set('”’。，、？！…：:；;!?.,」』》）)·—')
FONTS={
 'body':(FONT_ROOT/'NotoSerifSC[wght].ttf',0,500),
 'bold':(FONT_ROOT/'NotoSerifSC[wght].ttf',0,600),
 'serif-regular':(FONT_ROOT/'NotoSerifSC[wght].ttf',0,400),
 'serif-medium':(FONT_ROOT/'NotoSerifSC[wght].ttf',0,500),
 'serif-semibold':(FONT_ROOT/'NotoSerifSC[wght].ttf',0,600),
 'serif-black':(FONT_ROOT/'NotoSerifSC[wght].ttf',0,900),
 'headline':(FONT_ROOT/'MaShanZheng-Regular.ttf',0,None),
 'cover-title':(FONT_ROOT/'MaShanZheng-Regular.ttf',0,None),
 'heading':(FONT_ROOT/'MaShanZheng-Regular.ttf',0,None),
 'serif-bold':(FONT_ROOT/'NotoSerifSC[wght].ttf',0,700),
 'sans':(FONT_ROOT/'NotoSansSC[wght].ttf',0,900),
 'sans-black':(FONT_ROOT/'NotoSansSC[wght].ttf',0,900),
 'sans-bold':(FONT_ROOT/'NotoSansSC[wght].ttf',0,700),
 'display':(FONT_ROOT/'MaShanZheng-Regular.ttf',0,None),
 'brush':(FONT_ROOT/'MaShanZheng-Regular.ttf',0,None),
 'signature':(FONT_ROOT/'NotoSerifSC[wght].ttf',0,400),
 'songti':(FONT_ROOT/'NotoSerifSC[wght].ttf',0,700),
 # 标题展示字体：默认思源黑体 Heavy；内容.json 写 title_font 时换成那个字库（如阿里妈妈数黑体）
 'title-display':(FONT_ROOT/'NotoSansSC[wght].ttf',0,900),
 # 封面两行：思源宋体 Black（最接近原版封面的宋黑融合字）
 'cover-display':(FONT_ROOT/'NotoSerifSC[wght].ttf',0,900)}
# 正文候选字体（按题材选，一篇只用一款）：用到时才去本机/assets/fonts 里找，找不到直接报错，不静默回退。
# 每项：[(文件 glob, 期望 (family, style) 或 None)]，ttc 按名字找 index。
_SYS_ASSET='/System/Library/AssetsV2/com_apple_MobileAsset_Font*/*/AssetData/'
SYSTEM_FONTS={
 'songti-sc':[('/System/Library/Fonts/Supplemental/Songti.ttc',('Songti SC','Regular'))],
 'songti-sc-bold':[('/System/Library/Fonts/Supplemental/Songti.ttc',('Songti SC','Bold'))],
 'fangsong':[(_SYS_ASSET+'STFANGSO.ttf',('STFangsong','Regular')),(str(Path.home()/'Library/Fonts/STFANGSO.ttf'),None)],
 'kaiti':[(_SYS_ASSET+'Kaiti.ttc',('Kaiti SC','Regular'))],
 'wenkai':[(str(FONT_ROOT/'LXGWWenKai-Medium.ttf'),None),(str(Path.home()/'Library/Fonts/LXGWWenKai-Medium.ttf'),None),('/Library/Fonts/LXGWWenKai-Medium.ttf',None)],
 'pingfang-light':[(_SYS_ASSET+'PingFang.ttc',('PingFang SC','Light'))],
 'pingfang':[(_SYS_ASSET+'PingFang.ttc',('PingFang SC','Regular'))],
 'pingfang-semibold':[(_SYS_ASSET+'PingFang.ttc',('PingFang SC','Semibold'))],
 'serif-latin':[('/System/Library/Fonts/Supplemental/Times New Roman.ttf',None)],
 'serif-latin-bold':[('/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf',None)]}
def find_system_font(name):
 import glob
 for pattern,want in SYSTEM_FONTS[name]:
  for path in sorted(glob.glob(pattern)):
   if want is None:return (Path(path),0,None)
   for i in range(64):
    try:f=ImageFont.truetype(path,20,index=i)
    except OSError:break
    if f.getname()==want:return (Path(path),i,None)
 raise FileNotFoundError(f'找不到正文字体 {name}：{[p for p,_ in SYSTEM_FONTS[name]]}。换一款字体，或把字库（如 LXGW WenKai，OFL）放进 assets/fonts/')
# 仅用于拉丁字母和数字的辅助字体：找不到 Times New Roman 时回退随包 Noto Serif SC 并警告，其余正文字体仍报错
LATIN_FALLBACKS={'serif-latin':400,'serif-latin-bold':700}
LAYOUTS={'cover','story','split','collage','points','quote','full','ending'}
from functools import lru_cache
@lru_cache(maxsize=96)
def load_font(path,size,index,weight):
 f=ImageFont.truetype(path,size,index=index)
 if weight is not None:
  if isinstance(weight,bool) or not isinstance(weight,(int,float)) or not math.isfinite(weight):
   raise ValueError('weight须为有限数字；静态字体请设为null或省略')
  try:axes=f.get_variation_axes()
  except OSError as exc:raise ValueError('该字库是静态字体，不能设置变量字重；weight请设为null或省略') from exc
  weight_axes=[a for a in axes if a['name'] in (b'Weight','Weight')]
  if not weight_axes:raise ValueError('该字库没有Weight变量轴；weight请设为null或省略')
  if any(not a['minimum']<=weight<=a['maximum'] for a in weight_axes):
   raise ValueError('weight超出该字体Weight变量轴范围')
  f.set_variation_by_axes([weight if a in weight_axes else a['default'] for a in axes])
 return f

@lru_cache(maxsize=96)
def warn_title_fallback(reason):
 warnings.warn('授权标题字体配置错误：'+reason+'；headline / cover-title / heading 回退到 v6 的 Noto Serif SC Bold700。本次未使用所配置的授权字库。',RuntimeWarning,stacklevel=3)

@lru_cache(maxsize=8)
def warn_latin_fallback(name):
 warnings.warn(f'找不到 {name} 对应的 Times New Roman，拉丁字母和数字回退到随包的 Noto Serif SC。',RuntimeWarning,stacklevel=4)

def resolved_font(name,size,config):
 """返回实际字库与审计信息；授权入口只覆盖三个标题key，不影响正文。"""
 size=max(1,int(size))
 if name not in FONTS and name in SYSTEM_FONTS:
  try:FONTS[name]=find_system_font(name)
  except FileNotFoundError:
   if name not in LATIN_FALLBACKS:raise
   FONTS[name]=(FONT_ROOT/'NotoSerifSC[wght].ttf',0,LATIN_FALLBACKS[name]);warn_latin_fallback(name)
 p,i,weight=FONTS[name];override=config.get('fonts',{}).get(name,{})
 p,i,weight=override.get('path',p),override.get('index',i),override.get('weight',weight)
 if override.get('path'):p=asset_path(Path.cwd(),p)
 licensed=config.get('fonts',{}).get('licensed_headline',{})
 if name in TITLE_FONT_KEYS and licensed and (not isinstance(licensed,dict) or licensed.get('path') is not None):
  requested=licensed.get('path') if isinstance(licensed,dict) else licensed
  try:
   if not isinstance(licensed,dict):raise ValueError('fonts.licensed_headline须为含path/index/weight的对象')
   if not isinstance(requested,(str,Path)) or not str(requested).strip():raise ValueError('path须为非空字体文件路径')
   target=Path(requested).expanduser()
   target=asset_path(Path.cwd(),target)
   if not target.is_file():raise FileNotFoundError('字体文件不存在：'+str(target))
   index=licensed.get('index',0);selected_weight=licensed.get('weight')
   if isinstance(index,bool) or not isinstance(index,int) or index<0:raise ValueError('index须为非负整数')
   face=load_font(str(target),size,index,selected_weight)
   return face,{'path':str(target),'index':index,'weight':selected_weight,'source':'licensed_headline','fallback':False}
  except (OSError,ValueError,TypeError) as exc:
   requested_index=licensed.get('index',0) if isinstance(licensed,dict) else None
   requested_weight=licensed.get('weight') if isinstance(licensed,dict) else None
   reason=f'{requested!s}（index={requested_index}, weight={requested_weight}）：{exc}';warn_title_fallback(reason)
   p,i,weight=FONTS['serif-bold']
   return load_font(str(p),size,i,weight),{'path':str(p),'index':i,'weight':weight,'source':'v6-fallback','fallback':True,'requested_path':str(requested),'requested_index':requested_index,'requested_weight':requested_weight,'error':reason}
 fallback=name in LATIN_FALLBACKS and not override and Path(p)==FONT_ROOT/'NotoSerifSC[wght].ttf'
 source='latin-fallback' if fallback else 'override' if override else 'builtin'
 return load_font(str(p),size,i,weight),{'path':str(p),'index':i,'weight':weight,'source':source,'fallback':fallback}

def font(name,size,config):return resolved_font(name,size,config)[0]

def page_config(config,page):
 override=page.get('config',{});merged={**config,**override}
 if config.get('fonts') or override.get('fonts'):
  merged['fonts']={**config.get('fonts',{}),**override.get('fonts',{})}
 return merged
def rgba(c):return c if isinstance(c,tuple) else c

def muted_accent(color):
 from PIL import ImageColor
 rgb=ImageColor.getrgb(color);h,s,v=colorsys.rgb_to_hsv(*(c/255 for c in rgb))
 return '#%02X%02X%02X'%tuple(round(c*255) for c in colorsys.hsv_to_rgb(h,s*.70,v*.75))

def rich_chars(text,accent,fill):
 for part in re.split(r'(\[\[.*?\]\])',text,flags=re.S):
  hi=part.startswith('[[') and part.endswith(']]');s=part[2:-2] if hi else part
  for ch in s:yield ch,accent if hi else fill

@lru_cache(maxsize=8192)
def missing_glyph(face,char):
 mask,tofu=face.getmask(char),face.getmask(chr(0x10ffff))
 return mask.size==tofu.size and bytes(mask)==bytes(tofu)

@lru_cache(maxsize=16384)
def ink_box(face,char,stroke=0):
 mask,offset=face.getmask2(char,anchor='ls',stroke_width=stroke)
 bounds=mask.getbbox()
 return tuple(bounds[i]+offset[i%2] for i in range(4)) if bounds else None

def draw_3d_text(canvas,e,cfg,W,H,audit):
 """45度逐像素挤出；马善政清晰版B，仅1px同色加粗，无外描边。"""
 light=normalize_tone(cfg.get('tone','暗'))=='浅'
 scale=W/1440;depth=e.get('depth',1 if light else 7);bold=e.get('bold',1)
 shadow={**({'color':'#A39B8D','offset':[2,3],'blur':2,'opacity':.12} if light else {'color':'#000000','offset':[6,7],'blur':5,'opacity':110/255}),**e.get('soft_shadow',{})}
 if depth<0 or bold<0 or shadow['blur']<0 or not 0<=shadow['opacity']<=1:raise ValueError('3d参数超出范围')
 plain={k:v for k,v in e.items() if k not in ['effect','soft_shadow','stroke_fill','shadow','glow','bg']}
 key=e.get('font','body');actual=font(key,e.get('size',60)*scale,cfg)
 default_shift=.35 if key in TITLE_FONT_KEYS and actual.getname()[0]=='Ma Shan Zheng' else 0
 plain.update(stroke=round(bold*scale),tight_punctuation=e.get('tight_punctuation','all' if default_shift else False),
              punctuation_shift=e.get('punctuation_shift',default_shift))
 face=Image.new('RGBA',canvas.size);records=[];draw_text(face,plain,cfg,W,H,records)
 mask=face.getchannel('A');dx,dy=[round(v*scale) for v in shadow['offset']]
 blur=shadow['blur']*scale
 soft=Image.new('RGBA',canvas.size,shadow['color'])
 soft.putalpha(mask.filter(ImageFilter.GaussianBlur(blur)).point(lambda a:round(a*shadow['opacity'])))
 if e.get('bg'):
  x,y,w,h=e['box'];ImageDraw.Draw(canvas).rectangle((x*W,y*H,(x+w)*W,(y+h)*H),fill=e['bg'])
 canvas.alpha_composite(soft,(dx,dy))
 solid=Image.new('RGBA',canvas.size,e.get('shadow_color','#D4CDBF' if light else '#0C0C0C'));solid.putalpha(mask)
 steps=round(depth*scale)
 for offset in range(steps,0,-1):canvas.alpha_composite(solid,(offset,offset))
 canvas.alpha_composite(face)
 record=records[0];bounds=record['ink_bounds']
 if bounds:
  effect_bounds=[min(bounds[0],bounds[0]+dx-3*blur),min(bounds[1],bounds[1]+dy-3*blur),
                 max(bounds[2]+steps,bounds[2]+dx+3*blur),max(bounds[3]+steps,bounds[3]+dy+3*blur)]
 else:effect_bounds=None
 record.update(effect='3d',depth=depth,depth_pixels=steps,bold=bold,shadow_color=e.get('shadow_color','#D4CDBF' if light else '#0C0C0C'),
               soft_shadow=shadow,effect_bounds=effect_bounds,external_outline=False,
               punctuation_shift=0 if plain['tight_punctuation']=='all' else plain['punctuation_shift'])
 audit.append(record)

LATIN_CHARS=set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789%.+')

def draw_hscaled(canvas,e,cfg,W,H,audit):
 """文字层横向压缩（hscale<1 变窄）：在宽 1/hscale 的框里排好，再整体横向缩放，左边 x 不动。审计里的墨迹框同步换算。"""
 k=float(e['hscale'])
 if not .5<=k<=1.5:raise ValueError('hscale须在0.5–1.5之间')
 x,y,w,h=e['box'];x0=x*W
 inner={**e,'box':[x,y,w/k,h]};inner.pop('hscale')
 layer=Image.new('RGBA',(math.ceil(max(canvas.width/k,x0+w*W/k+W*.2))+4,canvas.height))
 n=len(audit);draw_text(layer,inner,cfg,W,H,audit)
 shrunk=layer.resize((max(1,round(layer.width*k)),layer.height),Image.Resampling.LANCZOS)
 dx=round(x0*(1-k))
 if canvas.width-max(dx,0)>0:
  part=shrunk.crop((max(-dx,0),0,max(-dx,0)+canvas.width-max(dx,0),canvas.height))
  canvas.alpha_composite(part,(max(dx,0),0))
 fx=lambda v:round(v*k+dx,2)
 for r in audit[n:]:
  r['box']=e['box'];r['hscale']=k
  for key in ('ink_bounds','effect_bounds'):
   if r.get(key):b=r[key];r[key]=[fx(b[0]),b[1],fx(b[2]),b[3]]
  for g in r.get('glyphs') or []:
   if g['ink_bounds']:b=g['ink_bounds'];g['ink_bounds']=[fx(b[0]),b[1],fx(b[2]),b[3]]
  for v in r.get('punctuation_gaps') or []:v['gap_pixels']=round(v['gap_pixels']*k,3);v['gap_em']=round(v['gap_em']*k,6)

# 排字规则（typo=True 时生效，数值见 references/排字细节.md）：破折号画两段细线、省略号画三个等距圆点、
# 【】窄排、间隔号窄排、正文里的数字和拉丁字母换西文衬线字体。
TYPO={'dash_len':.74,'dash_thick':.045,'dash_adv':.86,'dots_d':.12,'dots_pitch':1/3,'bracket':.44,'bracket_margin':.03,'middot':.30,'latin_font':'serif-latin','latin_scale':1.07,'justify_space_max':.50,'justify_max':.05}
SQUEEZE_OPEN=set('「『（(“‘《【')
SQUEEZE=set('，。、：；！？」』）)”’》】')|SQUEEZE_OPEN   # 两端对齐时可挤到半宽的全角标点
@lru_cache(maxsize=256)
def han_center(face):
 b=face.getbbox('国',anchor='ls');return (b[1]+b[3])/2

def draw_special(d,sp,x,baseline,cw,size,face,color,stroke=0):
 """画排字规则里的图形字：dash（一段细线，两字「——」即两段带间隙）、dots（三个等距圆点）。返回墨迹框。"""
 cy=baseline+han_center(face)
 if sp=='dash':
  L=TYPO['dash_len']*size;t=max(1.5,TYPO['dash_thick']*size+stroke)
  box=[x+(cw-L)/2,cy-t/2,x+(cw+L)/2,cy+t/2]
  if d:d.rectangle(box,fill=color)
 else:
  r=TYPO['dots_d']*size/2+stroke/2;p=TYPO['dots_pitch']*size;box=None
  for j in (-1,0,1):
   c=x+cw/2+j*p
   if d:d.ellipse([c-r,cy-r,c+r,cy+r],fill=color)
  box=[x+cw/2-p-r,cy-r,x+cw/2+p+r,cy+r]
 return box

def draw_text(canvas,e,cfg,W,H,audit):
 if e.get('hscale',1)!=1:return draw_hscaled(canvas,e,cfg,W,H,audit)
 if e.get('effect')=='3d':return draw_3d_text(canvas,e,cfg,W,H,audit)
 if e.get('glow'):
  setting=e['glow'];setting=setting if isinstance(setting,dict) else {'radius':setting}
  layer=Image.new('RGBA',canvas.size);plain={k:v for k,v in e.items() if k!='glow'}
  draw_text(layer,plain,cfg,W,H,audit)
  halo=layer.filter(ImageFilter.GaussianBlur(setting.get('radius',10)*W/1440))
  halo.putalpha(halo.getchannel('A').point(lambda a:round(a*setting.get('opacity',.32))))
  canvas.alpha_composite(halo);canvas.alpha_composite(layer);return
 if e.get('soft_shadow'):
  setting=e['soft_shadow'];setting=setting if isinstance(setting,dict) else {}
  color=setting.get('color','#000000');dx,dy=setting.get('offset',[10,14])
  plain={k:v for k,v in e.items() if k!='soft_shadow'}
  plain.update(fill=color,accent=color,stroke_fill=color,shadow=False)
  bx,by,bw,bh=plain['box'];plain['box']=[bx+dx/1440,by+dy/(1440*4/3),bw,bh]
  layer=Image.new('RGBA',canvas.size);draw_text(layer,plain,cfg,W,H,[])
  layer=layer.filter(ImageFilter.GaussianBlur(setting.get('blur',9)*W/1440))
  layer.putalpha(layer.getchannel('A').point(lambda a:round(a*setting.get('opacity',.72))))
  canvas.alpha_composite(layer)
 x,y,w,h=e['box'];x*=W;y*=H;w*=W;h*=H
 size=e.get('size',60)*W/1440;spacing=e.get('spacing',2)*W/1440
 f,font_info=resolved_font(e.get('font','body'),size,cfg);lineheight=e.get('lineheight',size*1.36);lineheight*=W/1440 if 'lineheight' in e else 1
 chars=list(rich_chars(e['text'],e.get('accent',cfg['accent']),e.get('fill','#FFFFFF')))
 lines=[];line=[];width=0;fallbacks=set();compact={};previous_ink=None;previous_char=None;soft=[]
 optical=e.get('tight_punctuation')=='all';gap=e.get('punctuation_gap',.10)*size
 typo=bool(e.get('typo'));stroke=e.get('stroke',0)
 latin_key=e.get('latin_font') or (TYPO['latin_font'] if typo else None)
 latin_scale=e.get('latin_scale',TYPO['latin_scale'] if typo and not e.get('latin_font') else .92)
 if optical and not 0<=gap<=.15*size:raise ValueError('punctuation_gap须在0至0.15em之间')
 # 悬挂标点：允许最多0.6个字出界；严格盒宽用于换行，不截掉字。
 for ch,color in chars:
  if ch=='\n':lines.append((line,width));soft.append(False);line=[];width=0;previous_ink=None;previous_char=None;continue
  cf=f;shift=0
  # 可选：毛笔等标题里的英文字母和数字换成黑体（latin_font），默认 0.92 倍字号、共用基线。
  if latin_key and ch in LATIN_CHARS:cf=font(latin_key,size*latin_scale,cfg)
  if not ch.isspace() and missing_glyph(cf,ch):
   cf=font(e.get('fallback_font','sans-bold'),size,cfg)
   if missing_glyph(cf,ch):raise ValueError('主字体与补字字体均缺字：'+ch)
   fallbacks.add(ch)
  if typo and ch in '—…【】·':
   sp=None
   if ch in '—…':sp='dash' if ch=='—' else 'dots';cw=(TYPO['dash_adv'] if ch=='—' else 1)*size+spacing
   else:
    cw=(TYPO['bracket'] if ch in '【】' else TYPO['middot'])*size+spacing;bb=ink_box(cf,ch,stroke)
    if not bb:shift=0
    elif ch=='【':shift=cw-spacing-TYPO['bracket_margin']*size-bb[2]
    elif ch=='】':shift=TYPO['bracket_margin']*size-bb[0]
    else:shift=(cw-spacing)/2-(bb[0]+bb[2])/2
   if width+cw>w and line and (ch not in CLOSING_PUNCTUATION or width+cw-w>.6*size) and ch!='】':   # 最多悬挂 0.6 字
    lines.append((line,width));soft.append(True);line=[];width=0
   line.append((ch,color,cw,cf,shift,sp));width+=cw;compact[ch]=round(cw,2);previous_ink=None;previous_char=None;continue
  cw=cf.getlength(ch)+spacing
  move=e.get('punctuation_shift',0)
  # 字形整体向前移动，同时收回推进宽，避免把空隙留给下一字；共用原基线。
  if not optical and move and ch in '：:，、；。？！':
   if not 0<=move<=.5:raise ValueError('punctuation_shift须在0至0.5之间')
   shift=-move*size;cw=max(size*.12,cw-move*size);compact[ch]=round(cw,2)
  if e.get('tight_punctuation') is True and ch in '：:':
   bounds=ink_box(cf,ch)
   if bounds:
    pad=size*.035;shift=pad-bounds[0];cw=bounds[2]-bounds[0]+2*pad+spacing
    compact[ch]=round(cw,2)
  bounds=ink_box(cf,ch,e.get('stroke',0))
  def optical_position(cursor,last_ink,last_char):
   offset=0;advance=cf.getlength(ch)+spacing
   if bounds:
    if last_ink is not None and (ch in PUNCTUATION or last_char in PUNCTUATION):
     offset=last_ink+gap-cursor-bounds[0]
    elif not line and ch in PUNCTUATION:offset=-bounds[0]
    if ch in PUNCTUATION:advance=offset+bounds[2]+gap
    else:advance+=offset
   return advance,offset
  if optical:cw,shift=optical_position(width,previous_ink,previous_char)
  if width+cw>w and line and e.get('justify') and not optical:
   # 标点挤压：行内全角标点最多压到半宽，先吸收超出的量，放得下就不换行
   room=[(j,g[2]-spacing-size*.5) for j,g in enumerate(line) if g[0] in SQUEEZE and g[2]-spacing>size*.55]
   need=width+cw-w;total=sum(r for _,r in room)
   if room and total>=need:
    for j,r in room:
     cut=r*need/total;g=line[j];line[j]=(g[0],g[1],g[2]-cut,g[3],g[4]-(cut if g[0] in SQUEEZE_OPEN else 0),g[5])
    width-=need
  if width+cw>w and line and ch not in CLOSING_PUNCTUATION:
   lines.append((line,width));soft.append(True);line=[];width=0;previous_ink=None;previous_char=None
   if optical:cw,shift=optical_position(width,None,None)
  if optical and ch in PUNCTUATION:compact[ch]=round(cw,2)
  line.append((ch,color,cw,cf,shift,None));width+=cw
  previous_ink=width-cw+shift+bounds[2] if bounds else None;previous_char=ch if bounds else None
 if line:lines.append((line,width));soft.append(False)
 if e.get('justify'):
  # 两端对齐：段末行不动；含空格的行只拉宽空格，否则把余量均分到字间（相邻两个拉丁字符之间不加）。
  extra_soft=set(e.get('soft_breaks',[]))
  for i,(row,rw) in enumerate(lines[:-1]):
   if not (soft[i] or i in extra_soft):continue
   n=len(row)
   while n and row[n-1][0]==' ':n-=1
   content=row[:n];rw_c=sum(g[2] for g in content);extra=w-rw_c
   if n<2 or extra<=0:continue
   inner=[j for j in range(1,n-1) if content[j][0]==' ']
   pair_ok=lambda a,b:not (a in LATIN_CHARS and b in LATIN_CHARS) and not (optical and (a in PUNCTUATION or b in PUNCTUATION)) and not (a==b and a in '—…')
   slots=[j for j in range(n-1) if pair_ok(content[j][0],content[j+1][0])]   # 标点两侧不拉，守住标点间距
   if inner and extra/len(inner)<=TYPO['justify_space_max']*size:slots=inner      # 空格拉得开就只拉空格
   if not slots or extra/len(slots)>TYPO['justify_max']*size:continue          # 要拉太多就不拉（留参差，别出现大窟窿）
   add=extra/len(slots);row=list(content)
   for j in slots:g=row[j];row[j]=(g[0],g[1],g[2]+add,g[3],g[4],g[5])
   lines[i]=(row,rw_c+extra)
 used=len(lines)*lineheight
 if used>h+1:raise ValueError(f"文字溢出 {e['text'][:25]}: {used:.0f}>{h:.0f}px；分段/增高框，不自动缩字号")
 d=ImageDraw.Draw(canvas);ink_bounds=[];glyphs=[]
 for li,(row,rw) in enumerate(lines):
  xx=x+(max(0,w-rw)/2 if e.get('align')=='center' else max(0,w-rw) if e.get('align')=='right' else 0)
  yy=y+li*lineheight
  if e.get('bg'):
   d.rectangle((xx-9,yy-4,xx+rw+9,yy+lineheight-3),fill=e['bg'])
  # 所有字形共用字体基线，不能按各字墨迹顶端对齐（lt会抬高标点）。
  ascent,descent=f.getmetrics();baseline=yy+ascent
  pen=xx
  for ch,color,cw,cf,shift,sp in row:
   bounds=ink_box(cf,ch,e.get('stroke',0)) if not sp else None
   if sp:
    positioned=draw_special(None,sp,pen,baseline,cw,size,f,color,stroke)
    ink_bounds.append(positioned);glyphs.append({'char':ch,'line':li,'ink_bounds':positioned,'fill':color})
   elif bounds:
    positioned=[pen+shift+bounds[0],baseline+bounds[1],pen+shift+bounds[2],baseline+bounds[3]]
    ink_bounds.append(positioned);glyphs.append({'char':ch,'line':li,'ink_bounds':positioned,'fill':color})
   else:glyphs.append({'char':ch,'line':li,'ink_bounds':None,'fill':color})
   pen+=cw
  angle=e.get('italic',0)
  if angle:
   if not -15<=angle<=15:raise ValueError('italic角度须在-15至15度之间')
   pad=round(size*.45);rh=max(round(lineheight),ascent+descent)+8
   row_layer=Image.new('RGBA',(math.ceil(rw)+pad*2+12,rh))
   rd=ImageDraw.Draw(row_layer);rx=pad
   for ch,color,cw,cf,shift,sp in row:
    if sp:
     if e.get('shadow'):draw_special(rd,sp,rx+4,ascent+4,cw,size,f,'#000000',stroke)
     draw_special(rd,sp,rx,ascent,cw,size,f,color,stroke);rx+=cw;continue
    if e.get('shadow'):rd.text((rx+shift+4,ascent+4),ch,font=cf,fill='#000000',anchor='ls')
    rd.text((rx+shift,ascent),ch,font=cf,fill=color,anchor='ls',stroke_width=e.get('stroke',0),stroke_fill=e.get('stroke_fill',color));rx+=cw
   k=math.tan(math.radians(angle))
   row_layer=row_layer.transform(row_layer.size,Image.Transform.AFFINE,(1,k,-k*ascent,0,1,0),Image.Resampling.BICUBIC)
   canvas.alpha_composite(row_layer,(round(xx-pad),round(yy)))
  else:
   for ch,color,cw,cf,shift,sp in row:
    if sp:
     if e.get('shadow'):draw_special(d,sp,xx+4,baseline+4,cw,size,f,'#000000',stroke)
     draw_special(d,sp,xx,baseline,cw,size,f,color,stroke);xx+=cw;continue
    if e.get('shadow'):d.text((xx+shift+4,baseline+4),ch,font=cf,fill='#000000',anchor='ls')
    d.text((xx+shift,baseline),ch,font=cf,fill=color,anchor='ls',stroke_width=e.get('stroke',0),stroke_fill=e.get('stroke_fill',color));xx+=cw
 bounds=[round(min(b[0] for b in ink_bounds),2),round(min(b[1] for b in ink_bounds),2),round(max(b[2] for b in ink_bounds),2),round(max(b[3] for b in ink_bounds),2)] if ink_bounds else None
 gaps=punctuation_gaps(glyphs,size)
 if optical:
  violations=[v for v in gaps if v['gap_em']>.2+1e-6 or v['gap_em']<-.001]
  if typo:violations=[v for v in violations if not set(v['pair'])&set('—…【】·')]   # 排字规则自带间距
  if violations:raise ValueError('毛笔标点实际墨迹间距超限：'+str(violations))
 audit.append({'kind':'text','box':e['box'],'lines':len(lines),'used_height':round(used),'capacity_height':round(h),'text':e['text'],
  'font':e.get('font','body'),'font_file':font_info,'size':e.get('size',60),'stroke_width':e.get('stroke',0),
  'stroke_fill':e.get('stroke_fill'),'soft_shadow':e.get('soft_shadow'),'ink_bounds':bounds,
  'fallback_characters':sorted(fallbacks),'compact_punctuation_advances':compact,
  'tight_punctuation':e.get('tight_punctuation',False),'punctuation_gaps':gaps,'glyphs':glyphs,'latin_font':latin_key,'typo':typo,'justify':bool(e.get('justify'))})

def punctuation_gaps(glyphs,size):
 """按同一行相邻可见字形的真实墨迹边界测空白；空格与换行不跨越。"""
 result=[]
 for a,b in zip(glyphs,glyphs[1:]):
  if a['line']!=b['line'] or not a['ink_bounds'] or not b['ink_bounds']:continue
  if a['char'] not in PUNCTUATION and b['char'] not in PUNCTUATION:continue
  gap=b['ink_bounds'][0]-a['ink_bounds'][2]
  result.append({'pair':a['char']+b['char'],'line':a['line'],'gap_pixels':round(gap,3),'gap_em':round(gap/size,6),
                 'adjacent_han':any('\u3400'<=c<='\u9fff' for c in (a['char'],b['char']))})
 return result

def disc_portrait(e,base,W,H,cfg):
 """实心圆盘与柔影；真实透明人物向指定方向越圆，其他方向以圆弧收边。"""
 scale=W/1440;radius=round(e['radius']*scale);cx,cy=round(e['center'][0]*W),round(e['center'][1]*H)
 direction=e.get('breakout_direction','top');extra=round(e.get('breakout',100)*scale)
 if radius<=0 or extra<=0 or direction not in ['top','bottom','left','right']:raise ValueError('disc_portrait半径/出界幅度须>0，方向须top/bottom/left/right')
 path=asset_path(base,e['cutout_path'])
 with Image.open(path) as source:
  if source.mode!='RGBA' or source.getchannel('A').getextrema()[0]==255:raise ValueError('disc_portrait只接受经确认的真实透明RGBA抠图：'+str(path))
  subject=source.copy()
 bbox=subject.getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox()
 if not bbox:raise ValueError('disc_portrait人物为空')
 subject=subject.crop(bbox);vertical=direction in ['top','bottom']
 # 仅调整圆底时可保留既有人物的尺寸和位置，避免盘径与人物缩放耦合。
 portrait_radius=round(e.get('portrait_radius',e['radius'])*scale)
 if portrait_radius<=0:raise ValueError('disc_portrait portrait_radius须>0')
 dimension=2*portrait_radius+extra
 ratio=dimension/(subject.height if vertical else subject.width)
 region=subject.size;scaled_size=(round(subject.width*ratio),round(subject.height*ratio));geometry=ratio_audit(region,scaled_size,'disc-portrait-contain',source=str(path),alpha_crop=list(bbox))
 subject=subject.resize(scaled_size,Image.Resampling.LANCZOS)
 if vertical:pos=(round(cx-subject.width/2),cy-portrait_radius-extra if direction=='top' else cy-portrait_radius)
 else:pos=(cx-portrait_radius-extra if direction=='left' else cx-portrait_radius,round(cy-subject.height/2))
 offset=e.get('portrait_offset',[0,0]);pos=tuple(p+round(v*scale) for p,v in zip(pos,offset))
 if min(pos)<0 or pos[0]+subject.width>W or pos[1]+subject.height>H:raise ValueError('disc_portrait人物越过画布；调整中心/半径/出界幅度')
 disc=Image.new('L',(W,H));ImageDraw.Draw(disc).ellipse((cx-radius,cy-radius,cx+radius,cy+radius),fill=255)
 allowance=disc.copy();dd=ImageDraw.Draw(allowance)
 if direction=='top':dd.rectangle((0,cy-portrait_radius-extra,W,cy),fill=255)
 elif direction=='bottom':dd.rectangle((0,cy,W,cy+portrait_radius+extra),fill=255)
 elif direction=='left':dd.rectangle((cx-portrait_radius-extra,0,cx,H),fill=255)
 else:dd.rectangle((cx,0,cx+portrait_radius+extra,H),fill=255)
 person=Image.new('RGBA',(W,H));person.alpha_composite(subject,pos)
 person.putalpha(ImageChops.multiply(person.getchannel('A'),allowance))
 person_mask=person.getchannel('A').point(lambda a:255 if a>=128 else 0)
 outside=ImageChops.subtract(person_mask,disc);outside_pixels=outside.histogram()[255]
 if not outside_pixels:raise ValueError('disc_portrait人物没有实际越过圆盘边缘')
 face_records=[]
 for face in e.get('face_boxes',[]):
  x,y,w,h=face;sw,sh=Image.open(path).size
  fb=[pos[0]+(x*sw-bbox[0])*ratio,pos[1]+(y*sh-bbox[1])*ratio,pos[0]+((x+w)*sw-bbox[0])*ratio,pos[1]+((y+h)*sh-bbox[1])*ratio]
  points=[(fb[0],fb[1]),(fb[2],fb[1]),(fb[0],fb[3]),(fb[2],fb[3]),((fb[0]+fb[2])/2,fb[3])]
  complete=all(0<=xx<W and 0<=yy<H and allowance.getpixel((round(xx),round(yy)))>0 for xx,yy in points)
  if not complete:raise ValueError('disc_portrait圆形遮罩截断Vision人脸框，请调整人物尺寸或位置：'+e['source_id'])
  face_records.append({'source_face':face,'rendered_face_box':fb,'complete':complete})
 geometry['face_check']={'detector':e.get('face_detection_method'),'faces':face_records,'partial_face_ids':[],'mode':'equal-scale-before-disc-mask'}
 disc_pixels=disc.histogram()[255]
 visible_disc_pixels=ImageChops.subtract(disc,person_mask).histogram()[255]
 visible_disc_ratio=visible_disc_pixels/max(1,disc_pixels)
 if visible_disc_ratio<.40:
  raise ValueError(f'disc_portrait圆盘可见面积{visible_disc_ratio:.1%}<40%：{e["source_id"]}；缩小/移位人物或调整盘径')
 shadow={**{'color':'#000000','offset':[8,10],'blur':12,'opacity':.5},**e.get('soft_shadow',{})}
 if shadow['blur']<0 or not 0<=shadow['opacity']<=1:raise ValueError('disc_portrait柔影参数错误')
 layer=Image.new('RGBA',(W,H));shade=Image.new('RGBA',(W,H),shadow['color'])
 shade.putalpha(disc.filter(ImageFilter.GaussianBlur(shadow['blur']*scale)).point(lambda a:round(a*shadow['opacity'])))
 layer.alpha_composite(shade,tuple(round(v*scale) for v in shadow['offset']))
 disc_color=e.get('disc_color') or muted_accent(cfg['accent'])
 solid=Image.new('RGBA',(W,H),disc_color);solid.putalpha(disc);layer.alpha_composite(solid);layer.alpha_composite(person)
 coverage=ImageChops.lighter(disc,person_mask)
 record={'transform':geometry,'kind':'disc_portrait','source_id':e['source_id'],'cutout_path':str(path),'center':[cx,cy],'radius_pixels':radius,
         'disc_color':disc_color,'outline':False,'breakout_direction':direction,'breakout_pixels':extra,'portrait_radius_pixels':portrait_radius,
         'portrait_offset_pixels':[round(v*scale) for v in offset],
         'actual_outside_pixels':outside_pixels,'actual_outside_bounds':outside.getbbox(),'person_ink_bounds':person_mask.getbbox(),
         'disc_total_pixels':disc_pixels,'disc_visible_pixels':visible_disc_pixels,'disc_visible_ratio':round(visible_disc_ratio,6),
         'disc_visibility_method':'圆盘总像素中未被人物alpha>=128遮挡的面积，柔影不计分母',
         'person_opaque_pixels':person_mask.histogram()[255],'soft_shadow':shadow}
 return layer,person_mask,coverage,record

def processed_image(e,base,target,cfg,audit=None):
 im=Image.open(asset_path(base,e['path'])).convert('RGBA');original_size=im.size
 crop_box=None
 if e.get('crop'):
  a=e['crop'];crop_box=tuple(round(v*(im.width if i%2==0 else im.height)) for i,v in enumerate(a));im=im.crop(crop_box)
 if e.get('mask'):
  mask=Image.open(asset_path(base,e['mask'])).convert('L')
  # 原尺寸人物mask须与照片同步裁切，不能将完整轮廓拉伸套在已裁照片上。
  if crop_box and mask.size==original_size:mask=mask.crop(crop_box)
  ratio_audit(mask.size,im.size,'subject-mask-sync',source=e['mask']);mask=mask.resize(im.size);im.putalpha(mask)
 fx=e.get('effects',[]);fx=[fx] if isinstance(fx,str) else fx
 alpha=im.getchannel('A')
 if 'mono' in fx or 'sepia' in fx:
  gray=ImageOps.grayscale(im)
  im=(ImageOps.colorize(gray,'#251e12','#efe3c9') if 'sepia' in fx else gray.convert('RGB')).convert('RGBA');im.putalpha(alpha)
 if 'aged' in fx:
  rgb=ImageEnhance.Color(im.convert('RGB')).enhance(.6);im=rgb.convert('RGBA');im.putalpha(alpha)
  noise=Image.fromarray(np.random.default_rng(19).integers(65,195,(im.height,im.width),dtype=np.uint8),'L').convert('RGB')   # 单色颗粒：三通道同值
  im=Image.blend(im,noise.convert('RGBA'),.045);im.putalpha(alpha)
 if e.get('saturation',1)!=1:
  factor=e['saturation']
  if not isinstance(factor,(int,float)) or not 0<=factor<=2:raise ValueError('saturation须在0–2之间')
  im=ImageEnhance.Color(im.convert('RGB')).enhance(factor).convert('RGBA');im.putalpha(alpha)
 tw,th=target
 if e.get('fit','contain') not in ['cover','contain']:raise ValueError('fit只允许cover或透明抠图contain')
 if e.get('fit','contain')=='cover':
  faces,excluded=local_faces(e,original_size,im.size);focus,face_check=safe_focus(im.size,(tw,th),faces,tuple(e.get('focus',[.5,.5])))
  geometry=fit_geometry(im.size,(tw,th),focus);geometry['face_check']={**face_check,'explicit_crop_excluded_face_ids':excluded,'detector':e.get('face_detection_method')};im=ImageOps.fit(im,(tw,th),Image.Resampling.LANCZOS,centering=tuple(focus))
 else:
  # contain也应按框等比放大；thumbnail只缩小，会让小幅版画缩在大框中心。
  if e.get('cover_only',cfg.get('cover_only',True)) and im.getchannel('A').getextrema()[0]>=255:raise ValueError('矩形照片必须cover，contain只用于真实透明抠图')
  region=im.size;im=ImageOps.contain(im,(tw,th),Image.Resampling.LANCZOS);geometry=ratio_audit(region,im.size,'contain',frame_size=[tw,th])
  plate=Image.new('RGBA',(tw,th));plate.alpha_composite(im,(int((tw-im.width)/2),int((th-im.height)/2)));im=plate
 if e.get('face_boxes') and geometry['method']=='contain':geometry['face_check']={'retained_face_ids':list(range(len(e['face_boxes']))),'partial_face_ids':[],'mode':'transparent-contain-no-crop','detector':e.get('face_detection_method')}
 if e.get('unsharp_mask'):
  setting=e['unsharp_mask'];radius=setting.get('radius',1);percent=setting.get('percent',60);threshold=setting.get('threshold',3)
  if not 0<radius<=2 or not 0<percent<=120 or not 0<=threshold<=10:raise ValueError('轻微锐化须radius(0,2]、percent(0,120]、threshold[0,10]')
  alpha=im.getchannel('A');im=im.filter(ImageFilter.UnsharpMask(radius=radius,percent=percent,threshold=threshold));im.putalpha(alpha)
  geometry['unsharp_mask']={'radius':radius,'percent':percent,'threshold':threshold,'stage':'after-equal-scale-crop'}
 if audit is not None:audit.append({'source':e['path'],'declared_crop':e.get('crop'),'rotation':e.get('rotate',0),**geometry})
 if 'circle' in fx:
  m=Image.new('L',im.size);ImageDraw.Draw(m).ellipse((0,0,tw-1,th-1),fill=255);im.putalpha(ImageChops.multiply(im.getchannel('A'),m))
 if 'torn' in fx:
  m=Image.new('L',im.size);dd=ImageDraw.Draw(m);rng=random.Random(e.get('seed',42))
  top=[(x,rng.randint(0,10)) for x in range(0,tw+1,14)];right=[(tw-rng.randint(0,10),y) for y in range(0,th+1,14)];bottom=[(x,th-rng.randint(0,10)) for x in range(tw,-1,-14)];left=[(rng.randint(0,10),y) for y in range(th,-1,-14)]
  dd.polygon(top+right+bottom+left,fill=255);im.putalpha(ImageChops.multiply(im.getchannel('A'),m))
  outline=im.getchannel('A').filter(ImageFilter.MaxFilter(13));border=Image.new('RGBA',im.size,'white');border.putalpha(outline);border.alpha_composite(im);im=border
 if e.get('outline'):
  m=im.getchannel('A');dil=m.filter(ImageFilter.MaxFilter(int(e.get('outline_width',13))|1));layer=Image.new('RGBA',im.size,e['outline']);layer.putalpha(dil);layer.alpha_composite(im);im=layer
 if e.get('darken'):
  rgb=ImageEnhance.Brightness(im.convert('RGB')).enhance(1-e['darken']);a=im.getchannel('A');im=rgb.convert('RGBA');im.putalpha(a)
 if e.get('opacity',1)<1:im.putalpha(im.getchannel('A').point(lambda x:round(x*e['opacity'])))
 if e.get('rotate'):im=im.rotate(e['rotate'],resample=Image.Resampling.BICUBIC,expand=False)
 return im

def dark_backdrop(e,base,W,H,cfg,audit=None):
 """图片满页宽；局部图上下余弦羽化≥25%，整页图不裁成悬浮矩形。"""
 x,y,w,h=e['box']
 if abs(x)>1e-6 or abs(w-1)>1e-6:raise ValueError('dark_backdrop必须横向full-bleed：x=0、width=1')
 if y<0 or h<=0 or y+h>1.000001:raise ValueError('dark_backdrop超出页面')
 full=abs(y)<1e-6 and abs(h-1)<1e-6
 fade=e.get('fade_fraction',0 if full else .25)
 if not full and not .25<=fade<=.5:raise ValueError('局部dark_backdrop上下羽化各须≥图高25%（≤50%）')
 if not 0<=fade<=.5:raise ValueError('fade_fraction须在0–0.5之间')
 tw,th=W,round(h*H);pic=processed_image({**e,'fit':'cover'},base,(tw,th),cfg,audit)
 ramp=Image.new('L',(1,th),255);pixels=[];fh=round(th*fade)
 for j in range(th):
  distance=min(j,th-1-j);t=min(1,distance/max(1,fh))
  pixels.append(round(255*(.5-.5*math.cos(math.pi*t))) if fh else 255)
 ramp.putdata(pixels);mask=ramp.resize((tw,th));pic.putalpha(ImageChops.multiply(pic.getchannel('A'),mask))
 return pic,{'kind':'dark_backdrop','source_id':e.get('source_id'),'path':e['path'],'box':e['box'],
             'full_bleed':True,'full_page':full,'fade_fraction':fade,'fade_pixels_each':fh,
             'top_bottom_alpha':[pixels[0],pixels[-1]],'darken':e.get('darken',0),'ramp':'cosine;上下渐变，不加平涂底板'}

def watermark_layer(cfg,W,H):
 """预览用中性占位；未显式启用时兼容历史署名像素。"""
 neutral=cfg.get('watermark_style')=='neutral'
 if neutral:
  size=round(cfg.get('watermark_size',22)*W/1440);color=cfg.get('watermark_color','#8A8A8A')
  opacity=cfg.get('watermark_opacity',.65);name=cfg.get('watermark_text',str(cfg.get('account_name','账号名')).replace('{','').replace('}',''))
  plate=Image.new('RGBA',(round(230*W/1440),round(65*W/1440)))
  ImageDraw.Draw(plate).text((0,0),name,font=font('serif-regular',size,cfg),fill=color)
  plate.putalpha(plate.getchannel('A').point(lambda a:round(a*opacity)))
  pos=(W-round(160*W/1440),H-round(75*W/1440))
 else:
  name=cfg.get('account_name','{账号名}');size=30;color=cfg['accent'];opacity=1
  plate=Image.new('RGBA',(330,90));ImageDraw.Draw(plate).text((8,15),name,font=font('signature',30,cfg),fill=color)
  plate=plate.rotate(-6,resample=Image.Resampling.BICUBIC);pos=(W-350,H-125)
 layer=Image.new('RGBA',(W,H));layer.alpha_composite(plate,pos)
 return layer,{'style':'neutral' if neutral else 'signature','text':name,'color':color,'size':size,
               'opacity':opacity,'ink_bounds':layer.getchannel('A').getbbox()}

def hand_mark(canvas,e,audit,W,H):
 target=e.get('target_text');record=next((r for r in audit if target and target in re.sub(r'\[\[|\]\]|\n','',r['text'])),None)
 if record:
  chars=[g for g in record['glyphs'] if g['ink_bounds']];joined=''.join(g['char'] for g in chars);start=joined.find(target)
  if start<0:raise ValueError('手绘圈目标未找到实际字形：'+target)
  bs=[g['ink_bounds'] for g in chars[start:start+len(target)]]
  box=[min(b[0] for b in bs),min(b[1] for b in bs),max(b[2] for b in bs),max(b[3] for b in bs)]
 else:
  if target:raise ValueError('手绘圈目标文字不存在：'+target)
  x,y,w,h=e['box'];box=[x*W,y*H,(x+w)*W,(y+h)*H]
 pad=e.get('padding',12)*W/1440;box=[box[0]-pad,box[1]-pad*.6,box[2]+pad,box[3]+pad*.6]
 dd=ImageDraw.Draw(canvas);color=e.get('fill','#C92928');width=max(2,round(e.get('width',4)*W/1440))
 if e['kind']=='hand_underline':
  points=[(box[0]+(box[2]-box[0])*j/30,box[3]+math.sin(j*.6)*1.5) for j in range(31)]
 else:
  cx,cy=(box[0]+box[2])/2,(box[1]+box[3])/2;rx,ry=(box[2]-box[0])/2,(box[3]-box[1])/2
  points=[(cx+(rx+math.sin(j*.48)*1.5)*math.cos(j*math.pi/72),cy+(ry+math.sin(j*.71)*1.1)*math.sin(j*math.pi/72)) for j in range(146)]
 dd.line(points,fill=color,width=width,joint='curve')
 return {'kind':e['kind'],'target_text':target,'ink_bounds':box,'fill':color,'width':width}

def arrow(canvas,e,W,H,cfg):
 p=[(a*W,b*H) for a,b in e['points']];p0,p1,p2=p;pts=[]
 for i in range(65):
  t=i/64;pts.append(((1-t)**2*p0[0]+2*(1-t)*t*p1[0]+t*t*p2[0],(1-t)**2*p0[1]+2*(1-t)*t*p1[1]+t*t*p2[1]))
 d=ImageDraw.Draw(canvas);color=e.get('fill',cfg['accent']);lw=max(2,round(e.get('width',5)*W/1440));d.line(pts,fill=color,width=lw,joint='curve')
 angle=math.atan2(p2[1]-pts[-3][1],p2[0]-pts[-3][0]);sz=e.get('head',30)*W/1440
 for a in [angle+2.6,angle-2.6]:d.line([p2,(p2[0]+sz*math.cos(a),p2[1]+sz*math.sin(a))],fill=color,width=lw)

def default_elements(p):
 l=p['layout'];t=p.get('title','');body=p.get('body','');ims=p.get('images',[]);els=[]
 def tx(text,box,size=60,**kw):
  if text:
   if kw.get('font')=='headline':kw={'effect':'3d',**kw}
   els.append(dict(kind='text',text=text,box=box,size=size,**kw))
 def pic(i,box,**kw):
  if len(ims)>i:els.append(dict(kind='image',path=ims[i]['path'],effects=ims[i].get('effects',[]),box=box,**{'fit':'cover',**kw}))
 if l=='cover':pic(0,[.04,.205,.92,.525]);tx(t,[.06,.74,.88,.23],124,font='headline')
 elif l=='story':tx(t,[.07,.05,.86,.13],104,font='headline');tx(body,[.08,.21,.84,.30]);pic(0,[.04,.54,.92,.36],fit='cover')
 elif l=='split':tx(t,[.05,.06,.9,.14],112,font='headline');tx(body,[.06,.23,.47,.67]);pic(0,[.53,.25,.47,.74])
 elif l=='collage':tx(t,[.05,.05,.9,.13],106,font='headline');pic(0,[.05,.25,.67,.33],fit='cover');pic(1,[.58,.38,.42,.60]);tx(body,[.06,.62,.52,.32])
 elif l=='points':tx(t,[.05,.05,.9,.15],110,font='headline');pic(0,[0,.26,.32,.56]);tx(body,[.36,.24,.59,.67])
 elif l=='quote':pic(0,[0,0,1,1],fit='cover',darken=.60,role='background');tx(t,[.07,.10,.86,.27],106,font='headline');tx(body,[.08,.43,.84,.49])
 elif l=='full':pic(0,[0,0,1,1],fit='cover',darken=.65,role='background');tx(t,[.06,.08,.88,.2],106,font='headline');tx(body,[.08,.66,.84,.27])
 elif l=='ending':tx(t,[.07,.06,.86,.2],114,font='headline');tx(body,[.10,.3,.8,.21],align='center');pic(0,[.12,.55,.76,.39])
 return els

def render(script,out,width=1440,assets_root=None):
 from io_paths import set_assets_root
 set_assets_root(assets_root)
 data=json.loads(script.read_text(encoding='utf-8'));cfg={'accent':'#FCF374','background':'#000000','account_name':'{账号名}','series_name':'{系列名}','bookmark':False,'watermark_style':'neutral',**data.get('config',{})}
 if width!=1440:raise ValueError('成品固定1440×1920；预览另用拼图脚本等比裁切')
 W=width;H=width*4//3;out.mkdir(parents=True,exist_ok=True);reports=[]
 for i,p in enumerate(data['pages'],1):
  if p['layout'] not in LAYOUTS:raise ValueError('未知版式 '+p['layout'])
  pcfg=page_config(cfg,p);pcfg['tone']=normalize_tone(data.get('tone',pcfg.get('tone','暗')));im=Image.new('RGBA',(W,H),p.get('background',pcfg['background']));audit=[]
  if p.get('paper_texture'):
   rng=random.Random(817);grain=Image.new('L',(144,192));grain.putdata([rng.randrange(90,170) for _ in range(144*192)])
   texture=ImageOps.colorize(grain.resize((W,H),Image.Resampling.BICUBIC),'#D6CBBB','#FFF9EE').convert('RGBA')
   im=Image.blend(im,texture,.08)
  elements=list(p.get('elements',default_elements(p)));foreground=[]
  coverage=Image.new('L',(W,H));image_audit=[];component_audit=[];transform_audit=[]
  bookmark=p.get('bookmark',pcfg.get('bookmark',False))
  if bookmark and p.get('bookmark_text',True):
   x=.08 if bookmark!='right' else .80
   elements.append(dict(kind='text',text=pcfg['series_name']+'\n— vol.'+str(p.get('volume','01'))+' —',box=[max(0,x-.065),.115,.30,.08],size=34,align='center'))
  # 先绘制全部图片/装饰，再绘制文字，文字位于图片上层。例外：标了 above_text 的图片（page(layer_order='text-under-images')）
  # 在文字之后画，顺序变成「底色 → 投影 → 文字 → 图片」，图片可以压住文字边缘。没标的页面与原来完全一样。
  late=[e for e in elements if e.get('above_text') and e['kind'] in ('image','dark_backdrop')]
  for phase in (0,1):
   for e in (elements if phase==0 else late):
    if phase==0 and any(e is v for v in late):continue
    kind=e['kind']
    if kind in ['image','dark_backdrop']:
     x,y,w,h=e['box']
     if kind=='dark_backdrop':
      pic,details=dark_backdrop(e,script.parent,W,H,pcfg,transform_audit);component_audit.append(details)
     else:pic=processed_image(e,script.parent,(round(w*W),round(h*H)),pcfg,transform_audit)
     pos=(round(x*W),round(y*H))
     if e.get('soft_shadow'):
      setting=e['soft_shadow'];m=Image.new('L',(W,H));m.paste(pic.getchannel('A'),pos)
      shade=Image.new('RGBA',(W,H),setting.get('color','#000000'))
      shade.putalpha(m.filter(ImageFilter.GaussianBlur(setting.get('blur',12)*W/1440)).point(lambda a:round(a*setting.get('opacity',.5))))
      im.alpha_composite(shade,tuple(round(v*W/1440) for v in setting.get('offset',[8,10])))
     im.alpha_composite(pic,pos)
     # 按实际不透明像素的并集计面积；透明留白、重复叠放和低透明氛围层不能凑面积。
     visible=e.get('opacity',1)>.25 and e.get('coverage',True)
     mask=Image.new('L',(W,H))
     if visible:
      mask.paste(pic.getchannel('A').point(lambda a:255 if a>=128 else 0),pos)
      coverage=ImageChops.lighter(coverage,mask)
     image_audit.append({'path':e['path'],'source_id':e.get('source_id',e['path']),
                         'visible':visible,'opaque_pixels':mask.histogram()[255],'opaque_bounds':mask.getbbox(),
                         'kind':kind,'soft_shadow':e.get('soft_shadow')})
     source=Image.open(asset_path(script.parent,e['path']))
     is_cutout=e.get('mask') or e.get('role')=='foreground' or (source.mode=='RGBA' and source.getchannel('A').getextrema()[0]<255)
     if is_cutout and e.get('role')!='background' and e.get('opacity',1)>.25:
      mask=Image.new('L',(W,H));mask.paste(pic.getchannel('A').point(lambda a:255 if a>=128 else 0),pos)
      foreground.append((e['path'],mask))
    elif kind=='disc_portrait':
     layer,mask,visible,record=disc_portrait(e,script.parent,W,H,pcfg)
     im.alpha_composite(layer);coverage=ImageChops.lighter(coverage,visible)
     foreground.append((e['cutout_path'],mask));component_audit.append(record);transform_audit.append(record['transform'])
     image_audit.append({'path':e['cutout_path'],'source_id':e['source_id'],'visible':True,'opaque_pixels':mask.histogram()[255]})
    elif kind=='arrow':arrow(im,e,W,H,pcfg)
    elif kind in ['rect','ellipse']:
     x,y,w,h=e['box'];drawer=ImageDraw.Draw(im)
     method=drawer.ellipse if kind=='ellipse' else drawer.rectangle
     method((x*W,y*H,(x+w)*W,(y+h)*H),fill=e.get('fill'),outline=e.get('outline'),width=round(e.get('width',4)*W/1440))
   if phase:break
   if bookmark:
    x=.08 if bookmark!='right' else .80;dd=ImageDraw.Draw(im)
    dd.polygon([(x*W,0),((x+.08)*W,0),((x+.08)*W,.075*H),((x+.04)*W,.1*H),(x*W,.075*H)],fill=pcfg['accent'])
   collisions=[]
   for e in elements:
    if e['kind'] not in ['text','caption']:continue
    x,y,w,h=e['box'];box=(round(x*W),round(y*H),round((x+w)*W),round((y+h)*H));area=(box[2]-box[0])*(box[3]-box[1])
    for path,mask in foreground:
     if e.get('text_role')=='label':continue   # 人名标签本来就贴在图上
     overlap=mask.crop(box).histogram()[255]/max(1,area)
     collisions.append({'text':e['text'][:30],'image':path,'opaque_overlap':round(overlap,6)})
     if overlap>.03:raise ValueError(f"碰撞：文本框与抠图不透明区域重叠{overlap:.1%}>3%：{e['text'][:30]} / {path}")
    if e['kind']=='caption':e={'size':28,'font':'sans','spacing':0,'lineheight':36,'bg':'#000000',**e}
    draw_text(im,e,pcfg,W,H,audit)
  for e in elements:
   if e['kind'] in ['hand_circle','hand_underline']:component_audit.append(hand_mark(im,e,audit,W,H))
  if p.get('border'):
   ImageDraw.Draw(im).rectangle((5,5,W-6,H-6),outline=p.get('border') if isinstance(p['border'],str) else pcfg['accent'],width=p.get('border_width',12))
  if p.get('watermark',True):
   layer,wm=watermark_layer(pcfg,W,H);im.alpha_composite(layer)
  else:wm=None
  path=out/f'p{i:02}.png';im.convert('RGB').save(path);reports.append({'page':i,'layout':p['layout'],'size':[W,H],'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'text':audit,'collisions':collisions,
   'page_script_sha256':hashlib.sha256(json.dumps(p,ensure_ascii=False,sort_keys=True).encode()).hexdigest(),'config_script_sha256':hashlib.sha256(json.dumps(data.get('config',{}),ensure_ascii=False,sort_keys=True).encode()).hexdigest(),'image_transforms':transform_audit,'images':image_audit,'components':component_audit,'watermark':wm,'image_elements':sum(v['visible'] for v in image_audit),
   'image_area_ratio':round(coverage.histogram()[255]/(W*H),6)})
 (out/'render-report.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf-8');return reports
if __name__=='__main__':
 a=argparse.ArgumentParser(description='渲染可编辑页面脚本；默认素材路径相对脚本，可显式传素材根目录')
 a.add_argument('script',type=Path);a.add_argument('--out',type=Path,required=True)
 a.add_argument('--assets-root',type=Path)
 v=a.parse_args();print('Rendered',len(render(v.script.resolve(),v.out.resolve(),assets_root=v.assets_root)),'pages')
