# BEI Knowledge Hub - Deployment Guide

## Production Deployment to AWS Docker Swarm

### Prerequisites

- AWS CLI configured
- Docker Swarm cluster running
- GitHub Container Registry access
- Doppler CLI for secrets management

### Deployment Process

#### 1. Configure Secrets in Doppler

```bash
doppler setup --project bei-knowledge-hub --config prd

# Add required secrets
doppler secrets set GEMINI_API_KEY="your-key" --project bei-knowledge-hub --config prd
doppler secrets set SUPABASE_URL="https://xxx.supabase.co" --project bei-knowledge-hub --config prd
doppler secrets set SUPABASE_SERVICE_ROLE_KEY="your-key" --project bei-knowledge-hub --config prd
doppler secrets set KNOWLEDGE_HUB_API_KEY="your-api-key" --project bei-knowledge-hub --config prd
```

#### 2. Push to Main Branch

```bash
git push origin main
```

This triggers GitHub Actions which:
1. Runs tests
2. Builds Docker image
3. Pushes to ghcr.io
4. Deploys to AWS Swarm

#### 3. Manual Deployment (if needed)

```bash
# SSH to Swarm manager
aws ssm start-session --target i-xxxxx

# Deploy stack
docker stack deploy -c aws-swarm-stack.yml knowledge-hub

# Check status
docker service ps knowledge-hub_knowledge-hub

# View logs
docker service logs -f knowledge-hub_knowledge-hub
```

### Deployment Guards

The `.github/workflows/deploy.yml` includes safety checks:

- ✅ Verifies repository is `bei-knowledge-hub`
- ✅ Blocks deployment to BEI-ERP services
- ✅ Blocks deployment to bei-tasks
- ✅ Only deploys `knowledge-hub` service

### Rollback Procedure

```bash
# Get previous image
docker service inspect knowledge-hub_knowledge-hub --format='{{.PreviousSpec.TaskTemplate.ContainerSpec.Image}}'

# Rollback
docker service update --image <previous-image> knowledge-hub_knowledge-hub

# Or use built-in rollback
docker service rollback knowledge-hub_knowledge-hub
```

### Health Checks

- **Endpoint:** `GET /health`
- **Expected:** `{"status": "healthy"}`
- **Interval:** 30s
- **Timeout:** 10s

### Monitoring

- **Logs:** `docker service logs knowledge-hub_knowledge-hub`
- **Metrics:** `GET /metrics` (Prometheus format)
- **Status:** `docker service ps knowledge-hub_knowledge-hub`

### Scaling

```bash
# Scale to 4 replicas
docker service scale knowledge-hub_knowledge-hub=4

# Scale down
docker service scale knowledge-hub_knowledge-hub=2
```

### Troubleshooting

**Service won't start:**
```bash
# Check service status
docker service ps knowledge-hub_knowledge-hub --no-trunc

# View logs
docker service logs --tail=100 knowledge-hub_knowledge-hub

# Check secrets
doppler secrets --project bei-knowledge-hub --config prd
```

**Database connection issues:**
- Verify Supabase credentials in Doppler
- Check network connectivity from Swarm to Supabase

**Image pull failures:**
- Verify GitHub Container Registry access
- Check image tag exists: `ghcr.io/bebang-enterprise-inc/bei-knowledge-hub:latest`
