"""Markdown to Discord embed formatter"""

import re
from typing import Dict, Any, List


def format_markdown(content: str) -> Dict[str, Any]:
    """Convert markdown to Discord embed structure.

    Extracts:
    - Title (# heading or first line)
    - Description (body text)
    - Fields (## subheadings with content)
    - Footer (Source: ... | Date: ... patterns)

    Args:
        content: Markdown string

    Returns:
        Discord embed dict (without color/style)
    """
    lines = content.strip().split("\n")
    embed: Dict[str, Any] = {}
    fields: List[Dict[str, Any]] = []

    title = None
    description_lines = []
    footer_text = None
    current_field = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Extract title (# heading)
        if line.startswith("# "):
            title = line[2:].strip()
            continue

        # Extract fields (## subheading)
        if line.startswith("## "):
            if current_field:
                fields.append(current_field)
            current_field = {"name": line[3:].strip(), "value": "", "inline": False}
            continue

        # Extract footer patterns (Source: ... | Date: ...)
        footer_match = re.search(r"(Source|来源|出处):\s*(.+?)(?:\s*[|·]\s*(.+))?$", line, re.IGNORECASE)
        if footer_match:
            footer_parts = [footer_match.group(2)]
            if footer_match.group(3):
                footer_parts.append(footer_match.group(3))
            footer_text = " · ".join(footer_parts)
            continue

        # Accumulate content
        if current_field:
            current_field["value"] += line + "\n"
        else:
            description_lines.append(line)

    # Finalize last field
    if current_field:
        current_field["value"] = current_field["value"].strip()
        fields.append(current_field)

    # Build embed
    if title:
        embed["title"] = title

    description = "\n".join(description_lines).strip()
    if description:
        embed["description"] = description[:4096]  # Discord limit

    if fields:
        embed["fields"] = fields[:25]  # Discord limit

    if footer_text:
        embed["footer"] = {"text": footer_text[:2048]}  # Discord limit

    return embed
