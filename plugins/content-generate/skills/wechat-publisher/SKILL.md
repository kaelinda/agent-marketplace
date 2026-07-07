---
name: wechat-publisher
description: >
  微信公众号草稿发布。当用户说"发到公众号"、"发布到微信公众号"、"发草稿到公众号"、
  "把这篇文章发到公众号"时使用。支持 Markdown / HTML 两种输入，自动上传封面图与正文图片，
  创建公众号草稿（不直接群发）。多账号支持（--account tech/parenting）。
---

# wechat-publisher：微信公众号草稿发布

把 Markdown 或 HTML 文章一键发布到**微信公众号草稿箱**（创建草稿，不会自动群发，需登录后台预览后发布）。支持多套排版主题、封面图上传、正文图片自动上传到微信 CDN、多账号切换。

> 路径约定：下文中的 `<skill_dir>` 会被 Claude Code 自动替换为本 skill 的安装目录
> （`plugins/content-generate/skills/wechat-publisher`）。直接在终端运行时，请把
> `<skill_dir>` 替换为实际路径。

---

## 前置准备（首次使用必读）

本 skill 依赖 Node.js 与（可选）Python 环境，并需要你自己的微信公众号凭证。

### 1. 安装依赖

```bash
cd "<skill_dir>"
npm install        # Node.js 发布工具依赖
# 可选：Python 发布工具依赖
pip install requests
```

### 2. 配置微信公众号凭证

复制凭证模板并填入你自己的 AppID / AppSecret：

```bash
cp "<skill_dir>/.env.example" "<skill_dir>/.env"
# 编辑 <skill_dir>/.env，填入：
#   WECHAT_APP_ID=你的AppID
#   WECHAT_APP_SECRET=你的AppSecret
```

**多账号场景**（可选）：若需在多个公众号间切换，改用 `wechat.env` / `wechat-parenting.env`
（参考 `<skill_dir>/wechat.env.example`），发布时通过 `--account tech|parenting` 选择。

### 3. 配置 IP 白名单

