#!/usr/bin/env python3
"""
微信公众号 HTML 文章发布工具

用法:
    python3 publish_html.py \
        --file /path/to/article.html \
        --title "文章标题" \
        --cover /tmp/cover.jpg \
        --author "AICoder" \
        --digest "摘要内容"
"""

import argparse
import os
import sys
import json
import requests
from pathlib import Path
from typing import Optional, Dict, Any

# 账号配置映射
ACCOUNT_ENV_FILES = {
    'tech': 'wechat.env',           # 技术账号（默认）
    'parenting': 'wechat-parenting.env',  # 育儿账号
}

# 加载环境变量
def load_env(account: str = 'tech'):
    """加载指定账号的 wechat.env 文件"""
    env_file = ACCOUNT_ENV_FILES.get(account, 'wechat.env')
    
    # 查找 env 文件
    possible_paths = [
        Path(__file__).parent.parent / env_file,
        Path(__file__).parent.parent.parent / env_file,
        Path.home() / ".openclaw" / env_file,
    ]
    
    for env_path in possible_paths:
        if env_path.exists():
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('export '):
                        line = line[7:]  # 移除 'export '
                    if '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        # 移除引号
                        value = value.strip('"').strip("'")
                        os.environ[key] = value
            print(f"✅ 已加载环境变量: {env_path} (账号: {account})")
            return
    
    print("⚠️ 未找到 wechat.env 文件，尝试使用系统环境变量")

# Token 缓存
_token_cache = {
    'token': None,
    'expires_at': 0
}

def get_access_token() -> str:
    """获取微信 access_token"""
    app_id = os.environ.get('WECHATAPPID') or os.environ.get('WECHAT_APP_ID')
    app_secret = os.environ.get('WECHATAPPSECRET') or os.environ.get('WECHAT_APP_SECRET')
    
    if not app_id or not app_secret:
        raise ValueError("缺少环境变量: WECHATAPPID 或 WECHATAPPSECRET")
    
    # 检查缓存（提前 5 分钟过期）
    import time
    if _token_cache['token'] and time.time() < _token_cache['expires_at'] - 300:
        return _token_cache['token']
    
    # 获取新 token
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={app_id}&secret={app_secret}"
    resp = requests.get(url, timeout=10)
    data = resp.json()
    
    if 'errcode' in data:
        raise Exception(f"获取 access_token 失败: {data['errcode']} - {data['errmsg']}")
    
    # 缓存 token
    _token_cache['token'] = data['access_token']
    _token_cache['expires_at'] = time.time() + data['expires_in']
    
    return data['access_token']

def upload_thumb_image(image_path: str) -> str:
    """上传封面图，返回 thumb_media_id"""
    token = get_access_token()
    
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"封面图不存在: {image_path}")
    
    # 方式1：尝试上传为永久素材
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image"
    
    with open(image_path, 'rb') as f:
        files = {'media': (os.path.basename(image_path), f, 'image/jpeg')}
        resp = requests.post(url, files=files, timeout=30)
    
    data = resp.json()
    
    if 'errcode' in data:
        # 如果永久素材失败，尝试临时素材
        print(f"⚠️ 永久素材上传失败，尝试临时素材: {data.get('errcode')} - {data.get('errmsg')}")
        url = f"https://api.weixin.qq.com/cgi-bin/media/upload?access_token={token}&type=thumb"
        
        with open(image_path, 'rb') as f:
            files = {'media': (os.path.basename(image_path), f, 'image/jpeg')}
            resp = requests.post(url, files=files, timeout=30)
        
        data = resp.json()
        
        if 'errcode' in data:
            raise Exception(f"封面上传失败: {data['errcode']} - {data['errmsg']}")
    
    # 微信 API 返回的 thumb media_id 字段名
    if 'media_id' in data:
        return data['media_id']
    elif 'thumb_media_id' in data:
        return data['thumb_media_id']
    else:
        # 打印完整响应用于调试
        print(f"⚠️ API 响应: {data}")
        raise Exception("封面上传失败：未找到 media_id 字段")

