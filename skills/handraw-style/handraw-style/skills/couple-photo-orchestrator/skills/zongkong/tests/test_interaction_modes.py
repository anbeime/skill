from pathlib import Path
import subprocess
import sys
import tempfile
import yaml

ROOT = Path(__file__).resolve().parents[3]
INIT = ROOT / "skills" / "zongkong" / "scripts" / "init_project.py"
THEME = ROOT / "skills" / "zongkong" / "scripts" / "theme_manager.py"

def read(path):
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))

def test_mode_contract_text_exists():
    text=(ROOT/"skills/zongkong/references/interaction-modes.md").read_text(encoding="utf-8")
    assert "自主模式本身就是轻量逐步确认" in text
    assert "A/B/C 只表示方向" in text
    assert "用户明确说“抽卡”才切" in text
    assert "1 张自适应布局八宫格" in text


def test_new_project_defaults_user_directed_and_theme_inherits_mode():
    with tempfile.TemporaryDirectory() as td:
        project=Path(td)/"p"
        subprocess.run([sys.executable,str(INIT),"mode-test","--project-dir",str(project)],check=True,capture_output=True,text=True)
        root=read(project/"project.yaml")
        assert root["interaction_mode"] == "user_directed"
        subprocess.run([sys.executable,str(THEME),"set-mode",str(project),"card_draw"],check=True,capture_output=True,text=True)
        subprocess.run([sys.executable,str(THEME),"create",str(project),"--name","draw theme"],check=True,capture_output=True,text=True)
        root=read(project/"project.yaml")
        theme=read(project/"themes/THEME-001/project.yaml")
        assert root["interaction_mode"] == "card_draw"
        assert theme["interaction_mode"] == "card_draw"
        assert theme["confirmation_authority"] == "ai_recommendation"

def test_switch_mode_keeps_active_theme():
    with tempfile.TemporaryDirectory() as td:
        project=Path(td)/"p"
        subprocess.run([sys.executable,str(INIT),"mode-test","--project-dir",str(project)],check=True,capture_output=True,text=True)
        subprocess.run([sys.executable,str(THEME),"create",str(project),"--name","theme"],check=True,capture_output=True,text=True)
        subprocess.run([sys.executable,str(THEME),"set-mode",str(project),"card_draw"],check=True,capture_output=True,text=True)
        root=read(project/"project.yaml")
        assert root["themes"]["active_theme_id"] == "THEME-001"
        subprocess.run([sys.executable,str(THEME),"set-mode",str(project),"user_directed"],check=True,capture_output=True,text=True)
        root=read(project/"project.yaml")
        theme=read(project/"themes/THEME-001/project.yaml")
        assert root["themes"]["active_theme_id"] == "THEME-001"
        assert theme["interaction_mode"] == "user_directed"
        assert theme["confirmation_authority"] == "user"
