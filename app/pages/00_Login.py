"""
Login / Register page for Tri-Lieu-Tam-Ly.
Entry point for all users.
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.data.db import init_db, seed_demo_users
from app.auth import login, register

st.set_page_config(page_title="Đăng nhập — Tri Liệu Tâm Lý", page_icon="🧠")

# ─── Init ───────────────────────────────────────────────────────────────────

def _init():
    init_db()
    seed_demo_users()

_init()


# ─── Session state defaults ───────────────────────────────────────────────────

if "user" not in st.session_state:
    st.session_state.user = None


# ─── Helpers ─────────────────────────────────────────────────────────────────

def go_to_chat():
    st.switch_page("pages/01_Therapy_Chat.py")


def go_dashboard():
    st.switch_page("pages/04_Stakeholder_Dashboard.py")


def go_expert():
    st.switch_page("pages/03_Expert_Editor.py")


# ─── Header ──────────────────────────────────────────────────────────────────

st.markdown("""
<div style="text-align:center; padding: 2rem 0 1rem">
    <h1>🧠 Tri Liệu Tâm Lý</h1>
    <p style="color: #888; font-size: 1rem;">
        Hệ điều hướng hiện tượng sống — sống khớp dài hạn
    </p>
</div>
""", unsafe_allow_html=True)


# ─── Login / Register tabs ───────────────────────────────────────────────────

tab1, tab2 = st.tabs(["Đăng nhập", "Đăng ký"])


with tab1:
    with st.form("login_form"):
        st.markdown("### Đăng nhập")
        email    = st.text_input("Email", placeholder="email@example.com")
        password = st.text_input("Mật khẩu", type="password")

        col1, col2 = st.columns([1, 2])
        with col1:
            submitted = st.form_submit_button("Đăng nhập", type="primary", use_container_width=True)

        if submitted:
            if not email or not password:
                st.error("Vui lòng nhập email và mật khẩu.")
            else:
                user = login(email, password)
                if user:
                    st.session_state.user = user
                    st.success(f"Chào {user['name']}!")
                    st.rerun()
                else:
                    st.error("Email hoặc mật khẩu không đúng.")

    st.markdown("---")
    st.markdown("**Demo accounts:**")
    st.code("Expert: expert@demo.local / expert123")
    st.code("Admin:  admin@demo.local / admin123")


with tab2:
    with st.form("register_form"):
        st.markdown("### Đăng ký tài khoản mới")
        name     = st.text_input("Tên của bạn", placeholder="Nguyễn Văn A")
        email    = st.text_input("Email", placeholder="email@example.com")
        password = st.text_input("Mật khẩu", type="password")
        confirm  = st.text_input("Xác nhận mật khẩu", type="password")

        submitted = st.form_submit_button("Tạo tài khoản", type="primary", use_container_width=True)

        if submitted:
            if not name or not email or not password:
                st.error("Vui lòng điền đầy đủ thông tin.")
            elif password != confirm:
                st.error("Mật khẩu xác nhận không khớp.")
            elif len(password) < 8:
                st.error("Mật khẩu phải có ít nhất 8 ký tự.")
            else:
                try:
                    # Lấy danh sách email được phép từ Secrets
                    allowed_raw = st.secrets.get("ALLOWED_EMAILS", "")
                    allowed_list = [
                        e.strip()
                        for e in str(allowed_raw).split(",")
                        if e.strip()
                    ] if allowed_raw else None
                    user = register(email, name, password, role="user",
                                  allowed_emails=allowed_list)
                    st.session_state.user = user
                    st.success("Tài khoản đã tạo thành công!")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))


# ─── Redirect if already logged in ───────────────────────────────────────────

if st.session_state.user:
    role = st.session_state.user.get("role", "user")
    if role in ("expert", "admin"):
        st.info(f"Đã đăng nhập với vai trò: **{role}**")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("💬 Bắt đầu trị liệu", type="primary"):
                go_to_chat()
        with col2:
            if st.button("📝 Sửa prompts"):
                go_expert()
        with col3:
            if role == "admin" and st.button("📊 Dashboard"):
                go_dashboard()
    else:
        if st.button("💬 Bắt đầu buổi trị liệu", type="primary", use_container_width=True):
            go_to_chat()
