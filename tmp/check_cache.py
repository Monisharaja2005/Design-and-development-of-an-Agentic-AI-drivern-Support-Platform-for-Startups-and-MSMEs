import sqlite3
TRANSLATION_DB = "translations_cache.db"
try:
    with sqlite3.connect(TRANSLATION_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM cache;")
        count = cursor.fetchone()[0]
        print(f"Cache count: {count}")
        cursor.execute("SELECT lang_code, COUNT(*) FROM cache GROUP BY lang_code;")
        rows = cursor.fetchall()
        for row in rows:
            print(f"  {row[0]}: {row[1]}")
except Exception as e:
    print(f"Error: {e}")
