"""
Tri-Lieu Therapy Chat — W1-W7 session loop.
Gate D → State Machine → LLM → W7 Synthesis.
"""

import os
import streamlit as st
import sys
import uuid
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import app.data.db as db
from app.auth import get_user_from_session
from app.state.gate_d import gate_d_check, format_safety_message, trigger_gate_d
from app.state.session_machine import TherapySessionMachine, WStep
from app.state.w7_synthesize import (
    generate_6a_and_homework,
    persist_homework,
    build_session_summary,
)
from app.api.llm import (
    build_framework_context,
    build_system_prompt,
    call_model_therapy,
    summarize_history,
)

# ─── Helpers (must be defined BEFORE use in Streamlit) ────────────────────────

def _extract_channel_data(response: str, w_step: WStep) -> dict:
    """
    Simple extraction of channel data from LLM response.
    """
    channel_map = {
        WStep.W2: "C",
        WStep.W3: "D",
        WStep.W4: "E",
        WStep.W4b: "F",
        WStep.W5: "G",
        WStep.W6: "H",
    }
    channel = channel_map.get(w_step)
    if channel:
        return {channel: response[:500]}
    return {}


st.set_page_config(page_title="Buổi Trị Liệu", page_icon="🧠")

# ─── Auth guard ───────────────────────────────────────────────────────────────

if not st.session_state.get("user"):
    st.warning("Vui lòng đăng nhập trước.")
    st.switch_page("pages/00_Login.py")

user = get_user_from_session(st.session_state.user)
if not user:
    st.error("Phiên đăng nhập đã hết hạn.")
    st.session_state.user = None
    st.rerun()

if not user.get("active", True):
    st.error("⚠️ Tài khoản đã bị khóa. Vui lòng liên hệ chuyên gia.")
    st.markdown(format_safety_message("vi"))
    st.stop()

# ─── Provider config ─────────────────────────────────────────────────────────

PROVIDER  = "gemini"
API_KEY   = str(st.secrets.get("GEMINI_API_KEY", "")).strip()
MODEL     = str(st.secrets.get("GEMINI_MODEL", "gemini-2.0-flash")).strip()

# ─── Session state init ─────────────────────────────────────────────────────

if "machine" not in st.session_state:
    st.session_state.machine = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())


def start_new_session():
    """Initialize a fresh therapy session."""
    machine = TherapySessionMachine(
        session_id=st.session_state.session_id,
        user_id=user["id"],
    )
    # Get last session's W-step
    sessions = db.get_user_sessions(user["id"], limit=1)
    last_w = sessions[0]["current_w"] if sessions else None
    machine.init_session(last_w)
    st.session_state.machine = machine
    st.session_state.chat_history = []


def get_provider_config():
    """Return (provider, api_key, model) tuple for Gemini."""
    api_key = str(st.secrets.get("GEMINI_API_KEY", "")).strip()
    model   = str(st.secrets.get("GEMINI_MODEL", "gemini-2.0-flash")).strip()
    return "gemini", api_key, model


# ─── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### Buổi Trị Liệu")

    machine = st.session_state.get("machine")

    if machine:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.metric("Bước", machine.current_step.value)
        with col2:
            st.metric("Mode", machine.mode)

        st.markdown(f"**Trạng thái:** {machine.step_label()}")

        plan_steps = [s.value for s in machine.plan]
        st.markdown(f"**Plan:** {' → '.join(plan_steps)}")

        st.markdown("---")
        if st.button("🔄 Phiên mới", use_container_width=True):
            st.session_state.machine = None
            st.session_state.chat_history = []
            st.session_state.session_id = str(uuid.uuid4())
            st.rerun()
    else:
        st.info("Chưa có phiên hoạt động.")

    st.markdown("---")
    st.markdown(f"**Người dùng:** {user['name']}")
    st.markdown(f"**Email:** {user['email']}")
    st.markdown(f"**Vai trò:** {user['role']}")

    st.markdown("---")
    if st.button("📋 Bài tập về nhà"):
        st.switch_page("pages/02_Homework.py")
    if st.button("📝 Trang chuyên gia"):
        st.switch_page("pages/03_Expert_Editor.py")
    if st.button("🚪 Đăng xuất"):
        st.session_state.user = None
        st.switch_page("pages/00_Login.py")


# ─── Header ──────────────────────────────────────────────────────────────────

st.markdown("## Buổi Trị Liệu")

if not st.session_state.machine:
    st.markdown("Chào bạn. Hệ thống này là không gian để **khám phá** — không phải chẩn đoán hay điều trị y khoa.")
    st.markdown("Mọi thứ bạn chia sẻ đều được giữ bảo mật trong phạm vi hệ thống.")
    st.markdown("Bạn có thể dừng bất cứ lúc nào.")

    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button("▶️ Bắt đầu buổi trị liệu", type="primary", use_container_width=True):
            start_new_session()
            st.rerun()
    st.stop()