def create_draft(article: Dict[str, Any]) -> str:
    """创建草稿，返回 media_id"""
    token = get_access_token()
    
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
    
    # 过滤掉 None 值
    filtered_article = {k: v for k, v in article.items() if v is not None}
    
    payload = {'articles': [filtered_article]}
    
    # 使用 ensure_ascii=False 避免中文被转义成 Unicode 编码
    headers = {'Content-Type': 'application/json; charset=utf-8'}
    resp = requests.post(url, data=json.dumps(payload, ensure_ascii=False).encode('utf-8'), headers=headers, timeout=30)
    data = resp.json()
    
    if 'errcode' in data:
        raise Exception(f"创建草稿失败: {data['errcode']} - {data['errmsg']}")
    
    return data['media_id']

def download_cover_image(url: str, output_path: str) -> str:
    """下载封面图"""
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    
    with open(output_path, 'wb') as f:
        f.write(resp.content)
    
    print(f"✅ 封面图已下载: {output_path}")
    return output_path

def main():
    parser = argparse.ArgumentParser(description='微信公众号文章发布工具')
    parser.add_argument('--file', required=True, help='HTML 文章文件路径')
    parser.add_argument('--title', required=True, help='文章标题')
    parser.add_argument('--cover', required=True, help='封面图路径')
    parser.add_argument('--author', default='AICoder', help='作者名')
    parser.add_argument('--digest', help='摘要（可选，默认取正文前54字）')
    parser.add_argument('--content-source-url', help='原文链接（可选）')
    parser.add_argument('--account', choices=['tech', 'parenting'], default='tech',
                        help='公众号账号: tech=技术号(默认), parenting=育儿号')
    
    args = parser.parse_args()
    
    # 加载环境变量
    load_env(args.account)
    
    # 读取 HTML 内容
    if not os.path.exists(args.file):
        print(f"❌ 文件不存在: {args.file}")
        sys.exit(1)
    
    with open(args.file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # 验证内容大小（微信限制 2MB）
    content_size = len(html_content.encode('utf-8'))
    if content_size > 2 * 1024 * 1024:
        print(f"❌ 文章内容过大: {content_size / 1024 / 1024:.2f}MB（最大 2MB）")
        sys.exit(1)
    
    print(f"📝 开始发布文章: {args.title}")
    print(f"📄 内容大小: {content_size / 1024:.1f} KB")
    
    # 上传封面图
    print(f"🎨 上传封面图: {args.cover}")
    try:
        thumb_media_id = upload_thumb_image(args.cover)
        print(f"✅ 封面上传成功: {thumb_media_id}")
    except Exception as e:
        print(f"❌ 封面上传失败: {e}")
        sys.exit(1)
    
    # 准备摘要
    if not args.digest:
        # 从 HTML 中提取正文内容作为摘要
        import re
        
        # 1. 只提取 body 或 article 内的内容
        body_match = re.search(r'<(?:body|article)[^>]*>(.*?)</(?:body|article)>', html_content, re.S | re.I)
        content = body_match.group(1) if body_match else html_content
        
        # 2. 移除 style 和 script 标签及其内容
        content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.S | re.I)
        content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.S | re.I)
        
        # 3. 移除所有 HTML 标签
        text = re.sub(r'<[^>]+>', '', content)
        
        # 4. 清理空白字符：多个空白/换行合并为一个空格
        text = re.sub(r'\s+', ' ', text).strip()
        
        # 5. 取前 54 个字符作为摘要
        args.digest = text[:54]
        
        if not args.digest:
            args.digest = args.title  # 如果提取失败，使用标题作为摘要
    
    # 构建文章对象
    article = {
        'title': args.title,
        'author': args.author,
        'content': html_content,
        'digest': args.digest,
        'thumb_media_id': thumb_media_id,
        'need_open_comment': 1,
        'only_fans_can_comment': 0,
    }
    
    if args.content_source_url:
        article['content_source_url'] = args.content_source_url
    
    # 创建草稿
    print("📤 正在创建草稿...")
    try:
        media_id = create_draft(article)
        print(f"\n✅ 发布成功！")
        print(f"   标题: {args.title}")
        print(f"   作者: {args.author}")
        print(f"   草稿ID: {media_id}")
        print(f"\n📌 请登录微信公众号后台 -> 内容与互动 -> 草稿箱 -> 预览并发布")
    except Exception as e:
        print(f"❌ 创建草稿失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
