#!/usr/bin/env python3
"""
视频下载工具 - 基于yt-dlp
功能：下载视频、提取视频元数据、下载缩略图
用途：配合爆款解析铲屎官进行视频链接解析反推
"""

import os
import sys
import json
import argparse
from typing import Dict, Optional, Any
from pathlib import Path

try:
    import yt_dlp
except ImportError:
    print("错误：未安装yt-dlp库")
    print("请运行：pip install yt-dlp>=2024.1.0")
    sys.exit(1)


class VideoDownloaderError(Exception):
    """视频下载异常"""
    pass


class VideoDownloader:
    """视频下载器 - 基于yt-dlp"""

    def __init__(self, output_dir: str = "./downloads"):
        """
        初始化视频下载器

        Args:
            output_dir: 下载输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def download_video(
        self,
        url: str,
        format: str = "best",
        download_thumbnail: bool = True
    ) -> Dict[str, Any]:
        """
        下载视频及元数据

        Args:
            url: 视频URL
            format: 视频格式（best/bestvideo+bestaudio等）
            download_thumbnail: 是否下载缩略图

        Returns:
            包含视频信息、文件路径、元数据的字典

        Raises:
            VideoDownloaderError: 下载失败
        """
        # 配置yt-dlp选项
        ydl_opts = {
            'format': format,
            'outtmpl': str(self.output_dir / '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'writeinfojson': True,  # 写入视频信息JSON
            'writesubtitles': False,  # 不下载字幕
            'writethumbnail': download_thumbnail,  # 下载缩略图
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # 提取视频信息
                info = ydl.extract_info(url, download=True)

                # 构建返回结果
                result = {
                    'success': True,
                    'url': url,
                    'video_info': self._extract_video_info(info),
                    'files': self._get_file_paths(info),
                    'metadata': info
                }

                print(f"✓ 视频下载成功: {info['title']}")
                return result

        except yt_dlp.utils.DownloadError as e:
            raise VideoDownloaderError(f"下载失败: {str(e)}")
        except Exception as e:
            raise VideoDownloaderError(f"未知错误: {str(e)}")

    def get_video_info(self, url: str) -> Dict[str, Any]:
        """
        仅获取视频信息，不下载

        Args:
            url: 视频URL

        Returns:
            视频信息字典

        Raises:
            VideoDownloaderError: 获取失败
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                result = {
                    'success': True,
                    'url': url,
                    'video_info': self._extract_video_info(info),
                    'metadata': info
                }

                print(f"✓ 视频信息获取成功: {info['title']}")
                return result

        except Exception as e:
            raise VideoDownloaderError(f"获取视频信息失败: {str(e)}")

    def _extract_video_info(self, info: Dict) -> Dict[str, Any]:
        """
        提取关键视频信息

        Args:
            info: yt-dlp返回的完整信息字典

        Returns:
            提取后的关键信息
        """
        return {
            'title': info.get('title', '未知标题'),
            'uploader': info.get('uploader', '未知作者'),
            'channel_id': info.get('channel_id', ''),
            'duration': info.get('duration', 0),
            'view_count': info.get('view_count', 0),
            'like_count': info.get('like_count', 0),
            'comment_count': info.get('comment_count', 0),
            'upload_date': info.get('upload_date', ''),
            'description': info.get('description', ''),
            'tags': info.get('tags', []),
            'webpage_url': info.get('webpage_url', url),
            'thumbnail': info.get('thumbnail', ''),
            'ext': info.get('ext', ''),
            'resolution': f"{info.get('width', 0)}x{info.get('height', 0)}" if info.get('width') else '',
            'filesize': info.get('filesize', 0),
            'fps': info.get('fps', 0),
        }

    def _get_file_paths(self, info: Dict) -> Dict[str, str]:
        """
        获取下载文件的路径

        Args:
            info: yt-dlp返回的完整信息字典

        Returns:
            文件路径字典
        """
        files = {}

        # 视频文件路径
        video_filename = ydl.prepare_filename(info)
        if os.path.exists(video_filename):
            files['video'] = video_filename

        # 信息JSON文件路径
        info_json_filename = video_filename.replace(info['ext'], 'info.json')
        if os.path.exists(info_json_filename):
            files['info_json'] = info_json_filename

        # 缩略图文件路径
        if info.get('thumbnail'):
            # yt-dlp会自动下载缩略图并保存
            thumbnail_extensions = ['.jpg', '.webp', '.png']
            for ext in thumbnail_extensions:
                thumbnail_filename = video_filename.replace(info['ext'], ext)
                if os.path.exists(thumbnail_filename):
                    files['thumbnail'] = thumbnail_filename
                    break

        return files

    def download_playlist(
        self,
        url: str,
        max_videos: int = 10
    ) -> Dict[str, Any]:
        """
        下载播放列表中的视频

        Args:
            url: 播放列表URL
            max_videos: 最大下载视频数

        Returns:
            下载结果字典

        Raises:
            VideoDownloaderError: 下载失败
        """
        ydl_opts = {
            'format': 'best',
            'outtmpl': str(self.output_dir / '%(playlist_index)s_%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'writeinfojson': True,
            'playlistend': max_videos,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

                result = {
                    'success': True,
                    'url': url,
                    'playlist_title': info.get('title', '未知播放列表'),
                    'playlist_count': info.get('playlist_count', 0),
                    'downloaded_count': len(info.get('entries', [])),
                    'videos': []
                }

                # 提取每个视频的信息
                for entry in info.get('entries', []):
                    if entry:
                        video_info = self._extract_video_info(entry)
                        result['videos'].append(video_info)

                print(f"✓ 播放列表下载成功: {result['downloaded_count']}/{result['playlist_count']}")
                return result

        except Exception as e:
            raise VideoDownloaderError(f"播放列表下载失败: {str(e)}")


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description="视频下载工具 - 基于yt-dlp")

    subparsers = parser.add_subparsers(dest="command", help="命令")

    # 下载视频命令
    download_parser = subparsers.add_parser("download", help="下载视频")
    download_parser.add_argument("url", help="视频URL")
    download_parser.add_argument("--format", default="best", help="视频格式")
    download_parser.add_argument("--output", default="./downloads", help="输出目录")
    download_parser.add_argument("--no-thumbnail", action="store_true", help="不下载缩略图")

    # 获取信息命令
    info_parser = subparsers.add_parser("info", help="获取视频信息")
    info_parser.add_argument("url", help="视频URL")

    # 下载播放列表命令
    playlist_parser = subparsers.add_parser("playlist", help="下载播放列表")
    playlist_parser.add_argument("url", help="播放列表URL")
    playlist_parser.add_argument("--output", default="./downloads", help="输出目录")
    playlist_parser.add_argument("--max", type=int, default=10, help="最大下载数")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        downloader = VideoDownloader(output_dir=args.output)

        if args.command == "download":
            result = downloader.download_video(
                url=args.url,
                format=args.format,
                download_thumbnail=not args.no_thumbnail
            )
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif args.command == "info":
            result = downloader.get_video_info(url=args.url)
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif args.command == "playlist":
            result = downloader.download_playlist(
                url=args.url,
                max_videos=args.max
            )
            print(json.dumps(result, indent=2, ensure_ascii=False))

    except VideoDownloaderError as e:
        print(f"错误: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
