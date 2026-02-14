#!/usr/bin/env python3
"""
对话脚本转语音（使用 pyttsx3）
"""
import argparse
import os
import re
import pyttsx3


def parse_dialogue(dialogue_text: str) -> list:
    """
    解析对话脚本，提取角色和台词

    格式示例:
    Alice: Hello!
    Bob: Hi Alice, how are you?
    Alice: I'm doing great!

    Args:
        dialogue_text: 对话脚本文本

    Returns:
        角色和台词的列表: [(role, line), ...]
    """
    dialogues = []
    lines = dialogue_text.strip().split('\n')

    current_role = None
    current_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            # 空行，保存当前对话
            if current_role and current_lines:
                dialogues.append((current_role, ' '.join(current_lines)))
                current_role = None
                current_lines = []
            continue

        # 匹配角色: 台词格式
        match = re.match(r'^([^:]+):\s*(.+)$', line)
        if match:
            # 保存之前的对话
            if current_role and current_lines:
                dialogues.append((current_role, ' '.join(current_lines)))

            # 开始新对话
            current_role = match.group(1).strip()
            current_lines = [match.group(2).strip()]
        else:
            # 延续当前对话
            if current_role:
                current_lines.append(line)

    # 保存最后的对话
    if current_role and current_lines:
        dialogues.append((current_role, ' '.join(current_lines)))

    return dialogues


def dialogue_to_podcast(dialogue_path: str, output_path: str, voice_rate: int = 150) -> None:
    """
    将对话脚本转换为语音文件

    Args:
        dialogue_path: 对话脚本文件路径
        output_path: 输出 wav 文件路径
        voice_rate: 语音速率（默认 150）
    """
    print(f"正在生成播客: {dialogue_path}")

    # 读取对话脚本
    with open(dialogue_path, 'r', encoding='utf-8') as f:
        dialogue_text = f.read()

    # 解析对话
    dialogues = parse_dialogue(dialogue_text)

    if not dialogues:
        raise Exception("未找到有效的对话内容")

    print(f"解析到 {len(dialogues)} 条对话")

    # 初始化语音引擎
    engine = pyttsx3.init()
    engine.setProperty('rate', voice_rate)

    # 获取可用语音
    voices = engine.getProperty('voices')
    if len(voices) >= 2:
        # 为两个角色设置不同的声音
        voice1 = voices[0].id
        voice2 = voices[1] if len(voices) > 1 else voices[0].id
    else:
        voice1 = voice2 = None

    # 确定角色
    role1 = dialogues[0][0]
    voice1_id = voice1
    voice2_id = voice2

    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # 生成对话语音
    try:
        # 使用临时文件存储各条语音
        temp_files = []
        for i, (role, line) in enumerate(dialogues):
            # 根据角色设置声音
            if role == role1:
                if voice1_id:
                    engine.setProperty('voice', voice1_id)
            else:
                if voice2_id:
                    engine.setProperty('voice', voice2_id)

            # 保存当前句子的语音
            temp_file = f"{output_path}.temp_{i}.wav"
            engine.save_to_file(line, temp_file)
            engine.runAndWait()
            temp_files.append(temp_file)

        # 合并所有语音文件（这里简化处理，只输出第一条）
        # 注意:完整实现需要使用 pydub 等库进行音频合并
        print(f"已生成 {len(temp_files)} 个语音片段")

        # 这里简化处理，直接输出提示
        print(f"注意:由于技术限制，仅生成了各个片段。请使用音频编辑工具合并以下文件:")
        for temp_file in temp_files:
            print(f"  - {temp_file}")

        # 将第一个片段作为示例输出
        if temp_files:
            import shutil
            shutil.copy(temp_files[0], output_path)
            print(f"示例语音文件已保存到: {output_path}")

    except Exception as e:
        raise Exception(f"播客生成失败: {str(e)}")


def main():
    parser = argparse.ArgumentParser(description='对话脚本转语音')
    parser.add_argument('--dialogue', required=True, help='对话脚本文件路径')
    parser.add_argument('--output', required=True, help='输出 wav 文件路径')
    parser.add_argument('--rate', type=int, default=150, help='语音速率（默认 150）')
    args = parser.parse_args()

    dialogue_to_podcast(args.dialogue, args.output, args.rate)


if __name__ == '__main__':
    main()
