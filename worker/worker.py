import time
import psycopg2
import os

def get_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        dbname=os.getenv("DB_NAME")
    )

while True:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT id, message FROM logs WHERE analyzed = false LIMIT 5")
    rows = cur.fetchall()

    for row in rows:
        log_id, message = row

        # fake LLM response (replace later)
        analysis = f"Possible issue detected: {message}"

        cur.execute(
            "UPDATE logs SET analyzed=true, analysis=%s WHERE id=%s",
            (analysis, log_id)
        )

    conn.commit()
    cur.close()
    conn.close()

    time.sleep(5)