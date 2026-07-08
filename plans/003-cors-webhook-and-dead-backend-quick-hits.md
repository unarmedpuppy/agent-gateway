# Plan 003: CORS allowlist, fail-closed webhook, and repoint the dead LLM backend

> **Executor instructions**: Follow this plan step by step. Run every
> verification command before moving on. On any STOP condition, stop and
> report. Update this plan's row in `plans/README.md` when done.
>
> **Drift check (run first)**: `git diff --stat bae8f73..HEAD -- gateway/main.py gateway/config.py core/config.py gateway/adapters/mattermost/webhooks.py gateway/adapters/mattermost/config.py`
> Mismatch with the excerpts below = STOP.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW–MED — the webhook fail-closed change breaks Tayne's Mattermost trigger if the deployed `TAYNE_WEBHOOK_TOKEN` is unset (intentional; must be verified before deploy); the backend repoint has no downside since the current default is already dead
- **Depends on**: none (independent quick hits; complements plan 001)
- **Category**: security / migration
- **Planned at**: commit `bae8f73`, 2026-07-07

## Why this matters

Three convention/correctness gaps, each a small, self-contained fix:

1. **Wildcard CORS with credentials** — `gateway/main.py:59-64` sets `allow_origins=["*"]` + `allow_credentials=True`. This violates `homelab-app-template/CONVENTIONS.md` §2 ("never `allow_origins=["*"]` with credentials"), and the combination is invalid per the CORS spec (browsers reject it), so it's both insecure-signalling and non-functional for credentialed requests.
2. **Fail-open Mattermost webhook** — `gateway/adapters/mattermost/webhooks.py:44`: `if settings.tayne_webhook_token and token != settings.tayne_webhook_token:` — if `TAYNE_WEBHOOK_TOKEN` is unset, the check is skipped and *any* POST to `/webhook/mattermost/tayne` drives Tayne (LLM cost + impersonation). Same fail-open anti-pattern this fleet's security audit called out elsewhere.
3. **Dead LLM backend defaults** — `gateway/config.py:17` (`http://llm-router:8000`) and `core/config.py:8` (`http://local-ai-router:8000`) both 404 post-cutover (ECOSYSTEM §2.2 lists agent-gateway's `LOCAL_AI_URL` as a broken reference; fix → `http://ai-gateway:8000` + `lai-*` key).

## Current state

- `gateway/main.py:58-64`:

  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["*"],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  ```

- `gateway/adapters/mattermost/webhooks.py:43-47`:

  ```python
  settings = get_mattermost_settings()
  if settings.tayne_webhook_token and token != settings.tayne_webhook_token:
      logger.warning(f"Invalid webhook token from {user_name}")
      raise HTTPException(status_code=401, detail="Invalid webhook token")
  ```

- `gateway/config.py:17` → `local_ai_url: str = Field(default="http://llm-router:8000")`
- `core/config.py:8` → `local_ai_url: str = os.getenv("LOCAL_AI_URL", "http://local-ai-router:8000")`
- `docker-compose.yml:7,21` set `LOCAL_AI_URL=${LOCAL_AI_URL:-http://llm-router:8000}` (deployed default also dead) — but compose is an AGENTS.md anti-goal; fix the code defaults and flag the compose in your report.
- `gateway/adapters/mattermost/config.py:55` → `tayne_webhook_token: str = Field(default="")`.

## Commands you will need

| Purpose | Command | Expected |
|---------|---------|----------|
| Lint | `ruff check .` | exit 0 |
| Tests | `pytest` | pass |
| Grep dead URLs | `grep -rn "llm-router:8000\|local-ai-router:8000" gateway core` | no matches after fix |
| Webhook probe | with `TAYNE_WEBHOOK_TOKEN` unset, `curl -s -o /dev/null -w '%{http_code}' -X POST localhost:8023/webhook/mattermost/tayne` | `503` after fix |

## Scope

**In scope**:
- `gateway/main.py` (CORS block)
- `gateway/config.py` (default URL + a `cors_origins` setting)
- `core/config.py` (default URL)
- `gateway/adapters/mattermost/webhooks.py` (fail-closed)
- Tests under `tests/`
- `.env.example` files (document `CORS_ORIGINS`, confirm `LOCAL_AI_URL`)

**Out of scope**:
- `docker-compose.yml` (AGENTS.md anti-goal — report the needed env change: `LOCAL_AI_URL=http://ai-gateway:8000`, `LOCAL_AI_API_KEY=<lai-* key>`, `CORS_ORIGINS`, `TAYNE_WEBHOOK_TOKEN`)
- Endpoint API-key auth (plan 001)
- `core/agents/tayne/persona.py` (anti-goal)

## Git workflow

- Branch: `advisor/003-cors-webhook-backend`
- Commits per fix, conventional style
- Do NOT push/tag; do NOT build images (CI does it on merge).

## Steps

### Step 1: Env-driven CORS allowlist
Add `cors_origins: str = Field(default="")` to `gateway/config.py` (comma-separated). In `gateway/main.py`, parse it into a list; if empty, default to the known internal/UI origins (determine them — there may be none, in which case an empty allowlist is correct and `allow_credentials` can stay). Never `["*"]` with credentials.

**Verify**: `ruff check .` clean; a test asserts a disallowed `Origin` gets no `access-control-allow-origin` header.

### Step 2: Fail-closed webhook
Change `webhooks.py:44` so an unset token refuses service:

```python
if not settings.tayne_webhook_token:
    logger.error("TAYNE_WEBHOOK_TOKEN not configured; refusing webhook")
    raise HTTPException(status_code=503, detail="webhook not configured")
if token != settings.tayne_webhook_token:
    raise HTTPException(status_code=401, detail="Invalid webhook token")
```

**Verify**: webhook probe → 503 with token unset; 401 with wrong token; passes with correct token (existing behavior).

### Step 3: Repoint dead backend defaults
`gateway/config.py:17` and `core/config.py:8` → default `http://ai-gateway:8000`.

**Verify**: `grep -rn "llm-router:8000\|local-ai-router:8000" gateway core` → no matches.

### Step 4: Docs
Add `CORS_ORIGINS` and confirm `LOCAL_AI_URL`/`LOCAL_AI_API_KEY` in the three `.env.example` files.

**Verify**: `grep -rn "CORS_ORIGINS\|LOCAL_AI_URL" *.env.example core/.env.example gateway/.env.example`.

## Test plan

- Tests under `tests/gateway/` (follow existing structure):
  1. webhook 503 when token unset, 401 when wrong
  2. CORS: disallowed origin → no ACAO header
- Verification: `pytest` → all pass with new tests.

## Done criteria

- [ ] `grep -rn 'allow_origins=\["\*"\]' gateway` → no match
- [ ] `grep -rn "llm-router:8000\|local-ai-router:8000" gateway core` → no match
- [ ] webhook probe returns 503 when `TAYNE_WEBHOOK_TOKEN` unset
- [ ] `ruff check .` and `pytest` exit 0
- [ ] Report lists required deployed-compose env changes
- [ ] `plans/README.md` row updated

## STOP conditions

- Excerpts at `bae8f73` don't match (drift).
- You can't determine any legitimate CORS origin and are unsure whether the SPA/UI calls the gateway from a browser — report; an empty allowlist that breaks a real UI is worse than the status quo.

## Maintenance notes

- If the persona-gateway rebuild (plan 002) lands first, fold these three fixes into its baseline rather than doing them twice.
- Deployed default in `docker-compose.yml` still says `llm-router` — the code default is a safety net; the real fix is the deployed env (report it).