在 [微信公众平台](https://mp.weixin.qq.com/) → 设置与开发 → 基本配置 → IP 白名单 中，
添加运行本 skill 的机器出口 IP。否则 `getAccessToken` 会返回 40164。

> 获取 AppID/AppSecret：登录 mp.weixin.qq.com → 开发 → 基本配置。
> 本 skill **不会**上传你的凭证到任何第三方服务，凭证仅在本机 `.env` 中读取。

---

## 核心规范

### 封面图规范
- **尺寸：** 900×383 (2.35:1)
- **格式：** JPG/PNG
- **大小：** 建议 < 2MB

**获取方式：**

**方式1：从 Unsplash 下载（推荐，符合主题）**
```bash
curl -L -o /tmp/cover.jpg "https://images.unsplash.com/photo-图片ID?w=900&h=383&fit=crop"
```

**方式2：使用 Picsum 随机图**
```bash
curl -L -o /tmp/cover.jpg "https://picsum.photos/900/383"
```

**常用主题图片：**
| 主题 | Unsplash 关键词 |
|------|----------------|
| 技术编程 | photo-1555066931-4365d14bab8c |
| AI/机器学习 | photo-1677442136019-21780ecad995 |
| 商业金融 | photo-1460925895917-afdab827c52f |
| 生活情感 | photo-1506905925346-21bda4d32df4 |

### HTML 文章结构规范

**标准模板：**

```html
<section>
 <!-- 引言/摘要框 -->
 <section style="padding: 16px; background: #f5f5f5; border-radius: 8px; margin: 20px 0;">
   <p style="line-height: 1.8; color: #333; font-size: 15px; margin: 0;">引言/摘要内容...</p>
 </section>

 <!-- 正文 -->
 <section style="margin: 28px 0;">
   <h2 style="font-size: 18px; color: #2c3e50; border-left: 4px solid #3498db; padding-left: 12px;">小标题</h2>
   <p style="line-height: 1.8; color: #333; font-size: 15px; margin-top: 12px;">正文内容...</p>
 </section>

 <!-- 文末署名 -->
 <section style="margin-top: 30px; padding-top: 15px; border-top: 1px solid #eee;">
   <p style="font-size: 12px; color: #999; text-align: center;">作者：AICoder</p>
 </section>
</section>
```

**样式规范：**
- 正文行高：1.8
- 正文颜色：#333
- 正文字号：15px
- 小标题字号：18px
- 小标题颜色：#2c3e50
- 小标题左边框：4px solid #3498db

### 写作风格（去除 AI 味）

| 禁用 ❌ | 推荐 ✅ |
|--------|--------|
| "不是……而是……" | 直接说"它是……" |
| "首先、其次、最后" | 自然段落过渡 |
| 超过5条的整齐列表 | 用独立段落描述 |
| "综上所述"结尾 | 结尾直接收，不套路 |
| 大量 emoji 🦞 | 少用 emoji |

**AI 味识别清单：**
- [ ] 是否有"不是……而是……"句式
- [ ] 是否有"首先、其次、最后"三段式
- [ ] 是否有超过5条的整齐列表
- [ ] 是否以"综上所述"或"总而言之"结尾
- [ ] 是否过度使用 emoji

---

## 发布方式

### 方式1：Markdown 转 HTML（推荐）

**优势：**
- 支持 Markdown 语法
- 自动转换主题样式
- 图片自动上传到微信 CDN

**命令：**

```bash
# 准备封面图
curl -L -o /tmp/cover.jpg "https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=900&h=383&fit=crop"

# 发布（Markdown 文件）
node "<skill_dir>/src/cli.js" publish \
  --title "文章标题" \
  --markdown /tmp/article.md \
  --cover /tmp/cover.jpg \
  --author "AICoder" \
  --theme reader
```

**可用主题：**
- `reader`：暖色调沉浸阅读（默认）
- `codefine`：深色代码风格
- `ocean`：海蓝色调专业沉稳（推荐，紧凑）
- `chatex`：聊天消息风格

**默认推荐：** 使用 Python 发布工具时，采用紧凑排版（margin:6px），适合公众号阅读。

### 方式2：直接发布 HTML

**优势：**
- 完全控制 HTML 结构
- 适合精细排版
- Python 脚本更稳定

**命令：**

```bash
# 准备封面图
curl -L -o /tmp/cover.jpg "https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=900&h=383&fit=crop"

# 发布（HTML 文件）
python3 "<skill_dir>/scripts/publish_html.py" \
  --file /tmp/article.html \
  --title "文章标题" \
  --cover /tmp/cover.jpg \
  --author "AICoder" \
  --digest "摘要内容"
```

**参数说明：**
- `--file`：HTML 文章文件路径（必填）
- `--title`：文章标题（必填）
- `--cover`：封面图路径（必填）
- `--author`：作者名（默认：AICoder）
- `--digest`：摘要（可选，默认取正文前54字）
- `--account`：账号选择（默认 `tech`，可选 `parenting`，对应不同的 `wechat*.env`）

---

## 完整示例

### 示例：发布一篇文章

```bash
# 1. 准备封面图
curl -L -o /tmp/cover.jpg "https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=900&h=383&fit=crop"

# 2. 准备内容（Markdown 或 HTML）
# 方式A：Markdown 文件
cat > /tmp/article.md << 'EOF'
# 文章标题

> 来源：xxx
> 作者：xxx

## 引言
引言内容...

## 正文
正文内容...
EOF

# 方式B：HTML 文件
cat > /tmp/article.html << 'EOF'
<section>
 <section style="padding: 16px; background: #f5f5f5; border-radius: 8px; margin: 20px 0;">
   <p style="line-height: 1.8; color: #333; font-size: 15px; margin: 0;">引言内容...</p>
 </section>

 <section style="margin: 28px 0;">
   <h2 style="font-size: 18px; color: #2c3e50; border-left: 4px solid #3498db; padding-left: 12px;">标题</h2>
   <p style="line-height: 1.8; color: #333; font-size: 15px; margin-top: 12px;">正文内容...</p>
 </section>

 <section style="margin-top: 30px; padding-top: 15px; border-top: 1px solid #eee;">
   <p style="font-size: 12px; color: #999; text-align: center;">作者：AICoder</p>
 </section>
</section>
EOF

# 3. 发布（二选一）
# 使用 Node.js
node "<skill_dir>/src/cli.js" publish \
  --title "文章标题" \
  --markdown /tmp/article.md \
  --cover /tmp/cover.jpg \
  --theme reader

# 或使用 Python
python3 "<skill_dir>/scripts/publish_html.py" \
  --file /tmp/article.html \
  --title "文章标题" \
  --cover /tmp/cover.jpg \
  --author "AICoder"
```

**先测试连接是否正常：**

```bash
node "<skill_dir>/src/cli.js" test
```

---

## 配置文件

**凭证文件位置：** `<skill_dir>/.env`（从 `.env.example` 复制并填入你自己的凭证）

**`.env` 内容示例：**
```bash
WECHAT_APP_ID=wx_your_app_id
WECHAT_APP_SECRET=你的AppSecret
```

**IP 白名单：**
需要在微信公众号后台 → 设置与开发 → 基本配置 → IP白名单 中添加服务器出口 IP。

---

## 错误处理

| 错误码 | 含义 | 解决方案 |
|--------|------|---------|
| 40001 | AppSecret 错误 | 检查 .env 中的 AppSecret |
| 40007 | 无效的 media_id | 封面图上传失败，重试 |
| 40125 | invalid appsecret | AppSecret 不正确 |
| 40164 | 出口 IP 不在白名单 | 在公众号后台 IP 白名单中加入当前 IP |
| 45001 | 文章内容过长 | 内容限制 2MB，需要精简 |
| 45003 | 标题过长 | 标题限制 64 字符 |

---

## 关键文件

| 用途 | 路径 |
|------|------|
| Node.js 发布工具 | `<skill_dir>/src/cli.js` |
| Python 发布工具 | `<skill_dir>/scripts/publish_html.py` |
| 凭证模板 | `<skill_dir>/.env.example` |
| 凭证文件（用户自建，勿提交） | `<skill_dir>/.env` |

---

## 推荐工作流

**从内容收录到公众号发布的完整流程：**

```
1. 用户说："收录长文 https://..."
   ↓
2. 提取原文、生成发布内容
   ↓
3. 用户说："发到公众号"
   ↓
4. 准备封面图（Unsplash / Picsum）
   ↓
5. 准备正文（Markdown 或 HTML，去除 AI 味）
   ↓
6. 调用 wechat-publisher skill 创建草稿
   ↓
7. 发布成功，返回 media_id
   ↓
8. 登录公众号后台 → 草稿箱 → 预览 → 群发
```

---

## 依赖

**Node.js 发布工具（方式1）：**
- Node.js ≥ 18（ESM）
- 依赖见 `package.json`：`marked`、`node-fetch`、`form-data`、`chalk`、`minimist`、`dotenv`、`turndown`、`cli-progress`、`openai`

**Python 发布工具（方式2）：**
- Python ≥ 3.6
- `requests` 库

---

## 安全与隐私

- 凭证（AppID / AppSecret）只存于本机 `.env` / `wechat*.env`，**不会**被上传或写入仓库（已加入 `.gitignore`）。
- 本 skill 仅调用微信公众号官方 API（`api.weixin.qq.com`），不经过任何第三方。
- 只创建**草稿**，不会自动群发；群发需你登录后台手动确认。
