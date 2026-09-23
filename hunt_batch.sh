#!/bin/bash
# Batch image hunt for the 10 post topics (Bing via rig + download)
cd /home/ubuntu/x-op
PY=./venv/bin/python
declare -A TOPICS=(
  ["macstudio"]="Mac Studio M5 Ultra Apple"
  ["grok"]="Grok 4.7 xAI launch"
  ["grandblue"]="Grand Blue anime season 4"
  ["narnia"]="Narnia Greta Gerwig wood between the worlds"
  ["fortnite"]="Fortnite Halloween event 2026"
  ["streetfighter"]="Street Fighter movie 2026 teaser"
  ["jojo"]="JoJo Steel Ball Run anime"
  ["googlebook"]="Googlebook laptop Google"
  ["gpt6"]="GPT-6 OpenAI"
)
for slug in "${!TOPICS[@]}"; do
  echo "=== $slug: ${TOPICS[$slug]}"
  timeout 120 $PY media_web.py "${TOPICS[$slug]}" --n 2 --slug "$slug" 2>&1 | grep -E "^OK|^bing|images saved" | head -4
done
echo "HUNT DONE"
