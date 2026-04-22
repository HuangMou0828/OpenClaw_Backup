---
name: discord-news-digest
description: Format multiple news articles as a Discord news digest with categories and sources
---

# Discord News Digest

Format multiple news articles as a structured Discord embed with categories, sources, and links.

## Usage

When the user wants to format multiple news articles or create a news digest for Discord, use the `format_news_digest` tool.

## Parameters

- `articles` (array, required): List of news articles
  - `headline` (string, required): Article headline
  - `summary` (string): Brief summary
  - `source` (string): Source name
  - `category` (string): Category (tech/finance/sports/etc)
  - `url` (string): Article URL
  - `published_at` (string): Publication time
- `digest_title` (string): Title for the digest (default: "今日资讯")
- `style` (string): Visual style - `default` (rainbow), `tech`, `finance`, `sports`
- `timestamp` (string): Digest timestamp

## Examples

**Tech news digest:**
```
Format these tech articles as a Discord digest:
[
  {
    "headline": "AI Startup Raises $100M",
    "summary": "TechVenture AI secures Series B funding",
    "source": "VentureBeat",
    "category": "tech",
    "url": "https://..."
  }
]
```

**Multi-category digest:**
```
Create a news digest with these articles:
- Tech: AI breakthrough announced
- Finance: Stock market hits record high
- Sports: Championship finals results
```

## Output

Returns Discord embed JSON with:
- Title with 📰 icon
- Each article as a field with category prefix
- Links to original articles
- Total article count in footer
- Rainbow color by default (cycles by day of week)

## Tips

- Supports up to 10 articles (Discord field limit: 25)
- Use `style="tech"` for tech-focused digests (blue color)
- Use `style="finance"` for finance news (green color)
- Use `style="default"` for rainbow color (changes daily)
- Summaries are truncated to 200 chars for readability
