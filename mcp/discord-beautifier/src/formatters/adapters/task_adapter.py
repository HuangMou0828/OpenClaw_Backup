"""Task / Monitoring report adapter - optimized for Discord field-based layout.

Parsing strategy:
  - Extract overall status from conclusion section
  - Build metrics summary as inline fields
  - Highlight problems/warnings in dedicated fields
  - Use status icons (✅/❌/⚠️) consistently

Handles:
  - L5 health check
  - Memory promotion reports
  - AI usage reports
  - Generic task reports
"""

import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta


SH_TZ = timezone(timedelta(hours=8))


def parse_l5_health_markdown(markdown_text: str) -> Dict[str, Any]:
    """Parse L5 health check Markdown into structured report.

    Returns:
      {
        "report_type": "health_check",
        "title": "L5 健康巡检",
        "status": "success" | "warning" | "error",
        "summary": "结论文本",
        "metrics": {"正常": 5, "异常": 2},
        "problem_list": ["问题1", "问题2"],
        "sections": {"section_name": [{"name", "value", "status"}]},
        "timestamp": "2024-03-15 09:00"
      }
    """
    text = markdown_text.strip()
    lines = text.split("\n")

    result = {
        "report_type": "health_check",
        "title": "L5 健康巡检",
        "status": "unknown",
        "summary": "",
        "metrics": {},
        "problem_list": [],
        "sections": {},
        "timestamp": datetime.now(SH_TZ).strftime("%Y-%m-%d %H:%M"),
    }

    current_section = "general"
    sections: Dict[str, List[Dict[str, Any]]] = {}
    metrics: Dict[str, Any] = {}
    problem_list: List[str] = []

    i = 0
    n = len(lines)

    while i < n:
        line = lines[i].strip()

        if not line:
            i += 1
            continue

        # ## 结论 or ## Conclusion
        if re.match(r"^##\s*[结定]论", line) or re.match(r"^##\s*Conclusion", line, re.IGNORECASE):
            i += 1
            conclusion_parts = []
            while i < n:
                next_line = lines[i].strip()
                if next_line.startswith("## ") or next_line.startswith("# "):
                    break
                if next_line:
                    conclusion_parts.append(next_line)
                i += 1

            conclusion_text = " ".join(conclusion_parts)
            result["summary"] = conclusion_text

            # Detect status
            if "✅" in conclusion_text or "正常" in conclusion_text or "ok" in conclusion_text.lower():
                result["status"] = "success"
            elif "⚠️" in conclusion_text or "警告" in conclusion_text:
                result["status"] = "warning"
            elif "❌" in conclusion_text or "错误" in conclusion_text or "失败" in conclusion_text:
                result["status"] = "error"
            else:
                result["status"] = "success"
            continue

        # ## Section header
        section_match = re.match(r"^##\s+(.+)", line)
        if section_match:
            section_name = section_match.group(1).strip()
            # Skip automation hint sections
            if "自动化" in section_name or "操作提示" in section_name:
                i += 1
                while i < n and not lines[i].strip().startswith("##"):
                    i += 1
                continue

            current_section = section_name
            if current_section not in sections:
                sections[current_section] = []
            i += 1
            continue

        # Extract status from line
        line_status = "unknown"
        if "✅" in line:
            line_status = "success"
        elif "❌" in line:
            line_status = "error"
        elif "⚠️" in line:
            line_status = "warning"

        clean_line = re.sub(r"^[✅❌⚠️]\s*", "", line)

        # Bullet list: - key: value
        bullet_match = re.match(r"^-\s+(.+?)[：:\-]\s*(.*)$", clean_line)
        if bullet_match:
            key = bullet_match.group(1).strip()
            value = bullet_match.group(2).strip()

            # Extract metrics
            num_match = re.search(r"(\d+)", value)
            if num_match:
                metrics[key] = int(num_match.group(1))

            # Detect problem list
            if "问题" in key or "异常" in key or "错误" in key:
                # Collect problems from following lines
                j = i + 1
                while j < n:
                    next_line = lines[j].strip()
                    if next_line.startswith("## ") or next_line.startswith("# "):
                        break
                    if next_line.startswith("- ") and (".md" in next_line or "/" in next_line):
                        problem_text = next_line[2:].strip()
                        # Clean up problem text
                        problem_text = re.sub(r"^[✅❌⚠️]\s*", "", problem_text)
                        if problem_text and not problem_text.startswith("断链"):
                            problem_list.append(problem_text)
                    j += 1

            # Add to section
            if current_section not in sections:
                sections[current_section] = []
            sections[current_section].append({
                "name": key,
                "value": value,
                "status": line_status
            })

        i += 1

    result["metrics"] = metrics
    result["problem_list"] = problem_list
    result["sections"] = sections

    return result


