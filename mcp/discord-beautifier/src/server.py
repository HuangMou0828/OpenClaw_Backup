#!/usr/bin/env python3
"""Discord Beautifier MCP Server

Extensible formatter system for Discord embeds with multiple information types.
Includes adapters for converting cron output Markdown to embed JSON in one step.
"""

import json
import sys
from typing import Any

from mcp.server import Server
from mcp.types import Tool, TextContent

# Import core components
from core.registry import registry
from styles.presets import get_rainbow_info, get_rainbow_color

# Import formatters
from formatters.generic_formatter import GenericFormatter
from formatters.news.news_formatter import NewsFormatter
from formatters.task.task_formatter import TaskReportFormatter

# Import adapters
from formatters.adapters.news_adapter import parse_ai_news_markdown
from formatters.adapters.task_adapter import parse_l5_health_markdown, parse_task_report_markdown


# Initialize server
app = Server("discord-beautifier")

# Register all formatters
registry.register(GenericFormatter())
registry.register(NewsFormatter())
registry.register(TaskReportFormatter())


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools from registered formatters + adapters."""
    tools = []

    # Add formatter tools
    for formatter in registry.list_all():
        tools.append(
            Tool(
                name=formatter.get_tool_name(),
                description=formatter.get_tool_description(),
                inputSchema=formatter.get_tool_schema(),
            )
        )

    # Adapter tool: AI News Markdown → Discord embed (one step)
    tools.append(
        Tool(
            name="format_ai_news",
            description=(
                "Convert AI news cron Markdown output to Discord embed in one step. "
                "Input is the raw Markdown text from the AI news cron job. "
                "Automatically detects news categories (🔥/🏭/🤖/💡/🛠) and builds "
                "a rainbow-colored Discord embed. Use this for 资讯类 cron jobs."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "markdown": {
                        "type": "string",
                        "description": "Raw Markdown text from AI news cron output",
                    },
                    "digest_title": {
                        "type": "string",
                        "description": "Optional title override (default: AI 热点日报)",
                        "default": "AI 热点日报",
                    },
                },
                "required": ["markdown"],
            },
        )
    )

    # Adapter tool: Task/Monitoring Markdown → Discord embed (one step)
    tools.append(
        Tool(
            name="format_task_check",
            description=(
                "Convert task monitoring cron Markdown output to Discord embed in one step. "
                "Input is the raw Markdown text from task/health check cron jobs. "
                "Automatically detects status (✅/❌/⚠️), metrics, and details. "
                "Supports L5 health check, memory promotion, daily AI usage reports, etc. "
                "Use this for 个人任务类 cron jobs."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "markdown": {
                        "type": "string",
                        "description": "Raw Markdown text from task/monitoring cron output",
                    },
                    "report_title": {
                        "type": "string",
                        "description": "Optional title override",
                    },
                    "report_type": {
                        "type": "string",
                        "description": "Report type hint (auto-detected if omitted)",
                        "enum": ["daily_summary", "cron_result", "health_check", "auto"],
                        "default": "auto",
                    },
                },
                "required": ["markdown"],
            },
        )
    )

    # Existing utility tools
    tools.append(
        Tool(
            name="send_to_discord_via_bot",
            description=(
                "Send a Discord embed message using a bot token and channel ID. "
                "Faster than webhook, supports higher rate limits. "
                "Uses local proxy if available (127.0.0.1:7897)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "embed": {
                        "type": "object",
                        "description": "Discord embed JSON",
                    },
                    "channel_id": {
                        "type": "string",
                        "description": "Discord channel ID to send to",
                    },
                    "bot_token": {
                        "type": "string",
                        "description": "Discord bot token (Bot <token>)",
                    },
                },
                "required": ["embed", "channel_id", "bot_token"],
            },
        )
    )

    tools.append(
        Tool(
            name="get_rainbow_color",
            description="Get the current day's rainbow color info (for debugging/demos)",
            inputSchema={"type": "object", "properties": {}},
        )
    )

    return tools


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    if name == "format_ai_news":
        from formatters.adapters.news_adapter import build_news_embed

        markdown_text = arguments["markdown"]
        digest_title = arguments.get("digest_title", "AI 热点日报")

        # Parse Markdown → structured articles
        parsed = parse_ai_news_markdown(markdown_text)
        articles = parsed.get("articles", [])

        if not articles:
            return [TextContent(type="text", text=json.dumps({
                "error": "No articles found in markdown. Check format."
            }, indent=2))]

        # Build embed using optimized field-based layout
        embed = build_news_embed(parsed, digest_title)
        embed["color"] = get_rainbow_color()

        result = {"embeds": [embed]}

        # Add debug info
        rainbow_info = get_rainbow_info()
        result["_debug"] = {
            **rainbow_info,
            "article_count": len(articles),
            "format": parsed.get("format", "unknown")
        }

        return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]

    elif name == "format_task_check":
        from formatters.adapters.task_adapter import build_task_embed

        markdown_text = arguments["markdown"]
        report_title = arguments.get("report_title")
        report_type = arguments.get("report_type", "auto")

        # Auto-detect report type from content
        if report_type == "auto":
            if "健康巡检" in markdown_text or "Health Check" in markdown_text:
                report_type = "health_check"
            elif "晋升" in markdown_text or "promotion" in markdown_text.lower():
                report_type = "daily_summary"
            elif "使用" in markdown_text and "日报" in markdown_text:
                report_type = "daily_summary"
            else:
                report_type = "cron_result"

        # Parse Markdown → structured report
        if report_type == "health_check":
            parsed = parse_l5_health_markdown(markdown_text)
        else:
            parsed = parse_task_report_markdown(markdown_text)
            if report_title:
                parsed["title"] = report_title

        # Build embed using optimized layout
        embed = build_task_embed(parsed)
        embed["color"] = get_rainbow_color()

        result = {"embeds": [embed]}

        # Add debug info
        rainbow_info = get_rainbow_info()
        result["_debug"] = {
            **rainbow_info,
            "report_type": report_type,
            "status_detected": parsed.get("status", "unknown"),
            "problem_count": len(parsed.get("problem_list", [])),
        }

        return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]

    elif name == "send_to_discord_via_bot":
        import requests

        embed = arguments["embed"]
        channel_id = arguments["channel_id"]
        bot_token = arguments["bot_token"]

        proxies = {
            "http": "http://127.0.0.1:7897",
            "https": "http://127.0.0.1:7897",
        }

        payload = {"content": None, "embeds": [embed] if isinstance(embed, dict) else embed}

        try:
            response = requests.post(
                f"https://discord.com/api/v10/channels/{channel_id}/messages",
                json=payload,
                headers={
                    "Authorization": f"Bot {bot_token}",
                    "Content-Type": "application/json",
                },
                proxies=proxies,
                verify=False,
                timeout=15,
            )
            response.raise_for_status()
            resp_data = response.json()
            return [TextContent(type="text", text=json.dumps({
                "success": True,
                "message_id": resp_data.get("id"),
                "channel_id": channel_id,
            }, indent=2))]
        except Exception as e:
            return [TextContent(type="text", text=json.dumps({
                "success": False,
                "error": str(e),
                "channel_id": channel_id,
            }, indent=2))]

    elif name == "get_rainbow_color":
        from styles.presets import RAINBOW_HEX, RAINBOW_COLORS
        info = get_rainbow_info()
        info["all_colors"] = [
            {"day_index": i, "day": ["周日","周一","周二","周三","周四","周五","周六"][i],
             "hex": RAINBOW_HEX[i], "decimal": RAINBOW_COLORS[i]}
            for i in range(7)
        ]
        return [TextContent(type="text", text=json.dumps(info, indent=2, ensure_ascii=False))]

    else:
        # Dispatch to registered formatters
        formatter = registry.get(name)
        if formatter:
            data = arguments
            is_valid, error = formatter.validate_input(data)
            if not is_valid:
                return [TextContent(type="text", text=json.dumps({
                    "error": f"Validation failed: {error}"
                }, indent=2))]
            result_embed = formatter.format(data)
            result = {"embeds": [result_embed]}
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}, indent=2))]


async def main():
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
