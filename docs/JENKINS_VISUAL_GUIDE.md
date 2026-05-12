# Jenkins Pipeline Setup - Visual Quick Reference

Quick visual guide for setting up the AI Log Analyzer pipeline in Jenkins UI.

## 🎯 Quick Overview

```
Push Jenkinsfile to GitHub
        ↓
Create Pipeline job in Jenkins UI (one-time setup)
        ↓
Click "Build Now" (manual) OR push to GitHub (auto with webhook)
        ↓
Pipeline runs all stages automatically
        ↓
Tests run, images build, optionally push to Docker Hub
```

---

## ✅ Pre-Flight Checklist

Before starting, verify:

- [ ] Jenkins running: `http://localhost:8080`
- [ ] Can login to Jenkins
- [ ] Docker Hub token added to Jenkins credentials (you mentioned this is done ✓)
- [ ] GitHub token added to Jenkins credentials (you mentioned this is done ✓)
- [ ] `Jenkinsfile` in your repo: `https://github.com/paambust/ai-log-analyzer/blob/main/Jenkinsfile`

---

## 🔧 Three Simple Steps to Set Up

### Step 1️⃣: Create New Pipeline Job (2 minutes)

**On Jenkins Dashboard:**
1. Click **+ New Item**
2. Type job name: `ai-logs-analyzer`
3. Select **Pipeline** (the one with box icons)
4. Click **OK**

✓ You're now in the Job Configuration page.

---

### Step 2️⃣: Configure SCM (Git) (2 minutes)

**On the Configuration page, scroll to "Pipeline" section:**

Change **Definition** dropdown to: `Pipeline script from SCM`

Now configure **SCM** section:

| Field | Value |
|-------|-------|
| **SCM** | `Git` |
| **Repository URL** | `https://github.com/paambust/ai-log-analyzer.git` |
| **Credentials** | Select your GitHub token |
| **Branch Specifier** | `*/main` |
| **Script Path** | `Jenkinsfile` |

If GitHub credentials not in dropdown, add them:
- Click **Add** → **Jenkins**
- **Kind**: `Username with password`
- **Username**: `paambust`
- **Password**: Your GitHub personal access token (NOT password)
- **ID**: `github-credentials`
- Click **Create**

✓ Now select it from the dropdown.

---

### Step 3️⃣: Save & Build (1 minute)

**Bottom of page:**
1. Click **Save** button (blue)
2. You're back on job page
3. Click **Build Now** (left sidebar)

✓ Build starts! Click build number in **Build History** to see progress.

---

## ▶️ Running Pipeline

### Method A: Simple Test Build

```
Click: Build Now
Wait: 2-3 minutes for docker-compose to build and test
Result: See ✓ if all tests passed
```

### Method B: Build & Push to Docker Hub

```
Click: Build with Parameters
Form appears with options:
  - DOCKER_REGISTRY: docker.io (leave as is)
  - DOCKER_USERNAME: pawambust (leave as is)
  - IMAGE_TAG: latest (or set to v1.0.0)
  - PUSH_IMAGES: ☐ UNCHECK for test, ☑ CHECK to actually push

Set PUSH_IMAGES to ☑ Checked
Click: Build
Wait: 5-10 minutes (buils for two architectures)
Result: See images on hub.docker.com/r/pawambust/ai-log-analyzer-api
```

---

## 📊 Pipeline Stages (What Happens)

```
Build Timeline:
├─ Checkout (30 sec)           → Clones code from GitHub
├─ Build Services (1 min)      → Builds Docker images locally
├─ Start Services (30 sec)     → Starts API, Worker, PostgreSQL
├─ Health Checks & Tests (1 min) → Runs test suite
├─ View Logs (30 sec)          → Shows service logs
├─ Cleanup Services (30 sec)   → Stops containers
├─ Build Multi-Arch (5 min)    → [Only if PUSH_IMAGES=true]
│                               → Builds for AMD64 + ARM64
├─ Docker Hub Summary (10 sec) → [Only if PUSH_IMAGES=true]
│                               → Shows published URLs
└─ Cleanup Images (30 sec)     → [Only if PUSH_IMAGES=true]
                               → Removes local copies

Total time: ~2-3 min (without push), ~7-10 min (with push)
```

---

## 🎬 Step-by-Step Screenshots (Text Description)

### Screen 1: Jenkins Dashboard
```
┌─────────────────────────────────────┐
│ Jenkins                             │
├─────────────────────────────────────┤
│ [+] New Item   [New View]           │
│                                     │
│ Build Name    Status  |  Last Build │
│ ────────────────────────────────────│
│ my-old-job 2  ✓ (blue)  |  2 days  │
│ tutorial      🔴 (red)   |  5 days  │
│                                     │
└─────────────────────────────────────┘
       ↓ Click "+ New Item"
```

### Screen 2: Create Job
```
┌─────────────────────────────────────┐
│ Create New Item                     │
├─────────────────────────────────────┤
│ Enter an item name:                 │
│ [ai-logs-analyzer________]          │
│                                     │
│ Type:                               │
│ ○ Freestyle job                     │
│ ○ Pipeline  ← SELECT THIS ONE       │
│ ○ Multibranch Pipeline              │
│ ○ Organization Folder               │
│                                     │
│            [OK]  [Cancel]           │
└─────────────────────────────────────┘
```

