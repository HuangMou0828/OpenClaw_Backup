---
name: discord-news
description: Format news articles as Discord news cards with automatic metadata extraction
---

# Discord News

Specialized skill for formatting news articles as Discord embed cards with news styling.

## Usage

When the user wants to format news content for Discord, automatically extract:
- Headline (becomes embed title with 📰 icon)
- Article content (becomes description)
- Source and date (becomes footer)

Always use `style="news"` for consistent news card appearance.

## Examples

**Input:**
```
Format this news for Discord:
# AI Startup Raises $100M Series B
TechVenture AI announced today it has raised $100 million in Series B funding 
led by Sequoia Capital. The company plans to expand its team and accelerate 
product development.
Source: VentureBeat | 2024-03-15
```

**Your response:**
Call `format_as_discord_embed` with:
- content: [the markdown above]
- style: "news"

## Tips

- Always use blue color scheme (news preset)
- Extract source and date into footer
- Keep descriptions concise (under 2000 chars)
- Add 📰 emoji prefix automatically
