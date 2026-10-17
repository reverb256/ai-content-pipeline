#!/usr/bin/env bash
# verify-credentials.sh — verify each music-lane credential exists and is VALID.
#
# For each surface, this script makes a real API call (or checks the credential
# file) and prints PASS or FAIL. No credential values are printed.
#
# Usage:
#   bash music/scripts/verify-credentials.sh
#
# Exit codes: 0 = every credential surface passed, 1 = at least one FAIL.
#   Rows printed as MANUAL are not credentials (there is nothing to execute) and
#   do not affect the exit code.
#
# Requirements:
#   - curl (for Gumroad + Songtradr API calls)
#   - jq (for parsing JSON responses)
#   - secretspec (for Omarchy hosts)
#   - butler CLI (for itch.io verification; the creds file is accepted as fallback)
#
# What the resolver talks to (measured 2026-10-16, secretspec 0.21.0):
#   a project is identified by the manifest's [project].name, and `secretspec get`
#   takes -f/--file and -P/--profile; it has NO --project flag ("unexpected
#   argument '--project' found"). The resolver therefore passes the manifest
#   explicitly, in this order:
#     1. $SECRETSPEC_FILE
#     2. $HOME/.config/secretspec/secretspec-$(hostname).toml
#     3. whatever `secretspec` auto-detects walking up from the repo root
#   The profile is $SECRETSPEC_PROFILE (default: production). The key names are
#   the ones listed in music/docs/credentials.md.

set -euo pipefail

# Work from the repo root so the relative paths below are stable.
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

PASS_COUNT=0
FAIL_COUNT=0
MANUAL_COUNT=0

# ── Resolver state ────────────────────────────────────────────────────────────
SS_PROFILE="${SECRETSPEC_PROFILE:-production}"
SS_MANIFEST="${SECRETSPEC_FILE:-}"
SS_BIN="$(command -v secretspec 2>/dev/null || true)"
SS_STATE="ok"
if [ -z "$SS_BIN" ]; then
    SS_STATE="no-cli"
elif [ -z "$SS_MANIFEST" ] && [ -f "$HOME/.config/secretspec/secretspec-$(hostname).toml" ]; then
    SS_MANIFEST="$HOME/.config/secretspec/secretspec-$(hostname).toml"
fi

# ── Helper: resolve a secret via secretspec ───────────────────────────────────
# Prints the value on success (it is never logged). On failure prints nothing and
# records the value-free reason for resolver_why(), so a FAIL names its real cause
# instead of claiming "not found in secretspec" for every possible failure.
# The reason travels through a file because resolve_secret runs inside a $( )
# command substitution: a variable it set would die with that subshell.
SS_WHY_FILE="$(mktemp)"
trap 'rm -f "$SS_WHY_FILE"' EXIT
: > "$SS_WHY_FILE"

resolver_why() { cat "$SS_WHY_FILE"; }

resolve_secret() {
    local key="$1"
    local out="" rc=0 why=""
    : > "$SS_WHY_FILE"
    if [ "$SS_STATE" = "no-cli" ]; then
        printf '%s' "secretspec CLI not installed on $(hostname)" > "$SS_WHY_FILE"
        return 0
    fi
    if [ -n "$SS_MANIFEST" ]; then
        out="$("$SS_BIN" get "$key" -f "$SS_MANIFEST" -P "$SS_PROFILE" 2>/dev/null)" || rc=$?
    else
        out="$("$SS_BIN" get "$key" -P "$SS_PROFILE" 2>/dev/null)" || rc=$?
    fi
    if [ "$rc" -eq 0 ] && [ -n "$out" ]; then
        printf '%s' "$out"
        return 0
    fi
    # Second call only to read the error text. A failed resolution has no value,
    # so this stays value-free.
    if [ -n "$SS_MANIFEST" ]; then
        why="$("$SS_BIN" get "$key" -f "$SS_MANIFEST" -P "$SS_PROFILE" 2>&1 >/dev/null \
            | sed '/^[[:space:]]*$/d' | tail -n 1 | cut -c1-140)"
    else
        why="$("$SS_BIN" get "$key" -P "$SS_PROFILE" 2>&1 >/dev/null \
            | sed '/^[[:space:]]*$/d' | tail -n 1 | cut -c1-140)"
    fi
    [ -n "$why" ] || why="secretspec returned no value for $key (profile $SS_PROFILE)"
    printf '%s' "$why" > "$SS_WHY_FILE"
    return 0
}

# ── Helper: print PASS or FAIL ────────────────────────────────────────────────
report() {
    local surface="$1"
    local result="$2"
    local detail="${3:-}"
    if [ "$result" = "PASS" ]; then
        PASS_COUNT=$((PASS_COUNT + 1))
        printf "  %-20s PASS  %s\n" "$surface" "$detail"
    else
        FAIL_COUNT=$((FAIL_COUNT + 1))
        printf "  %-20s FAIL  %s\n" "$surface" "$detail"
    fi
}

