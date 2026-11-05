#!/usr/bin/env python3
"""Prepare private conversation share drafts; publish only after a user click."""
from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
import mimetypes
import os
import re
import sys
import urllib.error
import urllib.request
import uuid
from urllib.parse import urlsplit
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

BASE_URL = "https://handraw-style.com"
# The share target is the handraw-web backend's work-publish contract.  It
# accepts {"entry": {...}} and answers {"id", "kind": "work", "url"}.  The
# previous value pointed at the Discourse plugin, which handraw-web replaces.
WORK_ENDPOINT = "/api/entries"
PACKAGE_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_AUTH = PACKAGE_ROOT / "client/cache/conversation_share.auth.json"


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def image_record(path):
    path = Path(path).resolve(strict=True)
    with Image.open(path) as image:
        image.verify()
    with Image.open(path) as image:
        width, height = image.size
    return {"path": str(path), "sha256": digest(path.read_bytes()),
            "width": width, "height": height}


def resolved_ids(style_ids=None, layout_ids=None):
    result = {}
    for key, values, filename, id_key in [
        ("resolved_style_ids", style_ids, "styles.json", "number"),
        ("resolved_layout_ids", layout_ids, "layouts.json", "id"),
    ]:
        if values is not None:
            if not isinstance(values, list) or not all(isinstance(x, str) for x in values):
                raise ValueError("使用编号必须是列表；未使用请传空列表。")
            values = list(dict.fromkeys(x.strip().upper() for x in values))
            index = json.loads((PACKAGE_ROOT / "skills/handdraw-style-prompter/references" / filename).read_text(encoding="utf-8"))
            allowed = {item[id_key] for item in index}
            if any(x not in allowed for x in values):
                raise ValueError("画风或图型编号未收录，请核对实际采用的编号。")
        result[key] = values
    return {**result, "resolved_ids_sha256": digest(json.dumps(result, sort_keys=True).encode("utf-8"))}


def id_note(draft):
    fields = resolved_ids(draft.get("resolved_style_ids"), draft.get("resolved_layout_ids"))
    if draft.get("resolved_ids_sha256") and draft["resolved_ids_sha256"] != fields["resolved_ids_sha256"]:
        raise ValueError("使用编号已更改，请重新准备编号备注。")
    tags = []
    for key, label in [("resolved_style_ids", "画风"), ("resolved_layout_ids", "图型")]:
        if fields[key]:
            tags.append(f"【{label}：{'、'.join(fields[key])} 】")
    return " ".join(tags)


def shared_prompt(draft):
    tags = id_note(draft)
    return draft["original_request"] + ("\n" + tags if tags else "")


def work_assets(draft):
    id_note(draft)
    styles, layouts = draft.get("resolved_style_ids"), draft.get("resolved_layout_ids")
    if styles is None or layouts is None:
        raise ValueError("请补充实际使用的画风和图型编号；未使用时请明确注明。")
    if len(styles) > 2 or len(layouts) > 1:
        raise ValueError("作品广场每件作品最多关联两个画风和一个图型，请拆分作品。")
    return ([{"ref": "official:" + item, "role": "style"} for item in styles] +
            [{"ref": "official:" + item, "role": "layout"} for item in layouts])


def validate_work(draft):
    work_assets(draft)
    if not 1 <= len(draft.get("images", [])) <= 9:
        raise ValueError("单件作品支持封面与最多8张附图，请拆分后分享。")
    if not 5 <= len(draft.get("title", "")) <= 160:
        raise ValueError("作品标题需为5至160个字符。")


def upload_url(record):
    url = record.get("url")
    if not url:
        short = record.get("short_url", "")
        if not re.fullmatch(r"upload://[A-Za-z0-9_.-]+", short):
            raise ValueError("缺少有效作品图片地址。")
        url = "/uploads/short-url/" + short.removeprefix("upload://")
    if url.startswith("//"):
        url = "https:" + url
    parsed = urlsplit(url)
    local = url.startswith("/uploads/") and not parsed.netloc
    remote = (parsed.scheme == "https" and parsed.hostname in
              {"handraw-style.com", "img.handraw-style.com", "static.handraw-style.com"}
              and not parsed.username and not parsed.password and parsed.port in {None, 443})
    if not (local or remote) or re.search(r"[\r\n<>\[\]()\\]", url):
        raise ValueError("作品图片必须使用本站上传地址。")
    return url


