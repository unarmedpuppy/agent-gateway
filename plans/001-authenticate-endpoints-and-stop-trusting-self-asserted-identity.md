# Plan 001: Authenticate the gateway/core endpoints and stop trusting self-asserted identity

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving on.
> On any STOP condition, stop and report. When done, update this plan's row
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat bae8f73..HEAD -- gateway/api/ core/routes/ core/auth/ gateway/adapters/mattermost/webhooks.py`
> Mismatch with the excerpts below = STOP.

## Status

- **Priority**: P1 (highest-leverage security work in this repo)
- **Effort**: M
- **Risk**: MED — adding auth to endpoints breaks any current unauthenticated caller (n8n's `agent-gateway:8000/send`, Mattermost outgoing webhook); those callers must get the key/secret at the same time
- **Depends on**: none (but see the persona-gateway rebuild spike, plan 002 — these fixes are *requirements* that rebuild must carry, not throwaway work)
- **Category**: security
- **Planned at**: commit `bae8f73`, 2026-07-07

## Why this matters

agent-gateway is flagged in SECURITY-AUDIT-2026-07-02 §4.1 as a **public, unauthenticated** Traefik endpoint that holds Discord/Mattermost bot tokens and routes into agent-core, which has Docker control tools. Two concrete, independent exposures:

1. **`POST /send` and `POST /react` (gateway, port 8023) have no auth at all.** Any caller who can reach the service can send a message to any channel as any configured bot (`bot` and `channel` are free-form request fields — `gateway/api/send.py:20-26`). Impersonation of Tayne/Monitor/Trading bots and channel spam are one unauthenticated POST away.
2. **`POST /v1/agent/{id}/chat` (core, port 8022) resolves the caller's *role* from identity fields supplied in the request body.** `core/routes/chat.py:147-194` calls `resolve_user_role(platform=request.user.platform, platform_user_id=request.user.platform_user_id, …)`, and `core/auth/users.py:33-38` maps `discord:244649852473049088` → `ToolRole.ADMIN`. ADMIN unlocks `docker_compose_up`/`docker_compose_down`/`trigger_backup` (`core/tools/control/docker_compose.py:56-57,132-133`). Because the identity is **self-asserted in the JSON body**, any caller can claim to be Josh and obtain ADMIN tool access. The role system is sound; its trust boundary is not — it trusts the network peer to tell the truth about who they are.

The ecosystem audit plans to rebuild this repo into the **persona-gateway** for Avery/Iris (ECOSYSTEM §4). Whether the code is rebuilt or repointed, these two properties — authenticated service boundary, and identity that comes from a *verified* channel (webhook signature / platform user id proven by the adapter) rather than a client-supplied field — are non-negotiable requirements. Fixing them now also de-risks the rebuild by making the target behavior explicit.

## Current state

- `gateway/api/send.py:36-114` — `/send` and `/react` handlers, no auth dependency.
- `gateway/main.py` — mounts `send_router` and `mm_webhook_router`; CORS is `allow_origins=["*"]` + `allow_credentials=True` (`gateway/main.py:59-64`) — invalid/oversharing combo (browsers reject `*`+credentials, and it signals no origin discipline). (CORS is also addressed in plan 003.)
- `core/routes/chat.py:29-34` — `ChatRequest.user` is a client-supplied `UserInfo{platform, platform_user_id, display_name}`.
- `core/routes/chat.py:183-192` — role resolved from those fields; `enable_tools` (also client-supplied, default `True`) gates tool exposure.
- `core/auth/users.py:33-53` — `WHITELISTED_USERS` maps `discord:244649852473049088` → ADMIN; default role PUBLIC.
- `gateway/config.py:11-18` / `core/config.py:5-21` — both have `local_ai_api_key` (used as an *outbound* Bearer to the LLM backend, `core/routes/chat.py:99-100`); neither service requires an *inbound* key.
- `gateway/adapters/mattermost/webhooks.py:44` — webhook token check is fail-open: `if settings.tayne_webhook_token and token != settings.tayne_webhook_token:` → unset token skips the check (plan 003 also touches this; do the chat/send auth here, webhook hardening there, to keep commits reviewable — but note the overlap).

## Commands you will need

| Purpose | Command | Expected |
|---------|---------|----------|
| Lint | `ruff check .` | exit 0 |
| Tests | `pytest` | all pass (5 test files exist under `tests/`) |
| Local run | `docker compose up -d` then `curl -s localhost:8023/health` | healthy |
| Probe /send without key | `curl -s -o /dev/null -w '%{http_code}' -X POST localhost:8023/send -H 'content-type: application/json' -d '{"platform":"discord","bot":"tayne","channel":"x","message":"y"}'` | `401` after fix |

Install deps in a disposable venv you create (`python3 -m venv /tmp/agw && /tmp/agw/bin/pip install -e .`) if `pytest`/`ruff` aren't already available — do not install into system Python.

## Scope

**In scope**:
- `gateway/api/send.py` (add auth dependency to `/send`, `/react`)
- `gateway/config.py` (add inbound `gateway_api_key` setting)
- `core/routes/chat.py` (add auth dependency; stop trusting client-supplied role for privileged tools)
- `core/config.py` (add inbound `core_api_key` setting)
- `core/auth/middleware.py` (add the verified-identity plumbing if needed)
- New: `gateway/api/auth.py` and/or `core/routes/auth.py` — a `require_api_key` dependency (mirror `homelab-app-template`'s `app/auth.py` `X-API-Key`, opt-in: unset key → open for backward-compat during migration, set key → required)
- Tests under `tests/`
- `core/.env.example`, `gateway/.env.example`, `.env.example` (document new vars)

**Out of scope**:
- `core/agents/tayne/persona.py` (AGENTS.md anti-goal)
- `docker-compose.yml` (AGENTS.md anti-goal — but note in report: deployed compose must pass the new keys; and the Traefik-side ClientIP/forward-auth split lives in `home-server`, tracked in ECOSYSTEM §2.5.2)
- The persona-gateway rebuild itself (plan 002)
- CORS + webhook fail-open (plan 003) — except acknowledging the overlap

## Git workflow

- Branch: `advisor/001-authenticate-endpoints`
- Commits per logical unit, conventional style (repo uses `feat:`/`fix:`/`refactor:` — see `git log`)
- CI/CD pushes to Harbor on merge (AGENTS.md); do NOT build/push images manually, do NOT push/tag unless instructed.

## Steps

### Step 1: Add an `X-API-Key` dependency to each service
Create a `require_api_key` FastAPI dependency per service, reading the key from settings (`gateway_api_key` / `core_api_key`). Opt-in semantics per homelab convention: unset → dependency is a no-op (keeps migration non-breaking); set → header `X-API-Key` must match or 401. Model it on `homelab-app-template/CONVENTIONS.md` §2 and its `app/auth.py`.

**Verify**: `ruff check .` exits 0; unit test asserts 401 when key set and header missing/wrong, 200 when correct, open when unset.

### Step 2: Protect the mutating gateway endpoints
Add `dependencies=[Depends(require_api_key)]` to `/send` and `/react` in `gateway/api/send.py`. Leave `/health` and read-only `/adapters` open.

**Verify**: probe command above → 401 with key set; the n8n caller (report this) must send `X-API-Key`.

### Step 3: Protect core `/v1/agent/{id}/chat` AND fix the identity trust boundary
Two parts:
- (a) Add `require_api_key` to the chat route so only trusted internal callers (the gateway) reach it.
- (b) **Privileged-tool identity must not come from the request body.** The gateway is the only component that has *verified* who the platform user is (Discord SDK / signed Mattermost webhook). Change the contract so ADMIN/TRUSTED roles are only granted when the caller is the authenticated gateway AND the identity was established by the adapter — not by a raw client POST. Minimum viable: gate `enable_tools`/privileged roles behind the API key (an unauthenticated caller gets PUBLIC regardless of what `user.platform_user_id` claims); document that the gateway must only forward identities it verified. If a fuller signed-identity handoff is warranted, capture it as an open question for the persona-gateway spike (plan 002) rather than over-building here.

**Verify**: test — a chat request *without* the API key that claims `discord:244649852473049088` resolves to PUBLIC (no ADMIN tools offered); *with* the key, the mapped role applies. `pytest` green.

### Step 4: Document env vars
Add `GATEWAY_API_KEY` / `CORE_API_KEY` to the three `.env.example` files with a one-line comment (opt-in behavior).

**Verify**: `grep -rn "API_KEY" *.env.example core/.env.example gateway/.env.example` shows the new vars.

## Test plan

- New tests in `tests/gateway/` and `tests/core/` (follow the existing test files' structure — read them first):
  1. `/send` → 401 without key (key set), 200 with key
  2. chat route → PUBLIC role when unauthenticated even if body claims an ADMIN id
  3. chat route → mapped role when authenticated
  4. `require_api_key` no-op when key unset (backward-compat)
- Verification: `pytest` → all pass including the 4 new tests.

## Done criteria

- [ ] `ruff check .` exits 0
- [ ] `pytest` exits 0 with the new tests present
- [ ] `/send`, `/react`, `/v1/agent/{id}/chat` return 401 without the key (when configured)
- [ ] A body-supplied ADMIN identity does NOT grant ADMIN tools without authentication
- [ ] `grep -rn 'allow_origins=\["\*"\]' gateway core` — unchanged here (owned by plan 003); do not silently alter
- [ ] Report lists the callers that must start sending `X-API-Key` (n8n `/send`, gateway→core) and the deployed-compose env additions
- [ ] `plans/README.md` row updated

## STOP conditions

- Excerpts at `bae8f73` don't match (drift).
- You discover a caller of `/send` or `/chat` that cannot be given a key (e.g. a browser-origin call) — report; that changes the auth design.
- Fixing identity trust turns out to require the signed-handoff design — STOP, fold it into plan 002's spike rather than half-building it.

## Maintenance notes

- These two properties (authenticated boundary, verified-not-asserted identity) are hard requirements for the persona-gateway rebuild (plan 002). If the rebuild replaces this code, port the *tests* forward as executable spec.
- Reviewer: confirm no privileged tool is reachable on a path that skips `require_api_key`.
- The Traefik-level exposure (public router, `docker.sock` on agent-core) is tracked in ECOSYSTEM §2.5.2 / §4.2 and lives in `home-server` — app-level auth here is defense-in-depth, not a substitute.
