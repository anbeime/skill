import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).resolve().parents[1] / "skills/personal-library/scripts/personal_library.py"), run_name="__main__")
