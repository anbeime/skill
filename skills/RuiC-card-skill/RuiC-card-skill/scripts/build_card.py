import bpy, math, os, json
from pathlib import Path
from mathutils import Vector, Quaternion
import sys
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
R=Path(args[0]).resolve() if args else Path.cwd()
CFG=json.loads((R/'card-config.json').read_text(encoding='utf-8-sig'))
(R/'renders').mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for g in list(bpy.data.node_groups):
    if g.bl_idname=='ShaderNodeTree': bpy.data.node_groups.remove(g)
scene=bpy.context.scene
scene.render.engine='CYCLES'; scene.cycles.samples=32
scene.cycles.use_denoising=True
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type='OPTIX'; prefs.get_devices()
    gpu=False
    for dev in prefs.devices:
        dev.use=dev.type!='CPU'; gpu=gpu or dev.use
    if gpu: scene.cycles.device='GPU'
except Exception as e: print('GPU fallback',e)
scene.render.resolution_x=1080; scene.render.resolution_y=1500; scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'; scene.render.image_settings.color_mode='RGBA'
scene.render.film_transparent=False
scene.view_settings.view_transform='AgX'
scene.view_settings.look='AgX - Medium High Contrast'
scene.render.fps=24; scene.frame_start=1; scene.frame_end=96
world=bpy.data.worlds.new('深靛摄影棚'); scene.world=world; world.use_nodes=True
world.node_tree.nodes['Background'].inputs['Color'].default_value=(.045,.065,.10,1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value=.4

def node(tree,typ,name,x=0,y=0):
    n=tree.nodes.new(typ); n.name=name; n.label=name; n.location=(x,y); return n
def link(t,a,ao,b,bi): t.links.new(a.outputs[ao],b.inputs[bi])
def val(t,op,name,x,y,a=None,b=None):
    n=node(t,'ShaderNodeMath',name,x,y); n.operation=op
    if a is not None: n.inputs[0].default_value=a
    if b is not None: n.inputs[1].default_value=b
    return n
def vec(t,op,name,x,y):
    n=node(t,'ShaderNodeVectorMath',name,x,y); n.operation=op; return n
def socket(g,name,direction,kind,default=None):
    s=g.interface.new_socket(name=name,in_out=direction,socket_type=kind)
    if default is not None: s.default_value=default
    return s
# Reusable view-dependent UV offset. Surface normal controls grazing-angle denominator.
g=bpy.data.node_groups.new('视差 · 通用 UV / Parallax','ShaderNodeTree')
socket(g,'缩放','INPUT','NodeSocketFloat',1.25); socket(g,'深度','INPUT','NodeSocketFloat',.4)
socket(g,'视差效果','OUTPUT','NodeSocketVector')
ni=node(g,'NodeGroupInput','只调缩放与深度',-1000,320); no=node(g,'NodeGroupOutput','视差效果',920,200)
uv=node(g,'ShaderNodeTexCoord','纹理坐标 UV',-1000,100)
sub=vec(g,'SUBTRACT','中心归零 UV − 0.5',-800,100); sub.inputs[1].default_value=(.5,.5,.5); link(g,uv,'UV',sub,0)
fma=vec(g,'MULTIPLY_ADD','缩放后加回中心',-570,100); fma.inputs[2].default_value=(.5,.5,.5); link(g,sub,0,fma,0); link(g,ni,'缩放',fma,1)
geo=node(g,'ShaderNodeNewGeometry','几何数据 · 视线及法向',-1000,-210)
normal=node(g,'ShaderNodeVectorTransform','法向 世界 → 物体',-800,-220); normal.vector_type='NORMAL'; normal.convert_from='WORLD'; normal.convert_to='OBJECT'; link(g,geo,'Normal',normal,'Vector')
view=node(g,'ShaderNodeVectorTransform','视线 世界 → 物体',-800,-450); view.vector_type='VECTOR'; view.convert_from='WORLD'; view.convert_to='OBJECT'; link(g,geo,'Incoming',view,'Vector')
dot=vec(g,'DOT_PRODUCT','视线与法向夹角',-550,-270); link(g,normal,0,dot,0); link(g,view,0,dot,1)
ab=val(g,'ABSOLUTE','正向角度',-330,-270); link(g,dot,'Value',ab,0)
cl=val(g,'MAXIMUM','限制掠射角防止 UV 爆开',-130,-270,b=.35); link(g,ab,0,cl,0)
dep=val(g,'MULTIPLY','深度 × 位移单位 0.14',-330,-530,b=.14); link(g,ni,'深度',dep,0)
div=val(g,'DIVIDE','深度 / 夹角',80,-300); link(g,dep,0,div,0); link(g,cl,0,div,1)
xy=vec(g,'MULTIPLY','仅保留平面 XY',-320,-730); xy.inputs[1].default_value=(1,1,0); link(g,view,0,xy,0)
sc=vec(g,'SCALE','矢量缩放 · 深度',310,-160); link(g,xy,0,sc,0); link(g,div,0,sc,'Scale')
add=vec(g,'ADD','居中 UV + 视线偏移',650,200); link(g,fma,0,add,0); link(g,sc,0,add,1); link(g,add,0,no,'视差效果')
g['说明']='缩放控制 UV。深度正负控制前后反向视差；物体 X 旋转须保留 90°。法向变换用于视线夹角，额外视线变换用于真实平面偏移。'
# Angle-dependent foil shared by face and edges.
f=bpy.data.node_groups.new('镭射 · 条带与木版花纹','ShaderNodeTree'); socket(f,'UV','INPUT','NodeSocketVector'); socket(f,'全息颜色','OUTPUT','NodeSocketColor'); socket(f,'条纹遮罩','OUTPUT','NodeSocketFloat')
fi=node(f,'NodeGroupInput','纹理输入',-1100,250); fo=node(f,'NodeGroupOutput','镭射输出',950,180)
fg=node(f,'ShaderNodeNewGeometry','几何视线',-1100,-130)
vt=node(f,'ShaderNodeVectorTransform','视线到卡牌局部',-900,-130); vt.vector_type='VECTOR'; vt.convert_from='WORLD'; vt.convert_to='OBJECT'; link(f,fg,'Incoming',vt,0)
vs=vec(f,'SCALE','转卡驱动镭射位移',-710,-130); vs.inputs['Scale'].default_value=2.4; link(f,vt,0,vs,0)
ad=vec(f,'ADD','UV + 角度',-520,270); link(f,fi,'UV',ad,0); link(f,vs,0,ad,1)
mp=node(f,'ShaderNodeMapping','映射 · Y 32°',-330,350); mp.inputs['Rotation'].default_value[1]=math.radians(32); link(f,ad,0,mp,0)
wave=node(f,'ShaderNodeTexWave','条带 · 0.55 / 畸变 7',-80,400); wave.wave_type='BANDS'; wave.bands_direction='X'; wave.inputs['Scale'].default_value=.55; wave.inputs['Distortion'].default_value=7; wave.inputs['Detail Scale'].default_value=1.5; link(f,mp,0,wave,0)
mp2=node(f,'ShaderNodeMapping','映射副本 · 花纹 UV',-700,-420); link(f,fi,'UV',mp2,0)
pat=node(f,'ShaderNodeTexNoise','木版颗粒花纹',-460,-420); pat.inputs['Scale'].default_value=94; pat.inputs['Detail'].default_value=2; link(f,mp2,0,pat,0)
mul=node(f,'ShaderNodeMixRGB','正片叠底',150,250); mul.blend_type='MULTIPLY'; mul.inputs[0].default_value=.55; link(f,wave,'Color',mul,1); link(f,pat,'Color',mul,2)
plus=node(f,'ShaderNodeMixRGB','相加 · 花纹',350,250); plus.blend_type='ADD'; plus.inputs[0].default_value=.12; link(f,mul,0,plus,1); link(f,pat,'Fac',plus,2)
ramp=node(f,'ShaderNodeValToRGB','粉 → 黄 → 蓝 → 白',560,250)
ramp.color_ramp.elements.remove(ramp.color_ramp.elements[1]); ramp.color_ramp.elements[0].position=.0; ramp.color_ramp.elements[0].color=(.7,.10,.34,1)
for pos,col in [(.35,(1,.68,.16,1)),(.68,(.10,.48,1,1)),(1,(1,1,1,1))]: ramp.color_ramp.elements.new(pos).color=col
link(f,plus,0,ramp,0); link(f,ramp,0,fo,'全息颜色')
mask=node(f,'ShaderNodeValToRGB','窄条纹发光遮罩',370,-80); mask.color_ramp.elements[0].position=.76; mask.color_ramp.elements[1].position=.94; link(f,wave,'Fac',mask,0); link(f,mask,0,fo,'条纹遮罩')
# Loaded images are kept separate and packed for portable blend.
images={k:bpy.data.images.load(str(R/'assets'/v),check_existing=True) for k,v in {'subject':'subject.png','text':'text.png','background':'background.png','lineart':'lineart.png'}.items()}
if (R/'assets'/'effects.png').exists(): images['effects']=bpy.data.images.load(str(R/'assets'/'effects.png'),check_existing=True)
images['lineart'].colorspace_settings.name='Non-Color'
has_fx='effects' in images
def material(name):
    m=bpy.data.materials.new(name); m.use_nodes=True; m.node_tree.nodes.clear(); return m,m.node_tree

def parallax(t,name,scale,depth,x,y):
    n=node(t,'ShaderNodeGroup',name,x,y); n.node_tree=g; n.inputs['缩放'].default_value=scale; n.inputs['深度'].default_value=depth; return n

def tex(t,key,name,p,x,y):
    n=node(t,'ShaderNodeTexImage',name,x,y); n.image=images[key]; n.extension='CLIP' if key in ('subject','text','lineart','effects') else 'EXTEND'; link(t,p,'视差效果',n,'Vector'); return n

def bsdf(t,name,x,y):
    b=node(t,'ShaderNodeBsdfPrincipled',name,x,y); b.inputs['Metallic'].default_value=1; b.inputs['Roughness'].default_value=1; b.inputs['Emission Color'].default_value=(0,0,0,1); return b

def foil(t,p,x,y):
    n=node(t,'ShaderNodeGroup','镭射条带',x,y); n.node_tree=f; link(t,p,'视差效果',n,'UV'); return n
main,t=material('01 · 主体 + 背景 / 核心合成')
out=node(t,'ShaderNodeOutputMaterial','最终表面',1760,360)
pS=parallax(t,'主体 · 1.25 / 0.28',1.25,.28,-1200,620); pB=parallax(t,'背景 · 1 / −0.2',1,-.2,-1200,-160)
sT=tex(t,'subject','主体角色 PNG · 换卡替换这里',pS,-950,600); bT=tex(t,'background','背景图 · 换卡替换这里',pB,-950,-140)
fs=foil(t,pS,-930,260); fb=foil(t,pB,-930,-500)
over=node(t,'ShaderNodeMixRGB','叠加 · 主体镭射',-550,570); over.blend_type='OVERLAY'; over.inputs[0].default_value=.22; link(t,sT,'Color',over,1); link(t,fs,'全息颜色',over,2)
sB=bsdf(t,'主体原理化 · 金属1 / 糙度1',-260,550); link(t,over,0,sB,'Base Color')
bov=node(t,'ShaderNodeMixRGB','背景轻镭射',-550,-180); bov.blend_type='OVERLAY'; bov.inputs[0].default_value=.18; link(t,bT,'Color',bov,1); link(t,fb,'全息颜色',bov,2)
bB=bsdf(t,'背景原理化 · 金属1 / 糙度1',-260,-140); link(t,bov,0,bB,'Base Color')
# Subtle illumination preserves printing under metallic finish without emitting from subject BSDF.
se=node(t,'ShaderNodeEmission','只让镭射条纹发光',-60,90); link(t,fs,'全息颜色',se,'Color')
sm=val(t,'MULTIPLY','条纹强度',-320,90,b=.34); link(t,fs,'条纹遮罩',sm,0); link(t,sm,0,se,'Strength')
sa=node(t,'ShaderNodeAddShader','主体 + 条纹',270,530); link(t,sB,0,sa,0); link(t,se,0,sa,1)
# White-background contour threshold, restricted to a moving foil sweep.
lt=tex(t,'lineart','白底线描图 · 换卡替换这里',pS,-900,1080)
lr=node(t,'ShaderNodeValToRGB','阈值 · 黑底白线',-630,1080); lr.color_ramp.elements[0].position=.06; lr.color_ramp.elements[0].color=(1,1,1,1); lr.color_ramp.elements[1].position=.25; lr.color_ramp.elements[1].color=(0,0,0,1); link(t,lt,'Color',lr,0)
lh=node(t,'ShaderNodeHueSaturation','线描饱和度 0',-400,1060); lh.inputs['Saturation'].default_value=0; link(t,lr,0,lh,'Color')
le=node(t,'ShaderNodeEmission','线描自发光 · 40',-160,1060); le.inputs['Color'].default_value=(1,1,1,1); le.inputs['Strength'].default_value=40
lm=val(t,'MULTIPLY','线描 × 镭射扫光',-160,840); link(t,lh,0,lm,0); link(t,fs,'条纹遮罩',lm,1)
la=val(t,'MULTIPLY','限制辉光覆盖 0.018',60,840,b=.018); link(t,lm,0,la,0)
ls=node(t,'ShaderNodeMixShader','线描发光与镭射结果混合',520,600); link(t,la,0,ls,0); link(t,sa,0,ls,1); link(t,le,0,ls,2)
# Voronoi edge star flecks, sparse corners multiplied by animated 4D noise.
v=node(t,'ShaderNodeTexVoronoi','闪星 · 距离到边缘',-550,-680); v.feature='DISTANCE_TO_EDGE'; v.inputs['Scale'].default_value=105; link(t,pB,'视差效果',v,'Vector')
vr=node(t,'ShaderNodeValToRGB','细闪点阈值',-310,-660); vr.color_ramp.elements[0].position=.012; vr.color_ramp.elements[0].color=(1,1,1,1); vr.color_ramp.elements[1].position=.04; vr.color_ramp.elements[1].color=(0,0,0,1); link(t,v,'Distance',vr,0)
hs=node(t,'ShaderNodeHueSaturation','闪星色相饱和度明度',-70,-650); hs.inputs['Saturation'].default_value=.6; link(t,vr,0,hs,'Color')
noise=node(t,'ShaderNodeTexNoise','闪烁 · 四维噪波',-550,-990); noise.noise_dimensions='4D'; noise.inputs['Scale'].default_value=165; noise.inputs['W'].default_value=0; noise.inputs['W'].keyframe_insert('default_value',frame=1); noise.inputs['W'].default_value=2; noise.inputs['W'].keyframe_insert('default_value',frame=96); link(t,pB,'视差效果',noise,'Vector')
nr=node(t,'ShaderNodeValToRGB','稀疏星点',-300,-980); nr.color_ramp.elements[0].position=.70; nr.color_ramp.elements[1].position=.79; link(t,noise,'Fac',nr,0)
st=val(t,'MULTIPLY','星点 × 闪烁',160,-650); link(t,hs,0,st,0); link(t,nr,0,st,1)
stren=val(t,'MULTIPLY','闪星亮度',370,-650,b=5); link(t,st,0,stren,0)
be=node(t,'ShaderNodeEmission','背景闪星自发光',600,-330); be.inputs['Color'].default_value=(.70,.88,1,1); link(t,stren,0,be,'Strength')
ba=node(t,'ShaderNodeAddShader','背景 + 闪星',860,-140); link(t,bB,0,ba,0); link(t,be,0,ba,1)
mix=node(t,'ShaderNodeMixShader','主体 Alpha 叠加背景',1340,400); link(t,sT,'Alpha',mix,0); link(t,ba,0,mix,1); link(t,ls,0,mix,2)
# Effects layer (sparks/thorns deco): above the character, below the text plane,
# on its own mid-depth parallax so it floats between subject (0.28) and text (0).
pE=None
if has_fx:
    pE=parallax(t,'特效 · 1 / 0.14',1,.14,-1200,-900)
    eT=tex(t,'effects','特效荆棘 PNG · 换卡替换这里',pE,-950,-880)
    fE=foil(t,pE,-930,-1080)
    eov=node(t,'ShaderNodeMixRGB','特效轻镭射',-560,-860); eov.blend_type='OVERLAY'; eov.inputs[0].default_value=.12; link(t,eT,'Color',eov,1); link(t,fE,'全息颜色',eov,2)
    eB=bsdf(t,'特效原理化 · 金属1 / 糙度1',-270,-860); link(t,eov,0,eB,'Base Color')
    emix=node(t,'ShaderNodeMixShader','特效 Alpha 叠加',1560,400); link(t,eT,'Alpha',emix,0); link(t,mix,0,emix,1); link(t,eB,0,emix,2); link(t,emix,0,out,'Surface')
else:
    link(t,mix,0,out,'Surface')
# Text plane at zero parallax.
textmat,tt=material('02 · 文字透明 / 深度0')
tp=parallax(tt,'文字 · 1 / 0',1,0,-650,250); tx=tex(tt,'text','文字 PNG · 换卡替换这里',tp,-420,250); tb=bsdf(tt,'文字原理化',-130,300); link(tt,tx,'Color',tb,'Base Color')
# A small text-only emission guarantees typography stays readable at oblique angles.
link(tt,tx,'Color',tb,'Emission Color'); tb.inputs['Emission Strength'].default_value=.35
trans=node(tt,'ShaderNodeBsdfTransparent','透明底',-130,0); tm=node(tt,'ShaderNodeMixShader','文字 Alpha',220,220); link(tt,tx,'Alpha',tm,0); link(tt,trans,0,tm,1); link(tt,tb,0,tm,2); to=node(tt,'ShaderNodeOutputMaterial','文字表面',460,220); link(tt,tm,0,to,'Surface')
# Edge slot: only holographic chain plus Bright/Contrast; black base.
edge,et=material('03 · 卡边镭射 / 材质槽2')
eu=node(et,'ShaderNodeTexCoord','卡边坐标',-650,0); ef=node(et,'ShaderNodeGroup','仅保留镭射',-430,0); ef.node_tree=f; link(et,eu,'UV',ef,'UV')
eb=node(et,'ShaderNodeBrightContrast','亮度1',-180,0); eb.inputs['Bright'].default_value=1; link(et,ef,'全息颜色',eb,'Color')
ep=bsdf(et,'卡边黑色金属',50,0); ep.inputs['Base Color'].default_value=(0,0,0,1); ep.inputs['Roughness'].default_value=.32; link(et,eb,0,ep,'Emission Color'); ep.inputs['Emission Strength'].default_value=.42
eo=node(et,'ShaderNodeOutputMaterial','镭射卡边',390,0); link(et,ep,0,eo,'Surface')
gold,gt=material('04 · 古金压边'); gp=bsdf(gt,'古金金属',0,0); gp.inputs['Base Color'].default_value=(.63,.37,.10,1); gp.inputs['Roughness'].default_value=.29; go=node(gt,'ShaderNodeOutputMaterial','金边',360,0); link(gt,gp,0,go,0)
back,bt=material('05 · 背面靛蓝'); bp=bsdf(bt,'靛蓝背面',0,0); bp.inputs['Base Color'].default_value=(.009,.02,.036,1); bo=node(bt,'ShaderNodeOutputMaterial','背面',350,0); link(bt,bp,0,bo,0)
# Collection and parent pivot keep every imported plane's X rotation visibly at 90 degrees.
cardcol=bpy.data.collections.new('卡牌 · 可复用成品'); scene.collection.children.link(cardcol)
refcol=bpy.data.collections.new('素材平面 · 背景参考'); scene.collection.children.link(refcol)
def move_col(o,c):
    for coll in list(o.users_collection): coll.objects.unlink(o)
    c.objects.link(o)
pivot=bpy.data.objects.new('转卡控制 · 播放时间线预览',None); cardcol.objects.link(pivot)
pivot['主体缩放']=CFG.get('parameters',{}).get('subjectScale',1.25); pivot['主体深度']=CFG.get('parameters',{}).get('subjectDepth',.4); pivot['背景深度']=CFG.get('parameters',{}).get('backgroundDepth',-.25)
pivot['特效缩放']=CFG.get('parameters',{}).get('effectsScale',1); pivot['特效深度']=CFG.get('parameters',{}).get('effectsDepth',.14)
pivot['使用说明']='材质的参数已通过驱动关联到此物体自定义属性。播放 1–96 帧查看闪卡。'
driver_pairs=[(pS,'缩放','主体缩放'),(pS,'深度','主体深度'),(pB,'深度','背景深度')]
if has_fx: driver_pairs += [(pE,'缩放','特效缩放'),(pE,'深度','特效深度')]
for n,inp,prop in driver_pairs:
    fc=n.inputs[inp].driver_add('default_value'); dr=fc.driver; dr.type='SCRIPTED'; v=dr.variables.new(); v.name='value'; v.targets[0].id=pivot; v.targets[0].data_path='["'+prop+'"]'; dr.expression='value'

def perimeter(w,h,r,n=12):
    pts=[]
    for cx,cy,start in [(w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),(-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)]:
        for j in range(n+1):
            a=math.radians(start+j*90/n); pts.append((cx+r*math.cos(a),cy+r*math.sin(a)))
    return pts

def plane(name,w,h,mat,y=0,thickness=0,coll=cardcol):
    pts=perimeter(w,h,.20); N=len(pts); verts=[(x,z,0) for x,z in pts]; faces=[tuple(range(N))]
    if thickness:
        verts += [(x,z,-thickness) for x,z in pts]; faces += [tuple(reversed(range(N,2*N)))]
        faces += [(i,(i+1)%N,(i+1)%N+N,i+N) for i in range(N)]
    me=bpy.data.meshes.new(name+'网格'); me.from_pydata(verts,[],faces); me.update(); o=bpy.data.objects.new(name,me); coll.objects.link(o)
    o.location=(0,0,0); o.rotation_euler=(math.pi/2,0,0); o.location.y=y; o.parent=pivot
    me.materials.append(mat)
    if thickness:
        me.materials.append(edge); me.materials.append(back)
        for pol in me.polygons:
            if pol.index==1: pol.material_index=2
            elif pol.index>1: pol.material_index=1
    layer=me.uv_layers.new(name='UVMap')
    for pol in me.polygons:
        for li in pol.loop_indices:
            co=me.vertices[me.loops[li].vertex_index].co; layer.data[li].uv=(co.x/w+.5,co.y/h+.5)
    o['导入约定']='Alt+G 清空位置；物体模式 X=90°，未应用旋转。'
    return o
card=plane('主体平面 · 完整视差合成',6.3,9.45,main,0,.045)
textob=plane('文字平面 · Alpha PNG',6.3,9.45,textmat,-.014)
# Relief mode: subject / effects / text become separate physical planes (lightbox
# diorama). The front face keeps only background + foil laminate; the subject mix
# is disconnected so the character does not double-draw.
RELIEF=CFG.get('sourceMode')=='relief'
layers_cfg=CFG.get('layers',{}) if RELIEF else {}
relief_objs=[]
if RELIEF:
    if mix.inputs[0].links: t.links.remove(mix.inputs[0].links[0])
    def relief_y(d): return -(0.541+1.818*d)
    textob.location.y=relief_y(layers_cfg.get('text',{}).get('depth',.72))
    def apply_crop_uv(o,w,h,crop_uv):
        me=o.data; layer=me.uv_layers.active or me.uv_layers[0]
        u0,v0,u1,v1=crop_uv
        for pol in me.polygons:
            for li in pol.loop_indices:
                x,z=me.vertices[me.loops[li].vertex_index].co[:2]
                u,v=(x/w+.5),(z/h+.5)
                layer.data[li].uv=(u0+u*(u1-u0),v0+v*(v1-v0))
    def norm_crop(key,crop):
        if not crop: return None
        iw,ih=images[key].size; x0,y0,x1,y1=crop
        # crop is given top-left-origin pixels; Blender V=1 is the image top
        return (x0/iw, 1-y1/ih, x1/iw, 1-y0/ih)
    def relief_plane(name,w,h,mat,y,offset=(0,0),crop_uv=None):
        rr=min(.2,min(w,h)*.15)
        pts=perimeter(w,h,rr); N=len(pts)
        verts=[(x,z+offset[1],0) for x,z in pts]; faces=[tuple(range(N))]
        me=bpy.data.meshes.new(name+'网格'); me.from_pydata(verts,[],faces); me.update(); o=bpy.data.objects.new(name,me); cardcol.objects.link(o)
        o.rotation_euler=(math.pi/2,0,0); o.location=(offset[0],y,0); o.parent=pivot
        me.materials.append(mat)
        layer=me.uv_layers.new(name='UVMap')
        for pol in me.polygons:
            for i,li in enumerate(pol.loop_indices):
                x,z=pts[i]; u,v=(x/w+.5),(z/h+.5)
                if crop_uv is not None:
                    u0,v0,u1,v1=crop_uv
                    u=u0+u*(u1-u0); v=v0+v*(v1-v0)
                layer.data[li].uv=(u,v)
        o['导入约定']='浮雕独立层：几何内嵌偏移与裁切 UV，物体 X=90°，未应用旋转。'
        return o
    def relief_mat(name,key):
        m,rt=material(name)
        tn=node(rt,'ShaderNodeTexImage',name+' texture',-400,100); tn.image=images[key]; tn.extension='CLIP'
        bs=bsdf(rt,'Printed relief',-100,100); link(rt,tn,'Color',bs,'Base Color')
        tr=node(rt,'ShaderNodeBsdfTransparent','Clear cutout',-100,-200)
        mx=node(rt,'ShaderNodeMixShader','Cutout alpha',200,100); link(rt,tr,0,mx,1); link(rt,bs,0,mx,2)
        if images[key].channels==4:
            link(rt,tn,'Alpha',mx,0)
        else:
            lum=node(rt,'ShaderNodeRGBToBW','Effect luminance',-400,-150)
            ramp=node(rt,'ShaderNodeValToRGB','Black-background effect matte',-120,-150)
            ramp.color_ramp.elements[0].position=.0; ramp.color_ramp.elements[0].color=(0,0,0,1)
            ramp.color_ramp.elements[1].position=.08; ramp.color_ramp.elements[1].color=(1,1,1,1)
            link(rt,tn,'Color',lum,0); link(rt,lum,0,ramp,0); link(rt,ramp,0,mx,0)
        o=node(rt,'ShaderNodeOutputMaterial','Relief surface',450,100); link(rt,mx,0,o,'Surface')
        return m
    sub=layers_cfg.get('subject',{})
    subob=relief_plane('Relief subject',sub.get('width',6.9),sub.get('height',10.98),relief_mat('Relief / subject','subject'),relief_y(sub.get('depth',.28)),tuple(sub.get('offset',[0,-0.1])),norm_crop('subject',sub.get('crop')))
    relief_objs.append(subob)
    if has_fx:
        ef=layers_cfg.get('effects',{})
        fxob=relief_plane('Relief effects',ef.get('width',7.2),ef.get('height',10.8),relief_mat('Relief / effects','effects'),relief_y(ef.get('depth',.5)),tuple(ef.get('offset',[0,-0.3])),norm_crop('effects',ef.get('crop')))
        relief_objs.append(fxob)
    # Text: the full-card text plane can be UV-cropped (e.g. keep only the bottom
    # line), and an enlarged title plane can be added as its own floating layer.
    tcfg=layers_cfg.get('text',{})
    tfull_crop=norm_crop('text',tcfg.get('crop'))
    if tfull_crop is not None: apply_crop_uv(textob,6.3,9.45,tfull_crop)
    ttitle=layers_cfg.get('textTitle')
    if ttitle:
        tw=ttitle.get('width',6.3); th=ttitle.get('height',.85)
        tobj=relief_plane('文字平面 · 标题',tw,th,textmat,relief_y(tcfg.get('depth',.72)),tuple(ttitle.get('offset',[0,0])),norm_crop('text',ttitle.get('crop')))
        relief_objs.append(tobj)
# The physical background import is hidden because its BSDF is already mixed into the front face.
bgmat,bgt=material('06 · 独立背景参考'); bpg=parallax(bgt,'背景复用 · −0.2',1,-.2,-500,100); btex=tex(bgt,'background','背景 PNG',bpg,-280,100); bbs=bsdf(bgt,'背景原理化',0,100); link(bgt,btex,0,bbs,'Base Color'); bout=node(bgt,'ShaderNodeOutputMaterial','表面',350,100); link(bgt,bbs,0,bout,0)
bgo=plane('背景平面 · 已在主体材质合成',6.3,9.45,bgmat,.025,coll=refcol); bgo.hide_render=True; bgo.hide_set(True)

def ring(name,w,h,width,mat,y):
    outer=perimeter(w,h,.20); inner=perimeter(w-width*2,h-width*2,max(.20-width,.01)); N=len(outer)
    verts=[(x,z,0) for x,z in outer+inner]; faces=[(i,(i+1)%N,(i+1)%N+N,i+N) for i in range(N)]
    me=bpy.data.meshes.new(name); me.from_pydata(verts,[],faces); me.update(); ob=bpy.data.objects.new(name,me); cardcol.objects.link(ob); ob.parent=pivot; ob.rotation_euler.x=math.pi/2; ob.location.y=y; me.materials.append(mat)
    uv=me.uv_layers.new(name='UVMap')
    for pol in me.polygons:
        for li in pol.loop_indices:
            v=me.vertices[me.loops[li].vertex_index].co; uv.data[li].uv=(v.x/w+.5,v.y/h+.5)
    return ob
ring('外圈 · 全息压边',6.3,9.45,.060,edge,-.025)
ring('内圈 · 古金细边',6.13,9.28,.018,gold,-.026)
for frame,ang in [(1,(-3,0,-14)),(25,(2,0,0)),(49,(4,0,14)),(73,(-2,0,0)),(96,(-3,0,-14))]:
    pivot.rotation_euler=[math.radians(x) for x in ang]; pivot.keyframe_insert('rotation_euler',frame=frame)
# Camera and studio lights.
def aim(o,p): o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(0,-20,0)); cam=bpy.context.object; cam.name='成品相机'; aim(cam,(0,0,0)); cam.data.type='ORTHO'; cam.data.ortho_scale=11.25; scene.camera=cam
for name,loc,energy,size,color in [('柔光主灯',(-3,-8,4),2100,9,(1,.90,.72)),('正面均匀补光',(3,-7,-2),1650,8,(.72,.85,1)),('顶部金光',(0,-4,7),800,5,(1,.70,.32))]:
    bpy.ops.object.light_add(type='AREA',location=loc); o=bpy.context.object; o.name=name; o.data.energy=energy; o.data.shape='DISK'; o.data.size=size; o.data.color=color; aim(o,(0,0,0))
