#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HandRaw Style Community Client - 社区账号与内容管理模块
用于打通手绘风网站 (handraw-style.com) Discourse 账号系统，
支持：账号登录/绑定、作品与提示词一键分享发布、查看和管理（编辑/删除）我的帖子。
"""

import os
import sys
import json
import uuid
import subprocess
import mimetypes
import urllib.request
import urllib.error
import urllib.parse
import http.cookiejar
from pathlib import Path

# 默认手绘风社区基准配置
DEFAULT_COMMUNITY_URL = "https://handraw-style.com"
DEFAULT_CATEGORY_ID = 4  # 默认板块: 创作与变现

# 凭据存储路径 (优先用户主目录 ~/.handraw-style/，后备客户端缓存目录)
HOME_DIR = Path.home() / ".handraw-style"
AUTH_FILE = HOME_DIR / "community_auth.json"
COOKIE_FILE = HOME_DIR / "community_cookies.txt"

if getattr(sys, "frozen", False):
    _local_app_data = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
    CLIENT_CACHE_DIR = (Path(_local_app_data) / "HandRawStyleStudio" / "cache") if _local_app_data else HOME_DIR / "cache"
else:
    CLIENT_CACHE_DIR = Path(__file__).resolve().parent.parent / "client" / "cache"
CLIENT_AUTH_FILE = CLIENT_CACHE_DIR / "community_auth.json"


def ensure_auth_dirs():
    HOME_DIR.mkdir(parents=True, exist_ok=True)
    try:
        CLIENT_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass


def load_auth_profile():
    """读取已保存的用户登录凭据"""
    for filepath in [AUTH_FILE, CLIENT_AUTH_FILE]:
        if filepath.exists():
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data and (data.get("api_key") or data.get("session_cookie") or data.get("username")):
                        return data
            except Exception:
                pass
    return None


def save_auth_profile(data):
    """保存用户登录凭据到本地文件"""
    ensure_auth_dirs()
    success = False
    for filepath in [AUTH_FILE, CLIENT_AUTH_FILE]:
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            success = True
        except Exception:
            pass
    return success


def clear_auth_profile():
    """清除登录凭据 (退出登录)"""
    for filepath in [AUTH_FILE, CLIENT_AUTH_FILE, COOKIE_FILE]:
        if filepath.exists():
            try:
                os.remove(filepath)
            except Exception:
                pass


class DiscourseClient:
    def __init__(self, base_url=DEFAULT_COMMUNITY_URL):
        self.base_url = base_url.rstrip("/")
        self.cookie_jar = http.cookiejar.LWPCookieJar()
        ensure_auth_dirs()
        if COOKIE_FILE.exists():
            try:
                self.cookie_jar.load(str(COOKIE_FILE), ignore_discard=True, ignore_expires=True)
            except Exception:
                pass
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookie_jar))
        self.auth = load_auth_profile() or {}

    def _save_cookies(self):
        try:
            self.cookie_jar.save(str(COOKIE_FILE), ignore_discard=True, ignore_expires=True)
        except Exception:
            pass

    def get_csrf_token(self):
        """获取 Discourse CSRF Token"""
        req = urllib.request.Request(
            f"{self.base_url}/session/csrf.json",
            headers={
                "User-Agent": "HandRawStudio/1.0",
                "Accept": "application/json"
            }
        )
        with self.opener.open(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("csrf", "")

    def login_with_password(self, username_or_email, password):
        """
        使用用户名/邮箱与密码登录 Discourse
        """
        csrf = self.get_csrf_token()
        payload = urllib.parse.urlencode({
            "login": username_or_email,
            "password": password
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{self.base_url}/session",
            data=payload,
            headers={
                "User-Agent": "HandRawStudio/1.0",
                "X-CSRF-Token": csrf,
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )

        with self.opener.open(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("error"):
                raise ValueError(data.get("error"))

            user_info = data.get("user") or {}
            self._save_cookies()

            profile = {
                "auth_type": "session",
                "username": user_info.get("username", username_or_email),
                "user_id": user_info.get("id"),
                "name": user_info.get("name"),
                "avatar_template": user_info.get("avatar_template"),
                "trust_level": user_info.get("trust_level"),
                "base_url": self.base_url
            }
            save_auth_profile(profile)
            self.auth = profile
            return profile

    def login_with_api_key(self, api_key, username=None):
        """
        使用 Discourse API Key 绑定登录
        """
        headers = {
            "Api-Key": api_key,
            "User-Agent": "HandRawStudio/1.0",
            "Accept": "application/json"
        }
        if username:
            try:
                # 仅 ASCII 用户名可安全放入 Api-Username 请求头
                username.encode('ascii')
                headers["Api-Username"] = username
            except UnicodeEncodeError:
                pass

        req = urllib.request.Request(f"{self.base_url}/session/current.json", headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            user_info = data.get("current_user") or {}
            real_username = user_info.get("username") or username or "user"
            profile = {
                "auth_type": "api_key",
                "api_key": api_key,
                "username": real_username,
                "user_id": user_info.get("id"),
                "name": user_info.get("name"),
                "avatar_template": user_info.get("avatar_template"),
                "trust_level": user_info.get("trust_level"),
                "base_url": self.base_url
            }
            save_auth_profile(profile)
            self.auth = profile
            return profile

    def whoami(self):
        """获取当前登录用户信息"""
        if not self.auth:
            return {"logged_in": False}

        username = self.auth.get("username")
        # 尝试在线校验最新会话状态
        headers = {"User-Agent": "HandRawStudio/1.0", "Accept": "application/json"}
        if self.auth.get("api_key"):
            headers["Api-Key"] = self.auth.get("api_key")
            try:
                username.encode('ascii')
                headers["Api-Username"] = username
            except (UnicodeEncodeError, AttributeError):
                pass
            req = urllib.request.Request(f"{self.base_url}/session/current.json", headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=8) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    u = data.get("current_user")
                    if u:
                        self.auth.update({
                            "username": u.get("username"),
                            "name": u.get("name"),
                            "avatar_template": u.get("avatar_template"),
                            "trust_level": u.get("trust_level"),
                            "user_id": u.get("id")
                        })
                        save_auth_profile(self.auth)
            except Exception:
                pass

        return {
            "logged_in": True,
            "username": self.auth.get("username"),
            "name": self.auth.get("name"),
            "user_id": self.auth.get("user_id"),
            "trust_level": self.auth.get("trust_level"),
            "avatar_url": self.get_avatar_url(self.auth.get("avatar_template")),
            "auth_type": self.auth.get("auth_type"),
            "community_url": self.base_url
        }

    def get_avatar_url(self, template, size=120):
        if not template:
            return f"{self.base_url}/images/avatar.png"
        url = template.replace("{size}", str(size))
        if not url.startswith("http"):
            url = f"{self.base_url}{url}"
        return url

    def upload_image(self, file_path_or_bytes, filename=None):
        """上传图片到 Discourse，返回 upload 对象"""
        if isinstance(file_path_or_bytes, (str, Path)):
            path = Path(file_path_or_bytes)
            if not path.exists():
                raise FileNotFoundError(f"本地图片文件不存在: {path}")
            filename = filename or path.name
            with open(path, "rb") as f:
                img_data = f.read()
        else:
            img_data = file_path_or_bytes
            filename = filename or f"handraw_{uuid.uuid4().hex[:8]}.png"

        mime_type, _ = mimetypes.guess_type(filename)
        mime_type = mime_type or "image/png"

        boundary = f"----HandRawBoundary{uuid.uuid4().hex}"
        body = bytearray()
        body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="type"\r\n\r\ncomposer\r\n'.encode('utf-8'))
        body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="synchronous"\r\n\r\ntrue\r\n'.encode('utf-8'))
        body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{filename}"\r\nContent-Type: {mime_type}\r\n\r\n'.encode('utf-8'))
        body.extend(img_data)
        body.extend(f'\r\n--{boundary}--\r\n'.encode('utf-8'))

        headers = {
            "User-Agent": "HandRawStudio/1.0",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Accept": "application/json"
        }

        # 认证头装配
        if self.auth.get("api_key"):
            headers["Api-Key"] = self.auth.get("api_key")
            username = self.auth.get("username")
            if username:
                try:
                    username.encode('ascii')
                    headers["Api-Username"] = username
                except UnicodeEncodeError:
                    pass
            req = urllib.request.Request(f"{self.base_url}/uploads.json", data=bytes(body), headers=headers)
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        else:
            csrf = self.get_csrf_token()
            headers["X-CSRF-Token"] = csrf
            req = urllib.request.Request(f"{self.base_url}/uploads.json", data=bytes(body), headers=headers)
            with self.opener.open(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))

    def list_categories(self, refresh=False):
        """获取论坛所有板块列表（带缓存与离线兜底）"""
        if hasattr(self, "_categories_cache") and self._categories_cache and not refresh:
            return self._categories_cache
        url = f"{self.base_url}/categories.json"
        headers = {"User-Agent": "HandRawStudio/1.0", "Accept": "application/json"}
        if self.auth.get("api_key"):
            headers["Api-Key"] = self.auth.get("api_key")
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                cats = data.get("category_list", {}).get("categories", [])
                result = []
                for c in cats:
                    result.append({
                        "id": c.get("id"),
                        "name": c.get("name"),
                        "slug": c.get("slug"),
                        "description": c.get("description_text", ""),
                        "topic_count": c.get("topic_count", 0),
                        "post_count": c.get("post_count", 0)
                    })
                self._categories_cache = result
                return result
        except Exception:
            fallback = [
                {"id": 4, "name": "综合大厅", "slug": "creation-monetization", "description": "社区公告、新人报到与行业资讯交流大厅"},
                {"id": 5, "name": "好用的工具", "slug": "tools", "description": "开源项目与工具分享，工作流与排错求助"},
                {"id": 6, "name": "创作交流", "slug": "creative-exchange", "description": "创作经验交流与提示词分享"},
                {"id": 7, "name": "运营与变现", "slug": "operations", "description": "起号与运营变现经验分享"},
                {"id": 8, "name": "实战作品与爆款", "slug": "showcase", "description": "晒成片、晒图文、爆款拆解点评"},
                {"id": 9, "name": "手绘skill", "slug": "handraw-skill", "description": "手绘风专项Skill交流与改进建议"}
            ]
            self._categories_cache = fallback
            return fallback

    def resolve_category(self, category_input=None):
        """智能解析板块名称、关键词或ID，返回规范的 category_id (支持泛用性全板块路由)"""
        if category_input is None or category_input == "":
            return DEFAULT_CATEGORY_ID

        if isinstance(category_input, int):
            return category_input
        if str(category_input).strip().isdigit():
            return int(str(category_input).strip())

        cat_str = str(category_input).strip().lower()
        cats = self.list_categories()

        # 1. 精确名称或 slug 匹配
        for c in cats:
            if cat_str == c["name"].lower() or cat_str == str(c["slug"]).lower():
                return c["id"]

        # 2. 包含匹配
        for c in cats:
            if cat_str in c["name"].lower() or cat_str in str(c["slug"]).lower() or c["name"].lower() in cat_str:
                return c["id"]

        # 3. 语义关键词映射
        keywords_map = {
            "工具": 5, "开源": 5, "workflow": 5, "工作流": 5, "排错": 5, "软件": 5,
            "创作": 6, "提示词": 6, "prompt": 6, "经验": 6, "交流": 6, "画风": 6,
            "运营": 7, "变现": 7, "推流": 7, "带货": 7, "起号": 7, "商业": 7,
            "爆款": 8, "作品": 8, "实战": 8, "晒图": 8, "成片": 8, "案例": 8,
            "skill": 9, "手绘": 9, "技能": 9, "插件": 9,
            "大厅": 4, "综合": 4, "公告": 4, "新人": 4
        }
        for kw, cid in keywords_map.items():
            if kw in cat_str:
                return cid

        return DEFAULT_CATEGORY_ID

    def create_topic(self, title, content, category=None, tags=None, image_path=None):
        """
        通用发帖方法：可向论坛任意板块发布纯文本或图文主题
        """
        if not self.auth:
            raise PermissionError("尚未登录手绘风社区账号，请先执行登录或绑定！")

        category_id = self.resolve_category(category)

        img_markdown = ""
        img_url = None
        if image_path:
            p = Path(image_path)
            if p.exists():
                print(f"[*] 正在上传配图至社区: {image_path} ...")
                upload_res = self.upload_image(str(p))
                img_url = upload_res.get("url") or upload_res.get("short_url")
                short_url = upload_res.get("short_url") or img_url
                orig_name = upload_res.get("original_filename", "配图")
                img_markdown = f"![{orig_name}]({short_url})\n\n"
            else:
                print(f"[!] 警告：配图文件不存在，将作为纯文本发布: {image_path}")

        raw_text = content
        if content.startswith("@") and Path(content[1:]).exists():
            with open(content[1:], "r", encoding="utf-8") as f:
                raw_text = f.read()
        elif Path(content).exists() and Path(content).is_file():
            try:
                with open(content, "r", encoding="utf-8") as f:
                    raw_text = f.read()
            except Exception:
                raw_text = content

        full_raw = f"{img_markdown}{raw_text}".strip()

        if len(title.strip()) < 5:
            title = f"【分享】{title.strip()} · 手绘风社区"

        tag_list = []
        if tags:
            if isinstance(tags, list):
                tag_list = tags
            elif isinstance(tags, str):
                tag_list = [t.strip() for t in tags.replace("，", ",").split(",") if t.strip()]

        payload = {
            "title": title.strip(),
            "raw": full_raw,
            "category": category_id
        }
        if tag_list:
            payload["tags"] = tag_list

        cats = self.list_categories()
        cat_name = next((c["name"] for c in cats if c["id"] == category_id), f"板块#{category_id}")
        print(f"[*] 正在向 [{cat_name}] (ID: {category_id}) 发布主题: 《{title}》 ...")

        post_data = self._post_json(f"{self.base_url}/posts.json", payload)

        topic_id = post_data.get("topic_id")
        topic_slug = post_data.get("topic_slug", "topic")
        post_id = post_data.get("id")
        full_url = f"{self.base_url}/t/{topic_slug}/{topic_id}"

        return {
            "success": True,
            "post_id": post_id,
            "topic_id": topic_id,
            "topic_slug": topic_slug,
            "category_id": category_id,
            "category_name": cat_name,
            "title": title,
            "url": full_url,
            "image_url": img_url
        }

    def reply_topic(self, topic_id, content, image_path=None):
        """
        通用回复方法：向指定主题发布跟帖回复
        """
        if not self.auth:
            raise PermissionError("尚未登录手绘风社区账号，请先执行登录或绑定！")

        img_markdown = ""
        img_url = None
        if image_path:
            p = Path(image_path)
            if p.exists():
                print(f"[*] 正在上传跟帖配图至社区: {image_path} ...")
                upload_res = self.upload_image(str(p))
                img_url = upload_res.get("url") or upload_res.get("short_url")
                short_url = upload_res.get("short_url") or img_url
                orig_name = upload_res.get("original_filename", "配图")
                img_markdown = f"![{orig_name}]({short_url})\n\n"

        raw_text = content
        if content.startswith("@") and Path(content[1:]).exists():
            with open(content[1:], "r", encoding="utf-8") as f:
                raw_text = f.read()

        full_raw = f"{img_markdown}{raw_text}".strip()
        payload = {
            "topic_id": int(topic_id),
            "raw": full_raw
        }
        print(f"[*] 正在向主题 (ID: {topic_id}) 发布回复 ...")
        post_data = self._post_json(f"{self.base_url}/posts.json", payload)
        post_num = post_data.get("post_number", 1)
        full_url = f"{self.base_url}/t/topic/{topic_id}/{post_num}"

        return {
            "success": True,
            "post_id": post_data.get("id"),
            "topic_id": topic_id,
            "post_number": post_num,
            "url": full_url,
            "image_url": img_url
        }

    def share_creation(self, image_path, prompt, title=None, style_id=None, style_name=None,
                       color_id=None, color_name=None, category=None, tags=None, notes=None):
        """
        一键分享作品与提示词到社区论坛（支持指定任意板块）
        """
        if not self.auth:
            raise PermissionError("尚未登录手绘风社区账号，请先执行登录或绑定！")

        # 智能解析目标板块，默认优先"创作交流"板块 (ID 6)
        target_category = category if category is not None else 6
        category_id = self.resolve_category(target_category)

        print(f"[*] 正在上传作品图片至手绘风社区: {image_path} ...")
        upload_res = self.upload_image(image_path)
        img_url = upload_res.get("url") or upload_res.get("short_url")
        short_url = upload_res.get("short_url") or img_url
        orig_name = upload_res.get("original_filename", "作品")

        # 智能生成标题
        if not title:
            style_label = f"#{style_id}" if style_id else "原创手绘"
            theme_snippet = prompt.split("，")[0].split("。")[0].split(",")[0][:25]
            title = f"【手绘风 {style_label}】{theme_snippet}"

        if len(title) < 5:
            title = f"{title} · 手绘风创作分享"

        # 构造图文出版级 Markdown 帖子结构
        meta_items = []
        if style_id:
            s_name = f" · {style_name}" if style_name else ""
            meta_items.append(f"🎨 **画风编号**：`#{style_id}{s_name}`")
        if color_id:
            c_name = f" · {color_name}" if color_name else ""
            meta_items.append(f"🌈 **主题色彩**：`{color_id}{c_name}`")
        meta_items.append(f"👤 **创作者**：@{self.auth.get('username')}")

        meta_block = "\n".join(meta_items)
        notes_block = f"\n> 💡 **创作心得/说明**：\n> {notes}\n" if notes else ""

        raw_content = f"""![{orig_name}]({short_url})

