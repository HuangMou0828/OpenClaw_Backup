# Project Structure

```
discord-beautifier/
├── src/
│   ├── core/                          # Core framework
│   │   ├── __init__.py
│   │   ├── base_formatter.py          # Abstract base class for all formatters
│   │   └── registry.py                # Formatter registry for dynamic routing
│   │
│   ├── formatters/                    # Formatter implementations
│   │   ├── __init__.py
│   │   ├── detector.py                # Auto-detect markdown/json
│   │   ├── markdown.py                # Markdown parser
│   │   ├── json_formatter.py          # JSON parser
│   │   ├── generic_formatter.py       # Generic formatter (backward compatible)
│   │   │
│   │   ├── news/                      # News digest formatters
│   │   │   ├── __init__.py
│   │   │   └── news_formatter.py      # Multi-article news digest
│   │   │
│   │   └── task/                      # Task report formatters
│   │       ├── __init__.py
│   │       └── task_formatter.py      # Task execution reports
│   │
│   ├── styles/                        # Color and style presets
│   │   ├── __init__.py
│   │   └── presets.py                 # Rainbow colors + preset styles
│   │
│   ├── server.py                      # MCP server entry point
│   └── utils.py                       # Utility functions
│
├── skills/                            # Agent skill definitions
│   ├── discord-output.md              # Generic formatting skill
│   ├── discord-news.md                # News formatting skill
│   ├── discord-news-digest.md         # News digest skill
│   └── discord-task-report.md         # Task report skill
│
├── examples/                          # Usage examples and configs
│   ├── usage.md                       # Detailed usage examples
│   ├── openclaw-config.json           # OpenClaw MCP configuration
│   └── claude-config.json             # Claude Code MCP configuration
│
├── pyproject.toml                     # Python project metadata
├── README.md                          # Main documentation
├── EXTENSION_GUIDE.md                 # Guide for adding new formatters
├── LICENSE                            # MIT license
└── .gitignore                         # Git ignore rules
```

## Architecture Overview

### Core Layer (`src/core/`)

**BaseFormatter** - Abstract base class defining the formatter interface:
- `format(data)` - Convert input to Discord embed
- `validate_input(data)` - Validate input structure
- `get_tool_name()` - Return MCP tool name
- `get_tool_description()` - Return tool description
- `get_tool_schema()` - Return JSON schema for input

**FormatterRegistry** - Central registry managing all formatters:
- `register(formatter)` - Register a formatter instance
- `get(tool_name)` - Get formatter by tool name
- `list_all()` - Get all registered formatters

### Formatter Layer (`src/formatters/`)

**Generic Formatter** - Backward compatible with original tool:
- Tool: `format_as_discord_embed`
- Auto-detects markdown/json
- Applies preset styles (news/report/alert/changelog/rainbow)

**News Formatter** - Multi-article news digests:
- Tool: `format_news_digest`
- Handles multiple articles with categories
- Supports tech/finance/sports styles
- Rainbow color by default

**Task Formatter** - Task execution reports:
- Tool: `format_task_report`
- Status-based coloring (success/failure/warning/info)
- Metrics display (completed/failed/duration)
- Detailed breakdowns

### Style Layer (`src/styles/`)

**Rainbow Color System** - Daily rotating colors (Shanghai timezone):
- 周日: 🔴 红 #EB2F2F
- 周一: 🟠 橙 #E8642C
- 周二: 🟡 黄 #F5A623
- 周三: 🟢 绿 #44D1A5
- 周四: 🔵 蓝 #3B82F6
- 周五: 🟣 紫 #A855F7
- 周六: 🌈 靛 #6366F1

**Preset Styles**:
- `news` - Blue with 📰 icon
- `report` - Purple with 📊 icon
- `alert` - Red with ⚠️ icon
- `changelog` - Green with 🚀 icon
- `rainbow` - Daily rotating color with 🌈 icon

### Server Layer (`src/server.py`)

**MCP Server** - Entry point for all tool calls:
1. Registers all formatters on startup
2. Generates tool definitions from formatters
3. Routes tool calls to appropriate formatter
4. Handles utility tools (send_to_discord, etc.)
5. Returns formatted Discord embed JSON

## Data Flow

```
User Request
    ↓
MCP Server (server.py)
    ↓
Registry.get(tool_name)
    ↓
Formatter.validate_input(data)
    ↓
Formatter.format(data)
    ↓
Style.apply_style(embed, style)
    ↓
Discord Embed JSON
    ↓
User / Discord API
```

## Extension Points

### Adding a New Formatter Type

1. Create `src/formatters/<type>/<type>_formatter.py`
2. Extend `BaseFormatter` class
3. Implement required methods
4. Register in `src/server.py`

See `EXTENSION_GUIDE.md` for detailed instructions.

### Adding a New Style

1. Add color constant to `src/styles/presets.py`
2. Add style config to `PRESET_STYLES` dict
3. Update `apply_style()` function if needed

### Adding a New Skill

1. Create `skills/<skill-name>.md`
2. Add frontmatter with name and description
3. Document usage, parameters, and examples
4. Copy to agent's skills directory

## Key Design Decisions

### Why Registry Pattern?

- **Extensibility**: Add new formatters without modifying server.py
- **Discoverability**: Tools are auto-generated from registered formatters
- **Separation**: Business logic (formatters) separate from routing (server)

### Why BaseFormatter Abstract Class?

- **Contract**: Enforces consistent interface across all formatters
- **Type Safety**: Clear method signatures and return types
- **Documentation**: Self-documenting through method names and schemas

### Why Separate Formatter Types?

- **Specialization**: Each type optimized for its use case
- **Validation**: Type-specific input validation
- **Evolution**: Types can evolve independently

### Why Rainbow Color System?

- **Visual Variety**: Different color each day keeps digests fresh
- **Consistency**: Same color for all digests on a given day
- **Cultural**: Aligns with Shanghai timezone for target users

## File Responsibilities

| File | Responsibility |
|------|----------------|
| `base_formatter.py` | Define formatter interface |
| `registry.py` | Manage formatter instances |
| `generic_formatter.py` | Backward compatibility |
| `news_formatter.py` | News digest formatting |
| `task_formatter.py` | Task report formatting |
| `presets.py` | Colors and styles |
| `server.py` | MCP protocol handling |
| `detector.py` | Input format detection |
| `markdown.py` | Markdown parsing |
| `json_formatter.py` | JSON parsing |

## Dependencies

- `mcp>=1.0.0` - MCP protocol implementation
- `requests` - HTTP requests for Discord API (optional)
- Python 3.10+ - Type hints and modern syntax

## Testing Strategy

1. **Unit Tests**: Test each formatter in isolation
2. **Integration Tests**: Test full MCP tool calls
3. **Manual Tests**: Test with real agents (OpenClaw/Claude)

## Future Extensions

Potential new formatter types:
- `AlertFormatter` - System alerts and warnings
- `ChangelogFormatter` - Release notes and changelogs
- `MetricsFormatter` - Monitoring metrics and dashboards
- `ThreadFormatter` - Multi-message thread formatting
- `PollFormatter` - Interactive polls and surveys