# Compositor glow.
scene.use_nodes=True; ct=scene.node_tree; ct.nodes.clear(); rl=node(ct,'CompositorNodeRLayers','渲染层',0,0); gl=node(ct,'CompositorNodeGlare','辉光 · 高质量',250,0); gl.glare_type='FOG_GLOW'; gl.quality='HIGH'; gl.threshold=1.5; gl.size=8; co=node(ct,'CompositorNodeComposite','最终图像',510,0); link(ct,rl,'Image',gl,'Image'); link(ct,gl,'Image',co,'Image')
# Portable Chinese interface and ready-to-open camera view.
try:
    bpy.context.preferences.view.language='zh_HANS'
except Exception:
    bpy.context.preferences.view.language='zh_CN'
bpy.context.preferences.view.use_translate_interface=True
bpy.context.preferences.view.use_translate_tooltips=True
bpy.context.preferences.view.use_translate_new_dataname=False
bpy.context.preferences.view.show_splash=False
bpy.ops.wm.save_userpref()
scene.frame_set(25)
bpy.ops.object.select_all(action='DESELECT'); card.select_set(True); bpy.context.view_layer.objects.active=card
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA'
            area.spaces.active.shading.type='MATERIAL'
            area.spaces.active.overlay.show_overlays=False
for im in images.values(): im.pack()
scene['制作说明']='日式浮世绘 · 角色 · 雷之呼吸 壹之型 霹雳一闪。按空格播放转动。渲染有高质量辉光。'
scene['素材来源']='角色/背景/线描/文字为用户提供的成品分层图；特效层（effects.png，可选）位于人物之上、文字之下。'
scene.render.filepath=str(R/'renders'/'hero.png')

