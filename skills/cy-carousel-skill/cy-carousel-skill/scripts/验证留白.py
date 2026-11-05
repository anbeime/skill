"""历史暗色篇留白统计；浅色篇使用浅色排版.blank_paper。"""
from pathlib import Path
from PIL import Image
import numpy as np
from 图像等比 import cover_cell
import argparse,json

def measure(path):
 with Image.open(path) as image:a=np.asarray(cover_cell(image,(360,480)).convert('L'),dtype=float)
 best=cur=0
 for empty in (a.max(1)-a.min(1)<18):cur=cur+1 if empty else 0;best=max(best,cur)
 tiles=[a[y:y+30,x:x+30] for y in range(0,480,30) for x in range(0,360,30)]
 return round(sum(v.max()-v.min()<18 for v in tiles)/len(tiles)*100),round(best/480*100)

def check(paths):
 rows=[dict(page=i,empty_tiles=t,empty_band=b) for i,(t,b) in enumerate(map(measure,paths),1)]
 errors=[];mean=sum(r['empty_tiles'] for r in rows)/max(1,len(rows))
 if not rows:errors.append('没有传入内页')
 if mean>20:errors.append(f'暗篇空格子均值{mean:.1f}%>20%')
 if sum(r['empty_tiles']>22 for r in rows)>4:errors.append('空格子>22%的页面超过4页')
 errors.extend(f'P{r["page"]:02}连续空带{r["empty_band"]}%>12%' for r in rows if r['empty_band']>12)
 return {'passed':not errors,'mean_empty_tiles':mean,'pages':rows,'errors':errors}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('images',type=Path,nargs='+');a=ap.parse_args();r=check(a.images)
 print(json.dumps(r,ensure_ascii=False,indent=2));raise SystemExit(0 if r['passed'] else 1)
