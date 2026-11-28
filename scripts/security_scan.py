#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""技能包安全扫描器。

扫描 skills/ 下随仓分发的技能文件，检出常见危险模式：
- 远程内容直接管道给 shell 执行（curl | sh）
- 读取 SSH/AWS/Kube 等凭证文件
- 将环境变量 / shell 历史外传
- base64 等编码后直接执行（混淆执行）
- 对家目录 / 根目录的 rm -rf

严重级别：high → 退出码 1（CI 失败）；medium → 仅 GitHub Actions 注解警告。

用法:
    python scripts/security_scan.py --path skills
    python scripts/security_scan.py --path skills --fail-on medium   # 提高拦截阈值
"""
import argparse
import re
import sys
from pathlib import Path

# (规则ID, 严重级别, 编译后的正则, 说明)
RULES = [
    ("NET-REMOTE-EXEC", "high", re.compile(
        r"\b(curl|wget|fetch)\b[^\n|;&]{0,200}\|\s*(sudo\s+)?(?:ba|z|da)?sh\b"),
     "下载内容直接管道给 shell 执行（curl|sh）"),
    ("CRED-ACCESS", "high", re.compile(
        r"\.ssh/(id_rsa|id_ed25519|authorized_keys)|\.aws/credentials|\.netrc|\.kube/config|\.env\b"),
     "读取常见凭证/密钥文件"),
    ("ENV-EXFIL", "high", re.compile(
        r"\b(curl|wget)\b[^\n]{0,200}(-d|--data|-F|--form|--upload-file)\b[^\n]{0,200}"
        r"(\$\(env\)|\benv\s*\||process\.env|os\.environ)"),
     "将环境变量内容外传"),
    ("HISTORY-EXFIL", "high", re.compile(
        r"\b(curl|wget|scp)\b[^\n]{0,200}(_history|\.hist)\b"),
     "外传 shell 历史/会话文件"),
    ("OBFUSC-EXEC", "medium", re.compile(
        r"\b(base64\s+-d|base64\s+--decode|openssl\s+enc\s+-d)\b[^\n|;&]{0,200}\|\s*(sudo\s+)?(?:ba|z|da)?sh\b"),
     "base64/openssl 解码后直接执行（混淆执行）"),
    ("DESTROY-FS", "medium", re.compile(
        r"rm\s+(-[a-zA-Z]*[rf][a-zA-Z]*\s+)+(~|\$HOME|/)(\s|/|$)"),
     "对家目录/根目录执行递归删除"),
    ("EVAL-REMOTE", "medium", re.compile(
        r"\beval\b[^\n]{0,80}(\$\(|`)?\s*(curl|wget)\b"),
     "eval 执行远程获取的内容"),
    ("PYTHON-REMOTE-EXEC", "medium", re.compile(
        r"python3?\s+-c\s+[\"'][^\n]{0,300}(urllib|requests\.get|os\.system|subprocess)"),
     "python -c 内嵌远程下载/系统调用"),
]

MAX_FILE_SIZE = 512 * 1024  # 跳过超过 512KB 的文件（大概率是二进制/数据文件）
SKIP_DIRS = {".git", "node_modules", "__pycache__"}
SCAN_EXTENSIONS = {
    ".md", ".txt", ".py", ".sh", ".bash", ".zsh", ".js", ".ts", ".mjs",
    ".json", ".yaml", ".yml", ".toml", ".rb", ".ps1", ".bat", ".cmd",
    ".fish", ".lua", ".pl", ".php",
}


def iter_files(root: Path):
    if root.is_file():
        yield root
        return
    for p in sorted(root.rglob("*")):
        if p.is_dir():
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.suffix.lower() not in SCAN_EXTENSIONS:
            continue
        try:
            if p.stat().st_size > MAX_FILE_SIZE:
                continue
            p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        yield p


def scan(root: Path, fail_on: str):
    findings = []  # (severity, rule_id, file, line_no, line_text, desc)
    files_scanned = 0
    for f in iter_files(root):
        files_scanned += 1
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for line_no, line in enumerate(text.splitlines(), 1):
            for rule_id, severity, pattern, desc in RULES:
                if severity == "high" and fail_on == "high" or \
                   severity in ("high", "medium") and fail_on == "medium":
                    pass  # 阈值只影响退出码，扫描始终全量
                if pattern.search(line):
                    findings.append((severity, rule_id, str(f), line_no, line.strip()[:120], desc))
    return files_scanned, findings


def main():
    parser = argparse.ArgumentParser(description="技能包安全扫描器")
    parser.add_argument("--path", default="skills", help="扫描根目录（默认 skills）")
    parser.add_argument("--fail-on", choices=["high", "medium"], default="high",
                        help="达到该级别即令 CI 失败（默认 high；medium 仅警告）")
    parser.add_argument("--fail-on-medium", action="store_true", help="等价于 --fail-on medium")
    args = parser.parse_args()
    if args.fail_on_medium:
        args.fail_on = "medium"

    root = Path(args.path)
    if not root.exists():
        print(f"::notice::扫描目录不存在，跳过: {root}")
        return 0

    files_scanned, findings = scan(root, args.fail_on)

    print(f"## 🛡️ 技能包安全扫描报告", end="\n\n")
    print(f"- 扫描目录: `{root}`")
    print(f"- 扫描文件数: {files_scanned}")
    print(f"- 发现问题: {len(findings)} 条"
          f"（high {sum(1 for x in findings if x[0] == 'high')} /"
          f" medium {sum(1 for x in findings if x[0] == 'medium')}）")
    print()

    for severity, rule_id, f, line_no, line, desc in findings:
        # GitHub Actions 注解格式，自动出现在 PR diff 与 Annotations 面板
        tag = "error" if severity == "high" else "warning"
        print(f"::{tag} file={f},line={line_no},title={rule_id}::{desc}")
        print(f"- **[{severity.upper()}] `{rule_id}`** `{f}:{line_no}` — {desc}")
        print(f"  > `{line}`")
    if not findings:
        print("✅ 未检出危险模式。")
    return 1 if any(s == "high" or (args.fail_on == "medium" and s == "medium")
                    for s, *_ in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
