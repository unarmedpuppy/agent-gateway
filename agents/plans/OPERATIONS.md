# Agent Gateway Operations Reference

## Architecture

```
Discord/Mattermost → agent-gateway (8023) → agent-core (8022) → llm-router (homelab-ai)
```

**Two services, one compose file:**
- `agent-core` - AI agent logic, tools, personas (Tayne)
- `agent-gateway` - Platform adapters (Discord, Mattermost)

Both run from `home-server/apps/agent-gateway/docker-compose.yml` using Harbor images.

## Deployment

### Server Details
- Host: `192.168.86.47`
- Port: `4242`
- User: `unarmedpuppy`
- Path: `~/server/apps/agent-gateway/`

### Quick Deploy
```bash
# From local machine
ssh unarmedpuppy@192.168.86.47 -p 4242 "cd ~/server/apps/agent-gateway && docker compose pull && docker compose up -d"
```

### Manual Build & Push (bypassing CI/CD)
```bash
# Copy source to server
scp -P 4242 -r ~/repos/personal/agent-gateway/gateway/* unarmedpuppy@192.168.86.47:/tmp/gateway-build/

# Build and push on server
ssh unarmedpuppy@192.168.86.47 -p 4242 "cd /tmp/gateway-build && docker build -t harbor.server.unarmedpuppy.com/library/agent-gateway:latest . && docker push harbor.server.unarmedpuppy.com/library/agent-gateway:latest"

# Restart
ssh unarmedpuppy@192.168.86.47 -p 4242 "cd ~/server/apps/agent-gateway && docker compose pull && docker compose up -d"
```

## Configuration

### Required Environment Variables (server .env)

```bash
# /home/unarmedpuppy/server/apps/agent-gateway/.env

# LLM Router
LOCAL_AI_URL=http://llm-router:8000
LOCAL_AI_API_KEY=lai_xxxxx  # Generate from llm-router

# Discord
DISCORD_TOKEN=MTQ...  # Bot token from Discord Developer Portal

# Mattermost
MATTERMOST_URL=mattermost.server.unarmedpuppy.com
MATTERMOST_BOT_TAYNE_TOKEN=xxxxx
```

### Generate LLM Router API Key
```bash
docker exec llm-router python scripts/manage-api-keys.py create agent-core
```

### Discord Developer Portal Requirements
Enable these Privileged Gateway Intents:
- ✅ MESSAGE CONTENT INTENT (required for reading messages in servers)
- ✅ SERVER MEMBERS INTENT (optional)

## Troubleshooting

### Common Issues Fixed (Jan 2025)

| Issue | Symptom | Fix |
|-------|---------|-----|
| Relative imports | `ImportError: attempted relative import` | Dockerfile: `uvicorn gateway.main:app` (not `main:app`) |
| Missing export | `cannot import name 'RateLimitConfig'` | Add to `shared/__init__.py` exports |
| Form data | `requires "python-multipart"` | Add `python-multipart>=0.0.6` to requirements.txt |
| No channel messages | Bot works in DMs but not servers | Add `intents.guilds = True` and `intents.guild_messages = True` |

### Check Logs
```bash
ssh unarmedpuppy@192.168.86.47 -p 4242 "docker logs agent-gateway --tail 50"
ssh unarmedpuppy@192.168.86.47 -p 4242 "docker logs agent-core --tail 50"
```

### Health Checks
```bash
# Gateway health
curl http://localhost:8023/health

# Core health  
curl http://localhost:8022/health

# List agents
curl http://localhost:8022/v1/agents
```

## Repository Structure

### agent-gateway repo (source)
```
agent-gateway/
├── core/           # agent-core source → Harbor image
├── gateway/        # agent-gateway source → Harbor image
└── agents/plans/   # This documentation
```

### home-server repo (deployment)
```
home-server/apps/agent-gateway/
├── docker-compose.yml   # Both services, x-enabled: true
├── .env                 # Secrets (gitignored)
└── .env.example
```

**Note:** Previously had separate `agent-core/` and `mattermost-gateway/` directories - these were consolidated into `agent-gateway/` (Jan 2025).

## CI/CD

Push to `main` branch triggers GitHub Actions:
1. Builds Docker images
2. Pushes to Harbor (`harbor.server.unarmedpuppy.com/library/`)
3. Optionally deploys via SSH (on tags or manual trigger)

Images:
- `harbor.server.unarmedpuppy.com/library/agent-core:latest`
- `harbor.server.unarmedpuppy.com/library/agent-gateway:latest`
