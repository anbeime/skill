"""YAML frontmatter 解析器"""

import re
import os
from typing import Tuple, Optional
from xml.sax.saxutils import escape, quoteattr

from .models import SkillDocument, SkillMetadata, SkillContent
from .errors import ParseError


def parse_skill_file(file_path: str) -> SkillDocument:
    """
    解析技能文件 (SKILL.md)

    格式:
        ---
        name: skill-name
        description: 技能描述
        version: 1.0.0
        ---
        # Markdown 正文
    """
    if not os.path.exists(file_path):
        raise ParseError(f"文件不存在: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    return parse_skill_text(raw_text, file_path)


def parse_skill_text(raw_text: str, file_path: str = "") -> SkillDocument:
    """解析技能文本"""
    doc = SkillDocument(raw_text=raw_text, file_path=file_path)

    # 提取 YAML frontmatter
    frontmatter, body = _split_frontmatter(raw_text)
    if frontmatter:
        doc.has_frontmatter = True
        doc.frontmatter_raw = frontmatter
        doc.metadata = _parse_yaml_frontmatter(frontmatter)
    else:
        doc.has_frontmatter = False

    # 解析正文
    doc.content = _parse_content(body or raw_text)

    return doc


def _split_frontmatter(text: str) -> Tuple[Optional[str], str]:
    """分离 YAML frontmatter 和正文"""
    # 匹配开头的 --- ... ---
    pattern = r'^\s*---\s*\n(.*?)\n---\s*\n?(.*)'
    match = re.match(pattern, text, re.DOTALL)
    if match:
        return match.group(1), match.group(2)
    return None, text


def _parse_yaml_frontmatter(yaml_text: str) -> SkillMetadata:
    """简易 YAML 解析（不依赖 PyYAML，支持常用格式）"""
    meta = SkillMetadata()

    # 尝试用 PyYAML 解析（如果可用）
    try:
        import yaml
        data = yaml.safe_load(yaml_text)
        if isinstance(data, dict):
            meta.name = str(data.get("name", ""))
            meta.description = str(data.get("description", ""))
            meta.version = str(data.get("version", ""))
            meta.author = str(data.get("author", ""))
            meta.homepage = str(data.get("homepage", ""))
            meta.license = str(data.get("license", ""))

            tags = data.get("tags", [])
            if isinstance(tags, list):
                meta.tags = [str(t) for t in tags]
            elif isinstance(tags, str):
                meta.tags = [t.strip() for t in tags.split(",")]

            deps = data.get("dependencies", data.get("dependency", []))
            if isinstance(deps, list):
                meta.dependencies = [str(d) for d in deps]
            elif isinstance(deps, str):
                meta.dependencies = [deps]

            # 收集非标准字段
            known_keys = {"name", "description", "version", "author",
                          "tags", "dependencies", "dependency",
                          "homepage", "license"}
            for k, v in data.items():
                if k not in known_keys:
                    meta.extra[k] = v
            return meta
    except ImportError:
        pass

    # 回退到简易解析
    for line in yaml_text.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip().lower()
            value = value.strip()

            if key == "name":
                meta.name = value
            elif key == "description":
                meta.description = value
            elif key == "version":
                meta.version = value
            elif key == "author":
                meta.author = value
            elif key == "homepage":
                meta.homepage = value
            elif key == "license":
                meta.license = value
            elif key == "tags":
                if value.startswith("["):
                    meta.tags = [t.strip().strip('"\'') for t in value.strip("[]").split(",")]
                else:
                    meta.tags = [value]
            elif key in ("dependencies", "dependency"):
                if value.startswith("["):
                    meta.dependencies = [d.strip().strip('"\'') for d in value.strip("[]").split(",")]
                else:
                    meta.dependencies = [value]
            else:
                meta.extra[key] = value

    return meta


def _parse_content(body: str) -> SkillContent:
    """解析 Markdown 正文"""
    content = SkillContent(raw=body, line_count=len(body.strip().split("\n")))

    # 按标题拆分
    current_heading = ""
    current_text = []
    for line in body.split("\n"):
        heading_match = re.match(r'^(#{1,6})\s+(.+)', line)
        if heading_match:
            if current_heading:
                content.sections[current_heading] = "\n".join(current_text)
            current_heading = heading_match.group(2).strip()
            current_text = []
        else:
            current_text.append(line)
    if current_heading:
        content.sections[current_heading] = "\n".join(current_text)

    # 提取代码块
    content.code_blocks = re.findall(r'```[\s\S]*?```', body)

    return content


def read_properties(file_path: str) -> dict:
    """读取技能属性（用于 CLI read-properties 命令）"""
    doc = parse_skill_file(file_path)
    result = {
        "name": doc.metadata.name,
        "description": doc.metadata.description,
        "version": doc.metadata.version,
        "author": doc.metadata.author,
        "tags": doc.metadata.tags,
        "dependencies": doc.metadata.dependencies,
        "homepage": doc.metadata.homepage,
        "license": doc.metadata.license,
        "has_frontmatter": doc.has_frontmatter,
        "line_count": doc.content.line_count,
        "sections": list(doc.content.sections.keys()),
        "code_blocks_count": len(doc.content.code_blocks),
    }
    if doc.metadata.extra:
        result["extra_fields"] = doc.metadata.extra
    return result


def to_prompt(file_path: str) -> str:
    """将技能转换为 XML prompt 格式"""
    doc = parse_skill_file(file_path)
    lines = ['<skill>']

    # Metadata
    lines.append('  <metadata>')
    lines.append(f'    <name>{escape(doc.metadata.name)}</name>')
    lines.append(f'    <description>{escape(doc.metadata.description)}</description>')
    if doc.metadata.version:
        lines.append(f'    <version>{escape(doc.metadata.version)}</version>')
    if doc.metadata.author:
        lines.append(f'    <author>{escape(doc.metadata.author)}</author>')
    if doc.metadata.tags:
        lines.append(f'    <tags>{escape(", ".join(doc.metadata.tags))}</tags>')
    if doc.metadata.dependencies:
        lines.append(f'    <dependencies>{escape(", ".join(doc.metadata.dependencies))}</dependencies>')
    lines.append('  </metadata>')

    # Content sections
    lines.append('  <content>')
    for heading, text in doc.content.sections.items():
        lines.append(f'    <section name={quoteattr(heading)}>')
        lines.append(f'      {escape(text.strip()[:500])}')
        lines.append(f'    </section>')
    lines.append('  </content>')

    lines.append('</skill>')
    return "\n".join(lines)
