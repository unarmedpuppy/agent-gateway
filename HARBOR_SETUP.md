# Harbor CI/CD Setup

## Required GitHub Secrets

Configure these secrets in GitHub repository settings for the agent-gateway repo:

### Required Secrets

1. **HARBOR_REGISTRY**
   - Value: `harbor.server.unarmedpuppy.com`
   - Description: Harbor registry URL

2. **HARBOR_USERNAME**
   - Value: Your Harbor username (typically `admin` or service account)
   - Description: Harbor registry username

3. **HARBOR_PASSWORD**
   - Value: Your Harbor password or API token
   - Description: Harbor registry password/token

### How to Configure

1. Go to: https://github.com/unarmedpuppy/agent-gateway/settings/secrets/actions
2. Click "New repository secret"
3. Add each secret listed above

### Harbor Account Details

- **URL**: https://harbor.server.unarmedpuppy.com
- **Project**: `library` (for custom images)
- **Default Admin**: `admin` / `Harbor12345` (change password immediately)

### CI/CD Workflow

The `.github/workflows/build-and-push.yml` workflow will:
1. Build Docker images for `agent-core` and `agent-gateway` services
2. Tag them with `harbor.server.unarmedpuppy.com/library/agent-core:latest` and `harbor.server.unarmedpuppy.com/library/agent-gateway:latest`
3. Push to Harbor registry using the configured secrets

### Next Steps

1. Configure the GitHub secrets listed above
2. Push any changes to trigger the CI/CD workflow
3. Verify images appear in Harbor UI: https://harbor.server.unarmedpuppy.com/harbor/projects
4. Update home-server to use Harbor images in `apps/agent-gateway/docker-compose.yml`

### Testing

After CI/CD completes, test pulling images:
```bash
docker pull harbor.server.unarmedpuppy.com/library/agent-core:latest
docker pull harbor.server.unarmedpuppy.com/library/agent-gateway:latest
```