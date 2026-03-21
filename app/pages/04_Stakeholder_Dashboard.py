"""
Stakeholder Dashboard — anonymised aggregate view.
Admin/Expert only. Shows KPIs, session flow, Gate D alerts + User Profiles.
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import app.data.db as db
from app.auth import get_user_from_session, is_at_least

st.set_page_config(page_title="Dashboard", page_icon="📊")

# ─── Auth guard ───────────────────────────────────────────────────────────────

if not st.session_state.get("user"):
    st.warning("Vui lòng đăng nhập trước.")
    st.switch_page("pages/00_Login.py")

user = get_user_from_session(st.session_state.user)
if not user:
    st.error("Phiên đăng nhập đã hết hạn.")
    st.session_state.user = None
    st.rerun()

if not is_at_least(user.get("role", ""), "admin"):
    st.error("⚠️ Chỉ quản trị viên mới có quyền truy cập dashboard.")
    st.stop()

# ─── Load stats ───────────────────────────────────────────────────────────────

stats = db.get_dashboard_stats()
gate_events = db.get_gate_d_events(limit=20)

# ─── Tab layout ────────────────────────────────────────────────────────────────

tabs = st.tabs(["📊 Tổng Quan Hệ Thống", "👤 Hồ Sơ Người Dùng"])

# ════════════════════════════════════════════════════════════════════════════════
# TAB 1: System Overview
# ════════════════════════════════════════════════════════════════════════════════

with tabs[0]:

    st.markdown("## 📊 Dashboard — Tổng Quan Hệ Thống")

    # ─── KPI cards ────────────────────────────────────────────────────────────

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("👥 Người dùng hoạt động (7 ngày)", stats["active_users"])
    kpi2.metric("📅 Phiên hôm nay", stats["sessions_today"])
    kpi3.metric("🧠 H trung bình", f"{stats['avg_h']}/10")
    kpi4.metric("⚠️ Gate D (30 ngày)", stats["gate_d_count"],
                 delta="⚠️ Cảnh báo" if stats["gate_d_count"] > 0 else None,
                 delta_color="inverse")

    st.markdown("---")

    # ─── Sessions by W-step ────────────────────────────────────────────────────

    col_chart, col_mode = st.columns(2)

    with col_chart:
        st.markdown("### 📈 Số phiên theo bước W")
        w_data = stats["sessions_by_w"]
        w_order = ["W1", "W2", "W3", "W4", "W4b", "W5", "W6", "W7", "DONE"]
        w_labels = [w for w in w_order if w in w_data]
        w_values = [w_data[w] for w in w_labels]
        if w_values:
            st.bar_chart({"Bước W": dict(zip(w_labels, w_values))})
        else:
            st.info("Chưa có dữ liệu phiên.")

    with col_mode:
        st.markdown("### 🥧 Phân bố Mode")
        mode_data = stats["sessions_by_mode"]
        if mode_data:
            mode_labels = {
                "A": "Mode A — Triệu chứng",
                "B": "Mode B — Ý nghĩa",
                "C": "Mode C — Tích hợp sâu",
                "E": "Mode E — Quan hệ",
            }
            pie_data = {mode_labels.get(k, k): v for k, v in mode_data.items()}
            st.bar_chart(pie_data)
        else:
            st.info("Chưa có dữ liệu mode.")

    st.markdown("---")

    # ─── Recent sessions (anonymised) ──────────────────────────────────────────

    import pandas as pd

    st.markdown("### 📋 Phiên gần đây (ẩn danh)")

    recent_sessions = []
    conn = db.get_db()
    cur = conn.execute(
        """SELECT s.id, s.started_at, s.current_w, s.current_mode,
                  s.gate_d_triggered, s.session_summary
           FROM therapy_sessions s
           ORDER BY s.started_at DESC LIMIT 20"""
    )
    for row in cur.fetchall():
        recent_sessions.append({
            "session_id": row["id"][:8] + "…",
            "started_at": row["started_at"][:16],
            "W": row["current_w"],
            "Mode": row["current_mode"] or "—",
            "Gate D": "⚠️" if row["gate_d_triggered"] else "✅",
            "Summary": (row["session_summary"] or "—")[:60],
        })
    conn.close()

    if recent_sessions:
        df = pd.DataFrame(recent_sessions)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Chưa có phiên nào.")

    # ─── Gate D Events ─────────────────────────────────────────────────────────

    st.markdown("---")
    with st.expander("⚠️ Sự kiện Gate D (nhạy cảm — chỉ admin)"):
        if gate_events:
            gate_df = pd.DataFrame([
                {
                    "session_id": e["session_id"][:8] + "…",
                    "user_id": e["user_id"][:8] + "…",
                    "reason": e["reason"],
                    "trigger_text": (e["trigger_text"] or "")[:60],
                    "created_at": e["created_at"][:16],
                }
                for e in gate_events
            ])
            st.dataframe(gate_df, use_container_width=True, hide_index=True)
        else:
            st.success("✅ Không có sự kiện Gate D nào trong 30 ngày qua.")

    # ─── Navigation ────────────────────────────────────────────────────────────

    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("💬 Phiên trị liệu", use_container_width=True):
            st.switch_page("pages/01_Therapy_Chat.py")
    with col2:
        if st.button("📝 Sửa prompts", use_container_width=True):
            st.switch_page("pages/03_Expert_Editor.py")
    with col3:
        if st.button("🚪 Đăng xuất", use_container_width=True):
            st.session_state.user = None
            st.switch_page("pages/00_Login.py")

# ════════════════════════════════════════════════════════════════════════════════
# TAB 2: User Profiles (admin/expert only — already gated at top of file)
# ════════════════════════════════════════════════════════════════════════════════

with tabs[1]:

    st.markdown("## 👤 Hồ Sơ Người Dùng")

    # ─── User selector ────────────────────────────────────────────────────────

    users = db.get_all_users()
    if not users:
        st.info("Chưa có người dùng nào trong hệ thống.")
    else:
        # Format for display
        user_options = {
            f"{u['email']} ({u['name'] or '—'}) [{u['role']}]": u["id"]
            for u in users
        }
        selected_label = st.selectbox(
            "Chọn người dùng:",
            options=list(user_options.keys()),
        )
        uid = user_options[selected_label]
        selected_user = next(u for u in users if u["id"] == uid)

        st.markdown("---")

        # ─── Basic info ───────────────────────────────────────────────────────
        col_info1, col_info2, col_info3, col_info4 = st.columns(4)
        col_info1.markdown(f"**Email:**\n{selected_user['email']}")
        col_info2.markdown(f"**Tên:**\n{selected_user['name'] or '—'}")
        col_info3.markdown(f"**Vai trò:**\n{selected_user['role']}")
        col_info4.markdown(
            f"**Ngày tham gia:**\n{selected_user['created_at'][:10]}"
        )

        # ─── Load all profile data ─────────────────────────────────────────────
        progress = db.load_user_progress(uid)
        stats_hw = db.get_user_homework_stats(uid)
        sessions_hw = db.get_user_session_summaries(uid)

        st.markdown("---")

        # ─── H-Presence + Homework Stats ───────────────────────────────────────
        col_h, col_hw1, col_hw2, col_hw3 = st.columns([1, 1, 1, 1])
        h_val = progress.get("h_presence", 5.0)
        col_h.metric("🧠 H-Presence", f"{h_val:.1f}/10")
        col_hw1.metric("📋 Tổng bài tập", stats_hw["total"])
        col_hw2.metric("⏳ Đang chờ", stats_hw["pending"])
        col_hw3.metric(
            "✅ Hoàn thành",
            f"{stats_hw['completion_rate']}%",
            delta="Tốt" if stats_hw["completion_rate"] >= 50 else "Cần cải thiện",
            delta_color="normal" if stats_hw["completion_rate"] >= 50 else "off",
        )

        st.markdown("---")

        # ─── Channel Profile ───────────────────────────────────────────────────
        st.markdown("### 🎯 Hồ Sơ Kênh")

        channel_display = {
            "c_raw":       "C — Hiện tượng",
            "d_loops":     "D — Dòng & Vòng lặp",
            "e_layers":    "E — Tầng & Bậc",
            "f_patterns":  "F — Khuôn lệch",
            "g_awareness": "G — Tỉnh biết",
        }

        for key, label in channel_display.items():
            val = progress.get(key, "") or ""
            with st.expander(f"**{label}**"):
                st.text_area(
                    label="",
                    value=val[:500],
                    disabled=True,
                    label_visibility="collapsed",
                    height=80,
                )

        st.markdown("---")

        # ─── Session History Table ──────────────────────────────────────────────
        st.markdown("### 📋 Lịch Sử Phiên")

        if sessions_hw:
            rows = []
            for s in sessions_hw:
                rows.append({
                    "Ngày":      s.get("started_at", "")[:10],
                    "Bước W":    s.get("current_w", "—"),
                    "Mode":      s.get("current_mode", "—"),
                    "Trạng thái": (
                        "⚠️ Đã dừng" if s.get("gate_d_triggered")
                        else ("✅ Hoàn tất" if s.get("ended_at") else "🔴 Đang dở")
                    ),
                    "Tóm tắt": (s.get("session_summary") or "—")[:80],
                })
            import pandas as pd
            df_sessions = pd.DataFrame(rows)
            st.dataframe(df_sessions, use_container_width=True, hide_index=True)
        else:
            st.info("Người dùng này chưa có phiên nào.")

        # ─── Navigation ────────────────────────────────────────────────────────
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💬 Xem lịch sử chat", use_container_width=True):
                st.switch_page("pages/05_Chat_History.py")
        with col2:
            if st.button("💬 Quay lại buổi trị liệu", use_container_width=True):
                st.switch_page("pages/01_Therapy_Chat.py")
