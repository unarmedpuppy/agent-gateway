# Plan 002: Persona-gateway rebuild — design/spike

> **Executor instructions**: This is a **design/spike plan**, not a build-everything
> plan. Its deliverable is a written design + a small proof-of-concept, not a
> production rewrite. Follow the steps, answer the open questions with evidence
> from this repo and the linked audits, and produce the design doc. On any STOP
> condition, stop and report. Update this plan's row in `plans/README.md` when done.
>
> **Drift check (run first)**: `git diff --stat bae8f73..HEAD` — this repo is DORMANT;
> any new commits mean someone else started the rebuild — STOP and reconcile.

## Status

- **Priority**: P2
- **Effort**: L (spike-scoped: days of design + PoC, not the full build)
- **Risk**: LOW (design work; no production change until the design is accepted)
- **Depends on**: plan 001 (its auth/identity fixes are inputs — carry them as requirements)
- **Category**: direction
- **Planned at**: commit `bae8f73`, 2026-07-07

## Why this matters

ECOSYSTEM-AUDIT-2026-07-02 §4 designates agent-gateway as the base for the **persona-gateway** (Avery/Iris) — "the one net-new build in the whole plan", currently 0% built. The audit's stated shape (§2.2, §7 disposition table, remediation tracker §143): rebrand → `persona-gateway`, **personas become config** (not hardcoded like `core/agents/tayne/persona.py`), the backend repoints from the dead LLM router to **Oak's harness API**, and the rebuild kills the `agent-gateway`/`ai-gateway` name collision. This spike turns that one-paragraph intent into an executable design so the actual build is a follow-up of concrete plans.

## Current state — what exists to build on

- **Adapter pattern** (salvageable, keep): `gateway/adapters/base.py` + `discord/` + `mattermost/` with a registry (`gateway/adapters/__init__.py`), unified `/send`/`/react` outbound API (`gateway/api/send.py`), and Mattermost outgoing-webhook intake (`gateway/adapters/mattermost/webhooks.py`). This multi-platform seam is the reusable core.
- **Persona-as-code** (must become config): `core/agents/tayne/persona.py` and the fallback `gateway/shared/persona.py` hardcode Tayne's prompt/personality. The rebuild's central refactor is persona → config file (one per persona: Avery, Iris, …), loaded at startup.
- **Role/tool system** (keep, but re-anchor identity — see plan 001): `core/auth/` + `core/tools/` (read_only / control / media). Sound design; identity trust boundary is broken (plan 001).
- **Dead backends** (must repoint): `gateway/config.py:17` and `core/config.py:8` default to `http://llm-router:8000` / `http://local-ai-router:8000` — both 404 post-cutover (ECOSYSTEM §2.2). The rebuild points at ai-gateway for LLM and, per the audit, **Oak's agent-harness API** for agent execution.
- **Persona seed material lives in another repo**: Avery's identity files are in `openclaw-config/workspace/` (`AGENTS.md`, `IDENTITY.md`, `SOUL.md`, `MEMORY.md`, `BOOT.md`, `HEARTBEAT.md`) — see `openclaw-config/plans/DISPOSITION.md`. Extract these as the Avery persona config's source of truth. Iris has no in-repo definition found — an open question.
- **Tests**: 5 files under `tests/` — thin. The rebuild should raise this.

## Open questions the spike must answer (with evidence)

1. **Persona config schema.** What fields? (system prompt, model, temperature/max_tokens — currently on the agent object in `core/agents/base.py`; fallback/guardrail hooks — `gateway/shared/guardrails.py`; per-persona bot token + channels.) Propose a YAML/TOML schema and show Tayne + Avery expressed in it.
2. **Backend split.** Which calls go to **ai-gateway** (LLM completions, `/v1/chat/completions`, `lai-*` key) vs **Oak's harness API** (agent execution with memory/tools)? The current code does LLM-with-tools inline in `core/routes/chat.py:65-144`. Does persona-gateway keep inline tool-calling against ai-gateway, or delegate whole turns to Oak? Get the harness API surface from `agent-harness`/`agent-context` before deciding.
3. **Verified identity handoff** (from plan 001). How does a persona know the *real* platform user so ADMIN tools are safe? Design the adapter→core identity contract (signed/trusted, not body-asserted).
4. **Name collision resolution.** New repo/service/container/domain names; how the `agent-gateway`↔`ai-gateway` confusion is retired (ECOSYSTEM §4).
5. **Iris.** Is there any existing definition of the Iris persona anywhere in the fleet, or is it net-new? (Search `agent-context`, `agent-memory`, wiki.)
6. **Migration path.** Rebuild in place (rename this repo) vs new repo + archive this one? The audit's §7 table says KEEP→rename; confirm nothing else imports `agent-gateway` package paths.

