#!/usr/bin/env python3
"""
检查并安装 pake-cli 工具
"""

import subprocess
import sys


def check_node_version():
    """检查 Node.js 版本"""
    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        version_str = result.stdout.strip().lstrip('v')
        major_version = int(version_str.split('.')[0])

        if major_version < 18:
            print(f"❌ Node.js 版本过低（当前：{version_str}，要求：≥ 18.0.0）")
            return False

        print(f"✅ Node.js 版本检查通过：{version_str}")
        return True

    except FileNotFoundError:
        print("❌ 未找到 Node.js，请先安装 Node.js ≥ 18.0.0")
        return False
    except Exception as e:
        print(f"❌ Node.js 版本检查失败：{str(e)}")
        return False


def check_pake_installed():
    """检查 pake-cli 是否已安装"""
    try:
        result = subprocess.run(
            ["pake", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        version = result.stdout.strip() or result.stderr.strip()
        print(f"✅ pake-cli 已安装：{version}")
        return True, version

    except FileNotFoundError:
        print("⚠️  pake-cli 未安装")
        return False, None
    except subprocess.CalledProcessError:
        # pake 命令存在但 --version 参数可能不被支持
        print("✅ pake-cli 已安装（版本信息不可用）")
        return True, "unknown"
    except Exception as e:
        print(f"⚠️  pake-cli 检查失败：{str(e)}")
        return False, None


def install_pake():
    """安装 pake-cli"""
    print("\n📦 开始安装 pake-cli...")

    # 优先使用 pnpm
    for package_manager in ["pnpm", "npm"]:
        try:
            print(f"🔧 使用 {package_manager} 安装...")
            result = subprocess.run(
                [package_manager, "install", "-g", "pake-cli"],
                capture_output=True,
                text=True,
                check=True
            )
            print("✅ pake-cli 安装成功")
            return True

        except FileNotFoundError:
            print(f"⚠️  {package_manager} 未找到，尝试下一个包管理器...")
            continue
        except subprocess.CalledProcessError as e:
            print(f"❌ 使用 {package_manager} 安装失败：")
            print(f"   stdout: {e.stdout}")
            print(f"   stderr: {e.stderr}")
            continue

    print("\n❌ 所有安装方式均失败")
    print("请手动安装：")
    print("  npm install -g pake-cli")
    print("  或")
    print("  pnpm install -g pake-cli")
    return False


def main():
    """主函数"""
    print("=" * 50)
    print("Web-to-App 环境检查工具")
    print("=" * 50)

    # 检查 Node.js
    print("\n[1/2] 检查 Node.js 环境...")
    if not check_node_version():
        sys.exit(1)

    # 检查/安装 pake-cli
    print("\n[2/2] 检查 pake-cli...")
    installed, version = check_pake_installed()

    if not installed:
        if not install_pake():
            sys.exit(1)

    print("\n" + "=" * 50)
    print("✅ 环境检查完成，可以开始打包应用")
    print("=" * 50)


if __name__ == "__main__":
    main()
