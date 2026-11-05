"""图片等比硬规则。几何审计以实际resize尺寸或cover的源裁切区域计算。"""
from PIL import Image,ImageOps
from pathlib import Path
import json
import subprocess
import tempfile

def cell_faces(source,source_name=None):
 import sys
 if sys.platform!='darwin':raise ValueError('非macOS请提供已确认face_boxes；无人脸须人工确认后传空列表')
 with tempfile.TemporaryDirectory(prefix='cy-vision-') as td:
  folder=Path(td);picture=folder/'source.png';source.save(picture)
  inputs=folder/'input.json';output=folder/'faces.json';inputs.write_text(json.dumps([str(picture)]),encoding='utf-8')
  cache=Path(tempfile.gettempdir())/'cy-vision-module-cache';cache.mkdir(exist_ok=True)
  run=subprocess.run(['swift','-module-cache-path',str(cache),str(Path(__file__).with_name('检测人脸.swift')),str(inputs),str(output)],capture_output=True,text=True,encoding='utf-8',timeout=60)
  if run.returncode or not output.exists():raise ValueError('Vision不可用，不能跳过验脸；请提供已核实框：'+run.stderr[-600:])
  record=json.loads(output.read_text(encoding='utf-8'))[0]
  if record['status']!='success':raise ValueError('Vision失败：'+record.get('error','未知错误'))
  return record['faces'],'live-macOS-Vision'

def ratio_audit(source_region,target,method,**extra):
 sw,sh=source_region;tw,th=target
 if min(sw,sh,tw,th)<=0:raise ValueError('图片尺寸须为正数')
 error=abs((tw/th)/(sw/sh)-1)
 record={'method':method,'source_region_size':[sw,sh],'resized_size':[tw,th],'source_aspect':sw/sh,'rendered_aspect':tw/th,'aspect_error_ratio':error,'passed':error<=.01,**extra}
 if error>.01:raise ValueError(f'禁止拉伸：{method}图片宽高比误差{error:.3%}>1%；源区域{sw}×{sh}，缩放后{tw}×{th}')
 return record

def cover_cell(source,size,audit=None,source_name=None,focus=(.5,.35),face_boxes=None):
 """整页对照/盲测/缩略图：3:4格子，等比裁切铺满，参考长页裁切偏上。"""
 if abs(size[0]/size[1]-.75)>.001:raise ValueError('整页拼图格子须3:4')
 check={'mode':'same-aspect-no-crop','partial_face_ids':[]}
 if abs(source.width/source.height-size[0]/size[1])>.000001:
  if face_boxes is None:face_boxes,method=cell_faces(source,source_name)
  else:method='caller-verified-face-boxes'
  from 保脸裁切 import local_faces,safe_focus
  faces,_=local_faces({'face_boxes':face_boxes},source.size,source.size)
  focus,check=safe_focus(source.size,size,faces,focus);check['detector']=method;check['face_boxes']=face_boxes
 source=source.convert('RGB');pic=ImageOps.fit(source,size,Image.Resampling.LANCZOS,centering=focus)
 rec=fit_geometry(source.size,size,focus);rec.update(method='grid-cover',source=source_name,cell_size=list(size),focus=list(focus),black_padding=False,face_check=check)
 if audit is not None:audit.append(rec)
 return pic


def fit_geometry(source_size,target,focus=(.5,.5)):
 """ImageOps.fit默认bleed=0的真实源裁切窗口；裁切后再同比缩放。"""
 sw,sh=source_size;tw,th=target;aspect=tw/th
 if sw/sh>aspect:ch=sh;cw=sh*aspect
 else:cw=sw;ch=sw/aspect
 x=(sw-cw)*focus[0];y=(sh-ch)*focus[1]
 return ratio_audit((cw,ch),(tw,th),'cover-crop',source_size=list(source_size),source_crop_box=[x,y,x+cw,y+ch],scale_x=tw/cw,scale_y=th/ch)
