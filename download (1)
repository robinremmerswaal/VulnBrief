"""
SQLite-opslag voor VulnBrief.

Alles staat in één database.py zodat de opzet overzichtelijk blijft voor
een klein project als dit. Geen ORM nodig voor dit volume.
"""
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, date

DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), "..", "data", "app.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    notes TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    finding_name TEXT NOT NULL,
    severity TEXT NOT NULL,
    hosts TEXT DEFAULT '',
    age_days INTEGER DEFAULT 0,
    cvss_score REAL,
    vpr_score REAL,
    solution TEXT DEFAULT '',
    cves TEXT DEFAULT '',
    is_resolved INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS previous_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    meeting_date TEXT NOT NULL,
    raw_text TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS action_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    previous_note_id INTEGER NOT NULL REFERENCES previous_notes(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open'
);

CREATE TABLE IF NOT EXISTS briefings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    generated_at TEXT NOT NULL,
    content_markdown TEXT NOT NULL,
    input_snapshot TEXT DEFAULT ''
);
"""


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with get_conn() as conn:
        conn.executescript(SCHEMA)


# --- Clients ---

def create_client(name: str, notes: str = "") -> int:
    with get_conn() as conn:
        cur = conn.execute("INSERT INTO clients (name, notes) VALUES (?, ?)", (name, notes))
        return cur.lastrowid


def list_clients():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM clients ORDER BY name").fetchall()
        return [dict(r) for r in rows]


def get_client(client_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()
        return dict(row) if row else None


# --- Findings ---

def add_finding(client_id: int, finding_name: str, severity: str, hosts: str,
                 age_days: int, cvss_score: float | None, vpr_score: float | None,
                 solution: str, cves: str) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO findings
               (client_id, finding_name, severity, hosts, age_days, cvss_score, vpr_score, solution, cves)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (client_id, finding_name, severity, hosts, age_days, cvss_score, vpr_score, solution, cves),
        )
        return cur.lastrowid


def list_findings(client_id: int, only_open: bool = False):
    with get_conn() as conn:
        query = "SELECT * FROM findings WHERE client_id = ?"
        if only_open:
            query += " AND is_resolved = 0"
        query += " ORDER BY CASE severity WHEN 'Critical' THEN 0 WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END, age_days DESC"
        rows = conn.execute(query, (client_id,)).fetchall()
        return [dict(r) for r in rows]


def set_finding_resolved(finding_id: int, resolved: bool):
    with get_conn() as conn:
        conn.execute("UPDATE findings SET is_resolved = ? WHERE id = ?", (1 if resolved else 0, finding_id))


def delete_finding(finding_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM findings WHERE id = ?", (finding_id,))


# --- Previous meeting notes + action items ---

def add_previous_note(client_id: int, meeting_date: str, raw_text: str) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO previous_notes (client_id, meeting_date, raw_text) VALUES (?, ?, ?)",
            (client_id, meeting_date, raw_text),
        )
        return cur.lastrowid


def add_action_item(previous_note_id: int, text: str, status: str = "open") -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO action_items (previous_note_id, text, status) VALUES (?, ?, ?)",
            (previous_note_id, text, status),
        )
        return cur.lastrowid


def set_action_item_status(item_id: int, status: str):
    with get_conn() as conn:
        conn.execute("UPDATE action_items SET status = ? WHERE id = ?", (status, item_id))


def get_latest_previous_note(client_id: int):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM previous_notes WHERE client_id = ? ORDER BY meeting_date DESC LIMIT 1",
            (client_id,),
        ).fetchone()
        if not row:
            return None
        note = dict(row)
        items = conn.execute(
            "SELECT * FROM action_items WHERE previous_note_id = ? ORDER BY id", (note["id"],)
        ).fetchall()
        note["action_items"] = [dict(i) for i in items]
        return note


def list_previous_notes(client_id: int):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM previous_notes WHERE client_id = ? ORDER BY meeting_date DESC", (client_id,)
        ).fetchall()
        notes = []
        for row in rows:
            note = dict(row)
            items = conn.execute(
                "SELECT * FROM action_items WHERE previous_note_id = ? ORDER BY id", (note["id"],)
            ).fetchall()
            note["action_items"] = [dict(i) for i in items]
            notes.append(note)
        return notes


# --- Briefings ---

def save_briefing(client_id: int, content_markdown: str, input_snapshot: dict) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO briefings (client_id, generated_at, content_markdown, input_snapshot) VALUES (?, ?, ?, ?)",
            (client_id, datetime.utcnow().isoformat(), content_markdown, json.dumps(input_snapshot, default=str)),
        )
        return cur.lastrowid


def list_briefings(limit: int = 100):
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT briefings.*, clients.name AS client_name
               FROM briefings JOIN clients ON clients.id = briefings.client_id
               ORDER BY generated_at DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_briefing(briefing_id: int):
    with get_conn() as conn:
        row = conn.execute(
            """SELECT briefings.*, clients.name AS client_name
               FROM briefings JOIN clients ON clients.id = briefings.client_id
               WHERE briefings.id = ?""",
            (briefing_id,),
        ).fetchone()
        return dict(row) if row else None
