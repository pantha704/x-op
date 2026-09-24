#!/bin/bash
# scrub-public.sh - rebuild the PUBLIC template repo from live ops, identity-free.
#
# The public repo (your_account/x-op) is a scrubbed template anyone can run on
# their own account. The live ops tree (~/x-op) contains the operator's handle,
# state, logs and images - never push it public. Update flow:
#
#   bash ops/scrub-public.sh [--push]
#
# - clones the live tree to a temp dir
# - rewrites ALL history: identity -> scrubbed tokens, anonymous authors
# - prunes operational data (logs, images, reports, state, campaign)
# - (--push) force-pushes the result to the public repo
set -euo pipefail

LIVE=/home/ubuntu/x-op
PUB=https://github.com/your_account/x-op.git
TMP=/tmp/x-op-pub-build
REPL=/tmp/x-op-replacements.txt

cat > "$REPL" <<'EOF'
your_handle==>your_handle
your_account==>your_account
Operator==>Operator
OPERATOR==>OPERATOR
operator==>operator
operator@x-op.local==>contributor@x-op.example
EOF

rm -rf "$TMP"
git clone -q "$LIVE" "$TMP"
cd "$TMP"
git filter-repo --force --replace-text "$REPL" \
  --invert-paths \
  --path logs/ --path images/ --path reports/ --path campaign/ \
  --path research/post-patterns/raw/ --path worker/ \
  --name-callback 'return b"x-op contributor"' \
  --email-callback 'return b"contributor@x-op.example"'

echo "=== identity check (must be 0) ==="
grep -riE 'operator|your_account|pratham' . 2>/dev/null | grep -v '.git/' | wc -l
git log --all -p 2>/dev/null | grep -ciE 'operator|your_account' || true

if [ "${1:-}" = "--push" ]; then
  git remote add origin "$PUB" 2>/dev/null || git remote set-url origin "$PUB"
  git push --force origin main
  echo "public template rebuilt + pushed"
fi
