from fastapi import FastAPI
import psycopg2
import os

app = FastAPI()

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