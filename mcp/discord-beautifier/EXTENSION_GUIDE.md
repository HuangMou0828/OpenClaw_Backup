# Extension Guide

This guide shows how to add new formatter types to discord-beautifier.

## Architecture Overview

The system uses a **registry pattern** for extensibility:

```
User Request → MCP Server → Registry → Formatter → Discord Embed JSON
```

**Key components:**
- `BaseFormatter`: Abstract base class defining the formatter interface
- `FormatterRegistry`: Central registry managing all formatters
- `server.py`: MCP server that routes tool calls to formatters

## Adding a New Formatter Type

### Step 1: Create Formatter Class

Create a new file in `src/formatters/<type>/` directory:

```python
# src/formatters/alert/alert_formatter.py
from typing import Dict, Any
from core.base_formatter import BaseFormatter


class AlertFormatter(BaseFormatter):
    """Formatter for alerts and warnings."""

    def format(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert alert data to Discord embed.

        Args:
            data: {
                "title": "Alert title",
                "message": "Alert message",
                "severity": "critical|high|medium|low",
                "source": "System name",
                "timestamp": "2024-03-15 14:30"
            }

        Returns:
            Discord embed dict
        """
        severity = data.get("severity", "medium")
        
        # Severity colors
        severity_colors = {
            "critical": 15158332,  # Red
            "high": 15105570,      # Orange
            "medium": 16776960,    # Yellow
            "low": 3447003         # Blue
        }
        
        severity_icons = {
            "critical": "🚨",
            "high": "⚠️",
            "medium": "⚡",
            "low": "ℹ️"
        }
        
        icon = severity_icons.get(severity, "⚠️")
        color = severity_colors.get(severity, 15105570)
        
        embed = {
            "title": f"{icon} {data.get('title', 'Alert')}",
            "description": data.get("message", ""),
            "color": color,
            "fields": []
        }
        
        # Add severity field
        embed["fields"].append({
            "name": "严重程度",
            "value": severity.upper(),
            "inline": True
        })
        
        # Add source field
        if "source" in data:
            embed["fields"].append({
                "name": "来源",
                "value": data["source"],
                "inline": True
            })
        
        # Add footer
        timestamp = data.get("timestamp", "")
        embed["footer"] = {"text": f"🚨 Alert · {timestamp}"}
        
        return embed

    def validate_input(self, data: Dict[str, Any]) -> tuple[bool, str]:
        """Validate alert input."""
        if "title" not in data:
            return False, "Missing required field: title"
        
        if "message" not in data:
            return False, "Missing required field: message"
        
        severity = data.get("severity")
        if severity and severity not in ["critical", "high", "medium", "low"]:
            return False, f"Invalid severity: {severity}"
        
        return True, None

    def get_tool_name(self) -> str:
        return "format_alert"

    def get_tool_description(self) -> str:
        return (
            "Format alerts and warnings as Discord embed. "
            "Supports severity levels (critical/high/medium/low) with color coding."
        )

    def get_tool_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Alert title"
                },
                "message": {
                    "type": "string",
                    "description": "Alert message"
                },
                "severity": {
                    "type": "string",
                    "description": "Severity level",
                    "enum": ["critical", "high", "medium", "low"],
                    "default": "medium"
                },
                "source": {
                    "type": "string",
                    "description": "Alert source system"
                },
                "timestamp": {
                    "type": "string",
                    "description": "Alert timestamp"
                }
            },
            "required": ["title", "message"]
        }
```

### Step 2: Create `__init__.py`

```python
# src/formatters/alert/__init__.py
"""Init file for alert formatters package"""
```

### Step 3: Register in `server.py`

Add import and registration:

```python
# In src/server.py

# Add import at top
from formatters.alert.alert_formatter import AlertFormatter

# In the registration section (after other registry.register calls)
registry.register(AlertFormatter())
```

That's it! The new `format_alert` tool is now available.

### Step 4: Test

```python
# Test input
{
  "title": "Database Connection Lost",
  "message": "Production database unreachable since 14:30 UTC",
  "severity": "critical",
  "source": "Monitoring System",
  "timestamp": "2024-03-15 14:30"
}
```

## Formatter Interface Reference

### Required Methods

#### `format(data: Dict[str, Any]) -> Dict[str, Any]`
Convert input data to Discord embed dict.

**Returns:** Discord embed with these fields:
- `title` (string): Embed title
- `description` (string): Main content
- `color` (int): Decimal color code
- `fields` (array): List of `{name, value, inline}` objects
- `footer` (object): `{text, icon_url}` object

#### `get_tool_name() -> str`
Return MCP tool name (e.g., `"format_alert"`).

#### `get_tool_description() -> str`
Return human-readable tool description.

#### `get_tool_schema() -> Dict[str, Any]`
Return JSON schema for input validation.

### Optional Methods

