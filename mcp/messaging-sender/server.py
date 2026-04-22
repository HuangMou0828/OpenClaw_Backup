#!/usr/bin/env python3
"""Feishu + Discord Sender MCP Server

提供统一的消息发送能力：
- 飞书：send_to_feishu / send_feishu_text
- Discord：send_to_discord / send_discord_text

凭证从同目录 config.json 读取（gitignored），不硬编码在源码里。
"""

import json
import os
from pathlib import Path
from typing import Any

import requests
from mcp.server import Server
from mcp.types import Tool, TextContent

app = Server("messaging-sender")

# ─── Credential loading ───────────────────────────────────────────────────────

_config = None

def _load_config() -> dict:
    global _config
    if _config is None:
        p = Path(__file__).parent / "config.json"
        _config = json.loads(p.read_text()) if p.exists() else {}
    return _config

def _feishu_app_id() -> str:
    return _load_config().get("feishu", {}).get("app_id", "")

def _feishu_app_secret() -> str:
    return _load_config().get("feishu", {}).get("app_secret", "") or os.environ.get("FEISHU_APP_SECRET", "")

def _discord_bot_token() -> str:
    return _load_config().get("discord", {}).get("bot_token", "")

# ─── Feishu helpers ──────────────────────────────────────────────────────────

