#!/usr/bin/env python3
"""
文件下载服务
为生成的文件提供 HTTP 下载服务
"""

import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Optional


class FileDownloadHandler(SimpleHTTPRequestHandler):
    """文件下载处理器"""

    def __init__(self, *args, directory: str = None, **kwargs):
        self.directory = directory
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """处理 GET 请求"""
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(self._generate_index_page().encode('utf-8'))
        else:
            # 获取文件路径
            file_path = self.translate_path(self.path)

            # 检查文件是否存在
            if os.path.exists(file_path) and os.path.isfile(file_path):
                # 获取文件名
                filename = os.path.basename(file_path)

                # 设置下载头
                self.send_response(200)
                self.send_header('Content-type', 'application/octet-stream')
                self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
                self.end_headers()

                # 发送文件
                with open(file_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404, 'File Not Found')

    def _generate_index_page(self):
        """生成索引页面"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>视频创作套件 - 文件下载</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                }
                h1 {
                    color: #333;
                    border-bottom: 2px solid #007bff;
                    padding-bottom: 10px;
                }
                .file-list {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                    gap: 15px;
                    margin-top: 20px;
                }
                .file-item {
                    background-color: white;
                    padding: 15px;
                    border-radius: 5px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    transition: transform 0.2s;
                }
                .file-item:hover {
                    transform: translateY(-3px);
                    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
                }
                .file-name {
                    font-weight: bold;
                    color: #007bff;
                    margin-bottom: 5px;
                }
                .file-info {
                    font-size: 12px;
                    color: #666;
                }
                .download-btn {
                    display: inline-block;
                    margin-top: 10px;
                    padding: 8px 16px;
                    background-color: #007bff;
                    color: white;
                    text-decoration: none;
                    border-radius: 4px;
                    font-size: 14px;
                }
                .download-btn:hover {
                    background-color: #0056b3;
                }
                .section {
                    margin: 30px 0;
                }
                .section-title {
                    font-size: 20px;
                    color: #333;
                    margin-bottom: 15px;
                    padding-left: 10px;
                    border-left: 4px solid #007bff;
                }
            </style>
        </head>
        <body>
            <h1>🎬 视频创作套件 - 文件下载</h1>
            <p>所有生成的文件都可以从这里下载</p>
        """

        # 添加各个目录的文件
        directories = {
            'output/final': '📹 最终视频',
            'output/images': '🖼️ 生成图片',
            'output/audio': '🎵 音频文件',
            'output/subtitles': '📝 字幕文件',
            'drafts': '📋 脚本草稿'
        }

        for dir_path, title in directories.items():
            full_path = os.path.join(self.directory, dir_path)
            if os.path.exists(full_path):
                files = self._get_files_in_directory(full_path)
                if files:
                    html += f'<div class="section">'
                    html += f'<h2 class="section-title">{title}</h2>'
                    html += f'<div class="file-list">'
                    for file_info in files:
                        html += f'''
                        <div class="file-item">
                            <div class="file-name">{file_info['name']}</div>
                            <div class="file-info">
                                大小: {file_info['size']}<br>
                                修改时间: {file_info['mtime']}
                            </div>
                            <a href="{file_info['url']}" class="download-btn">下载</a>
                        </div>
                        '''
                    html += f'</div></div>'

        html += """
        </body>
        </html>
        """

        return html

    def _get_files_in_directory(self, directory: str):
        """获取目录中的所有文件"""
        files = []
        try:
            for filename in sorted(os.listdir(directory)):
                file_path = os.path.join(directory, filename)
                if os.path.isfile(file_path):
                    # 获取文件信息
                    size = os.path.getsize(file_path)
                    mtime = os.path.getmtime(file_path)

                    # 格式化大小
                    if size < 1024:
                        size_str = f"{size} B"
                    elif size < 1024 * 1024:
                        size_str = f"{size / 1024:.1f} KB"
                    elif size < 1024 * 1024 * 1024:
                        size_str = f"{size / (1024 * 1024):.1f} MB"
                    else:
                        size_str = f"{size / (1024 * 1024 * 1024):.1f} GB"

                    # 格式化时间
                    import time
                    mtime_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mtime))

                    # 生成 URL
                    rel_path = os.path.relpath(file_path, self.directory)
                    url = f"/{rel_path.replace(os.sep, '/')}"

                    files.append({
                        'name': filename,
                        'size': size_str,
                        'mtime': mtime_str,
                        'url': url
                    })
        except Exception as e:
            print(f"读取目录失败: {directory}, 错误: {e}")

        return files

    def log_message(self, format, *args):
        """禁用默认日志"""
        pass


def start_file_server(
    directory: str = "./output",
    host: str = "0.0.0.0",
    port: int = 8080
) -> None:
    """
    启动文件下载服务

    参数:
        directory: 文件目录
        host: 主机地址
        port: 端口号
    """
    # 确保目录存在
    os.makedirs(directory, exist_ok=True)

    # 切换到目标目录
    os.chdir(directory)

    # 创建自定义处理器
    handler = lambda *args, **kwargs: FileDownloadHandler(*args, directory=directory, **kwargs)

    # 创建服务器
    server = HTTPServer((host, port), handler)

    print(f"\n{'='*60}")
    print(f"📡 文件下载服务已启动")
    print(f"{'='*60}")
    print(f"📁 文件目录: {os.path.abspath(directory)}")
    print(f"🌐 访问地址: http://{host}:{port}")
    print(f"{'='*60}")
    print(f"\n按 Ctrl+C 停止服务\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print(f"\n\n🛑 服务已停止")
        server.shutdown()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="文件下载服务")
    parser.add_argument("--directory", default="./output", help="文件目录")
    parser.add_argument("--host", default="0.0.0.0", help="主机地址")
    parser.add_argument("--port", type=int, default=8080, help="端口号")

    args = parser.parse_args()

    start_file_server(
        directory=args.directory,
        host=args.host,
        port=args.port
    )
