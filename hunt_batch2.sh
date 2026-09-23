#!/bin/bash
# Image hunt for the rebuilt batch (games/anime/tech)
cd /home/ubuntu/x-op
PY=./venv/bin/python
declare -A TOPICS=(
  ["fnaf"]="FNAF Foxy plush Five Nights at Freddy's"
  ["spacemarine"]="Space Marine 2 Warhammer 40k"
  ["dk64"]="Donkey Kong 64 Nintendo 64"
  ["ahoge"]="ahoge anime hair antenna"
  ["mina"]="Mina Ashido My Hero Academia black dress"
  ["models"]="OpenAI GPT Anthropic Claude AI"
  ["destinyb"]="Destiny 2 Bungie comeback"
)
for slug in "${!TOPICS[@]}"; do
  echo "=== $slug: ${TOPICS[$slug]}"
  timeout 120 $PY media_web.py "${TOPICS[$slug]}" --n 2 --slug "$slug" 2>&1 | grep -E "^OK|^bing|images saved" | head -4
done
echo "HUNT DONE"
