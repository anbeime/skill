#!/usr/bin/env python3
"""
抖音视频信息提取脚本

功能：从抖音视频URL提取视频的详细信息
输入：抖音视频URL
输出：JSON格式的视频信息（标题、描述、文案等）

使用方法：
1. 首选方案：使用抖音API或网页抓取
2. 备选方案：使用yt-dlp
"""

import sys
import json
import argparse
import re
import requests
from urllib.parse import urlparse, parse_qs

try:
    from yt_dlp import YoutubeDL
    YTDLP_AVAILABLE = True
except ImportError:
    YTDLP_AVAILABLE = False


def extract_video_id_from_url(url: str) -> str:
    """
    从抖音URL中提取视频ID

    Args:
        url: 抖音视频URL

    Returns:
        str: 视频ID
    """
    # 支持多种抖音URL格式
    patterns = [
        r'/video/(\d+)',  # https://www.douyin.com/video/7300000000000000000
        r'/share/video/(\d+)',  # https://www.douyin.com/share/video/7300000000000000000
        r'item_ids=(\d+)',  # 参数中包含item_ids
        r'aweme_id=(\d+)',  # 参数中包含aweme_id
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None


def extract_douyin_web(url: str) -> dict:
    """
    通过网页抓取提取抖音视频信息

    Args:
        url: 抖音视频URL

    Returns:
        dict: 包含视频信息的字典
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.douyin.com/',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }

    try:
        # 获取视频ID
        video_id = extract_video_id_from_url(url)
        if not video_id:
            return {
                'success': False,
                'data': {},
                'message': '无法从URL中提取视频ID'
            }

        # 尝试通过网页抓取
        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        response.raise_for_status()

        # 尝试从HTML中提取数据
        html_content = response.text

        # 尝试匹配脚本中的数据
        # 抖音视频信息通常在script标签中的__INITIAL_STATE__或类似变量中
        script_pattern = r'<script>.*?window\.__INITIAL_STATE__\s*=\s*({.*?});.*?</script>'
        match = re.search(script_pattern, html_content, re.DOTALL | re.MULTILINE)

        if match:
            try:
                data_str = match.group(1)
                data = json.loads(data_str)

                # 尝试从数据中提取视频信息
                if 'videoData' in data:
                    video_data = data['videoData']
                elif 'aweme' in data and 'detail' in data['aweme']:
                    video_data = data['aweme']['detail']
                else:
                    # 尝试其他路径
                    video_data = None

                if video_data:
                    # 提取标题和描述
                    title = video_data.get('desc', '')
                    description = video_data.get('desc', '')

                    # 提取文案（如果有字幕）
                    subtitles = []
                    if 'text' in video_data:
                        subtitles = video_data['text']

                    # 提取作者信息
                    author_info = video_data.get('author', {})
                    uploader = author_info.get('nickname', '')
                    uploader_id = author_info.get('uid', '')

                    # 提取统计数据
                    statistics = video_data.get('statistics', {})
                    like_count = statistics.get('digg_count', 0)
                    comment_count = statistics.get('comment_count', 0)
                    share_count = statistics.get('share_count', 0)
                    play_count = statistics.get('play_count', 0)

                    result = {
                        'title': title,
                        'description': description,
                        'uploader': uploader,
                        'uploader_id': uploader_id,
                        'view_count': play_count,
                        'like_count': like_count,
                        'comment_count': comment_count,
                        'duration': video_data.get('duration', 0) // 1000 if video_data.get('duration') else 0,  # 毫秒转秒
                        'tags': [],
                        'categories': [],
                        'subtitles': subtitles,
                    }

                    return {
                        'success': True,
                        'data': result,
                        'message': '视频信息提取成功（网页抓取）'
                    }
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                pass

        # 如果上面的方法失败，尝试简单的HTML解析提取
        # 从meta标签中提取
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'lxml')

        # 提取描述
        desc = ''
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            desc = meta_desc.get('content', '')

        # 提取标题
        title = ''
        meta_title = soup.find('meta', attrs={'property': 'og:title'})
        if meta_title:
            title = meta_title.get('content', '')

        if desc or title:
            result = {
                'title': title or desc[:50],
                'description': desc,
                'uploader': '',
                'uploader_id': '',
                'view_count': 0,
                'like_count': 0,
                'comment_count': 0,
                'duration': 0,
                'tags': [],
                'categories': [],
                'subtitles': desc.split('\n') if desc else [],
            }

            return {
                'success': True,
                'data': result,
                'message': '视频信息提取成功（HTML解析）'
            }

        return {
            'success': False,
            'data': {},
            'message': '无法从网页中提取视频信息'
        }

    except Exception as e:
        return {
            'success': False,
            'data': {},
            'message': f'网页抓取失败: {str(e)}'
        }


def extract_douyin_ytdlp(url: str) -> dict:
    """
    通过yt-dlp提取抖音视频信息

    Args:
        url: 抖音视频URL

    Returns:
        dict: 包含视频信息的字典
    """
    if not YTDLP_AVAILABLE:
        return {
            'success': False,
            'data': {},
            'message': 'yt-dlp未安装'
        }

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitlesformat': 'json',
        'extract_flat': False,
        'nocheckcertificate': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'referer': 'https://www.douyin.com/',
        'ignoreerrors': True,
        'socket_timeout': 30,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            if not info:
                return {
                    'success': False,
                    'data': {},
                    'message': '无法获取视频信息'
                }

            result = {
                'title': info.get('title') or info.get('alt_title') or '',
                'description': info.get('description') or '',
                'uploader': info.get('uploader') or info.get('channel') or '',
                'uploader_id': info.get('uploader_id') or '',
                'view_count': info.get('view_count') or 0,
                'like_count': info.get('like_count') or 0,
                'comment_count': info.get('comment_count') or 0,
                'duration': info.get('duration') or 0,
                'tags': info.get('tags') or [],
                'categories': info.get('categories') or [],
            }

            # 提取字幕
            subtitles = []
            if result['description']:
                desc_text = result['description']
                desc_clean = re.sub(r'#\S+', '', desc_text)
                desc_clean = re.sub(r'https?://\S+', '', desc_clean)
                desc_clean = desc_clean.strip()
                if desc_clean:
                    subtitles.append(desc_clean)

            # 尝试从字幕文件提取
            if 'subtitles' in info and info['subtitles']:
                for lang, sub_list in info['subtitles'].items():
                    if sub_list:
                        try:
                            sub_url = sub_list[0].get('url', '')
                            if sub_url:
                                response = requests.get(sub_url, timeout=10, headers={
                                    'User-Agent': ydl_opts['user_agent'],
                                    'Referer': ydl_opts['referer']
                                })
                                if response.status_code == 200:
                                    sub_data = response.json()
                                    if 'events' in sub_data:
                                        sub_texts = []
                                        for event in sub_data['events']:
                                            if 'segs' in event:
                                                text = ''.join([seg.get('utf8', '') for seg in event['segs']])
                                                if text.strip():
                                                    sub_texts.append(text.strip())
                                        if sub_texts:
                                            subtitles = ' '.join(sub_texts)
                                            break
                        except Exception:
                            pass
                        if subtitles and isinstance(subtitles, str):
                            break

            result['subtitles'] = subtitles

            return {
                'success': True,
                'data': result,
                'message': '视频信息提取成功（yt-dlp）'
            }

    except Exception as e:
        return {
            'success': False,
            'data': {},
            'message': f'yt-dlp提取失败: {str(e)}'
        }


def extract_douyin_video(url: str) -> dict:
    """
    提取抖音视频信息（主函数，尝试多种方法）

    Args:
        url: 抖音视频URL

    Returns:
        dict: 包含视频信息的字典
    """
    # 验证URL
    if not url or 'douyin.com' not in url.lower():
        return {
            'success': False,
            'data': {},
            'message': '请提供有效的抖音视频链接'
        }

    # 方法1：网页抓取（首选，成功率较高）
    result = extract_douyin_web(url)
    if result['success']:
        return result

    # 方法2：yt-dlp（备选）
    result = extract_douyin_ytdlp(url)
    if result['success']:
        return result

    # 都失败
    return {
        'success': False,
        'data': {},
        'message': '无法提取视频信息。抖音平台有访问限制，建议：1) 使用其他视频链接；2) 直接复制视频文案提供给智能体进行分析'
    }


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='提取抖音视频信息')
    parser.add_argument('url', help='抖音视频URL')
    parser.add_argument('--output', '-o', help='输出文件路径（可选）', default=None)

    args = parser.parse_args()

    # 提取视频信息
    result = extract_douyin_video(args.url)

    # 输出结果
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"结果已保存到: {args.output}")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))

    # 返回状态码
    sys.exit(0 if result['success'] else 1)


if __name__ == '__main__':
    main()
