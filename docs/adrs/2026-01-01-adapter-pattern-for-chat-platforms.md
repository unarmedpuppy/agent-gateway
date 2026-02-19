# Adapter Pattern for Multi-Platform Chat

- **Date:** 2026-01-01
- **Status:** Accepted
- **Authors:** Joshua Jenquist
- **Impacted Repos/Services:** agent-gateway, Discord, Mattermost, Telegram integrations

## Context

AI agent personas (Tayne, Sentinel, Analyst) need to be accessible from multiple chat platforms. Each platform has different APIs, message formats, authentication, and event models. Without abstraction, adding a platform means duplicating all agent logic.

## Decision

Implement platform adapters that conform to a unified interface. Each adapter handles platform-specific concerns (auth, message parsing, delivery). The agent core (personas, tools, LLM routing) is platform-agnostic and composed by the gateway.

**Architecture:**
```
Platform → Adapter → Unified Interface → Agent Core → LLM Router
```

Middleware stack: Auth → Platform adapter → Unified interface → Agent core → Response.

## Options Considered

### Option A: Separate bot per platform
Simple per-bot. Duplicates agent logic. Changes to personas must be made in N places.

### Option B: Adapter pattern with unified core (selected)
One agent core, multiple platform adapters. Adding a platform is a single adapter implementation. Agent logic changes propagate to all platforms automatically.

## Consequences

### Positive
- Adding a platform is a single adapter file
- Agent persona changes apply everywhere instantly
- Agent core is testable without any platform dependency

### Negative
- Lowest common denominator — platform-specific features (reactions, threads, embeds) need adapter-level handling
- Adapter must translate between platform message format and unified format
