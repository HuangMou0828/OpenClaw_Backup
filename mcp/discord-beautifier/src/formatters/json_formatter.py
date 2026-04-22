"""JSON to Discord embed formatter"""

import json
from typing import Dict, Any


def format_json(content: str) -> Dict[str, Any]:
    """Convert JSON to Discord embed structure.

    Supports two input formats:
    1. Direct embed format: {"title": "...", "description": "...", ...}
    2. Structured data: {"headline": "...", "content": "...", "source": "...", ...}

    Args:
        content: JSON string

    Returns:
        Discord embed dict (without color/style)
    """
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        return {"description": f"Invalid JSON: {e}"}

    # If already in embed format, return as-is
    if "title" in data or "description" in data or "fields" in data:
        return data

    # Otherwise, map common fields
    embed: Dict[str, Any] = {}

    # Map title variants
    for title_key in ["headline", "title", "subject", "name", "标题"]:
        if title_key in data:
            embed["title"] = str(data[title_key])
            break

    # Map description variants
    for desc_key in ["content", "description", "body", "text", "summary", "内容", "摘要"]:
        if desc_key in data:
            embed["description"] = str(data[desc_key])[:4096]
            break

    # Map footer variants
    footer_parts = []
    for source_key in ["source", "来源", "出处"]:
        if source_key in data:
            footer_parts.append(str(data[source_key]))
            break

    for time_key in ["time", "date", "timestamp", "时间", "日期"]:
        if time_key in data:
            footer_parts.append(str(data[time_key]))
            break

    if footer_parts:
        embed["footer"] = {"text": " · ".join(footer_parts)[:2048]}

    # Map fields (if data has nested objects/arrays)
    fields = []
    for key, value in data.items():
        if key in ["headline", "title", "content", "description", "source", "time", "date", "标题", "内容", "来源", "时间"]:
            continue  # Skip already mapped fields

        if isinstance(value, (dict, list)):
            continue  # Skip complex nested structures

        fields.append({
            "name": key,
            "value": str(value)[:1024],
            "inline": True
        })

    if fields:
        embed["fields"] = fields[:25]  # Discord limit

    return embed
