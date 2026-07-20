"""Build and render Mermaid flowcharts."""

from __future__ import annotations

import base64
import json
import re
import shutil
import subprocess
import zlib
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "_", value.strip())
    normalized = normalized.strip("_")
    return normalized or "node"


def _escape_mermaid_text(value: str) -> str:
    return value.replace('"', "'").replace("\n", "<br/>")


@dataclass(slots=True)
class FlowStep:
    """Single step in a Mermaid flowchart."""

    text: str
    node_id: str | None = None
    shape: str = "rect"
    metadata: dict[str, str] = field(default_factory=dict)

    def resolved_node_id(self, index: int) -> str:
        if self.node_id:
            return self.node_id
        return f"step_{index}_{_slugify(self.text)}"


class MermaidFlowchart:
    """Composable Mermaid flowchart builder."""

    _SHAPE_TEMPLATES = {
        "rect": '[{label}]',
        "round": '({label})',
        "stadium": '([{label}])',
        "subroutine": '[[{label}]]',
        "cylindrical": '[( {label} )]',
        "circle": '(({label}))',
        "diamond": '{{{label}}}',
        "hexagon": '{{{{{label}}}}}',
        "parallelogram": '[/ {label} /]',
    }

    def __init__(
        self,
        title: str,
        direction: str = "TD",
        class_definitions: Iterable[str] | None = None,
    ) -> None:
        self.title = title
        self.direction = direction
        self.class_definitions = list(class_definitions or [])
        self.steps: list[FlowStep] = []
        self.links: list[tuple[str, str, str | None]] = []

    def add_step(self, text: str, *, node_id: str | None = None, shape: str = "rect") -> FlowStep:
        step = FlowStep(text=text, node_id=node_id, shape=shape)
        self.steps.append(step)
        return step

    def add_link(self, source_id: str, target_id: str, label: str | None = None) -> None:
        self.links.append((source_id, target_id, label))

    @classmethod
    def from_steps(
        cls,
        title: str,
        steps: Iterable[str],
        *,
        direction: str = "TD",
        first_shape: str = "round",
        last_shape: str = "stadium",
    ) -> "MermaidFlowchart":
        flowchart = cls(title=title, direction=direction)
        step_items = [step for step in steps if step.strip()]
        for index, step_text in enumerate(step_items):
            if index == 0:
                shape = first_shape
            elif index == len(step_items) - 1:
                shape = last_shape
            else:
                shape = "rect"
            flowchart.add_step(step_text, shape=shape)
        return flowchart

    def to_mermaid(self) -> str:
        lines = [
            "---",
            f"title: {self.title}",
            "---",
            f"flowchart {self.direction}",
        ]

        resolved_steps: list[tuple[str, FlowStep]] = []
        for index, step in enumerate(self.steps, start=1):
            node_id = step.resolved_node_id(index)
            label = _escape_mermaid_text(step.text)
            template = self._SHAPE_TEMPLATES.get(step.shape, self._SHAPE_TEMPLATES["rect"])
            lines.append(f"    {node_id}{template.format(label=label)}")
            resolved_steps.append((node_id, step))

        if self.links:
            for source_id, target_id, label in self.links:
                connector = f' -->|{_escape_mermaid_text(label)}| ' if label else " --> "
                lines.append(f"    {source_id}{connector}{target_id}")
        else:
            for (source_id, _), (target_id, _) in zip(resolved_steps, resolved_steps[1:]):
                lines.append(f"    {source_id} --> {target_id}")

        lines.extend(f"    {class_definition}" for class_definition in self.class_definitions)
        return "\n".join(lines) + "\n"

    def write(self, output_path: str | Path) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_mermaid(), encoding="utf-8")
        return path


