# ali-oss

将文件上传到阿里云 OSS（对象存储）。支持配置**多个 bucket** 并指定**默认 bucket**，
自动探测 bucket 所在 region，列举 / 删除对象，以及生成预签名分享链接。

纯 Python 3 标准库实现（内置 OSS V1 / HMAC-SHA1 签名），**无需安装 `oss2` 等 SDK**。

## 安全说明（重要）

- 凭证与 bucket 配置保存在仓库**之外**：默认 `~/.config/ali-oss/config.json`（权限 `0600`）。
  插件源码里**不写入任何 AccessKey**。
- AccessKey 属于敏感信息。建议为上传场景单独创建一个**仅授权目标 bucket** 的 RAM 子账号，
  不要使用主账号 AK；一旦泄露应立即在阿里云控制台轮换。

## 快速开始

```bash
cd plugins/content-generate/skills/ali-oss
SCRIPT=scripts/ali_oss.py

# 1. 配置一个 bucket（region 省略时自动探测），并设为默认
python3 $SCRIPT add-bucket kael-obsidian \
  --access-key-id   "$ALI_OSS_ACCESS_KEY_ID" \
  --access-key-secret "$ALI_OSS_ACCESS_KEY_SECRET" \
  --default

# 2. 上传文件（不带 --bucket 时用默认 bucket）
python3 $SCRIPT upload ./cover.png --prefix blog/2026
#   → https://kael-obsidian.oss-cn-beijing.aliyuncs.com/blog/2026/cover.png

# 3. 列举 / 分享 / 删除
python3 $SCRIPT list --prefix blog/2026
python3 $SCRIPT sign-url blog/2026/cover.png --expires 3600
python3 $SCRIPT delete blog/2026/cover.png
```

## 多 bucket 管理

```bash
python3 $SCRIPT add-bucket bucket-a --access-key-id ... --access-key-secret ... --default
python3 $SCRIPT add-bucket bucket-b --access-key-id ... --access-key-secret ...
python3 $SCRIPT list-buckets          # 带 * 的是默认 bucket
python3 $SCRIPT set-default bucket-b  # 切换默认
python3 $SCRIPT upload x.png --bucket bucket-a   # 指定 bucket 覆盖默认
```

## 命令一览

| 命令 | 说明 |
|------|------|
| `add-bucket NAME` | 新增/更新 bucket，省略 endpoint 时自动探测 region |
| `remove-bucket NAME` | 删除 bucket 配置 |
| `set-default NAME` | 设置默认 bucket |
| `list-buckets` | 列出已配置 bucket（密钥不显示） |
| `info` | 显示配置路径与默认 bucket |
| `upload PATH...` | 上传文件/目录（`--recursive`、`--prefix`、`--key`、`--content-type`、`--acl`、`--sign`） |
| `list` | 列举对象（`--prefix`、`--max-keys`） |
| `delete KEY` | 删除对象 |
| `sign-url KEY` | 生成预签名 GET 链接（`--expires`，默认 1 小时） |

## 配置文件

参见 [`references/config.example.json`](references/config.example.json)。可用 `--config PATH`
或环境变量 `ALI_OSS_CONFIG` 覆盖默认路径。

## 测试

```bash
python3 tests/test_ali_oss.py   # 离线单测，不联网
```

更多细节见 [SKILL.md](SKILL.md)。
