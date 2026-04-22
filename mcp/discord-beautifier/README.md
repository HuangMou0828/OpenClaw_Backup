# Discord Beautifier

**Extensible MCP server for formatting content as beautiful Discord embeds.**

## Features

- 🎨 **Multi-type formatters**: News digests, task reports, and generic content
- 🌈 **Rainbow color system**: Daily rotating colors based on day of week
- 🔧 **Extensible architecture**: Easy to add new formatter types
- 🤖 **MCP compatible**: Works with OpenClaw, Claude Code, and any MCP client
- 🚀 **Zero-config startup**: stdio protocol, no HTTP server needed

## Architecture

```
discord-beautifier/
├── src/
│   ├── core/
│   │   ├── base_formatter.py    # Abstract base class for formatters
│   │   └── registry.py          # Formatter registry for dynamic routing
│   ├── formatters/
│   │   ├── generic_formatter.py # Backward-compatible generic formatter
│   │   ├── news/
│   │   │   └── news_formatter.py    # News digest formatter
│   │   └── task/
│   │       └── task_formatter.py    # Task report formatter
│   ├── styles/
│   │   └── presets.py           # Color presets and rainbow system
│   └── server.py                # MCP server entry point
```

## Installation

```bash
cd discord-beautifier
pip install -e .
```

## Quick Start

### 1. Configure your agent

**OpenClaw:**
```json
{
  "mcpServers": {
    "discord-beautifier": {
      "command": "python",
      "args": ["/path/to/discord-beautifier/src/server.py"]
    }
  }
}
```

**Claude Code:**
Add to `~/.claude/settings.json`:
```json
{
  "mcpServers": {
    "discord-beautifier": {
      "command": "python",
      "args": ["/Users/hm/discord-beautifier/src/server.py"]
    }
  }
}
```

### 2. Use in conversation

**Generic formatting (backward compatible):**
```
Format this as Discord:
# Breaking News
AI startup raises $100M
Source: TechCrunch | 2024-03-15
```

**News digest:**
```
Format these articles as a news digest for Discord:
[
  {
    "headline": "AI Breakthrough",
    "summary": "New model achieves human-level reasoning",
    "source": "Nature",
    "category": "tech",
    "url": "https://..."
  }
]
```

**Task report:**
```
Format this task execution result for Discord:
{
  "title": "Daily Backup Report",
  "status": "success",
  "metrics": {"completed": 5, "failed": 0, "duration": "2m 30s"}
}
```

## Available Tools

### Formatter Tools

#### `format_as_discord_embed`
Generic formatter with auto-detection (backward compatible).

**Input:**
- `content` (string): Markdown or JSON string
- `style` (string): `auto`, `news`, `report`, `alert`, `changelog`, `rainbow`

#### `format_news_digest`
Format news articles and information digests.

**Input:**
- `articles` (array): List of articles with `headline`, `summary`, `source`, `category`, `url`, `published_at`
- `digest_title` (string): Title for the digest (default: "今日资讯")
- `style` (string): `default` (rainbow), `tech`, `finance`, `sports`
- `timestamp` (string): Digest timestamp

#### `format_task_report`
Format task execution reports and daily summaries.

**Input:**
- `title` (string): Report title
- `report_type` (string): `daily_summary`, `cron_result`, `build_status`, `test_result`
- `status` (string): `success`, `failure`, `warning`, `info`
- `metrics` (object): Execution metrics (`completed`, `failed`, `duration`, custom fields)
- `details` (array): Detailed items with `name`, `value`, `inline`
- `summary` (string): Overall summary text
- `timestamp` (string): Report timestamp

### Utility Tools

#### `send_to_discord_via_bot`
Send embed using Discord bot token (faster, higher rate limits).

#### `send_to_discord`
Send embed using Discord webhook URL.

#### `get_rainbow_color`
Get current day's rainbow color info (debugging).

## Rainbow Color System

Colors cycle by day of week (Shanghai timezone UTC+8):

| Day | Color | Hex | Decimal |
|-----|-------|-----|---------|
| 周日 | 🔴 红 | #EB2F2F | 15413039 |
| 周一 | 🟠 橙 | #E8642C | 15229996 |
| 周二 | 🟡 黄 | #F5A623 | 16098851 |
| 周三 | 🟢 绿 | #44D1A5 | 4510117 |
| 周四 | 🔵 蓝 | #3B82F6 | 3900150 |
| 周五 | 🟣 紫 | #A855F7 | 11032055 |
| 周六 | 🌈 靛 | #6366F1 | 6514417 |

## Extending with New Formatters

### 1. Create formatter class

```python
# src/formatters/alert/alert_formatter.py
from core.base_formatter import BaseFormatter

class AlertFormatter(BaseFormatter):
    def format(self, data):
        # Your formatting logic
        return {
            "title": f"⚠️ {data['title']}",
            "color": 15158332,
            "description": data['message']
        }
    
    def get_tool_name(self):
        return "format_alert"
    
    def get_tool_description(self):
        return "Format alerts and warnings"
    
    def get_tool_schema(self):
        return {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "message": {"type": "string"}
            },
            "required": ["title", "message"]
        }
```

### 2. Register in server.py

```python
from formatters.alert.alert_formatter import AlertFormatter

# In server.py, add to registration section:
registry.register(AlertFormatter())
```

That's it! The new formatter is automatically available as an MCP tool.

## Examples

See `examples/` directory for:
- `usage.md`: Detailed usage examples
- `openclaw-config.json`: OpenClaw configuration
- `claude-config.json`: Claude Code configuration

## License

MIT

## Contributing

PRs welcome! To add a new formatter type:
1. Create formatter class extending `BaseFormatter`
2. Implement required methods
3. Register in `server.py`
4. Add tests and examples
