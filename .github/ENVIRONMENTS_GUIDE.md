# GitHub Environments Configuration Guide

This guide explains how to configure GitHub Environments for the deployment workflow.

## Overview

The project uses three environments:

- **dev** - Development environment (auto-deploys from `develop` branch)
- **qa** - QA/Staging environment (auto-deploys from `staging` branch)
- **prod** - Production environment (auto-deploys from `main` branch with approval)

## Setting Up Environments

### 1. Create Environments in GitHub

1. Go to your repository on GitHub
2. Click **Settings** → **Environments**
3. Click **New environment** for each: `dev`, `qa`, `prod`

### 2. Configure Environment Protection Rules

#### DEV Environment

- ✅ No protection rules needed (fast iteration)
- Environment URL: `https://dev.your-domain.com`

#### QA Environment

- ✅ **Wait timer**: 2 minutes (optional - allows CI to complete)
- Environment URL: `https://qa.your-domain.com`

#### PROD Environment

- ✅ **Required reviewers**: Add team members who must approve deployments
- ✅ **Wait timer**: 5 minutes (optional - cooling period)
- ✅ **Deployment branches**: Restrict to `main` branch only
- Environment URL: `https://your-domain.com`

### 3. Add Environment Secrets

Navigate to each environment and add these secrets:

#### Common Secrets (all environments)

```
DOCKER_REGISTRY_URL=ghcr.io
DOCKER_USERNAME=your-github-username
```

#### DEV Environment Secrets

```
SSH_HOST=dev-server.example.com
SSH_USER=deploy-user
SSH_KEY=<your-ssh-private-key>
DATABASE_URL=<dev-database-url>
API_KEY=<dev-api-key>
```

#### QA Environment Secrets

```
SSH_HOST=qa-server.example.com
SSH_USER=deploy-user
SSH_KEY=<your-ssh-private-key>
DATABASE_URL=<qa-database-url>
API_KEY=<qa-api-key>
```

#### PROD Environment Secrets

```
SSH_HOST=prod-server.example.com
SSH_USER=deploy-user
SSH_KEY=<your-ssh-private-key>
DATABASE_URL=<prod-database-url>
API_KEY=<prod-api-key>
MONITORING_WEBHOOK=<your-monitoring-url>
```

## Deployment Flow

### Automatic Deployments

```
develop branch push  → Build Images → Deploy to DEV
   ↓
staging branch push  → Build Images → Deploy to QA
   ↓
main branch push     → Build Images → Wait for Approval → Deploy to PROD
```

### Manual Deployments

1. Go to **Actions** → **Deploy** workflow
2. Click **Run workflow**
3. Select the environment (dev/qa/prod)
4. Click **Run workflow**

## Branch Strategy

```
feature/xxx  →  develop  →  staging  →  main
                   ↓          ↓         ↓
                  DEV        QA       PROD
```

### Recommended Workflow

1. **Development**:
   - Create feature branch from `develop`
   - Make changes and test locally
   - Create PR to `develop`
   - After approval → Auto-deploy to DEV

2. **QA Testing**:
   - Create PR from `develop` to `staging`
   - QA team tests in DEV first
   - After approval → Auto-deploy to QA
   - QA team performs full testing

3. **Production Release**:
   - Create PR from `staging` to `main`
   - Add release notes to PR
   - After approval → Triggers PROD deployment
   - Requires manual approval in GitHub
   - Stakeholders notified

## Environment Variables in Workflows

Access environment secrets in your workflow steps:

```yaml
- name: Deploy to server
  run: |
    echo "${{ secrets.SSH_KEY }}" > private_key
    chmod 600 private_key
    ssh -i private_key ${{ secrets.SSH_USER }}@${{ secrets.SSH_HOST }} \
      "cd /app && docker-compose pull && docker-compose up -d"
  env:
    DATABASE_URL: ${{ secrets.DATABASE_URL }}
    API_KEY: ${{ secrets.API_KEY }}
```

## Customizing Deployment Commands

### Example: AWS ECS Deployment

```yaml
- name: Deploy to AWS ECS
  env:
    AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
    AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
  run: |
    aws ecs update-service \
      --cluster stock-portfolio-${{ inputs.environment }} \
      --service backend \
      --force-new-deployment
```

### Example: Kubernetes Deployment

```yaml
- name: Deploy to Kubernetes
  run: |
    kubectl set image deployment/backend \
      backend=ghcr.io/${{ github.repository }}/backend:${{ needs.build-images.outputs.image-tag }} \
      -n ${{ inputs.environment }}
```

### Example: Docker Compose on VM

```yaml
- name: Deploy via Docker Compose
  run: |
    ssh ${{ secrets.SSH_USER }}@${{ secrets.SSH_HOST }} << 'EOF'
      cd /app
      export IMAGE_TAG=${{ needs.build-images.outputs.image-tag }}
      docker-compose pull
      docker-compose up -d
    EOF
```

## Monitoring and Notifications

Add monitoring and notification steps to your deployment jobs:

### Slack Notification

```yaml
- name: Notify Slack
  if: always()
  uses: slackapi/slack-github-action@v1
  with:
    payload: |
      {
        "text": "Deployment to ${{ inputs.environment }}: ${{ job.status }}",
        "blocks": [
          {
            "type": "section",
            "text": {
              "type": "mrkdwn",
              "text": "Deployment Status: *${{ job.status }}*"
            }
          }
        ]
      }
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

### Discord/Teams/Email

Similar patterns apply - use their respective GitHub Actions or webhook integrations.

## Rollback Procedure

### Automatic Rollback (on failure)

Add to deployment steps:

```yaml
- name: Rollback on failure
  if: failure()
  run: |
    echo "Deployment failed, rolling back..."
    docker-compose down
    docker-compose up -d --use-previous-image
```

### Manual Rollback

1. Go to **Actions** → **Deploy** workflow
2. Click **Run workflow**
3. Select the environment
4. The rollback job will restore the previous version

## Best Practices

✅ **Always test in DEV first** before promoting to QA
✅ **Use staging/QA for final validation** before PROD
✅ **Require approvals for PROD** deployments
✅ **Tag production releases** for easy rollback
✅ **Monitor deployments** with health checks
✅ **Notify teams** of deployment status
✅ **Keep secrets up to date** and rotate regularly
✅ **Document deployment procedures** for your team

## Troubleshooting

### Deployment Stuck on "Waiting for approval"

- Check if required reviewers are set up correctly
- Ensure reviewers have been notified
- Check the Environments settings in GitHub

### SSH Connection Fails

- Verify SSH_KEY secret is correct
- Check SSH_HOST and SSH_USER values
- Ensure server allows connections from GitHub IPs

### Docker Image Pull Fails

- Verify GITHUB_TOKEN has package read permissions
- Check image tags are correct
- Ensure images were built successfully

### Health Check Fails

- Verify the application is running
- Check environment variables are set correctly
- Review application logs for errors
