#!/bin/bash
# Bulk aesthetic run: prep ~100 candidates -> post them spaced -> resync state -> resume worker.
cd /home/ubuntu/x-op
echo "=== bulk run START $(date -u '+%Y-%m-%d %H:%M:%S') ===" >> logs/aesthetic-bulk-run.log
./venv/bin/python aesthetic_bulk_prep.py --target 80 --passes 8 --min-likes 120 >> logs/aesthetic-bulk-run.log 2>&1
./venv/bin/python aesthetic_bulk_post.py --gap-min 40 --gap-max 75 >> logs/aesthetic-bulk-run.log 2>&1
cd /home/ubuntu/.hermes/profiles/bounty
hermes cron resume 4dc9d12c20a8 >> /home/ubuntu/x-op/logs/aesthetic-bulk-run.log 2>&1
cd /home/ubuntu/x-op
./venv/bin/python - <<'PY' >> logs/aesthetic-bulk-run.log 2>&1
import json, time, os
day = time.strftime('%Y-%m-%d')
fn = 'logs/aesthetic-%s.jsonl' % time.strftime('%Y%m%d')
n = 0
if os.path.exists(fn):
    n = sum(1 for l in open(fn) if l.strip())
st = json.load(open('worker/aesthetic-state.json'))
st.update({'last_post_iso': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'posts_today': max(st.get('posts_today', 0), n), 'day': day})
json.dump(st, open('worker/aesthetic-state.json', 'w'), indent=1)
print('state synced: posts_today=', st['posts_today'])
PY
echo "=== bulk run END $(date -u '+%Y-%m-%d %H:%M:%S') ===" >> logs/aesthetic-bulk-run.log
