# Usage Examples

## Basic Usage

### 1. Format Markdown as Discord Embed

**Input:**
```markdown
# Breaking: New AI Model Released
OpenAI announced GPT-5 today with 10x performance improvements.
The model features enhanced reasoning and multimodal capabilities.

Source: TechCrunch | 2024-03-15
```

**Agent command:**
```
Format this as a Discord news card: [paste markdown above]
```

**Output:**
```json
{
  "embeds": [{
    "title": "📰 Breaking: New AI Model Released",
    "description": "OpenAI announced GPT-5 today with 10x performance improvements.\nThe model features enhanced reasoning and multimodal capabilities.",
    "color": 3447003,
    "footer": {
      "text": "📰 TechCrunch · 2024-03-15"
    }
  }]
}
```

---

### 2. Format JSON as Discord Embed

**Input:**
```json
{
  "headline": "Server Maintenance Scheduled",
  "content": "Database maintenance window: 2024-03-20 02:00-04:00 UTC",
  "source": "DevOps Team",
  "time": "2024-03-15"
}
```

**Agent command:**
```
Format this as a Discord alert: [paste JSON above]
```

**Output:**
```json
{
  "embeds": [{
    "title": "⚠️ Server Maintenance Scheduled",
    "description": "Database maintenance window: 2024-03-20 02:00-04:00 UTC",
    "color": 15158332,
    "footer": {
      "text": "⚠️ DevOps Team · 2024-03-15"
    }
  }]
}
```

---

### 3. Auto-Style Detection

**Input:**
```markdown
# Version 2.0 Released
- New dashboard UI
- Performance improvements
- Bug fixes

Source: Engineering Team | 2024-03-15
```

**Agent command:**
```
Format this for Discord (auto-detect style): [paste markdown above]
```

**Output:**
```json
{
  "embeds": [{
    "title": "🚀 Version 2.0 Released",
    "description": "- New dashboard UI\n- Performance improvements\n- Bug fixes",
    "color": 3066993,
    "footer": {
      "text": "🚀 Engineering Team · 2024-03-15"
    }
  }]
}
```

---

## Advanced Usage

### 4. With Fields (Subheadings)

**Input:**
```markdown
# Q1 Performance Report

## Revenue
$2.5M (+25% YoY)

## Customer Satisfaction
92% (target: 90%)

## Active Users
15,000 (+30% MoM)

Source: Analytics Team | 2024-03-31
```

**Output:**
```json
{
  "embeds": [{
    "title": "📊 Q1 Performance Report",
    "color": 10181046,
    "fields": [
      {
        "name": "Revenue",
        "value": "$2.5M (+25% YoY)",
        "inline": false
      },
      {
        "name": "Customer Satisfaction",
        "value": "92% (target: 90%)",
        "inline": false
      },
      {
        "name": "Active Users",
        "value": "15,000 (+30% MoM)",
        "inline": false
      }
    ],
    "footer": {
      "text": "📊 Analytics Team · 2024-03-31"
    }
  }]
}
```

---

## Integration with OpenClaw

### Example Workflow

1. **Generate content with LLM:**
```
User: Summarize today's tech news
OpenClaw: [generates markdown summary]
```

2. **Format for Discord:**
```
User: Format that as Discord
OpenClaw: [calls format_as_discord_embed tool]
```

3. **Send to Discord:**
```
User: Send it to our #news channel
OpenClaw: [calls send_to_discord with webhook URL]
```

---

## Style Presets

| Style | Color | Icon | Use Case |
|-------|-------|------|----------|
| `news` | Blue | 📰 | News articles, announcements |
| `report` | Purple | 📊 | Reports, summaries, analytics |
| `alert` | Red | ⚠️ | Alerts, warnings, errors |
| `changelog` | Green | 🚀 | Releases, updates, changelogs |
| `auto` | - | - | Auto-detect based on content |

---

---

## New Formatter Types

### 5. News Digest (Multi-Article)

**Tool:** `format_news_digest`

**Input:**
```json
{
  "articles": [
    {
      "headline": "AI Startup Raises $100M",
      "summary": "TechVenture AI secures Series B funding led by Sequoia Capital",
      "source": "VentureBeat",
      "category": "tech",
      "url": "https://example.com/article1",
      "published_at": "2024-03-15 08:00"
    },
    {
      "headline": "New Climate Report Released",
      "summary": "UN report shows accelerating climate change impacts",
      "source": "Reuters",
      "category": "science",
      "url": "https://example.com/article2",
      "published_at": "2024-03-15 09:30"
    }
  ],
  "digest_title": "今日科技资讯",
  "style": "tech",
  "timestamp": "2024-03-15 10:00"
}
```

