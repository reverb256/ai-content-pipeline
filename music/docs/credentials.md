# Music Lane Credential Map

**Purpose:** Single reference for every credential the music lane needs.
Names and locations only. NEVER values.

**Storage convention:**
- Omarchy hosts (zephyr, etc.) → secretspec (`secretspec get <KEY>`)
- VPS hosts → sops (per-file `sops://` aliases in secretspec.toml)
- Never in the repo. Never in chat. Never in committed env files.

---

## Credential inventory

| # | Credential name | Type | Used by | Where stored | How to verify |
|---|---|---|---|---|---|
| 1 | `DISTROKID_SESSION` | Web session (Playwright profile) | `music/publish/playwright/distrokid.py` | Playwright browser profile at `~/browsers/distrokid/` | Dashboard loads without login redirect |
| 2 | `GUMROAD_ACCESS_TOKEN` | OAuth access token | `music/publish/gumroad.py` | secretspec (Omarchy) / sops (VPS) | `GET /v2/products` returns 200 |
| 3 | `BUTLER_API_KEY` | API key (source: wharf) | `music/publish/itchio.py`, butler CLI | secretspec + `~/.config/itch/butler_creds` | `butler push --dry-run` succeeds |
| 4 | `SONGTRADR_EMAIL` | Email (login identifier) | Songtradr API login | secretspec (Omarchy) / sops (VPS) | `POST /api/v1/user/login` returns JWT |
| 5 | `SONGTRADR_PASSWORD` | Password | Songtradr API login | secretspec (Omarchy) / sops (VPS) | `POST /api/v1/user/login` returns JWT |
| 6 | `SONGTRADR_JWT` | JWT bearer token (short-lived) | Songtradr API calls | secretspec (refreshed at runtime) | `GET /api/v1/user/me` returns 200 |
| 7 | `SOCAN_MEMBER_NUMBER` | Public identifier (not a secret) | Track registration | `music/docs/credentials.md` (this file) | Manual: visible in SOCAN portal |
| 8 | `SOCAN_USER_ID` | Portal login ID | SOCAN member portal | secretspec (Omarchy) / sops (VPS) | Manual: portal login succeeds |
| 9 | `SOCAN_PASSWORD` | Portal password | SOCAN member portal | secretspec (Omarchy) / sops (VPS) | Manual: portal login succeeds |

---

## Secret names in secretspec

The following keys must exist in secretspec under project `nixos-cluster-secrets`,
profile `production`:

```
GUMROAD_ACCESS_TOKEN
BUTLER_API_KEY
SONGTRADR_EMAIL
SONGTRADR_PASSWORD
SONGTRADR_JWT
SOCAN_USER_ID
SOCAN_PASSWORD
```

Add each with:
```bash
secretspec set <KEY> --project nixos-cluster-secrets --profile production
```

Resolve each with:
```bash
secretspec get <KEY> --project nixos-cluster-secrets --profile production
```

---

## Environment variables for music scripts

The music scripts expect these environment variables to be set in the shell
before running:

```bash
export GUMROAD_ACCESS_TOKEN="$(secretspec get GUMROAD_ACCESS_TOKEN)"
export BUTLER_API_KEY="$(secretspec get BUTLER_API_KEY)"
export SONGTRADR_EMAIL="$(secretspec get SONGTRADR_EMAIL)"
export SONGTRADR_PASSWORD="$(secretspec get SONGTRADR_PASSWORD)"
# SONGTRADR_JWT is obtained at runtime via the login API call
```

For Omarchy hosts, the `secretspec` CLI resolves the value server-side. The
plaintext never appears in the process environment unless explicitly exported.

For VPS hosts, the sops:// provider in secretspec.toml resolves the value from
the per-file sops-encrypted YAML.

---

## What is NOT a credential

- `music/quota-ledger.json` — pipeline state, not a secret
- `music/genres.yaml`, `music/lanes.yaml` — registry data, not secrets
- `music/autonomy.yaml` — rung state, not a secret
- `SOCAN_MEMBER_NUMBER` — public identifier, safe to store in this file
- ISRC codes — public identifiers, not secrets
- Payee names / PayPal emails — needed for payout setup but not API secrets

---

## Verification

Run `music/scripts/verify-credentials.sh` to check every credential. The script
makes real API calls and prints PASS or FAIL per surface.
