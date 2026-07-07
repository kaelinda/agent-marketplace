---
name: aliyun-oss-upload
description: "Use when uploading files/attachments to Alibaba Cloud OSS. Covers ossutil CLI, Python SDK (oss2), credential setup, URL generation, and common upload patterns."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [aliyun, oss, upload, storage, cloud, attachment]
    related_skills: []
---

# 阿里云 OSS 文件上传

## Overview

阿里云对象存储 OSS (Object Storage Service) 是海量、安全、低成本、高可靠的云存储服务。本 skill 覆盖通过 **ossutil CLI** 和 **Python SDK (oss2)** 上传文件到 OSS 的完整流程，包括凭证配置、上传策略、URL 生成和常见问题排查。

## When to Use

- 需要上传文件/图片/视频/文档到阿里云 OSS
- 需要为应用生成可访问的文件 URL
- 需要批量上传目录或设置文件访问权限
- 需要在自动化流程中集成 OSS 上传

## 默认配置（用户已验证）

以下是 OSS 配置说明：

**环境变量配置（推荐）：**
```bash
export OSS_AK="your_access_key_id"
export OSS_SK="your_access_key_secret"
export OSS_BUCKET="kaelblog"
export OSS_ENDPOINT="oss-cn-beijing.aliyuncs.com"
export OSS_REGION="华北2（北京）"
```

**快速使用：**
```python
import oss2
import os

# 从环境变量读取 AccessKey
auth = oss2.Auth(os.environ.get("OSS_AK"), os.environ.get("OSS_SK"))
bucket = oss2.Bucket(auth, "https://oss-cn-beijing.aliyuncs.com", "kaelblog")
```
# 上传并获取公开 URL
with open("image.jpg", "rb") as f:
    bucket.put_object("images/image.jpg", f, headers={'Content-Type': 'image/jpeg'})
url = "https://kaelblog.oss-cn-beijing.aliyuncs.com/images/image.jpg"
```

> ⚠️ **Endpoint 必须是 `oss-cn-beijing`（华北2）。** 用 `oss-cn-hangzhou` 会返回 403 `AccessDenied` + "The bucket you are attempting to access must be addressed using the specified endpoint"。这是 2026-06-07 实测确认的：kaelblog bucket 绑定在北京 region，杭州 endpoint 直接拒绝。
>
> 其他 bucket（如 `cherry-studio-zzs`、`kael-hub`、`kael-obsidian` 等）也在同一 AK 下可用，endpoint 均为 `oss-cn-beijing.aliyuncs.com`。

---

## 前置条件（新环境配置）

### 1. 创建 AccessKey

1. 登录 [阿里云控制台](https://ram.console.aliyun.com/) → AccessKey 管理
2. 创建 AccessKey，记录 `AccessKey ID` 和 `AccessKey Secret`
3. **安全建议**：使用 RAM 子账号 + 最小权限策略（`AliyunOSSFullAccess`）

### 2. 创建 Bucket

1. 进入 [OSS 控制台](https://oss.console.aliyun.com/) → 创建 Bucket
2. 记录 Bucket 名称和 Endpoint（如 `oss-cn-hangzhou.aliyuncs.com`）
3. 设置读写权限：`private`（推荐）或 `public-read`

---

## 方法一：ossutil CLI（推荐用于命令行）

### 安装

```bash
# macOS
brew install ossutil

# Linux (x86_64)
curl -o ossutil64 https://gosspublic.alicdn.com/ossutil/1.7.18/ossutil64
chmod +x ossutil64
sudo mv ossutil64 /usr/local/bin/ossutil
```

### 配置凭证

```bash
# 交互式配置（推荐首次使用）
ossutil config

# 按提示输入：
# AccessKey ID:     LTAI5t****
# AccessKey Secret: ****
# Endpoint:         oss-cn-hangzhou.aliyuncs.com
# STSToken:         （留空，使用长期凭证）
```

配置文件位置：`~/.ossutilconfig`

### 环境变量配置（适合 CI/CD）

```bash
export OSS_ACCESS_KEY_ID="LTAI5t****"
export OSS_ACCESS_KEY_SECRET="****"
export OSS_ENDPOINT="oss-cn-hangzhou.aliyuncs.com"
export OSS_BUCKET="my-bucket"
```

### 上传命令

```bash
# 上传单个文件
ossutil cp ./file.pdf oss://my-bucket/files/file.pdf

