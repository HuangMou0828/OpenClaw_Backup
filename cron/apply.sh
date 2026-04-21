#!/usr/bin/env bash
# 把本地改动按 job 粒度推到 live（不覆盖 jobs.json 整体，走 CLI 保证兼容）
# 用法: ./apply.sh [--dry-run] [--force]
#   --dry-run  只打印要做什么，不实际执行
#   --force    不询问，直接执行

DRY_RUN=false
FORCE=false
[[ "$1" == "--dry-run" ]] && DRY_RUN=true
[[ "$1" == "--force" ]] && FORCE=true

python3 - <<'PYEOF'
import json, subprocess, sys

with open('cron/jobs.json') as f:
    local_jobs = json.load(f)

live_raw = subprocess.run(['openclaw', 'cron', 'list', '--json'], capture_output=True, text=True)
live_jobs = json.loads(live_raw.stdout)

for job in local_jobs:
    name = job.get('name', '')
    live_id = next((lj.get('id') for lj in live_jobs if lj.get('name') == name), None)

    schedule_expr = job.get('schedule', {}).get('expr', '')
    tz = job.get('schedule', {}).get('tz', 'Asia/Shanghai')
    session = job.get('sessionTarget', 'current')
    agent = job.get('agentId') or ''
    message = job.get('payload', {}).get('message', '')

    if not live_id:
        action = f'ADD  {name}'
    else:
        action = f'EDIT {name} ({live_id})'

    cmd = ['openclaw', 'cron', 'add' if not live_id else 'edit', *([] if not live_id else [live_id]),
           '--name', name, '--cron', schedule_expr, '--tz', tz, '--session', session]
    if agent and agent != 'main':
        cmd += ['--agent', agent]
    cmd += ['--message', message]

    print(action)
    print('  cmd:', ' '.join(f'"{c}"' if ' ' in c else c for c in cmd[:6]), '...')

    if DRY_RUN:
        print('  [dry-run] skipped')
        continue

    if not FORCE:
        print('  execute? [y/N]', end=' ', flush=True)
        try:
            resp = input().strip().lower()
        except EOFError:
            resp = 'n'
    else:
        resp = 'y'

    if resp == 'y':
        result = subprocess.run(cmd)
        print('  ✅ done' if result.returncode == 0 else f'  ❌ failed (exit {result.returncode})')
    else:
        print('  ⏭ skipped')

PYEOF
