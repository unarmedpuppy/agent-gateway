# GitHub Actions Auto-Deploy Setup

This guide explains how to set up automatic deployment to your server via GitHub Actions on tag push.

## Overview

When you push a tag like `v1.0.0`, the workflow will:
1. Build and push Docker images to Harbor
2. SSH into the server
3. Pull latest changes and restart containers

## Required Secrets

Configure these in your repo: **Settings → Secrets and variables → Actions**

| Secret | Value | Description |
|--------|-------|-------------|
| `HARBOR_REGISTRY` | `harbor.server.unarmedpuppy.com` | Harbor registry URL |
| `HARBOR_USERNAME` | Your Harbor username | Registry auth |
| `HARBOR_PASSWORD` | Your Harbor password | Registry auth |
| `DEPLOY_HOST` | `192.168.86.47` | Server IP address |
| `DEPLOY_PORT` | `4242` | SSH port |
| `DEPLOY_USER` | `github-deploy` | SSH username |
| `DEPLOY_SSH_KEY` | (see below) | Private SSH key |

## SSH Key Setup (One-Time)

### 1. Generate Deployment Key

On your local machine:
```bash
# Generate a dedicated deploy key (no passphrase for CI/CD)
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github-deploy-key -N ""

# View the private key (add this to GitHub Secrets as DEPLOY_SSH_KEY)
cat ~/.ssh/github-deploy-key

# View the public key (add this to server)
cat ~/.ssh/github-deploy-key.pub
```

### 2. Create Deploy User on Server

```bash
ssh -p 4242 unarmedpuppy@192.168.86.47

# Create github-deploy user
sudo useradd -m -s /bin/bash github-deploy

# Set up SSH directory
sudo mkdir -p /home/github-deploy/.ssh
sudo chmod 700 /home/github-deploy/.ssh

# Add the public key (paste your github-deploy-key.pub content)
echo 'ssh-ed25519 AAAA... github-actions-deploy' | sudo tee /home/github-deploy/.ssh/authorized_keys
sudo chmod 600 /home/github-deploy/.ssh/authorized_keys
sudo chown -R github-deploy:github-deploy /home/github-deploy/.ssh

# Unlock account for SSH key auth
sudo usermod -p '*' github-deploy
```

### 3. Configure Sudo Access

```bash
# Create sudoers file for github-deploy
sudo tee /etc/sudoers.d/github-deploy << 'EOF'
# GitHub Actions deploy user - restricted docker access

# Docker operations (read + restart)
github-deploy ALL=(ALL) NOPASSWD: /usr/bin/docker compose *
github-deploy ALL=(ALL) NOPASSWD: /usr/bin/docker pull *
github-deploy ALL=(ALL) NOPASSWD: /usr/bin/docker image prune -f

# Git operations
github-deploy ALL=(ALL) NOPASSWD: /usr/bin/git -C /home/unarmedpuppy/server *
EOF

# Validate syntax
sudo visudo -cf /etc/sudoers.d/github-deploy
```

### 4. Grant Access to Server Directory

```bash
# Add github-deploy to the same group as unarmedpuppy
sudo usermod -aG unarmedpuppy github-deploy

# Ensure server directory is group-readable
chmod -R g+rX /home/unarmedpuppy/server
```

### 5. Test SSH Connection

```bash
# From local machine
ssh -p 4242 -i ~/.ssh/github-deploy-key github-deploy@192.168.86.47 'whoami'
# Should output: github-deploy

# Test docker access
ssh -p 4242 -i ~/.ssh/github-deploy-key github-deploy@192.168.86.47 'sudo docker ps --format "{{.Names}}" | head -3'
```

### 6. Add Secrets to GitHub

1. Go to your repo → Settings → Secrets and variables → Actions
2. Add each secret:
   - `DEPLOY_HOST`: `192.168.86.47`
   - `DEPLOY_PORT`: `4242`
   - `DEPLOY_USER`: `github-deploy`
   - `DEPLOY_SSH_KEY`: Paste entire contents of `~/.ssh/github-deploy-key` (private key)

## Usage

### Deploy via Tag

```bash
# Create and push a tag to trigger deployment
git tag v1.0.0
git push origin v1.0.0
```

### Deploy via Manual Trigger

1. Go to Actions → "Build and Deploy"
2. Click "Run workflow"
3. Check "Deploy after build"
4. Click "Run workflow"

### Build Only (No Deploy)

Normal pushes to `main` only build images, no deployment.

## Workflow Behavior

| Trigger | Build | Deploy |
|---------|-------|--------|
| Push to main (with changes) | ✅ | ❌ |
| Push tag `v*` | ✅ | ✅ |
| Manual with deploy=true | ✅ | ✅ |
| Manual with deploy=false | ✅ | ❌ |

## Adapting for Other Repos

Copy the workflow and adjust:

1. **Change paths filter** for your services
2. **Update deploy script** with correct app path:
   ```yaml
   script: |
     cd ~/server
     git pull origin main
     cd apps/YOUR_APP_NAME  # <-- Change this
     sudo docker compose pull
     sudo docker compose up -d --remove-orphans
   ```

## Troubleshooting

### SSH Connection Failed
- Verify `DEPLOY_SSH_KEY` includes `-----BEGIN/END-----` lines
- Check server firewall allows port 4242
- Verify user is unlocked: `sudo passwd -S github-deploy`

### Permission Denied for Docker
- Ensure sudoers file is correct
- Run `sudo visudo -cf /etc/sudoers.d/github-deploy` to validate

### Git Pull Failed
- Check github-deploy has read access to server directory
- Verify user is in `unarmedpuppy` group

### Deploy Job Skipped
- Only runs on tags (`v*`) or manual trigger with deploy=true
- Check "if" conditions in workflow