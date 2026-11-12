"""Export ECharts configurations to image formats."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path


def is_echarts_cli_available() -> bool:
    return shutil.which("npx") is not None


def render_echarts_file(
    input_path: str | Path,
    output_path: str | Path,
    *,
    format: str | None = None,
    cli_timeout_seconds: int = 60,
) -> Path:
    """Render an ECharts JSON config file to an image.

    Args:
        input_path: Path to ECharts JSON config file.
        output_path: Output image file path.
        format: Output format (png, jpeg, svg, pdf). Inferred from output_path if None.
        cli_timeout_seconds: Timeout for CLI rendering.

    Returns:
        Path to the rendered output file.
    """
    input_file = Path(input_path)
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    if format is None:
        format = output_file.suffix.lstrip(".").lower()
        if not format:
            format = "png"

    if format not in {"png", "jpeg", "jpg", "svg", "pdf"}:
        raise ValueError(f"Unsupported output format: {format}")

    if format in {"jpeg", "jpg"}:
        format = "jpeg"

    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    config = json.loads(input_file.read_text(encoding="utf-8"))

    html_content = _build_echarts_html(config, format)

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".html", delete=False, encoding="utf-8"
    ) as f:
        f.write(html_content)
        temp_html = Path(f.name)

    try:
        _render_via_puppeteer(temp_html, output_file, format=format, timeout=cli_timeout_seconds)
    except FileNotFoundError:
        if shutil.which("node") is None:
            raise RuntimeError(
                "Node.js is not installed. Please install Node.js to render ECharts images."
            ) from None
        raise
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Rendering timed out after {cli_timeout_seconds} seconds.")
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        stdout = (exc.stdout or "").strip()
        error_msg = stderr or stdout or "Unknown error"
        raise RuntimeError(f"ECharts rendering failed: {error_msg}") from exc
    finally:
        temp_html.unlink(missing_ok=True)

    return output_file


def _build_echarts_html(config: dict, format: str) -> str:
    width = config.get("width", 800)
    height = config.get("height", 600)

    config_json = json.dumps(config, ensure_ascii=False, separators=(",", ":"))

    background_color = config.get("backgroundColor", "#ffffff")

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      background: {background_color};
      width: {width}px;
      height: {height}px;
      overflow: hidden;
    }}
    #chart {{
      width: {width}px;
      height: {height}px;
    }}
  </style>
</head>
<body>
  <div id="chart"></div>
  <script>
    var chart = echarts.init(document.getElementById('chart'), null, {{
      renderer: 'canvas',
      width: {width},
      height: {height}
    }});
    var option = {config_json};
    chart.setOption(option);

    // Export after render completes
    setTimeout(function() {{
      window._echarts_export_format = '{format}';
      window._echarts_export_done = true;
    }}, 500);
  </script>
</body>
</html>"""


def _render_via_puppeteer(
    html_path: Path,
    output_path: Path,
    *,
    format: str,
    timeout: int,
) -> None:
    script = f"""
const puppeteer = require('puppeteer');
const path = require('path');

(async () => {{
  const browser = await puppeteer.launch({{
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  }});
  const page = await browser.newPage();

  const fileUrl = 'file://' + path.resolve('{html_path}');
  await page.goto(fileUrl, {{ waitUntil: 'networkidle0', timeout: {timeout * 1000} }});

  // Wait for chart to render
  await new Promise(r => setTimeout(r, 1000));

  const chart = await page.$('#chart');
  if (!chart) throw new Error('Chart element not found');

  const boundingBox = await chart.boundingBox();

  if ('{format}' === 'svg') {{
    const svg = await page.evaluate(() => {{
      const canvas = document.querySelector('#chart canvas');
      if (!canvas) return null;
      const svgData = new XMLSerializer().serializeToString(canvas);
      return svgData;
    }});
    if (svg) {{
      require('fs').writeFileSync('{output_path}', svg);
    }} else {{
      // Fallback: get SVG directly
      const content = await page.content();
      const svgMatch = content.match(/<svg[^>]*>.*<\\/svg>/s);
      if (svgMatch) {{
        require('fs').writeFileSync('{output_path}', svgMatch[0]);
      }} else {{
        throw new Error('SVG export not supported for this chart type');
      }}
    }}
  }} else {{
    await page.setViewport({{
      width: Math.ceil(boundingBox.width),
      height: Math.ceil(boundingBox.height)
    }});

    await page.evaluate(() => {{
      const chartInst = document.querySelector('#chart canvas');
      if (chartInst && chartInst.style) {{
        chartInst.style.background = 'white';
      }}
    }});

    const screenshotOptions = {{
      path: '{output_path}',
      type: '{format}',
      fullPage: false,
      clip: {{
        x: boundingBox.x,
        y: boundingBox.y,
        width: boundingBox.width,
        height: boundingBox.height
      }}
    }};

    if ('{format}' === 'jpeg' || '{format}' === 'jpg') {{
      screenshotOptions.type = 'jpeg';
      screenshotOptions.quality = 95;
    }}

    await page.screenshot(screenshotOptions);
  }}

  await browser.close();
  process.exit(0);
}})().catch(err => {{
  console.error(err);
  process.exit(1);
}});
"""

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".js", delete=False, encoding="utf-8"
    ) as f:
        f.write(script)
        script_path = Path(f.name)

    try:
        result = subprocess.run(
            ["node", str(script_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            stderr = result.stderr.strip()
            stdout = result.stdout.strip()
            error_msg = stderr or stdout or "Unknown error"
            raise RuntimeError(f"Puppeteer rendering failed: {error_msg}")
    finally:
        script_path.unlink(missing_ok=True)