def render_mermaid_file(
    input_path: str | Path,
    output_path: str | Path,
    *,
    theme: str = "default",
    background_color: str = "white",
    scale: int = 2,
    width: int | None = None,
    height: int | None = None,
    cli_timeout_seconds: int = 45,
    prefer_remote: bool = False,
) -> Path:
    input_file = Path(input_path)
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    diagram_text = input_file.read_text(encoding="utf-8")

    if prefer_remote:
        _render_via_mermaid_ink(
            diagram_text,
            output_file,
            theme=theme,
            background_color=background_color,
            scale=scale,
            width=width,
            height=height,
        )
        return output_file

    if shutil.which("npx") is None:
        _render_via_mermaid_ink(
            diagram_text,
            output_file,
            theme=theme,
            background_color=background_color,
            scale=scale,
            width=width,
            height=height,
        )
        return output_file

    config = {
        "theme": theme,
        "flowchart": {"curve": "basis"},
        "fontFamily": "PingFang SC, Hiragino Sans GB, Microsoft YaHei, sans-serif",
    }
    config_path = output_file.with_suffix(".mermaid-config.json")
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    command = [
        "npx",
        "-y",
        "@mermaid-js/mermaid-cli",
        "-i",
        str(input_file),
        "-o",
        str(output_file),
        "-t",
        theme,
        "-b",
        background_color,
        "-s",
        str(scale),
        "-c",
        str(config_path),
    ]
    if width is not None:
        command.extend(["-w", str(width)])
    if height is not None:
        command.extend(["-H", str(height)])

    try:
        subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=cli_timeout_seconds,
        )
    except FileNotFoundError as exc:
        _render_via_mermaid_ink(
            diagram_text,
            output_file,
            theme=theme,
            background_color=background_color,
            scale=scale,
            width=width,
            height=height,
        )
        return output_file
    except subprocess.TimeoutExpired:
        _render_via_mermaid_ink(
            diagram_text,
            output_file,
            theme=theme,
            background_color=background_color,
            scale=scale,
            width=width,
            height=height,
        )
        return output_file
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        stdout = (exc.stdout or "").strip()
        local_error = stderr or stdout or "未知错误"
        try:
            _render_via_mermaid_ink(
                diagram_text,
                output_file,
                theme=theme,
                background_color=background_color,
                scale=scale,
                width=width,
                height=height,
            )
            return output_file
        except RuntimeError as remote_exc:
            raise RuntimeError(f"Mermaid 导出失败。本地错误: {local_error}；远程错误: {remote_exc}") from exc
    finally:
        config_path.unlink(missing_ok=True)

    return output_file


def _render_via_mermaid_ink(
    diagram_text: str,
    output_file: Path,
    *,
    theme: str,
    background_color: str,
    scale: int,
    width: int | None,
    height: int | None,
) -> None:
    extension = output_file.suffix.lower().lstrip(".")
    if extension not in {"png", "svg", "pdf"}:
        raise RuntimeError(f"远程渲染暂不支持输出格式: {output_file.suffix or '<none>'}")

    payload = json.dumps(
        {"code": diagram_text, "mermaid": {"theme": theme}},
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    encoded = "pako:" + urllib.parse.quote(
        base64.urlsafe_b64encode(zlib.compress(payload, 9)).decode("ascii").rstrip("="),
        safe=":_-",
    )

    if extension == "svg":
        endpoint = "svg"
        query_params: dict[str, str] = {}
    elif extension == "png":
        endpoint = "img"
        query_params = {"type": "png"}
    else:
        endpoint = "pdf"
        query_params = {"fit": ""}

    if background_color:
        query_params["bgColor"] = f"!{background_color}" if background_color.isalpha() else background_color
    if width is not None:
        query_params["width"] = str(width)
    if height is not None:
        query_params["height"] = str(height)
    if width is not None or height is not None:
        query_params["scale"] = str(max(1, min(scale, 3)))

    query_string = urllib.parse.urlencode(query_params, doseq=False)
    url = f"https://mermaid.ink/{endpoint}/{encoded}"
    if query_string:
        url = f"{url}?{query_string}"

    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = response.read()
    except urllib.error.URLError as exc:
        raise RuntimeError(f"远程渲染服务不可用: {exc}") from exc

    output_file.write_bytes(payload)