machine = st.session_state.machine

# ─── Chat history ────────────────────────────────────────────────────────────

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ─── Step intro banner ────────────────────────────────────────────────────────

if not machine.is_done():
    with st.chat_message("assistant"):
        st.info(f"**{machine.step_label()}** — Bước {machine.current_step.value}")
        st.caption("Tôi sẽ đặt một số câu hỏi để hiểu bạn hơn. Không có câu trả lời đúng hay sai.")


# ─── User input ──────────────────────────────────────────────────────────────

user_input = st.chat_input("Bạn muốn chia sẻ gì hôm nay…")

if user_input:
    # ── Gate D Layer 1: synchronous keyword check ────────────────────────────
    triggered, reason = gate_d_check(user_input)
    if triggered:
        # Persist user message first
        machine.save_message("user", user_input)

        # Lock user
        db.lock_user(user["id"], locked_by="gate_d")
        machine.lock_due_to_gate_d()
        db.save_gate_d_event(machine.session_id, user["id"], reason, user_input)

        # Show safety message
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": format_safety_message("vi"),
        })
        st.session_state.locked = True
        st.error("⚠️ Hệ thống đã dừng. Vui lòng liên hệ chuyên gia.")
        st.rerun()

    # ── Save user message ──────────────────────────────────────────────────
    machine.save_message("user", user_input)
    st.session_state.chat_history.append({"role": "user", "content": user_input})

    # ── Build system prompt ─────────────────────────────────────────────────
    # ── Load framework context once per session ─────────────────────────
    if "framework_context" not in st.session_state:
        st.session_state.framework_context = build_framework_context()

    # ── Load user progress once per session (refreshes on new session start)
    if "cached_user_progress" not in st.session_state:
        st.session_state.cached_user_progress = db.load_user_progress(user["id"])

    # ── Build minimal system prompt ──────────────────────────────────
    prev_summary = summarize_history(st.session_state.chat_history)
    system_prompt = build_system_prompt(
        w_step=machine.current_step,
        mode=machine.mode,
        channel_context=machine.channel_state,
        framework_context=st.session_state.framework_context,
        prev_summary=prev_summary,
        user_progress=st.session_state.cached_user_progress,
    )

    # ── LLM call ────────────────────────────────────────────────────
    provider, api_key, model = get_provider_config()

    if not api_key:
        with st.chat_message("assistant"):
            st.error("⚠️ Chưa có API key hoặc GEMINI_API_KEY không đúng.")
            st.caption("Vui lòng kiểm tra Streamlit Cloud Settings → Secrets.")
        st.stop()

    with st.chat_message("assistant"):
        with st.spinner("Đang xử lý…"):
            try:
                response = call_model_therapy(
                    api_key=api_key,
                    model=model,
                    system=system_prompt,
                    messages=[
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.chat_history
                    ],
                    w_step=machine.current_step,
                )
            except Exception as e:
                response = f"Lỗi: {e}"

    # ── Save assistant response ─────────────────────────────────────────────
    machine.save_message("assistant", response)
    st.session_state.chat_history.append({"role": "assistant", "content": response})

    # ── Extract channel data and advance state machine ─────────────────────
    # Simple extraction from response (advanced: use LLM to extract structured data)
    captured = _extract_channel_data(response, machine.current_step)
    next_step = machine.advance(captured)

    # ── W7: synthesize ────────────────────────────────────────────────────
    if machine.is_done():
        actions_6a, homework, indicators = generate_6a_and_homework(
            machine.channel_state, machine.mode,
        )
        session_summary = build_session_summary(
            machine.channel_state, machine.mode, actions_6a, indicators,
        )
        machine.finish(session_summary, actions_6a, homework, indicators)
        persist_homework(user["id"], machine.session_id, homework)

        with st.chat_message("assistant"):
            st.success("✅ **Buổi trị liệu hoàn tất!**")
            st.markdown("---")
            st.markdown("### 📋 Tổng hợp Buổi Trị Liệu")
            st.markdown(f"**Hiện tượng chính:** {machine.channel_state.get('C', '...') or '...'}")

            col_a, col_b = st.columns(2)
            with col_a:
                with st.expander("**6A Hành Động**"):
                    for a in actions_6a:
                        badge = {"primary": "🟢", "secondary": "🟡", "background": "⚪"}.get(a[1], "⚪")
                        st.markdown(f"{badge} **{a[0]}** ({a[1]}): {a[2]}")

            with col_b:
                with st.expander("**Bài Tập Về Nhà**"):
                    for hw in homework:
                        st.markdown(f"- **{hw['action_letter']}**: {hw['assignment']}")

            st.markdown("---")
            st.info("💾 Kết quả đã được lưu. Bạn có thể xem chi tiết tại trang **Bài tập về nhà**.")
            if st.button("📋 Xem bài tập về nhà"):
                st.switch_page("pages/02_Homework.py")

    st.rerun()