{meta_block}
{notes_block}
---

### 📝 完整出版级生图提示词 (Prompts)

```markdown
{prompt.strip()}
```

---
*本帖由 [HandRaw Style Studio](https://handraw-style.com) 一键分享生成。欢迎点赞、交流与临摹复现！*
"""

        topic_payload = {
            "title": title,
            "raw": raw_content,
            "category": category_id
        }
        if tags and isinstance(tags, list):
            topic_payload["tags"] = tags
        elif tags and isinstance(tags, str):
            topic_payload["tags"] = [t.strip() for t in tags.replace("，", ",").split(",") if t.strip()]
        else:
            auto_tags = ["手绘风", "提示词分享"]
            if style_id:
                auto_tags.append(f"style-{style_id}")
            topic_payload["tags"] = auto_tags

        cats = self.list_categories()
        cat_name = next((c["name"] for c in cats if c["id"] == category_id), f"板块#{category_id}")
        print(f"[*] 正在向 [{cat_name}] (ID: {category_id}) 发布帖子: 《{title}》 ...")
        post_data = self._post_json(f"{self.base_url}/posts.json", topic_payload)

        topic_id = post_data.get("topic_id")
        topic_slug = post_data.get("topic_slug", "topic")
        post_id = post_data.get("id")
        full_url = f"{self.base_url}/t/{topic_slug}/{topic_id}"

        return {
            "success": True,
            "post_id": post_id,
            "topic_id": topic_id,
            "topic_slug": topic_slug,
            "category_id": category_id,
            "category_name": cat_name,
            "title": title,
            "url": full_url,
            "image_url": img_url
        }

    def list_my_posts(self, username=None, limit=20):
        """
        获取当前登录用户发布的全部帖子列表
        """
        target_user = username or self.auth.get("username")
        if not target_user:
            raise PermissionError("请先登录或指定用户名查看帖子！")

        quoted_user = urllib.parse.quote(target_user)
        url = f"{self.base_url}/topics/created-by/{quoted_user}.json"

        headers = {"User-Agent": "HandRawStudio/1.0", "Accept": "application/json"}
        if self.auth.get("api_key"):
            headers["Api-Key"] = self.auth.get("api_key")
            u = self.auth.get("username")
            if u:
                try:
                    u.encode('ascii')
                    headers["Api-Username"] = u
                except UnicodeEncodeError:
                    pass
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        else:
            req = urllib.request.Request(url, headers=headers)
            with self.opener.open(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))

        topics = data.get("topic_list", {}).get("topics", [])
        results = []
        for t in topics[:limit]:
            topic_id = t.get("id")
            slug = t.get("slug", "topic")
            image_url = t.get("image_url")
            if image_url and not image_url.startswith("http"):
                image_url = f"{self.base_url}{image_url}"

            results.append({
                "topic_id": topic_id,
                "title": t.get("title"),
                "slug": slug,
                "url": f"{self.base_url}/t/{slug}/{topic_id}",
                "created_at": t.get("created_at"),
                "views": t.get("views", 0),
                "like_count": t.get("like_count", 0),
                "posts_count": t.get("posts_count", 1),
                "image_url": image_url,
                "category_id": t.get("category_id")
            })
        return results

    def delete_post(self, topic_id=None, post_id=None):
        """
        删除帖子或主题 (需要当前用户具备删除权限)
        """
        if not self.auth:
            raise PermissionError("尚未登录手绘风社区账号！")

        if topic_id:
            url = f"{self.base_url}/t/{topic_id}.json"
        elif post_id:
            url = f"{self.base_url}/posts/{post_id}.json"
        else:
            raise ValueError("必须提供 topic_id 或 post_id")

        headers = {
            "User-Agent": "HandRawStudio/1.0",
            "Accept": "application/json"
        }

        try:
            if self.auth.get("api_key"):
                headers["Api-Key"] = self.auth.get("api_key")
                username = self.auth.get("username")
                if username:
                    try:
                        username.encode('ascii')
                        headers["Api-Username"] = username
                    except UnicodeEncodeError:
                        pass
                req = urllib.request.Request(url, headers=headers, method="DELETE")
                with urllib.request.urlopen(req, timeout=10) as resp:
                    return resp.status in (200, 204)
            else:
                csrf = self.get_csrf_token()
                headers["X-CSRF-Token"] = csrf
                req = urllib.request.Request(url, headers=headers, method="DELETE")
                with self.opener.open(req, timeout=10) as resp:
                    return resp.status in (200, 204)
        except urllib.error.HTTPError as e:
            try:
                err_data = json.loads(e.read().decode("utf-8"))
                errors = err_data.get("errors", [])
                err_msg = " | ".join(errors) if errors else str(e)
            except Exception:
                err_msg = str(e)
            raise PermissionError(f"删除失败 (HTTP {e.code}): {err_msg}")

    def edit_post(self, post_id, new_raw, new_title=None):
        """编辑帖子内容或标题"""
        payload = {"post": {"raw": new_raw}}
        if new_title:
            payload["title"] = new_title
        return self._put_json(f"{self.base_url}/posts/{post_id}.json", payload)

    def _post_json(self, url, payload):
        data_bytes = json.dumps(payload).encode("utf-8")
        headers = {
            "User-Agent": "HandRawStudio/1.0",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if self.auth.get("api_key"):
            headers["Api-Key"] = self.auth.get("api_key")
            username = self.auth.get("username")
            if username:
                try:
                    username.encode('ascii')
                    headers["Api-Username"] = username
                except UnicodeEncodeError:
                    pass
            req = urllib.request.Request(url, data=data_bytes, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))
        else:
            csrf = self.get_csrf_token()
            headers["X-CSRF-Token"] = csrf
            req = urllib.request.Request(url, data=data_bytes, headers=headers, method="POST")
            with self.opener.open(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))

    def _put_json(self, url, payload):
        data_bytes = json.dumps(payload).encode("utf-8")
        headers = {
            "User-Agent": "HandRawStudio/1.0",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if self.auth.get("api_key"):
            headers["Api-Key"] = self.auth.get("api_key")
            req = urllib.request.Request(url, data=data_bytes, headers=headers, method="PUT")
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))
        else:
            csrf = self.get_csrf_token()
            headers["X-CSRF-Token"] = csrf
            req = urllib.request.Request(url, data=data_bytes, headers=headers, method="PUT")
            with self.opener.open(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))


# ---------------- 命令行 CLI 支持 ----------------

def cli_main():
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass

    import argparse
    parser = argparse.ArgumentParser(description="HandRaw Style 社区互动命令行工具 (全板块通用发帖与内容管理)")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # login
    p_login = subparsers.add_parser("login", help="登录手绘风社区账号")
    p_login.add_argument("--username", "-u", help="用户名或邮箱")
    p_login.add_argument("--password", "-p", help="登录密码")
    p_login.add_argument("--api-key", "-k", help="Discourse API Key (可选直接绑定)")

    # whoami
    subparsers.add_parser("whoami", help="查看当前登录账号状态")

    # logout
    subparsers.add_parser("logout", help="退出当前登录账号")

    # categories (板块列表)
    subparsers.add_parser("categories", help="列出社区全部板块、ID与说明")

    # post (通用全板块发帖)
    p_post = subparsers.add_parser("post", help="发布通用帖子（支持任意板块、纯文本或图文）")
    p_post.add_argument("--title", "-t", required=True, help="帖子标题（至少5个字符）")
    p_post.add_argument("--content", "-c", required=True, help="Markdown正文内容，或传入 @filepath.md")
    p_post.add_argument("--category", "-C", default=None, help="目标板块名称或ID (如 '创作交流' / '好用的工具' / '手绘skill' / 6 等)")
    p_post.add_argument("--image", "-i", default=None, help="可选：自动上传并在帖首嵌入配图")
    p_post.add_argument("--tags", default=None, help="逗号分隔的标签列表 (如 '手绘风,工具,分享')")

    # share (手绘创作专用分享)
    p_share = subparsers.add_parser("share", help="分享手绘作品与提示词到社区 (智能排版)")
    p_share.add_argument("--image", "-i", required=True, help="要分享的图片本地路径")
    p_share.add_argument("--prompt", required=True, help="生成的完整提示词")
    p_share.add_argument("--title", "-t", help="帖子标题（留空自动生成）")
    p_share.add_argument("--category", "-C", default=None, help="目标板块名称或ID (默认优先: 创作交流 / 6)")
    p_share.add_argument("--style", "-s", help="画风编号 (如 048)")
    p_share.add_argument("--style-name", help="画风名称")
    p_share.add_argument("--color", "-c", help="主题色编号 (如 C-01)")
    p_share.add_argument("--notes", "-n", help="创作心得或说明")
    p_share.add_argument("--tags", default=None, help="自定义标签 (逗号分隔)")

    # reply (回复主题)
    p_reply = subparsers.add_parser("reply", help="回复论坛指定主题")
    p_reply.add_argument("--topic-id", "-id", type=int, required=True, help="目标主题ID")
    p_reply.add_argument("--content", "-c", required=True, help="回复正文内容，或 @filepath.md")
    p_reply.add_argument("--image", "-i", default=None, help="可选：回复中附带的配图路径")

    # my-posts
    p_posts = subparsers.add_parser("my-posts", help="查看我发布的帖子列表")
    p_posts.add_argument("--limit", type=int, default=15, help="显示数量")

    # delete
    p_del = subparsers.add_parser("delete", help="删除我的指定帖子")
    p_del.add_argument("--topic-id", type=int, required=True, help="要删除的主题 ID")

    # deploy (发布/同步画廊静态页面与资产至云端社区)
    p_deploy = subparsers.add_parser("deploy", help="同步并发布画廊静态页面、样式数据与图片资产至云端社区")
    p_deploy.add_argument("--announce", action="store_true", help="部署完成后自动在论坛「手绘skill」板块发布更新公告帖")
    p_deploy.add_argument("--git", action="store_true", help="同时提交并推送到 GitHub 远端 handraw-static 仓库")

    args = parser.parse_args()
    client = DiscourseClient()

    if args.command == "login":
        if args.api_key:
            res = client.login_with_api_key(args.api_key, args.username)
            print(f"[OK] API Key 绑定成功！欢迎创作者: @{res.get('username')}")
        elif args.username and args.password:
            res = client.login_with_password(args.username, args.password)
            print(f"[OK] 登录成功！欢迎回来: @{res.get('username')} (信任等级: TL{res.get('trust_level')})")
        else:
            print("请输入 --username 和 --password，或提供 --api-key 进行登录。")

    elif args.command == "whoami":
        info = client.whoami()
        if info.get("logged_in"):
            print(f"✅ 当前已登录手绘风社区账号:")
            print(f"   用户名: @{info.get('username')}")
            print(f"   昵称: {info.get('name') or '无'}")
            print(f"   社区地址: {info.get('community_url')}")
            print(f"   认证方式: {info.get('auth_type')}")
        else:
            print("❌ 当前未登录任何手绘风社区账号。请使用 login 命令进行登录绑定。")

    elif args.command == "logout":
        clear_auth_profile()
        print("[OK] 已安全退出手绘风社区账号并清除本地凭据。")

    elif args.command == "categories":
        cats = client.list_categories(refresh=True)
        print("📌 手绘风社区可用板块一览 (发帖可直接指定板块名称或ID):")
        print("-" * 65)
        for c in cats:
            desc = f" - {c['description']}" if c.get("description") else ""
            print(f" • [ID: {c['id']:2d}] {c['name']:<12s} ({c.get('slug', 'default')}){desc}")
        print("-" * 65)

    elif args.command == "post":
        res = client.create_topic(
            title=args.title,
            content=args.content,
            category=args.category,
            tags=args.tags,
            image_path=args.image
        )
        print(f"🎉 帖子已成功发布至 [{res.get('category_name')}]！")
        print(f"   标题: {res.get('title')}")
        print(f"   直达链接: {res.get('url')}")
        if res.get("image_url"):
            print(f"   配图短链: {res.get('image_url')}")

    elif args.command == "share":
        res = client.share_creation(
            image_path=args.image,
            prompt=args.prompt,
            title=args.title,
            category=args.category,
            style_id=args.style,
            style_name=args.style_name,
            color_id=args.color,
            notes=args.notes,
            tags=args.tags
        )
        print(f"🎉 作品与提示词已成功分享到 [{res.get('category_name')}]！")
        print(f"   标题: {res.get('title')}")
        print(f"   直达链接: {res.get('url')}")

    elif args.command == "reply":
        res = client.reply_topic(
            topic_id=args.topic_id,
            content=args.content,
            image_path=args.image
        )
        print(f"💬 回复成功！直达链接: {res.get('url')}")

    elif args.command == "my-posts":
        posts = client.list_my_posts(limit=args.limit)
        if not posts:
            print("暂未发布任何帖子。快去生成一幅手绘画作分享吧！")
        else:
            print(f"📚 你在手绘风社区发布的帖子列表 (共 {len(posts)} 条):")
            for idx, p in enumerate(posts, 1):
                print(f"[{idx}] (ID: {p['topic_id']}) {p['title']}")
                print(f"    链接: {p['url']} | 浏览: {p['views']} | 点赞: {p['like_count']} | 回复: {p['posts_count']}")

    elif args.command == "delete":
        try:
            ok = client.delete_post(topic_id=args.topic_id)
            if ok:
                print(f"🗑️ 帖子 (ID: {args.topic_id}) 已成功删除。")
            else:
                print(f"删除失败，请检查网络或是否拥有该帖子的删除权限。")
        except Exception as e:
            print(f"⚠️ {e}")

    elif args.command == "deploy":
        candidates = [
            Path(__file__).resolve().parent / "sync_to_static.py",
            Path(__file__).resolve().parents[1] / "scripts" / "sync_to_static.py",
            Path(__file__).resolve().parents[2] / "scripts" / "sync_to_static.py",
            Path(os.environ.get("HANDRAW_STYLE_ROOT", Path(__file__).resolve().parents[1])) / "scripts" / "sync_to_static.py",
        ]
        sync_script = None
        for c in candidates:
            if c.exists():
                sync_script = c
                break

        if not sync_script:
            print("❌ 未找到 scripts/sync_to_static.py 脚本！")
            sys.exit(1)

        cmd = [sys.executable, str(sync_script), "--deploy"]
        if getattr(args, "git", False):
            cmd.append("--git")

        print("🚀 正在执行静态画廊与资产部署上云...")
        res = subprocess.run(cmd)
        if res.returncode != 0:
            print(f"❌ 静态部署执行失败 (Exit code {res.returncode})")
            sys.exit(res.returncode)

        print("\n✅ 风格画廊与静态资产已成功同步部署到云端服务器！")
        print("   风格画廊首页: https://handraw-style.com/gallery/index.html")
        print("   提示词拼装器: https://handraw-style.com/gallery/tutorials.html")
        print("   自建资产图库: https://handraw-style.com/gallery/assets.html")

        if getattr(args, "announce", False):
            print("\n📢 正在自动生成论坛更新公告并发布至「手绘skill」板块...")
            version_path = sync_script.parent.parent / "version.json"
            version_str = "最新版"
            if version_path.exists():
                try:
                    with open(version_path, "r", encoding="utf-8") as f:
                        version_str = f"v{json.load(f).get('version', '')}"
                except Exception:
                    pass

            manifest_path = sync_script.parent.parent.parent / "handraw-static" / "manifest.json"
            styles_count = 365
            if manifest_path.exists():
                try:
                    with open(manifest_path, "r", encoding="utf-8") as f:
                        styles_count = json.load(f).get("styles_count", 365)
                except Exception:
                    pass

            title = f"【官方更新】手绘风格画廊 {version_str} 全新上线与在线拼装指南"
            content = f"""## 🎨 手绘风格画廊 {version_str} 已同步上线！

手绘风生态静态资源与风格画廊已完成全量更新，包含全量 {styles_count} 种视觉画风、主题色彩、版式结构库以及全新写实摄影与自建资产！

### 🔗 在线直达
- 🏛️ **风格画廊首页**: [https://handraw-style.com/gallery/index.html](https://handraw-style.com/gallery/index.html)
- 🧩 **提示词拼装器与教程**: [https://handraw-style.com/gallery/tutorials.html](https://handraw-style.com/gallery/tutorials.html)
- 🗂️ **自建资产图库**: [https://handraw-style.com/gallery/assets.html](https://handraw-style.com/gallery/assets.html)

欢迎大家在评论区交流画风使用心得或反馈建议！
"""
            post_res = client.post_topic(
                title=title,
                raw=content,
                category_name="手绘skill",
                tags="更新,画风库,公告,gallery"
            )
            print(f"🎉 公告帖子已发布至 [{post_res.get('category_name')}]！")
            print(f"   标题: {post_res.get('title')}")
            print(f"   直达链接: {post_res.get('url')}")

    else:
        parser.print_help()


if __name__ == "__main__":
    cli_main()
