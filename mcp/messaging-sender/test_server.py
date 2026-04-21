#!/usr/bin/env python3
"""Quick smoke test for feishu-sender MCP"""
import subprocess
import json
import sys

proc = subprocess.Popen(
    [sys.executable, "server.py"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd="/Users/hm/feishu-sender",
)

# Send tools/list
req = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
proc.stdin.write(req.encode() + b"\n")
proc.stdin.flush()
out = proc.stdout.readline()
print("=== tools/list ===")
print(json.dumps(json.loads(out), indent=2, ensure_ascii=False)[:500])

proc.terminate()
proc.wait(timeout=3)
print("\n✅ Server starts OK")
