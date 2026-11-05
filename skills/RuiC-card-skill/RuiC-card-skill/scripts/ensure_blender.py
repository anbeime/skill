"""Find Blender or install a checksum-verified official portable copy in a project.

Downloads come from the official Blender release directory unless RUIC_BLENDER_BASE
names another base URL. The .sha256 for the package is fetched from that same base, so
a mirror protects against a corrupt or truncated transfer, not against the mirror
itself — point it at a source you trust, and leave it unset to take the official one.
"""
from pathlib import Path
import argparse,hashlib,os,platform,re,shutil,subprocess,tarfile,urllib.request,zipfile
DEFAULT_BASE='https://download.blender.org/release/Blender4.5/'
BASE=(os.environ.get('RUIC_BLENDER_BASE') or DEFAULT_BASE).rstrip('/')+'/'
def find_blender(project,override=None):
    candidates=[]
    if override:candidates.append(Path(override))
    system=shutil.which('blender')
    if system:candidates.append(Path(system))
    tools=Path(project)/'tools'
    if tools.exists():
        candidates.extend(tools.glob('blender*/blender.exe'))
        candidates.extend(tools.glob('blender*/blender'))
        candidates.extend(tools.glob('Blender.app/Contents/MacOS/Blender'))
    if platform.system()=='Darwin':candidates.append(Path('/Applications/Blender.app/Contents/MacOS/Blender'))
    for p in candidates:
        if p.is_file():return p.resolve()
    return None

def fetch(url,target):
    req=urllib.request.Request(url,headers={'User-Agent':'Holo-Card-Studio/1.0'})
    with urllib.request.urlopen(req,timeout=90) as response,target.open('wb') as out:shutil.copyfileobj(response,out)

def ensure_blender(project,override=None):
    project=Path(project).resolve();existing=find_blender(project,override)
    if existing:return existing
    if override:raise FileNotFoundError('Specified Blender executable does not exist: '+str(override))
    system=platform.system();machine=platform.machine().lower()
    if system=='Windows':suffix='windows-arm64.zip' if 'arm' in machine else 'windows-x64.zip'
    elif system=='Linux':
        if machine not in ('x86_64','amd64'):raise RuntimeError('Select a supported official Linux build for '+machine)
        suffix='linux-x64.tar.xz'
    elif system=='Darwin':suffix='macos-arm64.dmg' if 'arm' in machine else 'macos-x64.dmg'
    else:raise RuntimeError('Unsupported platform: '+system)
    listing=urllib.request.urlopen(BASE,timeout=30).read().decode('utf8')
    found=set(re.findall(r'blender-(4\.5\.\d+)-'+re.escape(suffix),listing))
    if not found:raise RuntimeError('No matching official Blender package for '+suffix)
    version=max(found,key=lambda v:tuple(map(int,v.split('.'))));name='blender-'+version+'-'+suffix
    tools=project/'tools';tools.mkdir(parents=True,exist_ok=True);package=tools/name
    checksum=tools/('blender-'+version+'.sha256');fetch(BASE+checksum.name,checksum)
    entries=[l.split() for l in checksum.read_text().splitlines()]
    hashes=[row[0].lower() for row in entries if len(row)>1 and row[-1].lstrip('*')==name]
    if len(hashes)!=1:raise RuntimeError('Official checksum entry missing or ambiguous')
    expected=hashes[0]
    def digest(path):
        h=hashlib.sha256()
        with path.open('rb') as data:
            for part in iter(lambda:data.read(1024*1024),b''):h.update(part)
        return h.hexdigest()
    if not package.exists() or digest(package)!=expected:
        partial=package.with_suffix(package.suffix+'.part');fetch(BASE+name,partial)
        if digest(partial)!=expected:raise RuntimeError('Official Blender SHA-256 mismatch; package not executed')
        partial.replace(package)
    if package.suffix=='.zip':
        with zipfile.ZipFile(package) as z:
            for entry in z.infolist():
                dest=(tools/entry.filename).resolve()
                if not dest.is_relative_to(tools):raise RuntimeError('Unsafe archive path')
                if (entry.external_attr>>16)&0o170000==0o120000:raise RuntimeError('Unexpected ZIP symlink')
            z.extractall(tools)
    elif name.endswith('.tar.xz'):
        with tarfile.open(package) as tar:
            if hasattr(tarfile,'data_filter'):tar.extractall(tools,filter='data')
            else:
                for member in tar.getmembers():
                    if member.issym() or member.islnk() or not (tools/member.name).resolve().is_relative_to(tools):raise RuntimeError('Unsafe archive member')
                tar.extractall(tools)
    else:
        import plistlib
        mount=plistlib.loads(subprocess.check_output(['hdiutil','attach','-nobrowse','-readonly','-plist',str(package)]))
        points=[e['mount-point'] for e in mount['system-entities'] if 'mount-point' in e]
        if len(points)!=1:raise RuntimeError('Could not select mounted Blender disk')
        try:
            apps=list(Path(points[0]).glob('*.app'))
            if len(apps)!=1:raise RuntimeError('Could not select Blender app bundle')
            shutil.copytree(apps[0],tools/'Blender.app',symlinks=True,dirs_exist_ok=True)
        finally:subprocess.run(['hdiutil','detach',points[0]],check=True)
    exe=find_blender(project)
    if not exe:raise RuntimeError('Installation extracted but Blender executable not found')
    config=(exe.parent/'portable'/'config') if system!='Darwin' else (tools/'Blender.app'/'Contents'/'Resources'/'portable'/'config')
    config.mkdir(parents=True,exist_ok=True)
    print('Official SHA-256 verified; Blender installed:',exe)
    return exe
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('project');p.add_argument('--blender');a=p.parse_args();print(ensure_blender(a.project,a.blender))
