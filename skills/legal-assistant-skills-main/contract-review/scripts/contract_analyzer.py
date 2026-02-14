#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合同智能分析模块

自动提取合同文本,识别合同类型和关键条款位置,
为批注提供智能搜索关键词或行号定位。
"""

import subprocess
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from defusedxml import minidom


class ContractAnalyzer:
    """合同智能分析器"""

    def __init__(self, contract_path: str):
        """
        初始化分析器

        Args:
            contract_path: 合同文件路径
        """
        self.contract_path = Path(contract_path)
        self.full_text = ""
        self.paragraphs = []
        self.contract_type = "unknown"
        self.key_clauses = {}

    def extract_text(self) -> str:
        """
        使用pandoc提取合同纯文本

        Returns:
            str: 合同的纯文本内容
        """
        try:
            result = subprocess.run(
                ["pandoc", "-f", "docx", "-t", "plain", str(self.contract_path)],
                capture_output=True,
                text=True,
                check=True,
                timeout=30
            )
            self.full_text = result.stdout
            return self.full_text
        except subprocess.CalledProcessError as e:
            print(f"⚠️  pandoc提取失败: {e}")
            return ""
        except subprocess.TimeoutExpired:
            print(f"⚠️  pandoc提取超时")
            return ""
        except FileNotFoundError:
            print(f"⚠️  未找到pandoc命令,请先安装: sudo apt-get install pandoc")
            return ""

    def extract_paragraphs_with_line_numbers(self) -> List[Tuple[int, str]]:
        """
        提取段落文本及对应的行号

        Returns:
            List[Tuple[int, str]]: [(行号, 段落文本), ...]列表
        """
        if not self.full_text:
            self.extract_text()

        lines = self.full_text.split('\n')
        self.paragraphs = []

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped:  # 跳过空行
                self.paragraphs.append((i, stripped))

        return self.paragraphs

    def identify_contract_type(self) -> str:
        """
        识别合同类型

        Returns:
            str: 合同类型 (training/purchase/service/cooperation/unknown)
        """
        if not self.full_text:
            self.extract_text()

        text_lower = self.full_text.lower()

        # 关键词匹配规则
        type_keywords = {
            "training": ["培训", "训练", "课程", "讲师", "学员"],
            "purchase": ["采购", "购销", "买方", "卖方", "订购", "货物"],
            "service": ["服务", "提供", "服务费", "维护", "技术支持"],
            "cooperation": ["合作", "推广", "联合", "协议", "框架"],
        }

        # 统计每种类型的关键词出现次数
        type_scores = {}
        for contract_type, keywords in type_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                type_scores[contract_type] = score

        # 返回得分最高的类型
        if type_scores:
            self.contract_type = max(type_scores, key=type_scores.get)
        else:
            self.contract_type = "unknown"

        return self.contract_type

    def find_clause_location(self, search_keywords: List[str]) -> Optional[int]:
        """
        查找包含指定关键词的条款所在行号

        Args:
            search_keywords: 搜索关键词列表

        Returns:
            Optional[int]: 找到的行号,未找到返回None
        """
        if not self.paragraphs:
            self.extract_paragraphs_with_line_numbers()

        # 遍历所有段落,查找包含任一关键词的段落
        for line_num, paragraph in self.paragraphs:
            for keyword in search_keywords:
                if keyword in paragraph:
                    return line_num

        return None

    def analyze_common_fields(self) -> Dict[str, List[str]]:
        """
        分析合同中的常见字段,返回多个可能的搜索关键词

        支持中英文标点符号变体

        Returns:
            Dict[str, List[str]]: 字段名到关键词列表的映射
        """
        if not self.full_text:
            self.extract_text()

        # 定义常见字段,支持中英文标点符号变体
        common_fields = {
            "合同编号": [
                "合同编号:", "协议编号:", "合同号:", "协议号:", "编号:",
                "合同编号：", "协议编号：", "合同号：", "协议号：", "编号：",  # 中文冒号
            ],
            "合同金额": [
                "合同总金额", "协议总金额", "合同价款", "协议价款", "费用总额", "总金额",
                "¥", "人民币", "元",  # 金额符号
            ],
            "签署日期": [
                "签署日期", "签订日期", "签约日期", "签署时间", "生效日期",
                "签署日期：", "签订日期：",  # 中文冒号
            ],
            "甲方": [
                "甲方:", "甲方（", "需方:", "买方:", "委托方:",
                "甲方：", "甲方（", "需方：",  # 中文冒号
            ],
            "乙方": [
                "乙方:", "乙方（", "供方:", "卖方:", "服务方:",
                "乙方：", "乙方（", "供方：",  # 中文冒号
            ],
            "违约责任": [
                "违约责任", "违约金", "赔偿责任", "赔偿条款",
                "违约责任：", "违约金：",  # 中文冒号
            ],
            "争议解决": [
                "争议解决", "纠纷解决", "管辖", "诉讼", "仲裁",
                "争议解决：",  # 中文冒号
            ],
            "保密条款": [
                "保密", "商业秘密", "保密义务", "保密条款",
                "保密：",  # 中文冒号
            ],
        }

        # 检查每个字段在合同中的实际表述
        found_fields = {}
        for field_name, keywords in common_fields.items():
            found_keywords = []
            for keyword in keywords:
                if keyword in self.full_text:
                    found_keywords.append(keyword)
            if found_keywords:
                found_fields[field_name] = found_keywords

        return found_fields

    def generate_smart_search_keywords(self) -> Dict[str, List[str]]:
        """
        生成智能搜索关键词

        基于合同内容分析,为常见审核点提供最合适的搜索关键词。

        Returns:
            Dict[str, List[str]]: 审核点到关键词列表的映射
        """
        # 先分析常见字段
        common_fields = self.analyze_common_fields()

        # 生成智能搜索关键词映射
        smart_keywords = {
            "合同编号为空": common_fields.get("合同编号", ["合同编号:", "协议编号:"]),
            "金额表述不一致": common_fields.get("合同金额", ["合同总金额", "总金额", "¥"]),
            "签署日期": common_fields.get("签署日期", ["签署日期", "签订日期"]),
            "甲方信息": common_fields.get("甲方", ["甲方:"]),
            "乙方信息": common_fields.get("乙方", ["乙方:"]),
            "违约责任条款": common_fields.get("违约责任", ["违约责任", "违约金"]),
            "争议解决条款": common_fields.get("争议解决", ["争议解决", "协商"]),
            "保密条款": common_fields.get("保密条款", ["保密", "商业秘密"]),
        }

        return smart_keywords

    def get_contract_summary(self) -> Dict:
        """
        获取合同摘要信息

        Returns:
            Dict: 包含合同类型、关键词字段等信息的字典
        """
        if not self.full_text:
            self.extract_text()

        if not self.paragraphs:
            self.extract_paragraphs_with_line_numbers()

        if self.contract_type == "unknown":
            self.identify_contract_type()

        smart_keywords = self.generate_smart_search_keywords()

        return {
            "contract_type": self.contract_type,
            "total_paragraphs": len(self.paragraphs),
            "text_length": len(self.full_text),
            "smart_keywords": smart_keywords,
            "found_fields": len(smart_keywords)
        }


def demo():
    """演示合同分析功能"""
    # 示例用法
    analyzer = ContractAnalyzer("合同.docx")

    # 1. 提取文本
    text = analyzer.extract_text()
    print(f"提取文本长度: {len(text)}")

    # 2. 识别合同类型
    contract_type = analyzer.identify_contract_type()
    print(f"合同类型: {contract_type}")

    # 3. 分析常见字段
    common_fields = analyzer.analyze_common_fields()
    print(f"发现字段: {list(common_fields.keys())}")

    # 4. 生成智能搜索关键词
    smart_keywords = analyzer.generate_smart_search_keywords()
    print("智能搜索关键词:")
    for field, keywords in smart_keywords.items():
        print(f"  {field}: {keywords}")

    # 5. 获取合同摘要
    summary = analyzer.get_contract_summary()
    print(f"\n合同摘要: {summary}")


if __name__ == "__main__":
    demo()
