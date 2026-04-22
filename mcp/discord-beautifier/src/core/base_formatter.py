"""Base formatter interface for all Discord embed formatters"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseFormatter(ABC):
    """Abstract base class for all formatters.

    Each formatter handles a specific information type (news, task, alert, etc.)
    and converts structured data into Discord embed format.
    """

    @abstractmethod
    def format(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert input data to Discord embed dict.

        Args:
            data: Structured input data (format depends on formatter type)

        Returns:
            Discord embed dict with title, description, fields, color, footer, etc.
        """
        pass

    def validate_input(self, data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate input data structure.

        Args:
            data: Input data to validate

        Returns:
            (is_valid, error_message)
        """
        # Default: no validation
        return True, None

    def get_tool_schema(self) -> Dict[str, Any]:
        """Return JSON schema for this formatter's input.

        Used to generate MCP tool definitions.

        Returns:
            JSON schema dict
        """
        return {
            "type": "object",
            "properties": {},
            "required": []
        }

    def get_tool_name(self) -> str:
        """Return the MCP tool name for this formatter.

        Returns:
            Tool name (e.g., "format_news_digest")
        """
        return "format_unknown"

    def get_tool_description(self) -> str:
        """Return human-readable description for this formatter.

        Returns:
            Tool description
        """
        return "Format data as Discord embed"
