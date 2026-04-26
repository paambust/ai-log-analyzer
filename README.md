# AI Log Analyzer

A containerized microservices application for collecting, storing, and analyzing application logs using AI-powered insights. The system ingests logs via REST API and processes them asynchronously using a worker service.

## Table of Contents

- [Project Overview](#project-overview)
- [System Architecture](#system-architecture)
- [Prerequisites](#prerequisites)
- [Installation & Setup](#installation--setup)
- [Database Schema](#database-schema)
- [API Documentation](#api-documentation)
- [Worker Service](#worker-service)
- [Environment Configuration](#environment-configuration)
- [Running the Application](#running-the-application)
- [Development Guide](#development-guide)
- [Troubleshooting](#troubleshooting)

---

## Project Overview

**AI Log Analyzer** is a distributed system designed to:

1. **Collect logs** from multiple microservices via REST API endpoints
2. **Store logs** in a PostgreSQL database with metadata (service, level, timestamp)
3. **Analyze logs** asynchronously using LLM (Language Model) to generate insights
4. **Track analysis status** and store results for later retrieval

### Key Features

- **RESTful API** for log ingestion
- **Asynchronous processing** with a dedicated worker service
- **Database persistence** using PostgreSQL 15
- **Docker containerization** for easy deployment
- **Scalable architecture** supporting multiple services sending logs
- **AI-powered analysis** with LLM integration ready

---

## System Architecture

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│  Services   │         │  API Service │         │  PostgreSQL │
│ (Log Send)  ├────────→│  (FastAPI)   ├────────→│  (logsdb)   │
└─────────────┘         └──────────────┘         └─────────────┘
                         Port 8000                    Port 5432
                                ▲
                                │
                                │ (polls)
                                │
                         ┌──────────────┐
                         │ Worker Svc   │
                         │ (Analyzer)   │
                         └──────────────┘
```

### Component Breakdown

#### 1. **PostgreSQL Database** (`postgres:15`)
- Stores all log records and analysis results
- Persistent volume (`pgdata`) for data durability
- Credentials: `admin:admin`
- Database: `logsdb`
- Port: `5432` (exposed for debugging)

#### 2. **API Service** (FastAPI on Python 3.11)
- Exposes REST endpoints for log ingestion
- Connects to PostgreSQL to store logs
- Handles incoming requests from multiple services
- Port: `8000`
- Technology: FastAPI + uvicorn + psycopg2

#### 3. **Worker Service** (Python)
- Runs continuously as a background process
- Polls the database every 5 seconds for unanalyzed logs
- Fetches up to 5 logs at a time (batch processing)
- Generates AI-powered analysis for each log
- Updates the database with analysis results
- Technology: psycopg2 + requests

---

## Prerequisites

- **Docker** (v20.10+)
- **Docker Compose** (v1.29+)
- **Git**
- Optional: PostgreSQL client tools for manual database access

### Verify Installation

```bash
docker --version
docker-compose --version
```

---

## Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/ai-log-analyzer.git
cd ai-log-analyzer
```

### 2. Configure Environment Variables

Create or update `.env` file (optional for defaults):

```env
# Database Configuration
DB_HOST=postgres
DB_PORT=5432
DB_USER=admin
DB_PASSWORD=admin
DB_NAME=logsdb

# API Configuration
API_PORT=8000
API_HOST=0.0.0.0

# LLM Configuration
LLM_API_KEY=your_api_key_here
LLM_MODEL=gpt-4
LLM_ENDPOINT=https://api.openai.com/v1
```

### 3. Build and Start Services

```bash
# Build images and start all services
sudo docker-compose up -d --build

# Verify containers are running
sudo docker-compose ps
```

Expected output:
```
NAME              STATUS              PORTS
postgres          Up X seconds        0.0.0.0:5432->5432/tcp
api-service       Up X seconds        0.0.0.0:8000->8000/tcp
worker-service    Up X seconds        (no ports)
```

---

## Database Schema

### Logs Table

The `logs` table stores all incoming log records and their analysis status.

```sql
CREATE TABLE logs (
    id SERIAL PRIMARY KEY,
    service TEXT,
    level TEXT,
    message TEXT,
    analyzed BOOLEAN DEFAULT FALSE,
    analysis TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Column Descriptions

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL | Auto-incrementing unique identifier |
| `service` | TEXT | Name of the service sending the log (e.g., "auth-service", "api-gateway") |
| `level` | TEXT | Log severity level (INFO, WARNING, ERROR, CRITICAL, DEBUG) |
| `message` | TEXT | The actual log message content |
| `analyzed` | BOOLEAN | Flag indicating if log has been analyzed (default: FALSE) |
| `analysis` | TEXT | AI-generated analysis/insights (NULL if not yet analyzed) |
| `created_at` | TIMESTAMP | Server timestamp when log was received |

### Create the Table

After starting the services, connect to the database and create the table:

```bash
# Access the PostgreSQL container
sudo docker exec -it postgres sh

# Connect to the database
psql -U admin -d logsdb

# Create the table
CREATE TABLE logs (
    id SERIAL PRIMARY KEY,
    service TEXT,
    level TEXT,
    message TEXT,
    analyzed BOOLEAN DEFAULT FALSE,
    analysis TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

# Verify table creation
\dt

# Exit
\q
exit
```

---

## API Documentation

### Base URL

```
http://localhost:8000
```

### Endpoints

#### 1. Health Check

**Endpoint:** `GET /health`

**Purpose:** Verify API service is running and healthy.

**Response:**
```json
{
    "status": "ok"
}
```

**Example:**
```bash
curl http://localhost:8000/health
```

---

#### 2. Create Log Entry

**Endpoint:** `POST /logs`

**Purpose:** Submit a new log for storage and analysis.

**Request Body:**
```json
{
    "service": "auth-service",
    "level": "ERROR",
    "message": "Failed to authenticate user: token expired"
}
```

**Required Fields:**
- `service` (string): Service name
- `level` (string): Log level
- `message` (string): Log message

**Response:**
```json
{
    "status": "stored"
}
```

**HTTP Status Codes:**
- `200 OK`: Log successfully stored
- `400 Bad Request`: Missing or invalid fields
- `500 Internal Server Error`: Database connection failed

**Example:**
```bash
curl -X POST http://localhost:8000/logs \
  -H "Content-Type: application/json" \
  -d '{
    "service": "payment-service",
    "level": "WARNING",
    "message": "Payment processing took 8 seconds"
  }'
```

---

### API Implementation Details

**File:** `api/main.py`

- Uses **FastAPI** framework for async request handling
- Connects to PostgreSQL using **psycopg2** library
- Connection pooling could be added for production
- Currently uses direct inserts; consider adding transaction handling

---

## Worker Service

### Overview

The Worker Service is a long-running background process that performs asynchronous log analysis.

**File:** `worker/worker.py`

### Workflow

```
1. Connect to PostgreSQL database
2. Poll every 5 seconds for unanalyzed logs (LIMIT 5)
3. For each log:
   - Extract log ID and message
   - Call LLM API for analysis (placeholder in current code)
   - Generate analysis insight
4. Update logs table:
   - Set analyzed = TRUE
   - Store analysis result
5. Repeat
```

### Current Implementation

```python
# Polling frequency
time.sleep(5)  # Checks database every 5 seconds

# Batch size
LIMIT 5  # Processes up to 5 logs per cycle

# Analysis (placeholder)
analysis = f"Possible issue detected: {message}"
```

### Production Considerations

1. **LLM Integration**: Replace placeholder with actual LLM API calls
   ```python
   import requests
   
   response = requests.post(
       f"{os.getenv('LLM_ENDPOINT')}/chat/completions",
       headers={"Authorization": f"Bearer {os.getenv('LLM_API_KEY')}"},
       json={"messages": [{"role": "user", "content": f"Analyze: {message}"}]}
   )
   analysis = response.json()["choices"][0]["message"]["content"]
   ```

2. **Error Handling**: Add try-catch for network/API failures

3. **Logging**: Implement structured logging for debugging

4. **Scaling**: Add multiple worker instances for higher throughput

---

## Environment Configuration

### Database Environment Variables

These are set in `docker-compose.yml` and passed to containers:

```yaml
environment:
  DB_HOST: postgres          # Hostname (service name in Docker)
  DB_PORT: 5432             # PostgreSQL default port
  DB_USER: admin            # Database username
  DB_PASSWORD: admin        # Database password (CHANGE IN PRODUCTION!)
  DB_NAME: logsdb           # Database name
```

### Service-Specific Variables

**Worker Service:**
```yaml
LLM_API_KEY: your_key_here  # API key for LLM service
```

### Changing Credentials

**⚠️ Security Warning:** Default credentials are for development only.

To change database credentials:

1. Update `docker-compose.yml`:
   ```yaml
   postgres:
     environment:
       POSTGRES_USER: your_username
       POSTGRES_PASSWORD: your_password  # Use strong password!
       POSTGRES_DB: your_database
   ```

2. Rebuild and restart:
   ```bash
   sudo docker-compose down -v  # Remove old data
   sudo docker-compose up -d --build
   ```

---

## Running the Application

### Start All Services

```bash
# Build and start (development mode)
sudo docker-compose up -d --build

# View logs
sudo docker-compose logs -f
```

### Stop All Services

```bash
sudo docker-compose down
```

### Remove All Data and Containers

```bash
# Stop and remove containers, volumes
sudo docker-compose down -v

# This will delete the pgdata volume!
```

### View Individual Service Logs

```bash
# API service logs
sudo docker-compose logs api

# Worker service logs
sudo docker-compose logs worker

# Database logs
sudo docker-compose logs postgres

# Live logs with tail
sudo docker-compose logs -f api
```

### Access PostgreSQL Directly

```bash
# Interactive shell
sudo docker exec -it postgres sh

# Inside container, connect to database
psql -U admin -d logsdb

# List tables
\dt

# View logs table structure
\d logs

# Query logs
SELECT * FROM logs;
SELECT * FROM logs WHERE analyzed = FALSE;
SELECT * FROM logs WHERE level = 'ERROR';

# Exit
\q
exit
```

---

## Development Guide

### Project Structure

```
ai-log-analyzer/
├── api/
│   ├── Dockerfile          # API service container definition
│   ├── main.py             # FastAPI application
│   └── requirements.txt     # Python dependencies
├── worker/
│   ├── Dockerfile          # Worker service container definition
│   ├── worker.py           # Async log processor
│   └── requirements.txt     # Python dependencies
├── docker-compose.yml       # Multi-container orchestration
├── README.md               # This file
└── .env                    # Environment variables (optional)
```

### Local Development (Without Docker)

For faster iteration during development:

```bash
# Install PostgreSQL locally
# (macOS: brew install postgresql, Ubuntu: sudo apt-get install postgresql)

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r api/requirements.txt
pip install -r worker/requirements.txt

# Set environment variables
export DB_HOST=localhost
export DB_PORT=5432
export DB_USER=admin
export DB_PASSWORD=admin
export DB_NAME=logsdb

# Run API locally
cd api
uvicorn main:app --reload --port 8000

# In another terminal, run worker
cd worker
python worker.py
```

### Adding New API Endpoints

Edit `api/main.py`:

```python
@app.get("/logs/count")
def count_logs():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM logs")
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return {"total_logs": count}
```

### Modifying Worker Logic

Edit `worker/worker.py`:

Change polling frequency:
```python
time.sleep(10)  # Poll every 10 seconds instead of 5
```

Change batch size:
```python
cur.execute("SELECT id, message FROM logs WHERE analyzed = false LIMIT 10")
```

---

## Troubleshooting

### Issue: Docker Compose Build Fails

**Error:** `sudo docker compose --build` returns exit code 1

**Solutions:**

1. Check Docker daemon is running:
   ```bash
   sudo systemctl start docker
   ```

2. Verify docker-compose.yml syntax:
   ```bash
   docker-compose config
   ```

3. Clean and rebuild:
   ```bash
   sudo docker-compose down -v
   sudo docker-compose up -d --build
   ```

---

### Issue: Cannot Connect to Database

**Error:** `psql: error: connection to server on socket "/var/run/postgresql/.s.PGSQL.5432" failed: FATAL: database "admin" does not exist`

**Solution:** Use correct connection parameters:

```bash
# Wrong (defaults to database named 'admin'):
psql -U admin

# Correct (specifies 'logsdb' database):
psql -U admin -d logsdb
```

---

### Issue: API Service Crashes on Startup

**Error:** Container exits immediately after starting

**Debugging:**

```bash
# Check logs
sudo docker-compose logs api

# Common cause: Missing database connection
# Ensure postgres service is healthy first:
sudo docker-compose ps
sudo docker-compose logs postgres
```

---

### Issue: Worker Service Not Processing Logs

**Debugging:**

1. Check if worker is running:
   ```bash
   sudo docker-compose ps worker-service
   ```

2. View worker logs:
   ```bash
   sudo docker-compose logs -f worker
   ```

3. Verify logs table exists:
   ```bash
   sudo docker exec -it postgres psql -U admin -d logsdb -c "\dt"
   ```

4. Check for unanalyzed logs:
   ```bash
   sudo docker exec -it postgres psql -U admin -d logsdb \
     -c "SELECT COUNT(*) FROM logs WHERE analyzed = FALSE;"
   ```

---

### Issue: High Disk Usage

**Cause:** PostgreSQL volume growing too large

**Solution:**

```bash
# Clean up old logs
sudo docker exec -it postgres psql -U admin -d logsdb \
  -c "DELETE FROM logs WHERE created_at < NOW() - INTERVAL '30 days';"

# Or remove and recreate (WARNING: deletes all data)
sudo docker-compose down -v
sudo docker-compose up -d --build
```

---

## Performance Optimization Tips

1. **Add Database Indexes:**
   ```sql
   CREATE INDEX idx_analyzed ON logs(analyzed);
   CREATE INDEX idx_created_at ON logs(created_at);
   CREATE INDEX idx_service ON logs(service);
   ```

2. **Use Connection Pooling:**
   - Replace direct `psycopg2` connections with **pgbouncer**

3. **Scale Worker Service:**
   - Run multiple worker instances with Docker Compose `replicas`

4. **Add Caching:**
   - Cache frequent queries with **Redis**

5. **Implement Batch Processing:**
   - Increase `LIMIT` in worker query for better throughput

---

## Security Notes

⚠️ **Development-Only Configuration**

The current setup uses:
- Default database credentials (`admin:admin`)
- Exposed database port (`5432`)
- No authentication on API endpoints
- No HTTPS/TLS

**For Production, implement:**

1. Strong database passwords
2. Network isolation (no direct DB port exposure)
3. API authentication (JWT, API keys)
4. HTTPS/TLS encryption
5. Rate limiting
6. Input validation and sanitization
7. Secrets management (environment vault, Kubernetes secrets)

---

## Future Enhancements

- [ ] Real LLM integration (OpenAI, Azure OpenAI, etc.)
- [ ] API authentication and rate limiting
- [ ] Advanced filtering and search endpoints
- [ ] Dashboard UI for log visualization
- [ ] Alert system for critical logs
- [ ] Log retention policies
- [ ] Metrics and monitoring (Prometheus)
- [ ] Horizontal scaling with Kubernetes
- [ ] Database backups and recovery

---

## Support & Contribution

For issues or questions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review Docker Compose logs: `sudo docker-compose logs`
3. Verify database schema with: `\d logs`

---


**Last Updated:** April 2026
