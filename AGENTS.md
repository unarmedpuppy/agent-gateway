# Agent Gateway - Agent Instructions

## Project Summary

Platform-agnostic AI agent system with unified adapters for Discord, Mattermost, and more.

## Structure

```
agent-gateway/
├── core/                    # Agent Core service (port 8022)
│   ├── agents/              # AI personas (Tayne, etc.)
│   │   └── tayne/           # Tayne persona definition
│   ├── auth/                # Role-based access control
│   ├── routes/              # FastAPI routes (chat, health, tools)
│   └── tools/               # Server control tools
│       ├── control/         # Write operations (restart, backup)
│       ├── media/           # Plex, Sonarr, Radarr
│       └── read_only/       # Status checks, logs, disk usage
├── gateway/                 # Unified Gateway service (port 8023)
│   ├── adapters/            # Platform adapters
│   │   ├── discord/         # Discord bot adapter
│   │   ├── mattermost/      # Mattermost webhooks + API
│   │   └── telegram/        # (future)
│   ├── api/                 # FastAPI routes (health, send)
│   └── shared/              # Guardrails, rate limiting, persona
└── agents/                  # Agent documentation and skills
    └── plans/               # Architecture plans
```

## Quick Commands

```bash
# Build and run locally
docker compose up -d

# Test services
curl http://localhost:8022/health  # agent-core
curl http://localhost:8023/health  # agent-gateway

# View logs
docker logs agent-core
docker logs agent-gateway

# Run tests
pytest

# Run linter
ruff check .

# Format code
ruff format .
```

## Architecture

**Two services:**
1. **agent-core** - AI logic, personas, tools (port 8022)
2. **agent-gateway** - Platform adapters, webhooks (port 8023)

**Flow:**
```
Platform → Gateway → Core → LLM Router → Response → Gateway → Platform
```

## Development

- CI/CD pushes to Harbor on merge to main
- home-server pulls images from Harbor
- Never build manually - push to GitHub

## Boundaries

### Always Do
- Update both services when changing shared interfaces
- Test locally with docker-compose before pushing
- Update .env.example when adding new env vars
- Run `ruff check .` before committing
- Add tests for new tools and routes
- Follow existing patterns in the codebase (see similar files)

### Never Do
- Commit secrets or tokens
- Build and push Docker images manually
- Modify home-server deployment directly (use git)
- Add new dependencies without justification
- Suppress type errors or linter warnings
- Skip tests for new functionality

## Anti-Goals (Code Not to Touch)

Unless explicitly requested, do NOT modify:
- `core/agents/tayne/persona.py` - Tayne's personality is intentionally crafted
- `.github/workflows/` - CI/CD pipeline is stable
- `docker-compose.yml` - Production deployment config
- Any `.env` files - Contains secrets (use .env.example for templates)

## Definition of Done

A task is complete when:
- [ ] Code follows existing patterns in the codebase
- [ ] `ruff check .` passes with no errors
- [ ] `pytest` passes (or new tests added for new code)
- [ ] `docker compose up -d` builds and runs successfully
- [ ] Health endpoints respond: `curl localhost:8022/health && curl localhost:8023/health`
- [ ] .env.example updated if new env vars added
- [ ] No secrets committed
