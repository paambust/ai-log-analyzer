# Jenkins Pipeline Quick Start

This guide helps you set up the AI Log Analyzer pipeline in your Jenkins instance.

## Prerequisites
- Jenkins instance running (see [jenkins.md](../jenkins.md))
- GitHub account and repository access
- Docker Hub account with push access (optional, for multi-arch builds)

# Run Jenkins container and to allow host docker engine doing the heavy lifting while building docker images
```
~ % docker run -d \
  --name jenkins-test \
  -p 8080:8080 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v jenkins_home_lab:/var/jenkins_home \
  jenkins/jenkins:lts

docker run -d \
  --name jenkins-lab \
  --user root \
  -p 8080:8080 \
  -p 50000:50000 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v $(pwd):/home/ubuntu/ai-log-analyzer \
  -v jenkins_home_lab:/var/jenkins_home \
  docker.io/library/pawambust.jenkins:lts-pawan-0.1

docker exec jenkins-test cat /var/jenkins_home/secrets/initialAdminPassword
3827d4072f5e4d0d862ef4214288034e
http://localhost:8080
```
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
7. Now select it from the dropdown

---

### PART 4: Save Configuration
Scroll to **bottom** of page

Click **Save** button (blue button)

✓ Pipeline job is now created!

---

## Running the Pipeline

### Option A: Run Without Parameters (Quick Test)

1. In Jenkins, from the job page, click **Build Now** (left sidebar)
2. A new build starts (listed in **Build History** at bottom-left)
3. Click the build number (e.g., `#1`) to see details
4. Click **Console Output** to watch real-time logs

Expected output:
```
[Pipeline] Start of Pipeline
[Pipeline] stage
[Pipeline] { (Checkout)
[Pipeline] checkout
 > git init /var/jenkins_home/workspace/ai-logs-analyzer
 > git fetch...
[Pipeline] echo
Commit message: ...
...
```

### Option B: Run With Parameters (Multi-Arch Build)

This option builds and pushes multi-arch images to Docker Hub.

1. From job page, click **Build with Parameters** (left sidebar)
2. You'll see a form with parameter inputs:

```
DOCKER_REGISTRY:    docker.io
DOCKER_USERNAME:    pawambust  (auto-filled from Jenkinsfile default)
IMAGE_TAG:          latest  (or set to v1.0.0)
PUSH_IMAGES:        ☐ (checkbox)
```

**To push images to Docker Hub**, CHECK the `PUSH_IMAGES` box:
```
PUSH_IMAGES:        ☑ Checked!
```

3. Click **Build** button
4. Pipeline starts with these custom parameters

---

## Monitoring Pipeline Execution

### During Build
- Click build number (e.g., `#1`)
- Click **Console Output**
- Watch logs in real-time

### What Each Stage Does

```
1. Checkout          → Clones your GitHub repo
2. Build Services    → Builds Docker images with docker-compose
3. Start Services    → Spins up API, Worker, PostgreSQL
4. Health Checks     → Runs integration tests
5. View Logs         → Captures service logs for debugging
6. Cleanup Services  → Stops and removes containers
7. Build Multi-Arch  → (Only if PUSH_IMAGES=true) Builds for ARM64 + AMD64
8. Docker Hub Summary→ Shows published image URLs
9. Cleanup Images    → (Only if PUSH_IMAGES=true) Removes local images
```

### Expected Output

**Successful build (PUSH_IMAGES=false):**
```
[Pipeline] stage
[Pipeline] { (Checkout)
...
[Pipeline] { (Health Checks & Tests)
Installing test dependencies...
Successfully installed requests==2.32.3 pytest==7.4.4
Running integration tests...
✓ API Health Check: Status: 200
✓ Create Log: Status: 200
✓ Retrieve Logs: Retrieved 5 logs
✓ All tests passed!
...
Finished: SUCCESS ✓
```

**Successful build (PUSH_IMAGES=true):**
```
...
[Pipeline] { (Build Multi-Arch Images)
Authenticating to Docker Hub...
Docker buildx version ...
Building API image for amd64,arm64...
#1 [internal] load build definition from Dockerfile
...
#20 exporting to oci image format
[output_1] digest: sha256:abc123...
Logging out from Docker Hub...
...
======================================
Multi-Arch Images Published to Docker Hub:
======================================
API Service:    docker.io/pawambust/ai-log-analyzer-api:latest
Worker Service: docker.io/pawambust/ai-log-analyzer-worker:latest
Platforms: linux/amd64, linux/arm64
======================================
...
Finished: SUCCESS ✓
```

