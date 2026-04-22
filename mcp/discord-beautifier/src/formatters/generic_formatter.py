"""Generic formatter for backward compatibility with original format_as_discord_embed tool"""

from typing import Dict, Any
from core.base_formatter import BaseFormatter
from formatters.detector import detect_format
from formatters.markdown import format_markdown
from formatters.json_formatter import format_json
from styles.presets import apply_style


class GenericFormatter(BaseFormatter):
    """Generic formatter that auto-detects markdown/json and applies styles.

    This maintains backward compatibility with the original format_as_discord_embed tool.
    """

    def format(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format markdown or json content with style.

        Args:
            data: {"content": "...", "style": "auto|news|report|alert|changelog|rainbow"}

        Returns:
            Discord embed dict
        """
        content = data.get("content", "")
        style = data.get("style", "auto")

        # Detect input format
        format_type = detect_format(content)

        # Format based on type
        if format_type == "markdown":
            embed_data = format_markdown(content)
        elif format_type == "json":
            embed_data = format_json(content)
        else:
            return {"description": f"Unsupported format: {format_type}"}

        # Apply style
        styled_embed = apply_style(embed_data, style)

        return styled_embed

    def get_tool_name(self) -> str:
        return "format_as_discord_embed"

    def get_tool_description(self) -> str:
        return (
            "Convert Markdown or JSON content to Discord embed format. "
            "Automatically detects input type and applies styling. "
            "Supports 'rainbow' style which cycles colors by day of week."
        )

    def get_tool_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "Markdown or JSON string to format",
                },
                "style": {
                    "type": "string",
                    "description": "Preset style: auto (default), news, report, alert, changelog, rainbow",
                    "enum": ["auto", "news", "report", "alert", "changelog", "rainbow"],
                    "default": "auto",
                },
            },
            "required": ["content"],
        }
