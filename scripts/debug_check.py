#!/usr/bin/env python3
"""
Run this in your project root to diagnose the save issue.
python debug_check.py
"""
import sqlite3, json, os, sys

DB_FILE = os.getenv("DB_FILE", "users.db")

if not os.path.exists(DB_FILE):
    print(f"❌ users.db not found at: {os.path.abspath(DB_FILE)}")
    print("   → Server has never started, or DB_FILE env var points elsewhere.")
    sys.exit(1)

print(f"✓ Found: {DB_FILE}")

with sqlite3.connect(DB_FILE) as conn:
    # Check columns
    cols = [row[1] for row in conn.execute("PRAGMA table_info(users)").fetchall()]
    print(f"\nColumns in users table: {cols}")
    
    has_saved = 'saved_schemes' in cols
    print(f"{'✓' if has_saved else '❌'} saved_schemes column: {'EXISTS' if has_saved else 'MISSING'}")
    
    if not has_saved:
        print("\n→ FIX: Run this SQL once:")
        print('  ALTER TABLE users ADD COLUMN saved_schemes TEXT DEFAULT \'[]\';')
    
    # Check users
    rows = conn.execute("SELECT email, saved_schemes FROM users").fetchall()
    print(f"\nUsers in DB: {len(rows)}")
    for email, schemes_raw in rows:
        try:
            schemes = json.loads(schemes_raw or '[]')
            print(f"  {email}: {len(schemes)} saved scheme(s)")
            if schemes:
                print(f"    First: {schemes[0].get('scheme_name','?')}")
        except:
            print(f"  {email}: <bad JSON>")

print("\nDone.")
