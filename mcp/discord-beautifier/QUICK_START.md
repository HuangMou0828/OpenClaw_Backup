# Quick Start Guide

Get discord-beautifier running in 5 minutes.

## Installation

```bash
cd /Users/hm/discord-beautifier
pip install -e .
```

## Configuration

### For OpenClaw

Add to your OpenClaw MCP config:

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

### For Claude Code

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

Restart your agent after configuration.

## Test It

### Test 1: Generic Formatting

```
Format this as Discord:
# Hello World
This is a test message.
Source: Test | 2024-03-15
```

Expected: Discord embed JSON with title, description, footer.

### Test 2: News Digest

```
Format this news digest:
{
  "articles": [
    {
      "headline": "Test Article",
      "summary": "This is a test",
      "source": "Test Source",
      "category": "tech"
    }
  ],
  "digest_title": "Test Digest"
}
```

Expected: Discord embed with article field and rainbow color.

### Test 3: Task Report

```
Format this task report:
{
  "title": "Test Report",
  "status": "success",
  "metrics": {
    "completed": 5,
    "failed": 0
  }
}
```

Expected: Discord embed with green color and metrics field.

## Available Tools

After configuration, these tools are available:

1. **format_as_discord_embed** - Generic formatter (markdown/json)
2. **format_news_digest** - Multi-article news digests
3. **format_task_report** - Task execution reports
4. **send_to_discord_via_bot** - Send via Discord bot
5. **send_to_discord** - Send via webhook
6. **get_rainbow_color** - Get today's rainbow color

## Troubleshooting

### Tool not showing up

1. Check MCP config path is correct
2. Restart agent
3. Check Python version (requires 3.10+)

### Import errors

```bash
cd /Users/hm/discord-beautifier
pip install -e .
```

### Server not starting

```bash
# Test server directly
python /Users/hm/discord-beautifier/src/server.py
```

Should start without errors (will wait for stdio input).

## Next Steps

- Read `README.md` for full documentation
- See `examples/usage.md` for more examples
- Check `EXTENSION_GUIDE.md` to add custom formatters
- Review `ARCHITECTURE.md` to understand the design

## Common Use Cases

### Daily News Digest

```
Create a tech news digest with today's articles and format for Discord
```

### Build Status Report

```
Format the latest build results as a Discord task report
```

### Generic Content

```
Format this markdown as Discord with rainbow style
```

## Getting Help

- Check `examples/usage.md` for examples
- Read `EXTENSION_GUIDE.md` for customization
- Review `ARCHITECTURE.md` for design details
- Open an issue on GitHub for bugs
