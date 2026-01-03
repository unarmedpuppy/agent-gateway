# Agent Core

Platform-agnostic AI agent service. Hosts multiple AI personas (Tayne, Sentinel, Analyst) that can be accessed by Discord, Mattermost, Telegram, or any HTTP client.

## Access

- **Internal URL**: http://agent-core:8000 (Docker network)
- **External URL**: https://agent-core.server.unarmedpuppy.com
- **Local Port**: 8022
- **Status**: Active

## Quick Start

```bash
# Copy environment file
cp .env.example .env

# Start the service
docker compose up -d

# Test health
curl http://localhost:8022/health

# List agents
curl http://localhost:8022/v1/agents

# Chat with Tayne
curl -X POST http://localhost:8022/v1/agent/tayne/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello Tayne!",
    "user": {
      "platform": "curl",
      "platform_user_id": "test-user",
      "display_name": "Test User"
    }
  }'
```

## API Endpoints

### GET /v1/health
Detailed health check including Local AI Router connectivity.

### GET /v1/agents
List all available agents.

```json
{
  "agents": [
    {"id": "tayne", "name": "Tayne", "description": "Helpful assistant with dry humor"}
  ]
}
```

### POST /v1/agent/{agent_id}/chat
Chat with a specific agent.

**Request:**
```json
{
  "message": "What's the server status?",
  "user": {
    "platform": "discord",
    "platform_user_id": "123456789",
    "display_name": "Josh"
  },
  "conversation_id": "discord-channel-456",
  "context": {
    "channel_name": "general",
    "history": []
  }
}
```

**Response:**
```json
{
  "response": "All 12 containers running. Disk at 67%. ...Hat wobble nominal.",
  "agent": "tayne",
  "conversation_id": "discord-channel-456",
  "tools_used": []
}
```

## Agents

| Agent | Description | Persona |
|-------|-------------|---------|
| **tayne** | General assistant | Helpful first, dry humor second. Competent with subtle absurdist flair. |

## Architecture

```
Platform Adapters          Agent Core              LLM Backend
┌─────────────────┐       ┌──────────────┐       ┌─────────────────┐
│ Discord Bot     │──────▶│              │──────▶│ Local AI Router │
├─────────────────┤       │   Agents:    │       └─────────────────┘
│ Mattermost GW   │──────▶│   - Tayne    │
├─────────────────┤       │   - Sentinel │
│ Telegram Bot    │──────▶│   - Analyst  │
└─────────────────┘       └──────────────┘
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LOCAL_AI_URL` | `http://local-ai-router:8000` | Local AI Router URL |
| `LOCAL_AI_API_KEY` | (empty) | API key for Local AI Router |
| `LOG_LEVEL` | `INFO` | Logging level |

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn main:app --reload --port 8022

# Run tests
pytest
```

## Related

- [Agent Core Architecture Plan](../../agents/plans/agent-core-architecture.md)
- [Discord Reaction Bot](../discord-reaction-bot/) - Discord adapter
- [Mattermost Gateway](../mattermost-gateway/) - Mattermost adapter
- [Local AI Router](../local-ai-router/) - LLM backend