# 上传并设置 Content-Type
ossutil cp ./image.png oss://my-bucket/images/ --meta "content-type:image/png"

# 上传整个目录（递归）
ossutil cp ./dist/ oss://my-bucket/static/ -r

# 上传并设置为公共读
ossutil cp ./public.html oss://my-bucket/ --acl public-read

# 上传并设置 Cache-Control
ossutil cp ./style.css oss://my-bucket/css/ --meta "cache-control:max-age=86400"

# 覆盖上传（强制）
ossutil cp ./updated.pdf oss://my-bucket/docs/ --update

# 并发上传大文件（分片）
ossutil cp ./big-video.mp4 oss://my-bucket/videos/ --jobs 4 --parallel 3
```

### 查看与管理

```bash
# 列出 Bucket 内文件
ossutil ls oss://my-bucket/path/

# 查看文件详情
ossutil stat oss://my-bucket/file.pdf

# 删除文件
ossutil rm oss://my-bucket/old-file.pdf

# 生成签名 URL（临时访问）
ossutil sign oss://my-bucket/private-file.pdf --timeout 3600
```

---

## 方法二：Python SDK (oss2)

### 安装

```bash
pip install oss2
```

### 基础上传

```python
import oss2
from pathlib import Path

# 认证
auth = oss2.Auth('LTAI5t****', '****')
bucket = oss2.Bucket(auth, 'https://oss-cn-hangzhou.aliyuncs.com', 'my-bucket')

# 上传文件
with open('report.pdf', 'rb') as f:
    result = bucket.put_object('files/report.pdf', f)

print(f"ETag: {result.etag}")
print(f"Status: {result.status}")
```

### 带元数据和 ACL 上传

```python
# 设置 Headers
headers = {
    'Content-Type': 'image/png',
    'Cache-Control': 'max-age=86400',
    'x-oss-object-acl': 'public-read',  # 设置公共读
}

with open('banner.png', 'rb') as f:
    bucket.put_object('images/banner.png', f, headers=headers)
```

### 生成访问 URL

```python
# 公开文件 URL（Bucket 为 public-read 时）
endpoint = 'https://oss-cn-hangzhou.aliyuncs.com'
bucket_name = 'my-bucket'
object_key = 'files/report.pdf'
public_url = f"https://{bucket_name}.oss-cn-hangzhou.aliyuncs.com/{object_key}"
# 或
public_url = f"{endpoint.replace('https://', f'https://{bucket_name}.')}/{object_key}"

# 私有文件签名 URL（限时访问）
signed_url = bucket.sign_url('GET', object_key, 3600)  # 1小时有效
print(signed_url)
```

### 批量上传

```python
from pathlib import Path

upload_dir = Path('./dist')
for file_path in upload_dir.rglob('*'):
    if file_path.is_file():
        object_key = f"static/{file_path.relative_to(upload_dir)}"
        with open(file_path, 'rb') as f:
            bucket.put_object(object_key, f)
        print(f"✓ {object_key}")
```

### 流式上传（适合大文件）

```python
import oss2

# 分片上传大文件
oss2.resumable_upload(
    bucket,
    'videos/large-video.mp4',
    './large-video.mp4',
    store=oss2.ObjectStore(),
    part_size=10 * 1024 * 1024,  # 10MB per part
    num_threads=4,
)
```

### 上传 Bytes / String

```python
import json

# 上传 JSON 数据
data = json.dumps({"key": "value"}, ensure_ascii=False)
bucket.put_object('api/response.json', data.encode('utf-8'))

# 上传内存中的 bytes
bucket.put_object('data/binary.dat', binary_data)
```

---

## 常用上传场景模板

### 场景 1：上传附件并返回可访问 URL

```python
def upload_attachment(file_path: str, bucket, prefix: str = "attachments") -> str:
    """上传文件并返回公共访问 URL"""
    filename = Path(file_path).name
    object_key = f"{prefix}/{filename}"
    
    with open(file_path, 'rb') as f:
        bucket.put_object(object_key, f)
    
    return f"https://{bucket.bucket_name}.oss-cn-hangzhou.aliyuncs.com/{object_key}"
