#!/bin/bash
# Aesthetic image hunt for the soft batch
cd /home/ubuntu/x-op
PY=./venv/bin/python
declare -A TOPICS=(
  ["aes1"]="aesthetic anime scenery sunset wallpaper"
  ["aes2"]="anime girl window rain cozy"
  ["aes3"]="cozy anime room night lamp"
  ["aes4"]="anime night sky stars silhouette"
  ["aes5"]="anime sunrise clouds aesthetic"
  ["aes6"]="anime sky clouds scenery"
  ["aes7"]="cozy anime cafe rainy day"
  ["aes8"]="anime train window sunset"
  ["aes9"]="cherry blossom anime aesthetic night"
  ["aes10"]="anime field flowers summer evening"
)
for slug in "${!TOPICS[@]}"; do
  echo "=== $slug"
  timeout 120 $PY media_web.py "${TOPICS[$slug]}" --n 2 --slug "$slug" 2>&1 | grep -E "^OK|images saved" | head -3
done
echo "SOFT HUNT DONE"
