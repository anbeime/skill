"""Build a user-owned Blender/Three.js project from prepared layered artwork."""
from pathlib import Path
import argparse,json,shutil,subprocess,sys
from ensure_blender import ensure_blender
from validate_assets import validate
from generate_typography import create

def main():
    p=argparse.ArgumentParser();p.add_argument('--project',required=True);p.add_argument('--blender');p.add_argument('--skip-render',action='store_true');p.add_argument('--skip-npm',action='store_true');a=p.parse_args()
    root=Path(a.project).resolve();scripts=Path(__file__).resolve().parent;skill=scripts.parent
    config=root/'card-config.json'
    if not config.exists():raise FileNotFoundError('Write card-config.json from references/config.example.json first')
    if not (root/'assets'/'text.png').exists():create(root)
    validate(root);blender=ensure_blender(root,a.blender)
    cmd=[str(blender),'--background','--factory-startup','--python',str(scripts/'build_card.py'),'--',str(root)]
    if a.skip_render:cmd.append('--skip-render')
    subprocess.run(cmd,check=True)
    if not (root/'card.blend').exists():raise RuntimeError('Blender did not save card.blend; inspect its log')
    subprocess.run([str(blender),'--background','--python',str(scripts/'export_web.py'),'--',str(root)],check=True)
    if not (root/'web'/'assets'/'card.glb').exists():raise RuntimeError('GLB export failed')
    web=root/'web';shutil.copytree(skill/'assets'/'web-template',web,dirs_exist_ok=True)
    cfg=json.loads(config.read_text(encoding='utf-8-sig'))
    layers=['subject','background','text','lineart']
    if (root/'assets'/'effects.png').exists():layers.append('effects')
    cfg['assets']={name:'./assets/'+name+'.png' for name in layers};cfg['assets']['model']='./assets/card.glb'
    (web/'card-config.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf8')
    for name in layers:shutil.copy2(root/'assets'/(name+'.png'),web/'assets'/(name+'.png'))
    if not a.skip_npm:
        npm=shutil.which('npm.cmd') or shutil.which('npm')
        if not npm:raise RuntimeError('Install Node.js/npm, then run npm install --ignore-scripts in web/')
        subprocess.run([npm,'install','--ignore-scripts','--no-audit','--no-fund'],cwd=web,check=True)
    # Bundle the viewer into ONE file (three + icons baked in). Per-module URLs
    # like node_modules/.../fingerprint.js get blocked by ad blockers, which
    # killed the page (stuck at "正在装裱作品"). A single file is unblockable.
    # The page loads app.bundle.js, so an edit to app.js only ships after a rebuild:
    # try bun, then esbuild. A missing bundler is never fatal — the template already
    # ships a built bundle. (Note: `which('bun') or Path(...)` is always truthy, so
    # the home-directory candidate has to be existence-checked, not just defaulted.)
    if (web/'app.js').exists():
        bun=shutil.which('bun')
        if not bun:
            local=Path.home()/'.bun'/'bin'/('bun.exe' if sys.platform=='win32' else 'bun')
            bun=str(local) if local.exists() else None
        npx=shutil.which('npx.cmd') or shutil.which('npx')
        if bun:
            cmd=[bun,'build','./app.js','--outfile=./app.bundle.js','--target=browser']
        elif npx:
            cmd=[npx,'--yes','esbuild@0.25.0','app.js','--bundle','--format=esm','--target=es2020','--outfile=app.bundle.js']
        else:
            cmd=None
        if cmd is None:
            print('bun/esbuild not found; using prebuilt app.bundle.js from the template')
        else:
            try:
                if subprocess.run(cmd,cwd=web,check=False).returncode!=0:
                    print('bundle rebuild failed; keeping the prebuilt app.bundle.js from the template')
            except OSError as error:
                print('bundle rebuild skipped ('+str(error)+'); keeping the prebuilt app.bundle.js')
    print('Completed:',root/'card.blend');print('Preview: node',web/'server.mjs');print('Open http://127.0.0.1:4173 after starting the server')
if __name__=='__main__':main()
