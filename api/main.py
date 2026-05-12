from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import psycopg2
import os
from contextlib import contextmanager
import sys

app = FastAPI()

def init_database():
    """Initialize database tables - run on startup"""
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT", 5432)),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            dbname=os.getenv("DB_NAME")
        )
        cur = conn.cursor()
        
        # Create logs table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id SERIAL PRIMARY KEY,
                service VARCHAR(255) NOT NULL,
                level VARCHAR(50) NOT NULL,
                message TEXT NOT NULL,
                analyzed BOOLEAN DEFAULT FALSE,
                analysis TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create index for faster queries
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_logs_analyzed 
            ON logs(analyzed)
        """)
        
        conn.commit()
        cur.close()
        conn.close()
        print("✓ Database tables initialized successfully", file=sys.stderr)
        return True
    except Exception as e:
        print(f"✗ Database initialization failed: {e}", file=sys.stderr)
        return False

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on application startup"""
    init_database()

def get_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        dbname=os.getenv("DB_NAME")
    )

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/logs")
def create_log(log: dict):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO logs (service, level, message) VALUES (%s, %s, %s)",
        (log["service"], log["level"], log["message"])
    )

    conn.commit()
    cur.close()
    conn.close()

    return {"status": "stored"}


@app.get("/logs")
def get_logs(analyzed: bool = None, limit: int = 10):
    """Retrieve logs with optional filtering"""
    conn = get_conn()
    cur = conn.cursor()
    
    if analyzed is None:
        cur.execute(
            "SELECT id, service, level, message, analyzed, analysis, created_at FROM logs ORDER BY created_at DESC LIMIT %s",
            (limit,)
        )
    else:
        cur.execute(
            "SELECT id, service, level, message, analyzed, analysis, created_at FROM logs WHERE analyzed=%s ORDER BY created_at DESC LIMIT %s",
            (analyzed, limit)
        )
    
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    return [
        {
            "id": row[0],
            "service": row[1],
            "level": row[2],
            "message": row[3],
            "analyzed": row[4],
            "analysis": row[5],
            "created_at": str(row[6])
        }
        for row in rows
    ]


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    """HTML dashboard to view logs and analysis in browser"""
    conn = get_conn()
    cur = conn.cursor()
    
    # Get latest analyzed logs
    cur.execute("""
        SELECT id, service, level, message, analysis, created_at 
        FROM logs 
        WHERE analyzed = true 
        ORDER BY created_at DESC 
        LIMIT 20
    """)
    
    analyzed_rows = cur.fetchall()
    
    # Get unanalyzed logs
    cur.execute("""
        SELECT id, service, level, message, created_at 
        FROM logs 
        WHERE analyzed = false 
        ORDER BY created_at DESC 
        LIMIT 10
    """)
    
    unanalyzed_rows = cur.fetchall()
    cur.close()
    conn.close()
    
    # Build HTML
    analyzed_html = ""
    for row in analyzed_rows:
        analyzed_html += f"""
        <div class="log-card analyzed">
            <div class="log-header">
                <span class="service">{row[1]}</span>
                <span class="level {row[2].lower()}">{row[2]}</span>
                <span class="timestamp">{row[5]}</span>
            </div>
            <div class="log-message"><strong>Message:</strong> {row[3]}</div>
            <div class="log-analysis"><strong>Analysis:</strong><pre>{row[4]}</pre></div>
        </div>
        """
    
    unanalyzed_html = ""
    for row in unanalyzed_rows:
        unanalyzed_html += f"""
        <div class="log-card unanalyzed">
            <div class="log-header">
                <span class="service">{row[1]}</span>
                <span class="level {row[2].lower()}">{row[2]}</span>
                <span class="timestamp">{row[4]}</span>
            </div>
            <div class="log-message"><strong>Message:</strong> {row[3]}</div>
            <div class="analyzing">🔄 Analyzing...</div>
        </div>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Log Analyzer - Dashboard</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: #0f172a;
                color: #e2e8f0;
                padding: 20px;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
            }}
            h1 {{
                text-align: center;
                margin-bottom: 30px;
                color: #3b82f6;
            }}
            .section {{
                margin-bottom: 40px;
            }}
            .section h2 {{
                font-size: 20px;
                margin-bottom: 15px;
                color: #60a5fa;
                border-bottom: 2px solid #1e40af;
                padding-bottom: 10px;
            }}
            .log-card {{
                background: #1e293b;
                border-left: 4px solid #3b82f6;
                border-radius: 6px;
                padding: 15px;
                margin-bottom: 12px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            }}
            .log-card.analyzed {{
                border-left-color: #10b981;
            }}
            .log-card.unanalyzed {{
                border-left-color: #f59e0b;
                opacity: 0.7;
            }}
            .log-header {{
                display: flex;
                gap: 12px;
                margin-bottom: 10px;
                flex-wrap: wrap;
            }}
            .service {{
                background: #3b82f6;
                padding: 4px 10px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }}
            .level {{
                padding: 4px 10px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }}
            .level.error {{ background: #ef4444; }}
            .level.warning {{ background: #f59e0b; }}
            .level.info {{ background: #06b6d4; }}
            .level.debug {{ background: #8b5cf6; }}
            .timestamp {{
                color: #94a3b8;
                font-size: 12px;
                margin-left: auto;
            }}
            .log-message {{
                margin: 8px 0;
                padding: 8px;
                background: rgba(0,0,0,0.2);
                border-radius: 4px;
                font-size: 14px;
            }}
            .log-analysis {{
                margin-top: 10px;
                padding: 10px;
                background: rgba(16, 185, 129, 0.1);
                border-left: 3px solid #10b981;
                border-radius: 4px;
            }}
            .log-analysis pre {{
                white-space: pre-wrap;
                word-wrap: break-word;
                font-size: 12px;
                margin-top: 5px;
                font-family: 'Courier New', monospace;
            }}
            .analyzing {{
                color: #f59e0b;
                font-size: 14px;
                font-weight: bold;
                text-align: center;
                padding: 10px;
            }}
            .refresh {{
                text-align: center;
                margin-top: 30px;
                font-size: 12px;
                color: #64748b;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔍 AI Log Analyzer Dashboard</h1>
            
            <div class="section">
                <h2>✅ Analyzed Logs ({len(analyzed_rows)})</h2>
                {analyzed_html if analyzed_html else '<p style="color: #64748b;">No analyzed logs yet</p>'}
            </div>
            
            <div class="section">
                <h2>⏳ Analyzing ({len(unanalyzed_rows)})</h2>
                {unanalyzed_html if unanalyzed_html else '<p style="color: #64748b;">All logs analyzed!</p>'}
            </div>
            
            <div class="refresh">
                🔄 Refresh page to see updates (Worker processes logs every 10 seconds)
            </div>
        </div>
        <script>
            // Auto-refresh every 10 seconds
            setTimeout(() => location.reload(), 10000);
        </script>
    </body>
    </html>
    """
    
    return html
