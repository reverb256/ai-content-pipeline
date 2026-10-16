# GLASS-BREAK — one-time human checklist for the music lane

**Purpose:** Everything after this list is autonomous. These are the irreducible
human actions — they require identity, money, or a legal agreement. A bot must
never be sent to "go get credentials" (CoS dispatch boundary).

**How to use:** Complete each item top to bottom. One sitting. Each entry gives
the exact URL, the exact fields to fill, the exact cost, where the resulting
credential is stored, and the verification command that proves it works.

**Storage convention (fleet standard):**
- Omarchy hosts (zephyr, etc.) → secretspec (`secretspec get <KEY>`)
- VPS hosts → sops (per-file `sops://` aliases)
- Never in the repo. Never in chat. Never in env files committed to git.

**After all items pass:** Run `music/scripts/verify-credentials.sh` one final
time. All-PASS means the loop runs.

---

## Item 1 — DistroKid account + credential

| Field | Value |
|---|---|
| **URL** | https://distrokid.com |
| **Signup** | https://distrokid.com/signup |
| **Cost** | $24.99/yr (unlimited releases, no caps, no AI exclusions) |
| **Why human-only** | Annual fee = money decision + legal agreement (architecture §7 item 2) |
| **API status** | No official API. Two community automations exist for Playwright fallback (architecture §10.2). Upload is via the logged-in web session. |

**Fields to complete at signup:**
- Email + password
- Artist/stage name
- Legal name (must match payout identity)
- Country: Canada
- Tax form (W-8BEN for non-US, or W-9 if US citizen)

**Payout setup (same form):**
- Payee name (must match legal name)
- Payment method: PayPal or bank transfer (ACH/wire)
- Payout threshold: default or custom

**Credential produced:**
- A logged-in DistroKid web session (Playwright adapter uses the persistent browser profile)
- No API token to store. The session cookie IS the credential.

**Where stored:**
- Playwright browser profile at `~/browsers/distrokid/` (persistent context)
- Login state survives restarts. The Playwright adapter reuses it.

**Verification command:**
```bash
# The DistroKid Playwright adapter proves the session by loading the dashboard.
# Manual check: open https://distrokid.com/dashboard in the persistent profile.
# If the dashboard loads without a login redirect, the session is valid.
echo "DistroKid: manual verification — open distrokid.com/dashboard in the Playwright profile"
echo "If the dashboard loads (no login redirect): PASS"
echo "If redirected to login: FAIL — re-login via the Playwright adapter"
```

---

## Item 2 — Gumroad account + API access_token

| Field | Value |
|---|---|
| **URL** | https://gumroad.com |
| **API docs** | https://gumroad.com/api |
| **OAuth app creation** | https://gumroad.com/settings/advanced (scroll to "Applications") |
| **Cost** | Free. Gumroad takes 10% of each sale (no monthly fee). |
| **Why human-only** | Identity verification + payout setup (architecture §7 item 6) |

**Fields to complete at signup:**
- Email + password
- Display name
- Country: Canada

**API token creation:**
1. Go to https://gumroad.com/settings/advanced
2. Click "Create new application" (or "Add application")
3. Application name: `music-lane`
4. Redirect URL: `http://localhost:9999/oauth/callback` (not used in headless mode)
5. Scopes needed: `view_public`, `edit_products`, `view_sales`
6. Click "Generate access token"
7. Copy the token immediately (shown once)

**Payout setup (same settings area):**
- PayPal email (Gumroad pays via PayPal)
- Must verify email address before publishing products

**Credential produced:**
- `GUMROAD_ACCESS_TOKEN` — OAuth access token

**Where stored (Omarchy host — zephyr):**
```bash
# Store via secretspec (the fleet standard for Omarchy hosts)
secretspec set GUMROAD_ACCESS_TOKEN --project nixos-cluster-secrets --profile production
# The token resolves via: secretspec get GUMROAD_ACCESS_TOKEN
# The music/publish/gumroad.py adapter reads it from the environment.
# Export it in the shell before running the adapter:
export GUMROAD_ACCESS_TOKEN="$(secretspec get GUMROAD_ACCESS_TOKEN)"
```