```

### 场景 2：上传临时文件并返回签名 URL

```python
def upload_temp_file(file_path: str, bucket, expire_seconds: int = 7200) -> str:
    """上传私有文件并返回限时签名 URL"""
    filename = Path(file_path).name
    object_key = f"temp/{filename}"
    
    with open(file_path, 'rb') as f:
        bucket.put_object(object_key, f)
    
    return bucket.sign_url('GET', object_key, expire_seconds)
```

### 场景 3：覆盖上传（更新已有文件）

```python
def update_file(file_path: str, object_key: str, bucket) -> bool:
    """覆盖上传指定路径的文件"""
    with open(file_path, 'rb') as f:
        result = bucket.put_object(object_key, f)
    return result.status == 200
```

---

## Endpoint 速查表

| 地域 | Endpoint |
|------|----------|
| 华东1（杭州） | `oss-cn-hangzhou.aliyuncs.com` |
| 华东2（上海） | `oss-cn-shanghai.aliyuncs.com` |
| 华北2（北京） | `oss-cn-beijing.aliyuncs.com` |
| 华南1（深圳） | `oss-cn-shenzhen.aliyuncs.com` |
| 中国（香港） | `oss-cn-hongkong.aliyuncs.com` |
| 新加坡 | `oss-ap-southeast-1.aliyuncs.com` |
| 美国（硅谷） | `oss-us-west-1.aliyuncs.com` |
| 欧洲（法兰克福） | `oss-eu-central-1.aliyuncs.com` |

---

## Common Pitfalls

1. **Endpoint 缺少协议前缀**。oss2 SDK 需要完整 URL `https://oss-cn-xxx.aliyuncs.com`，ossutil CLI 只需 `oss-cn-xxx.aliyuncs.com`。

2. **Bucket 权限误设为 public-read-write**。除非特殊需求，始终使用 `private` + 签名 URL，避免数据泄露。

3. **中文文件名乱码**。上传前用 `urllib.parse.quote()` 对 object_key 中的中文部分编码：
   ```python
   from urllib.parse import quote
   object_key = f"files/{quote('报告.pdf')}"
   ```

4. **上传大文件未用分片**。>100MB 文件建议用 `oss2.resumable_upload()` 或 `ossutil cp --jobs`，避免超时。

5. **AccessKey 泄露**。不要在代码中硬编码 AK，使用环境变量或阿里云 STS 临时凭证。

6. **签名 URL 时区问题**。oss2 签名 URL 默认使用 UTC 时间，确保服务器时区正确，否则链接可能提前失效。

7. **Content-Type 缺失**。浏览器访问时若 Content-Type 不正确会触发下载而非预览。上传时显式设置 `content-type`。

8. **ossutil config 与环境变量冲突**。环境变量优先级高于 `~/.ossutilconfig`，CI/CD 中注意清理冲突变量。

---

## Verification Checklist

- [ ] AccessKey 已配置（环境变量或 ossutil config）
- [ ] Endpoint 与 Bucket 地域匹配
- [ ] 上传命令执行成功（无 403/404 错误）
- [ ] 文件可通过 URL 访问（curl 测试）
- [ ] 权限设置正确（私有文件用签名 URL）
- [ ] 大文件使用分片上传
- [ ] 敏感信息未硬编码在代码中

---

## One-Shot Recipes

### 快速上传并分享

```bash
# 1. 配置
export OSS_ACCESS_KEY_ID="LTAI5t****"
export OSS_ACCESS_KEY_SECRET="****"

# 2. 上传
ossutil cp ./resume.pdf oss://my-bucket/docs/resume.pdf

# 3. 生成签名链接
ossutil sign oss://my-bucket/docs/resume.pdf --timeout 86400
```

### Python 一键上传函数

```python
import oss2
from pathlib import Path

def quick_upload(file_path: str, object_key: str, 
                 ak: str, sk: str, 
                 endpoint: str, bucket_name: str,
                 public: bool = False) -> str:
    """一键上传并返回 URL"""
    auth = oss2.Auth(ak, sk)
    bucket = oss2.Bucket(auth, f'https://{endpoint}', bucket_name)
    
    headers = {}
    if public:
        headers['x-oss-object-acl'] = 'public-read'
    
    with open(file_path, 'rb') as f:
        bucket.put_object(object_key, f, headers=headers)
    
    if public:
        return f"https://{bucket_name}.{endpoint}/{object_key}"
    return bucket.sign_url('GET', object_key, 3600)
```
