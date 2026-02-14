#!/usr/bin/env python3
"""
复制文本到系统剪贴板

支持平台：macOS, Windows, Linux
用途：辅助手动发布，将内容复制到剪贴板供用户粘贴使用
"""

import argparse
import os
import sys


def copy_text_to_clipboard_macos(text: str) -> bool:
    """复制文本到macOS剪贴板"""
    try:
        from AppKit import NSPasteboard, NSPasteboardTypeString

        pasteboard = NSPasteboard.generalPasteboard()
        pasteboard.clearContents()
        pasteboard.setString_forType_(text, NSPasteboardTypeString)
        return True

    except ImportError as e:
        print(f"错误: 缺少依赖: {e}", file=sys.stderr)
        print("安装: pip install pyobjc-framework-Cocoa", file=sys.stderr)
        return False
    except Exception as e:
        print(f"复制失败: {e}", file=sys.stderr)
        return False


def copy_text_to_clipboard_windows(text: str) -> bool:
    """复制文本到Windows剪贴板"""
    try:
        import pyperclip
        pyperclip.copy(text)
        return True
    except ImportError:
        # 回退到win32clipboard
        try:
            import win32clipboard
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(text, win32clipboard.CF_UNICODETEXT)
            win32clipboard.CloseClipboard()
            return True
        except ImportError:
            print(f"错误: 缺少依赖", file=sys.stderr)
            print("安装: pip install pyperclip 或 pip install pywin32", file=sys.stderr)
            return False
        except Exception as e:
            print(f"复制失败: {e}", file=sys.stderr)
            return False
    except Exception as e:
        print(f"复制失败: {e}", file=sys.stderr)
        return False


def copy_text_to_clipboard_linux(text: str) -> bool:
    """复制文本到Linux剪贴板"""
    try:
        import subprocess
        
        # 尝试使用xclip
        try:
            process = subprocess.Popen(['xclip', '-selection', 'clipboard'],
                                      stdin=subprocess.PIPE)
            process.communicate(text.encode('utf-8'))
            return True
        except FileNotFoundError:
            pass
        
        # 尝试使用xsel
        try:
            process = subprocess.Popen(['xsel', '--clipboard', '--input'],
                                      stdin=subprocess.PIPE)
            process.communicate(text.encode('utf-8'))
            return True
        except FileNotFoundError:
            pass
        
        print(f"错误: 需要xclip或xsel工具", file=sys.stderr)
        print("安装: sudo apt-get install xclip 或 sudo apt-get install xsel", file=sys.stderr)
        return False
        
    except Exception as e:
        print(f"复制失败: {e}", file=sys.stderr)
        return False


def copy_text_to_clipboard(text: str) -> bool:
    """根据平台复制文本到剪贴板"""
    import platform
    system = platform.system()
    
    if system == 'Darwin':
        return copy_text_to_clipboard_macos(text)
    elif system == 'Windows':
        return copy_text_to_clipboard_windows(text)
    elif system == 'Linux':
        return copy_text_to_clipboard_linux(text)
    else:
        print(f"错误: 不支持的平台 {system}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="复制文本到系统剪贴板",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 直接复制文本
  python copy_to_clipboard.py --text "要复制的文本"
  
  # 从文件复制
  python copy_to_clipboard.py --file /path/to/file.txt
  
  # 复制文章内容
  python copy_to_clipboard.py --title "文章标题" --content "文章内容"
        """
    )
    
    parser.add_argument("--text", help="要复制的文本")
    parser.add_argument("--file", help="从文件读取文本")
    parser.add_argument("--title", help="文章标题")
    parser.add_argument("--content", help="文章内容")
    parser.add_argument("--output", action='store_true',
                       help="输出复制的文本（用于验证）")
    
    args = parser.parse_args()
    
    # 确定要复制的文本
    text_to_copy = None
    
    if args.text:
        text_to_copy = args.text
    elif args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                text_to_copy = f.read()
        except Exception as e:
            print(f"错误: 读取文件失败: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.title or args.content:
        # 组合标题和内容
        parts = []
        if args.title:
            parts.append(args.title)
        if args.content:
            parts.append(args.content)
        text_to_copy = '\n\n'.join(parts)
    else:
        # 从标准输入读取
        text_to_copy = sys.stdin.read()
    
    if not text_to_copy:
        print("错误: 没有提供要复制的文本", file=sys.stderr)
        sys.exit(1)
    
    # 复制到剪贴板
    if copy_text_to_clipboard(text_to_copy):
        print("✅ 文本已复制到剪贴板")
        
        if args.output:
            print("\n" + "="*50)
            print("复制的文本:")
            print("="*50)
            print(text_to_copy)
            print("="*50)
        
        return 0
    else:
        print("❌ 复制失败", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
