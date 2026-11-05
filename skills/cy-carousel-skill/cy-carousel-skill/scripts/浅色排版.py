from io_paths import asset_path
"""浅色矩形照片路径：密度取自成图，不能用噪声或背景标签代替内容。"""
from pathlib import Path
from PIL import Image, ImageOps, ImageColor, ImageDraw
import numpy as np
from render import normalize_tone

def box_mean(a,k=9):
    padded=np.pad(a,k//2,mode='reflect')
    integral=np.pad(padded,((1,0),(1,0))).cumsum(0).cumsum(1)
    return (integral[k:,k:]-integral[:-k,k:]-integral[k:,:-k]+integral[:-k,:-k])/(k*k)

def blank_paper(image):
    # 与监管统计校准：240宽，9×9局部RGB平均亮度标准差；P02 v1≈62.8%、P05≈59.1%。
    im=ImageOps.contain(image.convert('RGB'),(240,10000),Image.Resampling.LANCZOS)
    a=np.asarray(im,dtype=np.float64).mean(2)
    std=np.sqrt(np.maximum(0,box_mean(a*a)-box_mean(a)**2))
    return float(((std<3)&(a>170)).mean())

def face_text_rules(p,record):
    """cover保脸后还要避开文字贴条；检查逐行字宽，不能拿整段空文本框代替。"""
    hits=[]
    for e in [v for v in p.get('elements',[]) if v['kind']=='image']:
        t=next((v for v in record.get('image_transforms',[]) if v.get('source')==e['path']),{})
        fc=t.get('face_check',{}); crop=fc.get('source_crop_box')
        if not crop:continue
        cw,ch=t['source_region_size'];x0,y0,_,_=crop;x,y,w,h=e['box']
        faces=[]
        for f in fc.get('detected_local_faces',[]):
            if f['id'] not in fc.get('retained_face_ids',[]):continue
            a,b,c,d=f['box']
            faces.append((f['id'],[x*1440+(a-x0)*w*1440/cw,y*1920+(b-y0)*h*1920/ch,
                                   x*1440+(c-x0)*w*1440/cw,y*1920+(d-y0)*h*1920/ch]))
        for tx in [v for v in p.get('elements',[]) if v['kind'] in ('text','caption')]:
            tr=next((v for v in record['text'] if v['text']==tx['text'] and v['box']==tx['box']),None);regions=[]
            # 脚本/报告一致性由统一geometry_rules核SHA；此处不把缺失审计误写成已验脸。
            if tr is None:continue
            if tx.get('bg'):
                for ln in set(g['line'] for g in tr['glyphs']):
                    gl=[g['ink_bounds'] for g in tr['glyphs'] if g['line']==ln and g['ink_bounds']]
                    if not gl:continue
                    yy=tx['box'][1]*1920+ln*tx['lineheight']
                    regions.append([min(a[0] for a in gl)-9,yy-4,max(a[2] for a in gl)+9,yy+tx['lineheight']-3])
            else:regions=[g['ink_bounds'] for g in tr['glyphs'] if g['ink_bounds']]
            for fid,(a,b,c,d) in faces:
                # Union avoids double-counting overlapping glyph/strip boxes (>100% was impossible).
                import math
                ox,oy=math.floor(a),math.floor(b);fw,fh=math.ceil(c)-ox,math.ceil(d)-oy
                face_mask=Image.new('1',(max(1,fw),max(1,fh)));drawer=ImageDraw.Draw(face_mask)
                for q in regions:
                    x0,y0,x1,y1=max(a,q[0]),max(b,q[1]),min(c,q[2]),min(d,q[3])
                    if x1>x0 and y1>y0:drawer.rectangle((math.floor(x0)-ox,math.floor(y0)-oy,math.ceil(x1)-ox-1,math.ceil(y1)-oy-1),fill=1)
                overlap=float(np.asarray(face_mask,dtype=bool).mean())
                if overlap>.03:hits.append({'source_id':e['source_id'],'face_id':fid,'text':tx['text'],'face_area_overlap':overlap,'basis':'文字墨迹外接框/逐行贴条与脸框相交像素并集，保守检查'})
    return {'passed':not hits,'collisions':hits}

def light_editorial_rules(data,reports,script,pages_dir):
    errors=[];rows=[];red_brush=0
    if normalize_tone(data.get('tone',data.get('config',{}).get('tone')))!='浅':
        errors.append('light-editorial-v2只能用于浅色篇')
    for n,p in enumerate(data['pages'],1):
        if p['layout']=='cover':continue
        from render import page_config
        cfg=page_config(data.get('config',{}),p)
        record=next(r for r in reports if r['page']==n)
        wm=record.get('watermark') or {}
        if wm.get('style')!='neutral' or wm.get('text')!=cfg.get('watermark_text',str(cfg.get('account_name','账号名')).replace('{','').replace('}','')) or wm.get('size',100)>26 or len(set(ImageColor.getrgb(wm.get('color','#FF0000'))))!=1:
            errors.append(f'P{n:02}预览水印不是灰色小字账号名')
        for t in record['text']:
            ink=t.get('effect_bounds') or t.get('ink_bounds')
            if ink and (ink[0]<0 or ink[1]<0 or ink[2]>1440 or ink[3]>1920):
                errors.append(f'P{n:02}文字实际墨迹出画布：{t["text"][:20]}')
        face_text=face_text_rules(p,record)
        errors.extend(f'P{n:02}文字/贴条覆盖人脸：{hit["text"][:15]}' for hit in face_text['collisions'])
        output=Path(record.get('output_file',pages_dir/f'p{n:02}.png'))
        with Image.open(output) as im: blank=blank_paper(im)
        if blank>.38:errors.append(f'P{n:02}空白纸面{blank:.2%}>38%')
        photos=[];cutouts=[];body=[];names=[];headings=[];circles=[];marks=[]
        for e in p.get('elements',[]):
            kind=e['kind']
            if kind=='image':
                with Image.open(asset_path(script.parent,e['path'])) as im:
                    transparent=im.mode=='RGBA' and im.getchannel('A').getextrema()[0]<255
                if transparent or e.get('mask'):cutouts.append(e['source_id'])
                elif e.get('photo_role'):
                    shadow=e.get('soft_shadow',{})
                    photos.append({'source_id':e['source_id'],'width_ratio':e['box'][2],
                                   'box':e['box'],'shadow':shadow,'fit':e.get('fit')})
                    if e.get('fit')!='cover':errors.append(f'P{n:02}矩形照片不是等比cover')
                    if shadow.get('offset')!=[6,8] or shadow.get('blur')!=10 or not .30<=shadow.get('opacity',0)<=.40:
                        errors.append(f'P{n:02}矩形照片缺少6/8、模糊10、透明度约0.35的柔影')
            elif kind=='disc_portrait':cutouts.append(e['source_id'])
            elif kind=='text':
                size=e.get('size',60);rgb=ImageColor.getrgb(e.get('fill','#FFFFFF'))
                if e.get('font','body')=='body':
                    body.append({'text':e['text'],'size':size,'width_ratio':e['box'][2],
                                 'lineheight_ratio':e.get('lineheight',size*1.5)/size})
                    if not 58<=size<=64:errors.append(f'P{n:02}正文{size}px不在58–64px')
                    if not .45<=e['box'][2]<=.60:errors.append(f'P{n:02}正文宽度{e["box"][2]:.1%}不在45–60%')
                    if not 1.45<=e.get('lineheight',size*1.5)/size<=1.55:errors.append(f'P{n:02}正文行高不是约1.5倍')
                if e.get('text_role')=='photo-name':
                    names.append(e)
                    if e.get('font')!='sans-bold' or not 28<=size<=34 or e.get('bg')!='#000000' or rgb!=(255,255,255):
                        errors.append(f'P{n:02}人名标签须黑底白字、黑体Bold、28–34px')
                if e.get('heading_level')=='primary':
                    headings.append(e['text'])
                    if max(rgb)>45 or e.get('font') not in ('serif-black','headline'):
                        errors.append(f'P{n:02}主标题未用黑色粗重字')
                t=next((a for a in record['text'] if a['text']==e['text'] and a['box']==e['box']),{})
                if 'MaShanZheng' in t.get('font_file',{}).get('path','') and max(rgb)-min(rgb)>35:
                    red_brush+=1
            if kind in ('hand_circle','hand_underline'):
                marks.append(e.get('target_text'));circles.append(e.get('target_text')) if kind=='hand_circle' else None
                if not e.get('target_text'):errors.append(f'P{n:02}手绘标记没有真实关键字目标')
                else:
                    import re
                    target=e['target_text']
                    tr=next((t for t in record['text'] if target in re.sub(r'\[\[|\]\]|\n','',t['text'])),{})
                    glyphs=[g for g in tr.get('glyphs',[]) if g.get('ink_bounds')]
                    start=''.join(g['char'] for g in glyphs).find(target)
                    if start<0:errors.append(f'P{n:02}手绘关键词缺少实际字形审计：{target}')
                    elif len({g['line'] for g in glyphs[start:start+len(target)]})>1:
                        errors.append(f'P{n:02}手绘关键词跨行变成大圈/长线：{target}')
        if not photos or max(e['width_ratio'] for e in photos)<.40:errors.append(f'P{n:02}缺少宽≥40%的矩形主照片')
        if len(cutouts)>1:errors.append(f'P{n:02}人物抠图{len(cutouts)}>1')
        if len(circles)>2:errors.append(f'P{n:02}红圈{len(circles)}>2')
        # 只核确名人物；匿名泳者不编名字。矩形/圆盘的名字标签须靠照片一角。
        identified={e['subject_name'] for e in p.get('elements',[]) if e['kind'] in ('image','disc_portrait') and e.get('subject_name')}
        for name in identified:
            if not any(name==t.get('person_name',t['text']) for t in names):errors.append(f'P{n:02}确名人物{name}缺少黑白人名标签')
        rows.append({'page':n,'blank_paper_ratio':round(blank,6),'rectangular_photos':photos,
                     'person_cutouts':cutouts,'body_blocks':body,'photo_name_labels':[e['text'] for e in names],
                     'black_primary_headings':headings,'red_circles':circles,'hand_marks':marks,'face_text_check':face_text})
    if red_brush>3:errors.append(f'全篇深红毛笔标题{red_brush}>3处')
    return {'profile':'light-editorial-v2','passed':not errors,'measurement':{
        'blank':'240宽等比LANCZOS；9×9反射边界局部窗口，RGB平均亮度标准差<3且亮度>170的成图像素占比；整页不排除照片/文字，不添加噪声凑密度',
        'blank_limit':.38,'body_size':[58,64],'body_width':[.45,.60],
        'photo':'原图不透明矩形、等比cover；每页≥1，主图宽≥40%，柔影6/8、10、0.35',
        'priority':'浅篇矩形照片取代暗篇抠图≥5页/圆盘≥2页配额；出现的抠图≤1且圆盘仍验露出≥40%，不因深红最多3处而强制每页彩色大字。'},
        'summary':{'blank_max':max((r['blank_paper_ratio'] for r in rows),default=0),
                   'blank_mean':sum(r['blank_paper_ratio'] for r in rows)/max(1,len(rows)),
                   'red_brush_count':red_brush,'rectangular_photo_pages':sum(bool(r['rectangular_photos']) for r in rows)},
        'pages':rows,'errors':errors}
