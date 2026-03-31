#!/usr/bin/env python3
"""
Run this ONCE in your project root to fix the database.
python fix_db.py
"""
import sqlite3, os

DB_FILE = os.getenv("DB_FILE", "users.db")

if not os.path.exists(DB_FILE):
    print(f"❌ {DB_FILE} not found. Start your server first, then run this.")
    exit(1)

with sqlite3.connect(DB_FILE) as conn:
    # Add column if missing
    try:
        conn.execute("ALTER TABLE users ADD COLUMN saved_schemes TEXT DEFAULT '[]'")
        conn.commit()
        print("✓ Added saved_schemes column")
    except sqlite3.OperationalError:
        print("✓ saved_schemes column already exists")
    
    # Verify
    cols = [r[1] for r in conn.execute("PRAGMA table_info(users)").fetchall()]
    print(f"✓ Columns now: {cols}")

print("\nDone. Restart your server: python mainm.py")
