#!/usr/bin/env python3
"""
AI News RSS Fetcher & Deduplicator
Uses curl for fetching (SSL-friendly), python for parsing.
Usage: python3 fetch_rss_news.py <sources_json_path>
"""
import json
import sys
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import re
from collections import defaultdict
import time
import signal
import atexit

PROXY = "http://127.0.0.1:7897"
CLASH_VERGE_APP = "/Applications/Clash Verge.app"
proxy_was_started = False

def proxy_available():
    """Check if proxy port is listening."""
    try:
        result = subprocess.run(["lsof", "-i", ":7897"], capture_output=True, timeout=2)
        return result.returncode == 0
    except Exception:
        return False

def start_clash_verge():
    """Start Clash Verge if not running."""
    global proxy_was_started
    try:
        # Check if already running
        check = subprocess.run(["pgrep", "-f", "verge-mihomo"], capture_output=True)
        if check.returncode == 0:
            return False  # Already running

        # Start Clash Verge
        subprocess.Popen(["open", "-a", CLASH_VERGE_APP],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL)

        # Wait for proxy to be ready (max 10s)
        for _ in range(20):
            time.sleep(0.5)
            if proxy_available():
                proxy_was_started = True
                return True
        return False
    except Exception:
        return False

def stop_clash_verge():
    """Stop Clash Verge if we started it."""
    global proxy_was_started
    if not proxy_was_started:
        return
    try:
        # Find verge-mihomo process
        result = subprocess.run(["pgrep", "-f", "verge-mihomo"],
                              capture_output=True, text=True)
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                try:
                    subprocess.run(["kill", pid], timeout=2)
                except Exception:
                    pass
    except Exception:
        pass

# Register cleanup on exit
atexit.register(stop_clash_verge)

def fetch_url(url, use_proxy=False, timeout=15):
    """Fetch URL via curl (handles SSL certs properly on macOS)."""
    cmd = [
        "curl", "-s", "--max-time", str(timeout),
        "-H", "User-Agent: Mozilla/5.0"
    ]
    if use_proxy:
        cmd += ["--proxy", PROXY]
    cmd.append(url)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 5)
        return result.stdout
    except Exception:
        return None

def parse_feed(content, source_name):
    """Parse RSS/Atom XML, return list of dicts with title/link/pub_ts."""
    items = []
    if not content or len(content) < 50:
        return items
    try:
        root = ET.fromstring(content)
    except Exception:
        return items
    ns_prefix = ""
    if root.tag.startswith("{"):
        ns_prefix = "{" + root.tag.split("}")[0][1:] + "}"
    item_tags = ["item", "entry"]
    for item in root.iter():
        tag = item.tag.split("}")[-1] if "}" in item.tag else item.tag
        if tag not in item_tags:
            continue
        title, link, pub_date, description = None, None, None, None
        for child in item:
            child_tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if child_tag == "title":
                title = (child.text or "").strip()
            elif child_tag == "link":
                link = (child.text or "").strip() if child.text else None
            elif child_tag in ("pubDate", "published", "updated", "dc:date"):
                if child.text:
                    pub_date = child.text.strip()
            elif child_tag == "description":
                desc_text = re.sub(r'<[^>]+>', '', child.text or "")
                description = desc_text.strip()[:200]
        if not title:
            continue
        if not link:
            link = ""
        pub_ts = None
        if pub_date:
            date_str = pub_date.strip()
            date_str = re.sub(r'\s+', ' ', date_str)  # collapse multiple spaces
            for fmt in [
                "%Y-%m-%d %H:%M:%S %z",
                "%a, %d %b %Y %H:%M:%S %z",
                "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d"
            ]:
                try:
                    ts_str = date_str
                    if 'Z' in ts_str:
                        ts_str = ts_str.replace('Z', '+0000')
                    pub_ts = datetime.strptime(ts_str, fmt).timestamp()
                    break
                except Exception:
                    pass
        items.append({
            "title": title,
            "link": link,
            "pub_date": pub_date or "",
            "pub_ts": pub_ts or 0,
            "description": description or "",
            "source": source_name
        })
    return items

def main():
    if len(sys.argv) < 2:
        print("Usage: fetch_rss_news.py <sources_json_path>", file=sys.stderr)
        sys.exit(1)
    with open(sys.argv[1]) as f:
        config = json.load(f)
    sources = config.get("sources", [])
    cutoff = (datetime.now() - timedelta(hours=48)).timestamp()

    # Check proxy, start if needed
    proxy_ok = proxy_available()
    if not proxy_ok:
        started = start_clash_verge()
        if started:
            proxy_ok = True

    all_items = []
    source_results = {}
    for src in sources:
        name = src["name"]
        url = src["url"]
        use_proxy = src.get("proxy", False) and proxy_ok
        content = fetch_url(url, use_proxy=use_proxy)
        has_xml = content and ("<rss" in content or "<feed" in content or "<?xml" in content)
        if has_xml:
            items = parse_feed(content, name)
            source_results[name] = {"ok": True, "count": len(items)}
            for item in items:
                if item["pub_ts"] >= cutoff:
                    all_items.append(item)
        else:
            source_results[name] = {"ok": False, "count": 0}
    # 按来源分组去重，保证来源多样性
    by_source = defaultdict(list)
    seen_by_source = defaultdict(set)

    for item in sorted(all_items, key=lambda x: x["pub_ts"], reverse=True):
        src = item["source"]
        norm = item["title"].lower()[:80]
        if norm not in seen_by_source[src]:
            seen_by_source[src].add(norm)
            by_source[src].append(item)

    # 轮询式采样：先保证来源多样性，不足再从各源继续补齐
    result = []
    num_sources = max(len(by_source), 1)
    # 动态单源上限：均摊到15条，至少5条兜底（源少时能填满15）
    max_per_source = max(5, -(-15 // num_sources))
    round_robin_idx = {src: 0 for src in by_source}

    while len(result) < 15 and any(round_robin_idx[s] < len(by_source[s]) for s in by_source):
        for src in sorted(by_source.keys()):
            idx = round_robin_idx[src]
            if idx < len(by_source[src]) and idx < max_per_source:
                result.append(by_source[src][idx])
                round_robin_idx[src] += 1
            if len(result) >= 15:
                break
    ok = [k for k, v in source_results.items() if v["ok"]]
    fail = [k for k, v in source_results.items() if not v["ok"]]
    output = {
        "proxy_available": proxy_ok,
        "ok_sources": ok,
        "fail_sources": fail,
        "total_raw": len(all_items),
        "articles": [{
            "title": a["title"],
            "link": a["link"],
            "pub_date": a["pub_date"],
            "description": a["description"],
            "source": a["source"]
        } for a in result]
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
