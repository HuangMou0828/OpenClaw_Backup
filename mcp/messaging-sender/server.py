#!/usr/bin/env python3
"""Feishu + Discord + Dot. Sender MCP Server

提供统一的消息发送能力：
- 飞书：send_to_feishu / send_feishu_text
- Discord：send_to_discord / send_discord_text
- Dot. 墨水屏：send_dot_text / send_dot_image

凭证从同目录 config.json 读取（gitignored），不硬编码在源码里。
"""

import base64
import json
import os
from pathlib import Path
from typing import Any

import requests
from mcp.server import Server
from mcp.types import Tool, TextContent

app = Server("messaging-sender")

DOT_BASE_URL = "https://dot.mindreset.tech"

# ─── Credential loading ───────────────────────────────────────────────────────

_config = None

def _load_config() -> dict:
    global _config
    if _config is None:
        p = Path(__file__).parent / "config.json"
        _config = json.loads(p.read_text()) if p.exists() else {}
    return _config

def _feishu_app_id() -> str:
    return _load_config().get("feishu", {}).get("app_id", "") or os.environ.get("FEISHU_APP_ID", "")

def _feishu_app_secret() -> str:
    return _load_config().get("feishu", {}).get("app_secret", "") or os.environ.get("FEISHU_APP_SECRET", "")

def _discord_bot_token() -> str:
    return _load_config().get("discord", {}).get("bot_token", "") or os.environ.get("DISCORD_BOT_TOKEN", "")

def _discord_proxy() -> dict | None:
    """Get Discord proxy config from config.json."""
    proxy_url = _load_config().get("discord", {}).get("proxy")
    if proxy_url:
        return {"http": proxy_url, "https": proxy_url}
    return None

def _dot_api_key() -> str:
    return _load_config().get("dot", {}).get("api_key", "") or os.environ.get("DOT_API_KEY", "")

def _dot_device_id() -> str:
    return _load_config().get("dot", {}).get("device_id", "") or os.environ.get("DOT_DEVICE_ID", "")

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

def send_discord_message(bot_token: str, channel_id: str, content: str | None = None, embed: dict | list | None = None) -> dict:
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    payload = {"content": content, "embeds": None}
    if embed:
        payload["embeds"] = [embed] if isinstance(embed, dict) else embed

    proxies = _discord_proxy()
    response = requests.post(
        url, json=payload,
        headers={"Authorization": f"Bot {bot_token}", "Content-Type": "application/json"},
        proxies=proxies, timeout=15,
    )
    response.raise_for_status()
    data = response.json()
    if isinstance(data, dict) and data.get("code"):
        raise Exception(f"Discord API error: {data}")
    return data


def _process_icon(input_val: str) -> str:
    """
    Dot text API 的 icon 字段只接受 base64 PNG。
    本函数验证输入是否为有效的 base64 PNG，是则原样返回，否抛异常。
    """
    try:
        data = base64.b64decode(input_val)
    except Exception:
        raise ValueError(f"icon 不是有效的 base64: {input_val[:40]}...")
    if not (data[:4] == b'\x89PNG' or data[:3] == b'\xff\xd8\xff'):
        raise ValueError(f"icon base64 不是 PNG/JPEG 图片")
    return input_val


