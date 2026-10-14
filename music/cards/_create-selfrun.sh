#!/usr/bin/env bash
# One-shot: create the self-run / asset-market music cards on the `music` board.
set -euo pipefail
cd /home/j_kro/Projects/ai-content-pipeline

create() {
  local title="$1" assignee="$2" body="$3"
  echo "--- $assignee :: $title"
  hermes kanban --board music create "$title" --body-file "$body" --assignee "$assignee"
}

create "music: asset-pack generator (loops, stems, one-shots, SFX)" \
       "storyteller" \
       "music/cards/asset-pack-generator.md"

create "music: itch.io + Gumroad API publish adapters" \
       "distributor" \
       "music/cards/storefront-adapters.md"

create "music: Playwright adapters for no-API surfaces" \
       "producer" \
       "music/cards/playwright-adapters.md"

create "music: self-run scheduler + music oracle (always-on host)" \
       "producer" \
       "music/cards/self-run-scheduler-oracle.md"

create "music: glass-break checklist + credential provisioning" \
       "producer" \
       "music/cards/glass-break-checklist.md"

echo
echo "=== MUSIC BOARD ==="
hermes kanban --board music list
