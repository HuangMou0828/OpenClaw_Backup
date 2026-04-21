# Feishu + Discord Sender MCP

统一的消息发送 MCP，支持飞书和 Discord。凭证外置，源码不含敏感信息。

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
  }
}
```

### 3. 注册到 OpenClaw

在 `openclaw.json` 的 `mcp.servers` 中添加：

```json
"feishu-sender": {
  "command": "python3",
  "args": ["/path/to/feishu-sender/server.py"]
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

## 调用示例

```
tool: feishu-sender
name: send_feishu_text
arguments: {"text": "Hello!", "receive_id": "ou_xxx"}
```

```
tool: feishu-sender
name: send_discord_text
arguments: {"text": "Hello!", "channel_id": "123456789"}
```
