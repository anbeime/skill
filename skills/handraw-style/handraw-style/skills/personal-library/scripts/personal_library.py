#!/usr/bin/env python3
"""Portable, opt-in Handraw personal resources; only standard-library dependencies."""
from __future__ import annotations

import argparse
import hashlib
import http.cookiejar
import json
import os
import re
import shutil
import stat
import tempfile
import urllib.parse
import urllib.request
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

MAX_ARCHIVE = 25 * 1024 * 1024
MAX_EXPANDED = 100 * 1024 * 1024
BASE_URL = "https://handraw-style.com"


def home() -> Path:
    return Path(os.environ.get("HANDRAW_PROFILE_HOME", str(Path.home() / ".handraw-style"))).expanduser()


class Library:
    def __init__(self, root: Path | str | None = None):
        self.root = Path(root or home() / "personal-library").resolve()

    def index(self) -> dict:
        path = self.root / "library.json"
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"schema_version": 1, "resources": []}

    def write(self, data: dict) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        temporary = self.root / f".index-{uuid.uuid4().hex}.tmp"
        temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(self.root / "library.json")
        skill_root = os.environ.get("HANDRAW_SKILL_ROOT")
        if skill_root:
            mirror = Path(skill_root).resolve() / ".handraw-personal"
            mirror.mkdir(parents=True, exist_ok=True)
            safe_json = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
            (mirror / "library.js").write_text("window.HANDRAW_PERSONAL_LIBRARY=" + safe_json + ";\n", encoding="utf-8")

    def get(self, resource_id: str) -> dict:
        return next((item for item in self.index()["resources"] if item["id"] == resource_id), None) or self._missing(resource_id)

    @staticmethod
    def _missing(resource_id):
        raise ValueError(f"找不到本地资源：{resource_id}")

    @staticmethod
    def validate_resource(resource: dict) -> None:
        if not isinstance(resource, dict) or resource.get("kind") not in {"style", "layout", "package", "work", "experience"}:
            raise ValueError("资源类型无效")
        if not str(resource.get("license", "")).strip():
            raise ValueError("缺少授权说明")
        if resource["kind"] in {"style", "layout"}:
            if not resource.get("prompt_zh") or not resource.get("prompt_en"):
                raise ValueError("画风／图型需要中英文定义")

    def create(self, kind: str, name: str, zh: str, en: str, license_text: str, origin: dict | None = None,
               examples: list[str] | None = None) -> dict:
        resource = {"id": f"mine:{uuid.uuid4()}", "kind": kind, "name": name,
                    "prompt_zh": zh, "prompt_en": en, "license": license_text, "version": "1.0.0",
                    "section": "owned", "origin": origin, "examples": examples or [],
                    "created_at": datetime.now(timezone.utc).isoformat()}
        self.validate_resource(resource)
        data = self.index()
        data["resources"].append(resource)
        self.write(data)
        return resource

    def update(self, resource_id: str, **changes) -> dict:
        data = self.index()
        resource = next((item for item in data["resources"] if item["id"] == resource_id), None)
        if not resource or resource["section"] != "owned":
            raise ValueError("只能修改自己创建的资源；收藏请先创建派生副本")
        allowed = {"name", "prompt_zh", "prompt_en", "license", "version", "examples"}
        resource.update({key: value for key, value in changes.items() if key in allowed and value is not None})
        self.validate_resource(resource)
        resource["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.write(data)
        return resource

    def import_bundle(self, bundle: Path | str, expected_sha256: str, source_id: str | None = None,
                      source_url: str | None = None, author: dict | None = None) -> dict:
        path = Path(bundle)
        if not re.fullmatch(r"[0-9a-fA-F]{64}", expected_sha256):
            raise ValueError("请提供有效的 SHA256 校验值")
        if path.stat().st_size > MAX_ARCHIVE:
            raise ValueError("资源包过大")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != expected_sha256.lower():
            raise ValueError("SHA256 校验失败，未导入资源")
        with zipfile.ZipFile(path) as archive:
            items = archive.infolist()
            if len(items) > 1000 or sum(item.file_size for item in items) > MAX_EXPANDED:
                raise ValueError("解压后资源过大")
            names = set()
            for item in items:
                name = item.filename.replace("\\", "/")
                parts = PurePosixPath(name).parts
                if (name.startswith("/") or ":" in name or ".." in parts or
                        stat.S_ISLNK(item.external_attr >> 16) or name in names):
                    raise ValueError("资源包包含不安全或重复路径")
                names.add(name)
            info = archive.getinfo("manifest.json")
            if info.file_size > 1024 * 1024:
                raise ValueError("资源清单过大")
            manifest = json.loads(archive.read(info))
            if manifest.get("schema_version") != 1:
                raise ValueError("资源包版本不受支持")
            resource = manifest["resource"]
            self.validate_resource(resource)
            canonical_source = source_id or resource.get("id")
            if not canonical_source or len(str(canonical_source)) > 200:
                raise ValueError("缺少稳定的来源 ID")
            local_id = "community:" + hashlib.sha256(str(canonical_source).encode()).hexdigest()[:24]
            data = self.index()
            existing = next((item for item in data["resources"] if item["id"] == local_id), None)
            if existing and existing.get("sha256") == digest:
                return existing
            self.root.mkdir(parents=True, exist_ok=True)
            # A content-addressed directory makes interrupted updates leave the old resource usable.
            destination = self.root / "bundles" / digest
            destination.parent.mkdir(parents=True, exist_ok=True)
            if not destination.exists():
                with tempfile.TemporaryDirectory(dir=destination.parent) as temporary:
                    staging = Path(temporary) / "resource"
                    staging.mkdir()
                    actual_bytes = 0
                    for item in items:
                        relative = PurePosixPath(item.filename.replace("\\", "/"))
                        output = staging.joinpath(*relative.parts)
                        if item.is_dir():
                            output.mkdir(parents=True, exist_ok=True)
                            continue
                        output.parent.mkdir(parents=True, exist_ok=True)
                        with archive.open(item) as incoming, output.open("wb") as outgoing:
                            while chunk := incoming.read(65536):
                                actual_bytes += len(chunk)
                                if actual_bytes > MAX_EXPANDED:
                                    raise ValueError("解压数据超过限制")
                                outgoing.write(chunk)
                    staging.replace(destination)
            item = {key: value for key, value in resource.items() if key not in {"section", "path", "origin", "id"}}
            item.update(id=local_id, section="collected", sha256=digest,
                        path=str(destination.relative_to(self.root)),
                        origin={"id": canonical_source, "url": source_url, "author": author or resource.get("author")},
                        updated_at=datetime.now(timezone.utc).isoformat())
            data["resources"] = [record for record in data["resources"] if record["id"] != local_id] + [item]
            self.write(data)
            return item

    def fork(self, resource_id: str, name: str) -> dict:
        resource = self.get(resource_id)
        return self.create(resource["kind"], name, resource.get("prompt_zh", ""), resource.get("prompt_en", ""),
                           resource["license"], {"parent_id": resource["id"], "source": resource.get("origin"),
                                                 "redistribution_requires_original_license": True})

    def import_definition(self, resource: dict, expected_sha256: str, source_id: str,
                          source_url: str | None = None, author: dict | None = None) -> dict:
        self.validate_resource(resource)
        if resource['kind'] not in {'style', 'layout'} or not source_id or len(source_id) > 200:
            raise ValueError('只能将画风或图型导入个人库')
        canonical = json.dumps(resource, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
        digest = hashlib.sha256(canonical).hexdigest()
        if digest != expected_sha256:
            raise ValueError('定义校验失败，未导入个人库')
        local_id = 'community:' + hashlib.sha256(source_id.encode()).hexdigest()[:24]
        data = self.index()
        existing = next((row for row in data['resources'] if row['id'] == local_id), None)
        if existing and existing.get('sha256') == digest:
            return existing
        item = {key: value for key, value in resource.items() if key not in {'id', 'section', 'path', 'origin'}}
        item.update(id=local_id, section='collected', sha256=digest,
                    origin={'id': source_id, 'url': source_url, 'author': author or resource.get('author')},
                    updated_at=datetime.now(timezone.utc).isoformat())
        data['resources'] = [row for row in data['resources'] if row['id'] != local_id] + [item]
        self.write(data)
        return item

    def export(self, resource_id: str, output: Path | str) -> dict:
        resource = self.get(resource_id)
        if resource["section"] != "owned":
            raise ValueError("收藏不能直接作为自己的原创导出；请检查授权后创建派生副本")
        output = Path(output)
        output.parent.mkdir(parents=True, exist_ok=True)
        manifest = {"schema_version": 1, "resource": resource}
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        return {"path": str(output.resolve()), "sha256": hashlib.sha256(output.read_bytes()).hexdigest()}


class Client:
    def __init__(self):
        profile_path = home() / "community_auth.json"
        if not profile_path.exists():
            raise ValueError("请先使用 community-share 绑定社区账号")
        self.profile = json.loads(profile_path.read_text(encoding="utf-8"))
        base = self.profile.get("base_url", BASE_URL).rstrip("/")
        if base != BASE_URL:
            raise ValueError("社区同步只向 https://handraw-style.com 发送凭据")
        jar = http.cookiejar.LWPCookieJar(str(home() / "community_cookies.txt"))
        if Path(jar.filename).exists():
            jar.load(ignore_discard=True, ignore_expires=False)
        self.opener = urllib.request.build_opener(SameOriginRedirect(), urllib.request.HTTPCookieProcessor(jar))

    def fetch(self, path: str, maximum: int = MAX_ARCHIVE) -> bytes:
        if not path.startswith("/studio/api/") or path.startswith("//") or ".." in path:
            raise ValueError("下载地址不属于本站资源 API")
        headers = {"Accept": "application/json", "X-Requested-With": "XMLHttpRequest",
                   "User-Agent": "HandRawStudio/1.0"}
        if self.profile.get("api_key"):
            headers["Api-Key"] = self.profile["api_key"]
            username = self.profile.get("username", "")
            if username and username.isascii():
                headers["Api-Username"] = username
        if self.profile.get("user_api_key"):
            headers["User-Api-Key"] = self.profile["user_api_key"]
        request = urllib.request.Request(BASE_URL + path, headers=headers)
        with self.opener.open(request, timeout=35) as response:
            if urllib.parse.urlsplit(response.url).netloc != "handraw-style.com":
                raise ValueError("拒绝跨站下载")
            content = response.read(maximum + 1)
        if len(content) > maximum:
            raise ValueError("下载内容超过大小限制")
        return content

    def sync(self, library: Library, resource_id: str | None = None) -> list[dict] | dict:
        data = json.loads(self.fetch("/studio/api/library"))
        resources = [item for item in data['collected'] + data.get('owned', []) + data.get('official', []) if item['kind'] in {'style', 'layout'}]
        if not resource_id:
            return [{key: item.get(key) for key in ("id", "ref", "title", "name", "kind", "version", "collected", "unlocked")} for item in resources]
        resource = next((item for item in resources if item['id'] == resource_id or item.get('ref') == resource_id), None)
        if resource and resource.get('unlocked') and (resource.get('content_url') or resource.get('source') == 'official'):
            url = resource.get('content_url') or '/studio/api/assets/' + urllib.parse.quote(resource['ref'], safe='') + '/content'
            result = json.loads(self.fetch(url))
            return library.import_definition(result['resource'], result['sha256'], resource_id,
                                             BASE_URL + '/studio?view=explore&asset=' + urllib.parse.quote(resource.get('ref', resource_id)), resource.get('author'))
        if not resource or not resource.get("unlocked") or not resource.get("download_url"):
            raise ValueError("资源尚未解锁或不可下载；同步不会自动扣分")
        payload = self.fetch(resource["download_url"])
        with tempfile.TemporaryDirectory() as temporary:
            bundle = Path(temporary) / "resource.zip"
            bundle.write_bytes(payload)
            return library.import_bundle(bundle, resource["sha256"], resource_id,
                                         BASE_URL + "/studio?entry=" + resource_id, resource.get("author"))


class SameOriginRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, new_url):
        parsed = urllib.parse.urlsplit(new_url)
        if parsed.scheme != "https" or parsed.netloc != "handraw-style.com":
            raise ValueError("拒绝向外站重定向社区凭据")
        return super().redirect_request(request, response, code, message, headers, new_url)


def main():
    os.environ.setdefault('HANDRAW_SKILL_ROOT', str(Path(__file__).resolve().parents[3]))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list")
    show = commands.add_parser("show"); show.add_argument("id")
    create = commands.add_parser("create")
    for name in ("kind", "name", "zh", "en", "license"):
        create.add_argument("--" + name, required=True)
    create.add_argument("--example", action="append", default=[])
    update = commands.add_parser("update"); update.add_argument("id")
    for name in ("name", "zh", "en", "license", "version"):
        update.add_argument("--" + name)
    update.add_argument("--example", action="append")
    importing = commands.add_parser("import")
    importing.add_argument("bundle", type=Path)
    importing.add_argument("--sha256", required=True)
    importing.add_argument("--source-id")
    sync = commands.add_parser("sync"); sync.add_argument("--id"); sync.add_argument("--list-only", action="store_true")
    fork = commands.add_parser("fork"); fork.add_argument("id"); fork.add_argument("--name", required=True)
    export = commands.add_parser("export"); export.add_argument("id"); export.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    library = Library(args.root)
    if args.command == "list": result = library.index()
    elif args.command == "show": result = library.get(args.id)
    elif args.command == "create": result = library.create(args.kind, args.name, args.zh, args.en, args.license, examples=args.example)
    elif args.command == "update": result = library.update(args.id, name=args.name, prompt_zh=args.zh,
                                                           prompt_en=args.en, license=args.license,
                                                           version=args.version, examples=args.example)
    elif args.command == "import": result = library.import_bundle(args.bundle, args.sha256, args.source_id)
    elif args.command == "fork": result = library.fork(args.id, args.name)
    elif args.command == "export": result = library.export(args.id, args.output)
    else: result = Client().sync(library, None if args.list_only else args.id)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, zipfile.BadZipFile) as error:
        raise SystemExit(str(error)) from error
