"""知易平台 HTTP 客户端（零外部依赖，仅标准库）。

该平台即本机 Genie 生态的「知识中枢」，提供：
- PDF / 文本解析与灌库：/api/knowledge/import/text , /api/pdf/extract/*
- 真实检索（向量+关键词）：/api/knowledge/search（keyword 字段）

它在本机以 :8000 提供，等价于「MinerU（解析）+ Qdrant（向量检索）」的本地真身。
本客户端只做薄封装：成功返回结构化数据，失败（不可达/异常）一律返回 None，
由调用方决定如何诚实回退 —— 绝不在失败时用本地结果冒充平台结果。
"""
from __future__ import annotations
import os
import json
import urllib.request
import urllib.error


class ZhijiaClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000", timeout: int = 40):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.available = False  # 最近一次 health 结果

    # ------------------------------------------------------------------
    def health(self) -> bool:
        try:
            req = urllib.request.Request(f"{self.base_url}/api/pdf/status", method="GET")
            with urllib.request.urlopen(req, timeout=5) as r:
                ok = r.status == 200
                self.available = ok
                return ok
        except Exception:
            self.available = False
            return False

    # ------------------------------------------------------------------
    def import_text(self, content: str, auto_save: bool = True) -> dict | None:
        """把文本灌入平台知识库（真实解析 + 向量化）。返回平台响应或 None。"""
        if not content or not content.strip():
            return None
        payload = {"content": content, "auto_save": auto_save, "preview_only": False}
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                f"{self.base_url}/api/knowledge/import/text",
                data=data, headers={"Content-Type": "application/json"}, method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception:
            return None

    # ------------------------------------------------------------------
    def search(self, keyword: str, limit: int = 5) -> list[dict] | None:
        """真实检索（平台知识库）。返回命中卡片列表或 None。"""
        if not keyword or not keyword.strip():
            return None
        payload = {"keyword": keyword, "limit": limit}
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                f"{self.base_url}/api/knowledge/search",
                data=data, headers={"Content-Type": "application/json"}, method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                out = json.loads(r.read().decode("utf-8"))
            if isinstance(out, list):
                return out
            # 有些版本把结果包在 {"results":[...]}
            return out.get("results", []) if isinstance(out, dict) else []
        except Exception:
            return None

    # ------------------------------------------------------------------
    def extract_pdf_text(self, pdf_path: str) -> str | None:
        """真实 PDF 文本抽取（multipart）。仅当存在真实 PDF 时使用。"""
        if not os.path.exists(pdf_path):
            return None
        boundary = "----antinetzhijia"
        try:
            with open(pdf_path, "rb") as f:
                file_bytes = f.read()
            body = (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="file"; filename="{os.path.basename(pdf_path)}"\r\n'
                f"Content-Type: application/pdf\r\n\r\n"
            ).encode("utf-8") + file_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")
            req = urllib.request.Request(
                f"{self.base_url}/api/pdf/extract/text",
                data=body,
                headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                out = json.loads(r.read().decode("utf-8"))
            # 兼容不同返回结构，尽力取出文本
            if isinstance(out, dict):
                for k in ("text", "extracted_text", "content"):
                    if isinstance(out.get(k), str) and out[k].strip():
                        return out[k]
            return None
        except Exception:
            return None
