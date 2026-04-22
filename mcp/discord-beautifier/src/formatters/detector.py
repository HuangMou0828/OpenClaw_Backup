"""Auto-detect input format (markdown vs json)"""

import json


def detect_format(content: str) -> str:
    """Detect if content is markdown or json.

    Args:
        content: Input string

    Returns:
        "markdown" or "json"
    """
    content = content.strip()

    # Try parsing as JSON
    if content.startswith(("{", "[")):
        try:
            json.loads(content)
            return "json"
        except json.JSONDecodeError:
            pass

    # Default to markdown
    return "markdown"
