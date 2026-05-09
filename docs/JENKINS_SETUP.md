# Jenkins Pipeline Quick Start

This guide helps you set up the AI Log Analyzer pipeline in your Jenkins instance.

## Prerequisites
- Jenkins instance running (see [jenkins.md](../jenkins.md))
- GitHub account and repository access
- Docker Hub account with push access (optional, for multi-arch builds)

## Step 1: Create Jenkins Credentials for Docker Hub

Go to your Jenkins instance and add Docker Hub credentials:

1. Navigate to **Manage Jenkins** → **Manage Credentials**
2. Click **System** 
3. Click **Global credentials (unrestricted)**
4. Click **+ Add Credentials**
5. Fill in:
   - **Kind**: Username with password
   - **Username**: Your Docker Hub username
   - **Password**: Your Docker Hub personal access token
   - **ID**: `docker-hub-credentials`
   - **Description**: Docker Hub credentials
6. Click **Create**

## Step 2: Create a New Pipeline Job

1. Go to Jenkins Dashboard
2. Click **+ New Item** or **Create a job**
3. Job name: `ai-logs-analyzer`
4. Choose **Pipeline**
5. Click **OK**

## Step 3: Configure Pipeline

In the job configuration page:

### General Tab
- Discard old builds: Check this
  - Days to keep builds: 7
  - Max # of builds to keep: 20

### Build Triggers
- **GitHub hook trigger for GITScm polling** (enables webhooks)

### Pipeline Tab
Select **Pipeline script from SCM**:
- **SCM**: Git
- **Repository URL**: `https://github.com/yourusername/ai-log-analyzer.git`
- **Credentials**: Select your GitHub credentials (or use HTTPS)
- **Branch Specifier**: `*/main`
- **Script Path**: `Jenkinsfile`

Click **Save**

## Step 4: Update Pipeline Parameters

Edit the Jenkinsfile to customize for your environment:

```groovy
parameters {
    string(name: 'DOCKER_REGISTRY', defaultValue: 'docker.io', description: 'Docker registry')
    string(name: 'DOCKER_USERNAME', defaultValue: 'YOUR_DOCKER_HUB_USERNAME', description: 'Docker Hub username')
    string(name: 'IMAGE_TAG', defaultValue: 'latest', description: 'Docker image tag')
    booleanParam(name: 'PUSH_IMAGES', defaultValue: false, description: 'Push multi-arch images to Docker Hub')
}
```

Replace `YOUR_DOCKER_HUB_USERNAME` with your actual Docker Hub username.

## Step 5: Test the Pipeline

1. In Jenkins, click **Build with Parameters**
2. Set parameters:
   - DOCKER_REGISTRY: `docker.io`
   - DOCKER_USERNAME: Your Docker Hub username
   - IMAGE_TAG: `test`
   - PUSH_IMAGES: Unchecked (for initial test)
3. Click **Build**
4. Monitor the build in **Console Output**

Expected stages:
- ✓ Checkout
- ✓ Build Services
- ✓ Start Services
- ✓ Health Checks & Tests
- ✓ View Logs
- ✓ Cleanup Local Services
- (PUSH_IMAGES skipped if not checked)

## Step 6: Set Up GitHub Webhook (Optional)

Enable automatic builds when you push to GitHub:

### In GitHub
1. Go to your repository
2. **Settings** → **Webhooks** → **Add webhook**
3. Set Payload URL:
   - `http://your-jenkins-server:8080/github-webhook/`
   - Replace `your-jenkins-server` with your Jenkins server hostname/IP
4. Content type: `application/json`
5. Events: **Just the push event**
6. Click **Add webhook**

### In Jenkins (if needed)
1. **Manage Jenkins** → **Configure System**
2. Find **GitHub** section
3. Add GitHub credentials (personal access token from GitHub)
4. Click **Test connection**

## Step 7: Multi-Architecture Image Builds

To build and push multi-architecture images:

1. Create Docker Hub credentials in Jenkins (see Step 1)
2. Run the pipeline with **Build with Parameters**:
   - DOCKER_USERNAME: Your Docker Hub username
   - IMAGE_TAG: `v1.0.0` (or your version)
   - PUSH_IMAGES: **Check this** ✓
3. Pipeline will build for `linux/amd64` and `linux/arm64`
4. Images will be pushed to Docker Hub
5. View at: `https://hub.docker.com/r/your-username/ai-log-analyzer-api`

## Monitoring Builds

### View Build Logs
1. Click on the build number (e.g., `#1`)
2. Click **Console Output**
3. Scroll to see each stage

### Build Status
- Blue = Success ✓
- Red = Failed ✗
- Yellow = In Progress

### Build History
Automatically kept for 7 days (configurable in Step 3)

## Troubleshooting

### Build Fails: "docker.sock: Permission denied"
The Jenkins container cannot access the Docker daemon.

**Solution**: In Jenkins container settings, ensure `/var/run/docker.sock` is properly mounted:
```bash
docker inspect jenkins-test | grep -A 5 Mounts
```

### Build Fails: "docker buildx not found"
Multi-architecture builds require buildx.

**Solution**: Jenkins container needs buildx support:
```bash
docker exec jenkins-test docker buildx version
```

If missing, buildx installs automatically in the pipeline.

### Tests Fail: "Connection refused on port 8000"
API service didn't start in time.

**Solution**: Pipeline waits 5 seconds. For slower systems:
- Edit Jenkinsfile: Increase sleep time in "Start Services" stage
- Or increase `HEALTH_CHECK_DELAY` in `tests/test_api.py`

### Cannot Push to Docker Hub
Docker credentials not configured.

**Solution**:
1. Ensure Docker Hub credentials added to Jenkins (Step 1)
2. Verify `DOCKER_USERNAME` matches Docker Hub username
3. Use personal access token, not password
4. Test: `docker login -u your-username`

## Next Steps

- ✓ Configure email notifications for build failures
- ✓ Add pre-deployment testing stages
- ✓ Set up production deployment stage
- ✓ Configure build status badges for GitHub README
- ✓ Add Slack notifications

## Related Documentation

- [CICD_PIPELINE.md](./CICD_PIPELINE.md) - Detailed pipeline documentation
- [../jenkins.md](../jenkins.md) - Jenkins setup guide
- [../README.md](../README.md) - Main project README