## Commands you will need

| Purpose | Command | Expected |
|---------|---------|----------|
| Lint (PoC) | `ruff check .` | exit 0 |
| Tests | `pytest` | pass |
| Adapter inventory | `ls gateway/adapters/*/` | discord, mattermost |
| Find package-path importers | `grep -rn "agent-gateway\|from gateway\|from core" ../ --include=*.py --include=*.yml -l` | list to check for external coupling |

## Scope

**In scope** (spike deliverables):
- A design doc at `plans/design-persona-gateway.md` answering all six open questions
- A **proof-of-concept persona config loader**: a schema file + loader that renders Tayne from config (behind a flag, not replacing the hardcoded path) — enough to prove the config approach
- One example persona config for **Avery**, seeded from `openclaw-config/workspace/` content
- A follow-up plan list (what the real build's numbered plans should be)

**Out of scope**:
- Actually deleting `core/agents/tayne/persona.py` or ripping out hardcoded personas
- Renaming the repo/containers (that's an owner-executed migration once the design is accepted)
- Building Iris (unknown until Q5 is answered)
- Any production deploy

## Git workflow

- Branch: `advisor/002-persona-gateway-spike`
- Commits: `docs: persona-gateway rebuild design`, `feat(spike): PoC persona config loader (flagged)`
- Do NOT push/tag; do NOT build images.

## Steps

### Step 1: Inventory & coupling check
Run the importer grep; confirm whether any live repo imports this one's package paths (affects Q6). Read `agent-harness`/`agent-context` for Oak's API surface (Q2).

**Verify**: coupling findings + Oak API notes recorded in the design doc.

### Step 2: Draft the persona config schema (Q1) and express Tayne + Avery
Pull Avery's traits from `openclaw-config/workspace/IDENTITY.md`/`SOUL.md` (read-only; that repo has tracked secrets — do NOT copy any token, only persona prose).

**Verify**: two persona config files exist in the PoC; schema documented.

### Step 3: PoC loader
Implement a config loader that produces the same runtime persona object the code uses today, gated behind an env flag so nothing changes by default.

**Verify**: `pytest` includes a test loading Tayne-from-config and asserting the system prompt matches the current hardcoded one; `ruff check .` clean.

### Step 4: Answer Q2–Q6 in the design doc; enumerate the real build plans

**Verify**: `plans/design-persona-gateway.md` addresses all six questions with evidence and lists the follow-up build plans.

## Test plan

- One PoC test: config-loaded Tayne persona == current hardcoded persona (regression guard for the eventual cutover).
- No broad suite here — the spike's product is the design + PoC.

## Done criteria

- [ ] `plans/design-persona-gateway.md` answers Q1–Q6 with repo evidence
- [ ] PoC persona-config loader exists behind a flag; `pytest`/`ruff` green
- [ ] Avery persona config drafted from openclaw-config salvage (no secrets copied)
- [ ] Follow-up build plans enumerated
- [ ] `plans/README.md` row updated

## STOP conditions

- New commits on this DORMANT repo (someone else started) — reconcile first.
- Oak's harness API can't be located/understood from `agent-harness`/`agent-context` — report; Q2 blocks the design.
- The rebuild scope balloons — resist; this plan's job is the design, not the build.

## Maintenance notes

- Carry plan 001's auth + verified-identity properties into the design as hard requirements; port its tests forward.
- The `openclaw-config` and `server-agent-config` DISPOSITION plans both point salvage (personas, agent-safety posture) at this rebuild — cross-reference them.