**Output:**
```json
{
  "embeds": [{
    "title": "📰 今日科技资讯",
    "color": 3447003,
    "fields": [
      {
        "name": "TECH | AI Startup Raises $100M",
        "value": "TechVenture AI secures Series B funding led by Sequoia Capital\n[阅读原文](https://example.com/article1) · VentureBeat",
        "inline": false
      },
      {
        "name": "SCIENCE | New Climate Report Released",
        "value": "UN report shows accelerating climate change impacts\n[阅读原文](https://example.com/article2) · Reuters",
        "inline": false
      }
    ],
    "footer": {
      "text": "🌈 共 2 条资讯 · 2024-03-15 10:00"
    }
  }]
}
```

---

### 6. Task Report

**Tool:** `format_task_report`

**Input:**
```json
{
  "title": "Daily Backup Report",
  "report_type": "daily_summary",
  "status": "success",
  "metrics": {
    "completed": 5,
    "failed": 0,
    "duration": "2m 30s"
  },
  "details": [
    {
      "name": "Database Backup",
      "value": "✅ Completed (1.2GB)",
      "inline": true
    },
    {
      "name": "File Backup",
      "value": "✅ Completed (3.5GB)",
      "inline": true
    }
  ],
  "summary": "All backup tasks completed successfully",
  "timestamp": "2024-03-15 02:00"
}
```

**Output:**
```json
{
  "embeds": [{
    "title": "✅ Daily Backup Report",
    "description": "All backup tasks completed successfully",
    "color": 3066993,
    "fields": [
      {
        "name": "📊 执行统计",
        "value": "✅ 完成: 5\n❌ 失败: 0\n⏱️ 耗时: 2m 30s",
        "inline": false
      },
      {
        "name": "Database Backup",
        "value": "✅ Completed (1.2GB)",
        "inline": true
      },
      {
        "name": "File Backup",
        "value": "✅ Completed (3.5GB)",
        "inline": true
      }
    ],
    "footer": {
      "text": "🤖 每日汇总 · 2024-03-15 02:00"
    }
  }]
}
```

---

### 7. Task Report with Failure

**Input:**
```json
{
  "title": "Build Pipeline Failed",
  "report_type": "build_status",
  "status": "failure",
  "metrics": {
    "completed": 3,
    "failed": 2,
    "duration": "8m 15s"
  },
  "details": [
    {
      "name": "Unit Tests",
      "value": "✅ Passed (120/120)",
      "inline": false
    },
    {
      "name": "Integration Tests",
      "value": "❌ Failed (5/10)\nError: Database connection timeout",
      "inline": false
    }
  ],
  "summary": "Build failed due to integration test failures",
  "timestamp": "2024-03-15 14:30"
}
```

**Output:**
```json
{
  "embeds": [{
    "title": "❌ Build Pipeline Failed",
    "description": "Build failed due to integration test failures",
    "color": 15158332,
    "fields": [
      {
        "name": "📊 执行统计",
        "value": "✅ 完成: 3\n❌ 失败: 2\n⏱️ 耗时: 8m 15s",
        "inline": false
      },
      {
        "name": "Unit Tests",
        "value": "✅ Passed (120/120)",
        "inline": false
      },
      {
        "name": "Integration Tests",
        "value": "❌ Failed (5/10)\nError: Database connection timeout",
        "inline": false
      }
    ],
    "footer": {
      "text": "🤖 构建状态 · 2024-03-15 14:30"
    }
  }]
}
```

---

## Tips

1. **Markdown structure matters:**
   - `# Heading` → embed title
   - `## Subheading` → embed field
   - `Source: X | Date: Y` → footer

2. **Keep it concise:**
   - Title: max 256 chars
   - Description: max 4096 chars
   - Fields: max 25 fields

3. **Use auto-style for flexibility:**
   - Keywords like "alert", "warning" → red alert style
   - Keywords like "release", "update" → green changelog style
   - Keywords like "news", "breaking" → blue news style

4. **JSON mapping:**
   - `headline`/`title` → embed title
   - `content`/`description` → embed description
   - `source` + `time`/`date` → footer

5. **Choose the right formatter:**
   - `format_as_discord_embed`: Generic content, backward compatible
   - `format_news_digest`: Multiple news articles with categories
   - `format_task_report`: Task execution results with metrics
