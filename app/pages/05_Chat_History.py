"""
Chat History page — user can browse all past sessions and read full conversations.
Security: user sees ONLY role + content + created_at.
Hidden: channel, w_step, raw C-H data.
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import app.data.db as db
from app.auth import get_user_from_session

st.set_page_config(page_title="Lịch Sử Phiên", page_icon="📜")

# ─── Auth guard ───────────────────────────────────────────────────────────────

if not st.session_state.get("user"):
    st.warning("Vui lòng đăng nhập trước.")
    st.switch_page("pages/00_Login.py")

user = get_user_from_session(st.session_state.user)
if not user:
    st.error("Phiên đăng nhập đã hết hạn.")
    st.session_state.user = None
    st.rerun()

# ─── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### 📜 Lịch Sử Phiên")
    st.markdown(f"**Người dùng:** {user['name']}")
    st.markdown(f"**Email:** {user['email']}")
    st.markdown("---")
    if st.button("💬 Buổi Trị liệu", use_container_width=True):
        st.switch_page("pages/01_Therapy_Chat.py")
    if st.button("📋 Bài tập về nhà", use_container_width=True):
        st.switch_page("pages/02_Homework.py")
    st.markdown("---")
    if st.button("🚪 Đăng xuất", use_container_width=True):
        st.session_state.user = None
        st.switch_page("pages/00_Login.py")

# ─── Load all sessions ────────────────────────────────────────────────────────

sessions = db.get_all_sessions(user["id"])

st.markdown("## 📜 Lịch Sử Phiên")
st.caption(f"Tổng cộng: {len(sessions)} phiên")

if not sessions:
    st.info("Bạn chưa có phiên nào. Bắt đầu một buổi trị liệu mới.")
    if st.button("💬 Bắt đầu buổi trị liệu"):
        st.switch_page("pages/01_Therapy_Chat.py")
    st.stop()

# ─── Session selector ─────────────────────────────────────────────────────────

def format_session(s: dict) -> str:
    """Format a session for the radio selector."""
    date = s.get("started_at", "?")
    date_str = date[:10] if date else "?"
    w = s.get("current_w", "?")
    mode = s.get("current_mode", "?")
    summary = s.get("session_summary") or ""
    summary_short = summary[:50] if summary else ""

    # Status badge
    if s.get("gate_d_triggered"):
        badge = "⚠️"
    elif s.get("ended_at"):
        badge = "✅"
    else:
        badge = "🔴"

    return f"{badge} {date_str} · {w} · Mode {mode} · {summary_short}"

options = [format_session(s) for s in sessions]
idx = st.radio("Chọn phiên để xem:", options, label_visibility="collapsed")

# Find selected session
selected_idx = options.index(idx)
selected_session = sessions[selected_idx]

# ─── Session header ───────────────────────────────────────────────────────────

sid = selected_session["id"]
session_messages = db.get_session_messages(sid)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Bước", selected_session.get("current_w", "—"))
col2.metric("Mode", selected_session.get("current_mode", "—"))
col3.metric(
    "Trạng thái",
    "⚠️ Đã dừng" if selected_session.get("gate_d_triggered")
    else ("✅ Hoàn tất" if selected_session.get("ended_at") else "🔴 Đang dở")
)
col4.metric("Tin nhắn", len(session_messages))

if selected_session.get("session_summary"):
    with st.expander("📝 Tóm tắt phiên"):
        st.markdown(selected_session["session_summary"])

st.divider()

# ─── Chat messages ────────────────────────────────────────────────────────────
# SECURITY: Only render role + content + created_at.
# Hidden from user: channel, w_step, raw C-H data.

st.markdown("### 💬 Nội dung cuộc trò chuyện")

if not session_messages:
    st.info("Phiên này chưa có tin nhắn nào.")
else:
    for msg in session_messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        created_at = msg.get("created_at", "")
        time_str = created_at[11:16] if len(created_at) > 16 else ""

        with st.chat_message(role):
            st.markdown(content)
            st.caption(f"{time_str}")

st.divider()

# ─── Navigation ───────────────────────────────────────────────────────────────

col_prev, col_next = st.columns(2)
if selected_idx > 0:
    col_prev.button("⬅️ Phiên trước", use_container_width=True, key="prev_sess")
if selected_idx < len(sessions) - 1:
    col_next.button("Phiên sau ➡️", use_container_width=True, key="next_sess")

if st.button("💬 Quay lại buổi trị liệu", use_container_width=True):
    st.switch_page("pages/01_Therapy_Chat.py")
