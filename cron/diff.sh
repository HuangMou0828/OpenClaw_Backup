#!/usr/bin/env bash
# 对比本地 cron/jobs.json 和 live cron（只看 job 定义，不比运行时 state）
set -e

python3 - <<'PYEOF'
import json, subprocess, sys, difflib

# Load local jobs.json (raw array)
with open('cron/jobs.json') as f:
    local = json.load(f)

# Get live jobs from openclaw CLI (wrapped format)
result = subprocess.run(['openclaw', 'cron', 'list', '--json'], capture_output=True, text=True)
live_raw = json.loads(result.stdout)
live = live_raw.get('jobs', [])

# Normalize: sort by name so order doesn't matter
local_sorted = sorted(local, key=lambda j: j.get('name',''))
live_sorted = sorted(live, key=lambda j: j.get('name',''))

# Compare
a = json.dumps(local_sorted, sort_keys=True, ensure_ascii=False, indent=2)
b = json.dumps(live_sorted, sort_keys=True, ensure_ascii=False, indent=2)

if a == b:
    print("✅ live 与 jobs.json 一致（无可见差异）")
else:
    diff = difflib.unified_diff(
        a.splitlines(), b.splitlines(),
        fromfile='cron/jobs.json (本地)', tofile='live (openclaw cron list)'
    )
    lines = list(diff)
    if lines:
        print('\n'.join(lines))
    else:
        print("✅ 无差异")
PYEOF
