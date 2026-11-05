# -*- coding: utf-8 -*-
"""
Comprehensive Audit & Verification Script for all 280 Business Markdown Files.
"""
import os
import re

BUSINESS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "business")

def audit_all():
    print(f"Auditing files in: {BUSINESS_DIR}")
    files = sorted([f for f in os.listdir(BUSINESS_DIR) if f.endswith(".md")])
    print(f"Found {len(files)} markdown files.")

    expected_count = 331
    if len(files) != expected_count:
        print(f"ERROR: Expected {expected_count} files, found {len(files)}")

    errors = []
    total_words = 0
    total_bytes = 0

    styles_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills", "handdraw-style-prompter", "references", "styles.json")
    import json
    styles = json.load(open(styles_path, "r", encoding="utf-8"))

    for s in styles:
        num_str = s["number"]
        filename = f"{num_str}.md"
        filepath = os.path.join(BUSINESS_DIR, filename)

        if not os.path.exists(filepath):
            errors.append(f"Missing file: {filename}")
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        size = len(content.encode("utf-8"))
        total_bytes += size
        total_words += len(content)

        # Structural checks
        checks = [
            (f"# {num_str}", "Missing or mismatched level 1 title"),
            ("风格编号", "Missing style number metadata"),
            ("英文生图名称", "Missing generation name metadata"),
            ("商业定位", "Missing business positioning metadata"),
            ("## 一、 为什么适合这些生意", "Missing section 1 header"),
            ("## 二、 优先商业应用场景与物料矩阵", "Missing section 2 header"),
            ("| 商业场景 | 核心物料载体 |", "Missing scenario table"),
            ("## 三、 可落地的代表性商业项目策划", "Missing section 3 header"),
            ("### 策划案：", "Missing project proposal title"),
            ("## 四、 执行要点与适用边界", "Missing section 4 header"),
            ("## 五、 推荐图型与配色搭配", "Missing section 5 header"),
            ("推荐搭配图型", "Missing recommended layouts"),
            ("推荐主题色", "Missing recommended colors"),
        ]

        for needle, err_msg in checks:
            if needle not in content:
                errors.append(f"[{filename}] {err_msg}")

        # Check table row count (must have at least header + separator + 5 rows = 7 lines)
        table_lines = [l for l in content.splitlines() if l.strip().startswith("|") and l.strip().endswith("|")]
        if len(table_lines) < 7:
            errors.append(f"[{filename}] Scenario table has only {len(table_lines)} rows, expected >= 7")

        if size < 2500:
            errors.append(f"[{filename}] File size too small ({size} bytes)")

    print(f"Total Bytes across {expected_count} files: {total_bytes:,} bytes ({total_bytes/1024/1024:.2f} MB)")
    print(f"Total Characters: {total_words:,} chars")
    print(f"Average File Size: {total_bytes/expected_count:.0f} bytes ({total_words/expected_count:.0f} chars)")

    if errors:
        print(f"\nAUDIT FAILED with {len(errors)} issues:")
        for e in errors[:20]:
            print(" -", e)
        if len(errors) > 20:
            print(f" ... and {len(errors) - 20} more errors.")
        return False
    else:
        print(f"\nALL {expected_count} BUSINESS FILES PASSED THE QUALITY & STRUCTURE AUDIT PERFECTLY! (100% SUCCESS)")
        return True

if __name__ == "__main__":
    audit_all()