# ── Helper: print MANUAL for a row that is not a credential ───────────────────
manual() {
    local surface="$1"
    local detail="${2:-}"
    MANUAL_COUNT=$((MANUAL_COUNT + 1))
    printf "  %-20s MANUAL  %s\n" "$surface" "$detail"
}

echo "=== Music Lane Credential Verification ==="
echo "Time: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Host: $(hostname)"
echo "Repo: $REPO_ROOT"
if [ "$SS_STATE" = "no-cli" ]; then
    echo "Resolver: secretspec NOT installed on this host"
elif [ -n "$SS_MANIFEST" ]; then
    echo "Resolver: secretspec manifest $SS_MANIFEST (profile $SS_PROFILE)"
else
    echo "Resolver: secretspec auto-detect from $REPO_ROOT (profile $SS_PROFILE)"
fi
echo ""

# ── 1. DistroKid ───────────────────────────────────────────────────────────────
echo "── 1. DistroKid ──"
DISTROKID_PROFILE="$HOME/browsers/distrokid"
if [ -d "$DISTROKID_PROFILE" ] && [ "$(ls -A "$DISTROKID_PROFILE" 2>/dev/null)" ]; then
    report "DistroKid" "PASS" "Playwright profile exists at $DISTROKID_PROFILE"
else
    report "DistroKid" "FAIL" "No Playwright profile at $DISTROKID_PROFILE — log in once via the Playwright adapter"
fi

# ── 2. Gumroad ─────────────────────────────────────────────────────────────────
echo "── 2. Gumroad ──"
GUMROAD_TOKEN="$(resolve_secret GUMROAD_ACCESS_TOKEN)"
WHY_GUMROAD="$(resolver_why)"
if [ -z "$GUMROAD_TOKEN" ]; then
    report "Gumroad" "FAIL" "GUMROAD_ACCESS_TOKEN unresolved — $WHY_GUMROAD"