def parse_task_report_markdown(markdown_text: str) -> Dict[str, Any]:
    """Parse generic task report Markdown.

    Auto-detects report type and extracts structured data.
    """
    text = markdown_text.strip()

    # Detect report type
    if "记忆晋升" in text or "memory" in text.lower() and "promot" in text.lower():
        return _parse_memory_promotion(text)
    elif "AI 使用" in text or "token" in text.lower():
        return _parse_ai_usage_report(text)
    else:
        return _parse_generic_task_report(text)


def _parse_memory_promotion(text: str) -> Dict[str, Any]:
    """Parse memory promotion report."""
    lines = text.split("\n")
    details: List[Dict[str, Any]] = []
    promoted_count = 0
    archived_count = 0
    degraded_count = 0
    pending_count = 0

    promoted_items: List[str] = []
    degraded_items: List[str] = []

    current_section = ""

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Section headers
        if line.startswith("###") or line.startswith("##"):
            current_section = line.lstrip("#").strip()
            continue

        # Extract counts from summary line
        count_match = re.search(r"\[.*?promoted:\s*(\d+).*?pending:\s*(\d+).*?archived:\s*(\d+).*?degraded:\s*(\d+)", line)
        if count_match:
            promoted_count = int(count_match.group(1))
            pending_count = int(count_match.group(2))
            archived_count = int(count_match.group(3))
            degraded_count = int(count_match.group(4))
            continue

        # Bullet items
        if line.startswith("- "):
            item_text = line[2:].strip()
            item_text = re.sub(r"^[✅❌⚠️]\s*", "", item_text)

            if "已晋升" in current_section or "✅" in line:
                promoted_items.append(item_text)
            elif "已降级" in current_section or "降级" in current_section:
                degraded_items.append(item_text)

    # Build summary
    summary_parts = []
    if promoted_count > 0:
        summary_parts.append(f"晋升 {promoted_count} 条")
    if archived_count > 0:
        summary_parts.append(f"归档 {archived_count} 条")
    if degraded_count > 0:
        summary_parts.append(f"降级 {degraded_count} 条")

    summary = "、".join(summary_parts) if summary_parts else "无变更"

    # Determine status
    status = "success"
    if degraded_count > 0:
        status = "warning"

    return {
        "report_type": "memory_promotion",
        "title": "记忆晋升报告",
        "status": status,
        "summary": summary,
        "metrics": {
            "晋升": promoted_count,
            "归档": archived_count,
            "降级": degraded_count,
            "待处理": pending_count,
        },
        "promoted_items": promoted_items[:5],  # Limit to 5 for display
        "degraded_items": degraded_items[:5],
        "problem_list": [],
        "sections": {},
        "timestamp": datetime.now(SH_TZ).strftime("%Y-%m-%d %H:%M"),
    }


def _parse_ai_usage_report(text: str) -> Dict[str, Any]:
    """Parse AI usage daily/weekly report."""
    lines = text.split("\n")
    details: List[str] = []
    total_tokens = 0
    model_usage: Dict[str, int] = {}

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Extract token counts
        token_match = re.search(r"(\d+[\d,]*)\s*(?:tokens|Token)", line, re.IGNORECASE)
        if token_match:
            tokens = int(token_match.group(1).replace(",", ""))
            total_tokens += tokens

            # Extract model name
            model_match = re.search(r"(claude|gpt|gemini|deepseek)[\w\-]*", line, re.IGNORECASE)
            if model_match:
                model_name = model_match.group(0)
                model_usage[model_name] = model_usage.get(model_name, 0) + tokens

        if line.startswith("- ") or line.startswith("* "):
            details.append(line[2:].strip())

    return {
        "report_type": "ai_usage_daily",
        "title": "AI 使用日报",
        "status": "info",
        "summary": f"总计 {total_tokens:,} tokens",
        "metrics": {"总 tokens": total_tokens, **model_usage},
        "details": details[:10],  # Limit to 10 lines
        "problem_list": [],
        "sections": {},
        "timestamp": datetime.now(SH_TZ).strftime("%Y-%m-%d %H:%M"),
    }


