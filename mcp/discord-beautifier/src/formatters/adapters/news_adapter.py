"""AI News Digest adapter - optimized for Discord field-based layout.

Parsing strategy:
  - Parse Markdown into structured articles
  - Each article becomes a Discord field (not crammed into description)
  - Category icons as field name prefixes
  - Summary truncated to ~150 chars for readability
  - Description shows category overview

Full format (LLM generates this):
  ## 🔥 本日最重要的3条
  ### 1️⃣ 标题
  Long summary paragraph...
  📍 https://...

Compact format (fallback):
  🔥 本日头条（3条）：Title1、Title2...
"""

import re
from typing import Dict, Any, List


CATEGORY_MAP = {
    "🔥": "头条",
    "🏭": "产业",
    "🤖": "模型",
    "💡": "洞察",
    "🛠": "工具",
    "📊": "数据",
    "🔧": "技术",
    "🧠": "模型",
    "🛠️": "工具",
}

CATEGORY_ICONS = {
    "头条": "🔥",
    "产业": "🏭",
    "模型": "🤖",
    "洞察": "💡",
    "工具": "🛠",
    "数据": "📊",
    "技术": "🔧",
    "其他": "📋",
}


def parse_ai_news_markdown(markdown_text: str) -> Dict[str, Any]:
    """Parse AI news Markdown into structured articles.

    Returns:
      {
        "articles": [{"headline", "summary", "url", "category"}, ...],
        "categories": {"头条": [...], "产业": [...]},
        "date": "2024-03-15",
        "format": "full" | "compact"
      }
    """
    text = markdown_text.strip()

    # Detect format
    if re.search(r"###\s*[1１](?:\uFE0F[\u20E3])?[\u20E3]?|###\s*[1１][.．]", text):
        return _parse_full_format(text)
    else:
        return _parse_compact_format(text)


def _parse_full_format(text: str) -> Dict[str, Any]:
    """Parse full format with section headers and article blocks."""
    articles: List[Dict[str, str]] = []
    categories: Dict[str, List[Dict[str, str]]] = {}
    current_category = "其他"

    lines = text.split("\n")
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i].strip()

        # Category section: ## 🔥 category name
        cat_match = re.match(r"##\s*([🔥🏭🤖💡🛠📊🔧🧠🛠️])\s*(.+)", line)
        if cat_match:
            emoji = cat_match.group(1)
            cat_name = cat_match.group(2).strip()
            current_category = CATEGORY_MAP.get(emoji, cat_name)
            if current_category not in categories:
                categories[current_category] = []
            i += 1
            continue

        # Article header: ### 1️⃣ Article Title
        art_match = re.match(r"###\s*[1-9１-９](?:\uFE0F[\u20E3])?[\u20E3]?\s*(.+)$", line)
        if art_match:
            headline = art_match.group(1).strip()
            summary_parts: List[str] = []
            url = ""

            # Collect content until separator/next article/new section
            i += 1
            while i < n:
                content_line = lines[i].strip()

                # Stop conditions
                if content_line in ("---", "——", "--") or content_line.startswith("---"):
                    i += 1
                    break
                if re.match(r"###\s*[1-9１-９]", content_line):
                    break
                if re.match(r"##\s*", content_line):
                    break

                # Extract URL
                url_match = re.search(r"📍\s*(https?://[^\s]+)", content_line)
                if url_match:
                    url = url_match.group(1).rstrip(".,;:")
                elif content_line and not content_line.startswith("📍"):
                    summary_parts.append(content_line)

                i += 1

            summary = " ".join(summary_parts).strip()

            # Truncate summary to ~200 chars for field display
            if len(summary) > 200:
                summary = summary[:197] + "..."

            article = {
                "headline": headline,
                "summary": summary,
                "url": url,
                "category": current_category,
            }
            articles.append(article)
            if current_category not in categories:
                categories[current_category] = []
            categories[current_category].append(article)
            continue

        # Bullet item: - **Title** — Summary
        bullet_match = re.match(r"-\s+\*\*(.+?)\*\*(?:\s*[—\-]\s*(.*))?$", line)
        if bullet_match:
            headline = bullet_match.group(1).strip()
            summary = bullet_match.group(2).strip() if bullet_match.group(2) else ""

            # Truncate summary
            if len(summary) > 200:
                summary = summary[:197] + "..."

            # Look for URL on next lines
            url = ""
            j = i + 1
            while j < min(i + 4, n):
                url_match = re.search(r"📍\s*(https?://[^\s]+)", lines[j].strip())
                if url_match:
                    url = url_match.group(1).rstrip(".,;:")
                    break
                if lines[j].strip() and not lines[j].strip().startswith("📍"):
                    if not lines[j].strip().startswith("- "):
                        break
                j += 1

            article = {
                "headline": headline,
                "summary": summary,
                "url": url,
                "category": current_category,
            }
            articles.append(article)
            if current_category not in categories:
                categories[current_category] = []
            categories[current_category].append(article)

        i += 1

    date = extract_date_from_markdown(text)

    return {
        "articles": articles,
        "categories": categories,
        "date": date,
        "format": "full",
    }


