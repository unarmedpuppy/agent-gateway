# Agent Gateway

Platform-agnostic AI agent system with unified adapters for Discord, Mattermost, and more.

## Architecture

```
                              ┌─────────────────────────────────────────────────┐
                              │              agent-gateway                       │
                              │                                                  │
   Discord ◄────────────────► │  adapters/discord/    (Discord SDK)             │
   Mattermost ◄──────────────► │  adapters/mattermost/ (MM API + webhooks)       │
   Telegram ◄────────────────► │  adapters/telegram/   (future)                  │
                              │                                                  │
                              │  POST /send     - Unified outbound messaging    │
                              │  GET  /health   - Adapter health status         │
                              │  POST /webhook/* - Platform webhooks            │
                              └───────────────────────────────────────────────────┘
                                                      │
                                                      ▼
                              ┌─────────────────────────────────────────────────┐
                              │              agent-core                          │
                              │                                                  │
                              │  agents/tayne/   - AI personas                  │
                              │  tools/          - Server control tools         │
                              │  auth/           - Role-based access            │
                              │                                                  │
                              │  POST /v1/agent/{id}/chat                       │
                              └───────────────────────────────────────────────────┘
                                                      │
                                                      ▼
                              ┌─────────────────────────────────────────────────┐
                              │           homelab-ai (llm-router)               │
                              │                                                  │
                              │  POST /v1/chat/completions                      │
                              └───────────────────────────────────────────────────┘
```

## Services

### agent-core

Platform-agnostic AI agent service. Hosts personas (Tayne, Sentinel, Analyst) with tool access.

**Endpoints:**
- `GET /health` - Health check
- `GET /v1/agents` - List agents
- `GET /v1/tools` - List tools
- `POST /v1/agent/{id}/chat` - Chat with agent

### agent-gateway

Unified platform adapter. Connects to Discord, Mattermost, etc.

**Endpoints:**
- `GET /health` - Adapter health
- `GET /adapters` - List adapters
- `POST /send` - Send message to any platform
- `POST /webhook/mattermost/tayne` - Mattermost webhook

## Quick Start

```bash
# Copy environment files
cp core/.env.example core/.env
cp gateway/.env.example gateway/.env

# Edit .env files with your tokens

# Start services
docker compose up -d

# Test
curl http://localhost:8022/health  # agent-core
curl http://localhost:8023/health  # agent-gateway
```

## Configuration

### Environment Variables

**agent-core:**
- `LOCAL_AI_URL` - LLM Router URL (default: `http://llm-router:8000`)
- `LOCAL_AI_API_KEY` - API key for LLM Router

**agent-gateway:**
- `DISCORD_TOKEN` - Discord bot token
- `MATTERMOST_BOT_TAYNE_TOKEN` - Mattermost Tayne bot token
- `AGENT_CORE_URL` - Agent Core URL (default: `http://agent-core:8000`)

## CI/CD

GitHub Actions builds and pushes to Harbor on merge to main:
- `harbor.server.unarmedpuppy.com/library/agent-core:latest`
- `harbor.server.unarmedpuppy.com/library/agent-gateway:latest`

**Required Secrets:**
- `HARBOR_REGISTRY` - Harbor URL
- `HARBOR_USERNAME` - Harbor username
- `HARBOR_PASSWORD` - Harbor password

## Development

```bash
# Install dependencies
cd core && pip install -r requirements.txt
cd gateway && pip install -r requirements.txt

# Run locally
cd core && uvicorn main:app --reload --port 8022
cd gateway && uvicorn main:app --reload --port 8023
```

## Related

- [homelab-ai](https://github.com/unarmedpuppy/homelab-ai) - LLM Router
- [home-server](https://github.com/unarmedpuppy/home-server) - Server deployment
