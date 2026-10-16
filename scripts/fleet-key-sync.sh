#!/usr/bin/env bash
# fleet-key-sync.sh — sync OPENCODE_GO_API_KEY into root + profile .env files on this host.
# Canonical value is read from stdin (one line) — e.g.:
#   grep '^OPENCODE_GO_API_KEY=' ~/.hermes/.env | ssh <host> 'bash ~/.hermes/scripts/fleet-key-sync.sh'
# --dry-run prints intended changes only. Key VALUES are never printed (hashes only).
set -u
DRY=0
[ "${1:-}" = "--dry-run" ] && DRY=1
KEYNAME="OPENCODE_GO_API_KEY"
H="$HOME/.hermes"

IFS= read -r keyline
case "$keyline" in
  "$KEYNAME"=*) : ;;
  *) echo "FATAL: stdin does not carry a $KEYNAME line"; exit 2 ;;
esac
keyhash=$(printf '%s' "$keyline" | sha256sum | cut -c1-20)

ts=$(date +%Y%m%d-%H%M%S)
bk="$H/backups/opencode-key-sync/$ts"

ok=0; changed=0; empty=0
for f in "$H/.env" "$H"/profiles/*/.env; do
  [ -e "$f" ] || continue
  if [ ! -s "$f" ]; then
    echo "EMPTY-SKIP   $f"
    empty=$((empty + 1))
    continue
  fi
  cur=$(grep -m1 "^$KEYNAME=" "$f" 2>/dev/null || true)
  if [ "$cur" = "$keyline" ]; then
    ok=$((ok + 1))
    continue
  fi
  changed=$((changed + 1))
  if [ "$DRY" = 1 ]; then
    if [ -n "$cur" ]; then echo "WOULD-REPLACE $f"; else echo "WOULD-ADD     $f"; fi
    continue
  fi
  mkdir -p "$bk"
  cp -p "$f" "$bk/$(echo "$f" | tr '/' '_')"
  tmp="$f.tmp.$$"
  grep -v "^$KEYNAME=" "$f" > "$tmp" || true
  if [ -n "$(tail -c1 "$tmp" 2>/dev/null)" ]; then printf '\n' >> "$tmp"; fi
  printf '%s\n' "$keyline" >> "$tmp"
  chmod --reference="$f" "$tmp" 2>/dev/null || chmod 600 "$tmp"
  mv "$tmp" "$f"
  echo "UPDATED       $f"
done

echo "----"
echo "keyhash=$keyhash ok=$ok changed=$changed empty=$empty root=$([ -e "$H/.env" ] && echo present || echo MISSING)"
mis=0
for f in "$H/.env" "$H"/profiles/*/.env; do
  [ -s "$f" ] || continue
  h=$(grep -m1 "^$KEYNAME=" "$f" 2>/dev/null | tr -d '\n' | sha256sum | cut -c1-20)
  [ "$h" = "$keyhash" ] || { echo "MISMATCH  $f"; mis=$((mis + 1)); }
done
echo "mismatches=$mis"
