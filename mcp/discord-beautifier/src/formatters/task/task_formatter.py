"""Task report formatter for personal task execution results"""

from typing import Dict, Any, List
from core.base_formatter import BaseFormatter


class TaskReportFormatter(BaseFormatter):
    """Formatter for task execution reports and daily summaries.

    Handles personal task results, cron job outputs, build status, etc.
    """

    def format(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format task report as Discord embed.

        Args:
            data: {
                "report_type": "daily_summary|cron_result|build_status|test_result",
                "title": "任务执行报告",
                "status": "success|failure|warning|info",
                "metrics": {
                    "completed": 10,
                    "failed": 2,
                    "duration": "5m 30s",
                    "custom_key": "custom_value"
                },
                "details": [
                    {"name": "任务1", "value": "成功", "inline": true},
                    {"name": "任务2", "value": "失败: 超时", "inline": true}
                ],
                "summary": "整体执行情况良好",
                "timestamp": "2024-03-15 14:30"
            }

        Returns:
            Discord embed dict
        """
        report_type = data.get("report_type", "task_report")
        title = data.get("title", "任务报告")
        status = data.get("status", "info")
        metrics = data.get("metrics", {})
        details = data.get("details", [])
        summary = data.get("summary", "")
        timestamp = data.get("timestamp", "")

        # Status configuration
        status_config = {
            "success": {"color": 3066993, "icon": "✅", "label": "成功"},
            "failure": {"color": 15158332, "icon": "❌", "label": "失败"},
            "warning": {"color": 15105570, "icon": "⚠️", "label": "警告"},
            "info": {"color": 3447003, "icon": "ℹ️", "label": "信息"}
        }

        config = status_config.get(status, status_config["info"])

        # Build embed
        embed = {
            "title": f"{config['icon']} {title}",
            "color": config["color"],
            "fields": []
        }

        # Add summary as description
        if summary:
            embed["description"] = summary[:4096]

        # Add metrics field
        if metrics:
            metrics_lines = []

            # Standard metrics with icons
            if "completed" in metrics:
                metrics_lines.append(f"✅ 完成: {metrics['completed']}")
            if "failed" in metrics:
                metrics_lines.append(f"❌ 失败: {metrics['failed']}")
            if "duration" in metrics:
                metrics_lines.append(f"⏱️ 耗时: {metrics['duration']}")

            # Custom metrics
            for key, value in metrics.items():
                if key not in ["completed", "failed", "duration"]:
                    metrics_lines.append(f"• {key}: {value}")

            if metrics_lines:
                embed["fields"].append({
                    "name": "📊 执行统计",
                    "value": "\n".join(metrics_lines),
                    "inline": False
                })

        # Add detail fields (limit to 20 for Discord)
        for detail in details[:20]:
            name = detail.get("name", "详情")
            value = detail.get("value", "无内容")
            inline = detail.get("inline", False)

            embed["fields"].append({
                "name": name[:256],
                "value": str(value)[:1024],
                "inline": inline
            })

        # Add footer with report type and timestamp
        report_type_labels = {
            "daily_summary": "每日汇总",
            "cron_result": "定时任务",
            "build_status": "构建状态",
            "test_result": "测试结果"
        }

        footer_text = f"🤖 {report_type_labels.get(report_type, report_type)}"
        if timestamp:
            footer_text += f" · {timestamp}"

        embed["footer"] = {"text": footer_text}

        return embed

    def validate_input(self, data: Dict[str, Any]) -> tuple[bool, str]:
        """Validate task report input."""
        if "title" not in data:
            return False, "Missing required field: title"

        status = data.get("status")
        if status and status not in ["success", "failure", "warning", "info"]:
            return False, f"Invalid status: {status}. Must be one of: success, failure, warning, info"

        return True, None

    def get_tool_name(self) -> str:
        return "format_task_report"

    def get_tool_description(self) -> str:
        return (
            "Format task execution reports, daily summaries, cron job results, "
            "and build status as Discord embed. Supports metrics, status indicators, "
            "and detailed breakdowns."
        )

    def get_tool_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "report_type": {
                    "type": "string",
                    "description": "Type of report",
                    "enum": ["daily_summary", "cron_result", "build_status", "test_result"],
                    "default": "task_report"
                },
                "title": {
                    "type": "string",
                    "description": "Report title"
                },
                "status": {
                    "type": "string",
                    "description": "Overall status",
                    "enum": ["success", "failure", "warning", "info"],
                    "default": "info"
                },
                "metrics": {
                    "type": "object",
                    "description": "Execution metrics (completed, failed, duration, etc.)",
                    "properties": {
                        "completed": {"type": "number"},
                        "failed": {"type": "number"},
                        "duration": {"type": "string"}
                    }
                },
                "details": {
                    "type": "array",
                    "description": "Detailed items",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "value": {"type": "string"},
                            "inline": {"type": "boolean", "default": False}
                        },
                        "required": ["name", "value"]
                    }
                },
                "summary": {
                    "type": "string",
                    "description": "Overall summary text"
                },
                "timestamp": {
                    "type": "string",
                    "description": "Report timestamp"
                }
            },
            "required": ["title"]
        }
