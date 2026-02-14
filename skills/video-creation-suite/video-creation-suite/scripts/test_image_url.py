#!/usr/bin/env python3
"""
测试单个图片URL解析
"""

import re
import requests


coze_url = "https://s.coze.cn/image/w8FwHY3qC50/"

# 发送请求获取HTML
response = requests.get(coze_url, timeout=30)
html = response.text

print("=" * 80)
print("HTML内容:")
print("=" * 80)
print(html)
print("=" * 80)
print()

# 尝试提取图片URL
patterns = [
    r'https://p\d+-coze-space-sign\.byteimg\.com/[^"\s<>]+~tplv-jv50ctfexx-compress-v2:q90\.jpeg[^"\s<>]*',
    r'https://p\d+-coze-space-sign\.byteimg\.com/[^"\s<>]+~tplv-jv50ctfexx-compress-v2:q90\.webp[^"\s<>]*',
    r'https://[^"\s<>]+\.(?:jpg|jpeg|png|webp)[^"\s<>]*',
    r'href="(https://[^"]+)"',
]

print("尝试提取图片URL:")
for i, pattern in enumerate(patterns, 1):
    match = re.search(pattern, html)
    if match:
        url = match.group(0)
        url = url.replace('&amp;', '&')
        url = url.replace('&lt;', '<')
        url = url.replace('&gt;', '>')
        url = url.replace('&quot;', '"')
        print(f"  模式 {i}: {url}")
    else:
        print(f"  模式 {i}: 未匹配")

print()
print("所有http/https链接:")
all_urls = re.findall(r'https?://[^\s<>"]+', html)
for url in all_urls[:10]:
    print(f"  {url}")