**Where stored (VPS host):**
```bash
# Store in a per-file sops-encrypted YAML, then reference via secretspec sops:// alias
# Example: /home/j_kro/Work/Projects/nixos-secrets/secrets/music/gumroad-access-token.yaml
# secretspec.toml entry:
#   sops_music_gumroad_access_token = "sops:///home/j_kro/Work/Projects/nixos-secrets/secrets/music/gumroad-access-token.yaml"
#   GUMROAD_ACCESS_TOKEN = { ref = { item = "data" }, providers = ["sops_music_gumroad_access_token"] }
```

**Verification command:**
```bash
# Real API call — lists products for the authenticated user.
# A 200 response with a JSON array proves the token is valid.
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $GUMROAD_ACCESS_TOKEN" \
  https://api.gumroad.com/v2/products
# Expected: 200 (even if the product list is empty)
# 401 = token invalid or expired
```

---

## Item 3 — itch.io account + butler API key

| Field | Value |
|---|---|
| **URL** | https://itch.io |
| **Signup** | https://itch.io/register |
| **Butler docs** | https://itch.io/docs/butler |
| **Cost** | Free |
| **Why human-only** | Identity (architecture §7 item 6) |

**Fields to complete at signup:**
- Email + password
- Username (used in butler push targets: `<user>/<game>:<channel>`)

**API key creation:**
1. Go to https://itch.io/user/settings/api-keys
2. Click "Generate new API key"
3. Source: `wharf` (this is the butler/wharf key — the only one that works with butler)
4. Copy the key

**Butler CLI (if not already installed):**
```bash
# Install butler (single binary)
curl -L -o ~/.local/bin/butler https://broth.itch.ovh/butler/linux-amd64/LATEST/default/butler
chmod +x ~/.local/bin/butler

# One-time login (stores key at ~/.config/itch/butler_creds)
butler login
# Paste the API key when prompted
```

**Credential produced:**
- `BUTLER_API_KEY` — itch.io API key (source: wharf)
- Also stored by butler at `~/.config/itch/butler_creds` after `butler login`

**Where stored (Omarchy host — zephyr):**
```bash
# Primary: secretspec
secretspec set BUTLER_API_KEY --project nixos-cluster-secrets --profile production

# Secondary: butler's own config (for CLI usage)
# ~/.config/itch/butler_creds — written by 'butler login', read by butler CLI
```

**Where stored (VPS host):**
```bash
# sops-encrypted file + secretspec sops:// alias (same pattern as Gumroad)
```

**Verification command:**
```bash
# butler push with --dry-run verifies the key without uploading.
# A successful dry-run proves the credential is valid.
butler push --dry-run ~/empty-test-dir your-itch-username/test-project:html5
# Expected: "Dry run — no files would be uploaded" (or a listing of what would upload)
# If the key is invalid: "401 Unauthorized" or "Invalid API key"

# Alternative: verify the key file exists and is non-empty
test -s ~/.config/itch/butler_creds && echo "PASS: butler_creds present" || echo "FAIL: no butler creds"
```

---

## Item 4 — Songtradr account + API login

| Field | Value |
|---|---|
| **URL** | https://www.songtradr.com |
| **API docs** | https://api.songtradr.com/swagger-ui/index.html |
| **Python client** | `songtradr-api-client-python` (PyPI) |
| **Cost** | Free tier available (paid tiers unlock more features) |
| **Why human-only** | Identity + sync agreement (architecture §7 item 4) |

