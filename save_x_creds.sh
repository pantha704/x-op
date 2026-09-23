#!/usr/bin/env bash
# Save the @your_handle X login for rig re-login.
# RUN THIS YOURSELF (LO) in a terminal / over RDP. The password is read with echo off and never
# printed, never sent to the agent, never in chat. File is chmod 600 in a 700 dir.
#
#   bash /home/ubuntu/x-op/save_x_creds.sh
#
set -u

DIR="$HOME/.config/x-op"
FILE="$DIR/x-creds.json"
mkdir -p "$DIR"
chmod 700 "$DIR"

echo "=== save X creds for the rig (values hidden) ==="
read -r -p "X email or username: " IDENT
if [ -z "$IDENT" ]; then echo "aborted: empty identifier"; exit 1; fi

read -r -s -p "X password (hidden): " PASS; echo
if [ -z "$PASS" ]; then echo "aborted: empty password"; exit 1; fi

read -r -s -p "X password again (hidden): " PASS2; echo
if [ "$PASS" != "$PASS2" ]; then echo "aborted: passwords do not match"; exit 1; fi

printf '{\n "identifier": "%s",\n "password": "%s"\n}\n' \
  "$(printf '%s' "$IDENT" | sed 's/\\/\\\\/g; s/"/\\"/g')" \
  "$(printf '%s' "$PASS" | sed 's/\\/\\\\/g; s/"/\\"/g')" > "$FILE"

chmod 600 "$FILE"
unset PASS PASS2

echo "saved: $FILE ($(stat -c '%a' "$FILE"))"
echo "the agent can now re-login the rig without seeing the values."
