# CI/CD Trigger Instructions

## Workflow Status: ✅ Ready

The `.github/workflows/build-and-push.yml` workflow is configured and ready to run.

## Manual Trigger Options

### Option 1: GitHub Web UI (Recommended)

1. **Navigate to Actions**:
   - Go to: https://github.com/unarmedpuppy/agent-gateway/actions
   - Click "Build and Push Docker Images" workflow

2. **Configure Secrets First** (if not done):
   - Go to: https://github.com/unarmedpuppy/agent-gateway/settings/secrets/actions
   - Add these secrets:
     ```
     HARBOR_REGISTRY = harbor.server.unarmedpuppy.com
     HARBOR_USERNAME = <your Harbor username>
     HARBOR_PASSWORD = <your Harbor password/token>
     ```

3. **Trigger Build**:
   - Click "Run workflow" button
   - Select branch: `main`
   - Click "Run workflow"

### Option 2: Push Trigger (After Secrets Configured)

The workflow automatically triggers on pushes to main that change:
- `core/**` files
- `gateway/**` files  
- `.github/workflows/build-and-push.yml`

To trigger via push:
```bash
cd ~/repos/personal/agent-gateway
git commit --allow-empty -m "trigger: build and push images"
git push origin main
```

## What the Workflow Does

1. **Detect Changes**: Only rebuild services that changed
2. **Build Agent Core**: Creates `harbor.server.unarmedpuppy.com/library/agent-core:latest`
3. **Build Agent Gateway**: Creates `harbor.server.unarmedpuppy.com/library/agent-gateway:latest`
4. **Push to Harbor**: Authenticates and pushes both images

## Expected Build Time: ~5-8 minutes

## Verification Steps

### 1. Check GitHub Actions
- Go to: https://github.com/unarmedpuppy/agent-gateway/actions
- Look for green checkmarks on both build jobs

### 2. Verify Harbor Images
- Go to: https://harbor.server.unarmedpuppy.com/harbor/projects/library/repository
- Look for:
  - `agent-core:latest`
  - `agent-gateway:latest`

### 3. Test Pull Images (Optional)
```bash
# On server or local machine with Harbor access
docker pull harbor.server.unarmedpuppy.com/library/agent-core:latest
docker pull harbor.server.unarmedpuppy.com/library/agent-gateway:latest
```

## Troubleshooting

### Build Failures
- Check the GitHub Actions logs for specific errors
- Verify Harbor secrets are correct
- Ensure Harbor is accessible

### Harbor Login Issues
- Verify Harbor URL: `harbor.server.unarmedpuppy.com`
- Check username/password in Harbor UI
- Test manual login: `docker login harbor.server.unarmedpuppy.com`

### No Workflow Trigger
- Ensure secrets are configured before triggering
- Check file paths match trigger conditions
- Use manual workflow dispatch if needed

## Next Steps After Build

Once images are successfully built:

1. **Deploy on Server**:
   ```bash
   ssh -p 4242 unarmedpuppy@192.168.86.47
   cd ~/server
   git pull
   cd apps/agent-gateway
   docker compose up -d
   ```

2. **Test Services**:
   - Agent Core: `http://localhost:8000/health`
   - Agent Gateway: `http://localhost:8001/health`

3. **Verify Discord/Mattermost**:
   - Send test messages
   - Check for responses via agent-core

## Workflow Dependencies

The workflow requires these secrets to be configured:
- `HARBOR_REGISTRY` ✅ (documented)
- `HARBOR_USERNAME` ⚠️ (needs configuration)
- `HARBOR_PASSWORD` ⚠️ (needs configuration)

**Status**: Ready to build once secrets are configured.