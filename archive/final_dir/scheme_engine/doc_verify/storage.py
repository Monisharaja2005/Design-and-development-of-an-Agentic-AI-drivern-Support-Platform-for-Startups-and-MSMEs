from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from .models import SchemeAuditEvent, VerificationReport
from .registry import AuthorityRegistry
from .security import EncryptionService


class VerificationStorage:
    def __init__(self, db_path: Path, encryption: EncryptionService):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.encryption = encryption
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS authority_registry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    authority_name TEXT UNIQUE NOT NULL,
                    aliases_json TEXT NOT NULL,
                    domains_json TEXT NOT NULL,
                    document_types_json TEXT NOT NULL,
                    version INTEGER NOT NULL DEFAULT 1
                );

                CREATE TABLE IF NOT EXISTS validation_reports (
                    report_id TEXT PRIMARY KEY,
                    generated_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    authenticity_score REAL NOT NULL,
                    fraud_risk TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    encrypted_payload BLOB NOT NULL
                );

                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    actor_role TEXT NOT NULL,
                    action TEXT NOT NULL,
                    resource_id TEXT,
                    details_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS scheme_audit_events (
                    event_id TEXT PRIMARY KEY,
                    scheme_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    actor_role TEXT NOT NULL,
                    action TEXT NOT NULL,
                    detail TEXT NOT NULL,
                    level TEXT NOT NULL DEFAULT 'info'
                );

                CREATE TABLE IF NOT EXISTS app_users (
                    user_id TEXT PRIMARY KEY,
                    full_name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'verifier',
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )

    def seed_authorities(self, registry: AuthorityRegistry) -> None:
        with self._connect() as conn:
            for record in registry.records:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO authority_registry (
                        authority_name, aliases_json, domains_json, document_types_json, version
                    )
                    VALUES (?, ?, ?, ?, 1)
                    """,
                    (
                        record.authority_name,
                        json.dumps(record.aliases),
                        json.dumps(record.domains),
                        json.dumps(record.document_types),
                    ),
                )

    def save_report(self, report: VerificationReport) -> None:
        payload = report.model_dump_json().encode("utf-8")
        encrypted = self.encryption.encrypt(payload)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO validation_reports (
                    report_id, generated_at, status, authenticity_score, fraud_risk, version, encrypted_payload
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    report.report_id,
                    report.generated_at.isoformat(),
                    report.status.value,
                    report.authenticity_score,
                    report.fraud_risk.value,
                    report.version,
                    encrypted,
                ),
            )

    def get_report(self, report_id: str) -> VerificationReport | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT encrypted_payload FROM validation_reports WHERE report_id = ?",
                (report_id,),
            ).fetchone()
        if not row:
            return None
        decrypted = self.encryption.decrypt(row["encrypted_payload"])
        return VerificationReport.model_validate_json(decrypted.decode("utf-8"))

    def log_audit(self, actor_role: str, action: str, resource_id: str | None, details: dict[str, object]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO audit_logs (created_at, actor_role, action, resource_id, details_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    datetime.now(tz=UTC).isoformat(),
                    actor_role,
                    action,
                    resource_id,
                    json.dumps(details),
                ),
            )

    def add_scheme_audit_event(
        self,
        *,
        scheme_id: str,
        actor_role: str,
        action: str,
        detail: str,
        level: str = "info",
    ) -> SchemeAuditEvent:
        event = SchemeAuditEvent(
            event_id=str(uuid4()),
            scheme_id=scheme_id,
            created_at=datetime.now(tz=UTC),
            actor_role=actor_role,
            action=action,
            detail=detail,
            level=level,
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO scheme_audit_events (
                    event_id, scheme_id, created_at, actor_role, action, detail, level
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_id,
                    event.scheme_id,
                    event.created_at.isoformat(),
                    event.actor_role,
                    event.action,
                    event.detail,
                    event.level,
                ),
            )
        return event

    def list_scheme_audit_events(self, scheme_id: str, limit: int = 200) -> list[SchemeAuditEvent]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT event_id, scheme_id, created_at, actor_role, action, detail, level
                FROM scheme_audit_events
                WHERE scheme_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (scheme_id, max(1, min(limit, 1000))),
            ).fetchall()
        return [
            SchemeAuditEvent(
                event_id=row["event_id"],
                scheme_id=row["scheme_id"],
                created_at=datetime.fromisoformat(row["created_at"]),
                actor_role=row["actor_role"],
                action=row["action"],
                detail=row["detail"],
                level=row["level"],
            )
            for row in rows
        ]

    def create_user(self, *, full_name: str, email: str, password_hash: str, role: str = "verifier") -> dict[str, str]:
        now = datetime.now(tz=UTC).isoformat()
        user_id = str(uuid4())
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO app_users (user_id, full_name, email, password_hash, role, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 1, ?, ?)
                """,
                (user_id, full_name, email.lower(), password_hash, role, now, now),
            )
        return {"user_id": user_id, "full_name": full_name, "email": email.lower(), "role": role}

    def get_user_by_email(self, email: str) -> dict[str, str] | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT user_id, full_name, email, password_hash, role, is_active, created_at, updated_at
                FROM app_users
                WHERE lower(email) = lower(?)
                LIMIT 1
                """,
                (email,),
            ).fetchone()
        if not row:
            return None
        return {
            "user_id": str(row["user_id"]),
            "full_name": str(row["full_name"]),
            "email": str(row["email"]),
            "password_hash": str(row["password_hash"]),
            "role": str(row["role"]),
            "is_active": bool(row["is_active"]),
            "created_at": str(row["created_at"]),
            "updated_at": str(row["updated_at"]),
        }
