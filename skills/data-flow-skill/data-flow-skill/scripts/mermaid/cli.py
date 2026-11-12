"""CLI for generating and exporting Mermaid flowcharts."""

from __future__ import annotations

import argparse

try:
    from .flowchart import MermaidFlowchart, render_mermaid_file
    from .echarts_export import render_echarts_file
except ImportError:
    from flowchart import MermaidFlowchart, render_mermaid_file
    from echarts_export import render_echarts_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate Mermaid flowcharts and export images.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build", help="Generate a Mermaid flowchart from ordered steps.")
    build_parser.add_argument("--title", required=True, help="Chart title.")
    build_parser.add_argument("--step", action="append", required=True, help="Ordered step text. Repeat this flag.")
    build_parser.add_argument("--output", required=True, help="Output .mmd file path.")
    build_parser.add_argument("--direction", default="TD", help="Mermaid direction, e.g. TD or LR.")

    render_parser = subparsers.add_parser("render", help="Render a Mermaid file to an image or PDF.")
    render_parser.add_argument("--input", required=True, help="Input .mmd file path.")
    render_parser.add_argument("--output", required=True, help="Output file path, e.g. .png/.svg/.pdf.")
    render_parser.add_argument("--theme", default="default", help="Mermaid theme.")
    render_parser.add_argument("--background", default="white", help="Background color.")
    render_parser.add_argument("--scale", type=int, default=2, help="Render scale.")
    render_parser.add_argument("--width", type=int, help="Optional canvas width.")
    render_parser.add_argument("--height", type=int, help="Optional canvas height.")

    export_parser = subparsers.add_parser("export", help="Generate a Mermaid file and immediately render it.")
    export_parser.add_argument("--title", required=True, help="Chart title.")
    export_parser.add_argument("--step", action="append", required=True, help="Ordered step text. Repeat this flag.")
    export_parser.add_argument("--mmd-output", required=True, help="Output .mmd file path.")
    export_parser.add_argument("--image-output", required=True, help="Rendered output path.")
    export_parser.add_argument("--direction", default="TD", help="Mermaid direction, e.g. TD or LR.")
    export_parser.add_argument("--theme", default="default", help="Mermaid theme.")
    export_parser.add_argument("--background", default="white", help="Background color.")
    export_parser.add_argument("--scale", type=int, default=2, help="Render scale.")
    export_parser.add_argument("--width", type=int, help="Optional canvas width.")
    export_parser.add_argument("--height", type=int, help="Optional canvas height.")

    echarts_parser = subparsers.add_parser("echarts", help="Render an ECharts JSON config to an image.")
    echarts_parser.add_argument("--input", required=True, help="Input ECharts JSON config file path.")
    echarts_parser.add_argument("--output", required=True, help="Output image file path.")
    echarts_parser.add_argument(
        "--format",
        choices=["png", "jpeg", "svg", "pdf"],
        help="Output format. Inferred from output path if not specified.",
    )
    echarts_parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Rendering timeout in seconds (default: 60).",
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "build":
        flowchart = MermaidFlowchart.from_steps(args.title, args.step, direction=args.direction)
        path = flowchart.write(args.output)
        print(path)
        return 0

    if args.command == "render":
        path = render_mermaid_file(
            args.input,
            args.output,
            theme=args.theme,
            background_color=args.background,
            scale=args.scale,
            width=args.width,
            height=args.height,
        )
        print(path)
        return 0

    if args.command == "export":
        flowchart = MermaidFlowchart.from_steps(args.title, args.step, direction=args.direction)
        mmd_path = flowchart.write(args.mmd_output)
        image_path = render_mermaid_file(
            mmd_path,
            args.image_output,
            theme=args.theme,
            background_color=args.background,
            scale=args.scale,
            width=args.width,
            height=args.height,
        )
        print(image_path)
        return 0

    if args.command == "echarts":
        path = render_echarts_file(
            args.input,
            args.output,
            format=args.format,
            cli_timeout_seconds=args.timeout,
        )
        print(path)
        return 0

    parser.error("Unsupported command.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