### Build Status Colors
- 🔵 **Blue** = Successful
- 🔴 **Red** = Failed
- ⚪ **Gray** = In progress or not run

---

## Setting Up GitHub Webhook (Optional - For Auto-Triggers)

This makes the pipeline run automatically when you push to GitHub.

### In Jenkins:
1. Go to Jenkins job page
2. Click **Configure** (left sidebar)
3. Find **Build Triggers** section
4. Check ✓ **GitHub hook trigger for GITScm polling**
5. Click **Save**

### In GitHub:
1. Go to your repository: `https://github.com/paambust/ai-log-analyzer`
2. Click **Settings** (top-right, gear icon)
3. Click **Webhooks** (left sidebar)
4. Click **Add webhook**
5. Fill the form:

```
Payload URL:
  http://your-jenkins-server:8080/github-webhook/
  
  Replace "your-jenkins-server" with your Jenkins IP
  Example: http://192.168.0.5:8080/github-webhook/

Content type:
  application/json ▼

Events:
  Select: Just the push event ●

Active:
  ☑ Check this box

```

6. Click **Add webhook**

**Verify**: Green checkmark ✓ means webhook is working.

Now, every push to GitHub automatically triggers a Jenkins build!

---

## First Build Checklist

Use this checklist for your first build:

- [ ] Visit Jenkins: `http://localhost:8080`
- [ ] Create Pipeline job named: `ai-logs-analyzer`
- [ ] Set Repository URL to your GitHub repo
- [ ] Set Script Path to: `Jenkinsfile`
- [ ] Save configuration
- [ ] Click **Build Now**
- [ ] Wait for build to complete
- [ ] Check Console Output for any errors
- [ ] If successful, try **Build with Parameters** with PUSH_IMAGES=true
- [ ] Check Docker Hub for new images
- [ ] Verify images are multi-arch: Visit hub.docker.com/r/pawambust/ai-log-analyzer-api

---

## Troubleshooting Your First Build

### Build Fails: "Jenkinsfile not found"
**Cause**: `Jenkinsfile` not in your repo
**Solution**:
```bash
git add Jenkinsfile
git commit -m "Add CI/CD pipeline"
git push origin main
```

### Build Fails: "docker-compose: command not found"
**Cause**: Jenkins container doesn't have docker-compose
**Solution**: Ensure Jenkins has docker-compose installed:
```bash
docker exec jenkins-test docker-compose version
```

### Build Fails: "docker-hub-credentials not found"
**Cause**: Credential ID mismatch in Jenkinsfile
**Solution**:
1. Verify credential ID in Jenkins: `docker-hub-credentials`
2. Verify Jenkinsfile has same ID: `credentials('docker-hub-credentials')`
3. IDs are case-sensitive!

### Build Fails: "HTTP Error 403"
**Cause**: GitHub token expired or has wrong permissions
**Solution**:
1. Go to GitHub: Settings → Developer settings → Personal access tokens
2. Delete old token, create new one with `repo` + `admin:repo_hook` scopes
3. Update Jenkins credentials with new token

### Build Fails: "Service didn't respond in time"
**Cause**: Services took too long to start
**Solution**: Edit Jenkinsfile, in "Start Services" stage:
```groovy
sleep 5  ← Change to: sleep 10
```

### Tests Pass But Docker Push Fails
**Cause**: Docker Hub token missing or invalid
**Solution**:
1. Verify Docker Hub token is valid: https://hub.docker.com/settings/security
2. Test manually: `docker login -u pawambust` (use token as password)
3. Update Jenkins credentials with new token

---

## Next Steps

After first successful build:

1. **GitHub Webhook** - Set up auto-triggers on push (see section above)
2. **Build Notifications** - Add email alerts for failures
3. **More Tests** - Add additional health checks
4. **Production Deploy** - Add deployment stage to pipeline
5. **Build Badges** - Add status badges to GitHub README

---

## Related Documentation

- [Jenkinsfile](../Jenkinsfile) - Pipeline definition
- [CICD_PIPELINE.md](./CICD_PIPELINE.md) - Detailed pipeline info
- [DOCKER_CREDENTIALS.md](./DOCKER_CREDENTIALS.md) - Credential management
- [JENKINS_FAQ.md](./JENKINS_FAQ.md) - Common questions
- [../jenkins.md](../jenkins.md) - Jenkins container setup
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