def work_payload(draft):
    validate_work(draft)
    if len(draft["uploads"]) != len(draft["images"]):
        raise ValueError("作品图片尚未全部上传。")
    images = [upload_url(record) for record in draft["uploads"]]
    return {"kind": "work", "title": draft["title"],
            "summary": "由手绘风 Skill 生成的作品，附原始提示词与实际使用编号。",
            "cover_url": images[0], "price": 0, "paid_opt_in": False,
            "content": {"prompt": shared_prompt(draft),
                        "parameters": {"style_ids": draft["resolved_style_ids"],
                                       "layout_ids": draft["resolved_layout_ids"]},
                        "examples": [{"theme": f"作品{i}", "image": url}
                                     for i, url in enumerate(images[1:], 2)]},
            # Stable per draft: a retried publish must return the same work
            # rather than creating a duplicate.
            "requestId": f"skill-{draft['draft_id']}",
            "assets": work_assets(draft)}


def annotate_draft(path, style_ids=None, layout_ids=None):
    path = Path(path).resolve(strict=True)
    lock = path.with_name(path.name + ".publish.lock")
    fields = resolved_ids(style_ids, layout_ids)
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise RuntimeError("该草稿正在发布，不能修改编号备注。") from None
    try:
        os.close(fd)
        draft = json.loads(path.read_text(encoding="utf-8"))
        if draft.get("status") != "ready" or draft.get("receipt"):
            raise ValueError("仅可修改待发布草稿的编号备注。")
        draft.update(fields)
        write_json(path, draft)
        return draft
    finally:
        lock.unlink(missing_ok=True)


def prepare_draft(path, original_request, images, title=None, category=8, style_ids=None, layout_ids=None):
    """No network calls. Preserve the user message byte-for-byte as UTF-8 text."""
    path = Path(path).resolve()
    fields = resolved_ids(style_ids, layout_ids)
    if not isinstance(original_request, str) or not original_request.strip():
        raise ValueError("缺少原始创作指令；不能用解析后提示词代替。")
    records = [image_record(image) for image in images]
    if not records or len({x["path"] for x in records}) != len(records):
        raise ValueError("请提供至少一张图片，且图片不能重复。")
    category = int(category)
    title = title or "【作品分享】" + original_request.strip().splitlines()[0][:64]
    title = title.strip()
    if not 5 <= len(title) <= 160 or category <= 0:
        raise ValueError("标题需为5至160个字符，分类ID必须为正数。")
    content_id = digest(json.dumps({"request": original_request,
        "images": [x["sha256"] for x in records], "title": title,
        "category": category}, ensure_ascii=False).encode("utf-8"))
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing.get("content_id") != content_id:
            raise ValueError("该草稿已有其他内容；请另建草稿，不覆盖原记录。")
        for key, supplied in [("resolved_style_ids", style_ids), ("resolved_layout_ids", layout_ids)]:
            if supplied is not None and existing.get(key) != fields[key]:
                raise ValueError("草稿已有不同编号；请用 annotate 更新待发布草稿。")
        return existing
    draft = {"schema_version": 3, "destination": "work_square", "draft_id": uuid.uuid4().hex,
        "content_id": content_id, "created_at": now(), "status": "ready",
        "title": title, "category": category,
        "original_request": original_request,
        "original_request_sha256": digest(original_request.encode("utf-8")),
        "images": records, "uploads": [], "receipt": None, **fields}
    write_json(path, draft)
    return draft


def markdown_body(draft):
    original = shared_prompt(draft)
    longest = max((len(x) for x in re.findall(r"`+", original)), default=0)
    fence = "`" * max(3, longest + 1)
    images = "\n\n".join(f"![作品{i}]({upload_url(item)})"
                           for i, item in enumerate(draft["uploads"], 1))
    return (f"{images}\n\n## 最初的指令\n\n{fence}text\n{original}\n{fence}"
            f"\n\n<!-- handraw-conversation-share:{draft['draft_id']} -->")