#### `validate_input(data: Dict[str, Any]) -> tuple[bool, str]`
Validate input data before formatting.

**Returns:** `(is_valid, error_message)`

## Best Practices

### 1. Color Consistency

Use consistent colors for similar concepts:
- Success: `3066993` (green)
- Error: `15158332` (red)
- Warning: `15105570` (orange)
- Info: `3447003` (blue)
- Rainbow: Use `get_rainbow_color()` from `styles.presets`

### 2. Field Limits

Discord has limits:
- Title: 256 characters
- Description: 4096 characters
- Fields: Max 25 fields
- Field name: 256 characters
- Field value: 1024 characters
- Footer text: 2048 characters

Truncate content to stay within limits.

### 3. Input Validation

Always validate required fields in `validate_input()`:

```python
def validate_input(self, data):
    if "required_field" not in data:
        return False, "Missing required field: required_field"
    return True, None
```

### 4. Schema Documentation

Provide clear descriptions in schema:

```python
def get_tool_schema(self):
    return {
        "type": "object",
        "properties": {
            "field_name": {
                "type": "string",
                "description": "Clear description of what this field does"
            }
        },
        "required": ["field_name"]
    }
```

### 5. Error Handling

Let exceptions bubble up to `server.py` - it handles error formatting:

```python
def format(self, data):
    # Don't wrap in try/except - server.py handles it
    return embed
```

## Examples of Formatter Types

### Simple Formatter (Minimal Fields)

```python
class SimpleFormatter(BaseFormatter):
    def format(self, data):
        return {
            "title": data["title"],
            "description": data["content"],
            "color": 3447003
        }
```

### Complex Formatter (Multiple Fields)

```python
class ComplexFormatter(BaseFormatter):
    def format(self, data):
        embed = {
            "title": data["title"],
            "color": 3447003,
            "fields": []
        }
        
        for item in data["items"]:
            embed["fields"].append({
                "name": item["name"],
                "value": item["value"],
                "inline": item.get("inline", False)
            })
        
        return embed
```

### Dynamic Color Formatter

```python
from styles.presets import get_rainbow_color

class DynamicFormatter(BaseFormatter):
    def format(self, data):
        return {
            "title": data["title"],
            "color": get_rainbow_color(),  # Daily rotating color
            "description": data["content"]
        }
```

## Testing Your Formatter

### 1. Unit Test

```python
# tests/test_alert_formatter.py
from formatters.alert.alert_formatter import AlertFormatter

def test_alert_formatter():
    formatter = AlertFormatter()
    
    data = {
        "title": "Test Alert",
        "message": "Test message",
        "severity": "high"
    }
    
    result = formatter.format(data)
    
    assert "title" in result
    assert result["title"].startswith("⚠️")
    assert result["color"] == 15105570  # Orange
```

### 2. Integration Test

Start the MCP server and test with your agent:

```bash
python src/server.py
```

Then in your agent:
```
Format this alert for Discord:
{
  "title": "Test Alert",
  "message": "This is a test",
  "severity": "critical"
}
```

## Common Patterns

### Pattern 1: Status-Based Formatting

```python
STATUS_CONFIG = {
    "success": {"color": 3066993, "icon": "✅"},
    "failure": {"color": 15158332, "icon": "❌"}
}

def format(self, data):
    status = data["status"]
    config = STATUS_CONFIG[status]
    
    return {
        "title": f"{config['icon']} {data['title']}",
        "color": config["color"]
    }
```

### Pattern 2: List Aggregation

```python
def format(self, data):
    embed = {"title": data["title"], "fields": []}
    
    for item in data["items"][:25]:  # Discord limit
        embed["fields"].append({
            "name": item["name"],
            "value": item["value"][:1024],  # Truncate
            "inline": False
        })
    
    return embed
```

### Pattern 3: Metrics Display

```python
def format(self, data):
    metrics = data["metrics"]
    
    metrics_text = "\n".join([
        f"✅ Success: {metrics['success']}",
        f"❌ Failed: {metrics['failed']}",
        f"⏱️ Duration: {metrics['duration']}"
    ])
    
    return {
        "title": data["title"],
        "fields": [{"name": "📊 Metrics", "value": metrics_text}]
    }
```

## Troubleshooting

### Formatter not showing up

Check:
1. Formatter is imported in `server.py`
2. `registry.register()` is called
3. `get_tool_name()` returns unique name

### Validation errors

Check:
1. `validate_input()` returns `(True, None)` for valid input
2. Required fields are present in input
3. Schema matches actual validation logic

### Embed not rendering

Check:
1. Color is decimal (not hex)
2. Field values are strings
3. Lengths are within Discord limits
4. Return format is `{"embeds": [embed_dict]}`

## Next Steps

- Add tests for your formatter
- Update `examples/usage.md` with examples
- Create a skill file in `skills/` directory
- Submit a PR if contributing to the project
