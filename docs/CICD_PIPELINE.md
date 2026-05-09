# CI/CD Pipeline & Multi-Arch Build Guide

This document explains the Jenkins pipeline and multi-architecture Docker build setup for the AI Log Analyzer project.

## Overview

The CI/CD pipeline is defined in the `Jenkinsfile` and performs the following:
1. **Checkout** - Clones the repository
2. **Build Services** - Builds Docker images using docker-compose
3. **Start Services** - Spins up all services (API, Worker, PostgreSQL)
4. **Health Checks & Tests** - Runs integration tests against the running services
5. **View Logs** - Captures service logs for debugging
6. **Cleanup** - Stops and removes containers
7. **Build Multi-Arch Images** - Builds for AMD64 and ARM64 architectures
8. **Push to Docker Hub** - Publishes images (optional)

## Prerequisites

### For Local Development
- Docker and Docker Compose installed
- Python 3.9+
- Git

### For Jenkins
- Jenkins instance running (configured as in jenkins.md)
- Docker daemon accessible from Jenkins container
- Docker Hub credentials configured in Jenkins

### For Multi-Architecture Builds
- Docker buildx installed and configured
- Docker Hub account with push access
- QEMU for cross-platform building (usually handled automatically by buildx)

## Pipeline Parameters

The Jenkins pipeline accepts the following parameters:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `DOCKER_REGISTRY` | `docker.io` | Docker registry URL |
| `DOCKER_USERNAME` | `paambust` | Docker Hub username |
| `IMAGE_TAG` | `latest` | Tag for built images |
| `PUSH_IMAGES` | `false` | Whether to push multi-arch images to Docker Hub |

## Usage

### Option 1: Run Pipeline with Default Settings (Local Testing Only)
1. Go to Jenkins UI
2. Click on your pipeline job (e.g., "ai-logs-analyzer")
3. Click **Build Now**
4. Pipeline will:
   - Clone your repo
   - Build local images
   - Run integration tests
   - Clean up containers
   - ✓ No images pushed to Docker Hub

### Option 2: Build, Test, and Push Multi-Arch Images
1. Go to Jenkins UI
2. Click on your pipeline job
3. Click **Build with Parameters**
4. Set parameters:
   - `DOCKER_USERNAME`: Your Docker Hub username
   - `IMAGE_TAG`: Version tag (e.g., `v1.0.0` or `latest`)
   - `PUSH_IMAGES`: **Check this box** ✓
5. Click **Build**
6. Pipeline will:
   - Build and test locally
   - Build multi-arch images (amd64 + arm64)
   - Push to Docker Hub
   - Display published image URLs

### Option 3: Manual Multi-Arch Build (Without Jenkins)

```bash
# 1. Install dependencies
pip install -r tests/requirements.txt

# 2. Set environment variables
export DOCKER_REGISTRY="docker.io"
export DOCKER_USERNAME="your-docker-username"
export IMAGE_TAG="v1.0.0"

# 3. Log in to Docker Hub
docker login

# 4. Run the build script
chmod +x build-multiarch.sh
./build-multiarch.sh
```

## Testing

### Local Integration Tests
The pipeline automatically runs integration tests in the `Health Checks & Tests` stage.

To run tests manually:

```bash
# 1. Start services
docker-compose up -d

# 2. Wait for services to be ready
sleep 10

# 3. Install test dependencies
pip install -r tests/requirements.txt

# 4. Run tests
python3 tests/test_api.py

# 5. Stop services
docker-compose down
```

### Test Coverage
The test suite verifies:
- ✓ API health endpoint responds
- ✓ Database connectivity
- ✓ Create log endpoint (POST /logs)
- ✓ Retrieve logs endpoint (GET /logs)
- ✓ Different log severity levels
- ✓ Multiple concurrent API calls

## Docker Images

### Published Images
After pushing multi-arch images, they are available at:
- **API**: `docker.io/your-username/ai-log-analyzer-api:tag`
- **Worker**: `docker.io/your-username/ai-log-analyzer-worker:tag`

### Supported Platforms
- `linux/amd64` (Intel/AMD processors)
- `linux/arm64` (ARM processors, Apple Silicon, Raspberry Pi, AWS Graviton)

### Pull Multi-Arch Images
```bash
# Pull the correct image for your platform automatically
docker pull docker.io/your-username/ai-log-analyzer-api:latest
docker pull docker.io/your-username/ai-log-analyzer-worker:latest
```

## GitHub Integration

### Webhook Setup
1. In Jenkins: Manage Jenkins → Configure System → GitHub
2. Add your GitHub credentials
3. In your GitHub repo: Settings → Webhooks → Add webhook
   - Payload URL: `http://your-jenkins-server:8080/github-webhook/`
   - Content type: `application/json`
   - Events: Push events

### Automatic Builds
After webhook setup, every push to your repo will:
1. Trigger the Jenkins pipeline automatically
2. Run tests
3. Report results back to GitHub (if configured)

## Troubleshooting

### Pipeline Fails at "Health Checks & Tests"
- Check if services started properly: `docker-compose ps`
- View service logs: `docker-compose logs api`
- Verify database is initialized and accessible
- Ensure port 8000 is not already in use

### Multi-Arch Build Fails
- Verify Docker buildx: `docker buildx version`
- Ensure QEMU is installed: Check Docker desktop settings
- Check Docker Hub login: `docker login`

### Services Won't Start
- Port conflicts: `sudo lsof -i :8000` (check port 8000)
- Docker socket permissions: `ls -la /var/run/docker.sock`
- Database connection: Check PostgreSQL container logs

## Environment Variables for Jenkins

Add these to Jenkins credentials or pipeline:

```groovy
environment {
    DOCKER_USERNAME = credentials('docker-username')
    DOCKER_PASSWORD = credentials('docker-password')
    DOCKER_REGISTRY = 'docker.io'
}
```

In Jenkins UI:
1. Manage Jenkins → Manage Credentials
2. Add credentials for Docker Hub username/password
3. Use in Jenkinsfile pipeline

## Performance Tips

1. **Enable Docker layer caching** for faster builds
2. **Use image registries** to cache base images locally
3. **Parallel testing** - Add more test stages for larger test suites
4. **Build only on push** - Configure pipeline triggers to avoid unnecessary builds

## Next Steps

1. ✓ Configure GitHub webhook for automatic builds
2. ✓ Add more integration tests for your specific use cases
3. ✓ Set up build status badges in GitHub README
4. ✓ Configure Jenkins email notifications for build failures
5. ✓ Add deployment stages for production environments

---

For more information, see the main [README.md](../README.md)
