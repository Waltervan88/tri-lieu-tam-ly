"""
Unit tests for app/data/db.py
"""

import pytest
import sys, os, tempfile, sqlite3

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ─── Test DB setup ────────────────────────────────────────────────────────────
# Override DB_PATH to use a temp file so tests don't touch real data

import app.data.db as _db

_original_path = _db.DB_PATH


@pytest.fixture(autouse=True)
def _patch_db(monkeypatch):
    """Replace DB_PATH with a temp file for every test."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        monkeypatch.setattr(_db, "DB_PATH", f.name)
    # Initialise schema on the temp db
    _db.init_db()
    yield
    # Cleanup
    try:
        os.unlink(_db.DB_PATH)
    except OSError:
        pass


# ─── User tests ──────────────────────────────────────────────────────────────

def test_create_and_get_user():
    uid = _db.create_user(
        email="alice@test.local",
        name="Alice",
        password_hash="$2b$12$fake.hash",
        role="user",
    )
    assert uid["email"] == "alice@test.local"
    assert uid["role"] == "user"

    user = _db.get_user_by_email("alice@test.local")
    assert user is not None
    assert user["name"] == "Alice"
    assert user["active"] == 1


def test_get_user_by_id():
    uid = _db.create_user("bob@test.local", "Bob", "hash", "expert")
    user = _db.get_user_by_id(uid["id"])
    assert user["name"] == "Bob"


def test_lock_user():
    uid = _db.create_user("carol@test.local", "Carol", "hash", "user")
    _db.lock_user(uid["id"], locked_by="gate_d")
    user = _db.get_user_by_id(uid["id"])
    assert user["active"] == 0
    assert user["locked_by"] == "gate_d"


def test_init_user_progress():
    uid = _db.create_user("dave@test.local", "Dave", "hash")
    _db.init_user_progress(uid["id"])
    progress = _db.load_user_progress(uid["id"])
    assert progress["h_presence"] == 5.0
    assert progress["g_awareness"] == ""


# ─── Session tests ────────────────────────────────────────────────────────────

def test_create_and_get_session():
    uid = _db.create_user("eve@test.local", "Eve", "hash")
    import uuid
    sid = str(uuid.uuid4())
    _db.create_session(sid, uid["id"])
    sess = _db.get_session(sid)
    assert sess["user_id"] == uid["id"]
    assert sess["current_w"] == "W1"


def test_update_session_step():
    uid = _db.create_user("frank@test.local", "Frank", "hash")
    import uuid
    sid = str(uuid.uuid4())
    _db.create_session(sid, uid["id"])
    _db.update_session_step(sid, "W3", "B")
    sess = _db.get_session(sid)
    assert sess["current_w"] == "W3"
    assert sess["current_mode"] == "B"


def test_user_sessions_list():
    uid = _db.create_user("greg@test.local", "Greg", "hash")
    import uuid
    for _ in range(3):
        _db.create_session(str(uuid.uuid4()), uid["id"])
    sessions = _db.get_user_sessions(uid["id"])
    assert len(sessions) == 3


# ─── Message tests ───────────────────────────────────────────────────────────

def test_save_and_get_messages():
    uid = _db.create_user("iris@test.local", "Iris", "hash")
    import uuid
    sid = str(uuid.uuid4())
    _db.create_session(sid, uid["id"])
    _db.save_message(sid, "user", "Tôi cảm thấy mệt mỏi.", "C", "W2")
    _db.save_message(sid, "assistant", "Bạn có thể nói thêm về điều đó không?", "C", "W2")
    msgs = _db.get_session_messages(sid)
    assert len(msgs) == 2
    assert msgs[0]["role"] == "user"
    assert msgs[1]["role"] == "assistant"


# ─── Snapshot tests ───────────────────────────────────────────────────────────

def test_save_and_get_snapshot():
    uid = _db.create_user("jack@test.local", "Jack", "hash")
    import uuid
    sid = str(uuid.uuid4())
    _db.create_session(sid, uid["id"])
    _db.save_snapshot(sid, "W2", {"C": "đau đầu, mất ngủ"}, "raw output here")
    snap = _db.get_latest_snapshot(sid)
    import json
    assert json.loads(snap["channel_data"])["C"] == "đau đầu, mất ngủ"


# ─── Homework tests ──────────────────────────────────────────────────────────

def test_insert_and_fetch_homework():
    uid = _db.create_user("kate@test.local", "Kate", "hash")
    import uuid
    sid = str(uuid.uuid4())
    _db.create_session(sid, uid["id"])
    _db.insert_homework(uid["id"], sid, "Thực hành hít thở sâu 5 phút", "primary", "NHỊP")
    pending = _db.get_pending_homework(uid["id"])
    assert len(pending) == 1
    assert pending[0]["action_letter"] == "NHỊP"

    _db.mark_homework_done(pending[0]["id"], "Đã làm 3 lần trong tuần")
    completed = _db.get_completed_homework(uid["id"])
    assert len(completed) == 1
    assert completed[0]["report"] == "Đã làm 3 lần trong tuần"


# ─── Gate D event tests ──────────────────────────────────────────────────────

def test_save_and_get_gate_d_event():
    uid = _db.create_user("leo@test.local", "Leo", "hash")
    import uuid
    sid = str(uuid.uuid4())
    _db.create_session(sid, uid["id"])
    event_id = _db.save_gate_d_event(sid, uid["id"], "suicide", "tôi muốn tự tử")
    events = _db.get_gate_d_events()
    assert len(events) >= 1
    assert events[0]["reason"] == "suicide"


# ─── Dashboard stats tests ────────────────────────────────────────────────────

def test_dashboard_stats():
    uid = _db.create_user("mia@test.local", "Mia", "hash")
    _db.init_user_progress(uid["id"])
    import uuid
    sid = str(uuid.uuid4())
    _db.create_session(sid, uid["id"])
    _db.update_session_step(sid, "W5", "B")
    stats = _db.get_dashboard_stats()
    assert "active_users" in stats
    assert "sessions_by_w" in stats
    assert "sessions_by_mode" in stats
    assert stats["sessions_by_w"].get("W5") == 1


# ─── Progress update tests ────────────────────────────────────────────────────

def test_update_user_progress():
    uid = _db.create_user("noah@test.local", "Noah", "hash")
    _db.init_user_progress(uid["id"])
    _db.update_user_progress(uid["id"], {
        "c_raw": "cảm thấy cô đơn",
        "h_presence": 3.5,
        "f_khat_chhet": 1,
    })
    progress = _db.load_user_progress(uid["id"])
    assert "cảm thấy cô đơn" in progress["c_raw"]
    assert progress["h_presence"] == 3.5
    assert progress["f_khat_chhet"] == 1
