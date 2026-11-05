#!/usr/bin/env python3
"""Loopback-only share preview with a real, user-clicked publish button."""
from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from conversation_share import (CommunityAPI, DEFAULT_AUTH, PACKAGE_ROOT,
                                image_record, load_key, publish_draft, shared_prompt, validate_work, write_json)

CACHE = PACKAGE_ROOT / "client/cache/conversation-share-ui"
SERVICE = "handraw-conversation-share"
INSTANCE = hashlib.sha256(str(PACKAGE_ROOT.resolve()).encode()).hexdigest()[:16]
DEFAULT_PORT = 18763
TOKEN = re.compile(r"[a-f0-9]{32}")

PAGE = r'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>分享到手绘风</title><style>
:root{color-scheme:light;font-family:system-ui,"Microsoft YaHei",sans-serif;color:#172240;background:#f8f5ed}
*{box-sizing:border-box}body{margin:0}main{max-width:960px;margin:auto;padding:36px 24px 120px}.brand{font-size:14px;color:#3958b6;font-weight:700;letter-spacing:.08em}h1{font-size:32px;line-height:1.3;margin:12px 0 8px}p{color:#667085;line-height:1.7}.meta{display:flex;gap:10px;flex-wrap:wrap;margin:20px 0}.pill{background:#eceffc;color:#29428f;padding:7px 12px;border-radius:24px;font-size:13px}.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}.image-card{padding:8px;background:white;border:1px solid #e6e3da;border-radius:14px}.image-card img{display:block;width:100%;height:auto;border-radius:8px}.image-card span{display:block;color:#798095;font-size:12px;margin:7px 3px 0}.card{background:white;border:1px solid #e6e3da;border-radius:16px;padding:22px;margin:24px 0}h2{font-size:18px;margin:0 0 12px}pre{white-space:pre-wrap;overflow-wrap:anywhere;line-height:1.8;font:14px/1.8 system-ui,"Microsoft YaHei",sans-serif;margin:0;color:#35415e}.bar{position:fixed;bottom:0;left:0;right:0;background:#fffdf8f5;border-top:1px solid #e6e3da;padding:16px 24px}.bar-inner{max-width:912px;margin:auto;display:flex;align-items:center;justify-content:space-between;gap:20px}button,.post-link{border:0;border-radius:12px;padding:14px 24px;background:#f36b27;color:white;font-weight:700;font-size:16px;cursor:pointer;text-decoration:none;white-space:nowrap}button:disabled{opacity:.5;cursor:default}#status{font-size:14px;line-height:1.6;color:#536078}#error{color:#b53131;white-space:pre-wrap}#post-link{display:none}#status.success{color:#237245}@media(max-width:650px){main{padding:24px 16px 150px}h1{font-size:26px}.grid{grid-template-columns:repeat(2,minmax(0,1fr))}.bar-inner{align-items:stretch;flex-direction:column;gap:10px}.bar{padding:12px 16px}button{text-align:center}}
.page-header{display:flex;justify-content:space-between;align-items:center;gap:14px;flex-wrap:wrap}.header-links{display:flex;align-items:center;gap:18px;flex-wrap:wrap}.header-links a{color:#3958b6;text-decoration:none;font-size:13px;white-space:nowrap}.header-links a:hover{text-decoration:underline}.header-links a:focus-visible{outline:2px solid #3958b6;outline-offset:4px;border-radius:2px}
</style></head><body><main><header class="page-header"><div class="brand">手绘风 · 作品分享</div><nav class="header-links" aria-label="手绘风网站链接"><a href="https://handraw-style.com/signup" target="_blank" rel="noopener noreferrer">注册</a><a href="https://handraw-style.com/" target="_blank" rel="noopener noreferrer">网站首页</a><a href="https://handraw-style.com/my/preferences/account" target="_blank" rel="noopener noreferrer" title="登录后在账号设置中生成个人 API Key">获取API KEY</a></nav></header>
<h1 id="title">正在打开分享草稿…</h1><p>确认图片与最初的指令，点击下方按钮分享到作品广场。</p>
<div class="meta"><span class="pill" id="count"></span><span class="pill" id="account"></span><span class="pill">作品广场</span></div>
<div class="grid" id="images"></div><section class="card"><h2>分享提示词</h2><pre id="original"></pre></section>
<p>分享图片、原始指令及实际使用的画风和图型编号，账号凭据保存在本机。</p><p id="error" role="alert"></p></main>
<div class="bar"><div class="bar-inner"><div id="status" role="status">正在读取草稿，尚未发布。</div><button id="publish" disabled>分享到作品广场</button><a id="post-link" class="post-link" target="_blank" rel="noopener noreferrer">查看广场作品 ↗</a></div></div>
<script>
const token=location.pathname.split('/').filter(Boolean)[1];
const endpoint='/api/share/'+encodeURIComponent(token);
const btn=document.getElementById('publish'), status=document.getElementById('status'), error=document.getElementById('error');
let busy=false;
function showPublished(data){btn.style.display='none';const a=document.getElementById('post-link');a.href=data.work_url||data.legacy_forum_url;a.style.display='inline-block';if(data.work_url){status.textContent='已分享到作品广场，重复打开本页不会再次发布。';status.className='success';}else{a.textContent='查看原论坛帖 ↗';status.textContent='这是旧版论坛发布记录，作品广场分享请使用新草稿。';}}
async function load(initial=false){const r=await fetch(endpoint,{cache:'no-store'});const d=await r.json();if(!r.ok)throw new Error(d.error||'无法读取草稿');
if(initial){document.getElementById('title').textContent=d.title;document.getElementById('original').textContent=d.shared_prompt;document.getElementById('count').textContent=d.images.length+' 张图片';document.getElementById('account').textContent=d.account_name?'发布账号 @'+d.account_name:'尚未绑定网站账号';
const grid=document.getElementById('images');for(const [i,im] of d.images.entries()){const c=document.createElement('div');c.className='image-card';const img=document.createElement('img');img.src=im.src;img.alt='作品 '+(i+1);const label=document.createElement('span');label.textContent='图片 '+(i+1);c.append(img,label);grid.append(c);}}
if(d.status==='published'){showPublished(d);}else if(d.status==='publication_uncertain'||d.status==='publishing'){status.textContent=d.status==='publishing'?'正在提交作品…':'上次发布结果未确认，请先核对作品广场，避免重复发布。';btn.disabled=true;}else if(d.draft_error){status.textContent=d.draft_error;btn.disabled=true;}else if(d.status==='uploading'){status.textContent='正在上传图片 '+d.uploaded_count+'/'+d.images.length+'…';btn.disabled=true;}else if(!busy){status.textContent='草稿已就绪，点击后将公开分享到作品广场。';btn.disabled=false;}return d;}
btn.addEventListener('click',async()=>{if(busy)return;busy=true;btn.disabled=true;btn.textContent='正在发布…';error.textContent='';status.textContent='正在连接账号并上传图片…';
const timer=setInterval(()=>load().catch(()=>{}),1500);
try{const r=await fetch(endpoint+'/publish',{method:'POST',headers:{'Content-Type':'application/json','X-Handraw-Share':token},body:'{}'});const d=await r.json();if(!r.ok)throw new Error(d.error||'发布失败');await load();if(!d.verified)status.textContent='作品广场已返回作品链接；内容与关联回读暂未全部确认。';}
catch(e){error.textContent=e.message;}finally{clearInterval(timer);busy=false;btn.textContent='分享到作品广场';await load().catch(()=>{});}});
load(true).catch(e=>{error.textContent=e.message;status.textContent='分享草稿暂时不可用。';});
</script></body></html>'''


def registry_path(cache, token):
    if not TOKEN.fullmatch(token):
        raise ValueError("分享链接无效。")
    return Path(cache) / "pages" / (token + ".json")


def register_draft(path, cache=CACHE):
    path = Path(path).resolve(strict=True)
    draft = json.loads(path.read_text(encoding="utf-8"))
    token = draft.get("share_page_token")
    if not token:
        token = uuid.uuid4().hex
        draft["share_page_token"] = token
        write_json(path, draft)
    registration = registry_path(cache, token)
    if registration.exists():
        existing = json.loads(registration.read_text(encoding="utf-8"))
        if Path(existing["draft"]).resolve() != path:
            raise ValueError("分享链接已绑定其他草稿。")
    write_json(registration, {"draft": str(path)})
    return token


class ShareServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, cache=CACHE, api_factory=None):
        self.cache = Path(cache)
        self.api_factory = api_factory or (lambda: CommunityAPI(load_key()))
        super().__init__(address, ShareHandler)


class ShareHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # Capability URLs and raw instructions are not written to access logs.

    @property
    def origin(self):
        return f"http://127.0.0.1:{self.server.server_port}"

    def send(self, status, body, content_type="application/json; charset=utf-8"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False).encode("utf-8")
        elif isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; img-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self'; base-uri 'none'; form-action 'self'")
        self.end_headers()
        self.wfile.write(body)

    def valid_host(self):
        return self.headers.get("Host") == f"127.0.0.1:{self.server.server_port}"

    def draft(self, token):
        registration = json.loads(registry_path(self.server.cache, token).read_text(encoding="utf-8"))
        path = Path(registration["draft"])
        return path, json.loads(path.read_text(encoding="utf-8"))

    def do_GET(self):
        if not self.valid_host():
            return self.send(403, {"error": "Host不匹配。"})
        path = self.path.split("?", 1)[0]
        if path == "/health":
            return self.send(200, {"service": SERVICE, "instance": INSTANCE, "version": 9})
        page = re.fullmatch(r"/share/([a-f0-9]{32})/?", path)
        info = re.fullmatch(r"/api/share/([a-f0-9]{32})", path)
        image = re.fullmatch(r"/share/([a-f0-9]{32})/image/(\d+)", path)
        try:
            if page:
                self.draft(page[1])
                return self.send(200, PAGE, "text/html; charset=utf-8")
            if info:
                _, draft = self.draft(info[1])
                account = draft.get("account", {}).get("username")
                if not account and DEFAULT_AUTH.exists():
                    account = json.loads(DEFAULT_AUTH.read_text(encoding="utf-8")).get("username")
                draft_error = None
                if draft["status"] != "published":
                    try:
                        validate_work(draft)
                    except ValueError as error:
                        draft_error = str(error)
                receipt = draft.get("receipt") or {}
                is_work = receipt.get("destination") == "work_square"
                return self.send(200, {"title": draft["title"], "original_request": draft["original_request"],
                    "shared_prompt": shared_prompt(draft),
                    "resolved_style_ids": draft.get("resolved_style_ids"),
                    "resolved_layout_ids": draft.get("resolved_layout_ids"),
                    "images": [{"src": f"/share/{info[1]}/image/{i}", "width": item["width"], "height": item["height"]}
                               for i, item in enumerate(draft["images"])],
                    "status": draft["status"], "uploaded_count": len(draft["uploads"]),
                    "work_url": receipt.get("url") if is_work else None,
                    "legacy_forum_url": receipt.get("url") if not is_work else None,
                    "draft_error": draft_error, "account_name": account})
            if image:
                _, draft = self.draft(image[1])
                record = draft["images"][int(image[2])]
                if image_record(record["path"])["sha256"] != record["sha256"]:
                    raise ValueError("图片已更改。")
                content_type = mimetypes.guess_type(record["path"])[0] or "image/png"
                return self.send(200, Path(record["path"]).read_bytes(), content_type)
            return self.send(404, {"error": "页面不存在。"})
        except (OSError, ValueError, KeyError, IndexError):
            return self.send(404, {"error": "分享草稿或图片不可用。"})

    def do_POST(self):
        if not self.valid_host() or self.headers.get("Origin") != self.origin:
            return self.send(403, {"error": "只允许本地分享页面提交。"})
        match = re.fullmatch(r"/api/share/([a-f0-9]{32})/publish", self.path)
        if not match or self.headers.get("X-Handraw-Share") != match[1]:
            return self.send(403, {"error": "分享操作无效。"})
        if self.headers.get("Content-Type") != "application/json":
            return self.send(415, {"error": "请求格式无效。"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 <= length <= 1024:
                return self.send(413, {"error": "请求过大。"})
            self.rfile.read(length)
            path, _ = self.draft(match[1])
            receipt = publish_draft(path, self.server.api_factory())
            return self.send(200, receipt)
        except (OSError, ValueError, RuntimeError) as error:
            return self.send(409, {"error": str(error)})


def ensure_share_link(path, port=DEFAULT_PORT, cache=CACHE):
    token = register_draft(path, cache)
    origin = f"http://127.0.0.1:{port}"
    def healthy():
        try:
            with urllib.request.urlopen(origin + "/health", timeout=1) as response:
                data = json.load(response)
                return data.get("service") == SERVICE and data.get("instance") == INSTANCE
        except (OSError, ValueError):
            return False
    if not healthy():
        Path(cache).mkdir(parents=True, exist_ok=True)
        with (Path(cache) / "server.log").open("ab") as log:
            flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            subprocess.Popen([sys.executable, "-X", "utf8", str(Path(__file__).resolve()),
                "serve", "--port", str(port), "--cache", str(cache)],
                stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                creationflags=flags, start_new_session=os.name != "nt")
        for _ in range(40):
            if healthy():
                break
            time.sleep(.1)
        else:
            raise RuntimeError("本地分享页面未启动，请检查服务日志或端口占用。")
    return origin + "/share/" + token


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    link = sub.add_parser("link")
    link.add_argument("--draft", required=True)
    link.add_argument("--port", type=int, default=DEFAULT_PORT)
    serve = sub.add_parser("serve")
    serve.add_argument("--port", type=int, default=DEFAULT_PORT)
    serve.add_argument("--cache", type=Path, default=CACHE)
    args = parser.parse_args()
    if args.command == "link":
        print(ensure_share_link(args.draft, args.port))
    else:
        ShareServer(("127.0.0.1", args.port), args.cache).serve_forever()


if __name__ == "__main__":
    main()
