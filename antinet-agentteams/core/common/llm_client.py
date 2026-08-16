"""LLMClient：材料智能体的 LLM 在环客户端（零外部依赖，仅用标准库）。

设计原则（对齐 AGENTS.md 第 3 节出域策略与降级铁律）：
- 主链路：本地 NPU 模型 Genie（端口 8910，OpenAI 兼容，无需 key），
  与后端 agents / hermes 使用同一个真实本地大模型。
- 备用链路：我们的 FreeLLM（默认 9000，需 unified API key）。
- 云端/异构部署时，用环境变量把上述任一链路重定向到「可达的 freellm OpenAI 兼容端点」：
    ANTINET_LLM_BASE_URL  -> 主链路端点（优先级最高，覆盖 Genie）
    ANTINET_LLM_MODEL     -> 模型名
    ANTINET_LLM_API_KEY   -> 主链路 Bearer
    FREELLM_BASE_URL      -> 备用 freellm 端点（可指向云端可达地址，而非 localhost）
    FREELLM_API_KEY       -> 我们的 freellm unified key
- 两者皆不可达时返回 None，调用方必须如实降级为规则引擎，
  并在卡片/报告里标注 llm_involved=False（绝不允许静默冒充 LLM 已参与）。

本客户端不写死任何云端默认值；本地不设置环境变量则默认走本机 Genie（8910）。
"""
from __future__ import annotations
import os
import json
import urllib.request
import urllib.error


class LLMClient:
    def __init__(
        self,
        model: str = "qwen2.5vl3b-8380-2.42",
        genie_url: str = "http://127.0.0.1:8910/v1/chat/completions",
        freellm_url: str | None = None,
        freellm_key: str | None = None,
        timeout: int = 120,
    ):
        # —— 环境变量覆盖（云端 / 异构部署统一入口）——
        env_base = os.environ.get("ANTINET_LLM_BASE_URL")       # 主链路 LLM（OpenAI 兼容）
        env_model = os.environ.get("ANTINET_LLM_MODEL")
        env_key = os.environ.get("ANTINET_LLM_API_KEY")         # 主链路 Bearer
        env_freellm_url = os.environ.get("FREELLM_BASE_URL")    # 备用 freellm（可指向可达地址）
        env_freellm_key = os.environ.get("FREELLM_API_KEY")     # 我们的 freellm key

        self.model = env_model or model
        self.genie_url = env_base or genie_url                  # 主链路：云端覆盖 > 本地 Genie
        self.primary_key = env_key                             # 主链路鉴权（云端常需 Bearer）
        self.freellm_url = (
            env_freellm_url or freellm_url or "http://localhost:9000/v1/chat/completions"
        )
        # freellm key 可被 FREELLM_API_KEY 或主链路 ANTINET_LLM_API_KEY 提供
        self.freellm_key = env_freellm_key or env_key or freellm_key
        self.timeout = timeout
        self.used_llm = False        # 本轮是否真的调用了 LLM
        self.endpoint_used: str | None = None

    # ------------------------------------------------------------------
    def health(self) -> bool:
        """快速探活 Genie（本地 NPU 服务）。"""
        try:
            req = urllib.request.Request("http://127.0.0.1:8910/v1/models", method="GET")
            with urllib.request.urlopen(req, timeout=5) as r:
                return r.status == 200
        except Exception:
            return False

    # ------------------------------------------------------------------
    def chat(self, system: str, user: str, max_tokens: int = 512, temperature: float = 0.3) -> str | None:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user})
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        # 1) 主链路 LLM（本地 Genie 或云端覆盖端点 ANTINET_LLM_BASE_URL）
        text = self._post(self.genie_url, payload, self.primary_key)
        if text is not None:
            self.used_llm = True
            self.endpoint_used = self.genie_url
            return text
        # 2) FreeLLMAPI（需 key）
        if self.freellm_key:
            text = self._post(self.freellm_url, payload, self.freellm_key)
            if text is not None:
                self.used_llm = True
                self.endpoint_used = "freellm:9000"
                return text
        return None

    # ------------------------------------------------------------------
    def _post(self, url: str, payload: dict, api_key: str | None) -> str | None:
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                resp = json.loads(r.read().decode("utf-8"))
            return resp["choices"][0]["message"]["content"]
        except Exception:
            return None


def extract_json(text: str) -> dict | None:
    """从模型输出中尽量稳健地抽取第一个 JSON 对象。"""
    if not text:
        return None
    s = text.find("{")
    e = text.rfind("}")
    if s == -1 or e == -1 or e <= s:
        return None
    try:
        return json.loads(text[s : e + 1])
    except Exception:
        return None
