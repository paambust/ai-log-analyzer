# Docker-Compose Not Found in Jenkins - Solution

## The Problem

**Error**: `docker-compose: not found` in Jenkins pipeline

**Why it happens**:
- Host machine has `docker-compose` installed ✓
- Jenkins **container** doesn't have it installed ✗
- Jenkins container = separate filesystem from the host
- Just because host has a tool doesn't mean the container does

## Solution Implemented

I've updated the `Jenkinsfile` to handle this automatically with three approaches:

### Approach 1: Setup Stage (Automatic Installation)
Added a new **Setup** stage that runs first:

```groovy
stage('Setup') {
    steps {
        sh '''
            # Checks if docker-compose exists
            # If not, either uses docker compose v2 OR installs it
        '''
    }
}
```

This stage:
1. ✓ Checks if `docker-compose` command exists
2. ✓ If not, checks if `docker compose` v2 is available (newer Docker)
3. ✓ If still not available, **automatically downloads and installs** docker-compose

### Approach 2: Fallback Command
All docker-compose calls now use this pattern:

```bash
COMPOSE="docker-compose"
if ! command -v docker-compose &> /dev/null; then
    COMPOSE="docker compose"
fi
$COMPOSE up -d
```

Tries v1 first, falls back to v2 if available.

### Approach 3: Manual Install (If Needed)
If autoinstall fails, you can manually install in the Jenkins container:

```bash
docker exec -it jenkins-test bash

# Inside container:
curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Verify:
docker-compose --version

exit
```

---

## How to Test the Fix

1. **Push updated Jenkinsfile to GitHub**:
```bash
git add Jenkinsfile
git commit -m "Fix docker-compose not found in Jenkins container"
git push origin main
```

2. **Run Jenkins pipeline again**:
   - Go to Jenkins UI
   - Click **Build Now**
   - Watch the **Setup** stage - should see:
     ```
     ✓ Checking dependencies...
     ✓ docker-compose available
     docker-compose version 1.29.2, build unknown
     ```

3. **If you see that output**, the fix worked! ✓

---

## Understanding the Issue Better

### What IS docker-compose?
It's just a binary (executable file) that orchestrates Docker containers.

Location on host: `/usr/bin/docker-compose` or similar

### Why Host's docker-compose Doesn't Help
```
Host filesystem:           Jenkins Container filesystem:
/usr/bin/                  ❌ /usr/bin/ (container's own)
  └─ docker-compose ✓
  └─ docker ✓             
  └─ ...                     └─ docker ✓
                             └─ ... 
                             └─ docker-compose? ❌ NOT HERE!
```

The host's tools are **not visible** inside the container unless they're **mounted**.

### Mount Strategy
We could mount it like Docker socket:
```bash
docker run ... -v /usr/bin/docker-compose:/usr/bin/docker-compose ...
```

But this is **not ideal** because:
- Version mismatch issues
- Binary compatibility across Linux versions
- Maintenance headache

**Better approach**: Install inside container (what we're doing now)

---

## Docker-Compose Versions

### v1 (docker-compose)
```bash
docker-compose --version
-> docker-compose version 1.29.2
```
- Standalone binary
- Must be installed separately
- Older syntax

### v2 (docker compose)
```bash
docker compose --version
-> Docker Compose version v2.20.0
```
- Built into Docker
- Modern syntax
- Faster, more features

Our updated Jenkinsfile supports both!

---

## What the Updated Jenkinsfile Does

### Stage Order:
1. **Setup** ← NEW!
   - Checks for docker-compose
   - Installs if missing
   
2. Checkout
3. Build Services
4. Start Services
5. Health Checks & Tests
6. View Logs
7. Cleanup Services
8. Build Multi-Arch (optional)
9. Docker Hub Summary (optional)
10. Cleanup Images (optional)

---

## If Install Still Fails

### Check Internet Connection
The Setup stage downloads docker-compose from GitHub. It needs internet:

```bash
# Test from Jenkins container
docker exec jenkins-test curl https://github.com -I

# If this fails, check network/firewall
```

### Alternative: Pre-Install in Container

Before using Jenkins:

```bash
# Install docker-compose in Jenkins container
docker exec jenkins-test sh -c '
    curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-Linux-x86_64" \
        -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    docker-compose --version
'
```

### Check if Docker Compose V2 is Available
Newer Docker comes with compose built-in:

```bash
# Check in Jenkins container
docker exec jenkins-test docker compose version
```

If that works, the Setup stage will use it automatically.

---

## Full Updated Jenkinsfile

The `Jenkinsfile` is now updated with:
- ✓ New **Setup** stage for dependency checking
- ✓ All `docker-compose` calls now fallback to `docker compose`
- ✓ Automatic installation if needed
- ✓ Error handling for network issues

---

## Related Changes

Updated files:
- `Jenkinsfile` - Main pipeline file

No other files need changes. The rest of the infrastructure (docker-compose.yml, tests, etc.) stays the same.

---

## Next Steps

1. Commit and push the updated Jenkinsfile
2. Run the pipeline again
3. Check for green ✓ in Setup stage
4. All subsequent stages should work

If you hit any other issues, they'll be clearer now without the docker-compose error blocking everything.

---

## Troubleshooting Checklist

- [ ] Git push updated Jenkinsfile
- [ ] Run "Build Now" in Jenkins
- [ ] Setup stage completes with ✓
- [ ] First error should be something else (not docker-compose)
- [ ] If no other errors, pipeline succeeds!

**Enjoy your working CI/CD pipeline!** 🚀