def button(draft_path, draft, host="codex", page_url=None):
    if draft.get("status") == "published":
        if draft["receipt"].get("destination") != "work_square":
            return f"[查看原论坛帖（旧版记录）]({draft['receipt']['url']})"
        return f"[查看已分享作品]({draft['receipt']['url']})"
    if page_url:
        return f"[分享到网站]({page_url})"
    return "**分享到网站**：回复“分享到网站”，即可将本次图片、最初指令及编号备注分享到作品广场。"


class APIRejected(RuntimeError):
    pass


class PostOutcomeUnknown(RuntimeError):
    pass


class CommunityAPI:
    def __init__(self, key):
        if not key or not re.fullmatch(r"[A-Za-z0-9_-]{16,256}", key):
            raise ValueError("个人API Key格式无效。")
        self.key = key

    def request(self, method, endpoint, data=None, content_type=None):
        if not endpoint.startswith("/") or endpoint.startswith("//"):
            raise ValueError("API路径无效。")
        headers = {"Api-Key": self.key, "Accept": "application/json",
                   "User-Agent": "HandrawConversationShare/1.0"}
        if content_type:
            headers["Content-Type"] = content_type
        request = urllib.request.Request(BASE_URL + endpoint, data=data,
                                         headers=headers, method=method)
        try:
            # Never follow redirects carrying credentials to a different host.
            class NoRedirect(urllib.request.HTTPRedirectHandler):
                def redirect_request(self, *args, **kwargs):
                    return None
            with urllib.request.build_opener(NoRedirect).open(request, timeout=45) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            if method == "POST" and endpoint == WORK_ENDPOINT and error.code >= 500:
                raise PostOutcomeUnknown("作品发布响应未确认，请先核对作品广场，勿重复发布。") from None
            detail = ""
            try:
                payload = json.loads(error.read(65536).decode("utf-8"))
                errors = payload.get("errors") or payload.get("error") or payload.get("message")
                if isinstance(errors, list):
                    detail = "；".join(x for x in errors if isinstance(x, str))
                elif isinstance(errors, str):
                    detail = errors
                detail = html.unescape(re.sub(r"<[^>]+>", "", detail))
                detail = re.sub(r"[\x00-\x1f]", " ", detail.replace(self.key, "[凭据已隐藏]"))[:500]
            except (OSError, ValueError, AttributeError):
                pass
            suffix = f"：{detail}" if detail else "。"
            raise APIRejected(f"网站API拒绝请求（HTTP {error.code}）{suffix}") from None
        except (OSError, ValueError) as error:
            if method == "POST" and endpoint == WORK_ENDPOINT:
                raise PostOutcomeUnknown("作品发布响应未确认，请先核对作品广场，勿重复发布。") from None
            raise RuntimeError("网站连接失败或响应无效，请稍后重试。") from None

    def current_user(self):
        # handraw-web exposes the signed-in account on /api/boot.  An invalid or
        # revoked API key yields no user, which is the same rejection reason as
        # before, so callers need no change.
        boot = self.request("GET", "/api/boot")
        user = boot.get("user") or boot.get("currentUser") or None
        if not user or not user.get("username"):
            raise APIRejected("凭据未绑定有效社区账号。")
        return {"username": user["username"], "user_id": user.get("id")}

    def check_work_access(self):
        # Publishing a work is open to any active account on handraw-web; the
        # account check above already proves the key is valid and active.
        boot = self.request("GET", "/api/boot")
        if not (boot.get("user") or boot.get("currentUser")):
            raise APIRejected("当前账号暂无作品广场发布权限，请登录网站检查账号状态。")

    def upload(self, record):
        # handraw-web takes a JSON body with a data URL and answers with a
        # same-origin media path, so no multipart/short-url round trip is needed.
        path = Path(record["path"])
        mime = mimetypes.guess_type(path.name)[0] or "image/png"
        data_url = f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")
        result = self.request(
            "POST",
            "/api/uploads",
            json.dumps({"dataUrl": data_url, "nameZh": path.stem, "cat": "share"}, ensure_ascii=False).encode("utf-8"),
            "application/json; charset=utf-8",
        )
        url = result.get("url") or result.get("imageUrl")
        if not isinstance(url, str) or not url.startswith("/"):
            raise RuntimeError("图片上传响应缺少有效站内地址。")
        return {"url": url, "id": result.get("id"), "sha256": record["sha256"]}

    def create_work(self, entry):
        return self.request("POST", WORK_ENDPOINT, json.dumps({"entry": entry}, ensure_ascii=False).encode("utf-8"),
            "application/json; charset=utf-8")

    def get_work(self, entry_id):
        # handraw-web serves a work through the forum resource API, which
        # returns the resource record plus its curation/thread context.
        return self.request("GET", f"/api/forum/resources/work/{uuid.UUID(str(entry_id))}")

    def get_work_content(self, entry_id):
        # The same resource payload carries the work's prompt and images, so the
        # content check reads it from there instead of a second endpoint.
        detail = self.get_work(entry_id)
        resource = detail.get("resource") or {}
        return {
            "content": {
                "prompt": resource.get("prompt") or "",
                "examples": [
                    {"theme": "", "image": url}
                    for url in (resource.get("images") or [])[1:]
                ],
            }
        }


