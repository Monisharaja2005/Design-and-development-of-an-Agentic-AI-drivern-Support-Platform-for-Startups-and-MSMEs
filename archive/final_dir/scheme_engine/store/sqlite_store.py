from __future__ import annotations

import sqlite3
import time


class SqliteStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self._init_schema()

    def _init_schema(self):
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY,
                name TEXT,
                url TEXT UNIQUE,
                category TEXT,
                tags TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS pages (
                id INTEGER PRIMARY KEY,
                source_id INTEGER,
                url TEXT UNIQUE,
                content_type TEXT,
                title TEXT,
                text TEXT,
                text_hash TEXT,
                created_at INTEGER
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS schemes (
                id INTEGER PRIMARY KEY,
                page_id INTEGER,
                source_id INTEGER,
                name TEXT,
                summary TEXT,
                eligibility TEXT,
                benefits TEXT,
                application TEXT,
                documents TEXT,
                geography TEXT,
                confidence REAL,
                fingerprint TEXT UNIQUE,
                created_at INTEGER
            )
            """
        )
        self.conn.commit()

    def upsert_source(self, name: str, url: str, category: str, tags: list[str]):
        tags_str = ",".join(tags or [])
        cur = self.conn.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO sources (name, url, category, tags) VALUES (?, ?, ?, ?)",
            (name, url, category, tags_str),
        )
        self.conn.commit()
        cur.execute("SELECT id FROM sources WHERE url = ?", (url,))
        row = cur.fetchone()
        return row[0] if row else None

    def insert_page(self, source_id: int, url: str, content_type: str, title: str, text: str, text_hash: str):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO pages (source_id, url, content_type, title, text, text_hash, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (source_id, url, content_type, title, text, text_hash, int(time.time())),
        )
        self.conn.commit()
        cur.execute("SELECT id FROM pages WHERE url = ?", (url,))
        row = cur.fetchone()
        return row[0] if row else None

    def insert_scheme(self, page_id: int, source_id: int, scheme: dict, fingerprint: str):
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT OR IGNORE INTO schemes
            (page_id, source_id, name, summary, eligibility, benefits, application, documents, geography, confidence, fingerprint, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                page_id,
                source_id,
                scheme.get("name"),
                scheme.get("summary"),
                scheme.get("eligibility"),
                scheme.get("benefits"),
                scheme.get("application"),
                scheme.get("documents"),
                scheme.get("geography"),
                scheme.get("confidence"),
                fingerprint,
                int(time.time()),
            ),
        )
        self.conn.commit()
