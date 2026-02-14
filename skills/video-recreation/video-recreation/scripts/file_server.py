#!/usr/bin/env python3
"""
HTTP文件服务器
提供简单的文件下载服务,支持大文件
"""

import os
import sys
import argparse
import http.server
import socketserver
from pathlib import Path
from urllib.parse import unquote


class FileHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """自定义HTTP请求处理器,添加文件列表功能"""

    def __init__(self, *args, directory=None, **kwargs):
        if directory:
            self.directory = directory
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """处理GET请求"""
        # 解码路径
        path = unquote(self.path)

        # 根路径返回文件列表
        if path == '/' or path == '/index.html':
            self.send_file_list()
        else:
            # 其他路径提供文件下载
            super().do_GET()

    def send_file_list(self):
        """发送文件列表HTML页面"""
        try:
            # 获取目录中的文件
            files = []
            for item in os.listdir(self.directory):
                item_path = os.path.join(self.directory, item)
                if os.path.isfile(item_path):
                    size = os.path.getsize(item_path)
                    files.append({
                        'name': item,
                        'size': self.format_size(size)
                    })

            # 按名称排序
            files.sort(key=lambda x: x['name'])

            # 生成HTML
            html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>文件下载服务器</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #007bff;
            padding-bottom: 10px;
        }}
        .info {{
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        th {{
            background-color: #007bff;
            color: white;
            text-align: left;
            padding: 12px;
            font-weight: bold;
        }}
        td {{
            padding: 12px;
            border-bottom: 1px solid #ddd;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        a.download-link {{
            display: inline-block;
            padding: 8px 16px;
            background-color: #28a745;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            font-size: 14px;
        }}
        a.download-link:hover {{
            background-color: #218838;
        }}
        .size {{
            color: #666;
            font-weight: bold;
        }}
        .file-icon {{
            margin-right: 8px;
        }}
    </style>
</head>
<body>
    <h1>📁 文件下载服务器</h1>

    <div class="info">
        <strong>服务器信息:</strong><br>
        目录: {self.directory}<br>
        文件数: {len(files)}<br>
    </div>

    <table>
        <thead>
            <tr>
                <th>文件名</th>
                <th>大小</th>
                <th>操作</th>
            </tr>
        </thead>
        <tbody>
"""

            for file_info in files:
                html += f"""
            <tr>
                <td><span class="file-icon">📄</span>{file_info['name']}</td>
                <td><span class="size">{file_info['size']}</span></td>
                <td>
                    <a href="/{file_info['name']}" class="download-link" download>⬇️ 下载</a>
                </td>
            </tr>
"""

            html += """
        </tbody>
    </table>

    <div style="margin-top: 20px; color: #666;">
        <small>提示: 点击"下载"按钮即可下载文件。大文件可能需要较长时间。</small>
    </div>
</body>
</html>
"""

            # 发送响应
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))

        except Exception as e:
            self.send_error(500, f"服务器错误: {str(e)}")

    @staticmethod
    def format_size(size_bytes):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"


def start_server(directory='.', port=8000):
    """
    启动HTTP文件服务器

    参数:
        directory: 要共享的目录
        port: 端口号
    """
    # 获取绝对路径
    directory = os.path.abspath(directory)

    # 检查目录是否存在
    if not os.path.isdir(directory):
        print(f"❌ 错误: 目录不存在 - {directory}")
        sys.exit(1)

    # 创建服务器
    handler = FileHTTPRequestHandler
    handler.directory = directory

    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"\n{'='*60}")
        print(f"📁 文件下载服务器已启动")
        print(f"{'='*60}")
        print(f"📂 共享目录: {directory}")
        print(f"🌐 访问地址: http://localhost:{port}")
        print(f"📡 本地访问: http://127.0.0.1:{port}")
        print(f"{'='*60}\n")

        print(f"按 Ctrl+C 停止服务器\n")

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n✅ 服务器已停止")


def main():
    parser = argparse.ArgumentParser(description='HTTP文件下载服务器')
    parser.add_argument('--directory', '-d', type=str, default='.',
                       help='要共享的目录(默认当前目录)')
    parser.add_argument('--port', '-p', type=int, default=8000,
                       help='端口号(默认8000)')

    args = parser.parse_args()

    # 启动服务器
    start_server(
        directory=args.directory,
        port=args.port
    )


if __name__ == '__main__':
    main()
