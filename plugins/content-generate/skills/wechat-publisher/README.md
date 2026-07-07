# wechat-publisher

将 Markdown / HTML 文章一键发布到**微信公众号草稿箱**，支持多主题排版、封面图与正文图片自动上传、多账号切换。创建的是草稿，不会自动群发，需登录公众号后台预览后发布。

属于 `content-generate` 插件，常与同插件的 `md-to-html`（Markdown → 可发布 HTML）配合使用：先用 `md-to-html` 渲染，再用本 skill 投递到公众号。

> 下文 `<skill_dir>` 指 skill 安装目录 `plugins/content-generate/skills/wechat-publisher`。

## 功能特性

- ✅ **Markdown → 微信 HTML**：支持微信公众号兼容的 HTML 格式
- ✅ **图片自动上传**：本地图片自动上传到微信 CDN
- ✅ **封面图支持**：上传封面图到草稿箱（900×383）
- ✅ **多主题定制**：4 款排版主题可选
- ✅ **内联样式**：自动应用微信兼容的内联 CSS
- ✅ **多账号**：通过 `--account tech|parenting` 在多个公众号间切换
- ✅ **HTML 直发**：Python 脚本可直接发布手写 HTML，适合精细排版

## 主题

| 主题 | 风格 | 适用场景 |
|------|------|----------|
| `reader`（默认）| 暖色调沉浸阅读 | 技术文章、博客 |
| `codefine` | 深色代码风格 | 编程教程、代码演示 |
| `ocean` | 海蓝色调专业沉稳 | 产品文档、新闻 |
| `chatex` | 聊天消息风格 | 教程、问答 |

## 安装

```bash
cd "<skill_dir>"
npm install
pip install requests   # 可选，仅在使用 Python HTML 发布方式时需要
```

## 配置凭证

1. 复制凭证模板：

```bash
cp "<skill_dir>/.env.example" "<skill_dir>/.env"
```

2. 编辑 `.env`，填入你的微信公众号凭证：

```env
WECHAT_APP_ID=wx_your_app_id
WECHAT_APP_SECRET=your_app_secret
```

3. 在 [微信公众平台](https://mp.weixin.qq.com/) → 设置与开发 → 基本配置 → IP 白名单 中添加本机出口 IP。

> 多账号：改用 `wechat.env` / `wechat-parenting.env`（参考 `wechat.env.example`），发布时加 `--account tech|parenting`。

## 使用方法

### 测试连接

```bash
node "<skill_dir>/src/cli.js" test
```

### Markdown 发布（默认 reader 主题）

```bash
node "<skill_dir>/src/cli.js" publish \
  --title "文章标题" \
  --markdown ./article.md \
  --author "作者名"
```

### 指定主题

```bash
# CodeFine 主题（深色代码风格）
node "<skill_dir>/src/cli.js" publish \
  --title "代码教程" --markdown ./code.md --theme codefine

# Ocean 主题（海蓝配色）
node "<skill_dir>/src/cli.js" publish \
  --title "产品更新" --markdown ./changelog.md --theme ocean
```

### 带封面图

```bash
node "<skill_dir>/src/cli.js" publish \
  --title "文章标题" --markdown ./article.md --cover ./cover.jpg
```

### 直接发布 HTML（Python）

```bash
python3 "<skill_dir>/scripts/publish_html.py" \
  --file ./article.html \
  --title "文章标题" \
  --cover ./cover.jpg \
  --author "AICoder" \
  --digest "摘要内容"
```

### 查看所有主题

```bash
node "<skill_dir>/src/cli.js" themes
```

## 工作流程

```
Markdown / HTML 文件
    ↓
选择主题（reader/codefine/ocean/chatex）
    ↓
解析 + 处理图片（本地图片上传到微信 CDN）
    ↓
主题样式 HTML
    ↓
上传封面图 → thumb_media_id
    ↓
创建草稿 → 草稿箱
    ↓
登录公众号后台 → 预览 → 群发
```

## 限制

- 草稿箱中的图文消息被群发后会从草稿箱移除
- 图片必须使用微信 CDN URL（外链图片不支持，本工具会自动上传）
- 文章内容不超过 2MB
- 需要已认证的公众号（订阅号或服务号），并开启素材/草稿接口权限

## 故障排除

### 40125 error（AppSecret 错误）
检查 `.env` 中的 `WECHAT_APP_SECRET` 是否正确。

### 40001 error（access_token 错误）
1. 检查 AppID 和 AppSecret 是否匹配
2. 检查 access_token 是否过期（有效期 2 小时）
3. 确认服务器 IP 已加入白名单

### 40164 error（IP 不在白名单）
在公众号后台 → 设置与开发 → 基本配置 → IP 白名单 中加入报错里提示的 IP。

### 图片上传失败
确保图片格式为 jpg/png/gif/webp，且大小适中。

更多错误码见 [SKILL.md](./SKILL.md#错误处理)。

## 安全与隐私

- 凭证只存于本机 `.env` / `wechat*.env`，已被 `.gitignore` 忽略，不会进入仓库。
- 仅调用微信公众号官方 API（`api.weixin.qq.com`），不经过任何第三方。
- 只创建草稿，不自动群发。

## License

MIT
