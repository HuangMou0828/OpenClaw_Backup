---
name: discord-output
description: Format content as beautiful Discord embed cards with automatic styling
---

# Discord Output

Formats Markdown or JSON content as Discord embed cards with automatic styling.

## Usage

When the user wants to format content for Discord output, use the `format_as_discord_embed` tool.

## Parameters

- `content`: Markdown or JSON string to format
- `style`: Optional preset style (auto, news, report, alert, changelog)

## Examples

**News article:**
```
Format this as Discord:
# Breaking: New AI Model Released
OpenAI announced GPT-5 today with 10x performance improvements.
Source: TechCrunch | 2024-03-15
```

**Report:**
```
Format this report for Discord:
# Q1 Performance Summary
Revenue increased 25% YoY. Customer satisfaction at 92%.
```

**Alert:**
```
Send this alert to Discord:
# Critical: Database Connection Lost
Production database unreachable since 14:30 UTC.
```

## Output

Returns Discord embed JSON ready to send via webhook or copy-paste into Discord API.

## Tips

- Use `style="auto"` (default) for automatic style detection
- Markdown headings become embed titles
- Subheadings (##) become fields
- "Source: X | Date: Y" patterns become footers
- JSON input is automatically mapped to embed structure
