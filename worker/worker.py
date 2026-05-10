import time
import psycopg2
import os
import requests


def get_conn(max_retries=5, retry_delay=2):
    """Connect to database with retry logic"""
    for attempt in range(max_retries):
        try:
            return psycopg2.connect(
                host=os.getenv("DB_HOST"),
                port=int(os.getenv("DB_PORT", 5432)),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                dbname=os.getenv("DB_NAME")
            )
        except psycopg2.OperationalError as e:
            if attempt < max_retries - 1:
                print(f"Connection attempt {attempt + 1} failed. Retrying in {retry_delay}s...")
                time.sleep(retry_delay)
            else:
                print(f"Failed to connect after {max_retries} attempts")
                raise


def analyze_log_with_llm(service, level, message):
    llm_endpoint = os.getenv("LLM_ENDPOINT", "http://192.168.0.3:11434/api/generate")
    
    prompt = f"""You are a senior DevOps/SRE engineer with expertise in system troubleshooting.

Analyze the following production log entry and provide actionable insights:

**Service:** {service}
**Severity Level:** {level}
**Log Message:** {message}

Please provide a structured analysis with:

1. **Issue Summary** (1-2 sentences): What problem does this log indicate?
2. **Root Cause Analysis** (brief): What likely caused this? 
3. **Severity Rating** (select one): CRITICAL | HIGH | MEDIUM | LOW
4. **Immediate Actions** (1-3 bullet points): What should be done right now?
5. **Long-term Prevention** (1-2 bullet points): How to prevent this recurring?

Be concise but specific. Focus on actionable items."""

    try:
        response = requests.post(
            llm_endpoint,
            json={
                "model": "tinyllama",
                "prompt": prompt,
                "stream": False,
                "temperature": 0.3,
                "top_k": 40,
                "top_p": 0.9
            },
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("response", "No response from LLM")
        else:
            return f"LLM error: {response.status_code} - Auto-generated analysis for {service} [{level}]: {message}"
    except requests.exceptions.ConnectionError:
        # LLM not available - generate mock analysis for testing
        severity_map = {"ERROR": "HIGH", "CRITICAL": "CRITICAL", "WARNING": "MEDIUM"}
        severity = severity_map.get(level, "LOW")
        return f"[MOCK ANALYSIS - LLM unavailable]\nService: {service}\nLog Level: {level}\nSeverity: {severity}\nMessage: {message}\n\nNote: This is a mock analysis. Connect LLM for full analysis."
    except Exception as e:
        return f"Failed to call LLM: {str(e)} - Using default analysis"


while True:
    try:
        conn = get_conn()
        cur = conn.cursor()

        # Analyze unanalyzed logs (not just ERROR, to support testing)
        cur.execute("""
            SELECT id, service, level, message 
            FROM logs 
            WHERE analyzed = false
            LIMIT 5
        """)

        rows = cur.fetchall()

        for row in rows:
            log_id, service, level, message = row

            try:
                print(f"Analyzing log {log_id}: [{level}] {service}")
                analysis = analyze_log_with_llm(service, level, message)
            except Exception as e:
                analysis = f"LLM failed: {str(e)}"

            cur.execute(
                "UPDATE logs SET analyzed=true, analysis=%s WHERE id=%s",
                (analysis, log_id)
            )
            print(f"  ✓ Log {log_id} analyzed and marked")

        conn.commit()
        cur.close()
        conn.close()
        
        # Sleep before next iteration
        time.sleep(10)
        
    except Exception as e:
        print(f"Worker error: {e}")
        time.sleep(10)  # Retry after delay