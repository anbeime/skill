#!/usr/bin/env python3
"""
执行网页打包命令
将网页 URL 转换为桌面应用
"""

import subprocess
import sys
import os
from typing import Optional, Dict


def build_app(
    url: str,
    name: Optional[str] = None,
    icon: Optional[str] = None,
    width: Optional[int] = None,
    height: Optional[int] = None,
    min_width: Optional[int] = None,
    min_height: Optional[int] = None,
    zoom: Optional[int] = None,
    options: Optional[Dict[str, any]] = None
) -> str:
    """
    执行网页打包

    Args:
        url: 网页 URL（必需）
        name: 应用名称
        icon: 图标路径（本地或远程 URL）
        width: 窗口宽度（默认 1200）
        height: 窗口高度（默认 780）
        min_width: 最小宽度
        min_height: 最小高度
        zoom: 初始缩放级别（50-200）
        options: 其他可选参数（字典格式）

    Returns:
        生成的应用文件路径

    Raises:
        ValueError: 参数验证失败
        RuntimeError: 打包失败
    """

    # 参数验证
    if not url:
        raise ValueError("URL 参数不能为空")

    # 构建 pake 命令
    cmd = ["pake", url]

    # 添加可选参数
    if name:
        cmd.extend(["--name", name])

    if icon:
        cmd.extend(["--icon", icon])

    if width:
        cmd.extend(["--width", str(width)])

    if height:
        cmd.extend(["--height", str(height)])

    if min_width:
        cmd.extend(["--min-width", str(min_width)])

    if min_height:
        cmd.extend(["--min-height", str(min_height)])

    if zoom:
        if not (50 <= zoom <= 200):
            raise ValueError("zoom 参数必须在 50-200 之间")
        cmd.extend(["--zoom", str(zoom)])

    # 添加其他高级选项
    if options:
        option_map = {
            "hide-title-bar": "hide-title-bar",
            "fullscreen": "fullscreen",
            "maximize": "maximize",
            "always-on-top": "always-on-top",
            "debug": "debug",
            "multi-instance": "multi-instance",
            "ignore-certificate-errors": "ignore-certificate-errors",
            "new-window": "new-window",
            "dark-mode": "dark-mode",
            "disabled-web-shortcuts": "disabled-web-shortcuts",
            "force-internal-navigation": "force-internal-navigation",
        }

        for key, value in options.items():
            if key in option_map:
                if value is True:
                    cmd.append(f"--{option_map[key]}")
                elif isinstance(value, str) and value:
                    cmd.extend([f"--{option_map[key]}", value])

        # 特殊处理 inject 参数（支持多个文件）
        if "inject" in options and options["inject"]:
            inject_files = options["inject"]
            if isinstance(inject_files, str):
                # 单个文件或逗号分隔的多个文件
                cmd.extend(["--inject", inject_files])
            elif isinstance(inject_files, list):
                for file in inject_files:
                    cmd.extend(["--inject", file])

        # 特殊处理 activation-shortcut
        if "activation-shortcut" in options and options["activation-shortcut"]:
            cmd.extend(["--activation-shortcut", options["activation-shortcut"]])

        # 特殊处理 app-version
        if "app-version" in options and options["app-version"]:
            cmd.extend(["--app-version", options["app-version"]])

        # 特殊处理 installer-language
        if "installer-language" in options and options["installer-language"]:
            cmd.extend(["--installer-language", options["installer-language"]])

        # 特殊处理 use-local-file
        if "use-local-file" in options and options["use-local-file"]:
            cmd.append("--use-local-file")

        # 特殊处理 multi-arch
        if "multi-arch" in options and options["multi-arch"]:
            cmd.append("--multi-arch")

        # 特殊处理 proxy-url
        if "proxy-url" in options and options["proxy-url"]:
            cmd.extend(["--proxy-url", options["proxy-url"]])

        # 特殊处理 targets
        if "targets" in options and options["targets"]:
            cmd.extend(["--targets", options["targets"]])

    print("=" * 60)
    print("🚀 开始打包应用")
    print("=" * 60)
    print(f"📍 URL: {url}")
    print(f"📝 命令: {' '.join(cmd)}")
    print("=" * 60)

    # 执行命令
    try:
        # 使用当前工作目录作为输出目录
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )

        # 输出日志
        if result.stdout:
            print(result.stdout)

        # 查找生成的文件
        output_files = []
        cwd = os.getcwd()

        # 根据平台查找生成的文件
        if sys.platform == "darwin":
            # macOS: 查找 .dmg 或 .app
            for file in os.listdir(cwd):
                if file.endswith(".dmg") or (name and file.startswith(name)):
                    output_files.append(os.path.join(cwd, file))
        elif sys.platform == "win32":
            # Windows: 查找 .msi 或 .exe
            for file in os.listdir(cwd):
                if file.endswith(".msi") or file.endswith(".exe") or (name and file.startswith(name)):
                    output_files.append(os.path.join(cwd, file))
        else:
            # Linux: 查找 .deb, .AppImage
            for file in os.listdir(cwd):
                if file.endswith(".deb") or file.endswith(".AppImage") or (name and file.startswith(name)):
                    output_files.append(os.path.join(cwd, file))

        print("=" * 60)
        print("✅ 打包成功！")
        print("=" * 60)

        if output_files:
            print("📦 生成的文件：")
            for file in output_files:
                file_size = os.path.getsize(file) / (1024 * 1024)  # MB
                print(f"   - {file} ({file_size:.2f} MB)")
        else:
            print("⚠️  未找到生成的文件，请检查当前工作目录")

        print("=" * 60)

        return output_files[0] if output_files else ""

    except subprocess.CalledProcessError as e:
        print("=" * 60)
        print("❌ 打包失败")
        print("=" * 60)
        print(f"错误码: {e.returncode}")
        print(f"\n标准输出:\n{e.stdout}")
        print(f"\n错误输出:\n{e.stderr}")
        print("=" * 60)

        # 提供解决建议
        print("\n💡 可能的解决方案：")
        print("1. 检查网络连接（需要下载依赖）")
        print("2. 验证 Node.js 和 Rust 版本")
        print("3. 使用 --debug 参数查看详细日志")
        print("4. 检查 URL 是否可访问")

        raise RuntimeError(f"打包失败: {e.stderr}") from e

    except Exception as e:
        print(f"❌ 执行失败: {str(e)}")
        raise RuntimeError(f"执行失败: {str(e)}") from e


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description="将网页打包成桌面应用")
    parser.add_argument("url", help="网页 URL（必需）")
    parser.add_argument("--name", help="应用名称")
    parser.add_argument("--icon", help="图标路径")
    parser.add_argument("--width", type=int, help="窗口宽度")
    parser.add_argument("--height", type=int, help="窗口高度")
    parser.add_argument("--debug", action="store_true", help="启用调试模式")

    args = parser.parse_args()

    try:
        options = {}
        if args.debug:
            options["debug"] = True

        build_app(
            url=args.url,
            name=args.name,
            icon=args.icon,
            width=args.width,
            height=args.height,
            options=options
        )

    except Exception as e:
        print(f"\n❌ 错误: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
