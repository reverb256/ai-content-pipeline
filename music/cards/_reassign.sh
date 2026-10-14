#!/usr/bin/env bash
# Reassign the music-board producer cards to music-producer.
# Skips cards that are currently running (claimed) — those finish on their owner.
set -uo pipefail

CARDS="t_a8e2b160 t_3fa2d716 t_ef4773bd t_b17ddffc t_98c95aad t_667cda4a t_f247f8cd t_a22307e9 t_14d438ea"

for c in $CARDS; do
  status=$(hermes kanban --board music show "$c" 2>/dev/null | awk '/^  status:/{print $2}')
  if [ "$status" = "running" ]; then
    echo "SKIP   $c (running — owner finishes it)"
    continue
  fi
  printf '%-12s -> ' "$c"
  hermes kanban --board music assign "$c" music-producer 2>&1 | tail -1 || echo "FAILED"
done

echo
echo "=== AFTER ==="
hermes kanban --board music list
