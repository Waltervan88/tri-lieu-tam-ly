"""
SQLite database setup and connection helpers for Tri-Lieu-Tam-Ly.
Schema: users, expert_prompts, therapy_sessions, session_messages,
        session_state_snapshots, homework, user_progress, gate_d_events.
"""

import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# ─── Path ───────────────────────────────────────────────────────────────────

DB_PATH = Path(__file__).parent.parent.parent / "data" / "therapy.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# ─── Connection ──────────────────────────────────────────────────────────────

def get_db() -> sqlite3.Connection:
    """Return a writable connection with row factory."""
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_db_readonly() -> sqlite3.Connection:
    """Return a read-only connection for dashboard queries."""
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


# ─── Schema Init ─────────────────────────────────────────────────────────────

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id            TEXT PRIMARY KEY,
    email         TEXT UNIQUE NOT NULL,
    name          TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL DEFAULT 'user',
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    locked_at     DATETIME,
    locked_by     TEXT,
    active        INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS expert_prompts (
    id          TEXT PRIMARY KEY,
    prompt_key  TEXT NOT NULL,
    version     INTEGER NOT NULL,
    content     TEXT NOT NULL,
    created_by  TEXT NOT NULL,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active   INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS therapy_sessions (
    id                  TEXT PRIMARY KEY,
    user_id             TEXT NOT NULL,
    started_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    ended_at            DATETIME,
    current_w           TEXT NOT NULL DEFAULT 'W1',
    current_mode        TEXT,
    gate_d_triggered    INTEGER DEFAULT 0,
    session_summary     TEXT,
    output_6a           TEXT,
    homework_json       TEXT,
    indicators_json     TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS session_messages (
    id          TEXT PRIMARY KEY,
    session_id  TEXT NOT NULL,
    role        TEXT NOT NULL,
    content     TEXT NOT NULL,
    channel     TEXT,
    w_step      TEXT,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES therapy_sessions(id)
);

CREATE TABLE IF NOT EXISTS session_state_snapshots (
    id              TEXT PRIMARY KEY,
    session_id      TEXT NOT NULL,
    w_step          TEXT NOT NULL,
    channel_data    TEXT NOT NULL,
    raw_llm_output  TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES therapy_sessions(id)
);

CREATE TABLE IF NOT EXISTS homework (
    id             TEXT PRIMARY KEY,
    user_id        TEXT NOT NULL,
    session_id     TEXT NOT NULL,
    assignment     TEXT NOT NULL,
    dose           TEXT NOT NULL,
    action_letter  TEXT NOT NULL,
    completed      INTEGER DEFAULT 0,
    report         TEXT,
    due_date       DATETIME,
    completed_at   DATETIME,
    created_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (session_id) REFERENCES therapy_sessions(id)
);

CREATE TABLE IF NOT EXISTS user_progress (
    id               TEXT PRIMARY KEY,
    user_id          TEXT UNIQUE NOT NULL,
    c_raw            TEXT,
    d_loops          TEXT,
    e_layers         TEXT,
    f_patterns       TEXT,
    g_awareness      TEXT,
    h_presence       REAL DEFAULT 5.0,
    f_khat_chhet     INTEGER DEFAULT 0,
    last_session_id  TEXT,
    updated_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS gate_d_events (
    id           TEXT PRIMARY KEY,
    session_id   TEXT NOT NULL,
    user_id      TEXT NOT NULL,
    reason       TEXT NOT NULL,
    trigger_text TEXT,
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sessions_user   ON therapy_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_session ON session_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_snapshots_session ON session_state_snapshots(session_id, w_step);
CREATE INDEX IF NOT EXISTS idx_homework_user    ON homework(user_id, completed);
CREATE INDEX IF NOT EXISTS idx_prompts_active   ON expert_prompts(prompt_key, is_active);
CREATE INDEX IF NOT EXISTS idx_gate_d_user      ON gate_d_events(user_id);
"""


def init_db() -> None:
    """Create all tables. Safe to call multiple times."""
    conn = get_db()
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    conn.close()


def seed_demo_users() -> None:
    """
    Seed one expert and one admin account for demo purposes.
    Passwords are plain-text placeholders — replace before production.
    """
    import bcrypt

    conn = get_db()
    cur = conn.cursor()

    # Demo expert
    expert_hash = bcrypt.hashpw("expert123".encode(), bcrypt.gensalt()).decode()
    cur.execute(
        "INSERT OR IGNORE INTO users (id,email,name,password_hash,role) VALUES (?,?,?,?,?)",
        (str(uuid.uuid4()), "expert@demo.local", "Dr. Expert", expert_hash, "expert"),
    )

    # Demo admin
    admin_hash = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
    cur.execute(
        "INSERT OR IGNORE INTO users (id,email,name,password_hash,role) VALUES (?,?,?,?,?)",
        (str(uuid.uuid4()), "admin@demo.local", "Admin Demo", admin_hash, "admin"),
    )

    conn.commit()
    conn.close()


# ─── User helpers ────────────────────────────────────────────────────────────

def get_user_by_email(email: str) -> dict | None:
    conn = get_db()
    cur = conn.execute(
        "SELECT * FROM users WHERE email = ? AND active = 1", (email,)
    )
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_id(uid: str) -> dict | None:
    conn = get_db()
    cur = conn.execute("SELECT * FROM users WHERE id = ?", (uid,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def create_user(email: str, name: str, password_hash: str, role: str = "user") -> dict:
    conn = get_db()
    uid = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO users (id,email,name,password_hash,role) VALUES (?,?,?,?,?)",
        (uid, email, name, password_hash, role),
    )
    conn.commit()
    conn.close()
    return {"id": uid, "email": email, "name": name, "role": role}


def lock_user(uid: str, locked_by: str) -> None:
    conn = get_db()
    conn.execute(
        "UPDATE users SET active=0, locked_at=?, locked_by=? WHERE id=?",
        (datetime.now().isoformat(), locked_by, uid),
    )
    conn.commit()
    conn.close()


def init_user_progress(uid: str) -> None:
    """Seed empty progress row for a new user."""
    conn = get_db()
    conn.execute(
        "INSERT OR IGNORE INTO user_progress (id,user_id) VALUES (?,?)",
        (str(uuid.uuid4()), uid),
    )
    conn.commit()
    conn.close()


# ─── Session helpers ─────────────────────────────────────────────────────────

def create_session(session_id: str, user_id: str) -> None:
    conn = get_db()
    conn.execute(
        "INSERT INTO therapy_sessions (id,user_id) VALUES (?,?)",
        (session_id, user_id),
    )
    conn.commit()
    conn.close()


def update_session_step(session_id: str, current_w: str, current_mode: str) -> None:
    conn = get_db()
    conn.execute(
        "UPDATE therapy_sessions SET current_w=?, current_mode=? WHERE id=?",
        (current_w, current_mode, session_id),
    )
    conn.commit()
    conn.close()


def update_session_output(
    session_id: str,
    session_summary: str,
    output_6a: str,
    homework_json: str,
    indicators_json: str,
) -> None:
    conn = get_db()
    conn.execute(
        """UPDATE therapy_sessions
           SET ended_at=?, session_summary=?, output_6a=?,
               homework_json=?, indicators_json=?
           WHERE id=?""",
        (
            datetime.now().isoformat(),
            session_summary,
            output_6a,
            homework_json,
            indicators_json,
            session_id,
        ),
    )
    conn.commit()
    conn.close()


def trigger_gate_d(user_id: str, session_id: str, reason: str,
                 trigger_text: str = "") -> None:
    """
    Hard-stop Gate D: lock user + save audit event.
    Signature must match the call from session_machine.py.
    """
    lock_user(user_id, locked_by="gate_d")
    save_gate_d_event(session_id, user_id, reason, trigger_text)


def get_session(session_id: str) -> dict | None:
    conn = get_db()
    cur = conn.execute("SELECT * FROM therapy_sessions WHERE id=?", (session_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_sessions(user_id: str, limit: int = 20) -> list[dict]:
    conn = get_db()
    cur = conn.execute(
        """SELECT * FROM therapy_sessions
           WHERE user_id=? ORDER BY started_at DESC LIMIT ?""",
        (user_id, limit),
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─── Message helpers ─────────────────────────────────────────────────────────

def save_message(session_id: str, role: str, content: str,
                 channel: str | None, w_step: str | None) -> str:
    msg_id = str(uuid.uuid4())
    conn = get_db()
    conn.execute(
        "INSERT INTO session_messages (id,session_id,role,content,channel,w_step) VALUES (?,?,?,?,?,?)",
        (msg_id, session_id, role, content, channel, w_step),
    )
    conn.commit()
    conn.close()
    return msg_id


def get_session_messages(session_id: str) -> list[dict]:
    conn = get_db()
    cur = conn.execute(
        "SELECT * FROM session_messages WHERE session_id=? ORDER BY created_at ASC",
        (session_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─── Snapshot helpers ────────────────────────────────────────────────────────

def save_snapshot(session_id: str, w_step: str,
                  channel_data: dict, raw_llm_output: str = "") -> None:
    import json
    conn = get_db()
    conn.execute(
        "INSERT INTO session_state_snapshots (id,session_id,w_step,channel_data,raw_llm_output) VALUES (?,?,?,?,?)",
        (str(uuid.uuid4()), session_id, w_step, json.dumps(channel_data), raw_llm_output),
    )
    conn.commit()
    conn.close()


def get_latest_snapshot(session_id: str) -> dict | None:
    conn = get_db()
    cur = conn.execute(
        """SELECT * FROM session_state_snapshots
           WHERE session_id=? ORDER BY created_at DESC LIMIT 1""",
        (session_id,),
    )
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


# ─── User progress helpers ────────────────────────────────────────────────────

def load_user_progress(user_id: str) -> dict:
    """Return progress row or a default empty dict if none exists."""
    conn = get_db()
    cur = conn.execute("SELECT * FROM user_progress WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        d = dict(row)
        # Ensure string fields return "" not None
        str_fields = ["c_raw","d_loops","e_layers","f_patterns","g_awareness"]
        for f in str_fields:
            if d.get(f) is None:
                d[f] = ""
        return d
    return {
        "h_presence": 5.0,
        "g_awareness": "",
        "f_khat_chhet": 0,
        "d_loops": "",
        "e_layers": "",
        "c_raw": "",
        "f_patterns": "",
    }


def update_user_progress(user_id: str, channel_state: dict) -> None:
    """Merge captured channel data into user_progress row."""
    conn = get_db()
    updates = []
    params = []
    allowed = ["c_raw", "d_loops", "e_layers", "f_patterns",
               "g_awareness", "h_presence", "f_khat_chhet"]
    for key in allowed:
        if key in channel_state:
            updates.append(f"{key}=?")
            params.append(str(channel_state[key]))

    if updates:
        updates.append("updated_at=?")
        params.append(datetime.now().isoformat())
        params.append(user_id)
        conn.execute(
            f"UPDATE user_progress SET {','.join(updates)} WHERE user_id=?",
            params,
        )
        conn.commit()
    conn.close()


# ─── Homework helpers ────────────────────────────────────────────────────────

def insert_homework(user_id: str, session_id: str,
                    assignment: str, dose: str, action_letter: str,
                    due_date: str | None = None) -> str:
    hw_id = str(uuid.uuid4())
    conn = get_db()
    if due_date is None:
        due_date = (datetime.now() + timedelta(days=7)).isoformat()
    conn.execute(
        """INSERT INTO homework
           (id,user_id,session_id,assignment,dose,action_letter,due_date)
           VALUES (?,?,?,?,?,?,?)""",
        (hw_id, user_id, session_id, assignment, dose, action_letter, due_date),
    )
    conn.commit()
    conn.close()
    return hw_id


def get_pending_homework(user_id: str) -> list[dict]:
    conn = get_db()
    cur = conn.execute(
        """SELECT * FROM homework
           WHERE user_id=? AND completed=0 ORDER BY due_date ASC""",
        (user_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_completed_homework(user_id: str, limit: int = 20) -> list[dict]:
    conn = get_db()
    cur = conn.execute(
        """SELECT * FROM homework
           WHERE user_id=? AND completed=1 ORDER BY completed_at DESC LIMIT ?""",
        (user_id, limit),
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def mark_homework_done(hw_id: str, report: str = "") -> None:
    conn = get_db()
    conn.execute(
        """UPDATE homework SET completed=1, completed_at=?, report=? WHERE id=?""",
        (datetime.now().isoformat(), report, hw_id),
    )
    conn.commit()
    conn.close()


# ─── Gate D helpers ──────────────────────────────────────────────────────────

def save_gate_d_event(session_id: str, user_id: str,
                      reason: str, trigger_text: str) -> str:
    event_id = str(uuid.uuid4())
    conn = get_db()
    conn.execute(
        "INSERT INTO gate_d_events (id,session_id,user_id,reason,trigger_text) VALUES (?,?,?,?,?)",
        (event_id, session_id, user_id, reason, trigger_text),
    )
    conn.commit()
    conn.close()
    return event_id


def get_gate_d_events(limit: int = 50) -> list[dict]:
    conn = get_db()
    cur = conn.execute(
        "SELECT * FROM gate_d_events ORDER BY created_at DESC LIMIT ?",
        (limit,),
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─── User Profile & Chat History helpers ──────────────────────────────────────

def get_all_users() -> list[dict]:
    """Return all active users for the profile selector dropdown."""
    conn = get_db()
    cur = conn.execute(
        """SELECT id, email, name, role, created_at, active
           FROM users WHERE active=1 ORDER BY created_at DESC"""
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_sessions(user_id: str) -> list[dict]:
    """Return ALL sessions for a user with no limit — for chat history."""
    conn = get_db()
    cur = conn.execute(
        """SELECT id, started_at, ended_at, current_w, current_mode,
                  gate_d_triggered, session_summary
           FROM therapy_sessions
           WHERE user_id=? ORDER BY started_at DESC""",
        (user_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_user_session_summaries(user_id: str) -> list[dict]:
    """Return session history oldest→newest for trend analysis."""
    conn = get_db()
    cur = conn.execute(
        """SELECT id, started_at, ended_at, current_w, current_mode,
                  session_summary, homework_json
           FROM therapy_sessions
           WHERE user_id=? ORDER BY started_at ASC""",
        (user_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_user_homework_stats(user_id: str) -> dict:
    """Return homework completion stats for a user."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM homework WHERE user_id=?", (user_id,))
    total = cur.fetchone()[0]
    cur.execute(
        "SELECT COUNT(*) FROM homework WHERE user_id=? AND completed=1", (user_id,)
    )
    completed = cur.fetchone()[0]
    conn.close()
    return {
        "total": total,
        "completed": completed,
        "pending": total - completed,
        "completion_rate": round(completed / total * 100, 1) if total > 0 else 0.0,
    }


# ─── Dashboard helpers ───────────────────────────────────────────────────────

def get_dashboard_stats() -> dict:
    conn = get_db()
    cur = conn.cursor()

    # Active users (7-day)
    seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
    cur.execute(
        "SELECT COUNT(*) FROM users WHERE active=1 AND created_at>=?",
        (seven_days_ago,),
    )
    active_users = cur.fetchone()[0]

    # Sessions today
    today = datetime.now().date().isoformat()
    cur.execute(
        "SELECT COUNT(*) FROM therapy_sessions WHERE date(started_at)=?",
        (today,),
    )
    sessions_today = cur.fetchone()[0]

    # Avg H-level
    cur.execute("SELECT AVG(h_presence) FROM user_progress")
    avg_h = cur.fetchone()[0] or 0.0

    # Gate D events (30-day)
    thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
    cur.execute(
        "SELECT COUNT(*) FROM gate_d_events WHERE created_at>=?",
        (thirty_days_ago,),
    )
    gate_d_count = cur.fetchone()[0]

    # Sessions by W-step
    cur.execute(
        """SELECT current_w, COUNT(*) as cnt
           FROM therapy_sessions GROUP BY current_w"""
    )
    by_w = {r["current_w"]: r["cnt"] for r in cur.fetchall()}

    # Mode distribution
    cur.execute(
        """SELECT current_mode, COUNT(*) as cnt
           FROM therapy_sessions WHERE current_mode IS NOT NULL
           GROUP BY current_mode"""
    )
    by_mode = {r["current_mode"]: r["cnt"] for r in cur.fetchall()}

    conn.close()
    return {
        "active_users": active_users,
        "sessions_today": sessions_today,
        "avg_h": round(avg_h, 1),
        "gate_d_count": gate_d_count,
        "sessions_by_w": by_w,
        "sessions_by_mode": by_mode,
    }
