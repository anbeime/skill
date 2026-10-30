#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
strip_platform_syntax.py — 清理提示词里的平台专有语法，输出可移植纯文本。

用法:
    python strip_platform_syntax.py input.md [-o cleaned.md]

清理对象（均为常见平台占位符 / 指令，目标 AI 不认）:
    - {{var}} / {var} / {{ 用户输入 }} 类占位符  -> 改为通用描述
    - "调用 XX 工具" / "使用 XX 插件" 类工具指令 -> 改为"基于你的知识回答"
    - 方括号 UI 标签如 [按钮] / <<模块>>         -> 删除
只做轻量正则替换，不改动角色/技能/流程/格式/约束五段实质内容。
"""
import argparse
import re
import sys

PLACEHOLDER_RE = re.compile(r"\{\{.*?\}\}|\{[^}\n]{1,40}\}")
TOOL_RE = re.compile(r"(调用|使用|运行)\s*[\"'\u300c\u300d]?[A-Za-z0-9_\u4e00-\u9fa5]{1,20}[\u5de5\u5177\u63d2\u4ef6\u6307\u4ee4\u80fd\u529b]*")
UI_TAG_RE = re.compile(r"[\[<][^\]\n]{1,20}[\]>]|[\u300c\u300d][^\u300d\n]{1,20}[\u300d]")

REPLACEMENTS = [
    (PLACEHOLDER_RE, "用户会提供具体需求"),
    (TOOL_RE, "请基于你的知识回答"),
    (UI_TAG_RE, ""),
]


def clean(text: str) -> str:
    for rx, rep in REPLACEMENTS:
        text = rx.sub(rep, text)
    # 合并多余空行
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def main():
    ap = argparse.ArgumentParser(description="清理提示词平台专有语法")
    ap.add_argument("input", help="输入提示词文件 (.md/.txt)")
    ap.add_argument("-o", "--output", help="输出文件，缺省则打印到 stdout")
    args = ap.parse_args()

    try:
        with open(args.input, encoding="utf-8") as f:
            src = f.read()
    except FileNotFoundError:
        sys.exit(f"[错误] 找不到文件: {args.input}")

    out = clean(src)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out)
        print(f"[完成] 已写出: {args.output} ({len(out)} 字符)")
    else:
        print(out)


if __name__ == "__main__":
    main()