# Fixed typography safe region, distinct from parallax controls.
safe=t.nodes.new('ShaderNodeVectorMath'); safe.operation='MULTIPLY_ADD'; safe.name='素材排版安全区'; safe.location=(-1200,1350)
safe_scale=CFG.get('safeArea',{}).get('scale',1.12); safe_offset=CFG.get('safeArea',{}).get('offset',[-.06,-.085])
safe.inputs[1].default_value=(safe_scale,safe_scale,1); safe.inputs[2].default_value=(*safe_offset,0)
t.links.new(pS.outputs['视差效果'],safe.inputs[0]); t.links.new(safe.outputs[0],sT.inputs['Vector']); t.links.new(safe.outputs[0],lt.inputs['Vector'])
over.inputs[0].default_value=.14; sm.inputs[1].default_value=.10; la.inputs[1].default_value=.006
for ob in bpy.data.objects:
    if ob.type=='LIGHT': ob.data.energy*=.48
pattern=f.nodes.new('ShaderNodeTexImage'); pattern.name='花纹贴图'; pattern.image=images['background']; pattern.location=(-450,-700)
f.links.new(mp2.outputs[0],pattern.inputs['Vector']); f.links.new(pattern.outputs['Color'],mul.inputs[2])
scene['制作说明']=CFG.get('title','Card')+' · '+CFG.get('technique','')

