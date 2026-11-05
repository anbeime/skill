from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

def test_share_copy_template_is_propagation_card():
    text = (ROOT / "skills/paishe/templates/share-copy.md").read_text(encoding="utf-8")
    assert "【分享文案】" in text
    assert "复刻提示词" in text
    assert "current_skill_name" in text
    assert "share_hashtags" in text
    assert "share_cta" in text
    assert "转发、收藏、复刻" in text

def test_reproduction_prompt_is_short_skill_entry():
    text = (ROOT / "skills/paishe/templates/share-copy.md").read_text(encoding="utf-8")
    assert "@{{current_skill_name}}" in text
    assert "不是完整生图 Prompt" in text
    assert "couple-photo-orchestrator" in text

def test_forbidden_mode_notice_removed_from_runtime_rules():
    runtime_files = [
        ROOT / "SKILL.md",
        ROOT / "skills/zongkong/SKILL.md",
        ROOT / "skills/paishe/SKILL.md",
    ]
    forbidden_exact = "你当前处于抽卡模式，如需切换回自主模式请告诉我。"
    for path in runtime_files:
        text = path.read_text(encoding="utf-8")
        assert forbidden_exact not in text, path

def test_share_copy_template_forbids_workflow_status():
    text = (ROOT / "skills/paishe/templates/share-copy.md").read_text(encoding="utf-8")
    for phrase in ["新卡已生成", "抽卡结果", "当前处于抽卡模式", "切换回自主模式"]:
        assert phrase in text

def test_cta_must_be_dynamic():
    text = (ROOT / "skills/paishe/templates/share-copy.md").read_text(encoding="utf-8")
    assert "CTA 句式必须动态变化" in text


def test_reproduction_heading_is_mandatory_visible_field():
    text = (ROOT / "skills/paishe/templates/share-copy.md").read_text(encoding="utf-8")
    assert "**复刻提示词**" in text
    assert "强制可见标题" in text
    assert "不得省略标题" in text

def test_hashtags_require_hash_prefix_and_no_label_list():
    text = (ROOT / "skills/paishe/templates/share-copy.md").read_text(encoding="utf-8")
    assert "每一个标签都必须以 `#` 开头" in text
    assert "用空格分隔" in text
    assert "#杭州情侣照 #曲院风荷 #江南雨景" in text
    assert "禁止写 `标签：杭州情侣照、曲院风荷`" in text
