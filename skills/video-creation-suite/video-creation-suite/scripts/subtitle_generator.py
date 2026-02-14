#!/usr/bin/env python3
"""
字幕文件生成脚本
根据分镜脚本生成SRT/ASS格式字幕文件
"""

import os
import sys
from typing import Dict, Any, List


def generate_subtitle(subtitle_data: Dict[str, Any],
                      output_file: str,
                      format: str = "srt") -> bool:
    """
    生成字幕文件

    参数:
        subtitle_data: 字幕数据,包含文本和时间戳
        output_file: 输出文件路径
        format: 字幕格式 (srt/ass)

    返回:
        是否成功
    """
    try:
        # 获取字幕条目
        subtitles = subtitle_data.get('subtitles', [])

        if not subtitles:
            raise ValueError("字幕数据中没有条目")

        # 确保输出目录存在
        output_dir = os.path.dirname(output_file)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        # 根据格式生成字幕
        if format.lower() == "srt":
            content = generate_srt_content(subtitles)
        elif format.lower() == "ass":
            content = generate_ass_content(subtitles)
        else:
            raise ValueError(f"不支持的字幕格式: {format}")

        # 写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)

        return True

    except Exception as e:
        print(f"生成字幕文件失败: {str(e)}")
        return False


def generate_srt_content(subtitles: List[Dict[str, Any]]) -> str:
    """
    生成SRT格式内容

    参数:
        subtitles: 字幕条目列表

    返回:
        SRT格式内容字符串
    """
    lines = []

    for i, sub in enumerate(subtitles, start=1):
        start_time = sub.get('start_time', '00:00:00,000')
        end_time = sub.get('end_time', '00:00:00,000')
        text = sub.get('text', '')
        position = sub.get('position', 'bottom center')

        lines.append(f"{i}")
        lines.append(f"{start_time} --> {end_time}")
        # SRT格式不支持位置标注,这里简化处理
        lines.append(text)
        lines.append("")

    return "\n".join(lines)


def generate_ass_content(subtitles: List[Dict[str, Any]]) -> str:
    """
    生成ASS格式内容

    参数:
        subtitles: 字幕条目列表

    返回:
        ASS格式内容字符串
    """
    lines = []

    # ASS头部
    lines.append("[Script Info]")
    lines.append("Title: Generated Subtitle")
    lines.append("ScriptType: v4.00+")
    lines.append("")

    lines.append("[V4+ Styles]")
    lines.append("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding")
    lines.append("Style: Default,Arial,20,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,0,2,10,10,10,1")
    lines.append("")

    lines.append("[Events]")
    lines.append("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text")
    lines.append("")

    for sub in subtitles:
        start_time = sub.get('start_time', '0:00:00.00')
        end_time = sub.get('end_time', '0:00:00.00')
        text = sub.get('text', '')
        position = sub.get('position', 'bottom center')

        # 转换时间格式
        start_ass = convert_to_ass_time(start_time)
        end_ass = convert_to_ass_time(end_time)

        # 位置标注
        position_tag = ""
        if position == "bottom center":
            position_tag = "{\\an8}"  # 底部居中
        elif position == "top center":
            position_tag = "{\\an2}"  # 顶部居中
        elif position == "center":
            position_tag = "{\\an5}"  # 居中

        lines.append(f"Dialogue: 0,{start_ass},{end_ass},Default,,0,0,0,,{position_tag}{text}")

    return "\n".join(lines)


def convert_to_ass_time(time_str: str) -> str:
    """
    转换时间格式为ASS格式

    参数:
        time_str: 时间字符串,格式如 "00:00:00,000" 或 "0:00:00.00"

    返回:
        ASS格式时间字符串
    """
    # 替换逗号为点
    time_str = time_str.replace(',', '.')

    # 解析时间
    if ':' in time_str:
        parts = time_str.split(':')
        hours = parts[0].zfill(1)
        minutes = parts[1].zfill(2)
        seconds = parts[2].split('.')[0].zfill(2)
        centiseconds = parts[2].split('.')[1][:2].zfill(2)
    else:
        raise ValueError(f"时间格式错误: {time_str}")

    return f"{hours}:{minutes}:{seconds}.{centiseconds}"


def validate_subtitle_data(subtitle_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    验证字幕数据

    参数:
        subtitle_data: 字幕数据

    返回:
        验证结果字典
    """
    result = {
        'valid': True,
        'errors': [],
        'warnings': []
    }

    subtitles = subtitle_data.get('subtitles', [])

    if not subtitles:
        result['valid'] = False
        result['errors'].append("字幕数据中没有条目")
        return result

    # 验证每个条目
    for i, sub in enumerate(subtitles):
        # 检查必需字段
        if 'text' not in sub:
            result['warnings'].append(f"条目{i+1}缺少文本")
        if 'start_time' not in sub:
            result['errors'].append(f"条目{i+1}缺少开始时间")
        if 'end_time' not in sub:
            result['errors'].append(f"条目{i+1}缺少结束时间")

        # 检查时间格式
        if 'start_time' in sub:
            try:
                convert_to_ass_time(sub['start_time'])
            except:
                result['errors'].append(f"条目{i+1}的开始时间格式错误")
        if 'end_time' in sub:
            try:
                convert_to_ass_time(sub['end_time'])
            except:
                result['errors'].append(f"条目{i+1}的结束时间格式错误")

    if result['errors']:
        result['valid'] = False

    return result


def print_validation_result(result: Dict[str, Any]):
    """
    打印验证结果

    参数:
        result: 验证结果字典
    """
    if result['valid']:
        print("✅ 字幕数据验证通过")
    else:
        print("❌ 字幕数据验证失败")

    if result['errors']:
        print("\n错误:")
        for error in result['errors']:
            print(f"  - {error}")

    if result['warnings']:
        print("\n警告:")
        for warning in result['warnings']:
            print(f"  - {warning}")


if __name__ == '__main__':
    import argparse
    import json

    parser = argparse.ArgumentParser(description='字幕文件生成脚本')
    parser.add_argument('--subtitle', type=str, required=True,
                       help='字幕数据JSON文件路径')
    parser.add_argument('--output', type=str, required=True,
                       help='输出文件路径')
    parser.add_argument('--format', type=str, default="srt",
                       choices=['srt', 'ass'],
                       help='字幕格式')

    args = parser.parse_args()

    # 读取字幕数据
    with open(args.subtitle, 'r', encoding='utf-8') as f:
        subtitle_data = json.load(f)

    # 验证字幕数据
    validation_result = validate_subtitle_data(subtitle_data)
    print_validation_result(validation_result)

    if not validation_result['valid']:
        sys.exit(1)

    # 生成字幕文件
    success = generate_subtitle(
        subtitle_data=subtitle_data,
        output_file=args.output,
        format=args.format
    )

    if success:
        print(f"\n✅ 字幕文件生成成功: {args.output}")
    else:
        print(f"\n❌ 字幕文件生成失败")
        sys.exit(1)
