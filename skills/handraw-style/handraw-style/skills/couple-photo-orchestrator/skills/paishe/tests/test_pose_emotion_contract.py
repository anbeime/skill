from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

def test_pose_emotion_contract_has_required_layers():
    text = (ROOT / "skills/paishe/references/pose-emotion-contract.md").read_text(encoding="utf-8")
    for key in ["动作意图", "关键身体力学", "重心", "Pose-family", "Couple contact topology", "固定情绪 few-shot", "framing_adaptation"]:
        assert key in text

def test_shot_template_exposes_pose_fields():
    text = (ROOT / "skills/paishe/templates/shot-list.md").read_text(encoding="utf-8")
    for key in ["动作事件", "姿势结构", "关键受力 / 重心", "关系 / 接触", "情绪动机", "视线", "景别适配"]:
        assert key in text
