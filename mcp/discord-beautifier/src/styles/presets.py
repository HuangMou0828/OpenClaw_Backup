"""Preset styles for Discord embeds"""

import datetime
from typing import Dict, Any


# Rainbow 7 colors (decimal) — based on local day of week
# 周日=0(红) 周一=1(橙) 周二=2(黄) 周三=3(绿) 周四=4(蓝) 周五=5(紫) 周六=6(靛)
_SH_TZ = datetime.timezone(datetime.timedelta(hours=8))

RAINBOW_COLORS = [
    15413039,  # 0=周日 🔴 红    #EB2F2F
    15229996,  # 1=周一 🟠 橙    #E8642C
    16098851,  # 2=周二 🟡 黄    #F5A623
    4510117,   # 3=周三 🟢 绿    #44D1A5
    3900150,   # 4=周四 🔵 蓝    #3B82F6
    11032055,  # 5=周五 🟣 紫    #A855F7
    6514417,   # 6=周六 🌈 靛    #6366F1
]

RAINBOW_HEX = [
    "#EB2F2F", "#E8642C", "#F5A623",
    "#44D1A5", "#3B82F6", "#A855F7", "#6366F1"
]

# Legacy Discord color palette (decimal)
COLORS = {
    "blue":   3447003,
    "green":  3066993,
    "red":    15158332,
    "orange": 15105570,
    "purple": 10181046,
    "yellow": 16776960,
    "gray":   9807270,
}


PRESET_STYLES = {
    "news": {
        "color": COLORS["blue"],
        "title_prefix": "📰 ",
        "footer_icon": "📰",
    },
    "report": {
        "color": COLORS["purple"],
        "title_prefix": "📊 ",
        "footer_icon": "📊",
    },
    "alert": {
        "color": COLORS["red"],
        "title_prefix": "⚠️ ",
        "footer_icon": "⚠️",
    },
    "changelog": {
        "color": COLORS["green"],
        "title_prefix": "🚀 ",
        "footer_icon": "🚀",
    },
    "rainbow": {
        "color": None,   # resolved at call time
        "title_prefix": "🌈 ",
        "footer_icon": "🌈",
    },
}


def get_rainbow_color() -> int:
    """Return today's rainbow color based on local timezone day of week.
    Python weekday(): Mon=0, Tue=1, ... Sun=6
    We want: Sun=0, Mon=1, ... Sat=6
    """
    now_sh = datetime.datetime.now(_SH_TZ)
    day_index = (now_sh.weekday() + 1) % 7
    return RAINBOW_COLORS[day_index]


def get_rainbow_info() -> Dict[str, Any]:
    """Return current rainbow color info for debugging."""
    now_sh = datetime.datetime.now(_SH_TZ)
    day_index = (now_sh.weekday() + 1) % 7
    days_cn = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"]
    return {
        "day_index": day_index,
        "day_name": days_cn[day_index],
        "color_decimal": RAINBOW_COLORS[day_index],
        "color_hex": RAINBOW_HEX[day_index],
    }


def apply_style(embed: Dict[str, Any], style: str) -> Dict[str, Any]:
    """Apply preset style to embed.

    Args:
        embed: Base embed dict
        style: Style name (auto, news, report, alert, changelog, rainbow)

    Returns:
        Styled embed dict
    """
    # Auto-detect style based on content
    if style == "auto":
        style = detect_style(embed)

    # Handle rainbow separately — color depends on current day
    if style == "rainbow":
        embed["color"] = get_rainbow_color()
        prefix = PRESET_STYLES["rainbow"]["title_prefix"]
        if "title" in embed and not embed["title"].startswith(prefix):
            embed["title"] = prefix + embed["title"]
        footer_icon = PRESET_STYLES["rainbow"]["footer_icon"]
        if "footer" in embed:
            footer_text = embed["footer"].get("text", "")
            if not footer_text.startswith(footer_icon):
                embed["footer"]["text"] = footer_icon + " " + footer_text
        else:
            rainbow_info = get_rainbow_info()
            embed["footer"] = {
                "text": f"🌈 今日色彩: {rainbow_info['color_hex']} · {rainbow_info['day_name']}"
            }
        return embed

    # Get style config
    style_config = PRESET_STYLES.get(style, {})

    # Apply color
    if "color" in style_config and style_config["color"]:
        embed["color"] = style_config["color"]

    # Apply title prefix
    if "title" in embed and "title_prefix" in style_config:
        prefix = style_config["title_prefix"]
        if not embed["title"].startswith(prefix):
            embed["title"] = prefix + embed["title"]

    # Apply footer icon
    if "footer" in embed and "footer_icon" in style_config:
        icon = style_config["footer_icon"]
        footer_text = embed["footer"].get("text", "")
        if not footer_text.startswith(icon):
            embed["footer"]["text"] = icon + " " + footer_text

    return embed


def detect_style(embed: Dict[str, Any]) -> str:
    """Auto-detect appropriate style based on content."""
    title = embed.get("title", "").lower()
    description = embed.get("description", "").lower()
    content = title + " " + description

    # Alert keywords
    alert_words = ["alert", "warning", "error", "critical", "urgent", "警告", "错误", "紧急"]
    if any(word in content for word in alert_words):
        return "alert"

    # Changelog keywords
    changelog_words = ["release", "version", "update", "changelog", "发布", "更新", "版本"]
    if any(word in content for word in changelog_words):
        return "changelog"

    # News keywords
    news_words = ["breaking", "news", "announced", "新闻", "发布", "宣布"]
    if any(word in content for word in news_words):
        return "news"

    # Report keywords
    report_words = ["report", "summary", "analysis", "报告", "摘要", "分析"]
    if any(word in content for word in report_words):
        return "report"

    # Default to rainbow (our daily digest use case)
    return "rainbow"
