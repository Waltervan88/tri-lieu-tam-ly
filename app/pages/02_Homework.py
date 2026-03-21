"""
Homework Tracker page for users.
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import app.data.db as db
from app.auth import get_user_from_session

st.set_page_config(page_title="Bài Tập Về Nhà", page_icon="📋")

# ─── Auth guard ───────────────────────────────────────────────────────────────

if not st.session_state.get("user"):
    st.warning("Vui lòng đăng nhập trước.")
    st.switch_page("pages/00_Login.py")

user = get_user_from_session(st.session_state.user)
if not user:
    st.error("Phiên đăng nhập đã hết hạn.")
    st.session_state.user = None
    st.rerun()

# ─── Header ──────────────────────────────────────────────────────────────────

st.markdown("## 📋 Bài Tập Về Nhà")

# ─── Load data ────────────────────────────────────────────────────────────────

pending   = db.get_pending_homework(user["id"])
completed = db.get_completed_homework(user["id"], limit=20)
sessions  = db.get_user_sessions(user["id"], limit=10)

# ─── Summary cards ─────────────────────────────────────────────────────────────

col1, col2, col3 = st.columns(3)
col1.metric("Đang chờ", len(pending))
col2.metric("Đã hoàn thành", len(completed))
col3.metric("Tổng buổi", len(sessions))


# ─── Pending homework ─────────────────────────────────────────────────────────

st.markdown("### 🟡 Đang chờ")

if not pending:
    st.info("Không có bài tập đang chờ. Bắt đầu một buổi trị liệu mới để nhận bài tập.")
else:
    for hw in pending:
        action_colors = {
            "NHỊP": "🔵", "SÁNG": "🟡", "NGHĨA": "🟣",
            "THÂN": "🟢", "VIỆC": "🟠", "GẮN": "⚪",
        }
        badge = action_colors.get(hw["action_letter"], "⚪")

        dose_labels = {"primary": "A chính", "secondary": "A phụ", "background": "Nền"}
        dose_label = dose_labels.get(hw["dose"], hw["dose"])

        due_date = hw.get("due_date", "")[:10] if hw.get("due_date") else "—"

        with st.container():
            col_icon, col_text, col_btn = st.columns([1, 8, 2])
            with col_icon:
                st.markdown(f"### {badge}")
            with col_text:
                st.markdown(f"**[{hw['action_letter']}]** — {hw['assignment']}")
                st.caption(f"Dose: {dose_label} · Hạn: {due_date}")
            with col_btn:
                if st.button("✅ Hoàn thành", key=f"done_{hw['id']}"):
                    db.mark_homework_done(hw["id"], "")
                    st.rerun()

        st.markdown("---")


# ─── Completed homework ────────────────────────────────────────────────────────

st.markdown("### ✅ Đã hoàn thành")

if not completed:
    st.info("Chưa có bài tập hoàn thành.")
else:
    for hw in completed[:10]:
        action_colors = {
            "NHỊP": "🔵", "SÁNG": "🟡", "NGHĨA": "🟣",
            "THÂN": "🟢", "VIỆC": "🟠", "GẮN": "⚪",
        }
        badge = action_colors.get(hw["action_letter"], "⚪")
        completed_at = hw.get("completed_at", "")[:10] if hw.get("completed_at") else "—"

        with st.container():
            col_icon, col_text = st.columns([1, 9])
            with col_icon:
                st.markdown(f"{badge}")
            with col_text:
                st.markdown(f"~~**[{hw['action_letter']}]** — {hw['assignment']}~~")
                st.caption(f"Hoàn thành: {completed_at}")
                if hw.get("report"):
                    with st.expander("📝 Báo cáo"):
                        st.text(hw["report"])


# ─── Navigation ────────────────────────────────────────────────────────────────

st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    if st.button("💬 Quay lại buổi trị liệu", use_container_width=True):
        st.switch_page("pages/01_Therapy_Chat.py")
with col2:
    if st.button("🚪 Đăng xuất", use_container_width=True):
        st.session_state.user = None
        st.switch_page("pages/00_Login.py")