def _parse_generic_task_report(text: str) -> Dict[str, Any]:
    """Parse generic task report."""
    lines = text.split("\n")
    details: List[str] = []
    metrics: Dict[str, Any] = {}
    status = "success"

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Detect status
        if "❌" in line or "失败" in line or "error" in line.lower():
            status = "error"
        elif "⚠️" in line or "警告" in line:
            if status != "error":
                status = "warning"

        # Extract metrics
        metric_match = re.search(r"(\w+)[：:]\s*(\d+)", line)
        if metric_match:
            key = metric_match.group(1)
            value = int(metric_match.group(2))
            metrics[key] = value

        if line.startswith("- ") or line.startswith("* "):
            details.append(line[2:].strip())

    return {
        "report_type": "generic",
        "title": "任务报告",
        "status": status,
        "summary": "",
        "metrics": metrics,
        "details": details[:10],
        "problem_list": [],
        "sections": {},
        "timestamp": datetime.now(SH_TZ).strftime("%Y-%m-%d %H:%M"),
    }


def build_task_embed(parsed: Dict[str, Any]) -> Dict[str, Any]:
    """Build Discord embed from parsed task report.

    Strategy:
      - Title: status icon + report title
      - Description: summary text
      - Fields:
        1. Metrics (inline) - key stats
        2. Problems (if any) - highlighted issues
        3. Details (if needed) - additional info
      - Footer: report type + timestamp
      - Color: based on status
    """
    report_type = parsed.get("report_type", "generic")
    title = parsed.get("title", "任务报告")
    status = parsed.get("status", "info")
    summary = parsed.get("summary", "")
    metrics = parsed.get("metrics", {})
    problem_list = parsed.get("problem_list", [])
    timestamp = parsed.get("timestamp", "")

    # Status config
    status_config = {
        "success": {"color": 3066993, "icon": "✅"},
        "error": {"color": 15158332, "icon": "❌"},
        "warning": {"color": 15105570, "icon": "⚠️"},
        "info": {"color": 3447003, "icon": "ℹ️"},
        "unknown": {"color": 9807270, "icon": "❓"},
    }

    config = status_config.get(status, status_config["info"])

    embed = {
        "title": f"{config['icon']} {title}",
        "description": summary[:4096] if summary else None,
        "color": config["color"],
        "fields": [],
    }

    # Add metrics field (inline)
    if metrics:
        metrics_lines = []
        for key, value in list(metrics.items())[:6]:  # Limit to 6 metrics
            # Format with status icons
            if key in ["正常", "成功", "完成", "晋升"]:
                metrics_lines.append(f"✅ {key}: {value}")
            elif key in ["异常", "失败", "错误"]:
                metrics_lines.append(f"❌ {key}: {value}")
            elif key in ["警告", "待处理", "降级"]:
                metrics_lines.append(f"⚠️ {key}: {value}")
            else:
                metrics_lines.append(f"• {key}: {value}")

        if metrics_lines:
            embed["fields"].append({
                "name": "📊 统计信息",
                "value": "\n".join(metrics_lines),
                "inline": True
            })

    # Add problem list field (if any)
    if problem_list:
        problem_text = "\n".join([f"{i+1}. {p[:100]}" for i, p in enumerate(problem_list[:5])])
        embed["fields"].append({
            "name": f"⚠️ 待处理问题 ({len(problem_list)})",
            "value": problem_text[:1024],
            "inline": False
        })

    # Add promoted/degraded items for memory promotion
    if report_type == "memory_promotion":
        promoted_items = parsed.get("promoted_items", [])
        degraded_items = parsed.get("degraded_items", [])

        if promoted_items:
            promoted_text = "\n".join([f"• {item[:80]}" for item in promoted_items])
            embed["fields"].append({
                "name": "✅ 已晋升",
                "value": promoted_text[:1024],
                "inline": False
            })

        if degraded_items:
            degraded_text = "\n".join([f"• {item[:80]}" for item in degraded_items])
            embed["fields"].append({
                "name": "⚠️ 已降级",
                "value": degraded_text[:1024],
                "inline": False
            })

    # Add details for AI usage reports
    if report_type == "ai_usage_daily":
        details = parsed.get("details", [])
        if details:
            details_text = "\n".join([f"• {d[:100]}" for d in details[:8]])
            embed["fields"].append({
                "name": "📝 使用详情",
                "value": details_text[:1024],
                "inline": False
            })

    # Footer
    report_type_labels = {
        "health_check": "健康巡检",
        "memory_promotion": "记忆晋升",
        "ai_usage_daily": "AI 使用日报",
        "ai_usage_weekly": "AI 使用周报",
        "generic": "任务报告",
    }

    footer_text = f"🤖 {report_type_labels.get(report_type, report_type)}"
    if timestamp:
        footer_text += f" · {timestamp}"

    embed["footer"] = {"text": footer_text}

    return embed