### Screen 3: Job Configuration - Pipeline Section
```
┌─────────────────────────────────────┐
│ Job Configuration                   │
│                                     │
│ [General] [Build Env] [Build Triggers]
│ [Pipeline] ← Click this tab         │
│                                     │
│ Pipeline:                           │
│                                     │
│ Definition: [Pipeline script from SCM ▼]
│                                     │
│ SCM Configuration:                  │
│ ┌────────────────────────────────┐  │
│ │ SCM: [Git ▼]                   │  │
│ │                                │  │
│ │ Repository URL:                │  │
│ │ [https://github.com/paambust...│  │
│ │                                │  │
│ │ Credentials:                   │  │
│ │ [github-credentials ▼]         │  │
│ │                                │  │
│ │ Branch Specifier:              │  │
│ │ [*/main]                       │  │
│ │                                │  │
│ │ Script Path:                   │  │
│ │ [Jenkinsfile]                  │  │
│ └────────────────────────────────┘  │
│                                     │
│              [Save]  [Cancel]       │
└─────────────────────────────────────┘
```

### Screen 4: Job Page - Ready to Build
```
┌──────────────────────────────────┐
│ ai-logs-analyzer                 │
├──────────────────────────────────┤
│ ← Back  [Refresh]                │
│                                  │
│ LEFT SIDEBAR:                    │
│ • Build Now       ← Click this   │
│ • Build with Parameters          │
│ • Configure                      │
│ • Delete Job                     │
│ • Rename                         │
│                                  │
│ BUILD HISTORY:                   │
│ Recent Builds:                   │
│ (empty - no builds yet)          │
│                                  │
└──────────────────────────────────┘
```

### Screen 5: Build Running - Console Output
```
┌──────────────────────────────────────┐
│ Build #1 - Console Output            │
├──────────────────────────────────────┤
│ [Pipeline] Start of Pipeline         │
│ [Pipeline] stage                     │
│ [Pipeline] { (Checkout)              │
│  > git init /var/jenkins_home/ws...  │
│  > git fetch --tags --force...       │
│  > git checkout -f abc123def...      │
│ [Pipeline] }                         │
│ [Pipeline] stage                     │
│ [Pipeline] { (Build Services)        │
│  > docker-compose build --no-cache   │
│  Building api                        │
│  Step 1/4 : FROM python:3.11-slim    │
│  ...                                 │
│ [Pipeline] { (Start Services)        │
│  > docker-compose up -d              │
│  Creating network...                 │
│  Creating postgres...                │
│  Creating api-service...             │
│ [Pipeline] { (Health Checks & Tests) │
│  Installing test dependencies...     │
│  Running integration tests...        │
│  ✓ API Health Check: Status: 200     │
│  ✓ Create Log: Status: 200           │
│ ...                                  │
│ Finished: SUCCESS ✓                  │
└──────────────────────────────────────┘
```

---

## 🚀 Your Next Actions

### Immediate (Right Now):
1. Commit and push `Jenkinsfile` to GitHub
2. Go to `http://localhost:8080/`
3. Create Pipeline job (follow steps above)
4. Click **Build Now**
5. View Console Output

### Next 5 Minutes:
- ✓ Watch first build complete
- ✓ Verify tests pass
- ✓ Check for any errors

### After First Success:
- [ ] Run with **Build with Parameters** and set PUSH_IMAGES=true
- [ ] Verify images appear on Docker Hub
- [ ] Set up GitHub webhook (auto-triggers on push)

---

## 🐛 Common Setup Mistakes

| Mistake | Fix |
|---------|-----|
| "Jenkinsfile not found" | Push to GitHub first: `git push` |
| Script Path wrong | Ensure it says `Jenkinsfile` (not `Jenkinsfiles` or `jenkins/file`) |
| GitHub credentials not in dropdown | Click **Add** to create GitHub credentials |
| SCM shows "Git" not available | Ensure Git plugin installed in Jenkins |
| Build fails: "docker-compose not found" | Verify Jenkins container setup with docker-compose |
| PUSH_IMAGES checkbox not appearing | This is a parameter in Jenkinsfile - don't worry, just use Build Now |

---

## 📋 Jenkinsfile Locations

Make sure these files are in your GitHub repo:

```
ai-log-analyzer/
├── Jenkinsfile ← This one! Must be in root
├── docker-compose.yml
├── tests/
│   ├── test_api.py
│   └── requirements.txt
├── api/
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
└── worker/
    ├── Dockerfile
    ├── worker.py
    └── requirements.txt
```

---

## ✨ Final Tips

1. **First build will be slow** (2-3 min) because it downloads base images
   - Subsequent builds are faster (cached layers)

2. **Console output is your friend**
   - If something fails, check Console Output for error messages
   - Scroll down to see full logs

3. **Build with Parameters** only appears if Jenkinsfile has `parameters {}` block
   - Ours does, so it should appear in left sidebar

4. **Webhook (auto-trigger) setup is separate**
   - Manual builds work first, webhook is optional enhancement

5. **Docker Hub images won't appear** unless you set PUSH_IMAGES=true
   - First test without pushing (PUSH_IMAGES=false)

---

## Need Help?

Check these docs:
- [JENKINS_FAQ.md](./JENKINS_FAQ.md) - Common questions
- [CICD_PIPELINE.md](./CICD_PIPELINE.md) - How pipeline works
- [DOCKER_CREDENTIALS.md](./DOCKER_CREDENTIALS.md) - Credential management
- [../Jenkinsfile](../Jenkinsfile) - The pipeline code itself