def send_dot_api(path: str, body: dict, api_key: str) -> dict:
    response = requests.post(
        f"{DOT_BASE_URL}{path}",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=body, timeout=15,
    )
    response.raise_for_status()
    return response.json()


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
        # ── Dot. ──────────────────────────────────────────────────────────────
        Tool(
            name="send_dot_text",
            description="在 Dot. 墨水屏设备上显示文字内容。",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "标题文字。"},
                    "message": {"type": "string", "description": "主要文字内容。"},
                    "signature": {"type": "string", "description": "签名/底部文字。"},
                    "icon": {"type": "string", "description": "图标图片。可传本地路径、URL 或 base64（自动处理为高对比黑白 PNG，尺寸为 40 的整数倍，最大 160px）。"},
                    "link": {"type": "string", "description": "点击跳转链接。"},
                    "device_id": {"type": "string", "description": "设备序列号（不填用 config.json 或 DOT_DEVICE_ID）。"},
                    "api_key": {"type": "string", "description": "Dot. API key（不填用 config.json 或 DOT_API_KEY）。"},
                    "refresh_now": {"type": "boolean", "description": "立即显示（默认 true），false 则排队不刷新。"},
                    "taskKey": {"type": "string", "description": "文本槽位标识，用于区分多个文本 API（默认不传则使用第一个槽位）。"},
                },
                "required": ["message"],
            },
        ),
        Tool(
            name="send_dot_image",
            description="在 Dot. 墨水屏设备上显示 PNG 图片。",
            inputSchema={
                "type": "object",
                "properties": {
                    "image_path": {"type": "string", "description": "本地 PNG 图片路径（与 image_base64 二选一）。"},
                    "image_base64": {"type": "string", "description": "Base64 编码的 PNG 图片数据（与 image_path 二选一）。"},
                    "link": {"type": "string", "description": "点击跳转链接。"},
                    "border": {"type": "number", "description": "屏幕边框颜色：0=白色（默认），1=黑色。"},
                    "dither_type": {"type": "string", "enum": ["DIFFUSION", "ORDERED", "NONE"], "description": "抖动类型（默认 DIFFUSION）。"},
                    "dither_kernel": {"type": "string", "description": "抖动算法（默认 FLOYD_STEINBERG）。"},
                    "device_id": {"type": "string", "description": "设备序列号（不填用 config.json 或 DOT_DEVICE_ID）。"},
                    "api_key": {"type": "string", "description": "Dot. API key（不填用 config.json 或 DOT_API_KEY）。"},
                    "refresh_now": {"type": "boolean", "description": "立即显示（默认 true）。"},
                },
                "required": [],
            },
        ),
        # ── eink template renderer ───────────────────────────────────────────
        Tool(
            name="render_eink_template",
            description=(
                "用 JSON 模板 + 数据渲染 1-bit 墨水屏图片，返回 base64 PNG。"
                "支持元素：text/icon/image/line/rect/qrcode/container（vbox|hbox 自动布局）。"
                "默认尺寸 296×152（Dot. 2.66 寸），可在模板 meta 里覆盖。"
                "模板可传入 dict、JSON 字符串，或 templates/ 目录下的模板名（如 schedule）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "template": {
                        "description": "模板：JSON 对象、JSON 字符串或 templates/ 下的模板名。",
                    },
                    "data": {"type": "object", "description": "模板变量数据，匹配 ${var} 占位符。"},
                    "save_path": {"type": "string", "description": "可选，把渲染结果保存到本地路径（PNG/BMP）。"},
                    "return_base64": {"type": "boolean", "description": "是否返回 base64 PNG（默认 true）。"},
                },
                "required": ["template"],
            },
        ),
        Tool(
            name="send_eink_template",
            description=(
                "渲染模板并直接发送到 Dot. 墨水屏（一键完成）。"
                "等同于 render_eink_template + send_dot_image 的组合。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "template": {"description": "模板：JSON 对象、JSON 字符串或 templates/ 下的模板名。"},
                    "data": {"type": "object", "description": "模板变量数据。"},
                    "link": {"type": "string", "description": "点击跳转链接。"},
                    "border": {"type": "number", "description": "屏幕边框颜色：0=白色（默认），1=黑色。"},
                    "device_id": {"type": "string", "description": "设备序列号（不填用 config.json）。"},
                    "api_key": {"type": "string", "description": "Dot. API key（不填用 config.json）。"},
                    "refresh_now": {"type": "boolean", "description": "立即显示（默认 true）。"},
                    "save_path": {"type": "string", "description": "可选，同时把渲染结果保存到本地路径，便于调试。"},
                },
                "required": ["template"],
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

    # ── Dot. ──────────────────────────────────────────────────────────────────

    elif name == "send_dot_text":
        api_key = arguments.get("api_key") or _dot_api_key()
        device_id = arguments.get("device_id") or _dot_device_id()
        if not api_key:
            return err("api_key required: set dot.api_key in config.json or DOT_API_KEY env")
        if not device_id:
            return err("device_id required: set dot.device_id in config.json or DOT_DEVICE_ID env")
        body: dict[str, Any] = {"refreshNow": arguments.get("refresh_now", True)}
        if arguments.get("title") is not None:
            body["title"] = arguments["title"]
        if arguments.get("message") is not None:
            body["message"] = arguments["message"]
        if arguments.get("signature") is not None:
            body["signature"] = arguments["signature"]
        if arguments.get("link") is not None:
            body["link"] = arguments["link"]
        if arguments.get("icon") is not None:
            body["icon"] = _process_icon(arguments["icon"])
        if arguments.get("taskKey") is not None:
            body["taskKey"] = arguments["taskKey"]
        try:
            result = send_dot_api(f"/api/authV2/open/device/{device_id}/text", body, api_key)
            return [TextContent(type="text", text=json.dumps({"success": True, "device_id": device_id, "message": result.get("message", "ok")}, indent=2, ensure_ascii=False))]
        except Exception as e:
            return err(str(e))

    elif name == "send_dot_image":
        api_key = arguments.get("api_key") or _dot_api_key()
        device_id = arguments.get("device_id") or _dot_device_id()
        if not api_key:
            return err("api_key required: set dot.api_key in config.json or DOT_API_KEY env")
        if not device_id:
            return err("device_id required: set dot.device_id in config.json or DOT_DEVICE_ID env")
        # Resolve image data
        image_b64 = arguments.get("image_base64")
        if not image_b64 and arguments.get("image_path"):
            image_b64 = base64.b64encode(Path(arguments["image_path"]).read_bytes()).decode()
        if not image_b64:
            return err("image_path or image_base64 required")
        body = {"refreshNow": arguments.get("refresh_now", True), "image": image_b64}
        if arguments.get("link") is not None:
            body["link"] = arguments["link"]
        if arguments.get("border") is not None:
            body["border"] = arguments["border"]
        if arguments.get("dither_type") is not None:
            body["ditherType"] = arguments["dither_type"]
        if arguments.get("dither_kernel") is not None:
            body["ditherKernel"] = arguments["dither_kernel"]
        try:
            result = send_dot_api(f"/api/authV2/open/device/{device_id}/image", body, api_key)
            return [TextContent(type="text", text=json.dumps({"success": True, "device_id": device_id, "message": result.get("message", "ok")}, indent=2, ensure_ascii=False))]
        except Exception as e:
            return err(str(e))

    # ── eink template renderer ────────────────────────────────────────────────

    elif name == "render_eink_template":
        try:
            from eink_renderer import load_template, render, render_to_base64
        except ImportError as e:
            return err(f"eink_renderer import failed: {e}")
        try:
            tpl = load_template(arguments["template"])
            data = arguments.get("data") or {}
            if arguments.get("save_path"):
                img = render(tpl, data)
                img.save(arguments["save_path"])
            png_b64 = render_to_base64(tpl, data) if arguments.get("return_base64", True) else None
            return [TextContent(type="text", text=json.dumps({
                "success": True,
                "width": tpl.get("meta", {}).get("width", 296),
                "height": tpl.get("meta", {}).get("height", 152),
                "saved_to": arguments.get("save_path"),
                "image_base64": png_b64,
            }, indent=2, ensure_ascii=False))]
        except Exception as e:
            return err(f"render failed: {e}")

    elif name == "send_eink_template":
        api_key = arguments.get("api_key") or _dot_api_key()
        device_id = arguments.get("device_id") or _dot_device_id()
        if not api_key:
            return err("api_key required: set dot.api_key in config.json or DOT_API_KEY env")
        if not device_id:
            return err("device_id required: set dot.device_id in config.json or DOT_DEVICE_ID env")
        try:
            from eink_renderer import load_template, render, render_to_base64
        except ImportError as e:
            return err(f"eink_renderer import failed: {e}")
        try:
            tpl = load_template(arguments["template"])
            data = arguments.get("data") or {}
            if arguments.get("save_path"):
                render(tpl, data).save(arguments["save_path"])
            image_b64 = render_to_base64(tpl, data)
        except Exception as e:
            return err(f"render failed: {e}")

        body: dict[str, Any] = {
            "refreshNow": arguments.get("refresh_now", True),
            "image": image_b64,
            "ditherType": "NONE",  # 模板已生成 1-bit，禁止 Dot 端再 dither
        }
        if arguments.get("link") is not None:
            body["link"] = arguments["link"]
        if arguments.get("border") is not None:
            body["border"] = arguments["border"]
        try:
            result = send_dot_api(f"/api/authV2/open/device/{device_id}/image", body, api_key)
            return [TextContent(type="text", text=json.dumps({
                "success": True,
                "device_id": device_id,
                "saved_to": arguments.get("save_path"),
                "message": result.get("message", "ok"),
            }, indent=2, ensure_ascii=False))]
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
