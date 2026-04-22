---
name: discord-task-report
description: Format task execution results, daily summaries, and build status as Discord embeds
---

# Discord Task Report

Format task execution results, daily summaries, cron job outputs, and build status as structured Discord embeds with metrics and status indicators.

## Usage

When the user wants to format task execution results, daily reports, build status, or test results for Discord, use the `format_task_report` tool.

## Parameters

- `title` (string, required): Report title
- `report_type` (string): Type of report
  - `daily_summary`: Daily task summary
  - `cron_result`: Cron job execution result
  - `build_status`: Build pipeline status
  - `test_result`: Test execution result
- `status` (string): Overall status
  - `success`: Green color with ✅ icon
  - `failure`: Red color with ❌ icon
  - `warning`: Orange color with ⚠️ icon
  - `info`: Blue color with ℹ️ icon
- `metrics` (object): Execution metrics
  - `completed` (number): Number of completed tasks
  - `failed` (number): Number of failed tasks
  - `duration` (string): Execution duration
  - Custom fields supported
- `details` (array): Detailed items
  - `name` (string): Item name
  - `value` (string): Item value
  - `inline` (boolean): Display inline (default: false)
- `summary` (string): Overall summary text
- `timestamp` (string): Report timestamp

## Examples

**Daily backup report:**
```
Format this backup report for Discord:
{
  "title": "Daily Backup Report",
  "report_type": "daily_summary",
  "status": "success",
  "metrics": {
    "completed": 5,
    "failed": 0,
    "duration": "2m 30s"
  },
  "summary": "All backup tasks completed successfully"
}
```

**Build failure:**
```
Format this build failure for Discord:
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
    {"name": "Unit Tests", "value": "✅ Passed (120/120)"},
    {"name": "Integration Tests", "value": "❌ Failed (5/10)"}
  ]
}
```

**Cron job result:**
```
Format this cron job result:
{
  "title": "Database Cleanup Job",
  "report_type": "cron_result",
  "status": "success",
  "metrics": {
    "duration": "45s"
  },
  "details": [
    {"name": "Records Deleted", "value": "1,234", "inline": true},
    {"name": "Space Freed", "value": "2.5GB", "inline": true}
  ]
}
```

## Output

Returns Discord embed JSON with:
- Title with status icon (✅/❌/⚠️/ℹ️)
- Color based on status (green/red/orange/blue)
- Metrics section with execution statistics
- Detailed items as fields
- Report type and timestamp in footer

## Tips

- Use `status="success"` for successful executions (green)
- Use `status="failure"` for failures (red)
- Use `status="warning"` for partial success (orange)
- Use `status="info"` for informational reports (blue)
- Add custom metrics beyond completed/failed/duration
- Use `inline: true` for compact metric display
- Supports up to 20 detail fields (Discord limit: 25)