bpy.ops.wm.save_as_mainfile(filepath=str(R/'card.blend'))
report={'blender':bpy.app.version_string,'language':bpy.context.preferences.view.language,'interface_translation':bpy.context.preferences.view.use_translate_interface,'config':bpy.utils.user_resource('CONFIG'),'render_engine':scene.render.engine,'device':scene.cycles.device,'images':{k:{'size':list(v.size),'channels':v.channels,'packed':bool(v.packed_file)} for k,v in images.items()},'planes':{o.name:{'rotation_degrees':[round(math.degrees(a),2) for a in o.rotation_euler],'mode':o.mode} for o in [card,textob,bgo]+relief_objs},'parameters':{k:pivot[k] for k in ['主体缩放','主体深度','背景深度']+ (['特效缩放','特效深度'] if has_fx else [])},'effects_layer':bool(has_fx),'source_mode':CFG.get('sourceMode','composite'),'relief_layers':{k:{'width':v.get('width'),'height':v.get('height'),'offset':v.get('offset'),'depth':v.get('depth'),'crop':v.get('crop')} for k,v in layers_cfg.items()},'frames':[1,25,49,73,96]}
(R/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
if '--skip-render' not in args: bpy.ops.render.render(write_still=True)
print('BUILD_AND_HERO_RENDER_COMPLETE')
