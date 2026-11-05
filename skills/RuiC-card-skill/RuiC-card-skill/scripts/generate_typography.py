"""Create an accurately typeset transparent text layer from project metadata."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import argparse,json,os

def create(project):
    root=Path(project);cfg=json.loads((root/'card-config.json').read_text(encoding='utf-8-sig'))
    with Image.open(root/'assets'/'background.png') as bg:W,H=bg.size
    candidates=[cfg.get('font'),str(Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'/'simkai.ttf'),'/System/Library/Fonts/STHeiti Light.ttc','/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc','/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf']
    font=next((p for p in candidates if p and Path(p).is_file()),None)
    if not font:raise RuntimeError('Provide config.font pointing to an installed font with glyph coverage')
    # Work on a consistent design canvas, scaling only the generated typography to the source size.
    im=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(im);sx=W/1024;sy=H/1536;gold=(244,208,135,255);cream=(255,241,206,255)
    def txt(x,y,value,size,anchor='la',fill=cream,max_width=850):
        size=max(8,round(size*sx));f=ImageFont.truetype(font,size)
        while d.textbbox((0,0),value,font=f)[2]>max_width*sx and size>10:size-=1;f=ImageFont.truetype(font,size)
        d.text((x*sx,y*sy),value,font=f,fill=fill,anchor=anchor,stroke_width=max(1,round(sx)),stroke_fill=(16,21,27,220))
    def line(y):d.line((70*sx,y*sy,954*sx,y*sy),fill=gold,width=max(1,round(2*sx)))
    txt(72,49,cfg.get('subtitle',''),25,fill=gold);txt(72,87,cfg.get('title',''),88,max_width=875)
    txt(76,195,cfg.get('collection',''),22,fill=gold);line(245);line(1280)
    txt(512,1300,cfg.get('tagline',''),31,anchor='ma',fill=gold);txt(512,1346,cfg.get('technique',''),69,anchor='ma')
    txt(72,1467,cfg.get('edition','001 / 001'),20,fill=gold);txt(950,1467,'HOLOGRAPHIC',18,anchor='ra',fill=gold,max_width=380)
    dest=root/'assets'/'text.png';im.save(dest);return dest
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('project');a=p.parse_args();print(create(a.project))
