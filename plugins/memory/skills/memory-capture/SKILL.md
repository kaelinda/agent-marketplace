---
name: capture
description: 存储新的长期记忆。自动分类、敏感数据检测、命名空间路由。
category: memory-foundation
---

# capture — 记忆存储

## 触发条件
- 用户明确要求记住某事
- 会话结束后 commit 提取候选记忆
- Agent 识别到值得持久化的信息

## 用法
```bash
ov-memory capture --content "内容" [--type TYPE] [--title TITLE] [--scope SCOPE] [--auto-classify]
```

### 参数
| 参数 | 说明 |
|------|------|
| `--content` | 记忆内容（必填） |
| `--type` | 记忆类型（project/environment/case/preference/decision/profile/agent_reflection） |
| `--title` | 记忆标题（默认取内容前80字符） |
| `--scope` | 指定写入的命名空间路径（默认按类型自动路由） |
| `--auto-classify` | CLI 层面显示分类结果并强制使用自动分类（覆盖 `--type`） |

> 不指定 `--type` 且不加 `--auto-classify` 时，CLI 层也会自动调用 `classify_with_confidence()`。

## 处理流程
1. **敏感检测** — 扫描密码、API密钥、个人信息；block 级自动脱敏
2. **类型分类** — 未指定类型时自动推断（`classifier.classify()`）
3. **命名空间路由** — 根据类型分配 scope（user/preferences/、/projects/、/environments/ 等）
4. **写入存储** — 通过 adapter 写入后端

## 内部接口
```python
from skills.capture.scripts.capture import run_capture
result = run_capture(config, content="nginx配置在/etc/nginx/", memory_type="environment", title="Nginx路径")
result = run_capture(config, content="...", scope="custom/scope/path")  # 自定义 scope
```

## 安全规则
- 包含密码/API密钥/token 的内容默认阻止存储
- 可通过 `security.deny_sensitive` 配置调整策略
- 脱敏后仍含敏感数据则拒绝