def get_tenant_access_token(app_id: str, app_secret: str) -> str:
    response = requests.post(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        headers={"Content-Type": "application/json"},
        json={"app_id": app_id, "app_secret": app_secret},
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()
    if data.get("code") != 0:
        raise Exception(f"Failed to get token: {data}")
    return data["tenant_access_token"]


def send_feishu_message(token: str, receive_id: str, receive_id_type: str, msg_type: str, content: str) -> dict:
    url = "https://open.feishu.cn/open-apis/im/v1/messages"
    params = {"receive_id_type": receive_id_type}
    payload = {"receive_id": receive_id, "msg_type": msg_type, "content": content}
    response = requests.post(
        url, params=params, headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=payload, timeout=15,
    )
    response.raise_for_status()
    data = response.json()
    if data.get("code") != 0:
        raise Exception(f"Failed to send message: {data}")
    return data


# ─── Discord helpers ─────────────────────────────────────────────────────────

DISCORD_PROXIES = {"http": "http://127.0.0.1:7897", "https": "http://127.0.0.1:7897"}

def send_discord_message(bot_token: str, channel_id: str, content: str | None = None, embed: dict | list | None = None) -> dict:
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    payload = {"content": content, "embeds": None}
    if embed:
        payload["embeds"] = [embed] if isinstance(embed, dict) else embed
    response = requests.post(
        url, json=payload,
        headers={"Authorization": f"Bot {bot_token}", "Content-Type": "application/json"},
        proxies=DISCORD_PROXIES, verify=False, timeout=15,
    )
    response.raise_for_status()
    data = response.json()
    if isinstance(data, dict) and data.get("code"):
        raise Exception(f"Discord API error: {data}")
    return data


# ─── Tools ───────────────────────────────────────────────────────────────────

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="send_to_feishu",
            description="发送飞书消息（支持 text/post/interactive）。凭证可省略，默认从 config.json 读取。",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "消息内容。text 为纯文本；post/interactive 为对应 JSON 字符串。"},
                    "receive_id": {"type": "string", "description": "接收者 ID（open_id 格式 ou_xxx）。"},
                    "msg_type": {"type": "string", "enum": ["text", "post", "interactive"], "default": "text"},
                    "receive_id_type": {"type": "string", "enum": ["open_id", "user_id", "union_id", "email", "chat_id"], "default": "open_id"},
                    "app_id": {"type": "string", "description": "飞书 app_id（不填用 config.json）"},
                    "app_secret": {"type": "string", "description": "飞书 app_secret（不填用 config.json 或 FEISHU_APP_SECRET）"},
                },
                "required": ["content", "receive_id"],
            },
        ),
        Tool(
            name="send_feishu_text",
            description="发送纯文本消息到飞书（便捷封装）。",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "纯文本内容。"},
                    "receive_id": {"type": "string", "description": "接收者 open_id（ou_xxx）。"},
                    "app_id": {"type": "string", "description": "飞书 app_id。"},
                    "app_secret": {"type": "string", "description": "飞书 app_secret。"},
                },
                "required": ["text", "receive_id"],
            },
        ),
        Tool(
            name="send_to_discord",
            description="发送 Discord 消息（支持纯文本或 embed JSON）。凭证可省略，默认从 config.json 读取。",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "纯文本内容（可选，与 embed 二选一）。"},
                    "embed": {"type": "object", "description": "Discord embed JSON（可选，与 content 二选一）。"},
                    "channel_id": {"type": "string", "description": "Discord channel ID。"},
                    "bot_token": {"type": "string", "description": "Discord bot token（不填用 config.json）"},
                },
                "required": ["channel_id"],
            },
        ),
        Tool(
            name="send_discord_text",
            description="发送纯文本到 Discord（便捷封装）。",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "纯文本内容。"},
                    "channel_id": {"type": "string", "description": "Discord channel ID。"},
                    "bot_token": {"type": "string", "description": "Discord bot token。"},
                },
                "required": ["text", "channel_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    def err(msg: str) -> list[TextContent]:
        return [TextContent(type="text", text=json.dumps({"success": False, "error": msg}, indent=2, ensure_ascii=False))]

    # ── Feishu ────────────────────────────────────────────────────────────────

    if name == "send_to_feishu":
        app_id = arguments.get("app_id") or _feishu_app_id()
        app_secret = arguments.get("app_secret") or _feishu_app_secret()
        if not app_secret:
            return err("app_secret required: set feishu.app_secret in config.json or FEISHU_APP_SECRET env")
        try:
            token = get_tenant_access_token(app_id, app_secret)
            result = send_feishu_message(token, arguments["receive_id"], arguments.get("receive_id_type", "open_id"),
                                        arguments.get("msg_type", "text"), arguments["content"])
            return [TextContent(type="text", text=json.dumps({
                "success": True, "message_id": result.get("data", {}).get("message_id"),
                "receive_id": arguments["receive_id"],
            }, indent=2, ensure_ascii=False))]
        except Exception as e:
            return err(str(e))

    elif name == "send_feishu_text":
        app_id = arguments.get("app_id") or _feishu_app_id()
        app_secret = arguments.get("app_secret") or _feishu_app_secret()
        if not app_secret:
            return err("app_secret required: set feishu.app_secret in config.json or FEISHU_APP_SECRET env")
        try:
            token = get_tenant_access_token(app_id, app_secret)
            result = send_feishu_message(token, arguments["receive_id"], "open_id", "text",
                                        json.dumps({"text": arguments["text"]}))
            return [TextContent(type="text", text=json.dumps({
                "success": True, "message_id": result.get("data", {}).get("message_id"),
                "receive_id": arguments["receive_id"],
            }, indent=2, ensure_ascii=False))]
        except Exception as e:
            return err(str(e))

    # ── Discord ───────────────────────────────────────────────────────────────

    elif name == "send_to_discord":
        channel_id = arguments["channel_id"]
        content = arguments.get("content")
        embed = arguments.get("embed")
        bot_token = arguments.get("bot_token") or _discord_bot_token()
        if not content and not embed:
            return err("content or embed required")
        if not bot_token:
            return err("bot_token required: set discord.bot_token in config.json")
        try:
            result = send_discord_message(bot_token, channel_id, content=content, embed=embed)
            msg_id = result.get("id") if isinstance(result, dict) else None
            return [TextContent(type="text", text=json.dumps({"success": True, "message_id": msg_id, "channel_id": channel_id}, indent=2, ensure_ascii=False))]
        except Exception as e:
            return err(str(e))

    elif name == "send_discord_text":
        channel_id = arguments["channel_id"]
        bot_token = arguments.get("bot_token") or _discord_bot_token()
        if not bot_token:
            return err("bot_token required: set discord.bot_token in config.json")
        try:
            result = send_discord_message(bot_token, channel_id, content=arguments["text"])
            msg_id = result.get("id") if isinstance(result, dict) else None
            return [TextContent(type="text", text=json.dumps({"success": True, "message_id": msg_id, "channel_id": channel_id}, indent=2, ensure_ascii=False))]
        except Exception as e:
            return err(str(e))

    else:
        return err(f"Unknown tool: {name}")


# ─── main ─────────────────────────────────────────────────────────────────────

async def main():
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
