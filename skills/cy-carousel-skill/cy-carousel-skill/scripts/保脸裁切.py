"""检测框先换算到显式裁片，再调整cover focus；任何仍可见的人脸不得被截半。"""
from 图像等比 import fit_geometry

def local_faces(e,original_size,crop_size):
 sw,sh=original_size;crop=e.get('crop',[0,0,1,1]);b=[round(v*(sw if i%2==0 else sh)) for i,v in enumerate(crop)];faces=[];excluded=[]
 for i,(x,y,w,h) in enumerate(e.get('face_boxes',[])):
  f=[x*sw,y*sh,(x+w)*sw,(y+h)*sh];intersection=max(0,min(f[2],b[2])-max(f[0],b[0]))*max(0,min(f[3],b[3])-max(f[1],b[1]))
  if not intersection:excluded.append(i);continue
  if f[0]<b[0]-.01 or f[1]<b[1]-.01 or f[2]>b[2]+.01 or f[3]>b[3]+.01:raise ValueError(f'显式crop截断Vision人脸框#{i}，请移动/扩大裁片')
  faces.append({'id':i,'box':[f[0]-b[0],f[1]-b[1],f[2]-b[0],f[3]-b[1]]})
 return faces,excluded

def safe_focus(size,target,faces,preferred=(.5,.5)):
 base=fit_geometry(size,target,preferred);cw,ch=base['source_region_size'];sw,sh=size;dx=sw-cw;dy=sh-ch
 xs={max(0,min(dx,dx*preferred[0])),0,dx};ys={max(0,min(dy,dy*preferred[1])),0,dy}
 for f in faces:
  a,b,c,d=f['box'];xs.update([max(0,min(dx,a-2)),max(0,min(dx,c+2-cw))]);ys.update([max(0,min(dy,b-2)),max(0,min(dy,d+2-ch))])
 candidates=[]
 for x in xs:
  for y in ys:
   kept=[];cut=[];excluded=[]
   for f in faces:
    a,b,c,d=f['box'];inter=max(0,min(c,x+cw)-max(a,x))*max(0,min(d,y+ch)-max(b,y))
    if not inter:excluded.append(f['id'])
    elif a>=x-.01 and b>=y-.01 and c<=x+cw+.01 and d<=y+ch+.01:kept.append(f['id'])
    else:cut.append(f['id'])
   if not cut and (kept or not faces):
    score=((x-dx*preferred[0])/max(sw,1))**2+((y-dy*preferred[1])/max(sh,1))**2-len(kept)*.0001
    candidates.append((score,x,y,kept,excluded))
 if not candidates:raise ValueError('当前cover框无法完整保留可见人脸，须调整图框/原裁片或换图；不允许拉伸/留边')
 _,x,y,kept,excluded=min(candidates);focus=[x/dx if dx>1e-7 else .5,y/dy if dy>1e-7 else .5]
 return focus,{'detected_local_faces':faces,'retained_face_ids':kept,'wholly_excluded_face_ids':excluded,'partial_face_ids':[],'focus':focus,'source_crop_box':[x,y,x+cw,y+ch]}
