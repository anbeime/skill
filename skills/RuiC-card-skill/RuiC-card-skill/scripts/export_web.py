import bpy,sys,json
from pathlib import Path
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
root=Path(args[0]) if args else Path(__file__).resolve().parent
blend=next((p for p in [root/'card.blend'] if p.exists()),None)
if blend is None: raise FileNotFoundError('Missing card.blend')
bpy.ops.wm.open_mainfile(filepath=str(blend))
pivot=bpy.data.objects['转卡控制 · 播放时间线预览']; pivot.animation_data_clear(); pivot.rotation_euler=(0,0,0)
materials={}
for role in ['front','edge','back','text','gold','subject','effects']:
    m=bpy.data.materials.new('web_'+role); m.diffuse_color=(.7,.5,.2,1); m.use_nodes=True; materials[role]=m
cardcol=bpy.data.collections['卡牌 · 可复用成品']
relief=any('Relief' in o.name for o in cardcol.objects)
bpy.ops.object.select_all(action='DESELECT')
for ob in list(cardcol.objects):
    if ob.type!='MESH': continue
    if 'Relief subject' in ob.name:
        ob.data.materials.clear(); ob.data.materials.append(materials['subject']); ob.select_set(True); continue
    if 'Relief effects' in ob.name:
        ob.data.materials.clear(); ob.data.materials.append(materials['effects']); ob.select_set(True); continue
    if '文字平面' in ob.name:
        if not relief: ob.hide_render=True; continue
        ob.data.materials.clear(); ob.data.materials.append(materials['text']); ob.select_set(True); continue
    if '主体平面' in ob.name:
        old_indices=[p.material_index for p in ob.data.polygons]
        ob.data.materials.clear()
        for role in ['front','edge','back']: ob.data.materials.append(materials[role])
        for p,i in zip(ob.data.polygons,old_indices): p.material_index=i
        ob.select_set(True); continue
    role='gold' if '古金' in ob.name else 'edge'; ob.data.materials.clear(); ob.data.materials.append(materials[role]); ob.select_set(True)
pivot.select_set(True)
output=root/'web'/'assets'/'card.glb'; output.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(output),export_format='GLB',use_selection=True,export_materials='EXPORT',export_animations=False,export_cameras=False,export_lights=False,export_yup=True)
print('EXPORTED',output,'relief' if relief else 'composite')