def _parse_compact_format(text: str) -> Dict[str, Any]:
    """Parse compact format: 🔥 头条（3条）：Title1、Title2..."""
    articles: List[Dict[str, str]] = []
    categories: Dict[str, List[Dict[str, str]]] = {}

    lines = text.split("\n")
    current_emoji = None
    current_category = "其他"

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Detect category line: 🔥 头条（3条）：...
        cat_match = re.match(r"^([🔥🏭🤖💡🛠📊🔧🧠🛠️])\s*(.+?)(?:（\d+条）)?[：:]\s*(.+)", line)
        if cat_match:
            current_emoji = cat_match.group(1)
            cat_name = cat_match.group(2).strip()
            current_category = CATEGORY_MAP.get(current_emoji, cat_name)
            line = cat_match.group(3)
        elif current_emoji:
            # Continuation line
            colon_idx = line.find("：")
            if colon_idx == -1:
                colon_idx = line.find(":")
            if colon_idx != -1:
                line = line[colon_idx + 1:].strip()
            else:
                continue

        # Parse items separated by 、 or |
        if current_emoji and line:
            items = re.split(r"[、|｜～]\s*", line)
            for item in items:
                item = item.strip()
                if not item:
                    continue
                item = re.sub(r"^[•\-\*]\s*", "", item)

                # Split title — summary
                if "—" in item:
                    parts = item.split("—", 1)
                elif " - " in item:
                    parts = item.split(" - ", 1)
                else:
                    parts = [item, ""]

                headline = parts[0].strip()
                summary = parts[1].strip() if len(parts) > 1 else ""

                # Truncate summary
                if len(summary) > 200:
                    summary = summary[:197] + "..."

                if headline:
                    article = {
                        "headline": headline,
                        "summary": summary,
                        "url": "",
                        "category": current_category,
                    }
                    articles.append(article)
                    if current_category not in categories:
                        categories[current_category] = []
                    categories[current_category].append(article)

    return {
        "articles": articles,
        "categories": categories,
        "date": "",
        "format": "compact",
    }


def extract_date_from_markdown(markdown_text: str) -> str:
    """Extract date string from markdown."""
    match = re.search(r"(\d{4}[年.\-/]\d{2}[月.\-/]\d{2}[日]?)", markdown_text)
    if match:
        date_str = match.group(1)
        date_str = date_str.replace("年", "-").replace("月", "-").replace("日", "")
        return date_str.strip(".-/")
    return ""


def build_news_embed(parsed: Dict[str, Any], digest_title: str = "AI 热点日报") -> Dict[str, Any]:
    """Build Discord embed from parsed news data.

    Strategy:
      - Title: digest title + day of week
      - Description: category overview (e.g., "头条 3 · 产业 4 · 模型 3")
      - Fields: each article as a field (icon + headline as name, summary + url as value)
      - Footer: total count + date
      - Color: rainbow (set by caller)
    """
    from styles.presets import get_rainbow_info

    articles = parsed.get("articles", [])
    categories = parsed.get("categories", {})
    date = parsed.get("date", "")

    if not articles:
        return {
            "title": f"📰 {digest_title}",
            "description": "暂无资讯",
            "color": 3447003,
            "fields": [],
        }

    # Build category overview for description
    rainbow_info = get_rainbow_info()
    day_name = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"][rainbow_info["day_index"]]

    cat_summary = []
    for cat_name, cat_articles in categories.items():
        icon = CATEGORY_ICONS.get(cat_name, "📋")
        cat_summary.append(f"{icon} {cat_name} {len(cat_articles)}")

    description = "今日资讯：" + " · ".join(cat_summary)

    # Build fields (one per article, limit to 15 for readability)
    fields = []
    for article in articles[:15]:
        cat_icon = CATEGORY_ICONS.get(article["category"], "📋")
        field_name = f"{cat_icon} {article['headline']}"

        # Truncate field name to 256 chars (Discord limit)
        if len(field_name) > 256:
            field_name = field_name[:253] + "..."

        # Build field value
        value_parts = []
        if article["summary"]:
            value_parts.append(article["summary"])
        if article["url"]:
            value_parts.append(f"📍 [阅读原文]({article['url']})")

        field_value = "\n".join(value_parts) if value_parts else "无内容"

        # Truncate field value to 1024 chars (Discord limit)
        if len(field_value) > 1024:
            field_value = field_value[:1021] + "..."

        fields.append({
            "name": field_name,
            "value": field_value,
            "inline": False
        })

    # Build footer
    footer_text = f"🌈 共 {len(articles)} 条资讯"
    if date:
        footer_text += f" · {date}"

    embed = {
        "title": f"📰 {digest_title} · {day_name}",
        "description": description,
        "fields": fields,
        "footer": {"text": footer_text},
    }

    return embed