def load_key(auth_file=DEFAULT_AUTH):
    key = os.environ.get("HANDRAW_COMMUNITY_API_KEY", "").strip()
    if key:
        return key
    candidates = [Path(auth_file), Path.home() / ".handraw-style/community_auth.json",
                  PACKAGE_ROOT / "client/cache/community_auth.json"]
    for path in candidates:
        if path.is_file():
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("api_key"):
                return data["api_key"]
    raise APIRejected("尚未绑定手绘风账号，请先绑定个人API Key。")


def publish_draft(path, api):
    path = Path(path).resolve(strict=True)
    lock = path.with_name(path.name + ".publish.lock")
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise RuntimeError("该草稿正在发布，请等待完成；不要重复点击。") from None
    try:
        os.close(fd)
        draft = json.loads(path.read_text(encoding="utf-8"))
        if draft.get("status") == "published":
            if draft["receipt"].get("destination") != "work_square":
                raise ValueError("旧草稿已发布为论坛帖，请为作品广场另建分享草稿。")
            return draft["receipt"]
        if draft.get("status") in {"publishing", "publication_uncertain"}:
            raise PostOutcomeUnknown("上次发布结果未确认，请先核对网站，勿重复发布。")
        original = draft.get("original_request")
        if not isinstance(original, str) or not original.strip() or digest(original.encode("utf-8")) != draft.get("original_request_sha256"):
            raise ValueError("原始指令缺失或已更改，请重新准备分享草稿。")
        validate_work(draft)
        if not draft.get("images"):
            raise ValueError("分享草稿没有图片。")
        for record in draft["images"]:
            if image_record(record["path"])["sha256"] != record["sha256"]:
                raise ValueError("图片已更改，请重新准备分享草稿。")
        account = api.current_user()
        if draft.get("account") and draft["account"] != account:
            raise ValueError("该草稿已有其他账号的上传记录，请使用原账号继续。")
        api.check_work_access()
        draft["account"] = account
        draft["destination"] = "work_square"
        draft["status"] = "uploading"
        write_json(path, draft)
        try:
            for index, record in enumerate(draft["images"]):
                if index < len(draft["uploads"]):
                    if draft["uploads"][index]["sha256"] != record["sha256"]:
                        raise ValueError("上传记录与图片不一致。")
                    continue
                draft["uploads"].append(api.upload(record))
                write_json(path, draft)
            payload = work_payload(draft)
        except Exception:
            draft["status"] = "ready"
            write_json(path, draft)
            raise
        draft["status"] = "publishing"
        write_json(path, draft)
        try:
            result = api.create_work(payload)
            entry_id = str(uuid.UUID(result["id"]))
            if result.get("kind") != "work":
                raise ValueError("发布结果不是作品。")
        except APIRejected:
            draft["status"] = "ready"
            write_json(path, draft)
            raise
        except Exception:
            draft["status"] = "publication_uncertain"
            write_json(path, draft)
            raise PostOutcomeUnknown("作品发布结果未确认，请先核对作品广场；此草稿已阻止重复发布。") from None
        # The server owns the canonical address; fall back to the resource route
        # only if it did not send one.
        work_url = str(result.get("url") or f"/forum/?view=resource&kind=work&id={entry_id}")
        if work_url.startswith("/"):
            work_url = BASE_URL + work_url
        receipt = {"success": True, "destination": "work_square", "entry_id": entry_id,
                   "url": work_url, "published_at": now(),
                   "verified": False, "associations_verified": False}
        draft.update(status="published", receipt=receipt)
        write_json(path, draft)
        try:
            detail = api.get_work(entry_id)
            resource = detail.get("resource") or {}
            # The resource payload is the source of truth for identity, the
            # stored prompt, the image order and the linked styles/layout.
            stored_prompt = str(resource.get("prompt") or "")
            stored_images = list(resource.get("images") or [])
            stored_styles = list(resource.get("styles") or [])
            stored_layout = str(resource.get("layout") or "")
            expected_styles = [a["ref"].split(":", 1)[1] for a in payload["assets"] if a.get("role") == "style"]
            expected_layouts = [a["ref"].split(":", 1)[1] for a in payload["assets"] if a.get("role") == "layout"]

            receipt["associations_verified"] = (
                sorted(stored_styles) == sorted(expected_styles)
                and stored_layout == (expected_layouts[0] if expected_layouts else "")
            )
            receipt["verified"] = (
                str(resource.get("id") or "") == entry_id
                and stored_prompt == payload["content"]["prompt"]
                and stored_images[:1] == [payload["cover_url"]]
                and receipt["associations_verified"]
            )
        except Exception:
            # Verification is best effort; a failed readback must not claim success.
            receipt["verified"] = False
            receipt["associations_verified"] = False
        write_json(path, draft)
        return receipt
    finally:
        lock.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("prepare", help="Prepare locally; never uploads or posts")
    prepare.add_argument("--draft", required=True)
    prepare.add_argument("--original-request-file", required=True)
    prepare.add_argument("--image", action="append", required=True)
    prepare.add_argument("--title")
    prepare.add_argument("--category", type=int, default=8, help=argparse.SUPPRESS)  # Legacy draft compatibility only.
    prepare.add_argument("--host", choices=["codex", "claude"], default="codex")
    annotate = sub.add_parser("annotate", help="Append actual style/layout IDs to an unpublished draft")
    annotate.add_argument("--draft", required=True)
    for command in (prepare, annotate):
        styles = command.add_mutually_exclusive_group(required=command is annotate)
        styles.add_argument("--style", action="append", dest="style_ids")
        styles.add_argument("--no-style", action="store_const", dest="style_ids", const=[])
        layouts = command.add_mutually_exclusive_group(required=command is annotate)
        layouts.add_argument("--layout", action="append", dest="layout_ids")
        layouts.add_argument("--no-layout", action="store_const", dest="layout_ids", const=[])
    publish = sub.add_parser("publish", help="Publish after the user clicks Share")
    publish.add_argument("--draft", required=True)
    publish.add_argument("--auth-file", type=Path, default=DEFAULT_AUTH)
    bind = sub.add_parser("bind", help="Read a personal API key from stdin, never echo it")
    bind.add_argument("--auth-file", type=Path, default=DEFAULT_AUTH)
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            # newline='' preserves the exact line endings from the captured user message.
            with open(args.original_request_file, encoding="utf-8", newline="") as stream:
                original = stream.read()
            draft = prepare_draft(args.draft, original, args.image, args.title, args.category,
                                  args.style_ids, args.layout_ids)
            if draft.get("status") == "published":
                print(button(args.draft, draft, args.host))
            else:
                from conversation_share_ui import ensure_share_link
                print(button(args.draft, draft, args.host, ensure_share_link(args.draft)))
        elif args.command == "annotate":
            draft = annotate_draft(args.draft, args.style_ids, args.layout_ids)
            from conversation_share_ui import ensure_share_link
            print(button(args.draft, draft, page_url=ensure_share_link(args.draft)))
        elif args.command == "publish":
            print(json.dumps(publish_draft(args.draft, CommunityAPI(load_key(args.auth_file))), ensure_ascii=False))
        else:
            key = sys.stdin.read().strip()
            user = CommunityAPI(key).current_user()
            write_json(args.auth_file, {"api_key": key, "base_url": BASE_URL, **user})
            print(json.dumps({"success": True, **user}, ensure_ascii=False))
    except Exception as error:
        print(json.dumps({"success": False, "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
