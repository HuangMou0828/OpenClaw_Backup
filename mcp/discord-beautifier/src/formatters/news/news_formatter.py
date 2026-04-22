"""News digest formatter for news/article aggregation"""

from typing import Dict, Any, List
from core.base_formatter import BaseFormatter
from styles.presets import get_rainbow_color


class NewsFormatter(BaseFormatter):
    """Formatter for news articles and information digests.

    Handles external information sources like news, articles, announcements.
    """

    def format(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format news digest as Discord embed.

        Args:
            data: {
                "articles": [
                    {
                        "headline": "...",
                        "summary": "...",
                        "source": "...",
                        "category": "tech|finance|sports|...",
                        "url": "...",
                        "published_at": "..."
                    }
                ],
                "digest_title": "今日资讯",
                "style": "news|tech|finance|default",
                "timestamp": "2024-03-15 08:00"
            }

        Returns:
            Discord embed dict
        """
        articles = data.get("articles", [])
        digest_title = data.get("digest_title", "今日资讯")
        style = data.get("style", "default")
        timestamp = data.get("timestamp", "")

        # Choose color based on style
        color_map = {
            "tech": 3447003,      # Blue
            "finance": 3066993,   # Green
            "sports": 15105570,   # Orange
            "default": get_rainbow_color()  # Rainbow by day
        }
        color = color_map.get(style, color_map["default"])

        # Build embed
        embed = {
            "title": f"📰 {digest_title}",
            "color": color,
            "fields": []
        }

        # Add articles as fields (limit to 10 for Discord)
        for article in articles[:10]:
            category = article.get("category", "").upper()
            headline = article.get("headline", "无标题")
            summary = article.get("summary", "")
            url = article.get("url", "")
            source = article.get("source", "")

            # Build field value
            value_parts = []
            if summary:
                value_parts.append(summary[:200])  # Truncate long summaries

            link_parts = []
            if url:
                link_parts.append(f"[阅读原文]({url})")
            if source:
                link_parts.append(source)

            if link_parts:
                value_parts.append(" · ".join(link_parts))

            field_value = "\n".join(value_parts) if value_parts else "无内容"

            embed["fields"].append({
                "name": f"{category} | {headline}" if category else headline,
                "value": field_value[:1024],  # Discord field value limit
                "inline": False
            })

        # Add footer with count and timestamp
        total_count = len(articles)
        footer_text = f"🌈 共 {total_count} 条资讯"
        if timestamp:
            footer_text += f" · {timestamp}"

        embed["footer"] = {"text": footer_text}

        # Add description if no articles
        if not articles:
            embed["description"] = "暂无资讯"

        return embed

    def validate_input(self, data: Dict[str, Any]) -> tuple[bool, str]:
        """Validate news digest input."""
        if "articles" not in data:
            return False, "Missing required field: articles"

        if not isinstance(data["articles"], list):
            return False, "Field 'articles' must be an array"

        return True, None

    def get_tool_name(self) -> str:
        return "format_news_digest"

    def get_tool_description(self) -> str:
        return (
            "Format news articles and information digests as Discord embed. "
            "Supports multiple articles with categories, sources, and links. "
            "Uses rainbow color by default (cycles by day of week)."
        )

    def get_tool_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "articles": {
                    "type": "array",
                    "description": "Array of news articles",
                    "items": {
                        "type": "object",
                        "properties": {
                            "headline": {"type": "string", "description": "Article headline"},
                            "summary": {"type": "string", "description": "Brief summary"},
                            "source": {"type": "string", "description": "Source name"},
                            "category": {"type": "string", "description": "Category (tech/finance/sports/etc)"},
                            "url": {"type": "string", "description": "Article URL"},
                            "published_at": {"type": "string", "description": "Publication time"}
                        },
                        "required": ["headline"]
                    }
                },
                "digest_title": {
                    "type": "string",
                    "description": "Title for the digest (default: 今日资讯)",
                    "default": "今日资讯"
                },
                "style": {
                    "type": "string",
                    "description": "Visual style (default uses rainbow)",
                    "enum": ["default", "tech", "finance", "sports"],
                    "default": "default"
                },
                "timestamp": {
                    "type": "string",
                    "description": "Digest timestamp"
                }
            },
            "required": ["articles"]
        }
