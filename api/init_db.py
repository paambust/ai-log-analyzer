#!/usr/bin/env python3
"""
Initialize the PostgreSQL database with required tables
This script should run on API startup to ensure tables exist
"""

import psycopg2
from psycopg2 import sql
import os
import time
import sys


def wait_for_db(max_retries=30, retry_delay=2):
    """Wait for database to be ready"""
    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(
                host=os.getenv("DB_HOST"),
                port=int(os.getenv("DB_PORT", 5432)),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                dbname=os.getenv("DB_NAME")
            )
            print("✓ Database connection established")
            return conn
        except psycopg2.OperationalError as e:
            if attempt < max_retries - 1:
                print(f"  Attempt {attempt + 1}/{max_retries} - Waiting for database...")
                time.sleep(retry_delay)
            else:
                print(f"✗ Failed to connect after {max_retries} attempts")
                raise


def create_tables():
    """Create required database tables if they don't exist"""
    conn = wait_for_db()
    cur = conn.cursor()
    
    try:
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
        print("✓ Database tables initialized successfully")
        
    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    try:
        create_tables()
        print("✓ Database initialization complete")
        sys.exit(0)
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        sys.exit(1)
