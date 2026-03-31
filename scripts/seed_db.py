import sqlite3
import json

with sqlite3.connect('users.db') as conn:
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            full_name TEXT,
            profile_data TEXT
        )
    ''')
    profile = {
        'businessName': 'Demo Corp', 
        'sector': 'Technology', 
        'state': 'Tamil Nadu', 
        'entityType': 'Private Limited'
    }
    conn.execute(
        "INSERT OR REPLACE INTO users (email, password, full_name, profile_data) VALUES (?, ?, ?, ?)", 
        ('demo@example.com', 'demo1234', 'Demo User', json.dumps(profile))
    )
    conn.commit()
print("Seeded database with demo user.")
