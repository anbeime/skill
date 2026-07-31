#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skill Local Cache CLI - 通用的 Skill 本地缓存管理工具

提供公域/私域数据隔离、认证Token管理、JSON嵌套操作等能力。
通过环境变量或自动探测识别工作空间。

目录结构: {workspace}/skills_local_cache/
  .shared/    - 公域数据（跨Skill共享，如 mt_auth_tokens.json）
  .metadata/  - 系统元数据
  {skill}/    - 私域数据（data/ cache/ config/ logs/）

详细规范见 SKILL.md。
"""

import os
import re
import sys
import json
import argparse
import shutil
from pathlib import Path
from typing import Optional, Any, Dict, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

# fcntl 仅 Unix 可用，Windows 下跳过文件锁
try:
    import fcntl
    _HAS_FCNTL = True
except ImportError:
    _HAS_FCNTL = False


@dataclass
class CacheConfig:
    """缓存配置"""
    workspace: Path
    cache_dir_name: str = "skills_local_cache"

    @property
    def cache_root(self) -> Path:
        return self.workspace / self.cache_dir_name


class WorkspaceDetector:
    """工作空间探测器 - 自动识别 Agent 工作空间"""

    # 环境变量优先级（从高到低）
    ENV_VARS = [
        "SKILL_CACHE_WORKSPACE",  # 最高优先级：用户显式指定
        "AGENT_WORKSPACE",         # 通用 Agent 工作空间
        "CLAUDE_WORKSPACE",        # Claude Code 工作空间
        "XIAOMEI_WORKSPACE",       # 小美工作空间
    ]

    # 工作空间标记文件（用于向上探测）
    WORKSPACE_MARKERS = [
        ".git",                     # Git 仓库
        "CLAUDE.md",              # Claude Code 标记
        "AGENTS.md",              # Agent 配置
        ".xiaomei-workspace",      # 小美标记（兼容性）
        ".claude",                 # Claude 配置目录
    ]

    # 已知工作空间路径（按优先级排序）
    KNOWN_WORKSPACES = [
        Path.home() / ".xiaomei-workspace",    # 小美搭档默认
        Path.home() / ".openclaw" / "workspace",  # OpenClaw 沙箱默认
    ]

    @classmethod
    def detect(cls, start_path: Optional[Path] = None) -> Path:
        """
        自动检测工作空间路径

        策略：
        1. 检查环境变量（最高优先级）
        2. 检查已知工作空间路径是否存在
        3. 从当前目录向上探测标记文件
        4. 创建默认路径 ~/.xiaomei-workspace
        """
        # 1. 环境变量检查
        for env_var in cls.ENV_VARS:
            if path := os.getenv(env_var):
                workspace = Path(path).expanduser().resolve()
                if workspace.exists():
                    return workspace
                workspace.mkdir(parents=True, exist_ok=True)
                return workspace

        # 2. 已知工作空间路径检查
        for known_path in cls.KNOWN_WORKSPACES:
            if known_path.exists():
                return known_path

        # 3. 向上探测标记文件
        if start_path is None:
            start_path = Path.cwd()

        current = start_path.resolve()
        while current != current.parent:
            for marker in cls.WORKSPACE_MARKERS:
                if (current / marker).exists():
                    return current
            current = current.parent

        # 4. 默认路径
        default = cls.KNOWN_WORKSPACES[0]  # ~/.xiaomei-workspace
        default.mkdir(parents=True, exist_ok=True)
        return default


class SkillCacheManager:
    """Skill 缓存管理器"""

    # 标准子目录类型
    SUBDIR_TYPES = {
        "data": "持久化业务数据",
        "cache": "临时缓存（可清理）",
        "config": "配置文件",
        "logs": "操作日志",
    }

    def __init__(self, config: Optional[CacheConfig] = None):
        if config is None:
            workspace = WorkspaceDetector.detect()
            config = CacheConfig(workspace=workspace)
        self.config = config
        self._ensure_structure()

    def _ensure_structure(self):
        """确保基础目录结构存在"""
        self.config.cache_root.mkdir(parents=True, exist_ok=True)

        # 创建元数据目录
        metadata_dir = self.config.cache_root / ".metadata"
        metadata_dir.mkdir(exist_ok=True)

        # 创建公域数据目录
        shared_dir = self.config.cache_root / ".shared"
        shared_dir.mkdir(exist_ok=True)

    def _set_secure_permissions(self, file_path: Path) -> None:
        """
        设置安全的文件权限

        跨平台兼容处理：
        - Unix/Linux/macOS: 设置 600 权限（仅所有者读写）
        - Windows: 设置隐藏属性（如果可行）
        """
        import platform

        try:
            if platform.system() in ("Linux", "Darwin"):  # Unix-like 系统
                import stat
                os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR)
            elif platform.system() == "Windows":
                # Windows 上 os.chmod 只能设置只读属性
                # 敏感文件建议存放于用户目录下
                pass
        except Exception:
            # 权限设置失败不影响主流程
            pass

    def _get_shared_file_path(self, filename: str) -> Path:
        """获取公域文件路径（跨 Skill 共享）"""
        shared_path = self.config.cache_root / ".shared"
        shared_path.mkdir(parents=True, exist_ok=True)
        return shared_path / filename

    # ==================== 公域数据管理（跨 Skill 共享）====================

    def shared_read(self, filename: str) -> Dict:
        """
        读取公域文件（跨 Skill 共享）

        Args:
            filename: 文件名
        """
        file_path = self._get_shared_file_path(filename)

        if not file_path.exists():
            return {
                "success": False,
                "error": f"公域文件不存在: {file_path}"
            }

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            return {
                "success": True,
                "content": content,
                "path": str(file_path),
                "file": filename
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def shared_write(self, filename: str, content: str) -> Dict:
        """写入公域文件（跨 Skill 共享，带文件锁保护）"""
        file_path = self._get_shared_file_path(filename)

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                if _HAS_FCNTL:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    f.write(content)
                finally:
                    if _HAS_FCNTL:
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)

            # 设置保守的文件权限（其他用户不可读）
            self._set_secure_permissions(file_path)

            return {
                "success": True,
                "path": str(file_path),
                "file": filename,
                "operation": "write"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def shared_delete(self, filename: str) -> Dict:
        """删除公域文件"""
        file_path = self._get_shared_file_path(filename)

        if not file_path.exists():
            return {
                "success": False,
                "error": f"公域文件不存在: {file_path}"
            }

        try:
            file_path.unlink()
            return {
                "success": True,
                "path": str(file_path),
                "file": filename
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def shared_list(self) -> Dict:
        """列出所有公域文件"""
        shared_path = self.config.cache_root / ".shared"

        if not shared_path.exists():
            return {"success": True, "files": []}

        try:
            files = [
                {
                    "name": f.name,
                    "size": f.stat().st_size,
                    "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
                }
                for f in shared_path.iterdir() if f.is_file()
            ]

            return {"success": True, "files": files}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==================== 认证 Token 管理（公域）====================

    def auth_get(self, skill_name: str, key: Optional[str] = None) -> Dict:
        """
        获取认证 Token

        结构: mt_auth_tokens.json
        {
          "skill_name": {
            "user_token": "...",
            "device_token": "...",
            ...
          }
        }
        """
        result = self.shared_read("mt_auth_tokens.json")

        if not result["success"]:
            if "不存在" in result.get("error", ""):
                return {
                    "success": True,
                    "skill": skill_name,
                    "data": {},
                    "found": False
                }
            return result

        try:
            data = json.loads(result["content"])
            skill_data = data.get(skill_name, {})

            if key:
                return {
                    "success": True,
                    "skill": skill_name,
                    "key": key,
                    "value": skill_data.get(key),
                    "found": key in skill_data
                }

            return {
                "success": True,
                "skill": skill_name,
                "data": skill_data,
                "found": bool(skill_data)
            }
        except json.JSONDecodeError as e:
            return {"success": False, "error": f"JSON解析错误: {e}"}

    def auth_set(self, skill_name: str, auth_data: Dict) -> Dict:
        """
        设置认证 Token

        auth_data: 任意键值对，如 user_token, device_token, expires_at 等
        """
        # 读取现有数据
        result = self.shared_read("mt_auth_tokens.json")

        if result["success"]:
            try:
                data = json.loads(result["content"])
            except json.JSONDecodeError:
                data = {}
        else:
            data = {}

        # 更新或创建 Skill 的认证数据
        if skill_name not in data:
            data[skill_name] = {}

        # 合并新数据
        data[skill_name].update(auth_data)

        # 添加元信息
        data[skill_name]["_updated_at"] = datetime.now().isoformat()

        # 写回文件
        content = json.dumps(data, ensure_ascii=False, indent=2)
        return self.shared_write("mt_auth_tokens.json", content)

    def auth_delete(self, skill_name: str, key: Optional[str] = None) -> Dict:
        """
        删除认证 Token

        key 为 None 时删除整个 Skill 的认证数据
        key 指定时删除特定字段
        """
        result = self.shared_read("mt_auth_tokens.json")

        if not result["success"]:
            return result

        try:
            data = json.loads(result["content"])

            if skill_name not in data:
                return {
                    "success": False,
                    "error": f"未找到 Skill 的认证数据: {skill_name}"
                }

            if key is None:
                # 删除整个 Skill 的认证数据
                del data[skill_name]
            else:
                # 删除特定字段
                if key in data[skill_name]:
                    del data[skill_name][key]
                else:
                    return {
                        "success": False,
                        "error": f"未找到键: {key}"
                    }

            content = json.dumps(data, ensure_ascii=False, indent=2)
            return self.shared_write("mt_auth_tokens.json", content)

        except json.JSONDecodeError as e:
            return {"success": False, "error": f"JSON解析错误: {e}"}

    def auth_list(self) -> Dict:
        """列出所有已存储认证的 Skill"""
        result = self.shared_read("mt_auth_tokens.json")

        if not result["success"]:
            if "不存在" in result.get("error", ""):
                return {"success": True, "skills": []}
            return result

        try:
            data = json.loads(result["content"])
            skills = [
                {
                    "name": name,
                    "keys": list(info.keys()),
                    "updated_at": info.get("_updated_at", "unknown")
                }
                for name, info in data.items()
                if not name.startswith("_")
            ]

            return {"success": True, "skills": skills}
        except json.JSONDecodeError as e:
            return {"success": False, "error": f"JSON解析错误: {e}"}

    def _get_skill_path(self, skill_name: str, subdir: str = "data") -> Path:
        """获取 Skill 目录路径"""
        if subdir not in self.SUBDIR_TYPES:
            raise ValueError(f"未知子目录类型: {subdir}。可用: {list(self.SUBDIR_TYPES.keys())}")

        skill_path = self.config.cache_root / skill_name / subdir
        skill_path.mkdir(parents=True, exist_ok=True)
        return skill_path

    def _get_file_path(self, skill_name: str, filename: str, subdir: str = "data") -> Path:
        """获取文件完整路径"""
        return self._get_skill_path(skill_name, subdir) / filename

    # ==================== 基础 CRUD ====================

    def write(self, skill_name: str, filename: str, content: str,
              subdir: str = "data", append: bool = False) -> Dict:
        """写入文件（带文件锁保护）"""
        file_path = self._get_file_path(skill_name, filename, subdir)
        mode = "a" if append else "w"

        try:
            with open(file_path, mode, encoding="utf-8") as f:
                if _HAS_FCNTL:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    f.write(content)
                finally:
                    if _HAS_FCNTL:
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)

            # config 目录下的文件设置安全权限
            if subdir == "config":
                self._set_secure_permissions(file_path)

            return {
                "success": True,
                "path": str(file_path),
                "skill": skill_name,
                "file": filename,
                "operation": "append" if append else "write"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def read(self, skill_name: str, filename: str, subdir: str = "data") -> Dict:
        """读取文件"""
        file_path = self._get_file_path(skill_name, filename, subdir)

        if not file_path.exists():
            return {
                "success": False,
                "error": f"文件不存在: {file_path}"
            }

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            return {
                "success": True,
                "content": content,
                "path": str(file_path),
                "skill": skill_name,
                "file": filename
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete(self, skill_name: str, filename: str, subdir: str = "data") -> Dict:
        """删除文件"""
        file_path = self._get_file_path(skill_name, filename, subdir)

        if not file_path.exists():
            return {
                "success": False,
                "error": f"文件不存在: {file_path}"
            }

        try:
            file_path.unlink()

            return {
                "success": True,
                "path": str(file_path),
                "skill": skill_name,
                "file": filename
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_files(self, skill_name: str, subdir: Optional[str] = None) -> Dict:
        """列出文件"""
        if subdir:
            skill_path = self._get_skill_path(skill_name, subdir)
            paths = [skill_path]
        else:
            # 列出所有子目录
            skill_root = self.config.cache_root / skill_name
            paths = [skill_root / d for d in self.SUBDIR_TYPES.keys()]

        result = {}
        for path in paths:
            if path.exists():
                key = path.name
                result[key] = [
                    {
                        "name": f.name,
                        "size": f.stat().st_size,
                        "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
                    }
                    for f in path.iterdir() if f.is_file()
                ]

        return {
            "success": True,
            "skill": skill_name,
            "files": result
        }

    def list_skills(self) -> Dict:
        """列出所有 Skill"""
        if not self.config.cache_root.exists():
            return {"success": True, "skills": []}

        skills = [
            d.name for d in self.config.cache_root.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        ]

        return {"success": True, "skills": skills}

    # ==================== JSON 专用操作 ====================

    def json_get(self, skill_name: str, filename: str, key_path: str,
                 subdir: str = "data") -> Dict:
        """
        获取 JSON 中的值

        key_path 支持:
        - 简单键: "name"
        - 嵌套键: "user.profile.name"
        - 数组索引: "users[0].name" 或 "users.0.name"
        """
        result = self.read(skill_name, filename, subdir)
        if not result["success"]:
            return result

        try:
            data = json.loads(result["content"])
            value = self._get_nested_value(data, key_path)

            return {
                "success": True,
                "value": value,
                "key": key_path,
                "skill": skill_name,
                "file": filename
            }
        except json.JSONDecodeError as e:
            return {"success": False, "error": f"JSON解析错误: {e}"}
        except KeyError as e:
            return {"success": False, "error": f"键不存在: {e}"}

    def json_set(self, skill_name: str, filename: str, key_path: str,
                 value: Any, subdir: str = "data") -> Dict:
        """设置 JSON 中的值"""
        result = self.read(skill_name, filename, subdir)

        if result["success"]:
            try:
                data = json.loads(result["content"])
            except json.JSONDecodeError:
                data = {}
        else:
            data = {}

        try:
            self._set_nested_value(data, key_path, value)

            content = json.dumps(data, ensure_ascii=False, indent=2)
            return self.write(skill_name, filename, content, subdir)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def json_delete(self, skill_name: str, filename: str, key_path: str,
                    subdir: str = "data") -> Dict:
        """删除 JSON 中的键"""
        result = self.read(skill_name, filename, subdir)
        if not result["success"]:
            return result

        try:
            data = json.loads(result["content"])
            self._delete_nested_key(data, key_path)

            content = json.dumps(data, ensure_ascii=False, indent=2)
            return self.write(skill_name, filename, content, subdir)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def json_append(self, skill_name: str, filename: str, key_path: str,
                    value: Any, subdir: str = "data") -> Dict:
        """向数组追加元素"""
        result = self.json_get(skill_name, filename, key_path, subdir)

        if result["success"] and isinstance(result.get("value"), list):
            arr = result["value"]
            arr.append(value)
            return self.json_set(skill_name, filename, key_path, arr, subdir)
        elif not result["success"]:
            # 键不存在，创建新数组
            return self.json_set(skill_name, filename, key_path, [value], subdir)
        else:
            return {"success": False, "error": f"目标不是数组: {key_path}"}

    # ==================== 行操作 ====================

    def line_get(self, skill_name: str, filename: str, line_num: int,
                 subdir: str = "data") -> Dict:
        """获取指定行"""
        result = self.read(skill_name, filename, subdir)
        if not result["success"]:
            return result

        lines = result["content"].splitlines()
        if line_num < 1 or line_num > len(lines):
            return {"success": False, "error": f"行号越界: {line_num} (总行数: {len(lines)})"}

        return {
            "success": True,
            "line": lines[line_num - 1],
            "line_num": line_num,
            "total_lines": len(lines)
        }

    def line_append(self, skill_name: str, filename: str, line: str,
                    subdir: str = "data") -> Dict:
        """追加一行"""
        file_path = self._get_file_path(skill_name, filename, subdir)

        # 确保文件以换行结尾
        result = self.read(skill_name, filename, subdir)
        if result["success"]:
            content = result["content"]
            if content and not content.endswith("\n"):
                line = "\n" + line
        else:
            line = line + "\n"

        return self.write(skill_name, filename, line + "\n", subdir, append=True)

    def line_replace(self, skill_name: str, filename: str, line_num: int,
                     content: str, subdir: str = "data") -> Dict:
        """替换指定行"""
        result = self.read(skill_name, filename, subdir)
        if not result["success"]:
            return result

        lines = result["content"].splitlines()
        if line_num < 1 or line_num > len(lines):
            return {"success": False, "error": f"行号越界: {line_num}"}

        lines[line_num - 1] = content
        new_content = "\n".join(lines) + "\n"

        return self.write(skill_name, filename, new_content, subdir)

    # ==================== 管理操作 ====================

    def clean(self, skill_name: Optional[str] = None, subdir: str = "cache",
              older_than_days: int = 7) -> Dict:
        """清理过期缓存"""
        cutoff = datetime.now() - timedelta(days=older_than_days)
        deleted = []
        errors = []

        if skill_name:
            paths = [self._get_skill_path(skill_name, subdir)]
        else:
            # 清理所有 Skill 的 cache
            paths = [
                self.config.cache_root / d / subdir
                for d in self.list_skills().get("skills", [])
            ]

        for path in paths:
            if not path.exists():
                continue

            for f in path.iterdir():
                if not f.is_file():
                    continue

                mtime = datetime.fromtimestamp(f.stat().st_mtime)
                if mtime < cutoff:
                    try:
                        f.unlink()
                        deleted.append(str(f))
                    except Exception as e:
                        errors.append({"file": str(f), "error": str(e)})

        return {
            "success": True,
            "deleted_count": len(deleted),
            "deleted": deleted,
            "errors": errors
        }

    def info(self, skill_name: Optional[str] = None) -> Dict:
        """获取缓存信息"""
        info_data = {
            "workspace": str(self.config.workspace),
            "cache_root": str(self.config.cache_root),
            "timestamp": datetime.now().isoformat()
        }

        if skill_name:
            skill_path = self.config.cache_root / skill_name
            if not skill_path.exists():
                return {"success": False, "error": f"Skill 不存在: {skill_name}"}

            sizes = {}
            for subdir in self.SUBDIR_TYPES.keys():
                subdir_path = skill_path / subdir
                if subdir_path.exists():
                    size = sum(f.stat().st_size for f in subdir_path.rglob("*") if f.is_file())
                    sizes[subdir] = {
                        "size_bytes": size,
                        "size_human": self._human_readable_size(size),
                        "file_count": len(list(subdir_path.rglob("*")))
                    }

            info_data["skill"] = skill_name
            info_data["subdirs"] = sizes
        else:
            skills = self.list_skills().get("skills", [])
            info_data["total_skills"] = len(skills)
            info_data["skills"] = skills

        return {"success": True, "info": info_data}

    # ==================== 辅助方法 ====================

    def _get_nested_value(self, data: Any, key_path: str) -> Any:
        """获取嵌套值"""
        # 处理数组索引格式: users[0].name
        key_path = re.sub(r'\[(\d+)\]', r'.\1', key_path)

        keys = key_path.split(".")
        current = data

        for key in keys:
            if key.isdigit():
                # 数组索引
                idx = int(key)
                if not isinstance(current, list):
                    raise KeyError(f"期待数组但得到 {type(current)}")
                if idx >= len(current):
                    raise KeyError(f"数组索引越界: {idx}")
                current = current[idx]
            elif isinstance(current, dict):
                if key not in current:
                    raise KeyError(f"键不存在: {key}")
                current = current[key]
            else:
                raise KeyError(f"无法访问键 '{key}'，当前类型: {type(current)}")

        return current

    def _set_nested_value(self, data: Dict, key_path: str, value: Any):
        """设置嵌套值"""
        # 统一处理数组索引格式: users[0].name -> users.0.name
        key_path = re.sub(r'\[(\d+)\]', r'.\1', key_path)

        keys = key_path.split(".")
        current = data

        # 遍历除最后一个 key 外的所有 key（用于导航到目标位置）
        for i, key in enumerate(keys[:-1]):
            next_key = keys[i + 1]

            # 如果当前是 list 且 key 是数字索引
            if isinstance(current, list) and key.isdigit():
                idx = int(key)
                # 扩展列表容量
                while len(current) <= idx:
                    current.append(None)
                # 如果该位置为 None，根据下一个 key 类型创建合适的数据结构
                if current[idx] is None:
                    if next_key.isdigit():
                        current[idx] = []
                    else:
                        current[idx] = {}
                current = current[idx]

            # 如果当前是 dict，确保 key 存在并进入
            elif isinstance(current, dict):
                if key not in current:
                    # 根据下一个 key 判断是创建 list 还是 dict
                    if next_key.isdigit():
                        current[key] = []
                    else:
                        current[key] = {}
                current = current[key]
            else:
                raise TypeError(f"无法在 {type(current)} 上设置键 '{key}'")

        # 设置最终值（最后一个 key）
        final_key = keys[-1]
        if isinstance(current, list) and final_key.isdigit():
            # 最终目标是列表索引
            idx = int(final_key)
            while len(current) <= idx:
                current.append(None)
            current[idx] = value
        elif isinstance(current, dict):
            current[final_key] = value
        else:
            raise TypeError(f"无法在 {type(current)} 上设置最终键 '{final_key}'")

    def _delete_nested_key(self, data: Dict, key_path: str):
        """删除嵌套键"""
        key_path = re.sub(r'\[(\d+)\]', r'.\1', key_path)

        keys = key_path.split(".")
        current = data

        for key in keys[:-1]:
            if key.isdigit():
                current = current[int(key)]
            else:
                current = current[key]

        final_key = keys[-1]
        if final_key.isdigit():
            del current[int(final_key)]
        else:
            del current[final_key]

    def _human_readable_size(self, size_bytes: int) -> str:
        """转换为人类可读大小"""
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.2f} TB"


# ==================== CLI 接口 ====================

def main():
    parser = argparse.ArgumentParser(
        description="Skill Local Cache CLI - 通用的 Skill 本地缓存管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
【私域数据】（Skill 隔离）
  # 写入私域文件
  skill-cache write my-skill config.json --content '{"key": "value"}' --type config

  # 读取私域文件
  skill-cache read my-skill config.json

  # JSON 嵌套操作
  skill-cache json-get my-skill data.json --key database.host
  skill-cache json-set my-skill data.json --key users[0].name --value "张三"
  skill-cache json-append my-skill data.json --key items --value '{"id": 1}'

  # 清理过期缓存
  skill-cache clean my-skill --type cache --older-than 7

【公域数据】（跨 Skill 共享）
  # 认证 Token 管理
  skill-cache auth set meituan-coupon-workbuddy --data '{"user_token":"xxx","device_token":"yyy"}'
  skill-cache auth get meituan-coupon-workbuddy
  skill-cache auth get meituan-coupon-workbuddy --key user_token
  skill-cache auth list
  skill-cache auth delete meituan-coupon-workbuddy

  # 通用公域文件
  skill-cache shared write global_config.json --content '{"api_endpoint":"https://..."}'
  skill-cache shared read global_config.json
  skill-cache shared list

【目录结构】
  skills_local_cache/
  ├── .metadata/              # 元数据
  ├── .shared/                # 公域数据
  │   ├── mt_auth_tokens.json    # 认证 Token（所有 Skill 共享）
  │   └── global_config.json  # 全局配置
  └── {skill_name}/           # 私域数据（Skill 隔离）
      ├── data/
      ├── cache/
      ├── config/
      └── logs/

环境变量:
  SKILL_CACHE_WORKSPACE  - 显式指定工作空间路径
  AGENT_WORKSPACE        - 通用 Agent 工作空间
  CLAUDE_WORKSPACE       - Claude Code 工作空间
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # write 命令
    write_parser = subparsers.add_parser("write", help="写入文件")
    write_parser.add_argument("skill", help="Skill 名称")
    write_parser.add_argument("file", help="文件名")
    write_parser.add_argument("--content", "-c", required=True, help="文件内容")
    write_parser.add_argument("--type", "-t", default="data",
                              choices=["data", "cache", "config", "logs"],
                              help="子目录类型")
    write_parser.add_argument("--append", "-a", action="store_true", help="追加模式")

    # read 命令
    read_parser = subparsers.add_parser("read", help="读取文件")
    read_parser.add_argument("skill", help="Skill 名称")
    read_parser.add_argument("file", help="文件名")
    read_parser.add_argument("--type", "-t", default="data",
                              choices=["data", "cache", "config", "logs"])

    # delete 命令
    delete_parser = subparsers.add_parser("delete", help="删除文件")
    delete_parser.add_argument("skill", help="Skill 名称")
    delete_parser.add_argument("file", help="文件名")
    delete_parser.add_argument("--type", "-t", default="data",
                              choices=["data", "cache", "config", "logs"])

    # list 命令
    list_parser = subparsers.add_parser("list", help="列出文件")
    list_parser.add_argument("skill", nargs="?", help="Skill 名称（可选）")
    list_parser.add_argument("--type", "-t", choices=["data", "cache", "config", "logs"],
                            help="子目录类型")

    # json-get 命令
    json_get_parser = subparsers.add_parser("json-get", help="获取 JSON 值")
    json_get_parser.add_argument("skill", help="Skill 名称")
    json_get_parser.add_argument("file", help="文件名")
    json_get_parser.add_argument("--key", "-k", required=True, help="键路径（如 user.name 或 users[0].id）")
    json_get_parser.add_argument("--type", "-t", default="data",
                                  choices=["data", "cache", "config", "logs"])

    # json-set 命令
    json_set_parser = subparsers.add_parser("json-set", help="设置 JSON 值")
    json_set_parser.add_argument("skill", help="Skill 名称")
    json_set_parser.add_argument("file", help="文件名")
    json_set_parser.add_argument("--key", "-k", required=True, help="键路径")
    json_set_parser.add_argument("--value", "-v", required=True, help="值（JSON 格式）")
    json_set_parser.add_argument("--type", "-t", default="data",
                                  choices=["data", "cache", "config", "logs"])

    # json-delete 命令
    json_del_parser = subparsers.add_parser("json-delete", help="删除 JSON 键")
    json_del_parser.add_argument("skill", help="Skill 名称")
    json_del_parser.add_argument("file", help="文件名")
    json_del_parser.add_argument("--key", "-k", required=True, help="键路径")
    json_del_parser.add_argument("--type", "-t", default="data",
                                  choices=["data", "cache", "config", "logs"])

    # json-append 命令
    json_append_parser = subparsers.add_parser("json-append", help="追加到 JSON 数组")
    json_append_parser.add_argument("skill", help="Skill 名称")
    json_append_parser.add_argument("file", help="文件名")
    json_append_parser.add_argument("--key", "-k", required=True, help="数组键路径")
    json_append_parser.add_argument("--value", "-v", required=True, help="要追加的值（JSON 格式）")
    json_append_parser.add_argument("--type", "-t", default="data",
                                     choices=["data", "cache", "config", "logs"])

    # line 命令
    line_parser = subparsers.add_parser("line", help="行操作")
    line_subparsers = line_parser.add_subparsers(dest="line_cmd")

    line_get = line_subparsers.add_parser("get", help="获取指定行")
    line_get.add_argument("skill", help="Skill 名称")
    line_get.add_argument("file", help="文件名")
    line_get.add_argument("--num", "-n", type=int, required=True, help="行号")
    line_get.add_argument("--type", "-t", default="data",
                          choices=["data", "cache", "config", "logs"])

    line_append = line_subparsers.add_parser("append", help="追加行")
    line_append.add_argument("skill", help="Skill 名称")
    line_append.add_argument("file", help="文件名")
    line_append.add_argument("--content", "-c", required=True, help="行内容")
    line_append.add_argument("--type", "-t", default="data",
                             choices=["data", "cache", "config", "logs"])

    line_replace = line_subparsers.add_parser("replace", help="替换行")
    line_replace.add_argument("skill", help="Skill 名称")
    line_replace.add_argument("file", help="文件名")
    line_replace.add_argument("--num", "-n", type=int, required=True, help="行号")
    line_replace.add_argument("--content", "-c", required=True, help="新内容")
    line_replace.add_argument("--type", "-t", default="data",
                              choices=["data", "cache", "config", "logs"])

    # clean 命令
    clean_parser = subparsers.add_parser("clean", help="清理缓存")
    clean_parser.add_argument("skill", nargs="?", help="Skill 名称（可选，不提供则清理所有）")
    clean_parser.add_argument("--type", "-t", default="cache",
                              choices=["data", "cache", "config", "logs"])
    clean_parser.add_argument("--older-than", "-d", type=int, default=7,
                              help="清理超过 N 天的文件")

    # info 命令
    info_parser = subparsers.add_parser("info", help="查看信息")
    info_parser.add_argument("skill", nargs="?", help="Skill 名称（可选）")

    # ==================== 公域数据命令 ====================

    # shared 命令组
    shared_parser = subparsers.add_parser("shared", help="公域数据管理（跨 Skill 共享）")
    shared_subparsers = shared_parser.add_subparsers(dest="shared_cmd")

    # shared read
    shared_read = shared_subparsers.add_parser("read", help="读取公域文件")
    shared_read.add_argument("file", help="文件名")

    # shared write
    shared_write = shared_subparsers.add_parser("write", help="写入公域文件")
    shared_write.add_argument("file", help="文件名")
    shared_write.add_argument("--content", "-c", required=True, help="文件内容")

    # shared delete
    shared_delete = shared_subparsers.add_parser("delete", help="删除公域文件")
    shared_delete.add_argument("file", help="文件名")

    # shared list
    shared_subparsers.add_parser("list", help="列出公域文件")

    # auth 命令组（专用于认证 Token 管理）
    auth_parser = subparsers.add_parser("auth", help="认证 Token 管理（公域）")
    auth_subparsers = auth_parser.add_subparsers(dest="auth_cmd")

    # auth get
    auth_get = auth_subparsers.add_parser("get", help="获取认证信息")
    auth_get.add_argument("skill", help="Skill 名称")
    auth_get.add_argument("--key", "-k", help="特定键（可选）")

    # auth set
    auth_set = auth_subparsers.add_parser("set", help="设置认证信息")
    auth_set.add_argument("skill", help="Skill 名称")
    auth_set.add_argument("--data", "-d", required=True, help="JSON 格式的认证数据")

    # auth delete
    auth_delete = auth_subparsers.add_parser("delete", help="删除认证信息")
    auth_delete.add_argument("skill", help="Skill 名称")
    auth_delete.add_argument("--key", "-k", help="特定键（可选，不指定则删除整个 Skill 认证）")

    # auth list
    auth_subparsers.add_parser("list", help="列出所有认证的 Skill")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # 初始化管理器
    manager = SkillCacheManager()

    # 执行命令
    if args.command == "write":
        result = manager.write(
            args.skill, args.file, args.content,
            args.type, args.append
        )

    elif args.command == "read":
        result = manager.read(args.skill, args.file, args.type)
        if result["success"]:
            print(result["content"])
            return

    elif args.command == "delete":
        result = manager.delete(args.skill, args.file, args.type)

    elif args.command == "list":
        if args.skill:
            result = manager.list_files(args.skill, args.type)
        else:
            result = manager.list_skills()

    elif args.command == "json-get":
        result = manager.json_get(args.skill, args.file, args.key, args.type)
        if result["success"]:
            print(json.dumps(result["value"], ensure_ascii=False, indent=2))
            return

    elif args.command == "json-set":
        import json as json_module
        try:
            value = json_module.loads(args.value)
        except json_module.JSONDecodeError:
            value = args.value  # 作为字符串
        result = manager.json_set(args.skill, args.file, args.key, value, args.type)

    elif args.command == "json-delete":
        result = manager.json_delete(args.skill, args.file, args.key, args.type)

    elif args.command == "json-append":
        import json as json_module
        try:
            value = json_module.loads(args.value)
        except json_module.JSONDecodeError:
            value = args.value
        result = manager.json_append(args.skill, args.file, args.key, value, args.type)

    elif args.command == "line":
        if args.line_cmd == "get":
            result = manager.line_get(args.skill, args.file, args.num, args.type)
            if result["success"]:
                print(result["line"])
                return
        elif args.line_cmd == "append":
            result = manager.line_append(args.skill, args.file, args.content, args.type)
        elif args.line_cmd == "replace":
            result = manager.line_replace(args.skill, args.file, args.num, args.content, args.type)
        else:
            line_parser.print_help()
            return

    elif args.command == "clean":
        result = manager.clean(args.skill, args.type, args.older_than)

    elif args.command == "info":
        result = manager.info(args.skill)

    # ==================== 公域数据命令处理 ====================

    elif args.command == "shared":
        if args.shared_cmd == "read":
            result = manager.shared_read(args.file)
            if result["success"]:
                print(result["content"])
                return
        elif args.shared_cmd == "write":
            result = manager.shared_write(args.file, args.content)
        elif args.shared_cmd == "delete":
            result = manager.shared_delete(args.file)
        elif args.shared_cmd == "list":
            result = manager.shared_list()
        else:
            shared_parser.print_help()
            return

    elif args.command == "auth":
        if args.auth_cmd == "get":
            result = manager.auth_get(args.skill, args.key)
            if result["success"] and "value" in result:
                print(json.dumps(result["value"], ensure_ascii=False, indent=2))
                return
            elif result["success"] and "data" in result:
                print(json.dumps(result["data"], ensure_ascii=False, indent=2))
                return
        elif args.auth_cmd == "set":
            import json as json_module
            try:
                auth_data = json_module.loads(args.data)
            except json_module.JSONDecodeError as e:
                print(json.dumps({"success": False, "error": f"JSON解析错误: {e}"}, ensure_ascii=False))
                return
            result = manager.auth_set(args.skill, auth_data)
        elif args.auth_cmd == "delete":
            result = manager.auth_delete(args.skill, args.key)
        elif args.auth_cmd == "list":
            result = manager.auth_list()
        else:
            auth_parser.print_help()
            return

    else:
        parser.print_help()
        return

    # 输出结果
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
