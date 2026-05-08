# Feishu + Discord + Dot. Sender MCP

统一的消息发送 MCP，支持飞书、Discord、Dot. 墨水屏设备。凭证外置，源码不含敏感信息。

## 快速开始

### 1. 克隆后配置凭证

```bash
cp config.json.example config.json
# 编辑 config.json，填入真实凭证
```

### 2. 配置示例（config.json）

```json
{
  "feishu": {
    "app_id": "cli_xxxx",
    "app_secret": "xxxx"
  },
  "discord": {
    "bot_token": "Bot xxxx"
  },
  "dot": {
    "api_key": "dot_app_xxxx",
    "device_id": "XXXXXXXXXXXX"
  }
}
```

> **Dot. 凭证获取方式：**
> - `api_key`：Dot. App → More → API Keys → Create API Key
> - `device_id`：Dot. App → Device → Device Serial Number

### 3. 注册到 OpenClaw

在 `openclaw.json` 的 `mcp.servers` 中添加：

```json
"messaging-sender": {
  "command": "python3",
  "args": ["/path/to/messaging-sender/server.py"]
}
```

## 工具

### 飞书

| 工具 | 说明 |
|------|------|
| `send_feishu_text` | 发送纯文本（最常用） |
| `send_to_feishu` | 通用接口，支持 text/post/interactive |

### Discord

| 工具 | 说明 |
|------|------|
| `send_discord_text` | 发送纯文本 |
| `send_to_discord` | 通用接口，支持文本或 embed JSON |

### Dot. 墨水屏

| 工具 | 说明 |
|------|------|
| `send_dot_text` | 在设备上显示文字（标题 + 正文 + 签名），支持 icon 字段传入任意图片自动处理 |
| `send_dot_image` | 在设备上显示 PNG 图片（支持本地路径或 base64） |

## 调用示例

### 飞书

```
tool: messaging-sender
name: send_feishu_text
arguments: {"text": "Hello!", "receive_id": "ou_xxx"}
```

### Discord

```
tool: messaging-sender
name: send_discord_text
arguments: {"text": "Hello!", "channel_id": "123456789"}
```

### Dot.

#### send_dot_text - icon 字段说明

**icon 字段只接受 base64 PNG**。

使用方式：先从 iconfont 渲染出 PNG，拿到 base64 再传入。

渲染脚本参考 `knowledge/icon-to-base64.py`，已预渲染的 icon 位于 `/Users/hm/openclaw-config/asset/font/icons/`。

```json
tool: messaging-sender
name: send_dot_text
arguments: {"title": "提醒", "message": "该喝水了", "signature": "AI助手", "icon": "<base64 PNG>"}
```

#### send_dot_image

```
tool: messaging-sender
name: send_dot_image
arguments: {"image_path": "/path/to/chart.png"}
```
