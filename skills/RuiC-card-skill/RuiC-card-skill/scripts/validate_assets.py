"""Validate four equal-size image layers and genuine transparent alpha.

When subject/text lacks an alpha channel but carries a painted checkerboard
(gray/white grid some image tools return instead of transparency), the board
is converted to real alpha via checkerboard_to_alpha.py before validation.
"""
from pathlib import Path
from PIL import Image,ImageStat
import argparse,json

def validate(project):
    root=Path(project);report={};size=None
    # The effects layer is optional, but when present it is held to the same bar as
    # the other RGBA layers: same canvas, real alpha, nothing empty.
    names=['subject','background','lineart','text']
    if (root/'assets'/'effects.png').exists():names.insert(1,'effects')
    for name in names:
        file=root/'assets'/(name+'.png')
        im=Image.open(file)
        if im.format!='PNG':raise ValueError(str(file)+' is not a PNG')
        if not size:size=im.size
        if im.size!=size:raise ValueError('Layer dimensions differ: '+name)
        if min(im.size)<256:raise ValueError('Artwork is too small')
        item={'size':im.size,'mode':im.mode}
        if name in ['subject','text','effects']:
            if 'A' not in im.getbands():
                # Some image tools paint a checkerboard into RGB instead of
                # returning alpha. Convert it deterministically when present.
                im=im.convert('RGB')
                try:
                    import checkerboard_to_alpha as c2a
                    det=c2a.detect_checkerboard(im)
                except ImportError:
                    det=None
                if det:
                    out,fix=c2a.convert_to_alpha(im,det)
                    im.close();out.save(file)
                    im=Image.open(file)
                    item['mode']=im.mode
                    item['checkerboard_fixed']=fix
                    item['note']='painted checkerboard converted to true alpha'
                else:
                    raise ValueError(name+' lacks real alpha; a painted checkerboard is invalid (or install numpy to auto-convert it)')
            alpha=im.getchannel('A');hist=alpha.histogram();transparent=sum(hist[:16])/sum(hist);solid=sum(hist[128:])/sum(hist)
            if transparent<.01 or solid<.001:raise ValueError(name+' needs both visible and truly transparent pixels')
            item.update(transparent_fraction=round(transparent,4),visible_fraction=round(solid,4))
        if name=='lineart':
            lo,hi=im.convert('L').getextrema()
            if lo>80 or hi<230:raise ValueError('Line art needs dark contours on white')
        report[name]=item
        im.close()
    (root/'asset-validation.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf8');return report
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('project');a=p.parse_args();print(json.dumps(validate(a.project),indent=2,ensure_ascii=False))
