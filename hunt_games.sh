#!/bin/bash
# Image hunt for the games/PC/Genshin batch
cd /home/ubuntu/x-op
PY=./venv/bin/python
declare -A TOPICS=(
  ["gg1"]="Genshin Impact Vesna character teaser"
  ["gg2"]="Nodusfall HoYoverse dark fantasy game"
  ["gg3"]="Honkai Star Rail anime characters"
  ["gg4"]="HoYoverse miHoYo logo"
  ["gg5"]="Counter-Strike 2 game"
  ["gg6"]="Wallpaper Engine Steam app"
  ["gg7"]="Valve Steam Frame VR headset"
  ["gg8"]="Steam Deck 2 Valve handheld"
  ["gg9"]="Elden Ring Nightreign game"
  ["gg10"]="Tokyo Game Show 2026"
)
for slug in "${!TOPICS[@]}"; do
  echo "=== $slug"
  timeout 120 $PY media_web.py "${TOPICS[$slug]}" --n 2 --slug "$slug" 2>&1 | grep -E "^OK|images saved" | head -3
done
echo "GAMES HUNT DONE"
