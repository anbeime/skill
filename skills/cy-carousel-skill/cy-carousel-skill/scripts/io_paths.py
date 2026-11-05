"""素材根目录由调用者提供；页面脚本及随包清单只存相对路径。"""
from pathlib import Path
import contextvars
_root=contextvars.ContextVar('assets_root',default=None)
def set_assets_root(root=None):
    _root.set(Path(root).expanduser().resolve() if root is not None else None)
def asset_path(base,value):
    p=Path(value).expanduser()
    return p.resolve() if p.is_absolute() else ((_root.get() or Path(base))/p).resolve()
def check_relative_spec(data):
    errors=[]
    def walk(obj,location='root'):
        if isinstance(obj,dict):
            for key,value in obj.items():
                if key in ('path','mask','subject_mask','cutout_path') and isinstance(value,str):
                    if Path(value).is_absolute() or '..' in Path(value).parts:errors.append(f'{location}.{key}: 必须为素材根目录内的相对路径')
                walk(value,location+'.'+key)
        elif isinstance(obj,list):
            for i,value in enumerate(obj):walk(value,f'{location}[{i}]')
    walk(data);return errors
