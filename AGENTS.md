# Agent Gateway - Agent Instructions

## Project Summary

Platform-agnostic AI agent system with unified adapters for Discord, Mattermost, and more.

**Structure:**
- `core/` - Agent Core service (personas, tools, auth)
- `gateway/` - Unified Gateway service (platform adapters)
- `agents/` - Agent documentation and skills

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

### Never Do
- Commit secrets or tokens
- Build and push Docker images manually
- Modify home-server deployment directly (use git)
