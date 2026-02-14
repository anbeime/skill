#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
标准合同审核工作流程
Contract Review Standard Workflow

提供完整的合同审核流程,包括:
- 智能合同分析
- 解包文档
- 初始化Document对象
- 批量添加批注(支持多关键词搜索)
- 自动验证批注
- 保存并打包文档
- 生成合同概要
- 生成业务流程图(Mermaid)并渲染图片
- 生成审核报告

使用示例:
    from scripts.workflow import ContractReviewWorkflow

    comments = [
        {
            "search": ["合同总价", "协议总金额", "总金额"],
            "comment": "【问题类型】合同价款条款\\n【风险等级】🔴 高风险..."
        }
    ]

    workflow = ContractReviewWorkflow("合同.docx", "审核人")
    workflow.run_full_workflow(comments, "合同_审核版.docx")
"""

import sys
import os
import shutil
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# 添加技能路径
skill_dir = Path(__file__).parent.parent
if str(skill_dir) not in sys.path:
    sys.path.insert(0, str(skill_dir))

try:
    from scripts.contract_analyzer import ContractAnalyzer
except ImportError:
    from contract_analyzer import ContractAnalyzer

from scripts.document import Document
from scripts.summary_renderer import render_summary_docx
from scripts.opinion_renderer import render_opinion_docx
from scripts.mermaid_renderer import (
    normalize_mermaid_code,
    render_mermaid_file,
    write_mermaid_file,
)
from scripts.ooxml.unpack import unpack_document
from scripts.ooxml.pack import pack_document


def _detect_output_language(*texts: Optional[str]) -> Optional[str]:
    combined = "\n".join([text for text in texts if text])
    if not combined:
        return None
    cjk_count = 0
    latin_count = 0
    for char in combined:
        if "\u4e00" <= char <= "\u9fff":
            cjk_count += 1
        elif "A" <= char <= "Z" or "a" <= char <= "z":
            latin_count += 1
    if cjk_count == 0 and latin_count == 0:
        return None
    if cjk_count >= latin_count:
        return "zh"
    return "en"


def _detect_output_language_from_contract(contract_path: Path) -> Optional[str]:
    try:
        with zipfile.ZipFile(contract_path) as zf:
            xml = zf.read("word/document.xml")
    except Exception:
        return None

    try:
        root = ET.fromstring(xml)
    except Exception:
        return None

    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    texts = []
    for node in root.findall(".//w:t", ns):
        if node.text:
            texts.append(node.text)
    combined = "".join(texts)
    return _detect_output_language(combined)


_CN_SECTION_LABELS = {
    1: "一",
    2: "二",
    3: "三",
    4: "四",
    5: "五",
    6: "六",
    7: "七",
    8: "八",
    9: "九",
    10: "十",
}


def _section_cn(index: int) -> str:
    return _CN_SECTION_LABELS.get(index, str(index))


class ContractReviewWorkflow:
    """
    完整的合同审核工作流程

    该类封装了合同审核的所有步骤,确保每个步骤都正确执行,
    并提供详细的反馈和验证机制。
    """

    def __init__(
        self,
        contract_path: str,
        reviewer_name: str = "合同审核助手",
        output_dir: str = None,
        enable_analysis: bool = True,
        enable_smart_keyword_expansion: bool = False,
    ):
        """
        初始化工作流程

        Args:
            contract_path: 合同文档路径(.docx文件)
            reviewer_name: 审核人姓名,用于批注作者
            output_dir: 输出目录(如果为None,自动创建"审核结果：「原合同文件名」"文件夹)
            enable_analysis: 是否启用智能合同分析(默认True)
            enable_smart_keyword_expansion: 是否启用智能关键词扩展(默认False)
        """
        self.contract_path = Path(contract_path)
        self.reviewer_name = reviewer_name
        self.reviewer_initials = "审核"
        self.enable_analysis = enable_analysis
        self.enable_smart_keyword_expansion = enable_smart_keyword_expansion
        self.output_language = None
        self.output_dir_default = output_dir is None

        # 如果未指定输出目录,创建审核结果文件夹
        if output_dir is None:
            original_name = self.contract_path.stem
            output_dir = self.contract_path.parent / f"审核结果：{original_name}"

        self.output_dir = Path(output_dir)
        self.unpacked_dir = None
        self.doc = None
        self.comments_added = []  # type: List[Dict]
        self.comments_failed = []  # type: List[Dict]
        self.start_time = datetime.now()
        self.contract_analyzer = None  # type: Optional[ContractAnalyzer]
        self.flowchart_mmd_path = None  # type: Optional[Path]
        self.flowchart_image_path = None  # type: Optional[Path]
        self.flowchart_error = None  # type: Optional[str]
        self.flowchart_rendered = False
        self.summary_path = None  # type: Optional[Path]
        self.summary_error = None  # type: Optional[str]
        self.opinion_path = None  # type: Optional[Path]
        self.opinion_error = None  # type: Optional[str]

        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 初始化智能分析器
        if self.enable_analysis:
            try:
                print(f"\n🔍 初始化智能合同分析...")
                self.contract_analyzer = ContractAnalyzer(str(self.contract_path))
                summary = self.contract_analyzer.get_contract_summary()
                print(f"✓ 合同类型: {summary['contract_type']}")
                print(f"✓ 段落数量: {summary['total_paragraphs']}")
                print(f"✓ 识别字段: {summary['found_fields']}个")
            except Exception as e:
                print(f"⚠️  智能分析初始化失败: {e}")
                print(f"  将继续使用标准模式")

    @staticmethod
    def _strip_risk_level_line(comment_text: str) -> str:
        """
        Remove any line that contains the risk level label from comment text.

        The reviewer name already encodes risk level, so we omit the line
        like "【风险等级】..." from the comment content.
        """
        if not comment_text:
            return comment_text

        lines = comment_text.splitlines()
        kept = [line for line in lines if "风险等级" not in line]

        cleaned = []
        previous_blank = False
        for line in kept:
            if line.strip():
                cleaned.append(line)
                previous_blank = False
            else:
                if not previous_blank:
                    cleaned.append(line)
                previous_blank = True

        while cleaned and not cleaned[0].strip():
            cleaned.pop(0)
        while cleaned and not cleaned[-1].strip():
            cleaned.pop()

        return "\n".join(cleaned)

    def _ensure_output_dir_for_language(self, output_language: Optional[str]) -> None:
        if output_language != "en" or not self.output_dir_default:
            return

        original_name = self.contract_path.stem
        english_dir = self.contract_path.parent / f"Review_Result_{original_name}"
        if self.output_dir == english_dir:
            return

        old_dir = self.output_dir
        self.output_dir = english_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        try:
            if old_dir.exists() and not any(old_dir.iterdir()):
                old_dir.rmdir()
        except Exception:
            pass

    def step0_copy_contract(self) -> bool:
        """
        步骤0: 复制原合同到审核目录

        将原始合同文件复制到审核结果目录,作为备份和审核基础。

        Returns:
            bool: 成功返回True,失败返回False
        """
        print(f"\n{'='*60}")
        print(f"步骤0: 复制原合同")
        print(f"{'='*60}")
        print(f"📄 复制原合同到审核目录...")

        try:
            # 复制原合同到输出目录
            target_path = self.output_dir / self.contract_path.name
            shutil.copy2(self.contract_path, target_path)
            print(f"✓ 已复制原合同: {target_path.name}")
            print(f"  📁 审核目录: {self.output_dir}")
            return True
        except Exception as e:
            print(f"✗ 复制失败: {e}")
            self.comments_failed.append({
                'step': '复制原合同',
                'error': str(e)
            })
            return False

    def step1_unpack(self, unpacked_subdir: str = "unpacked") -> bool:
        """
        步骤1: 解包文档

        将.docx文件解包为XML文件,以便进行编辑和批注。
        解包后的文件将存放在输出目录中的unpacked子目录。

        注意:使用审核目录中的合同副本,而不是原始合同

        Args:
            unpacked_subdir: 解包子目录名称(相对于output_dir)

        Returns:
            bool: 成功返回True,失败返回False
        """
        print(f"\n{'='*60}")
        print(f"步骤1: 解包文档")
        print(f"{'='*60}")
        print(f"📦 解包文档: {self.contract_path.name}")

        try:
            # 使用审核目录中的合同副本
            contract_copy = self.output_dir / self.contract_path.name

            # 在输出目录中创建解包子目录
            self.unpacked_dir = str(self.output_dir / unpacked_subdir)
            unpack_document(str(contract_copy), self.unpacked_dir)
            print(f"✓ 解包完成: {self.unpacked_dir}")
            return True
        except Exception as e:
            print(f"✗ 解包失败: {e}")
            self.comments_failed.append({
                'step': 'unpack',
                'error': str(e)
            })
            return False

    def step2_initialize(self) -> bool:
        """
        步骤2: 初始化Document对象

        创建Document对象,用于后续的批注操作。

        Returns:
            bool: 成功返回True,失败返回False
        """
        print(f"\n{'='*60}")
        print(f"步骤2: 初始化文档对象")
        print(f"{'='*60}")
        print(f"🔧 初始化Document对象")

        try:
            self.doc = Document(
                self.unpacked_dir,
                author=self.reviewer_name,
                initials=self.reviewer_initials
            )
            print(f"✓ 初始化完成")
            print(f"  - 审核人: {self.reviewer_name}")
            print(f"  - 工作目录: {self.unpacked_dir}")
            return True
        except Exception as e:
            print(f"✗ 初始化失败: {e}")
            self.comments_failed.append({
                'step': 'initialize',
                'error': str(e)
            })
            return False

    def step3_add_comments(self, comments: List[Dict]) -> bool:
        """
        步骤3: 批量添加批注

        根据提供的批注列表,批量添加批注到文档中。
        使用跨节点文本搜索,处理文本被分割在多个XML节点的情况。

        支持多种搜索方式:
        - 单个关键词: "search": "合同编号:"
        - 多个关键词: "search": ["合同编号:", "协议编号:", "合同号:"]
        - 系统会依次尝试每个关键词,直到找到匹配

        智能优化(启用 enable_smart_keyword_expansion 时):
        - 如果提供了单个关键词,会自动基于合同内容扩展为多个关键词
        - 例如: "合同编号:" -> ["合同编号:", "协议编号:", "合同号:"]

        Args:
            comments: 批注列表,每个元素包含'search'、'comment'和可选的'risk_level'字段
                - 批注正文不需要包含“【风险等级】”行(如包含会自动移除)

        Returns:
            bool: 全部成功返回True,部分或全部失败返回False
        """
        print(f"\n{'='*60}")
        print(f"步骤3: 添加批注 (使用跨节点搜索 + 精准匹配优先)")
        print(f"{'='*60}")
        print(f"💬 添加 {len(comments)} 个批注...")

        smart_keywords = None
        if self.contract_analyzer:
            smart_keywords = self.contract_analyzer.generate_smart_search_keywords()
            print(f"\n🧠 智能搜索关键词建议:")
            for field, keywords in list(smart_keywords.items())[:3]:  # 只显示前3个
                print(f"   {field}: {keywords}")

        all_success = True
        precise_match_count = 0
        fallback_count = 0

        for i, comment_data in enumerate(comments, 1):
            try:
                # 获取搜索文本和批注内容
                search_text = comment_data['search']
                comment_text = comment_data['comment']
                comment_text = self._strip_risk_level_line(comment_text)
                risk_level = comment_data.get('risk_level', '中风险')  # 默认中风险

                # 支持多关键词搜索
                search_keywords = [search_text] if isinstance(search_text, str) else search_text

                # 智能优化:如果启用扩展,尝试扩展关键词
                if len(search_keywords) == 1 and self.enable_smart_keyword_expansion and smart_keywords:
                    original_keyword = search_keywords[0]
                    # 标准化关键词(去除标点符号)进行模糊匹配
                    normalized_original = original_keyword.rstrip(':：')

                    # 查找包含标准化关键词的字段(使用更宽松的匹配)
                    for field, keywords in smart_keywords.items():
                        # 标准化该字段的所有关键词
                        normalized_keywords = [k.rstrip(':：') for k in keywords]

                        # 宽松匹配:如果用户搜索"合同编号",匹配包含"编号"的字段
                        if (normalized_original in normalized_keywords or
                            any(normalized_original in nk or nk in normalized_original
                                for nk in normalized_keywords)):
                            # 使用完整的原始关键词列表
                            search_keywords = keywords
                            print(f"  🧠 智能扩展: '{original_keyword}' -> {keywords}")
                            break

                # 使用跨节点搜索查找目标段落 (允许fallback到标题)
                para = self.doc.find_paragraph_by_text(search_keywords, allow_fallback=True)

                # 判断是否使用了fallback (检查段落是否包含任一关键词)
                para_text = self.doc.get_paragraph_text(para)
                used_fallback = not any(keyword in para_text for keyword in search_keywords)

                if used_fallback:
                    fallback_count += 1
                    match_type = "🔄 Fallback到标题"
                else:
                    precise_match_count += 1
                    match_type = "🎯 精准匹配"

                # 添加批注(包含风险等级)
                comment_id = self.doc.add_comment(
                    start=para,
                    end=para,
                    text=comment_text,
                    risk_level=risk_level
                )
                self.comments_added.append({
                    'id': comment_id,
                    'search': search_keywords[0] if len(search_keywords) == 1 else search_keywords,
                    'risk_level': risk_level,
                    'status': 'success',
                    'fallback_used': used_fallback
                })

                # 显示匹配的关键词
                matched_keyword = search_keywords[0] if used_fallback else next((k for k in search_keywords if k in para_text), search_keywords[0])
                print(f"✓ {i}/{len(comments)}: {match_type} - {matched_keyword[:40]}")

            except Exception as e:
                # 添加批注时出错
                self.comments_failed.append({
                    'search': comment_data.get('search', 'unknown'),
                    'reason': str(e)
                })
                print(f"✗ {i}/{len(comments)}: 失败 - {str(e)[:80]}")

        # 打印详细统计
        success_count = len(self.comments_added)
        failed_count = len(self.comments_failed)
        precision_rate = precise_match_count / success_count * 100 if success_count > 0 else 0

        print(f"\n批注添加完成:")
        print(f"  ✓ 成功: {success_count} 个")
        print(f"    ├── 🎯 精准匹配: {precise_match_count} 个 ({precision_rate:.1f}%)")
        print(f"    └── 🔄 Fallback: {fallback_count} 个 ({100-precision_rate:.1f}%)")
        print(f"  ✗ 失败: {failed_count} 个")

        # 检查是否达到90%精准匹配目标
        if success_count > 0:
            if precision_rate >= 90:
                print(f"\n✅ 优秀!精准匹配率达到{precision_rate:.1f}% (目标: ≥90%)")
            elif precision_rate >= 70:
                print(f"\n⚠️ 良好,但精准匹配率{precision_rate:.1f}%未达到90%目标")
            else:
                print(f"\n❌ 精准匹配率{precision_rate:.1f}%过低,建议优化搜索关键词")

        return failed_count == 0

    def step4_verify(self) -> dict:
        """
        步骤4: 验证批注

        验证所有批注是否成功添加到文档中,包括:
        - comments.xml中存在批注
        - document.xml中存在批注引用

        Returns:
            dict: 验证结果字典
        """
        print(f"\n{'='*60}")
        print(f"步骤4: 验证批注")
        print(f"{'='*60}")
        print(f"🔍 验证批注是否成功添加...")

        verification = self.doc.verify_comments()

        print(f"\n验证结果:")
        print(f"  📊 批注总数: {verification['total']}")
        print(f"  ✓ 文档引用: {verification['found']}")
        if verification['missing'] > 0:
            print(f"  ✗ 缺失引用: {verification['missing']}")
            print(f"  ⚠️  警告: 有{verification['missing']}个批注可能无法正常显示")
        else:
            print(f"  ✓ 所有批注引用完整")

        # 显示批注列表预览
        if verification['comment_list']:
            print(f"\n批注列表预览 (前5个):")
            for i, comment in enumerate(verification['comment_list'][:5], 1):
                preview = comment['preview'].replace('\n', ' ')
                print(f"  {i}. [{comment['id']}] {comment['author']}: {preview}")
            if len(verification['comment_list']) > 5:
                print(f"  ... 还有 {len(verification['comment_list']) - 5} 个")

        return verification

    def step5_save(self, output_filename: str = None, validate: bool = True) -> bool:
        """
        步骤5: 保存并打包文档

        保存所有修改并打包为.docx文件。
        输出文件将保存在输出目录中。

        Args:
            output_filename: 输出文件名(如"合同_审核版.docx"),如果为None则使用原文件名加上"_reviewed"后缀
            validate: 是否验证文档

        Returns:
            bool: 成功返回True,失败返回False
        """
        print(f"\n{'='*60}")
        print(f"步骤5: 保存并打包文档")
        print(f"{'='*60}")
        print(f"💾 保存文档...")

        try:
            # 保存修改到临时目录
            self.doc.save(validate=validate)
            print(f"✓ 文档已保存到临时目录")

            # 如果未指定输出文件名,使用原文件名加上_reviewed后缀
            if output_filename is None:
                original_name = self.contract_path.stem
                output_filename = f"{original_name}_reviewed.docx"

            # 构建完整的输出路径
            output_path = str(self.output_dir / output_filename)

            # 打包为.docx文件
            pack_document(self.doc.unpacked_path, output_path, validate=False)
            file_size = Path(output_path).stat().st_size / 1024  # KB
            print(f"✓ 文档已打包: {output_path} ({file_size:.1f} KB)")

            return True
        except Exception as e:
            print(f"✗ 保存失败: {e}")
            print(f"  提示: 如果遇到验证错误,可以尝试设置 validate=False")
            self.comments_failed.append({
                'step': 'save',
                'error': str(e)
            })
            return False

    def step6_generate_summary(
        self,
        summary_text: Optional[str],
        summary_filename: str = "合同概要.docx",
        summary_font: str = "仿宋",
    ) -> bool:
        """
        步骤6: 合同概要提取

        将合同概要内容保存为DOCX富文本,输出到审核结果目录。

        Args:
            summary_text: 合同概要文本(严格按格式输出)
            summary_filename: 输出文件名
            summary_font: 概要字体(默认仿宋)

        Returns:
            bool: 成功返回True,失败返回False
        """
        print(f"\n{'='*60}")
        print(f"步骤6: 合同概要提取")
        print(f"{'='*60}")
        print(f"🧾 生成合同概要...")

        if not summary_text:
            print("⚠️  未提供合同概要内容,跳过该步骤")
            return True

        try:
            content = summary_text.strip()
            if not content.endswith("\n"):
                content += "\n"
            summary_path = self.output_dir / summary_filename
            render_summary_docx(content, summary_path, font_name=summary_font)
            self.summary_path = summary_path
            print(f"✓ 已生成合同概要: {summary_path.name}")
            return True
        except Exception as e:
            self.summary_error = str(e)
            self.comments_failed.append({
                'step': 'summary',
                'error': str(e)
            })
            print(f"✗ 合同概要生成失败: {e}")
            return False

    def step7_generate_opinion(
        self,
        opinion_text: Optional[str],
        opinion_filename: str = "综合审核意见.docx",
        opinion_font: str = "仿宋",
    ) -> bool:
        """
        步骤7: 生成综合审核意见

        将综合审核意见保存为DOCX富文本,输出到审核结果目录。

        Args:
            opinion_text: 综合审核意见文本(两段自然段落)
            opinion_filename: 输出文件名
            opinion_font: 意见字体(默认仿宋)

        Returns:
            bool: 成功返回True,失败返回False
        """
        print(f"\n{'='*60}")
        print(f"步骤7: 生成综合审核意见")
        print(f"{'='*60}")
        print(f"📝 生成综合审核意见...")

        if not opinion_text:
            print("⚠️  未提供综合审核意见内容,跳过该步骤")
            return True

        try:
            content = opinion_text.strip()
            if not content.endswith("\n"):
                content += "\n"
            opinion_path = self.output_dir / opinion_filename
            title_text = "综合审核意见"
            if self.output_language == "en":
                title_text = "Consolidated Review Opinion"
            render_opinion_docx(
                content,
                opinion_path,
                font_name=opinion_font,
                title_text=title_text,
            )
            self.opinion_path = opinion_path
            print(f"✓ 已生成综合审核意见: {opinion_path.name}")
            return True
        except Exception as e:
            self.opinion_error = str(e)
            self.comments_failed.append({
                'step': 'opinion',
                'error': str(e)
            })
            print(f"✗ 综合审核意见生成失败: {e}")
            return False

    def step6_generate_flowchart(
        self,
        mermaid_code: Optional[str],
        mmd_filename: str = "business_flowchart.mmd",
        image_filename: str = "business_flowchart.png",
        render_image: bool = True,
        theme: str = "default",
        background_color: str = "white",
    ) -> bool:
        """
        步骤8: 生成业务流程图 (Mermaid)

        将 Mermaid flowchart 代码保存为 .mmd 文件并渲染为图片。
        输出文件保存在审核结果目录中。

        Args:
            mermaid_code: Mermaid flowchart 代码
            mmd_filename: .mmd 文件名
            image_filename: 图片文件名(.png/.svg)
            render_image: 是否渲染图片(默认True)
            theme: Mermaid 主题
            background_color: 背景色

        Returns:
            bool: 成功返回True,失败返回False
        """
        print(f"\n{'='*60}")
        print(f"步骤8: 生成业务流程图")
        print(f"{'='*60}")
        print(f"🗺️  生成业务流程图...")

        if not mermaid_code:
            print("⚠️  未提供Mermaid流程图代码,跳过该步骤")
            return True

        self.flowchart_error = None
        self.flowchart_rendered = False

        try:
            normalized = normalize_mermaid_code(mermaid_code)
            self.flowchart_mmd_path = write_mermaid_file(
                normalized,
                self.output_dir,
                mmd_filename,
            )
            print(f"✓ 已保存Mermaid源文件: {self.flowchart_mmd_path.name}")

            image_path = self.output_dir / image_filename
            self.flowchart_image_path = image_path
            if render_image:
                if image_path.exists():
                    try:
                        image_path.unlink()
                    except Exception:
                        pass
                render_mermaid_file(
                    self.flowchart_mmd_path,
                    image_path,
                    theme=theme,
                    background_color=background_color,
                )
                self.flowchart_rendered = True
                print(f"✓ 已渲染流程图图片: {self.flowchart_image_path.name}")
            else:
                print("⚠️  已跳过图片渲染(仅保存.mmd文件)")

            return True
        except Exception as e:
            self.flowchart_error = str(e)
            self.comments_failed.append({
                'step': 'flowchart',
                'error': str(e)
            })
            if self.flowchart_image_path and self.flowchart_image_path.exists():
                try:
                    self.flowchart_image_path.unlink()
                except Exception:
                    pass
            print(f"✗ 流程图生成失败: {e}")
            if isinstance(e, FileNotFoundError):
                print("  提示: 请安装 Mermaid CLI: npm i -g @mermaid-js/mermaid-cli")
            return False

    def step7_generate_report(self, report_filename: str = "review_report.txt") -> bool:
        """
        步骤9: 生成审核报告

        生成详细的审核报告,包括:
        - 审核基本信息
        - 批注统计
        - 失败批注详情
        - 验证结果
        - 执行时间

        报告将保存在输出目录中。

        Args:
            report_filename: 报告文件名(如"review_report.txt")

        Returns:
            bool: 成功返回True,失败返回False
        """
        print(f"\n{'='*60}")
        print(f"步骤9: 生成审核报告")
        print(f"{'='*60}")
        print(f"📄 生成审核报告...")

        try:
            duration = (datetime.now() - self.start_time).total_seconds()

            # 构建完整的报告路径
            report_path = str(self.output_dir / report_filename)

            precise_matches = [c for c in self.comments_added if not c.get('fallback_used', False)]
            fallback_matches = [c for c in self.comments_added if c.get('fallback_used', False)]
            comment_failures = [c for c in self.comments_failed if 'search' in c]
            other_failures = [c for c in self.comments_failed if 'search' not in c]
            language = self.output_language or "zh"

            with open(report_path, 'w', encoding='utf-8') as f:
                if language == "en":
                    f.write("=" * 60 + "\n")
                    f.write("Contract Review Comment Report\n")
                    f.write("=" * 60 + "\n\n")

                    f.write("1. Basic Information\n")
                    f.write("-" * 60 + "\n")
                    f.write(f"Reviewer: {self.reviewer_name}\n")
                    f.write(f"Document: {self.contract_path}\n")
                    f.write(f"Review Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Duration: {duration:.2f} seconds\n")
                    if self.summary_path or self.summary_error:
                        if self.summary_path:
                            f.write(f"Contract Summary: {self.summary_path.name}\n")
                        elif self.summary_error:
                            f.write(f"Contract Summary: Failed ({self.summary_error})\n")
                    if self.opinion_path or self.opinion_error:
                        if self.opinion_path:
                            f.write(f"Consolidated Opinion: {self.opinion_path.name}\n")
                        elif self.opinion_error:
                            f.write(f"Consolidated Opinion: Failed ({self.opinion_error})\n")

                    flowchart_image_path = self.flowchart_image_path
                    if flowchart_image_path is None:
                        candidate = self.output_dir / "business_flowchart.png"
                        if candidate.exists():
                            flowchart_image_path = candidate
                            self.flowchart_image_path = candidate

                    if self.flowchart_mmd_path or self.flowchart_error or self.flowchart_rendered:
                        if self.flowchart_rendered and flowchart_image_path and flowchart_image_path.exists():
                            f.write(f"Flowchart Image: {flowchart_image_path.name}\n")
                        elif self.flowchart_error:
                            f.write(f"Flowchart Image: Failed ({self.flowchart_error})\n")
                        if self.flowchart_mmd_path:
                            f.write(f"Flowchart Source: {self.flowchart_mmd_path.name}\n")
                    f.write("\n")

                    f.write("2. Comment Statistics\n")
                    f.write("-" * 60 + "\n")
                    f.write(f"Added Successfully: {len(self.comments_added)}\n")
                    if len(self.comments_added) > 0:
                        precise_rate = len(precise_matches) / len(self.comments_added) * 100
                        f.write(f"  - Exact Match: {len(precise_matches)} ({precise_rate:.1f}%)\n")
                        f.write(f"  - Fallback: {len(fallback_matches)} ({100-precise_rate:.1f}%)\n")
                    f.write(f"Failed: {len(comment_failures)}\n")
                    total_attempts = len(self.comments_added) + len(comment_failures)
                    success_rate = len(self.comments_added) / total_attempts * 100 if total_attempts else 0
                    f.write(f"Success Rate: {success_rate:.1f}%\n\n")

                    section_index = 3
                    if fallback_matches:
                        f.write(f"{section_index}. Fallback Comment Details\n")
                        f.write("-" * 60 + "\n")
                        f.write(
                            f"{len(fallback_matches)} comments were added to the document title because no exact match was found.\n\n"
                        )
                        for i, comment in enumerate(fallback_matches, 1):
                            f.write(f"{i}. Search Text: {comment['search']}\n")
                            f.write(f"   Risk Level: {comment['risk_level']}\n\n")
                        f.write("Note: These comments may require manual location in the document.\n\n")
                        section_index += 1

                    if comment_failures:
                        f.write(f"{section_index}. Failed Comment Details\n")
                        f.write("-" * 60 + "\n")
                        for i, failed in enumerate(comment_failures, 1):
                            f.write(f"{i}. Search Text: {failed['search']}\n")
                            f.write(f"   Failure Reason: {failed['reason']}\n\n")
                        section_index += 1

                    if other_failures:
                        f.write(f"{section_index}. Other Step Errors\n")
                        f.write("-" * 60 + "\n")
                        for i, failed in enumerate(other_failures, 1):
                            f.write(f"{i}. Step: {failed.get('step', 'unknown')}\n")
                            f.write(f"   Error: {failed['error']}\n\n")
                        section_index += 1

                    verification = self.doc.verify_comments()
                    f.write(f"\n{section_index}. Verification Results\n")
                    f.write("-" * 60 + "\n")
                    f.write(f"Total Comments: {verification['total']}\n")
                    f.write(f"References Found: {verification['found']}\n")
                    f.write(f"Missing References: {verification['missing']}\n")
                    section_index += 1

                    if verification['comment_list']:
                        f.write(f"\n{section_index}. Comment List\n")
                        f.write("-" * 60 + "\n")
                        for i, comment in enumerate(verification['comment_list'], 1):
                            f.write(f"{i}. [ID:{comment['id']}] {comment['author']}\n")
                            f.write(f"   Preview: {comment['preview']}\n\n")

                    f.write("\n" + "=" * 60 + "\n")
                    f.write(f"Report Generated At: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 60 + "\n")
                else:
                    f.write("=" * 60 + "\n")
                    f.write("合同审核批注报告\n")
                    f.write("=" * 60 + "\n\n")

                    # 基本信息
                    f.write("一、基本信息\n")
                    f.write("-" * 60 + "\n")
                    f.write(f"审核人: {self.reviewer_name}\n")
                    f.write(f"文档: {self.contract_path}\n")
                    f.write(f"审核时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"执行时长: {duration:.2f} 秒\n")
                    if self.summary_path or self.summary_error:
                        if self.summary_path:
                            f.write(f"合同概要: {self.summary_path.name}\n")
                        elif self.summary_error:
                            f.write(f"合同概要: 生成失败 ({self.summary_error})\n")
                    if self.opinion_path or self.opinion_error:
                        if self.opinion_path:
                            f.write(f"综合审核意见: {self.opinion_path.name}\n")
                        elif self.opinion_error:
                            f.write(f"综合审核意见: 生成失败 ({self.opinion_error})\n")
                    flowchart_image_path = self.flowchart_image_path
                    if flowchart_image_path is None:
                        candidate = self.output_dir / "business_flowchart.png"
                        if candidate.exists():
                            flowchart_image_path = candidate
                            self.flowchart_image_path = candidate

                    if self.flowchart_mmd_path or self.flowchart_error or self.flowchart_rendered:
                        if self.flowchart_rendered and flowchart_image_path and flowchart_image_path.exists():
                            f.write(f"流程图图片: {flowchart_image_path.name}\n")
                        elif self.flowchart_error:
                            f.write(f"流程图图片: 生成失败 ({self.flowchart_error})\n")
                        if self.flowchart_mmd_path:
                            f.write(f"流程图源码: {self.flowchart_mmd_path.name}\n")
                    f.write("\n")

                    # 批注统计
                    f.write("二、批注统计\n")
                    f.write("-" * 60 + "\n")
                    f.write(f"成功添加: {len(self.comments_added)} 个\n")

                    if len(self.comments_added) > 0:
                        precise_rate = len(precise_matches) / len(self.comments_added) * 100
                        f.write(f"  ├── 精准匹配: {len(precise_matches)} 个 ({precise_rate:.1f}%)\n")
                        f.write(f"  └── Fallback: {len(fallback_matches)} 个 ({100-precise_rate:.1f}%)\n")

                    f.write(f"添加失败: {len(comment_failures)} 个\n")
                    total_attempts = len(self.comments_added) + len(comment_failures)
                    success_rate = len(self.comments_added) / total_attempts * 100 if total_attempts else 0
                    f.write(f"成功率: {success_rate:.1f}%\n\n")

                    section_index = 3
                    if fallback_matches:
                        f.write(f"{_section_cn(section_index)}、Fallback批注详情\n")
                        f.write("-" * 60 + "\n")
                        f.write(f"以下{len(fallback_matches)}个批注因未找到精确匹配,已添加到文档标题:\n\n")
                        for i, comment in enumerate(fallback_matches, 1):
                            f.write(f"{i}. 搜索文本: {comment['search']}\n")
                            f.write(f"   风险等级: {comment['risk_level']}\n\n")
                        f.write("注意: 这些批注可能需要您手动定位到相关条款。\n\n")
                        section_index += 1

                    if comment_failures:
                        f.write(f"{_section_cn(section_index)}、失败批注详情\n")
                        f.write("-" * 60 + "\n")
                        for i, failed in enumerate(comment_failures, 1):
                            f.write(f"{i}. 搜索文本: {failed['search']}\n")
                            f.write(f"   失败原因: {failed['reason']}\n\n")
                        section_index += 1

                    if other_failures:
                        f.write(f"{_section_cn(section_index)}、其他步骤错误\n")
                        f.write("-" * 60 + "\n")
                        for i, failed in enumerate(other_failures, 1):
                            f.write(f"{i}. 步骤: {failed.get('step', 'unknown')}\n")
                            f.write(f"   错误信息: {failed['error']}\n\n")
                        section_index += 1

                    verification = self.doc.verify_comments()
                    f.write(f"\n{_section_cn(section_index)}、验证结果\n")
                    section_index += 1

                    f.write("-" * 60 + "\n")
                    f.write(f"批注总数: {verification['total']}\n")
                    f.write(f"文档引用: {verification['found']}\n")
                    f.write(f"缺失引用: {verification['missing']}\n")

                    if verification['comment_list']:
                        f.write(f"\n{_section_cn(section_index)}、批注列表\n")

                        f.write("-" * 60 + "\n")
                        for i, comment in enumerate(verification['comment_list'], 1):
                            f.write(f"{i}. [ID:{comment['id']}] {comment['author']}\n")
                            f.write(f"   预览: {comment['preview']}\n\n")

                    f.write("\n" + "=" * 60 + "\n")
                    f.write(f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 60 + "\n")

            print(f"✓ 报告已生成: {report_path}")
            return True

        except Exception as e:
            print(f"✗ 报告生成失败: {e}")
            return False

    def step8_cleanup_output(self,
    output_docx_filename: str,
    report_filename: str) -> Path:
        """
        步骤10: 清理输出,只保留最终结果文件

        在审核结果目录中,删除临时文件,只保留:
        1. 原合同(docx) - 已在step0复制到审核目录
        2. 审核后的合同(docx)
        3. 审核报告(txt)

        注意: 审核目录本身就是最终输出目录,无需创建新目录

        Args:
            output_docx_filename: 输出文档文件名
            report_filename: 报告文件名

        Returns:
            Path: 最终输出目录路径(即self.output_dir)
        """
        print(f"\n{'='*60}")
        print(f"步骤10: 清理输出文件")
        print(f"{'='*60}")
        print(f"🧹 清理中间文件,只保留最终结果...")

        try:
            # 最终输出目录就是当前工作目录
            final_output_dir = self.output_dir

            # 重命名审核后的合同
            source_docx = self.output_dir / output_docx_filename
            original_name = self.contract_path.stem
            if self.output_language == "en":
                target_docx = final_output_dir / f"{original_name}_Reviewed.docx"
            else:
                target_docx = final_output_dir / f"{original_name}_审核版.docx"

            if source_docx.exists() and source_docx != target_docx:
                shutil.move(str(source_docx), str(target_docx))
                print(f"✓ 已重命名审核后的合同: {target_docx.name}")
            elif source_docx.exists():
                print(f"✓ 审核后的合同: {target_docx.name}")

            # 重命名审核报告
            source_report = self.output_dir / report_filename
            if self.output_language == "en":
                target_report = final_output_dir / "Review_Report.txt"
            else:
                target_report = final_output_dir / "审核报告.txt"

            if source_report.exists() and source_report != target_report:
                shutil.move(str(source_report), str(target_report))
                print(f"✓ 已重命名审核报告: {target_report.name}")
            elif source_report.exists():
                print(f"✓ 审核报告: {target_report.name}")

            # 删除unpacked临时目录
            unpacked_dir = self.output_dir / "unpacked"
            if unpacked_dir.exists():
                try:
                    shutil.rmtree(unpacked_dir)
                    print(f"✓ 已删除临时目录: {unpacked_dir.name}")
                except Exception as e:
                    print(f"⚠️  删除临时目录失败: {e}")

            print(f"\n✓ 清理完成!")
            print(f"  📁 最终输出目录: {final_output_dir}")
            output_files = [
                f"{self.contract_path.name} (原合同)",
                target_docx.name,
                target_report.name,
            ]

            if self.summary_path and self.summary_path.exists():
                output_files.append(self.summary_path.name)
            if self.opinion_path and self.opinion_path.exists():
                output_files.append(self.opinion_path.name)
            if self.flowchart_rendered and self.flowchart_image_path and self.flowchart_image_path.exists():
                output_files.append(self.flowchart_image_path.name)
            if self.flowchart_mmd_path and self.flowchart_mmd_path.exists():
                output_files.append(self.flowchart_mmd_path.name)

            print(f"  📄 包含文件:")
            for i, filename in enumerate(output_files, 1):
                print(f"    {i}. {filename}")

            return final_output_dir

        except Exception as e:
            print(f"✗ 清理失败: {e}")
            print(f"⚠️  最终文件仍在: {self.output_dir}")
            return self.output_dir

    def run_full_workflow(self,
                         comments: List[Dict],
                         output_docx_filename: str = None,
                         report_filename: str = "review_report.txt",
                         validate_doc: bool = False,
                         cleanup: bool = True,
                         parallel_outputs: bool = True,
                         summary_text: Optional[str] = None,
                         summary_filename: str = "合同概要.docx",
                         summary_font: str = "仿宋",
                         opinion_text: Optional[str] = None,
                         opinion_filename: str = "综合审核意见.docx",
                         opinion_font: str = "仿宋",
                         flowchart_mermaid: Optional[str] = None,
                         flowchart_mmd_filename: str = "business_flowchart.mmd",
                         flowchart_image_filename: str = "business_flowchart.png",
                         render_flowchart: bool = True) -> bool:
        """
        运行完整工作流程

        按顺序执行所有步骤:复制原合同→解包→初始化→添加批注→验证→保存→生成合同概要→生成综合审核意见→生成流程图→生成报告→清理输出

        工作流程:
        1. 创建审核结果目录: 中文为“审核结果：原合同文件名”，英文为“Review_Result_{原合同文件名}”
        2. 复制原合同到审核目录
        3. 在审核目录中进行审核操作
        4. 清理临时文件,只保留基础文件(如有概要/意见/流程图输出,会一并保留):
           - 原合同(docx)
           - 审核后的合同(docx)
           - 审核报告(txt)

        Args:
            comments: 批注列表
            output_docx_filename: 输出文档文件名(如"合同_审核版.docx"),如果为None则自动生成
            report_filename: 报告文件名(如"review_report.txt")
            validate_doc: 是否验证文档(默认False,避免OOXML兼容性问题导致保存失败)
            cleanup: 是否清理中间文件(默认True)
            summary_text: 合同概要文本(如提供则输出概要文件)
            summary_filename: 合同概要文件名
            summary_font: 合同概要字体(默认仿宋)
            parallel_outputs: 是否并行生成概要/意见/流程图(默认True)
            opinion_text: 综合审核意见文本(如提供则输出意见文件)
            opinion_filename: 综合审核意见文件名
            opinion_font: 综合审核意见字体(默认仿宋)
            flowchart_mermaid: Mermaid流程图代码(如提供则生成流程图文件)
            flowchart_mmd_filename: Mermaid源文件名(.mmd)
            flowchart_image_filename: Mermaid渲染图片名(.png/.svg)
            render_flowchart: 是否渲染图片(默认True)

        Returns:
            bool: 全部步骤成功返回True,否则返回False

        注意:
            默认禁用Schema验证(validate_doc=False),原因:
            1. 部分Word文档包含不间断空格(\\xa0),需要xml:space='preserve'属性
            2. 部分文档已有批注扩展文件(commentsExtensible.xml等)
            3. 这些格式问题不影响Word正常使用,但会导致验证失败
            4. 如需严格验证,可手动设置validate_doc=True
        """
        print("\n" + "=" * 60)
        print("合同审核工作流程")
        print("Contract Review Workflow")
        print("=" * 60)

        output_language = _detect_output_language(summary_text, opinion_text, flowchart_mermaid)
        if output_language is None:
            output_language = _detect_output_language_from_contract(self.contract_path)
        if output_language is None:
            output_language = "en"
        self.output_language = output_language
        self._ensure_output_dir_for_language(output_language)
        if output_language == "en":
            if self.reviewer_name == "合同审核助手":
                self.reviewer_name = "Contract Review Assistant"
            if self.reviewer_initials == "审核":
                self.reviewer_initials = "CR"
            if summary_font == "仿宋":
                summary_font = "Times New Roman"
            if opinion_font == "仿宋":
                opinion_font = "Times New Roman"
            if report_filename == "review_report.txt":
                report_filename = "Review_Report.txt"
        if output_language == "en":
            if summary_filename == "合同概要.docx":
                summary_filename = "Contract_Summary.docx"
            if opinion_filename == "综合审核意见.docx":
                opinion_filename = "Consolidated_Opinion.docx"
        print(f"\n📁 审核输出目录: {self.output_dir}")

        # 执行所有步骤
        success = True

        # 步骤0: 复制原合同到审核目录
        if not self.step0_copy_contract():
            return False

        if not self.step1_unpack():
            return False

        if not self.step2_initialize():
            return False

        if not self.step3_add_comments(comments):
            print("\n⚠️  部分批注添加失败,但继续保存...")
            success = False

        verification = self.step4_verify()
        if verification['missing'] > 0:
            print("\n⚠️  验证发现问题,但继续保存...")
            success = False

        if not self.step5_save(output_docx_filename, validate=validate_doc):
            return False

        if parallel_outputs and (summary_text or opinion_text or flowchart_mermaid):
            tasks = {}
            with ThreadPoolExecutor(max_workers=3) as executor:
                if summary_text:
                    tasks[executor.submit(
                        self.step6_generate_summary,
                        summary_text,
                        summary_filename,
                        summary_font,
                    )] = "summary"
                if opinion_text:
                    tasks[executor.submit(
                        self.step7_generate_opinion,
                        opinion_text,
                        opinion_filename,
                        opinion_font,
                    )] = "opinion"
                if flowchart_mermaid:
                    tasks[executor.submit(
                        self.step6_generate_flowchart,
                        flowchart_mermaid,
                        flowchart_mmd_filename,
                        flowchart_image_filename,
                        render_flowchart,
                    )] = "flowchart"

                for future in as_completed(tasks):
                    try:
                        ok = future.result()
                    except Exception as e:
                        ok = False
                        step_name = tasks[future]
                        self.comments_failed.append({
                            'step': step_name,
                            'error': str(e)
                        })
                        print(f"✗ 输出生成失败: {step_name} - {e}")
                    if not ok:
                        success = False
        else:
            if not self.step6_generate_summary(summary_text, summary_filename, summary_font):
                success = False

            if not self.step7_generate_opinion(opinion_text, opinion_filename, opinion_font):
                success = False

            if not self.step6_generate_flowchart(
                flowchart_mermaid,
                flowchart_mmd_filename,
                flowchart_image_filename,
                render_image=render_flowchart,
            ):
                success = False

        if not self.step7_generate_report(report_filename):
            success = False

        # 清理输出,只保留最终结果
        if cleanup:
            # 构建输出文件名
            if output_docx_filename is None:
                original_name = self.contract_path.stem
                output_docx_filename = f"{original_name}_reviewed.docx"

            # 执行清理
            final_output_dir = self.step8_cleanup_output(output_docx_filename, report_filename)

            # 获取最终文件路径
            original_name = self.contract_path.stem
            if self.output_language == "en":
                final_docx = final_output_dir / f"{original_name}_Reviewed.docx"
                final_report = final_output_dir / "Review_Report.txt"
            else:
                final_docx = final_output_dir / f"{original_name}_审核版.docx"
                final_report = final_output_dir / "审核报告.txt"
        else:
            # 不清理,使用临时目录
            final_output_dir = self.output_dir
            if output_docx_filename is None:
                output_docx_filename = f"{self.contract_path.stem}_reviewed.docx"
            final_docx = final_output_dir / output_docx_filename
            final_report = final_output_dir / report_filename

        # 最终总结
        print("\n" + "=" * 60)
        print("工作流程完成!")
        print("=" * 60)
        print(f"\n📊 最终统计:")
        print(f"  ✓ 成功添加批注: {len(self.comments_added)} 个")
        comment_failures = [c for c in self.comments_failed if 'search' in c]
        print(f"  ✗ 添加失败: {len(comment_failures)} 个")

        # 统计精准匹配和fallback
        precise_matches = [c for c in self.comments_added if not c.get('fallback_used', False)]
        fallback_matches = [c for c in self.comments_added if c.get('fallback_used', False)]

        if len(self.comments_added) > 0:
            precise_rate = len(precise_matches) / len(self.comments_added) * 100
            print(f"\n精准匹配情况:")
            print(f"  🎯 精准匹配: {len(precise_matches)} 个 ({precise_rate:.1f}%)")
            print(f"  🔄 Fallback: {len(fallback_matches)} 个 ({100-precise_rate:.1f}%)")

        print(f"\n📁 最终输出:")
        print(f"  📄 审核后的合同: {final_docx}")
        print(f"  📋 审核报告: {final_report}")
        if summary_text:
            if self.summary_path:
                print(f"  🧾 合同概要: {self.summary_path}")
            elif self.summary_error:
                print(f"  ⚠️ 合同概要生成失败: {self.summary_error}")
        if opinion_text:
            if self.opinion_path:
                print(f"  📝 综合审核意见: {self.opinion_path}")
            elif self.opinion_error:
                print(f"  ⚠️ 综合审核意见生成失败: {self.opinion_error}")
        if flowchart_mermaid:
            if self.flowchart_rendered and self.flowchart_image_path and self.flowchart_image_path.exists():
                print(f"  🗺️ 业务流程图: {self.flowchart_image_path}")
            elif self.flowchart_error:
                print(f"  ⚠️ 业务流程图生成失败: {self.flowchart_error}")
            if self.flowchart_mmd_path:
                print(f"  🧾 Mermaid源文件: {self.flowchart_mmd_path}")
        print(f"  📂 输出目录: {final_output_dir}")
        print(f"  ⏱️  总耗时: {(datetime.now() - self.start_time).total_seconds():.2f} 秒")

        if success:
            print(f"\n✅ 所有步骤执行成功!")
        else:
            print(f"\n⚠️  工作流程完成,但部分步骤存在问题,请查看报告详情。")

        return success


# 便捷函数
def review_contract(contract_path: str,
                   comments: List[Dict],
                   output_docx_filename: str = None,
                   reviewer_name: str = "合同审核助手",
                   report_filename: str = "review_report.txt",
                   output_dir: str = None,
                   enable_smart_keyword_expansion: bool = False,
                   summary_text: Optional[str] = None,
                   summary_filename: str = "合同概要.docx",
                   summary_font: str = "仿宋",
                   opinion_text: Optional[str] = None,
                   opinion_filename: str = "综合审核意见.docx",
                   opinion_font: str = "仿宋",
                   flowchart_mermaid: Optional[str] = None,
                   flowchart_mmd_filename: str = "business_flowchart.mmd",
                   flowchart_image_filename: str = "business_flowchart.png",
                   render_flowchart: bool = True,
                   parallel_outputs: bool = True) -> bool:
    """
    便捷函数:一键完成合同审核

    创建审核结果目录: 中文为“审核结果：原合同文件名”，英文为“Review_Result_{原合同文件名}”
    所有文件(原合同、审核后的合同、审核报告)将保存在审核结果目录中。

    Args:
        contract_path: 合同文档路径
        comments: 批注列表
        output_docx_filename: 输出文档文件名(如"合同_审核版.docx"),如果为None则自动生成
        reviewer_name: 审核人姓名
        report_filename: 报告文件名(如"review_report.txt")
        output_dir: 输出目录路径(如果为None,自动创建默认审核结果文件夹)
        enable_smart_keyword_expansion: 是否启用智能关键词扩展(默认False)
        summary_text: 合同概要文本(如提供则输出概要文件)
        summary_filename: 合同概要文件名
        summary_font: 合同概要字体(默认仿宋)
        opinion_text: 综合审核意见文本(如提供则输出意见文件)
        opinion_filename: 综合审核意见文件名
        opinion_font: 综合审核意见字体(默认仿宋)
        flowchart_mermaid: Mermaid流程图代码(如提供则生成流程图文件)
        flowchart_mmd_filename: Mermaid源文件名(.mmd)
        flowchart_image_filename: Mermaid渲染图片名(.png/.svg)
        render_flowchart: 是否渲染图片(默认True)
        parallel_outputs: 是否并行生成概要/意见/流程图(默认True)

    Returns:
        bool: 成功返回True,失败返回False

    Example:
        >>> comments = [{"search": "合同总价", "comment": "批注内容"}]
        >>> review_contract("合同.docx", comments, "合同_审核版.docx")
        >>> # 最终输出: 审核结果：合同.docx/
        >>> #           ├── 合同.docx (原合同)
        >>> #           ├── 合同_审核版.docx
        >>> #           ├── 审核报告.txt
        >>> #           ├── 合同概要.docx (如提供概要)
        >>> #           ├── 综合审核意见.docx (如提供意见)
        >>> #           ├── business_flowchart.png (如提供流程图)
        >>> #           └── business_flowchart.mmd (如提供流程图)
        >>> # 或者使用自定义输出目录
        >>> review_contract("合同.docx", comments, output_dir="my_output")
    """
    workflow = ContractReviewWorkflow(
        contract_path,
        reviewer_name,
        output_dir,
        enable_smart_keyword_expansion=enable_smart_keyword_expansion,
    )
    return workflow.run_full_workflow(
        comments,
        output_docx_filename,
        report_filename,
        summary_text=summary_text,
        summary_filename=summary_filename,
        summary_font=summary_font,
        opinion_text=opinion_text,
        opinion_filename=opinion_filename,
        opinion_font=opinion_font,
        flowchart_mermaid=flowchart_mermaid,
        flowchart_mmd_filename=flowchart_mmd_filename,
        flowchart_image_filename=flowchart_image_filename,
        render_flowchart=render_flowchart,
        parallel_outputs=parallel_outputs,
    )


if __name__ == "__main__":
    # 示例用法
    print("Contract Review Workflow")
    print("这是一个工作流程模块,请导入使用:")
    print()
    print("from scripts.workflow import ContractReviewWorkflow")
    print()
    print("comments = [")
    print('    {"search": "关键词", "comment": "批注内容"},')
    print("]")
    print()
    print('workflow = ContractReviewWorkflow("合同.docx", "审核人")')
    print('workflow.run_full_workflow(comments, "合同_审核版.docx")')
