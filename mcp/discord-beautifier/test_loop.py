#!/usr/bin/env python3
"""
Discord 渲染样式调试循环
每次调整 render_* 函数后重新运行此脚本,去 Discord 看效果
"""
import os, sys, requests, re
from datetime import datetime, timezone, timedelta

sys.path.insert(0, "src")
from formatters.adapters.news_adapter import parse_ai_news_markdown
from formatters.adapters.task_adapter import parse_l5_health_markdown, parse_task_report_markdown
from styles.presets import get_rainbow_color
from mock_data import AI_NEWS_MOCK, L5_HEALTH_MOCK, AI_USAGE_DAILY_MOCK, MEMORY_PROMOTE_MOCK, INBOX_IMPORT_MOCK

BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN") or sys.exit("set DISCORD_BOT_TOKEN env var")
CHANNEL_ID = os.environ.get("DISCORD_CHANNEL_ID") or sys.exit("set DISCORD_CHANNEL_ID env var")
PROXIES = {"http": "http://127.0.0.1:7897", "https": "http://127.0.0.1:7897"}

SH_TZ = timezone(timedelta(hours=8))
now = datetime.now(SH_TZ)
day_name = ["周日","周一","周二","周三","周四","周五","周六"][now.isoweekday() % 7]

def send(embed):
    payload = {"content": None, "embeds": [embed]}
    resp = requests.post(
        f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages",
        json=payload,
        headers={"Authorization": f"Bot {BOT_TOKEN}", "Content-Type": "application/json"},
        proxies=PROXIES, verify=False, timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["id"]

def rainbow_embed(title, description=None):
    return {
        "title": title,
        "color": get_rainbow_color(),
        "description": description,
        "fields": [],
        "footer": {"text": f"🌈 AI 热点小推车 · {day_name}"}
    }

# ══════════════════════════════════════════════
# RENDER 1: AI 每日热点简报
# ══════════════════════════════════════════════
def render_ai_news(md: str) -> dict:
    parsed = parse_ai_news_markdown(md)
    articles = parsed["articles"]

    # ── 去重:同 headline 只保留第一条 ──
    seen, deduped = [], []
    for a in articles:
        h = a.get("headline", "").strip()
        if h not in seen:
            seen.append(h); deduped.append(a)
    articles = deduped

    categories = {}
    for a in articles:
        cat = a.get("category", "其他")
        categories.setdefault(cat, []).append(a)

    cat_icons = {"头条":"🔥","产业":"🏭","模型":"🤖","洞察":"💡","工具":"🛠","其他":"📋"}
    total_chars = sum(len(a.get("summary","")) for a in articles)

    embed = {
        "title": f"📰 AI 热点日报 · {day_name}",
        "color": get_rainbow_color(),
        "description": (
            f'共 **{len(articles)} 条**新闻 | 摘要约 **{total_chars}** 字\n'
            f'🔥 头条 · 🏭 产业 · 🤖 模型 · 💡 洞察'
        ),
        "fields": [],
        "footer": {"text": f'🌈 共 {len(articles)} 条 · AI 热点日报 · {now.strftime("%m/%d")} {day_name}'},
    }

    for cat_name, cat_articles in categories.items():
        icon = cat_icons.get(cat_name, "📋")

        embed["fields"].append({
            "name": f'{icon} {cat_name}',
            "value": '---',
            "inline": False,
        })

        for i, a in enumerate(cat_articles):
            headline = a.get("headline", "")
            summary = a.get("summary", "")
            url = a.get("url", "")

            if len(summary) > 200:
                summary = summary[:197] + "..."

            num_emoji = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
            num = num_emoji[i] if i < len(num_emoji) else "▪️"

            # value = 摘要(code block) + 查看全文(斜体超链接)，不再重复标题
            value_parts = []
            if summary:
                value_parts.append(f'```\n{summary}\n```')
            if url:
                value_parts.append(f'*📍 [查看全文]({url})*')

            embed["fields"].append({
                "name": f'{num} {headline[:50]}{"..." if len(headline) > 50 else ""}',
                "value": "\n".join(value_parts),
                "inline": False,
            })

    return embed


# ══════════════════════════════════════════════
# RENDER 2: L5 健康巡检
# ══════════════════════════════════════════════
def render_l5_health(md: str) -> dict:
    parsed = parse_l5_health_markdown(md)
    status = parsed.get("status", "unknown")
    status_icon = {"success": "✅", "warning": "⚠️", "error": "❌"}.get(status, "❓")

    embed = {
        "title": f"{status_icon} L5 健康巡检",
        "color": get_rainbow_color(),
        "description": (parsed.get("summary", "") or ""),
        "fields": [],
        "footer": {"text": f"🤖 定时任务 · L5 Health Check"}
    }

    import re as re2

    for section_name, items in parsed.get("sections", {}).items():
        if not items:
            continue
        section_display = section_name.replace("## ", "").strip()

        if section_display in ("Vault 健康", "执行统计", "概况"):
            # ── 表格样式:代码块等宽对齐 ──
            col1_w = 20
            rows = []
            for item in items:
                name = re2.sub(r"^[✅❌⚠️]\s*", "", item.get("name","")).strip()
                value = item.get("value", "")
                item_status = item.get("status", "")
                icon = {"success":"✅","warning":"⚠️","error":"❌"}.get(item_status,"")
                rows.append(f"{icon} {name:<{col1_w}} {value}")

            table_text = "\n".join(rows)
            embed["fields"].append({
                "name": f"📊 {section_display}",
                "value": f"```\n{table_text}\n```",
                "inline": False,
            })

        else:
            # ── 普通列表 ──
            lines = []
            for item in items:
                name = item.get("name","")
                value = item.get("value","")
                istatus = item.get("status","")
                icon = {"success":"✅","warning":"⚠️","error":"❌"}.get(istatus,"")
                lines.append(f'{icon} **{name}**' + (f': {value}' if value else ''))
            embed["fields"].append({
                "name": f"📋 {section_display}" if section_display != "general" else "📋 详情",
                "value": "\n".join(lines),
                "inline": False,
            })

    # ── 问题列表:编号 + 引用块头部 ──
    problem_list = parsed.get("problem_list", [])
    if problem_list:
        header = f'> ⚠️ 共发现 **{len(problem_list)}** 条问题,建议及时处理'
        items_text = "\n".join(f'  {i+1}. {p}' for i, p in enumerate(problem_list))
        embed["fields"].append({
            "name": f"⚠️ 具体问题({len(problem_list)}条)",
            "value": f"```\n{header}\n\n{items_text}\n```",
            "inline": False,
        })

    return embed


# ══════════════════════════════════════════════
# RENDER 3: AI 使用日报(通用任务报告)
# ══════════════════════════════════════════════
def render_task_report(md: str, title: str = "📊 任务报告") -> dict:
    parsed = parse_task_report_markdown(md)

    embed = {
        "title": title,
        "color": get_rainbow_color(),
        "description": None,
        "fields": [],
        "footer": {"text": f"🤖 定时任务"}
    }

    for section_name, items in parsed.get("sections", {}).items():
        if not items:
            continue
        section_display = section_name.replace("## ", "").strip()

        lines = []
        for item in items:
            name = item.get("name","")
            value = item.get("value","")
            istatus = item.get("status","")
            icon = {"success":"✅","warning":"⚠️","error":"❌"}.get(istatus,"")
            lines.append(f"{icon} **{name}**" + (f": {value}" if value else ""))

        if len("\n".join(lines)) <= 1024:
            embed["fields"].append({
                "name": f"📋 {section_display}",
                "value": "\n".join(lines),
                "inline": False,
            })
        else:
            # 内容太长则截断
            val = "\n".join(lines)[:1018] + "..."
            embed["fields"].append({
                "name": f"📋 {section_display}",
                "value": val,
                "inline": False,
            })

    return embed


# ══════════════════════════════════════════════
# RENDER 4: 记忆晋升报告
# ══════════════════════════════════════════════
def render_memory_promote(md: str) -> dict:
    parsed = parse_task_report_markdown(md)

    embed = {
        "title": "🧠 记忆晋升报告",
        "color": get_rainbow_color(),
        "description": None,
        "fields": [],
        "footer": {"text": "🤖 定时任务 · 每日记忆晋升"}
    }

    for section_name, items in parsed.get("sections", {}).items():
        if not items:
            continue
        section_display = section_name.replace("## ", "").strip()
        lines = []
        for item in items:
            name = item.get("name","")
            value = item.get("value","")
            istatus = item.get("status","")
            icon = {"success":"✅","warning":"⚠️","error":"❌"}.get(istatus,"")
            lines.append(f"{icon} **{name}**" + (f": {value}" if value else ""))

        embed["fields"].append({
            "name": f"📋 {section_display}",
            "value": "\n".join(lines),
            "inline": False,
        })

    return embed


# ══════════════════════════════════════════════
# RENDER 5: Inbox 导入
# ══════════════════════════════════════════════
def render_inbox_import(data: dict) -> dict:
    summary = data.get("summary", {})
    imported = summary.get("imported", 0)
    archived = summary.get("archived", 0)
    skipped = summary.get("skipped", 0)
    failed = summary.get("failed", 0)

    embed = {
        "title": "📥 Inbox 同步报告",
        "color": get_rainbow_color(),
        "description": data.get("message", ""),
        "fields": [
            {
                "name": "📊 同步结果",
                "value": f"✅ 新增 **{imported}** 条 | 📦 归档 **{archived}** 条 | ⏭ 跳过 **{skipped}** 条" + (f" | ❌ 失败 **{failed}** 条" if failed else ""),
                "inline": False,
            }
        ],
        "footer": {"text": "🤖 定时任务 · Inbox Import"}
    }
    return embed


# ══════════════════════════════════════════════
# 主循环
# ══════════════════════════════════════════════
if __name__ == "__main__":
    print(f"🎨 样式调试 · {day_name}\n")

    print("[1/2] AI 每日热点简报...")
    e1 = render_ai_news(AI_NEWS_MOCK)
    id1 = send(e1)
    print(f"    ✅ {id1}")

    print("[2/2] L5 健康巡检...")
    e2 = render_l5_health(L5_HEALTH_MOCK)
    id2 = send(e2)
    print(f"    ✅ {id2}")

    print(f"\n🔗 AI新闻: https://discord.com/channels/{CHANNEL_ID}/{id1}")
    print(f"🔗 L5健康: https://discord.com/channels/{CHANNEL_ID}/{id2}")
