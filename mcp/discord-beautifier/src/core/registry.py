"""Formatter registry for dynamic routing"""

from typing import Dict, List, Optional
from core.base_formatter import BaseFormatter


class FormatterRegistry:
    """Central registry for all formatters.

    Manages formatter instances and provides lookup by tool name.
    """

    def __init__(self):
        self._formatters: Dict[str, BaseFormatter] = {}

    def register(self, formatter: BaseFormatter) -> None:
        """Register a formatter instance.

        Args:
            formatter: Formatter instance to register
        """
        tool_name = formatter.get_tool_name()
        self._formatters[tool_name] = formatter

    def get(self, tool_name: str) -> Optional[BaseFormatter]:
        """Get formatter by tool name.

        Args:
            tool_name: MCP tool name

        Returns:
            Formatter instance or None if not found
        """
        return self._formatters.get(tool_name)

    def list_all(self) -> List[BaseFormatter]:
        """Get all registered formatters.

        Returns:
            List of formatter instances
        """
        return list(self._formatters.values())

    def get_tool_names(self) -> List[str]:
        """Get all registered tool names.

        Returns:
            List of tool names
        """
        return list(self._formatters.keys())


# Global registry instance
registry = FormatterRegistry()