**Fields to complete at signup:**
- Email + password
- First name + last name
- Country: Canada
- Account type: "Music Creator" or "Artist" (NOT "Music Supervisor" — that's the buyer side)
- Agree to the Music Creator Agreement

**API authentication:**
- Auth endpoint: `POST https://api.songtradr.com/api/v1/user/login`
- Request body: `{"email": "...", "password": "..."}`
- Response contains `jwtToken` — use as `Authorization: Bearer <jwtToken>` in all subsequent calls
- No separate API key to generate; the JWT token IS the credential.

**Credential produced:**
- A JWT bearer token (obtained via login API call, valid until expiry)

**Where stored (Omarchy host — zephyr):**
```bash
# The JWT token is short-lived. Store it in secretspec and refresh on expiry.
secretspec set SONGTRADR_JWT --project nixos-cluster-secrets --profile production
secretspec set SONGTRADR_EMAIL --project nixos-cluster-secrets --profile production
secretspec set SONGTRADR_PASSWORD --project nixos-cluster-secrets --profile production
```

**Where stored (VPS host):**
```bash
# Same sops:// pattern. Store email + password; JWT is obtained at runtime.
```

**Verification command:**
```bash
# Real API call — login and verify the JWT works.
# Returns 200 with a JWT token if credentials are valid.
RESP=$(curl -s -X POST https://api.songtradr.com/api/v1/user/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$SONGTRADR_EMAIL\",\"password\":\"$SONGTRADR_PASSWORD\"}")
echo "$RESP" | jq -r '.jwtToken' | grep -q . && echo "PASS: Songtradr login OK" || echo "FAIL: Songtradr login failed"

# Then verify the JWT with a real API call (e.g., get user profile):
JWT=$(echo "$RESP" | jq -r '.jwtToken')
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $JWT" \
  https://api.songtradr.com/api/v1/user/me
# Expected: 200
```

---

## Item 5 — SOCAN registration (Canadian PRO)

| Field | Value |
|---|---|
| **URL** | https://www.socan.com/sign-up-for-performing-rights/ |
| **Member portal** | https://www.socan.com/new-member-portal/ |
| **Writer ID creation** | https://www.socan.com/jsp/en/mem/memberCreateWriter.jsp |
| **Cost** | Free to join (no membership fee) |
| **Why human-only** | Legal identity documents + Canadian PRO enrolment (architecture §7 item 3) |

**Fields to complete at signup:**
- First name + last name (must match legal ID)
- Email
- Date of birth
- Social Insurance Number (last 4 digits — required for Canadian writers)
- Mailing address
- Phone number
- Create a User ID + password

**What SOCAN accepts (verified 2026-10-08):**
- **AI-Assisted Works** = registrable. "Substantial human input, author uses AI as a tool."
- **AI-Generated Outputs** = NOT registrable. "Content autonomously generated, minimal human input."
- Our pipeline qualifies: lyrics are human-authored (writer profile), AI renders instrumentals.
- See `music/docs/pro-registration.md` for the full registration path.

**Credential produced:**
- SOCAN member number
- SOCAN User ID + password (for the member portal)

**Where stored:**
- Member number: record in `music/docs/credentials.md` (it is not a secret — it is a public identifier)
- User ID + password: secretspec
```bash
secretspec set SOCAN_USER_ID --project nixos-cluster-secrets --profile production
secretspec set SOCAN_PASSWORD --project nixos-cluster-secrets --profile production
```

**Verification command:**
```bash
# SOCAN has no public API. Verification is a manual portal login.
echo "SOCAN: manual verification — log in at https://www.socan.com/new-member-portal/"
echo "If the portal loads and shows the member dashboard: PASS"
echo "If login fails: FAIL — check credentials"
```

---

## Item 6 — Payout + tax details on each surface

This item is NOT a credential. It is a one-time configuration of payout identity
and tax information on each platform. Every surface needs this before revenue
can be collected.

| Surface | Payout method | Tax form | Where to set up |
|---|---|---|---|
| **DistroKid** | PayPal or bank transfer | W-8BEN (non-US) or W-9 (US) | https://distrokid.com/settings/payout |
| **Gumroad** | PayPal only | Tax interview at signup ( Gumroad handles 1099-K) | https://gumroad.com/settings/payout |
| **itch.io** | PayPal or direct deposit | W-8BEN or W-9 | https://itch.io/user/settings/payout |
| **Songtradr** | PayPal (via their payment system) | Tax interview at signup | https://www.songtradr.com/settings (after login) |
| **SOCAN** | Direct deposit (Canadian members) | No tax form — SOCAN is a Canadian PRO | Member portal after login |

**Critical rule:** The payee name on every surface MUST match the legal name
used on DistroKid and SOCAN. Mismatched payee names cause payment holds.

**Verification command:**
```bash
echo "=== Payout verification ==="
echo "1. DistroKid: log in at distrokid.com → Settings → Payout. Confirm payee name matches legal name."
echo "2. Gumroad: log in at gumroad.com → Settings → Payout. Confirm PayPal email is correct."
echo "3. itch.io: log in at itch.io → User Settings → Payout. Confirm payment method is set."
echo "4. Songtradr: log in at songtradr.com → Settings. Confirm payout method is configured."
echo "5. SOCAN: log in at socan.com portal → Account. Confirm direct deposit info is set."
echo ""
echo "All five must show the same legal name (or the same PayPal email) to pass."
```

---

## Item 7 — Publish-policy decision: the autonomy rung each lane starts at

This item is a CREATIVE-DIRECTION decision. It is j_kro's call, not a bot's.

**The autonomy ladder (architecture §11.2):**

| Rung | Behaviour | Promotion evidence |
|---|---|---|
| **advisory** | produces, human approves each publish | — (starting rung) |
| **supervised** | publishes to private/draft, human flips public | 10 clean advisory publishes |
| **monitored** | publishes public, human audits weekly | 20 clean supervised, zero strikes |
| **full** | publishes public, human audits monthly | 50 clean monitored, revenue positive |

**Current state (from `music/autonomy.yaml`):**
All 10 lanes start at `advisory`. Zero clean publishes. Zero platform strikes.

**The decision:**
For each lane, j_kro decides the starting rung. The safe default is `advisory`
for all lanes — the system produces, j_kro approves each publish. Lanes can be
promoted as evidence accumulates.

**Where recorded:**
- `music/autonomy.yaml` — the `rung:` field per lane
- j_kro approves rung changes on the kanban board with evidence

**Verification command:**
```bash
# Show the current rung for every lane
python3 -c "
import yaml
with open('music/autonomy.yaml') as f:
    doc = yaml.safe_load(f)
for name, lane in doc['lanes'].items():
    print(f'  {name:25s} rung={lane[\"rung\"]}  publishes={lane[\"evidence\"][\"clean_publishes\"]}')
"
# Every lane should show rung=advisory on first run.
# If any lane shows a different rung, j_kro has already set it.
```

---

## Summary — one-page checklist

```
[ ] 1. DistroKid account created ($24.99/yr). Payout + tax form set up.
[ ] 2. Gumroad account created. API token generated. PayPal payout set up.
[ ] 3. itch.io account created. Butler API key generated (source: wharf).
[ ] 4. Songtradr account created. API login verified (JWT obtained).
[ ] 5. SOCAN membership obtained. Writer ID created.
[ ] 6. Payout + tax details configured on ALL FIVE surfaces.
[ ] 7. Publish-policy rung decided for each lane (default: advisory).

After all items pass:
    bash music/scripts/verify-credentials.sh
    # All surfaces should print PASS.
    # Any FAIL means that credential is missing or invalid.
```

**What NOT to do:**
- Do NOT create any account from a bot.
- Do NOT ask for any credential value in chat.
- Do NOT store any credential in the repo.
- Do NOT store any credential in a file that gets committed to git.
- Do NOT skip the tax form — an incomplete tax form blocks payouts.