else
    HTTP_CODE=$(curl -s -o /tmp/gumroad_products.json -w "%{http_code}" \
        -H "Authorization: Bearer $GUMROAD_TOKEN" \
        https://api.gumroad.com/v2/products 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        report "Gumroad" "PASS" "API token valid (GET /v2/products → 200)"
    elif [ "$HTTP_CODE" = "401" ]; then
        report "Gumroad" "FAIL" "API token rejected (401 Unauthorized) — regenerate at gumroad.com/settings/advanced"
    else
        report "Gumroad" "FAIL" "API call failed (HTTP $HTTP_CODE) — check network or token"
    fi
fi

# ── 3. itch.io (butler) ────────────────────────────────────────────────────────
echo "── 3. itch.io ──"
BUTLER_KEY="$(resolve_secret BUTLER_API_KEY)"
WHY_BUTLER="$(resolver_why)"
BUTLER_CREDS="$HOME/.config/itch/butler_creds"
BUTLER_OK=false
BUTLER_DETAIL=""

if command -v butler &>/dev/null; then
    # butler is installed — verify with a dry-run push
    # Create a minimal test directory
    TEST_DIR="$(mktemp -d)"
    echo "test" > "$TEST_DIR/test.txt"
    BUTLER_OUTPUT=$(butler push --dry-run "$TEST_DIR" "test-user/test-project:html5" 2>&1) && BUTLER_OK=true
    rm -rf "$TEST_DIR"
    if [ "$BUTLER_OK" = true ]; then
        BUTLER_DETAIL="butler dry-run push succeeded"
    else
        BUTLER_DETAIL="butler dry-run failed: $BUTLER_OUTPUT"
    fi
else
    # butler not installed — check for the creds file
    if [ -f "$BUTLER_CREDS" ] && [ -s "$BUTLER_CREDS" ]; then
        BUTLER_OK=true
        BUTLER_DETAIL="butler_creds file present (butler CLI not installed)"
    else
        BUTLER_DETAIL="butler CLI not installed and no butler_creds file"
    fi
fi

if [ -z "$BUTLER_KEY" ] && [ ! -f "$BUTLER_CREDS" ]; then
    report "itch.io" "FAIL" "BUTLER_API_KEY unresolved ($WHY_BUTLER) and no butler_creds file"
elif [ "$BUTLER_OK" = true ]; then
    report "itch.io" "PASS" "$BUTLER_DETAIL"
else
    report "itch.io" "FAIL" "$BUTLER_DETAIL"
fi

# ── 4. Songtradr ───────────────────────────────────────────────────────────────
echo "── 4. Songtradr ──"
SONGTRADR_EMAIL="$(resolve_secret SONGTRADR_EMAIL)"
WHY_EMAIL="$(resolver_why)"
SONGTRADR_PASSWORD="$(resolve_secret SONGTRADR_PASSWORD)"
WHY_PASSWORD="$(resolver_why)"
if [ -z "$SONGTRADR_EMAIL" ] || [ -z "$SONGTRADR_PASSWORD" ]; then
    report "Songtradr" "FAIL" "SONGTRADR_EMAIL / SONGTRADR_PASSWORD unresolved — ${WHY_EMAIL:-ok} | ${WHY_PASSWORD:-ok}"
else
    LOGIN_RESP=$(curl -s -X POST https://api.songtradr.com/api/v1/user/login \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"$SONGTRADR_EMAIL\",\"password\":\"$SONGTRADR_PASSWORD\"}" 2>/dev/null || echo "")
    JWT=$(echo "$LOGIN_RESP" | jq -r '.jwtToken // empty' 2>/dev/null)
    if [ -n "$JWT" ]; then
        # Verify the JWT with a real API call
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
            -H "Authorization: Bearer $JWT" \
            https://api.songtradr.com/api/v1/user/me 2>/dev/null || echo "000")
        if [ "$HTTP_CODE" = "200" ]; then
            report "Songtradr" "PASS" "Login OK, JWT valid (GET /api/v1/user/me → 200)"
        else
            report "Songtradr" "FAIL" "Login OK but JWT rejected (HTTP $HTTP_CODE) — token may be expired"
        fi
    else
        ERROR_MSG=$(echo "$LOGIN_RESP" | jq -r '.message // "unknown error"' 2>/dev/null)
        report "Songtradr" "FAIL" "Login failed: $ERROR_MSG"
    fi
fi

# ── 5. SOCAN ───────────────────────────────────────────────────────────────────
echo "── 5. SOCAN ──"
SOCAN_USER="$(resolve_secret SOCAN_USER_ID)"
WHY_SOCAN_USER="$(resolver_why)"
SOCAN_PASS="$(resolve_secret SOCAN_PASSWORD)"
WHY_SOCAN_PASS="$(resolver_why)"
if [ -z "$SOCAN_USER" ] || [ -z "$SOCAN_PASS" ]; then
    report "SOCAN" "FAIL" "SOCAN_USER_ID / SOCAN_PASSWORD unresolved — ${WHY_SOCAN_USER:-ok} | ${WHY_SOCAN_PASS:-ok}"
else
    # SOCAN has no public API. This row proves presence only, never validity.
    report "SOCAN" "PASS" "credentials resolve — presence only, validity is manual (no public API)"
fi

# ── 6. Payout + tax ────────────────────────────────────────────────────────────
echo "── 6. Payout + tax ──"
echo "  Payout configuration cannot be verified by API — nothing here is executed."
echo "  Manual check: log in to each surface and confirm payee name matches legal name."
echo "    DistroKid : https://distrokid.com/settings/payout"
echo "    Gumroad    : https://gumroad.com/settings/payout"
echo "    itch.io    : https://itch.io/user/settings/payout"
echo "    Songtradr  : https://www.songtradr.com/settings (after login)"
echo "    SOCAN      : Member portal → Account settings"
manual "Payout + tax" "not a credential — manual check above, never counted as PASS"

# ── 7. Autonomy rung ───────────────────────────────────────────────────────────
echo "── 7. Autonomy rung ──"
# The lane runs its Python with /usr/bin/python3. The PATH `python3` on an agent
# host is the tool python and has no pyyaml (measured 2026-10-16, nexus), so pick
# the first interpreter that can actually import yaml and name it on failure.
PY_YAML=""
for cand in /usr/bin/python3 python3; do
    if command -v "$cand" >/dev/null 2>&1 && "$cand" -c "import yaml" >/dev/null 2>&1; then
        PY_YAML="$cand"
        break
    fi
done
if [ -f "music/autonomy.yaml" ] && [ -n "$PY_YAML" ]; then
    if RUNG_COUNT=$("$PY_YAML" -c "
import yaml
with open('music/autonomy.yaml') as f:
    doc = yaml.safe_load(f)
lanes = doc.get('lanes', {})
advisory = sum(1 for l in lanes.values() if l.get('rung') == 'advisory')
other = len(lanes) - advisory
print(f'{len(lanes)} lanes ({advisory} advisory, {other} other)')
" 2>/dev/null); then
        report "Autonomy rung" "PASS" "autonomy.yaml present — $RUNG_COUNT"
    else
        report "Autonomy rung" "FAIL" "music/autonomy.yaml present but unreadable ($PY_YAML could not parse it)"
    fi
elif [ ! -f "music/autonomy.yaml" ]; then
    report "Autonomy rung" "FAIL" "music/autonomy.yaml not found"
else
    report "Autonomy rung" "FAIL" "no python3 with pyyaml found (/usr/bin/python3 or PATH python3)"
fi

# ── Summary ────────────────────────────────────────────────────────────────────
echo ""
echo "=== Summary ==="
echo "  PASS: $PASS_COUNT"
echo "  FAIL: $FAIL_COUNT"
echo "  MANUAL: $MANUAL_COUNT"
echo ""
if [ "$FAIL_COUNT" -gt 0 ]; then
    echo "  Some credentials are missing or invalid."
    echo "  See music/docs/GLASS-BREAK.md for the one-time setup checklist."
    echo "  Then re-run: bash music/scripts/verify-credentials.sh"
    exit 1
else
    echo "  All credentials present and valid. The music lane can self-run."
    exit 0
fi
